# [T-1584] TRACE=0 前処理同一性検査の3穴を閉じた — 塞いだ先で 3 回続けて「旧拒否が静かに消えた」

- 日付: 2026-08-24
- wave: dev-wave-t1584-trace0-identity-holes (branch `worktree-dev-wave-t1584-trace0-identity-holes`)
- 起点の裁定: D751 (ユーザー裁定。3穴を正式計測前に同一 wave で修理する)
- 一次資料: `output/insights/2026-08-23_t1506-mocc-trace0-unblock.md` §4、
  `docs/archive/worklog-phase3-0823-872.md` entry 872
- 関連既裁定: D297 (保証の名前)、D722 (owner protocol define と commit 由来の不在証明)、
  D723 (証明できない限界を明記する)
- 成果物 commit: `336f4edb` (実装)、`5bfa7b9b` (fix 第 1 巡)、`209c969e` (和集合化)

## 1. 3穴は「今日実際に発火する」ことを先に実測した

D751 は 3 穴を挙げていたが、いずれも「出うる」という記述だった。実装前に probe
(`<job>/probe-three-holes.py`、repo 外) で発火を実測した。

| 穴 | 実測 |
|---|---|
| (1a) CMake 間接供給 `set(MODE MQLOCK)` + `${MODE}` | 検出 **false** (直接 literal は true) |
| (1b) 行継続 `#defi\`+改行+`ne MQLOCK 1` | g++-12 が `#define MQLOCK 1` と**同一に解釈** (穴は理論でなく実在)、現行 regex は検出 **false** |
| (2) macro include operand 差替え | 実 checker が **rc=0・`result=pass`** = false-green を end-to-end で確認 |
| (3) report 自己矛盾 | 実 checker が rc=0、activity hash `af03305d…` vs `0c83b55f…` で不一致なのに `identical: true` |

**穴3 の到達可能性には限定がある。** 実 pair (`511c9538`→`058d0c4e`) は追加 include が
最終 index (`new_include_index: 10`、既存 include 10 本) のため既存 marker の番号が動かず、
activity hash は一致して自己矛盾は顕在化しない。顕在化するのは追加 index が最終でない形で、
`_mocc_trace_include_addition_index` が任意 index を許すため到達可能である。
段 6 の敵対レンズはこの限定を独立に検証し「正しい」「親は『閉じなくてよい』へ滑らせていない」と
判定した。

## 2. 実測が設計を反転させた — fail-closed 強化 5 件を却下

段 3 の敵対相談 2 本は「未解決 CMake 値を fail-closed にする」方向の強化を複数提案した。
親が実 repo の母集合を測った結果 (`<job>/probe-reachability.json`、supply file 1088 件)、
**そのすべてが実 repo を赤にする**ことが確定した。

| 提案された fail-closed 述語 | 実 repo 母集合 | 裁定 |
|---|---|---|
| 未解決 macro 名を持つ供給 token を拒否 | **29 件** | 却下 |
| repo 内 `set()` 由来で解決不能なら拒否 | shirakami `CompileOptions.cmake:77` が該当 | 却下 |
| 供給 file に raw string があれば拒否 | **9 件** (`include/trace.hh` を含む) | 却下 |
| CMake bracket argument があれば拒否 | 1 件 (実体は quoted 内の C++ 属性) | 却下 |
| 未認識 output-producing command があれば拒否 | 31 件 | 却下 |
| `#import` / digraph `%:` を拒否 | **0 件** | 採用 |
| marker prefix を含む source を拒否 | **0 件** | 採用 |

代わりに立てた原則は 2 つである。

1. **新しい拒否は「静的に証明できたときだけ」の形にする。** 証明できない値は
   「供給と主張しない」に倒し、拒否理由にしない。残る限界は D723 と同型に docstring へ明記する。
2. **lexer の誤りは fail-closed で回避せず lexer を正す。** raw string と bracket argument は
   lexer を正確にすると「見えていなかった供給 call が見える」= 拒否が増える方向にだけ効き、
   実 repo を赤にしない。

## 3. 本 wave の中心的な発見 — 正規化を足すたびに旧拒否が静かに消える

**同型の退行が 3 例そろった。**

| 例 | 足した正規化 | 消えた旧拒否 | 検出者 |
|---|---|---|---|
| 1 | CMake bracket-aware lexer | bracket 内の見かけの供給 call を拾う旧走査 | 段 6 敵対レビュー |
| 2 | raw/logical の位置・綴り対応 gate | `len(raw) != len(logical)` の件数拒否 | 段 6 焦点再レビュー |
| 3 | 先頭 UTF-8 BOM の除去 | BOM 有無の差による include 行列の不一致拒否 | 段 6 焦点再レビュー |

