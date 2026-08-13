---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t1062-acceptance-scheduler
seq: 3
---

## 新規

### {{F:hookwrapper-value-is-not-final}}. hookwrapper の post-yield 値を最終値とみなした [恒真ゲート]

- 事象: 段 2 プランが `pytest_xdist_make_scheduler` の hookwrapper の post-yield 値を実効
  scheduler の attest にしていた。後から登録された外側 wrapper は、内側 wrapper が値を見た
  **後**に戻り値を差し替えられるため、conftest に `loadgroup` を見せたまま DSession が別の
  scheduler を使う形が成立する。実装していれば「差し替えを検出する」と称する検査が、
  差し替えを一切検出しない恒真な gate になっていた。
- 根本原因: pluggy の wrapper 意味論を「自分が最後に見る」と誤読した。firstresult の hookspec
  でも、wrapper は入れ子であり最終値の保証は最外周にしかない。
- 恒久対応: {{D:effective-scheduler-attestation}} の決定 1 (値源は DSession が実際に保持した
  `.sched` の実型で、`pytest_runtestloop` の post-yield で固定する)。変異 MUT-A1 が
  この逆変異を殺す。
- 再発検知: 変異 MUT-A1 (runtestloop の固定を外す) と、後登録 wrapper で差し替える live-xdist
  テスト `test_live_xdist_sessionfinish_scheduler_swap_keeps_runtestloop_value`。

### {{F:dispatch-relay-drops-tail-marker}}. 計測環境の転送形式を無視した wire 設計 [テスト代表性]

- 事象: 段 2 プランは受入 log の marker を行頭 exact prefix で抽出する設計だった。
  Pegasus dispatch は compute 側 stdout の各行へ `| ` を前置し、成功時は末尾 4 KiB
  (失敗時 64 KiB) しか relay しない。この設計では**実受入が必ず marker 0 行と判定され
  rc=70 になる**。さらに conftest 自身が failure digest を最大 48 KiB、marker より後に出すため、
  marker を `pytest_sessionfinish` で出すと relay tail から押し出されうる。
- 根本原因: local の pytest 出力を wire と同一視した。既存の marker 前例
  (`IZANAGI_GROWTH_HOLD_SUMMARY_V1`) は local terminal 出力の前例にすぎず、待ち手が見る
  dispatch log への到達を証明していなかった。
- 恒久対応: {{D:effective-scheduler-attestation}} の決定 3 と 5 (marker は
  `pytest_unconfigure` の最後 = failure digest より後、抽出器は bare 形と `| ` 前置形の両方を
  受けて exact-one)。実測した relay 後の literal
  `| IZANAGI_EFFECTIVE_SCHEDULER_V1 {"effective_scheduler":"loadgroup"}` をテストへ pin した。
- 再発検知: 変異 MUT-B1 (`| ` 前置形を外す) と MUT-A2b (marker を failure digest より前へ移す)、
  および親が land 前に `--force-dispatch` で回す配線 probe。

### {{F:digest-truncates-expected-nodes}}. 失敗要約の予算超過で期待 node の完全集合が得られない [手順漏れ]

- 事象: 波及の大きい変異 (MUT-C3、land が `serial` を拒否する正例) は 64 件を赤にしたが、
  failure digest は 48 KiB 予算で 12 件しか描画せず 52 件を省略した。DW-M08 が要求する
  「期待 node は完全集合」は、job stdout からの抽出では**原理的に満たせない**。
  再登録して再走しても MISMATCH が続く。
- 根本原因: 変異の設計時に波及件数を見積もらず、共有 receipt factory を経由する層へ
  単一 literal の変異を当てた。DW-M08 の node 抽出は digest の描画結果に依存する。
- 恒久対応: 変異の runner 範囲を `-k` で当該契約テストへ絞り、赤の件数を digest 予算内へ
  収めてから完全集合を採る (本 wave の spec-c4 が実例)。生 ledger は
  `/work/1/SFC/tanab/dev-wave-jobs/t1062-acceptance-scheduler/mutation/` に残す。
- 再発検知: `IZANAGI_FAILURE_DIGEST_ACCOUNT` の `omitted_failures` が 0 でない変異走行を
  「完全集合が採れていない」と読む (本 fragment がその読み方の正本)。

### {{F:signal-restore-test-family-flake}}. signal 復元系テスト族のフレークを単発と誤認した [テスト代表性]

- 事象: entry 541 は `test_public_main_real_signal_after_success_uses_restored_handler` の
  1 件をフレークとして起票した。本 wave で同一コマンドを 4 回走らせたところ、3 走は緑で、
  赤になった 1 走は毎回**族の別のテスト**だった
  (`test_public_main_failure_restores_handler_without_release`、
  `test_signal_after_core_success_uses_restored_real_handler`)。単発ではなく族の性質である。
- 根本原因: 実 signal を扱う subprocess テストが 48 worker の並列下で timing 競合する。
  1 件だけを見て「その node のフレーク」と結論した。
- 恒久対応: [T-1066] を族として更新し、変異検査では族を含む file を runner 範囲から外す
  (含めると期待 node の完全集合が原理的に安定しない)。
- 再発検知: 変異 baseline の赤 node が走行ごとに族内で移動すること。本 wave の
  `ledger-c2.json` と `ledger-c3.json` の baseline が実例。

### {{F:marker-breaks-exact-tail-contract}}. conftest の出力を 1 行増やして別機構の末尾契約を壊した [テスト代表性]

- 事象: 実効 scheduler の marker を `pytest_unconfigure` の最後 (failure digest より後) に出した
  結果、`test_pytest_failure_digest.py::test_e2e_real_conftest_digest_has_real_failures_and_exact_account`
  が赤になった。同テストは digest の END 行が stdout の**末尾**であることを要求している。
  受入全走で初めて出た。段 3 と段 6 の敵対レビュー計 4 本は、いずれも「marker が既存 consumer と
  衝突しないか」を明示的に検査したうえで**衝突なしと結論していた**。
- 根本原因: conftest は全 pytest 走行に効くため、出力を 1 行増やすだけで、出力の末尾や総量を
  exact に検査する既存 e2e と衝突しうる。焦点走の file 集合に当該 e2e を含めていなかったため、
  受入全走まで検出が遅れた。
- 恒久対応: {{D:effective-scheduler-attestation}} の決定 3 を「digest の直前」へ改め、
  既存契約側は 1 文字も変えなかった。変異 MUT-A2c (marker を digest より後へ戻す) が
  当該 e2e と本 wave のテストの両方で殺される。
- 再発検知: conftest の出力を増減する wave は、焦点走の file 集合へ
  `orchestrator/tests/test_pytest_failure_digest.py` を必ず含める。
