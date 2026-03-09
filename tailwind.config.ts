/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: {
            50: '#EBF5FF',
            100: '#E1EFFE',
            600: '#1C64F2',
            900: '#1E3A8A',
          },
          yellow: {
            100: '#FEF9C3',
            400: '#FACC15',
            500: '#EAB308',
          },
        },
        paper: '#F9FAFB',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}