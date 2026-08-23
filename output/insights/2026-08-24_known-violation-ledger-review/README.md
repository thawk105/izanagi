# known-violation 台帳 53 件の全数監査 (2026-08-24)

wave: `dev-wave-known-violation-review-20260823` / base main `5a4cbfa8`。
**実装差分ゼロ。撤去件数 0。この wave は「消せない」ことを確定させた監査である。**

受入全走 1 回目が main 側の赤 (F434 再発) を掘り当てたため一度は自分で修復したが、
別セッションが先に同じ赤を main へ着地させていた (`3876fbe8`、2026-08-24 00:48 JST) ため、
自分の修復は落として main 側を採った。最終的な実装差分はゼロである。

一次資料は `verbatim/` に凍結した。実測スクリプトは `verbatim/measurement-scripts.md`。

## 依頼と答え

ユーザーの問いは 3 つあった。

**1. known-violation は育っていく一方か。** — **はい。**

各 blob の `KNOWN_PROVENANCE_VIOLATIONS` tuple を `ast` で構文解析し、`--first-parent` で
main の本線だけを追った。件数の変化点は**増加 20 回・減少 2 回**。
意味のある減少は 1 回だけである。

| 時刻 | commit | 件数 | 増減 |
|---|---|---:|---:|
| 2026-08-21T18:24 | `5f1c0d6ccd` | 53 | +6 |
| 2026-08-21T22:49 | `e0ac92775c` | **34** | **−19** (T-1479 の checker 是正) |
| 2026-08-22T08:50 | `4c03b959a7` | 38 | −1 |
| 2026-08-23T19:29 | `bc927d03c4` | **53** | +7 (元の水準へ復帰) |

**−19 の是正は 44.7 時間で完全に食い潰された。34→53 は約 10 件/日。**
生成器を止めずに台帳だけ減らしても 2 日と持たない、という直接の実測である。

**2. 0 件にできるか。** — **現行契約では不可能。AI 側の作業で消せる entry は 1 件も無い。**

**3. テストが間違っている箇所を直せるか。** — **直せる箇所は無かった。**
親と段 2 の子が独立に到達した是正案は、段 3 の敵対レンズが反例で倒した。

## 53 件の全数分類 (訂正後)

53 findings / **52 unique commits** (`649fe5a060` は 1 commit に 2 finding)。

| 生成器 | 件数 | 消せるか |
|---|---:|---|
| G1 trailer の綴り誤り (2026-08-09 の単一事故、literal 全件同一) | 22 | 不可 (履歴不変) |
| G2 role の綴り誤り (`role=fix`) | 1 | 不可 |
| G3 `--no-edit` merge で trailer 完全欠落 | 8 | 不可 |
| G4 trailer 完全欠落 (revert / ユーザー直接 commit) | 2 | 不可 |
| G4b trailer block の配置誤り | 1 | 不可 |
| G5 台帳自身の競合を親が手解決した merge | 11 | 不可 (案 A 却下) |
| G6 manager が実装面を直接 commit | 8 | 不可 |

G6 の 8 件の内訳: 解析 script を `output/insights/` へ置いたため実装面判定に当たった 3 件、
submodule gitlink の前進 1 件、台帳登録 commit そのもの 2 件、その他の直接 commit 2 件。

## なぜ 49 件が不可逆なのか

known-violation は「過去の commit がその時点で有効だった規約に違反していた」という事実の記録で
あり、commit message を書き換えずに事実を消す手段が無い。履歴の書き換えは禁止されている。

**legacy 免除の仮説は反証した。** 最大の塊である G1 の 22 件は trailer literal が全件同一
(`product=claude; model=claude-opus-5[1m]; reasoning=high; role=orchestrator`) で、
不適合は model の角括弧と `role=orchestrator` の 2 点である。当初は「規則が後から出来たのでは」と
疑ったが、値の文字集合規則 `IDENT` と role の許可集合はいずれも checker 導入 commit
`50c1ef4e` (2026-07-14) から在り、`docs/ai-provenance.md` も違反 commit `f277efd446`
(2026-08-08) の時点で同じ本文だった。**後付け規則の被害ではなく真の違反である。**

