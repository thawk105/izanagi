# 段 1 brief — 床値 protocol の再封印を AI へ開放する (案 1 + 案 3)

wave = floor-reseal-authority / 2026-08-16 / branch worktree-dev-wave-floor-reseal-authority

## 確定済みユーザー裁定 (2026-08-16、逐語控え = rulings-inbox/2026-08-16-floor-reseal-ai-authority.md)

- **案 1** = 床値 protocol のうち AI が更新してよいのは `contract_sha256` と `ccbench_pin` の 2 つだけ。
  それ以外を変える改訂は引き続き人間手番。
- **案 3** = 床値 protocol は (環境契約 hash, ccbench pin) の組ごとに 1 つ。同じ組への 2 件目を機械的に拒否。
  既存の凍結 bytes は 1 件も上書きしない (追加のみ)。
- 案 2 (測り直しの事前登録) は不採用。
- 2026-08-10 / 08-11 の Q2 (承認 A・発効 X ともに人間) を**この限定範囲でのみ**解除する。
- Q3 (lockstep) は破らない。D437 はこの裁定で部分的に supersede される。

## 段 1 前の実測 (read-only、実装差分ゼロ)

| # | 実測 | 値 | 出典 |
|---|---|---|---|
| M-1 | 封印済み protocol の `ccbench_pin` | `d706650cdb31e442bef45b9b4216951d4fb40969` | `output/s8b-freeze/floor_protocol.json` |
| M-2 | HEAD の `external/ccbench` gitlink | `511c9538e4e8efa54b45cda62e72389ed3b706ec` | `git ls-tree HEAD external/ccbench` |
| M-3 | `s8b_approved.CCBENCH_FULL_SHA` | `511c9538e4e8efa54b45cda62e72389ed3b706ec` | `s8b_approved.py:67` |
| M-4 | 封印済み protocol の `contract_sha256` | `e576e9cd…e242c01` | 同 artifact |
| M-5 | active 環境契約 (activation serial 1) | pegasus g1 = `e576e9cd…e242c01` (g2 は登録済み・非活性) | `env_contract_activations/00000001.json`, `env_contract.py:245-303` |
| M-6 | 封印 path | `output/s8b-freeze/floor_protocol.json` 固定・create-only | `s8b_floor_campaign.py:161,794` |
| M-7 | 凍結チェーン検証は保留中 | `freeze_verification_hold.HELD = True`、解除は**ユーザー明示命令のみ** | `freeze_verification_hold.py:14,54-62` |
| M-8 | 保留中の該当 check | `s8b-floor.protocol-bytes-expected-pin` / `s8b-floor.sealed-protocol-ccbench-pin-current-head` | 同 `:20-21` |
| M-9 | 床値 campaign が使う protocol | 固定 1 本 (`PROTOCOL_PATH="output/s8b-freeze/floor_protocol.json"`) | `tools/pegasus/floor_campaign.sh:947` |
| M-10 | 封印済み protocol の live admission | **今日も PASS** (`validate_protocol_against_current`)。`validate_protocol` は `ccbench_pin` を HEAD と cross-check しない | 親の probe (下記) |
| M-11 | 承認定数から今日組み立て直した protocol と封印済みの差 | **`ccbench_pin` の 1 field だけ**。他 17 key は完全一致 | 同 probe |
| M-12 | 組み立て直した canonical sha256 | `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a` | 同 probe |
| M-13 | 固定 path を参照する production consumer | Python 5 件 + shell 1 件 = 6 件 (`certified_writer_admission.py:207`, `s8b_holdout_admission.py:53`, `s8b_holdout_freeze.py:46`, `s8b_ratified_freeze.py:76`, `s8b_prediction_runner.py:79`, `floor_campaign.sh:947`) | grep |

probe = `/work/1/SFC/tanab/dev-wave-jobs/wave-floor-reseal-authority/probe_current_admission.py` (repo 外・read-only)。

**結論:** (contract, pin) の組は既に乖離している。封印済み = (g1, `d706650`)、現在 = (g1, `511c9538`)。
**現在の組に対応する床値 protocol は 1 件も存在しない。** DW-G04 の発火 gate は既存 artifact で書ける。

## scope (この wave が作るもの)

