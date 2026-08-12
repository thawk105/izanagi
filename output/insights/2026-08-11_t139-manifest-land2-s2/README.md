# 2026-08-11 [T-139] land 2 session 2 — 承認 manifest 実装の停止と裁定 4 件

wave `dev-wave-t139-manifest-land2-s2` / branch `worktree-dev-wave-t139-manifest-w2`。

## この session が何をしたか

ユーザー裁定 RP-1 (a) は「approval manifest 実体 + resolver + 受領証 writer + 固定 semantic
validator + conformance vectors を 1 session に統合せよ」だった。**段 2 のプラン起草と段 3 の
敵対 2 レンズが独立に NO-GO を返し、親は段 4 で「8 件のうち 7 件は本 session で実装しない」と
裁定した。**

実装したのは **§S7 #2 (Git trust root 部分集合、確定裁定 RP-2 (a) の逐語) の 1 件だけ**である。

| file | 内容 |
|---|---|
| `package.md` | **ユーザー裁定 4 問 (Q1〜Q4)** と、撤回した親の主張 |
| `verbatim/` | 段 2〜段 6 の子成果物の逐語 |

## 停止の理由 (3 点)

1. **承認済み文書の内部矛盾 4 件。** 承認済み `record-items-v2.md` が固定 semantic validator に
   要求する検査のうち 4 件は、同じく承認済みの `receipt-schema-v1.json` に**入力そのものが
   存在しない**。両者は D282 で exact bytes 承認済みで、本 session は bytes を変更できない。
   → `package.md` Q1
2. **manifest 表現が未裁定。** D291 の land により承認根が 2 本 (`F_r` / `F_p`) になり、
   D282 の閉包と D291 の `exact_closure` を 1 枚の平坦な manifest に同居させられない。
   → `package.md` Q2
3. **確定裁定 RP-4 (a) が D292 により失効。** 「公表 core 3 文書の凍結承認 + fold = pilot 解禁条件」は、
   D292 が解除を canonical decision の専権としたため成り立たない。
   → `package.md` Q3

## 実装した 1 件 (§S7 #2)

`orchestrator/preregistration/blobref.py` の Git 起動経路が、`git` を**名前解決**し
(`subprocess.run(["git", ...])`)、環境 allowlist に `PATH` を含んでいた。
`PATH` 上の偽 `git` が `rev-parse` / `merge-base` の出力だけを偽装すれば、**`F_r` より前の
checkout で測った試行が「承認済み事前登録の子孫で測った」として受理される** (SHA の偽造は不要)。

**正確な位置づけ (段 6 レビュー B の指摘で訂正):**
穴は既存の基盤層 (`orchestrator/preregistration/`) に現に存在したが、
**その穴を通る production 経路もまだ無い。** この package を呼ぶ非 test の caller は
repo 全体で **0 件**である (`s8c_preregistration` は別 module で無関係)。
したがって本 session が動かしたのは基盤層の受理集合であって、**production の受理集合ではない。**
「現行の production gate が保護された」とは記録できない。
**初稿の「新規の休眠コードを積むことではなく既存の穴を塞ぐこと」という書き方は、
production 結線済みと誤読させるため撤回する。**

RP-2 (a) が列挙する 8 項目のうち **6 項目が未充足**だった。

## 本 session が land しない理由

S6 (a) は「land は最後の session が 1 回だけ」と定める。本 session は最終ではない
(`submit_pilot` / PBS preflight / driver / collector / correctness 還流 / certified 側 consumer /
pilot 投入 / §S7 #4 / #5 / #6 が残る)。branch tip を次 session へ引き渡す。
