import React from "react";
import { Sun, Moon } from "lucide-react";
import { useTheme } from "../contexts/ThemeContext";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === "dark";

  return (
    <button
      onClick={toggleTheme}
      aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"}
      title={isDark ? "Switch to light mode" : "Switch to dark mode"}
      className="flex items-center gap-2 px-3 py-2 rounded-xl border
                 bg-white border-gray-200 text-gray-700 hover:bg-gray-100
                 dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300 dark:hover:bg-slate-700
                 transition-colors"
    >
      {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
      <span className="text-sm hidden sm:inline">{isDark ? "Light" : "Dark"}</span>
    </button>
  );
}