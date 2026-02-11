/**
 * Vault store for managing vault state and file tree.
 */
import { writable, derived, get } from 'svelte/store';
import {
	vaultApi,
	type VaultInfo,
	type FileTreeItem,
	type NoteResponse,
	type VaultCreateRequest
} from '../api';

interface VaultState {
	vaults: VaultInfo[];
	activeVaultId: string | null;
	defaultVaultId: string | null;
	fileTree: FileTreeItem[];
	currentNote: NoteResponse | null;
	loading: boolean;
	noteLoading: boolean;
	error: string | null;
	/** True only after vault has been selected on backend - safe to make note requests */
	vaultReady: boolean;
}

const STORAGE_KEY = 'activeVaultId';
const browser = typeof window !== 'undefined';

function getStoredVaultId(): string | null {
	if (!browser) return null;
	return localStorage.getItem(STORAGE_KEY);
}

function setStoredVaultId(vaultId: string | null): void {
	if (!browser) return;
	if (vaultId) {
		localStorage.setItem(STORAGE_KEY, vaultId);
	} else {
		localStorage.removeItem(STORAGE_KEY);
	}
}

interface CachedNote {
	note: NoteResponse;
	cachedAt: number;
}

// In-memory note cache, keyed by "vaultId:notePath"
const noteCache = new Map<string, CachedNote>();

// Cache TTL in milliseconds (5 minutes)
const CACHE_TTL = 5 * 60 * 1000;

const initialState: VaultState = {
	vaults: [],
	activeVaultId: null,
	defaultVaultId: null,
	fileTree: [],
	currentNote: null,
	loading: false,
	noteLoading: false,
	error: null,
	vaultReady: false
};

