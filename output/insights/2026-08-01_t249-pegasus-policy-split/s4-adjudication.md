# 段 4 裁定 + plan v2 — [T-249]

親裁定。段 2 プラン (`s2-plan.md`)、段 3 レンズ A (`s3-lens-a.md`) / B (`s3-lens-b.md`) を受けて確定する。

## 0. 段 1 では未見だった新事実 (裁定の前提を一部覆す)

- 凍結された `tools/pegasus/policy.json:18-21` の `perf_candidates` は
  `/usr/lib/linux-tools/5.15.0-135-generic/perf` と `.../5.15.0-100-generic/perf` を指すが、
  **ログインノード `pegasus02` にはどちらも存在しない**。実在するのは
  `5.15.0-101-generic` / `5.15.0-136-generic` / `5.15.0-173-generic`、稼働カーネルは `5.15.0-186-generic`。
  (計算ノード側は未測。runbook §1 の「全 node 同構成」前提に立てば同様と推定されるが、**推定であって実測ではない**)
- `orchestrator/qualification/submission.py:105-124` はこの候補列から perf を解決し、
  機能しなければ `SubmissionPreparationError` で fail-closed する。
- したがって **D107 が「残る構造問題」と呼んだものは仮想ではなく、現に直せない stale 値として実在する**。
  そして直せない理由はまさに「共有 policy の bytes を T-139 の certified 証拠が凍結している」ことである。
- ただし `perf_candidates` を読む consumer には **T-126 (identity 束縛) が含まれる**ため、
  この値の是正は identity 契約の整理 = D96 手続を要し、本 wave では閉じられない。

## 1. 所見の real / refuted と採否

| # | レンズ | 判定 | 採否 | 裁定 |
|---|---|---|---|---|
| A1 / B1 | 両方 | **real / Critical** | **採用** | 索引だけでは裁定 (b) を実装しない。scope を実再編まで戻す (下記 2)。ただし identity 束縛部は返す |
| A2 / B6 | 両方 | real (B6 は nit) | **採用 (限定形)** | registry は**所在 inventory** に限定し、「run を支配した設定の再導出元」とは名乗らない。owner/consumer 対応検査までは作らない (過剰設計) |
| A3 / B3 | 両方 | **real / Major** | **採用** | 命名 regex 走査をやめ、**専用 directory の閉集合列挙**にする。既存 2 path は legacy 例外として registry に明示登録 |
| A4 | A | **real / Major** | **採用** | registry 本体の tracked 性も検査し、変異に事前登録する |
| A5 | A | real (scope 外) | **採用 (記録のみ)** | policy.json の直接 SHA pin は tracked 4 file (主 evidence + submit/campaign-identity/campaign-root receipt)。`output/env/pegasus/**` no-touch を維持し、閉包を裁定パッケージへ渡す |
| A6 | A | **refuted** | — | registry-only / 同値移設は `REQUIRED_CODE_IDENTITY_PATHS` を変えないので D96 不要。D96 が要るのは identity set 変更のみ |
| A7 | A | real / Minor | **採用 (手順として)** | `t126_reservation_policy_v1.json` も親の統合前 base diff 検査対象へ加える |
| A8 / B7 | 両方 | **real / Major** | **採用** | request `876519` は**5 file 対象走で 2 failed / 392 passed**。全走ではない。brief・worklog・insight はこの限定形でのみ記す。全走は段 6/7 で別 request を取る |
| A9 / B5 | 両方 | **refuted** | — | 間接書換え経路は確認できず、byte drift の死角は symlink・consumer 取り残し・discovery 層に限定される |
| B2 | B | **real / Major** | **採用 (層を明記)** | 本 wave の gate は pytest 層のみ。shell/Python の resolver 化と CI/land gate は **scope 外・裁定パッケージ**。「全層を塞いだ」とは書かない |
| B4 | B | real / Minor | **採用** | 同一 bytes symlink が純増検出力。現行 path の存在/tracked は既存 node が先に kill するので**純増に数えない** |

