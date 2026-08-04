# 段 4 裁定 — [T-425] (軽量版のため段 2・3 なし、brief の provisional 前提を親が裁定)

## 裁定

- (P1) **採用**: 動作点は balanced (rr50 系) + write-heavy (rr5 系) の 2 点。rr50 は Pegasus registered calibration の exact 署名 (1M/48)。rr5 は分散最大側の scoping。rr95 は省く — linux 3 点の非一様性 (0.11%〜1.07%) は転移知識として package に引用し、Pegasus での対象別実測は真正 floor 設計 (裁定後) の射程とする。
- (P2) **採用**: SESSIONS=8 / SESSION_REPS=5 / WITHIN_REPS=10 / EXTIME=3 は既存 driver のまま。「測定規模の縮小」は点数 (3→2) と infra (新設なし) で行い、統計形は既存 linux 値と同形比較可能に保つ。
- (P3) **採用**: 単一テナント検査は既存 `_assert_single_tenant` のまま。gen_S Exclusive OFF の残余 (他ユーザー共存・common-mode 不可視) は scoping 値の解釈制約として package に明記する。
- (P4) **採用**: queue 滞留 (保守 15:00–19:00 + QUE 227) で wave 内に測定完了しない場合、submit receipt + 有効性検査 (F49 (ii) の (a)(b)(c)) + 値スロット pending の package で閉じる。省略でなく待ちの実測として記録する。

## プラン v2 (file 粒度)

1. **scoping driver (python)**: `orchestrator/campaign/pegasus_floor_scoping.py` (新規、between_run_floor.py の最小 env 化再利用 — measure_point / between_run_noise_floor / buildcache を同形で呼ぶ)。
   - 必須 CLI: `--out-dir` (必須引数)。repo の `output/` 配下 (特に `env/*/calibration`) を指す path は**拒否** (realpath 照合、fail-closed)。
   - 定数: records/threads/clocks_per_us は `output/env/pegasus/calibration/registered/` の registered calibration JSON から実行時に読み手書き値と照合 (p2_2._resolve と同型)。numactl は Pegasus 契約どおり空。cache_root は out-dir 配下 (worktree/submodule 内 build-variants を作らない)。
   - 出力 JSON に D145 (2) の estimand field: `evidence_class="same-submission-cohort-allocation-session-median-cv"`, `time_window_clusters=1`, `eligible_for_compare=false`。ファイル名は `scoping_between_run_*.json` (consumer glob `between_run_noise_*.json` に不一致)。
   - 三軸語 literal は変数合成 (I3)。
2. **job script**: `tools/pegasus/floor_scoping.sh` (新規、floor_campaign.sh の interpreter gate 部 (157-178 行型) を踏襲した薄い wrapper)。PBS: SFC / gen_S / 1 node / elapstim 03:00:00。`qsub -v` 経由の環境変数渡し (F99)。official 系の submit receipt 連鎖 (nonce 束縛) は**要求しない** — scoping は certified 系 artifact を作らないため。job 内で git HEAD・script sha256・hostname・qstat 束縛は記録する (provenance は残すが受理系へ配線しない)。
3. **テスト**: `orchestrator/tests/test_pegasus_floor_scoping.py` (新規)。out-dir 拒否/受理、registered 照合の mismatch 赤、estimand field、glob 不可視性。
4. **非編集**: stability.py / screening_driver.py / p2_2.py / between_run_floor.py / 既存 tools/pegasus/* / hooks / 凍結成果物。

## 変異事前登録 (DW-M01、位置は diff 確定後に M07 で anchor 再検証)

| ID | 変異 | 期待 kill (赤 node) | 単一理由性 |
|---|---|---|---|
| M1 | out-dir 拒否分岐を恒真 (拒否解除) | repo 内 calibration dir を渡すテストが受理して赤 | この層以外に同入力を拒む gate なし (新規経路) |
| M2 | registered calibration 照合を恒真 | mismatch fixture テストが ValueError 不発で赤 | 同上 (driver 内唯一の照合点) |
| M3 | estimand field 3 点の emission を除去 | field 存在検査テストが赤 | schema 検査は新テストのみ |
| M4 | 出力ファイル名を `between_run_noise_*` 形へ | glob 不可視性テストが赤 | 同上 |

- 正例 (過剰拒否検出): repo 外の正当な out-dir を受理して走る unit テストを併置 (mock measure)。
- 本 wave はテスト強化だけの wave ではない (新実装 + 新テスト) ため DW-M08 の新旧両走は非該当。
- shell wrapper は mutation harness (python) の対象外 — 静的検査 (bash -n / 既存 test_pegasus_floor_tools の形に倣う受理検査があれば追随) で扱い、matrix の射程外と worklog に明記。

## 段 6 構成 (軽量版)

- 敵対レビュー 2 本は DW-C00 軽量版条項で省略。ただし**裁定パッケージ (親起草 docs) には read-only codex レンズ 1 本**を当てる ((162) で親 brief 誤り 4 件が子に反証された前例への保険。実装 diff も同レンズの視野に含める)。
- fix 子: 赤・所見発生時に必須 (D95)。
- 変異 matrix + 受入 (dispatch_compute 経由 tests) は親が実走。省略しない。
