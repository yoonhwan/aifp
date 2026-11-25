<div align="center">

# daily-trend-viewer

**在一个页面里查看 YouTube、Shorts、Instagram Reels、X、Threads、TikTok 热门内容和 AI 视频资讯的本地网站 —— 无需 API 密钥,也无需额外安装包。**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 按分类 × 时间段(今天 · 本周 · 本月)筛选 YouTube 和 Shorts 热门视频,按播放量或点赞数排序。点击卡片可在弹窗中播放。
- 用页头的搜索框按任意关键词搜索 YouTube,结果按播放量排序。
- AI 视频标签页显示新发布和热门的视频生成模型(Hugging Face),以及国内外 AI 视频新闻(Google 新闻 RSS)。
- Reels、X、Threads、TikTok 标签页汇总你关注的账号的最新内容。账号可在页面上添加 · 删除。
- 结果缓存 1 小时,点击右上角的刷新按钮可立即更新。
- 只使用 Python 标准库。服务器只监听 `127.0.0.1`。

## 快速开始

```bash
# 在仓库根目录
cd feature-pack/daily-trend-viewer/app
python3 server.py
# 在浏览器打开 http://localhost:28088 · 用 Ctrl+C 停止
```

## 安装

让智能体来装:对它说"阅读 `feature-pack/daily-trend-viewer/INSTALL.md` 并安装"。

手动安装:只需要 Python 3.8 或更高版本。`app/` 文件夹就是整个应用,可以整个复制到任意位置,也可以直接在原处运行。如果端口 28088 已被占用,把 `app/server.py` 开头的 `PORT = 28088` 改成空闲端口。

```bash
# macOS: 双击 app/실행-Mac.command(出现 Gatekeeper 警告时右键 → 打开),或者
cd app && python3 server.py
# Windows: 双击 app\실행-Windows.bat
# 检查 —— 返回 200 即正常
curl -s -o /dev/null -w "%{http_code}" http://localhost:28088/
```

## 用法

### 标签页

| 标签页 | 内容 | 排序 |
|---|---|---|
| YouTube / Shorts | 分类(全部 · AI · 吃播 · 美妆 · Vlog · 综艺 · 电影/剧集 · 科技 · 知识 · 旅行 · 动物) × 时间段 | 播放量 · 点赞 |
| AI 视频 | 新视频生成模型 · 热门模型 · AI 视频新闻(以文字为主) | — |
| Reels | 关注账号的最新 Reels | 播放量 · 点赞 · 评论 |
| X | 关注账号的最新帖子 | 点赞 · 回复 · 转推 |
| Threads | 关注账号的最新帖子(被拦截时改为账号链接) | 点赞 · 回复 · 转发 |
| TikTok | 实时热门推荐(韩国) + 关注账号的最新视频 | 播放量 · 点赞 · 评论 |

热门 AI 视频在 YouTube 标签页的"AI"分类里。搜索后会切换到视频标签页,点击分类即可取消搜索。

### 账号列表

在页面上修改账号后,`app/` 里会生成下列文件。备份或迁移时请一起复制。

| 标签页 | 文件 |
|---|---|
| Reels | `reels_accounts.json` |
| X | `x_accounts.json` |
| Threads | `threads_accounts.json` |
| TikTok | `tiktok_accounts.json` |

### 数据来源与限制

- YouTube:按播放量排序调用内部搜索 API(InnerTube)。YouTube 的公开热门榜单已在 2025 年下线,所以改用搜索来实现。
- Reels:无需登录调用 instagram.com 网页使用的内部 API。每个账号最多取最新 12 条,请求过于频繁时 Instagram 可能会暂时限制。缩略图通过服务器代理(`/api/img`)转发。
- X:无需登录调用嵌入组件使用的 syndication API。该 API 没有播放量,因此去掉了按播放量排序。
- Threads:目前默认被拦截,会改为显示账号链接。在 `server.py` 的 `THREADS_DOC_IDS` 中填入有效的 doc_id 即可实时获取。
- TikTok:经由免费公开 API tikwm(`www.tikwm.com/api`)。因为是免费档,服务器以低并发(3)调用并缓存 1 小时。

### 注意事项

- TikTok 请求(账号名 · 查询记录)会发送到第三方服务 tikwm.com。该服务一旦变化,TikTok 标签页随时可能失效。
- 所有平台数据都来自非官方、无需认证的内部 API。这在各服务条款下属于灰色地带,可能随时被拦截。仅供个人浏览,请避免频繁刷新。
- 本包的 `server.py` 比原版多了 2 个安全补丁:修改账号的 POST 请求校验 Origin,以及加强图片代理的主机检查。

## 环境要求

- macOS 或 Windows
- Python 3.8 或更高版本(只用标准库 · 无额外安装包)
- API 密钥 / 账号:无
- 安装时间:不到 1 分钟

## 链接

- [INSTALL.md](INSTALL.md)
- [test/verify.md](test/verify.md) —— 详细验证
- [原始发布帖](https://www.threads.com/@xazinga/post/DadL9WQD9ex)
- [AI Feature Pack 目录](../../README.zh-CN.md)
