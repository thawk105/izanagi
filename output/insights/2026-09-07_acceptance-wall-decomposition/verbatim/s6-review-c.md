## 総括

静的レビュー結果は `blocker: 0`、`should-fix: 2`、`nit: 0` です。

現行受入で使われる通常の pytest Item について、`_canonical_item` 一回化による実用上の検出力低下は確認できませんでした。ただし、アクセスごとに値を変える Item に対する形式的な受理集合は広がっており、その前提がテストにも契約にも固定されていません。

追加された呼出し回数検査は旧実装への復帰で赤になります。一方、report bytes 一致検査は同じ現行 renderer を両辺で呼ぶ恒真形です。

削除した 2 node は残置側と同一命題です。現行 pin の取り残しも見つかりませんでした。pytest は実走していません。

## gate の検出力への攻撃

`_canonical_item` は `path`、`nodeid`、`xdist_group` を読み、`ItemRecord(nodeid, file, group)` を作ります。`tools/acceptance_shards.py:742-768`。変更後は各 Item を一度だけ読み、その結果を records と `id(item) -> nodeid` の両方に格納します。`tools/acceptance_shards.py:771-783,840-850`。同じ snapshot が report state に入ります。`tools/acceptance_shards.py:856-862`。

各 gate が現在検出しているものは次のとおりです。

- `assignment_closure_gate`: selected 間の重複、records と selected の集合不一致、同一 file/group の shard 分断、real-repo conflict group の分断を検出します。`tools/acceptance_shards.py:445-474`。その前段で exact partition も検査します。`tools/acceptance_shards.py:665-670`。
- `_observed_universes_gate`: 全 shard の `ItemRecord` 列、つまり nodeid/file/group の完全一致を検査します。`tools/acceptance_shards.py:487-492,655-658`。同一 process 内の時間変化は検査しません。
- `_login_universe_gate`: login 親の独立 collect-only nodeid と shard 側 nodeid の multiset 一致を検査します。file/group は対象外です。`tools/acceptance_shards.py:495-496,661-663`、login collection は `tools/run_tests.py:1402-1424`。
- `_finished_gate`: report の selected と `pytest_runtest_logfinish` で観測した実行 nodeid の multiset 一致を検査します。`tools/acceptance_shards.py:499-500,672-677,865-869,979-982`。
- `validate_report_evidence`: worker collection digest、worker occupancy の形と item 合計、group-to-worker、JUnit path、terminal count を検査します。`tools/acceptance_shards.py:518-600`。live Item を再観測する gate ではありません。

旧実装だけが赤にする改竄は構成できます。

1. Item の `nodeid` property を、`_canonical_item` からの最初のアクセスでは実在 nodeid A、2 回目では universe 外の nodeid B、それ以外の pytest runtime からは A を返すようにする。
2. 旧実装は records を A で作った後、二度目の `_canonical_item` が返す B を retention 判定に使います。`HEAD:tools/acceptance_shards.py:832-843`。A は全 shard で deselect され、selected に残る A と finished が一致せず赤になります。
3. 新実装は A を map に再利用して Item を正しく retain します。全 shard の observed universe は A、login collection と runtime logfinish も A、assignment closure と evidence も自己整合するため緑になります。

ただし、現行受入でこの改竄を利用できる経路は確認できませんでした。標準 pytest Node の `nodeid` は格納済み `_nodeid` を返すだけです。`/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/nodes.py:195-201,272-275`。marker も格納済みリストを走査します。同 file `:330-349`。repo 全体にも custom Item subclass や `pytest_collect_file` はありません。

現行 conftest は inner collection hook の後で loadgroup suffix を除去します。`orchestrator/tests/conftest.py:2058-2061`。これは旧実装の二度目の読取りより後であり、両実装とも観測できません。また `_canonical_item` 自身が同 suffix を正規化済みです。`tools/acceptance_shards.py:765-767`。

したがって、人工 Item に対する形式的検出力は低下していますが、今回の 5 ファイルの変更を含む通常受入で悪用可能な経路ではありません。安定 Item を契約上の前提にしない場合は blocker へ昇格します。

