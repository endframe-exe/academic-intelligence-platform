import React from "react";
import { Navigate } from "react-router-dom";
import { MagnificationDock } from "./ui/MagnificationDock";
import { useAuth } from "../context/AuthContext";

export function WorkspaceLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center pt-16 text-xs uppercase tracking-[0.12em] text-[#4a5364]">
        Loading academic workspace...
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="min-h-screen bg-[#efe9dd] pt-[58px] pb-28">
      <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6">{children}</div>
      <MagnificationDock />
    </div>
  );
}
