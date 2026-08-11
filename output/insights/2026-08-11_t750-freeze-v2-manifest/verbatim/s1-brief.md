# 親 brief — dev-wave [T-750] 統合実装 (freeze v2 producer + oracle manifest CLI) 段 1

wave `dev-wave-t750-freeze-v2-manifest` / branch `worktree-dev-wave-t750-freeze-v2-manifest` /
base main `0c0fbf25`。状態の正本 = worklog 末尾 (405)。材料 =
`output/insights/2026-08-11_t8b-restart-integration/` (§R-6 / §R-7、`stage4-ruling.md`)。

## 確定済みユーザー裁定 (前提)

- **[T-750] (1) producer identity = (a)** (worklog 405)。v2 生成を**記録上の generator である
  旧 module (`orchestrator/campaign/s8b_holdout_freeze.py`) 内へ実装**して記録を真実に保つ。
  transition table (`_TRANSITION_V1_TO_G1` の `/generator/path` 不許可) は変更しない。
- **[T-750] (2) budget authority = (a)** (worklog 405)。後段の人間承認が **budget 数値そのものを
  承認する契約**に含める ([T-657] の人間手番路線と整合)。
- **[T-782] = (b)** (worklog 404)。reviewed spec (schedule / run contract / campaign ID) を
  **凍結成果物として先に作り**、manifest CLI はその bytes を hash 照合するだけにする。
  **spec の承認者と時点を起票文で明示する** → (P1)。
- **[T-781] = 択保留・調査先行** (worklog 404)。W-1 (official 解禁) は実装しない。
  → A-12 により **実 floor result は存在せず、生成できるのは synthetic fixture だけ**。
- 実装時 must-fix: **A-8 / B-9** (出力 path containment)、**B-8** (namespace 検査)。

## 並走ガード 3 条件 (Q3 (a)、worklog 378)

(i) ノード同居なし (ii) [T-139] pilot / 本走の走行中はキュー投入を控える
(iii) 裁定帯域は A 優先。**本 wave はキュー投入をしない** (実走が synthetic 限定のため計算資源不要)。
受入全走の dispatch を投入する直前に `qstat` を再確認する。

## 起動時の所有権確認 ([T-782] spec 凍結)

1. **凍結は未了。** `output/` 直下に spec 成果物は不在 (実測: `output/` は README/campaigns/
   dev-wave-supervisor/env/insights/reports/s1-budget/s1-freeze/s6-rounds/s8b-freeze/
   s8c-preregistration/t080-migration/task-runs のみ)。
2. **8b 残余 wave (`dev-wave-t8b-restart-residue`、稼働中) の射程と突き合わせ済み。**
   同 wave の brief §scope 外 が「**W-3 / W-4 / W-5 — [T-750] 未裁定。freeze v2 再凍結と
   oracle 実走は着手しない**」と明記 (同 wave の base main `0c336b8e` は worklog 405 を含まない)。
   同 wave の scope = `s8b_floor_campaign.py` / `orchestrator/tests/README.md` /
   `docs/phase3-8b-restart-runbook.md`。→ **未所有と確定。本 wave が spec 凍結から実施する。**
   本 wave は runbook を編集しない (file 所有の非重複を維持)。

## 段 1 実測 (すべて本 wave で実物から採取。既存 docs を根拠にしていない)

- **M-1 (DW-O09 pin 閉包 — 単位 A の編集は凍結 bytes を変えない)。**
  `s8b_holdout_freeze.py` を pin するのは (i) `output/s8b-freeze/holdout_freeze.json` の
  `/generator/{path,sha256}`、(ii) T-080 受領証 `output/t080-migration/legacy-freeze-repin.receipt.json`
  の `metadata_fields`、(iii) `test_s8b_oracle_driver.py:192-197` の同 tuple。
  **(ii) は `disposition="metadata-only"`** であり、受領証は `recorded_sha256=1910fff3…` を
  metadata 扱いのドリフトとして受理済み。実測: 現 worktree の module sha は `89cb2970…` で
  記録値と既に不一致だが、`s8b_holdout_freeze.py verify` は **rc=0** (受領証経路)。
  → 単位 A の編集で凍結 bytes・受領証・pin はいずれも変わらない。
- **M-2 (B-8 の機序を実物で確認)。** `s8b_ratified_freeze._assert_namespace_clean` は
  `git status --porcelain --untracked-files=all -- output/s8b-freeze` の非空を
  `namespace-dirty` で拒否する。candidate を canonical namespace 配下へ書くと
  `resolve_active_generation` は `no-active` でなく `namespace-dirty` に倒れる → (P4)。
- **M-3 (A-9 の機序を実物で確認)。** `s8b_oracle_manifest._validate_schedule:310-328` は
  「与えられた cell 集合の中での完全ブロック性」しか検査せず、`build_manifest:729-732` は
  holdout が freeze の部分集合であることしか要求しない。configuration 側の網羅要求は
  **どこにも無い**。→ 各 holdout 1 configuration・`n=1` の schedule が通る。
- **M-4 (W-4 の CLI は未存在)。** `s8b_oracle_manifest.py` に `main` / argparse は 1 つも無い
  (`build_manifest` / `write_manifest` / `verify_manifest` の API のみ)。新設は純増。
- **M-5 (純増検出力 — 性質で検索)。** (i)「producer の出力先が canonical namespace / symlink /
  root 外を指す」を拒否する検査は `s8b_holdout_freeze.py` に無い (`generate` は
  `output_path.exists()` の 1 件のみ)。(ii)「schedule の configuration 集合が freeze の
  構成集合を網羅する」検査は repo 全体に無い (M-3)。(iii)「budget 値が承認 record と一致する」
  検査は無い (`_validate_execution_snapshot:642-656` は有限非負・key exact のみ)。
