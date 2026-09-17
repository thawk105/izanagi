---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-17
wave: dev-wave-f976-f977-lock-notify
seq: 3
---

## 再発

### F982

- **再発: 2026-09-17** — 実 repo ロック gate の wave で、変異 harness の probe 走 (runner 選択 =
  `test_real_repo_serialization.py` + `test_wave_land_window.py` の 2 file) の baseline が
  `test_real_repo_writers_do_not_materialize_oracle_environment_candidates` の決定的な赤で止まった
  (WAL lock の JSON 不一致、内側の `test_p3_s4_loop.py` の `wal.read_lock(lay) == build_v2_lock(...)`)。
  同じ commit の wave worktree で `test_p3_s4_loop.py` を含まない 10 file / 7 file の焦点走は緑だったが、
  それは別 module (`test_s8c_*` 等) の収集が `site_policy` を setup 前に import していたためで、
  2 file だけの選択では既報どおり再現した。既報の運用に従い `test_p3_s4_loop.py` を runner 選択へ足して
  probe を投げ直し、初回の sidecar は erratum として job dir に保全した。変更面は conftest のロック層と
  `wave_land_window.py` で、wrapper・site 中立化 fixture・WAL・ident は触っていない。

## supersede 追記

- F976 **supersede: 2026-09-17** — 恒久対応「未実施」は {{D:real-repo-writer-gate-and-rolled-back-notice}} で writer 優先 gate (fresh 取得と昇格、reader は保持ゼロ時だけ検査) として実装した。deadline 245 秒と同時実行数は不変。gate 取得前からの厳密な優先と昇格失敗後の state 回復は保証しない。
- F977 **supersede: 2026-09-17** — 機構側予防のうち「巻き戻しを列へ通知する」は {{D:real-repo-writer-gate-and-rolled-back-notice}} で `wave_land_window.py message --kind rolled-back` として実装し、送信義務を runbook の land 手順と command 入口 項 9 に置いた。「fold の失敗で land の merge まで戻さない」は D2104 項 34 で採らないと裁定した。
