静的監査のみです。pytest・`check_docs.py` の実走はしていません。

1. 既存テストの巻き添え

**refuted** — 新 lint で既存負例が赤くなる根拠はない。

`_build_min_repo()` は `_SYNTHETIC_CLEANUP_COMMAND` をそのまま command に書く (`test_check_docs.py:318`, `:514`, `:525`)。その逐語コピーには `F26` と `docs/failures.md` の同一行がある (`test_check_docs.py:355`)。

また `_assert_cleanup_digest_violation()` は違反件数を 1 件に固定している (`test_check_docs.py:6599`, `:6602`)。既存の command 負例は class 表記、H2 表記、末尾 fence だけを変え、edge 行を変えない (`test_check_docs.py:6627`, `:6652`, `:6664`, `:6676`, `:6688`)。したがって新 finding は増えず、段 2 の見落としではない (`s2-out.md:111`, `:121`)。

2. pin 閉包

**refuted** — 実 command の 3 箇所の pin を同期する必要はない。`CLEANUP_COMMAND_SHA256` は `tools/check_docs.py:389`、test 側定数は `test_check_docs.py:264`、逐語 fixture は `test_check_docs.py:318` にある。test は両者の一致を固定している (`test_check_docs.py:6539`, `:6545`)。

**real** — ただし新しい負例で合成 command を改変する場合、tmp repo にコピーされた `tools/check_docs.py` の digest だけは一時的に再束縛する必要がある。更新しなければ digest finding と edge finding の 2 件になり、helper の 1 件 assert と衝突する (`test_check_docs.py:6602`, `s2-out.md:99`, `:109`)。恒久定数・逐語 fixture は変更してはならない。

3. 文書予算と F173 再演

**refuted** — 提示された 2 行は現行 2 行と UTF-8 で 239 bytes、行文字数は 62/59 であり、`TextLimit(6_000, 100)` (`tools/check_docs.py:173`, `:174`) に収まる。現行の予算は `docs/skill-self-improvement.md:83`, `:84` にある。

削除語も唯一の到達手段ではない。byte・最長行は同じ文書の `:46`、実検査は `tools/check_docs.py:4016`, `:4024`、方針は `docs/decisions.md:3741` に残る。「lint に固定せず」も `docs/decisions.md:10647` に残り、F173 禁止規則も `docs/skill-self-improvement.md:49`, `:50` に残る。したがって F173 の再演だと断定する所見は refuted。

**real** — ただし提示文案は R1 を満たさない。brief は呼称を「住所 (address edge) の構造 lint」に固定し、効能を非協調 drift 検出・意図顕在化、trust root を人間レビューと要求している (`brief.md:8`, `:16`, `:17`)。提示文案の「住所 (到達 edge) の構造」には exact 呼称・`lint`・効能語がない。段 2 案 C はこの語を含む byte 中立案だった (`s2-out.md:167`, `:170`, `:171`, `:174`)。

4. routing と重複

**refuted** — 3 分割の考え方自体は routing 規則に合う。decisions は採用理由、skill 文書は実行契約、failures は事象・原因・恒久対応を担う (`docs/skill-self-improvement.md:24`, `:26`, `:36`)。

**real** — 現行 P3 は R1 を R2 の skill 文書だけで済ませるとしており (`brief.md:62`, `:64`)、新 D へ R1 を置く方針と矛盾する。さらに新 D が効能・trust root を書き、skill の提示文案も「敵対監査と人間レビュー」を書けば、R1 が二重化する。既存 D227 も同じ境界を説明している (`docs/decisions.md:10616`, `:10628`, `:10647`)。

D は R1 の採用理由だけ、skill は pin/構造契約だけ、F173 は事故と訂正だけに分離すべきである。

5. F173 恒久対応

**real** — 現在の F173 の

> 機械化は `docs/dev-wave/**` の byte 予算に阻まれており、段 8 の改善候補として残す。

という記述 (`docs/failures.md:4404`) は、この wave の実装形には当たらない。

edge lint の実装面は `tools/check_docs.py` の command guard (`tools/check_docs.py:3887`, `:4072`) であり、`TextLimit` の対象は command と skill 文書 (`tools/check_docs.py:168`, `:174`) である。command 本文の byte も 3959/4000 のまま (`docs/failures.md:4403`)。

最小訂正案は次の 1 文への置換。

`この種の edge lint は tools/check_docs.py 側に置けるため、docs/dev-wave/** の byte 予算には阻まれない。`

6. 安い代替

**real** — F173 そのものについては、既存の `DW-O16` 焦点再レビューが実際に捕捉していると package 自身が記録している (`package.md:110`, `:117`)。`DW-O16` は人手レビュー手順であり (`docs/dev-wave/operations.md:84`, `:86`)、今回の事故を止める安い既存経路ではある。

**speculative** — ただし、それが新 lint と同じ将来変異全体への決定的検出力を持つとは静的には証明できない。既存の自動検査は file 全体の literal 存在 (`tools/check_docs.py:4103`, `:4129`) や archive 名の到達性 (`tools/check_docs.py:4697`) であり、同一可視行の共起検査ではない。よって「同じ自動検出力」の代替なしという結論は維持されるが、DW-O16 を代替候補から外す根拠は弱い。

7. `DW-G05`

**refuted（成果物単位）** — 新 finding は command guard の `findings` に追加され (`tools/check_docs.py:4559`)、最終的に `check_docs` の rc だけを変える (`tools/check_docs.py:4758`)。certified 選択・レポート・試行台帳の値や参照を直接読む経路ではない。`DW-G05` の対象もその 3 種類に限定される (`docs/dev-wave/core.md:65`, `:67`)。

**real（無限定の表現）** — 変わるのは AI 作業手順と command の受理集合である。したがって「受理集合は変わらない」とだけ書くのは誤りで、package のいう「AI 作業手順の受理集合だけが変わる」(`package.md:150`, `:152`) と限定すべきである。

8. 過剰実装

**refuted** — 段 2 プランは専用関数・新台帳・新 gate を作らず、既存 command loop に限定している (`s2-out.md:3`, `:32`)。F51、helper path、Skill 側、path 実在性、全 F 番号到達性も明示的に除外されている (`brief.md:31`, `:32`, `:33`; `package.md:137`, `:143`)。

**real** — 段 2 の最終推奨は案 B で、241 bytes・現行比 +2 bytes (`s2-out.md:155`, `:162`, `:165`)。親の R2 は byte 中立が条件なので、案 Cへ差し替えるか、文案を再裁定する必要がある。また F173 修正を実施するなら、R4 の「worklog に backlog と記録 בלבד」(`brief.md:25`) からの scope 変更を明示すべきである。

最小修正案は、R1 の所有先を D か skill の一方に固定し、byte 中立の案 C相当へ統一し、tmp checker の pin だけを負例内で再束縛し、F173:4404 を訂正すること。

## 総括

NO-GO

既存負例の巻き添えと実 command の pin 変更は起きない。  
一方、R1 呼称・効能の欠落、案 B の +2 bytes、F173 の誤記、routing 所有の曖昧さは修正必須。  
この報告は静的検査のみで、pytest 実走結果は含まない。