/**
 * Authentication store for managing user auth state.
 */
import { writable, derived } from 'svelte/store';
import { authApi, type AuthStatus } from '../api';

interface AuthState {
	authenticated: boolean;
	loading: boolean;
	error: string | null;
}

// Check if we have a login hint cookie (set by login, cleared by logout)
// This lets us skip the API call entirely for definitely-unauthenticated users
function hasLoginHint(): boolean {
	if (typeof document === 'undefined') return false;
	return document.cookie.includes('auth_hint=1');
}

function setLoginHint(): void {
	if (typeof document === 'undefined') return;
	// Set a non-httpOnly hint cookie (expires with session or in 24h)
	document.cookie = 'auth_hint=1; path=/; max-age=86400; SameSite=Lax';
}

function clearLoginHint(): void {
	if (typeof document === 'undefined') return;
	document.cookie = 'auth_hint=; path=/; max-age=0';
}

// If no login hint, we know user is definitely not authenticated
const initialState: AuthState = {
	authenticated: false,
	loading: hasLoginHint(), // Only show loading if there might be a session
	error: null
};

function createAuthStore() {
	const { subscribe, set, update } = writable<AuthState>(initialState);

	return {
		subscribe,

		/**
		 * Check current authentication status with the server.
		 * Skips API call if we know user is definitely not authenticated.
		 */
		async checkStatus(): Promise<boolean> {
			// Fast path: if no login hint, user is definitely not authenticated
			if (!hasLoginHint()) {
				set({
					authenticated: false,
					loading: false,
					error: null
				});
				return false;
			}

			update((state) => ({ ...state, loading: true, error: null }));

			try {
				const status = await authApi.status();
				
				// If server says not authenticated, clear the hint
				if (!status.authenticated) {
					clearLoginHint();
				}
				
				update((state) => ({
					...state,
					authenticated: status.authenticated,
					loading: false
				}));
				return status.authenticated;
			} catch {
				clearLoginHint();
				update((state) => ({
					...state,
					authenticated: false,
					loading: false
				}));
				return false;
			}
		},

		/**
		 * Login with password.
		 */
		async login(password: string): Promise<boolean> {
			update((state) => ({ ...state, loading: true, error: null }));

			try {
				await authApi.login(password);
				// Set hint cookie so future visits know to check auth
				setLoginHint();
				update((state) => ({
					...state,
					authenticated: true,
					loading: false
				}));
				return true;
			} catch (e) {
				const error = e as { detail?: string };
				update((state) => ({
					...state,
					authenticated: false,
					loading: false,
					error: error.detail || 'Login failed'
				}));
				return false;
			}
		},

		/**
		 * Logout current user.
		 */
		async logout(): Promise<void> {
			// Clear hint cookie immediately
			clearLoginHint();
			
			// Clear state immediately for responsive UI
			set({
				authenticated: false,
				loading: false,
				error: null
			});

			// Fire API call in background - don't block on it
			try {
				await authApi.logout();
			} catch {
				// Ignore errors on logout
			}
		},

		/**
		 * Clear any error state.
		 */
		clearError(): void {
			update((state) => ({ ...state, error: null }));
		},

		/**
		 * Mark initial loading as done (for pages that don't need auth check).
		 */
		markLoadingDone(): void {
			update((state) => ({ ...state, loading: false }));
		}
	};
}

export const auth = createAuthStore();

// Derived store for checking if authenticated
export const isAuthenticated = derived(auth, ($auth) => $auth.authenticated);
export const isAuthLoading = derived(auth, ($auth) => $auth.loading);
export const authError = derived(auth, ($auth) => $auth.error);

