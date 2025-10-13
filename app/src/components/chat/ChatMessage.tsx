/**
 * ChatMessage Component
 * Displays a single chat message (user or assistant)
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Colors } from '../../config/colors';

interface ChatMessageProps {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  sources?: string[];
}

/**
 * Chat Message Component
 */
export const ChatMessage: React.FC<ChatMessageProps> = ({
  role,
  content,
  timestamp,
  sources,
}) => {
  const isUser = role === 'user';

  // Clean markdown formatting for better mobile display
  const cleanContent = (text: string): string => {
    return text
      // Remove markdown headers (##, ###, etc)
      .replace(/^#{1,6}\s+/gm, '')
      // Remove bold/italic markers
      .replace(/\*\*\*/g, '')
      .replace(/\*\*/g, '')
      .replace(/\*/g, '')
      // Remove inline code markers
      .replace(/`([^`]+)`/g, '$1')
      // Clean up multiple newlines
      .replace(/\n{3,}/g, '\n\n')
      // Remove horizontal rules
      .replace(/^---+$/gm, '')
      .trim();
  };

  return (
    <View style={[styles.container, isUser ? styles.userContainer : styles.assistantContainer]}>
      {/* Message Bubble */}
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        <Text style={[styles.content, isUser ? styles.userContent : styles.assistantContent]}>
          {cleanContent(content)}
        </Text>

        {/* Sources (if available) */}
        {sources && sources.length > 0 && (
          <View style={styles.sourcesContainer}>
            <Text style={styles.sourcesTitle}>מקורות:</Text>
            {sources.map((source, index) => (
              <Text key={index} style={styles.sourceItem}>
                • {source}
              </Text>
            ))}
          </View>
        )}
      </View>

      {/* Timestamp (optional) */}
      {timestamp && (
        <Text style={[styles.timestamp, isUser ? styles.userTimestamp : styles.assistantTimestamp]}>
          {new Date(timestamp).toLocaleTimeString('he-IL', {
            hour: '2-digit',
            minute: '2-digit',
          })}
        </Text>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    marginVertical: 8,
    paddingHorizontal: 16,
  },
  userContainer: {
    alignItems: 'flex-end',
  },
  assistantContainer: {
    alignItems: 'flex-start',
  },
  bubble: {
    maxWidth: '80%',
    borderRadius: 16,
    padding: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 1,
  },
  userBubble: {
    backgroundColor: Colors.primary,
  },
  assistantBubble: {
    backgroundColor: Colors.white,
    borderWidth: 1,
    borderColor: Colors.secondaryLight,
  },
  content: {
    fontSize: 16,
    lineHeight: 24,
    textAlign: 'right',
  },
  userContent: {
    color: Colors.white,
  },
  assistantContent: {
    color: Colors.textPrimary,
  },
  sourcesContainer: {
    marginTop: 12,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: Colors.lightGray,
  },
  sourcesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textSecondary,
    marginBottom: 6,
    textAlign: 'right',
  },
  sourceItem: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginBottom: 4,
    textAlign: 'right',
  },
  timestamp: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 4,
  },
  userTimestamp: {
    textAlign: 'right',
  },
  assistantTimestamp: {
    textAlign: 'left',
  },
});
