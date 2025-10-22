/**
 * Hook to automatically refresh Clerk tokens
 */
import { useEffect, useRef } from 'react';
import { useAuth } from '@clerk/clerk-expo';

export const useTokenRefresh = () => {
  const { getToken, isLoaded } = useAuth();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!isLoaded) return;

    // Refresh token every 45 minutes (tokens usually expire after 1 hour)
    const refreshToken = async () => {
      try {
        console.log('Refreshing authentication token...');
        await getToken({ skipCache: true });
        console.log('Token refreshed successfully');
      } catch (error) {
        console.error('Failed to refresh token:', error);
      }
    };

    // Initial refresh
    refreshToken();

    // Set up interval for periodic refresh
    intervalRef.current = setInterval(refreshToken, 45 * 60 * 1000); // 45 minutes

    // Cleanup
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isLoaded, getToken]);

  // Return a function to manually refresh token
  const refreshTokenManually = async () => {
    try {
      const token = await getToken({ skipCache: true });
      return token;
    } catch (error) {
      console.error('Manual token refresh failed:', error);
      throw error;
    }
  };

  return { refreshTokenManually };
};