いずれも「より正確な解析へ置き換えた」つもりの変更が、**旧解析が偶然拾っていた入力を
受理側へ移した**ものである。正確さの向上と受理集合の単調性は独立であり、
前者を理由に後者を失ってよい理由はない。

**恒久対応: 正規化を足すときは旧 view を置き換えず必ず和集合にする。**
新旧どちらかの view が拒否したら拒否する。C/C++ の phase-2 view / 物理行 view では
最初からこの形を採っていたが、他の 3 面へ一様に適用していなかった。

さらに**診断文も和集合にする**。両 gate が同時に成立する入力で先に評価した方の message だけを
出すと、もう一方の診断を pin したテストが赤になる (実走で 3 nodeid が順に露見した)。
入力はいずれの巡でも拒否されており、揺れたのは診断文だけである。両方の理由句を逐語で含む
1 つの `CheckError` にすることで、テストの期待値を 1 行も変えずに閉じた。

## 4. 修理の内容

### 穴1 (不在証明)

- `set()` / `string(CONCAT)` / `list(APPEND)` の literal 引数だけを source order で静的解決し、
  三値 (`SUPPLIES` / `DOES_NOT_SUPPLY` / `UNPROVABLE_REPO_VALUE`) に分類する。
  **`UNPROVABLE_REPO_VALUE` は拒否理由にしない** (§2 の原則 1)。
- 行継続は translation phase 2 の順序に合わせ comment 除去の**前**に適用し、
  phase-2 view と物理行 view の**和集合**で供給を探す。
- 供給 lexer を raw string 対応、CMake lexer を bracket argument 対応にする
  (quote 内の `[[` は開かない)。いずれも旧 view との和集合。
- `set_property(... COMPILE_DEFINITIONS ...)`、空白分離 `-D MQLOCK`、digraph `%:define`、
  先頭 BOM を認識面へ足す (実 repo 母集合はすべて 0 件)。
- checkout view と commit view を**別 namespace** で解析する。同一 logical path が
  両 view にあるのは重複構文ではない (これを混ぜると実 repo が赤になる)。
- `_repo_supply_files` の列挙は 1 回だけ行って再利用する (subprocess 倍率 1.00)。

### 穴2 (include operand)

operand が literal header token でない `#include`、`#import`、digraph、comment 形成 directive、
line-spliced include を比較前に拒否する。**operand macro の実効値解決は採らない** —
正しく行うには先行 define、command-line define、条件分岐、関数形式 macro、context ごとの
展開結果まで preprocessor と同じ規則で扱う必要があり、marker 方式へ部分的な展開器を足す方が危険である。
実 repo に該当形は 0 件だが、負の対照が発火を証明する。

### 穴3 (report 自己矛盾)

`identical` を**元値と digest の両方**から算出し、両者が食い違えば fail-closed で拒否する
(hash 等値だけに gate を寄せない)。mocc 例外は `identical: false` と
`policy_comparison.accepted: true` を併記して自己矛盾を解消し、old/new 双方の
`active_markers` を記録する。非互換な report 変更のため schema を v2 へ上げた。

### 3穴に含まれないが同時に閉じたもの

marker 名を行継続で分断して `\b<marker>\b` の衝突検査を抜け、source 側 `#define` が marker を
`0` へ再定義する false-green (段 3 敵対レンズが検出)。include を活性から非活性へ移した pair が
`result: pass` を得る形であり、穴2 と同じ include 同一性の面にある一行違いの兄弟である。
これを開けたまま穴2 だけを閉じると恒真な保証になるため、同 wave で閉じた。

## 5. 変異検査 — probe が親の静的判定を 2 件覆した

期待 node を推論で書かず、`DW-M07` に従って全件 SURVIVED 期待の probe 巡で観測 node を集めた。

第 1 巡 (23 変異、commit `5bfa7b9b`、baseline PASSED) の結果:

- **M6b (`set_property` 主分岐の除去) が SURVIVED。** 親が monotonicity view のループへ
  `set_property` を含めたため、主分岐を消しても旧 view 側が同じ helper を呼んで拒否していた。
  親も fix 子も静的には「単一理由性 OK」と判定していた。**probe を省けば誤って KILLED として
  台帳へ載せていた。** 実効 gate は両経路が共用する `_set_property_compile_definition_tokens`。
- **M11b (line-spliced include 専用拒否) が SURVIVED。** 対応 gate が先に拒否する冗長 gate。
  段 6 の敵対レビューが静的に予告していた形と一致する。`DW-M03` に従い単独変異の証拠から外した。
- M3 は 6 node、M18 は 8 node を落とす過剰決定であることも実測で確定した。
  M18 の期待集合には焦点再レビューが予告した symlink node と列挙 1 回の meta-test が入る。

## 6. 正直な留保

