// theme.js - DigitalLogicHub brand palette
// Import this in every page: import { T, css } from "../theme";

export const T = {
  // ── Brand teal scale ────────────────────────────────
  lightest: "#EAF6F7",
  light:    "#DFF3F4",
  soft:     "#C7EBEE",
  mid:      "#9ED6DB",
  teal:     "#5BBAC4",
  deep:     "#2EA7B2",

  // ── Dark text / UI ──────────────────────────────────
  dark:     "#1F2937",
  muted:    "#4B5563",
  gray:     "#9CA3AF",

  // ── Backgrounds ─────────────────────────────────────
  white:    "#FFFFFF",
  bg:       "#F3F4F6",
  accent:   "#FFEED2",

  // ── Semantic ────────────────────────────────────────
  success:  "#166534",
  successBg:"#DCFCE7",
  successBorder:"#86EFAC",
  error:    "#991B1B",
  errorBg:  "#FEE2E2",
  errorBorder:"#FCA5A5",
  warning:  "#92400E",
  warningBg:"#FFEED2",
};

// Reusable inline-style helpers
export const css = {
  page: {
    minHeight: "100vh",
    background: `linear-gradient(135deg, ${T.lightest} 0%, ${T.light} 40%, ${T.soft} 100%)`,
    fontFamily: "'Segoe UI', system-ui, sans-serif",
  },

  card: {
    background: T.white,
    border: `1.5px solid ${T.soft}`,
    borderRadius: 20,
    boxShadow: "0 4px 24px rgba(46,167,178,0.10)",
  },

  input: {
    width: "100%",
    padding: "12px 16px",
    background: T.lightest,
    border: `1.5px solid ${T.soft}`,
    borderRadius: 12,
    color: T.dark,
    fontSize: 15,
    fontFamily: "inherit",
    outline: "none",
    boxSizing: "border-box",
    transition: "border-color 0.15s",
  },

  inputFocus: {
    borderColor: T.teal,
    background: T.white,
  },

  btn: {
    padding: "12px 24px",
    background: `linear-gradient(135deg, ${T.teal}, ${T.deep})`,
    color: T.white,
    border: "none",
    borderRadius: 12,
    fontWeight: 700,
    fontSize: 15,
    cursor: "pointer",
    width: "100%",
    fontFamily: "inherit",
    transition: "opacity 0.15s, transform 0.15s",
    letterSpacing: "0.01em",
  },

  btnSecondary: {
    padding: "10px 20px",
    background: T.lightest,
    color: T.deep,
    border: `1.5px solid ${T.soft}`,
    borderRadius: 12,
    fontWeight: 600,
    fontSize: 14,
    cursor: "pointer",
    fontFamily: "inherit",
    transition: "background 0.15s",
  },

  label: {
    fontSize: 12,
    fontWeight: 700,
    color: T.muted,
    letterSpacing: "0.06em",
    textTransform: "uppercase",
    display: "block",
    marginBottom: 6,
  },

  errorBox: {
    padding: "10px 14px",
    background: T.errorBg,
    border: `1px solid ${T.errorBorder}`,
    borderRadius: 10,
    color: T.error,
    fontSize: 13,
    fontWeight: 500,
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 14,
  },

  successBox: {
    padding: "10px 14px",
    background: T.successBg,
    border: `1px solid ${T.successBorder}`,
    borderRadius: 10,
    color: T.success,
    fontSize: 13,
    fontWeight: 500,
    display: "flex",
    alignItems: "center",
    gap: 8,
    marginBottom: 14,
  },
};