<div align="center">

# Group Friend.skill

> *"You big model developers are the codegod, you've liberated front-end brothers, and you'll also liberate back-end brothers, testing brothers, operation and maintenance brothers, network security brothers, IC brothers, and finally liberate yourself and all of humanity"*

> *"I'll keep an eye on you!"*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://python.org)
[![Claude Code](https://img.shields.io/badge/Claude%20Code-Skill-blueviolet)](https://claude.ai/code)
[![AgentSkills](https://img.shields.io/badge/AgentSkills-Standard-green)](https://agentskills.io)

<br>


   ![pig](images/pig-skill.png)


<br>

Your group friend left the group, leaving empty chat records with no one to miss them?<br>
Your online friend went silent, leaving only past laughter and memories?<br>
Your gaming teammate stopped playing, taking all the默契 and cooperation away?<br>
Your best friend moved away, and their familiar chat style disappeared overnight?<br>

**Turn cold partings into warm Skills, welcome to cyber immortality!**

Provide group friend's raw materials (QQ group chat records, screenshots) plus your subjective description<br>
Generate a **true AI Skill that can chat on their behalf**<br>Answer questions in their tone, know when they would send emoticons, and when they would go silent

[Data Sources](#supported-data-sources) · [Installation](#installation) · [Usage](#usage) · [Examples](#examples) · [Detailed Installation](INSTALL.md) · [**中文**](README.md)

</div>

---

### 🌟 This project is based on [Colleague.skill](https://github.com/titanwings/colleague-skill)

> If you're interested, please also support the original project [Colleague.skill](https://github.com/titanwings/colleague-skill). 🌟🌟🌟
> 
> If you find this interesting, please give it a Star!

---

## Supported Data Sources

| Source | Message Records | Notes |
|--------|:--------------:|-------|
| QQ Group Chat Records | ✅ TXT/JSON | Supports official export and third-party tool export |
| Images / Screenshots | ✅ | Manual upload |
| Direct Text Paste | ✅ | Manual input |

### Recommended QQ Chat Export Tools

The following tools are independent open-source projects, this project does not include their code, only adapts their export formats in the parser:

| Tool | Platform | Description |
|------|----------|-------------|
| [QQ Chat Exporter](https://github.com/shuakami/qq-chat-exporter) | Windows | QQ chat record export, supports multiple formats |


---

## Installation

### Claude Code

> **Important**: Claude Code looks for skills in `.claude/skills/` from the **git repository root directory**. Please execute in the correct location.

```bash
# Install to current project (execute in git repository root)
mkdir -p .claude/skills
git clone https://github.com/Neko-Suwako/pig-skill .claude/skills/pig-skill

# Or install globally (available for all projects)
git clone https://github.com/Neko-Suwako/pig-skill ~/.claude/skills/pig-skill
```

### OpenClaw

```bash
git clone https://github.com/Neko-Suwako/pig-skill ~/.openclaw/workspace/skills/pig-skill
```

### Dependencies (Optional)

```bash
pip3 install -r requirements.txt
```

---

## Usage

In Codex / AgentSkills style environments, enter:

```
$pig-skill
```

Follow the prompts to enter group friend's nickname, basic information (age, gender, occupation, hobbies), personality tags, then select data sources. All fields can be skipped, generation is possible with just description.

After completion, use `$pig-{slug}` for the full skill and `$pig-{slug}-persona` for the persona-only companion skill.

### Management Commands

| Command | Description |
|---------|-------------|
| `python scripts/skill_writer.py --action list --base-dir ./pigs` | List all group friend skills |
| `$pig-{slug}` | Call the complete skill |
| `$pig-{slug}-persona` | Load only the persona |
| `python scripts/version_manager.py --action rollback --slug {slug} --version {version} --base-dir ./pigs` | Roll back to a historical version |

---

## Examples

> Input: `Xiao Ming, 25 years old, male, programmer, likes gaming, ENFP Gemini, talkative, loves sending emoticons, often stays up late`

**Scenario 1: Group Chat Interaction**

```
User      ❯ Are you there?

Group Friend.skill ❯ Yeah yeah, just started a game, what's up bro? [game emoticon]
```

**Scenario 2: Discussing Games**

```
User      ❯ Any good games to recommend lately?

Group Friend.skill ❯ "Genshin Impact: Song of the Empty Moon"!
```

**Scenario 3: Daily Chat**

```
User      ❯ The weather is nice today

Group Friend.skill ❯ Yeah! But I'm gaming in the dorm, don't feel like going out [lying down emoticon]
```

---

## Features

### Generated Skill Structure

Each group friend Skill consists of Persona parts that drive output:

| Part | Content |
|------|---------|
| **Persona** | 5-layer personality structure: Hard Rules → Identity → Expression Style → Chat Behavior Patterns → Interest Preferences |

Operation logic: `Receive task → Persona judges attitude → Output in their tone`

### Supported Tags

**Chat Style**: Talkative · Lurker · Loves sending emoticons · Loves sending voice messages · Quick reply · Spammer

**Personality Traits**: Outgoing · Introverted · Humorous · Serious · Impulsive · Calm · Direct · Reserved · Enthusiastic · Cold

**Hobbies**: Gamer · Anime fan · Music lover · Sports enthusiast · Foodie · Travel lover · Tech enthusiast

**Communication Style**: Direct · Indirect · Sarcastic · Gentle · Rational · Emotional · Argumentative · Agreeable

### Evolution Mechanism

- **Append Files** → Automatically analyze increments → Merge into corresponding parts without overwriting existing conclusions
- **Dialogue Correction** → Say "He wouldn't do that, he should be xxx" → Write to Correction layer, take effect immediately
- **Version Management** → Automatically archive each update, support rollback to any historical version

---

## Project Structure

This project follows the [AgentSkills](https://agentskills.io) open standard, the entire repo is a skill directory:

```
pig-skill/
├── SKILL.md              # skill entry with standard frontmatter
├── CLAUDE.md             # module navigation and contract
├── agents/openai.yaml    # UI metadata
├── references/           # analysis and merge references
│   ├── intake.md
│   ├── persona-analyzer.md
│   ├── persona-builder.md
│   ├── merger.md
│   └── correction-handler.md
├── scripts/              # Python utilities
│   ├── qq_chat_parser.py
│   ├── skill_writer.py
│   └── version_manager.py
├── tests/                # script contract tests
├── pigs/                 # generated group friend skills and sample outputs
├── requirements.txt
└── LICENSE
```

---

## Notes

- **Raw material quality determines Skill quality**: Chat records + screenshots > Manual description only
- Recommended collection priority: **Long articles he actively wrote** > **Interactive messages** > Daily messages
- This is still a demo version, please be understanding if there are bugs, and feel free to raise issues!

---

<div align="center">

MIT License © [Neko-Suwako]


</div>
