/**
 * Chat History Screen
 * Shows list of all chat conversations
 */
import React, { useEffect, useState } from 'react';
import {
  StyleSheet,
  SafeAreaView,
  View,
  Text,
  Pressable,
  ScrollView,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';
import { aiChatApi, ChatConversation } from '../utils/aiChatApi';
import { useChatStore } from '../stores/chatStore';

/**
 * Conversation Card Component
 */
interface ConversationCardProps {
  conversation: ChatConversation;
  onPress: () => void;
  onDelete: () => void;
}

const ConversationCard: React.FC<ConversationCardProps> = ({
  conversation,
  onPress,
  onDelete,
}) => {
  return (
    <Pressable onPress={onPress} style={styles.conversationCard}>
      <View style={styles.conversationContent}>
        <Text style={styles.conversationTitle} numberOfLines={1}>
          {conversation.title}
        </Text>
        {conversation.last_message && (
          <Text style={styles.conversationLastMessage} numberOfLines={2}>
            {conversation.last_message}
          </Text>
        )}
        <View style={styles.conversationMeta}>
          <Text style={styles.conversationMetaText}>
            {conversation.message_count} הודעות
          </Text>
          <Text style={styles.conversationMetaText}>•</Text>
          <Text style={styles.conversationMetaText}>
            {new Date(conversation.updated_at).toLocaleDateString('he-IL')}
          </Text>
        </View>
      </View>

      {/* Delete Button */}
      <Pressable
        onPress={(e) => {
          e.stopPropagation();
          onDelete();
        }}
        style={styles.deleteButton}
      >
        <Text style={styles.deleteButtonText}>🗑️</Text>
      </Pressable>
    </Pressable>
  );
};

/**
 * Chat History Screen Component
 */
export const ChatHistoryScreen: React.FC = () => {
  const navigation = useNavigation();
  const { getToken } = useAuth();
  const {
    conversations,
    setConversations,
    deleteConversationFromStore,
    isLoadingConversations,
    setLoadingConversations,
  } = useChatStore();

  const [refreshing, setRefreshing] = useState(false);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      setLoadingConversations(true);
      const convs = await aiChatApi.getConversations(getToken);
      setConversations(convs);
    } catch (error: any) {
      console.error('Error loading conversations:', error);
      Alert.alert('שגיאה', 'לא הצלחנו לטעון את השיחות. נסה שוב.');
    } finally {
      setLoadingConversations(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    setRefreshing(true);
    loadConversations();
  };

  const handleConversationPress = (conversation: ChatConversation) => {
    navigation.navigate('AIMentorChat', { conversationId: conversation.id });
  };

  const handleDeleteConversation = async (conversationId: string) => {
    Alert.alert(
      'מחיקת שיחה',
      'האם אתה בטוח שברצונך למחוק את השיחה? פעולה זו לא ניתנת לביטול.',
      [
        { text: 'ביטול', style: 'cancel' },
        {
          text: 'מחק',
          style: 'destructive',
          onPress: async () => {
            try {
              await aiChatApi.deleteConversation(conversationId, getToken);
              deleteConversationFromStore(conversationId);
              Alert.alert('הצלחה', 'השיחה נמחקה בהצלחה');
            } catch (error: any) {
              console.error('Error deleting conversation:', error);
              Alert.alert('שגיאה', 'לא הצלחנו למחוק את השיחה. נסה שוב.');
            }
          },
        },
      ]
    );
  };

  const handleNewChat = () => {
    navigation.navigate('AIMentorChat', { conversationId: null });
  };

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backButtonText}>←</Text>
        </Pressable>
        <Text style={styles.headerTitle}>שיחות עם מרצה AI</Text>
        <View style={styles.headerSpacer} />
      </View>

      {/* New Chat Button */}
      <Pressable onPress={handleNewChat} style={styles.newChatButton}>
        <Text style={styles.newChatButtonText}>+ שיחה חדשה</Text>
      </Pressable>

      {/* Loading State */}
      {isLoadingConversations && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>טוען שיחות...</Text>
        </View>
      ) : conversations.length === 0 ? (
        /* Empty State */
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>💬</Text>
          <Text style={styles.emptyTitle}>אין שיחות עדיין</Text>
          <Text style={styles.emptySubtitle}>
            התחל שיחה חדשה עם מרצה AI לשאול שאלות על החומר
          </Text>
          <Pressable onPress={handleNewChat} style={styles.emptyButton}>
            <Text style={styles.emptyButtonText}>התחל שיחה</Text>
          </Pressable>
        </View>
      ) : (
        /* Conversations List */
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          refreshing={refreshing}
          onRefresh={handleRefresh}
        >
          {conversations.map((conversation) => (
            <ConversationCard
              key={conversation.id}
              conversation={conversation}
              onPress={() => handleConversationPress(conversation)}
              onDelete={() => handleDeleteConversation(conversation.id)}
            />
          ))}
        </ScrollView>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
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
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  headerSpacer: {
    width: 40,
  },
  newChatButton: {
    margin: 16,
    backgroundColor: Colors.primary,
    borderRadius: 12,
    paddingVertical: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  newChatButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.white,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 16,
    paddingBottom: 16,
  },
  conversationCard: {
    flexDirection: 'row',
    backgroundColor: Colors.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 1,
  },
  conversationContent: {
    flex: 1,
  },
  conversationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: 6,
    textAlign: 'right',
  },
  conversationLastMessage: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 8,
    textAlign: 'right',
  },
  conversationMeta: {
    flexDirection: 'row',
    gap: 8,
    justifyContent: 'flex-end',
  },
  conversationMetaText: {
    fontSize: 12,
    color: Colors.textSecondary,
  },
  deleteButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  deleteButtonText: {
    fontSize: 20,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    color: Colors.textSecondary,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: Colors.textPrimary,
    marginBottom: 8,
    textAlign: 'center',
  },
  emptySubtitle: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 24,
  },
  emptyButton: {
    backgroundColor: Colors.primary,
    borderRadius: 12,
    paddingHorizontal: 32,
    paddingVertical: 16,
  },
  emptyButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.white,
  },
});
