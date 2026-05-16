import type { ID } from "@/types/api";

export type User = {
  id: ID;
  username: string;
  email: string;
  full_name: string;
  avatar: string | null;
  bio: string | null;
  country: string | null;
  institution: string | null;
  github_url: string | null;
  linkedin_url: string | null;
  created_at: string;
  updated_at: string;
};

export type AuthTokens = {
  refresh: string;
  access: string;
};

export type RegisterPayload = {
  username: string;
  email: string;
  full_name: string;
  password: string;
  password_confirm: string;
};

export type RegisterResponse = {
  user: User;
  tokens: AuthTokens;
};

export type LoginPayload = {
  username: string;
  password: string;
};

export type LoginResponse = AuthTokens;

export type RefreshTokenPayload = {
  refresh: string;
};

export type RefreshTokenResponse = {
  access: string;
};