- **M-6 (synthetic 経路は既存)。** `orchestrator/tests/s8b_v2_freeze_fixture.py` が
  per-pair floor + budget の充填形を単一源で生成する。A-12 下の正例はこれを使う。
- **M-7 (DW-O10 producer write-path)。** 本 wave の producer が書くのは v2 candidate JSON
  1 種のみ。`output/s8b-freeze/` 配下には 1 byte も書かない (不変条件 2)。

## scope (実装する)

- **A. [T-750](1) W-3 freeze v2 producer** — `s8b_holdout_freeze.py` 内に v2 g1 candidate 生成を
  足す。入力 = v1 active freeze bytes + floor 成果物 + **承認 record**。出力 = candidate JSON。
  budget は承認 record の数値と exact 一致でなければ拒否 ([T-750](2))。
  A-8/B-9 の出力 path containment と B-8 の namespace 拒否を同じ関数で閉じる。
- **B. [T-782](b) reviewed spec の凍結機構** — spec schema (schedule 生成パラメータ /
  run contract / campaign ID) と承認 record、その検証器を新設する。
- **C. W-4 oracle manifest CLI** — 承認済み spec bytes だけを入力に manifest を組む CLI。
  caller 供給の schedule を受理しない (A-9 封鎖)。

## scope 外 → 実装しない

- W-1 (official 解禁)、W-2 床値実測、W-5 oracle 実走。実 floor result の生成 (A-12)。
- `docs/phase3-8b-restart-runbook.md` の編集 (残余 wave が所有)。
- certificate v2 / journal / ratified verifier の拡張 (D86(5) の先送り、A-5)。

## 不変条件 (破ったら停止)

1. v1 の `verify()` / `verify_document()` / `generate` / `search` / `verify_cli_with_t080_receipt` の
   **受理集合を 1 件も変えない**。T-080 受領証と `V1_FREEZE_SHA256` を変えない。
2. `output/s8b-freeze/` 配下に実ファイルを作らない (= 発効しない)。canonical namespace への
   書き込みは機械拒否する。`FROZEN_MANIFEST`・`floor_protocol.json` の 3 pin を変えない。
3. transition table (`_TRANSITION_V1_TO_G1` / `_TRANSITION_GN_TO_GN1`) を変えない。
4. 新設束縛は **fail-closed のみ**。「記録があるから認可済み」型 unlock を作らない (D86(8))。
   AI が承認者になる経路 (自己承認・既定値による承認省略) を作らない。
5. 実走データを作らない。正例は synthetic fixture のみ (A-12)。
6. キュー投入をしない。並走ガード 3 条件を維持する。

## 成果物影響 (`DW-G05`、1 行ずつ)

- **A を実装しない場合:** v2 世代を作る唯一の経路が無く、floor/budget を充填した世代が発効できない
  ため certified 選択が永久に v1 の `floor=null` / `budget=null` で止まる。
- **A の budget 束縛を欠く場合:** 巨大値の budget JSON が承認を経ずに世代へ入り、事前登録済み
  探索予算が実質無効化されて ledger reservation の総枠 gate が fail-open する。
- **B / C を実装しない場合:** 縮小 schedule (各 holdout 1 configuration・`n=1`) の manifest が
  通り、比較すべき configuration を走らせないまま judge が `unique-best` を返して
  **certified 選択の winner が直接改変される** (A-9)。
- **A-8/B-9 を閉じない場合:** `--output` に `output/s8b-freeze/active/<64hex>.json` を渡せば
  active loader を停止でき、oracle 全体が可用性ごと落ちる。
- **B-8 を閉じない場合:** candidate 生成のたびに `resolve_active_generation` が
  `namespace-dirty` へ倒れ、本物の namespace 汚染と区別できなくなる。

## 親の provisional 裁定 (攻撃対象。段 3 で必ず攻撃させる)

- **(P1) spec の承認者と時点。** 承認者 = **ユーザー (人間)**、時点 = **将来の実凍結手番**。
  本 wave は spec schema・承認 record schema・検証器・candidate 生成までを実装し、
  **実 spec の発効 (canonical path への設置と承認 record の署名) は行わない**。
  CLI は承認済み spec 不在時に `no-approved-spec` で fail-closed する。
  AI が `--approver` を自分で埋めて通せる経路を作らない。
- **(P2) spec が凍結するのは schedule の rows ではなく生成パラメータ**
  (`n` / `master_seed` / `block_sizes` / `holdout_ids` / `configuration_ids`) とし、
  CLI が `build_schedule` で決定論的に再生成して `schedule_sha256` を照合する。
  **加えて CLI は spec の `configuration_ids` が active ratified freeze の各 holdout の
  構成集合と exact 一致することを要求する** (A-9 を spec 承認だけに委ねず機械でも封じる)。
- **(P3) budget authority の形。** 承認 record が `budget` の数値そのものを含み、producer は
  入力 budget JSON と record の値の **canonical bytes 完全一致**を要求する。差があれば赤。
- **(P4) candidate の出力先。** 既定は canonical namespace の**外**
  (`output/s8b-freeze-candidates/` を提案)。canonical namespace 配下・symlink・
  repo root 外・既存ファイルへの出力はすべて拒否する。
- **(P5) 並列分割。** 単位 A = `s8b_holdout_freeze.py` + `test_s8b_holdout_freeze.py`、
  単位 B = 新 module (spec) + `s8b_oracle_manifest.py` + 対応 test。file 所有は素集合。

## 並列分割

本 wave は **受理集合を変える gate を新設し正しさ防壁に触れる**ため `DW-C00` により軽量版に
しない。段 2 プラン 1 本、段 3 敵対 2 レンズ、段 5 実装 2 本 (単位 A / 単位 B)、段 6 レビュー 2 本。
