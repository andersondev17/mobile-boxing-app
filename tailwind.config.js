/** @type {import('tailwindcss').Config} */
module.exports = {
  // NOTE: Update this to include the paths to all files that contain Nativewind classes.
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#FF4500", // Naranja-rojo principal
          50: "#FFF4ED",
          100: "#FFE6D3",
          200: "#FFCBA6",
          300: "#FFA574",
          400: "#FF7340",
          500: "#FF4500",     // Main color
          600: "#E63900",     // HOVER STATE ⭐
          700: "#CC3300",
          800: "#B32D00",
          900: "#7A1F00"
        },
        secondary: {
          DEFAULT: "#1E3A8A", // Azul profundo
          50: "#EFF6FF",
          100: "#DBEAFE",
          200: "#BFDBFE",
          300: "#93C5FD",
          400: "#60A5FA",
          500: "#3B82F6",
          600: "#2563EB",
          700: "#1D4ED8",
          800: "#1E40AF",     // Fondo principal
          900: "#1E3A8A"      // Azul más profundo
        },
        accent: {
          orange: "#FF6B35",    // Naranja vibrante (CTAs secundarios)
          cosmic: "#8B5CF6",    // Violeta espacial (highlights)
          neon: "#00D4AA",      // Verde cyan (success/progress)
          stellar: "#F59E0B"    // Dorado (achievements)
        },
        light: {
          100: "#D6C6FF",
          200: "#A8B5DB",
          300: "#9CA4AB",
        },
        gymshock: {
          dark: {
            900: "#030014",     // Azul negro profundo (main bg)
            800: "#1E293B",     // Azul gris (cards)
            700: "#334155",     // Bordes suaves
            600: "#475569"      // Texto secundario
          }
        },
        dark: {
          100: "#151312",
          200: "#221F3D",
        },
      },
      backgroundImage: {
        'cosmic-fire': 'linear-gradient(135deg, #FF4500 0%, #FF6B35 50%, #1E40AF 100%)',
      }
    },
  },
  plugins: [],
}