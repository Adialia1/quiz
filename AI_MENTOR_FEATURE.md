# AI Mentor Feature Documentation

## 🎯 Overview

The AI Mentor feature provides an interactive chat interface where users can ask questions about legal topics and receive AI-powered answers with optional source references. The feature includes conversation history management, allowing users to continue previous discussions.

## ✨ Features

### Core Functionality
- **Real-time Chat**: Interactive chat interface with AI-powered legal expert
- **Conversation History**: Save and continue previous conversations
- **Source References**: Optional display of legal document sources
- **Hebrew RTL Support**: Fully localized for Hebrew with RTL layout
- **Quick Questions**: Pre-defined example questions for new users

### User Experience
- **Seamless Navigation**: Easy access from home screen
- **Conversation Management**: View, continue, and delete conversations
- **Auto-scroll**: Automatic scrolling to new messages
- **Typing Indicators**: Visual feedback when AI is responding
- **Welcome Screen**: Helpful introduction for first-time users

## 📁 File Structure

### Frontend (React Native)

```
app/
├── src/
│   ├── components/
│   │   └── chat/
│   │       ├── ChatMessage.tsx       # Individual message bubble
│   │       └── ChatInput.tsx         # Message input field
│   ├── screens/
│   │   ├── ChatHistoryScreen.tsx    # List of all conversations
│   │   └── AIMentorChatScreen.tsx   # Main chat interface
│   ├── stores/
│   │   └── chatStore.ts             # Zustand store for chat state
│   └── utils/
│       └── aiChatApi.ts             # API utility functions
```

### Backend (FastAPI)

```
api/
└── routes/
    └── chat.py                       # Chat API endpoints
```

## 🔌 API Endpoints

### 1. Send Message
**POST** `/api/chat/send`

Send a message to the AI Mentor and receive a response.

**Request Body:**
```json
{
  "message": "מהו מידע פנים?",
  "conversation_id": "uuid-optional",
  "include_sources": false
}
```

**Response:**
```json
{
  "message": {
    "id": "msg-uuid",
    "conversation_id": "conv-uuid",
    "role": "assistant",
    "content": "מידע פנים הוא...",
    "timestamp": "2025-10-13T...",
    "sources": ["מקור 1", "מקור 2"]
  },
  "conversation_id": "conv-uuid",
  "conversation_title": "מהו מידע פנים..."
}
```

### 2. Get Conversations
**GET** `/api/chat/conversations`

Retrieve all conversations for the current user.

**Response:**
```json
[
  {
    "id": "conv-uuid",
    "title": "מהו מידע פנים...",
    "created_at": "2025-10-13T...",
    "updated_at": "2025-10-13T...",
    "message_count": 4,
    "last_message": "תודה על ההסבר..."
  }
]
```

### 3. Get Conversation Messages
**GET** `/api/chat/conversations/{conversation_id}/messages`

Get all messages in a specific conversation.

**Response:**
```json
[
  {
    "id": "msg-uuid",
    "conversation_id": "conv-uuid",
    "role": "user",
    "content": "מהו מידע פנים?",
    "timestamp": "2025-10-13T...",
    "sources": null
  },
  {
    "id": "msg-uuid-2",
    "conversation_id": "conv-uuid",
    "role": "assistant",
    "content": "מידע פנים הוא...",
    "timestamp": "2025-10-13T...",
    "sources": ["חוק ניירות ערך..."]
  }
]
```

### 4. Delete Conversation
**DELETE** `/api/chat/conversations/{conversation_id}`

Delete a conversation and all its messages.

**Response:**
```json
{
  "message": "שיחה נמחקה בהצלחה"
}
```

### 5. Rename Conversation
**PATCH** `/api/chat/conversations/{conversation_id}/rename`

Rename a conversation.

**Request Body:**
```json
{
  "title": "שיחה על מידע פנים"
}
```

**Response:**
```json
{
  "message": "שיחה שונתה בהצלחה",
  "title": "שיחה על מידע פנים"
}
```

## 🎨 UI Components

### ChatMessage Component

Displays individual chat messages with proper styling for user vs assistant messages.

**Props:**
```typescript
interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  sources?: string[];
}
```

**Features:**
- Different styling for user/assistant messages
- Optional timestamp display
- Source references display
- RTL text alignment

### ChatInput Component

Input field for composing and sending messages.

**Props:**
```typescript
interface ChatInputProps {
  onSend: (message: string) => void;
  isSending?: boolean;
  placeholder?: string;
}
```

**Features:**
- Multiline text input (up to 5000 characters)
- Send button with loading state
- Keyboard-aware layout
- RTL support

## 🗄️ State Management

### Chat Store (Zustand)

**State:**
```typescript
interface ChatState {
  currentConversation: ChatConversation | null;
  messages: ChatMessage[];
  conversations: ChatConversation[];
  isLoadingMessages: boolean;
  isLoadingConversations: boolean;
  isSendingMessage: boolean;
}
```

