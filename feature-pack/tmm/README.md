<div align="center">

# tmm

**A one-screen TUI to pick, preview and message dozens of tmux agent seats from your phone over SSH — without attaching**

[English](README.md) · [한국어](README.ko.md) · [日本語](README.ja.md) · [简体中文](README.zh-CN.md)

</div>

> Part of [AI Feature Pack](../../README.md) — packs are independent; install only what you need.

## What it does

- Shows each tmux session as one seat row — category, whether an agent runs, status, model, last message time, age, folder. Narrow it down with a fuzzy filter.
- Puts seats waiting for you (`HUMAN` · `BLOCK` · `STUCK`) at the top and rings the terminal bell when a new one appears.
- Previews a pane without attaching. `Enter` attaches; `C-a d` detaches back to the picker.
- `^S` sends a message to the seat under the cursor and checks delivery · `^K` closes the seat.
- `^D` ended sessions view: finds agent sessions lost to a reboot or kill from their transcripts and restores them with resume.
- `^F` fork hands a conversation over to another agent; `^Y` shows the conversation (transcript) path.

Built for Claude Code · Codex · OMX · OpenCode · Command Code · Pi seats started with `tmuxc`, but it works on plain tmux sessions too.

## Quick start

```bash
brew install bash tmux fzf               # if missing (bash 4+ required)
bash feature-pack/tmuxc/install.sh       # the required tmuxc pack first
bash feature-pack/tmm/install.sh
tmm doctor                               # check dependencies and environment
tmm                                      # open the TUI
```

## Install

### Let your agent do it

Tell your agent: "Read `feature-pack/tmm/INSTALL.md` and install it." The agent checks prerequisites → runs `install.sh` → sets category rules → verifies → (optional) fork model aliases and phone access. Install time (~1 min).

### Manual install

What `install.sh` does:

1. Checks `bash>=4` · `tmux` · `fzf` (exit 2 with install hints if missing). Stops if `tmuxc` is not installed.
2. Copies the binary and libexec to `~/.tmm/versions/<version>/core/` and updates the `~/.tmm/current` symlink.
3. Creates the `~/.local/bin/tmm` symlink (backs up an existing regular file) and adds `~/.local/bin` to PATH in `~/.zshrc` / `~/.bashrc` if needed.
4. Warns if `~/.zshrc` has `alias tmm=` (the alias would shadow the binary).
5. Copies examples to `~/.tmm/categories` · `~/.tmm/models` if they are missing (keeps existing ones) and creates `~/.tmm/forks/`.
6. Verifies with `tmm doctor`.

```bash
bash feature-pack/tmm/install.sh
tmm doctor
tmm ls | head                          # if the status column shows ?, check the seat-scan path → TMM_SCAN
bash feature-pack/tmm/test/verify.sh   # regression test on an isolated tmux socket (existing sessions untouched)
bash feature-pack/tmm/uninstall.sh     # uninstall (~/.tmm/categories is kept)
```

### Category rules

Write one `glob<TAB>label` per line in `~/.tmm/categories`. The first match from the top wins. A session that matches no rule gets the first token of its name (up to 5 characters before `-` / `_`) after the role prefix (`TMM_CAT_STRIP`, default `FB_ ft-`) is removed, so the file only needs what this rule cannot do (merging aliases, unifying case). For names made of lowercase letters, digits and `-` in the form `<project>-<team>-<role>…`, when the third token is a reserved role word (master · arch · da · tester · checker · analyst · pm · nano · repro · tool), the second token (the team) becomes the label.

```bash
tmux ls -F '#S' | sed 's/#[0-9]*$//' | sort -u     # list the current session prefixes
```

### Phone access (Termius example)

1. Mac: System Settings → General → Sharing → turn on Remote Login.
2. Create a dedicated key, add the public key to `~/.ssh/authorized_keys`, keep the private key in a password manager and paste it into the Termius Keychain on your phone.
3. Address: `ipconfig getifaddr en0` on the same Wi-Fi, `tailscale ip -4` when away (Tailscale recommended).
4. Termius host: address · port 22 · user · key · **Startup command = `tmm`** — the picker opens as soon as you connect.
5. Use Ctrl on the phone keyboard toolbar for `^S` and the like. With a `C-a` tmux prefix, detach with Ctrl → a → d.

