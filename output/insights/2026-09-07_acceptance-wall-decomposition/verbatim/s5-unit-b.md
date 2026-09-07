## 実装した内容

- B1: [`tools/acceptance_shards.py`](/work/1/SFC/tanab/izanagi/.codex/worktrees/accwall-unit-b/tools/acceptance_shards.py) で `_canonical_item` を item ごとに一度だけ呼び、`id(item) → nodeid` を選択処理へ再利用。
- 旧実装との records / selected / loads / report の byte 一致と、呼出し回数 `len(items)` を固定する検査を追加。
- B2: 指定された autonomous test 1 node と F176 の `go_condition` param 1 nodeだけを削除。
- duration ledger から対応する2 keyを削除し、`nodeid_count` を `19519 → 19517` に更新。
- docs、commit、stage、branch、pushは変更していない。

## 受理集合の変化 (現行 / 変更後)

- 現行: 全 collection を各 worker が導出し、assignment closure、shard間 universe、login universe、finished、report evidenceの不一致を拒否する。
- 変更後: 安定した pytest Item に対する records / selected / loads / report bytesと、各 gateの受理・拒否条件は不変。collection絞り込み、skip、追加deselectはない。
- B1で意図的に除去したのは、同一Itemの二度目の観測だけ。アクセスごとに値を変える人工的Itemでは二度目の差異を観測しなくなる。
- universeの変更は、裁定指定の重複2 node削除だけ。distinct input集合とproduction call集合は縮小しない。

## 削除に伴う pin 閉包 (探した key と見つけた pin)

検索したkey:

- 削除・残置双方のfunction名と完全nodeid
- `go_condition` / `go_condition_not_met`
- 対象test file basename
- `nodeid_count`
- 旧件数の完全 framing `"nodeid_count": 19519`

見つかった現行machine pin:

- [`acceptance_duration_ledger.json`](/work/1/SFC/tanab/izanagi/.codex/worktrees/accwall-unit-b/orchestrator/tests/acceptance_duration_ledger.json) の削除対象2 key
- 同ledgerの `nodeid_count`
- `test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations` の、件数とmapping長の一致検査

別のliteral nodeid goldenや固定件数meta-testはなかった。`output/insights` 内の過去mutation ledger／collection artifactには旧nodeidが残るが、過去時点の証拠であり現行pinではないため変更していない。

## 実走した検査

- 自走harnessによるfocused検査: `20 passed in 13.88s`
  - B1 byte・呼出し回数検査
  - observed universe、assignment closure、finished、login universeの正負例
  - mergeとreport evidence
  - `test_p3_role_invalid_partial_passes`
  - F176の残存2 parameterized function全件
  - ledger schema／件数整合
- B1追加node単独: `1 passed in 4.53s`
- `python3 tools/check_codex_agents.py`: rc=0
- `python3 tools/check_docs.py`: rc=0
- AST構文、JSON、`nodeid_count == len(mapping) == 19517`: rc=0
- `git diff --check`: rc=0
- `tools/run_tests.py` は予告どおりqueue preflightで rc=16、child未起動。生成されたexact dispatch artifactは除去済み。
- `test_run_tests_shards.py` 全file harnessは進捗停止後に中断し rc=130。完走証拠には数えていない。

## 波及可能性

- `records_from_items(items, repo)` の既存2引数契約は維持し、追加keywordはhookだけが使用する。
- 新規検査nodeのdurationは未測定なのでledgerへ合成追加していない。
- gate実装自身を変更した自己認証限界は残るため、親の独立reviewと受入全走が最終証拠になる。

## 未解決・前提

- 受入全走と性能A/Bは未実走。実走権威は親。
- 親docs未land由来の赤finding集合は空。docs checkerも緑。
- staged変更はなく、変更pathは指定された5 fileだけ。

## 総括

単位Bは実装済み・focused実走済み・受入全走未実走。親による全走確認待ちであり、closedとは申告しない。