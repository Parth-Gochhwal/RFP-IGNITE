import { ChangeEvent } from "react";
import { useTheme } from "../theme/ThemeContext";

export function Header() {
  const { theme, setTheme } = useTheme();

  // Handle theme change via centralized provider
  const handleThemeChange = (e: ChangeEvent<HTMLSelectElement>) => {
    const value = e.target.value as typeof theme;
    setTheme(value);
  };

  return (
    <header className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 shadow-sm transition-colors">
      <div className="max-w-7xl mx-auto px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-800 dark:text-white">
              RFP Ignite – Agentic RFP Response Console
            </h1>
            <p className="text-sm text-slate-600 dark:text-slate-400 mt-1">
              Sales · Technical · Pricing – Multi-agent AI Orchestration
            </p>
          </div>

          <div className="flex items-center gap-4">
            
            {/* Theme Switcher */}
            <select
              value={theme}
              onChange={handleThemeChange}
              className="px-3 py-1.5 rounded-md text-sm bg-slate-100 dark:bg-slate-800 
                         text-slate-700 dark:text-slate-300 border border-slate-300 dark:border-slate-700"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
              <option value="system">System</option>
            </select>

            <div className="text-xs text-slate-500 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-full">
              Client OEM
            </div>
            <div className="text-xs text-slate-500 dark:text-slate-300 bg-slate-100 dark:bg-slate-800 px-3 py-1.5 rounded-full">
              EY Hackathon
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}
