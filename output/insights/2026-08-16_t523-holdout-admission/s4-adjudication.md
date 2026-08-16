# 段 4 裁定 + プラン v2 — [T-523]

親裁定 / 2026-08-15 23:25 JST / base 330f67d0 / branch worktree-dev-wave-t523-holdout-admission

段 3 は 2 レンズとも NO-GO。所見 20 件を real/refuted・採用/不採用・scope 内/外で裁定する。
親は 5 件の中核主張を独立に裏取りした (下記 §0)。

## 0. 親が独立に確認した事実 (レンズの主張を鵜呑みにしない)

1. `run_once` (`orchestrator/calibrator/runner.py:392-421`) が subprocess を張る最下層で、
   `measure_point` はその呼び手 (`runner.py:534`)。→ brief (P1) は一段高すぎた。**認める。**
2. `run_once` を通さず ccbench を直接 spawn する production site が 4 本ある:
   `s1_verify_extime_calibration.py:260`、`s2_verify_calibration.py:115`、
   `s3_lock_coverage.py:87`、`backoff_profile.py:104-129`。
   → **`run_once` すら今日の共通境界ではない。認める。**
   ただし 4 本の実 flags は module 定数 (rr50 系) で、現状 holdout 比率へは到達しない。
   `backoff_profile._profile_run` だけは `workload` を引数で受けるため構造的には到達しうる。
3. ccbench は google gflags を使う (`external/ccbench/cc/silo/ycsb_silo.cc:26`
   `gflags::ParseCommandLineFlags`)。→ `--flagfile` / `--fromenv` / `--tryfromenv` /
   `FLAGS_*` 環境変数という**間接入力が実在する**。argv だけを見る分類器は不完全。**認める。**
4. `layout.repo_output_root()` は layout.py の位置から repo を導く
   (`layout.py:40-46`)。→ **worktree ごとに別の output/ を返す。認める。**
5. `campaign_claim.acquire_claim` は O_EXCL・crash 後も残す・release API 無しの one-shot claim
   (`campaign_claim.py:167-180`)。→ 「読んでから書く」窓を作らない原子的消費の既存前例。

## 1. 裁定 (所見ごと)

### 採用 = 本 wave で実装する (real, scope 内)

- **R-1 (A-2 gflags 間接入力):** gateway は `--flagfile` / `--fromenv` / `--tryfromenv` を
  拒否し、`FLAGS_` 接頭辞の環境変数を除去した閉じた env で binary を起動する。
  分類は正規化済み direct flag の last-wins 解釈で行う。
- **R-2 (A-3 perf_preflight seam):** admission 取得を production entrypoint の**最初期**へ置く。
  副作用を持ちうる注入 seam (`perf_preflight_fn` / `measure_fn` / `probe_fn`) は、
  admission 取得より前に呼ばれてはならない。production では副作用可能 seam を拒否する。
- **R-3 (A-4 seal 偽造):** `_seal` identity 方式を採らない。issuer が `id(token) -> state` に
  token 本体を保持し、検証は `state.token is token` を要求する identity capability にする。
  `copy` / `dataclasses.replace` / pickle / dict 復元 / private seal 直 import を境界テストへ入れる。
- **R-4 (A-5 token 再利用 → best-of-N):** **採用。ただし [T-524] の実験単位再定義ではない。**
  admission は cell ごとに、**既に凍結済みの schedule から導出した attempt 単位の single-use
  ticket** を発行する (planned 8 sessions/cell + protocol が凍結した認可済み retry 枠)。
  ticket は実測直前に原子的・durable に消費する。**新しい実験単位を定義せず、
  protocol が既に固定している attempt 数をそのまま数えるだけ**である点を D に明記する。
- **R-5 (A-6 worktree 分離):** 台帳と lock の root は `repo_output_root()` ではなく
  `git rev-parse --git-common-dir` から導く**全 worktree 共有の物理 root** とする。
- **R-6 (A-9 protocol bytes で key リセット):** 一回性 key から `protocol_sha256` を外す。
  key は測定効果を表す `(freeze_sha256, freeze_holdout_key, configuration_id, ccbench_pin, env_tag)`
  とする。protocol hash・manifest hash・run 座標は証跡 field として row に残すが key にしない。
- **R-7 (A-11 将来 holdout の drift):** 保護対象は hardcode した H1/H2 表ではなく、
  **検証済み freeze の holdouts から導出**する。導出集合と neutral 表の exact 集合一致を
  production gate にし、未知 holdout は拒否する (fail-closed)。
