import React, { useState } from 'react';
import { Pressable, StyleSheet, View, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { Text } from '@gluestack-ui/themed';
import { WebView } from 'react-native-webview';
import { MaterialIcons } from '@expo/vector-icons';
import { Colors } from '../config/colors';
import { API_URL } from '../config/api';

/**
 * Terms and Conditions Screen
 * Displays the app's terms of service PDF using WebView
 *
 * The PDF is served from the backend at /api/documents/terms
 */
export const TermsAndConditionsScreen: React.FC = () => {
  const navigation = useNavigation();
  const [loading, setLoading] = useState(true);

  // Use the dedicated API endpoint that serves the PDF
  const pdfUrl = `${API_URL}/api/documents/terms`;

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable
          style={({ pressed }) => [
            styles.backButton,
            pressed && styles.buttonPressed,
          ]}
          onPress={() => navigation.goBack()}
        >
          <MaterialIcons name="arrow-forward" size={24} color={Colors.textPrimary} />
        </Pressable>
        <Text style={styles.title}>תנאי שימוש</Text>
        <View style={styles.placeholder} />
      </View>

      {/* PDF Viewer */}
      <View style={styles.pdfContainer}>
        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>טוען מסמך...</Text>
          </View>
        )}

        <WebView
          source={{ uri: pdfUrl }}
          style={styles.webview}
          onLoadStart={() => setLoading(true)}
          onLoadEnd={() => setLoading(false)}
          onError={(syntheticEvent) => {
            const { nativeEvent } = syntheticEvent;
            console.error('WebView error:', nativeEvent);
            setLoading(false);
          }}
          startInLoadingState={true}
          scalesPageToFit={true}
          originWhitelist={['*']}
        />
      </View>
    </SafeAreaView>
  );
};

/**
 * Styles
 */
const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.white,
  },
  header: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: Colors.gray[200],
  },
  backButton: {
    padding: 8,
  },
  buttonPressed: {
    opacity: 0.6,
  },
  title: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  placeholder: {
    width: 40,
  },
  pdfContainer: {
    flex: 1,
    backgroundColor: Colors.gray[100],
  },
  webview: {
    flex: 1,
    backgroundColor: Colors.white,
  },
  loadingContainer: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: Colors.white,
    zIndex: 10,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: Colors.gray[600],
    textAlign: 'center',
  },
});
