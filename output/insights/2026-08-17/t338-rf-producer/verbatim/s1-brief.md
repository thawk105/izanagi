# [T-338] 段 1 brief — RF producer と attempt registry

正本: D481 / D282 / D229 / D162 / `output/insights/2026-08-17_t338-rf-trigger-realign/` /
archive worklog (626) の [T-338]。本 wave は **producer までに限る**。

## 段 1 実測 (親が一次資料から独立に測った。M1〜M9)

- **M1 (命令文の前提が崩れた その 1):** `orchestrator/campaign/s8b_floor_stats.py` は attempt
  registry を**持たない**。同ファイルは自分の保証境界として「raw session 自体の真正性
  (append-only journal・attempt registry・schedule 突合) は保証しない — それは F7 wave の責務」と
  明記する (`s8b_floor_stats.py:405-418`, `:690-693`)。
- **M2 (同 その 2):** `s8b_floor_campaign.py` 側の attempt registry は私有クラス `_Runner`
  (`:4516`) の私有メソッド群 (`:4592` 以降) であり、`self.records` / `self.schedule` と
  `IndexedFloorProtocol` (`:604`) の cell/round/retry 予算に構造的に束縛される。export されておらず
  再利用可能な部品ではない。
- **M3:** D229 決定 (7) が名指しする再利用先は `orchestrator/qualification/attempt_ledger.py`
  (473 行、create-only・series-global・hash 連鎖 `previous_event_sha256` / `event_sha256`)。
  こちらは公開 API を持つ独立モジュールである。
- **M4 (D496 関門の答え = 依存しない):** D282 pin 済み受領証 schema (1326 行) と record-items v2 の
  両方で `floor` / `床値` の出現は **0 件**。schema は `arms` に `stock` / `mode1` / `modeX` の
  3 arm を**同一受領証内で必須**にする。RF は床値表の引き当てではなく同一 campaign 内の対測定であり、
  D229 決定 (2)(3) の受理 (同じ標本共分散・同じ臨界値からの同時信頼領域) は arm の同時測定を
  構造的に要求する。D162 決定 (9) も「層 3 の calibration floor 閉表へ混載しない」と既に分離を命じる。
  したがって **D496 とは衝突せず一致する**。関門は発火しない。
- **M5:** 種別 field は候補名ではなく確定済み — `declared_use_class`、enum
  `{official, exploration, qualification, dry}` が D282 pin 済み schema の root 必須 field
  (`receipt-schema-v1.json:1225,1248`)。D162 決定 (11) の閂は [T-479] 択 (b) (archive (199)) で解除済み。
  D75 二義化なし (`artifact_role` / `artifact_class` とは別名、Python 側の出現 0 件)。
- **M6 (pin 実測):** `sha256(receipt-schema-v1.json)` =
  `d541ccd5919c7c3545c04a806ca7f9cf04e6391cdf1791d7b9273317199b047e`、
  `sha256(record-items-v2.md)` = `61ba2f8b009ab6a17d657a5e3af3ce8a3afb251e3da664fc0117cd46a048a480`。
  いずれも D282 payload と exact 一致。**pin 閉包 (DW-O09):** path 検索の hit は
  `orchestrator/tests/test_t139_approval_payload.py` 1 件、digest 検索も同 test のみ (他は docs)。
  → 両 blob は 1 byte も変えない。
- **M7 (実装被覆 = 0):** `declared_use_class` を出力する Python は repo 内に **0 件**、
  `t139-receipt` を書く producer も **0 件**。既存の `orchestrator/preregistration/` (3106 行) は
  承認 payload 解決・blob 読取・erratum 適用までで、受領証を**書かない**。
- **M8 (engine):** `jsonschema` 3.2.0 (draft-07)。D282 が dialect を draft-07 に選んだ理由と一致し、
  pin 済み schema をその場で検査できる。
- **M9 (緊張点):** schema の `attempt` は `qsub_result` / `performance_started_marker` /
  `cluster_slot_or_null` (1..13 または null) を必須にする。attempt は本質的に PBS 投入に紐づく。
  `pilot_submission = forbidden` の下で end-to-end の実受領証をどう得るかは (P2) の争点。

## 不変条件 (破ったら停止)

1. `pilot_submission = forbidden` / `main_submission = forbidden` / D292 の解除権威を維持する。
   本 wave は投入 gate を実装せず、投入権限を付与しない。解除条件の中身も定めない (D481 決定 (5)(6))。
2. D282 pin 済み 6 blob (target_core / addendum_a / derivation_map / erratum ×2 / record_items /
   receipt_schema) を 1 byte も変えない。schema は**適合対象**であって編集対象ではない。
3. `orchestrator/qualification/contract.py` の Pegasus 環境契約 (`env_tag` / `attestation_mode`) は
   D481 決定 (3) により対象外。1 byte も変えない。
4. producer は適格性を宣言しない。適格性 field・pairing 成否・受理状態・validator identity /
   結果は closed schema で reject する (D162 決定 (1)(2))。`declared_use_class` は利用意図であり
   合格宣言ではない。
