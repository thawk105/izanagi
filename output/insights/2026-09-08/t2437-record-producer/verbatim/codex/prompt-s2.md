単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer

必読事項の射影: 次の 5 ファイルを読め。**どれか 1 つでも読めなければ即停止し、その旨だけを出力せよ。**

- 親 brief (段 1。本 wave の scope・新事実 N1〜N5・不変条件・(P1)〜(P4) の正本):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/brief-s1.md`
- 先行決定 D1768 の逐語 (consumer 側の rejected 枝を production 形へ合わせた裁定。本 wave の producer が従う規則の出所):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/verbatim-d1768.md`
- 先行決定 D1715 の逐語 (T-2385 を起票した裁定):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/verbatim-d1715.md`
- 設計正本 `docs/phase3-8c-wiring-design.md` §3 の逐語 (record schema・issuer の位置・§3.4 outcome 対応表・§3.5 member 写像):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/verbatim-design-s3.md`
- 一次資料 (前 wave の insight 全文。§2 が「producer を書くか consumer を合わせるか」の判断、§11 が残る限界):
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2385-t2437-record-producer/verbatim-insight-rejected-witness.md`

# 段 2 — 実装プラン起草 (read-only)

あなたは izanagi の dev-wave 段 2 プラン起草者である。result-evidence record (`result-evidence/v1`) の
production producer を `orchestrator/campaign/reflux_result_evidence.py` へ新設する変更の、file:line 粒度の
実装プランを起草せよ。**実装はするな。ファイルを 1 byte も編集するな。commit するな。**

## repo

cwd は worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2385-t2437-record-producer` (local main 34af5a571 と同一) である。
repo 内のファイルは読んでよい。巨大ファイルは網羅読みせず `grep -n` で位置を特定してから `sed -n 'A,Bp'` で該当範囲だけ読め。まず次を読め。

- `orchestrator/campaign/reflux_result_evidence.py` 全体 (約 870 行。record schema 78-136、`validate_result_evidence` 236-330、`write_result_evidence_record` 444-456、`_canonical_wal_interval` / `_resolve_ordered_wal` 618-690、member 写像 769-870)
- `orchestrator/campaign/reflux_formal_consumer.py` の 110-180 (定数)、1148-1262 (`_wal_field`、`_valid_witness_anomaly`、`_witness_class_sha256`)、1264-1396 (`_validate_wal_outcomes` — consumer が rejected 枝で要求する全条件)
- `orchestrator/campaign/pipeline.py` の 1249-1262 (`_abort` — production の abort payload の形) と 1590-1606 (verifier reject 経路。`result_to_dict(vr)` から `trace_dir` を除いて `verify` へ載せる)
- `orchestrator/verifier/report.py` の 96-140 (`result_to_dict`) と `orchestrator/verifier/model.py` の `VerifyResult` / `Integrity` の定義 (grep で位置を出せ)
- `orchestrator/campaign/wal.py` の `emit` と `parse_line` (production の `wal.jsonl` の 1 行の形。`layout.py:207` `wal_file`)
- `orchestrator/campaign/p3_autonomous_workload_trial.py` の 425-490 (`OriginRunPlanInput` / `OriginProducerInputs`) と 1860-1900 (producer 出力が consumer へ渡る箇所)
- `orchestrator/tests/reflux_origin_fixture_builder.py` の 396-560 (fixture の WAL records・projection・record の作り。**bytes 不変が不変条件**)
- `orchestrator/tests/test_reflux_result_evidence.py` 全体 (golden 4 個と既存 21 test)
- `orchestrator/tests/test_reflux_formal_consumer.py` の `test_real_dense_cycle4_anomaly_passes_witness_structure_validator` と `test_real_dense_cycle4_report_schema_matches_consumer_key_sets` (実 verifier を走らせる作法の先例)
- `orchestrator/tests/test_verifier.py` の 33-66 (synthetic Silo source の束縛。これ無しでは全 fixture が indeterminate になる — 親が実測済み)

## 環境の制約 (read-only sandbox)

書込可能な tmp が無いので **pytest の緑を要求しない。静的検査でよい。** テストの実測は親が行う。走らせていないものを緑と書くな。
予算が尽きそうなら、途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 起草せよ

1. **方向の確認。** 親 brief §0 の N1 (WAL 側の「producer か consumer か」は D1768 で consumer 側に裁定済み) を file:line で裏取りせよ。record 層で「consumer を合わせる」余地が残っているか (FC09 / ledger の `constraint_sha256` 等式を緩めずに) を検査し、無ければ「record 層 producer を書く」を支持する根拠を 3 行以内で書け。反証があれば名指しせよ。
2. **編集面のアンカー表。** 追加・変更する file と関数を現行の行番号付きで列挙せよ。追加・変更・削除の別と、各変更が何行程度かを書け。**consumer (`reflux_formal_consumer.py`) の判定式・reason code・受理集合は変えない。** 変えるとすれば (P1) の import 差し替えだけである。
3. **S1 の導出関数の署名と 3 方向の分岐。** 入力 (`VerifyResult` か `verify` dict か — (P2))、出力 (`outcome`、`constraint_sha256`、発行拒否の型)、各分岐の条件を consumer の `_validate_wal_outcomes` 1264-1396 の要求と 1 対 1 に対応づけて書け。**producer が consumer より緩い形を発行しうる隙間** (例: `total_cycles == anomaly_count == 1` を見ずに class を出す、dirty integrity で class を出す、複数 class から 1 件を選ぶ) を列挙し、各々をどの条件で塞ぐかを示せ。設計 §3.4 の表の行と対応づけよ。
4. **(P1)〜(P4) の裁定案。** それぞれ支持または反証し、file:line で代案を示せ。(P1) の「式を 1 箇所へ寄せる」は consumer の bytes が変わる — 受理集合が不変であることをどう示すかも書け。(P3) の S3 (ordered WAL projection の producer) は `_canonical_wal_interval` 618-645 の逆関数として書けるか、production `wal.jsonl` の 1 build_attempt 区間の byte 境界をどう決めるかを file:line で示せ。含めない方がよければ理由を書け。
5. **正例・負例の設計 (実体を名指し)。** 親 brief §1 の fixture 実測 (accepted 3 件、rejected 3 件、indeterminate 2 件、`max_report=0` の切詰め) を使い、test を nodeid 粒度で列挙せよ。各 test が producer のどの分岐を通し、何を殺すかを 1 行で書け。**複数 witness class の負例**について、`orchestrator/tests/fixtures/` に `total_cycles >= 2` を出す実 trace があるか探せ (親は 8 件しか走査していない)。無ければ typed `VerifyResult` を合成する 1 件を明記付きで設計せよ。
6. **端から端の正例。** producer が実 verifier 走 (`fixtures/r9_dense_cycle4`) から作った rejected record と projection を、既存 fixture の origin 一式 (`reflux_origin_fixture_builder.py`) へ差し替えて consumer の `evaluate_formal_origin` が FC07 を通す (D338 のとおり最終は `P6Unavailable`) test を設計せよ。差し替えに要る材料 (ledger member の `constraint_sha256`、`evidence_digest`、WAL の trigger binding、build_attempt_id) を file:line で示せ。実現できない材料があれば名指しし、代替の到達点 (例: `_validate_wal_outcomes` を直接呼ぶ) を書け。
7. **不変条件の維持をどう示すか。** 親 brief §3 の各不変条件について「この変更がそれを壊していないこと」を示す検査を書け。特に fixture / golden bytes 不変と、producer が consumer より緩い形を出さない (規律 2) の**負例**を具体的に設計せよ。
8. **pin 閉包の裏取り。** 親 brief は「path pin は `test_reflux_result_evidence.py` の golden 4 個と受入所要台帳の nodeid だけ」と暫定判断した。`git grep` で裏取りするか反証せよ。`orchestrator/tests/README.md` の test file 登録、自走 harness (新 test file を作る場合)、`acceptance_duration_ledger.json` の被覆率 gate を実際に読め。**見落としがあれば名指しせよ。**
9. **変異候補の事前登録。** 段 6 で走らせる変異の候補を 8〜14 件、対象 file:line (実装後の見込み位置でよい) と「殺すはずの test nodeid」の対で挙げよ。他層が先に同じ入力を拒否して赤にする冗長な候補は挙げるな (帰属が壊れる)。特に「producer の条件を落としても consumer が拒否するので緑のまま」型の等価変異を見分け、producer 単体 test で殺せる形に照準せよ。
10. **事前予測。** 実装後、producer が r9_dense_cycle4 から作る class digest が consumer の `_witness_class_sha256` と一致するか、fixture golden 4 個が不変か、受入所要台帳の被覆率 gate が赤になるかを予測せよ。根拠と外れうる点を書け。予測は予測として明記せよ。

## 禁止

- 実装・編集・commit・push・branch 操作。
- 親 brief §2 の scope 外 (execution-provenance/v2 の issuer、`run_campaign()` 最終化点への配線、`run_origin_trial` の production 呼び手、`_initialize_locked` の production 拒否解除、33 attempt topology、witness 構造同値類、`dsg.py` 理由順、bool 型厳密性、terminal 外枠) を計画に入れること。必要なら「裁定パッケージ候補」として別節に書け。
- 仮想リスク向けの gate・検査・台帳・一般化の追加。**consumer の受理集合を広げる提案** (規律 2)。
- 出力へ結合文字 U+0300〜U+036F を使うこと。

## 出力形式

H2 見出しで上記 1〜10 を順に書き、最後に `## 総括` (5 行以内: 方向、編集面の総行数見込み、最大の不確実点、裁定パッケージ候補の有無) を必ず置け。
