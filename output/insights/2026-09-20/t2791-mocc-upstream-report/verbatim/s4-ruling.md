# 段 4 裁定 — [T-2791] (2026-09-20、軽量版: 段 2・3 省略)

## 所見と裁定

段 2・3 は DW-C00 の軽量版判定で省略 (docs-only、設計択一・正しさ防壁・受理集合に触れない)。段 1 の provisional 裁定を親が確定する。

| # | 前提 | 裁定 | 理由 |
|---|---|---|---|
| P1 | [T-1892] 5/42 と [T-1943] 1 cell を経緯として含める | 採用 (各 1〜2 文、一次資料は各自の insight) | T-2774 README §1 が比較対象として引く。上流の読者は「何がきっかけか」を要する。旧束縛の値はそのまま、合算しない |
| P2 | T-2774 §3 の静的順序論証を含める | 採用 (「observation-consistent static reading, not a root cause; execution order not observed」の限定を同段落に置く) | 上流の読者が自分で見る場所を示す。行番号は e9e477ca 束縛で現物照合済み。分岐 2/3 (hook / verifier 仮定) を排除していないと同段落で書く |
| P3 | 上流 master との `cc/mocc/transaction.cc` 差分の性質を書く | 採用 (本 wave の静的検算として、local mirror の `origin/master` = `50c7946d`、commit 日時 2026-06-28、fetch 日は未記録、を明記) | 上流の読者が最初に問う「あなたの branch は本家と何が違うか」に答える。新規測定ではない。上流 master そのもので走った走は無い、と明記 |
| P4 | 診断 arm 0/120 を書く | 採用 (「we do not propose this as a fix」を同段落に、2 変更が束ねられ寄与分離不能・未調整 p・family で有意と言わない) | 引数が含めよと言う観測。D2148 項 13 の「修正 PR 見送り」と両立させる書き方に限定 |

## plan v2 (成果物)

- `output/insights/2026-09-20/t2791-mocc-upstream-report/README.md` — 位置づけ (`authority: none` / `default_effect: no-state-change`)、還元判断: ユーザー確認待ち、送信は人間、
  段 6 レビューの所見と反映、一次資料の索引。
- 同 `report-draft.md` — 英語 issue 本文案。各段落の文に `[S-nn]` 番号を振る (evidence-map の鍵)。送信時に番号を落とす前提。
- 同 `evidence-map.md` — `[S-nn]` → 一次資料 path + sha256 (+ commit or 再計算日) の表。repo tracked は本 wave で `sha256sum`、job dir 原本は results 稿の表 + 本 wave 再計算。
- 変異 matrix: 実装面差分ゼロ → 免除 (DW-S04)。受入全走: 免除しない。実 repo を読むテスト: 変更 file は `output/insights/` と `docs/spool/` の追加のみ → `python3 tools/check_docs.py` を段 7 記録前に実走。
- 段 6: read-only codex レビュー 1 本。レンズ = (a) 上流の読者に誤読させる文 (根因確定・修正提案・不在証明・同等性・性能主張・「同一 binary」)、(b) 引数の「書かないこと」の混入、
  (c) report-draft の数値と一次資料の不一致 (evidence-map 経由で照合)。must-fix は親が本文で反映し、`[S-nn]` の対応を保つ。

## 条件 dispatch の再評価 (段 4 時点)

- DW-O08 / O09 / O10: freeze / oracle / proof chain / 凍結 bytes に触れない (results 稿は引用のみ、編集しない)。不成立。
- DW-O11: 削除なし。不成立。DW-O13: gate 新設なし。不成立。DW-O19: tracked file の一時変異なし。不成立。
- DW-O05: 段 6 の read-only codex 起動直前に読む。DW-O01 / O02: 起動直前。DW-O17: commit 直前。DW-O18 / O26 / O27: 受入前。DW-O23 / O25 / O28: 段 9。