```bash
ssh-keygen -t ed25519 -f ~/.ssh/mobile_ed25519 -N ''
cat ~/.ssh/mobile_ed25519.pub >> ~/.ssh/authorized_keys
# self-test from the desktop — non-interactive ssh has a short PATH, so wrap it in zsh -ilc
ssh -i ~/.ssh/mobile_ed25519 -o IdentitiesOnly=yes <IP> -t 'zsh -ilc tmm'
```

## Usage

### One row = one seat

| Column | Meaning |
|---|---|
| category | from `~/.tmm/categories`, otherwise the first token of the session name after the role prefix |
| `●` / `○` | agent running / shell only |
| session name | tmux session name. 20–44 cells depending on width · when cut, the middle folds and the trailing `#N` stays |
| `HUMAN` `BLOCK` `STUCK` `IDLE` `BUSY` | seat-scan verdict. HUMAN = waiting for you, BLOCK = stopped by an API error, STUCK = unsubmitted input left |
| model | short model name (e.g. `opus5·1m`). `·1m` = 1M context window |
| `12:33` / `12~33` | last message time. `:` = read from the Claude done marker, `~` = no marker, last tmux output time |
| `26m` | time since then (m / h / d) |
| folder | last folder of the pane cwd. 6–28 cells depending on width |

Sorting: `^T` most recent (default — the seat that spoke last is on top) · `^W` waiting seats pinned on top, then most recent · `^G` most recent within each category · `^H` waiting seats only.

### Keys

| Key | Action |
|---|---|
| ↑↓ / typing | move the cursor / fuzzy filter (`HUMAN`, part of a session name …) |
| `Enter` (category pane) · `Esc` / `⌫` (list, empty query) | switch panes — category pane ↔ list. `→` / `←` do the same |
| `Enter`, `^E`, double tap | attach. Detach with `C-a d` to return to the picker |
| `^S` | message the seat under the cursor — `[mobile→session] …` prefix + delivery check after 2 s. Blocked for seats without an agent |
| `^K` | close the seat (tmux session + the agent in it) |
| `^F` | fork — continue the conversation in a new agent session |
| `^Y` | transcript index — show the transcript path of the session under the cursor |
| `^H` / `^A` | waiting seats only / all |
| `^T` / `^W` / `^G` | most recent / waiting first / by category |
| `^V` | hide / show the category pane (hidden = tab bar, rotate with `Tab` / `S-Tab`) |
| `^R` | rescan status (ignores the cache · keeps sort and filter) |
| `^U` | cycle the preview refresh interval 1 → 5 → 10 → 15 s |
| `^P` / `^O` | preview off · on / bigger · smaller |
| `^D` / `^A` | ended sessions view ↔ live seats view |
| `^/` | redraw the help header. `?` is just a filter character |
| `^X` | quit |

### Split screen

- Inside tmux, the left is the category pane and the right is the session list (+ pane preview). Moving ↑↓ in the category pane changes the list right away.
- Running `tmm` with no arguments opens the picker inside a tmux session named `tmm`, so resizing the terminal window does not kill it. Each window you open gets its own picker (`tmm`, `tmm-2` …).
- Below 120 columns (phone) the category pane is 11 cells, otherwise 16. The preview sits on the right when the list pane is 120 columns or wider, otherwise below.
- The preview shows the newest content first and cuts the input box and statusline at the bottom to save phone screen space.
- With `TMM_SPLIT=0` or outside tmux you get the tab bar layout.

### Ended sessions view (`^D`)

The list switches to agent sessions that are no longer in tmux. Whether they were started with `tmuxc` or straight from a terminal, they are found as long as the transcript remains.

