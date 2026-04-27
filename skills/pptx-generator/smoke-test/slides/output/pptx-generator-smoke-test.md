<!-- Slide number: 1 -->

PPTX Generator Smoke Test
Target checks
16:9 layout
Theme contract
Page badges
writeFile output
Verify that the skill can produce a real four-slide deck with a cover, agenda, content, and closing slide.

skills-test workspace
April 13, 2026

### Notes:

<!-- Slide number: 2 -->
Agenda

01
Deck shape
Scope
Select the narrowest workflow for the incoming PPT task.
1 cover
1 agenda
1 content
1 closing

02
Build
Create slide modules that obey the documented theme contract.

03
Verify
Extract the generated deck back to Markdown and check the result.

2

### Notes:

<!-- Slide number: 3 -->
What This Smoke Test Covers
A real smoke test should prove the documented workflow can create a structured deck, not just sample snippets.

Verification loop
Theme object contract
100%

Build the deck
Extract Markdown
Check for leftover text
Confirm slide text
Page number badges
100%

PPTX write and reopen
95%

3

### Notes:

<!-- Slide number: 4 -->
Result
The skill now has a live-generated artifact that proves the core documented workflow can run end to end.

Generated
Extracted
Reviewed
A real PPTX file was written with PptxGenJS.
MarkItDown can read the output back to Markdown.
The extracted text can be reviewed for order and completeness.

Next: expand this smoke test into reusable scripts only if you want repeatable CI coverage.

4

### Notes: