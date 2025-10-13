#!/usr/bin/env python3
"""
Chat API Routes
Handles AI Mentor chat conversations and messages
"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import sys
from pathlib import Path
import uuid

sys.path.append(str(Path(__file__).parent.parent.parent))

from api.auth import get_current_user
from agent.agents.legal_expert import LegalExpertAgent

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


# In-memory storage (TODO: Replace with database)
# Structure: { user_id: { conversation_id: { messages: [], title: str, created_at: str, updated_at: str } } }
conversations_storage = {}


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


def get_user_conversations(user_id: str) -> dict:
    """Get all conversations for a user"""
    if user_id not in conversations_storage:
        conversations_storage[user_id] = {}
    return conversations_storage[user_id]


def create_conversation(user_id: str, title: str) -> str:
    """Create a new conversation"""
    conversation_id = str(uuid.uuid4())
    user_convs = get_user_conversations(user_id)

    now = datetime.now().isoformat()
    user_convs[conversation_id] = {
        "id": conversation_id,
        "title": title,
        "created_at": now,
        "updated_at": now,
        "messages": [],
    }

    return conversation_id


def add_message_to_conversation(
    user_id: str,
    conversation_id: str,
    role: str,
    content: str,
    sources: Optional[List[str]] = None
) -> ChatMessage:
    """Add a message to a conversation"""
    user_convs = get_user_conversations(user_id)

    if conversation_id not in user_convs:
        raise HTTPException(status_code=404, detail="Conversation not found")

    message_id = str(uuid.uuid4())
    timestamp = datetime.now().isoformat()

    message = ChatMessage(
        id=message_id,
        conversation_id=conversation_id,
        role=role,
        content=content,
        timestamp=timestamp,
        sources=sources,
    )

    user_convs[conversation_id]["messages"].append(message.dict())
    user_convs[conversation_id]["updated_at"] = timestamp

    return message


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    user: dict = Depends(get_current_user)
):
    """
    Send a message to AI Mentor

    Creates a new conversation if conversation_id is not provided
    """
    try:
        user_id = user["user_id"]

        # Create new conversation if needed
        if not request.conversation_id:
            title = generate_conversation_title(request.message)
            conversation_id = create_conversation(user_id, title)
            conversation_title = title
        else:
            conversation_id = request.conversation_id
            user_convs = get_user_conversations(user_id)
            if conversation_id not in user_convs:
                raise HTTPException(status_code=404, detail="Conversation not found")
            conversation_title = user_convs[conversation_id]["title"]

        # Add user message
        user_message = add_message_to_conversation(
            user_id,
            conversation_id,
            "user",
            request.message
        )

        # Get AI response
        expert = get_legal_expert()
        response = expert.process_with_rag(
            query=request.message,
            k=10
        )

        answer = response.get('answer', 'מצטער, לא הצלחתי לייצר תשובה. נסה שוב.')

        # Extract sources if requested
        sources = None
        if request.include_sources and response.get('sources'):
            sources = [
                f"{src.get('document', 'מסמך')} - עמוד {src.get('page', '?')}"
                for src in response['sources'][:5]
            ]

        # Add assistant message
        assistant_message = add_message_to_conversation(
            user_id,
            conversation_id,
            "assistant",
            answer,
            sources
        )

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
async def get_conversations(user: dict = Depends(get_current_user)):
    """
    Get all conversations for the current user
    """
    try:
        user_id = user["user_id"]
        user_convs = get_user_conversations(user_id)

        conversations = []
        for conv_id, conv_data in user_convs.items():
            last_message = None
            if conv_data["messages"]:
                last_msg = conv_data["messages"][-1]
                last_message = last_msg["content"][:100]
                if len(last_msg["content"]) > 100:
                    last_message += "..."

            conversations.append(
                ChatConversation(
                    id=conv_data["id"],
                    title=conv_data["title"],
                    created_at=conv_data["created_at"],
                    updated_at=conv_data["updated_at"],
                    message_count=len(conv_data["messages"]),
                    last_message=last_message
                )
            )

        # Sort by updated_at (most recent first)
        conversations.sort(key=lambda x: x.updated_at, reverse=True)

        return conversations

    except Exception as e:
        print(f"Error in get_conversations: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה בטעינת שיחות: {str(e)}")


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessage])
async def get_conversation_messages(
    conversation_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Get all messages for a specific conversation
    """
    try:
        user_id = user["user_id"]
        user_convs = get_user_conversations(user_id)

        if conversation_id not in user_convs:
            raise HTTPException(status_code=404, detail="Conversation not found")

        messages = user_convs[conversation_id]["messages"]
        return [ChatMessage(**msg) for msg in messages]

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in get_conversation_messages: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה בטעינת הודעות: {str(e)}")


@router.delete("/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user)
):
    """
    Delete a conversation
    """
    try:
        user_id = user["user_id"]
        user_convs = get_user_conversations(user_id)

        if conversation_id not in user_convs:
            raise HTTPException(status_code=404, detail="Conversation not found")

        del user_convs[conversation_id]

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
    user: dict = Depends(get_current_user)
):
    """
    Rename a conversation
    """
    try:
        user_id = user["user_id"]
        user_convs = get_user_conversations(user_id)

        if conversation_id not in user_convs:
            raise HTTPException(status_code=404, detail="Conversation not found")

        user_convs[conversation_id]["title"] = request.title
        user_convs[conversation_id]["updated_at"] = datetime.now().isoformat()

        return {"message": "שיחה שונתה בהצלחה", "title": request.title}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error in rename_conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"שגיאה בשינוי שם השיחה: {str(e)}")
