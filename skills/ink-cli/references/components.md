# Ink Community Components

Useful third-party components for building Ink CLI apps.

## Input Components

### ink-text-input
Text input field.
```bash
npm install ink-text-input
```
```tsx
import TextInput from 'ink-text-input';
<TextInput value={value} onChange={setValue} />
```

### ink-select-input
Dropdown/select input.
```bash
npm install ink-select-input
```
```tsx
import SelectInput from 'ink-select-input';
<SelectInput items={[{label: 'One', value: 1}]} onSelect={handleSelect} />
```

### ink-multi-select
Multi-select from a list.
```bash
npm install ink-multi-select
```

### ink-confirm-input
Yes/No confirmation.
```bash
npm install ink-confirm-input
```

### ink-quicksearch-input
Fast quicksearch-like navigation.
```bash
npm install ink-quicksearch-input
```

### ink-form
Complete form handling.
```bash
npm install ink-form
```

---

## Visual Components

### ink-spinner
Loading spinners.
```bash
npm install ink-spinner
```
```tsx
import Spinner from 'ink-spinner';
<Text><Spinner type="dots" /> Loading...</Text>
```
Types: `dots`, `line`, `pipe`, `simpleDots`, `simpleDotsScrolling`, `star`, `balloon`, `noise`, `bounce`, `boxBounce`, `circle`, etc.

### ink-progress-bar
Progress bars.
```bash
npm install ink-progress-bar
```

### ink-gradient
Gradient colored text.
```bash
npm install ink-gradient
```
```tsx
import Gradient from 'ink-gradient';
<Gradient name="rainbow">Rainbow text</Gradient>
```

### ink-big-text
Large ASCII text.
```bash
npm install ink-big-text
```

### ink-ascii
More font choices for big text (Figlet-based).
```bash
npm install ink-ascii
```

### ink-link
Clickable terminal links.
```bash
npm install ink-link
```
```tsx
import Link from 'ink-link';
<Link url="https://example.com">Click me</Link>
```

### ink-divider
Horizontal dividers.
```bash
npm install ink-divider
```

### ink-picture
Display images in terminal.
```bash
npm install ink-picture
```

---

## Layout Components

### ink-table
Render tables with columns and rows.
```bash
npm install ink-table
```
```tsx
import Table from 'ink-table';
<Table data={[{name: 'John', age: 30}]} />
```

### ink-tab
Tabbed interface.
```bash
npm install ink-tab
```

### ink-titled-box
Box with a title.
```bash
npm install ink-titled-box
```

### ink-scroll-view
Scrollable container.
```bash
npm install ink-scroll-view
```

### ink-scroll-list
Scrollable list.
```bash
npm install ink-scroll-list
```

---

## Utility Components

### ink-task-list
Task list with status indicators.
```bash
npm install ink-task-list
```
```tsx
import { TaskList, Task } from 'ink-task-list';
<TaskList>
  <Task label="Build" state="success" />
  <Task label="Test" state="loading" />
</TaskList>
```

### ink-markdown
Render syntax-highlighted markdown.
```bash
npm install ink-markdown
```

### ink-syntax-highlight
Code syntax highlighting.
```bash
npm install ink-syntax-highlight
```

### ink-spawn
Spawn and display child processes.
```bash
npm install ink-spawn
```

### ink-chart
Sparklines and bar charts.
```bash
npm install ink-chart
```

---

## Hooks

### ink-use-stdout-dimensions
Subscribe to terminal size changes.
```bash
npm install ink-use-stdout-dimensions
```
```tsx
import { useStdoutDimensions } from 'ink-use-stdout-dimensions';
const [columns, rows] = useStdoutDimensions();
```

---

## Styling Utilities

### ink-color-pipe
Create colored text with simpler style strings.
```bash
npm install ink-color-pipe
```
```tsx
import { ColorPipe } from 'ink-color-pipe';
<ColorPipe styles="red.bold">Error!</ColorPipe>
```

---

## Notable Apps Built with Ink

Reference implementations for patterns and inspiration:

- **Claude Code** - Anthropic's agentic coding tool
- **Gemini CLI** - Google's agentic coding tool
- **GitHub Copilot CLI** - GitHub's CLI assistant
- **Shopify CLI** - Build Shopify apps
- **Cloudflare Wrangler** - Cloudflare Workers CLI
- **Prisma** - Database toolkit
- **Gatsby** - Web framework
- **Terraform CDK** - Infrastructure as code
