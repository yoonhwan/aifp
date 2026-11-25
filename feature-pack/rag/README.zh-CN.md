<div align="center">

# rag

**把文档放进加密的本地数据库、进行检索并以 JSON 返回依据的 RAG 引擎 `airag` (CLI `ai-rag`)**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.zh-CN.md) 的功能包之一。各包相互独立,只装需要的即可。

## 功能

- 把原文 · 分块 · 向量存进一个加密的 SQLite(SQLCipher)文件。向量用 sqlite-vec,关键词用 FTS5。
- 只处理显式请求: `add` · `update` · `delete` · `manage restore`。不监视文件夹、不做定时任务、不自动发现,由使用方项目发送事件。
- 更新会生成新的修订版本,旧的原文字节和过去的检索结果(manifest)都会保留。已删除的原文可以恢复。
- 处理配置(嵌入 + 可选 LLM + 规范化设置)注册一次后不再改变。接入 LLM 后,会先生成语义分组 · 标签 · 摘要 · 英文翻译,再做嵌入。
- 检索 = BM25 + 向量 + RRF。从结果出发,在预算(深度 · 分块 · token · 字节)内扩展结构 · 引用 · 语义关联,并作为依据包返回。
- 文档适配器(`documents` 额外安装): PDF · DOCX · XLSX · HWP5 · HWPX,以及 PNG · JPEG · BMP · TIFF 的显式 OCR / 视觉模式。
- 每个命令都输出一个 JSON 响应 `{schema_version, request_id, ok, command, data, error}`。备份 · 恢复 · 诊断也是同样的格式。
- 引擎只返回依据。写出最终回答是上层智能体的工作。

### 处理流程

```text
原文 --[Docling · HWP/HWPX 适配器 · 对话适配器]--> 标准包 (Markdown + 结构 · 锚点)
  --[HybridChunker]--> 分块 --[发布嵌入 · FTS]--> 索引
  --[BM25 + 向量 + RRF]--> 检索 --[有预算的结构 · 语义扩展]--> 依据 (可包含原文)
```

## 快速开始

```bash
cd feature-pack/rag
uv sync                                     # 创建 .venv 并安装 airag

head -c 32 /dev/urandom > my.key            # 32 字节密钥 — 丢失后无法打开数据库
chmod 600 my.key
.venv/bin/ai-rag init my.db --key-fd 3 3< my.key
.venv/bin/ai-rag manage doctor              # 运行环境诊断
```

## 安装

### 没有 INSTALL.md

这个包目前还没有 `INSTALL.md`。想让智能体来装时,说"读 `feature-pack/rag/README.md` 和 `pyproject.toml` 并安装",它会按下面的手动安装步骤执行。

### 手动安装

包名是 `ai-feature-rag`,入口命令是 `ai-rag`(同一命令还有别名 `krb-rag`)。

```bash
cd feature-pack/rag
uv sync                                     # 基础依赖
uv sync --extra documents                   # PDF · DOCX · XLSX · OCR 适配器 (docling · easyocr)
uv run pytest                               # 离线测试 (标记为 integration 的测试默认跳过)
```

## 用法

### 命令

| 命令 | 作用 |
|---|---|
| `ai-rag init <db>` | 创建新的加密数据库 |
| `ai-rag add` · `update` · `delete` | 登记 · 更新(新修订版本) · 删除原文 — 重发同一个 `--request-id` 只生效一次 |
| `ai-rag search` | 用 `--collection` · `--query` · `--profile-key` 检索 · `--expand` 在同一快照内扩展 |
| `ai-rag expand --manifest-id N` | 从过去的检索结果扩展依据 (`--max-depth` · `--max-chunks` · `--max-tokens` · `--max-bytes` · `--max-edges`) |
| `ai-rag fetch original` · `source` · `chunk` · `manifest` · `expansion` | 重新取出原文字节 · 规范化结果 · 分块 · 过去的检索 · 过去的扩展 |
| `ai-rag manage profile --config <file>` | 注册处理配置 (JSON 文件: `embedding` · 可选 `llm` · `normalizer`) |
| `ai-rag manage status` · `list` · `show` | 状态 · 列表 · 查看单个原文 |
| `ai-rag manage retry` · `reindex` · `restore` | 重试失败的任务 · 用其他配置重新处理 · 恢复已删除的原文 |
| `ai-rag manage backup` · `restore-backup` | 创建备份 · 从备份恢复 |
| `ai-rag manage doctor` · `verify` | 安装诊断 · 数据库检查 |

除 `init` 外的数据库命令都接受 `--db <db>` 和 `--key-fd <fd>`。

### 示例

```bash
K="--db my.db --key-fd 3"

# 1) 注册处理配置 — 记下响应 data 里的 profile_key
.venv/bin/ai-rag manage profile $K --config profile.json 3< my.key

# 2) 登记一条文本原文
.venv/bin/ai-rag add $K --request-id req-1 --collection notes --source-key note-1 \
  --text "hello" --profile-key <profile_key> 3< my.key

# 3) 检索 — 之后用响应里的 manifest_id 做 expand · fetch manifest
.venv/bin/ai-rag search $K --collection notes --query "hello" \
  --profile-key <profile_key> --top-k 5 3< my.key
```

`profile.json` 的 `embedding` 里填写 `provider`(`lmstudio` 或 `openai-compatible`)· `endpoint` · `model` · `revision` · `dimension` · `tokenizer_revision`(固定的 commit 或 tag)。完整字段见 [src/airag/embeddings.py](src/airag/embeddings.py) 中的 `EmbeddingSpaceConfig`,LLM 字段见 [src/airag/llm_enrichment.py](src/airag/llm_enrichment.py) 中的 `ChatCompletionConfig`。从 Python 直接调用的示例是 [examples/explicit_consumer.py](examples/explicit_consumer.py)。

### 密钥处理

- 密钥是 32 字节的原始值,只从 `--key-fd` 指定的已打开文件描述符读取。命令行参数和日志里不会出现密钥。
- 目前还不能从 macOS Keychain 读取密钥。

### 已知限制

- 向量检索是全量比较(O(N))。不声称验证过 ANN 性能或韩语关键词检索质量。
- 不支持: XLSX 的重新计算和 array/data-table 公式、受保护或分发用的 HWP、DOCX 中位图以外 DrawingML 的自动渲染。
- HWP/HWPX 的锚点以节 · 段落 · 表为单位(没有渲染后的页码)。
- 文档内的图片会被提取并保留,但不会自动做视觉处理。
- 不会自动证明模型权重的修订版本。运维者声明的值与运行时 fingerprint 分开保存。

## 环境要求

- Python 3.13 及以上、低于 3.15 · `uv` 0.10.0 及以上
- 嵌入服务: 兼容 OpenAI 的 `/v1/embeddings` (LM Studio 等)
- 可选: 兼容 OpenAI 的 chat 服务 (LLM 预处理)
- 可选: HWP5 文档 = `java` + 本地 hwplib jar (文档适配器设置 `hwp_classpath`)
- API 密钥 / 账号: 引擎本身不需要

## 链接

- [docs/README.md](docs/README.md) — 文档导览 (韩语)
- [docs/PLAN.md](docs/PLAN.md) — 实现计划 · 验证记录 · 支持范围 (韩语)
- [docs/DECISIONS.md](docs/DECISIONS.md) — 设计决策记录 (韩语)
- [examples/explicit_consumer.py](examples/explicit_consumer.py) — 使用方事件适配器示例
- [rag-consumer](../rag-consumer/README.zh-CN.md) — 把对话记录送进这个引擎的配套包
- [AI Feature Pack 目录](../../README.zh-CN.md)
