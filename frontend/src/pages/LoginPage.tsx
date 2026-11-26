import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function LoginPage() {
  const { login, loginDemo } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDemo = async () => {
    setError(null);
    setSubmitting(true);
    try {
      await loginDemo();
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Demo login failed");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="mx-auto flex min-h-screen max-w-lg flex-col justify-center px-4 pt-20 pb-12">
      <div className="border border-[var(--hairline)] bg-[#efe9dd] p-6 sm:p-10">
        <p className="text-[11px] uppercase tracking-[0.14em] text-[#2c4a8f]">
          Student Access
        </p>
        <h1 className="mt-2 font-editorial text-3xl font-normal text-[#141c2b]">
          Sign in to Scholia
        </h1>
        <p className="mt-2 text-xs leading-6 text-[#4a5364]">
          Access your academic records, prediction intervals, and syllabus assessments.
        </p>

        <form onSubmit={handleSubmit} className="mt-6 space-y-4">
          <div>
            <label htmlFor="login-email" className="block text-[11px] uppercase tracking-[0.1em] text-[#4a5364]">
              Email
            </label>
            <input
              id="login-email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="student@niet.edu.in"
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs text-[#141c2b]"
            />
          </div>
          <div>
            <label htmlFor="login-password" className="block text-[11px] uppercase tracking-[0.1em] text-[#4a5364]">
              Password
            </label>
            <input
              id="login-password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full border border-[var(--hairline)] bg-[#e5ded0]/50 px-3 py-2 text-xs text-[#141c2b]"
            />
          </div>

          {error && (
            <p role="alert" className="border-l-2 border-[#141c2b] bg-[#e5ded0] px-3 py-2 text-xs">
              {error}
            </p>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="editorial-btn editorial-btn-primary w-full"
          >
            {submitting ? "Signing in..." : "Sign In"}
          </button>
        </form>

        <div className="my-6 border-t border-[var(--hairline)] pt-5">
          <p className="mb-3 text-[11px] uppercase tracking-[0.1em] text-[#767e8c]">
            Classroom / Reviewer Mode
          </p>
          <button
            type="button"
            disabled={submitting}
            onClick={handleDemo}
            className="editorial-btn w-full"
          >
            Enter Guest Demo (NIET Sem-1)
          </button>
        </div>

        <p className="text-xs text-[#4a5364]">
          New student?{" "}
          <Link to="/register" className="text-[#2c4a8f] underline underline-offset-4">
            Create an account
          </Link>
        </p>
      </div>
    </main>
  );
}