| Key · mark | Meaning |
|---|---|
| `◌` | ended |
| badge | where it was found: `SNAP` = `tmuxc save` snapshot (argv as saved) · `CC` Claude · `CDX` Codex · `CMD` Command Code · `OC` OpenCode |
| `^]` / `^\` | widen / narrow the window by 12 hours (starts at the last 12 hours · judged by transcript mtime) |
| `^L` | show every generation of a lineage (default: latest only) |
| `^T` / `^W` / `^G` | most recent / SNAP first / by category |
| `Enter` | restore — creates a tmux session in the original cwd, relaunches the agent with `--resume <session_id>` and attaches |
| `^B` | selective restore mode — enters with all visible rows checked, toggle with space, press `^B` again to restore only the checked ones (parallel batches of 5 · no attach) |

- The preview shows the last user / assistant message of that session.
- Restore model: argv from the snapshot for SNAP, otherwise the transcript `model` + `--effort high`. Claude gets the 1M window (`[1m]`) unless it is the fable family.
- Pi sessions are restored when a `tmuxc save` snapshot exists. `--scan` supports Claude and Codex only.
- `^S` (message) is not available in this view. Restore first.

### fork (`^F` · `tmm fork`)

Moves a live or ended session's conversation to another agent or model (for example after a rate limit). The source conversation is not touched.

- Same engine = native `tmuxc fork` branch — full history, new conversation id.
- Different engine = new `tmuxc open` session + context injection — the prompt gets the transcript path and a recent excerpt (`~/.tmm/forks/<time>-<source>.md`).
- In `^F`, pick a name · agent (claude / codex / opencode / cmd) · model (fzf search); the session is created and you return to the picker. The default name turns the source's `#N` into `#N+1`. Cancel at any step with `^C`.
- Model aliases = `~/.tmm/models` (yours · takes priority) + `~/.tmm/models.generated` (made by `tmm models refresh`). For OpenCode the `--model` prefix is the gateway, chosen by `TMM_MODELS_PROVIDER` (default `openrouter`) — `opencode/` = zen, `openrouter/` = OpenRouter.
- Claude gets `--ctx 1m` automatically unless it is the fable family.

```bash
# --dry-run only prints the command (no side effects)
tmm fork my-app-dev#1 --agent codex --model <alias> --dry-run
tmm fork my-app-dev#1 --agent claude --model sonnet --attach     # same-engine native fork
tmm models refresh                                    # live lists → ~/.tmm/models.generated
TMM_MODELS_PROVIDER=opencode tmm models refresh opencode
tmm models find <query>                               # search aliases and model ids
```

### Transcript index (`^Y` · `tmm idx`)

- `^Y` shows `agent · session_id · cwd · transcript · match` for the session under the cursor (any key returns). Use it to tell an agent "the earlier conversation is in this file".
- `tmm idx NAME|SID` prints the same from the CLI · `--path` = path only · `--json` = JSON.
- `match`: `exact` (exact name match) · `cwd` (by cwd) · `fallback` (most recently active file of a live session).

### Auto refresh

| Tier | What | Default interval |
|---|---|---|
| pane | redraws only the preview of the seat under the cursor | 1 s (`^U` cycles 1/5/10/15 · `TMM_AUTO_PREVIEW`) |
| all seats | recomputes status · last time · sort | 20 s fixed (`TMM_AUTO`) |

It pauses while you are attached and resumes after `C-a d`. After a refresh the cursor stays on the seat you were looking at, and the filter stays.

### CLI subcommands

```bash
tmm                 # TUI
tmm --auto N        # TUI, preview auto refresh every N s (0=off)
tmm ls [PAT]        # text list (filter)
tmm h               # HUMAN/BLOCK/STUCK seats only
tmm p NAME [N]      # last N lines of the pane
tmm s NAME "msg"    # message (guard + delivery check)
tmm a NAME [-i]     # attach (-i: keep the desktop window size)
tmm kill NAME [--yes]                 # close a seat
tmm ss              # raw seat-scan output
tmm save            # tmuxc save (needs tmuxc)
tmm doctor          # check dependencies and environment
tmm menu            # numbered menu when fzf is missing
tmm dead [PAT] [--since H] [--all]    # list ended sessions
tmm dp NAME|SID [N]                   # last N lines of an ended session's conversation
tmm restore NAME [--dry-run]          # restore one ended session → attach
tmm restore-all [--since H] [--dry-run] [--yes]   # restore everything in the window (no attach)
tmm idx NAME|SID [--json|--path]      # transcript path
tmm fork SRC --agent AG --model M [--name N] [--cwd C] [--effort E] [--ctx 1m] [--prompt P] [--dry-run] [--attach]
tmm models [AG]                       # list fork model aliases
tmm models refresh [AG...]            # rebuild the generated list from live lists
tmm models find QUERY                 # search aliases and model ids
```

