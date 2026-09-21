単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、それを理由に検査全体を打ち切ってはならない。

- /home/SFC/tanab/.claude/jobs/0adb58a3/tmp/codex/review-out.md (**1 巡目のレビュー出力の全文**。所見 1〜12 の原文)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/docs/paper-story/claim-evidence/2026-09-21.md (**fix 後の新稿**、767 行。行が非常に長いので `grep -n "^| C24 "` 等で行を特定し `awk 'NR==<n>'` で 1 行ずつ読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/paper-story-2026-09-21b/docs/paper-story/2026-09-21b.md (**fix 後の版**、5,493 行 — 全文 `cat` 禁止。`grep -n` で位置を出し `sed -n` で 80 行以内ずつ読め)
- /home/SFC/tanab/.claude/jobs/0adb58a3/tmp/brief-s1.md (親の段 1 brief と provisional 裁定)

読んでよい資料: 一次資料 (`docs/decisions.md` の D1441 / D2160 / D2166 / D2172 項 4・項 8 / D2174 項 3 / D2180 / D2184 / D2186 項 1 /
D2187 / D2190 / D2194 / D2196 / D2198 / D2199、`grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ)、
`output/insights/2026-09-20/t2797-b5-contrast/README.md` (§6 / §6.3 / §8。**とくに §8.1 の「本走の 108 系列 (3 workload × 3 arm × 12)」と
§8.2 の「LLM arm の親 (人間または AI) の手番: 108 系列 × 10 巡 = 1,080 巡」**)、`output/insights/2026-09-20/t2810-g1-launch-validation/README.md`、
`output/insights/2026-09-20/t2795-k2-pair-attempt/README.md`、`docs/failures.md` の F1034 (`grep -n "^### F1034"`)。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す。pytest・build・測定は走らせない。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。

## 役割

**お前は fix 後の焦点再レビュー (`DW-O16`) である。** 1 巡目 (`review-out.md`) の所見 1〜12 に対し、親が次のように裁定・処置した。
**所見ごとに closed / partial / regressed を判定し、対応表を必ず出せ。**

| 所見 | 親の裁定 | 処置 |
|---|---|---|
| 1 (g1 の旧状態が新稿に残存) | real / must-fix | 新稿 C24 (発効と validator 整合と P3 `allowed: false`、候補文書の削除は裁定のみ)、C36 (pin 更新の実施と「発効は前提の充足ではない」)、§2.4 の床値行、L43 を書き換えた |
| 2 (pin 前進前の現在形) | real / must-fix | 新稿 C34 (起点の pin は `e9e477ca`、入ったのは R/W hook まで)、§2.4 の mocc 行、L44 の禁止句を「pin 前進で certified 系列が開いた」へ替えた |
| 3 (B-5 の実装認可の否定) | real / must-fix | 新稿 C33、L47、§4.3 B-5、§2.4 の LLM 行を「D2172 項 4 が (α) の段階実装と (β) 上限付き試走を認可し 2026-09-21 に完了。本走は未認可」へ直した |
| 4 (B-7 の旧裁定との衝突) | real / must-fix | 新稿 L41 を「稿自身は充足を判定しない + D2174 項 3 が 4 語の限定付きで報告要件の充足を裁定 (D2044 項 3 を supersede)」へ、§4.3 B-7 を同旨へ直した |
| 5 (「非列挙は未裁定」の再導入) | real / must-fix | 新稿 §4.3 B-1 を D1441 の裁定済みへ直し、§7 冒頭に「前稿の執筆時点の誤り 1 件」として明記し、§7 の表に該当行を足した |
| 6 (検証相の記録義務・B-8 仕分けの旧手番) | real / must-fix | 新稿 C25、L40、§2.4 の B-8 行、§4.3 B-8 を「記録先は D2172 項 8 で決着、仕分け (2) の限定明記は発効 commit の wave、B-8 は承認済み・未実施」へ直した |
| 7 (LLM 親手番 1,080 巡) | real / must-fix | **版** §0 項 3 と §8 B-5 を「36 系列 × 10 巡 = 360 巡」へ直し、§8 B-5 に「insight §8.2 は 108 系列すべてに 10 巡を掛けており本版は採らない (凍結 insight は変更しない)」と根拠を明記した |
| 8 (L51 の時点) | real / should-fix | 新稿 L51 に時点 (2026-09-19 の初回投入操作 / 2026-09-20 の完走) を足した |
| 9 (C35 の出所欄) | real / should-fix | 新稿 C35 の (b) 欄に F1034 の消失と参照できる写し・再構成物・対応表を足し、旧「[T-2795] 裁定待ち」を pair 不成立と D2194 項 2 の現在地へ直した |
| 10 (§7 の継承表に 6 行不足) | real / should-fix | 新稿 §7 に C3 / C9 / C10 / C11 / C17a / C17b の行を足した |
| 11 (P3 を未実施へ戻す必要なし) | refuted | 現行維持 |
| 12 (L-A1S-4 は解除へ滑っていない) | refuted | 現行維持 |

**親が再走した検査:** `tools/check_docs.py` 違反なし、job dir の numcheck (path 実在・D 番号実在・転記 literal 35 件の一次資料での逐語存在・
claim-evidence が pin した版 sha256 と現物の一致 = `ca3d9e06…`) すべて一致。

## 検査すること

1. **所見 1〜10 の対応表** — 各所見が closed か partial か regressed か。**partial / regressed には該当 file・行 ID と対案を付けよ。**
2. **fix が新しい矛盾を作っていないか** (同じ稿の中で、同じ事実について古い現在形と新しい現在形が併存していないか)。とくに
   「未発効」「人間手番」「未着地」「承認のみ」「裁定待ち」「次版で仕分ける」の語が、g1・pin・B-5・B-7・B-8・K2 について残っていないか
   `grep` で網羅的に洗え。
3. **所見 7 の派生値の再計算** — 本走の系列数 (108 = 3 workload × 3 arm × 12)、LLM arm の系列数 (36)、1 系列 10 巡、親手番 360 巡、
   1 巡 10〜13 分から ≈ 60〜78 時間、を insight §8.1 / §8.2 / §6.3 と突き合わせて検算し、版の新しい文が原データと一致するかを判定せよ。
   **「1,080 巡」を版が引用として残している箇所 (insight の記述の引用) が、引用として正しく限定されているか**も見よ。
4. **所見 5 の処置の妥当性** — 前稿の B-1 行の誤りを「執筆時点の誤り」と呼べるか (D1441 の日付 2026-09-02 と前稿の作成日 2026-09-20)。
   §7 の新しい文が、版の「前版の執筆時点の誤りは 0 件」(版と稿は別の系列) と混同を生まないか。
5. **1 巡目で見落とした新しい所見**があれば挙げよ (ただし scope 外の提案・L-A1S-4 の解除・図の作成・新しい主張の追加は refuted)。

## 出力形式 (この見出しをそのまま使う)

## 対応表

| 所見 | closed / partial / regressed | 根拠 (file・行 ID・一次資料) |

## 新規所見

番号付き。`real / refuted`、`must-fix / should-fix / nit`、該当 file と節、対案。無ければ「無し」と書け。

## 再計算した派生値

所見 7 の検算と、その他に検算した数値。

## GO / NO-GO

## 総括

10 行以内。
