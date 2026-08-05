---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t520-measurement-turn
seq: 3
---

## 新規

### {{F:concurrent-dispatch-during-acceptance}}. 受入全走の隣で dispatch する検査を走らせ、9 件の偽の赤を得た [計測汚染] [手順漏れ]

- 事象: docs のみの commit を検査するため `tools/run_tests.py` と
  `tools/check_ai_provenance.py` を同時に起動したところ、受入全走が
  `9 failed, 6444 passed, 20 skipped` で返った。落ちたのはすべて `output/` の
  副作用スナップショット検査 (`test_official_*` 族) で、差分の実体は
  `output/pegasus-dispatch/<nonce>/request.json` と `output/task-runs/pilot.json` —
  **並走させた provenance 監査自身が dispatch 中に書いた receipt** だった。
  同じ tree を単独で再走すると `6453 passed, 20 skipped` (rc=0) で、赤は再現しない。
- 根本原因: `check_ai_provenance.py` は login で打つと計算ノードへ自動 dispatch し、その過程で
  `output/` 配下へ receipt を書く。一方で受入側には「実行前後で `output/` が bit 単位で不変」を
  assert する検査群がある。両者は互いを知らないため、同時に走らせると後者が前者の正当な
  書き込みを副作用として検出する。テスト側の隔離漏れではなく、**同じ作業木で 2 つの
  書き込み主体を同時に動かした操作側の誤り**である。
- 恒久対応: memory `no-concurrent-dispatch-during-acceptance` — 受入全走の最中に
  `output/` へ書く検査・ツール (provenance 監査、dispatch を伴うもの) を投入しない。
  既存の `no-acceptance-run-during-mutation` と同型の規律で、対象を変異 harness から
  「dispatch receipt を書く全経路」へ広げたものである。
- 再発検知: 赤が `output/pegasus-dispatch/` や `output/task-runs/` の差分だけを指しているなら、
  実装差分へ帰属する前に単独再走で再現性を実測する (`DW-O18`)。本件は単独再走で消えた。
