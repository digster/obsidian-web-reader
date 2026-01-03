<script lang="ts">
	import { vaultApi, type VaultCreateRequest, type VaultInfo } from '../api';
	import Portal from './Portal.svelte';

	interface Props {
		open: boolean;
		onClose: () => void;
		onSuccess: (vault: VaultInfo) => void;
	}

	let { open = $bindable(), onClose, onSuccess }: Props = $props();

	let name = $state('');
	let repoUrl = $state('');
	let token = $state('');
	let refreshInterval = $state<number | null>(null);
	let enableRefresh = $state(false);

	let loading = $state(false);
	let error = $state<string | null>(null);

	// Form validation
	let nameError = $derived(name.length > 0 && name.length < 1 ? 'Name is required' : null);
	let urlError = $derived(() => {
		if (!repoUrl) return null;
		if (!repoUrl.startsWith('https://')) return 'URL must start with https://';
		if (!repoUrl.includes('github.com') && !repoUrl.includes('gitlab.com'))
			return 'Only GitHub and GitLab URLs are supported';
		return null;
	});
	let tokenError = $derived(token.length > 0 && token.length < 10 ? 'Token seems too short' : null);

	let isValid = $derived(
		name.length > 0 &&
			repoUrl.length > 0 &&
			token.length > 0 &&
			!urlError() &&
			(!enableRefresh || (refreshInterval && refreshInterval >= 1 && refreshInterval <= 1440))
	);

	function resetForm() {
		name = '';
		repoUrl = '';
		token = '';
		refreshInterval = null;
		enableRefresh = false;
		error = null;
	}

	function handleClose() {
		if (!loading) {
			resetForm();
			onClose();
		}
	}

	async function handleSubmit(e: Event) {
		e.preventDefault();
		if (!isValid || loading) return;

		loading = true;
		error = null;

		try {
			const request: VaultCreateRequest = {
				name: name.trim(),
				repo_url: repoUrl.trim(),
				token: token.trim(),
				refresh_interval_minutes: enableRefresh && refreshInterval ? refreshInterval : null
			};

			const vault = await vaultApi.create(request);
			resetForm();
			onSuccess(vault);
		} catch (e) {
			const err = e as { detail?: string };
			error = err.detail || 'Failed to create vault. Please check your credentials.';
		} finally {
			loading = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && !loading) {
			handleClose();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<Portal>
		<!-- Backdrop -->
		<div
			class="fixed inset-0 z-[100] flex items-center justify-center overflow-y-auto bg-black/50 p-4 backdrop-blur-sm"
			onclick={(e) => e.target === e.currentTarget && handleClose()}
			role="dialog"
			aria-modal="true"
			aria-labelledby="modal-title"
		>
		<!-- Modal -->
		<div
			class="relative my-auto w-full max-w-lg rounded-xl border border-obsidian-200 bg-white p-6 shadow-2xl dark:border-obsidian-700 dark:bg-obsidian-900"
		>
			<!-- Close button -->
			<button
				type="button"
				class="absolute right-4 top-4 rounded-lg p-1 text-obsidian-500 transition-colors hover:bg-obsidian-100 hover:text-obsidian-700 dark:hover:bg-obsidian-800 dark:hover:text-obsidian-300"
				onclick={handleClose}
				disabled={loading}
				aria-label="Close modal"
			>
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M6 18L18 6M6 6l12 12"
					/>
				</svg>
			</button>

			<!-- Header -->
			<div class="mb-6">
				<h2 id="modal-title" class="text-xl font-semibold text-obsidian-900 dark:text-obsidian-100">
					Add New Vault
				</h2>
				<p class="mt-1 text-sm text-obsidian-500">
					Clone a vault from a GitHub repository using a deploy token.
				</p>
			</div>

			<!-- Form -->
			<form onsubmit={handleSubmit} class="space-y-5">
				<!-- Error message -->
				{#if error}
					<div
						class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-400"
					>
						<div class="flex items-start gap-2">
							<svg class="mt-0.5 h-4 w-4 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
								<path
									fill-rule="evenodd"
									d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
									clip-rule="evenodd"
								/>
							</svg>
							<span>{error}</span>
						</div>
					</div>
				{/if}

				<!-- Vault Name -->
				<div>
					<label
						for="vault-name"
						class="mb-1.5 block text-sm font-medium text-obsidian-700 dark:text-obsidian-300"
					>
						Vault Name
					</label>
					<input
						id="vault-name"
						type="text"
						bind:value={name}
						placeholder="My Obsidian Vault"
						class="w-full rounded-lg border border-obsidian-200 bg-white px-3 py-2 text-obsidian-900 placeholder-obsidian-400 transition-colors focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20 dark:border-obsidian-700 dark:bg-obsidian-800 dark:text-obsidian-100 dark:placeholder-obsidian-500"
						disabled={loading}
						required
					/>
					{#if nameError}
						<p class="mt-1 text-xs text-red-500">{nameError}</p>
					{/if}
				</div>

				<!-- Repository URL -->
				<div>
					<label
						for="repo-url"
						class="mb-1.5 block text-sm font-medium text-obsidian-700 dark:text-obsidian-300"
					>
						Repository URL
					</label>
					<input
						id="repo-url"
						type="url"
						bind:value={repoUrl}
						placeholder="https://github.com/username/vault-repo"
						class="w-full rounded-lg border border-obsidian-200 bg-white px-3 py-2 text-obsidian-900 placeholder-obsidian-400 transition-colors focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20 dark:border-obsidian-700 dark:bg-obsidian-800 dark:text-obsidian-100 dark:placeholder-obsidian-500"
						disabled={loading}
						required
					/>
					{#if urlError()}
						<p class="mt-1 text-xs text-red-500">{urlError()}</p>
					{/if}
					<p class="mt-1 text-xs text-obsidian-500">HTTPS URL of your GitHub or GitLab repository</p>
				</div>

				<!-- Deploy Token -->
				<div>
					<label
						for="deploy-token"
						class="mb-1.5 block text-sm font-medium text-obsidian-700 dark:text-obsidian-300"
					>
						Deploy Token
					</label>
					<input
						id="deploy-token"
						type="password"
						bind:value={token}
						placeholder="ghp_xxxxxxxxxxxx"
						class="w-full rounded-lg border border-obsidian-200 bg-white px-3 py-2 font-mono text-sm text-obsidian-900 placeholder-obsidian-400 transition-colors focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20 dark:border-obsidian-700 dark:bg-obsidian-800 dark:text-obsidian-100 dark:placeholder-obsidian-500"
						disabled={loading}
						required
					/>
					{#if tokenError}
						<p class="mt-1 text-xs text-red-500">{tokenError}</p>
					{/if}
					<p class="mt-1 text-xs text-obsidian-500">
						GitHub Personal Access Token or Deploy Key with read access
					</p>
				</div>

				<!-- Auto-refresh toggle -->
				<div class="rounded-lg border border-obsidian-200 p-4 dark:border-obsidian-700">
					<label class="flex cursor-pointer items-center gap-3">
						<input
							type="checkbox"
							bind:checked={enableRefresh}
							class="h-4 w-4 rounded border-obsidian-300 text-accent-600 focus:ring-accent-500 dark:border-obsidian-600"
							disabled={loading}
						/>
						<div>
							<span class="text-sm font-medium text-obsidian-700 dark:text-obsidian-300">
								Enable auto-sync
							</span>
							<p class="text-xs text-obsidian-500">Automatically pull updates at regular intervals</p>
						</div>
					</label>

					{#if enableRefresh}
						<div class="mt-4">
							<label
								for="refresh-interval"
								class="mb-1.5 block text-sm font-medium text-obsidian-700 dark:text-obsidian-300"
							>
								Sync Interval (minutes)
							</label>
							<input
								id="refresh-interval"
								type="number"
								bind:value={refreshInterval}
								min="1"
								max="1440"
								placeholder="60"
								class="w-full rounded-lg border border-obsidian-200 bg-white px-3 py-2 text-obsidian-900 placeholder-obsidian-400 transition-colors focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20 dark:border-obsidian-700 dark:bg-obsidian-800 dark:text-obsidian-100 dark:placeholder-obsidian-500"
								disabled={loading}
							/>
							<p class="mt-1 text-xs text-obsidian-500">
								Enter a value between 1 and 1440 minutes (24 hours)
							</p>
						</div>
					{/if}
				</div>

				<!-- Actions -->
				<div class="flex justify-end gap-3 pt-2">
					<button
						type="button"
						class="rounded-lg px-4 py-2 text-sm font-medium text-obsidian-700 transition-colors hover:bg-obsidian-100 dark:text-obsidian-300 dark:hover:bg-obsidian-800"
						onclick={handleClose}
						disabled={loading}
					>
						Cancel
					</button>
					<button
						type="submit"
						class="flex items-center gap-2 rounded-lg bg-accent-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-700 disabled:cursor-not-allowed disabled:opacity-50"
						disabled={!isValid || loading}
					>
						{#if loading}
							<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24">
								<circle
									class="opacity-25"
									cx="12"
									cy="12"
									r="10"
									stroke="currentColor"
									stroke-width="4"
									fill="none"
								/>
								<path
									class="opacity-75"
									fill="currentColor"
									d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
								/>
							</svg>
							<span>Cloning...</span>
						{:else}
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M12 4v16m8-8H4"
								/>
							</svg>
							<span>Add Vault</span>
						{/if}
					</button>
				</div>
			</form>
		</div>
	</div>
	</Portal>
{/if}

