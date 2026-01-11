const USER_ID_KEY = "impasse_user_id";

/**
 * Generate a UUID v4
 */
function generateUUID(): string {
  return "xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx".replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === "x" ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

/**
 * Get the current user's ID from localStorage.
 * If no ID exists, generates a new one and stores it.
 *
 * This is a temporary solution until proper authentication is implemented.
 * When auth is added, this should return the authenticated user's ID.
 */
export function getUserId(): string {
  if (typeof window === "undefined") {
    // Server-side rendering - return empty string
    return "";
  }

  let userId = localStorage.getItem(USER_ID_KEY);

  if (!userId) {
    userId = generateUUID();
    localStorage.setItem(USER_ID_KEY, userId);
  }

  return userId;
}

/**
 * Clear the stored user ID (useful for testing or logout)
 */
export function clearUserId(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(USER_ID_KEY);
  }
}