## id 再利用への攻撃

現在の production 経路では `id` 再利用による誤対応は成立しません。

- hook は pytest から `items: list[Any]` を受け取ります。`tools/acceptance_shards.py:834`。
- 同じ list を `records_from_items` が走査して map を作ります。`tools/acceptance_shards.py:841-843`。
- map の全 lookup が終わるまで同じ list が Item への強参照を保持します。`tools/acceptance_shards.py:848-852`。
- `items[:]` を置換するのは lookup 完了後です。`tools/acceptance_shards.py:853`。さらに retained/deselected も対象 Item を保持しています。
- map は hook 内の局所値で、後続 phase へ保存されません。保存されるのは records/selected/loads の値だけです。`tools/acceptance_shards.py:856-862`。

一時 Item を都度生成して以前の Item を解放する独自 Sequence を `records_from_items` に渡せば、理論上は ID 再利用を構成できます。しかし `nodeids_by_identity` を渡す唯一の caller は上記の list 経路です。

防御的には `(item, record)` の位置対応をそのまま保持すれば `id` 自体を不要にできますが、現行コードの誤対応所見ではありません。

## 恒真な保証の指摘

呼出し回数検査は有効です。

`SH._canonical_item` を counted wrapper に差し替えた後で production hook を呼び、`calls == len(original_items)` を検査しています。`orchestrator/tests/test_run_tests_shards.py:780-800`。旧実装へ戻すと、records 作成と `by_identity` 作成で各 Item を 2 回呼ぶため `2 * len(items)` となり赤になります。legacy expected の構築は monkeypatch 前なので count へ混入しません。

records/selected/loads の比較は、安定した synthetic Item に対する旧 collection 手順を別に記述している点では有効です。`orchestrator/tests/test_run_tests_shards.py:735-778,801-807`。ただし次の限界があります。

- synthetic Item は値が不変なので、上記の時間変化による旧新の受理差を攻撃しません。
- expected と actual の両方が現行 `_canonical_item`、`allocate`、`_digest`、`_canonical_json_bytes` を使います。共通 helper の同方向変異には独立でありません。

report bytes 一致は恒真形です。`report_bytes(state)` と `report_bytes(legacy_state)` の両方が、同じ現行 `pytest_sessionfinish` と同じ現行 serializer を呼びます。`orchestrator/tests/test_run_tests_shards.py:809-843`。先に records/selected が一致しているため、report の入力も実質同一です。

例えば report field の順序、serialization、rounding を現行 emitter 側で変更しても両辺が同じように変化し、`test_run_tests_shards.py:843` は緑のままです。これは HEAD 版 report bytes との一致を固定していません。

旧 HEAD で取得した literal bytes または SHA-256 を expected にするか、report assembly と serializer を含む独立な legacy renderer をテスト内に固定する必要があります。

## 削除 2 node の被覆検証

1 件目は同一命題です。

残置された `test_p3_role_invalid_partial_passes` は `_role_invalid_trial(tmp_path)` と `_verify(run, report)` だけです。`orchestrator/tests/test_autonomous_trial_completeness.py:2019-2021`。削除された HEAD 版も逐語的に同じ body でした。`HEAD:orchestrator/tests/test_autonomous_trial_completeness.py:2274-2276`。

共通 helper は invalid role から raw pointer を削除し、`failure_phase="pre-raw-write"` を設定します。`orchestrator/tests/test_autonomous_trial_completeness.py:404-472`。両方とも同じ `_role_invalid_trial` と同じ production verifier を使用します。`orchestrator/tests/test_autonomous_trial_completeness.py:1858-1890,2000-2003`。module marker が要求する `ratified_enforcement_source` も空の function-scope fixtureです。`orchestrator/tests/conftest.py:153-155`。削除による命題の縮小はありません。

2 件目も同一命題です。

残置 param は入力 `("NO-GO。GOの条件を満たさない。", "NO-GO")` です。`orchestrator/tests/test_codex_reasoning_ab.py:13262-13266`。残置 body は `TOOL.score_text` の valid と decision を検査します。`orchestrator/tests/test_codex_reasoning_ab.py:13309-13314`。削除側の body も同じ `TOOL.score_text` と同じ 2 assertion です。`orchestrator/tests/test_codex_reasoning_ab.py:13246-13251`。

