## 総括

- **real** — 差分は新規 node を **15 件**追加する。各 node の増分費用は O(1) または固定 artifact の変更量 O(変更量) であり、履歴・repository 全 file 数を新たに走査する node はない。D335 違反の must-fix は見つからない。`rulings-verbatim.md:21`、`test_p3_exploration_namespace.py:514`
- **refuted** — ledger 被覆率が 90% を割る懸念は成立しない。基準 collection 19,519 件に15件を加えた静的見積りは **19,534件**、既知 ledger 19,519件なので **99.923%**。`acceptance_duration_ledger.json:19523`、`test_acceptance_schedule_order.py:704`
- **real** — shard の file component 数は変わらないが、既存 component の weight は合計15増えるため、LPT による shard の置き場所・load 値は変わり得る。`tools/acceptance_shards.py:321`、`tools/acceptance_shards.py:415`
- **real** — pytest は一件も実走されていない。本レビューは静的検査であり、緑は主張しない。`s5b-report.md:57`、`s5b-report.md:68`
- **real** — certified 選択結果・材料レポート・試行台帳の値は変更しない。変わる成果物面は acceptance の universe が15件増えることと、外部入力欠落時に既存27 collected node が fail/error ではなく skip になり得ることだけである。`tools/acceptance_shards.py:425`、`test_t1434_t1222_science_slice.py:82`

## 1 新 node の費用と ledger 波及

| 判定 | 新 node | 費用 |
|---|---|---|
| real | `test_campaign_driver_discovery_names_are_pinned` | O(1)、7名 tuple 比較。`test_p3_exploration_namespace.py:514` |
| real | `test_campaign_driver_lexical_prefilter_matches_unfiltered_bounded_fixture` | O(1)、固定7 fileを2走査。`test_p3_exploration_namespace.py:526` |
| real | t189 requirements exact | O(変更量)、slice JSON と現在4件。`test_t189_oracle_wiring_slice.py:132` |
| real | t189 missing-one guard | O(変更量)、3 file生成・4 stat。`test_t189_oracle_wiring_slice.py:154` |
| real | t189 complete guard | O(変更量)、4 file生成・4 stat。`test_t189_oracle_wiring_slice.py:170` |
| real | t1434 requirements exact | O(変更量)、artifact と現在21件。`test_t1434_t1222_science_slice.py:409` |
| real | t1434 missing-one guard | O(変更量)、20 file生成・21 stat。`test_t1434_t1222_science_slice.py:452` |
| real | t1434 complete guard | O(変更量)、21 file生成・21 stat。`test_t1434_t1222_science_slice.py:468` |
| real | t1434 reader-A isolated guard | O(変更量)、artifact 内 reader 探索・1 file生成・1 stat。`test_t1434_t1222_science_slice.py:477` |
| real | B-10 provenance requirements exact | O(1)、固定 `HASHES` 22件。`test_b10_extended_figure_provenance.py:891` |
| real | B-10 provenance missing-one guard | O(1)、21 file生成・22 stat。`test_b10_extended_figure_provenance.py:906` |
| real | B-10 provenance complete guard | O(1)、22 file生成・22 stat。`test_b10_extended_figure_provenance.py:928` |
| real | plot B-10 requirements exact | O(変更量)、provenance JSON の22行。`test_plot_b10_extended_backoff.py:354` |
| real | plot B-10 missing-one guard | O(変更量)、JSON読取り・21 file生成・22 stat。`test_plot_b10_extended_backoff.py:369` |
| real | plot B-10 complete guard | O(変更量)、JSON読取り・22 file生成・22 stat。`test_plot_b10_extended_backoff.py:393` |

