<script lang="ts">
	import { onMount } from 'svelte';
	import type { NoteResponse } from '../api';

	interface Props {
		note: NoteResponse;
	}

	let { note }: Props = $props();
	let contentElement: HTMLDivElement;

	onMount(() => {
		// Initialize KaTeX for math rendering
		initMath();
		// Initialize syntax highlighting
		initHighlighting();
	});

	$effect(() => {
		// Re-run when note changes
		if (note && contentElement) {
			initMath();
			initHighlighting();
		}
	});

	async function initMath() {
		if (typeof window === 'undefined' || !contentElement) return;

		try {
			const katex = await import('katex');
			// @ts-ignore - CSS import
			await import('katex/dist/katex.min.css');

			// Render inline math
			contentElement.querySelectorAll('.math-inline').forEach((el) => {
				const math = el.getAttribute('data-math');
				if (math) {
					try {
						katex.default.render(math, el as HTMLElement, {
							throwOnError: false,
							displayMode: false
						});
					} catch (e) {
						console.warn('KaTeX error:', e);
					}
				}
			});

			// Render block math
			contentElement.querySelectorAll('.math-block').forEach((el) => {
				const math = el.getAttribute('data-math');
				if (math) {
					try {
						katex.default.render(math, el as HTMLElement, {
							throwOnError: false,
							displayMode: true
						});
					} catch (e) {
						console.warn('KaTeX error:', e);
					}
				}
			});
		} catch (e) {
			console.warn('Failed to load KaTeX:', e);
		}
	}

	async function initHighlighting() {
		if (typeof window === 'undefined' || !contentElement) return;

		try {
			const hljs = await import('highlight.js');
			// @ts-ignore - CSS import
			await import('highlight.js/styles/github-dark.css');

			contentElement.querySelectorAll('pre code').forEach((el) => {
				hljs.default.highlightElement(el as HTMLElement);
			});
		} catch (e) {
			console.warn('Failed to load highlight.js:', e);
		}
	}

	function formatDate(dateStr: string | null): string {
		if (!dateStr) return '';
		const date = new Date(dateStr);
		return date.toLocaleDateString('en-US', {
			year: 'numeric',
			month: 'long',
			day: 'numeric'
		});
	}
</script>

<article class="mx-auto max-w-3xl">
	<!-- Note Header -->
	<header class="mb-8">
		<h1 class="text-3xl font-bold text-obsidian-900 dark:text-obsidian-50">
			{note.title}
		</h1>

		<div class="mt-4 flex flex-wrap items-center gap-4 text-sm text-obsidian-500">
			{#if note.modified_at}
				<span class="flex items-center gap-1">
					<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							stroke-width="2"
							d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
						/>
					</svg>
					{formatDate(note.modified_at)}
				</span>
			{/if}

			{#if note.tags.length > 0}
				<div class="flex flex-wrap gap-2">
					{#each note.tags as tag}
						<a href="/search?q=tag:{tag}" class="tag">
							#{tag}
						</a>
					{/each}
				</div>
			{/if}
		</div>
	</header>

	<!-- Note Content -->
	<div
		bind:this={contentElement}
		class="prose prose-obsidian dark:prose-invert max-w-none"
	>
		{@html note.content_html}
	</div>

	<!-- Backlinks -->
	{#if note.backlinks.length > 0}
		<footer class="mt-12 border-t border-obsidian-200 pt-8 dark:border-obsidian-700">
			<h2 class="mb-4 text-lg font-semibold text-obsidian-900 dark:text-obsidian-50">
				Backlinks ({note.backlinks.length})
			</h2>
			<ul class="space-y-2">
				{#each note.backlinks as backlink}
					<li>
					<a
						href="#/note/{backlink.path}"
						class="flex items-center gap-2 text-accent-600 hover:underline dark:text-accent-400"
					>
							<svg class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
								<path
									stroke-linecap="round"
									stroke-linejoin="round"
									stroke-width="2"
									d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
								/>
							</svg>
							{backlink.title}
						</a>
					</li>
				{/each}
			</ul>
		</footer>
	{/if}
</article>

