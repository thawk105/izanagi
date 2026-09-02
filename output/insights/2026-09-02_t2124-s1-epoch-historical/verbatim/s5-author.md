## 変更した file

- [s1_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2124-author/orchestrator/campaign/s1_report.py:302)
  - E0 を局所拒否。
  - 中央 gate の purpose を `HISTORICAL_RAW` へ変更。
- [test_s1_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2124-author/orchestrator/tests/test_s1_report.py:28)
  - production callee を fixture 適用前に保存。
  - 既存 E0 負例を実 production 経路へ変更。
  - v2 historical 正例を追加。

変更はこの 2 ファイルだけです。docs・output は残しておらず、add・commit もしていません。

## 実装の要点

- E0 は `CampaignVerifierEpochRejected` として従来どおり WAL 読取前に拒否します。
- 中央 gate 呼出しを維持し、exact `CampaignReadPurpose` 型検査を残しました。
- 負例の dispatcher は block1 だけ保存済み実関数へ委譲し、例外や E0 診断を合成しません。
- 正例は共有 v2 helper、実 lock decode、記録 commit/blob 検証、実中央 gate を通します。
- 現行閉包取得だけを失敗 seam とし、呼出し回数が前提確認の 1 回だけであることを固定しました。

## 実走した検査

実装済み・pytest 未実走です。

- `orchestrator/tests/test_s1_report.py` 全体
  - `tools/run_tests.py` 経由で起動を試行。
  - `child_started=false`、`child_rc=null`、infrastructure `rc=16`。
  - pytest node 実行数 0、pass 0、fail 0。
- `orchestrator/tests/test_ccbench_spawn_sites.py` 全体
  - 同じ実行容量不足のため未起動。
- 静的検査
  - `git diff --check`: pass
  - 対象 2 ファイルの AST parse: pass
  - U+0300〜U+036F: 0 件
  - `check_codex_agents.py`: pass
  - `check_docs.py`: pass

## 制約 meta-test の洗い出しと結果

- `test_ccbench_spawn_sites.py` は `s1_report.py` を直接 AST inventory 対象にする制約 meta-testです。未実走です。
- node 新設に掛かる追加対象として、`test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` を特定しました。全収集 node と duration ledger の被覆を検査しますが、未実走です。
- `test_update_acceptance_duration_ledger.py::test_t1574_changed_suite_ledger_node_delta_is_exact` の exact 対象 suite に `test_s1_report.py` は含まれないため、今回の適用対象外です。

未実走理由は、Pegasus login の user-slice 使用量が実効上限 14 GiB を超え、最低 local 予算 1 GiBを確保できず、さらに `qstat -Q` が認証・socket error で compute dispatch を開始できなかったためです。

## 波及可能性の静的列挙

- production の直接 caller は同一 module の `_assess_campaign` だけです。`build_report`、`generate_report`、CLI はここから間接到達します。
- `artifact_admission`、replay、oracle、`s1_direct_comparison` の purpose は変更していません。
- 共有 `campaign_lock_test_support.py` は新規正例から利用するだけで、helper 自体や既存 consumer は未変更です。
- `test_s1_report.py` の autouse fixture は既存 node を引き続き固定 E1 に隔離し、対象負例と新規正例だけが実 callee を通ります。
- `test_ccbench_spawn_sites.py` は production source の process-launch inventory consumerです。今回 subprocess site は増えていません。
- 凍結 report を読む provenance test、S8B oracle 系の同名 private helper、中央 gate の他 consumer には直接変更はありません。

## 受理・拒否挙動の変化

- v1 / E0: 変更前後とも `v1-authority-absent` で拒否し、WAL を読みません。
- 正しい v2 / E1、現行閉包取得可能: 変更前後とも受理します。
- 正しい v2 / E1、現行閉包取得不能: 変更前は `E1-stale / current-closure-unavailable` で拒否、変更後は `E1 / recorded-closure` として受理します。
- malformed lock、記録 commit/blob 不整合: purpose 判定前の production 検証で従来どおり拒否します。
- 保存済み COMMIT 証拠検査と中央 purpose の exact 型検査は不変です。

## 赤の内訳

pytest の赤はありません。pytest 子が開始されていないため、期待赤・回帰赤のどちらにも分類できません。

確認できた赤相当は runner infrastructure `rc=16` のみです。原因は login-node のメモリ admission 不成立と compute queue 接続不能です。

## 総括

実装差分は指定された 2 ファイルだけに閉じています。  
E0 拒否と中央 exact 型検査を維持し、S-1 の v2 歴史参照だけを広げました。  
静的検査は成功していますが、pytest は実行環境不足により未実走です。  
作業ツリーには未 commit のコード・テスト差分だけが残っています。