1. **組 index と 2 件目の機械拒否 (案 3)** — 既存の固定 path artifact を含む全 protocol を
   (contract_sha256, ccbench_pin) で索引し、同一組 2 件目を fail-closed で拒否する。
   拒否は 2 層 = (a) 発行経路、(b) repo 全体を走査する常設不変条件検査 (手で足した 2 件目も落とす)。
2. **AI 発行可能な再封印経路 (案 1)** — 先行 protocol を解決し、
   不変 field を byte-exact に継承、`contract_sha256` と `ccbench_pin` だけを更新した
   protocol を、**組から決定論的に導出した path** へ create-only で追加する。
   `--confirm-user-freeze` と isatty を要求しない。
3. 既存の人間手番 `freeze_protocol` (isatty + confirm + T-080 receipt) は**そのまま残す**。

## scope 外 (実装しない。理由付き)

- **consumer の resolution 切替** — `floor_campaign.sh:947` の固定 path、`certified_writer_admission.py`、
  `s8b_holdout_admission.py`、`s8b_prediction_runner.py`、`s8b_ratified_freeze.py`。
  切り替えると式 3 (盲検封印) が発火して campaign launch が拒否される。これは正しい挙動だが、
  prediction の再封印という別の裁定事項を巻き込む。後続 wave へ。
- **環境世代 g2 の活性化** — D437 の対象。Q3 lockstep により、実際の再封印は g2 活性化と同一 chain で行う。
- **`freeze_verification_hold.HELD` の解除** — 解除条件は「ユーザーの明示命令のみ」(M-7)。触らない。
- **実際の再封印の実行** — 本 wave では行わない。env 世代が g1 のまま floor だけ進めると
  Q3 の片側交代になる。機構だけを land し、実発行は g2 活性化 chain の後続 wave。
- prediction seal の再封印、`s8b_approved` 承認定数の編集。

## 不変条件

- 規律 2。受理集合を**広げない**。既存の受理・拒否を 1 件も変えない。
- `output/s8b-freeze/floor_protocol.json` の bytes を 1 byte も変えない。
- `test_frozen_artifacts.py` の `FROZEN_MANIFEST` 23 key と
  `FROZEN_KEYSET_PROVISIONAL_82803D6D` を変えない (本 wave は新 artifact を repo へ追加しない)。
- `freeze_verification_hold.py` を編集しない。
- `s8b_approved.py` の承認定数を編集しない。
- 既存 protocol の上書き・削除・移動をしない (追加のみ)。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 案 1 の「不変」を、裁定文が列挙した 13 field ではなく
  **`contract_sha256` / `ccbench_pin` 以外の 16 field 全部**と解釈する
  (`schema` / `env_tag` / `wired_min_rel_floor` を含む)。
  根拠 = 「AI が更新してよいのは…2 つだけ」「これら以外を変える改訂は引き続き人間手番」。
- **(P2)** 不変 field の値は**先行 protocol から byte-exact に継承**し、`s8b_approved` 定数から
  再導出しない。定数は人間が編集可能なので、定数経由で不変 field が動く経路を塞ぐ。
- **(P3)** 新 protocol の path は組から**決定論的に導出**し、呼び手が選べない形にする。
  D437 が「receipt に選ばせると submitter が検証対象を選べる受理拡大になる」として却下した形を避ける。
- **(P4)** 案 3 の「機械的に拒否」は発行時拒否と常設不変条件検査の 2 層。片方だけにしない。
- **(P5)** `ccbench_pin` は HEAD gitlink の実測、`contract_sha256` は active activation が指す
  current contract から取る。どちらも呼び手引数にしない。
- **(P6)** 本 wave では実 repo へ新 protocol artifact を追加しない (Q3 lockstep)。
  親の live dogfood は「実 repo を走査して組 index を出す read-only 検査」で行う。

## 成果物影響 (DW-G05)

