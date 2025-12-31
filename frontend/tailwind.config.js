/** @type {import('tailwindcss').Config} */
export default {
	content: ['./src/**/*.{html,js,svelte,ts}'],
	darkMode: 'class',
	theme: {
		extend: {
			fontFamily: {
				sans: ['IBM Plex Sans', 'system-ui', 'sans-serif'],
				mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
				serif: ['Crimson Pro', 'Georgia', 'serif']
			},
			colors: {
				// Custom color palette for obsidian-like theme
				obsidian: {
					50: '#f7f7f8',
					100: '#eeeef0',
					200: '#d9d9de',
					300: '#b8b8c1',
					400: '#91919f',
					500: '#737384',
					600: '#5d5d6b',
					700: '#4c4c57',
					800: '#41414a',
					900: '#393940',
					950: '#1e1e21'
				},
				accent: {
					50: '#f0f9ff',
					100: '#e0f2fe',
					200: '#bae6fd',
					300: '#7dd3fc',
					400: '#38bdf8',
					500: '#0ea5e9',
					600: '#0284c7',
					700: '#0369a1',
					800: '#075985',
					900: '#0c4a6e',
					950: '#082f49'
				}
			},
			typography: (theme) => ({
				DEFAULT: {
					css: {
						'--tw-prose-body': theme('colors.obsidian.700'),
						'--tw-prose-headings': theme('colors.obsidian.900'),
						'--tw-prose-links': theme('colors.accent.600'),
						'--tw-prose-code': theme('colors.obsidian.800'),
						maxWidth: 'none',
						a: {
							textDecoration: 'none',
							'&:hover': {
								textDecoration: 'underline'
							}
						},
						'code::before': {
							content: '""'
						},
						'code::after': {
							content: '""'
						}
					}
				},
				invert: {
					css: {
						'--tw-prose-body': theme('colors.obsidian.200'),
						'--tw-prose-headings': theme('colors.obsidian.50'),
						'--tw-prose-links': theme('colors.accent.400'),
						'--tw-prose-code': theme('colors.obsidian.200')
					}
				}
			})
		}
	},
	plugins: [require('@tailwindcss/typography')]
};

