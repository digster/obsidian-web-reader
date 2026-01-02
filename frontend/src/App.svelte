<script lang="ts">
	import Router, { push, location } from 'svelte-spa-router';
	import { onMount } from 'svelte';
	import { auth, isAuthenticated, isAuthLoading, vault } from './lib/stores';
	import Header from './lib/components/Header.svelte';
	import Sidebar from './lib/components/Sidebar.svelte';
	
	// Import pages
	import Login from './pages/Login.svelte';
	import Home from './pages/Home.svelte';
	import Note from './pages/Note.svelte';
	import Search from './pages/Search.svelte';

	// Define routes
	const routes = {
		'/': Home,
		'/login': Login,
		'/note/*': Note,
		'/search': Search
	};

	let sidebarOpen = $state(false);

	// Check auth on mount
	onMount(() => {
		auth.checkStatus();
	});

	// Redirect logic based on auth state
	$effect(() => {
		if ($isAuthLoading) return; // Wait for auth check to complete
		
		const isLoginPage = $location === '/login';
		
		if (!$isAuthenticated && !isLoginPage) {
			push('/login');
		} else if ($isAuthenticated && isLoginPage) {
			push('/');
		}
	});

	// Load vaults when authenticated
	$effect(() => {
		if ($isAuthenticated && !$isAuthLoading) {
			vault.loadVaults();
		}
	});

	function toggleSidebar() {
		sidebarOpen = !sidebarOpen;
	}

	function closeSidebar() {
		sidebarOpen = false;
	}

	// Determine if we should show the full layout
	let showLayout = $derived($location !== '/login' && $isAuthenticated);
</script>

<svelte:head>
	<title>Obsidian Web Reader</title>
</svelte:head>

{#if $isAuthLoading}
	<!-- Loading screen while checking auth -->
	<div class="flex min-h-screen items-center justify-center bg-obsidian-50 dark:bg-obsidian-950">
		<div class="text-center">
			<div class="mx-auto mb-4 h-8 w-8 animate-spin rounded-full border-4 border-accent-200 border-t-accent-600"></div>
			<p class="text-sm text-obsidian-500 dark:text-obsidian-400">Loading...</p>
		</div>
	</div>
{:else if showLayout}
	<!-- Authenticated layout with header and sidebar -->
	<div class="flex h-screen flex-col">
		<Header onMenuToggle={toggleSidebar} />
		<div class="flex flex-1 overflow-hidden">
			<Sidebar open={sidebarOpen} onClose={closeSidebar} />
			<main class="custom-scrollbar flex-1 overflow-y-auto bg-obsidian-50 p-4 dark:bg-obsidian-950 lg:p-8">
				<Router {routes} />
			</main>
		</div>
	</div>
{:else}
	<!-- Login page (full screen, no layout) -->
	<Router {routes} />
{/if}



