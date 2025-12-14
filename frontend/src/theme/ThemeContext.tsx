// frontend/src/theme/ThemeContext.tsx
import { createContext, useContext, useEffect, useState, ReactNode } from "react";

export type ThemeMode = "light" | "dark" | "system";

type ThemeContextValue = {
  theme: ThemeMode;
  setTheme: (t: ThemeMode) => void;
  isDark: boolean;
};

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined);

const STORAGE_KEY = "rfp_ignite_theme";

function getInitialTheme(): ThemeMode {
  try {
    if (typeof window !== "undefined" && typeof window.localStorage !== "undefined") {
      const raw = window.localStorage.getItem(STORAGE_KEY);
      if (raw === "light" || raw === "dark" || raw === "system") return raw;
    }
  } catch (e) {
    // ignore localStorage errors
  }
  return "system";
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeRaw] = useState<ThemeMode>(getInitialTheme());
  const [prefersDark, setPrefersDark] = useState<boolean>(() => {
    if (typeof window === "undefined" || !("matchMedia" in window)) return false;
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  // wrapper that persists value and updates state
  const setTheme = (t: ThemeMode) => {
    try {
      localStorage.setItem(STORAGE_KEY, t);
    } catch (e) {
      // ignore
    }
    setThemeRaw(t);
  };

  // Listen for system preference changes
  useEffect(() => {
    if (typeof window === "undefined" || !("matchMedia" in window)) return;

    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    // handler receives MediaQueryListEvent in modern browsers
    const handler = (ev: MediaQueryListEvent) => setPrefersDark(ev.matches);

    // Prefer modern addEventListener if available
    if (typeof mq.addEventListener === "function") {
      mq.addEventListener("change", handler);
    } else if (typeof (mq as any).addListener === "function") {
      // older API fallback
      (mq as any).addListener(handler);
    }

    return () => {
      if (typeof mq.removeEventListener === "function") {
        mq.removeEventListener("change", handler);
      } else if (typeof (mq as any).removeListener === "function") {
        (mq as any).removeListener(handler);
      }
    };
  }, []);

  // Apply effective theme to <html> as .dark for Tailwind
  useEffect(() => {
    if (typeof document === "undefined") return;
    const root = document.documentElement;
    const effectiveDark = theme === "dark" || (theme === "system" && prefersDark);

    if (effectiveDark) root.classList.add("dark");
    else root.classList.remove("dark");

    root.setAttribute("data-theme", theme);
  }, [theme, prefersDark]);

  const value: ThemeContextValue = {
    theme,
    setTheme,
    isDark: theme === "dark" || (theme === "system" && prefersDark),
  };

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() {
  const ctx = useContext(ThemeContext);
  if (!ctx) throw new Error("useTheme must be used inside ThemeProvider");
  return ctx;
}
