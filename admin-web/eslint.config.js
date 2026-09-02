import js from "@eslint/js";
import globals from "globals";
import svelte from "eslint-plugin-svelte";
import prettier from "eslint-config-prettier";
import tsParser from "@typescript-eslint/parser";
import * as espree from "espree";
import svelteParser from "svelte-eslint-parser";
import tsPlugin from "@typescript-eslint/eslint-plugin";

export default [
  {
    ignores: ["dist", "node_modules", "src/App_old.svelte", "src/lib/components/ui/**"],
  },
  {
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
  },
  {
    files: ["**/*.test.{js,ts}", "**/*.spec.{js,ts}"],
    languageOptions: {
      globals: {
        ...globals.vitest,
      },
    },
  },
  js.configs.recommended,
  {
    files: ["**/*.ts"],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: "latest",
        sourceType: "module",
      },
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      "no-unused-vars": "off",
    },
  },
  {
    files: ["**/*.svelte"],
    languageOptions: {
      parser: svelteParser,
      parserOptions: {
        parser: {
          ts: tsParser,
          js: espree,
        },
        extraFileExtensions: [".svelte"],
      },
      globals: {
        ...globals.browser,
        ...globals.node,
        $state: "readonly",
        $derived: "readonly",
        $effect: "readonly",
        $$Events: "readonly",
      },
    },
    plugins: {
      svelte,
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      ...svelte.configs["flat/recommended"].rules,
      "no-inner-declarations": "off",
      "no-unused-vars": "off",
      "no-undef": "off",
    },
  },
  prettier,
];
