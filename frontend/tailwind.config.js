/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Nigerian flag colors
        'nigeria-green': '#008751',
        'nigeria-white': '#FFFFFF',
        // Custom color palette for severity levels
        'severity': {
          'critical': '#DC2626', // Red
          'high': '#EA580C',     // Orange
          'moderate': '#F59E0B', // Amber
          'low': '#16A34A',      // Green
        },
        // Incident type colors
        'incident': {
          'armed-attack': '#EF4444',
          'insurgent': '#DC2626',
          'kidnapping': '#F97316',
          'banditry': '#F59E0B',
          'clash': '#EAB308',
          'bombing': '#B91C1C',
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
}
