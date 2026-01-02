<script lang="ts">
	import { push } from 'svelte-spa-router';
	import { searchApi, type SearchResult } from '../api';

	let query = $state('');
	let results = $state<SearchResult[]>([]);
	let showResults = $state(false);
	let loading = $state(false);
	let debounceTimer: ReturnType<typeof setTimeout>;

	async function handleSearch() {
		if (!query.trim()) {
			results = [];
			return;
		}

		loading = true;
		try {
			const response = await searchApi.search(query);
			results = response.results;
		} catch (e) {
			results = [];
		}
		loading = false;
	}

	function handleInput() {
		clearTimeout(debounceTimer);
		if (query.trim().length > 1) {
			debounceTimer = setTimeout(handleSearch, 300);
			showResults = true;
		} else {
			results = [];
			showResults = false;
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && query.trim()) {
			push(`/search?q=${encodeURIComponent(query)}`);
			showResults = false;
		} else if (event.key === 'Escape') {
			showResults = false;
		}
	}

	function selectResult(path: string) {
		push(`/note/${path}`);
		showResults = false;
		query = '';
		results = [];
	}

	function handleBlur() {
		// Delay to allow click on results
		setTimeout(() => {
			showResults = false;
		}, 200);
	}
</script>

<div class="relative w-full max-w-md">
	<div class="relative">
		<input
			type="text"
			bind:value={query}
			oninput={handleInput}
			onkeydown={handleKeydown}
			onfocus={() => query.trim() && (showResults = true)}
			onblur={handleBlur}
			placeholder="Search notes..."
			class="w-full rounded-lg border border-obsidian-200 bg-obsidian-50 py-2 pl-10 pr-4 text-sm transition-colors placeholder:text-obsidian-400 focus:border-accent-500 focus:bg-white focus:outline-none focus:ring-2 focus:ring-accent-500/20 dark:border-obsidian-700 dark:bg-obsidian-800 dark:placeholder:text-obsidian-500 dark:focus:bg-obsidian-700"
		/>
		<div class="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3">
			{#if loading}
				<svg class="h-4 w-4 animate-spin text-obsidian-400" fill="none" viewBox="0 0 24 24">
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
			{:else}
				<svg class="h-4 w-4 text-obsidian-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
					/>
				</svg>
			{/if}
		</div>
	</div>

	<!-- Search Results Dropdown -->
	{#if showResults && results.length > 0}
		<div
			class="absolute top-full z-50 mt-2 w-full overflow-hidden rounded-lg border border-obsidian-200 bg-white shadow-lg dark:border-obsidian-700 dark:bg-obsidian-800"
		>
			<ul class="max-h-80 overflow-y-auto">
				{#each results.slice(0, 8) as result}
					<li>
						<button
							type="button"
							class="w-full px-4 py-3 text-left transition-colors hover:bg-obsidian-100 dark:hover:bg-obsidian-700"
							onclick={() => selectResult(result.path)}
						>
							<div class="font-medium text-obsidian-900 dark:text-obsidian-100">
								{result.title}
							</div>
							<div
								class="mt-1 line-clamp-2 text-sm text-obsidian-500 dark:text-obsidian-400"
							>
								{@html result.snippet}
							</div>
						</button>
					</li>
				{/each}
			</ul>
			{#if results.length > 8}
				<div class="border-t border-obsidian-200 px-4 py-2 dark:border-obsidian-700">
					<button
						type="button"
						class="text-sm text-accent-600 hover:text-accent-700 dark:text-accent-400"
						onclick={() => push(`/search?q=${encodeURIComponent(query)}`)}
					>
						View all {results.length} results →
					</button>
				</div>
			{/if}
		</div>
	{/if}
</div>

