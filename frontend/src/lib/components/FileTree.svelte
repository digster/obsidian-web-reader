<script lang="ts">
	import { location } from 'svelte-spa-router';
	import type { FileTreeItem } from '../api';

	interface Props {
		items: FileTreeItem[];
		level?: number;
	}

	let { items, level = 0 }: Props = $props();

	// Track expanded folders
	let expandedFolders = $state<Set<string>>(new Set());

	function toggleFolder(path: string) {
		if (expandedFolders.has(path)) {
			expandedFolders.delete(path);
		} else {
			expandedFolders.add(path);
		}
		expandedFolders = new Set(expandedFolders); // Trigger reactivity
	}

	function isActive(path: string): boolean {
		const currentPath = $location;
		return currentPath === `/note/${path}` || currentPath === `/note/${path}.md`;
	}
</script>

<ul class="space-y-0.5" style="padding-left: {level > 0 ? '0.75rem' : '0'}">
	{#each items as item}
		<li>
			{#if item.type === 'folder'}
				<button
					type="button"
					class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition-colors hover:bg-obsidian-100 dark:hover:bg-obsidian-800"
					onclick={() => toggleFolder(item.path)}
				>
					<svg
						class="h-4 w-4 text-obsidian-400 transition-transform"
						class:rotate-90={expandedFolders.has(item.path)}
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 5l7 7-7 7"
						/>
					</svg>
					<svg
						class="h-4 w-4"
						class:text-accent-500={expandedFolders.has(item.path)}
						class:text-obsidian-400={!expandedFolders.has(item.path)}
						fill="none"
						viewBox="0 0 24 24"
						stroke="currentColor"
					>
						{#if expandedFolders.has(item.path)}
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M5 19a2 2 0 01-2-2V7a2 2 0 012-2h4l2 2h4a2 2 0 012 2v1M5 19h14a2 2 0 002-2v-5a2 2 0 00-2-2H9a2 2 0 00-2 2v5a2 2 0 01-2 2z"
							/>
						{:else}
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
							/>
						{/if}
					</svg>
					<span class="truncate text-obsidian-700 dark:text-obsidian-300">{item.name}</span>
				</button>
				{#if expandedFolders.has(item.path) && item.children}
					<svelte:self items={item.children} level={level + 1} />
				{/if}
			{:else}
				<a
					href="#/note/{item.path.replace('.md', '')}"
					class="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition-colors hover:bg-obsidian-100 dark:hover:bg-obsidian-800"
					class:bg-accent-100={isActive(item.path)}
					class:dark:bg-accent-900={isActive(item.path)}
					class:text-accent-700={isActive(item.path)}
					class:dark:text-accent-300={isActive(item.path)}
				>
					<svg class="h-4 w-4 flex-shrink-0 text-obsidian-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
						/>
					</svg>
					<span class="truncate text-obsidian-700 dark:text-obsidian-300">{item.name}</span>
				</a>
			{/if}
		</li>
	{/each}
</ul>

