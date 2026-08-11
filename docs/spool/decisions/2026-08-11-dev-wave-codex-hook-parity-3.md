---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-codex-hook-parity
seq: 3
---

## {{D:codex-hook-wiring}}. Codex へ PreToolUse を配線し、発火は実測 gate で確かめる

**決定:** `.codex/hooks.json` の PreToolUse に `^apply_patch$` と `^Bash$` を配線する。判定核は
Claude と同じ `guard_write` / `guard_bash` を使い、Codex 専用の判定を二重実装しない。
`apply_patch` の path 抽出だけを `guard_write` に足し、相対 path は payload の `cwd` から絶対化する。
`delete` と `move` の元は lexical 判定も併用する。抽出は拒否を増やすためだけに使い、
抽出できたことを許可の根拠にしない。

Codex は hook が exit 2 のときだけ止まり、hook command 自体の失敗は素通しになるため、guard を
直接呼ばず `hooks/codex_guard.sh` (`0`/`2` 以外をすべて `2` へ写す) を経由し、bootstrap も
解決できなければ `exit 2` とする。

信頼登録の無い hook は無警告で無視されるため、**配線の存在を防護の証拠に数えない**。
`tools/check_codex_hooks.py` が使い捨て領域で allowed control と protected control を両方測り、
`apply_patch` と `Bash` の双方が発火しなければ非 0 とする。認証・枠・timeout・tool 未試行も非 0 で、
`skip` で緑にしない。trust bypass は argv に入れない。

本配線が閉じたのは `apply_patch` 経由と、Claude と同じ既知限界つきの Bash 経由だけである。
MCP / apps / plugins / 子の書込み面、script 経由・変数展開・persistent shell、
`output/s8b-freeze` への Bash 直接書き込みは開いたままであり、Claude と同等の防護になったとは記さない。
本決定は D55 / D56 の native role 再開条件を一切緩めない。

**理由:**
- Codex 単独運用では sandbox の外で manager を動かさないと受入全走を投入できない (計算ノードへの
  投入も上限付き実行も sandbox 内からは失敗することを実測)。その状態では hook だけが機械防壁になる。
- 判定核を共有すれば受理集合が 1 か所で決まり、Claude と Codex の drift が構造的に起きない。
- 「配線した」ことと「発火する」ことは別であり、後者を測らない検査は恒真になる (規律 6)。

**却下した選択肢:**
- Codex 専用の guard を新設する — 判定核が二重になり受理集合が分岐する。
- 配線の存在と JSON 妥当性だけを検査する — 信頼未登録でも緑になり、守っていないのに緑を作る。
- 発火検査を受入全走へ自動登録する — 受入は計算ノードで走り、そこは直接の外部通信ができず
  Codex CLI の到達性も未実測である。前提が立たないまま必須化すると受入が理由なく赤になる。
- `--dangerously-bypass-hook-trust` を gate に使う — 信頼が無いまま緑になり、gate の意味が消える。
