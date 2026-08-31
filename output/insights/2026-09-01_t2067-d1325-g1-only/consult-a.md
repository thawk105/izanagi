## 所見

### 1. 既存の g2 拒否枝を D1325 の成立点へ数えると、g2 の仕様を先取りする

- **対象:** brief:51-61、plan:13-24、plan:36-40、plan:58、plan:91-95、`s8b_ratified_freeze.py:3107-3110,3303-3309`
- **何が誤りか:** 親実測 3 の到達可能性を訂正したこと自体は正しい。しかし、`certificate-generation-scope` を「g1 のみ」の第 3 の成立点として記録すると、既存の launch certificate 用拒否枝を D1325 の選択・投影方針へ昇格させる。これは事実観測を越え、将来 g2 の full validation は拒否するという仕様を固定する読みになる。D1325 が固定したのは「今は g2 を設計しない」であり、「g2 を拒否する」ではない。
- **成果物への影響:** 本 wave が docs-only なら値と実行時受理集合は変わらない。一方、worklog の参照意味が変わり、将来 g2 を受理する変更が D1325 違反や退行と誤認される。現在の loader 受理と full-validation 拒否の差も、意図された恒久仕様として固定される。
- **親が採るべき対応:** 実測 3 の訂正は「HEAD `24014bdb259d971571f22b54a8f10a49352b825f` では先行 gate のため呼出しへ到達しない」に限定する。拒否枝を D1325 の成立点へ数えず、「本記録は g2 の受理・拒否・選択・投影を何も定義しない」と明記する。拒否を将来仕様にしたい場合だけ別の裁定パッケージへ返す。その場合の成果物影響は「将来 g2 の full-validation 受理集合を空に固定する」である。

### 2. 「3 箇所ですべて成立」は、現在は発火しない経路と恒真的な定数を保証へ昇格させている

- **対象:** brief:57-60、plan:9、plan:15-20、plan:66、plan:91-93、`s8b_holdout_freeze.py:52,1298-1305,2014-2018,2053-2056,2084`、`s8b_ratified_freeze.py:1399-1418,3107-3110`
- **何が誤りか:** 現 HEAD には generation、approval、active pointer、candidate の tracked artifact が無い。さらに `BUDGET_APPROVAL_SHA256` は `None` で、candidate builder は選択 identity より前の `:2018` で停止する。launch 側も active generation が無いため production artifact からは到達しない。`generation_number: 1` は g1 専用 builder が定数を書く構成であり、g2 入力を拒否する非恒真述語ではない。選択 helper 自体は generation 引数を持たない。
- **成果物への影響:** 現在の値・受理集合は変わらないが、「実装された条件付き検査」を「現に発火して守っている保証」と誤記する。将来 artifact が追加されたときの条件付き挙動を、現在観測済みの保証として引用できてしまう。
- **親が採るべき対応:** 「静的に呼出しと枝が存在する」「到達した場合に D1313(a) の拒否を行う」と限定する。「戻さない」は復元 authority と復元機構を追加しない裁定であり、削除攻撃を検知または阻止する保証ではない、と維持する。`generation_number: 1` は constructor の出力範囲であって独立した gate に数えない。

### 3. planned worklog に測定時点と非遡及性がなく、規律 7 上の誤読が残る

- **対象:** brief:17-27、brief:38-40、plan:32-45、plan:53-60、plan:84-86
- **何が誤りか:** brief は測定 commit を示すが、plan は worklog 本文へ commit と「過去 g1 を再判定しない」を必須化していない。「設計択一を閉じた」「追加保証は g1 限定」という圧縮表現だけでは、D1325 と現行コードにより既存 g1 成果物まで選択規則準拠へ昇格したと読める。これは規律 7 の当時判定と現行適合の分離に不足する。また「選択強制」は D1313(a) より広く、履歴上の最早 run や削除済み run まで含むように読める。
- **成果物への影響:** artifact bytes と実行時受理集合は変わらないが、worklog の参照を介して過去 g1 の判定が遡及的に強化されうる。docs 記録を後付けの正しさシグナルとして扱えば規律 3 にも触れる。
- **親が採るべき対応:** worklog に測定 commit、静的検査であること、過去 artifact の再判定や certified 昇格を行わないことを明記する。主張は D1313(a)(b)(c) をそのまま列挙または逐語参照し、「選択強制」の短縮語だけで済ませない。これなら規律 2 の gate 緩和も生じない。

### 4. (P1-1) の結論はよいが、「コード変更は何も変えない」という理由は誤り

