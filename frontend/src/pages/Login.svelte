<script lang="ts">
	import { push } from 'svelte-spa-router';
	import { auth, isAuthenticated, isAuthLoading, authError } from '../lib/stores';

	let password = $state('');
	let submitting = $state(false);

	async function handleSubmit(event: Event) {
		event.preventDefault();
		if (!password.trim() || submitting) return;

		submitting = true;
		const success = await auth.login(password);
		submitting = false;

		if (success) {
			push('/');
		}
	}

	// Redirect if already authenticated
	$effect(() => {
		if ($isAuthenticated && !$isAuthLoading) {
			push('/');
		}
	});
</script>

<div
	class="flex min-h-screen items-center justify-center bg-gradient-to-br from-obsidian-100 to-obsidian-200 px-4 py-12 dark:from-obsidian-900 dark:to-obsidian-950"
>
	<div
		class="w-full max-w-md space-y-8 rounded-2xl bg-white p-8 shadow-xl dark:bg-obsidian-800"
	>
		<!-- Logo/Header -->
		<div class="text-center">
			<div
				class="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-gradient-to-br from-accent-500 to-accent-700"
			>
				<svg
					class="h-8 w-8 text-white"
					fill="none"
					viewBox="0 0 24 24"
					stroke="currentColor"
					stroke-width="2"
				>
					<path
						stroke-linecap="round"
						stroke-linejoin="round"
						d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253"
					/>
				</svg>
			</div>
			<h1 class="text-2xl font-bold text-obsidian-900 dark:text-obsidian-50">
				Obsidian Web Reader
			</h1>
			<p class="mt-2 text-sm text-obsidian-600 dark:text-obsidian-400">
				Enter your password to access your vaults
			</p>
		</div>

		<!-- Login Form -->
		<form class="mt-8 space-y-6" onsubmit={handleSubmit}>
			{#if $authError}
				<div
					class="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/30 dark:text-red-400"
				>
					{$authError}
				</div>
			{/if}

			<div>
				<label
					for="password"
					class="block text-sm font-medium text-obsidian-700 dark:text-obsidian-300"
				>
					Password
				</label>
				<input
					id="password"
					name="password"
					type="password"
					autocomplete="current-password"
					required
					bind:value={password}
					class="mt-2 block w-full rounded-lg border border-obsidian-300 bg-white px-4 py-3 text-obsidian-900 placeholder-obsidian-400 focus:border-accent-500 focus:outline-none focus:ring-2 focus:ring-accent-500/20 dark:border-obsidian-600 dark:bg-obsidian-700 dark:text-obsidian-50 dark:placeholder-obsidian-500"
					placeholder="Enter your password"
				/>
			</div>

			<button
				type="submit"
				disabled={submitting || !password.trim()}
				class="flex w-full items-center justify-center rounded-lg bg-accent-600 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-accent-700 focus:outline-none focus:ring-2 focus:ring-accent-500/50 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-accent-500 dark:hover:bg-accent-600"
			>
				{#if submitting}
					<svg
						class="-ml-1 mr-2 h-4 w-4 animate-spin"
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
					Signing in...
				{:else}
					Sign in
				{/if}
			</button>
		</form>
	</div>
</div>



