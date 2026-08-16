import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        obsidian: "#07080d",
        panel: "#111827",
        signal: "#58f29b",
        amberline: "#f7c948",
        ice: "#b9d8ff"
      },
      boxShadow: {
        glow: "0 0 40px rgba(88, 242, 155, 0.14)"
      }
    }
  },
  plugins: []
};

export default config;
