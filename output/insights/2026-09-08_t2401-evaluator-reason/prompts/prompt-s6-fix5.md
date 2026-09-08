単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling3.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling3.md` — 段 6 裁定 3 巡目
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md` — 段 4 裁定 (設計 v2・不変条件 1〜7。**不変**)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_cli_entrypoints.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/campaign/s8c_preregistration.py` — 参照のみ (変更しない)

repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない・書かない。現在の tip は commit `0906b38d8`。

## 親が実測した事実 (推測ではない)

変異 matrix を 26 件走らせたところ、**2 件が生存した**。どちらも CLI 診断出力の guard を狭める変異である。

- `except Exception` を `except ZeroDivisionError` へ狭める → **SURVIVED (rc=0、失敗 node 0)**
- `except Exception` を `except OSError` へ狭める → **SURVIVED (rc=0、失敗 node 0)**

原因は、この 2 つの test が**guard の有無を区別できない**ことである。

- `test_main_keeps_stdout_and_exit_value_when_stderr_write_raises_oserror`
- `test_main_keeps_stdout_and_exit_value_when_stderr_write_raises_value_error`

どちらも子 process の中で `sys.stderr` を、`write` が例外を出す object へ差し替え、
`raise SystemExit(P.main([...]))` を実行する。そして
`stdout == 期待値`、`returncode == 1`、`stderr == b""` を検査する。

**guard が捕まえなかった場合でも、この 3 つはすべて成立してしまう。**

- 例外が `main()` の外へ出ると Python は未処理例外として終了する。**その終了コードも 1 である。**
- traceback は差し替えた `sys.stderr` object へ書かれるので、**実 fd 2 は空のままである。**
- stdout は診断 loop より前に出力済みなので変わらない。

つまり「guard が効いて `main()` が値を返した」ことを 1 つも観測していない。恒真に近い test である。

## この段の仕事

**この 2 つの test が「`main()` が実際に値を返した」ことを観測するようにする。** それ以外を実装しない。

### 編集してよい file (これ以外を 1 byte も変更しない)

- `orchestrator/tests/test_s8c_cli_entrypoints.py`

`orchestrator/campaign/s8c_preregistration.py` を変更しない。他の test file も変更しない。
新規 file を作らない。docs を編集しない。`git add` / `git commit` / push をしない。

### 実装

1. 子 process の script を、`P.main([...])` の**返り値を受け取ってから**終了する形にする。
   返り値を受け取れたこと自体を、**壊れていない出力先**へ記録する。
   例: 追加の argv で渡した file path へ返り値を書き、`SystemExit(rc)` で終わる。
   `sys.stderr` は差し替えたままにする (それが検査対象である)。
2. test 側で、**その記録が実在し、値が期待する終了値と一致すること**を assertion で固定する。
   guard が捕まえずに例外が外へ出た場合、この記録は作られないので test は落ちる。
3. 既存の 3 つの assertion (`stdout` の完全一致、`returncode`、`stderr == b""`) は
   **そのまま残す**。純増で足すこと。
4. 記録先に stdout を使わない (stdout の bytes 完全一致を壊す)。実 fd 2 も使わない
   (`stderr == b""` を壊す)。一時 file か、それに相当する壊れていない経路を使う。
   揮発する path を期待値へ焼き込まない。

### 変えてはならないもの

- 既存テストの期待値。反転・緩和・skip・削除を禁じる。
- production コード。
- 段 4 裁定の不変条件 1〜7。

### テストの走らせ方 (この sandbox の実測済み制約)

- `tools/run_tests.py` は使わない (dispatch preflight で rc=16 になる)。
- `python3 -m pytest` は使わない (guard が拒否する)。
- 走らせられるのは **`PYTHONPATH=. python3 orchestrator/tests/<file>.py`** の自走 harness だけである。
- **加えて次を必ず自分で確かめて報告に書くこと。**
  `s8c_preregistration.py` の CLI 診断出力の guard (`except Exception`) を**一時的に**
  `except ZeroDivisionError` へ変えて自走 harness を走らせ、**上記 2 test が落ちること**を実測する。
  次に `except OSError` へ変えて、**ValueError 側の test が落ちること**を実測する。
  **確認後は production file を必ず元に戻し、`git diff` で `s8c_preregistration.py` に
  差分が無いことを確かめて報告すること。** これができない場合は「未確認」と正直に書く。

## 禁止

- 上記 1 file 以外の**最終差分**。production の一時変更は上記の確認のためだけに許し、必ず戻す。
- 新規 file の作成、docs 編集、`git add` / `git commit` / push。
- 既存テストの期待値の変更・反転・緩和・skip・削除。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

次の H2 見出しをこの順で使う。

- `## 直した内容`
- `## guard を狭めると落ちることの実測` — 2 通りの狭窄それぞれについて、落ちた test 名と rc
- `## production を元に戻したことの確認` — `git diff` の結果
- `## 実走した nodeid と結果`
- `## 未了・懸念`
- `## 総括`

予算が尽きそうなら、その時点の実装状態をこの出力形式どおりに書いて終われ。無出力が最悪である。
