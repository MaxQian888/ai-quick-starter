# Bootstrap and Migration

## Choose a Path

### Path A: Modern-from-scratch (Preferred)

Use when you want full control and latest runtime/dependency alignment.

1. Initialize project:

```bash
mkdir my-ink-cli && cd my-ink-cli
npm init -y
```

2. Set modern package fields in `package.json`:

- `"type": "module"`
- `"engines": { "node": ">=20" }`
- scripts for `dev`, `build`, `start`, `test`

3. Install baseline deps:

```bash
npm i ink react
npm i -D typescript @types/react @types/node tsx ink-testing-library
```

4. Add entry file (for example `source/index.tsx`) and run with `tsx`.

### Path B: create-ink-app then upgrade

Use when you need quick scaffold speed, but upgrade immediately.

```bash
npx create-ink-app my-cli
cd my-cli
npm i ink@latest react@latest
npm i -D ink-testing-library@latest
```

Then verify versions:

```bash
npm ls ink react ink-testing-library --depth=0
```

## Why Upgrade is Mandatory After create-ink-app

Current official templates in `create-ink-app` are pinned to:

- `ink: 4.1.0`
- `react: 18.2.0`

This is below current Ink v6 + React 19 baseline, so treating scaffold output as production-ready without upgrade is unsafe.

## Existing Project Migration (v4/v5 -> v6+)

1. Detect current matrix:

```bash
node -v
npm ls ink react --depth=0
```

2. Upgrade dependencies:

```bash
npm i ink@latest react@latest
npm i -D ink-testing-library@latest
```

3. Re-check APIs and replace old assumptions:

- Add `usePaste` where paste behavior was implicitly handled.
- Prefer `renderToString` for non-interactive output jobs.
- Consider `kittyKeyboard` only when richer key metadata is required.

4. Re-run app and tests in both interactive and non-interactive contexts.

## Migration Checklist

- `node` satisfies Ink engine (`>=20`).
- `react` satisfies Ink peer dependency (`>=19.1.1`).
- Input handlers still behave correctly for arrow/escape/enter and paste flows.
- Output remains stable when `stdout` is not a TTY.
- CI tests use `ink-testing-library` and do not rely on terminal side effects.

## Common Migration Pitfalls

1. Upgraded `ink`, but forgot `react` major bump.
2. Kept old scaffold scripts that assume CJS runtime.
3. Ignored non-interactive mode, causing broken piped output.
4. Asserted outdated frame behavior in tests without adapting to current rendering flow.
