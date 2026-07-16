# 2026-07-16 8b 監査凍結・§9 承認前検証 — codex 敵対相談 3 本の記録

- 実行: codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only, cwd=repo
- 目的: checkpoint (c) 凍結プラン (C1) / §9 draft 8 項目の承認提示前検証 (C2) / セッション計画全体 (C3) の敵対的検証
- 経緯: 凍結対象の監査全文 audit-wave1/2-out.md の消失発見を受けたセッション (worklog 2026-07-16 (9) 予定) の一次記録
- 本ファイルは prompt と出力の逐語保存。裁定 (採用/変更) は worklog と成果物側に記録する

---

## C1 prompt

```markdown
# 敵対的検証依頼 C1 — 8b 二波監査記録の凍結プラン (checkpoint (c))

あなたは izanagi リポジトリ (cwd) の敵対的レビュアである。読み取り専用。以下の「私のプラン」を攻撃し、裁定を返せ。忖度不要。プランの弱点・自己欺瞞・規律違反 (特に「盛らない」「正直」) を探せ。

## 背景 (事実、検証可能)

- docs/phase3.md 現行チェックポイント「次:(c)」= 「8b 二波監査の全文 (scratchpad 退避分) を output/insights または監査 JSON へ凍結」。docs/worklog.md 2026-07-16 (5) エントリ (815〜851 行) が監査の要約の正本。
- **凍結対象の監査全文 (audit-wave1-out.md / audit-wave2-out.md) は消失した。** 全 /tmp/claude-*/ scratchpad に不在、~/.codex/sessions は本日午後の 4 件のみ (監査は午前実行)、Claude transcript にも内容なし。
- 残存証拠:
  1. worklog (5) の要約: 第 1 波 (A/C/D2 = 14 file) real 9 / refuted 5、第 2 波 (B/D1) real 4 / refuted 6。最重要 = report/judge の false-green 4 経路 (expected binding 欠落で binding_ok=True / retry で correctness red が後続 commit に上書き / holdout 全落ちでも determinate / manifest hash 自己申告受理) と driver の null-restore が未承認 floor で gate を開く恒真化。全 13 件を修正し番人テストを追加、修正はコミット済みコードに織込み済み。
  2. コミット済み実装 + テスト群: e247552..98e4133 (orchestrator/campaign/s8b_*.py、orchestrator/tests/test_s8b_*.py 計 ~6300 行)。番人テストはここに存在するはず。

## 私のプラン (これを攻撃せよ)

output/insights/2026-07-16_s8b-two-wave-audit.md (または JSON — 前例: output/insights/2026-07-14_codex-agent-adapter-reaudit.json) を新規作成して凍結する。内容:
1. 監査の来歴 (2 波、対象領域、codex read-only、real/refuted 選別方式)
2. real 13 件の再構成 — worklog 要約に記述のある 5 件は詳細、残り 8 件はコミット済みコードの番人テストから同定できる範囲で記述。**各項目に番人テスト参照 (file::test名) を付け、テストの実在を機械確認する**
3. refuted 11 件は件数のみ記録 (詳細は消失、復元不能と明記)
4. 全文消失の経緯 (揮発性 /tmp scratchpad へ退避 → セッション後に消失) と、この記録が「要約+コード証拠からの再構成」であって逐語の全文ではないことの明記

## 検証してほしい点 (最低限。他の攻撃面も歓迎)

1. **消失下での再構成凍結は正直か。** 代替案との比較裁定: (i) 凍結せず worklog に消失記録のみ / (ii) 新規に第 3 波監査を実施してそれを凍結 (来歴は別物になる) / (iii) 私の案 (再構成+消失明記) / (iv) 再構成 + 新規監査の併用。どれが最も防御可能か。
2. **再創作 (fabrication) リスク。** 「残り 8 件を番人テストから同定」は逆推定であり、テスト追加が監査起因か実装時から存在かを区別できるか?区別できないなら記述をどう限定すべきか。実際に orchestrator/tests/test_s8b_*.py をいくつか読み、worklog 記述の 5 件 (binding_ok / retry 上書き / 全落ち determinate / hash 自己申告 / null-restore 恒真) に対応する番人テストが同定可能かをサンプル確認せよ。
3. **置き場と形式。** output/README.md の insights 規定に照らし、.md か .json か、命名は妥当か。
4. **worklog の件数記述との整合。** 「real 9+4=13 / refuted 5+6=11」の合計と「全 13 件を F1/F2 で修正」の対応が取れているか、worklog 原文を読んで確認。

## 出力形式 (厳守)

```
## 裁定
(プラン全体: 採用 / 修正のうえ採用 / 棄却 — 1 行 + 理由 3 行以内)
## 代替案の比較
(i)〜(iv) の順位と理由
## REAL (採用すべき指摘)
- [C1-R1] ... (根拠: file:line または worklog 行)
## REFUTED (プランのままで問題ない点)
- [C1-F1] ...
## 推奨する凍結文書の骨子
(節構成と、各節に書いてよいこと/書いてはいけないこと)
```
```

