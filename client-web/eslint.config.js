import js from "@eslint/js";
import prettier from "eslint-config-prettier";
import svelte from "eslint-plugin-svelte";
import globals from "globals";
import * as espree from "espree";
import tsParser from "@typescript-eslint/parser";
import tsPlugin from "@typescript-eslint/eslint-plugin";
import svelteParser from "svelte-eslint-parser";

export default [
  {
    ignores: [".svelte-kit", "build", "dist", "node_modules"],
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
    },
    plugins: {
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      "no-undef": "off",
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
      },
    },
    plugins: {
      svelte,
      "@typescript-eslint": tsPlugin,
    },
    rules: {
      ...svelte.configs["flat/recommended"].rules,
      "no-inner-declarations": "off",
      "no-undef": "off",
      "no-unused-vars": "off",
    },
  },
  prettier,
];
