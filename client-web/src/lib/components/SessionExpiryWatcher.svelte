<script lang="ts">
  import { goto } from "$app/navigation";
  import { onDestroy } from "svelte";
  import { Button } from "$lib/components/ui/button";
  import { clearSession, extendSession, forceExpiryCountdown, getSession, sessionStore } from "$lib/api/session";
  import { logout } from "$lib/api/auth";

  export let warningWindowMs = 60000;
  export let intervalMs = 1000;

  type SessionState = {
    token?: string | null;
    refreshToken?: string | null;
    expiresAt?: string | null;
    forceLogoutCountdown?: boolean;
  } | null;

  let session: SessionState = null;
  let remainingMs: number | null = null;
  let showPrompt = false;
  let ticker: ReturnType<typeof setInterval> | null = null;
  let isForcedLogout = false;

  const unsubscribe = sessionStore.subscribe((value) => {
    session = value;
    isForcedLogout = Boolean(value?.forceLogoutCountdown);
    if (!session?.token || !session?.expiresAt) {
      hidePrompt();
      return;
    }
    ensureTicker();
    updateRemaining();
  });

  function ensureTicker() {
    if (ticker !== null) return;
    ticker = setInterval(updateRemaining, intervalMs);
  }

  function stopTicker() {
    if (ticker === null) return;
    clearInterval(ticker);
    ticker = null;
  }

  function hidePrompt() {
    showPrompt = false;
    remainingMs = null;
    stopTicker();
  }

  async function expireSession() {
    const current = getSession();
    try {
      if (current?.refreshToken) {
        await logout(current.refreshToken);
      }
    } catch {
      // Local logout still proceeds if the backend logout call fails.
    }
    clearSession();
    await goto("/login");
  }

  function updateRemaining() {
    if (!session?.token || !session?.expiresAt) {
      hidePrompt();
      return;
    }

    const expiresAt = Date.parse(session.expiresAt);
    if (Number.isNaN(expiresAt)) {
      forceExpiryCountdown();
      return;
    }

    remainingMs = expiresAt - Date.now();
    if (remainingMs <= 0) {
      hidePrompt();
      void expireSession();
      return;
    }

    showPrompt = remainingMs <= warningWindowMs;
  }

  function staySignedIn() {
    if (isForcedLogout) {
      void signOutNow();
      return;
    }
    extendSession();
    showPrompt = false;
    updateRemaining();
  }

  async function signOutNow() {
    await expireSession();
  }

  function formatRemaining(ms: number | null) {
    if (ms === null) return "--:--";
    const safeMs = Math.max(0, ms);
    const totalSeconds = Math.floor(safeMs / 1000);
    const minutes = String(Math.floor(totalSeconds / 60)).padStart(2, "0");
    const seconds = String(totalSeconds % 60).padStart(2, "0");
    return `${minutes}:${seconds}`;
  }

  onDestroy(() => {
    unsubscribe();
    stopTicker();
  });
</script>

{#if showPrompt && remainingMs !== null}
  <div class="fixed inset-0 z-40 flex items-center justify-center bg-black/60 p-4">
    <div class="w-full max-w-md rounded-2xl border border-border/70 bg-card p-6 text-card-foreground shadow-xl">
      <p class="text-sm font-semibold text-primary">Session ending soon</p>
      <h2 class="mt-1 text-2xl font-bold tracking-tight">We will sign you out shortly</h2>
      <p class="mt-2 text-sm text-muted-foreground">
        For security reasons, inactive sessions automatically close. Select "Stay signed in" to keep your portal access.
      </p>

      <div class="mt-5 rounded-2xl border border-dashed border-border/60 bg-muted/40 px-4 py-6 text-center">
        <p class="text-xs uppercase tracking-[0.3em] text-muted-foreground">Time remaining</p>
        <p class="mt-3 font-mono text-4xl font-semibold text-foreground">{formatRemaining(remainingMs)}</p>
      </div>

      {#if isForcedLogout}
        <p class="mt-4 rounded-md border border-amber-300/60 bg-amber-50 px-4 py-3 text-sm text-amber-900">
          Your session can’t be refreshed. You’ll need to sign in again.
        </p>
      {/if}

      <div class="mt-6 flex flex-wrap gap-3">
        <Button class="flex-1" onclick={() => staySignedIn()} disabled={isForcedLogout}>
          {isForcedLogout ? "Re-authentication required" : "Stay signed in"}
        </Button>
        <Button class="flex-1" variant="outline" onclick={() => signOutNow()}>
          Sign out now
        </Button>
      </div>
    </div>
  </div>
{/if}
