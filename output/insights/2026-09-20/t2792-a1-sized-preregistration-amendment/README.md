# A-1 balanced5 sized 本走 — 認可済み独立再現 (attempt-0002) の追補 (§6.1 / §6.4 の別版)

- authority: preregistration-amendment
- default_effect: no-state-change
- study_id: paper-story-a1-20260901-balanced5-sized-v1
- 適用: **将来の attempt-0002 一件** (D2172 項 2 が 1 attempt 限定で認可した独立再現) に限る。attempt-0001 と、それ以前・それ以外の
  attempt には適用しない。attempt-0003 以降を認可する文書ではない。
- 根拠: D2172 項 2 (2026-09-20、第 24 回 /rulings 項 2、ユーザー裁定「推奨通りで」)、D2156 項 3 (「同 study の次の投入には改めて認可が要る」の
  機械化)、D2120 項 3、一次資料 `output/insights/2026-09-19/a1-sized-attempt2/README.md` §7 (裁定パッケージ、択 1)。
- この文書は attempt-0002 の投入前に固定する。試行結果を見て値・規則を変更しない。
- **本文書は erratum (誤記訂正) ではない。** 元の事前登録 §6.1 / §6.4 に誤りは無く、本文書は D2172 項 2 に基づいて**将来の観測にのみ適用する
  規則の追加 (別版)** である。erratum の名で正当化しない。
- **本文書は投入そのものではない。** 投入は land 後の fresh submit-tree による別 wave が行い、その可否は本文書でなく認可 record と gate が決める。

## 保存する登録 (変えないもの)

元の登録は
`output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md`
(SHA-256: `6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2`)、
`orchestrator/campaign/paper_story_a1_paired.v3-sized.json`
(SHA-256: `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a`)、
source 契約 `orchestrator/campaign/paper_story_a1_source.v2.json`
(SHA-256: `b50a4edf86250033aa0e2b18efa2d7842d7c90025fdb901011fdad7adf052fe1`)、
source 追補 `output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md`
(SHA-256: `6093de244e6fc90607094608617032f427db4951ebffc847c7bcaa795309789b`) である。
**4 file の bytes をすべて保存する。** study、3 workload、各 arm、規模、30 対、5-rep 配置、root seed (3 workload とも §2.1 の値のまま)、
静定、競合検査、CV、無効の規則、`formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` は変更しない。

- **attempt-0001 の判定・公開 leaf・稿・図・限定 L-A1S-4 は遡及変更しない。** attempt-0001 の公開 leaf
  `output/insights/2026-09-13/paper-story-a1-balanced5-sized/` (README.md / receipt.json / result.json / .complete.json の 4 file) の bytes と内容集合は保存し、
  そこへ何も書き足さない。
- **本追補だけを根拠に L-A1S-4 (反復間の安定性へ一般化しない) を解除しない。** 解除の可否は attempt-0002 の測定が存在してから、
  別の results 稿と裁定で扱う。
- §6.4 の**本文は変更しない**。再走理由の閉じた列挙 (`build-failure-before-bench` / `verify-failure-before-bench` /
  `competing-tenant-detected-before-bench` / `scheduler-or-infrastructure-failure-before-bench`) と「性能の出力は再走を正当化しない」は不変。
- verifier の anomaly は従来どおり即 reject。trace-enabled 検証と trace-disabled 性能測定の分離、intent / attempt root / 受領証 namespace の
  再使用拒否、先行証拠の完全性検査、公開先の create-only は不変。

## §6.4 の追補 — 将来の attempt-0002 一件に対する例外の追加 (認可 record を持つ独立の観測 attempt)

元の §6.4 は「再走してよい理由は bench が始まる前の失敗の閉じた列挙だけ」と定める。driver の rear gate
`_assert_no_prior_v3_bench_start` はこれを機械化し、同じ study の先行 attempt が bench barrier に到達した証拠
(`barrier/bench-go.json`・`barrier/ready/` 三揃い・`barrier/bench-start/`) を持てば、同 study の group 再投入を理由を問わず拒否する
(commit `abff80d1b`、2026-09-03)。attempt-0001 は 2026-09-18 に bench に到達したので、attempt-0002 は現行 gate では投入できない
(2026-09-19 に実走で確認、D2156)。

本追補は D2172 項 2 に基づき、次のとおり**例外を 1 件だけ追加する**。

1. **認可の対象:** study `paper-story-a1-20260901-balanced5-sized-v1` の attempt 名 `attempt-0002` を、先行 attempt `attempt-0001` が
   bench に到達した状態で投入すること (同じ policy・同じ seed・同じ物理順の**同一配置の反復**、研究目的 = 反復間の安定性の観察)。
