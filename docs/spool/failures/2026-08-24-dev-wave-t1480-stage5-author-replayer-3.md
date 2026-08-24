---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-24
wave: dev-wave-t1480-stage5-author-replayer
seq: 3
---

## 新規

### {{F:mutation-timeout-counts-queue-wait}}. dispatch 経路の変異 TIMEOUT を「変異がハングした」と読み、無実の変異を fail-open 側へ倒しかけた [計測汚染] [手順漏れ]

- 事象: [T-1480] の変異 probe で M4 が `timeout_seconds: 300` に掛かって TIMEOUT になり、
  harness が停止した。前セッションの記録は「hang しうる変異」として扱われる形で残った。
  実際は queue 待ちだけで 300 秒を使い切っており、変異自体は 10 秒で完走して 17 件の
  失敗 node を出していた (= 十分に kill されていた)。
- 根本原因: `--runner-mode dispatch` では `timeout_seconds` が job の **queue 待ちを含む**
  壁時計である。同じ spec の M1/M2/M3 は queue が空いていたため 27〜30 秒で完走しており、
  混雑した瞬間に投入された 1 件だけが timeout になった。判定根拠は dispatch job 942745 の
  scheduler 逐語 `Created 14:14:30` / `Started 14:19:47` / `Ended 14:19:53` / `Elapse: 10S`。
- なぜ危険か: F32 の恒久対応 3 は timeout を「その変異が fail-closed から fail-open へ倒れた
  証拠」として記録すると定めている。queue 由来の timeout をそのまま読むと、**実際には検出されて
  いる変異を「gate をすり抜けた」と台帳へ書く**ことになる。誤りの向きが安全側でない。
- 恒久対応: memory `mutation-timeout-includes-dispatch-queue-wait` — TIMEOUT を結論にする前に
  submission dir の job stderr (`izdw-*.e<id>`) を読み、`Started - Created` (queue 待ち) と
  `Elapse` (実行時間) を分離する。`Elapse` が小さければ変異は無実で spec の timeout が
  短すぎただけと判定し、`timeout_seconds` を混雑を見込んだ値へ再登録して走り直す。
- 再発検知: 変異結果に TIMEOUT が 1 件でもあれば、その変異の submission dir の
  `Elapse` を台帳へ併記する。併記が無い TIMEOUT を fail-open の証拠として採用しない。

### {{F:orphan-hold-collapses-resume-diagnosis}}. orphan-hold を解除せず変異を resume し、投入側の拒否を変異側の PARSE_ERROR として記録した [手順漏れ]

- 事象: 上記 M4 の abort が残した orphan-hold (`orphan-holds/942745.nqsv.json`) を解除しないまま
  `--resume` を投入した。dispatch は即座に拒否し、harness からは
  `receipt 表示行が exactly one でない: 0` / `rc=16` / 所要 0.113 秒の **PARSE_ERROR** としてしか
  見えなかった。原因が変異側 (出力が読めない) か投入側 (そもそも走っていない) か区別できず、
  「canonical stdout から failed node を抽出できない」という変異側の言葉で記録が残った。
- 根本原因: harness は resume の前に orphan-hold の有無を検査しない。hold は
  「以後この worktree からの dispatch を止める」ラッチなので、投入拒否は必ず収集段の
  parse 失敗として現れる。所要 0.113 秒という値だけが投入側の異常を示していた。
- 恒久対応: memory `dispatch-qdel-arms-f47-latch` の復旧順 (qstat で不在または終端を確認 →
  dirty source を復元 → clean/HEAD を確認 → hold と sidecar を削除) を **resume の前に必ず** 通す。
  F453 が定めた 2 種 sidecar の両方確認と同じ位置で行う。
- 再発検知: 変異の PARSE_ERROR / rc=16 を見たら、その run の `duration_s` を先に見る。
  baseline 所要より 2 桁小さい値なら変異側ではなく投入側を疑い、hold の有無を確認する。

## 再発

### F333

- **再発: 2026-08-24** ([T-1480] wave)。`check_ai_provenance.py` を親の 2 分 command timeout の
  中で走らせた。この checker は既定の自動判定で計算ノードへ dispatch するため、親が SIGTERM
  された時点で job が孤児化し、wave worktree に pending orphan hold が武装した。
  今回は job 側が短く終わったため hold は自動解除され二次被害は出なかったが、成立していれば
  以後この worktree からの dispatch (受入を含む) が全面停止していた。
  恒久対応は既出 (長時間走りうる検査は余裕あるタイムアウト、または背景経路で起動する) —
  守らなかったこと自体が事象である。**「git を読むだけの checker だから軽い」という見積りが
  誤りで、dispatch するか否かは checker 側の自動判定が決める。**

### F383

- **再発: 2026-08-24** ([T-1480] wave)。変異 probe を detached で投入した後、待ち時間に
  記録 fragment 3 本と insight 1 本を同じ wave worktree へ書いた。`mutation_worktree.py` の
  wrapper は source 共有木の `status` / `submodule-status` の stdout bytes が走行の前後で
  不変であることだけを主張するので、untracked file が 4 件増えた時点でこの主張が破れ、
  wrapper は `shared_snapshot_matches: false` / rc=125 で終わった。
  変異の測定自体は固定 commit `5f9bc54b` の隔離 worktree で走っており、変異対象
  (`tools/codex_reasoning_ab.py`) には触れていないため実体は健全だが、**wrapper の保証は無効**である。
  恒久対応は既出 (変異走行中に tree へ書かない) — 守らなかったこと自体が事象である。
  今回は「編集したのは docs であって実装面ではない」という区別が無関係であることが顕在化した。
  **wrapper が見ているのは `git status` の bytes であり、追跡・未追跡も docs・実装面も区別しない。**
- 回復: 記録を先に commit して木を clean にしてから、本走を無干渉で走らせ直した。
