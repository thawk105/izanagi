## 直した 2 件

現行挙動は、正しい物理値の点を受理し、F718 入力 `raw=1000 / intent=1000` は supply arm が green、meaning arm だけが `decoded-meaning-mismatch` で red となり拒否します。この受理・拒否集合は変更していません。

- fix 1: [test_backoff_sweep.py:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_sweep.py:210)、[test_backoff_sweep.py:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_sweep.py:230)
  - helper と同じ source、request、実 compiler、cmake を使って supply record を生成。
  - `green/requested-default-preprocess-different` を固定。
- fix 2:
  - [test_backoff_overthrottle.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_overthrottle.py:74) で、全継承点の raw 値から物理 µs への写像を固定。
  - [test_backoff_requested_us.py:750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_requested_us.py:750) と [test_backoff_requested_us.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2419-meaning-decl/orchestrator/tests/test_backoff_requested_us.py:753) で、両 wrapper の空写像を固定。

## 追加した assert が固定するもの

- F718 テストは、同じ入力で supply が green、meaning だけが red である正例・負例の両方を持ちます。
- wrapper assert は正しい引数転送を確認する正例のみです。拒否動作は production helper の既存 F718 負例と key mismatch 負例が担当するため、wrapper test 内に重複追加していません。
- 既存 assert の削除、緩和、期待値変更はありません。

## 実走した検査

- `git diff --check --` 対象3ファイル: PASS
- 対象3ファイルの Python AST parse: PASS
- 次の nodeid は実装済み・未実走です。Pegasus ログインノードの実行防護が pytest 開始前に拒否したため、green や closed とは申告しません。
  - `test_backoff_sweep.py::test_real_family_helper_rejects_f718_intent_and_evaluator_records_red`
  - `test_backoff_overthrottle.py::test_condition_gate_uses_backoff_flags_from_imported_genomes`
  - `test_backoff_requested_us.py::test_driver_gate_wrappers_bind_fixed_and_requested_us_macros`
- テストの新設・改名はないため、制約 meta-test の追加対象はありません。

## 波及の静的列挙

- production helper の caller 閉包は sweep、extended、profile、repro、overthrottle、requested-us の6 driver、7呼び出しです。production コードは変更していません。
- 所有外経路には T2228 driver-gate liveness probe、screening、compiler-binding consumer がありますが、今回の変更は既存テストの assert 強化だけなので実行挙動への波及はありません。
- 共有 fixture は `condition_meaning_gate/supplied`、同 `stock`、`effectuation-ignored` と実体化 helper です。変更していません。
- 関連 consumer test は extended、profile、requested-us、overthrottle、repro、screening opt-in、P2.2 site-aware、compiler-binding、condition-meaning-gate 系です。

## 申告と実物の対応

- 今回編集したのは指定された既存テスト3ファイルだけです。
- `orchestrator/campaign/`、docs、patch、freeze、台帳、禁止対象は変更していません。
- 新しい test file、commit、push、git 状態を変更する操作はありません。
- worktree に先行して存在する実装差分には触れていません。

## 総括

裁定された2件の assert 強化を完了しました。  
F718 の赤理由は meaning mismatch だけに固定されます。  
両 wrapper の新しい物理 intent 引数も固定されます。  
静的検査は PASS、pytest は実行防護により未実走です。