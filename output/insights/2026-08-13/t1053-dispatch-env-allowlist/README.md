# [T-1053] 非帰属 checker の実運用到達の閂 — dispatch env allowlist へ 1 語

- wave: `dev-wave-t1053-t1066` (branch `worktree-dev-wave-t1053-t1066`)
- base main: `48b2caab`、実装 commit: `fb7e204f`
- 裁定: 第 11 回 rulings #1 (a) (2026-08-13 16:56 JST 確定)

## 何が閂だったか

`tools/check_acceptance_reds.py` は probe worktree の指紋が **ignored file も含めて完全に空**である
ことを要求する。ところが checker 自身が probe worktree の中で pytest を dispatch するため、
計算ノードが `__pycache__` を書き、指紋が破れて `status=invalid-input` / `rc=2` になっていた。

checker は `PYTHONDONTWRITEBYTECODE=1` を**既に**子環境へ渡していた
(`tools/check_acceptance_reds.py:683-690`)。落ちていたのは producer 側で、
`dispatch_compute.py:1341-1345` が `env_allowlist` に無い key を黙って濾していたためである。

## 変更

production は `TASKS["tests"].env_allowlist` への 1 語 + comment 1 行のみ。
指紋 gate の受理集合 (空 tree の hash だけを受理) は不変で、
`test_ignored_artifact_from_node_fails_closed` の期待値も無改変である。

検証は 3 層。

1. 閉じた列挙の exact pin (`test_tests_task_env_allowlist_is_exact`) を更新。
2. request env への projection を検証専用テストで固定 — 実運用値 `"1"`、allowlist 外 key の不在、
   値の passthrough (sentinel)。
3. `_job_run` が子環境へ同じ値を渡すことを sentinel で固定 (段 6 レビュー A の所見を閉じたもの)。

## 値の意味論 (親の実測、Python 3.10.12)

| 環境変数の値 | `sys.dont_write_bytecode` |
|---|---|
| 未設定 | False |
| `""` | False |
| `"0"` | False |
| `"1"` | True |
| `"no"` (任意の非空文字列) | True |

つまり伝播は**単調**であり、追加前より bytecode 残骸が増える値は存在しない。
段 3 レンズ A の blocker (値が拘束されないため監査の意味論が未束縛) は、
この実測を根拠に minor へ格下げした。値契約と receipt への environment 束縛は次の一手。

## 変異 matrix (2026-08-13、計算ノード、runner = 変更 test file 全体)

| ID | 変異 | 結果 | 殺したテスト |
|---|---|---|---|
| baseline | なし | PASSED (141 passed) | — |
| MUT-1 | allowlist から 1 語削除 | KILLED | projection test / exact pin |
| MUT-3 | request env の値を `"1"` へ固定正規化 | KILLED | sentinel passthrough |
| MUT-4 | `_job_run` で `child_env` から当該 key を落とす | KILLED | 子環境 projection test |

SURVIVED 0 / MISMATCH 0、事前登録と完全一致。生 ledger は `mutation-result.json`。

## 効いてくる時点 (段 6 レビュー B の指摘)

非帰属 checker は `tested_main` の checkout の `run_tests.py` → `dispatch_compute.py` を使う
(`tools/check_acceptance_reds.py:1194-1205`、`tools/run_tests.py:53-56`)。
したがって**この commit を `tested_main` に含む次以降の wave から**閂が外れる。
本 wave 自身の赤経路は救済しない。

## [T-1066] を実装しなかった理由

「受入投入前に ignored file を撤去する 1 行」は、code 上どの検査の赤も防がない。

- `--probe-root` は repo と全登録 worktree の外を起動時に強制する
  (`tools/check_acceptance_reds.py:1376-1416`)。
- 指紋は毎回 `git worktree add --detach` で作る fresh probe worktree だけを見る (`:772-799`、`:1194-1266`)。
- `tools/run_tests.py` / `tools/dev_wave_wait.py` / `tools/dev_wave_land.py` の各検査は
  ignored file を見ない。
- `output/pegasus-dispatch/` の無限定撤去は投入停止ラッチ `submission-disabled.json`
  (`tools/pegasus/dispatch_compute.py:1348-1352`) と他 invocation の receipt を消しうる。

`DW-S04` に従い親は不採用にせず、新事実を添えてユーザー再裁定へ返した。
