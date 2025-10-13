/**
 * AI Mentor Chat Screen
 * Main chat interface with AI Mentor
 */
import React, { useEffect, useRef, useState } from 'react';
import {
  StyleSheet,
  SafeAreaView,
  View,
  Text,
  Pressable,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';
import { aiChatApi } from '../utils/aiChatApi';
import { useChatStore } from '../stores/chatStore';
import { ChatMessage } from '../components/chat/ChatMessage';
import { ChatInput } from '../components/chat/ChatInput';

interface RouteParams {
  conversationId?: string | null;
}

/**
 * AI Mentor Chat Screen Component
 */
export const AIMentorChatScreen: React.FC = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const { conversationId } = (route.params as RouteParams) || {};
  const { getToken } = useAuth();
  const scrollViewRef = useRef<ScrollView>(null);

  const {
    currentConversation,
    messages,
    isSendingMessage,
    isLoadingMessages,
    setCurrentConversation,
    setMessages,
    addMessage,
    setLoadingMessages,
    setSendingMessage,
    clearCurrentChat,
  } = useChatStore();

  const [showSources, setShowSources] = useState(false);

  // Load conversation on mount
  useEffect(() => {
    if (conversationId) {
      loadConversation();
    } else {
      // New conversation
      clearCurrentChat();
    }

    // Cleanup on unmount
    return () => {
      // Don't clear if navigating to history
      // clearCurrentChat();
    };
  }, [conversationId]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (messages.length > 0) {
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);
    }
  }, [messages]);

  const loadConversation = async () => {
    if (!conversationId) return;

    try {
      setLoadingMessages(true);
      const msgs = await aiChatApi.getConversationMessages(conversationId, getToken);
      setMessages(msgs);

      // Set conversation metadata (we'll need to fetch this or get from store)
      // For now, just set the ID
      setCurrentConversation({
        id: conversationId,
        title: 'שיחה',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        message_count: msgs.length,
      });
    } catch (error: any) {
      console.error('Error loading conversation:', error);
      Alert.alert('שגיאה', 'לא הצלחנו לטעון את השיחה. נסה שוב.');
    } finally {
      setLoadingMessages(false);
    }
  };

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim() || isSendingMessage) return;

    try {
      setSendingMessage(true);

      // Add user message to UI immediately
      const tempUserMessage = {
        id: `temp-${Date.now()}`,
        conversation_id: currentConversation?.id || 'new',
        role: 'user' as const,
        content: messageText,
        timestamp: new Date().toISOString(),
      };
      addMessage(tempUserMessage);

      // Send message to API
      const response = await aiChatApi.sendMessage(
        {
          message: messageText,
          conversation_id: currentConversation?.id || undefined,
          include_sources: showSources,
        },
        getToken
      );

      // Update conversation if new
      if (!currentConversation && response.conversation_id) {
        setCurrentConversation({
          id: response.conversation_id,
          title: response.conversation_title || 'שיחה חדשה',
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
          message_count: 2,
        });
      }

      // Add assistant message
      addMessage(response.message);
    } catch (error: any) {
      console.error('Error sending message:', error);
      Alert.alert('שגיאה', error.message || 'לא הצלחנו לשלוח את ההודעה. נסה שוב.');
    } finally {
      setSendingMessage(false);
    }
  };

  const handleViewHistory = () => {
    navigation.navigate('ChatHistory');
  };

  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
        keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 0}
      >
        {/* Header */}
        <View style={styles.header}>
          <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
            <Text style={styles.backButtonText}>←</Text>
          </Pressable>

          <View style={styles.headerCenter}>
            <Text style={styles.headerTitle}>מרצה AI</Text>
            {currentConversation && (
              <Text style={styles.headerSubtitle} numberOfLines={1}>
                {currentConversation.title}
              </Text>
            )}
          </View>

          <Pressable onPress={handleViewHistory} style={styles.historyButton}>
            <Text style={styles.historyButtonText}>📋</Text>
          </Pressable>
        </View>

        {/* Messages */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
        >
          {isLoadingMessages ? (
            <View style={styles.loadingContainer}>
              <Text style={styles.loadingText}>טוען הודעות...</Text>
            </View>
          ) : messages.length === 0 ? (
            /* Welcome Message */
            <View style={styles.welcomeContainer}>
              <Text style={styles.welcomeIcon}>👨‍🏫</Text>
              <Text style={styles.welcomeTitle}>שלום! אני מרצה AI</Text>
              <Text style={styles.welcomeSubtitle}>
                אני כאן לעזור לך עם שאלות על החומר, חוקים, מושגים ועוד.{'\n'}
                שאל אותי כל שאלה!
              </Text>

              {/* Quick Questions */}
              <View style={styles.quickQuestions}>
                <Text style={styles.quickQuestionsTitle}>שאלות לדוגמה:</Text>
                <Pressable
                  onPress={() => handleSendMessage('מהו מידע פנים?')}
                  style={styles.quickQuestionButton}
                >
                  <Text style={styles.quickQuestionText}>מהו מידע פנים?</Text>
                </Pressable>
                <Pressable
                  onPress={() => handleSendMessage('מהם חובות הגילוי של חברה ציבורית?')}
                  style={styles.quickQuestionButton}
                >
                  <Text style={styles.quickQuestionText}>
                    מהם חובות הגילוי של חברה ציבורית?
                  </Text>
                </Pressable>
                <Pressable
                  onPress={() => handleSendMessage('הסבר לי על ניגוד עניינים')}
                  style={styles.quickQuestionButton}
                >
                  <Text style={styles.quickQuestionText}>הסבר לי על ניגוד עניינים</Text>
                </Pressable>
              </View>
            </View>
          ) : (
            /* Messages List */
            messages.map((message) => (
              <ChatMessage
                key={message.id}
                role={message.role}
                content={message.content}
                timestamp={message.timestamp}
                sources={message.sources}
              />
            ))
          )}
        </ScrollView>

        {/* Options Bar */}
        <View style={styles.optionsBar}>
          <Pressable
            onPress={() => setShowSources(!showSources)}
            style={[styles.optionButton, showSources && styles.optionButtonActive]}
          >
            <Text style={styles.optionButtonText}>
              {showSources ? '✓ ' : ''}הצג מקורות
            </Text>
          </Pressable>
        </View>

        {/* Input */}
        <ChatInput
          onSend={handleSendMessage}
          isSending={isSendingMessage}
          placeholder="שאל שאלה על החומר..."
        />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.lightGray,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backButtonText: {
    fontSize: 24,
    color: Colors.primary,
  },
  headerCenter: {
    flex: 1,
    alignItems: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.textPrimary,
  },
  headerSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginTop: 2,
  },
  historyButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  historyButtonText: {
    fontSize: 20,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    paddingVertical: 16,
    flexGrow: 1,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
  },
  welcomeContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  welcomeIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 12,
    textAlign: 'center',
  },
  welcomeSubtitle: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  quickQuestions: {
    width: '100%',
  },
  quickQuestionsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: 12,
    textAlign: 'right',
  },
  quickQuestionButton: {
    backgroundColor: Colors.secondaryLight,
    borderRadius: 12,
    padding: 16,
    marginBottom: 8,
  },
  quickQuestionText: {
    fontSize: 14,
    color: Colors.primary,
    textAlign: 'right',
  },
  optionsBar: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: Colors.background,
    borderTopWidth: 1,
    borderTopColor: Colors.lightGray,
    gap: 8,
  },
  optionButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.lightGray,
  },
  optionButtonActive: {
    backgroundColor: Colors.secondaryLight,
    borderColor: Colors.primary,
  },
  optionButtonText: {
    fontSize: 14,
    color: Colors.textPrimary,
  },
});
