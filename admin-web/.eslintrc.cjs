module.exports = {
  root: true,
  env: {
    browser: true,
    es2021: true,
  },
  extends: ["eslint:recommended", "plugin:svelte/recommended", "prettier"],
  parserOptions: {
    ecmaVersion: "latest",
    sourceType: "module",
    extraFileExtensions: [".svelte"],
  },
  overrides: [
    {
      files: ["*.svelte"],
      parser: "svelte-eslint-parser",
      parserOptions: {
        parser: {
          js: "espree",
          ts: "@typescript-eslint/parser",
        },
      },
    },
    {
      files: ["*.ts"],
      parser: "@typescript-eslint/parser",
    },
  ],
};
