---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-13
wave: dev-wave-t956-hooks-guard
seq: 2
---

## {{D:hooks-subtree-self-guard}}. hooks/ を guard 自身の判定対象へ加え、例外を exact README 1 件に絞る

**決定:** `hooks/` 配下は subtree 全体を guard_write (Write/Edit/MultiEdit/NotebookEdit と
apply_patch の全 directive) と guard_bash (書き込み・削除・移動) の拒否対象とする。
唯一の例外は exact `hooks/README.md` で、lexical と canonical の両側が README を指し、
現物が regular file・final component が symlink でない・`st_nlink == 1` の場合だけ
Write 系ツールで更新できる。**Bash 側には例外を置かない。**

**理由:**
- 起動前検証から `Popen` までの窓と、worker 存続中の再検証欠如が被覆外だった。保護対象へ
  加えれば、その窓の間の in-band 書き換えが受理集合から外れる。
- 保護面を拡張子で列挙すると取り残しが出る。guard は `python3 <script>` で起動されるので
  `sys.path[0]` が `hooks/` になり、`__pycache__` の `.pyc` と同名 module
  (`hooks/json.pyc` / `hooks/json.so`) が判定の中身を差し替えうる。subtree 全体が正しい。
- Bash 側に README 例外を置くと、(a) 例外に当たった時点で「保護対象に触れた」判定が消えて
  未知 writer が通り、(b) `ln -sfn <別対象> hooks/README.md && printf … > hooks/README.md`
  のような同一コマンド内の置換→書込みが成立する。必要な用途 (docs 編集) は Edit 系ツール
  経由なので、Bash 側に例外を作らなければ両方が構造的に起きない。

**却下した選択肢:**
- `hooks/*.py` と `*.sh` の列挙 — `__pycache__` と import shadow を取り残す。
- README を含めて全面保護 — docs 更新が人間手番になり、必要のない硬直を生む。
- guard_bash 側も README を例外にする — 上記 (a)(b) の穴が開く。
- env / CLI flag / 警告化の逃がし道 — 受理集合を縮める目的と正面から矛盾する。

## {{D:dual-canonical-deny-union}}. path 判定の canonical は 2 系統を保持し、既存判定は deny union にする

**決定:** `realpath(abspath(raw))` (legacy) と `realpath(raw)` (raw) の両方を保持する。
既存 4 判定 (campaign / exploration namespace / s8b-freeze / external ccbench) は
**どちらかが拒否と言えば拒否**とし、hooks 判定は lexical と raw canonical を見る。

**理由:**
- 2 つの解決に包含関係はない。`R/jump` が repo 外への symlink のとき、
  `R/jump/../output/campaigns/…` は legacy では保護面に入り raw では repo 外へ抜ける。
  逆に、symlink を解決して初めて保護面へ入る形は raw だけが捕まえる。
- 片方へ置き換えると、変更前に拒否していた入力が許可へ反転する。受理集合を縮める wave の
  不変条件に反する。deny union なら旧拒否を 1 件も失わず、新しく捕まえる分だけ増える。
- この反例は独立コンテキストの敵対レビュー 2 本が別々に構成した。親は当初「raw 起点は
  拒否しか増やさない」と裁定していたが、これは誤りだった。

**却下した選択肢:**
- raw 単独へ置換 — 上記の反転が起きる。
- legacy 単独のまま (raw を使わない) — symlink component の後ろに `..` が続く形を取り逃がす。
- 判定ごとに使い分ける — どちらを使うかの取り違えが新しい欠陥源になる。

## {{D:guard-self-edit-protocol}}. guard 自身を編集する wave の手順

**決定:** `hooks/` 配下の guard を変更する wave は次の手順に従う。

1. 実装子は保護対象外のファイル (テスト等) を先に書き終える。
2. guard_bash を先に patch する (この保護は Bash 経路だけなので apply_patch は通り続ける)。
3. guard_write は**完成形の全文を保護対象外の作業 directory へ書き**、`py_compile` と
   `decide()` の実測検証を通してから、**最後に 1 回だけ** apply_patch で本番へ入れて
   作業 directory を消す。
4. 親は次の子を起動する**前に統合 commit を作る**。
5. guard の修正が必要になったら、有効化前の commit から作り直す。

**理由:**
- `codex_guard.sh` は tool call ごとに guard を読み直すため、guard_write に判定が入った瞬間から
  同一 worktree での hooks/ 再編集は自分自身に拒否される。**構文エラーでも同じ** — 壊れた
  guard は rc≠0/2 が 2 へ正規化されて全拒否になる。
- `check_codex_hooks.validate_installation` が working bytes と HEAD blob の一致を要求するため、
  **guard を未 commit で変更している間は Codex 子を 1 本も起動できない**。「commit するか
  restore するか」しか選択肢がない。
- したがって「1 回きりの書き込み」を失敗すると作業場ごと詰む。完成形を保護対象外で検証してから
  入れる手順が、回避策を作らずにこれを避ける唯一の形である。

**却下した選択肢:**
- 一時的に判定を無効化する flag / env — 受理集合を縮める目的と矛盾し、fail-open 経路を残す。
- 親が guard を直接編集する — 実装面の Codex author 契約に反する。
- path 付き `git checkout -- hooks/…` での復元 — guard_bash が拒否する (設計どおり)。
  path-free の `git checkout -- .` は通るので、復元はそちらを使う。
