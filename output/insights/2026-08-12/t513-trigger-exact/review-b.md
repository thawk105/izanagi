## 総括

静的レビュー結果は **real 所見 1 件（nit 1）／must-fix 0 件**です。9 nodeid はすべて M1–M4 の少なくとも一つを検出します。検出力ゼロの nodeid はありません。

pytest・変異実走はしていません。以下はコードから導出した期待集合で、ユーザー提示の「9 passed」とは区別します。

### 変異別赤 node 表

全 nodeid の prefix は `orchestrator/tests/test_campaign.py::` です。

| nodeid suffix | M1 `.strip()` | M2 indent=`"    "` | M3 parsed text | M4 patch 4空白 |
|---|---:|---:|---:|---:|
| `test_trigger_predicate_hole_indent_matches_template_patch_bytes` | — | 赤 | — | 赤 |
| `test_trigger_binding_rejects_materialized_predicate_with_outer_spaces` | 赤 | — | — | — |
| `test_trigger_binding_rejects_materialized_predicate_with_leading_tab` | 赤 | — | — | — |
| `test_trigger_binding_rejects_materialized_predicate_with_trailing_space` | 赤 | — | — | — |
| `test_trigger_binding_rejects_materialized_predicate_with_four_space_indent` | 赤 | 赤 | — | — |
| `test_trigger_binding_rejects_materialized_predicate_with_crlf_line_ending` | 赤 | — | 赤 | — |
| `test_trigger_binding_rejects_materialized_predicate_with_cr_only_line_ending` | 赤 | — | 赤 | — |
| `test_trigger_build_start_binding_uses_same_source_evidence_as_both_cache_builds` | — | 赤 | — | — |
| `test_trigger_binding_rejects_crossed_materialized_predicate_and_mask` | — | 赤 | — | — |

期待赤の完全集合は次のとおりです。

- **M1:** outer-spaces、leading-tab、trailing-space、four-space、CRLF、CR-only の6件
- **M2:** drift、four-space、build-start 正例、crossed-binding の4件
- **M3:** CRLF、CR-only の2件
- **M4:** drift の1件

M1 は旧実装全体、すなわち `marker.hole_text` と両辺の `.strip()` 比較への復元として判定しています。M3 は `marker.hole_text` を使うがインデント込みの exact 比較は維持する変異です。

M2 で crossed-binding も赤になりますが、mask 不一致の検査ではなく [fixture の `"  "` literal assert](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5549) が先に発火するためです。期待 node 集合には含める一方、crossed-binding の独立 kill としては数えないでください。

## 所見

### [nit][real] `.strip()` が除去する空白族に未検査の代表が残る

現テストは空白、tab、CRLF、CR-only を固定していますが、垂直タブ `\v`、改ページ `\f`、NBSP `U+00A0`、全角空白 `U+3000` などは未検査です。

現実装は [raw payload の byte-exact 比較](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/campaign/pipeline.py:81)なので、これらをすべて拒否します。したがって現行バグではなくテスト不足の nit です。`\v`、`\f`、非 ASCII 空白1件程度を parameterize すれば閉じられます。

成果物影響: 現時点では値・受理集合は変わらないが、将来これらだけを正規化する回帰は現9件を通過でき、binding 付き lane の受理集合を広げて certified 選択・レポート・WAL 台帳へ非正準 source を流し得ます。

## 個別確認

- **drift locator:** [BEGIN/END を各1件と assert](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign.py:5388)し、その閉区間だけを `block` にしています。`#if/#else` も区間内で各1件です。区間外の11個超の `#if` decoyは参照されず、完全な同一 marker decoyを足せば BEGIN/END 件数で赤になります。must-fixなしです。
- **fixture自己参照:** helper は production parser・renderer・indent定数を使いますが、独立錨があります。patch実bytesの drift test、正例とcrossed fixtureの literal `"  "` assert、攻撃形の明示 `hole_line` が連動破損を捕捉します。emitterは契約上の正本で、別途独立 golden/oracle テストがあります。
- **制約meta-test:** 既存ファイルへの関数追加なので、[plain-runner/allowlist制約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_plain_runner_coverage.py:60)は不変です。新nodeは共有CCBench writerやrepo-status readerではないため、[real-repo収集・登録制約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_real_repo_serialization.py:567)へ追加しないのが正しいです。production側の追加importも相対importで、[campaign import制約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t513-trigger-exact/orchestrator/tests/test_campaign_import_invariant.py:1231)を満たします。これらmeta-testの実走結果は今回確認していません。
- **既存2テスト:** 正例は正準2空白を literal で固定したうえで certified/build/WALを検査しています。crossed-bindingは source mask 20、binding mask 21、buildなし、WAL abort、例外逐語を維持しています。fixture是正によりインデント不一致による早期拒否を除き、本来のmask不一致へ再照準されており、期待値の緩和はありません。