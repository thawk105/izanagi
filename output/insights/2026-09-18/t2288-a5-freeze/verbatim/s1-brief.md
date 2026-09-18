# 段 1 brief — [T-2288] B-4 床値 spec の A-5 を AI が確定して凍結 commit へ進める (dev-wave-t2288-a5-freeze)

2026-09-18 06:4x JST。起点 local main `d2ebef7a407dc6be61622ed596cf08b8b518f606` = worktree HEAD (clean、startup gate rc=0)。

## 研究前進
論文 B-4 (reflux ablation、`docs/phase3-b4-reflux-ablation-preregistration.md`) の材料レポートは §5 floor 欄が未記入で分析 verdict が
`protocol violation` 1 種に固定されている (§11.0)。本 wave は床値測定の凍結 spec 3 本を main に置き、後続の測定 wave が
「結果を見る前の凍結 commit」を成果物の祖先に持てる状態にする (§11.1 手順 6)。完了判定: 3 spec が tracked で commit され、
`floor_pair_driver --validate-only --expected-sha256` が 3 本とも rc=0・stderr 空、A-5 の値と集約対応が D として記録される。

## 確定済みユーザー裁定 (再裁定しない)
- D2120 項 4: A-5 は D1641 決定 1〜3 / D1638 の委任の下で AI が確定し凍結 commit へ進む (択 3)。§11.1 の「無裁定の既定値」禁止は委任下の確定に当たらない。
- D1641 決定 3 (12 項目の値)、D1695 (n = 62)、D1697 (5% は campaign 合算)、D1699 (参照は同 session)、D1974 (窓ちょうど 2、24 h 分離は人手)。
- D2088 (`extime 3`・`reps 5`・`ycsb_max_ope 10`)、D2089 (3 cell)、D2090 (較正 3 件)、D2069 (binary は `output/env/pegasus/binaries/<sha>` へ ignored 複写、凍結は path・sha・receipt)。
- D1936 項 7 / §5.1 追補 (b): 集約する spec の path と sha256 の列は呼び出し側から明示的に受け取る。別の manifest 形式を新設しない。

## scope
- 3 spec (`floor-pair-spec/v3`、rr95 / rr50 / rr5) を tracked file として置き、1 commit で凍結する。D95 決定 2 の実装面ではない (path `output/env/pegasus/floor-pair/…/*.json`、`_is_implementation_path` で False) → 親が直接書ける、変異 matrix 免除。
- 順序 (insight t2288-binder-precheck「凍結 wave への注意点」): main 取り込み確認 → `place` (済、rc=0、`7cdf0dc3…` 701,760 bytes mode 744、policy 現行一致) → 出力 dir を spec と同じ dir に (tracked spec が dir を実在させる) → spec commit (`source_commit` = その親) → `--validate-only --expected-sha256` 3 本。
- 記録: insight (`output/insights/2026-09-18/t2288-a5-freeze/`)、decisions fragment 1 件 (A-5 の値・命名・集約対応)、worklog fragment。
- scope 外: `--execute-window` の Pegasus job body (main の `tools/pegasus/admission_registry.json` に floor-pair 系の登録なし → F660 により別 wave)、床値実測、finalize、集約発行、§5 記入、gate・検査・台帳・一般化の追加。

## 親の provisional 裁定 (攻撃対象)
- (P1) 置き場と命名: dir `output/env/pegasus/floor-pair/t2288-f1/`。spec = `spec__env-pegasus__protocol-silo__threads-48__workload-<wl>-s0.9-rmw0.json`、窓 = `window__env-pegasus__protocol-silo__threads-48__workload-<wl>-s0.9-rmw0__campaign-<campaign_id>.jsonl`、summary = `summary__env-pegasus__protocol-silo__threads-48__workload-<wl>-s0.9-rmw0__campaign-t2288-f1-<wl>-c1c2.json` (D1641 決定 3 の命名成分、issuer の `__key-value` 様式に揃える)。集約の output_dir も同 dir。`<wl>` ∈ {rr95, rr50, rr5}。
- (P2) 窓 (3 spec 共通、UTC): w1 = [2026-09-19T00:00:00Z, 2026-09-27T00:00:00Z)、w2 = [2026-09-28T00:00:00Z, 2026-10-06T00:00:00Z)。w1 末と w2 頭の間が 24 h、半開区間なので任意の w1 session と w2 session は > 24 h 離れる (分離を構成で保証、D1974 の人手確認は式で閉じる)。幅 8 日 = job body wave の着地 + queue 待ち + 1 窓の走行 (124 session、較正実測の rep wall 3.5〜4.5 s から約 1.6 h) の余裕。窓判定は session 開始ごとで `outside_window` は FATAL。
- (P3) 識別子: campaign_id `t2288-f1-<wl>-c1` / `-c2` (spec 間で相異)、window_id `<wl>-w1` / `-w2`、pair_id `pair-<wl>`、cell_id `<wl>-t48-s0.9-rmw0` (D2089 wave の既存表記)。
- (P4) seed_hex = `sha256(UTF-8 "izanagi floor-pair-spec/v3 seed|<spec_relpath>|<source_commit>")`。公開式・spec ごとに相異・commit 直前に計算可能・結果を見ずに固定。randomization は side 順序だけを決め両 side は同一 bytes なので有利な選択は存在しない。
- (P5) 実行設定: `site PEGASUS_COMPUTE`、`env_tag pegasus`、`clocks_per_us 2100`、`numactl_argv []` (較正 certify 経路は NUMA node 数 1 で numactl None、較正 3 件とも `attestation_profile.numa` は 1 node)、`extra_env {}`、`use_perf false`、`timeout_s 120` (calibrator `BENCH_TIMEOUT_S`、実測 rep wall の 26 倍)、`probe_timeout_s 30`。
- (P6) 集約対応: 期待 spec 列 = 3 (relpath, sha256)、summary_paths = 3 summary relpath、output_dir = 同 dir。期待 file 名 `b4-floor-aggregate__env-pegasus__protocol-silo__threads-48__workload-set-<20hex>__campaign-set-<20hex>.json` は識別子確定後に計算して insight へ。
- (P7) `source_commit` = spec commit の親 (= commit 直前の HEAD)。main が進んでいれば ff-only で取り込んだ後の HEAD。
- (P8) 窓 3 spec 共通は「3 cell を別 node で並走できる」ため。campaign は cell ごと (D1641「1 セルあたり n を 1 campaign」)。

## 不変条件
規律 2 (binder の検査を 1 つも緩めない、driver・issuer・test は 0 byte 変更)、§5 の値セル bytes 不変、placeholder / 三軸語を spec と insight に含めない (`s8b_holdout_freeze search` rc=0)、capstone: 3 spec とも `--validate-only` rc=0 で plan 248 session・496 測定。

## 模擬 / 実の差
`place`・`--validate-only` は実 checkout・実 record・実較正・実 binary で実走 (login node、site gate なし)。`run_window` は走らせない。

## 分割方針
軽量版だが設計択一 (P1〜P6) が凍結値を決めるので段 2 plan 1 本・段 3 レンズ 2 本 (A: 既裁定との逐語整合と事前性、B: binder / issuer の実装照合と命名の機械制約)・段 6 レビュー 2 本を read-only codex で回す。実装子は不要 (実装面 0 byte)。
