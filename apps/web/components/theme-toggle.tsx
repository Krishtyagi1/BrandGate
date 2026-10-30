"use client";
import { useEffect, useRef, useState } from "react";
import { Moon, Sun } from "lucide-react";

type Theme = "light" | "dark";
const key = "brandgate-theme";
// Browser-only effects/events write this fallback; SSR never changes it.
let sessionPreference: Theme | null = null;

export default function ThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(null);
  const explicit = useRef(false);
  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)");
    function apply(value: Theme) {
      document.documentElement.dataset.theme = value;
      setTheme(value);
    }
    function readPreference() {
      let stored: string | null = null;
      try {
        stored = localStorage.getItem(key);
      } catch {
        /* Storage may be disabled. */
      }
      const preference =
        sessionPreference ??
        (stored === "light" || stored === "dark" ? stored : null);
      sessionPreference = preference;
      explicit.current = preference !== null;
      apply(
        preference !== null ? preference : media.matches ? "dark" : "light",
      );
    }
    readPreference();
    const systemChanged = () => {
      if (!explicit.current) apply(media.matches ? "dark" : "light");
    };
    const storageChanged = (event: StorageEvent) => {
      if (event.key === key || event.key === null) {
        sessionPreference =
          event.newValue === "light" || event.newValue === "dark"
            ? event.newValue
            : null;
        readPreference();
      }
    };
    media.addEventListener("change", systemChanged);
    window.addEventListener("storage", storageChanged);
    return () => {
      media.removeEventListener("change", systemChanged);
      window.removeEventListener("storage", storageChanged);
    };
  }, []);
  function toggle() {
    const next = theme === "dark" ? "light" : "dark";
    explicit.current = true;
    sessionPreference = next;
    document.documentElement.dataset.theme = next;
    setTheme(next);
    try {
      localStorage.setItem(key, next);
    } catch {
      /* Keep the in-memory choice across client-side navigation. */
    }
  }
  return (
    <button
      type="button"
      className="theme-toggle"
      onClick={toggle}
      aria-label={
        theme
          ? `Switch to ${theme === "dark" ? "light" : "dark"} theme`
          : "Change appearance"
      }
      title={
        theme
          ? `Switch to ${theme === "dark" ? "light" : "dark"} theme`
          : "Change appearance"
      }
    >
      {theme === "dark" ? (
        <Sun size={16} aria-hidden="true" />
      ) : (
        <Moon size={16} aria-hidden="true" />
      )}
      <span>{theme === "dark" ? "Light" : "Dark"}</span>
    </button>
  );
}
