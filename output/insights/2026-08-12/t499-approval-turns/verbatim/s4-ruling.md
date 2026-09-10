# 段 4 裁定 — [T-499] 凍結・承認手番 (A)(B)

## 裁定 (親)

**(A)(B) とも実施しない。新事実付きでユーザー再裁定へ返す** (`DW-S04` の「止めるときも親が
不採用にせず、新事実付きのユーザー再裁定待ちへ戻す」に従う)。段 5・6 を飛ばし `4→7→8→9`。

## 所見の real / refuted 裁定

| # | 所見 | 出所 | 裁定 | 採否 |
|---|---|---|---|---|
| 1 | reviewed spec / v2 世代 / budget approval は全 126 ref・dangling commit・全 worktree・job 保存域のどこにも存在しない | レンズ A | **real** (親検算: `git ls-files`、`grep -rn SPEC_REL`) | 採用 |
| 2 | docs / insights 内の JSON は schema 例であり承認済み artifact ではない | レンズ A | real | 採用 |
| 3 | `PIN_GATE_SPEC_RAW` や fixture の合成物は独立 golden で、実測・承認の証拠でない | レンズ A | real | 採用 |
| 4 | budget 数値も official floor も「あとは記入するだけ」ではない | レンズ A | real (親検算: `s8b_holdout_freeze.py:49,1161-1163`、`phase3.md:118-123`) | 採用 |
| 5 | 「spec の書き手が存在しない」は production 限定なら正しく、一般命題としては誤り (test helper は arbitrary root へ設置できる) | レンズ A | real | 採用・親の文言を訂正 |
| 6 | 「設置は即赤」は現行 root の schema v1 限定。D302 は将来の正式な再発行まで永久禁止していない | レンズ A | real | 採用・親の文言を訂正 |
| 7 | 「AI は approval commit を作れない」は広すぎる。検査は actor の身元でなく逐語 trailer | レンズ A・B が独立に一致 | **real** (親検算: `s8b_ratified_freeze.py:524-547`) | 採用・**親の当初主張を撤回** |
| 8 | D328 を (B) の独立 blocker とする親の補強は成立しない | レンズ A・B が独立に一致 | **real** | 採用・**親の当初主張を撤回** |
| 9 | 別 wave の敵対相談が [T-499] A/B を D328 の**明示的 keep 集合**へ入れるよう要求済み | レンズ A | **real** (親検算: `output/insights/2026-08-12_freeze-chain-hold-sweep/verbatim/s3-consult-sol.md:110-120`) | 採用 |
| 10 | 現行実装は構造層と内容同一性検証を分離しきれていない (`load_ratified_freeze` → `_verify_generation_semantics`) | レンズ B | real (親検算: `s8b_ratified_freeze.py:1315-1327`) | 採用・ただし所見 9 により**択一にはしない**。発効時の確認事項として記録 |
| 11 | hash 記入だけを「承認完了」と書いてはならない (D302: hash は識別子にすぎず承認は内容の再導出を伴う) | レンズ B | real | 採用 |
| 12 | 返却パッケージに選択肢・担当・発火条件が不足 | レンズ B | real | 採用 |
| 13 | 今日 AI が正当に完了できるのは docs の readiness 記録と D328 判定の訂正のみ。artifact 側にはない | レンズ A | real | 採用 = 本 wave の scope |

## 親が撤回する 2 つの主張 (正直に記録する)

段 1 brief で親は次を実施不能の根拠に挙げたが、**どちらも誤りだったので撤回する**。

1. **「AI は承認 commit を作れない」**: `_assert_user_commit` が見るのは非 merge・逐語
   `AI-Agent: none`・H 祖先性であり、内容を誰が選んだかではない。ユーザーが exact bytes を
   確定した後の機械的な Git 代行なら、provenance 規約上も `AI-Agent: none` が正当。
   **今回使えないのは、その exact bytes が無く、AI が承認判断をすれば実質的関与になるから**であって、
   機構が AI を排除しているからではない。
2. **「(B) は D328 と衝突する」**: D328 は正しさゲートと admission を明示的に対象外としており、
   承認連鎖の構造検証はそこに入る。さらに別 wave の敵対相談は (A)(B) を**保留してはいけない
   keep 集合**へ入れるよう要求している。よって D328 は (B) の blocker ではなく、
   むしろ (A)(B) の fail-closed は保ち続けるべき正しさ境界である。

## 実施不能の決め手 (訂正後)

- **(A)**: reviewed bytes と、その内容である研究設計値 (`n` / master seed / block size /
  campaign ID 等) が未確定のまま `APPROVED_SPEC_SHA256 = None` であること。
- **(B)**: budget pin / production official floor result / canonical generation record の
  **三者不在**。provenance と D328 は決め手ではない。

## 新事実の既記録性の確認 (`DW-S04` の要求)

`output/s8b-oracle-spec/` 等の不在は 2026-08-11 の insight
(`output/insights/2026-08-11_t804-spec-sha256/brief.md:45-46`) に既に記録がある。
しかし**第 5 束の委任時点の裁定文と手番確定リストには反映されておらず**、リストは
「candidate spec の内容確認 → canonical path への設置 → hash 記入の 3 手」と、
candidate が既に存在する前提で書かれていた。よって委任者から見て未見の新事実として扱う。

## 変異事前登録 (`DW-M01`)

**免除。** `DW-S04` の「免除は『実装しない』裁定済みかつ実装差分ゼロの wave の変異 matrix だけ」に
該当する。本 wave の成果物は docs のみで実装面 diff はゼロ。

## 受入の扱い

`DW-S04` は受入全走を免除しない。段 7 の記録前に `git diff --name-only` で docs 限定を判定し、
docs を対象にする nodeid の実在を確認して実走要否を決め、証拠を worklog へ 1 行残す。

## 成果物

- worklog fragment 1 本 (事実・撤回 2 件・裁定 2 問)。
- 裁定パッケージを repo 外 inbox へ控え (`land しない場合でも母集合から落とさないため`)。
- decisions fragment は書かない (新しい設計判断ではなく、既裁定の前提が未成立という事実報告)。
