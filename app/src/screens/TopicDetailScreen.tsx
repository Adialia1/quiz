import React, { useState, useEffect } from 'react';
import { StyleSheet, SafeAreaView, StatusBar, View, Text, Pressable, TextInput, ActivityIndicator, FlatList } from 'react-native';
import { Image } from 'expo-image';
import { useNavigation, useRoute } from '@react-navigation/native';
// Temporarily using FlatList instead of FlashList to debug AutoLayoutView error
// import { FlashList } from '@shopify/flash-list';
import { Colors } from '../config/colors';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

interface Concept {
  id: string;
  topic: string;
  title: string;
  explanation: string;
  example?: string;
  key_points: string[];
}

/**
 * Topic Detail Screen - Shows list of concepts with Start Game button
 */
export const TopicDetailScreen: React.FC = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const { topic } = route.params as { topic: string };

  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [filteredConcepts, setFilteredConcepts] = useState<Concept[]>([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadConcepts();
  }, [topic]);

  useEffect(() => {
    // Filter concepts based on search query
    if (searchQuery.trim() === '') {
      setFilteredConcepts(concepts);
    } else {
      const filtered = concepts.filter(concept =>
        concept.title.includes(searchQuery) ||
        concept.explanation.includes(searchQuery)
      );
      setFilteredConcepts(filtered);
    }
  }, [searchQuery, concepts]);

  const loadConcepts = async () => {
    try {
      const response = await fetch(`${API_URL}/api/concepts/topics/${encodeURIComponent(topic)}`);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      console.log('Loaded concepts:', data.length, 'items');
      setConcepts(data);
      setFilteredConcepts(data);
    } catch (error) {
      console.error('Error loading concepts:', error);
      // Show error to user
      setConcepts([]);
      setFilteredConcepts([]);
    } finally {
      setLoading(false);
    }
  };

  const handleStartGame = () => {
    navigation.navigate('FlashcardStudy', { topic, mode: 'all' });
  };

  const handleConceptPress = (concept: Concept) => {
    navigation.navigate('FlashcardStudy', {
      topic,
      mode: 'single',
      conceptId: concept.id
    });
  };

  const renderConceptItem = ({ item }: { item: Concept }) => (
    <Pressable
      onPress={() => handleConceptPress(item)}
      style={styles.conceptItem}
    >
      <View style={styles.conceptContent}>
        <Text style={styles.conceptTitle}>{item.title}</Text>
        <Text style={styles.conceptPreview} numberOfLines={2}>
          {item.explanation}
        </Text>
      </View>
      <Text style={styles.arrowIcon}>←</Text>
    </Pressable>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>טוען מושגים...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          {/* Back Button */}
          <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
            <Text style={styles.backIcon}>→</Text>
          </Pressable>

          {/* Title */}
          <Text style={styles.headerTitle}>{topic}</Text>

          {/* Logo */}
          <Image
            source={require('../../assets/icon.png')}
            style={styles.logo}
            contentFit="contain"
          />
        </View>
      </View>

      {/* Start Game Button */}
      <View style={styles.startButtonContainer}>
        <Pressable onPress={handleStartGame} style={styles.startButton}>
          <Text style={styles.startButtonIcon}>🎮</Text>
          <Text style={styles.startButtonText}>התחל משחק</Text>
        </Pressable>
      </View>

      {/* Search Bar */}
      <View style={styles.searchContainer}>
        <TextInput
          style={styles.searchInput}
          placeholder="חיפוש מושג..."
          placeholderTextColor={Colors.textSecondary}
          value={searchQuery}
          onChangeText={setSearchQuery}
        />
        <Text style={styles.searchIcon}>🔍</Text>
      </View>

      {/* Concepts List */}
      <View style={styles.listContainer}>
        {filteredConcepts.length === 0 ? (
          <View style={styles.emptyContainer}>
            <Text style={styles.emptyText}>לא נמצאו תוצאות</Text>
          </View>
        ) : (
          <FlatList
            data={filteredConcepts}
            renderItem={renderConceptItem}
            keyExtractor={(item) => item.id}
            showsVerticalScrollIndicator={false}
            ItemSeparatorComponent={() => <View style={styles.separator} />}
          />
        )}
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 16,
    backgroundColor: Colors.background,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backIcon: {
    fontSize: 28,
    color: Colors.textPrimary,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.textPrimary,
  },
  logo: {
    width: 60,
    height: 40,
  },
  startButtonContainer: {
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  startButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 25,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  startButtonIcon: {
    fontSize: 24,
  },
  startButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.white,
  },
  searchContainer: {
    paddingHorizontal: 24,
    paddingBottom: 16,
    flexDirection: 'row',
    alignItems: 'center',
  },
  searchInput: {
    flex: 1,
    backgroundColor: Colors.white,
    paddingVertical: 12,
    paddingHorizontal: 40,
    paddingRight: 16,
    borderRadius: 25,
    fontSize: 16,
    textAlign: 'right',
    borderWidth: 1,
    borderColor: Colors.secondaryLight,
  },
  searchIcon: {
    position: 'absolute',
    left: 40,
    fontSize: 20,
  },
  listContainer: {
    flex: 1,
    paddingHorizontal: 24,
  },
  conceptItem: {
    backgroundColor: Colors.white,
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  conceptContent: {
    flex: 1,
    marginRight: 12,
  },
  conceptTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: 4,
    textAlign: 'right',
  },
  conceptPreview: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'right',
    lineHeight: 20,
  },
  arrowIcon: {
    fontSize: 20,
    color: Colors.textSecondary,
  },
  separator: {
    height: 12,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 40,
  },
  emptyText: {
    fontSize: 16,
    color: Colors.textSecondary,
  },
});
