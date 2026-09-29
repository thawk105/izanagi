# 段 6 裁定 — [T-2273][T-2560] (2026-09-28)

対象: 統合 commit `56f8e97c0` (親 51f896352)。資料: codex/s6-review-a-out.md (レンズ A、修正後 GO)、codex/s6-review-b-out.md (レンズ B 過剰・削除・効果、所見なし GO)。
全史 provenance (実装後): 13,125 件、新規違反なし (provenance-1.log)。

| # | 所見 | real/refuted | 処置 |
|---|---|---|---|
| A1 (must-fix) | `MappingProxyType` の texts は背後の dict が書き換わりうるのに、新しい共通判定 cache `contains_by_literal_rel` は内容確認なしに別の式の走査へ再利用する。背後を書き換えて別の式で走査すると、旧実装なら hit する text を「literal 不在」で落とす | real (ただし production の `search_repository` は背後 dict を外へ出さないので到達しない。既存の `hits_by_expression` も proxy では内容確認をしないが、同じ式に限る。新 cache はそれを別の式へ広げる) | 採用・fix: cache の値に判定した text object 自体を持ち、`cached_text is text` のときだけ再利用する (str は不変なので同一 object なら内容も同一)。正例 test: proxy の背後 dict を書き換えた後の別式走査が旧実装どおり hit する (reference と report bytes 一致)。変異 M7 (identity 照合を外す) を事前登録 |
| A2 (should-fix) | str subclass の text で `find` が `in`・regex と食い違いうる | refuted (記録のみ) | 旧実装の軸 prefilter `axis_literal not in text` も subclass の `__contains__` に依存しており同型。production の text は `bytes.decode` の exact str。成果物の値・受理集合への影響を示せない (DW-G05) |
| A3 (should-fix) | `sre_parse` は 3.11 から非推奨、将来削除 | refuted (scope 外、記録のみ) | 実行環境は Python 3.10 (login・計算ノードとも `/usr/bin/python3.10`、pegasus03 の既定は 3.9)。3.11 以降で警告を error にした場合も import 失敗で走査全体が止まる fail-closed で、受理集合を静かに変えない。仮想リスク向けの互換層は足さない (依頼の scope 外) |
| B | 所見なし。効果は再 profile と系列で判定 | — | — |

## 変異の追加登録 (fix 前、DW-M01)

| ID | 変異 | 殺す番人 |
|---|---|---|
| M7 | 共通判定 cache の再利用条件から text object の identity 照合を外す | A1 の正例 test (背後書換え後の別式走査の hit) |

## 分類の erratum (DW-M03 / DW-M08)

M4 (局所化を外す)・M6 (共通判定の memo を外す) は report と受理集合を変えない出力等価な変異で、発火回数の番人だけが検出する。
DW-M03 により kill には数えず、「diagnostic sensitivity pin」(D513 の発火回数番人の検出力) として別枠に記録する。
kill に数えるのは M1・M2・M3・M5・M7 (report と受理集合が変わる)。P0 は SURVIVED 期待。

## fix の単位

所見は `orchestrator/campaign/s8b_holdout_freeze.py` と `orchestrator/tests/test_s8b_holdout_freeze.py` の 2 file に閉じるので一枚岩 (同じ子木 author-t2273is-impl に branch fix-t2273is-impl-1 を切る)。
