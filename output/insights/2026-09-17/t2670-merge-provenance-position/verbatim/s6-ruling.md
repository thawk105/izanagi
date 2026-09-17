# 段 6 裁定 (親、2026-09-17 22:17 JST 頃、レビュー完了 22:14 と実装 commit 22:19 の間) — [T-2670]

焦点走 f1 (計算ノード 4004.nqsv、7 file: test_dev_wave_wait / test_dev_wave_wait_compute / test_run_tests_shards /
test_dev_wave_land / test_resume_gate_acceptance_boundary / test_check_docs / test_check_wave_startup) = 1713 passed /
4 skipped (check_docs 実 repo 走の growth hold 3 + flaky hold 1、いずれも既存) / 68.9 秒 / rc=0。

## レビュー A (契約・正しさ境界) — NO-GO → 裁定後 GO 相当 (code 変更なし)

| # | 判定 | 採否 | 処置 |
|---|---|---|---|
| A1 | refuted | — | 裁定 §3 との一致を確認 (31 hunk、+170/−68) |
| A2 | refuted | — | merge 保持は D1233 と整合。保持 = land 適格ではない (D689/D731/D732 が判定) |
| A3 | real / nit | 表現採用 | 一時 message file の削除は「試行」(OSError 握り潰しは既存挙動)。D 文へ反映、cleanup 実処理は拡張しない |
| A4 | real / must-fix | **採用 (意図した帰結として明記、code 変更なし)** | 親 probe (`probe_real_checker_positions.py`、実 checker) で実測: (i) main にだけ trailer 無し commit A → 旧位置 rc=0「1 件、違反なし」、新位置 rc=1 で A を名指し (「3 件中 1 違反」)。(ii) main が A の既知違反 entry を追加 → 旧位置 rc=2「実行不能: index-only member does not match HEAD」(F206 再発 2026-09-01 の型)、新位置 rc=0「4 件、新規違反なし」(main の full 監査と同じ判定)。受理集合の変化は 2 方向: (a) main-only 違反の取り込みは受入投入前に拒否 (縮小)、(b) main 側の台帳追加を含む取り込みは data error で止まらず台帳規則で判定 (旧位置の偶発拒否の解消。最終判定は従来の手動復旧 = `--ff-only` 後の full 監査と同じ)。旧位置を復活させて偶発拒否を保存する案は採らない (レビューの推奨と一致)。D fragment に「受理集合の変化」節、F206 に supersede 1 行を足す |
| A5 | refuted | — | checker 意味論の確認 |
| A6 | refuted | — | 報告と実体の矛盾なし。実行履歴は親の焦点走・変異走で確定 |

## レビュー B (test・変異・consumer) — GO

| # | 判定 | 採否 | 処置 |
|---|---|---|---|
| B01 | refuted | — | 既存 test の弱体化なし |
| B02 | refuted | — | 新規負例は単一理由で M1〜M3 を runner 投入で検出 |
| B03 | refuted / nit | 採用 | 変異走で新規負例の個別 duration を記録 |
| B04 | refuted / nit | 採用 | 最終 spec の累積一意性と期待 node 完全集合は probe → 本走で満たす |
| B05 | refuted / nit | 採用 | M4 の赤理由を分けて記録: 実 git 負例 = cleanup failure (rc 70→74)、fake 2 本 = `git merge --abort` の出現 |
| B06 | refuted | — | consumer は静的に赤なし、f1 で 7 file 緑 |
| B07 | real / nit | 採用 | 記録に焦点走の対象 file 一覧を添える (上記) |
| B08 | refuted | — | 報告件数 27 の整合 |

## 結論

code の fix は 0 件。焦点再レビューは fix が無いため行わない (DW-S06-C)。実装は author の patch のまま commit し、
変異 matrix (probe → 本走) と受入へ進む。A4 の受理集合変化は D fragment・F206 supersede・最終報告に明記する。
