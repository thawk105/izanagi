# 段 1 brief — [T-1777] A-1 の対を交互配置へ改める

## 主目的 (scope)

A-1 対測定の「対」を、arm ごとの一括走行から **rep 単位の交互配置**へ改める実行機構を作る。
凍結済みの現行 A-1 study は書き換えず、**次の実走の配置**だけを対象にする。
本 wave では測定投入 (qsub) を行わない。

## 確定済みユーザー裁定・上位契約

- **D1027** — 現行 A-1 は凍結どおり走らせ、論文採用 estimand は別 study として事前登録する。
  差し替えはしない。本 wave は差し替えではない。
- **D95** — 実装面は Codex `role=author` が書く。親は brief・裁定・統合・記録だけ。
- **D1224** — 既存テストの期待値を変更・反転・削除しない。
- **D1028** — 使い手の居ない休眠 capability を作らない (型と consumer は同じ変更単位)。

## 実測した事実 (brief 前の棚卸し、DW-S01)

1. 凍結 v2 policy `orchestrator/campaign/paper_story_a1_paired.v2.json` の
   `pairing` は `design="arm-grouped-positional-v1"`,
   `execution_order="all adaptive reps, then all static10 reps"`, `time_block_shared=false`。
   balanced は `reps=205`、`scale.extime_s=3` なので 1 arm 区間 615 s。依頼の数値は凍結物から再現する。
2. `orchestrator/campaign/loop.py` と `orchestrator/campaign/pipeline.py` は
   enforcement source closure **exact 24 path** の member
   (`orchestrator/campaign/campaign_lock.py:49-74` の `CONTRACT_LOADER_RELATIVE_PATHS`)。
3. **T-1777 原文が着手条件にしていた「批准の執行設計の着地」は D1139 (2026-08-27 ユーザー裁定) で
   解消済み。** 批准集合との突き合わせによる拒否は廃止され、live closure は exact 24 path
   (`campaign_lock.py:47-48`, `contract_loader_binding.py:2`, `artifact_admission.py:67`)。
   記録 (commit ID・path→blob digest map) と自己整合検査は残るが、**関門ではない。**
   → 着手条件は満たされている。これは T-1777 原文の前提を覆す新事実として brief に出す。
4. closure member を編集すると、**commit 前の焦点走で `contract-loader-drift` 偽赤が機械的に出る**
   (F357)。変異 matrix には同型の共通核が出る (F358、再発 2026-08-20 が pipeline.py/loop.py で実測)。
   ERROR 経路は `failed_nodes` 抽出から漏れるので、共通核を引いた delta で判定する。
5. **配置は既に campaign identity に入っている。** `campaign_config()` が
   `search_config["pairing_design"] = policy["pairing"]["design"]` を置き
   (`paper_story_a1_paired.py:801-841`)、`search_config` は campaign lock の identity key
   (`campaign_lock.py:20`)。→ 依頼の「配置変更の前後を同じ campaign へ混ぜない」は
   **新しい機構ではなく既存構造で満たされる**。新設 gate を足す理由にはしない (DW-G05)。
6. 現行の反復は `pipeline._run_bench` → `measure_point(..., reps=N)` の **1 回呼び出し**で、
   `bench_lock()` の下に連続実行される (`pipeline.py:512-700`)。
   `loop.run_campaign` は genome ごとに `pipeline.evaluate` を回し、evaluate は
   build → verify → bench(reps=N) → commit を 1 variant 分まとめて実行する
   (`loop.py:388-460`, `pipeline.py:707-1560`)。
   → 交互配置は「両 arm の build/verify を先に済ませ、bench を rep 単位で交互に呼ぶ」形を要求する。
7. A-1 の source binding は `SOURCE_RELATIVE_PATHS` (driver / policy / pipeline.py / job sh) と
   `NON_CERTIFYING_SOURCE_RELATIVE_PATHS` (+ campaign_lock / ident / wal / **loop.py** /
   trial_registry) (`paper_story_a1_paired.py:114-131`)。`POLICY_SHA256` が v2 bytes を pin。
