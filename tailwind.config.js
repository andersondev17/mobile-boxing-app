/** @type {import('tailwindcss').Config} */
module.exports = {
  // NOTE: Update this to include the paths to all files that contain Nativewind classes.
  content: ["./app/**/*.{js,jsx,ts,tsx}", "./components/**/*.{js,jsx,ts,tsx}"],
  presets: [require("nativewind/preset")],
  theme: {
    extend: {
      fontFamily: {
        "spacemono": ["SpaceMono"],
        "oswaldbold": ["OswaldBold"],
        "oswaldmed": ["OswaldMedium"],
        "oswald": ["OswaldRegular"],
        "OswaldLight": ["OswaldLight"],
        "OswaldExtraLight": ["OswaldExtraLight"]
      },
      colors: {
        primary: {
          DEFAULT: "#B8860B", // Naranja-rojo principal
          50: "#FFF8DC",
          100: "#FFEFD5",
          200: "#FFE4B5",
          300: "#FFD700",
          400: "#DAA520",
          500: "#B8860B",     // Dorado principal
          600: "#9A7209",
          700: "#7D5E07",
          800: "#604A05",
          900: "#433603"
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
          gold: {
            600: "#FFB300",   // (CTAs principales)
            400: "#FFC107",   // (CTAs secundarios)
            200: "#FFCA28"  
          },
          cosmic: "#2C2C2C",    // Violeta espacial (highlights)
          neon: "#8B0000",      // Verde cyan (success/progress)
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
          100: "#0A0A0A",
          200: "#221F3D",
        },
      },
      backgroundImage: {
        'premiumGradient': 'linear-gradient(135deg, #0A0A0A 0%, #2C2C2C 50%, #B8860B 100%)',
        'legacyGlow': 'radial-gradient(circle, rgba(255,215,0,0.1) 0%, rgba(10,10,10,1) 70%)',
        'underground': 'linear-gradient(45deg, #8B0000 0%, #0A0A0A 100%)'
      }
    },
  },
  plugins: [],
}