- **対象:** brief:31-35、plan:47-51、plan:64-67、`s8b_holdout_freeze.py:2062-2077`
- **何が誤りか:** docs-only で足りることと、任意のコード変更が無影響であることは別である。`s8b_holdout_freeze.py` の bytes を変えると、future candidate の `generator.sha256` が変わる。generation gate や選択呼出しを変えれば受理集合も変わりうる。
- **成果物への影響:** 不要な holdout generator 編集は将来 candidate の generator 値と参照 hash を変更する。launch 側編集なら受理集合を変更しうる。
- **親が採るべき対応:** plan:66 の訂正を採用する。docs-only の理由は「D1325 が求めるのは設計択一の終端記録であり、現 wave に必要な実装差分が無い」とし、コード変更一般の無影響を理由にしない。

### 5. 元の (P1-2) は「実装しない」だけ正しく、「新事実として裁定へ返す」は誤り

- **対象:** brief:24-35、brief:51-61、plan:17-24、plan:67、`s8b_ratified_freeze.py:1054-1088,1252-1270,1298-1418,3073-3110,3303-3321,3548-3568`
- **何が誤りか:** 現コードでは g2 は `_launch_validate` の `:3107` で止まり、`:3305` の世代非依存な選択呼出しへ到達しない。したがって元の「選択が g2 へ伝播する」という新事実は存在せず、それを新しい次の一手や裁定事項にしてはならない。
- **成果物への影響:** 将来、現コードのまま妥当な g2 artifact だけが導入されると、一般世代の `resolve_active_generation` と `load_ratified_freeze` は g2 を静的に読みうる一方、投影 equality は省略される。`s8c_result_judge.py:2103-2159,2188-2205` のような load-only consumer は g2 の floor path/hash を参照できるが、`launch_validate` と `reverify_published_freeze` の g2 受理集合は空のままで、選択 identity は呼ばれない。将来、g2 対応として先行 gate だけを外せば、その時点で初めて世代非依存呼出しが g1 規則を g2 へ適用する。
- **親が採るべき対応:** 非対称の修正は実装せず、新規裁定にも返さない。現存する g2 artifact path または計測 ID が無いため `DW-G04` も実装を認めない。将来 g2 が実在した時点で D1325 どおり選択・投影・full validation を一体で設計する。今は既知の load-only 残余としてだけ維持する。

## 親 brief と plan のうち、検証して正しいと確認できた点

- `_official_earlier_floor_results` は現在存在する namespace を `s8b_holdout_freeze.py:1821` で列挙し、削除済み run の復元や不存在証明を行わない。plan の brief 行番号訂正は正しい。
- present な earlier run は適格性を再導出し、真なら選択集合へ加え、最小 run ID と selected を比較する。この条件付きの D1313(a) は実装されている。
- g1 の投影 equality は `s8b_ratified_freeze.py:1056-1085` に存在し、D1313(c) の範囲に一致する。
- 親実測 3 の到達可能性の結論は誤りで、brief の段 2 後訂正と plan の反証が正しい。
- historical reverify は selection identity を呼ばない。`result_type is LaunchValidatedFreeze` 条件は D1312 と一致する。
- D1241/D1313 の advisory/non-certifying 上限を維持し、T-2067 を完了でなく一部完了とする方針は正しい。
- docs-only とする結論、および plan が (P1-1) の過大な理由を退けた点は正しい。
- 実行時 gate、artifact、テスト期待値を変更しない限り、絶対規律 2 の緩和は生じない。

## 残る不確実性

- 検査は HEAD `24014bdb259d971571f22b54a8f10a49352b825f` の静的検査だけである。pytest、acceptance、実 artifact による発火確認は行っていない。
- 現 HEAD の tree には v2 generation、approval、active pointer、candidate、budget approval が無い。したがって production 発火については「未観測」であり、成功とも緑とも評価できない。
- 実際の worklog fragment はまだ無いため、D1/D3/D4 の所見は plan が指定する予定文言に対するものである。author が限定文を入れれば回避できる。
- repo 外バックアップ、人手による run 再配置、公開 API 外での `RatifiedFreeze` 直接構築は保証対象外である。

## 総括

最も重い欠陥は、既存の g2 拒否枝を D1325 の「g1 のみ」の成立点へ昇格させ、将来仕様を先取りする点である。  
次に重いのは、現在到達不能な candidate/launch 経路と g1 定数を「現に守る保証」として数える点である。  
親実測 3 の伝播結論は誤りであり、実装しない判断は正しいが、新規裁定事項として残してはならない。  
段 4 の推奨択一は、docs-only を維持しつつ「3 つの成立点」を撤回し、D1325 を governance 上の終端だけとして記録する案である。  
拒否枝を g2 の恒久仕様として残したい場合のみ別裁定へ返し、本 wave では実装しない。