## C1 出力 (逐語)

## 裁定

修正のうえ採用 — 「消失記録＋残存証拠からの再構成」としては正直だが、「監査全文の凍結」として閉じてはならない。  
安全に個別再構成できるのは13件中12件で、残る1件をテストから創作する案は棄却する。

## 代替案の比較

1. **(iv) 再構成＋新規監査** — 最も防御可能。歴史記録と現行コードの再監査を別成果物・別 ID で分離することが条件。新規監査を失われた二波の代替とは扱わない。
2. **(iii) 再構成＋消失明記** — 最小の採用可能案。ただし「12件を再構成、1件は個別内容不明」とし、checkpoint の「全文」も訂正する必要がある。
3. **(ii) 新規第3波のみ** — 現行コードの保証にはなるが、修正前コードを対象とした二波の来歴・refuted 11件を復元できない。
4. **(i) 消失記録のみ** — 嘘はないが、コミット本文とテストに残る回収可能な証拠まで捨て、監査記録を insight に残す規約にも最も弱い。

## REAL (採用すべき指摘)

- [C1-R1] 再構成文書を作って checkpoint (c) の「監査全文を凍結」を完了扱いするのは虚偽。「原文消失、代替再構成を凍結」に checkpoint 自体を改訂すべきであり、完了変更なら同じ commit に含める必要がある。根拠: [docs/phase3.md:43–47](/home/SFC/tanab/github/izanagi/docs/phase3.md:43)、[CLAUDE.md:150–152](/home/SFC/tanab/github/izanagi/CLAUDE.md:150)

- [C1-R2] 「残り8件を同定」は成立しない。コミット本文から回収できる監査 ID は F-1〜F-7、F-9、G-1〜G-4の計12件で、F-8が欠落している。worklog 詳細5件以外に安全に復元できるのは7件であり、最後の1件は「内容・修正・テスト対応不明」と残すべき。根拠: commit 4639558、405bc46、bdb3624、4d82c98、98e4133 の本文、[docs/worklog.md:830–835](/home/SFC/tanab/github/izanagi/docs/worklog.md:830)

- [C1-R3] テストから監査起因性は証明できない。対象実装とテストは各 feature commit で同時に新規追加されており、監査前後の版が Git にない。したがって `番人テスト` ではなく「現行修正を裏付ける regression evidence」と書くべき。コミット本文による監査 ID 対応は「commit-attributed」、テストだけの対応は「推定」と分ける。根拠: e247552..98e4133 の commit 統計、[docs/worklog.md:821–835](/home/SFC/tanab/github/izanagi/docs/worklog.md:821)

- [C1-R4] worklog 詳細5件との対応テストは同定可能。ただし意味を膨らませてはいけない。

  - binding 欠落: [test_s8b_oracle_report.py:274](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_s8b_oracle_report.py:274)
  - retry による red 上書き: [test_s8b_oracle_report.py:298](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_s8b_oracle_report.py:298)
  - manifest hash 自己申告: [test_s8b_oracle_report.py:319](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_s8b_oracle_report.py:319)
  - holdout 全落ち: [test_s8b_oracle_report.py:334](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_s8b_oracle_report.py:334)。このテストが保証するのは「期待 holdout の全 row が欠落」であり、「全試行が失敗結果を返した」まで拡張してはいけない。
  - null-restore: [test_s8b_oracle_driver.py:265](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_s8b_oracle_driver.py:265)、[s8b_oracle_driver.py:113–127](/home/SFC/tanab/github/izanagi/orchestrator/campaign/s8b_oracle_driver.py:113)。これは現行の fail-closed 修正を保証するが、消失した旧 null-restore 実装そのものを再現するテストではない。

- [C1-R5] F-8候補を、名前の似た `test_screen_marker_is_protocol_violation` や `test_only_manifest_campaign_is_read...` に割り当てる根拠はない。そうした逆推定はまさに fabrication になる。根拠: [test_s8b_oracle_report.py:366–390](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_s8b_oracle_report.py:366)

