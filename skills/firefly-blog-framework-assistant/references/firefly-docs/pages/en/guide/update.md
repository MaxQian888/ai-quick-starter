# Updating the template | Firefly Docs

- Source URL: https://docs-firefly.cuteleaf.cn/en/guide/update.html
- Crawled At (UTC): 2026-03-26T07:17:34.250094+00:00

## Extracted Content

Updating the template ​ 

This guide covers how to update the Firefly template to the latest version. 

Update Methods ​ 

Method 1: Git Merge (Recommended) ​ 

If you obtained the project via 
git clone 
, you can pull upstream updates through Git. 

1. Add Upstream Remote ​ 

If you haven't added the upstream remote yet: 

bash 

git remote add upstream https://github.com/CuteLeaf/Firefly.git 

2. Fetch Latest Code ​ 

bash 

git fetch upstream 

3. Merge Updates ​ 

bash 

git merge upstream/master 

4. Resolve Conflicts ​ 

If merge conflicts occur (usually in config files you've modified), resolve them manually: 

bash 

git add . git commit -m "merge: update Firefly theme" 

TIP 

It's recommended to only modify files in 
src/config/ 
(configuration) and 
src/content/ 
(content). Avoid modifying core theme files to minimize conflicts during updates. 

Method 2: Manual Override ​ 

If Git merge conflicts are too many or you've made extensive customizations: 

Back up your files: 

src/config/ 
— all configuration files 

src/content/ 
— posts and page content 

public/ 
— static assets (images, fonts, etc.) 

Download the latest version of Firefly 

Restore your backed-up files to the corresponding directories 

Reinstall dependencies: 

bash 

pnpm install 

Start the dev server and check for errors: 

bash 

pnpm dev 

Post-Update Checklist ​ 

After updating, check the following: 

Config compatibility : New versions may add config options. Check the repository's commit history for changes 

Type checking : TypeScript errors may indicate changed type definitions — add any new required fields based on the type definitions 

Dependencies : Run 
pnpm install 
to ensure dependencies are up to date 

Local preview : Run 
pnpm dev 
to preview locally and confirm pages render correctly 

Build test : Run 
pnpm build 
to confirm the build succeeds without errors
