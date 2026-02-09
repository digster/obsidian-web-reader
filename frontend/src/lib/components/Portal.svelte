<script lang="ts">
	import { onMount } from 'svelte';

	interface Props {
		children: import('svelte').Snippet;
	}

	let { children }: Props = $props();

	let container: HTMLDivElement;

	onMount(() => {
		// Move the container to body
		document.body.appendChild(container);

		// Lock body scroll while modal is open
		const previousOverflow = document.body.style.overflow;
		document.body.style.overflow = 'hidden';

		return () => {
			// Restore body scroll
			document.body.style.overflow = previousOverflow;
			// Clean up when component is destroyed
			if (container && container.parentNode === document.body) {
				document.body.removeChild(container);
			}
		};
	});
</script>

<div bind:this={container} class="portal-container">
	{@render children()}
</div>

<style>
	.portal-container {
		display: contents;
	}
</style>