2. **認可の形:** durable base (`policy.execution.durable_measurement_base` = attempt-0001 と同じ base) の直下に、認可 record
   `attempt-0002.authorization.json` を置く。record は次の key を **exact** に持つ (余分・欠落は拒否):
   `schema_version` (`paper-story-a1-paired-rerun-authorization/v1`)、`study_id`、`attempt_root` (base 直下の `attempt-0002` の絶対 path)、
   `source_commit` (fresh submit-tree の HEAD = `submit` / `materialize` の `--expected-head`)、`decision` (`{"id": "D2172", "item": 2,
   "decided_on": "2026-09-20"}`)、`authorization_sha256` (`authorization_sha256` 自身を除いた record の canonical JSON の SHA-256、
   破損検出用)。record は driver の subcommand `authorize-rerun` が create-only で書く。**解除対象の先行 attempt 名 (`attempt-0001`) は
   record に持たせず、driver 側の定数だけが持つ。**
3. **gate の挙動:** driver は認可の exact 集合を定数 1 件 `V3_SIZED_RERUN_AUTHORIZATIONS` = (study_id, attempt 名 `attempt-0002`,
   先行 attempt 名 `attempt-0001`, 裁定 `D2172`, 項 2, 裁定日 `2026-09-20`) として持つ。rear gate は、record の study_id・attempt 名
   (`attempt_root` の末尾と file 名) ・裁定 3 field がこの定数と一致し、かつ record の `source_commit` が投入時の HEAD と一致するときに限り、
   **同じ base の先行 attempt-0001 に対する**「bench 到達後の group 再投入禁止」だけを解除する。同 study の先行 attempt が bench に到達した
   状態での投入は、次の場合すべて従来どおり拒否する — 別 attempt 名、別 study、別 source sha、record 不在、record の破損・symlink・
   余分 key、裁定 field の不一致、attempt-0001 以外の同 study の先行 attempt (例: attempt-0003) が bench に到達している場合。
   変わらないもの: 別 study の正常な先行証拠は現行どおり拒否理由にならず、同 study の先行 bench 到達が無い初回投入は record が無くても
   現行どおり通る。先行証拠の完全性検査 (corrupt / unsafe の拒否) と study 不一致の拒否は、認可の成功を理由に省略しない
   (不正な record 自体は、走査より前に reader が拒否する)。
4. **これは「再走」ではない。** attempt-0002 は attempt-0001 の失敗後の再走ではなく、認可された独立の観測 attempt である。§6.4 の再走理由の
   列挙は変わらない。attempt-0002 自身が bench 開始後に失敗した場合、または attempt-0002 の性能値を理由に attempt-0003 を投入することは、
   本追補では認可しない (改めて裁定と、定数の追加と、新しい record が要る)。
5. **どこかの層で落ちたら再投入せず報告して止める** (2026-09-19 のユーザー裁定の付帯条件を継承)。

## §6.1 の追補 — 認可済み attempt の公開先

元の §6.1 は「成果物の公開先は `output/insights/2026-09-13/paper-story-a1-balanced5-sized` とし、公開は終端の生の束を一度しか作れない宛先へ
書き出す」と定める。この宛先は attempt-0001 が既に使ったので、attempt-0002 の公開は次のとおりにする。

- 認可 record を持つ attempt の公開先は、policy の `materialization_relative_path` に `-<attempt 名>` を付けた**兄弟 directory**
  `output/insights/2026-09-13/paper-story-a1-balanced5-sized-attempt-0002` とする。attempt-0001 の leaf 配下には置かない
  (「pilot の公開先には何も書き足さない」と同型で、attempt-0001 の公開先にも何も書き足さない)。
- この宛先も**一度しか作れない** (create-only、既存なら拒否)。公開先 gate `_exact_materialization_destination` は、同じ認可 record が
  `materialize` の `--expected-head` と一致するときだけこの兄弟 directory を受理し、record が無い attempt は従来の exact leaf のみ
  (既存なので拒否される)、record が一致しない attempt は拒否する。
- 公開される束の中身 (README.md / receipt.json / result.json / `.complete.json`) の形式・raw との対応・source binding・WAL 再検証・非認証 observation の
  consumer は不変。

## 機械可読の束縛

本追補は policy・source 契約 JSON に SHA-256 を足さない (凍結 bytes に触れない)。束縛は **source commit 経由**で行う — 認可 record の
`source_commit` は本追補と gate の実装を含む確定 commit (land 後の local main) から作った fresh submit-tree の HEAD であり、
`submit` と `materialize` はこの HEAD との一致を検査する。**本追補 file 自身を実行時に digest 検査する仕組みは無い**
(source contract v2 が source 追補を束縛するのとは異なる)。record の作成は「全成果物の land → fresh submit-tree の確定 → record → submit」の
順で行う。

## 限界 (言わないこと)

- 認可 record と self digest は破損検出であって電子署名ではない。**認可者が attempt-0001 の性能値を見た後に再現を選んだかどうかを、
  record は識別しない** (D2172 項 2: 「認可 record は『認可者が性能値を見た後の選択』を防ぐ装置とは称さない」)。
- 本追補の成立を測定の完了と表現しない。attempt-0002 の測定値は本追補の時点で存在しない。
- attempt-0002 の結果 (results 稿・2 attempt の並記・図) の形式は別途定める。プールしない (D1993 項 6)。
- 非認証 lane のまま。formal 昇格・要件充足判定・certified 化を含まない。
