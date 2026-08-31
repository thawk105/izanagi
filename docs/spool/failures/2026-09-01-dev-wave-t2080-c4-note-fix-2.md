---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-01
wave: dev-wave-t2080-c4-note-fix
seq: 2
---

## 新規

### {{F:historical-rollout-corpus-vanished}}. repo 外の実 rollout に束縛したテストが、その corpus の消失で受入全走を止めた [テスト代表性] [計測汚染]

- 事象: [T-2080] wave の受入全走 (2026-09-01 01:53 投入) が
  `21 error, 5 failed, 19033 passed, 67 skipped` で落ちた。赤 26 件はすべて
  `orchestrator/tests/test_codex_reasoning_ab.py` に集中し、本 wave の編集面
  (`docs/paper-story/README.md` への 45 行追加と spool fragment) とは交わらない。
  junit の distinct な message は 2 種で、いずれも 2026-07-29 の実 rollout を指す —
  `ValidationError: session 019fac6b-4f74-7a03-aa4d-8a9de22b352c rollout count is 0, expected 1`
  (22 件) と `FileNotFoundError: /home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-...jsonl`
  (4 件)。単独再走も同じ 26 件で落ちたので flake ではない。
- 根本原因: 同 test は `_HISTORICAL_SESSIONS = Path("/home/SFC/tanab/.codex/sessions")` という
  **repo の外にある実 corpus** に束縛されている。その 2026/07 配下は既に存在せず
  (`~/.codex/sessions/2026` の直下は `08` と `09` だけ)、`~/.codex/` に archived_sessions も無い。
  corpus の寿命を握っているのは repo ではなく codex CLI 側であり、**repo は消失を検知も復元も
  できない。** module scope の fixture `benchmark_snapshots` は
  `if not _HISTORICAL_SESSIONS.is_dir(): pytest.skip(...)` と**根の有無だけ**を見るので、
  部分的な剪定は skip にならず 26 件の hard red になる。
- 恒久対応: **未定。裁定パッケージとしてユーザーへ返す** ([T-2080] wave が停止した理由)。
  択一は (a) fixture の不在判定を「必要な rollout が実在するか」まで下げて skip させる、
  (b) 判定に使う rollout を repo 内の凍結 corpus へ移し repo が寿命を握る、
  (c) 該当 node を hold へ登録する、のいずれか。**(c) は既存 F を証拠に要求する `DW-O18` の
  条件を満たさないので本 wave では採らなかった。** テストを緩めて緑にする経路は採らない。
- 再発検知: 受入全走の赤が `test_codex_reasoning_ab.py` に集中し、message が
  `rollout count is 0` または `~/.codex/sessions/<過去日付>` の `FileNotFoundError` を含むなら本件型である。
  `ls ~/.codex/sessions/2026` で必要な月が実在するかを先に確かめる。
