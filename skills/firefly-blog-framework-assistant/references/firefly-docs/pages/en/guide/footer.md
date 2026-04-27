# Footer | Firefly Docs

- Source URL: https://docs-firefly.cuteleaf.cn/en/guide/footer.html
- Crawled At (UTC): 2026-03-26T07:17:33.390006+00:00

## Extracted Content

Footer ​ 

The footer configuration allows injecting custom HTML content at the bottom of the site, such as ICP filing numbers. 

Config Files ​ 

TypeScript config: 
src/config/footerConfig.ts 

HTML content: 
src/config/FooterConfig.html 

Properties ​ 

Property 

Type 

Default 

Description 

enable 

boolean 

false 

Enable footer HTML injection 

ts 

export const footerConfig : FooterConfig = { enable: false , }; 

Custom Content ​ 

Edit the 
src/config/FooterConfig.html 
file directly to add custom content: 

html 

<!-- src/config/FooterConfig.html example --> < div style = "text-align: center; font-size: 12px;" > < a href = "https://example.com" target = "_blank" >Custom footer content</ a > </ div > 

TIP 

After editing the HTML file, the page will auto-update in dev mode if 
enable 
is set to 
true 
.
