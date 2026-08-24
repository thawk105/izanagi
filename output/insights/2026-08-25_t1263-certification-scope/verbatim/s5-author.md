## 実装した内容

1. 実装 1: [tools/codex_reasoning_ab.py:9882](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/tools/codex_reasoning_ab.py:9882)

   snapshot cache を `(resolved path, descriptor SHA, case)` に変更しました。canonical replay 成功時だけ cache へ登録し、pre/post 比較を全 run で実行します。snapshot 検査がすべて成功した run の集合を導出し、[同ファイル:10186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/tools/codex_reasoning_ab.py:10186) から adjudication へ渡します。

2. 実装 2: [tools/codex_reasoning_ab.py:8687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/tools/codex_reasoning_ab.py:8687)

   `_load_adjudication` に default 無しの必須 keyword-only 引数を追加しました。[同ファイル:8812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/tools/codex_reasoning_ab.py:8812) の mapping join 一箇所だけで、指定された reason を一度積みます。

3. 実装 3: [tools/codex_reasoning_ab.py:10228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/tools/codex_reasoning_ab.py:10228)

   fresh な認証宣言を生成し、[verify_manifest:10246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/tools/codex_reasoning_ab.py:10246) の全 return path に付与しました。`_aggregate_verified` の直接返値には付与していません。

4. 実装 4: [test_codex_reasoning_ab.py:7496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1263-certification-scope/orchestrator/tests/test_codex_reasoning_ab.py:7496)

   宣言 3 経路、private helper 非宣言、fresh object、evidence 伝達、membership 正負、共有 oracle の全 run pre/post、既存 end-to-end 正例を追加・更新しました。既存 `_load_adjudication` 直呼出し 4 箇所も明示集合へ更新しています。

## 現行挙動と変更後挙動

現行では、同じ oracle identity を共有する二本目以降の run は pre/post 比較を省略されるため、その run 固有の `snapshot_after` 不一致を受理し得ました。membership 欠落に相当する入力は既存 snapshot reason でも拒否されるため、membership 検査単独で今日の受理集合は変わりません。

変更後は、共有 oracle の二本目以降でも pre/post 不一致を拒否します。受理集合を狭めるのはこの変更だけです。新しい membership reason は evidence 結線の構造的な固定であり、既存の赤を緑にする経路はありません。

`SCHEMA_VERSION=2`、既存 reason、`_replay_manifest` の tuple、`make_packets` と `_write_frozen_json`、中間 artifact bytes は変更していません。中間 CLI と artifact は引き続き未認証です。

## 走らせた検査

- AST 構文検査、`git diff --check`: rc=0、0.17 秒。対象は編集した 2 ファイルです。
- AST call/node 契約検査: rc=0、0.31 秒。新規 5 node、必須引数、直接 caller 7 箇所と alias caller 1 箇所、private helper 非宣言を確認しました。
- 中間の caller 件数 checker は alias を直接名呼出しとして数えたため rc=1、0.36 秒。その想定を訂正し、上記最終検査で rc=0 を確認しました。
- `python3 tools/run_tests.py orchestrator/tests/test_codex_reasoning_ab.py --collect-only -q`: rc=16、0.03 秒。Pegasus の `qstat -Q` preflight が rc=1 となり、child は起動されていません。

以下は実装済み・未実走です。

- `test_material_report_certification_scope_is_exact_on_all_return_paths`
- `test_material_packet_source_requires_replayed_snapshot_evidence`
- `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication`
- `test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run`
- `test_verify_replays_complete_fake_codex_experiment`
- `test_m6_verdict_packet_swap_restore_digest_layers_are_redundant`
- `test_reader_disagreement_is_conservative`
- 対象 test file 全体と `enforce_held_functions` 収集 guard

親 docs 未 land に由来する expected red finding は、射影範囲の静的検査ではありません。pytest 自体は未起動です。

## 波及可能性

- 所有外で `_load_adjudication` を直接呼ぶ caller は、新しい必須引数が無ければ `TypeError` になります。射影された 2 ファイル内の全 caller は更新済みです。
- `verify_manifest` / `aggregate_manifest` の厳密な top-level key 集合を期待する外部 consumer test は、追加 field への対応が必要になり得ます。
- 共有 fixture `_full_manifest` と `benchmark_snapshots` 自体は変更していませんが、新規 replay tests が利用します。
- 古い凍結 report、中間 packet、packet-state、verdict log、revealed map には宣言が追加されません。

## 守れなかったこと

- Pegasus dispatch infrastructure failure のため、pytest node を実走できませんでした。
- `tools/run_tests.py` が失敗時に禁止対象の `output/pegasus-dispatch/.../receipt.json` を一時生成しました。生成された exact なディレクトリは直ちに削除し、現在は残っていません。

## 総括

裁定 §2・§4 の実装を指定 2 ファイルへ限定して反映しました。  
membership 検査は構造ゲート、受理集合の縮小は全 run pre/post 検査だけです。  
宣言は公開 API の全返却経路にのみ fresh object として付きます。  
静的検査は rc=0、pytest は dispatch 障害により実装済み・未実走です。