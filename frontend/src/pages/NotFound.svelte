<script lang="ts">
	import { push } from 'svelte-spa-router';
</script>

<div class="mx-auto max-w-2xl">
	<div
		class="rounded-xl border border-obsidian-200 bg-white p-8 text-center dark:border-obsidian-700 dark:bg-obsidian-900"
	>
		<svg
			class="mx-auto h-16 w-16 text-obsidian-300 dark:text-obsidian-600"
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
		<h1 class="mt-4 text-2xl font-bold text-obsidian-900 dark:text-obsidian-50">
			Page Not Found
		</h1>
		<p class="mt-2 text-obsidian-500 dark:text-obsidian-400">
			The page you're looking for doesn't exist or has been moved.
		</p>
		<button
			type="button"
			class="mt-6 rounded-lg bg-accent-600 px-6 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-700"
			onclick={() => push('/')}
		>
			Go Home
		</button>
	</div>
</div>
