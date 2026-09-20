# [T-2813] dev-wave 引数の逐語 (ユーザー依頼、2026-09-20)

[T-2813] (P2、D2186 項 5、採用) `docs/dev-wave/operations.md` の DW-O26 焦点走集合の規則に「production file を変えた wave は、repo
  全体の inventory test 4 群 (`orchestrator/tests/test_campaign.py` の certified-writer caller inventory、`test_official_perf_closure.py` の
  perf file inventory、`test_p3_exploration_namespace.py`、`test_p3_b4_wiring_probe.py`) を参照関係に依らず焦点走に含める」の 1
  句を足す。追加はこの 1 句だけ。exact pin の更新は Codex author (D95) + fixture placeholder (DW-O25)、単節予算の超過は D782 / D961 の手順
  (削減 → 独立 3 例 → 最小増分) で AI が閉じ、上限を上げた場合だけ報告する。[T-2292] (DW-O26 の契約側更新はセットで行う)
  を同じ変更単位で閉じる。着手直前の local main から fresh worktree。実害の一次資料 `output/insights/2026-09-20/t2795-pair-launcher/README.md`
  §7、entry 1751。規律 2 を緩めない。guard 類への便乗拡張・仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
