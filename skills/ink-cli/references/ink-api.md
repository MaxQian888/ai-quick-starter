# Ink API Reference

Complete API documentation for Ink components, hooks, and functions.

## Components

### `<Text>`

Displays styled text. Only allows text nodes and nested `<Text>` inside.

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `color` | `string` | - | Text color (name, hex, rgb) |
| `backgroundColor` | `string` | - | Background color |
| `dimColor` | `boolean` | `false` | Dim the color |
| `bold` | `boolean` | `false` | Bold text |
| `italic` | `boolean` | `false` | Italic text |
| `underline` | `boolean` | `false` | Underlined text |
| `strikethrough` | `boolean` | `false` | Strikethrough text |
| `inverse` | `boolean` | `false` | Invert colors |
| `wrap` | `string` | `'wrap'` | `wrap`, `truncate`, `truncate-start`, `truncate-middle`, `truncate-end` |

```tsx
<Text color="green">Green</Text>
<Text color="#005cc5">Hex Blue</Text>
<Text color="rgb(232, 131, 136)">RGB Red</Text>
<Text bold italic>Bold Italic</Text>
<Text wrap="truncate-middle">Very long text here...</Text>
```

---

### `<Box>`

Flexbox container. Like `<div style="display: flex">`.

#### Dimension Props

| Prop | Type | Description |
|------|------|-------------|
| `width` | `number \| string` | Width in spaces or percentage |
| `height` | `number \| string` | Height in lines or percentage |
| `minWidth` | `number` | Minimum width |
| `minHeight` | `number` | Minimum height |

#### Padding Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `padding` | `number` | `0` | All sides |
| `paddingX` | `number` | `0` | Left and right |
| `paddingY` | `number` | `0` | Top and bottom |
| `paddingTop` | `number` | `0` | Top only |
| `paddingBottom` | `number` | `0` | Bottom only |
| `paddingLeft` | `number` | `0` | Left only |
| `paddingRight` | `number` | `0` | Right only |

#### Margin Props

Same pattern as padding: `margin`, `marginX`, `marginY`, `marginTop`, `marginBottom`, `marginLeft`, `marginRight`

#### Gap Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `gap` | `number` | `0` | Gap between children (both axes) |
| `columnGap` | `number` | `0` | Horizontal gap |
| `rowGap` | `number` | `0` | Vertical gap |

#### Flex Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `flexDirection` | `string` | `'row'` | `row`, `row-reverse`, `column`, `column-reverse` |
| `flexWrap` | `string` | `'nowrap'` | `nowrap`, `wrap`, `wrap-reverse` |
| `flexGrow` | `number` | `0` | Grow factor |
| `flexShrink` | `number` | `1` | Shrink factor |
| `flexBasis` | `number \| string` | - | Initial size |
| `alignItems` | `string` | - | `flex-start`, `center`, `flex-end` |
| `alignSelf` | `string` | `'auto'` | `auto`, `flex-start`, `center`, `flex-end` |
| `justifyContent` | `string` | - | `flex-start`, `center`, `flex-end`, `space-between`, `space-around`, `space-evenly` |

#### Visibility Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `display` | `string` | `'flex'` | `flex`, `none` |
| `overflow` | `string` | `'visible'` | `visible`, `hidden` |
| `overflowX` | `string` | `'visible'` | Horizontal overflow |
| `overflowY` | `string` | `'visible'` | Vertical overflow |

#### Border Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `borderStyle` | `string \| object` | - | `single`, `double`, `round`, `bold`, `singleDouble`, `doubleSingle`, `classic`, or custom object |
| `borderColor` | `string` | - | All borders color |
| `borderTopColor` | `string` | - | Top border color |
| `borderRightColor` | `string` | - | Right border color |
| `borderBottomColor` | `string` | - | Bottom border color |
| `borderLeftColor` | `string` | - | Left border color |
| `borderDimColor` | `boolean` | `false` | Dim all borders |
| `borderTop` | `boolean` | `true` | Show top border |
| `borderRight` | `boolean` | `true` | Show right border |
| `borderBottom` | `boolean` | `true` | Show bottom border |
| `borderLeft` | `boolean` | `true` | Show left border |

