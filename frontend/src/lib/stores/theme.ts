/**
 * Theme store for managing light/dark mode.
 */
import { writable } from 'svelte/store';

const browser = typeof window !== 'undefined';

type Theme = 'light' | 'dark' | 'system';

function getInitialTheme(): Theme {
	if (!browser) return 'system';

	const stored = localStorage.getItem('theme') as Theme | null;
	if (stored && ['light', 'dark', 'system'].includes(stored)) {
		return stored;
	}
	return 'system';
}

function getSystemTheme(): 'light' | 'dark' {
	if (!browser) return 'light';
	return window.matchMedia('(prefers-color-scheme: dark)').matches
		? 'dark'
		: 'light';
}

function applyTheme(theme: Theme): void {
	if (!browser) return;

	const effectiveTheme = theme === 'system' ? getSystemTheme() : theme;

	if (effectiveTheme === 'dark') {
		document.documentElement.classList.add('dark');
	} else {
		document.documentElement.classList.remove('dark');
	}

	localStorage.setItem('theme', theme);
}

function createThemeStore() {
	const { subscribe, set, update } = writable<Theme>(getInitialTheme());

	// Apply initial theme
	if (browser) {
		const initial = getInitialTheme();
		applyTheme(initial);

		// Listen for system theme changes
		window
			.matchMedia('(prefers-color-scheme: dark)')
			.addEventListener('change', () => {
				update((current) => {
					if (current === 'system') {
						applyTheme('system');
					}
					return current;
				});
			});
	}

	return {
		subscribe,

		/**
		 * Set the theme.
		 */
		setTheme(theme: Theme): void {
			applyTheme(theme);
			set(theme);
		},

		/**
		 * Toggle between light and dark (or cycle through if on system).
		 */
		toggle(): void {
			update((current) => {
				let next: Theme;
				if (current === 'light') {
					next = 'dark';
				} else if (current === 'dark') {
					next = 'light';
				} else {
					// system -> toggle to opposite of current system theme
					next = getSystemTheme() === 'dark' ? 'light' : 'dark';
				}
				applyTheme(next);
				return next;
			});
		}
	};
}

export const theme = createThemeStore();

