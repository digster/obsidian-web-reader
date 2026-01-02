/**
 * API client for communicating with the backend.
 */

const API_BASE = '/api';

export interface ApiError {
	detail: string;
	status: number;
}

class ApiClient {
	private async request<T>(
		endpoint: string,
		options: RequestInit = {}
	): Promise<T> {
		const url = `${API_BASE}${endpoint}`;

		const response = await fetch(url, {
			...options,
			credentials: 'include',
			headers: {
				'Content-Type': 'application/json',
				...options.headers
			}
		});

		if (!response.ok) {
			const error: ApiError = {
				detail: 'An error occurred',
				status: response.status
			};

			try {
				const data = await response.json();
				error.detail = data.detail || error.detail;
			} catch {
				// Ignore JSON parse errors
			}

			throw error;
		}

		return response.json();
	}

	async get<T>(endpoint: string): Promise<T> {
		return this.request<T>(endpoint, { method: 'GET' });
	}

	async post<T>(endpoint: string, body?: unknown): Promise<T> {
		return this.request<T>(endpoint, {
			method: 'POST',
			body: body ? JSON.stringify(body) : undefined
		});
	}

	async delete<T>(endpoint: string): Promise<T> {
		return this.request<T>(endpoint, { method: 'DELETE' });
	}
}

export const api = new ApiClient();

// API Types
export interface LoginRequest {
	password: string;
}

export interface TokenResponse {
	access_token: string;
	token_type: string;
}

export interface AuthStatus {
	authenticated: boolean;
	active_vault: string | null;
}

export interface VaultInfo {
	id: string;
	name: string;
	path: string;
	note_count: number;
}

export interface VaultCreateRequest {
	name: string;
	repo_url: string;
	token: string;
	refresh_interval_minutes?: number | null;
}

export interface VaultSyncResponse {
	vault_id: string;
	success: boolean;
	message: string;
}

export interface VaultListResponse {
	vaults: VaultInfo[];
	active_vault: string | null;
	default_vault: string | null;
}

export interface FileTreeItem {
	name: string;
	path: string;
	type: 'file' | 'folder';
	children?: FileTreeItem[];
}

export interface FileTreeResponse {
	vault_id: string;
	tree: FileTreeItem[];
}

export interface BacklinkInfo {
	path: string;
	title: string;
}

export interface NoteResponse {
	path: string;
	title: string;
	content_html: string;
	frontmatter: Record<string, unknown>;
	tags: string[];
	backlinks: BacklinkInfo[];
	modified_at: string | null;
}

export interface SearchResult {
	path: string;
	title: string;
	snippet: string;
	score: number;
}

export interface SearchResponse {
	query: string;
	results: SearchResult[];
	total: number;
}

// Auth API
export const authApi = {
	login: (password: string) =>
		api.post<TokenResponse>('/auth/login', { password }),

	logout: () => api.post<{ message: string }>('/auth/logout'),

	status: () => api.get<AuthStatus>('/auth/me')
};

// Vault API
export const vaultApi = {
	list: () => api.get<VaultListResponse>('/vaults'),

	select: (vaultId: string) =>
		api.post<{ message: string }>('/vaults/select', { vault_id: vaultId }),

	create: (request: VaultCreateRequest) =>
		api.post<VaultInfo>('/vaults/create', request),

	delete: (vaultId: string, deleteFiles: boolean = true) =>
		api.delete<{ message: string }>(
			`/vaults/${encodeURIComponent(vaultId)}?delete_files=${deleteFiles}`
		),

	sync: (vaultId: string) =>
		api.post<VaultSyncResponse>(`/vaults/${encodeURIComponent(vaultId)}/sync`),

	getTree: () => api.get<FileTreeResponse>('/vault/tree'),

	getNote: (path: string) =>
		api.get<NoteResponse>(`/vault/note/${encodeURIComponent(path)}`),

	getAttachmentUrl: (path: string) =>
		`${API_BASE}/vault/attachment/${encodeURIComponent(path)}`
};

// Search API
export const searchApi = {
	search: (query: string) =>
		api.get<SearchResponse>(`/search?q=${encodeURIComponent(query)}`),

	reindex: () => api.post<{ message: string }>('/search/reindex')
};