function createVaultStore() {
	const store = writable<VaultState>(initialState);
	const { subscribe, set, update } = store;

	let loadVaultsInProgress = false;

	return {
		subscribe,

		/**
		 * Load list of available vaults.
		 * Deduplicates concurrent calls to prevent race conditions.
		 */
		async loadVaults(): Promise<void> {
			if (loadVaultsInProgress) return;
			loadVaultsInProgress = true;

			update((state) => ({ ...state, loading: true, error: null }));

			try {
				const response = await vaultApi.list();
				let activeVault = response.active_vault;

				// Check localStorage for a stored vault preference
				const storedVaultId = getStoredVaultId();
				if (
					storedVaultId &&
					storedVaultId !== activeVault &&
					response.vaults.some((v) => v.id === storedVaultId)
				) {
					// Re-sync backend to match the user's stored preference
					try {
						await vaultApi.select(storedVaultId);
						activeVault = storedVaultId;
					} catch {
						// If re-select fails, fall back to what the backend returned
						setStoredVaultId(activeVault);
					}
				} else if (activeVault) {
					// Persist whatever the backend returned
					setStoredVaultId(activeVault);
				}

				update((state) => ({
					...state,
					vaults: response.vaults,
					activeVaultId: activeVault,
					defaultVaultId: response.default_vault,
					vaultReady: !!activeVault,
					loading: false
				}));

				// Load file tree if we have an active vault
				if (activeVault) {
					await this.loadFileTree();
				}
			} catch (e) {
				const error = e as { detail?: string };
				update((state) => ({
					...state,
					loading: false,
					vaultReady: false,
					error: error.detail || 'Failed to load vaults'
				}));
			} finally {
				loadVaultsInProgress = false;
			}
		},

		/**
		 * Select a vault as the active vault.
		 */
		async selectVault(vaultId: string): Promise<boolean> {
			// Clear file tree and note immediately for responsive UI
			update((state) => ({ 
				...state, 
				loading: true, 
				fileTree: [],
				currentNote: null,
				error: null 
			}));

			try {
				await vaultApi.select(vaultId);
				
				// Clear note cache when switching vaults
				this.clearNoteCache();
				
				// Load file tree for new vault BEFORE updating state
				const treeResponse = await vaultApi.getTree();
				
				// Persist vault selection to localStorage
				setStoredVaultId(vaultId);

				update((state) => ({
					...state,
					activeVaultId: vaultId,
					vaultReady: true,
					fileTree: treeResponse.tree,
					loading: false
				}));

				return true;
			} catch (e) {
				const error = e as { detail?: string };
				update((state) => ({
					...state,
					loading: false,
					error: error.detail || 'Failed to select vault'
				}));
				return false;
			}
		},

		/**
		 * Load file tree for the active vault.
		 */
		async loadFileTree(): Promise<void> {
			try {
				const response = await vaultApi.getTree();
				update((state) => ({
					...state,
					fileTree: response.tree
				}));
			} catch (e) {
				const error = e as { detail?: string };
				update((state) => ({
					...state,
					error: error.detail || 'Failed to load file tree'
				}));
			}
		},

		/**
		 * Load a specific note by path.
		 * Uses in-memory cache to avoid re-fetching recently loaded notes.
		 */
		async loadNote(path: string): Promise<NoteResponse | null> {
			// Get current vault ID for cache key
			const currentVaultId = get(store).activeVaultId;
			
			if (!currentVaultId) {
				update((state) => ({
					...state,
					error: 'No vault selected'
				}));
				return null;
			}
			
			const cacheKey = `${currentVaultId}:${path}`;
			const cached = noteCache.get(cacheKey);
			
			// Check if we have a valid cached note
			if (cached && (Date.now() - cached.cachedAt) < CACHE_TTL) {
				// Return from cache immediately, ensuring noteLoading is false
				update((state) => ({
					...state,
					currentNote: cached.note,
					noteLoading: false,
					error: null
				}));
				return cached.note;
			}

			update((state) => ({ ...state, noteLoading: true, error: null }));

			try {
				const note = await vaultApi.getNote(path);
				
				// Store in cache
				noteCache.set(cacheKey, {
					note,
					cachedAt: Date.now()
				});
				
				update((state) => ({
					...state,
					currentNote: note,
					noteLoading: false
				}));
				return note;
			} catch (e) {
				const error = e as { detail?: string };
				update((state) => ({
					...state,
					currentNote: null,
					noteLoading: false,
					error: error.detail || 'Failed to load note'
				}));
				return null;
			}
		},

		/**
		 * Clear current note.
		 */
		clearNote(): void {
			update((state) => ({ ...state, currentNote: null }));
		},

		/**
		 * Clear error state.
		 */
		clearError(): void {
			update((state) => ({ ...state, error: null }));
		},

		/**
		 * Reset store to initial state.
		 */
		reset(): void {
			this.clearNoteCache();
			setStoredVaultId(null);
			set(initialState);
		},

		/**
		 * Clear all cached notes.
		 */
		clearNoteCache(): void {
			noteCache.clear();
		},

		/**
		 * Invalidate a specific note from the cache (e.g., after edit).
		 */
		invalidateNote(path: string): void {
			const currentVaultId = get(store).activeVaultId;
			if (currentVaultId) {
				const cacheKey = `${currentVaultId}:${path}`;
				noteCache.delete(cacheKey);
			}
		},

		/**
		 * Get the number of cached notes (for debugging).
		 */
		getCacheSize(): number {
			return noteCache.size;
		},

		/**
		 * Create a new vault from a git repository.
		 */
		async addVault(request: VaultCreateRequest): Promise<VaultInfo | null> {
			update((state) => ({ ...state, loading: true, error: null }));

			try {
				const newVault = await vaultApi.create(request);

				// Reload vaults list
				const response = await vaultApi.list();
				update((state) => ({
					...state,
					vaults: response.vaults,
					loading: false
				}));

				return newVault;
			} catch (e) {
				const error = e as { detail?: string };
				update((state) => ({
					...state,
					loading: false,
					error: error.detail || 'Failed to create vault'
				}));
				return null;
			}
		},

		/**
		 * Delete a vault.
		 */
		async deleteVault(vaultId: string, deleteFiles: boolean = true): Promise<boolean> {
			update((state) => ({ ...state, loading: true, error: null }));

			try {
				await vaultApi.delete(vaultId, deleteFiles);

				// Clear note cache
				this.clearNoteCache();

				// Reload vaults list
				const response = await vaultApi.list();

				// Update stored vault after deletion
				setStoredVaultId(response.active_vault);

				update((state) => ({
					...state,
					vaults: response.vaults,
					activeVaultId: response.active_vault,
					defaultVaultId: response.default_vault,
					currentNote: null,
					loading: false
				}));

				// Load file tree if we still have an active vault
				if (response.active_vault) {
					await this.loadFileTree();
				} else {
					update((state) => ({ ...state, fileTree: [] }));
				}

				return true;
			} catch (e) {
				const error = e as { detail?: string };
				update((state) => ({
					...state,
					loading: false,
					error: error.detail || 'Failed to delete vault'
				}));
				return false;
			}
		},

		/**
		 * Sync a vault (git pull).
		 */
		async syncVault(vaultId: string): Promise<{ success: boolean; message: string }> {
			try {
				const result = await vaultApi.sync(vaultId);
				return { success: result.success, message: result.message };
			} catch (e) {
				const error = e as { detail?: string };
				return { success: false, message: error.detail || 'Failed to sync vault' };
			}
		}
	};
}

export const vault = createVaultStore();

// Derived stores
export const activeVault = derived(vault, ($vault) =>
	$vault.vaults.find((v) => v.id === $vault.activeVaultId)
);

export const vaultLoading = derived(vault, ($vault) => $vault.loading);
export const noteLoading = derived(vault, ($vault) => $vault.noteLoading);
export const vaultError = derived(vault, ($vault) => $vault.error);

