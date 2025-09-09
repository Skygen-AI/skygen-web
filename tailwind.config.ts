import type { Config } from 'tailwindcss'

export default {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
    './react-bits-components/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      fontFamily: {
        'figtree': ['Figtree', 'sans-serif'],
      },
      animation: {
        gradient: 'gradient 8s linear infinite',
        'animated-gradient': 'animated-gradient 4s linear infinite',
        'color-shift': 'color-shift 8s ease-in-out infinite',
        'flowing-gradient': 'flowing-gradient 3s linear infinite',
        'seamless-flow': 'seamless-flow 8s linear infinite',
      },
      keyframes: {
        gradient: {
          '0%, 100%': {
            'background-size': '200% 200%',
            'background-position': 'left center',
          },
          '50%': {
            'background-size': '200% 200%',
            'background-position': 'right center',
          },
        },
      },
    },
  },
  plugins: [],
} satisfies Config
