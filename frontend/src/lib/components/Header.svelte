<script lang="ts">
	import { push } from 'svelte-spa-router';
	import SearchBar from './SearchBar.svelte';
	import VaultSelector from './VaultSelector.svelte';
	import ThemeToggle from './ThemeToggle.svelte';
	import { auth } from '../stores';

	interface Props {
		onMenuToggle?: () => void;
	}

	let { onMenuToggle }: Props = $props();

	function handleLogout() {
		// Navigate immediately for responsive UX, logout API call happens in background
		push('/login');
		// Fire and forget - don't await the API call
		auth.logout();
	}
</script>

<header
	class="sticky top-0 z-40 flex h-16 items-center justify-between border-b border-obsidian-200 bg-white/80 px-4 backdrop-blur-sm dark:border-obsidian-700 dark:bg-obsidian-900/80"
>
	<div class="flex items-center gap-4">
		<!-- Mobile menu button -->
		<button
			type="button"
			class="rounded-lg p-2 hover:bg-obsidian-100 dark:hover:bg-obsidian-800 lg:hidden"
			onclick={onMenuToggle}
		>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M4 6h16M4 12h16M4 18h16"
				/>
			</svg>
		</button>

		<!-- Logo -->
		<a href="#/" class="flex items-center gap-2">
			<div
				class="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-accent-500 to-accent-700"
			>
				<svg class="h-5 w-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						stroke-width="2"
						d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
					/>
				</svg>
			</div>
			<span class="hidden font-semibold sm:inline">Obsidian Reader</span>
		</a>
	</div>

	<div class="flex flex-1 items-center justify-center px-4">
		<SearchBar />
	</div>

	<div class="flex items-center gap-2">
		<VaultSelector />
		<ThemeToggle />

		<button
			type="button"
			onclick={handleLogout}
			class="rounded-lg p-2 text-obsidian-500 hover:bg-obsidian-100 hover:text-obsidian-700 dark:text-obsidian-400 dark:hover:bg-obsidian-800 dark:hover:text-obsidian-200"
			title="Logout"
		>
			<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					stroke-width="2"
					d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
				/>
			</svg>
		</button>
	</div>
</header>