- **real** — `test_p3_exploration_namespace.py` の module import 時走査は依然 O(`campaign/*.py`) だが、差分前から存在した collection 費用である。新2 node の増分は O(1)。prefilter は全 file の read/NFKC を残し、marker 不在 file の parse/walk を省く。`test_p3_exploration_namespace.py:133`、`test_p3_exploration_namespace.py:159`
- **real** — ledger 未登録 unit はゼロ扱いでも除外でもない。unit 内に未登録 item が一つでもあれば unknown とし、既知 cost の降順96番目を代入して並べ替える。`conftest.py:1584`、`conftest.py:1602`、`test_acceptance_schedule_order.py:1167`
- **refuted** — 90%割れはない。差分に既存 node の削除・renameはなく15件だけ増えるため、19,519/19,534 = 99.923%。gate 自体は `covered / len(rows)` を評価する。`acceptance_duration_ledger.json:19523`、`test_acceptance_schedule_order.py:660`
- **refuted** — 新しい shard component は生まれない。component は file/group を頂点に作り、今回の node は既存5 file内で新しい group markerも持たない。weight 増分はそれぞれ `+2/+3/+4/+3/+3`。`tools/acceptance_shards.py:322`、`tools/acceptance_shards.py:350`

## 2 bounded fixture の有界性

- **real** — fixture は literal dict の固定7本で、実 `orchestrator/campaign/` の file 数に依存しない。`test_p3_exploration_namespace.py:528`
- **real** — production `_discover_campaign_drivers` を prefilter 有無で呼ぶが、両方とも `import_modules=False` である。実 module import は起きない。`test_p3_exploration_namespace.py:572`
- **refuted** — `tmp_path` 外への書込みはない。全 filename は固定 basename で、書込み先と探索 root は同じ `tmp_path`。`test_p3_exploration_namespace.py:569`、`test_p3_exploration_namespace.py:572`
- **real** — NFKC 正例を含み、生 source には marker がなく正規化後にはあることを直接確認する。`test_p3_exploration_namespace.py:555`、`test_p3_exploration_namespace.py:566`

## 3 guard の要求集合の費用

| 判定 | module | JSON導出時点・成長性 | 現在の stat 上限 |
|---|---|---|---:|
| real | t189 | helper 呼出しごとに slice JSON を読む。artifact の task/evidence 数に比例し、exact test が現在4件を固定。`test_t189_oracle_wiring_slice.py:44` | 12 |
| real | t1434 | helper 呼出しごとに artifact JSON を読む。descriptor 数に比例し、現在21件。reader-A 経路は1 stat。`test_t1434_t1222_science_slice.py:24`、`:49` | 114 |
| real | B-10 provenance | JSON は読まず module の `HASHES` key 22件から導出。現在のコード上は固定。`test_b10_extended_figure_provenance.py:120` | 352 |
| real | plot B-10 | helper 呼出しごとに checked-in provenance JSON を読む。`external_inputs` の成長に比例し、現在22件。`test_plot_b10_extended_backoff.py:37` | 66 |

- **refuted** — 追加 guard に module-level JSON read はない。すべて test 実行中の helper 呼出しであり、collection 時には path・literal定義だけである。`test_t1434_t1222_science_slice.py:24`、`test_plot_b10_extended_backoff.py:30`
- **real** — full run での静的上限は **544 stat**。内訳は実外部 root に405、追加した自己検査の一時 fixture に139。要求集合に比例するが、repository 全 file 数・履歴数には比例しない。`test_b10_extended_figure_provenance.py:124`、`test_t1434_t1222_science_slice.py:64`
- **real** — 544 stat が acceptance wall 上で何秒かは静的には言えない。固定 syscall 数なので D335 の must-fix ではないが、並列 filesystem 上の実費は実走後でなければ判定できない。`rulings-verbatim.md:23`

## 4 既存 node の受理集合