8. v2 policy の bytes を pin する閉包 (DW-O09、path 検索 + 識別子検索):
   `paper_story_a1_paired.py:76,114,136` (`POLICY_PATH` / `POLICY_RELATIVE_PATH` / `POLICY_SHA256`)、
   `orchestrator/tests/test_paper_story_a1_job_contract.py:49,241,1087`、
   `orchestrator/tests/test_paper_story_a1_headline.py:1240`、
   `orchestrator/tests/test_paper_story_a1_paired.py:818`、
   `docs/paper-story/2026-08-26.md`、`docs/paper-story/claim-evidence/2026-08-26.md`。
   loop.py / pipeline.py 自体の **bytes を pin する台帳・test・trust root は 0 件**
   (closure 名簿への path 収載は blob map の記録であって bytes pin ではない)。

## 不変条件 (違反したら停止)

- `paper_story_a1_paired.v2.json` と
  `output/insights/2026-08-26_paper-story-a1-sized-preregistration/README.md` の **bytes 不変**。
  `POLICY_SHA256` / `PREREGISTRATION_SHA256` も不変。
- 既存 certified gate、anomaly 即 reject、trace/perf 分離、観測者効果の分離を緩めない (絶対規律 1・2)。
- 既存テストの期待値を変更・反転・削除しない。`xfail`・`skip`・期待値緩和を使わない。
- **新 module を enforcement source closure へ足さない。** 実装は既存 24 path 内に収める。
- 配置変更の前後を同じ campaign へ混ぜない (事実 5 により既存 identity で成立。壊さないことが義務)。
- 測定投入 (qsub / 正式 A-1 実走) を行わない。

## 成果物の形

- `orchestrator/campaign/loop.py` / `pipeline.py` への交互 bench 実行経路 (既定は現行挙動のまま)。
- A-1 driver 側の配置選択子 (`pairing.design` の受理値の拡張)。
- 上記を実走させる test (正例 1 本 + 向きを分けた負例)。
- 変異事前登録 + 段 6 変異 matrix (共通核を引いた delta で判定)。
- worklog / decisions / insight fragment。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1-a)** 交互配置は**単一 campaign 内の rep 単位交互 bench**として実装する。
  「reps=1 の campaign を 205 本並べる」案は採らない — verify が campaign × arm ごとに走り、
  balanced で 2 回 → 410 回になり費用が爆発するため。
  *攻撃点:* verify 回数の見積りは正しいか。verify 証明書の再利用で B 案が成立しないか。
- **(P1-b)** 本 wave は「機構 + それを選ぶ配置選択子」までを 1 変更単位で作り、
  **v3 policy JSON の発行と新しい事前登録は次 wave**とする。
  *攻撃点:* これは D1028 が却下した「休眠 capability」に当たらないか。
  DW-G04 の「発火条件を満たす既存 artifact path か計測 ID を brief に書けるか」を満たすか。
- **(P1-c)** WAL の stage 列は variant ごとに
  `build_start, build_done, verify_done, bench_done, commit` を 1 本ずつ保つ
  (bench_done は交互実行の完了後に arm ごと 1 回)。
  *攻撃点:* 交互の実行順序はどこに耐久記録されるか。途中 crash の resume は成立するか。
  `wal.replay` の terminal 判定と両立するか。
- **(P1-d)** 交互配置では CV 再測 (`bench_max_rounds`) を rounds=1 に固定する
  (v2 の `invalid_rules` も「bench rounds is not exactly integer one」を要求している)。
  *攻撃点:* rounds=1 固定は `require_settled` / settle 契約 (絶対規律 4) と両立するか。
- **(P1-e)** `bench_lock()` は rep ごとに取得・解放する (現行は bench 全体で 1 回)。
  *攻撃点:* 競合検査 (`competing_bench_pids`) の発火頻度と、単一テナント直列性を壊さないか。

## 並列分割方針

- 段 2: read-only codex 1 本で file:line 粒度のプラン起草。
- 段 3: 異なるレンズ 2 本 (レンズ A = 正しさ防壁と WAL/identity 整合、
  レンズ B = 統計設計と交絡・費用見積り)。
- 段 5: 実装子 1 本 (loop.py / pipeline.py / driver は相互依存が強く分割しない)。
- 段 6: 敵対 review 2 本 + fix 子 + 変異 matrix。
