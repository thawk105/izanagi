# [T-2797] 段 1 brief — B-5 共通 Tier0 の実装 + LLM arm 親運用・全 arm 同一 walltime の設計 (2026-09-21 14:35 JST、base d99c556df)

- 研究前進: B-5 生成器対照 (LLM 生成器 vs random / sweep、論文の「LLM 生成器の必要性」実験) の本走は D2200 項 1 の段階認可で、発効束の未充足部品の 1 つが
  共通 Tier0 (§3.1: 「A / B の分離は Tier0 通過で決まる」)。完了判定 = B-5 mode の候補 slot で Tier0 (コンパイル + 固定スモーク) が実走し、
  不通過は `pipeline-submitted.json` を書かず A だけを消費し、通過・不通過が slot ごとに記録され、header の `tier0_status` が実装済みの契約を示す。
  加えて親運用と walltime の設計判断を decisions fragment + insight に記録する (実装しない)。
- 確定済み裁定 (逐語は verbatim/): D2200 項 1 (段階認可、(2) 5 = Tier0 未実装は受容せず実装、(1) 親運用・全 arm 同一 walltime の設計が AI 手番)、
  D2198 (B-5 実装: slot ごとに `p3_s4_loop` を subprocess 起動、b5 driver を coder build authority に登録する案は却下、A / B 消費点、無応答 2700 s)、
  事前登録 §3.1 / §3.3 (投入前の時間切れは A のみ、walltime = 試走の最大所要 × 倍率で全 arm 同一) / §4.1 (系列ごと fresh context、親は助言しない) / §12。
  倍率・発効 commit・§12 hash 採取・本走投入は本 wave の scope 外 (land 後の別段)。B-5 本走・校正は投入しない。
- 不変条件: 規律 2 (Tier0 は pipeline の正しさ検査を置換・短縮しない。Tier0 通過は certified を意味しない)。smoke の値を性能値・fitness・current_perf に使わない
  (規律 1: 性能値は pipeline の trace-disabled bench だけ)。非 B-5 経路 (既定の argv・identity preimage・`run_campaign` kwargs) は bytes 不変。
  stock slot (stock-start / block-stock) は候補でないので Tier0 を走らせない。仮想リスク向けの gate・台帳・一般化は足さない。
- 編集面の所有: T-2830 (段 6、所有 = `p3_s4_loop_pegasus.sh` / `b5_contrast_launch.py` / 両 test / `tools/pegasus/README.md`) には触らない。
  T-2632 (T-2830 land 待ち、予定所有 = `p3_s4_loop.py` / `p3_b4_prerun_caller.py`) → `p3_s4_loop.py` の変更は T-2632 の land 後に当てる。
- 実アンカー: 挿入点 `orchestrator/campaign/p3_s4_loop.py` `_run_one_iteration_resolved` の検疫通過 (2236-2244) → `_require_condition_gate` (2245-2257) →
  (Tier0) → `_write_b5_sidecar(..., "pipeline-submitted.json")` (2281-2283) → `run_campaign` (2286)。driver 側 = `b5_generator_contrast.py`
  `classify_slot` (297-409、`proposal-rejected.json` → rejected-preprocess の先例 309-312)、`_header` (551 `tier0_status`)、`_execute_slot` (570-636)。
  pipeline の build = `pipeline.py` `_build_one` (1985-2012、trace / perf の 2 build、`buildcache.build_v2`)。実行の既存口 = `calibrator/runner.py`
  (`run_once` gateway、`measure_point` / `_point_repro_command` 562)。spawn 目録 = `orchestrator/tests/test_ccbench_spawn_sites.py` (exact)。
- (P1) 親の provisional 裁定・攻撃対象: Tier0 は子 (`p3_s4_loop`) の B-5 mode の候補経路だけに置く (上の挿入点)。driver 側で build しない (D2198 と同型)。
- (P2) コンパイル = pipeline が後で使うのと同じ build 経路・同じ引数で trace-enabled / trace-disabled の両 binary を先に作る (cache 再利用で二重 build を避ける)。
  同一 cache key にならないなら理由と代替を plan で示す。
- (P3) 固定スモーク = trace-disabled binary を全 arm・全候補・全 workload で同一の小構成 argv で 1 回、bounded timeout 付きで実行し、rc=0 かつ出力を
  既存パーサで読んで正の commit / throughput が取れることを通過条件とする (F: smoke 検収は消費側パーサとの突合まで)。smoke の ratio は保護対象を避けた既存固定値。
  timeout は実環境 (Pegasus gen_S 計算ノード) で実測した smoke 所要の max への倍率で決める (DW-O13)。
- (P4) 不通過 (build 失敗・smoke 非 0 / 解析不能 / timeout) は候補起因・A のみ・retry なし。子は sidecar `tier0.json` (通過・不通過とも) を durable に書き、
  不通過なら `pipeline-submitted.json` を書かず rc 3 で終える。driver は `rejected-tier0` として A だけを進め、台帳に Tier0 結果を残す。
  score slot も同じ proposal 経路なので Tier0 を通る (不通過は既存の非 certified 分岐で系列を止める)。
- (P5) Tier0 開始前に durable な開始印を書き、job walltime の打切りが Tier0 中に起きても report が「投入前の時間切れ = A のみ」と分類できるようにする (§3.3)。
- (P6) 親運用の設計 (実装しない): `LLM_WAIT_S = 2700` は変えない。1 親 session = 同時 1 系列 (系列ごと fresh context、§4.1)、同時 LLM 系列数 ≤ 親の本数 p。
  試走の 1 巡 10〜13 分 (≤ 780 s) は 2700 s の 29% で余裕 3.4 倍。p は §7.1 の block 配置 (block あたり 12 組 × arm 順 6 通り) から導く候補値 4 を攻撃対象とする。
- (P7) walltime の設計 (実装しない): 探索 3 arm 同一 W = ceil(21,259 s × k)。21,259 s = 試走の series job Elapse の実測最大 (llm、lock 待ちと親待ちを含む、
  推定値で差し引かない)。k は倍率としてユーザーへ再提示 (gen_S 上限 86,400 s から k ≤ 4.06)。block-stock は arm でないので別基準 (5,447 s × k) を攻撃対象とする。
- 成果物: 実装 (Codex author) + test、insight `output/insights/2026-09-21/t2797-tier0/README.md`、decisions fragment 1 (設計判断 3 件)、worklog fragment。
- 分割方針: U1 = driver (`b5_generator_contrast.py` / `_report.py` / 両 test) — 今すぐ。U2 = 子 (`p3_s4_loop.py` + 新 test file + spawn 目録 test) — T-2632 land 後に
  land 済み main 上で author。U1/U2 の接点は `tier0.json` の schema で、段 4 plan v2 で固定する。
- 受入・実測: 受入は `tools/dev_wave_wait.py acceptance` (Pegasus、所在 = worklog)。smoke 所要の実測と Tier0 の生死確認は gen_S 計算ノードで 1 回
  (機体固有の作法 = `docs/pegasus-runbook.md`)。B-5 本走 job は投げない。
