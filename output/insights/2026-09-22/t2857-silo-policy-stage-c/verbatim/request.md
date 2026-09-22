# 依頼の逐語 (2026-09-22 08:4x JST、ユーザー直接起動の `/dev-wave` 引数)

[T-2856] → [T-2857] (P2 → P1、D2214) silo-function-policy 軸を 1 wave で進める。まず docs/axis-onboarding.md §4 の表に第 3 列
  (関数群・複数 hook・状態の軸) を足し、段階 E の planner-v4 再利用の例外を合わせて commit する (案は
  output/insights/2026-09-21/silo-function-synthesis-space/README.md §8)。続けて D2214 の必須条件どおり、段階 C を Codex author (D95)
  で実装・実測する (骨格 patch、api header、型付きの構文検査と単独 TU compile、probe build の焦点試験 3 hook、既存 3 負例の軸 ON
  積み直し、機構の変異、UBSan harness 1 回、手書き方策の生死確認)。計算は設計時の換算で 2.41〜4.12 node
  時間なので、投入前に合計見積りを示してユーザー確認 (D2212 項 4)。正しさゲートは不変、規律 2
  を緩めない。本題だけ、gate・検査・台帳・一般化の追加は scope 外。着手直前の local main から fresh worktree。