- **実装しない場合:** 環境契約 hash か ccbench pin が前進するたび、床値 protocol の再封印が
  人間の対話 shell 手番になる。現に (g1, `d706650`) → (g1, `511c9538`) の乖離が起きたまま、
  対応する床値 protocol は 0 件。certified 比較の物差しを新しい組で作れないため、
  **その組での certified 選択・材料レポート・試行台帳が 1 件も生成できない。**
  **ただし M-10 により、乖離は live admission を今日ブロックしていない** (`validate_protocol` は
  `ccbench_pin` を HEAD と cross-check しない)。止まっているのは凍結チェーン側の 2 検査であり、
  それは 2026-08-12 の裁定で**保留**にされている (M-7/M-8)。したがって
  「実装しないと今日何も走らない」とは書けない。正しい記述は
  **「記録された測定条件が実体と食い違ったままになり、新しい組で真正な物差しを封印できない」**である。
  親はこの点で初稿の brief を自ら訂正した (2026-08-16 14:30 JST)。
- **実装した場合の受理集合の変化:** 新規に受理されるのは
  「先行 protocol の 16 field と byte-exact、かつ組が未使用な protocol の追加」だけ。
  既存の受理・拒否 (固定 path の create-only、isatty gate、承認 pin 検査、`validate_protocol`) は不変。
  certified 選択・proof chain の**現在値は 1 件も変わらない** (本 wave は artifact を追加しないため)。

## 変更面の実アンカー

| path:line | 何か |
|---|---|
| `orchestrator/campaign/s8b_floor_contract.py:36-42` | `_PROTOCOL_KEYS` (exact 18 key) |
| `orchestrator/campaign/s8b_floor_contract.py:106-228` | `validate_protocol` (承認 pin・cross-field 照合) |
| `orchestrator/campaign/s8b_floor_contract.py:231-243` | `canonical_protocol_sha256` |
| `orchestrator/campaign/s8b_floor_campaign.py:161` | `_FLOOR_PROTOCOL_REL` |
| `orchestrator/campaign/s8b_floor_campaign.py:565-582` | `_ccbench_gitlink` (HEAD gitlink 実測) |
| `orchestrator/campaign/s8b_floor_campaign.py:585-676` | `build_protocol_document` |
| `orchestrator/campaign/s8b_floor_campaign.py:679-684` | `_guarded_freeze_dirs` |
| `orchestrator/campaign/s8b_floor_campaign.py:687-723` | `_write_protocol_document_create_only` |
| `orchestrator/campaign/s8b_floor_campaign.py:726-744` | `write_protocol_document` (凍結領域拒否) |
| `orchestrator/campaign/s8b_floor_campaign.py:747-825` | `freeze_protocol` (人間手番: confirm + isatty + T-080) |
| `orchestrator/campaign/s8b_floor_campaign.py:5674-` | `_freeze_protocol_parser` / CLI dispatch |
| `orchestrator/campaign/env_contract.py:240,628,706-713` | `_build_registry` / `REGISTRY` (activation 駆動 view) / `lookup` |
| `orchestrator/campaign/env_contract.py:671-703` | `resolve_by_contract_sha256` (歴史世代解決) |
| `orchestrator/campaign/s8b_approved.py:46-67` | 承認定数 (`CCBENCH_FULL_SHA` 等) |
| `orchestrator/campaign/freeze_verification_hold.py:14,16-38` | `HELD` / `HELD_CHECK_IDS` |
| `orchestrator/tests/test_frozen_artifacts.py:41-118` | `FROZEN_MANIFEST` / keyset pin |
| `orchestrator/tests/test_s8b_floor_campaign.py:1153-1180` | sealed pin hold の positive control |
| `orchestrator/tests/test_s8b_floor_campaign.py:6176-6177` | `ccbench_pin` / `protocol_sha256` の literal pin |
| `tools/pegasus/floor_campaign.sh:947` | `PROTOCOL_PATH` 固定 |

## 分割方針

実装は 1 単位。編集ファイルが `s8b_floor_contract.py` / `s8b_floor_campaign.py` / 対応 test に集中し、
所有を素集合に割れない。段 2 = codex plan 1 本、段 3 = 敵対 2 本、段 5 = 実装 1 本、
段 6 = 敵対レビュー 2 本 + fix + 変異 matrix + 受入全走。

## 受入・実測環境

- 焦点走: login node で `python3 tools/run_tests.py` (bounded local)。
- 受入全走: `tools/run_tests.py` の受入形。受入 lease を `tools/dev_wave_wait.py acceptance` で claim。
- 計算ノードでの実走 (床値 campaign 本走) は本 wave では行わない。
