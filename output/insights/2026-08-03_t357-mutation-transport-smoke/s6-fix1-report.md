[submit_leg2_bundle.sh](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/submit_leg2_bundle.sh:30) だけを修正しました。leg 2 の再実行はしておらず、緑は主張しません。

### 診断結果

親の診断は正しいです。

- [attempt1/leg2-ledger.json](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/attempt1/leg2-ledger.json) の baseline stdout では、外側 pytest worker は `/usr/bin/python3.10`、Python 3.10.12 です。
- baseline は `19 failed, 5244 passed, 19 skipped` で停止し、失敗 node はすべて `orchestrator/tests/test_t126_pegasus_tools.py` でした。
- stdout には、入れ子で起動した submitter が `@dataclass(..., slots=True)` を読み、`TypeError: dataclass() got an unexpected keyword argument 'slots'` で終了した証拠があります。
- 当該 submitter は bare `python3` を多数使用します。旧 bundle は harness と `run_tests.py` にだけ `/usr/bin/python3.10` を明示し、PATH を正規化していませんでした。
- 一方、[dispatch_compute.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/pegasus/dispatch_compute.py:339) は候補選択後、その dirname を PATH 先頭へ置いています。この差で入れ子 subprocess の interpreter が変わり得ます。

### `_job_script` との差分棚卸し

| 旧 bundle に無かった項目 | 対応 |
|---|---|
| `python3.10` → `/usr/bin/python3.10` → `/bin/python3.10` の順で `command -v` 選択 | 同じ順序で写した |
| 各候補自身による Python 3.10 以上の probe | 写した |
| 各候補自身による `pytest`, `xdist`, `packaging` import probe | 写した。外部 probe file ではなく同等の inline source |
| 選択した interpreter の dirname を PATH 先頭へ export | 写した |
| task-run 3 変数の unset | 旧版にも存在。PATH 設定後へ移し、維持した |
| compute-visible marker の原子的発行 | 写していない。bundle には dispatch submission directory/result protocol がなく、指定された stdout 診断で代替 |
| stage 付き `write_failure` result JSON | 写していない。既存の `leg2.rc` と rc 16/17/18/90–94 の契約を変更しないため |
| `REQUEST` を読み `exec ... --job-run` する経路 | 写していない。bundle は固定 harness の直接実行であり、`exec` すると終了後の clean/HEAD 検査が消えるため |
| nonce 由来の job name、`RESULT/PROBE/REQUEST/DISPATCHER/MARKER` 配線 | 写していない。単一固定 g01 bundle の成果物配置とは別の dispatch protocol のため |
| FQDN を明示した厳密な hostname regex | 写していない。指示どおり既存 hostname 検査を逐語維持した |

旧版にもあった PBS project/queue、`set -u`、cwd、Python 関連4変数の unset は維持しています。

### 診断出力

harness 起動直前に以下を stdout へ出すようにしました。

- `command -v python3` と version
- `command -v python3.10` と version
- 選択 interpreter の絶対 path と version
- PATH
- hostname

診断コマンドの失敗は `|| true` とし、合否条件には加えていません。候補選択時の version/module probe は従来どおり rc 16 の fail-closed 条件です。

### 静的確認

- 修正後は99行、実行 mode は755です。
- `bash -n` は成功しました。
- hostname、HEAD = anchor、clean tree、`--out` 未存在、spec SHA、および終了後の status/diff/HEAD 検査を維持しています。
- rc 90/91/92/93/94/16/17/18 の区別も維持しています。
- 現在 `g01/leg2-ledger.json` と `g01/leg2.rc` は未存在です。
- job worktree は clean、HEAD は `ea6ca433eb83d666ec64f3629cc35c769a2b5c19` です。

[compare_verdicts.py](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:1) は変更していません。leg 1 ledger は、比較器が要求する baseline `PASSED`、3 mutation、4比較 field、repo HEAD、spec SHA、5281 collected nodes をすべて持ち、静的には適合しています。問題は見つかりませんでした。leg 2 が未存在なので比較器の実行は未確認です。

### 残る非等価性と次の失敗候補

dispatch 経路にあり bundle 経路に残っていないものは次です。

- compute-visible marker、request/result schema、stage/error/interpreter を持つ原子的 result JSON
- task 閉集合、argv/environment の型検査、task 別 module probe、requested environment の適用
- dispatcher receipt、scheduler/accounting・stdout/stderr 回収
- `bootstrap` / `child` / `child-launch` の失敗分類
- `sys.executable` を再解決して子を起動する二層 launcher
- 厳密な FQDN 対応 hostname 検査
- dispatch の個別 child 実行に対し、bundle は一つの PBS allocation 内で collection・baseline・全変異を連続実行する構成

したがって次に落ち得る点は、module の単純 import 後に判明する version/plugin 非互換、PATH 以外の PBS 環境差、意図的な fake-bin PATH を使うテスト、単一 allocation 固有の資源・時間上限、baseline 後の変異結果差、dispatch receipt/accounting を持たないことによる診断不足です。

pytest、harness、leg 2、比較器、`check_codex_agents.py`、`check_docs.py`、provenance 監査は未実行・未確認です。repo の `git status --porcelain` は空で、repo tracked file は一切編集していません。本 turn の書き込み対象は上記 bundle script 1ファイルだけです。

## 総括

- 候補順・version/module probe・PATH 先頭化を dispatch と等価にした。
- harness 直前に interpreter、PATH、hostname の診断を追加した。
- 親の診断は正しい。
- 修正後は99行で、既存検査と rc 区分を維持した。
- 残る差1: bundle には dispatch の request/result・marker・receipt/accounting がない。
- 残る差2: bundle は単一 allocation の直接 local harness で、`_job_run` の閉集合 launcher を通らない。
- leg 2 の再走結果は未確認であり、緑は保証しない。