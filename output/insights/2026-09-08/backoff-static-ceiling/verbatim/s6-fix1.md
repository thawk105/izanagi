## 実装結果

FIX-1〜7 の指定範囲を4ファイルで修正しました。

- v4 provenance の実値を legacy binding に固定し、行側 `spec_sha256` も v4 と照合。[b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/backoff-ceiling-author/orchestrator/campaign/b10_backoff_shape_sweep.py:2805)
- legacy fixture を独立した v4 literal から生成し、v5 patch binding 混入の負例を追加。[test_b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/backoff-ceiling-author/orchestrator/tests/test_b10_backoff_shape_sweep.py:393)
- codec 全域を独立閉形式で検査し、T-2266 は成果物上の list 分離を検査。[test_backoff_extended_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/backoff-ceiling-author/orchestrator/tests/test_backoff_extended_sweep.py:291)
- D1106 の旧格子を独立 literal で固定し、`load_reference_binding` の実 AST が凍結 helper を2回呼ぶことを固定。[test_backoff_requested_us.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/backoff-ceiling-author/orchestrator/tests/test_backoff_requested_us.py:638)

## FIX 対応表

pytest 子が起動できなかったため、契約どおり `closed` とはしていません。

| FIX | 状態 | 残り |
|---|---|---|
| FIX-1 | partial（実装済み・未実走） | legacy write-heavy / balanced node の実走 |
| FIX-2 | partial（実装済み・未実走） | v4 正例と v5 混入負例の実走 |
| FIX-3 | partial（実装済み・未実走） | codec 0..9999 全域 node の実走 |
| FIX-4 | partial（実装済み・未実走） | D1106 literal・consumer AST node の実走 |
| FIX-5 | partial（実装済み・未実走） | canonical v5 hash と v4 schema 負例の実走 |
| FIX-6 | partial（実装済み・未実走） | config/report list 独立性 node の実走 |
| FIX-7 | partial（実装済み・未実走） | renamed node と命名・ledger meta-test の実走 |

`regressed` と判定した項目はありません。

## 受理・拒否の照合

| 面 | 修正前の実物 | 修正後の実物 | 申告との照合 |
|---|---|---|---|
| legacy write-heavy / balanced binding | 現行 v5 の5値を期待し、記録済みv4行を拒否 | provenance 現物のv4 5値だけを期待 | 一致 |
| legacy 行の `spec_sha256` | 現行 v5 spec と比較 | 凍結 v4 binding の spec と比較 | 一致 |
| legacy 行への v5 値混入 | legacy として受理し得た | exact binding 不一致で即 reject | 一致、正しさ側へ限定 |
| canonical v5 prereg | parse のみで現物 hash 突合なし | patch bytes と `EXPECTED_HOLE_LINE` の双方を実 hash と比較 | 一致 |
| schema 直前版 | v3 の拒否だけを固定 | v4 の拒否を固定 | 一致 |
| static codec | production の受理域は変更なし | 独立式 `µ` / `µ+2000` を全域比較 | 挙動不変、検査強化 |
| D1106 | production 定数を期待値にも利用 | 独立旧格子 literal＋実 consumer 接続を固定 | 挙動不変、検査強化 |
| T-2266 | tuple の処理系同一性を検査 | config/report の別 list と片方向変更非伝播を検査 | 成果物上の性質に一致 |

## 負例の赤理由

追加した v5 混入負例は、v4 行の `preregistration_binding.patch_sha256` だけを現行 v5 値へ変更します。行の canonical content digest と注入する digest 集合は再計算済みで、top-level spec その他の値は変えていません。

したがって落ちる理由は digest 不一致ではなく、凍結 v4 binding との exact equality 不一致です。

## 検査状況

成功した静的検査:

- 変更対象を含む11 Pythonファイルの `py_compile`
- `git diff HEAD --check`
- 変更 test 3ファイルの重複 test 名なし
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

次を `tools/run_tests.py` 経由で投入しましたが、いずれも `qstat -Q` の認証失敗により dispatch 前に rc=16 となりました。実走 nodeid は0件です。

- B-10 canonical v5、v4 schema負例、legacy write-heavy正負例、balanced正例
- codec全域、T-2266 identity/report、D1106 consumer
- `test_plain_runner_coverage.py`
- `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`
- 対象3 test file の collect-only

## 所有外への波及

- `_legacy_*_binding` は同じ production module の legacy validator、report collector、campaign-lock照合から消費されます。
- legacy fixture は `test_b10_backoff_shape_sweep.py` 内だけの共有 fixtureです。
- 3つの rename により `acceptance_duration_ledger.json` の旧 nodeid は履歴値として残っています。coverage meta-testを投入しましたが未実走です。
- Markdown/RST、patch、旧 provenance、旧成果物は今回編集していません。既存 staged docs 差分は保持しています。

## 作業ツリー状態

今回の4ファイルは、既存 staged 差分に対する unstaged fixとして `MM` です。shared `.git/worktrees/.../index.lock` が read-only のため staging はできませんでした。commit・pushは行っていません。

## 総括

FIX-1〜7 のコード・検査修正は実装済みで、受理境界を緩める変更はありません。静的ゲートは通過しましたが、Pegasus dispatch 基盤の認証失敗でpytest子が一件も起動していないため、最終状態は全項目とも「partial（実装済み・未実走）」です。