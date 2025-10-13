/**
 * ChatInput Component
 * Input field for sending messages in chat
 */
import React, { useState } from 'react';
import {
  View,
  TextInput,
  Pressable,
  StyleSheet,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Colors } from '../../config/colors';

interface ChatInputProps {
  onSend: (message: string) => void;
  isSending?: boolean;
  placeholder?: string;
}

/**
 * Chat Input Component
 */
export const ChatInput: React.FC<ChatInputProps> = ({
  onSend,
  isSending = false,
  placeholder = 'שאל שאלה...',
}) => {
  const [message, setMessage] = useState('');

  const handleSend = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isSending) {
      onSend(trimmedMessage);
      setMessage('');
    }
  };

  const canSend = message.trim().length > 0 && !isSending;

  return (
    <KeyboardAvoidingView
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <View style={styles.container}>
        <View style={styles.inputContainer}>
          {/* Text Input */}
          <TextInput
            style={styles.input}
            value={message}
            onChangeText={setMessage}
            placeholder={placeholder}
            placeholderTextColor={Colors.textSecondary}
            multiline
            maxLength={5000}
            editable={!isSending}
            textAlign="right"
            onSubmitEditing={handleSend}
          />

          {/* Send Button */}
          <Pressable
            onPress={handleSend}
            disabled={!canSend}
            style={[styles.sendButton, !canSend && styles.sendButtonDisabled]}
          >
            {isSending ? (
              <ActivityIndicator size="small" color={Colors.white} />
            ) : (
              <View style={styles.sendIcon}>
                <View style={styles.sendArrow} />
              </View>
            )}
          </Pressable>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    backgroundColor: Colors.background,
    borderTopWidth: 1,
    borderTopColor: Colors.lightGray,
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    gap: 8,
  },
  input: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: 24,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    maxHeight: 120,
    borderWidth: 1,
    borderColor: Colors.lightGray,
    textAlignVertical: 'center',
  },
  sendButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  sendButtonDisabled: {
    backgroundColor: Colors.lightGray,
  },
  sendIcon: {
    width: 24,
    height: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendArrow: {
    width: 0,
    height: 0,
    borderLeftWidth: 8,
    borderRightWidth: 8,
    borderBottomWidth: 12,
    borderLeftColor: 'transparent',
    borderRightColor: 'transparent',
    borderBottomColor: Colors.white,
    transform: [{ rotate: '90deg' }],
  },
});
