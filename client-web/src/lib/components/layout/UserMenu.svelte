<script lang="ts">
  import { goto } from "$app/navigation";
  import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuLabel,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
  } from "$lib/components/ui/dropdown-menu";
  import { Avatar, AvatarFallback } from "$lib/components/ui/avatar";
  import { buttonVariants } from "$lib/components/ui/button";
  import Icon from "$lib/components/ui/Icon.svelte";
  import { cn } from "$lib/utils.js";
  import { faRightFromBracket, faGear, faUserGear } from "@fortawesome/free-solid-svg-icons";
  import { clearSession, sessionStore } from "$lib/api/session";
  import { logout } from "$lib/api/auth";

  $: session = $sessionStore;
  $: signedInEmail = session?.userEmail ?? "omni.user@omnilogistics.co.zw";
  $: initials = signedInEmail.slice(0, 2).toUpperCase();

  async function handleSignOut() {
    try {
      await logout(session?.refreshToken);
    } catch (error) {
      // Clear local session even if the remote logout call fails.
    }
    clearSession();
    await goto("/login");
  }
</script>

<DropdownMenu>
  <DropdownMenuTrigger class={cn(buttonVariants({ variant: "ghost", size: "icon" }), "h-9 w-9 rounded-full p-0")}>
    <Avatar class="h-9 w-9 border">
      <AvatarFallback class="text-sm">{initials}</AvatarFallback>
    </Avatar>
    <span class="sr-only">Open user menu</span>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end" class="w-56">
    <DropdownMenuLabel class="text-xs text-muted-foreground">
      Signed in as
      <span class="block text-sm font-semibold text-foreground">{signedInEmail}</span>
    </DropdownMenuLabel>
    <DropdownMenuSeparator />
    <DropdownMenuItem class="flex items-center gap-2">
      <Icon icon={faUserGear} className="h-4 w-4" />
      Manage Profile
    </DropdownMenuItem>
    <DropdownMenuItem class="flex items-center gap-2">
      <Icon icon={faGear} className="h-4 w-4" />
      Workspace Settings
    </DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem class="flex items-center gap-2 text-destructive" onSelect={handleSignOut}>
      <Icon icon={faRightFromBracket} className="h-4 w-4" />
      Sign out
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
