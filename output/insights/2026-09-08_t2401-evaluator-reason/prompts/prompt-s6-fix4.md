単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling3.md

## 必読事項の射影

次の絶対パスだけを読む。読めなければ即停止し、その旨だけを出力する。

- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s6-ruling3.md` — 段 6 裁定 3 巡目 (敵対 fixture の arm/disarm)
- `/home/SFC/tanab/.claude/jobs/78b62369/tmp/t2401/s4-ruling.md` — 段 4 裁定 (設計 v2・不変条件 1〜7。**不変**)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason/orchestrator/tests/test_s8c_preregistration_core.py`

repository の root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2401-evaluator-reason` である。親側の `/work/1/SFC/tanab/izanagi` を読まない・書かない。現在の tip は commit `f3ca08c39`。

## 親が実測した事実 (推測ではない)

変異走行で診断 helper の reason 側 guard (`except BaseException`) を狭めたところ、
**pytest が rc=2 を返した。** rc=2 は「session が中断された」であり、テストの失敗 (rc=1) ではない。
失敗 node 自体は 3 件抽出できている。

```
failed_nodes:
  ...::test_invalid_preregistration_reasons_use_bounded_sentinel_without_leaking[missing-reason]
  ...::test_invalid_preregistration_reasons_use_bounded_sentinel_without_leaking[hostile-reason-property]
  ...::test_diagnostic_reason_guard_catches_keyboard_interrupt
IZANAGI_FAILURE_DIGEST_ACCOUNT failures=3 failed=2 errors=1
```

原因は、guard の負例に **`KeyboardInterrupt`** を使っていることである。guard を外すと
`KeyboardInterrupt` が helper の外へ出て、pytest はこれを利用者による中断と解釈して
session ごと止め rc=2 を返す。変異 harness は rc が 0/1 でないため結果を分類できず停止する。

## この段の仕事

**`KeyboardInterrupt` を、この test file 内で定義した専用の `BaseException` subclass へ置き換える。**
それ以外を実装しない。

### 編集してよい file (これ以外を 1 byte も変更しない)

- `orchestrator/tests/test_s8c_preregistration_core.py`

`orchestrator/campaign/s8c_preregistration.py` を変更しない。他の test file も変更しない。
新規 file を作らない。docs を編集しない。`git add` / `git commit` / push をしない。

### 実装

1. この test file 内に、`BaseException` を直接継承する専用の例外型を 1 つ定義する
   (`Exception` を継承してはならない。`Exception` を継承すると
   「`except Exception` では捕まらない例外」という命題を検査できなくなる)。
   pytest や runner が特別扱いする型 (`KeyboardInterrupt`、`SystemExit`、`GeneratorExit`) を
   継承してはならない。
2. 診断 helper の 2 つの guard (type 抽出側と reason 抽出側) の負例が使っている
   `KeyboardInterrupt` を、この専用型へ置き換える。**`SystemExit` を使っている負例はそのまま残す**
   (pytest はこれを通常の失敗として報告でき、rc=1 になる)。
3. test 名に `keyboard_interrupt` を含むものがあれば、実体に合わせて改名する。
   **固定している命題は変えない** — 「`except Exception` では捕まらない `BaseException` が
   診断抽出の中で出ても、helper は例外を外へ出さず sentinel を返し、
   fail-closed の 12 件 `ERROR` report が返る」ことを引き続き固定する。
4. arm / disarm の構造 (危険な挙動を検査対象の呼び出しの瞬間だけ有効にする) は維持する。
   armed でない状態で `repr()` しても例外が出ないことの assertion も維持する。

### 変えてはならないもの

- 固定している命題、既存テストの期待値 (反転・緩和・skip・削除の禁止)。
- production コード。
- 段 4 裁定の不変条件 1〜7。

### テストの走らせ方 (この sandbox の実測済み制約)

- `tools/run_tests.py` は使わない (dispatch preflight で rc=16 になる)。
- `python3 -m pytest` は使わない (guard が拒否する)。
- 走らせられるのは **`PYTHONPATH=. python3 orchestrator/tests/<file>.py`** の自走 harness だけである。
- **加えて次を必ず自分で確かめて報告に書くこと。** 専用型を使う負例を意図的に失敗させたとき
  (対象 assertion を一時反転させる等)、harness の rc が **1** になり session 中断 (rc=2) にも
  `INTERNALERROR` にもならないこと。**確認後は必ず元に戻し、`git diff` で反転が残っていないことを
  確かめて報告すること。**

## 禁止

- 上記 1 file 以外の変更、新規 file の作成、docs 編集、`git add` / `git commit` / push。
- production コードの変更。
- `Exception` を継承した型で代用すること (命題が変わる)。
- 実走していないものを緑と書くこと。
- 出力に結合文字 U+0300〜U+036F を使うこと。

## 出力形式

次の H2 見出しをこの順で使う。

- `## 直した内容`
- `## 固定している命題が変わっていないこと`
- `## rc=1 になることの確認` — どう確かめたか、rc、反転を戻したことの確認
- `## 実走した nodeid と結果`
- `## production 無変更の確認`
- `## 未了・懸念`
- `## 総括`

予算が尽きそうなら、その時点の実装状態をこの出力形式どおりに書いて終われ。無出力が最悪である。
