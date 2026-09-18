---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2746-k2-loop-round2
seq: 3
---

## 新規

### {{F:evidence-dir-prewritten-by-parent}}. 親が job body 所有の evidence attempt dir へ投入直後に file を置き、job を preflight で失った [手順漏れ]

- 事象: P3 段 4 loop の job body (`tools/pegasus/p3_s4_loop_pegasus.sh`) は `allocation-qstat.stdout` を自分で書き、既存なら
  `allocation qstat evidence is not fresh` で rc=2 にする。親は投入直後の `qstat -f` の写しを同名で attempt dir に置いたため、
  attempt-0001 (`4947.nqsv`) は Elapse 7 秒・driver 未起動で拒否された。評価は attempt-0002 (`4954.nqsv`) の 1 本で済んだが、
  投入は 2 本になり、ユーザー裁定 D2120 項 1 の「再投入なし」の文言から逸脱した (事後承認を裁定パッケージ候補として返した)。
- 根本原因: `tools/pegasus/README.md` §7 の投入手順が attempt dir を `mkdir` するとだけ書き、「job body が所有し投入側は触らない」
  ことを書いていなかった。親は evidence を揃えるつもりで所有権を侵した。
- 恒久対応: `tools/pegasus/README.md` §7 に「attempt directory は job body が所有する。投入側は `mkdir` 以外に何も置かない」を
  明記した (本 wave)。親の qstat 写しは job root 直下 (evidence dir の外) へ置く。
- 再発検知: job body の既存 fresh 検査 (263〜265 行) がそのまま検知器である。attempt-0001 の `job.stderr` を
  `output/insights/2026-09-18/t2746-k2-loop-round2/evidence/attempt-0001/` に残した。

## 再発

### F570

- **再発: 2026-09-18** — 層 3 の `verifications.items` には閉包検査そのものが無く、producer が `verify_done` に足した
  `commit_witness` (2026-08-11) と `proof_surfaces` (2026-09-03) が消費側 schema に届かないまま、現行の loop 型 campaign を
  renderer が `additionalProperties` 違反で描画できない状態が続いていた (2026-09-18 に 1 巡目 campaign の描画で発覚、台帳未記録)。
  D830 の導出型閉包を `verify_done` にも置き、`_view_row` の除外集合と qualification 分岐の key を AST で導出して schema と照合する
  検査を `orchestrator/tests/test_layer3_report.py` に足した ({{D:layer3-mechanism-layer-v3-agent-outputs}})。