- **refuted** — 完全な外部入力がある場合、今回の guard により新たに skip される既存 node はない。全 `os.stat` が成功すれば guard は戻り、既存 assertion へ進む。`test_t189_oracle_wiring_slice.py:62`、`test_b10_extended_figure_provenance.py:142`
- **real** — guard が捕捉するのは `FileNotFoundError` だけである。ENOTDIR、ELOOP、権限異常、内容不正、SHA不一致は skip に変換されない。`test_t1434_t1222_science_slice.py:74`、`test_plot_b10_extended_backoff.py:52`
- **real** — 欠落時の既存外部-byte consumer はすべて guard を通る。

  - t189: `test_optional_jobs_root_audits_pinned_prompt_and_receipt_bytes` の1 node。`test_t189_oracle_wiring_slice.py:119`
  - t1434: physical/m4/m6 の3 nodeと、reader-A 3関数の parameter 展開8 node、計11 node。`test_t1434_t1222_science_slice.py:124`、`:257`、`:279`、`:343`
  - B-10 provenance: 直接 guard 2 nodeと `_relocated_root` を通る12 node、計14 node。`test_b10_extended_figure_provenance.py:258`、`:324`、`:349`
  - plot B-10: canonical measurement を読む1 node。`test_plot_b10_extended_backoff.py:194`

- **refuted** — guard のない B-10 負例が外部 root 欠落で誤って hard red になる経路はない。receipt mapping・lexical escape は production が source access より先に構造拒否する。`test_b10_extended_figure_provenance.py:524`、`:540`、`tools/plotting/plot_b10_extended_backoff.py:276`、`:463`
- **real** — reader-A 3関数は artifact から reader-A output だけを引き、guard へ1件 tupleを渡す。無関係な20件が欠けても走る。独立対照も追加されている。`test_t1434_t1222_science_slice.py:343`、`:367`、`:391`、`:477`
- **real** — `test_physical_rejects_symlink_component` は外部内容を読む正例ではなく、作った symlink component の拒否を検査するため guard 無しでよい。`test_t1434_t1222_science_slice.py:508`
- **real** — 別軸として、prefilter は marker 不在 source の parse を省くため、既知3 campaign module の構文検出力を失う。これは段4で明示裁定済みの残余で、今回の guard による受理集合変更ではない。`s4-ruling.md:34`、`s4-ruling.md:41`

## 5 他 file への波及

- **real** — module 名・path の参照検索で得た明示 consumer は次のとおり。

  - `test_p3_build_authority_cli.py::test_tracked_python_coder_authority_ast_closure_is_exact` は p3 test source をAST走査する。追加コードは authority helper を増やさないため inventory を壊さない。`test_p3_build_authority_cli.py:128`、`:637`
  - `test_paper_story_a1_headline.py::test_existing_a1_non_touch_manifest_is_empty_from_base` は固定 commit 間 manifest に p3 file を含めるが、working-tree 差分を比較しない。`test_paper_story_a1_headline.py:1232`、`:1289`
  - `test_update_acceptance_duration_ledger.py::test_t1574_changed_suite_ledger_node_delta_is_exact` は p3 ledger prefix の既存26 entryを固定する。ledger が未変更なので壊れないが、新2 nodeも登録されない。`test_update_acceptance_duration_ledger.py:329`、`:368`
  - `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` は全 collection を consumer とし、今回の15件が分母へ増える。`test_acceptance_schedule_order.py:660`
  - `test_plain_runner_coverage.py` は全 `test_*.py` を動的に読む。既存 fileへの追記だけで、各 fileの `_run()` / `pytest.main` 形状は維持される。`test_plain_runner_coverage.py:44`、`:60`

- **refuted** — `test_codex_reasoning_ab.py` が参照するのは変更した test module ではなく、未変更の production `tools/t189_oracle_wiring_slice.py` とその bytes pinである。今回の test-local helper追加では壊れない。`test_codex_reasoning_ab.py:119`、`:6351`
- **refuted** — B-10 provenance file 内の `plot_b10_extended_backoff` 参照も、変更した test moduleではなく production generator pathである。`test_b10_extended_figure_provenance.py:70`、`:157`
- **real** — `_run()` の変更は既存規約と一致する。`Skip` を一般 `Exception` より先に捕捉し、skipped countを表示し、failed がなければ rc=0。`test_plot_b10_extended_backoff.py:404`、`test_plot_backoff_ci.py:441`
- **refuted** — 新規 test file はない。`git status --short -- orchestrator/tests` は変更対象5 fileだけで、差分中の追加は各既存 module 内にある。`test_p3_exploration_namespace.py:514`、`test_t189_oracle_wiring_slice.py:132`、`test_t1434_t1222_science_slice.py:409`、`test_b10_extended_figure_provenance.py:891`、`test_plot_b10_extended_backoff.py:354`

