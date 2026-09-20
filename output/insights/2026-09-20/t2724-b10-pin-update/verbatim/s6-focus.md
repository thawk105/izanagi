## 所見別 対応表 (closed / partial / regressed)

HEAD は `ac8bd027f`。fix 差分は指定の docs 3 file のみでした。以下、`decisions` は `docs/spool/decisions/2026-09-20-dev-wave-t2724-b10-pin-update-2.md` を指します。

| 所見 | 判定 | 根拠・残件 |
|---|---|---|
| A-1：n2 の期待 node 集合の範囲 | **closed** | [s4-ruling.md:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-b10-pin-update/s4-ruling.md:19) が B-10 test 3 file に固定。全 suite の s1 側検査を冗長 gate と明記し、証拠を「B-10 pin が s1-freeze の bytes も束縛する」に限定した。実測成立とは主張していない。 |
| A-2 / B-1：旧 checkout の拒否保証 | **closed** | `docs/b10-backoff-static-tail-submission.md:26`、`docs/phase3-8b-restart-runbook.md:326`、`decisions:19–22` のすべてが更新版 script の保証へ限定され、旧 script＋旧 tree は失効しないと明記。日付による失効の含意は解消。「main に載せた版以降」「同じ版」は chain 導入後の条件として読め、新たな時点誤認を阻害所見とは認めない。 |
| A-3 / B-2：未実走の完了形 | **closed** | `decisions:38–41` の「実施した」は削除され、結果・証拠を記録する予定形と未実施時の扱いに変更。`:21` も算法上の性質と実測を区別している。 |
| A nit：「codex 子 0 本」の時点 | **partial** | `docs/spool/worklog/2026-09-19-dev-wave-t2724-chain-land-2-1.md:19` は未変更。`:20` の履歴説明で解釈可能だが、工数行自体の限定はない。**通る正例：**「工数（受入前の記録時点）: codex 子 0 本。最終工数は entry 1688 を参照」。 |
| B nit：「唯一の形」の条件付け | **closed** | `decisions:33–35` に「G の取り込み・現行の全 file 完全一致検査・B-10 の継続利用を保つ条件下」が入った。 |
| B nit：submission の clean-scan 注意 | **partial** | `docs/b10-backoff-static-tail-submission.md:26` に追記なし。`docs/phase3-8b-restart-runbook.md:326` の注意は維持。**通る正例：**「chain 導入後の official 床値 clean scan は run_dir 3 file＋候補の hit 4/4 で赤になる。運用は restart runbook W-3 を参照」と補う。 |

## 新規所見

**新規の阻害所見・regression は認めません。**

- **docs parser：** `orchestrator/tests/test_b10_backoff_grid_submit.py:305` は指定節内の最初の code block を抽出する。submission の変更は §1 のみで、§2 の見出し・code block（`:28–37`）・placeholder は不変。
- **check_docs の予算：** `tools/check_docs.py:5947` 以降の予算対象に今回の3文書は含まれず、予算対象ファイルにも変更なし。この fix による予算超過はない。
- **spool frontmatter：** `decisions:1–7` は不変。必須5 field、日付、正の `seq`、ファイル名との対応は `tools/spool_fold.py:1062–1094` の条件に整合する。決定見出し（`:9`）も不変。

いずれも静的確認であり、`check_docs` 全体や spool fold の実行成功を示すものではありません。

## 判定 (GO / NO-GO と理由)

**GO：焦点再レビューとして、残りの検証へ進めます。**

must-fix と should はすべて closed。残る2件は既存の非阻害 nit です。実装変更を要求する理由はありません。

ただし、受入完了の判定ではありません。前渡しの焦点走・n1・n3 は確認済み事実として扱い、m1／m2／n2 は結果未取得、受入全走は未投入として扱います。n1／n3 の結果を job 本体の拒否実走の証拠へ拡張しません。

## 総括

文書の保証範囲、n2 の期待集合、実測状況の表現は修正されています。残る作業は検証結果の取得・記録と受入全走です。本レビューではファイル変更・テスト実行は行っていません。