- **R-8 (B-5 / TOCTOU):** admission の根拠は「実測より前に鍵ごとの原子的作成が成功したこと」
  だけとする。読んでから書く窓を作らない。既存行を根拠に token を再発行できるのは、
  同一 run identity を証明できる resume に限る。
- **R-9 (B-4 provisioning):** 台帳 root の親 directory 生成を明示的な preflight にする。
  外部 provisioning 前提にしない。
- **R-10 (A-8 journal 削除 resume):** ledger が発行済みなのに journal が不在な run dir の
  `--resume` を拒否する。
- **R-11 (A-10 / B-2 ratio-only の過剰拒否):** **拒否する方向を採用する。**
  effective rratio が保護比率なら、skew / rmw が freeze と違っても admission を要求する。
  これは規律 2 の方向であり、ユーザー裁定「pilot だから緩めてよい方向を採らない」に整合する。
  **brief I5 と §1 の「正当な非 holdout 測定を 1 件も巻き込まない」は訂正する** —
  code path は 1 件も巻き込まないが、**手打ちの `--workload ycsb_rratio=80,...` は拒否される**。
  これは受理集合の変更であり、D96 に従って新 D と境界テストを同じ commit に入れる。
- **R-12 (B-6 座標 exact 照合が T-525 相当):** **分離する。** gate の判定は保護 signature
  だけで行い、ledger row の座標 (records/threads/workload) は**改変検出の証跡**として保存・
  照合するだけで、holdout binding の意味論へ昇格させない。D に明記する。[T-525] は実装しない。
- **R-13 (A-7 名前の二義性):** `freeze_holdout_key` / `freeze_candidate_id` /
  `trial_workload_name` を分離する。曖昧な `holdout_id` alias を新 module と ledger に残さない。
  既存 floor artifact の `holdout_id` field は互換のため改名しない。

### 不採用 = 本 wave では実装しない (real だが scope 外 → 裁定パッケージへ)

- **R-14 (A-1 / B-1 直接 spawn 4 site の gateway 移行):** **実装しない。**
  代わりに **構造 meta-test** を実装する — production の ccbench spawn site を列挙し、
  各 site が gateway 経由であるか、または「保護比率へ到達しえない module 定数 flags」の
  allowlist に載っていることを要求する。新しい spawn site が増えたら赤になる。
  成果物影響: 移行しない場合、4 site の flags を将来 holdout 比率へ変えると漏洩しうるが、
  現状は到達不能 (実測済み) であり、meta-test が drift を検出する。
- **R-15 (B-3 下流 verifier / ratified closure / report への ledger 結線):** **実装しない。**
  成果物 schema (manifest/result) を変えるため独立 wave が要る。
  **本 wave は「台帳無しの result を下流が拒否する」とは主張しない。**
  主張は「台帳を通さずに実測できない」までである。この限界を D・worklog に明記する。
- **R-16 (A-7 未 commit ledger の削除):** 完全には塞げない。保証範囲 (同一物理 root を共有する
  process 間) を D に明記し、外部 append-only authority への確定は裁定パッケージへ。
- **R-17 (B-8 規模 / plan の共通 helper 抽出):** plan v1 の編集項目 2
  (`orchestrator/append_only_jsonl.py` 抽出) と 4 (`trial_registry.py:1569-1677` の refactor) は
  **不採用**。8c の durable 書込み経路を触っても成果物の値・受理集合・参照は 1 つも変わらず、
  proof chain を壊す risk だけが増える。新 module は自前の durable append を持つ。
- **R-18 (8c の TrialLaunchAdmission も seal 方式で同じ弱点を持つ):** 本 wave では直さない。
  8c の受理集合を変えないため。insight として記録し、裁定パッケージへ。

### 変異登録から外す (帰属不成立)

- **R-19 (A-12):** plan v1 の変異候補 3 (floor callback 直前 assert の除去) は、
  production 経路では前段の `_validate_live_admissions` が base/mutant 双方を先に拒否するため
  帰属が成立しない。**DW-M01 に従い登録しない**。実効 gate (`run_once` 側と ticket 消費側) へ
  再照準する。

### I6 の読み替え (親裁定)

- **R-20:** brief I6「8c 側の受理集合を変えない」は**受理集合と artifact の話**であって
  「`trial_registry.py` を 1 byte も触らない」ではない。R-7 により保護集合は freeze から
  導出されるため、`HOLDOUT_BINDINGS` を neutral leaf から射影する編集は**任意**とする。
  射影しない場合は、両定義の exact 一致を要求する meta-test を置くこと。
  いずれの場合も 8c の既存境界テストは**期待値無変更で緑**でなければならない。

