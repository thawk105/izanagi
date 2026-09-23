# [T-2854] 残り (1) — 段 6 裁定 (親、2026-09-23 09:18 JST)

対象: wave commit f7b69e3de (子 commit 5de23474d の限定 patch 統合)。レビュー A (正しさ境界) = GO・所見なし、レビュー B (過剰・削除) = GO・nit 3 件。

| 所見 | 判定 | 扱い |
|---|---|---|
| B1 旧 field 名の `hasattr` 検査 1 行が試験に残る | real (nit) | fix1 で削除 |
| B2 経路比較 helper が DSG を 2 回構築 | real (nit) | fix1 で 1 回に |
| B3 読みの照合で空 container を毎回生成 | real (nit) | fix1 の所要削減に含める |
| B の総括「所要 +52%」(比較条件が揃っていない) | 親が同時刻対照で再測: real | 下記 |

親の実測 (paired-timing.log、login、同じ実 trace・同じ引数・別 process、変更前 = main checkout cadaf3805、変更後 = f7b69e3de、交互 3 回):
workers=1 = 7.27 / 7.28 / 6.94 秒 → 9.98 / 9.99 / 9.84 秒、workers=2 = 4.53 / 4.67 / 4.65 秒 → 7.44 / 7.58 / 7.47 秒。辺数は全部 268,209、
verdict は変更前 indeterminate (印) → 変更後 serializable。cProfile (compact、workers=2) で存在検査 4.28 秒 (token 復号・per-row の生成が大半)。

成果物への影響 (DW-G05): certified・受理集合は変わらない。検査は親で逐次なので trace が大きいほど verifier の所要 (直列性検査が wave・計測の律速) に効く。
判定を変えない局所削減なので scope 内の should として fix1 に入れた (production 80 行以内、新抽象・並列化なし、既存期待値の変更禁止)。

fix 後: 焦点再レビュー 1 本 (DW-S06-C)、事前登録変異の anchor を fix 最終 commit で付け直し (DW-M07)、単独走・焦点走・実 trace probe・同時刻対照を再走。
