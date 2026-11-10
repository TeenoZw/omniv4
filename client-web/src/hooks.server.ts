import { redirect, type Handle } from "@sveltejs/kit";

const PRODUCTION_HOSTS: Record<string, string> = {
  "v4.omnilogistics.co.zw": "www.omnilogistics.co.zw",
  "portal-v4.omnilogistics.co.zw": "portal.omnilogistics.co.zw",
};

export const handle: Handle = async ({ event, resolve }) => {
  const productionHost = PRODUCTION_HOSTS[event.url.hostname];
  if (productionHost) {
    const destination = new URL(event.url);
    destination.hostname = productionHost;
    throw redirect(308, destination.toString());
  }

  return resolve(event);
};
