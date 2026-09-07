## 総括

blocker はゼロ、should-fix は 2 件、nit はゼロです。

実装本体について、静的に確認できる runtime break または fail-open は見つかりませんでした。`records_from_items` の互換性、例外から rc=16 への伝播、report 欠落時の併合拒否、削除 node の参照閉包、ledger の内部整合はいずれも保たれています。

ただし、B1 の新規検査は実運用の xdist worker → controller 集約経路を通しておらず、report bytes 不変の証明範囲が不足しています。また現在の未 commit 状態では、ledger が dirty なため既存の A1 非変更検査が確実にテスト赤になります。

レビューは静的検査のみです。pytest の実走結果は緑の根拠に使っていません。

## hook 実行文脈への攻撃

現行 xdist では、prompt の「controller と全 worker で走る」は、そのままでは成立しません。

- xdist controller の `DSession.pytest_collection` は `True` を返して controller 自身の collection を禁止します。したがって通常の shard 全走では、`pytest_collection_modifyitems` が item を処理するのは各 worker です。根拠: `/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:103-105`
- worker では xdist 自身が group suffix を nodeid に付与し、その後 `trylast=True` の shard hook が canonicalize します。根拠: `/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/remote.py:236-254`、[`tools/acceptance_shards.py:833`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:833)
- suite の wrapper hook は yield 前に marker を付け、yield 後に shard state を検査して suffix 除去と duration reorder を行います。したがって `_canonical_item` は marker 付与後、suffix 除去前の安定した item を読みます。根拠: [`orchestrator/tests/conftest.py:1988`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:1988)、同 `:2058-2070`
- worker は collection state の digest を `workeroutput` へ格納し、gw0 だけが full records / selected を渡します。controller は local state が無いため `_WORKER_PAYLOADS` 経路で一致を検査します。根拠: [`tools/acceptance_shards.py:923`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:923)、同 `:938-962`、`:965-977`
- serial 起動だけは controller 自身が hook を実行し、`_controller_state` の local state 分岐を使います。これは xdist 全走と異なる経路ですが、B1 の identity map 自体には worker/controller 分岐がありません。

`records_from_items` の呼出し元は repo 内で次の 1 箇所だけです。

1. `pytest_collection_modifyitems` からの呼出し: [`tools/acceptance_shards.py:841`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:841)

定義を含めても検索結果は 2 箇所だけです。新しい引数は keyword-only、既定値 `None` なので従来の `records_from_items(items, repo)` 契約も維持されています。根拠: 同 `:771-783`。他の呼び手を引数増減で壊す経路はありません。

worker/controller で異なる挙動を起こす反証シナリオは、worker payload 経路だけを壊す変異です。例えば `_worker_payload` の `records_digest` を変えても、新規検査は local state を直接 report 化するため緑のままです。一方、実際の xdist controller は `_WORKER_PAYLOADS` を読むので rc=16 になります。この検査不足を所見 D-01 とします。

## 例外時の挙動

変更部分の例外は fail-open しません。

- `_canonical_item` または新しい identity map 構築中に例外が出ると、`_izanagi_acceptance_shard_state` はまだ設定されていません。state の設定は canonicalize、allocate、deselect の完了後です。根拠: [`tools/acceptance_shards.py:771`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:771)、同 `:841-862`
- worker の state が無い場合、`_worker_payload` は `collection-state-missing` を返します。controller の `_controller_state` は正しい digest として受理せず例外にします。同 `:923-962`
- controller の report finalization 例外は捕捉され、`session.exitstatus = 16` になります。同 `:1033-1040`
- pytest 本体は sessionfinish 後の `session.exitstatus` を process rc として返します。根拠: `/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/main.py:359-373`
- shard dispatcher は rc が `0` または `1` 以外なら直ちに `dispatch-infrastructure` として rc=16 を返します。根拠: [`tools/acceptance_shards.py:1363`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:1363)、同 `:1387-1405`

一方、新規回帰テスト自身の assertion が失敗する場合は通常のテスト失敗です。collection state は既に存在するので report が書かれ、shard rc=1、併合結果 rc=1 になります。`merge_reports` は rc 0/1 のみを通常結果として扱い、1 をテスト赤へ集約します。根拠: 同 `:684-700`。

`report.json` が無いのに併合 gate を通過する経路もありません。

- `_load_reports` は欠落または不正 JSON を読み飛ばします。同 `:1121-1131`
- 全 process が rc 0/1 でも、欠落分により report index 集合が不足し、`report-index-set` の rc=16 になります。同 `:638-650`、`:1441-1463`
- report の atomic create に失敗した場合も finalizer が rc=16 に変更します。同 `:235-256`、`:1033-1040`

したがって、変更部分の例外について確認できた分類は次のとおりです。

- production collection/finalization 例外: rc=16
- 新規検査の assertion failure: rc=1 のテスト赤
- report 欠落: rc=16
- fail-open: なし

## 削除 2 node の波及

`test_f176_preserves_decision_mentions` は、残る parameter が 1 件でも問題ありません。

