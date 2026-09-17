## 変更した file と差分の要約

- [source_digest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/campaign/source_digest.py:1647): `-dD`、環境prefix cache、再帰取得、prefix不一致時のRuntimeErrorを実装。理由と残る限界をdocstringへ追記。
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2731-cpp-normalize-dd/orchestrator/tests/test_campaign.py:11833): A〜Hの8 nodeを追加。Gは一意な一時pathの実行可能shell scriptを使用し、終了時に片付けます。

既存test関数のAST不変、subprocess呼出し1箇所、`git diff --check`成功を確認。変更は指定2ファイルのみ。commitはしていません。

## 実走した nodeid と結果 (緑 / 赤 / 未実走)

**pytest実走は0件。すべて実装済み・未実走です。**

`tools/run_tests.py` 経由で以下を起動しましたが、すべてpytest起動前に停止しました。

- `test_campaign.py -k "source_digest or trace_diff"`
- 下記8 nodeのnodeid指定
- `test_ccbench_spawn_sites.py`
- `test_skip_classification.py`
- `test_campaign_import_invariant.py`
- `test_pytest_collection_config.py`
- `test_check_trace0_preprocess_identity.py`

新8 node（共通prefix: `orchestrator/tests/test_campaign.py::`）:

```text
test_source_digest_toplevel_macro_directives_change_identity
test_source_digest_toplevel_trace_directives_change_identity
test_source_digest_comment_only_preserves_stock
test_source_digest_unused_universal_supply_preserves_stock
test_source_digest_unused_protocol_supply_preserves_digest
test_source_digest_skipped_macro_directives_affect_only_live_variant
test_source_digest_cpp_environment_prefix_mismatch_fails_closed
test_source_digest_same_value_source_redefine_changes_identity
```

共通停止理由: **rc=16、`qstat -Q preflight rc=1`**。socket作成が拒否され、`child_started=false`。テストの赤ではありません。

ログ: [焦点走](/tmp/t2731-focus.log)、[新8 node](/tmp/t2731-eight.log)、[関連検査](/tmp/t2731-meta.log)。

## 所有外への波及 (静的列挙)

- `_normalize_contexts`: 文脈タグ・順序は不変。有効枝の指令がpre-imageへ加わります。
- `_trace_pair_diff`: 比較式は不変。TRACE枝内の未使用指令も差分となり、受理集合が狭まります。
- `tools/check_trace0_preprocess_identity.py`: 指令差がTRACE=0比較へ反映されます。consumer testは未実走です。
- `p3_s4_loop_trigger_gating.py`: 指令を含むproposalの既存artifact再利用で、pre-image不一致による停止が起こり得ます。
- 共有fixture・既存期待値・登録簿は変更していません。stock/templateの互換性は実走未確認です。
- meta-testとしてspawn登録、compiler選択、import例外台帳、collection設定を確認対象にしました。import例外台帳の行番号はidentityではなく注記です。

## 総括

plan v2の実装は完了しました。sandboxによる実行基盤停止のため検証は未完了であり、**closedとは申告しません**。