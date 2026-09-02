import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Tailwind-aware class name merger to keep UI components tidy.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
