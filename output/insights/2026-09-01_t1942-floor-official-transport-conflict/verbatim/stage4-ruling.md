# [T-1942] 段 4 裁定 (親、2026-09-01 19:10 JST)

基準: wave base `08a17b3b3`。裁定 inbox は wave 開始後の更新なし。
local main は wave 開始後 `834efe61f` へ進んだ (land 時に `DW-O23` で扱う)。

## 中心の裁定 — この wave では実装しない

**official 床値 campaign は投入できない。D926 を実装しても投入できない。**
段 2 プラン・段 3 レンズ A #4・レンズ B #4・親の独立実測がすべて同じ構造的矛盾を指している。

- `tools/pegasus/floor_campaign.sh:1231` は `--fetchcontent-base-dir` を**無条件で**渡す。
- `fetchcontent_base_dir` は 18 名の refreeze 不適格 seam の一員
  (`orchestrator/campaign/s8b_floor_contract.py:42-50`)。
- official mode は非既定 seam があれば**承認 gate の手前で**拒否する
  (`orchestrator/campaign/s8b_floor_campaign.py:6990-6994`)。
- `_derive_refreeze_eligibility` は「official かつ resume なし かつ非既定 seam ゼロ」だけを
  適格にする (`同:6906-6919`)。
- 由来: `1488fe683` ([T-1461]、2026-08-22) が**同じ commit で** staged transport を job script へ
  無条件配線し、`fetchcontent_base_dir` を不適格 seam へ登録した。commit message は offline build の
  生死実験に触れているが、official が起動不能・refreeze 不適格になることには触れていない。

解消には次のいずれかが要るが、いずれもこの wave の権限を超える。

- 18 名集合か判定式を変える → **D926 が明示的に禁止**し、正しさ防壁を緩める (規律 2)。採らない。
- staged transport を argv から外す → 既定経路は FetchContent が外部取得を試みる形になり
  (`s8b_floor_campaign.py:3202-3247`)、`docs/pegasus-runbook.md:811-825` の
  「依存ソースはログインノードで pinned staging し `FETCHCONTENT_SOURCE_DIR_*` で渡す運用を維持する」
  に反する。計算ノードは直結 network 不可である。
- staged transport を driver 内部の production 既定にする → 18 名集合も判定式も literal には
  変えずに解ける可能性があるが、**D926 が名指しした面の外**である。裁定パッケージへ回す。

`DW-G04` は「条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を brief に書ける場合だけ
実装する。書けなければ設計メモに留める」と定める。official の発火経路を書けない以上、
**D926 の実装は行わない。** 段 5・6 を飛ばし `4→7→8→9` とする。

ユーザー指示「通らなければ実測結果を記録して停止し、無理に迂回しない」に従う。

## 所見の裁定

### real・採用 (記録する)

- **レンズ A #4 / レンズ B #4 / 親 G-D — transport の構造的矛盾。** 上記の中心裁定。
- **レンズ B #1 — G-B の verdict は「ある時点で identity 衝突なし」までに狭める。** 採用。
  fresh reservation は resume marker 全件検査と 12 claim の逐次 `O_EXCL` 作成、その後の
  ledger 全体検証を行う (`s8b_holdout_admission.py:1612, 1636, 1742`)。read-only probe は
  claim 成功を保証しない。
- **レンズ B #2 — 既存 `measurement-generation-consumed` 192 件の双方向整合検査が要る。** 採用。
  `consume_attempt_ticket()` は対象 path だけでなく現行 generation の consumed 全体を走査する
  (`同:4827, 4847, 4877`)。
- **レンズ B #3 — attempt registry を G-B の予算根拠に使わない。** 採用。親の
  「実 pilot の登録簿がないので枠は 0 から始まる」は根拠として誤り。registry は scheduler
  recovery の retry 時だけ読まれ (`同:4960, 5173`)、budget 10 もその replay 内でだけ検査される
  (`同:5195`)。さらに現物 fixture の path は `<freeze>/<protocol>/registry.jsonl` だが、
  現行 consumer の canonical path は `<freeze>/registry.jsonl` である
  (`s8b_attempt_profile.py:378`)。**親の推論を撤回する。**
- **レンズ B #5 — one-cell の緑を 12-cell readiness と呼ばない。** 採用。
- **レンズ B #7 — D926 の投入 confirmation と D1161 の走行後 budget approval を呼び分ける。** 採用。
  AI に許されるのは `s8b_budget_approval_preflight.py:157` の `draft-not-an-approval` skeleton と
  read-only 検証までで、canonical candidate と pin の確定はユーザー手番である。