- **TRACE=0 の性能値は本 wave でも 1 件も生んでいない。** 本 wave が閉じたのは
  「検査が false-green を返す」ことであって、計測そのものではない。
- **この checker は「trace の完全除去」を証明しない。** 証明するのは D297 が定義した保証
  (選定 macro context における TRACE=0 正規化 preprocess 出力の同一性、および include 活性の同一性)
  だけである。それは規律 1 の**必要条件の一つ**であって十分条件ではない。実際、両 commit に
  `#undef TRACE` / `#define TRACE 1` を置けば checker は pass する (段 3 敵対レンズが実証)。
  完全除去の証明は別防壁 (実 compile command、全 TU、link object、trace symbol/data、
  build receipt) の領分である。
- **N1〜N19 のすべてが「旧 green を新 red にした」わけではない。** N8 (物理行 view)、
  N9 (generator guard)、N18 (残存 marker 写像) は修理前から reject され、N19 は旧実装に
  `_comparison_evidence` 自体が無い。これらは回帰 guard・単調性テスト・変異 guard・unit test であり、
  旧 green → 新 red を実際に示すのは N1〜N7、N10〜N14、N16、N17、N20 である。
- **CMake の実行意味は追っていない。** `if`/`else` の実行分岐、`foreach`、`function` 呼出し、
  `CACHE` / `PARENT_SCOPE` の実行時値、CMake の eager expansion と本実装の遅延展開の差
  (`set(A MQLOCK); set(B ${A}); set(A ${B})` は実 CMake では `MQLOCK`、本実装では循環)、
  変数鎖の深さ上限。これらの背後に registry macro が隠れうる。本分類が証明するのは
  「repo text に認識済みの当該供給源が無い」ことだけで、実 build の全 define の不在ではない。
  docstring へ明記した。
- **g++-13 は本機に不在で未実測。** g++-12 と g++-11 の 2 compiler で rc=0 を確認した。
  D297 自身が「複数 compiler で走らせ admission toolchain と同一とは主張しない」と述べている。
- **checker report は proof chain に入っていない。** `tools/pegasus/mocc_trace_pilot.sh` は
  checker の rc しか見ず、final receipt と job-result は report を hash 束縛しない。
  本 wave の report 修理は attempt artifact としては有効だが、「正式 proof chain まで閉じた」とは
  書けない。裁定パッケージ R1 として返す。

## 7. ユーザー裁定へ返す (scope 外の real 所見)

- **R1**: pilot receipt が checker report を hash 束縛せず、report が proof chain に入らない。
  **TRACE=0 値を正式材料へ昇格させる前に必要。**
- **R2**: この checker は D297 の保証だけを証明し trace の完全除去は証明しない。
  別防壁を設計するか、成果物側の文言を「必要条件の一つ」に統一するか。
- **R3**: `__has_include` 族の意味 (digraph の lexical 拒否は本 wave で実装したが、
  `-nostdinc` の checker と実 build の include path で真偽が変わりうる問題は残る)。
- **R4**: g++-13 / admission toolchain での実 pair 実測。
- **R5**: 解決不能な間接 CMake 値と CMake の実行意味の背後に registry macro が隠れうる限界。
  D723 と同型に「証明できない限界を明記する」で閉じるか、別の証明手段を設計するか。

## 8. 一次資料の所在

job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1584-trace0-identity-holes/` に保全。

- `probe-three-holes.py` / `probe-results.json` — 3穴の発火実測
- `probe-reachability.py` / `probe-reachability.json` — 段 4 の母集合実測 (fail-closed 却下の根拠)
- `probe-s6-reachability.py` / `probe-s6-reachability.json` — 段 6 の母集合実測
- `s1-brief.md` / `s1-brief-addendum.md` — 段 1 brief と追補
- `s2-plan.md` — 段 2 プラン
- `s3-consult-sol.md` / `s3-consult-luna.md` / `s3-luna-digest.md` — 段 3 敵対相談
- `s4-ruling.md` — 段 4 裁定 (負の対照と変異事前登録の正本)
- `s5-author.md` / `s5-implementation.diff` — 段 5 実装
- `s6-review-sol.md` / `s6-review-luna.md` — 段 6 敵対レビュー
- `s6-fix-ruling.md` / `s6-fix.md` / `s6-fix.diff` — fix 第 1 巡
- `s6-focus2.md` — 焦点再レビュー
- `s6-fix2-ruling.md` / `s6-fix2.md` / `s6-fix3.md` / `s6-fix4.md` — fix 第 2〜4 巡
- `mutation-spec-probe.json` / `mutation-ledger-probe.json` / `mutation-probe-digest.md` — 変異 probe 第 1 巡
- `baseline-checker-full.json` / `final-checker-g12.json` / `final-checker-g11.json` — 実 repo checker