## 2. plan v2 — 採用 scope

裁定 (b) の「タスク別 file へ再編」を、**凍結 bytes を 1 byte も変えずに実行できる範囲まで**実装する。
判定基準は「そのキーが凍結証拠または identity 契約に束縛された consumer から読まれているか」である。

### 移設する (task 固有かつ identity 非束縛)

| key (`policy.json`) | 移設先 | live consumer |
|---|---|---|
| `smoke_walltime`, `smoke_walltime_s` | `tools/pegasus/policies/calibration_v1.json` | `test_pegasus_tools.py` の PBS header 一致のみ |
| `certify_walltime`, `certify_walltime_s` | 同上 | `certify_calibration.sh`, `submit_certify.sh` |
| `finalize_reserve_s` (top-level) | 同上 | `certify_calibration.sh` |
| `floor_walltime`, `floor_walltime_s` | `tools/pegasus/policies/floor_v1.json` | `floor_campaign.sh`, `submit_floor.sh` |

**値は現行と完全同値で移す。受理集合を 1 bit も変えない。**

### 移設しない (理由付き)

- `silo_ladder_rung1` block — T-139 の凍結証拠と identity が bytes を束縛。**移設不能**。
- `project` / `queue` / `nodes` / `expected_cpu_model` / `expected_physical_cores` /
  `gflags_*` / `glog_*` / `perf_candidates` — D107 決定 1 が「複数タスクが共有する値は共有 policy に置く」と
  定めた**共有・サイト値**であり、そもそも task 固有ではない。加えて T-126 identity と T-139 が読む。
  → **移設しない。**「共有 file 自体が凍結されていて共有値を更新できない」残余問題は §3 へ返す。

### 移設後の不変条件

- 移設した 7 key は `policy.json` に bytes として残るが、**live consumer を持たなくなる** (T-139 の凍結
  snapshot の一部になる)。二重正本にはしない。これを検査 node で守る。
- `tools/pegasus/policy.json` と `output/env/pegasus/**` と
  `orchestrator/qualification/t126_reservation_policy_v1.json` は 1 byte も変えない。
- `orchestrator/qualification/contract.py`、`identity.py`、`submission.py`、`t126_driver.py`、
  `silo_ladder_rung1.py`、`silo_ladder_rung1.sh`、`submit_silo_ladder_rung1.sh`、
  `t126_qualification.sh`、`submit_t126_qualification.sh` は編集しない。
- production 挙動・実験の受理集合・certified 選択・proof chain を変えない。

### 新設する索引と gate

- `tools/pegasus/policies/registry_v1.json` — **所在 inventory**。repo-relative path のみを持つ。
  hash は複写しない。legacy 例外 2 件 (`tools/pegasus/policy.json`,
  `orchestrator/qualification/t126_reservation_policy_v1.json`) を明示 entry として持つ。
- 新 pytest node が守るもの (純増検出力):
  1. `tools/pegasus/policies/` 直下の全 regular file (registry 自身を除く) が registry に登録済み — **閉集合列挙**
  2. registry の全 entry が実在・regular file・**非 symlink**・tracked
  3. **registry 本体が tracked**
  4. `policy.json` の live consumer が T-139 経路と T-126 経路だけであること (移設済み 7 key を
     読む live consumer が居ないことの静的検査)

## 3. scope 外 real 所見 — 裁定パッケージとしてユーザーへ返す

1. **`perf_candidates` が stale で、共有 policy が凍結されているため直せない (新事実、上記 §0)。**
   是正には T-126 の共有値読みを task/site file へ付け替え、`REQUIRED_CODE_IDENTITY_PATHS` を
   整理する D96 手続が要る。**本 wave では触らない。**