### Settings

| Item | Location / variable | Default |
|---|---|---|
| category rules | `~/.tmm/categories` (`TMM_CATEGORIES`) | example copied at install |
| category role prefixes | `TMM_CAT_STRIP` | `FB_ ft-` (space separated) |
| fork model aliases | `~/.tmm/models` (`TMM_MODELS`) | example copied at install · wins over the generated list |
| generated fork models | `~/.tmm/models.generated` (`TMM_MODELS_GEN`) | made by `tmm models refresh` · do not edit |
| OpenCode provider | `TMM_MODELS_PROVIDER` | `openrouter` |
| fork excerpt folder / message count | `~/.tmm/forks/` (`TMM_FORKS`) / `TMM_FORK_EXCERPT_N` | 40 |
| status scan cache | `TMM_CACHE_TTL` | 20 s (`^R` ignores it) |
| seat-scan path | `TMM_SCAN` | installed `libexec/seat-scan.sh` → `~/.claude/skills/tmuxc/scripts/seat-scan.sh` |
| preview lines | `TMM_PREVIEW_LINES` | 40 |
| pane auto refresh | `TMM_AUTO_PREVIEW` / `tmm --auto N` / `^U` | 1 s · 0 = off |
| all-seats auto refresh | `TMM_AUTO` | 20 s · 0 = off |
| bell on new waiting seat | `TMM_BELL` | 1 (0 = off) |
| start screen | `TMM_TAB` | 1 = tab view · 0 = list |
| split screen | `TMM_SPLIT` | 1 (inside tmux only) · 0 = tab bar |
| ended view start window | `TMM_DEAD_SINCE` | 12 (hours) |
| live grace | `TMM_LIVE_GRACE` | 90 s — a transcript written within this is treated as live |
| restore boot wait | `TMM_RESTORE_TRIES` | 20 (× 3 s) |
| selective restore batch size | `TMM_RESTORE_BATCH` | 5 |

### Known limits · troubleshooting

- The done marker has only hours and minutes, no date. A seat left for more than two days can show a smaller age.
- fzf cuts the header instead of wrapping it, so on a narrow phone the end of the header may be hidden.

| Symptom | Fix |
|---|---|
| auto refresh does not run · `^Y` does nothing | check the fzf version (≥ 0.54) and `curl` with `tmm doctor` |
| same-engine fork does not carry the history | `tmuxc` < 0.4.0 — reinstall `tmuxc` |
| fork model menu is empty or lacks a model | rerun `install.sh` (copies the example) or `tmm models refresh` → `tmm models find QUERY` |
| OpenCode fork opens on another gateway | check the alias prefix · `TMM_MODELS_PROVIDER=openrouter tmm models refresh` |
| `tmm idx NAME` says "no index" | check `match` in `tmm idx NAME --json` |
| "boot not confirmed" after restore | the session is still there — attach and look at the pane |

## Requirements

- macOS or Linux
- `bash` ≥ 4 (the macOS default 3.2 does not work → `brew install bash`) · `tmux` ≥ 3.2 · `fzf` ≥ 0.54 · `python3` ≥ 3.9 (standard library only) · `curl`
- `tmuxc` ≥ 0.4.0 (`feature-pack/tmuxc`) — `install.sh` stops without it.
- Optional: Tailscale (access from outside) · an SSH client on your phone (e.g. Termius)
- API keys / accounts: none

## Links

- [INSTALL.md](INSTALL.md) — install guide for the agent
- [tmuxc pack](../tmuxc/) — required pack
- [test/verify.sh](test/verify.sh) — regression test
- [AI Feature Pack catalog](../../README.md)
