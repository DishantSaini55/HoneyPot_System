/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: "#05070d",
        panel: "#0b1020",
        panelSoft: "#101936",
        neonCyan: "#27d5ff",
        neonRed: "#ff3d5f",
        botYellow: "#b89f3f",
        slateText: "#94a3b8",
      },
      boxShadow: {
        neonCyan: "0 0 24px rgba(39, 213, 255, 0.35)",
        neonRed: "0 0 24px rgba(255, 61, 95, 0.35)",
      },
      keyframes: {
        pulseRed: {
          "0%, 100%": { opacity: "1" },
          "50%": { opacity: "0.35" },
        },
        glide: {
          "0%": { transform: "translateX(100%)" },
          "100%": { transform: "translateX(-120%)" },
        },
      },
      animation: {
        pulseRed: "pulseRed 1.1s ease-in-out infinite",
        glide: "glide 16s linear infinite",
      },
      fontFamily: {
        sans: ["Rajdhani", "Segoe UI", "sans-serif"],
        mono: ["JetBrains Mono", "Consolas", "monospace"],
      },
    },
  },
  plugins: [],
};