- [C1-R6] 「real/refuted 選別方式」の詳細は復元不能。書けるのは、worklog が「codex read-only、real/refuted 選別」と記録していることだけ。判定プロンプト、裁定者、severity、却下理由を一般的監査作法から補ってはいけない。また「14 file」は第1波の対象規模であり、finding 数ではない。根拠: [docs/worklog.md:830–834](/home/SFC/tanab/github/izanagi/docs/worklog.md:830)

- [C1-R7] 「揮発性 `/tmp` だったためセッション終了時に削除された」という因果も断定過剰。記録可能なのは「そのパスへ退避した」「後の探索時に存在しなかった」「正確な消失時刻・削除主体・原因は不明」。根拠: [docs/worklog.md:835–836](/home/SFC/tanab/github/izanagi/docs/worklog.md:835)

- [C1-R8] 推奨形式は Markdown、命名は `output/insights/2026-07-16_s8b-two-wave-audit-reconstruction.md`。通常の `...audit.md` は原文監査に見える。JSON は完全な finding/refuted 台帳に向くが、この不完全記録を精密に見せる危険があり、README に監査 JSON schema もない。なお insights は機械防護外なので、Git commit に入って初めて「凍結」と呼べる。根拠: [output/README.md:38–48](/home/SFC/tanab/github/izanagi/output/README.md:38)、[output/README.md:59](/home/SFC/tanab/github/izanagi/output/README.md:59)

## REFUTED (プランのままで問題ない点)

- [C1-F1] 件数は整合する。第1波 real 9 / refuted 5、第2波 real 4 / refuted 6なので、real 13 / refuted 11。「全13件を修正」も集計上は real 13件と対応しており、矛盾はない。ただし一件一テストの全単射までは意味しない。根拠: [docs/worklog.md:830–835](/home/SFC/tanab/github/izanagi/docs/worklog.md:830)

- [C1-F2] refuted 11件を件数だけ記録し、内容・却下理由は復元不能とする方針は正しい。空欄をもっともらしい却下理由で埋めるより防御可能。

- [C1-F3] `file::test名` の機械的な実在確認は可能。上記6シンボルは AST で存在確認できた。ただしこの環境では pytest が未導入だったため、現行通過を再実行したとは記録できない。178 passed は当時の worklog 記録としてのみ引用可能。根拠: [docs/worklog.md:821–824](/home/SFC/tanab/github/izanagi/docs/worklog.md:821)

- [C1-F4] 配置先 `output/insights/` は妥当。README は敵対的検証を探索妥当性文書の例として明示している。根拠: [output/README.md:43–59](/home/SFC/tanab/github/izanagi/output/README.md:43)

- [C1-F5] 「逐語録ではなく再構成」と明示した再構成自体は fabrication ではない。証拠の強さごとに書き分け、未知の1件を未知のまま残す限り採用できる。

## 推奨する凍結文書の骨子

1. **表題・記録種別**

   - 書いてよい: 「二波監査の原文消失記録および残存証拠からの再構成」
   - 書いてはいけない: 「監査全文」「復元版全文」「原監査記録」

2. **原文の状態**

   - 書いてよい: 元ファイル名、退避先が一時領域だったこと、後日不在を確認した探索範囲、原文 hash も存在しないこと
   - 書いてはいけない: 証拠のない削除時刻・削除主体・自動 cleanup の断定

3. **残存証拠と証拠階層**

   - worklog = 当時の集計・重要 finding の正本
   - commit 本文 = 監査 ID と remediation の contemporaneous attribution
   - 現行コード・テスト = 修正後 invariant の回帰証拠
   - 書いてはいけない: 現行テストを原監査の逐語 evidence と扱うこと

4. **確定できる集計**

   - 第1波: 対象 A/C/D2、14 files、real 9 / refuted 5
   - 第2波: 対象 B/D1、real 4 / refuted 6
   - 合計: real 13 / refuted 11
   - 選別手順の詳細は不明と明記

5. **real finding 再構成台帳**

   - `worklog-detail`: F-4、F-5、F-6、F-7、G-1
   - `commit-attributed`: F-1、F-2、F-3、F-9、G-2、G-3、G-4
   - `unreconstructed`: 1件。コミット ID 列では F-8 が欠落しているが、それが原監査の正式 ID だったかも断定しない
   - 各行には `historical_source`、`reconstructed_summary`、`fix_commit`、`current_regression_evidence`、`confidence` を持たせる
   - 書いてはいけない: 未知の1件への題名・severity・テスト割当て、一対一の監査起因テスト保証

