#!/usr/bin/env python3
"""
Chat API Routes
Handles AI Mentor chat conversations and messages
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import sys
from pathlib import Path
import uuid
import asyncio

sys.path.append(str(Path(__file__).parent.parent.parent))

from api.auth_simple import get_current_user_id
from agent.agents.legal_expert import LegalExpertAgent
from api.utils.cache import get_cached, set_cached, delete_pattern, CacheTTL
import os
from supabase import create_client, Client
import json

# Initialize Supabase client
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Initialize router
router = APIRouter(prefix="/api/chat", tags=["chat"])

# Initialize legal expert agent (singleton)
legal_expert = None


def get_legal_expert():
    """Get or initialize Legal Expert Agent"""
    global legal_expert
    if legal_expert is None:
        legal_expert = LegalExpertAgent(top_k=10, use_thinking_model=True)
    return legal_expert


async def invalidate_chat_cache(user_id: str, conversation_id: str = None):
    """Invalidate chat-related cache for a user"""
    try:
        # Invalidate user's conversation list
        await delete_pattern(f"chat:conversations:{user_id}")

        # If conversation_id provided, invalidate that conversation's messages
        if conversation_id:
            await delete_pattern(f"chat:messages:{conversation_id}")
    except Exception as e:
        print(f"⚠️  Cache invalidation error: {e}")
        # Don't fail the request if cache invalidation fails


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class SendMessageRequest(BaseModel):
    """Request to send a message"""
    message: str = Field(..., min_length=1, max_length=5000)
    conversation_id: Optional[str] = None
    include_sources: bool = Field(default=False)


class ChatMessage(BaseModel):
    """Chat message"""
    id: str
    conversation_id: str
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: str
    sources: Optional[List[str]] = None


class SendMessageResponse(BaseModel):
    """Response after sending a message"""
    message: ChatMessage
    conversation_id: str
    conversation_title: Optional[str] = None


class ChatConversation(BaseModel):
    """Chat conversation summary"""
    id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int
    last_message: Optional[str] = None


class RenameConversationRequest(BaseModel):
    """Request to rename a conversation"""
    title: str = Field(..., min_length=1, max_length=100)


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_conversation_title(first_message: str) -> str:
    """Generate a title for a conversation based on the first message"""
    # Take first 50 characters and add ellipsis if needed
    title = first_message[:50].strip()
    if len(first_message) > 50:
        title += "..."
    return title


def create_conversation(user_id: str, title: str) -> str:
    """Create a new conversation in database"""
    result = supabase.table("chat_conversations").insert({
        "user_id": user_id,
        "title": title,
    }).execute()

    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create conversation")

    return str(result.data[0]["id"])


async def add_message_to_conversation(
    user_id: str,
    conversation_id: str,
    role: str,
    content: str,
    sources: Optional[List[str]] = None
) -> ChatMessage:
    """Add a message to a conversation in database"""
    # Verify conversation exists and belongs to user
    conv_result = supabase.table("chat_conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).eq("is_deleted", False).execute()

    if not conv_result.data:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Insert message
    message_result = supabase.table("chat_messages").insert({
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "sources": sources,
    }).execute()

    if not message_result.data:
        raise HTTPException(status_code=500, detail="Failed to add message")

    msg_data = message_result.data[0]

    # Update conversation's updated_at
    supabase.table("chat_conversations").update({
        "updated_at": msg_data["created_at"]
    }).eq("id", conversation_id).execute()

    # Invalidate cache
    await invalidate_chat_cache(user_id, conversation_id)

    return ChatMessage(
        id=str(msg_data["id"]),
        conversation_id=str(msg_data["conversation_id"]),
        role=msg_data["role"],
        content=msg_data["content"],
        timestamp=msg_data["created_at"],
        sources=msg_data.get("sources"),
    )


def get_conversation_messages_from_db(conversation_id: str, user_id: str, limit: int = 10) -> List[dict]:
    """Get recent messages from a conversation"""
    # Verify conversation belongs to user
    conv_result = supabase.table("chat_conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).eq("is_deleted", False).execute()

    if not conv_result.data:
        return []

    # Get messages
    messages_result = supabase.table("chat_messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).limit(limit).execute()

    return messages_result.data if messages_result.data else []


async def process_ai_response_background(
    message_id: str,
    conversation_id: str,
    user_id: str,
    query: str,
    include_sources: bool
):
    """
    Background task to process AI response
    This runs asynchronously and updates the message when complete
    """
    try:
        print(f"🤖 Starting AI processing for message {message_id}")

        # Get AI response
        expert = get_legal_expert()
        response = expert.process_with_rag(query=query, k=10)

        answer = response.get('answer', 'מצטער, לא הצלחתי לייצר תשובה. נסה שוב.')

        # Extract sources if requested
        sources = None
        if include_sources and response.get('sources'):
            sources = [
                f"{src.get('document', 'מסמך')} - עמוד {src.get('page', '?')}"
                for src in response['sources'][:5]
            ]

        # Update the message with the actual response
        supabase.table("chat_messages").update({
            "content": answer,
            "sources": sources,
        }).eq("id", message_id).execute()

        # Update conversation's updated_at
        supabase.table("chat_conversations").update({
            "updated_at": datetime.now().isoformat()
        }).eq("id", conversation_id).execute()

        # Invalidate cache after updating message
        await invalidate_chat_cache(user_id, conversation_id)

        print(f"✅ AI processing complete for message {message_id}")

    except Exception as e:
        print(f"❌ Error in AI processing for message {message_id}: {str(e)}")
        # Update message with error
        supabase.table("chat_messages").update({
            "content": f"שגיאה בעיבוד התשובה: {str(e)}"
        }).eq("id", message_id).execute()

        # Invalidate cache even on error
        try:
            await invalidate_chat_cache(user_id, conversation_id)
        except Exception as cache_err:
            print(f"⚠️  Failed to invalidate cache after error: {cache_err}")


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    background_tasks: BackgroundTasks,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Send a message to AI Mentor

    Creates a new conversation if conversation_id is not provided.
    Returns immediately with a placeholder response while AI processes in background.
    """
    try:
        from api.routes.exams import get_user_by_clerk_id
        user = await get_user_by_clerk_id(clerk_user_id)
        user_id = str(user["id"])

        # Create new conversation if needed
        if not request.conversation_id:
            title = generate_conversation_title(request.message)
            conversation_id = create_conversation(user_id, title)
            conversation_title = title
        else:
            conversation_id = request.conversation_id
            # Verify conversation exists
            conv_result = supabase.table("chat_conversations").select("title").eq("id", conversation_id).eq("user_id", user_id).eq("is_deleted", False).execute()
            if not conv_result.data:
                raise HTTPException(status_code=404, detail="Conversation not found")
            conversation_title = conv_result.data[0]["title"]

        # Get conversation history for context BEFORE adding user message
        conversation_messages = get_conversation_messages_from_db(conversation_id, user_id, limit=10)

        # Build context from recent messages
        context = ""
        if conversation_messages:
            context = "\n\n".join([
                f"{'שאלה' if msg['role'] == 'user' else 'תשובה'}: {msg['content']}"
                for msg in conversation_messages
            ])
            context = f"הקשר השיחה הקודם:\n{context}\n\n"

        # Add user message
        user_message = await add_message_to_conversation(
            user_id,
            conversation_id,
            "user",
            request.message
        )

        # Create placeholder assistant message immediately (empty, will be updated by background task)
        placeholder_content = ""
        assistant_message = await add_message_to_conversation(
            user_id,
            conversation_id,
            "assistant",
            placeholder_content,
            None
        )

        # Prepare query with context and mobile-friendly instructions
        mobile_instruction = """
        הנחיות חשובות:
        - כתוב תשובה קצרה וממוקדת (2-4 פסקאות מקסימום)
        - השתמש בטקסט רגיל וברור ללא markdown מורכב
        - אם יש נקודות מרכזיות, רשום אותן בשורות נפרדות עם מקף בהתחלה
        - הימנע מטבלאות, כותרות מסובכות או עיצוב מורכב
        - התמקד במידע החשוב ביותר

        """

        query_with_context = f"{mobile_instruction}{context}שאלה נוכחית: {request.message}" if context else f"{mobile_instruction}שאלה: {request.message}"

        # Queue AI processing as background task
        background_tasks.add_task(
            process_ai_response_background,
            message_id=assistant_message.id,
            conversation_id=conversation_id,
            user_id=user_id,
            query=query_with_context,
            include_sources=request.include_sources
        )

        # Return immediately with placeholder
        return SendMessageResponse(
            message=assistant_message,
            conversation_id=conversation_id,
            conversation_title=conversation_title if not request.conversation_id else None
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in send_message: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה בשליחת הודעה: {str(e)}")


@router.get("/conversations", response_model=List[ChatConversation])
async def get_conversations(clerk_user_id: str = Depends(get_current_user_id)):
    """
    Get all conversations for the current user (with Redis cache)
    """
    try:
        from api.routes.exams import get_user_by_clerk_id
        user = await get_user_by_clerk_id(clerk_user_id)
        user_id = str(user["id"])

        # Try cache first
        cache_key = f"chat:conversations:{user_id}"
        cached = await get_cached(cache_key)
        if cached:
            print(f"✅ Cache HIT: Conversations for user {user_id[:8]}...")
            return [ChatConversation(**conv) for conv in json.loads(cached)]

        print(f"❌ Cache MISS: Conversations for user {user_id[:8]}...")

        # Get all conversations for user
        conv_result = supabase.table("chat_conversations").select("*").eq("user_id", user_id).eq("is_deleted", False).order("updated_at", desc=True).execute()

        conversations = []
        for conv_data in conv_result.data:
            # Get message count
            msg_count_result = supabase.table("chat_messages").select("id", count="exact").eq("conversation_id", conv_data["id"]).execute()
            message_count = msg_count_result.count if msg_count_result.count else 0

            # Get last message
            last_message = None
            last_msg_result = supabase.table("chat_messages").select("content").eq("conversation_id", conv_data["id"]).order("created_at", desc=True).limit(1).execute()
            if last_msg_result.data:
                last_msg_content = last_msg_result.data[0]["content"]
                last_message = last_msg_content[:100]
                if len(last_msg_content) > 100:
                    last_message += "..."

            conversations.append(
                ChatConversation(
                    id=str(conv_data["id"]),
                    title=conv_data["title"],
                    created_at=conv_data["created_at"],
                    updated_at=conv_data["updated_at"],
                    message_count=message_count,
                    last_message=last_message
                )
            )

        # Cache for 5 minutes
        await set_cached(cache_key, json.dumps([conv.dict() for conv in conversations]), ttl_seconds=CacheTTL.SHORT)

        return conversations

    except Exception as e:
        print(f"Error in get_conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה בטעינת שיחות: {str(e)}")


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessage])
async def get_conversation_messages(
    conversation_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Get all messages for a specific conversation (with Redis cache)
    """
    try:
        from api.routes.exams import get_user_by_clerk_id
        user = await get_user_by_clerk_id(clerk_user_id)
        user_id = str(user["id"])

        # Try cache first
        cache_key = f"chat:messages:{conversation_id}"
        cached = await get_cached(cache_key)
        if cached:
            print(f"✅ Cache HIT: Messages for conversation {conversation_id[:8]}...")
            return [ChatMessage(**msg) for msg in json.loads(cached)]

        print(f"❌ Cache MISS: Messages for conversation {conversation_id[:8]}...")

        # Verify conversation exists and belongs to user
        conv_result = supabase.table("chat_conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).eq("is_deleted", False).execute()

        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Get all messages
        messages_result = supabase.table("chat_messages").select("*").eq("conversation_id", conversation_id).order("created_at", desc=False).execute()

        messages = []
        for msg_data in messages_result.data:
            messages.append(
                ChatMessage(
                    id=str(msg_data["id"]),
                    conversation_id=str(msg_data["conversation_id"]),
                    role=msg_data["role"],
                    content=msg_data["content"],
                    timestamp=msg_data["created_at"],
                    sources=msg_data.get("sources"),
                )
            )

        # Cache for 1 minute (short TTL since messages update frequently)
        await set_cached(cache_key, json.dumps([msg.dict() for msg in messages]), ttl_seconds=CacheTTL.VERY_SHORT)

        return messages

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_conversation_messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה בטעינת הודעות: {str(e)}")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Delete a conversation (soft delete)
    """
    try:
        from api.routes.exams import get_user_by_clerk_id
        user = await get_user_by_clerk_id(clerk_user_id)
        user_id = str(user["id"])

        # Verify conversation exists and belongs to user
        conv_result = supabase.table("chat_conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).eq("is_deleted", False).execute()

        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Soft delete
        supabase.table("chat_conversations").update({
            "is_deleted": True,
            "updated_at": datetime.now().isoformat()
        }).eq("id", conversation_id).execute()

        # Invalidate cache
        await invalidate_chat_cache(user_id, conversation_id)

        return {"message": "שיחה נמחקה בהצלחה"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in delete_conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה במחיקת שיחה: {str(e)}")


@router.patch("/conversations/{conversation_id}/rename")
async def rename_conversation(
    conversation_id: str,
    request: RenameConversationRequest,
    clerk_user_id: str = Depends(get_current_user_id)
):
    """
    Rename a conversation
    """
    try:
        from api.routes.exams import get_user_by_clerk_id
        user = await get_user_by_clerk_id(clerk_user_id)
        user_id = str(user["id"])

        # Verify conversation exists and belongs to user
        conv_result = supabase.table("chat_conversations").select("id").eq("id", conversation_id).eq("user_id", user_id).eq("is_deleted", False).execute()

        if not conv_result.data:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Update title
        supabase.table("chat_conversations").update({
            "title": request.title,
            "updated_at": datetime.now().isoformat()
        }).eq("id", conversation_id).execute()

        # Invalidate cache
        await invalidate_chat_cache(user_id, conversation_id)

        return {"message": "שיחה שונתה בהצלחה", "title": request.title}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in rename_conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה בשינוי שם השיחה: {str(e)}")