遡及訂正の経路も全部潰した。

- `docs/provenance/correction.md` の `PR-C01` (`AI-Agent-Correction`) が唯一の遡及訂正機構だが、
  「一般 allowlist・設定・CLI 免除へ拡張しない。この枠は `6d7141dc` で消費済みであり、
  新しい担い手を追加してはならない」と明記されている。
- `AI-Agent-Waiver` は commit 自身の trailer を読むため、遡及適用に履歴書き換えを要する。
- git notes による外付け訂正の経路は repo 内に存在しない (全数検索で不在を確認)。
- trailer の文法を緩めて 22 件を通す案は絶対規律 2 に反する。

## 案 A が倒れた反例 (段 3 sol レンズ)

親と段 2 の子は独立に、次の述語へ到達していた — 「merge 結果の全行がいずれかの親に存在し、
かつ全親の版が結果の subsequence であるなら、その merge に実装面の著作は無い」。
これを満たす既存 entry は 4 件あり (`5823caf328` `3eaf2038ec` `0c0f3e71b3` `bf92f327ca`)、
撤去できると見込んでいた。

sol レンズの反例:

```python
# 親 P1
@audit
def check(value):
    return value

# 親 P2
@authorize
def check(value):
    return value

# merge 結果 R
@audit
@authorize
def check(value):
    return value
```

R の全行は親由来、P1 も P2 も R の subsequence、出現回数も上限内。
それでも R は `audit(authorize(check))` を選んでおり、逆順とは挙動が異なる。
**相対順序を決めたこと自体が実装著作である。**
両親が同じ 1 行を持ち R がそれを 2 回置く場合も同型で、二重登録という新しい挙動を作っている。

したがって D721 の中心理由「最終形からは自動解決と手解決を区別できない」は、述語を
集合包含から順序保存へ強めても解消しない。**D721 を維持し、撤去 0 とした。**

## 案 C が倒れた理由 (両レンズが独立に到達)

親は「逐語ミラーテスト `test_known_violation_ledger_matches_literal_entries` は `ruling` と
`note` という説明文まで逐語 pin しているが、受理集合に効くのは `commit` /
`expected_finding_kind` / `expected_finding_value` の 3 つだけなので pin する価値がない」と
主張していた。**これは誤りである。**

`ruling` と `note` は受理判定に使われない**からこそ**、全史監査ではその改変を検出できない。
`_known_violation_audit()` は照合に commit / kind / value しか使わず、実 commit 照合テストの
被覆は 31 件にとどまり最新 22 件を含まない。**任意の entry の `ruling` を
`"fabricated-ruling"` へ書き換えても全史監査は緑のままで、逐語ミラーだけが検出する。**

つまりこの pin を畳めば、受理集合と land 可否を変えずに台帳の裁定根拠と公開 note だけを
偽造・消去できる。

## 増加を減らす道は残っている (ただしユーザー裁定が要る)

merge 由来の `missing-codex-author` 19 件のうち **12 件は、変更した実装面 path が
`tools/check_ai_provenance.py` と `orchestrator/tests/test_check_ai_provenance.py` の
2 つだけ**だった。台帳を触ったこと以外に実装面の変更をしていない commit である。

構造はこうなっている。全 wave が単一の Python tuple の末尾へ追記し、同じ内容を逐語ミラーへも
書く。並行する 2 wave は必ずこの末尾で競合し、親が手で解決し、その手解決が
「Codex author なしの実装面編集」になって新しい entry を生む。**台帳が自分自身の生成器である。**

ただし段 3 luna レンズが 2 点を訂正した。

- **entry 単位の格納にしても競合はゼロにならない。** 同じ commit を 2 つの wave が独立に登録すれば
  同じ file を触る (`e86d363a` の note が実例)。「止める」ではなく「最大 12 件分**減らす**」が正しい。
- 12 のうち台帳登録 commit 2 件は、データ置き場を実装面として分類する限り防げない。**正味 10 件。**

