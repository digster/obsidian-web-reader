<script lang="ts">
	import { page } from '$app/stores';
	import { vault, isAuthenticated } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { NoteContent } from '$lib/components';

	let loading = $state(true);
	let error = $state<string | null>(null);

	// Get the note path from the URL
	let notePath = $derived($page.params.path);

	// Load the note when path changes
	$effect(() => {
		if (!$isAuthenticated) {
			goto('/login');
			return;
		}

		if (notePath) {
			loadNote(notePath);
		}
	});

	async function loadNote(path: string) {
		loading = true;
		error = null;

		const note = await vault.loadNote(path);

		if (!note) {
			error = `Note not found: ${path}`;
		}

		loading = false;
	}
</script>

<svelte:head>
	<title>{$vault.currentNote?.title || 'Note'} - Obsidian Reader</title>
</svelte:head>

{#if loading}
	<div class="flex h-64 items-center justify-center">
		<div class="text-center">
			<svg
				class="mx-auto h-8 w-8 animate-spin text-accent-500"
				fill="none"
				viewBox="0 0 24 24"
			>
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
			<p class="mt-2 text-obsidian-500">Loading note...</p>
		</div>
	</div>
{:else if error}
	<div class="mx-auto max-w-2xl">
		<div
			class="rounded-xl border border-red-200 bg-red-50 p-8 text-center dark:border-red-800 dark:bg-red-900/20"
		>
			<svg
				class="mx-auto h-12 w-12 text-red-400"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
			<h2 class="mt-4 text-xl font-semibold text-red-700 dark:text-red-300">Note Not Found</h2>
			<p class="mt-2 text-red-600 dark:text-red-400">{error}</p>
			<button
				type="button"
				class="mt-4 rounded-lg bg-red-100 px-4 py-2 text-sm font-medium text-red-700 transition-colors hover:bg-red-200 dark:bg-red-900/30 dark:text-red-300 dark:hover:bg-red-800/50"
				onclick={() => goto('/')}
			>
				Back to Home
			</button>
		</div>
	</div>
{:else if $vault.currentNote}
	<NoteContent note={$vault.currentNote} />
{/if}

