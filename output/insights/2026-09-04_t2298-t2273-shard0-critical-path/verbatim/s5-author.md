## 変更一覧

[対象テストファイル](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1182) のみ変更しました。

- lock 処理を shared-root、lock scope、共通 evidence scope、reader/writer fixture に分割。
- 同一 fd で seed `LOCK_EX → LOCK_UN → LOCK_SH/LOCK_EX` を実装。
- seed 後の double-check、残存 evidence の削除、metadata の一時ファイルへの書込み、`fsync`、`os.replace` を実装。
- `yield evidence` と patch の巻き戻しを本体 lock 内に保持。
- M17/M18 だけを `certified_evidence_writer` へ変更。
- commit、add、stash、branch 操作は未実施。

scope 前の受理・拒否挙動は変更していません。HEAD と変更後の17 consumerを AST 比較し、M17/M18 の fixture 識別子だけを正規化すると 17/17 が完全一致しました。assertion、期待値、受理集合の変更はありません。

## 追加した検査と DW-G05 の 1 行

| 検査 | 無い場合に通る退行 |
|---|---|
| `test_certified_evidence_lock_allows_two_readers` | reader が旧 `LOCK_EX` のままでも通る。 |
| `test_certified_evidence_seeded_reader_never_requests_exclusive` | seeded reader の短時間 EX 取得が通る。 |
| `test_certified_evidence_reader_blocks_nonblocking_writer` | reader の本体 lock 欠落が通る。 |
| `test_certified_evidence_writer_blocks_nonblocking_reader` | writer の `LOCK_SH` 化が通る。 |
| `test_certified_evidence_seed_double_check_observes_competing_seed` | 競合 worker による二重 seed が通る。 |
| `test_certified_evidence_fixture_scope_holds_both_modes_through_yield` | helper が正しくても実 fixture が yield 前に unlock する配線が通る。 |
| `test_certified_evidence_fixture_scope_yield_is_inside_lock_ast` | 共通 scope の yield を lock context 外へ移す変更が通る。 |
| `test_certified_evidence_metadata_is_fsynced_and_atomically_replaced` | 部分 metadata を ready 状態として直接公開する変更が通る。 |
| `test_certified_evidence_writer_direct_test_file_path_mutation_closure_excludes_called_helpers` | M17/M18 の writer 宣言漏れが通る。対象ファイル内の直接 path mutation だけを扱い、呼出先 helper 内の書込みは対象外。 |

元 plan の6本に、lens A must-fix の実 fixture/AST 2本と、変異 g を単独で殺せる atomic metadata 検査1本を加えた計9本です。

## 変異と殺す検査の対応

| 変異 | 赤になる検査 | 帰属 |
|---|---|---|
| a: writer mode を `LOCK_SH` | `test_certified_evidence_writer_blocks_nonblocking_reader` | 単一 |
| a2: writer wrapper が read を渡す | writer direct-path closure の wrapper-mode assertion | 単一 |
| b: reader が本体 lock を取らない | reader-blocks-writer、seeded-reader-no-EX | 帰属非一意 |
| c: M17 writer 宣言を外す | writer direct-path closure | 単一 |
| c2: M18 writer 宣言を外す | writer direct-path closure | 単一 |
| d: seed double-check を外す | seed-double-check | 単一 |
| e: reader を `LOCK_EX` に戻す | two-readers、seeded-reader-no-EX | 帰属非一意 |
| f: unlock 後へ yield を移す | fixture-scope 実検査、yield-position AST | 裁定指定の実配線・構造の二重固定 |
| g: temp+replace を直接 write に戻す | metadata-fsynced-and-atomically-replaced | 単一。登録する |

## 波及の静的列挙

- fixture consumer は引き続き17本。15本が read、M17/M18だけが write。
- 17 consumer の関数名と decorator は不変なので既存 nodeid は不変。
- 新規 node は上記9本だけ。既存 test の削除は0。
- `test_mutation_node_mapping_is_complete_and_one_to_one` は M01〜M18を固定する検査であり、新規検査には M 番号を付けていないため変更不要。
- fixture は当該 test module 内でのみ可視。所有外 caller、共有 conftest fixture、campaign 実装への API 変更はありません。
- `conftest.py`、`pytest.ini`、`tools/`、`docs/`、`orchestrator/campaign/`、`test_s8b_floor_campaign.py` は未変更。
- `git diff --check` 成功。禁止された U+0300〜U+036F は0文字です。

## 実走

実装済み・pytest 未実走です。

指定コマンドは編集前に実行を試みましたが、Pegasus ログインノードの PreToolUse 防護により pytest process 起動前に拒否されました。したがって緑の nodeid は報告しません。

代替の軽量診断結果:

- Python AST 構文解析: 成功
- consumer 数: 17
- consumer AST 不変確認: 17/17
- 重い seed を使わない新規 helper/AST 検査: 8本成功
- 実 evidence を作る fixture-scope 検査: 未実走

## 未解決点

- 計算ノードでの対象ファイル全走と collect-only 差分確認が必要です。
- M17/M18 の途中で worker が SIGKILL された場合、kernel lock は解放されても Python `finally` による evidence 復元は走らない既知限界が残ります。

## 総括

seed のみ排他、reader 共有、writer 排他への局所改修と、裁定済みの正例・負例、fixture 配線、writer 閉包、atomic metadata 検査を実装しました。差分は対象テストファイルだけに残してあります。