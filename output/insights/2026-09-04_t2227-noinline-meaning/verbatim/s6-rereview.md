## 対応表 (所見 → closed / partial / regressed)

| 所見 | 判定 | 根拠 |
|---|---|---|
| Review A must-fix: insight README、D1490 補遺、worklog fragment 欠落 | partial | fix は指示どおり3 literal限定で、記録類は未変更。親統合時の対応が残る。 |
| Review A nit: `.git` gitfile の直接検査なし | partial | 段5の検査は未変更。悪化もない。 |
| Review A nit: M3 killer の過大申告 | partial | `s5-author.md` は未変更。fix report は過大申告を繰り返していない。 |
| Review B must-fix | closed | 元レビューに must-fix なし。今回も新規回帰なし。 |
| Review B nit: 既存8 macro の `#if` 検査弱化 | partial | 対象検査は未変更。 |
| Review B nit: A-2 undeclared-message assert の非独立性 | partial | 対象検査は未変更。 |
| Review B nit: s1 raw/floor の直接 factory coverage 不足 | partial | 対象検査は未変更。 |
| Review B nit: t1683 値1 coverage と直接構築の識別不足 | partial | 対象検査は未変更。 |
| Review B nit: fixture の full-file hash・行番号波及 | closed | fix は fixture を変更せず、親の焦点走で fixture 起因の赤は報告されていない。 |
| Review B nit: configure 増分が見積りを2回超過 | partial | 実装と test 構成は未変更。 |
| Review B nit: M7/M8/M9 の個別 assert が独立 killer でない | partial | 各 node 全体では殺せる状態のまま。 |
| Review B nit: 非配線 driver と成果物の独立照合不足 | partial | fix の許可範囲外で未変更。Review A の記録 must-fix と連動する。 |
| 赤1: approved fixture の materializer SHA不一致 | closed | s1 全体の再計算値 `049642ca067d93b046df66b14ddfdda3782bb06c830f2803c71e0e60e42f316d` と literal が一致。 |
| 赤2: `PIN_GATE_SPEC_RAW` と SHA literal の不一致 | closed | 再計算値と `PIN_GATE_SPEC_SHA256` がともに `58190f7b402ea5a72d19e86e38d63ef2941e3281d1617a4a8ff986c2e4769f8e`。 |
| 赤3: s1 build sink 行番号 pin | closed | ASTでも `run_role` 内の唯一の `pipeline.evaluate(` は1219行。literalも1219。 |

## must-fix

- fix 子に新規 must-fix はない。差分は2 test fileの3 literal置換だけで、段5差分とs1本体には触れていない。
- 親統合に残る must-fixはReview Aの記録3点。未対応だと、対照値方式の決定根拠、非配線 driver、既受理成果物の走査範囲を指す正本参照が欠落する。

## nit

- 新規 nit はない。未解消の既存 nit は対応表の partial 各行のとおりで、今回のfixによる悪化は見つからない。

## 総括

fix は親の指示どおりで、焦点3件は静的には閉じている。

2種の同一性 pin は、審査済みのs1変更後のbytesへ固定値を追随させただけで、動的計算や検査緩和には変わっていない。今後s1が未審査で変われば再び不一致になるため、pinの目的は維持される。

他generator 4件のliteralは現ファイルhashとすべて一致。旧s1 hashと旧spec hashの残存参照も、同worktreeの非output領域では見つからなかった。`PIN_GATE_SCHEDULE_SHA256`、approved/subset schedule pinは不変で、schedule hashはschedule objectだけから導出されるため、materializer hash更新から波及する経路はない。

pytestは実行していない。判定は差分、AST、`hashlib`による静的検査に基づく。