6. **refuted finding**

   - 波別件数と合計だけ
   - 原 claim、却下理由、ID、severity は「原文消失により不明」
   - 新規監査で似た仮説が棄却されても、旧refuted 11件へ遡及対応させない

7. **任意の第3波監査**

   - 別ファイル、別日付、別 scope、別 ID 系列で `98e4133` 後の現行コードを監査
   - 二波の13/11集計には混ぜず、「原文復元」や欠落1件の補完と称しない

8. **checkpoint の処置**

   - 「原監査全文は復元不能。消失記録と12件の再構成、1件の個別内容不明を凍結した」と phase を訂正
   - 「全文凍結完了」とは書かない。
---

## C2 prompt

```markdown
# 敵対的検証依頼 C2 — §9 再凍結 draft 8 項目の承認提示前検証

あなたは izanagi リポジトリ (cwd) の敵対的レビュアである。読み取り専用。これからユーザーに docs/phase3-8b-descriptor-design.md §9「再凍結 draft 2026-07-16」の 8 項目の承認を求める。**承認を求めてよい状態か**を検証せよ。承認後は selector 予測の実実行が解禁されるため、ここが最後の関所である。忖度不要。

## 読むべきもの

- docs/phase3-8b-descriptor-design.md §9 (269 行〜) — 承認対象の 8 項目
- 同 §4 (対照設計)、§5.1 (variant 集合・oracle・予測選択)、§6 (判定基準) — §9 が「確定/変更」すると称する旧凍結の本文
- 実装: orchestrator/campaign/s8b_selector_freeze.py、s8b_selector_input.py、s8b_selector_output.py、s8b_selector_output_schema.json、s8b_selector_catalog.json、s8b_oracle_manifest.py、s8b_oracle_driver.py、s8b_oracle_judge.py、s8b_oracle_report.py、s8b_budget.py
- テスト: orchestrator/tests/test_s8b_*.py
- 役定義: .claude/agents/selector-8b.md (存在すれば)

## 検証してほしい点

1. **項目↔実装の食い違い。** 8 項目それぞれについて、コミット済み実装が項目の記述と一致するか。特に:
   - 項 2: カタログが本当に不透明 ID (c01..c06) + 中立語彙だけか。variant_binding の生値 (backoff 値・comparator・パス等) が selector 入力へ漏れる経路はないか (s8b_selector_input.py を精査)
   - 項 5: strict parser が実際に「未知キー・重複キー・複数選択・fence・非有限値」を全部拒否するか。恒真化 (謳うだけで発火しない) はないか
   - 項 6: selector_predictions.json の exclusive-create + 部分 hash (selector_basis) + commit pin が実装済みか、それとも未実装 (承認後に作る) か。draft の記述と実装状態の対応がユーザーに誤解なく伝わる書き方か
   - 項 8: resume 拒否が実装で発火するか
2. **項目間の隠れた結合。** 一部承認・一部差し戻しが可能な独立性があるか、それとも「項 X を差し戻すなら項 Y も無効」という結合があるか。結合があるなら提示時に明記すべき。
3. **内部矛盾・未規定の残り。** 8 項目で §4/§5.1/§6 の未規定点は尽きているか。承認しても実行時にまた「未規定でした」が出る穴があるか (例: selector への入力 payload の凍結、6 セルの実行順、predictions 生成の手続き)。
4. **提示形式。** 8 項目を 2 グループ × 4 項目 (グループ 1 = selector の入出力規律: 項 1,2,4,5 / グループ 2 = 凍結・判定・再開規律: 項 3,6,7,8) として multiSelect 承認で提示する案の妥当性。グループ分けが不自然なら代案を。

## 出力形式 (厳守)

```
## 裁定
(承認提示して良い / 修正後に提示 / 提示前に実装修正が必要 — 1 行 + 理由 3 行以内)
## 項目別検証表
| 項 | 実装との一致 | 根拠 (file:line) | 提示時の注意 |
## REAL (提示前に直すべき指摘)
- [C2-R1] ...
## REFUTED (問題ない点)
- [C2-F1] ...
## 提示文の推奨 (各項 1 行要約 + リスク 1 行、日本語)
```
```

## C2 出力 (逐語)

## 裁定
提示前に実装修正が必要  
理由: 項4/5は宣言に留まり、同一 raw の再利用や非 JSON raw を valid と偽装しても prediction verifier が受理する。  
理由: 現行 holdout freeze は design hash 不一致で失格し、項6の実 Git commit pin・oracle 前置 gate も未実装。  
理由: §6の判定量化と項8の全域 resume 拒否が未確定で、「承認＝実実行解禁」にはできない。

