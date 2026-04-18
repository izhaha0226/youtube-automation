import type { Config } from "tailwindcss";

export default {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        navy: "#0E1E3A",
        accent: "#E6B43C",
      },
    },
  },
  plugins: [],
} satisfies Config;
