import React, { createContext, useContext, useEffect, useState } from "react";
import { apiRequest, getStoredToken, setStoredToken } from "../lib/api";

export interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  is_demo: boolean;
}

export interface StudentProfile {
  id: string;
  user_id: string;
  education_level: string;
  institution: string;
  programme: string;
  academic_period: string;
  grading_scheme: string;
  demo_identifier: string | null;
  weekly_study_hours: number | null;
}

interface AuthResponse {
  access_token: string;
  user: User;
  profile: StudentProfile | null;
}

interface AuthContextValue {
  user: User | null;
  profile: StudentProfile | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: {
    name: string;
    email: string;
    password: string;
    education_level?: string;
    institution?: string;
    programme?: string;
    academic_period?: string;
  }) => Promise<void>;
  loginDemo: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<StudentProfile | null>(null);
  const [loading, setLoading] = useState(true);

  const refreshProfile = async () => {
    const token = getStoredToken();
    if (!token) {
      setUser(null);
      setProfile(null);
      setLoading(false);
      return;
    }
    try {
      const data = await apiRequest<{ user: User; profile: StudentProfile }>(
        "/students/me"
      );
      setUser(data.user);
      setProfile(data.profile);
    } catch {
      setStoredToken(null);
      setUser(null);
      setProfile(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refreshProfile();
  }, []);

  const login = async (email: string, password: string) => {
    const data = await apiRequest<AuthResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    });
    setStoredToken(data.access_token);
    setUser(data.user);
    setProfile(data.profile);
  };

  const register = async (payload: {
    name: string;
    email: string;
    password: string;
    education_level?: string;
    institution?: string;
    programme?: string;
    academic_period?: string;
  }) => {
    const data = await apiRequest<AuthResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify(payload),
    });
    setStoredToken(data.access_token);
    setUser(data.user);
    setProfile(data.profile);
  };

  const loginDemo = async () => {
    const data = await apiRequest<AuthResponse>("/auth/demo-login", {
      method: "POST",
      body: JSON.stringify({
        name: "NIET Demo Student",
        demo_identifier: "DEMO-CSDS-01",
      }),
    });
    setStoredToken(data.access_token);
    setUser(data.user);
    setProfile(data.profile);
  };

  const logout = () => {
    setStoredToken(null);
    setUser(null);
    setProfile(null);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        profile,
        loading,
        login,
        register,
        loginDemo,
        refreshProfile,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