- 残存 parameter は明示的な `id="focused_review_reason"` を持つため、nodeid は引き続き `test_f176_preserves_decision_mentions[focused_review_reason]` です。自動 ID 生成や単一 parameter 化による nodeid 消失はありません。根拠: [`orchestrator/tests/test_codex_reasoning_ab.py:13236`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_codex_reasoning_ab.py:13236)
- ledger にもこの残存 nodeid が登録されています。根拠: [`orchestrator/tests/acceptance_duration_ledger.json:5765`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:5765)
- 削除された `go_condition` と同じ入力は `go_condition_not_met` として残っています。同 test file `:13254-13266`
- repo 内 Python/JSON を横断検索した結果、削除された `[go_condition]` nodeid、旧件数 19519、削除 parameter を参照する別の machine pin はありません。

autonomous 側の削除 functionについても、削除 function 名の参照、`__all__`、meta-test はありません。

- 残存する同一 helper 利用 node は `test_p3_role_invalid_partial_passes` です。根拠: [`orchestrator/tests/test_autonomous_trial_completeness.py:2019`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_autonomous_trial_completeness.py:2019)
- `test_role_session_isolation.py` は対象 module を `F` として import しますが、利用しているのは `_complete_trial`、`_role_invalid_trial`、`_persist`、`_ROLES` で、削除 function は参照していません。根拠: `orchestrator/tests/test_role_session_isolation.py:32,99-109,706-716`

ledger consumer への波及は次のとおりです。

- `conftest.py` は `nodeid_count == len(mapping)` だけを document-level 条件とし、現 collection 総数との一致を要求しません。根拠: [`orchestrator/tests/conftest.py:1378`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:1378)
- `test_acceptance_schedule_order.py` が checked-in ledger に対して参照する具体値は real-repo writer の suffixed key で、削除 2 key と無関係です。根拠: [`orchestrator/tests/test_acceptance_schedule_order.py:824`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_acceptance_schedule_order.py:824)
- `test_update_acceptance_duration_ledger.py` の schema 検査も mapping 長との一致だけです。根拠: [`orchestrator/tests/test_update_acceptance_duration_ledger.py:306`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_update_acceptance_duration_ledger.py:306)
- `test_paper_story_a1_headline.py` は ledger 内容や件数を読まず、ledger path が working tree で dirty でないことを検査します。現在はこの条件を満たさないため所見 D-02 です。根拠: [`orchestrator/tests/test_paper_story_a1_headline.py:1232`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_paper_story_a1_headline.py:1232)、同 `:1241,1303-1312`

## 台帳の整合

静的 JSON 読取り結果は次のとおりです。

- `nodeid_count = 19517`
- mapping 長 = 19517
- 削除対象 2 key は不在
- 残置側 2 keyは存在
- 新規 `test_collection_canonicalizes_each_item_once_and_preserves_legacy_bytes` は不在

根拠: [`orchestrator/tests/acceptance_duration_ledger.json:2568`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/acceptance_duration_ledger.json:2568)、同 `:5765-5766,19521`。

新規 node の duration を合成追加しなかった判断は正しいです。`nodeid_count` は現 collection の総 node 数ではなく、測定済み mapping の entry 数です。未登録 node が存在しても document は無効になりません。

dispatch への影響も fail-soft です。

- duration が無い item を含む unit は unknown と判定されます。根拠: [`orchestrator/tests/conftest.py:1571`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/conftest.py:1571)、同 `:1587-1603`
- known unit があれば unknown unit は既定の 96 番目コスト相当として並べられます。同 `:1605-1617`
- focused collection が新規 node だけで、known cost が 1 件も無ければ reorder を行わず元順序を維持します。同 `:1605-1606`
- この unknown 規約は専用検査でも固定されています。根拠: [`orchestrator/tests/test_acceptance_schedule_order.py:1167`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_acceptance_schedule_order.py:1167)

従って未登録 node は受入や焦点走を壊しません。実測 JUnit が得られた後の ledger 更新対象にはなりますが、現時点で値を捏造しない方が計測規律に合います。

## 所有外への波及

静的に確認した所有外経路は次のとおりです。

- `orchestrator/tests/conftest.py`
  - shard hook より先に real-repo marker を付与する。
  - shard hook 後に state 閉包を検査する。
  - ledger により選択済み items を並べ替える。
  - 新規未登録 node は unknown cost になる。
- `tools/run_tests.py`
  - shard subprocess に plugin と spec 環境変数を渡す。根拠: `tools/run_tests.py:1495-1527`
  - subprocess rc と report を `run_parallel` で併合する。同 `:2302-2352`
- shard 全体
  - 2 node 削除と 1 node 追加により universe は net 1 node 減る。
  - allocator は file 単位の component weight を使うため、対象 3 file の重みが変わり、greedy allocation の後続 component 配置まで変わる可能性がある。これは correctness break ではないが、wall の比較に対する交絡になる。根拠: `tools/acceptance_shards.py:321-357`
- `orchestrator/tests/test_acceptance_schedule_order.py`
  - checked-in ledger を実際にロードし、duration lookup と並替え規約を検査する。
