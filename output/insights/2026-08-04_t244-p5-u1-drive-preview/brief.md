# 段 1 brief — [T-244] D121 P5 U-1: `drive` / `preview` 注入の拒否と既存 2 テストの seam 移行

- **scope:** `run_trial` の `drive` / `preview` caller 注入を正式経路で拒否し、これに依存していた
  transport テスト 2 件の注入手段を別 seam へ移す。U-2 (未予約 token) は P3 実装待ちで scope 外
  (並行 wave `wave-t244-p3-redesign` が P3 再設計中)。U-3 は「要求しない」裁定済みで実装なし。
- **確定済みユーザー裁定 (canonical = worklog (171)、選択肢定義 = p5-injection-gate/s4-adjudication.md §4):**
  U-1 塞ぐ / U-2 P3 receipt 依存・自前 token 禁止 / U-3 digest registry 不要・「session 共有を閉じた」と名乗らない。
- **前提実測 (main 4f0d020 = worktree base。実測は 2f04d6b 時点だが 2f04d6b..4f0d020 は docs のみでコード不変を確認済み):** 成功期待で claude-headless + drive/preview 注入する呼び出しは
  `test_claude_transport.py` の 2 件のみ (:1408 P1 flag-off、:1473 P2 flag-on。いずれも module 属性
  monkeypatch を既に併用)。fixture 経路の注入は 3 テストファイルで多数が正当利用。production 呼び出し元は
  CLI `main()` のみで両 kwargs を渡さない。既存 P5-1 gate は `p3_autonomous_workload_trial.py:1550`。
- **純増検出力:** D148 決定 (2) が明示的に未閉とした「正式 provider を名乗る run の世代 loop driver を
  caller が差し替える」経路の拒否。既存被覆 0 (性質検索で拒否側テストなし、2 件は許可へ依存)。
- **成果物影響 (DW-G05):** 実装しなければ、試行台帳に `provider="claude-headless"` と記録された run の
  attempts.jsonl / report.json の世代記録が caller 注入の偽 drive/preview 由来でありうる。実装により
  同呼び出しは artifact 作成前に拒否され、試行台帳の受理集合が狭まる (certified 選択・proof chain の値は不変)。
- **不変条件:** 正しさゲートを緩めない (既存 P5-1・transport gate・fixture 経路テストの検出力は不変)。
  受理集合の縮小ゆえ D96 (新 D + 境界テスト同時更新を同一変更単位)。「P5 を満たした」と名乗らない
  (U-2 未実装のまま)。token/receipt/reservation の語を新設しない。凍結成果物 bytes 不変
  (freeze/oracle/proof chain 非接触 — DW-O08/O09 評価済み、pin 検索は段 2 プランで対象 file 確定後に再確認)。
- **provisional 裁定 (攻撃対象):**
  (P1) 拒否は D148 決定 (1) の正式判定 `provider_kind == "claude-headless"` に限り、fixture 注入は残す。
  (P2) 別 seam = 2 テストを kwargs 注入から module 属性 monkeypatch へ移す。`run_trial` に新公開
  kwargs・opt-in flag を足さない (恒真化・受理拡大を作らない)。
  (P3) `drive` / `preview` kwargs は signature に残し fixture 24+ 箇所を壊さない。注入検出は
  sentinel 既定値等で行い、既定値関数 object の同一性比較に依存しない (実装子が具体化)。
  (P4) internal entrypoint (`_run_workload` 等) と `drive_iteration()` 直接反復は D114 どおり保証対象外のまま。
- **成果物の形:** production 1 file (`p3_autonomous_workload_trial.py`) + テスト更新
  (`test_claude_transport.py` 2 件の seam 移行、境界テスト新設/更新) + 新 D fragment + worklog fragment。
- **分割方針:** 軽量版だが受理集合が変わるため段 2・3・6 の敵対検証子は省かない。実装子 1 本
  (面が単一 file + テストで所有分離の必要なし)、段 3 レンズ 2 本、段 6 レビュー 2 本。
- **受入・実測環境:** worktree `dev-wave-t244-p5-u1-drive-preview` で `tools/run_tests.py`
  (cwd = repo root、DW-O18)。対象走 = `test_claude_transport.py` / `test_p3_autonomous_workload_trial.py` /
  `test_autonomous_trial_completeness.py`、受入全走は段 6/9。
