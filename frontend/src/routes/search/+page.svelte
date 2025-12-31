<script lang="ts">
	import { page } from '$app/stores';
	import { searchApi, type SearchResult } from '$lib/api';
	import { isAuthenticated } from '$lib/stores';
	import { goto } from '$app/navigation';

	let results = $state<SearchResult[]>([]);
	let loading = $state(false);
	let error = $state<string | null>(null);

	// Get query from URL
	let query = $derived($page.url.searchParams.get('q') || '');

	// Perform search when query changes
	$effect(() => {
		if (!$isAuthenticated) {
			goto('/login');
			return;
		}

		if (query) {
			performSearch(query);
		} else {
			results = [];
		}
	});

	async function performSearch(q: string) {
		loading = true;
		error = null;

		try {
			const response = await searchApi.search(q);
			results = response.results;
		} catch (e) {
			const err = e as { detail?: string };
			error = err.detail || 'Search failed';
			results = [];
		}

		loading = false;
	}
</script>

<svelte:head>
	<title>Search: {query} - Obsidian Reader</title>
</svelte:head>

<div class="mx-auto max-w-3xl">
	<!-- Search Header -->
	<div class="mb-8">
		<h1 class="text-2xl font-bold text-obsidian-900 dark:text-obsidian-50">
			Search Results
		</h1>
		{#if query}
			<p class="mt-2 text-obsidian-600 dark:text-obsidian-400">
				{#if loading}
					Searching for "<span class="font-medium">{query}</span>"...
				{:else}
					Found {results.length} result{results.length !== 1 ? 's' : ''} for "<span
						class="font-medium">{query}</span
					>"
				{/if}
			</p>
		{/if}
	</div>

	<!-- Loading State -->
	{#if loading}
		<div class="space-y-4">
			{#each Array(3) as _}
				<div class="animate-pulse rounded-xl bg-white p-6 dark:bg-obsidian-800">
					<div class="h-5 w-1/3 rounded bg-obsidian-200 dark:bg-obsidian-700"></div>
					<div class="mt-3 h-4 w-full rounded bg-obsidian-100 dark:bg-obsidian-700"></div>
					<div class="mt-2 h-4 w-2/3 rounded bg-obsidian-100 dark:bg-obsidian-700"></div>
				</div>
			{/each}
		</div>
	{:else if error}
		<!-- Error State -->
		<div
			class="rounded-xl border border-red-200 bg-red-50 p-6 text-center dark:border-red-800 dark:bg-red-900/20"
		>
			<svg
				class="mx-auto h-8 w-8 text-red-400"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
				/>
			</svg>
			<p class="mt-2 text-red-600 dark:text-red-400">{error}</p>
		</div>
	{:else if results.length === 0 && query}
		<!-- No Results -->
		<div
			class="rounded-xl bg-white p-8 text-center shadow-sm dark:bg-obsidian-800"
		>
			<svg
				class="mx-auto h-12 w-12 text-obsidian-300 dark:text-obsidian-600"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
				/>
			</svg>
			<h2 class="mt-4 text-lg font-medium text-obsidian-900 dark:text-obsidian-50">
				No results found
			</h2>
			<p class="mt-2 text-obsidian-500">
				Try adjusting your search terms or check the spelling.
			</p>
		</div>
	{:else if results.length > 0}
		<!-- Results List -->
		<div class="space-y-4">
			{#each results as result}
				<a
					href="/note/{result.path}"
					class="block rounded-xl bg-white p-6 shadow-sm transition-shadow hover:shadow-md dark:bg-obsidian-800"
				>
					<div class="flex items-start justify-between">
						<h2 class="text-lg font-semibold text-obsidian-900 dark:text-obsidian-50">
							{result.title}
						</h2>
						<span
							class="rounded-full bg-obsidian-100 px-2 py-0.5 text-xs text-obsidian-500 dark:bg-obsidian-700"
						>
							{result.score.toFixed(2)}
						</span>
					</div>
					<p class="mt-2 text-sm text-obsidian-500 dark:text-obsidian-400">
						{result.path}
					</p>
					<p
						class="mt-3 text-sm text-obsidian-600 dark:text-obsidian-300"
					>
						{@html result.snippet}
					</p>
				</a>
			{/each}
		</div>
	{:else}
		<!-- Empty State (no query) -->
		<div
			class="rounded-xl bg-white p-8 text-center shadow-sm dark:bg-obsidian-800"
		>
			<svg
				class="mx-auto h-12 w-12 text-obsidian-300 dark:text-obsidian-600"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
				/>
			</svg>
			<h2 class="mt-4 text-lg font-medium text-obsidian-900 dark:text-obsidian-50">
				Enter a search query
			</h2>
			<p class="mt-2 text-obsidian-500">
				Use the search bar above to find notes.
			</p>
		</div>
	{/if}
</div>