`TOOL` は module 冒頭で一度だけ同じ source からロードされます。`orchestrator/tests/test_codex_reasoning_ab.py:109-126`。`score_text` は引数 text と module regexだけを読む処理で、caller 名、pytest nodeid、fixture を参照しません。`tools/codex_reasoning_ab.py:8779-8853`。したがって param の所属 function が違っても命題は同一です。

## pin の取り残し

nodeid 側では、削除した完全 nodeid、function 名、param ID、入力 literal、両 test file の basename を検索しました。

- 削除した 2 node は現行 machine pin に残っていません。
- 残置側は ledger に存在します。`orchestrator/tests/acceptance_duration_ledger.json:2568,5766`。
- 削除 node が残る `output/insights` の mutation ledger や collection artifact は過去時点の観測記録であり、現行 consumer や golden ではありません。

件数側では `19519`、`19_519`、`19,519`、`19517`、`nodeid_count`、ledger consumer、mapping 長検査を検索しました。

- 現行の machine count は ledger の `19517` だけです。`orchestrator/tests/acceptance_duration_ledger.json:19521`。
- JSON を静的に読んだ結果、`nodeid_count == len(duration_seconds_by_nodeid) == 19517` です。
- schema validator と meta-test は literal 件数ではなく mapping 長との一致だけを検査します。`orchestrator/tests/conftest.py:1378-1397`、`orchestrator/tests/test_update_acceptance_duration_ledger.py:306-325`。
- suite node-set hash の meta-test対象に、今回の 2 test file は含まれません。`orchestrator/tests/test_update_acceptance_duration_ledger.py:329-404`。
- 新設した一回化テストは未測定なので ledger にありません。これは許容済みで、実 collection との meta-test も exact count ではなく coverage 90%以上です。`orchestrator/tests/test_acceptance_schedule_order.py:660-713`。
- `19519` は `docs/archive/worklog-phase3-0903-1218.md:485` と `docs/decisions.md:45257` に残りますが、前者は当時の ledger サイズ、後者は D1425 の当時の実測母数です。現行 pin ではなく、書き換えると履歴を改変します。

pin の取り残しはゼロです。

## 所見一覧 (severity 付き)

- **C-1: should-fix — 安定 Item 前提が固定されず、形式的受理集合が広がる。**
  - 攻撃シナリオ: `_canonical_item` からの初回 nodeid 読取りだけ A、二回目だけ universe 外 B、runtime では A を返す Item を投入する。旧実装は A を selected に記録しながら B で deselect して赤、新実装は A を再利用して全 gate が緑になる。
  - 根拠: `HEAD:tools/acceptance_shards.py:832-843`、`tools/acceptance_shards.py:771-783,840-862`。
  - 提案: native stable Item だけが入力契約であることを機械検査または契約化する。任意 Item を許すなら、二時点の canonical nodeid 安定性検査を残す。
  - 判定: 現行 repo に custom Item はなく、今回の 5 差分だけでは悪用不能なので blocker にはしません。

- **C-2: should-fix — report bytes の旧実装一致検査が恒真形。**
  - 攻撃シナリオ: report assembly、rounding、または serializer を変更する。両辺が同じ現行 `pytest_sessionfinish` を呼ぶため、旧 HEAD の bytes から変わっても equality は成立する。
  - 根拠: `orchestrator/tests/test_run_tests_shards.py:809-843`、`tools/acceptance_shards.py:965-1033`。
  - 提案: 旧 HEAD の固定 bytes/hash、または独立な legacy report renderer と比較する。

`blocker` 所見はゼロです。

## 未解決・要親裁定

- B1 の「検出力不変」を通常 pytest Item の安定性を前提とした契約として扱うか。そう扱わない場合、C-1 は `blocker` であり、一回化をそのまま受理できません。
- report bytes の保証を今回の wave で実保証へ直してから受理するか。現状の assertion は旧 report bytes の回帰防壁になっていません。