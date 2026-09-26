# 段 1 brief — [T-2849] 残り (2) 単位 8: MOCC の差し込みと動作点の較正

- 起点: local main `42d148868` (fresh worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2849-mocc-insertion`、開始 gate rc=0)。ccbench gitlink = C `68106660686232781bca3be792a750d3e19d7a8a`。
- 研究前進: VLDB 差分分析 P2 (5 手法比較の第 2 プロトコル)。完了判定 = 比較 harness の 1 slot 経路 (stock・機械生成候補・K0 LLM 候補) が protocol=mocc で pin C の較正済み動作点を使って通り、silo の既存経路の挙動・argv・campaign 設定が不変。残り (3) の疎通 (20〜40 候補 × 3 workload) は scope 外。
- 確定済みユーザー裁定・決定: D2220 項 6 (S2 = 固定 MOCC flags の上で S1 と同じ literal 材料化、stock 比で報告、既知最良の参照なしを明記、温度述語 hole は使わない = D2134 項 9)、D2233 (S1 実装)、D2236 (pin C で mocc は X/P 証拠あり)、D2150 項 1 (iv) (新 pin の較正値と主張する系列だけ再取得)、D2212 項 4 (1 タスク合計 2 node 時間以上は job Elapse 実測単価で見積もりユーザー確認)、D95 (実装は Codex author)。
- 較正の結果 (段 2 起動後に確定、commit `f72ad2c52`): pin C の mocc record 3 件 = rr5 `calibration-4b8329b42bb47c65.json` (29393、186 秒)・rr50 `calibration-ae83d7382329999b.json` (29394、181 秒)・rr95 `calibration-7f00a49f493e1015.json` (29395、216 秒)、いずれも accepted・records=1,000,000 (下限基準)・pinned_clean。計 583 秒 ≈ 0.16 node 時間。
- wave 先頭の較正 (投入時の記述): 既存 `tools/pegasus/submit_certify.sh --protocol mocc --rratio {5,50,95}` を pin C で 3 本同時投入 (29393/29394/29395.nqsv)。genome = `mocc|BACK_OFF=1,KEY_SORT=0,TEMPERATURE_RESET_OPT=1` (launcher 既定 = `between_run_floor.BASELINES["mocc"]`)。旧 pin 511c9538 の rr50/rr95 記録 (records=1,000,000、下限基準) は旧 pin の事実として参照のみ。

## 親の provisional 裁定 (攻撃対象)
- (P1) MOCC flags は BACK_OFF=1・KEY_SORT=0・TEMPERATURE_RESET_OPT=1 に固定 (設計 §9.2 案、較正 genome と同一)。stock = 同 flags + BACKOFF_FIXED=-1、候補 = 同 flags + BACKOFF_FIXED=<v> と合成枝の `double now_backoff = <v>;` 材料化 (silo と同じ hole・同じ template patch `patches/silo-backoff-fixed.patch`)。
- (P2) MOCC の動作点 = 今回の pin C 較正 record の records (workload ごと)。threads 48・extime 3・reps 5・workload 3 key と ycsb_max_ope は S1 (`p2_2` + `S2_FLAGS`) と同じ session 契約。silo の `calibrated_perf` は不変。較正 record id を MOCC の定数の出典として code か記録に残す。
- (P3) MOCC に参照 genome は無い。`--reference-genome` は silo 専用のまま。harness の block 対照は protocol=mocc のとき block-reference を測らず (stock だけ)、集約は stock 比で出す。
- (P4) protocol の選択面: `p3_s4_loop` に `--protocol {silo,mocc}` (既定 silo)、harness の `run-series`/`run-block-controls` と job body env に protocol を 1 つ通す。silo 既定時は argv・search_config・campaign identity・台帳 header を現行と byte 同一に保つ (新 key を足さない)。mocc 時だけ search_config/header に protocol を載せ campaign を分ける。
- (P5) hole marker 名 `silo-backoff-magnitude` はそのまま使い、記録上の取り違えは genome の protocol で区別する (改名しない)。
- (P6) 生死確認 (DW-G01): 実装後、計算ノードで protocol=mocc の stock-control 1 slot + 機械生成候補 1 slot を write-heavy で 1 回ずつ通す (verify 込み)。

## 不変条件
- 規律 1・2: trace は compile 時除去のまま、verifier・anomaly 即 reject・Tier0 は変えない。MOCC の検証は既存 verifier (pin C で X/P あり) をそのまま通す。
- silo 経路 (B-5 と T-2849 S1) の挙動・出力・既存 test 期待値は不変。B-5 module (`b5_generator_contrast.py`) は編集しない。
- 新しい gate・検査・台帳・一般化 (protocol 汎用 runner など) を足さない。tictoc 等は扱わない。
- 凍結台帳の hash pin は変更対象に無い (campaign_lock の source list は live 計算、admission_registry は class だけ)。

## 変更面の実アンカー (段 2 で file:line を確定)
- `orchestrator/campaign/p3_s4_loop.py`: genome 固定 `:2314` (stock)・`:2466` (候補)・`:3161` (B-5 sidecar 候補)、`default_cfg` の `"scale": "silo"` `:1769`、`calibrated_perf` `:1848`、`--reference-genome` 検査 `:3553-3574`、CLI `:3454` 付近。
- `orchestrator/campaign/t2849_comparison_harness.py`: `slot_argv` `:339-353`、`reference_genome` `:356`、`run_block_controls` `:620-640`、`_header`、CLI `:761`。
- `tools/pegasus/p3_s4_loop_pegasus.sh`: harness 分岐 `:54-83`・`:699-711` (env `IZANAGI_S4_T2849_PROTOCOL` を追加するか)。masstree prebuild `:583-694` が mocc build に足りるか。
- 試験: `orchestrator/tests/test_t2849_*.py`、`test_p3_s4_loop_job_contract.py`、`test_hooks.py` の job body 登録。

## 既存被覆と過去の型
- `p3_s4_loop.py`・`t2849_comparison_harness.py` に `--protocol` は無い (grep 0 件) = 純増。
- F435 (source_digest が mocc の実供給マクロを認識せず build 段で全滅) の再発を plan で確かめる: pipeline の mocc build が source_digest・diff 検疫・Tier0 を現行コードで通るか、既存の mocc 経路 (between_run_floor・certify) が pipeline を通っているか。

## 分割方針
- 段 2 plan 1 本 (read-only)、段 3 相談 2 本 (正しさ境界・整合 / 実効性と過剰)。段 5 author 1 本 (所有は上記 file 全部、単一子)。段 6 レビュー 2 本 + 変異 + 受入。
- 計算見積り: 較正 3 job (実測単価 238〜302 秒/本 → 約 0.25 node 時間)、生死確認 2 slot、焦点走、変異、受入。合計が 2 node 時間に近づけば投入前にユーザー確認。
