<script lang="ts">
	import { vault, activeVault } from '../lib/stores';
</script>

<div class="mx-auto max-w-4xl">
	<!-- Welcome Section -->
	<div class="mb-8 rounded-2xl bg-gradient-to-br from-accent-500 to-accent-700 p-8 text-white">
		<h1 class="text-3xl font-bold">Welcome to Obsidian Reader</h1>
		<p class="mt-2 text-accent-100">
			{#if $activeVault}
				Currently viewing: <strong>{$activeVault.name}</strong> ({$activeVault.note_count} notes)
			{:else}
				Select a vault from the dropdown to get started.
			{/if}
		</p>
	</div>

	<!-- Quick Stats -->
	{#if $activeVault}
		<div class="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			<div class="rounded-xl bg-white p-6 shadow-sm dark:bg-obsidian-800">
				<div class="flex items-center gap-4">
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-accent-100 dark:bg-accent-900/30"
					>
						<svg
							class="h-6 w-6 text-accent-600 dark:text-accent-400"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
							/>
						</svg>
					</div>
					<div>
						<div class="text-2xl font-bold text-obsidian-900 dark:text-obsidian-50">
							{$activeVault.note_count}
						</div>
						<div class="text-sm text-obsidian-500">Notes</div>
					</div>
				</div>
			</div>

			<div class="rounded-xl bg-white p-6 shadow-sm dark:bg-obsidian-800">
				<div class="flex items-center gap-4">
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-green-100 dark:bg-green-900/30"
					>
						<svg
							class="h-6 w-6 text-green-600 dark:text-green-400"
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
					<div>
						<div class="text-2xl font-bold text-obsidian-900 dark:text-obsidian-50">
							{$vault.vaults.length}
						</div>
						<div class="text-sm text-obsidian-500">Vaults</div>
					</div>
				</div>
			</div>

			<div class="rounded-xl bg-white p-6 shadow-sm dark:bg-obsidian-800 sm:col-span-2 lg:col-span-1">
				<div class="flex items-center gap-4">
					<div
						class="flex h-12 w-12 items-center justify-center rounded-lg bg-purple-100 dark:bg-purple-900/30"
					>
						<svg
							class="h-6 w-6 text-purple-600 dark:text-purple-400"
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
					</div>
					<div>
						<div class="text-sm font-medium text-obsidian-900 dark:text-obsidian-50">
							Full-Text Search
						</div>
						<div class="text-sm text-obsidian-500">Search across all notes</div>
					</div>
				</div>
			</div>
		</div>
	{/if}

	<!-- Getting Started -->
	<div class="rounded-xl bg-white p-6 shadow-sm dark:bg-obsidian-800">
		<h2 class="mb-4 text-xl font-semibold text-obsidian-900 dark:text-obsidian-50">
			Getting Started
		</h2>
		<ul class="space-y-3 text-obsidian-600 dark:text-obsidian-400">
			<li class="flex items-start gap-3">
				<span
					class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-accent-100 text-xs font-medium text-accent-700 dark:bg-accent-900/30 dark:text-accent-300"
				>
					1
				</span>
				<span>Select a vault from the dropdown in the header</span>
			</li>
			<li class="flex items-start gap-3">
				<span
					class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-accent-100 text-xs font-medium text-accent-700 dark:bg-accent-900/30 dark:text-accent-300"
				>
					2
				</span>
				<span>Browse notes using the sidebar file tree</span>
			</li>
			<li class="flex items-start gap-3">
				<span
					class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-accent-100 text-xs font-medium text-accent-700 dark:bg-accent-900/30 dark:text-accent-300"
				>
					3
				</span>
				<span>Use the search bar to find notes quickly</span>
			</li>
			<li class="flex items-start gap-3">
				<span
					class="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full bg-accent-100 text-xs font-medium text-accent-700 dark:bg-accent-900/30 dark:text-accent-300"
				>
					4
				</span>
				<span>Click on [[wiki links]] to navigate between notes</span>
			</li>
		</ul>
	</div>
</div>

