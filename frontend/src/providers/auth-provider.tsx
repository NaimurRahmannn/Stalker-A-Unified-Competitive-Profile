"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import {
  getCurrentUser,
  loginUser,
  registerUser,
} from "@/features/auth/api";
import type {
  LoginFormValues,
  RegisterFormValues,
} from "@/features/auth/schemas";
import type { User } from "@/features/auth/types";
import { clearTokens, hasTokens } from "@/lib/token";

export type AuthContextValue = {
  user: User | null;
  isLoading: boolean;
  login: (values: LoginFormValues) => Promise<User>;
  register: (values: RegisterFormValues) => Promise<User>;
  logout: () => void;
};

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const authVersionRef = useRef(0);

  // Hydrate the current user from an existing token on first mount.
  useEffect(() => {
    let cancelled = false;
    const authVersion = authVersionRef.current;

    void (async () => {
      try {
        if (hasTokens()) {
          const currentUser = await getCurrentUser();
          if (!cancelled && authVersionRef.current === authVersion) {
            setUser(currentUser);
          }
        }
      } catch {
        // Token is missing/expired/invalid — treat as logged out.
        if (!cancelled && authVersionRef.current === authVersion) {
          clearTokens();
          setUser(null);
        }
      } finally {
        if (!cancelled && authVersionRef.current === authVersion) {
          setIsLoading(false);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, []);

  const login = useCallback(async (values: LoginFormValues) => {
    authVersionRef.current += 1;
    setIsLoading(true);

    try {
      await loginUser(values);
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      return currentUser;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const register = useCallback(async (values: RegisterFormValues) => {
    authVersionRef.current += 1;
    setIsLoading(true);

    try {
      const { user: newUser } = await registerUser(values);
      setUser(newUser);
      return newUser;
    } finally {
      setIsLoading(false);
    }
  }, []);

  const logout = useCallback(() => {
    authVersionRef.current += 1;
    clearTokens();
    setUser(null);
    setIsLoading(false);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({ user, isLoading, login, register, logout }),
    [user, isLoading, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}
