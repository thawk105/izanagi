## 変更内容 (file ごと)

`R/ccbench` の [mocc transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/ccbench/cc/mocc/transaction.cc:113)、[silo transaction.cc](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/ccbench/cc/silo/transaction.cc:366)、[trace.hh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/ccbench/include/trace.hh) は clang-format 14 で整形済みです。mocc の `#line` を 116 から 115 に訂正しました。3 file とも、TRACE=0 の推定行番号の列が C2′ と両文脈で一致します。

[R/scripts/verify_format_only.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/scripts/verify_format_only.py) に R2 の (i)〜(vi)、[check_format_ci.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/scripts/check_format_ci.sh) に CI と同じ対象列挙と format 検査を実装しました。[run_judge.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/scripts/run_judge.sh) は new OID の事前照合、負例の削除、並行実行の rc 採取を実装しました。[run_ci_build.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-fmt-a/output/runs/t2854-fmt-ci/scripts/run_ci_build.sh) は CI image での offline build と指定の report・log 出力を実装しました。所有外の repo tracked file は編集せず、commit・push もしていません。

## 足した #line の一覧

| file・行 | 値 | 行の対応 |
|---|---:|---|
| mocc `transaction.cc:113` | 115 | 指令の次の空行を論理 115 行とし、後続の最初のコード行を C2′ と同じ 125 行に戻す。116 ではコード行が 1 行進んだ。 |
| silo `transaction.cc:366` | 365 | 直後の `}` を C2′ の 365 行に戻す。 |
| silo `transaction.cc:384` | 381 | 次の `}` を C2′ の 381 行に戻す。 |

## 実走した command と rc

- CI の `git ls-files -- cc include common | grep -E '\.(cc|hh|cpp)$' | xargs /usr/bin/clang-format --dry-run --Werror`: 213 file、rc=0。
- `check_format_ci.sh <clone> /usr/bin/clang-format`: clang-format 14.0.0、213 file、rc=0。
- `verify_format_only.py` の C2′ 対 C2′ 自己確認: rc=0。差分がないため (i) は適用外として JSON に `null` を記録。
- 同検証器の C2′ 対整形後作業ツリー: rc=0。(ii)〜(vi) は全 file・両文脈で成立。
- 一時 dir で文字列内の空白を増やした負例: 検証器 rc=1。(ii) は true、(iii) は false。
- `git diff --check`、3 shell script の `bash -n`: ともに rc=0。
- 計算ノード用 2 script の login での入口確認: bnode 条件によりそれぞれ rc=2。

## 未実走・残る懸念

`run_judge.sh` と `run_ci_build.sh` の計算ノードでの本走は未実施です。commit 後の `--new` に対する (i) の実判定、D297 report、CI image build report はまだありません。

## 総括

author A の所有範囲は実装済みです。format step と訂正後の推定行番号条件は通過しました。