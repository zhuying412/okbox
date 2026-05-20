/**
 * Shared TypeScript type definitions.
 */

/** API response wrapper */
export interface ApiResponse<T = unknown> {
  data: T;
  message?: string;
}

/** Paginated response */
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
}

/** User info */
export interface User {
  id: string;
  username: string;
  role: "admin" | "analyst" | "doctor";
  display_name: string;
}