## 項目別検証表
| 項 | 実装との一致 | 根拠 (file:line) | 提示時の注意 |
|---|---|---|---|
| 1 | 一致 | `s8b_selector_input.py:22-31`; `s8b_selector_freeze.py:221-248,394-404` | `c06 → stock_common` は項2の対応表に依存。項2差し戻し時は項1も再裁定。 |
| 2 | 部分一致 | `s8b_selector_catalog.json:1-10`; `s8b_selector_input.py:33-43,102-130`; `s8b_descriptor.py:208-212` | builder 出力には binding・backoff・comparator・path の漏洩なし。ただし実際に送信した prompt/payload を artifact に束縛する executor がない。 |
| 3 | 部分一致 | `s8b_selector_freeze.py:278-295,466-479` | target-local binding と family-ID 期待値は実装済み。実際に family 一致を判定する selector verdict consumer は未実装。項2・6に従属。 |
| 4 | 不一致 | `s8b_selector_freeze.py:2-5,63-69,343-348,351-463` | 6行の列挙は実装済みだが、fresh 4呼出し・一回限り・raw 非再利用はメタデータ宣言だけ。同一 child/raw でも通る。実行順も未凍結。 |
| 5 | 部分一致 | `s8b_selector_output.py:52-80,83-116`; `s8b_selector_freeze.py:298-323,554-560` | parser 単体は全列挙ケースを拒否する。しかし freeze verifier は raw を再 parse せず、記録済み status/choice を信用する。 |
| 6 | 部分一致 | `s8b_selector_freeze.py:251-275,482-517,520-608`; `test_s8b_selector_freeze.py:140,327-350`; `s8b_oracle_driver.py:101-164` | exclusive-create・body hash・basis 関数は実装済み、ファイル未生成との記載も正確。一方、任意の40桁値を commit として受理し、oracle gate は prediction freeze を要求しない。 |
| 7 | 一致 | `s8b_oracle_report.py:383-395`; `s8b_oracle_judge.py:82-105,219-234` | raw reps の試行中央値→構成中央値を使用し、floor を tie-break に使わない。承認後は「未再凍結」の docstring 更新が必要。 |
| 8 | 部分一致 | `s8b_oracle_driver.py:344-360,362-390,612-619`; `wal.py:75-92` | 同一 output root・同一 campaign の有効 WAL には発火する。別 output root、末尾切れだけの WAL、別 block/campaign まで包含する拒否ではない。 |

## REAL (提示前に直すべき指摘)
- [C2-R1] 現行 `holdout_freeze.json` は `design_source.sha256` が旧本文を指し、実際の `s8b_holdout_freeze.py verify` は `design_source sha256 不一致` で失敗する（`holdout_freeze.json:5-8`; `s8b_holdout_freeze.py:605-608`）。承認後に検証可能な再凍結を作り、それが通るまで selector を起動しない gate が必要。
- [C2-R2] adversarial positive control では、4 agent cell 全部に同一の Python ソース（非 JSON）を raw として割り当て、`status=valid`, `choice_id=c01` と偽装しても `verify_prediction_freeze()` が受理した。raw を再 parse し、status・choice・rationale・error code を再導出する必要がある。parser 実装自体も source hash に追加すべき。
- [C2-R3] 項4の実行規律は非発火保証である。module 自身が selector を実行せず、child ID・raw path・呼出し ID の一意性も検査しない。正準 payload の保存、固定順序、resolved model、実呼出し ID、raw の exclusive-create を扱う単一の trusted generation 手続きが必要。
- [C2-R4] 項6の commit pin は形式検査だけで、テストも存在しない `"a"*40` を正例にしている（`test_s8b_selector_freeze.py:140`）。`git cat-file` と HEAD/ancestor 条件を検査し、oracle manifest/gate に prediction file hash と basis hash を必須参照として追加すべき。後日 freeze 更新時に旧 freeze source をどこへ不変保存するかも規定が必要。
- [C2-R5] §6にはまだ、swapped 追従が「両 holdout/いずれか」、oracle floor 超が符号付き `on-off>floor` か絶対差か、三条件が同一 holdout で成立すべきか、非空 rationale の何を「descriptor 消費の証拠」とするか、が未規定。これらを凍結し、prediction と oracle を結合する三値 judge を実装しない限り判定不能。
- [C2-R6] 項8は全域 resume 拒否になっていない。`--output-root` 変更で別 WAL 空間を作れ、`wal.read_records()` は末尾切れのみなら空配列を返す。また block ごとに別 process/campaign を使う現設計との両立手続きがない。output root の manifest pin、WAL ファイル存在ベースの拒否、全 block の実行トポロジーとテストが必要。
- [C2-R7] 提案の2グループ×4 multiSelect は依存を分断する。項2差し戻しは1/3/6、項3差し戻しは6、項4または5差し戻しも6を無効にする。推奨単位は A=`1,2,3`、B=`4,5,6` を各 atomic bundle、C=`7,8` を相互独立の選択として提示すること。

