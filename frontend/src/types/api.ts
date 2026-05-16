export type ID = number | string;

export type ApiError = {
  detail?: string;
  message?: string;
  errors?: Record<string, string | string[]>;
  status?: number;
};

export type PaginatedResponse<T> = {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
};
