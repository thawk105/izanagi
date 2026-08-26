## 段 1 brief

**scope:** JSONL を行へ切っている 6 箇所を `splitlines()` から `split("\n")` へ変える。
U+2028 / U+2029 を含む event 行を受理する負例テストを同時に置く。それ以外は変えない。

**確定済みユーザー裁定:** {{D:jsonl-line-split-ratified}} (2026-08-25 裁定、2026-08-26 /rulings 全件で追認)。
裁定本文は branch worktree-rulings-20260826-adopt の
docs/spool/decisions/2026-08-26-rulings-20260826-adopt-2.md (未 land、実測で確認済み)。
却下済み選択肢: 「U+2028 / U+2029 を含む行を弾く拒否分岐を足す」— 正当な入力を壊す側に倒れる。

**実測で判明した裁定前提のずれ (段 4 で再裁定する材料、裁定は覆さない):**
- 実際に脆弱なのは `orchestrator/codex_roles/events.py:316` の 1 箇所だけ。ここだけが str を
  分割する。`str.splitlines()` は U+2028 / U+2029 / NEL / VT / FF でも切る。
- `tools/codex_worker_launch.py` の 5 箇所は **bytes** を分割する。実測では
  `bytes.splitlines()` は `\r` `\n` `\r\n` でしか切らず、U+2028 / U+2029 では切らない。
  よってこの 5 箇所は現状でも F609 の経路ではない。裁定どおり変えるが、これは
  一様化と多重防護であって単独の修理ではない。
- `tools/codex_worker_launch.py:327` は JSONL ではなく `git rev-parse --show-toplevel` の
  stdout であり、**対象外**。`split("\n")` にすると末尾改行で要素が 2 個になり
  `len(top_level_lines) != 1` が常に真となって tool が常時失敗する。
  T-1731 の「codex_worker_launch.py の 6 箇所」はこの 1 行を数え込んだ過大計上である。
- したがって裁定文の「6 箇所」= events.py 1 + codex_worker_launch.py 5。T-1774 の
  「parse_jsonl を含む 6 箇所」と一致する。
- 閉包検査: `strict_json_loads` の他の呼び手は文書全体を読むもので行分割をしない。
  行分割による JSONL 解釈は上記 6 箇所で閉じている。
- 凍結 pin 閉包: 両 file を bytes で pin している live な manifest / checker は無い
  (`DW-O08` / `DW-O09` / `DW-O10` は発火しない)。過去 wave の insight 成果物に path が
  現れるだけで、現用の pin ではない。

**不変条件 (絶対規律 2 を緩めない):**
- 正常な JSONL 入力に対する挙動は不変。受理集合は「壊れていた入力」の側にだけ広がる。
- `strict_json_loads` の厳格性、1 行 byte 上限 (`max_line_bytes`)、全体 byte 上限、
  空行 skip の既存規律を 1 つも弱めない。
- 拒否分岐の追加・置換をしない (裁定で却下済み)。

**成果物影響 (DW-G05):** 実装しない場合、U+2028 / U+2029 を含む tracked file を読む必要のある
wave は codex 子の全 attempt を構造的に失い続ける (F609 実測: 6/6 失敗、完成済み成果物 6 本と
約 2 時間の喪失)。台帳の数値ではなく dev-wave 実行そのものの可用性が変わる。

**変更面アンカー表 (実測、実アンカー):**

| # | file:line | 現在の式 | 分割対象の型 | 変更後 |
|---|---|---|---|---|
| 1 | orchestrator/codex_roles/events.py:316 | `text.splitlines()` | str (parse_jsonl 本体) | `text.split("\n")` |
| 2 | tools/codex_worker_launch.py:1273 | `complete.splitlines()` | bytes (live stdout) | `complete.split(b"\n")` |
| 3 | tools/codex_worker_launch.py:1406 | `complete.splitlines()` | bytes (live rollout) | `complete.split(b"\n")` |
| 4 | tools/codex_worker_launch.py:2335 | `raw.splitlines()` | bytes (記録済み rollout) | `raw.split(b"\n")` |
| 5 | tools/codex_worker_launch.py:4097 | `closed.splitlines()` | bytes (resume 時 stdout) | `closed.split(b"\n")` |
| 6 | tools/codex_worker_launch.py:4119 | `raw.splitlines()` | bytes (封印済み rollout) | `raw.split(b"\n")` |
| 対象外 | tools/codex_worker_launch.py:327 | `completed.stdout.splitlines()` | str (git 出力) | 変えない |

**親の provisional 裁定 (攻撃対象):**
- (P1) 負例テストは新規 file `orchestrator/tests/test_codex_jsonl_line_split.py` に置く。
  理由: 自然な置き場である `orchestrator/tests/test_codex_worker_launch.py` は稼働中の
  wave t1719 (pid 3882354、branch worktree-dev-wave-t1719-nproc-parity) が編集中で、
  編集面が重複する。新規 file には自走 harness を付ける。
- (P2) `tools/codex_worker_launch.py:327` は変えない (上記の実測理由)。
- (P3) 負例テストは 6 箇所すべてに 1 本ずつ対応させる。bytes 側 5 箇所は U+2028 / U+2029 を
  含む event を「切らずに 1 行として通す」ことを直接検査する。
- (P4) 変異事前登録は 6 箇所すべてを `splitlines()` へ戻す変異 6 本とする。

**並列分割方針:** 受理集合が変わるため `DW-C00` の軽量版に該当しない。段 2 プラン、段 3 敵対相談
2 本、段 5 実装子 1 本 (編集面が 2 file と 1 新規 test file で小さく分割の利がない)、
段 6 敵対レビュー 2 本 + fix を回す。

**環境:** login node で pytest 焦点走。受入全走は `tools/dev_wave_wait.py acceptance`。

## dev-wave 改善候補