## REFUTED (問題ない点)
- [C2-F1] catalog は `c01..c06` と機構分類だけで、backoff 値、flags、comparator、gate predicate、anchor、source path は含まれない。
- [C2-F2] parser 単体では未知キー・重複キー・配列による複数選択・Markdown fence・`NaN/±Infinity` がすべて実際に拒否される。
- [C2-F3] off は agent 非呼出しの `c06/stock_common` で固定され、invalid agent 出力への c06 fallback もない。
- [C2-F4] prediction writer の hard-link による atomic exclusive-create、body SHA-256、floor/budget を除外する selector basis は実装済み。
- [C2-F5] oracle の median-of-medians と exact tie、non-finite/欠測の判定不能化は実装・テストされている。
- [C2-F6] 同一 campaign に有効な WAL record があれば resume 拒否例外は実際に発火する。単なる `assert` ではない。
- [C2-F7] 現時点の未既知性再検索自体は rr80/rr20 とも0 hit、positive control 41 hit。現行 freeze の失格原因は既知化ではなく design hash 不一致。
- [C2-F8] 指定された設計・実装・テスト・role ファイルは tracked かつ対象差分なしであり、本裁定は commit 済み HEAD の内容に対するもの。

## 提示文の推奨 (各項 1 行要約 + リスク 1 行、日本語)
提示単位: A=`1–3` と B=`4–6` は bundle 承認、C=`7` と `8` は個別承認とし、2×4の独立 multiSelect は使わない。

1. 要約 — off の2セルは selector を呼ばず、常に `c06 = stock_common` を `decision_method=static_default` として記録する。  
   リスク — on/off 差には descriptor 有無だけでなく agent 呼出し有無も交絡するため、帰属には swapped 条件が必須。

2. 要約 — selector へ渡す候補は byte 固定の `c01..c06 + mechanism` のみとし、実送信 payload も保存・hash 照合する。  
   リスク — mechanism 語彙は性能値を隠すが機構分類までは隠さない。項2変更時は項1・3・6も再承認する。

3. 要約 — swapped 追従は target-local implementation の一致ではなく、valid な family choice ID の一致として判定する。  
   リスク — 支持できる主張は workload-aware family selection に限られ、exact implementation selection には拡張しない。

4. 要約 — prediction は2 static off行と4 fresh agent呼出しを固定順で各1回行い、再試行・出力再利用・途中閲覧による変更を禁止する。  
   リスク — 同一 payload の独立 LLM 呼出しには標本揺らぎが入り、一度の不調も再試行できない。

5. 要約 — raw 応答は凍結時と再検証時の双方で strict parse し、不正・欠測は `choice_id=null` の判定不能として固定する。  
   リスク — 1セルでも不正なら対応する§6条件を救済せず判定不能へ倒す。

6. 要約 — 承認後、検証済み freeze から専用手続きで prediction を exclusive-createし、body hash・実Git pin・selector basisを封印してからoracleを解禁する。  
   リスク — prediction は上書き不能であり、手続き違反時は再凍結・再承認が必要。現時点ではファイル未生成。

7. 要約 — oracle 値は各 trial の bench rep 中央値を取り、その trial 中央値群の中央値で構成値を決め、floor は argmax tie-break に使わない。  
   リスク — trial を等重みで扱い、exact tie は勝者なしとなる。n/reps 欠測規則も数値再凍結時に固定する。

8. 要約 — 実走開始後は全 manifest-owned campaign/WAL を対象に新 process 起動を拒否し、全 block の実行方法も事前固定する。  
   リスク — crash 後の継続を一切失うため、単一 processで完走できない block 設計とは両立しない。
---

## C3 prompt

