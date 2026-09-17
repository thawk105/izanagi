# 段 1 brief — [T-2710] t080 e2e 群の別系列化の採否を諮り直す調査 (2026-09-17)

- 基準: local main `38353207f` (fresh worktree `worktree-dev-wave-t2710-t080-series-inquiry`、clean、startup gate rc=0)
- 種別: 調査 wave。**実装差分ゼロ** (計測 probe は job dir に置き repo へ入れない)。段 4 で「実装しない」を確定し `4→7→8→9`。
- 設計択一が割れ (別系列化の可否)、正しさ防壁 (t080 public gate の e2e) に触れるので、段 2 plan 1 本 + 段 3 敵対 2 レンズは省かない (DW-C00)。

## 研究前進

直接の論文主張は進めない。土台: 受入全走の最遅 shard (shard-0) が 337.9〜351 秒で 5 分上限を超え続けている
(T-2236 の 2026-09-17 実測、session `895f300a…` = 337.9 / 249.2 / 204.1 秒)。shard-0 の span は最長単体 node
(t080 e2e、台帳 240 秒) にほぼ等しい (T-2559)。本 wave の完了判定 = D2104 項 28 が要求する 3 材料が insight に揃い、
採否をユーザーが決められる裁定パッケージが `docs/spool/` fragment で worklog 次の一手に載ること。

## scope (依頼どおり、純増だけ)

1. **被覆対応表**: t080 e2e 群の各 node が通す production 経路・拒否理由と、`growth_test_holds.py` で保留中の実 repo
   直接検査 (`test_s8b_repo_scan_invariant.py::test_real_repository_scan_matches_known_hits_and_has_positive_control`、
   `test_s8b_holdout_freeze.py::test_verify_{cli,direct_cli}_accepts_active_t080_receipt_exact_match` ほか) の被覆対応。
   「e2e だけが持つ検出力」「保留検査だけが持つ検出力」「両方が持つ」を分ける。
2. **利用時拒否の実効性 (負例で実測)**: 別系列へ移した場合に D2002 条件 3 が要求する「未検証状態での利用拒否」が
   どこで効き、負例を何件拒否できるか。
3. **移動後の最遅 shard wall の見積もり**: 台帳 (`acceptance_duration_ledger.json`、24,379 entry、T-2236 refresh 後) と
   session `895f300a…` の観測 universe で `tools/acceptance_shards.py::allocate()` を M 除外で再計算し、T-2236 の
   予測↔実測対応で wall に換算する。

scope 外 (依頼で明示): 受理集合の変更、`growth_test_holds.py` 保留の復帰、追加 gate・検査・台帳、実装。

## 確定済みユーザー裁定 (変えない)

- D2104 項 28: 受理集合不変、別系列化は 3 材料の後に諮り直す。項 29: proto 化は 10% 基準 (D357 / D1260) の内側で land しない。
- D2068: fixture 高速化 A (whitelist) / B (alternates) / C (blob 移送) 不採用。
- D700: t080 opt-in を撤去し受入全走へ戻した。**「受入とは別 gate で定期実行」は却下済み** (理由: 定期実行基盤が repo に無い、
  opt-in の改名、直接 helper 検査と e2e は受理集合が異なる)。D701: 既定 collection で 11 node が選択され setup へ到達する probe
  (`test_real_repo_serialization.py::test_stub_free_receipt_nodes_are_selected_and_reach_setup_by_default`)。
- D2002: 別系列化は 4 条件 (完走記録・独立期限検知 24h・未検証時の利用拒否・関連変更時の焦点走) 成立後。D2003: collection は
  縮めず実行母集合だけ分ける (`U = C − M`)。
- D358: real-repo 直列化は維持。規律 2: 正しさゲートを緩めない。
- F485: 同じ群が opt-in で 11 日腐った事故。再演を避ける。

## 不変条件

- 受理集合を変えない。保留検査を復帰させない。repo 内に probe / script / test を足さない。
- 数値は session id・commit・台帳の値から取り、login node の単発測定を根拠にしない (D2068)。見積もりは「見積もり」と書き、
  実走の主張にしない。

## 親の provisional 裁定 (攻撃対象)

- **(P1) M の定義** = D700 / D701 の 6 function / 11 node (fixture `_t080_stub_free_e2e_repo` の consumer、台帳合計 2,302 秒、
  最長 240 秒)。shared-base 群 (`test_t080_shared_base_builds_real_builder_once_across_processes` 150 秒を含む 12 node)、
  snapshot 群、`temp_roots_fail_closed` (41 秒) は M に含めない。変種 M′ = M + shared_base_builds (12 node) を見積もりに併記する。
- **(P2) 「利用時」の箇所** = (a) 受入 wrapper `tools/dev_wave_wait.py acceptance` の受領証、(b) `tools/dev_wave_land.py` の land、
  (c) `orchestrator/campaign/s8b_oracle_driver.py` の production 利用 (receipt 発行・public gate)。現行 repo には別系列の完走記録・
  期限検査・利用拒否のいずれも無い (CI / cron / timer 不在を本日再確認、`SANCTIONED_EXCLUSIONS` は空)。したがって負例実測は
  2 段: (i) 現行 repo が負例を拒否しないことの実測 (0/N)、(ii) D2002 条件 3 の最小判定器を repo 外 probe として書き、負例
  (未起動・期限切れ・commit 不一致・node 集合不一致・rc=0 だが finished≠selected・失敗) を全件拒否し正例を通すことの実測。
  (ii) は模擬であり production 配線ではない。
- **(P3) shard wall の見積もり方** = `allocate()` を観測 universe − M で再実行。現行割付は file 粒度なので
  `test_s8b_oracle_driver.py` の残り 136 node (うち real-repo 6) は shard-0 成分に残る。wall 換算は 2 モデルで挟む:
  (α) T-2236 の予測負荷→実測 wall の比例、(β) span = max(最長 node, real-repo lock union, 負荷/worker 数) + 前処理 60 秒。
  peer wave T-2750 (成分粒度を node へ) が land すれば前提が変わるので、その場合の再計算条件を書く。
- **(P4) D700 の却下理由は現在も真** (定期実行基盤の不在)。別系列化の採否は「基盤の新設費用 + D2002 4 条件の実装」を
  含めて諮る。本 wave はそれを作らない。

## 成果物の形

- `output/insights/2026-09-17/t2710-t080-series-inquiry/README.md` (被覆対応表・負例実測・見積もり・裁定パッケージ) +
  `stage1-brief.md` / `stage2-plan.md` / `stage3-lensA.md` / `stage3-lensB.md` / `stage4-ruling.md` の逐語 + probe 出力。
- `docs/spool/` fragment: worklog エントリ (T-2710 は「裁定パッケージ提示済み → ユーザー裁定待ち」へ)。decisions fragment は
  本 wave が決めた「調査のみ・実装しない」を D として残す。

## 並列分割・実測環境

- 段 2: codex plan 1 本 (read-only、file:line 粒度)。段 3: codex consult 2 本 (レンズ A = 検出力・受理集合、レンズ B = 実効性・費用)。
  段 5 / 6 は無し。親 probe は job dir `/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2710-t080-series-inquiry/`。
- 実測環境: login node (allocate 再計算・負例 probe は秒単位)。計算ノードへの受入投入は段 9 の受入 1 走だけ。
- peer: T-2273 / T-2750 [72bbfd] (shard-0 成分診断) と解析対象が重なるが、本 wave は read-only で code を触らない。
  docs は別 insight dir・別 spool fragment で衝突なし。T-2708 は稼働していない。
