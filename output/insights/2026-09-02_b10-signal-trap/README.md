# b10 job script の signal handler が set -u で落ちていた件

対象: `tools/pegasus/b10_backoff_shape_campaign.sh` の `on_signal`。
一次資料: `docs/worklog.md` エントリ 1186 機構欠陥 4 (実測 = `965996.nqsv` の scheduler.stderr)、
`output/insights/2026-08-31_t1905-b10-formal-run/README.md`。同エントリは「本 wave では未修正」と明記していた。

## 何が壊れていたか

```
on_signal() {
  local name=$1 number=$2 rc=$((128 + number))
  ...
}
```

bash は `local` を builtin として実行する。builtin の引数は**実行前に一括して語展開される**ため、
`number=$2` という代入が効くより先に `$((128 + number))` が評価される。script 冒頭の
`set -Eeuo pipefail` により `number` は未設定変数として扱われ、handler は即座に落ちる。

結果として `write_failure` に到達せず、SIGTERM / SIGINT / SIGHUP による強制終了の理由が
`$ATTEMPT_DIR/failure.json` に一切残らない。walltime 打ち切りもこの経路を通るため、
balanced の 6 時間打ち切りでは「なぜ終わったか」が失われた。

## 親による独立再現 (2026-09-02、Pegasus login node)

同じ形の関数を `set -Eeuo pipefail` 下で `on_signal TERM 15` として呼んだ結果。

| 版 | 終了 status | `write_failure` へ渡った引数 | stderr |
|---|---|---|---|
| 修正前 (1 文形) | 1 | 呼ばれない | `number: 未割り当ての変数です` |
| 修正後 (2 文形) | 143 | `['143', 'signal', 'received TERM']` | なし |

## 直し方

`local` を 2 文に分け、算術評価の前に `number` を確定させる。handler の他の行、trap 設置行、
`write_failure` の実装、job script の受理集合は変更していない。

## 族の広がり — 走査結果

同型欠陥 (同一の `local` / `declare` / `typeset` / `readonly` / `export` 文の中で、先行して代入される
名前を後続の代入の右辺が参照する) を `tools/`、`orchestrator/`、`hooks/` の全 shell script
(`.sh` / `.pbs` / shebang 付き file) へ機械走査した。**hit は当該 1 行だけ**である。

`tools/pegasus/` の姉妹 handler は以下のとおり既に健全で、いずれも `local` を分けているか、
算術を同じ文へ入れていない。

| script | handler | 形 |
|---|---|---|
| `floor_campaign.sh:451-454` | `on_signal` | `local` 3 文に分割 |
| `acceptance_nproc_study.sh:115-117` | `on_signal` | `local` 2 文に分割 |
| `certify_calibration.sh:86-91` | `on_signal` | 引数 1 個、算術なし |
| `mocc_trace_pilot.sh:158-163` | `on_signal` | 引数 1 個、算術なし |
| `t126_qualification.sh:350-355` | `on_signal` | 算術は `local` の外 |
| `t141_region_profile.sh:225-229` | `on_signal` | 引数 1 個、算術なし |

`DW-G03` の族一般化条件 (異なる producer/consumer での独立 2 例) は成立しない。したがって
検査 tool の新設も他 script の予防的書き換えも行わず、局所修復に留めた。

なお `on_err` (同 file) は `local rc=$? line=${BASH_LINENO[0]:-unknown}` であり、
`$?` も `BASH_LINENO` も展開時点で解決されるため同型ではない。`CURRENT_STAGE`・`PY`・
`ATTEMPT_DIR` はいずれも trap 設置より前に初期化されている。

## 既存テストが取り逃していた理由

`test_pegasus_submit_and_job_scripts_are_syntax_valid_and_use_pbs_contract` は
`assert "on_signal" in job_text` という**存在検査**しか持たない。壊れた handler も
`bash -n` の構文検査を通り、文字列としても存在するため、この gate は恒真に近い。

追加した `test_pegasus_job_signal_handler_records_failure_and_exits_with_signal_status` は
production file から `on_signal` の実体を一意に切り出して実際に実行し、`write_failure` へ渡る
引数と終了 status を見る。handler の本体をテスト側へ書き写していないので、production を壊せば
テストが赤になる。

## 凍結・受理集合への影響

- この script の sha256 を静的に pin する箇所は repo 内 (`output/` 以外) に無い。
  `job_script_sha256` は投入時に計算され、submission と result の間でのみ照合される runtime 束縛で、
  過去 receipt は当時の bytes を記録した履歴である (絶対規律 7)。
- `pegasus-b10-job-failure/v1` を読む消費者は repo 内に存在せず、producer 1 箇所のみ。
  したがって自動判定の受理集合は変わらない。変わるのは、強制終了時に理由が残るかどうかだけ。