```markdown
# 敵対的検証依頼 C3 — セッション計画全体の優先順・見落とし検証

あなたは izanagi リポジトリ (cwd) の敵対的レビュアである。読み取り専用。今セッションの計画を攻撃せよ。忖度不要。

## 現在地 (事実)

- docs/phase3.md 現行チェックポイント「次:」= (a) §9 再凍結 draft 8 項目のユーザー承認 (人間ゲート)、(b) floor/budget 再実測 → holdout freeze v2 再凍結 (env 選択が人間判断待ち、D59)、(c) 8b 二波監査全文の output/ 凍結、(d) 1 cycle 後の再判断。
- worklog 末尾 = docs/worklog.md 2026-07-16 (8)。未 push: 02c840c..HEAD (push は人間判断)。
- **発見: (c) の凍結対象 audit-wave1/2-out.md (監査全文、/tmp scratchpad 退避) が消失。** 残存証拠は worklog (5) の要約とコミット済みコード+番人テスト (e247552..98e4133) のみ。

## 今セッションの計画 (これを攻撃せよ)

1. (c) を実行: 残存証拠からの再構成 + 消失明記で output/insights/ へ凍結 (詳細は別相談 C1 が検証中)
2. (a) の準備: §9 の 8 項目をセッション末にユーザーへ承認提示 (実行はしない)
3. (b) は env 選択が人間判断のため着手しない。strict v2 verifier の先行実装もしない (freeze v2 の数値・schema 確定前の実装は投機的、規律 5)
4. 消失インシデントを docs/failures.md へ F 番号で追記 (worklog と同時)

## 検証してほしい点

1. **優先順の妥当性。** (c) + (a) 準備が今できる最善か。人間ゲートを待つ間に他にやるべき実行可能タスクの見落としはないか。docs/phase3.md の「後続段」開タスク一覧 (`grep -n "^[0-9]\{1,2\}\. \*\*" docs/phase3.md` で列挙、`N. **(完了` 除外) と must 表 (`grep -n "^## 現行 Phase 3 must" docs/phase3.md`) を実際に引いて、現行チェックポイントの着手順と矛盾しないか確認せよ。
2. **strict v2 verifier 先行実装の見送りは正か。** docs/phase3-8b-descriptor-design.md §5.2/§8 と output/s8b-freeze/holdout_freeze.json を読み、freeze v2 の schema が数値以外は確定しているなら、verifier 骨格の先行実装に価値があるか、それとも見送りが正か。
3. **failures.md 追記の要否。** docs/failures.md を読み、既存の型タグ体系に照らして「監査全文を揮発性 /tmp scratchpad に退避して消失」が新規 F エントリに値するか、既存タグの再発か。追記するなら恒久対応案 (例: 監査・相談の全文はセッション中に output/ か repo 内へ置く、scratchpad は当日限りと見なす) の妥当性。
4. **worklog (5) の他の未処理素材。** worklog 2026-07-16 (5) の「素材:」(リーク制御一次事例) は insight 凍結すべきか、worklog 記載で十分か。
5. **やってはいけないことの確認。** 今セッションで計測・push・selector 予測実実行・floor 再実測をしないという線引きに穴はないか。

## 出力形式 (厳守)

```
## 裁定
(計画: 採用 / 修正のうえ採用 / 棄却 — 1 行 + 理由 3 行以内)
## REAL (採用すべき指摘)
- [C3-R1] ... (根拠: file:line)
## REFUTED (計画のままで問題ない点)
- [C3-F1] ...
## 推奨する実行順 (今セッションの具体的タスク列)
```
```

## C3 出力 (逐語)

## 裁定
計画: 修正のうえ採用  
(c) 最優先と、承認前の selector・floor 計測停止は正しい。  
ただし、現 C1〜C3 の再消失防止、第二の人間ゲート提示、phase 正本ドリフト、F20 の恒久防壁を追加すべき。

## REAL (採用すべき指摘)
- [C3-R1] 最優先は再構成より先に、現在の C1〜C3 prompt/output を repo 内へ即時退避すること。消失原因を発見した同じセッションで、再び唯一のコピーを scratchpad に置いており再発中である。「当日限り」でも弱く、scratchpad は最初から非永続と扱うべきである。(根拠: docs/handoff/2026-07-16-8b-audit-freeze.md:23)
- [C3-R2] `phase3.md` の正本リストを修理する実行可能タスクが抜けている。段 6 は S′ 確定済みにもかかわらず未完タイトル・未チェックのまま、段 8 も「8b 未着手」のままである。後続段リストが完了状態の正本なので、単なる cosmetic drift ではない。(根拠: docs/phase3.md:51, docs/phase3.md:205, docs/phase3.md:225, docs/phase3.md:298, docs/worklog.md:741)
- [C3-R3] セッション末には §9 だけでなく、floor 再実測の env 選択も同時に人間へ提示すべきである。D59 上の既定は `linux-baremetal` 維持で、Pegasus 採用は専用 env-tag・再 calibration/floor・単独性確認・成果物追跡の四条件付き。この選択を提示しないと、解消可能な人間ゲートを一巡余計に残す。(根拠: docs/worklog.md:915, docs/decisions.md:2282)
- [C3-R4] 将来の (b) は「env 選択 → floor 計測 protocol と v2 exact schema の事前承認 → 再実測 → 数値充填・再凍結承認」と明記すべきである。現文面の「再実測 → 再凍結」だけでは、n・block・算出式・seed・reps 等を結果閲覧後に決める余地が残る。(根拠: docs/phase3-8b-descriptor-design.md:206, docs/phase3-8b-descriptor-design.md:255, docs/phase3-8b-descriptor-design.md:309)
- [C3-R5] 消失は新規 F20 `[手順漏れ]` に値する。F4 は突然死時の可変状態救出であり、今回は「完走済み監査の必須証拠を揮発性領域だけに置いた」という別の恒久対応を要する。対応は宣言だけでなく、監査 launcher の repo-local create-only 出力、または active handoff が transient-only pointer を持つ場合の lint まで実体化すべきである。(根拠: docs/failures.md:10, docs/failures.md:46, docs/handoff/README.md:9)
- [C3-R6] worklog (5) のリーク制御素材は worklog だけで終えない方がよい。ただし別の大文書を増やさず、再構成する監査・妥当性 insight に短い一次事例として統合する。主張できるのは「値だけでなく性能由来 lineage も遮断した設計」であり、selector 実走前なので有効性実証とは書かない。(根拠: docs/worklog.md:19, docs/worklog.md:837, docs/phase3-8b-descriptor-design.md:279, output/README.md:59)

## REFUTED (計画のままで問題ない点)
- [C3-F1] (c) を最優先にする判断は正しい。ただし成果物名・summary で「監査全文の復元」と称さず、「残存証拠からの再構成」とし、失われた finding 本文と推論部分を明示的に区別する。(根拠: docs/worklog.md:830, docs/worklog.md:835)
- [C3-F2] strict v2 verifier の現時点での先行実装見送りは正しい。確定しているのは意味上の項目集合であり、floor provenance、env-tag、測定 source/hash、n/block/formula、承認履歴を含む exact JSON schema は未確定である。現 JSON は `/v1` かつ null、driver には非 null を拒否する番人テストもあるため、安全上の穴はない。schema 承認後なら、数値確定前でも骨格を実装できる。(根拠: output/s8b-freeze/holdout_freeze.json:3, output/s8b-freeze/holdout_freeze.json:622, orchestrator/campaign/s8b_oracle_driver.py:121, orchestrator/tests/test_s8b_oracle_driver.py:265)
- [C3-F3] 他の研究実装を前倒しする必要はない。must 表の S1 は cross-protocol 時だけ発火、段 7 は 8b＋層3後、8c は 1 cycle 後に運営律速が確認された場合だけ、層3 v3 も次 loop 同時実装である。(根拠: docs/phase3.md:156, docs/phase3.md:262, docs/phase3.md:322, docs/phase3.md:330)
- [C3-F4] 今セッションで計測・push・selector 実予測・floor 再実測をしない線引きは正しい。加えて actual holdout payload を使う「dry run」、oracle 実走、仮値入り manifest 生成も禁止対象とする。一方、synthetic fixture の単体テスト、lint、文書修正、commit は可能である。(根拠: docs/phase3.md:43, docs/worklog.md:845, docs/worklog.md:847, docs/decisions.md:2290)

## 推奨する実行順 (今セッションの具体的タスク列)

1. 現在の C1〜C3 prompt/output を repo-local の create-only 成果物へ即時保存し、hash と path を handoff に記録。
2. 残存証拠だけで二波監査を再構成し、原文消失・再構成可能範囲・finding→修正 commit→番人テストの対応を明示。
3. F20 を追加し、handoff 規約または launcher/lint に transient-only 保存を防ぐ実体を同時導入。
4. リーク制御一次事例を、監査成果物内の短い妥当性 insight として凍結。
5. `phase3.md` の段 6 完了状態と段 8 の現状表記をチェックポイントへ同期。
6. 関連テスト・docs/Codex-agent 検査・provenance 監査を通し、worklog を一度だけ更新して commit。push はしない。
7. 最終提示で二つの人間判断を同時に求める。

   - §9 の 8 項目: 承認／項目別修正
   - floor 環境: `linux-baremetal` 継続／Pegasus 正式採用手続き開始

承認応答を得るまでは selector 予測・計測へ進まない。
