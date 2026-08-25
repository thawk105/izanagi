---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-acceptance-pole-cost
seq: 3
---

## 再発

### F95

- **再発: 2026-08-25** — 受入直列 pole の費用削減 wave で 3 例目。対象は
  `test_codex_reasoning_ab.py::test_verify_replays_complete_fake_codex_experiment` で、
  T-417 の恒久対応は依然未実施である。今回は台帳の指示どおり runner argv へ
  `--deselect <素の node id>` を足し、期待集合を同 file 内の**非 real-repo の兄弟 node**
  (`test_m5_generated_session_rows_require_set_equality` と
  `test_material_report_certification_scope_is_exact_on_all_return_paths`) へ再照準して
  一度で通した (baseline PASSED・3/3 KILLED・MISMATCH 0)。
  **新しい事実は、再照準が本 wave の当の問い「変更した real-repo node が自分の kill 義務を
  果たすか」を構造的に測れないこと**である。再照準先は変更していない兄弟 node であり、
  変更した node の検出力は harness の観測範囲の外に落ちる。そこで補償として、親が同じ変異を
  `DW-O19` の復元規律で一時注入し、対象 node 単体が赤になることを計算ノードで直接実測した
  (`1 failed`、失敗 assert は当の拒否理由の照合そのもの)。逐語は
  `output/insights/2026-08-25_acceptance-pole-cost-mutation.md` の §2 に残した。
  T-417 が入るまで、real-repo node を**変更する** wave はこの補償実測を省いてはならない。
