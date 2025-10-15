/**
 * Greeting utilities for personalized messages
 */

/**
 * Get time-based greeting in Hebrew
 * @param firstName - User's first name (optional)
 * @returns Time-appropriate greeting
 */
export const getTimeBasedGreeting = (firstName?: string): string => {
  const currentHour = new Date().getHours();

  // Determine greeting based on time of day
  let greeting: string;

  if (currentHour >= 6 && currentHour < 12) {
    // Morning: 6:00 - 11:59
    greeting = 'בוקר טוב';
  } else if (currentHour >= 12 && currentHour < 18) {
    // Afternoon: 12:00 - 17:59
    greeting = 'צהריים טובים';
  } else {
    // Evening/Night: 18:00 - 5:59
    greeting = 'ערב טוב';
  }

  // Add first name if provided
  if (firstName) {
    return `${greeting} ${firstName}`;
  }

  return greeting;
};

/**
 * Get time-based greeting with full name
 * @param firstName - User's first name (optional)
 * @param lastName - User's last name (optional)
 * @returns Time-appropriate greeting with full name if available
 */
export const getTimeBasedGreetingWithFullName = (
  firstName?: string,
  lastName?: string
): string => {
  const currentHour = new Date().getHours();

  // Determine greeting based on time of day
  let greeting: string;

  if (currentHour >= 6 && currentHour < 12) {
    greeting = 'בוקר טוב';
  } else if (currentHour >= 12 && currentHour < 18) {
    greeting = 'צהריים טובים';
  } else {
    greeting = 'ערב טוב';
  }

  // Add full name if available
  if (firstName && lastName) {
    return `${greeting} ${firstName} ${lastName}`;
  } else if (firstName) {
    return `${greeting} ${firstName}`;
  }

  return greeting;
};
