# 変異 matrix 実測結果 — P-C2 + P-C1(b) wave (2026-07-20) / 確定版

事前登録 = mutation-prereg.md (実装前に確定)。実測は親が統合状態に対して 1 変異ずつ注入 → 対象テスト
実行 → 必ず復元、で行った。ハーネス = mutate.py (置換対象が 1 箇所でなければ SPEC-ERROR で停止し、
「注入されなかった変異」を緑と誤報しない)。

## 最終結果: **18 変異 / 18 KILLED / 0 SURVIVED、全て帰属成立**

「帰属成立」= 受理集合または fail-closed 挙動が期待方向へ変化したために赤くなったこと。診断文字列の
変化だけで赤くなる kill は帰属不成立として数えない。

| # | 変異 | 赤くなったテスト |
|---|---|---|
| M-C2 | 全単射消費を外し未束縛 retry を無視 | test_resultful_window_retry_is_unbound_for_one_reason |
| M-C5r | attempt 集合述語 (frozenset) を無効化 | test_attempt_gap_has_one_lifecycle_reason |
| M-C6r | physical-topology 述語を無効化 | test_attempt_physical_order_must_match_numeric_order |
| M-C7 | retry window への pipeline record 混在を許す | test_retry_attempt_one_rejects_pipeline_record_for_one_reason |
| M-C8r | 隣接性を「後ろならどこでも可」に緩和 | test_retry_successor_must_be_physically_adjacent |
| M-C9r | terminal binding の identity 照合を無効化 | test_trial_result_attempt_must_match_owning_start |
| M-C10r | lifecycle 違反時に definitive-red で白へ戻す | test_global_issue_does_not_mask_definitive_correctness_red |
| M-C11 | trial-result が pipeline より後ろである検査を外す | test_trial_result_must_follow_all_pipeline_evidence |
| M-P1a | run_once の rc append を削除 | test_run_once_records_rc_and_keeps_three_tuple_when_not_strict |
| M-P1b | append を strict 判定の**後**へ移す | test_run_once_records_rc_and_keeps_three_tuple_when_not_strict |
| M-P2 | 採用 round でなく最終 round の rc を載せる | test_pipeline_records_returncodes_from_best_middle_round |
| M-P3 | `is` 同一性を `==` (dataclass equality) に変える | test_pipeline_cv_tie_keeps_first_round_returncodes_by_identity |
| M-P4 | 対応が一意でないとき fail-closed しない | test_pipeline_unmatched_returncode_round_aborts_before_bench_done |
| M-P5 | driver の record_rep_returncodes=True を削除 | test_transient_prepare_failure_retries_once |
| M-P6 | report の rc 欠落を [0]*5 で補完 | test_bench_returncodes_are_strict_and_do_not_publish_tps[missing] |
| M-P7 | 全ゼロ検査を any → all に反転 | test_global_issue_composes_row_local_assessment_reason |
| M-P8 | rc 件数検査を削除 | test_bench_returncodes_are_strict_and_do_not_publish_tps[short] |
| M-P9 | bool を int として受理 | test_bench_returncodes_are_strict_and_do_not_publish_tps[bool] |
| M-P10 | layer3 schema の optional property を削除 | test_bench_rep_returncodes_passes_real_view_and_schema |

## erratum — 初回集計の訂正 (F9/F15 型の再発を自ら踏んだ記録)

**初回に「15/15 KILLED、ゲートは全て実効」と記録したのは不正確だった。** 敵対レビュー 2 本が独立に
指摘し、親が fixture の実読で確認した結果、**M-C6 と M-C7 は受理集合を変えない変異**であり、テストが
理由文字列を厳密比較しているために赤くなっただけ (診断文字列 kill) と判明した。

- **M-C6 (初回)**: 物理順専用検査を削除しても、直後の `attempts != [1, 2]` が `[2,1]` を拒否 →
  受理集合は不変
- **M-C7 (初回)**: 混在検査を削除しても `S + pipeline + retry` は 3 record なので exact-length
  検査が拒否 → 受理集合は不変
- **親の追試で判明した根因**: 当時の fixture は「完全な committed trial 2 本を逆順に置く」もので
  **retry を 1 件も含まず**、複数の独立条件で赤くなる**過剰決定 fixture** だった。事前登録が自ら
  「他の拒否理由を除去した単一理由 fixture を作る」と定めていた条件を、実測時に親が確認していなかった
- **fix 段での是正**: (i) 集合述語を `frozenset` のみに縮小し順序を再検査しない構造へ分離、
  (ii) exact-shape ゲートから pipeline event を除外し専用述語だけが pipeline を見る構造へ分離、
  (iii) fixture を「集合・retry・identity は全て成立し、物理順だけが違反」の単一理由形へ差し替え。
  この是正後に撃ち直した M-C6r / M-C7 は**受理集合を変える変異として帰属成立**
- **教訓**: 「変異が殺された」は「テストが赤い」ではなく「受理集合が期待方向へ変わった」で判定する。
  変異実測時に fixture の過剰決定を検査する手順が抜けていた

## その他の実測メモ

- **M-P1b (append を strict 判定後へ移す)**: 相談 B が「official 経路は `strict_returncode=False`
  のため strict=False のテストだけでは等価変異」と事前に警告した箇所。実装者が strict=True 経路の
  独立ケースを書いたため実際に KILLED。**事前登録の改訂が効いた実例**
- **M-P3 (`is` → `==`)**: `ScalePoint` は通常の dataclass のため equality で別ラウンドへ誤対応
  しうる。CV 同値ケースのテストが検出
- **ハーネスの SPEC-ERROR が 4 回発火した** (M-P10 の初回、fix 後の M-C8/M-C9/M-C10)。いずれも
  「変異が注入されていない」状態であり、緑と誤報せず停止した。**注入されなかった変異を成功と数える
  事故**を構造的に防げることが実証された
- 事前登録の M-C1/M-C3 は M-C2 に包含、M-C4 は単一行変異では帰属が取れないため M-C2/M-C7 へ分解した
  (DFA の条件が逐次 return する構造上、単独では等価変異になる)
