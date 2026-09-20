---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2795-pair-launcher
seq: 2
---

## {{D:k2-pair-launcher-stock-control}}. K2 手動 loop の同 job stock 対照は driver の独立口 `--stock-control` で同 campaign に評価し、成功条件に source の STOCK 性を必須にする

**決定:** D2172 項 3 (i) の同 job pair launcher と項 4 (α) の K2 共有部品 (較正動作点 CLI、exact correctness opt-in) を次の形で実装した。

- stock 対照 (silo、`BACK_OFF=1`、`BACKOFF_FIXED=-1`) は driver の独立口 `--stock-control` で評価する。候補と**同じ campaign** (同 identity・同 WAL) に入れ、
  `--stock-control` 自身も stock genome も identity に焼かない。planner / coder / 検疫 / whiteboard / checkpoint に到達せず、WAL は `run_campaign` →
  `pipeline.evaluate` だけが書く。`--run-iteration` / 明示 `--value` / `--emit-planner-context` / `--no-build` / `--coder-role` / `--b4-reflux-ablation` /
  `--allow-coder-derived-build` と排他、`--isolate-worktree` を必須にする (別の pinned-clean stock root が要る)。
- stock の成功 (`outcome=certified-stock`、rc 0) は certified かつ **source が STOCK** (variant id が `variant_id(genome)` かつ BUILD_START の
  `src_token == STOCK`) のときだけ。非 STOCK の certified は `non-stock-source`、同 campaign に terminal 既存なら `skipped` (復元しない、ID を捏造しない)、
  いずれも rc 1。pair の成立は両 attempt の WAL outcome で判定し、driver rc・campaign id から判定しない (候補 CLI は提案 reject でも rc 0 を返す)。
- stock 用 condition gate は A-1 paired と同型 (`stock_comparison=True`、`MeaningCase(-1, None, expected_selected_branch=STOCK_ADAPTIVE_BRANCH)`、
  stock_root = pinned-clean な `external/ccbench`)。候補用の bits 宣言を stock に流用しない。
- stock の build admission は、stock-baseline 分岐が full `PIN` と短縮 `CURRENT_PIN` の exact 比較で入らないため、既存 driver と同じ
  `capability_resolver` で generator receipt (`GeneratorId.BACKOFF_SWEEP`、input = `p3-s4-loop-stock-control/v1|genome_sha256`) を発行する
  (class は machine-generated)。resolver は STOCK evidence にだけ receipt を返し、非 STOCK は None → admission-error で fail-closed。
  `build_admission.py` の pin 比較は変更しない (規律 2 の防壁側。正規化はユーザー裁定の候補)。
- job body は `IZANAGI_S4_STOCK_CONTROL` (未設定 / `0` off、`1` on、他・設定済み空値 rc=2) で候補の**後**に stock を 1 回起動する。同 K2 manifest /
  宣言値を渡し (同 campaign の条件)、`--coder-role` / `--allow-coder-derived-build` は渡さない。候補 rc を捕捉し、候補非零優先で集約する。
  既定は現行の 1 起動で argv は bytes 不変。
- 較正動作点は `--calibrated-perf --perf-workload {write-heavy,balanced,read-heavy}` (同時指定必須) で p2_2 の較正定数 (1M / 48 / 3 s / 5 reps) と
  3 workload + `ycsb_max_ope="10"` (`pipeline.S2_FLAGS`) から PerfConfig を組み、opt-in 時だけ search_config に
  `records / threads / perf_workload / extime / reps` を焼く。key 名は `perf_workload` (既存 `workload` key は他 driver で別意味、D75)。
  `--verify-performance` (較正必須) は `search_config["verify"] = legacy+performance` を焼き、既存の `loop._closed_verify_workloads` →
  `performance_correctness_workload(perf)` → `evaluate(extra_correctness=)` に接続する。legacy 既定 pass は残る (legacy 1 回 + performance `reps` 回)。
  記録先は campaign.lock の identity preimage。指定なしでは key を一つも足さず identity は bytes 不変。pipeline.py / loop.py は変更しない。
- 較正・verify の opt-in は job body に配線しない (B-5 試走 wave の launcher 設計で足す)。

**理由:**
- 設計メモ (K2 round 3、項 6) の要件 = 同 allocation・同 pin・同条件の stock、無改変 stock 源、pipeline 発行の WAL、identity への影響の整合。同 campaign なら
  identity preimage は genome を含まないので候補と同 ID になり、critic identity projection は既に `src_token` で stock label を持つ。
- 「stock」は名前ではなく digest で決まる (`source_digest` の STOCK token は current / baseline digest の一致)。名前だけで対照成立と誤認する経路を
  塞ぐため、成功条件に STOCK 性を必須にした (段 3 consult A の must-fix)。
- 候補用 condition gate の `MeaningCase(-1, bits)` は固定値 −1 の意味宣言であり、B-5 §5.2 の `-1` = 適応 backoff の意味を検査しない
  (段 3 consult A の must-fix)。A-1 paired の stock 形が既に存在する。
- 既存 `_resolve_duplicate` は whiteboard を更新するので stock から呼べない。fresh layout 運用 (D2172 項 3) では terminal skip は起きないので、
  復元の二層化は削り skip = 非成功にした (段 3 consult B)。
- exact correctness は既存の verify mode 機構で接続でき、pipeline の変更は不要。WAL verify record は `workload == {"tag": tag}` を exact 照合するので
  flags を足さず、search_config (campaign.lock) からの決定論的な復元を記録とした。§5.5 の全体成立 (実 argv・binary・toolchain の独立 receipt、seed・
  verifier 版の発効束) は主張しない。

**却下した選択肢:**
- 別 campaign で stock を評価する — 同 job・同 pin の対照を identity で分断し、設計メモの「identity への影響の整合」に反する。
- `--value -1` を stock の代用にする — 候補の受理域 1..1000 を広げる (規律 2 側の受理集合変更)。
- 無改変 PIN 木で `BACKOFF_FIXED` flag を渡して評価する — build の受理を別途確認する必要があり、b10 の applied 下 inert 先例から外れる。
- stock を候補の前に置く順序選択の env — B-5 §5.4 (初回 planner 前の stock → `current_perf`) は planner 入力への接続が別途要り、発火する
  artifact / 計測 ID が無い (DW-G04)。設計メモに留める。
- `build_admission.py` の pin 比較を full / short 両受理にする — admission gate の受理集合変更で、本 wave の scope 外 (裁定パッケージ候補)。
- 較正・verify の job body env を今回配線する — K2 pair 投入に不要で、TJ の pin 更新を増やすだけ。B-5 (β) の launcher 設計で足す。