#### Background Props

| Prop | Type | Description |
|------|------|-------------|
| `backgroundColor` | `string` | Background color (fills entire box) |

Custom border style object:
```tsx
<Box borderStyle={{
  topLeft: '↘', top: '↓', topRight: '↙',
  left: '→', right: '←',
  bottomLeft: '↗', bottom: '↑', bottomRight: '↖'
}}>
```

---

### `<Newline>`

Adds newline characters. Must be inside `<Text>`.

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `count` | `number` | `1` | Number of newlines |

---

### `<Spacer>`

Flexible space that expands along the major axis.

```tsx
<Box>
  <Text>Left</Text>
  <Spacer />
  <Text>Right</Text>
</Box>
```

---

### `<Static>`

Permanently renders output above everything else. Items never re-render.

| Prop | Type | Description |
|------|------|-------------|
| `items` | `Array` | Array of items to render |
| `style` | `object` | Box styles for container |
| `children` | `(item, index) => ReactElement` | Render function |

```tsx
<Static items={completedTasks}>
  {(task, index) => (
    <Box key={task.id}>
      <Text color="green">✔ {task.title}</Text>
    </Box>
  )}
</Static>
```

---

### `<Transform>`

Transforms string output before rendering. Only works with `<Text>` children.

| Prop | Type | Description |
|------|------|-------------|
| `transform` | `(line: string, index: number) => string` | Transform function |

```tsx
<Transform transform={s => s.toUpperCase()}>
  <Text>hello</Text>
</Transform>
// Output: HELLO
```

---

## Hooks

### `useInput(handler, options?)`

Handle keyboard input character by character.

```tsx
useInput((input, key) => {
  // input: string - the character(s) entered
  // key: object - metadata about special keys
}, { isActive: true });
```

#### Key Object Properties

| Property | Type | Description |
|----------|------|-------------|
| `leftArrow` | `boolean` | Left arrow pressed |
| `rightArrow` | `boolean` | Right arrow pressed |
| `upArrow` | `boolean` | Up arrow pressed |
| `downArrow` | `boolean` | Down arrow pressed |
| `return` | `boolean` | Enter/Return pressed |
| `escape` | `boolean` | Escape pressed |
| `ctrl` | `boolean` | Ctrl held |
| `shift` | `boolean` | Shift held |
| `tab` | `boolean` | Tab pressed |
| `backspace` | `boolean` | Backspace pressed |
| `delete` | `boolean` | Delete pressed |
| `pageUp` | `boolean` | Page Up pressed |
| `pageDown` | `boolean` | Page Down pressed |
| `meta` | `boolean` | Meta key held |

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `isActive` | `boolean` | `true` | Enable/disable input capture |

---

### `useApp()`

Access app control methods.

```tsx
const { exit } = useApp();
exit();           // Clean exit
exit(new Error()); // Exit with error (rejects waitUntilExit)
```

---

### `useStdin()`

Access stdin stream.

```tsx
const { stdin, isRawModeSupported, setRawMode } = useStdin();
```

| Property | Type | Description |
|----------|------|-------------|
| `stdin` | `stream.Readable` | The stdin stream |
| `isRawModeSupported` | `boolean` | Whether raw mode is supported |
| `setRawMode` | `(enabled: boolean) => void` | Enable/disable raw mode |

---

### `useStdout()`

Access stdout stream.

```tsx
const { stdout, write } = useStdout();
write('Direct output\n'); // Bypasses Ink rendering
```

---

### `useStderr()`

Access stderr stream.

```tsx
const { stderr, write } = useStderr();
write('Error output\n');
```

