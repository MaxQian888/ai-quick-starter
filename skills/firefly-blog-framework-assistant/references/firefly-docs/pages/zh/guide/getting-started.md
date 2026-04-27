# 快速开始 | Firefly Docs

- Source URL: https://docs-firefly.cuteleaf.cn/zh/guide/getting-started.html
- Crawled At (UTC): 2026-03-26T07:17:32.894281+00:00

## Extracted Content

快速开始 ​ 

Firefly 是一款基于 Astro 框架和 Fuwari 模板开发的清新美观且现代化个人博客主题，专为技术爱好者和内容创作者设计。该主题融合了现代 Web 技术栈，提供了丰富的功能模块和高度可定制的界面，让您能够轻松打造出专业且美观的个人博客网站。 

环境要求 ​ 

Node.js 22.0 或更高版本 

pnpm 包管理器（推荐） 

Git 

安装 ​ 

克隆仓库 

bash 

git clone https://github.com/CuteLeaf/Firefly.git cd Firefly 

安装依赖 

bash 

pnpm install 

启动开发服务器 

bash 

pnpm dev 

构建生产版本 

bash 

pnpm build 

项目结构 ​ 

Firefly/ ├── src/ │ ├── config/ # 配置文件目录 │ ├── components/ # 组件目录 │ ├── content/ # 内容目录（文章、页面） │ ├── layouts/ # 布局模板 │ ├── pages/ # 页面路由 │ └── types/ # 类型定义 ├── public/ # 静态资源 └── astro.config.mjs # Astro 配置 

配置文件概览 ​ 

所有配置文件位于 
src/config/ 
目录下： 

配置文件 

说明 

文档 

siteConfig.ts 

站点基础配置 

站点配置 

navBarConfig.ts 

导航栏配置 

导航栏 

sidebarConfig.ts 

侧边栏布局配置 

侧边栏 

profileConfig.ts 

个人资料配置 

个人资料 

backgroundWallpaper.ts 

背景壁纸配置 

背景壁纸 

commentConfig.ts 

评论系统配置 

评论系统 

musicConfig.ts 

音乐播放器配置 

音乐播放器 

fontConfig.ts 

字体配置 

字体 

coverImageConfig.ts 

封面图片配置 

封面图片 

expressiveCodeConfig.ts 

代码块配置 

代码块 

sakuraConfig.ts 

樱花特效配置 

樱花特效 

announcementConfig.ts 

公告配置 

公告 

footerConfig.ts 

页脚配置 

页脚 

licenseConfig.ts 

许可证配置 

许可证 

friendsConfig.ts 

友链配置 

友链 

sponsorConfig.ts 

赞助配置 

赞助 

adConfig.ts 

广告配置 

广告 

pioConfig.ts 

Live2D/Spine 模型配置 

看板娘