5. 受理集合を広げない。certified 選択・材料レポート・proof chain・凍結 bytes・既存 gate は不変。
6. `s8b_floor_*` を編集面に入れない (M2/M4 より不要であり、D496 が外す装置への結線を避ける)。

## scope と成果物 (DW-G05: 実装しない場合の成果物影響を各項に付す)

- **S1 RF attempt registry** — series-global・create-only・追記専用の試行台帳。全 attempt の双射、
  親系列 ID、`replaces_attempt_id` / `parent_attempt_id` の連鎖を保持する。
  *不実装なら:* validator が「失敗した投入を台帳と raw の双方から落とす」変異を検出できず、
  D229 決定 (8) の必須 kill 3 変異のうち 1 本が恒久に不発 → RF 判定の受理集合が実質拡大する。
- **S2 受領証 producer** — D282 pin 済み `t139-receipt/v1` に適合する raw 受領証を書く。
  3 arm (`stock`/`mode1`/`modeX`) を 1 受領証に収める。
  *不実装なら:* D481 が名指しした「raw receipt を出す producer が 0 件」の状態が続き、
  validator は合成 fixture しか読めず、D162 発火条件 (ii)(iii) は永久に成立しない。
- **S3 否定検査 (closed schema rejection)** — 適格性 field 混入・未知 field・自己申告合否を拒否。
  *不実装なら:* 恒真 gate になり、producer 自己申告が適格性へ昇格する経路が開く (規律 2 違反)。
- **scope 外 (実装しない):** validator / consumer、投入 gate、PBS driver 本体、approval manifest
  resolver、本走。順序 `producer → pilot → validator/consumer → 本走` (D229 決定 (6)) を保存する。

## 親の provisional 裁定 (攻撃対象。段 3 で潰してよい)

- **(P1) 土台は `orchestrator/qualification/` を取り、`s8b_floor_*` は取らない。** 根拠は M1〜M4。
  命令文が名指しした機構は M1 で不在、M2 で再利用不能、かつ D496 が外す装置に属する。
  D229 決定 (7) は「再利用するか複製するかは producer 実装段の設計択一」と本 wave へ委ねている。
  *攻撃面:* T-126 の台帳は二者 protocol 用であり 3 arm・RF の要求を取りこぼす可能性 (D162 決定 (8)
  が禁じたのは artifact の読み替えでありコード再利用ではない、が構造不一致は別問題)。
- **(P2) end-to-end の実受領証は `declared_use_class = "dry"` で得る。** schema の
  `study_stage` enum は `{pilot, main_run}` のみだが `declared_use_class` に `dry` があり、
  `cluster_slot_or_null` は null を許す。fixture 限定 leaf は D147 決定 (3) / D163 決定 (1) /
  D229 決定 (6) が却下した型なので採らない。
  *攻撃面:* `dry` 受領証が投入禁止の迂回に読まれないか。M9 の PBS 束縛 field を null で埋めた
  受領証が「実受領証」と呼べるか。呼べないなら本 wave は S2 を組み立て関数までに縮める。
- **(P3) DW-G01 の生死確認を段 5 の最初の成果物にする。** 「pin 済み draft-07 schema に適合する
  受領証を、cluster 投入なしで得られる事実だけで 1 通作れるか」を 100 行以内の使い捨て driver で
  先に確かめ、赤なら本実装へ進まず段 4 へ差し戻す。probe も実装面なので親は書かず Codex author が書く。
- **(P4) 変異事前登録は D229 決定 (8) の 3 変異を必須 kill に含める** — 失敗投入の台帳/raw 双方からの
  除去、親系列 ID の自己申告による累積有意水準リセット、anomaly の clean 申告。
- **(P5) 受入・実測環境は Pegasus login ノード内の本 worktree。** 計算ノード投入は行わない
  (producer 段に実測走行は無い)。受入は `python3 tools/run_tests.py` を相対・素の名前ちょうどで。

## 並列分割

段 5 は S1 (attempt registry) と S2+S3 (受領証 producer + 否定検査) の 2 所有へ分ける。
両者の接点は受領証 root の `attempts` 配列 1 箇所のみで、schema がその形を pin しているため
所有境界が競合しない。段 6 レビューは (a) 正しさ防壁と規律 2、(b) schema 適合と D282 pin 整合の 2 レンズ。

## 変更面 (実アンカー)

| path | 種別 | 備考 |
|---|---|---|
| `orchestrator/qualification/attempt_ledger.py` | 参照 (再利用元) | 編集可否は (P1) の裁定次第 |
| `orchestrator/preregistration/approval_payload.py` | 参照 | 承認 payload 解決の既存経路 |
| `output/insights/2026-08-11_t139-manifest-land1/receipt-schema-v1.json` | 不変 (pin) | 適合対象 |
| `output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md` | 不変 (pin) | 記録項目の正本 |
| `orchestrator/tests/test_t139_approval_payload.py` | 不変 | pin 閉包の唯一の Python |
| `orchestrator/campaign/s8b_floor_*.py` | 非接触 | (P1)・不変条件 6 |
| 新規 (段 4 で確定) | 追加 | RF producer 本体と test |
