import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { User } from '../api/types';
import { demoLoginApi, fetchMeApi, loginApi } from '../api/client';

interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<User>;
  demoLogin: (persona: string) => Promise<User>;
  logout: () => void;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'fasalsetu_token';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem(TOKEN_KEY));
  const [loading, setLoading] = useState<boolean>(true);

  const logout = useCallback(() => {
    sessionStorage.removeItem(TOKEN_KEY);
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    async function loadUser() {
      if (!token) {
        setLoading(false);
        return;
      }
      try {
        const currentUser = await fetchMeApi(token);
        setUser(currentUser);
      } catch (err) {
        console.warn('Session token invalid or expired:', err);
        logout();
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, [token, logout]);

  const login = async (username: string, password: string): Promise<User> => {
    setLoading(true);
    try {
      const res = await loginApi(username, password);
      sessionStorage.setItem(TOKEN_KEY, res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      return res.user;
    } finally {
      setLoading(false);
    }
  };

  const demoLogin = async (persona: string): Promise<User> => {
    setLoading(true);
    try {
      const res = await demoLoginApi(persona);
      sessionStorage.setItem(TOKEN_KEY, res.access_token);
      setToken(res.access_token);
      setUser(res.user);
      return res.user;
    } finally {
      setLoading(false);
    }
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        demoLogin,
        logout,
        isAuthenticated: !!user,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
