# [T-338] 段 4 裁定 (親) — 2026-08-17

段 2 プラン 1 本と段 3 敵対レンズ 2 本 (総括はいずれも NO-GO) を裁定する。
親自身の段 1 実測 (M1〜M9) と (P1)〜(P5) も裁定対象に含める。

## 裁定 0 (最上位): 本 wave は実装しない

**実装差分ゼロで終える。** 段 5・6 を飛ばし `4→7→8→9` とする。理由は次の連言である。

1. **投入なしでは真正な受領証が 1 枚も作れない。** D282 pin 済み schema の `attempt` は
   `qsub_result` / `performance_started_marker` / `cluster_slot_or_null` を必須とし、
   `declared_use_class = "dry"` にこれらの免除規定は無い (段 2 が実測、親が schema で確認)。
   qsub を呼ばずに値を合成すれば raw fact ではなくなる。`pilot_submission = forbidden` は維持である。
2. **永続 writer は禁止されている名前を要する。** record-items-v2 §6.10 は「受領証を永続化する
   関数自体」が `PreregBinding` を必須 keyword-only で受けることを要求する。`PreregBinding` は
   D264 が gate 完成まで非 export と定めた 4 名前の 1 つであり、D282 の `preserved` がこれを維持する。
3. **残るのは D264 が名指しで却下した形そのものである。** D264 は
   「台帳だけが『producer 実装済み』へ進む半実装は、直前の wave が blocker と判定した形である」と
   書いている。1 と 2 を引いた残余 (attempt registry + 純粋 assembler + 否定検査) はこの形に一致する。
4. **その残余は D229 決定 (8) の必須 kill を 1 件も達成しない。** 両レンズが独立に確認した
   (A-05 / LB-05)。段 2 プラン自身も 3 件すべてを現 scope では kill 不能と認めており、
   同プランの総括「後二件」は誤記である (親が本文と総括の食い違いを確認)。
5. **`DW-G04` を満たせない。** 発火条件を満たす既存 artifact path も計測 ID も brief に書けない。
   書けなければ設計メモに留める、が同 gate の定めである。

**したがって、本 wave の成果物は設計メモ・敵対レビュー 2 本・段 1 実測・本裁定・裁定パッケージに限る。**
拒否専用 adapter や fixture 限定 leaf を「producer 結線」として land しない (D163 決定 (1) の再適用)。

## 命令文が課した関門への答え

起動命令は「段 1 で D496 との相互作用を実測し、producer が床値表の存在に依存する形になるなら
実装せず設計択一を裁定パッケージで返す」と定めた。

**関門は発火しない。ただし本 wave は別の理由で実装しない。** 実測は次のとおり。

- D282 pin 済み受領証 schema (1326 行) と record-items-v2 の両方で `floor` / `床値` の出現は 0 件。
- schema は `arms` に `stock` / `mode1` / `modeX` を**同一受領証内で必須**とする。RF は床値表の
  引き当てではなく同一 campaign 内の対測定であり、D496 が求める形と一致する。
- D162 決定 (9) が既に「層 3 の calibration floor 閉表へ混載しない」と分離を命じている。

**この結論は「承認済み出力契約 (schema と record-items) に床値表への依存は無い」までに狭める。**
レンズ A-09 とレンズ B LB-09 が親の一般化を反証した。実測で確かめた反証内容は次の 2 点である。

- `orchestrator/qualification/__init__.py:7-18` は `.contract` を import し、
  `contract.py:18` は `orchestrator.calibrator.perf_preflight` を import する。新規 module を
  同 package へ置けば import graph に calibrator 系が入る。これは 床値表そのものではないが、
  「文字列 0 件だから依存なし」という推論は成立しない。
- D496 決定 (1)(3) は「同一 campaign 内の構成集合固定」と「失敗時の全構成再測定」という
  lifecycle 条件を持つ。attempt registry に campaign / 構成集合の identity が無いまま
  失敗 campaign を部分 terminal 化すれば、比較対象集合が変わる。これは裁定 0 の下では
  実装しないため発現しないが、次 wave の設計要件として残る。

## 命令文の前提の訂正 (実測)

起動命令は「既存機構は attempt registry を持つ `orchestrator/campaign/s8b_floor_stats.py` と
`s8b_floor_campaign.py`」と書いた。**両方とも成り立たない。**

- `s8b_floor_stats.py:405-418, 690-693` は自らの保証境界として「raw session 自体の真正性
  (append-only journal・attempt registry・schedule 突合) は保証しない — それは F7 wave の責務」と
  明記する。同ファイルに attempt registry は無い。
- `s8b_floor_campaign.py` のそれは私有クラス `_Runner` (`:4516`) の私有メソッド群 (`:4592` 以降) で、
  `self.records` / `self.schedule` と `IndexedFloorProtocol` (`:604`) に束縛され、export されていない。
