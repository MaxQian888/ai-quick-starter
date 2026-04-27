# Deployment Guide | Firefly Docs

- Source URL: https://docs-firefly.cuteleaf.cn/en/guide/deploy.html
- Crawled At (UTC): 2026-03-26T07:17:33.262838+00:00

## Extracted Content

Deployment Guide ​ 

This guide covers how to deploy your Firefly blog to various platforms. 

Local Build ​ 

If you use your own web server (e.g., Nginx, Apache, etc.), you can build locally and upload manually: 

bash 

pnpm build 

The build output is in the 
dist/ 
directory. Upload all files from that directory to your server. 

TIP 

The following platforms build and deploy automatically — no manual build required. 

Vercel ​ 

Vercel is one of the easiest platforms for deploying Astro projects. 

Option 1: Via Vercel Dashboard ​ 

Push your project to GitHub / GitLab / Bitbucket 

Log in to Vercel , click Add New → Project 

Import your repository 

Vercel will auto-detect the Astro framework: 

Framework Preset : 
Astro 

Build Command : 
pnpm build 

Output Directory : 
dist 

Install Command : 
pnpm install 

Set Node.js version: go to Settings → General → Node.js Version , select 
22.x 

Click Deploy 

Option 2: Using vercel.json ​ 

Create 
vercel.json 
in the project root: 

json 

{ "framework" : "astro" , "buildCommand" : "pnpm build" , "outputDirectory" : "dist" , "installCommand" : "pnpm install" } 

TIP 

Vercel supports automatic deployments: every push to the main branch triggers a build and deploy. 

Netlify ​ 

Netlify is another popular static site hosting platform. 

Option 1: Via Netlify Dashboard ​ 

Log in to Netlify 

Click Add new project → Import an existing project 

Connect your GitHub repository 

Configure build settings: 

Build command : 
pnpm build 

Publish directory : 
dist 

Set 
NODE_VERSION 
to 
22 
in Environment variables 

Click Deploy site 

Option 2: Using netlify.toml ​ 

Create 
netlify.toml 
in the project root: 

toml 

[ build ] command = "pnpm build" publish = "dist" [ build . environment ] NODE_VERSION = "22" 

GitHub Pages ​ 

Use GitHub Actions to deploy Firefly to GitHub Pages. 

Steps ​ 

In your GitHub repository: Settings → Pages → Source , select GitHub Actions 

Create 
.github/workflows/deploy.yml 
in the project root: 

yaml 

name : Deploy to GitHub Pages on : push : branches : [ main ] workflow_dispatch : permissions : contents : read pages : write id-token : write jobs : build : runs-on : ubuntu-latest steps : - name : Checkout uses : actions/checkout@v4 - name : Setup pnpm uses : pnpm/action-setup@v4 - name : Setup Node uses : actions/setup-node@v4 with : node-version : 22 cache : pnpm - name : Install dependencies run : pnpm install - name : Build run : pnpm build - name : Upload artifact uses : actions/upload-pages-artifact@v3 with : path : dist deploy : needs : build runs-on : ubuntu-latest environment : name : github-pages url : ${{ steps.deployment.outputs.page_url }} steps : - name : Deploy to GitHub Pages id : deployment uses : actions/deploy-pages@v4 

Set 
site 
and 
base 
in 
astro.config.mjs 
: 

js 

export default defineConfig ({ site: "https://<username>.github.io" , base: "/<repo-name>/" , }); 

WARNING 

No editing needed for 
base 
, if the GitHub Pages set a custom domain or the repo is named 
<username>.github.io 

Cloudflare Workers ​ 

Cloudflare Workers offers free serverless edge computing. That can also use to host static site. 

Option 1: Via Cloudflare Dashboard ​ 

Create 
wrangler.toml 
in the project root： 

toml 

name = "firefly" compatibility_date = "YYYY-MM-DD" # edit to today [ assets ] directory = "./dist" [ vars ] NODE_VERSION = "22" 

Log in to Cloudflare Dashboard 

Enter Compute → Workers & Pages , click Create application → Connect Github 

Select your GitHub repository 

Configure build settings: 

Build command : 
pnpm build 

Deploy command : 
npx wrangler deploy 

Click Deploy 

Option 2: Using Wrangler CLI ​ 

bash 

# Install Wrangler pnpm add -g wrangler # Login wrangler login # Build & deploy pnpm build wrangler deploy dist 

Cloudflare Pages ​ 

Cloudflare Pages offers free static site hosting. 

Option 1: Via Cloudflare Dashboard ​ 

Log in to Cloudflare Dashboard 

Enter Compute → Workers & Pages , click Create application → Pages → Connect to Git 

Select your GitHub repository 

Configure build settings: 

Framework preset : 
Astro 

Build command : 
pnpm build 

Build output directory : 
dist 

Set 
NODE_VERSION 
to 
22 
in Environment variables 

Click Save and Deploy 

Option 2: Using Wrangler CLI ​ 

bash 

# Install Wrangler pnpm add -g wrangler # Login wrangler login # Build & deploy pnpm build wrangler pages deploy dist 

EdgeOne Pages ​ 

EdgeOne Pages is a static site hosting service provided by Tencent Cloud's edge computing platform. 

Steps ​ 

Log in to EdgeOne Console 

Go to Site Acceleration → Pages , click Create Project 

Select Import from Git , connect your GitHub / GitLab repository 

Configure build settings: 

Framework preset : 
Astro 

Build command : 
pnpm build 

Output directory : 
dist 

Set 
NODE_VERSION 
to 
22 
in environment variables 

Click Start Deployment 

TIP 

EdgeOne Pages has edge nodes in mainland China, providing fast access for Chinese users. 

Alibaba Cloud ESA ​ 

Alibaba Cloud ESA (Edge Security Acceleration) offers a Pages static site hosting feature. 

Steps ​ 

Log in to Alibaba Cloud ESA Console 

Go to Pages , click Create Project 

Select Import from Git , connect your GitHub / GitLab repository 

Configure build settings: 

Framework preset : 
Astro 

Build command : 
pnpm build 

Output directory : 
dist 

Set 
NODE_VERSION 
to 
22 
in environment variables 

Click Start Deployment 

TIP 

Alibaba Cloud ESA has extensive edge nodes globally, with particularly broad coverage in mainland China, making it ideal for blogs targeting Chinese users. 

Custom Domain ​ 

Most platforms support custom domain binding. General steps: 

Add a CNAME record at your DNS provider pointing to the platform-assigned domain 

Add the custom domain in the platform dashboard 

Wait for DNS propagation (usually a few minutes to hours) 

Enable HTTPS (most platforms auto-provision SSL certificates) 

Deployment Notes ​ 

Ensure 
site 
in 
astro.config.mjs 
is set to your actual domain 

If deploying to a subpath (e.g., 
https://example.com/blog/ 
), set the 
base 
field 

Node.js version must be set to 22 or higher on all platforms 

After the initial deployment, subsequent code pushes will automatically trigger redeployment
