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
import { useTokenRefresh } from '../hooks/useTokenRefresh';
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
  const { refreshTokenManually } = useTokenRefresh();
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
  const [isThinking, setIsThinking] = useState(false);
  const [thinkingText, setThinkingText] = useState('מחפש מקורות...');
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

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
      // Clear polling interval
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
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

  /**
   * Poll for message updates when AI is processing
   * Checks if the assistant's message has been updated from placeholder
   */
  const startPollingForResponse = (convId: string, messageId: string) => {
    console.log('Starting polling for message:', messageId);

    let pollAttempts = 0;
    const maxAttempts = 60; // 60 attempts * 5 seconds = 5 minutes max (increased for AI responses)

    // Clear any existing polling
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }

    pollingIntervalRef.current = setInterval(async () => {
      pollAttempts++;
      console.log(`Polling attempt ${pollAttempts} for message ${messageId}`);

      try {
        // Get a fresh token for each poll attempt to avoid expiration
        const freshToken = await getToken({ template: 'default' });

        // Fetch latest messages with fresh token
        const msgs = await aiChatApi.getConversationMessages(convId, async () => freshToken);

        // Find the message we're waiting for
        const updatedMessage = msgs.find((m) => m.id === messageId);

        if (updatedMessage && updatedMessage.content && updatedMessage.content.trim() !== '') {
          // Message has been updated with actual response
          console.log('Message updated with response:', updatedMessage.content.substring(0, 50));
          setMessages(msgs);
          setIsThinking(false);
          setSendingMessage(false);

          // Stop polling
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        } else if (pollAttempts >= maxAttempts) {
          // Timeout - stop polling
          console.warn('Polling timeout reached');
          setIsThinking(false);
          setSendingMessage(false);
          Alert.alert('התראה', 'התשובה לוקחת זמן רב. אנא רענן את השיחה מאוחר יותר.');

          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
      } catch (error: any) {
        console.error('Polling error:', error);

        // Check if it's a token expiration error
        if (error.message && error.message.includes('expired')) {
          console.log('Token expired, stopping polling. User needs to refresh.');
          setIsThinking(false);
          setSendingMessage(false);
          Alert.alert('פג תוקף החיבור', 'אנא צא ונכנס שוב לאפליקציה');

          // Stop polling on auth errors
          if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null;
          }
        }
        // For other errors, continue polling (might be temporary network issue)
      }
    }, 5000); // Poll every 5 seconds
  };

  const handleSendMessage = async (messageText: string) => {
    if (!messageText.trim() || isSendingMessage) return;

    try {
      setSendingMessage(true);
      setIsThinking(true);

      // Animate thinking text - show each step once sequentially
      const thinkingStates = [
        'מחפש מקורות...',
        'מנתח מסמכים...',
        'מכין תשובה...',
      ];

      // Show each state sequentially
      const showThinkingSteps = () => {
        thinkingStates.forEach((state, index) => {
          setTimeout(() => {
            setThinkingText(state);
          }, index * 3500); // 3.5 seconds per step
        });
      };

      showThinkingSteps();

      // Add user message to UI immediately
      const tempUserMessage = {
        id: `temp-${Date.now()}`,
        conversation_id: currentConversation?.id || 'new',
        role: 'user' as const,
        content: messageText,
        timestamp: new Date().toISOString(),
      };
      addMessage(tempUserMessage);

      // Send message to API (returns immediately with placeholder)
      const response = await aiChatApi.sendMessage(
        {
          message: messageText,
          conversation_id: currentConversation?.id || undefined,
          include_sources: showSources,
        },
        getToken
      );

      console.log('API Response (placeholder):', response);

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

      // Don't add placeholder to UI - we show thinking animation instead
      // The actual message will be added when polling detects the response
      console.log('Placeholder message created, ID:', response.message.id);

      // Start polling for the actual AI response
      startPollingForResponse(response.conversation_id, response.message.id);
    } catch (error: any) {
      console.error('Error sending message:', error);

      // Check for token expiration
      if (error.message && (error.message.includes('expired') || error.message.includes('Invalid token'))) {
        Alert.alert(
          'פג תוקף החיבור',
          'אנא צא מהאפליקציה ונכנס שוב כדי לרענן את החיבור.',
          [{ text: 'אישור' }]
        );
      } else {
        Alert.alert('שגיאה', error.message || 'לא הצלחנו לשלוח את ההודעה. נסה שוב.');
      }

      setSendingMessage(false);
      setIsThinking(false);
      setThinkingText('מחפש מקורות...'); // Reset to initial state
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
            <Text style={styles.headerTitle}>מרצה חכם</Text>
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
              <Text style={styles.welcomeTitle}>שלום! אני מרצה חכם</Text>
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
            <>
              {/* Messages List */}
              {messages.map((message) => (
                <ChatMessage
                  key={message.id}
                  role={message.role}
                  content={message.content}
                  timestamp={message.timestamp}
                  sources={message.sources}
                />
              ))}

              {/* Thinking Animation */}
              {isThinking && (
                <View style={styles.thinkingContainer}>
                  <View style={styles.thinkingBubble}>
                    <View style={styles.thinkingContent}>
                      <View style={styles.thinkingDots}>
                        <View style={[styles.thinkingDot, styles.thinkingDot1]} />
                        <View style={[styles.thinkingDot, styles.thinkingDot2]} />
                        <View style={[styles.thinkingDot, styles.thinkingDot3]} />
                      </View>
                      <Text style={styles.thinkingTextStyle}>{thinkingText}</Text>
                    </View>
                  </View>
                </View>
              )}
            </>
          )}
        </ScrollView>

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
  thinkingContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    marginBottom: 8,
  },
  thinkingBubble: {
    alignSelf: 'flex-start',
    backgroundColor: Colors.primaryLight,
    borderRadius: 16,
    paddingHorizontal: 16,
    paddingVertical: 12,
    maxWidth: '80%',
  },
  thinkingContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  thinkingDots: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
  },
  thinkingTextStyle: {
    fontSize: 14,
    color: Colors.primary,
    fontWeight: '500',
  },
  thinkingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: Colors.primary,
  },
  thinkingDot1: {
    opacity: 0.4,
  },
  thinkingDot2: {
    opacity: 0.7,
  },
  thinkingDot3: {
    opacity: 1,
  },
});
