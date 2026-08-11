# 段 1 brief — dev-wave-t657-stage0-fold

worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold`
branch = `worktree-dev-wave-t657-stage0-fold`、base main = `856f4d4c`。
受入環境 = Pegasus (login で `tools/run_tests.py`、dispatch 判断は段 6 で確定)。

## 1. scope (3 本立て、[T-657] 段 0 の続き)

- **S-A (docs)** `docs/calibration-freeze-authority-bundle-design.md` §12 の帳簿畳み込み。
  §12.3 の R1 / R2 / R3 を §12.1 「確定済み」へ移し、§12.3 は「本 wave 時点で残る
  ユーザー裁定なし」へ書き換える。R1 は §7.5、R2 は §10.2、R3 は §10 の段 6 行が正本節。
- **S-B (実装面)** [T-795] (a) = 失効 record の exact schema を §7.5 に確定し、
  `orchestrator/tests/calibration_freeze_authority_contract.py` に
  「設計 §7.5 の key 表 ⇔ 検証器の定数」の drift 束縛を足す (§8.1 の selection enum 束縛と同型)。
- **S-C (実装面)** [T-796] = 段 6 完了 predicate の**構造部分**を §10 段 6 行に exact に書き、
  policy 依存部分を `required_gates` の未解決 entry として明示的に残す。

## 2. 確定済みユーザー裁定 (覆さない)

- R1 = (a): `revocations/<bundle_digest>.json`・**exact 7 key**・束当たり 0/1 件・時刻 UTC 秒 int。
- R2 = (b): 段 0 の完了は先送り確定 S / B の裁定後まで待つ。applicability は広げない。
- R3 = 分割: 段 6 は構造部分 (X の形状・ancestry) だけ段 0 で固定、policy 依存部分は後。
- Q3 (ii) = `no-lower-fallback-fail-closed` は不変 (失効後に下位へ落とさない)。
- 一次控え = `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md` §88。

## 3. 不変条件 (破ったら停止)

1. **段 0 status は `incomplete` のまま。** `CFAB-S-SEAL` / `CFAB-B-SIDE-EFFECT` は
   `unresolved` のまま、`_applicable_unresolved_count` を減らす変更をしない。
   `require_stage0_complete` が今日どおり失敗し続けることをテストで固定する。
2. **他者手番 gate 2 件は不変。** `FREEZE-AX-TOPOLOGY` (nonconforming / lower-impl-wave) と
   `FREEZE-CONFORMANCE-LITERAL` (unresolved / lower-wa-wave) の owner・status を動かさない。
3. **`CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` は `pending` のまま** (段 1 以降の手番)。
4. **fixture 行 (`CFAB-7.2-*` / `CFAB-11.*`) と 10 件の fixture case を増減しない。**
   `_EXPECTED_RAW_SHA256_BY_FIXTURE` / `_EXPECTED_FIXTURE_ENTRIES_SHA256` /
   `_EXPECTED_ROW_IDS_SHA256` / `row_coverage` を一切動かさない (S-B/S-C は行を足さない)。
5. **受理集合を緩めない。** 新しい gate entry は `incomplete` を維持する方向にだけ効く。
   失効 schema は「fallback しない terminal fail-closed」を弱めない。
6. 実装面 (`orchestrator/tests/*.py`、fixture JSON) は Codex `role=author` が書く。親は docs だけ。

## 4. 実測した前提 (brief 前、base `856f4d4c` の worktree)

- 現行 `required_gates` = 8 件、`entries_sha256` =
  `93cfe2b396d4831800537967d67628c7bca38b8b7595c4ffedaccb5e88211e41`、
  manifest `status` = `incomplete`、`row_coverage.pending_count` = 5、`row_count` = 10。
- 裁定 profile = 12 件。`CFAB-S-SEAL` / `CFAB-S-GUARANTEE` / `CFAB-B-SIDE-EFFECT` が `unresolved`。
- 設計 §8.1 の裁定 ID 12 件は `_PROFILE_IDS` と exact 一致が機械束縛済み
  (`_extract_ruling_ids`)。selection 列も `_SELECTION_ENUMS` と exact 束縛済み。
- `CFAB-S8-S10-CONTRADICTION` は **`required_gates` にだけあり `_PROFILE_IDS` には無い** —
  「設計上のユーザー裁定は gate 側、束ごとの裁定項目は profile 側」という既存の分離。
- **DW-O09 の pin 閉包 (実測):** 設計 doc の bytes を pin する凍結 manifest・trust root は
  **存在しない**。path を持つのは `calibration_freeze_authority_contract.py:19,42` と
  `manifest.v1.json` の `design_source.path` だけ。docs 側の hit は `docs/README.md` /
  `docs/decisions.md` / `docs/freeze-permanent-design.md` / runbook / worklog の**言及**であり
  bytes pin ではない。よって DW-O10 (producer write-path) は**不成立**。
- **既存被覆の性質検索 (機構名でなく):** 「失効 record の key 集合を設計本文と検証器で
  二重化して drift を落とす」検査は repo に**無い** (`revocation` の hit は下位 family の
  `s8b_ratified_freeze.py` だけ)。「段 6 の完了 predicate の構造部分を機械束縛する」検査も**無い**。
  よって S-B / S-C の純増検出力 = (i) 設計 §7.5 の key 表と検証器定数の片側書き換え、
  (ii) 段 6 構造 predicate の docs 側だけの緩和、の 2 型。
- **下位 family の先例 (実測):** `output/s8b-freeze/revocations/<generation_sha256>.json`、
  exact 4 key (`generation_sha256` / `revoked_by` / `revoked_at` / `reason`)、
  ファイル名 = **対象の digest** (record 自身の hash ではない)。R1 (a) はこれと同型。

## 5. 親の provisional 裁定 (攻撃対象)

- **(P1) R1 / R2 / R3 は `required_gates` へ足し、§8.1 の裁定 profile へは足さない。**
  根拠 = `CFAB-S8-S10-CONTRADICTION` と同型 (設計の完了判定に関する裁定であって、束ごとに
  値が変わる項目ではない)。gate ID 案 = `CFAB-R1-REVOCATION-RECORD` /
  `CFAB-R2-STAGE0-COMPLETION` / `CFAB-R3-STAGE6-PREDICATE`、owner = `user`、status = `resolved`。
- **(P2) 失効 record の exact 7 key** (裁定は件数 7 だけを固定し中身を指定していない。
  上位承認 A の 7 key と下位失効の 4 key から導出):
  `schema_version` (逐語 `calibration-freeze-authority-revocation/v1`) /
  `authority_bundle_generation` (exact int ≥ 1) /
  `bundle_digest` (64 lower-hex、file 名の stem と一致) /
  `revoked_active_pointer_raw_sha256` (失効させる X の raw sha256) /
  `revoked_by` (NFC・trim・1〜128 code point) / `revoked_at` (exact int の UTC 秒) /
  `reason` (非空 string)。
- **(P3) S-C の policy 依存部分は gate `CFAB-STAGE6-POLICY-PREDICATE`** を
  owner = `user`、status = `unresolved` で新設する。R2 (b) により段 0 は既に `incomplete`
  なので blocking 増は挙動を変えない。**これが R3 の「後で足す」を台帳上で可視にする唯一の場所**。
- **(P4) 段 6 構造 predicate の中身**: (i) X の top-level exact 5 key と `active/<raw sha256>.json`
  の形状、(ii) `parent_active_pointer_raw_sha256` が genesis のみ `null`・以外は既存 X の raw
  sha256、(iii) `bundle_digest` が A と一致、(iv) `approval_raw_sha256` が A の raw bytes と
  file 名の双方に一致、(v) 承認済み A への参照のみ。陰性は各単一変異が対応理由で落ちること。
- **(P5) fixture / row は増やさない。** 失効 record と段 6 構造 predicate に対応する
  §11.2 の新設拒否 row を足すかは、`CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` (段 1 以降の
  手番) の仕事として送る。段 0 は「schema と語彙の確定」まで。

## 6. 成果物影響 (DW-G05)

- **S-A 未実施:** 設計正本の §12.3 が「親が決めない」と書き続け、裁定済みの R1〜R3 を
  読んだ後続 wave が再び裁定パッケージへ差し戻す (certified 選択の値は変わらないが、
  段 1 以降の実装 wave が起票できず freeze 権威束の proof chain が前進しない)。
- **S-B 未実施:** 失効 record の形が未定のまま段 2〜4 が resolver を書き、
  同一束に矛盾する 2 通りの失効を置ける実装が成立しうる。そのとき resolver の
  「解決不能 → terminal fail-closed」が**どちらの record を読むかで受理集合が変わる**。
- **S-C 未実施:** 段 6 の完了判定が「未定義」のままとなり、§10 冒頭の
  「未定義と書かれた段は完了と宣言できない」により段 6 が永久に閉じない。
  発効 X の受理集合が固定されず、certified 選択の proof chain が上位束を参照できない。

## 7. 並列分割方針

- 段 5 は所有素集合で 2 単位。
  - **U1** = `orchestrator/tests/calibration_freeze_authority_contract.py` +
    `orchestrator/tests/fixtures/calibration_freeze_authority/manifest.v1.json` (S-B/S-C の gate と
    失効 schema 定数、3 つの sha256 pin 更新)。
  - **U2** = `orchestrator/tests/test_calibration_freeze_authority_contract.py`
    (陽性・陰性テスト、段 0 `incomplete` の固定)。
  - 依存: U1 → U2 (U2 は U1 の定数を参照)。よって**逐次**、U1 完了後に所有パス限定 patch を
    展開して U2 を投入する。
- docs (S-A + §7.5 / §10 / §12 の本文) は親が書く。実装子は docs を編集しない。

## 8. B 系並走ガード (runbook §0、Q3 = (a))

1. ノード同居なし — 本 wave の受入は login 実行を既定とし、計算ノード投入は行わない見込み。
   投入する場合は投入直前に `qstat` で再確認し、単独性を計算ノード上で確認する。
2. [T-139] の pilot / 本走 job 走行中はキュー投入を控える (本 brief 時点で
   `dev-wave-t139-manifest-land2-s2` が codex plan 実行中、キューは他 wave の受入 2 本)。
3. 裁定帯域は A (T-139 本走線) 優先 — 本 wave の裁定要求は A の後ろに並べる。