## 6 依頼への到達度と三部形式の下書き

- **real** — 第1点「5分以内」に対し、この差分が動かす full-acceptance 秒数の上界は静的には言えない。親の限定計測では discovery 187 file が 1.718秒から0.285秒になったが、これは全走 wall の上界ではなく、15 node追加・collection multiplicity・並列競合も含まない。`s4-ruling.md:24`、`s4-ruling.md:28`
- **real** — 第2点「ループが回らなくなるリスク」には、campaign discovery の係数低下と外部入力欠落による acceptance hard red の回避で部分的に答える。一方、最長単体 node、実運用の進化探索 loop、collection の file 数比例という残余には触れていない。`s4-ruling.md:92`、`s4-ruling.md:94`
- **real** — 第3点で閉じたのは、既知4 moduleについて「root はあるが内容が欠ける」場合を exact requirements に基づく可視 skipへ変え、完全入力時には assertionを維持した点。`test_t189_oracle_wiring_slice.py:72`、`test_b10_extended_figure_provenance.py:142`
- **real** — 閉じていないのは、外部 file 依存そのものの除去・repository 内への収容・全 test sourceを横断した依存発見である。動的 git-ignore依存もscope外のまま。登録簿・全走査 gateはD335裁定に従い作っていない。`s4-ruling.md:81`、`s4-ruling.md:91`

親向け三部形式の下書き:

- **real — 何から何へ:** campaign driver discovery は「187 fileすべてを parse/walk」から「全 fileを read/NFKCし、marker候補だけparse/walk」へ変わり、限定計測は1.718秒から0.285秒。既知外部入力欠落は27既存 nodeの hard red 経路から内容単位skipへ変わり、acceptance universeは15件増える。`s4-ruling.md:26`、`test_p3_exploration_namespace.py:138`
- **real — 残る律速:** 5分全走wallは未測定、最長単体 nodeは未変更、collection の file 数比例は残る。加えて15 nodeはduration未登録で96番目cost代入となり、3 campaign moduleの構文被覆穴も残る。`conftest.py:1602`、`s4-ruling.md:92`
- **real — 次に何を削るか:** queue復旧後に焦点走と全走で実wallを測り、15 nodeのdurationを記録する。その上で最長単体 nodeの分割可能性を先に判定し、なおcollectionが律速なら並列contentionとledger payloadを削る。`rulings-verbatim.md:6`、`s4-ruling.md:92`

## must-fix 一覧

- **refuted** — must-fix 該当なし。D335違反、ledger 90%割れ、新規 shard component、完全入力時の既存 node skip、consumer破壊、新規 test fileのいずれも静的証拠で成立しない。`rulings-verbatim.md:23`、`test_acceptance_schedule_order.py:712`、`tools/acceptance_shards.py:321`

## nit 一覧

- **real — nit:** 新15 nodeのduration未登録により、その loadgroup unitは96番目既知costで代用される。選択集合・受理結果は変えないが、実測後にledgerへ収録すれば順序精度が上がる。`conftest.py:1584`、`:1605`
- **real — nit:** t189・t1434・plot B-10 は一つの node 内でも artifact JSONを複数回読み得る。受理集合・成果物値・参照は変えず費用だけなので must-fix ではない。`test_t189_oracle_wiring_slice.py:44`、`test_t1434_t1222_science_slice.py:24`、`test_plot_b10_extended_backoff.py:37`