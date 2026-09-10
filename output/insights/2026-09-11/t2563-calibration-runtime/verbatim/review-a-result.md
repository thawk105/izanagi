## 総括

**比較実験：現候補は NO-GO。must-fix は signal 時の copy 回収 1 件。** 修正後は親の関連テスト・変異検査を経て比較実験へ進めます。**最終採用：時間式と consumer の整合解決、after の効果確認まで NO-GO。**

- **real／P2：signal で全回収を迂回する。**
  `tools/pegasus/certify_calibration.sh:615` の builtin `wait` 中に wrapper 自身が TERM/HUP を受けると、`:86–94` の trap が即座に `exit 128` します。EXIT cleanup（`:95–104`）も copy を回収しません。新しく背景化した `timeout cp` が生存したまま wrapper が終了できます。旧版の foreground command 待機では trap 実行が command 終了後まで遅延するため、これは差分による終了動作の変化です。後段測定への進入はありませんが、「全起動 copy を回収」は満たしません。
  **must-fix：copy 区間の捕捉可能な signal 経路でも、起動済み copy の終了・回収を済ませて非0終了すること。** 汎用 scheduler 改修は不要です。新テスト（`orchestrator/tests/test_pegasus_calibration_workload.py:1370`）は本番 signal trap を含まないため、この経路を検査していません。

- **refuted：通常の copy 失敗で早期終了し、他 copy が残る。**
  `certify_calibration.sh:614–628` は各 `wait` を条件文で扱い、失敗を保存して全 PID を待ちます。複数失敗でも source 順の最初の非0を返します。各 `timeout 120` も維持されています。

- **refuted：pristine／build／単独測定の境界が崩れる。**
  全成功後だけ既存 verifier（`:630–650`）、CCBench fresh worktree（`:652`）、同期 configure/build（`:722–723`）へ進みます。測定前の descendant 検査（`:739`）も残っています。固定された source と通常終了を前提に、受理条件の追加・削除はありません。新テストの成功 barrier と失敗時 verifier 不実行検査（`test_pegasus_calibration_workload.py:1416–1439`）もこの構造に対応します。

- **refuted：失敗コード 2 → 下位非0で既存 consumer が壊れる。**
  実読した範囲では該当 consumer はありません。`submit_certify.sh:223–229` が扱うのは qsub の終了コードです。`collect_receipt.py:116–141` は較正後の成果物を要求し、copy 失敗時は従来からその条件を満たしません。既存の pristine 拒否の `rc=2`（`test_pegasus_calibration_workload.py:1454`）も維持されています。数値変更自体は事実ですが、互換性 blocker の根拠はありません。

既知の時間式不整合は比較実験の追加 blocker にはしません。ただし最終採用には、`certify_calibration.sh:811` の式、`test_pegasus_tools.py:211–214` の固定期待、`orchestrator/calibrator/cli.py:727–732` の予算照合を整合させる必要があります。baseline 成功・実時間短縮だけでは代替できません。

read-only の静的レビューです。編集・テスト実走は行っておらず、緑とは判定していません。
