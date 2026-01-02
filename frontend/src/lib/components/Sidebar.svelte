<script lang="ts">
	import { vault } from '../stores';
	import FileTree from './FileTree.svelte';

	interface Props {
		open?: boolean;
		onClose?: () => void;
	}

	let { open = true, onClose }: Props = $props();
</script>

<!-- Mobile overlay -->
{#if open}
	<div
		class="fixed inset-0 z-40 bg-black/50 lg:hidden"
		onclick={onClose}
		role="button"
		tabindex="-1"
		onkeydown={(e) => e.key === 'Escape' && onClose?.()}
	></div>
{/if}

<!-- Sidebar -->
<aside
	class="fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-obsidian-200 bg-white transition-transform duration-300 dark:border-obsidian-700 dark:bg-obsidian-900 lg:static lg:z-auto lg:translate-x-0"
	class:translate-x-0={open}
	class:-translate-x-full={!open}
>
	<div class="flex h-16 items-center justify-between border-b border-obsidian-200 px-4 dark:border-obsidian-700 lg:hidden">
		<span class="font-semibold">Files</span>
		<button
			type="button"
			class="rounded-lg p-2 hover:bg-obsidian-100 dark:hover:bg-obsidian-800"
			onclick={onClose}
		>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
			</svg>
		</button>
	</div>

	<div class="custom-scrollbar flex-1 overflow-y-auto p-4">
		{#if $vault.loading}
			<div class="flex items-center justify-center py-8">
				<svg class="h-6 w-6 animate-spin text-obsidian-400" fill="none" viewBox="0 0 24 24">
					<circle
						class="opacity-25"
						cx="12"
						cy="12"
						r="10"
						stroke="currentColor"
						stroke-width="4"
					></circle>
					<path
						class="opacity-75"
						fill="currentColor"
						d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
					></path>
				</svg>
			</div>
		{:else if $vault.fileTree.length === 0}
			<div class="py-8 text-center text-sm text-obsidian-500">
				<svg class="mx-auto mb-2 h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
					/>
				</svg>
				<p>No files found</p>
				<p class="mt-1 text-xs">Select a vault to browse files</p>
			</div>
		{:else}
			<FileTree items={$vault.fileTree} />
		{/if}
	</div>
</aside>

