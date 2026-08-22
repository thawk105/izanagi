---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: rulings-20260821-calibration-registration
seq: 2
title: rr80/rr20 calibration dev-wave tooling の main land 前に、直近受入赤の解消確認と段6再検証で欠落テストを発見・修正した
---

## 本文

- 別 dev-wave manager セッションとして本 branch (tip cb54bc79) を引き継ぎ、受入・land を完了させる
  依頼を受けた。handoff は「実装完了・targeted test 5 passed・check_docs/spool_fold dry-run 成功」と
  していたが、repo 外 job dir (`dev-wave-jobs/rulings-20260821-calibration-registration/`) に残っていた
  直近の受入全走 (attempt 1、wave_tip=42343ef0、handoff 未記載) が `status: attributable-red`
  (3 ノード、原因は `certify_calibration.sh` の `CALIBRATION_RRATIO: unbound variable`) だったことを
  一次資料 (acceptance-red-check.json) から発見した。後続 commit `f8d32b0e` (fixture 更新、
  attempt 1 より後) がこれを解消していたが、修正後の受入全走は一度も再走されていなかった。
  親が該当 3 ノードを個別に実走し、現 tip で green であることを確認した。
- 信頼境界 (別セッション/別 AI 作業物の main 取り込み) の監査発火条件により、段6敵対レビュー2本
  (Codex reasoning=max、異なるレンズ) を実施した。レンズA は whitelist・binding・quoting を検証し
  問題なしと結論、レンズB は `certify_calibration.sh` の submit-binding 再照合に新設した
  `calibration_rratio` 一致検査に、不一致を実際に拒否することを確認するテストが皆無であると指摘した。
- 親が独立に手動変異検査 (`tools/pegasus/certify_calibration.sh` の該当 1 行を tracked file 一時変異、
  `git diff --stat` で単一箇所を確認後に本走・復元) を行い、同じ結論を確認した:
  `"calibration_rratio": (... == str(rratio) or True)` へ変異させても
  `test_pegasus_tools.py` + `test_pegasus_calibration_workload.py` 計66件が全て green のまま
  (SURVIVED)。fix 用 Codex `role=author` 子 (commit a0937f4e) に
  `test_certify_submit_binding_requires_matching_calibration_rratio` を追加させ、
  同じ変異を再度当てて 1 failed (新テストのみ)・66 passed で KILLED になることを確認した。
- レンズA はもう一件 (`submit_certify.sh --job-script` override 経由で receipt の ratio と実行 job body
  が乖離しうる) を blocker 相当として指摘したが、これは既に別途追跡されている
  [T-424] (`certify-job-script-binding`、`docs/archive/worklog-phase3-0820-746.md` 参照) の既知の
  残余であり、本 wave 自身の `{{D:t425-calibration-gate-actor}}` も T-424 の要求閉包を別途待つと
  明記済みである。本 wave の新規劣化ではなく、実装せず T-424 側の scope として scope 外に据え置く
  (実装しない場合の影響: `--job-script` override を使う経路に限り、ratio 詐称の理論的余地が
  T-424 解決まで残る。canonical な `submit_certify.sh --rratio N` 経路には影響しない)。
- nit 2件 (レンズB): (a) `test_pegasus_floor_tools.py` の `# 出典: certify_calibration.sh:N-M`
  引用は行シフトで人間向けラベルとして陳腐化しているが、抽出は文字列アンカーでありテストの
  正しさには影響しない。(b) `submit_certify.sh` の dirty-tree 検査が `output/` 全体を除外するよう
  今回拡張されたが、この scope 拡大の意図が裁定文に明記されていない。いずれも blocker ではなく、
  追加 wave は起票しない。
- **本 wave と無関係の発見:** `check_ai_provenance.py` の既定 full-history 監査を実行したところ、
  commit `09ce607b` (`external/ccbench` pin bump 511c9538→ef9328a3、author=thawk105、
  本 wave の外、本 branch では main からの取り込みで到達するだけ) に `AI-Agent` trailer が
  一切無く、新規違反として rc=1 になることを発見した。`docs/provenance/correction.md` の
  forward correction 枠 (PR-C01) は既に別件で消費済みで使えない。DW-O25 の
  `locked_main != tested_tip` 条件が成立する land ではこの全史監査が発火し rc=29 で拒否されうる。
  本 wave が導入した gap ではなく、修正方針 (waiver ratify か known-violation allowlist 追加) は
  ユーザー判断が必要なため、本 wave では対応せず記録に留める。

## 次の一手差分

### 新規

- {{T:legacy-ccbench-pin-bump-missing-provenance}} **P1・ユーザー判断待ち**: commit `09ce607b`
  (ccbench pin 511c9538→ef9328a3) に AI-Agent trailer が皆無で `check_ai_provenance.py` の
  既定 full-history 監査が rc=1 になる。forward correction 枠 (PR-C01) は消費済みで使えない。
  DW-O25 の条件成立時に land を rc=29 で拒否しうる。waiver ratify か known-violation allowlist
  追加かの方針をユーザーが決め、決定後に別 wave (または docs-only 軽量修正) で対応する。
