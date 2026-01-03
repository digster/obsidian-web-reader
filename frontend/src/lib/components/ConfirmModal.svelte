<script lang="ts">
	interface Props {
		open: boolean;
		title: string;
		message: string;
		confirmText?: string;
		cancelText?: string;
		variant?: 'danger' | 'warning' | 'info';
		loading?: boolean;
		onConfirm: () => void;
		onCancel: () => void;
	}

	let {
		open = $bindable(),
		title,
		message,
		confirmText = 'Confirm',
		cancelText = 'Cancel',
		variant = 'danger',
		loading = false,
		onConfirm,
		onCancel
	}: Props = $props();

	const variantStyles = {
		danger: {
			icon: 'text-red-500',
			button: 'bg-red-600 hover:bg-red-700 focus:ring-red-500'
		},
		warning: {
			icon: 'text-amber-500',
			button: 'bg-amber-600 hover:bg-amber-700 focus:ring-amber-500'
		},
		info: {
			icon: 'text-blue-500',
			button: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500'
		}
	};

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Escape' && !loading) {
			onCancel();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

{#if open}
	<!-- Backdrop -->
	<div
		class="fixed inset-0 z-[100] flex items-center justify-center overflow-y-auto bg-black/50 p-4 backdrop-blur-sm"
		onclick={(e) => e.target === e.currentTarget && !loading && onCancel()}
		role="dialog"
		aria-modal="true"
		aria-labelledby="confirm-title"
	>
		<!-- Modal -->
		<div
			class="relative my-auto w-full max-w-md rounded-xl border border-obsidian-200 bg-white p-6 shadow-2xl dark:border-obsidian-700 dark:bg-obsidian-900"
		>
			<div class="flex items-start gap-4">
				<!-- Icon -->
				<div
					class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-obsidian-100 dark:bg-obsidian-800"
				>
					{#if variant === 'danger'}
						<svg
							class="h-5 w-5 {variantStyles[variant].icon}"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
							/>
						</svg>
					{:else if variant === 'warning'}
						<svg
							class="h-5 w-5 {variantStyles[variant].icon}"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
							/>
						</svg>
					{:else}
						<svg
							class="h-5 w-5 {variantStyles[variant].icon}"
							fill="none"
							viewBox="0 0 24 24"
							stroke="currentColor"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								stroke-width="2"
								d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
							/>
						</svg>
					{/if}
				</div>

				<!-- Content -->
				<div class="flex-1">
					<h3
						id="confirm-title"
						class="text-lg font-semibold text-obsidian-900 dark:text-obsidian-100"
					>
						{title}
					</h3>
					<p class="mt-2 text-sm text-obsidian-600 dark:text-obsidian-400">
						{message}
					</p>
				</div>
			</div>

			<!-- Actions -->
			<div class="mt-6 flex justify-end gap-3">
				<button
					type="button"
					class="rounded-lg px-4 py-2 text-sm font-medium text-obsidian-700 transition-colors hover:bg-obsidian-100 dark:text-obsidian-300 dark:hover:bg-obsidian-800"
					onclick={onCancel}
					disabled={loading}
				>
					{cancelText}
				</button>
				<button
					type="button"
					class="flex items-center gap-2 rounded-lg px-4 py-2 text-sm font-medium text-white transition-colors disabled:cursor-not-allowed disabled:opacity-50 {variantStyles[
						variant
					].button}"
					onclick={onConfirm}
					disabled={loading}
				>
					{#if loading}
						<svg class="h-4 w-4 animate-spin" viewBox="0 0 24 24">
							<circle
								class="opacity-25"
								cx="12"
								cy="12"
								r="10"
								stroke="currentColor"
								stroke-width="4"
								fill="none"
							/>
							<path
								class="opacity-75"
								fill="currentColor"
								d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
							/>
						</svg>
					{/if}
					<span>{confirmText}</span>
				</button>
			</div>
		</div>
	</div>
{/if}

