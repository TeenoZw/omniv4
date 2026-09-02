<script lang="ts">
	import { DropdownMenu as DropdownMenuPrimitive } from "bits-ui";
	import { cn } from "$lib/utils.js";
	import Icon from "$lib/components/ui/Icon.svelte";
	import { faChevronRight } from "@fortawesome/free-solid-svg-icons";

	let {
		ref = $bindable(null),
		class: className,
		inset,
		children,
		...restProps
	}: DropdownMenuPrimitive.SubTriggerProps & {
		inset?: boolean;
	} = $props();
</script>

<DropdownMenuPrimitive.SubTrigger
	bind:ref
	class={cn(
		"data-[highlighted]:bg-accent data-[state=open]:bg-accent flex cursor-default select-none items-center gap-2 rounded-sm px-2 py-1.5 text-sm outline-none [&_svg]:pointer-events-none [&_svg]:size-4 [&_svg]:shrink-0",
		inset && "pl-8",
		className
	)}
	{...restProps}
>
	{@render children?.()}
	<Icon icon={faChevronRight} className="ml-auto size-4" />
</DropdownMenuPrimitive.SubTrigger>
