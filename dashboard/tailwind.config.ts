import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        scam: {
          red: "#EF4444",
          green: "#22C55E",
          amber: "#F59E0B",
        },
      },
    },
  },
  plugins: [],
};

export default config;
