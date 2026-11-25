<div align="center">

# termaid

**Mermaid ダイアグラムをターミナルでそのまま描く CLI `termaid-render` とエージェント用スキル**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> [AI Feature Pack](../../README.ja.md) のパックです。パック同士は独立しているので、必要なものだけ入れてください。

## できること

- Mermaid 記法を読み、スタイル付きのダイアグラムとしてターミナルに描きます(lipgloss による色・枠線・太字)。
- flowchart(`graph LR/TD`) — ノードの形(box · diamond · round · cylinder)、subgraph、エッジラベル。
- sequence diagram — participant、同期・非同期の矢印、`loop` · `alt/else` ブロック。
- class · state · ER ダイアグラムを基本サポートします。
- 入力は stdin パイプ(`echo '...' | termaid-render`)またはファイル(`termaid-render diagram.mmd`)です。
- スキルを入れると、設計の相談やアーキテクチャの説明のときにエージェントが自分でダイアグラムを描きます。

## クイックスタート

```bash
# ソース取得 · ビルドパッチ · ビルド · PATH に置く
git clone https://github.com/MKlolbullen/termaid.git ~/scripts/termaid
cd ~/scripts/termaid
mv internal/tui/builder.go internal/tui/builder.go.wip 2>/dev/null || true
sed -i '' 's/return NewBuilder(catalogueNames()), nil/return errView(fmt.Errorf("workflow builder not yet available")), nil/' internal/tui/menu.go 2>/dev/null || true
go build -o termaid-render ./cmd/render/
cp termaid-render /opt/homebrew/bin/termaid-render

# 最初のダイアグラム
echo 'graph LR
  A[Client] --> B{Auth?}
  B -->|yes| C[Service]
  B -->|no| D[401]' | termaid-render
```

## インストール

### エージェントに任せる

エージェントに「`feature-pack/termaid/INSTALL.md` を読んでインストールして」と伝えます。エージェントは Go の確認 → ソースの clone → ビルドパッチ → ビルド → PATH へのインストール → スキルのインストール → 検証の順に進めます。所要時間 (約2分)。

### 手動インストール

1. ソースを clone します(すでにあれば `git pull`)。
2. ビルドパッチを当てます(必須)。上流の `internal/tui/builder.go` はコンパイルできないので退避し、`internal/tui/menu.go` から `NewBuilder` の参照を消します — 「クイックスタート」の `mv` · `sed` の 2 行です。
3. `go build -o termaid-render ./cmd/render/` でビルドし、PATH にコピーします。
4. スキルを Claude Code のスキルパスにコピーして検証します。

```bash
# スキルのインストール (パックのフォルダで)
mkdir -p ~/.claude/skills/termaid/
cp skill/SKILL.md ~/.claude/skills/termaid/

# 検証
which termaid-render && echo "OK" || echo "FAIL"
termaid-render --help

# ソースを変えたあとの再ビルド
cd ~/scripts/termaid && go build -o termaid-render ./cmd/render/ && cp termaid-render /opt/homebrew/bin/
```

`INSTALL.md` が尋ねるパスと既定値:

| プレースホルダー | 意味 | 既定値 |
|---|---|---|
| `{{TERMAID_SOURCE_PATH}}` | ソースの置き場所 | `~/scripts/termaid` |
| `{{TERMAID_INSTALL_PATH}}` | バイナリの置き場所 | `/opt/homebrew/bin/termaid-render` |
| `{{CLAUDE_SKILLS_PATH}}` | Claude のスキルパス | `~/.claude/skills` |

## 使い方

```bash
# フローチャート (stdin パイプ — いちばんよく使う形)
echo 'graph LR
  A[Client] --> B{Auth?}
  B -->|yes| C[Service]
  B -->|no| D[401]' | termaid-render

# シーケンス図
echo 'sequenceDiagram
  C ->> S : POST /login
  S -->> C : 200 OK' | termaid-render

# ファイルから
termaid-render workflow.mmd

# ヘルプ
termaid-render --help
```

### 対応ダイアグラム

| 種類 | キーワード | 対応 |
|---|---|---|
| Flowchart | `graph TD/LR`, `flowchart` | O |
| Sequence | `sequenceDiagram` | O |
| Class | `classDiagram` | O |
| State | `stateDiagram-v2` | O |
| ER | `erDiagram` | O |
| Gantt | `gantt` | X (コードブロックのみ) |

- ノード: `[box]` · `(round)` · `{diamond}` · `[(cylinder)]` · `((circle))`
- 矢印(sequence): `->>` 同期 · `-->>` 非同期 · `-x` 失敗

### エージェントが使う場面

- 設計の相談(アーキテクチャ · API 設計 · DB スキーマ)、システム構成やコードの流れの説明、「図で見せて」のような依頼で使います。
- キーワード: 「diagram」 · 「chart」 · 「sequence」 · 「flow」 · 「architecture」 · 「mermaid」 · 「termaid」 と、それに当たる韓国語。
- 単純なコード修正 · 短い質問 · コードブロックで足りる場合は使いません。
- ダイアグラムは短く保ちます — 20 行を超えるか、ノードが 10 個以上なら分けます。

### トラブルシューティング

| 症状 | 原因 | 対処 |
|---|---|---|
| `termaid-render: command not found` | PATH にない | `cp termaid-render /opt/homebrew/bin/` |
| `go: command not found` | Go 未インストール | `brew install go` |
| `builder.go compile error` | 上流のコードが未完成 | ビルドパッチを確認 |
| `yaml unmarshal error` | TUI の `init()` パニック | `cmd/render/` だけビルド(TUI を回避) |

## 必要なもの

- macOS
- Go 1.22+ (`go version` · なければ `brew install go`)
- API キー · アカウント: なし

## リンク

- [INSTALL.md](INSTALL.md) — エージェント向けインストール手順
- [skill/SKILL.md](skill/SKILL.md) — エージェント用スキル
- [cli/install.md](cli/install.md) — CLI だけをインストール
- [termaid 上流ソース](https://github.com/MKlolbullen/termaid)
- [AI Feature Pack カタログ](../../README.ja.md)
