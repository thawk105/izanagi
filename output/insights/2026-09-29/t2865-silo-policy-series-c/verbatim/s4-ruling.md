# 段 4 裁定 — [T-2865] 系列 C (2026-09-29 10:15 JST)

入力: 段 3 相談 `codex/s3-consult.md` (check_codex_output rc=0、read-only 1 本、2 レンズ)。

1. **実装しない** (コード変更なし)。段 5・6 を飛ばし 4→7→8→9。記録の read-only review 1 本は段 7 の commit 前に置く (数値を書く wave、先例 T-2243)。
2. 指摘 1 real: check_stop は driver の開始前と結果記録後に掛かる (`p3_s4_loop_policy.py:450,485,503,528`)。起動済み pair は最後まで評価され、結果の `stop_reason` が予算に変わりうる。brief (P2) を訂正。「最大 4 pair」は費用の上限例で、達成本数の予測にしない。
3. 指摘 2 real: `release-policy.sh` に (a) preview JSON の `passed=true`、(b) proposal の `auditor.diff_digest` == preview の `diff_digest`、(c) proposal の `coder` == preview に掛けた coder.json の `coder` の照合を足す。repo 外の親専用運用 script の修正で、repo の gate・検査の新設ではない。
4. 指摘 3 real: `submit-policy.sh`・`release-policy.sh` は qsub / qrls の rc≠0 で非 0 終了する。
5. 指摘 4 real: pair の成立は runbook §1(f) のとおり計測 dir の候補・stock 両 WAL、stdout の stock outcome、系列 loop_state の iteration と履歴行で確かめる (T-2871 の verify-liveness.py を写す)。
6. 指摘 5 real: insight の分類表は preview reject (subtype/rule_id) / auditor veto / AuditorGateFailure / verifier anomaly (非 certified) / eval-exception / stopped-before / 欠番 / certified を分ける。
7. 指摘 6 要実測: 保留投入の scheduling 効果は、投入・解除・開始時刻 (qstat/sstat) を記録して実測値として書く。前提にしない。
8. (P1)(P3)(P4) は修正込みで採る。変異事前登録: 実装面なしのため無し (DW-M01 の対象外)。
