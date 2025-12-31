<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { auth, isAuthenticated, isAuthLoading, vault } from '$lib/stores';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { Header, Sidebar } from '$lib/components';

	let { children } = $props();
	let sidebarOpen = $state(false);

	// Determine if we should show the full layout (with header/sidebar)
	let showLayout = $derived($page.url.pathname !== '/login');

	onMount(async () => {
		// Check auth status on mount
		const authenticated = await auth.checkStatus();

		if (authenticated) {
			// Load vaults if authenticated
			await vault.loadVaults();
		} else if ($page.url.pathname !== '/login') {
			// Redirect to login if not authenticated and not already on login page
			goto('/login');
		}
	});

	// Watch for auth changes
	$effect(() => {
		if (!$isAuthLoading && !$isAuthenticated && $page.url.pathname !== '/login') {
			goto('/login');
		}
	});

	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}

	function closeSidebar() {
		sidebarOpen = false;
	}
</script>

{#if showLayout && $isAuthenticated}
	<div class="flex h-screen flex-col">
		<Header onMenuToggle={toggleSidebar} />

		<div class="flex flex-1 overflow-hidden">
			<Sidebar open={sidebarOpen} onClose={closeSidebar} />

			<main class="custom-scrollbar flex-1 overflow-y-auto bg-obsidian-50 p-4 dark:bg-obsidian-950 lg:p-8">
				{@render children()}
			</main>
		</div>
	</div>
{:else}
	{@render children()}
{/if}
