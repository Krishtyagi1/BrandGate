"use client";
import { useState, type FormEvent } from "react";
import { ArrowRight, ShieldCheck, BookOpen, Users } from "lucide-react";
import { Brand, Notice } from "./ui";
import { api, message, send } from "@/lib/api";

export function Auth({ onLogin }: { onLogin: () => Promise<void> }) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    setBusy(true);
    setError("");
    setSuccess("");
    try {
      const data = {
        email: form.get("email"),
        password: form.get("password"),
        ...(mode === "register" ? { name: form.get("name") } : {}),
      };
      const result = await api<{ message: string }>(
        `/auth/${mode}`,
        send("POST", data),
      );
      if (mode === "login") await onLogin();
      else {
        setMode("login");
        setSuccess(result.message);
      }
    } catch (err) {
      setError(message(err));
    } finally {
      setBusy(false);
    }
  }
  function switchMode(value: typeof mode) {
    setMode(value);
    setError("");
    setSuccess("");
  }
  return (
    <div className="auth-page">
      <section className="auth-story">
        <Brand />
        <div className="auth-story-content">
          <span className="story-symbol">
            <BookOpen size={30} />
          </span>
          <h1>
            A shared standard.
            <br />A clearer voice.
          </h1>
          <p>
            Bring your brand knowledge together, so every piece of content
            starts from the same source of truth.
          </p>
          <div className="story-points">
            <span>
              <ShieldCheck size={18} /> Knowledge your team has approved
            </span>
            <span>
              <Users size={18} /> People in control of every decision
            </span>
          </div>
        </div>
        <p className="auth-footnote">Your brand, thoughtfully kept.</p>
      </section>
      <main className="auth-form-area">
        <div className="auth-card">
          <BadgeLine />
          <h2>{mode === "login" ? "Welcome back" : "Create your account"}</h2>
          <p className="muted">
            {mode === "login"
              ? "Sign in to your brand workspace."
              : "Start with your account. Set up your organisation next."}
          </p>
          {error && <Notice kind="error">{error}</Notice>}
          {success && <Notice kind="success">{success}</Notice>}
          <form onSubmit={submit} key={mode}>
            {mode === "register" && (
              <label>
                Your name
                <input
                  name="name"
                  required
                  maxLength={80}
                  autoComplete="name"
                  placeholder="Alex Morgan"
                />
              </label>
            )}
            <label>
              Email address
              <input
                name="email"
                type="email"
                required
                autoComplete="email"
                placeholder="you@company.com"
              />
            </label>
            <label>
              Password
              <input
                name="password"
                type="password"
                required
                minLength={mode === "register" ? 12 : 1}
                maxLength={128}
                autoComplete={
                  mode === "register" ? "new-password" : "current-password"
                }
              />
              {mode === "register" && (
                <small>Use at least 12 characters.</small>
              )}
            </label>
            <button className="button primary full" disabled={busy}>
              {busy
                ? "Please wait…"
                : mode === "login"
                  ? "Sign in"
                  : "Create account"}
              <ArrowRight size={16} />
            </button>
          </form>
          <div className="auth-switch">
            {mode === "login" ? (
              <>
                New here?{" "}
                <button onClick={() => switchMode("register")}>
                  Create an account
                </button>
              </>
            ) : (
              <button onClick={() => switchMode("login")}>
                Back to sign in
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
function BadgeLine() {
  return (
    <div className="auth-kicker">
      <span className="status-dot" /> Brand governance workspace
    </div>
  );
}