- `test_official_perf_closure.py` の登録は path 単位の allowlist、`test_hooks.py` の
  `dispatch-required` は実行場所の分類で、いずれも内容に依存しない。

## 変異検査

事前登録は実装前に確定し、anchor は最終 commit `2d6f2dbf5b42e86e794b900e5a083e8658ef0592` に対して
再検証してから本走した。spec = `mutation-spec.json` (sha256
`24526170ca87b6aef0cc60a2edf9f19ede5b11ab98229b9506970cf5680e1fd8`)、報告 = `mutation-report.json`。

| id | 変異 | 期待 | 結果 | 赤になった node |
|---|---|---|---|---|
| M1-restore-single-local-assignment | 修正を 1 文形へ戻す | KILLED | **KILLED** | `test_pegasus_job_signal_handler_records_failure_and_exits_with_signal_status` |
| M2-shift-signal-status-base | `128 + number` を `1 + number` へ | KILLED | **KILLED** | 同上 |

baseline は PASSED (rc=0)。registered=2 / completed=2 / matching=2 / SURVIVED=0 / MISMATCH=0。
期待 node は完全集合で一致した。

単一理由性: 壊れた形も `bash -n` を通り、既存の `assert "on_signal" in job_text` も通る。
`128` は同 file 内で当該 1 箇所だけである。したがって両変異を赤にできる層は新設の挙動テストだけで、
前後に同じ入力を拒否する層は無い。

**1 回目の走行 (attempt 1) の記録。** 変異結果は attempt 2 と同一 (両変異 KILLED、baseline PASSED、
matching=2) だったが、wrapper の走行後検査「source/main 共有木の観測 bytes が不変」が不成立で
中止した。並行 wave が共有 checkout を触ったためであり、harness 自身の検査 (固定 HEAD 束縛、
復元時の内容比較、`flock` 単一走行、逐次 flush) はすべて通っている。中止後に source worktree が
clean で HEAD と修正 bytes が保たれていることを確認し、attempt 2 を走らせた。attempt 2 は
`shared_snapshot_matches=true`、`child_rc=0`、`teardown_completed=true` で完走した。

## 受入

`tools/dev_wave_wait.py acceptance` の全走。

| 項目 | 値 |
|---|---|
| verdict | `child-green` |
| tested main | `813b4cc963eedb6c2c5915f50316e0636993347a` |
| tested tip | `75be196375d7ffca24a93d0d6be82009b2bae1a8` |
| 結果 | 19773 件収集、19681 passed、92 skipped |
| effective scheduler | `loadgroup` |

焦点走 (受入前): 変更した test file 単独走 = 87 passed、変更した production file を参照する
consumer test (`test_hooks.py`、`test_official_perf_closure.py`) = 464 passed / 1 skipped。
AI provenance 全史監査 = 7673 件、新規違反なし。

本 insight を含む記録 commit の後に、その tip を束縛する受入を改めて走らせて land する。

## 計算資源の実測 (この wave の運用記録)

計算ノードの queue と login node のメモリが同時に飽和しており、焦点走は 3 回連続で
`queue-wait-timeout` (rc=16) になった。実測値: 実効天井 15.03 GB に対し回収不能量 7.79 GB、
他 wave の生存予約 6.47 GB で、`grant_budget()` は負の予算を返して必ず dispatch を選ぶ。
同時刻の queue には同一アカウントの `izdw-*` が 7 件たまっていた。混雑由来の rc=16 は
自分の差分に帰属しない。1 度だけ `qstat -f` 自体が 30 秒で応答せず失敗した。
いずれも orphan hold の規定手順 (qstat で不在を確認 → source の clean/HEAD 確認 → hold を手動削除)
で解消し、再投入で通した。

## 逐語の正規化 erratum

`verbatim/s5-author.md` は実装子の最終メッセージそのままでは行末空白を 1 行含み
`git diff --check` に触れたため、可視文字を変えない最小正規化 (各行の行末空白除去) を施した。

| 項目 | 値 |
|---|---|
| 原文 sha256 | `f143f00b4d97d08d767baf64e32eeef0c2ac4724fe8b64353ed2cc07948eb8d9` |
| 原文 bytes | 3700 |
| 正規化後 sha256 | `a93bd83c03e981b8e909a3d14da3cc10170b17c1ded944346f8d835784b0a3be` |
| 正規化後 bytes | 3698 |
| 変えた行数 | 1 (Markdown の 2 space 改行) |

復元法: 3 行目 (`[tools/pegasus/b10_backoff_shape_campaign.sh](...:107) は ... 修正しました。`) の
行末へ半角空白 2 個を戻すと原文 bytes と sha256 に一致する。
