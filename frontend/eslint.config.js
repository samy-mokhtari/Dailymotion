/**
 * ESLint Flat Config (Frontend)
 *
 * Purpose
 * - Enforce consistent code quality rules for the React/TypeScript frontend.
 * - Catch common mistakes early (during local pre-commit) and keep PRs clean.
 *
 * Why "flat config"?
 * - Since ESLint v9, the recommended default configuration format is `eslint.config.js`.
 * - Flat config is explicit, modern, and avoids legacy `.eslintrc.*` pitfalls.
 *
 * How it's used in this repo
 * - `pre-commit` runs ESLint on staged frontend files with `--fix` enabled.
 * - This config is located in `frontend/`, so CLI calls should reference it (e.g. via `--config frontend/eslint.config.js`)
 *   when executed from the repository root.
 *
 * Notes
 * - Keep formatting rules in Prettier; avoid conflicting style rules here.
 * - Extend cautiously: prefer adding targeted rules rather than large preset stacks.
 */

import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default [
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    ignores: ['dist/**', 'build/**', 'node_modules/**'],
  },
];