- D229 決定 (7) が名指しする再利用先は `orchestrator/qualification/attempt_ledger.py` である。

## 所見の裁定 (real / refuted)

| ID | 判定 | 採否 | 理由 |
|---|---|---|---|
| A-01 | real | 採用 | S2 は producer でない。裁定 0 の根拠 3。 |
| A-02 | real | 採用 | 全単長が caller 選択 snapshot との自己比較。外部固定 tip も producer 外 authority も無い。 |
| A-03 | real | 採用 | `parent_series_id` が registry と受領証で結合されず、片側改ざんで alpha 系列を切れる。 |
| A-04 | real | 採用 | `reason_code` を producer が決められ、anomaly の clean 申告を schema では kill できない。 |
| A-05 | real | 採用 | 必須 kill 3 件が全件不能。段 2 総括の「後二件」は誤記。 |
| A-06 | real | 採用 | `dry` は隔離札にならない。`declared_use_class` は受理入力にしてはならない。 |
| A-07 | real | 参考 | 基底 fixture の合格確認・拒否 keyword・件数を固定しない test 計画は偽緑を許す。実装しないため本 wave では発現しない。次 wave の要件へ繰り越す。 |
| A-08 | real | 採用 | probe の依存順が循環 (probe は S1 snapshot を要求するが順序は probe→S1)。かつ既知欠落で常に赤。 |
| A-09 | real | 採用 | 親 M4 の過剰一般化。上記のとおり結論を狭めた。 |
| LB-01 | real | 採用 | A-01 と同一。独立に到達。 |
| LB-02 | real | 採用 | registry に `study_id` / `study_stage` / campaign 境界が無く pilot と main を分離できない。 |
| LB-03 | real | 採用 | 外部 binding 無しで pin・fileRecord・qsub fact を受け取れば偽 receipt を作れる。 |
| LB-04 | real | 採用 | 永続 append/read と外部固定 tip が無く、末尾削除が replay を通る。 |
| LB-05 | real | 採用 | A-05 と同一。独立に到達。 |
| LB-06 | real | 採用 | 再利用候補の調査不足 (`s8b_holdout_admission.py` の O_EXCL ledger、`qualification/series.py`)。親 P1 は未確定へ差し戻す。 |
| LB-07 | real | 採用 | `BlobRef` は path・commit・sha256 であり、`load_approval_payload` は固定 commit の blob から読む (親が確認)。段 2 の「path・size・sha256」は誤り。 |
| LB-08 | real | 採用 | A-08 と同一。独立に到達。 |
| LB-09 | real | 採用 | D496 lifecycle 条件。上記で M4 を狭めた。 |
| LB-10 | real | 採用 | producer→pilot の handoff artifact が作られず依存辺が切れる。 |

**refuted は 0 件である。** 親は 20 所見すべてを real と裁定した。

## 親自身の (P1)〜(P5) の裁定

- **(P1) 差し戻し (未確定)。** `s8b_floor_*` を外す判断は M1/M2 により維持する。しかし
  「土台は `orchestrator/qualification/`」は LB-06 の指摘どおり調査不足であり、確定させない。
  再利用候補の棚卸し (`attempt_ledger.py` / `series.py` / `s8b_holdout_admission.py` の
  O_EXCL ledger / T-810 coordinator) は次 wave の段 1 要件とする。
- **(P2) 反証。** `dry` は qsub fact を免除せず、隔離札にもならない。段 2 と両レンズが独立に反証した。
- **(P3) 反証。** probe は依存循環と既知欠落により有効な生死実験にならない。裁定 0 により不要。
- **(P4) 反証。** 3 変異を必須 kill として登録できない。実装差分ゼロのため変異 matrix は免除される
  (`DW-S04`)。**「kill 済み」と記録してはならない。**
- **(P5) 維持。** 受入は本 worktree で行う。計算ノード投入は無い。

## 訂正する親の実測

- **M4** — 結論を「承認済み出力契約に床値表への依存は無い」へ狭めた (上記)。
- **M6** — 固定三つ組は **7 件** (`approved_blobs` 6 role + `target_core`、
  `test_t139_approval_payload.py:120` の `assert len(refs) == 7` で確認)。brief の「6 blob」は誤り。
  pin の権威経路は test ではなく `approval_payload.py:166-171` の `load_approval_payload` と
  `blobref.read_pinned_blob` である。
- **M2** — 「再利用不能」は直接再利用の範囲では正しいが、原子公開などの primitive まで否定する
  読み方は過剰である (レンズ A)。

## 変異事前登録

**免除。** `DW-S04` に従い、「実装しない」と裁定済みで実装差分ゼロの wave は変異 matrix を免除する。
受入全走は免除しない。
