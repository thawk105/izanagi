## 所見

1. **must-fix** — [silo_policy_recon.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/orchestrator/campaign/silo_policy_recon.py:43): 6 方策に対して `job=7` をそのまま slice に使うと、列は巡回せず基本列に戻る。裁定 P2 の「7 位置左へ巡回」なら 1 位置左の列になる。**影響:** job 7 の実行位置が予定と変わり、参照位置を分散する計測設計から外れる。**代案:** `offset = job % len(result)` で巡回し、test の期待列を独立に指定する。

2. **must-fix** — [silo_policy_recon.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/orchestrator/campaign/silo_policy_recon.py:81): compile command が `-DBACK_OFF=1 -DBACK_OFF=0 -DBACKOFF_FIXED=10` の場合も `effective=True` になる。**影響:** 後勝ちの `BACK_OFF=0` で build された値を fixed10 の参照値として受理し、比の分母が変わる。**代案:** `BACK_OFF` についても許可した引数がちょうど 1 個であることを検査し、重複値の負例を加える。

3. **should** — [test_silo_policy_recon.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/orchestrator/tests/test_silo_policy_recon.py:307): fixed10 test は `_build_variant` を stub し、実際の configure argv を検査していない。例えば `_build_variant` が `BACKOFF_FIXED` を argv に足し忘れてもこの test は通る。**影響:** build 配線の欠落を投入前の test で検出できない。**代案:** `_build_variant` の configure 呼出しを捕捉し、`-DCCBENCH_BACKOFF_FIXED=10` を確認する。

4. **nit** — [silo_policy_recon.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-silo-small-compare/orchestrator/campaign/silo_policy_recon.py:391): `cases` の順序は照合するが、出力される `case_order` は照合しない。例えば `cases` が正順で `case_order` だけ逆順でも受理する。**影響:** 順序の記録に食い違いが残るが、現在の比較値は変わらない。**代案:** 両方を予定列と照合する。

fixed10 の patch は使い捨て checkout 内で適用され、例外時も `applied` の `finally` と checkout の終了処理で復元される。genome と configure 引数への追加、両 verify 後の bench、早期 return 行の集計除外、段階 D の既存経路は静的には整合している。集計でエラー時に部分比較を空にする処理は、エラーを返し終了コードも非ゼロにするため、黙った受理にはならない。

## 変異 kill 点の判定

1. m-fx-flag: **成立**。`_one` の genome と build 引数を直接検査する。ただし実 configure argv の検査ではない。
2. m-fx-patch: **成立**。実 `_source` の適用木で marker を読む。
3. m-fx-define: **成立**。define 欠落時の status と build 後に run しないことを検査する。
4. m-cmp-max: **成立**。異なる 3 参照中央値で最大分母を検査する。
5. m-cmp-null: **成立**。fixed10 だけを非適格にして null を検査する。
6. m-cmp-order: **成立**。行順だけを入れ替え、順序エラーを検査する。
7. m-cmp-fxflags: **成立**。fixed10 の flag だけを 9 に変えて拒否を検査する。
8. m-rotation: **成立**。巡回を全廃すれば job 1〜5 で赤になる。ただし test も `job=7` の巡回漏れを踏襲している。
9. m-cmp-floor: **成立**。比 1.02 の非超過と 1.04 の超過を検査する。

## 総括

**NO-GO。** 静的レビューのみで、build・pytest は実行していない。

must-fix は **job 7 の巡回漏れ**と、**重複 `BACK_OFF` define を fixed10 として受理する検査**の 2 件。