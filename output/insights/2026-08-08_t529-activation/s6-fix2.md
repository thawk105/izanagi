実装は完了しました。ただし pytest は Pegasus dispatch preflight の `qstat -Q` 障害（rc=16）で開始できなかったため、全所見を `partial（実装済み・未実走）` と判定します。receipt 側、`env_contract.py`、`execution_guard.py`、docs、commit には触れていません。

変更後の挙動:

- T419 は不足していた import 閉包 5 パスのどれかが dirty なら `matched=False`。
- issuer は live directory 外・同一 filesystem の staging fileへ完全書込みと fsync を行い、hard-link no-replace で atomic publish。
- write/file fsync/directory fsync 失敗時は live file と staging residue を回収し、回収成功後は同名で再試行可能。
- 発行成功時は「未有効」を明示し、更新すべき head serial/state hashと「同一 commit＋全 process 再起動」を出力。
- source head 定数を変更しない production loader の tail削除・valid suffix負例と、leafへ定数を渡す spy を追加。
- ever-active は generic chain の完全 unionと、実 catalogの g1→g2→g1 後のg2歴史解決で固定。
- 歴史較正は archive-based source-stage で、current g2は成功し、欠落・改変したhistorical g1だけがresolverで拒否されることを固定。
- import-I/O監視をopen/stat/read/list系へ拡張し、worktreeとsource-stageを別subprocessで検査。
- 恒真な`terminal_rows` assertを除去。受理集合は変更していません。

所有外への静的波及:

- `env_contract.py`のloader/resolverは新テストの対象ですが、実装は未変更。
- `qualification/contract.py`のidentity集合をT419テストから読み、追加5パスが同正本に含まれることを確認。未変更。
- 新規T419 manifestの`related_paths`には5パスが追加されます。既存成果物は書き換えていません。
- calibration artifactは一時source-stage内だけで破損させ、worktreeの実体は未変更です。

## 総括

### 1. 所見対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| R4 T419 dirty scope | partial | 5パス追加、各パス単独dirty負例とidentity正本照合を追加。pytest未実走 |
| R5 issuer atomic publish | partial | 外部staging、hard-link no-replace、fsync、失敗回収・再試行を実装。pytest未実走 |
| R6 head更新・再起動契約 | partial | 成功出力/help/docstringとfresh-loader拒否テストを追加。pytest未実走 |
| R7 production head pin | partial | source定数不変のtail/suffix負例と引数spyを追加。pytest未実走 |
| R8 ever-active downgrade保持 | partial | exact unionと実catalog downgrade後g2 resolveを追加。pytest未実走 |
| R9 serial診断の冗長性 | partial | productionコメント、head全体の拒否、同serial・別valid state反例へ強化。pytest未実走 |
| R10 歴史較正の検出力 | partial | private cache観測に加え、実loader/resolverの欠落・改変負例を追加。pytest未実走 |
| R11 import-I/O検出力 | partial | open/stat系を広く監視し、2種類のsource layoutを別subprocess化。pytest未実走 |
| R12 恒真assert | partial | assertを除去し、非空loop末尾の`rows`を直接使用。pytest未実走 |
| regressed | 静的にはなし | compileall・diff check・限定smoke成功。ただし正式テスト未実走 |

### 2. 変更ファイルと行数

今回のfix単位は5ファイル、net約`+562`行です。

- `env_contract_activation.py`: 397行、`+3/-4`
- `issue_env_contract_activation.py`: 225行、`+109/-25`
- `t419_probe_causality.py`: 4529行、net `+5`
- `test_env_contract_activation.py`: 1019行、開始時598行からnet `+421`
- `test_t419_probe_causality.py`: 1716行、net `+53`

`test_env_contract.py`には今回の変更を加えていません。

### 3. 走らせた検査と結果

- `python3 -m compileall -q` 対象6ファイル: rc=0
- `git diff --check`: rc=0
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- issuer `--help`: rc=0、未有効化・head更新・再起動を表示
- pytest runner:
  - `test_env_contract_activation.py -q -rf`
  - 関連3ファイル `--collect-only -q`
  - いずれもテスト開始前にrc=16、`qstat -Q preflight rc=1`
- pytest外の限定smoke: issuer正常/失敗回収/再試行、head負例、downgrade歴史解決、歴史較正2種、import-I/O 2 layout、T419 dirty 5パスが成功

### 4. 未実走・未達

- pytest node、plain-runner meta-test、関連3ファイル全体は未実走。
- したがって緑・closedは未主張。
- 既知の赤であるT126 tracked-pathと`/tmp/.git`由来5件には到達していません。
- docs編集、commit、provenance監査は指示どおり未実施です。

### 5. 親への申し送り

dispatch復旧後、まず以下を`tools/run_tests.py`経由で実走してください。

- `test_env_contract_activation.py`
- `test_t419_probe_causality.py`
- `test_env_contract.py`
- `test_plain_runner_coverage.py`

特に新規nodeは、issuer失敗3条件、production tail/suffix、head spy、downgrade後g2 resolve、historical calibration 2条件、import-I/O 2 layout、T419 dirty 5条件です。