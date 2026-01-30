/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                background: "#0f172a", // Slate 900
                surface: "#1e293b",    // Slate 800
                primary: "#3b82f6",    // Blue 500
                accent: "#06b6d4",     // Cyan 500
                success: "#10b981",    // Emerald 500
                danger: "#ef4444",     // Red 500
                glass: "rgba(30, 41, 59, 0.7)", // Glassmorphism base
            },
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },
    plugins: [],
}