そして両レンズが独立に、この改修の着手条件として**逐語 pin の撤去自体をユーザー裁定にすること**を
挙げた。既存の正しさ防壁を撤去する判断は親の裁量ではない。

## 親の測定方法の欠陥 (F144 再発)

親は自作の実測スクリプト 4 本の欠陥に気づかないまま、結論をユーザーへ 3 度報告した。
敵対 2 レンズが実データで否定した。詳細は `verbatim/parent-remeasurement.md`。

1. `_commit_paths()` は変更 path を全部返し、`validate_implementation_author()` が
   `_is_implementation_path()` で絞った集合だけを finding 対象にする。
   スクリプトはこの前段 filter を再現せず、**gate と違う母集合を測っていた**。
2. `git merge-file` という blob 単位の低水準 3-way merge の結果を
   「実際の merge で競合し人が手解決した」と一般化して報告した。
   示せるのは「素の 3-way merge では競合した」までである。
3. `bytes.splitlines()` で末尾 LF の差を潰し、出現回数の条件も実装しないまま
   「plan の述語を満たす 4 件」と称した。
4. 生成器分類が canonical trailer を検査せず `'AI-Agent:' in body` だけを見たため、
   trailer block の配置誤り 1 件 (`3f2c43d758`) を「manager が実装面を直接 commit」へ誤分類した。

再測定では (1)(2) の値は偶然変わらなかった (12 件、増加 20 回・減少 2 回) が、
land 根拠としては成立していなかった。

**段 3 の所見 17 件はすべて real、refuted はゼロ。** 親が段 1 で置いた provisional 裁定 3 つは
全部覆された。棄却できた親の主張が 1 つも無かったのは異例である。

## 変異 matrix (撤回した局所修復に対して走らせたもの)

受入 1 回目の赤に対する自分の局所修復 (commit `cb27f437`) へ 2 変異を事前登録して実走した。
その後 main 側の先着修復 (`3876fbe8`) を採って自分の修復を落としたため、
**この変異台帳が対象としたコードは最終 tree に存在しない。** 記録として残すが、
最終 tree の実装差分はゼロであり `DW-S04` により変異 matrix は免除される。
台帳は `mutation-spec.json` と `mutation-result.json`。

- baseline: **PASSED** (rc=0、失敗ノードなし)
- **M01 KILLED** — 切り出し元と開始マーカーを修復前 (archive 側) へ戻す。
  失敗ノードは対象テスト 1 件のみ。
- **M02 KILLED** — 終了マーカーを `- [T-337]` から `- [T-338]` へずらす。
  失敗ノードは対象テスト 1 件のみ。
- SURVIVED 0 / MISMATCH 0 / TIMEOUT 0、registered=2・matching=2。
- 走行は `tools/mutation_worktree.py --commit cb27f437` の使い捨て worktree で行い、
  主 tree は変異させていない (走行後の `git status --porcelain` は空、HEAD は `cb27f437`)。
- wrapper の rc=125 は「source/main 共有木の観測 bytes が変化した」という事後検査であり、
  並行 wave が main を進めたことによる。変異判定そのものには影響しない。
- 本 wave はテスト強化ではなく fixture ポインタの追随なので、`DW-M08` の新旧両走は登録しない。

## 一次資料

- `verbatim/s1-brief.md`, `s1-brief-addendum.md`, `s1-brief-addendum2.md` — 段 1 brief と 2 度の追補
- `verbatim/s2-plan-v1.md` — 段 2 起草 (`check_codex_output` rc=0)
- `verbatim/s3-sol.md`, `verbatim/s3-luna.md` — 段 3 敵対 2 レンズ
- `verbatim/s4-ruling.md` — 段 4 裁定 (所見ごとの real/refuted と採否)
- `verbatim/parent-remeasurement.md` — sol の指摘を受けた親の再測定
- `verbatim/classification.md` — 53 件の全数表
- `verbatim/measurement-scripts.md` — 実測スクリプト 8 本の逐語 (欠陥のあるものも含む)