---

### `useFocus(options?)`

Make component focusable.

```tsx
const { isFocused } = useFocus({
  autoFocus: false,
  isActive: true,
  id: 'my-component'
});
```

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `autoFocus` | `boolean` | `false` | Auto-focus if nothing focused |
| `isActive` | `boolean` | `true` | Can receive focus |
| `id` | `string` | - | ID for programmatic focus |

---

### `useFocusManager()`

Programmatic focus control.

```tsx
const { enableFocus, disableFocus, focusNext, focusPrevious, focus } = useFocusManager();

focus('component-id');  // Focus specific component
focusNext();            // Tab behavior
focusPrevious();        // Shift+Tab behavior
```

---

### `useIsScreenReaderEnabled()`

Check if screen reader is active.

```tsx
const isScreenReaderEnabled = useIsScreenReaderEnabled();
```

---

## API Functions

### `render(tree, options?)`

Mount and render a component. Returns an `Instance`.

```tsx
const instance = render(<App />, {
  stdout: process.stdout,
  stdin: process.stdin,
  stderr: process.stderr,
  exitOnCtrlC: true,
  patchConsole: true,
  debug: false,
  maxFps: 30,
  incrementalRendering: false,
  onRender: ({ renderTime }) => {}
});
```

#### Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `stdout` | `stream.Writable` | `process.stdout` | Output stream |
| `stdin` | `stream.Readable` | `process.stdin` | Input stream |
| `stderr` | `stream.Writable` | `process.stderr` | Error stream |
| `exitOnCtrlC` | `boolean` | `true` | Exit on Ctrl+C |
| `patchConsole` | `boolean` | `true` | Intercept console.* calls |
| `debug` | `boolean` | `false` | Render each update separately |
| `maxFps` | `number` | `30` | Max render frequency |
| `incrementalRendering` | `boolean` | `false` | Only update changed lines |
| `onRender` | `function` | - | Callback after each render |

#### Instance Methods

| Method | Description |
|--------|-------------|
| `rerender(tree)` | Update the root component |
| `unmount()` | Unmount the app |
| `waitUntilExit()` | Promise that resolves on unmount |
| `clear()` | Clear output |

---

### `measureElement(ref)`

Measure a `<Box>` element's dimensions.

```tsx
const ref = useRef();

useEffect(() => {
  const { width, height } = measureElement(ref.current);
}, []);

<Box ref={ref}>...</Box>
```

---

## ARIA / Accessibility

Enable with `render(<App />, { isScreenReaderEnabled: true })` or `INK_SCREEN_READER=true`.

### ARIA Props (on `<Box>` and `<Text>`)

| Prop | Type | Description |
|------|------|-------------|
| `aria-label` | `string` | Screen reader label |
| `aria-hidden` | `boolean` | Hide from screen readers |
| `aria-role` | `string` | Semantic role |
| `aria-state` | `object` | State info |

#### Supported Roles
`button`, `checkbox`, `radio`, `radiogroup`, `list`, `listitem`, `menu`, `menuitem`, `progressbar`, `tab`, `tablist`, `timer`, `toolbar`, `table`

#### Supported States
`checked`, `disabled`, `expanded`, `selected` (all boolean)

```tsx
<Box aria-role="checkbox" aria-state={{ checked: true }}>
  <Text>Accept terms</Text>
</Box>
// Screen reader: "(checked) checkbox: Accept terms"
```

---

## Testing

Use `ink-testing-library`:

```tsx
import { render } from 'ink-testing-library';

const { lastFrame, rerender, unmount, stdin } = render(<App />);

// Check output
expect(lastFrame()).toContain('Hello');

// Simulate input
stdin.write('q');

// Update props
rerender(<App count={2} />);

// Cleanup
unmount();
```

---

## React DevTools

```bash
# Run your CLI with DEV=true
DEV=true my-cli

# In another terminal
npx react-devtools
```
