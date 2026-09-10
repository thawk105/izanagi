# T-2581 / T-2548 / T-2182 — 新pinでK2評価がcertifiedへ到達

D1936項1・2に従い、段4ループの新規試行を承認済み完全SHAへ固定した。既存Pegasus経路から測定WAL限定K2入力を1本投入し、現行verifier v2でterminal verdictを取得した。前回の4条件は今回の新規試行について4/4となった。

## 実測

| 項目 | 結果 |
|---|---|
| 固定superproject | `55d0f239945d34eaf39de500f076f332dc7e20b3` |
| CCBench | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| request / node | `990027.nqsv` / `bnode013` |
| Created / Started / Ended (JST) | 2026-09-10 12:51:54 / 12:54:30 / 12:55:32 |
| 会計Elapse | 67S（外側のqueue待ちを含まない） |
| campaign | `p3-s4-loop-s4-autonomous-409e13f8` |
| variant | `8a84a7b00103` |
| verdict | `serializable`、`certified=true` |
| commits / aborts / anomalies | 466113 / 81919 / 0 |
| 終端 | 1 committed / 0 aborted / 0 skipped、iteration=1、outcome=certified |
| trace / perf実行体 | `7d410c650c5170bd` / `2074fa5e7202a7ed` |
| fitness / CV | 713068 tps / 0.0058189437641328196 |

`verify[legacy]`のlegacyは既存workload設定名である。trace v1を受理した意味ではない。
現行parserはv1の5-field C recordを拒否し、read/write件数を含む7-field recordを要求する。
verifier・K2指示検出・anomaly時rejectは変更していない。`verify_done`の後に`bench_done`、最終`commit`がある。

## K2と候補の束縛

前回の`knowledge-manifest-wal-only.json`と`proposal-wal-only.json`を無変更で使った。
ファイルhash・投入条件は`run-card.md`。新しいrole生成や比較armは追加していない。

- manifest受領証は測定WAL1件を`git-blob-at-commit-path`でverifiedと記録する。
  digestは`396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e`。
- WAL `build_start`は同レコード内で、完全指定pin、`coder-authored` build admission、候補の
  `src_token=4a826c66bc5d883c7b3875adb429beec1c8260b92f3ad7a19544ff5af020ff71`、
  manifestとsource commit/path/sha256を束縛する。
- 最終commitのverifier evidenceは`serializable/certified=true`で、result hashは
  `c30cf281c7fc7e6b375b2056065ff6538370e49edd807179d1f450cc652278d4`。
- 旧campaign `1bebed32`は変更していない。新pinをidentityへ含めた新campaign `409e13f8`で評価した。
  variantとsrc_tokenは前回と同じであり、stock以外の既存値20の候補を再評価した記録である。

4条件のうち、受領証・候補provenance束縛・stockと異なるidentityに加え、今回terminalも得た。
job rc=0だけを根拠にしていない。前回のtrace-parse-errorや過去判定を遡及的にcertifiedへ変えない。

## 実装・レビュー・関連検査

実装面は隔離Codex authorが書いた5fileの13行置換だけ。完全pin literal、既存shell述語の40桁整合、
通常on/offとB4 baseの直接依存golden、job helper2値を更新した。親は限定patchを統合した。
独立相談2本と独立レビュー2本は採用範囲に修正必須所見なし。通常/B4の新旧goldenとK2 identityは
本体factoryを使わない正準JSON/SHA-256計算でも一致した。

- `test_p3_s4_loop.py`: 411 passed、56.66s。
- `test_p3_b4_closed_critic.py`: 72 passed、28.69s。
- `test_p3_s4_loop_job_contract.py`: 80 passed、7.42s。
- 参照関係で引いたconsumer25file: 2483 passed / 17 skipped、250.74s、request `990029.nqsv`。
  最初のbounded local走は4GiB上限でOOMとなり判定なし。runnerが計算ノードへ自動dispatchした結果である。
- 全て`tools/run_tests.py`経由。上記は焦点検査であり正式受入の代用ではない。
- `check_codex_agents.py`、`check_docs.py`: rc=0。runbookのliteral再掲lintはPIN記号参照に直して再検査した。
- 実装commit後の全史provenance: 9436件、新規違反0、既知履歴違反56件。

stubを含むjob正例の緑はshell/argvまでの証拠で、実HEAD接続やterminal成立は上記の計算ノード実走が担う。
過去の所要台帳を新nodeへ付け替えていない。

## 変異検査

`evidence/mutation.json`は2/2 KILLED、期待失敗nodeは各1件で完全一致した。
baselineは2 passed。M1は旧pinへの戻しでfactory identityの不一致、M2は7桁限定への戻しで
40桁K2正例の不当拒否を検出した。M1はidentity固定の感度でありverifier強度の証明ではない。
wrapperもrc=0、`shared_snapshot_matches=true`、`teardown_completed=true`、
`terminal_ledger=true`。使い捨てworktreeを撤去し、dispatch evidenceはrepo外へ退避済み。

## 証拠の所在と主張の範囲

一次資料はrepo外job root `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2581-k2-pin/` に保存した。
`evidence/attempt-0001/`にjob stdout/stderr、compute-result、reservation、事前構築receiptがある。
campaignの原本は同rootの`submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/`。
WAL・campaign lock・既存受領証を直接書換えたり複製していない。

これはrecords=100000/threads=4/extime=1/reps=2の既存配線規模で、`env_tag=pegasus`の単独評価である。
K2知識の性能への因果、比較優越、headline性能、新規CCの研究目標達成は主張しない。
`reproduction_or_selection` / `de_novo_claim=false`の宣言を保つ。