- `orchestrator/tests/test_update_acceptance_duration_ledger.py` と `tools/update_acceptance_duration_ledger.py`
  - ledger schema、既存 entry、将来の JUnit 更新を扱う。新規 node は次回の実測更新まで unknown のままになる。
- `orchestrator/tests/test_paper_story_a1_headline.py`
  - ledger の dirty 状態を A1 manifest 違反としてテスト赤にする。
- `orchestrator/tests/test_role_session_isolation.py`
  - autonomous test module の helper を直接 import するが、削除 function 自体への依存はない。
- `orchestrator/tests/test_real_repo_serialization.py`
  - `ItemRecord`、`allocate`、assignment closure を使うが、変更した `records_from_items` は呼ばない。根拠: `orchestrator/tests/test_real_repo_serialization.py:1650-1665`
- `tools/pegasus/run_acceptance_nproc_study.py`
  - `acceptance_shards.create_session` だけを直接呼び、変更した helper signature の影響は受けない。根拠: `tools/pegasus/run_acceptance_nproc_study.py:3379-3385`

## 効果の判定

B1 が wall を下げる機序は存在します。

旧実装は item ごとに `_canonical_item` を records 作成時と identity map 作成時の 2 回呼びました。新実装は 1 回の結果を両方へ使います。`_canonical_item` は `Path.resolve()`、repo 包含確認、nodeid 分解、marker 列挙を行うため、その 1 周分が各 xdist worker から消えます。根拠: [`tools/acceptance_shards.py:742`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:742)、同 `:771-783,841-850`。

ただし、削減量が受入 wall に現れることは測定されていません。

- 全 worker が collection を完了するまで scheduler は開始できないため、最遅 worker の critical path 上にこの処理があれば wall は下がります。
- wall に効くのは全 worker の削減時間の合計ではなく、各 shard の最遅 collection と、さらに 3 shard 中の最遅 shard です。
- import、pytest collection 本体、worker 起動、同期待ちが支配的なら、1 周削減は観測不能な可能性があります。
- 同じ wave で 2 node 削除、1 node 追加、3 file の component weight 変更、unknown duration node の追加が起きるため、combined pre/post A/B だけでは B1 単独効果を分離できません。

したがって記載すべき結論は「B1 は wall を下げうる機序を持つが、効果は測定されていない」です。親が効果を主張していない現状は正しいです。

## 所見一覧 (severity 付き)

1. D-01 — `should-fix`: B1 回帰検査が実運用の worker → controller report 経路を検査していない。

   - 反証シナリオ: `_worker_payload` または `_controller_state` の worker payload 分岐だけを壊す。新規検査は `_izanagi_acceptance_shard_state` を controller config へ直接設定して local state 分岐を使うため緑のままだが、実受入は report finalization で rc=16 になる。
   - 根拠: [`orchestrator/tests/test_run_tests_shards.py:789`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_run_tests_shards.py:789)、同 `:809-843`。production の別経路は [`tools/acceptance_shards.py:923`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/tools/acceptance_shards.py:923)、同 `:938-977`。
   - 提案: 同じ test node 内で gw0 と非 gw0 の worker configを構成し、`_worker_payload`、`pytest_testnodedown`、local state を持たない controller の `_controller_state` を通した report bytes 一致と、worker digest 不一致の rc=16 を固定する。

2. D-02 — `should-fix`: 現在の未 commit working tree で受入全走すると、ledger の dirty 状態により既存テストが確実に赤になる。

   - 反証シナリオ: 現在の `git status --short` は `M orchestrator/tests/acceptance_duration_ledger.json` を返す。`test_existing_a1_non_touch_manifest_is_empty_from_base` は同 path を manifest に含めて `git status --porcelain` の stdout が空であることを要求するため assertion failure になる。これは rc=16 ではなく report 付き rc=1 のテスト赤である。
   - 根拠: [`orchestrator/tests/test_paper_story_a1_headline.py:1232`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-acceptance-wall-20260907/orchestrator/tests/test_paper_story_a1_headline.py:1232)、同 `:1241,1303-1312`。
   - 提案: 5 file を原子的に commit した clean tree で受入全走を行う。もし pre-commit の受入全走が必須なら、この既存非変更検査との両立方法は親裁定が必要であり、検査を場当たり的に弱めてはならない。

blocker: ゼロ。

nit: ゼロ。

## 未解決・要親裁定

- D-01 の worker/controller payload 経路検査を landing 前の必須修正とするか。B1 契約が report bytes 完全一致まで要求しているため、必須にするのが妥当です。
- D-02 の実行順。現行のまま pre-commit 受入を行えば既知の rc=1 になります。atomic commit 後の clean tree で受入するならコード変更は不要です。
- B1 の wall 効果は未測定です。効果を主張する場合は親権威の同一 tip 対応 A/B、B1 単独を述べる場合は削除 node と ledger 順序変更を分離した ablation が必要です。
- 新規検査 node を ledger へ合成追加しない判断について、追加裁定は不要です。実測後に更新するのが正しいです。