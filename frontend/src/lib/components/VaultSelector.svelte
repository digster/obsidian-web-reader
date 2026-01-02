<script lang="ts">
	import { vault, activeVault } from '../stores';
	import { vaultApi, type VaultInfo } from '../api';
	import AddVaultModal from './AddVaultModal.svelte';
	import ConfirmModal from './ConfirmModal.svelte';

	let open = $state(false);
	let addModalOpen = $state(false);
	let deleteModalOpen = $state(false);
	let vaultToDelete = $state<VaultInfo | null>(null);
	let deleteLoading = $state(false);
	let syncingVaultId = $state<string | null>(null);

	async function selectVault(vaultId: string) {
		await vault.selectVault(vaultId);
		open = false;
	}

	function handleClickOutside(event: MouseEvent) {
		const target = event.target as HTMLElement;
		if (!target.closest('.vault-selector')) {
			open = false;
		}
	}

	function openAddModal() {
		open = false;
		addModalOpen = true;
	}

	function handleAddSuccess(newVault: VaultInfo) {
		addModalOpen = false;
		vault.loadVaults();
		// Select the newly created vault
		selectVault(newVault.id);
	}

	function openDeleteModal(v: VaultInfo, event: MouseEvent) {
		event.stopPropagation();
		vaultToDelete = v;
		deleteModalOpen = true;
	}

	async function handleDelete() {
		if (!vaultToDelete) return;

		deleteLoading = true;
		try {
			await vaultApi.delete(vaultToDelete.id, true);
			deleteModalOpen = false;
			vaultToDelete = null;
			await vault.loadVaults();
		} catch (e) {
			console.error('Failed to delete vault:', e);
		} finally {
			deleteLoading = false;
		}
	}

	async function handleSync(vaultId: string, event: MouseEvent) {
		event.stopPropagation();
		if (syncingVaultId) return;

		syncingVaultId = vaultId;
		try {
			const result = await vaultApi.sync(vaultId);
			if (!result.success) {
				console.error('Sync failed:', result.message);
			}
		} catch (e) {
			console.error('Sync error:', e);
		} finally {
			syncingVaultId = null;
		}
	}
</script>

<svelte:window onclick={handleClickOutside} />

<div class="vault-selector relative">
	<button
		type="button"
		class="flex items-center gap-2 rounded-lg border border-obsidian-200 bg-white px-3 py-2 text-sm transition-colors hover:bg-obsidian-50 dark:border-obsidian-700 dark:bg-obsidian-800 dark:hover:bg-obsidian-700"
		onclick={() => (open = !open)}
	>
		<svg class="h-4 w-4 text-obsidian-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				stroke-width="2"
				d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z"
			/>
		</svg>
		<span class="max-w-24 truncate">{$activeVault?.name || 'Select Vault'}</span>
		<svg
			class="h-4 w-4 text-obsidian-400 transition-transform"
			class:rotate-180={open}
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
		>
			<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
		</svg>
	</button>

	{#if open}
		<div
			class="absolute right-0 top-full z-50 mt-2 w-72 overflow-hidden rounded-lg border border-obsidian-200 bg-white shadow-lg dark:border-obsidian-700 dark:bg-obsidian-800"
		>
			<div
				class="flex items-center justify-between border-b border-obsidian-200 px-3 py-2 dark:border-obsidian-700"
			>
				<span class="text-xs font-medium uppercase tracking-wider text-obsidian-500">
					Available Vaults
				</span>
				<button
					type="button"
					class="flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-accent-600 transition-colors hover:bg-accent-50 dark:text-accent-400 dark:hover:bg-accent-900/30"
					onclick={openAddModal}
				>
					<svg class="h-3.5 w-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 4v16m8-8H4"
						/>
					</svg>
					Add Vault
				</button>
			</div>
			<ul class="max-h-80 overflow-y-auto">
				{#each $vault.vaults as v}
					<li class="group relative">
						<button
							type="button"
							class="flex w-full items-center gap-3 px-3 py-2.5 text-left transition-colors hover:bg-obsidian-100 dark:hover:bg-obsidian-700 {v.id === $vault.activeVaultId ? 'bg-accent-50 dark:bg-accent-900/30' : ''}"
							onclick={() => selectVault(v.id)}
						>
							<div
								class="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-lg bg-obsidian-100 dark:bg-obsidian-700"
							>
								<svg
									class="h-4 w-4 text-obsidian-600 dark:text-obsidian-300"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z"
									/>
								</svg>
							</div>
							<div class="min-w-0 flex-1">
								<div class="truncate font-medium text-obsidian-900 dark:text-obsidian-100">
									{v.name}
								</div>
								<div class="text-xs text-obsidian-500">
									{v.note_count} notes
								</div>
							</div>
							{#if v.id === $vault.activeVaultId}
								<svg
									class="h-4 w-4 flex-shrink-0 text-accent-600 dark:text-accent-400"
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M5 13l4 4L19 7"
									/>
								</svg>
							{/if}
						</button>

						<!-- Action buttons (shown on hover) -->
						<div
							class="absolute right-2 top-1/2 flex -translate-y-1/2 items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100"
						>
							<!-- Sync button -->
							<button
								type="button"
								class="rounded p-1.5 text-obsidian-500 transition-colors hover:bg-obsidian-200 hover:text-obsidian-700 dark:hover:bg-obsidian-600 dark:hover:text-obsidian-200"
								onclick={(e) => handleSync(v.id, e)}
								title="Sync vault"
								disabled={syncingVaultId === v.id}
							>
								<svg
									class="h-4 w-4"
									class:animate-spin={syncingVaultId === v.id}
									fill="none"
									viewBox="0 0 24 24"
									stroke="currentColor"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
									/>
								</svg>
							</button>

							<!-- Delete button -->
							<button
								type="button"
								class="rounded p-1.5 text-obsidian-500 transition-colors hover:bg-red-100 hover:text-red-600 dark:hover:bg-red-900/30 dark:hover:text-red-400"
								onclick={(e) => openDeleteModal(v, e)}
								title="Delete vault"
							>
								<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										stroke-width="2"
										d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
									/>
								</svg>
							</button>
						</div>
					</li>
				{:else}
					<li class="px-3 py-6 text-center text-sm text-obsidian-500">
						No vaults configured.
						<button
							type="button"
							class="mt-2 block w-full text-accent-600 hover:underline dark:text-accent-400"
							onclick={openAddModal}
						>
							Add your first vault
						</button>
					</li>
				{/each}
			</ul>
		</div>
	{/if}
</div>

<!-- Add Vault Modal -->
<AddVaultModal
	bind:open={addModalOpen}
	onClose={() => (addModalOpen = false)}
	onSuccess={handleAddSuccess}
/>

<!-- Delete Confirmation Modal -->
<ConfirmModal
	bind:open={deleteModalOpen}
	title="Delete Vault"
	message="Are you sure you want to delete '{vaultToDelete?.name}'? This will remove the vault and all its files from the server."
	confirmText="Delete Vault"
	variant="danger"
	loading={deleteLoading}
	onConfirm={handleDelete}
	onCancel={() => {
		deleteModalOpen = false;
		vaultToDelete = null;
	}}
/>
