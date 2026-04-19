import React from "react";

/**
 * TopicIcon.jsx
 * ─────────────
 * Renders a topic-specific icon inside a colored rounded square, plus
 * returns the matching color stops via render props so the card can colour
 * its topic label to match.
 *
 * Usage:
 *   <TopicIcon topic="Boolean Algebra" />
 *
 * Topic matching is case-insensitive and treats underscores and spaces the
 * same, so "Boolean Algebra" and "Boolean_Algebra" map to the same icon.
 */

// Icons are kept small (22x22 viewBox) and stroke-based so they scale crisply
// and respect the current color via the parent's --icon-color CSS variable.

const ICON_PATHS = {
  boolean_algebra: (
    // A logic-gate silhouette: D-shape with two input lines + one output
    <g strokeLinecap="round" strokeLinejoin="round">
      <path d="M5 6h5a5 5 0 0 1 5 5v2a5 5 0 0 1-5 5H5z" />
      <line x1="2" y1="9" x2="5" y2="9" />
      <line x1="2" y1="15" x2="5" y2="15" />
      <line x1="15" y1="12" x2="22" y2="12" />
    </g>
  ),

  memory_systems: (
    // A memory chip with pins on all four sides
    <g strokeLinecap="round" strokeLinejoin="round">
      <rect x="5" y="5" width="14" height="14" rx="1" />
      <rect x="9" y="9" width="6" height="6" />
      <line x1="2" y1="8" x2="5" y2="8" />
      <line x1="2" y1="12" x2="5" y2="12" />
      <line x1="2" y1="16" x2="5" y2="16" />
      <line x1="19" y1="8" x2="22" y2="8" />
      <line x1="19" y1="12" x2="22" y2="12" />
      <line x1="19" y1="16" x2="22" y2="16" />
      <line x1="8" y1="2" x2="8" y2="5" />
      <line x1="12" y1="2" x2="12" y2="5" />
      <line x1="16" y1="2" x2="16" y2="5" />
      <line x1="8" y1="19" x2="8" y2="22" />
      <line x1="12" y1="19" x2="12" y2="22" />
      <line x1="16" y1="19" x2="16" y2="22" />
    </g>
  ),

  fsm: (
    // Three state circles linked by transition lines
    <g strokeLinecap="round" strokeLinejoin="round">
      <circle cx="6" cy="6" r="3" />
      <circle cx="18" cy="6" r="3" />
      <circle cx="12" cy="18" r="3" />
      <path d="M9 6h6" />
      <path d="M7.5 9l3 6" />
      <path d="M16.5 9l-3 6" />
    </g>
  ),

  digital_basics: (
    // A 2x2 grid of binary digits
    <g fontSize="8" fontWeight="500" strokeWidth="0">
      <text x="3" y="10">10</text>
      <text x="13" y="10">01</text>
      <text x="3" y="20">01</text>
      <text x="13" y="20">10</text>
    </g>
  ),

  sequential_logic: (
    // Clock waveform (square pulse) + horizontal reference line
    <g strokeLinecap="round" strokeLinejoin="round" fill="none">
      <polyline points="3 17 7 17 7 12 11 12 11 17 15 17 15 12 19 12 19 17 22 17" />
      <line x1="3" y1="7" x2="22" y2="7" />
    </g>
  ),

  hdl_verilog: (
    // Angle-bracket code symbol  < >
    <g strokeLinecap="round" strokeLinejoin="round" fill="none">
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </g>
  ),

  combinational_logic: (
    // Crossed-wire circuit paths
    <g strokeLinecap="round" strokeLinejoin="round" fill="none">
      <path d="M3 7h6l6 10h6" />
      <path d="M3 17h6l6 -10h6" />
      <circle cx="9" cy="7" r="1.3" />
      <circle cx="9" cy="17" r="1.3" />
      <circle cx="15" cy="7" r="1.3" />
      <circle cx="15" cy="17" r="1.3" />
    </g>
  ),

  logic_simplification: (
    // Downward arrow indicating reduction/simplification
    <g strokeLinecap="round" strokeLinejoin="round" fill="none">
      <line x1="4" y1="6" x2="20" y2="6" />
      <line x1="6" y1="12" x2="18" y2="12" />
      <line x1="9" y1="18" x2="15" y2="18" />
      <path d="M10 21l2 2 2 -2" />
    </g>
  ),

  registers_and_counters: (
    // Three stacked rectangles representing register cells
    <g strokeLinecap="round" strokeLinejoin="round" fill="none">
      <rect x="3" y="6" width="5" height="12" rx="1" />
      <rect x="9.5" y="6" width="5" height="12" rx="1" />
      <rect x="16" y="6" width="5" height="12" rx="1" />
      <line x1="2" y1="12" x2="3" y2="12" />
      <line x1="21" y1="12" x2="22" y2="12" />
    </g>
  ),

  timing_and_performance: (
    // Stopwatch / timer icon
    <g strokeLinecap="round" strokeLinejoin="round" fill="none">
      <circle cx="12" cy="13" r="7" />
      <line x1="12" y1="13" x2="12" y2="9" />
      <line x1="12" y1="13" x2="15" y2="15" />
      <line x1="9" y1="3" x2="15" y2="3" />
      <line x1="12" y1="3" x2="12" y2="5" />
    </g>
  ),
};