## 2. プラン v2 (実装する形)

### 実装単位 (所有素集合、逐次)

**Unit 1 — 中立 leaf + 実行 gateway**

所有: `orchestrator/holdout_observation.py` (新規)、`orchestrator/calibrator/runner.py`、
`orchestrator/tests/test_holdout_observation.py` (新規)、
`orchestrator/tests/test_ccbench_spawn_sites.py` (新規)

- 保護 signature を検証済み freeze の holdouts から導出する純関数 (R-7)。
- gflags 間接入力の拒否と正規化 (R-1)。
- identity capability (`state.token is token`) の issuer / assert (R-3)。
- `run_once` に keyword-only の admission 引数を足し、tempdir/subprocess より前に検査する。
  保護比率でなく admission 未指定なら既存 call shape・受理を一切変えない。
- `measure_point` は admission を受け取り `run_once` へ転送するだけ。
- ccbench spawn site の構造 meta-test (R-14)。

**Unit 2 — admission + 一回性台帳 + 8b 結線**

所有: `orchestrator/campaign/s8b_holdout_admission.py` (新規)、
`orchestrator/campaign/s8b_floor_campaign.py`、
`orchestrator/tests/test_s8b_holdout_admission.py` (新規)、
`orchestrator/tests/test_s8b_floor_campaign.py`

- 共有 durable root (`--git-common-dir` 由来) の解決と provisioning (R-5, R-9)。
- key = `(freeze_sha256, freeze_holdout_key, configuration_id, ccbench_pin, env_tag)` (R-6)。
- cell claim を O_EXCL で原子的に取得し、成功だけを admission の根拠にする (R-8)。
- 凍結済み schedule から attempt ticket を導出し、実測直前に durable 消費する (R-4)。
- append-only の ledger row (証跡)。座標は改変検出のみ (R-12)。
- floor campaign: admission 取得を entrypoint 最初期へ (R-2)、`_Runner` へ mapping 必須化、
  callback 直前の再検査、ledger 有り + journal 不在の resume 拒否 (R-10)、
  CLI の protocol path を canonical へ固定。

### 本 wave が主張しないこと (D と worklog に明記)

1. 台帳無しの result を下流 verifier / ratified closure / report が拒否すること (R-15)。
2. 直接 `subprocess.run` する将来の producer を機械的に封鎖すること (R-14 は検出であって封鎖ではない)。
3. 未 commit ledger の削除に対する保護 (R-16)。
4. 独立 clone 間の一回性 (共有物理 root を前提とする)。

## 3. 事前登録変異 (DW-M01)

各変異は「同じ入力を前後の層が拒否しないこと」を実装子がコードで確認して報告する。
確認できないものは登録せず実効 gate へ再照準する。

| # | 位置 | 変異 | 期待 KILL の理由 (受理集合か fail-closed 挙動の変化) |
|---|---|---|---|
| M1 | 中立 leaf の保護集合導出 | freeze 由来集合を空へ | token 無し rr80 が subprocess spy へ到達する |
| M2 | `run_once` の gate 呼出し | 削除 | direct `run_once` の rr80 が token 無しで spawn される |
| M3 | gflags 間接入力の拒否 | `--flagfile` を許可 | flagfile 経由の rr80 が token 無しで spawn される |
| M4 | cell claim の作成 | `O_EXCL` を外す | 同 key の 2 回目 fresh run が受理される |
| M5 | attempt ticket の消費順 | 実測後へ移す | ticket 未消費のまま同一 attempt を再実測できる |
| M6 | 保護集合と freeze の集合一致検査 | 削除 | H3 を足した freeze fixture で未知 holdout が素通りする |
| M7 | identity capability 検査 | `isinstance` だけへ緩和 | caller 構築 token が受理される |

**正例 (過剰拒否の検出、DW-M01 後段):**
`P1` = rr50 / rr95 / rr5 の非 holdout が token 無しで従来どおり spawn されること。
全 workload を拒否する mutant はこの正例で赤になる。

## 4. D96 手続

- 新しい D を起こす (受理集合変更の理由・射程・却下案・保証限界)。
- 境界テスト: 新規 `test_holdout_observation.py` の保護比率必須 / 非保護 passthrough、
  既存 `test_s8b_floor_campaign.py` の成功形維持、`test_trial_registry.py` の 8c 期待値無変更。
- 新 D と境界テストを同じ commit に入れる。既存期待値の書換えで新挙動へ合わせない。
