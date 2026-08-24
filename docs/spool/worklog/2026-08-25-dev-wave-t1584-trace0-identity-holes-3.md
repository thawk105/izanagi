---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1584-trace0-identity-holes
seq: 3
title: [T-1584] TRACE=0前処理同一性検査の3穴を閉じ、正規化が旧拒否を消す退行を和集合で塞いだ (コード + docs、branch worktree-dev-wave-t1584-trace0-identity-holes)
---

## 本文

- D751 の3穴は実装前に probe で発火を実測した。穴1a (CMake間接供給) と穴1b (行継続 `#define`) は
  検出 false、穴2 (macro include operand 差替え) と穴3 (report 自己矛盾) は**実 checker が
  rc=0・`result=pass` を返す** end-to-end の false-green として確認した。穴1b は g++-12 が
  `#defi\`+改行+`ne MQLOCK 1` を `#define MQLOCK 1` と同一に解釈することも実測し、理論上の穴でないと確かめた。
- **実測が段 3 の設計提案を反転させた。** 敵対相談 2 本が提案した fail-closed 強化 5 件は、
  実 repo の母集合を測るとすべて実 repo を赤にした (未解決 macro 名の供給 call 29 件、
  raw string を含む供給 file 9 件 — trace ヘッダ自身を含む、未認識 output-producing command 31 件、
  bracket argument 1 件)。裁定で全件却下し、`{{D:unprovable-static-value-is-not-a-rejection}}` と
  「lexer の誤りは fail-closed で回避せず lexer を正す」原則に置き換えた。
- **本 wave の中心的な発見は3穴そのものではなく、塞ぐ過程で3回続けて起きた同型の退行である。**
  bracket-aware lexer、raw/logical 対応 gate、先頭 BOM 除去を足すたびに旧解析が拾っていた入力が
  受理側へ移った。3例とも実装子は受理集合を狭めたと自己申告し、既存テストも緑のままで、
  静的な敵対レビューだけが検出した。恒久対応は
  `{{D:normalization-must-union-old-view}}`、失敗型は `{{F:normalization-drops-old-rejection}}`。
- 診断文の往復で fix 巡を 2 つ消費した。件数 gate と対応 gate は同じ入力で同時に成立しうるため、
  先に評価した方の message だけを出す実装では、もう一方の診断を pin したテストが順に赤になった。
  入力はいずれの巡でも拒否されており、揺れたのは診断文だけである。DW-O16 の3巡上限に達したので
  親裁定で「拒否条件と同様に診断文も和集合にする」と決め、テストを1行も変えずに閉じた。
- **変異 probe が親と実装子の静的判定を2件覆した。** 期待 node を推論で書かず DW-M07 の
  全件 SURVIVED 期待 probe 巡を回したところ、両者が「単一理由性 OK」と判定した M6b が SURVIVED した。
  親自身が monotonicity view のループへ `set_property` を含めたため、主分岐を消しても旧 view が
  同じ helper を呼んで拒否していた。M11b も冗長 gate として SURVIVED した。
  実効 gate へ再照準した第2巡では SURVIVED 0 件になった。失敗型は
  `{{F:static-single-reason-judgment-masks-mutation}}`。
- 変異本走を1回捨てた。台帳は 25/25 KILLED で緑だったが、親が走行中に spool fragment を worktree へ
  書いたため wrapper の共有木事後検査が失敗した (rc=125)。台帳が緑でも wrapper の保証が壊れている
  以上採用せず、fragment を commit して tree を clean にしてから走らせ直した。
- 段 5 と段 6 の Codex 子は runner の queue preflight 障害で pytest を1件も実走できず、
  すべて「実装済み・未実走」と正直に申告した。テスト実測はすべて親が行った。
- **TRACE=0 の性能値は本 wave でも1件も生んでいない。** 閉じたのは検査が false-green を返すことで
  あって計測ではない。またこの checker が証明するのは D297 の保証だけで、規律1の「trace の完全除去」は
  **必要条件の一つ**にすぎない。両 commit に `#undef TRACE` / `#define TRACE 1` を置けば pass する
  ことを段 3 の敵対レンズが実証した。親 brief の成果物影響の記述を段 4 で訂正した。
- N1〜N20 のすべてが「旧 green を新 red にした」わけではない。N8・N9・N18 は修理前から reject され、
  N19 は旧実装に対象 helper が無い。旧 green → 新 red を実際に示すのは N1〜N7、N10〜N14、N16、N17、N20。
- g++-13 は本機に不在で未実測。g++-12 と g++-11 の2 compiler で rc=0 を確認した。

## 次の一手差分

### 完了

- [T-1584] D751 の3穴を修理し、各穴を単独発火させる負の対照を置いた。実装 commit は
  `336f4edb` / `5bfa7b9b` / `209c969e`。3穴に含まれない marker 分断 false-green も同時に閉じた。
  remaining: none
  base: f55368415ca6f6a225b7c40c9ff00cd5c62033ee20a8698f127dd93dcfe09668

### 新規

- {{T:mocc-trace0-report-proof-chain}} **P1・ユーザー裁定待ち**: pilot receipt が checker report を
  hash 束縛せず、report が proof chain に入らない。`tools/pegasus/mocc_trace_pilot.sh` は
  checker の rc しか見ず、final receipt と job-result は report の path・SHA-256・schema・guarantee を
  束縛しない。**TRACE=0 値を正式材料へ昇格させる前に必要。**
- {{T:trace-removal-beyond-preprocess-identity}} **P2・ユーザー裁定待ち**: この checker は D297 の
  保証だけを証明し trace の完全除去は証明しない。実 compile command・全 TU・link object・
  trace symbol/data・build receipt を結合する別防壁を設計するか、成果物側の文言を
  「必要条件の一つ」へ統一するか。
- {{T:has-include-semantics-and-toolchain-parity}} **P2・新規**: `__has_include` 族の意味は
  `-nostdinc` の checker と実 build の include path で真偽が変わりうる (digraph の lexical 拒否は
  本 wave で実装済み)。あわせて g++-13 / admission toolchain での実 pair 実測を行う。
- {{T:cmake-execution-semantics-absence-limit}} **P3・新規**: 解決不能な間接 CMake 値と実行意味
  (`if`/`else`、`foreach`、`function` 呼出し、`CACHE`/`PARENT_SCOPE`、eager expansion、変数鎖の
  深さ上限) の背後に registry macro が隠れうる限界。`{{D:unprovable-static-value-is-not-a-rejection}}`
  で docstring 明記としたが、別の証明手段を設計するかを裁定する。