// Each topic gets a distinct color pair:
//   bg    → light background behind the icon
//   fg    → strong foreground used for the icon strokes AND the topic label
//   fgDk  → slightly brighter variant used in dark mode for readability
const TOPIC_COLORS = {
  boolean_algebra:        { bg: "#E6F1FB", fg: "#185FA5", fgDk: "#85B7EB" },
  memory_systems:         { bg: "#EEEDFE", fg: "#534AB7", fgDk: "#AFA9EC" },
  fsm:                    { bg: "#E1F5EE", fg: "#0F6E56", fgDk: "#5DCAA5" },
  digital_basics:         { bg: "#FAEEDA", fg: "#854F0B", fgDk: "#EF9F27" },
  sequential_logic:       { bg: "#FBEAF0", fg: "#993556", fgDk: "#ED93B1" },
  hdl_verilog:            { bg: "#FAECE7", fg: "#993C1D", fgDk: "#F0997B" },
  combinational_logic:    { bg: "#F1EFE8", fg: "#444441", fgDk: "#B4B2A9" },
  logic_simplification:   { bg: "#EAF3DE", fg: "#3B6D11", fgDk: "#97C459" },
  registers_and_counters: { bg: "#FCEBEB", fg: "#A32D2D", fgDk: "#F09595" },
  timing_and_performance: { bg: "#F1EFE8", fg: "#5F5E5A", fgDk: "#B4B2A9" },
};

// Fallback when the topic isn't in the list
const DEFAULT_COLOR = { bg: "#F1EFE8", fg: "#5F5E5A", fgDk: "#B4B2A9" };
const DEFAULT_ICON = (
  <g strokeLinecap="round" strokeLinejoin="round" fill="none">
    <circle cx="12" cy="12" r="8" />
    <path d="M12 8v4l2 2" />
  </g>
);

/**
 * Normalize a topic string so "Boolean Algebra", "boolean_algebra",
 * "BOOLEAN ALGEBRA " all map to the same key.
 */
function normalizeTopic(topic) {
  if (!topic) return "";
  return topic
    .toLowerCase()
    .trim()
    .replace(/[\s&]+/g, "_")   // spaces and '&' → underscore
    .replace(/_+/g, "_");       // collapse multiple underscores
}

/**
 * Public helper: returns the colors for a given topic.
 * Useful for styling the topic label next to the icon.
 */
export function getTopicColors(topic) {
  const key = normalizeTopic(topic);
  return TOPIC_COLORS[key] || DEFAULT_COLOR;
}

export default function TopicIcon({ topic, size = 42 }) {
  const key = normalizeTopic(topic);
  const iconPath = ICON_PATHS[key] || DEFAULT_ICON;
  const colors = TOPIC_COLORS[key] || DEFAULT_COLOR;

  // Tailwind can't inline dynamic hex values, so we use the `style` prop for
  // the exact colors and rely on Tailwind's classes for shape / alignment.
  return (
    <div
      className="rounded-xl flex items-center justify-center flex-shrink-0 transition-colors"
      style={{
        width: size,
        height: size,
        backgroundColor: colors.bg,
      }}
      aria-hidden="true"
    >
      <svg
        width={Math.round(size * 0.52)}
        height={Math.round(size * 0.52)}
        viewBox="0 0 24 24"
        fill="none"
        stroke={colors.fg}
        strokeWidth="1.8"
      >
        {React.cloneElement(iconPath, {
          fill: iconPath.props.fill ?? colors.fg,
        })}
      </svg>
    </div>
  );
}
