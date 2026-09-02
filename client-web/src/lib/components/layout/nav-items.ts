import type { IconDefinition } from "@fortawesome/fontawesome-svg-core";
import {
  faGaugeSimpleHigh,
  faCreditCard,
  faHeadset,
  faPuzzlePiece,
  faShieldHalved,
  faGear,
} from "@fortawesome/free-solid-svg-icons";

export type NavItem = {
  title: string;
  href: string;
  icon: IconDefinition;
  badge?: string;
};

export const mainNav: NavItem[] = [
  {
    title: "Dashboard",
    href: "/app",
    icon: faGaugeSimpleHigh,
  },
  {
    title: "Billing",
    href: "/app/billing",
    icon: faCreditCard,
  },
  {
    title: "Support",
    href: "/app/support",
    icon: faHeadset,
  },
];

export const secondaryNav: NavItem[] = [
  {
    title: "Integrations",
    href: "/app/integrations",
    icon: faPuzzlePiece,
  },
  {
    title: "Security",
    href: "/app/security",
    icon: faShieldHalved,
  },
  {
    title: "Settings",
    href: "/app/settings",
    icon: faGear,
  },
];
