/**
 * StudyAssistant.jsx
 * ──────────────────
 * A floating AI study assistant chat panel for DigitalLogicHub.
 *
 * Usage:
 *   <StudyAssistant user={user} />
 *
 * Features:
 *   - Floating button (bottom-right) that expands into a chat panel
 *   - Sends conversation history (last 10 messages) for context
 *   - Shows typing indicator while waiting for a reply
 *   - Auto-scrolls to latest message
 *   - Keyboard shortcut: Enter to send, Shift+Enter for newline
 *   - Graceful error state with retry option
 *   - Respects dark mode via Tailwind dark: classes
 */

import React, { useState, useRef, useEffect, useCallback } from "react";
import api from "../services/api";
import {
  MessageCircle, X, Send, Loader2,
  Bot, User, AlertCircle, Minimize2,
} from "lucide-react";

const WELCOME_MESSAGE = {
  role: "assistant",
  content:
    "Hi! I'm your digital logic study assistant. I can help you with K-Maps, " +
    "number conversions, logic gates, and Boolean algebra. What would you like to explore?",
};

function TypingIndicator() {
  return (
    <div className="flex items-end gap-2 mb-3">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500
                      flex items-center justify-center flex-shrink-0">
        <Bot className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="bg-white dark:bg-slate-700 border border-gray-200 dark:border-slate-600
                      rounded-2xl rounded-bl-sm px-4 py-3 shadow-sm">
        <div className="flex gap-1 items-center h-4">
          {[0, 1, 2].map((i) => (
            <div
              key={i}
              className="w-1.5 h-1.5 rounded-full bg-gray-400 dark:bg-slate-400 animate-bounce"
              style={{ animationDelay: `${i * 150}ms` }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Message({ msg }) {
  const isUser = msg.role === "user";
  const isError = msg.role === "error";

  if (isUser) {
    return (
      <div className="flex items-end justify-end gap-2 mb-3">
        <div className="max-w-[78%] bg-gradient-to-br from-cyan-500 to-blue-500
                        text-white rounded-2xl rounded-br-sm px-4 py-2.5 shadow-sm">
          <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
        </div>
        <div className="w-7 h-7 rounded-full bg-gray-200 dark:bg-slate-600
                        flex items-center justify-center flex-shrink-0">
          <User className="w-3.5 h-3.5 text-gray-600 dark:text-slate-300" />
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="flex items-start gap-2 mb-3">
        <div className="w-7 h-7 rounded-full bg-red-100 dark:bg-red-500/20
                        flex items-center justify-center flex-shrink-0 mt-0.5">
          <AlertCircle className="w-3.5 h-3.5 text-red-500 dark:text-red-400" />
        </div>
        <div className="max-w-[78%] bg-red-50 dark:bg-red-500/10
                        border border-red-200 dark:border-red-500/20
                        rounded-2xl rounded-tl-sm px-4 py-2.5">
          <p className="text-red-600 dark:text-red-400 text-sm leading-relaxed">{msg.content}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex items-end gap-2 mb-3">
      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500
                      flex items-center justify-center flex-shrink-0">
        <Bot className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="max-w-[78%] bg-white dark:bg-slate-700
                      border border-gray-200 dark:border-slate-600
                      rounded-2xl rounded-bl-sm px-4 py-2.5 shadow-sm">
        <p className="text-gray-800 dark:text-slate-100 text-sm leading-relaxed whitespace-pre-wrap">
          {msg.content}
        </p>
      </div>
    </div>
  );
}

export default function StudyAssistant({ user }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([WELCOME_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  // Focus input when panel opens
  useEffect(() => {
    if (open) setTimeout(() => inputRef.current?.focus(), 100);
  }, [open]);

  const sendMessage = useCallback(async () => {
    const text = input.trim();
    if (!text || loading) return;

    const userMsg = { role: "user", content: text };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      // Send history excluding the welcome message and error messages,
      // keeping only real user/assistant exchanges (last 10)
      const history = messages
        .filter((m) => m.role === "user" || m.role === "assistant")
        .slice(-10)
        .map((m) => ({ role: m.role, content: m.content }));

      const res = await api.post(`/chat/${user.id}`, {
        message: text,
        history,
      });

      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.data.reply },
      ]);
    } catch (e) {
      const detail = e.response?.data?.detail;
      setMessages((prev) => [
        ...prev,
        {
          role: "error",
          content: detail || "Something went wrong. Please try again.",
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, messages, user.id]);

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => setMessages([WELCOME_MESSAGE]);

  return (
    <>
      {/* ── Floating toggle button ────────────────────────────────────────── */}
      <button
        onClick={() => setOpen((o) => !o)}
        aria-label="Open study assistant"
        className={`fixed bottom-6 right-6 z-40 w-14 h-14 rounded-full shadow-lg
                    flex items-center justify-center transition-all duration-200
                    bg-gradient-to-br from-cyan-500 to-blue-600
                    hover:from-cyan-400 hover:to-blue-500
                    shadow-cyan-500/30 hover:shadow-cyan-500/50 hover:scale-105
                    ${open ? "opacity-0 pointer-events-none scale-90" : "opacity-100"}`}
      >
        <MessageCircle className="w-6 h-6 text-white" />
      </button>

      {/* ── Chat panel ───────────────────────────────────────────────────── */}
      <div
        className={`fixed bottom-6 right-6 z-50 flex flex-col
                    w-[360px] max-w-[calc(100vw-2rem)]
                    h-[520px] max-h-[calc(100vh-6rem)]
                    bg-gray-50 dark:bg-slate-900
                    border border-gray-200 dark:border-slate-700
                    rounded-2xl shadow-2xl shadow-black/20
                    transition-all duration-200 origin-bottom-right
                    ${open
                      ? "opacity-100 scale-100 pointer-events-auto"
                      : "opacity-0 scale-90 pointer-events-none"
                    }`}
      >
        {/* Header */}
        <div className="flex items-center gap-3 px-4 py-3
                        border-b border-gray-200 dark:border-slate-700
                        bg-white dark:bg-slate-800 rounded-t-2xl flex-shrink-0">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-cyan-500 to-blue-500
                          flex items-center justify-center shadow-sm">
            <Bot className="w-4 h-4 text-white" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-gray-900 dark:text-white font-semibold text-sm">Study Assistant</p>
            <p className="text-gray-400 dark:text-slate-500 text-xs">Digital Logic · AI powered</p>
          </div>
          <div className="flex items-center gap-1">
            <button
              onClick={clearChat}
              title="Clear chat"
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600
                         dark:text-slate-500 dark:hover:text-slate-300
                         hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
            >
              <Minimize2 className="w-4 h-4" />
            </button>
            <button
              onClick={() => setOpen(false)}
              title="Close"
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600
                         dark:text-slate-500 dark:hover:text-slate-300
                         hover:bg-gray-100 dark:hover:bg-slate-700 transition-colors"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-0 scroll-smooth">
          {messages.map((msg, i) => (
            <Message key={i} msg={msg} />
          ))}
          {loading && <TypingIndicator />}
          <div ref={messagesEndRef} />
        </div>

        {/* Input */}
        <div className="px-3 py-3 border-t border-gray-200 dark:border-slate-700
                        bg-white dark:bg-slate-800 rounded-b-2xl flex-shrink-0">
          <div className="flex gap-2 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about K-Maps, gates, Boolean algebra…"
              rows={1}
              className="flex-1 resize-none bg-gray-50 dark:bg-slate-900
                         border border-gray-200 dark:border-slate-700
                         rounded-xl px-3 py-2.5 text-sm
                         text-gray-900 dark:text-white
                         placeholder-gray-400 dark:placeholder-slate-500
                         focus:outline-none focus:ring-2 focus:ring-cyan-500/40
                         transition-colors leading-relaxed
                         max-h-28 overflow-y-auto"
              style={{ fieldSizing: "content" }}
            />
            <button
              onClick={sendMessage}
              disabled={!input.trim() || loading}
              className="w-9 h-9 rounded-xl flex-shrink-0 flex items-center justify-center
                         bg-gradient-to-br from-cyan-500 to-blue-500
                         hover:from-cyan-400 hover:to-blue-400
                         disabled:opacity-40 disabled:cursor-not-allowed
                         shadow-sm shadow-cyan-500/20 transition-all"
            >
              {loading
                ? <Loader2 className="w-4 h-4 text-white animate-spin" />
                : <Send className="w-4 h-4 text-white" />
              }
            </button>
          </div>
          <p className="text-xs text-gray-400 dark:text-slate-600 mt-1.5 text-center">
            Enter to send · Shift+Enter for new line
          </p>
        </div>
      </div>
    </>
  );
}