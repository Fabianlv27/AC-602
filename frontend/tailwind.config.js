/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}", // <--- ESTA LÍNEA ES CRUCIAL
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}