- **レンズ B 親所見 #1 — 件数の訂正。** 採用。旧 manifest 588 件は「すべて絶対 path」ではなく
  **549 件が絶対 path、39 件が snapshot 相対**である。結論 (旧再走では現行 v3 経路の生死を測れない)
  は変わらない。
- **レンズ A #1・#2・#3 — 承認 gate の実装上の欠陥 3 件。** real と裁定する。ただし実装しないので
  この wave では適用しない。D926 を実装する将来の wave のために記録する。
  (#1 既定 `False` の control 引数は pilot の受理集合を文字どおり広げる。
   #2 「env が設定済みなら検査」は fail-open で D926 の早期拒否契約を満たさない。
   #3 負例は「gate を外すと赤でなくなる」ことを sentinel で示す必要がある。)

### 親の provisional 裁定の帰結

- **(P1-a) 維持。** 段 2・レンズ B が独立に支持した。
- **(P1-b) 維持 (静的読解として)。** 未実測である点も維持。
- **(P1-c) 撤回。** 旧 `claims` 36 件・`consumed` 228 件は fresh reservation の衝突述語から
  除外されている (`s8b_holdout_admission.py:1618-1620`)。判定対象は
  `measurement-generation-claims` (現在 24 件) と `measurement-generation-consumed` (192 件)。
- **(P1-d) 帰結として無効。** scope を D926 の名指し面に限ると official は到達できない。
- **(P1-e) 維持。** ただし実装しないので発効しない。

### 覆った前提の再裁定 — T-1942 の記述は現状と逆である

T-1942 は「判定床 0.030 は旧環境の write-heavy / balanced 由来で read-heavy を含まない」と書く。
`between_run_noise` の成果物を全件数えると 4 件しかなく、内訳は次のとおりである。

| 環境 | rr5 (write-heavy) | rr50 (balanced) | rr95 (read-heavy) |
|---|---|---|---|
| linux-baremetal (旧) | あり | あり | あり |
| pegasus (現行) | **なし** | **なし** | あり |

- 旧環境については誤り。read-heavy も測ってある。
- **現行 Pegasus で欠けているのは write-heavy と balanced のほうである。**
- 現行 Pegasus の rr95 実測値は within 0.996% / between 0.223% で、いずれも 0.030 を大きく下回る
  (`output/env/pegasus/calibration/between_run_noise_t48_skew0p9_rr95_rmw0.json`)。
- ただしレンズ B #6 のとおり、これらは cold-boot・温度ドリフトを含まない**下限**であり、
  genuine な cross-campaign / between-block floor は未較正である。成果物に
  「read-heavy は較正済み」と無限定に書いてはならない。

## 変異事前登録

実装面の差分がゼロなので `DW-S04` に従い変異 matrix を免除する。受入全走は免除しない。

## この wave の成果物

- ゲート 4 本 (G-A / G-B / G-C / G-D) の実測記録を insight として残す。
- worklog / decisions / failures の fragment を `docs/spool/` 形式で書く。
- **投入しない。実装しない。**

## 裁定パッケージ (ユーザーへ返す)

1. **staged transport と official 適格性の矛盾をどう解くか。**
   - (A) staged transport を driver 内部の production 既定にする。18 名集合と判定式は literal に
     変えずに済む可能性がある。payload の所在を caller seam でなく driver 側で導出する設計が要る。
     **親の推奨は (A)。** ただし「発見による暗黙の入力経路」を作らない形にできるかが設計論点である。
   - (B) 既定 (legacy) 経路が計算ノードの offline 条件で通るかを実測し、通れば argv から外す。
     runbook の運用方針に反し、`docs/pegasus-runbook.md:811-825` は proxy を FetchContent が
     honor するかは未確定と明記している。
   - (C) 18 名集合か `_derive_refreeze_eligibility` を変える。**D926 が禁止。規律 2 に反する。**
2. **T-1942 の本文が指す量を確定してほしい。** 「workload 別 between-block 床値」は
   (i) A-4 = s8b 床値 campaign の official 実測 (上記 1 で塞がっている)、
   (ii) `orchestrator/campaign/between_run_floor.py` が測る between-run noise floor
   (現行 Pegasus で rr5 / rr50 が欠けている) のどちらか、あるいは両方でありうる。
   (ii) は既存 driver で今すぐ測れて、1 のどの選択肢にも依存しない。
3. **テストが共有耐久領域へ書いている。** `floor-attempt-registries/` に holdout key `rr23` / `rr79`、
   `execution_uuid` = `campaign-fixture-execution` の登録簿が実在する。scope 外として記録のみ。
