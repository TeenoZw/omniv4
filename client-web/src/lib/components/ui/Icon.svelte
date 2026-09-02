<script lang="ts">
  import { FontAwesomeIcon } from "@fortawesome/svelte-fontawesome";
  import type { IconDefinition, SizeProp, FlipProp, RotateProp } from "@fortawesome/fontawesome-svg-core";
  import { cn } from "$lib/utils.js";

  export let icon: IconDefinition;
  export let size: SizeProp | undefined = undefined;
  export let className = "";
  export let title: string | undefined = undefined;
  export let spin = false;
  export let pulse = false;
  export let rotation: RotateProp | undefined = undefined;
  export let flip: FlipProp | undefined = undefined;
  export let fixedWidth = false;
  export let style: string | undefined = undefined;
</script>

<FontAwesomeIcon
  {icon}
  {size}
  {spin}
  {pulse}
  {rotation}
  {flip}
  {fixedWidth}
  class={cn("text-inherit", className)}
  {title}
  {style}
/>
