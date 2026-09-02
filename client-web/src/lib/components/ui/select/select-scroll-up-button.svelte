<script lang="ts">
	import { Select as SelectPrimitive, type WithoutChildrenOrChild } from "bits-ui";
	import { cn } from "$lib/utils.js";
	import Icon from "$lib/components/ui/Icon.svelte";
	import { faChevronUp } from "@fortawesome/free-solid-svg-icons";

	let {
		ref = $bindable(null),
		class: className,
		...restProps
	}: WithoutChildrenOrChild<SelectPrimitive.ScrollUpButtonProps> = $props();
</script>

<SelectPrimitive.ScrollUpButton
	bind:ref
	class={cn("flex cursor-default items-center justify-center py-1", className)}
	{...restProps}
>
	<Icon icon={faChevronUp} className="size-4" />
</SelectPrimitive.ScrollUpButton>
