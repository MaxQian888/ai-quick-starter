# Code Block | Firefly Docs

- Source URL: https://docs-firefly.cuteleaf.cn/en/guide/code-block.html
- Crawled At (UTC): 2026-03-26T07:17:33.083828+00:00

## Extracted Content

Code Block ​ 

Code block configuration is based on Expressive Code , supporting custom themes and code collapsing. 

Config File ​ 

src/config/expressiveCodeConfig.ts 

Properties ​ 

Property 

Type 

Default 

Description 

darkTheme 

string 

"one-dark-pro" 

Dark mode code theme 

lightTheme 

string 

"one-light" 

Light mode code theme 

See Expressive Code Themes for more themes. 

Code Collapsing ​ 

Property 

Type 

Default 

Description 

pluginCollapsible.enable 

boolean 

true 

Enable collapsing 

pluginCollapsible.lineThreshold 

number 

15 

Line count threshold for collapse button 

pluginCollapsible.previewLines 

number 

8 

Preview lines when collapsed 

pluginCollapsible.defaultCollapsed 

boolean 

true 

Default to collapsed for long blocks 

ts 

pluginCollapsible : { enable : true , lineThreshold : 15 , previewLines : 8 , defaultCollapsed : true , }, 

Language Badge ​ 

Property 

Type 

Default 

Description 

pluginLanguageBadge.enable 

boolean 

true 

Enable language badge 

ts 

// Language Badge Plugin Config pluginLanguageBadge : { enable : true , // Enable language badge }, 

WARNING 

Restart the Astro dev server after changing this configuration.
