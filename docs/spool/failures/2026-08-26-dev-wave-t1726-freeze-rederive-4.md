---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1726-freeze-rederive
seq: 4
---

## 新規

### {{F:output-snapshot-fix-reproduced-its-own-contamination}}. 汚染を消す修正の正例 test が同じ汚染を作った [テスト代表性] [計測汚染]

- 事象: 実 `output/` の棚卸し検査から git ignore 済み path を除外する修正
  (F62 の 2026-08-26 再発への恒久対応) を実装した際、実装子が足した**正例 test が
  実 repo の `output/` へ git 可視の directory を作った**。
  `test_..._detects_git_visible_real_output_changes` が
  `ROOT / "output" / f"snapshot-positive-...{pid}-{time_ns}"` を `mkdir` する形である。
  静的レビューでは妥当に見えたが、親が 2 file を単独走したところ
  **12 failed** で露見した。作成中の窓に並行して走る棚卸し test 10 件と、
  除外側の新 test 自身が巻き添えになった。修正後の同じ走は 576 passed / 8 skipped / rc=0。
- 根本原因: 「実 `output/` への git 可視な書き込みが検出されること」を示す正例は、
  素直に書くと**実 `output/` へ書く**ことになり、消そうとしている汚染源と同型になる。
  対象が共有された可変資源であるため、検出力の証明と非汚染が正面から衝突する。
- 恒久対応: snapshot helper は走査 root を引数に取る
  (`_t080_output_snapshot(root)` / `_real_output_snapshot(output=...)`)。
  **`tmp_path` を root に渡し、tmp 側へ実 ignore prefix と同じ相対名を作る**ことで、
  実 repo を 1 byte も触らずに除外と検出の両方を固定できる。
  ignore prefix はハードコードせず `git_ignored_output_prefixes(ROOT)` に実在することを
  test 内で先に assert する (`orchestrator/tests/output_snapshot_ignores.py`)。
- 再発検知: 共有された実資源を棚卸しする検査へ正例を足すときは、
  正例が**その実資源へ書いていないか**を実装後に必ず見る。
  静的レビューでは通る。対象 file を単独走させ、同じ走の中の他 test が
  巻き添えで落ちないことを確認する。

### {{F:same-scan-helper-duplicated-three-times}}. 同じ実 output 走査 helper が 3 file へ複製されていた [ドリフト]

- 事象: 実 `output/` を before/after で棚卸しする helper は、当初 2 つと認識されていた
  (`test_s8b_floor_campaign.py:1451` `_real_output_snapshot()` と
  `test_s8b_oracle_driver.py:554` `_t080_output_snapshot()`)。
  並行 session と親の双方がその前提で機構を設計したが、実際には
  `test_real_repo_serialization.py:473` に `_t080_output_snapshot()` の
  **byte 単位で同じ 3 つ目の複製**があり、実 `ROOT / "output"` を走査していた
  (呼び手は `test_t080_import_temp_environment_fails_closed_for_foreign_module` 826 / 842 行)。
  2 つだけ直しても連鎖赤は残る状態だった。
- 根本原因: 同じ不変条件を持つ helper が共有されず file ごとに複製されていた。
  複製は grep すれば出るが、**議論が「2 つ」で始まると誰も数え直さない。**
- 恒久対応: 除外規則を共有 module `orchestrator/tests/output_snapshot_ignores.py` へ 1 本化し、
  3 file すべてがそこから import する形にした。以後の複製は同 module を使う。
- 再発検知: 「N 箇所ある」と述べる前に識別子で全件検索する
  (`grep -rln '_real_output_snapshot\|_t080_output_snapshot' orchestrator/tests/*.py` は 3 file を返す)。
  他者から渡された件数を数え直さずに設計の前提に置かない。
