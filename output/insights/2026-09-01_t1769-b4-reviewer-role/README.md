# [T-1769] B-4 事前登録 §5.1 (i) の記入者・レビュー者指名と役割定義 (2026-09-01)

D1266 に従い、`docs/phase3-b4-reflux-ablation-preregistration.md` の §5.1「対象 driver と軸」bullet へ、
(i) の記入者・レビュー者の指名 (いずれも `thawk105`) と、レビュー者の役割定義文を同じ変更単位で足した。
docs のみの変更で、実装面の差分はゼロである。

## 何を書いたか

(i) の要求文 (「…記入者とレビュー者を **別 commit で先に固定する**。」) は 1 byte も変えず、
その直後・(ii) の開始前へ 3 文を追記した。

- 記入者とレビュー者はいずれも `thawk105` を指名する (D1266)。
- レビュー者は独立検査者ではなく、記入内容が事前登録の要求を満たすことの確認責任者であり、
  独立性を要求しない。
- この指名が固定するのは (i) の項目のうち記入者とレビュー者だけであり、(i) の充足を意味しない。

3 文目は段 3 の敵対相談が見つけた欠陥への対応である。段 2 の plan は要求文そのものを指名入りの文へ
**置換**する案だったが、それだと 6 項目すべてが一つの述語の目的語のまま残り、この commit が
(i) の freeze 完了なのか末尾 2 項目の先行指名なのかが、置換箇所だけを読んだ人には判別できない。
置換をやめて追記に変え、固定した範囲を明示して閉じた。

## 凍結 bytes と consumer への影響 (実測)

この文書は `tools/check_docs.py` の `LIVING_DOCS` に「発効前は living」として登録されており、
**文書全体の bytes を固定する pin は無い。** 機械が bytes を固定しているのは §5.1.1 だけである。

- `p3_b4_analysis_prereg_consumer.py` は §5.1.1 の raw と semantic の 2 つの sha256 を pin する。
  切り出しは H4「5.1.1 分析契約の一括凍結」から次の level<=4 見出しの直前まで。
  追記は H4 より前なので対象 bytes は不変。**編集後に実測した raw sha256 は
  `0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30` で、pin 値と一致した。**
- `p3_b4_admission_record.py` は `## 5.` 行と `### 5.1` 行の間だけを §5 の表として解析し、
  両者が各 1 個でなければ fail-closed する。追記は `### 5.1` より後で、新しい見出し・
  code fence・HTML コメントを含まない。編集後も 3 見出しは各 1 個のまま。
- **文書全文を束縛する admission record は存在しない。** production module は record の
  repository path を driver 種別ごとの exact 3 path
  (`docs/phase3-b4-reflux-ablation-admission-record-{base,sort,trigger}.json`) に固定する。
  その 3 path は `git ls-tree -r HEAD` にも作業木にも 1 件も無い。
- **文書の全文 hash はどこにも作られない。** `p3_b4_analysis_path.py` の
  `_generate_analysis_source_closure_receipt` は受け取った全文 bytes を §5.1.1 の切り出しにだけ使い、
  その section hash だけを receipt へ載せる。`_SOURCE_CLOSURE_PATHS` の member は Python source 5 本で、
  文書は member でない。

安全な追記位置の条件は「`### 5.1` より後、かつ H4 `#### 5.1.1` の開始 byte より前」かつ
「新しい見出し・fence・HTML コメントを足さない」である。**「§5.1 本体ならどこでも安全」は誤りで、
親 brief のこの一般化は段 3 の相談が正しく突いた。**

## 実装しなかった real 所見 (ユーザーの裁定へ返す)

1. **§10 の残件記述が部分的に古くなる。** §10 は「残るのは (i) の先行 freeze — 候補集合…記入者と
   レビュー者 — であり、人間の指名を含むため AI が確定できない」と書く。本変更で記入者・レビュー者が
   確定したので、この**理由の説明**は不完全になる。ただし「(i) の先行 freeze が残る」という
   §10 の主張自体は真のままである (残り 4 項目が未固定)。ユーザーが対象を §5.1 と明示したため
   本 wave では触らない。
2. **レビュー者の履行を観測可能にするか。** 段 3 の相談は「確認時点・項目別確認・確認事実の記録」を
   足すべきだと主張した。D1266 は役割定義文の中身を裁定済みであり、これらの追加は非同値な義務の
   新設にあたる。足さない現状では、レビュー者の履行は外形上観測できない。
   これが D1266 が受容した制約の範囲内かどうかが論点である。

相談は「事前登録の要求」の指し先が一意でないとして (i) へ限定する対案も出したが、**採らなかった。**
限定は確認義務を狭める向きであり、正しさ側を緩める。D1266 の逐語 (最も広い読み) を採った。

## 検査

- `tools/check_docs.py`: rc=0 (`check_docs: 違反なし`)。編集前の baseline も rc=0。
- 焦点走 (`tools/run_tests.py` 経由): `test_p3_b4_analysis_prereg_consumer.py`、
  `test_p3_b4_admission_record.py`、`test_p3_b4_closed_critic.py` の **123 passed**。
- §5.1.1 の raw sha256 を編集後に実測し、実装の pin 値と一致することを確認した。
- 受入全走の結果は worklog に書く。

## 逐語

`verbatim/` に段 1 brief、段 2 plan、段 3 敵対相談 2 本、段 4 裁定を置く。
`s3-consult-a1-rejected.md` は段 3 相談 A の初回出力で、内容は完成していたが最終見出しの階層が
出力検査の要求と違ったため不採用になったものである。親の prompt が見出し階層を混ぜていたのが原因で、
階層を明示した prompt で再投入したのが `s3-consult-a2.md` である。