**Actions:**
- `setCurrentConversation`: Set active conversation
- `setMessages`: Set messages for current conversation
- `addMessage`: Add new message to current conversation
- `setConversations`: Update conversations list
- `updateConversation`: Update conversation metadata
- `deleteConversationFromStore`: Remove conversation
- `clearCurrentChat`: Clear current conversation
- `reset`: Reset entire state

## 🚀 Getting Started

### 1. Backend Setup

The backend API routes are already integrated into the main FastAPI application.

**Start the API:**
```bash
cd /Users/adialia/Desktop/quiz-ai-mentor
./start_api.sh
```

The chat endpoints will be available at:
- `http://localhost:8000/api/chat/send`
- `http://localhost:8000/api/chat/conversations`
- etc.

### 2. Frontend Setup

No additional dependencies needed! All chat components use existing libraries:
- React Navigation (already installed)
- Zustand (already installed)
- React Native components

**Run the app:**
```bash
cd /Users/adialia/Desktop/quiz-ai-mentor/app
npm start
```

### 3. Using the Feature

1. **Access from Home Screen**: Tap on "מרצה AI" card
2. **View Conversations**: Opens chat history screen
3. **Start New Chat**: Tap "+ שיחה חדשה"
4. **Ask Questions**: Type and send messages
5. **Continue Conversations**: Tap any conversation to continue

## 🎨 Design Principles

### Colors
Following the app's design system from `src/config/colors.ts`:
- **Primary Blue (#0A76F3)**: User messages, buttons
- **White (#FFFFFF)**: Assistant messages, backgrounds
- **Secondary Light (#E3F2FD)**: Quick question buttons
- **Text Primary (#212121)**: Main text
- **Text Secondary (#757575)**: Timestamps, metadata

### Typography
- All text is right-aligned (RTL)
- Hebrew font support
- Clear hierarchy: titles (18-24px), body (16px), metadata (12-14px)

### Spacing
- Consistent 16px padding
- 12px border radius for cards
- 8px gaps between elements

## 🔐 Security

### Authentication
- All endpoints require Clerk authentication
- Token validation via `get_current_user` dependency
- User-specific conversation isolation

### Data Storage
**Current Implementation:**
- In-memory storage (dictionary)
- User conversations isolated by `user_id`

**TODO for Production:**
- Replace with Supabase/PostgreSQL database
- Add proper data persistence
- Implement conversation limits per user

## 🧪 Testing

### Manual Testing Checklist

**Chat Functionality:**
- [ ] Send a message in new conversation
- [ ] Receive AI response
- [ ] Continue conversation with follow-up
- [ ] View sources (toggle sources option)

**Conversation Management:**
- [ ] View all conversations
- [ ] Open existing conversation
- [ ] Delete conversation
- [ ] Start new conversation

**UI/UX:**
- [ ] Verify RTL layout
- [ ] Check Hebrew text display
- [ ] Test on iOS and Android
- [ ] Verify keyboard behavior
- [ ] Test auto-scroll to new messages

## 📝 Future Enhancements

### High Priority
1. **Database Integration**: Replace in-memory storage with Supabase
2. **Conversation Search**: Search within conversations
3. **Export Chat**: Export conversation as PDF or text
4. **Share Messages**: Share individual messages

### Medium Priority
5. **Voice Input**: Speech-to-text for questions
6. **Bookmarks**: Save important messages
7. **Message Reactions**: Like/dislike messages
8. **Context Memory**: Maintain conversation context

### Low Priority
9. **Chat Themes**: Customizable chat appearance
10. **Message Editing**: Edit sent messages
11. **Message Deletion**: Delete individual messages
12. **Typing Indicators**: Show when AI is typing

## 🐛 Known Issues

### Current Limitations
1. **In-Memory Storage**: Data lost on server restart
2. **No Pagination**: All messages loaded at once
3. **No Image Support**: Text-only messages
4. **No File Attachments**: Cannot attach documents

### Potential Improvements
1. Add message pagination for long conversations
2. Implement conversation search
3. Add conversation export functionality
4. Improve error handling and retry logic

## 📚 References

### Documentation
- [Legal Expert Agent](/agent/agents/legal_expert.py)
- [Clerk Authentication](/api/auth.py)
- [React Navigation](https://reactnavigation.org/)
- [Zustand Store](https://docs.pmnd.rs/zustand)

### Related Files
- Main API: `/api/main.py`
- Colors Config: `/app/src/config/colors.ts`
- Auth Store: `/app/src/stores/authStore.ts`

## 🎉 Conclusion

The AI Mentor feature provides a comprehensive chat interface for users to interact with the legal expert AI. The implementation follows the app's design principles, supports Hebrew RTL layout, and integrates seamlessly with the existing authentication and navigation systems.

**Key Benefits:**
- ✅ User-friendly chat interface
- ✅ Conversation history management
- ✅ Hebrew RTL support
- ✅ Source references for legal answers
- ✅ Seamless integration with existing app

**Next Steps:**
1. Test the feature thoroughly
2. Add database persistence
3. Gather user feedback
4. Implement enhancements based on usage patterns

---

**Created:** 2025-10-13
**Last Updated:** 2025-10-13
**Status:** ✅ Complete
