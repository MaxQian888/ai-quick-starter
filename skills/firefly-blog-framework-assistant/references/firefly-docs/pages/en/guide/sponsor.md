# Sponsor | Firefly Docs

- Source URL: https://docs-firefly.cuteleaf.cn/en/guide/sponsor.html
- Crawled At (UTC): 2026-03-26T07:17:34.182132+00:00

## Extracted Content

Sponsor ​ 

The sponsor configuration manages the sponsor page content, including donation methods and sponsor list. 

Config File ​ 

src/config/sponsorConfig.ts 

Basic Configuration ​ 

Property 

Type 

Default 

Description 

title 

string 

"" 

Page title (empty uses i18n) 

description 

string 

"" 

Page description (empty uses i18n) 

usage 

string 

- 

Sponsorship usage description 

showSponsorsList 

boolean 

true 

Show sponsors list 

showComment 

boolean 

true 

Show comment section on sponsor page (requires comment system enabled) 

showButtonInPost 

boolean 

true 

Show sponsor button on post pages 

Sponsor Methods ​ 

Property 

Type 

Required 

Description 

name 

string 

Yes 

Method name 

icon 

string 

No 

Icon (Iconify format) 

qrCode 

string 

No 

QR code image path (relative to public) 

link 

string 

No 

Donation link URL 

description 

string 

No 

Description text 

enabled 

boolean 

Yes 

Whether enabled 

Sponsor List Items ​ 

Property 

Type 

Required 

Description 

name 

string 

Yes 

Sponsor name 

amount 

string 

No 

Donation amount 

date 

string 

No 

Date (ISO format) 

ts 

sponsors : [ { name: "John Doe" , amount: "$10" , date: "2025-10-01" , }, ], 

TIP 

Set 
pages.sponsor 
to 
true 
in 
siteConfig.ts 
to enable the sponsor page. 

The sponsor page comment section is path-based ( 
/sponsor/ 
) and does not require creating a content entry like 
src/content/spec/sponsor.md 
.
