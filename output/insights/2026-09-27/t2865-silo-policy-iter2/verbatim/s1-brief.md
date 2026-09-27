# 段 1 brief — [T-2865] silo-function-policy 軸の 2 iteration 目以降 (2026-09-27、起点 local main 339d7c188)

**研究前進:** 論文の中心主張「LLM が workload 特化の CC 関数方策を合成し、ループが critic 診断を取り込んで反復する」の多 iteration 実証。完了判定 = 1 系列が critic 診断 (`--critic-output`) 付きで 2 iteration 以上回り、各 iteration に同じ job の stock 対照が付き、値・経過・計算量が insight に記録されている。

**確定済みユーザー裁定・依頼の束縛:** runbook §1 どおり (特に (g) critic → `--critic-output`)。§3.4 の骨格乱数所見は段 3 で修正要否を決め、直すなら変更前後を別条件として 1 iteration 目と混ぜない。骨格変更は Codex author、stock build の同一性は不変。計算は pair Elapse 765 秒 + LLM 約 6 分で見積もり、検査込み 2 node 時間以上ならユーザー確認。firewall (D2243 項 1)、auditor gate の閉じた出力形の prompt 明記 (runbook §1(d))。[T-2870] の role 本文・固定文面は触らない。規律 2 不変。仮想リスク向けの gate・検査・台帳・一般化は scope 外。

**brief 前の実測 (前提を覆す新事実):**
- 段階 F の loop campaign (`trees/e2e` の `…877344a7`) は `start_wall` = 16:32:05 JST、現在 19:24 JST で経過 2 時間 52 分。`MAX_WALLTIME_S = 3600` (p3_s4_loop.py:189) を超えており、`drive_iteration` は iteration を進める前に `check_stop` で `stopped-before / budget-walltime` を返す (p3_s4_loop_policy.py:447-451)。**旧系列 (条件 A) の 2 iteration 目は現行コードでは回せない。** 予算は D2256 項 3 (停止は予算だけ) と段階 F の裁定 (walltime 起点はコードで直さない) で固定。
- 新系列の walltime 予算 1 時間は、1 iteration ≈ pair job 765 秒 + LLM (coder・auditor・critic) 約 6〜8 分 + queue で約 20 分なので、**1 系列 ≈ 3 iteration (最大 4) で予算停止**する。`MAX_ITER = 10` には届かない。
- campaign identity (p3_s4_loop_policy.py:120-142) は骨格 patch の bytes を含まない。campaign dir は submit checkout の `output/` にできるので、checkout を分ければ別 campaign dir になる。
- 骨格 patch の sha256 `35524d75…` は段階 E 較正 `output/env/pegasus/calibration/silo_function_policy_coverage.json` に記録されているだけで、現行 patch と照合する検査・test は無い (grep 実測)。loop driver は較正 coverage を読まない。
- self_history は outcome だけで throughput を持たない。性能情報が coder に届く経路は baseline 2 scalar と critic 診断だけ。

**(P1) 親の provisional 裁定・攻撃対象:** 旧系列 A は iteration 1 で予算停止として閉じ (loop_state を編集しない・予算定数を変えない)、新しい submit checkout で系列 B を始めて iteration 1〜(予算停止まで) 回す。「2 iteration 目以降」は系列 B の iteration 2 以降で満たす。
**(P2) 親の provisional 裁定・攻撃対象:** 骨格の乱数初期値を最小修正する。系列 B はどのみち新系列なので、修正の追加費用は小さく、修正しないと B の critic 信号も骨格の相関で歪む。形は `TxExecutor` (worker thread 上で `thid` 付きで構築、ycsb_silo.cc:38) で thread 固有の決定的 seed (thid から splitmix 等、非 0 保証) を置く。hole・api・受理契約・hook 呼出し点・上限は不変。
**(P3) 親の provisional 裁定・攻撃対象:** 系列 B の iteration 1 の baseline 2 scalar は段階 F の bootstrap 値 (1,377,953 txn/s・12.18%) を再使用し stock job を投げない (stock build は patch を使わず同一)。
**(P4) 親の provisional 裁定・攻撃対象:** 条件の区別は campaign identity を変えず、insight に条件 A/B = submit checkout・骨格 patch sha256・HEAD を記録して行う (identity に骨格 digest を足すのは scope 外の一般化)。
**(P5) 親の provisional 裁定・攻撃対象:** critic は role `critic` を spawn し、入力は系列 B の campaign の `silo_policy_loop_digest.txt` の本文だけを prompt に貼り、他 file (insights・偵察・小比較・他 campaign) を読まないよう指示する。出力は 4 見出し (`## attribution`/`## recommend`/`## avoid`/`## uncertainty` 各 1 回) を明記。

**不変条件:** 正しさ gate (検疫・構文・単独 TU・auditor veto・digest 照合・legacy + 性能構成 verify) は不変。stock build (原型 source・方策 flag なし) の bytes 不変。予算定数・loop_state は不変。firewall は runbook §2。

**成果物:** (1) 骨格 patch の seed 最小修正 + test (Codex author)、(2) 系列 B の実走記録 insight `output/insights/2026-09-27/t2865-silo-policy-iter2/README.md` (条件 A/B の区別、iteration ごとの候補・auditor・pair 値・critic)、(3) runbook 追記 (walltime 予算で 1 系列 ≈ 3 iteration、critic spawn の読取範囲と出力形)、(4) decisions / worklog fragment。

**計算見積り:** 系列 B は最大 4 iteration × 765 秒 = 0.85 node 時間、stock job 0。検査 = 焦点走 3 回 ≈ 0.12、変異 ≈ 0.1〜0.2、受入 1〜2 回 ≈ 0.25〜0.5。合計 ≈ 1.3〜1.7 node 時間で 2 node 時間の線の下 → 確認なしで投入 (超えそうなら止めて確認)。

**分割方針:** 実装単位 1 (patch + test、1 Codex author)。段 2 plan 1 本、段 3 相談 2 レンズ (A 正しさ境界・整合・実効性、B 過剰・削除)、段 6 レビュー 2 本。受入・実測環境 = Pegasus (計算ノード job、login は LLM と preview のみ)。
