import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Canvas / background hierarchy
        canvas: "#080e18",
        base: "#0d1525",
        surface: {
          DEFAULT: "#111e33",
          raised: "#162540",
        },
        // Line / border hierarchy
        line: {
          subtle: "rgba(255,255,255,0.06)",
          strong: "rgba(255,255,255,0.10)",
          accent: "rgba(59,130,246,0.30)",
        },
        // Text hierarchy
        ink: {
          primary: "#eef2ff",
          secondary: "#8fa3c0",
          muted: "#4e6380",
        },
        // Brand accent — blue, trust, protection
        accent: {
          DEFAULT: "#3b82f6",
          dim: "rgba(59,130,246,0.12)",
          hover: "#2563eb",
        },
        // Semantic feedback — scam severity
        safe: {
          DEFAULT: "#22c55e",
          dim: "rgba(34,197,94,0.10)",
          text: "#86efac",
        },
        watch: {
          DEFAULT: "#f59e0b",
          dim: "rgba(245,158,11,0.10)",
          text: "#fcd34d",
        },
        threat: {
          DEFAULT: "#ef4444",
          dim: "rgba(239,68,68,0.10)",
          text: "#fca5a5",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "-apple-system",
          "BlinkMacSystemFont",
          '"Segoe UI"',
          "system-ui",
          "sans-serif",
        ],
      },
      fontSize: {
        // 4 active sizes with semantic roles
        "display": ["24px", { lineHeight: "1.15", fontWeight: "600", letterSpacing: "-0.02em" }],
        "ui":      ["14px", { lineHeight: "1.4",  fontWeight: "500"  }],
        "body":    ["15px", { lineHeight: "1.6",  fontWeight: "400"  }],
        "kicker":  ["11px", { lineHeight: "1",    fontWeight: "600", letterSpacing: "0.08em" }],
      },
      borderRadius: {
        // Two intentional radius values
        "chip": "2px",
        "panel": "8px",
        "none": "0",
      },
      boxShadow: {
        // One surface shadow
        "surface": "0 1px 3px rgba(0,0,0,0.40), 0 0 0 1px rgba(255,255,255,0.06)",
        "surface-raised": "0 4px 12px rgba(0,0,0,0.40), 0 0 0 1px rgba(255,255,255,0.08)",
      },
      spacing: {
        // Explicit named spacers derived from 4px base
        "1": "4px",
        "2": "8px",
        "3": "12px",
        "4": "16px",
        "5": "20px",
        "6": "24px",
        "7": "28px",
        "8": "32px",
        "9": "36px",
        "10": "40px",
        "11": "44px",
        "12": "48px",
        "14": "56px",
        "16": "64px",
        "18": "72px",
        "20": "80px",
        "24": "96px",
        "px": "1px",
      },
      transitionDuration: {
        "micro": "120ms",
        "base": "180ms",
      },
    },
  },
  plugins: [],
};

export default config;
