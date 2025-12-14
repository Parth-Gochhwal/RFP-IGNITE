// frontend/src/components/ThemeSwitcher.tsx
import { useState } from "react";
import { useTheme, ThemeMode } from "../theme/ThemeContext";

const OPTIONS: { key: ThemeMode; label: string; emoji: string }[] = [
  { key: "light", label: "Light", emoji: "☀️" },
  { key: "dark", label: "Dark", emoji: "🌙" },
  { key: "system", label: "System", emoji: "💻" },
];

export default function ThemeSwitcher(): JSX.Element {
  const { theme, setTheme } = useTheme();
  const [open, setOpen] = useState(false);

  const handleSelect = (key: ThemeMode) => {
    setTheme(key);
    setOpen(false);
  };

  return (
    <div className="relative inline-block text-left">
      <button
        onClick={() => setOpen((s) => !s)}
        className="inline-flex items-center gap-2 px-3 py-2 rounded-md bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 shadow-sm text-sm"
        aria-haspopup="true"
        aria-expanded={open}
        type="button"
      >
        <span className="text-sm">{OPTIONS.find((o) => o.key === theme)?.emoji}</span>
        <span className="hidden sm:inline text-xs text-gray-700 dark:text-gray-200">
          {OPTIONS.find((o) => o.key === theme)?.label}
        </span>
        <svg className="w-3 h-3 ml-1 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {open && (
        <div
          className="absolute right-0 mt-2 w-40 bg-white dark:bg-slate-800 border border-gray-200 dark:border-slate-700 rounded-md shadow-lg z-50"
          role="menu"
        >
          <div className="py-1">
            {OPTIONS.map((opt) => (
              <button
                key={opt.key}
                onClick={() => handleSelect(opt.key)}
                className={`w-full text-left px-3 py-2 text-sm flex items-center gap-2 ${
                  opt.key === theme ? "bg-gray-100 dark:bg-slate-700" : "hover:bg-gray-50 dark:hover:bg-slate-700"
                }`}
                role="menuitem"
                type="button"
              >
                <span className="text-sm">{opt.emoji}</span>
                <span className="flex-1">{opt.label}</span>
                {opt.key === theme && <span className="text-xs text-gray-500">Selected</span>}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