2. T-139 の `silo_ladder_rung1` block を凍結 file から動かすこと (evidence 再発行 = 実 job 再走が必要)。
3. `policy.json` の直接 SHA pin 閉包は tracked 4 file (A5)。実分割の裁定にはこの閉包全体を渡す。
4. shell / Python consumer を registry resolver 経由にすること、および CI / local-main land gate 層 (B2)。
5. `perf_candidates` の値そのものの更新 (別 ID で起票)。

## 4. 変異事前登録 (`DW-M01`)

すべて統合 commit 後の本走で実施する。kill = 受理集合または fail-closed 挙動が期待方向へ変わること。

| ID | 変異 | 期待 kill node | 単一理由性の根拠 |
|---|---|---|---|
| M1 | registry から `calibration_v1.json` entry を削除 | 新 node (閉集合列挙) | 手前に registry を読む検査は repo 内に存在しない |
| M2 | `tools/pegasus/policies/unregistered_v1.json` を tracked で追加 | 新 node (閉集合列挙) | 同上。既存 suite に policies/ の閉集合 scan はない |
| M3 | registry 本体を index から外す (untracked 化) | 新 node (registry tracked) | `REQUIRED_CODE_IDENTITY_PATHS` に registry は入らないので既存 parametrized node は見ない |
| M4 | `calibration_v1.json` を同一 bytes の symlink へ置換 | 新 node (非 symlink) | 既存 hash node は policies/ を読まない。bytes 一致なので内容検査では捕まらない |
| M5 | `certify_calibration.sh` の読み先を `policy.json` へ戻す | 新 node (live consumer 検査) | 値は同値なので既存 header 一致 node は緑のまま |
| M6 | `calibration_v1.json` の `certify_walltime_s` を 7199 へ | 既存 `test_pegasus_tools.py` の header 一致 node | **純増ゼロ。既存 node が先に kill する**ことの確認用 (帰属の分離) |
| M7 | **正例**: 規約に沿う新 task file を作り registry にも登録 | **どの node も赤にならないこと** | 承認外の過剰拒否がないことの正例 (`DW-M01`)。緑が期待値 |

`DW-M08` に従い、M1〜M5 は**変更前 HEAD (`7b24f81`) 版でも走らせる**。HEAD には新 node が無いため
どれも検出されないはずで、その差分が新テストの純増検出力である。M6 は HEAD でも既存 node が
検出するので純増ゼロとして記録する。

## 5. 実装単位の分割 (`DW-S05-A`)

編集ファイル所有を素集合にする。単位間に依存があるため **U1 → U2 の順に直列**で投入する。

- **U1 (新設面)**: `tools/pegasus/policies/calibration_v1.json`、`floor_v1.json`、`registry_v1.json`、
  `orchestrator/tests/test_pegasus_policy_registry.py` を排他所有。
- **U2 (付け替え面)**: `tools/pegasus/certify_calibration.sh`、`submit_certify.sh`、`floor_campaign.sh`、
  `submit_floor.sh`、`orchestrator/tests/test_pegasus_tools.py`、`test_pegasus_floor_tools.py` を排他所有。
- 親: docs (worklog / decisions / insights / `tools/pegasus/README.md`)、統合 commit、変異 matrix、
  受入全走、local main 取り込み。

`t141_region_profile.sh` は **付け替え対象外** — 読むのは共有・サイト値だけで、移設対象 7 key を
読まない。専用テストも無いため触らない。

## 6. 親の受入・検査手順

1. 統合後に `git diff --exit-code 7b24f81 -- tools/pegasus/policy.json output/env/pegasus
   orchestrator/qualification/t126_reservation_policy_v1.json`
2. `sha256sum tools/pegasus/policy.json` = `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac`
3. 計算ノードで**全走** (別 request ID を取得)。段 1 の request `876519` は
   「5 file 対象走で 2 failed / 392 passed」としてのみ記録し、受入全走とは呼ばない。
4. `python3 tools/check_docs.py`、`tools/check_codex_agents.py`、commit 後 provenance 監査。
