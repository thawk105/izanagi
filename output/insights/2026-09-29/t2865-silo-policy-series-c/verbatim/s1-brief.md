# 段 1 brief — [T-2865] silo-function-policy 軸の研究系列 C を複数 iteration 実走 (2026-09-29)

- **研究前進:** LLM が関数方策を合成する軸 (D2214) で、coder → auditor → 計算ノードの pair (候補 + 同 job の stock) → critic → 次の coder、
  という自律ループが**評価済み 2 iteration 以上**で閉じることを研究系列として初めて示す (系列 A・B は評価 1 iteration で閉じ、
  T-2871 の 2 本連続は LLM なしの liveness)。完了判定 = 新系列で評価済み pair ≥ 2 と、iteration ごとの certified/reject・anomaly 分類・同 job stock 比を insight に残すこと。
- **scope:** 実走と記録だけ。コード変更なし (要れば Codex author、D95)。固定文面 (leakproof_context) の改訂 [T-2870]・予算の数え方 [T-2881] の変更・仮想リスク向けの gate/検査/台帳は scope 外。
- **確定済み裁定:** 依頼逐語 (新しい detached submit checkout を着手直前の local main から作り bootstrap stock から、2 本目以降の pair は `qsub --after` で先に待ち行列へ、auditor の出力形は runbook §1(d) の prompt 明記、2 node 時間以上ならユーザー確認)。D2270 (段階 F)・D2274 (claim を手で退避しない)・D2281 (pair は iteration ごとの計測 campaign)。規律 2 は緩めない。
- **不変条件:** 正しさ gate (検疫・構文・単独 TU・auditor deny-only veto・digest 照合・legacy verify・性能構成 verify) を迂回しない。anomaly は即 reject として記録。claim を手で動かさない。
  リーク制御 (runbook §2): coder 入力は driver の emit 出力そのまま、他系列の値・偵察・小比較を渡さない、justification を critic に渡さない。
- **実測環境:** Pegasus。login = emit / preview / record-reject / LLM 子。計算ノード (gen_S, single-tenant job body) = stock・pair。
  submit checkout = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-series-c/trees/c` (local main `1887f56e4` から detach、hydrate、locked)。形は C++ (`--form cpp`、系列 A・B と同じ)。
- **見積り (job Elapse 単価):** bootstrap 309 s + pair 最大 4 本 × 793 s ≈ 3,481 s ≈ 0.97 node 時間 (+ 予算停止の空振り job 数十秒)。2 node 時間の線の下なので確認なしで投入。記録 land の受入 (≈0.25 node 時間) を足しても ≈1.2。
- **(P1) 親の provisional 裁定・攻撃対象:** 2 本目以降は、前の pair の開始を見た時点で `qsub -h --after <前>` で保留投入し、proposal 確定 (preview 通過 + auditor 受理) 後に `qrls`。
  保留しないと、前の pair 直後に LLM 段 (約 5 分) が終わる前に job が始まり proposal が無い。保留の解除後の scheduling 位置は未実測。
- **(P2)** 予算 = 系列の loop_state 作成から 3,600 s (check_stop は driver 起動時だけ、起動済み pair は最後まで走る) と MAX_ITER=10 (record-reject も 1 消費)。予算停止まで回し、止まった理由を記録する。最初の coder 案が preview で落ちれば login の record-reject で予算の時計が始まる (runbook どおり受け入れる)。
- **(P3)** 値は 1 候補 1 観測。同じ job の比 = 候補 5 rep 中央値 ÷ stock 5 rep 中央値。系列 A・B・liveness の値とは合算しない。性能主張にしない。
- **(P4)** 段構成: 軽量版。段 2 省略、段 3 read-only 相談 1 本 (正しさ境界・運用実効性の 2 レンズを 1 本)、段 4 で「実装しない」なら 4→7→8→9。
  計算ノードの数値を書く wave なので、記録の read-only review 1 本は残す (先例 T-2243)。
- **成果物:** insight `output/insights/2026-09-29/t2865-silo-policy-series-c/README.md` (+ `verbatim/` に依頼・brief・LLM 入出力)、spool fragment (worklog・必要なら decisions)。
- **DW-G05:** 記録を欠けば、系列 C の certified 候補・stock 比・reject 分類が台帳 (insight/worklog) に残らず、軸の自律ループが複数 iteration で閉じたという主張の根拠が無くなる。
