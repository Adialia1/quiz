/**
 * User API utilities
 */
import { API_URL } from '../config/api';

export interface UserData {
  id: string;
  clerk_user_id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  created_at: string;
  last_login_at?: string;
  onboarding_completed: boolean;
  subscription_status: string;
  subscription_expires_at?: string;
  total_questions_answered: number;
  total_exams_taken: number;
  average_score?: number;
  preferred_difficulty: string;
  is_admin: boolean;
}

/**
 * Fetch current user's profile from API
 * @param getToken - Clerk's getToken function
 * @returns User profile data
 */
export const fetchUserProfile = async (
  getToken: () => Promise<string | null>
): Promise<UserData> => {
  const token = await getToken();

  if (!token) {
    throw new Error('No authentication token available');
  }

  const response = await fetch(`${API_URL}/api/users/me`, {
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error('Failed to fetch user profile');
  }

  return response.json();
};

/**
 * Delete user account and all associated data
 * @param getToken - Clerk's getToken function
 * @returns Promise that resolves when account is deleted
 */
export const deleteUserAccount = async (
  getToken: () => Promise<string | null>
): Promise<void> => {
  const token = await getToken();

  if (!token) {
    throw new Error('No authentication token available');
  }

  const response = await fetch(`${API_URL}/api/users/delete`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new Error(errorData.message || 'Failed to delete account');
  }
};
