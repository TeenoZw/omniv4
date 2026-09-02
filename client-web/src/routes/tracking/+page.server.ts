import { redirect } from "@sveltejs/kit";

export const load = () => {
  throw redirect(302, "https://hosting.wialon.eu/?lang=en");
};
