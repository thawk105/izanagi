## 総括

- **real** — 現プランはそのまま author へ渡すべきではない。単位 A の `1.676 s → 0.245 s` はログインノード単一 process 内では実在するが、計算ノード 48 worker の wall 効果は未測定である。一方、単位 B の全-tree 登録 gate は D335 違反で、固定 literal 以外の repo 外入力も検出できない。根拠: `measurements.md:3-5,30-39,43-54`、`s2-plan.md:164-193,254-266`。
- **real** — 推奨する代替 scope は「既知の外部入力を module-local に防護し、動的 Git ignore 入力も閉じる」「全-tree 登録 gate は作らない」「性能面は T-2243 相当の計算ノード実測へ振る」である。単位 A は D335/D872 の扱いを裁定するまで、5 分問題の解決とは認定しない。根拠: `brief.md:19-22,75-80`、`rulings-verbatim.md:21-43,45-66`。
- **real** — `growth_test_holds.py` の現物は 61 entry ではなく **50 entry**。今回の A/B 対象 file は全て 0 entry だった。根拠: `growth_test_holds.py:155-616,665,798-810`。pytest は実走しておらず、以下は静的検査結果である。

## B-1 測定系を跨いだ一般化

- **real** — 親 brief はログインノード成分値を acceptance 改善 scope の根拠に置いているが、計算ノード wall への変換係数を持たない。`0.629 s` と `1.431 s` は各 probe 内では有効だが、`51.7 s` や `213.9 s` から引けない。根拠: `brief.md:19-22,33-46`、`measurements.md:3-5,37-54`。

- **real** — 明示的な比率混合は `s2-plan.md:254-258` の「27.4% × 85.4% ≒ 23.4 percentage point」である。27.4% は別の collector 計測、85.4% は別 probe の discovery 成分比であり、module collector 全体へ掛ける根拠がない。「上限寄り」でも有効な上限ではない。根拠: `measurements.md:28-39,43-47`、`s2-plan.md:254-258`。

- **refuted** — プランが acceptance wall 秒数を断定している、という強い疑いは退けられる。プラン自身が 48 worker wall、145 回分の加算、51.7 秒への同率適用、5 分達成を禁止している。根拠: `s2-plan.md:260-268`。ただし上記 23.4 pp 試算は削除すべきである。

- **real** — `3.437 / 12.542 = 27.4%` から言えるのは、「その計測 process では対象 file が file-collector 合計の27.4%だった」までである。対象 collector を全消去できた仮想上限でも、その走の file-collector 合計から 3.437 秒、collection 全体 14.36 秒の23.9%を超えては削れない。実際の prefilter 削減率、48-worker wall、51.7 秒の collective collection、全受入 wall は導けない。根拠: `measurements.md:43-54`。

- **real** — 48 worker は同じ collection を並列に行うため、理想的には 1 file の短縮は wall にほぼ「最遅 worker の短縮分」だけ効き、48 倍にはならない。3 shard process と login collect も重なって起動される。根拠: `measurements.md:47`、`acceptance_shards.py:1305-1335`。

  CPU 飽和が支配的なら、174 file 分の AST parse/allocation を除く効果は通常残り、aggregate CPU work ÷ 実効 core 数として効く。Lustre metadata/open/read が支配的なら `glob` と全 file の `read_text` が残るため効果はほぼ消える。memory 帯域が AST object の生成・walk 由来なら効くが、source read、page cache、他 module import 由来なら消える。根拠: `test_p3_exploration_namespace.py:131-147`、`s2-plan.md:19-29`。

## B-2 shard 割付と duration ledger への波及

- **real** — 既存 parameterized node ID が不変になる条件は、発見される stem の順序付き tuple、各 tree の `run_campaign` 判定、`hasattr(run_one_iteration)`、明示 `ids=[case[0] ...]` が全て不変であること。単なる set 一致だけでは一般には足りない。ただし現実装は sorted glob の filtered subsequence なので、同じ発見 membership なら順序も保たれる。根拠: `test_p3_exploration_namespace.py:131-158,574-577,1033-1035,1200-1202,1326-1328,1462-1464`。

- **real** — 単位 A は既存 ID を保っても、新設予定の2 test 自体が新しい node ID になる。現 ledger には両方とも entry がない。根拠: `s2-plan.md:31-55`、`acceptance_duration_ledger.json:19523-19525`。

- **real** — 単位 B の新規 file は、その file 内の全 node を一つの file component にする。group がなければ node 数を weight とする独立 componentとなり、全 component の LPT 再計算により既存 file の shard も移動し得る。ledger duration は shard 割付には使われない。根拠: `acceptance_shards.py:321-357,377-442,825-852`。

- **real** — ledger にない node は `_acceptance_duration_for_item` が `None` を返す。その node を含む loadgroup 全体が unknown となり、既知 unit があれば「96番目、または最後の既知高コスト値」を仮コストとして並べ替えられる。既知値が一件もなければ並べ替えない。ゼロ扱いではない。根拠: `conftest.py:904-906,1524-1544,1584-1617`。

- **refuted** — 新規 metatest に既存 xdist group や `REAL_REPO_ACCESS_BY_NODE` を付ける必要はない。計画上は checked-in source と `tmp_path` 上の guard を読むだけで、同 map が保護する親 working tree・共有 ccbench の reader/writer ではない。根拠: `conftest.py:258-388,511-561,1993-2001`。外部 root に suite 内 writer を追加する場合だけ再判定が必要である。

## B-3 scope の妥当性と repo 外束縛の全数

- **real** — brief の `test_t189...` と `test_t1434...` は独立2例ではない。同じ `/work/1/SFC/tanab/dev-wave-jobs` を読む同じ T-1434 系である。Git 履歴でも前者は `56ae5e848`、後者は `f24550a01`、同じ作者・同じ2026-08-28であり、独立 producer/consumer の証明にはならない。根拠: `brief.md:62-68,102-104`、`test_t189_oracle_wiring_slice.py:38,84-92`、`test_t1434_t1222_science_slice.py:21,49-55,77-84`。

- **real** — addendum の B-10 系は別 root・別 consumer 系統だが、2 file とも同じ commit `637dafa17` で同時導入されている。dev-wave 系との producer/consumer 多様性はあるものの、厳格な「独立再現」は静的資料から認定できない。新しい一般 registry/framework を許す根拠としては不足し、局所修復が妥当である。根拠: `brief-addendum.md:44-48`、`test_b10_extended_figure_provenance.py:21-24,282-308`、`test_plot_b10_extended_backoff.py:15-18,146-150`。

- **refuted** — original brief の「3件が全数」は addendum 自身により訂正済み。固定された `/home/`、`/work/`、`~/` literal については19個を確認し、通常時に実読込する固定既定値は addendum 記載どおり5 test module・3 rootだった。根拠: `brief-addendum.md:3-23,25-42`。

- **real** — ただし「repo 外束縛の全数は5 file」も、実行時入力全体については不成立である。`output_snapshot_ignores.py` は `git rev-parse --git-path info/exclude` と `git config --get core.excludesFile` の返す path を `expanduser()` し、実際に bytes を読む。これは新 gate が列挙する `test_*.py` の外にあり、absolute literal でもないため検出されない。consumer は `test_s8b_oracle_driver.py:570-643`、`test_s8b_floor_campaign.py:1700-1725`、`test_real_repo_serialization.py:722-803`。根拠: `output_snapshot_ignores.py:73-111,206-213`、`s2-plan.md:168-171`。

- **real** — 環境変数由来では、B-10 2 module の repo 外既定値に加え、`IZANAGI_SORT_SWO_REAL_MASSTREE_ROOT` を読む2 nodeがある。後者は env 未設定なら内容読込前に skip するため、防護済みの opt-in 外部入力であり、通常 acceptance の暗黙依存ではない。根拠: `test_sort_swo_dependency_material.py:329-338`、`test_s8b_floor_campaign.py:2623-2633`。

- **refuted** — `Path.home()` の実使用は `orchestrator/tests/` に見つからなかった。`expanduser` の実入力依存は上記 Git helper であり、`test_hooks.py:1091-1100` は tmp root へ差し替える合成 fixture である。

- **refuted** — 残る14個の machine-looking literal は実 filesystem を読まない fixture/契約値だった。対象は `test_acceptance_nproc_study.py:1334,1338`、`test_claude_session_ledger.py:1773`、`test_codex_reasoning_ab.py:397`、`test_hooks.py:1096`、`test_mocc_trace_pair.py:256,403,413`、`test_paper_story_a1_paired.py:873`、`test_paper_story_a2_certification.py:2464`、`test_pegasus_tools.py:427,461`、`test_real_repo_serialization.py:5399`、`test_t316_sandbox_probe.py:962`。

- **refuted** — 単位 A は collection 秒数の threshold gate を追加していない。追加予定は固定7件 pin と bounded fixture の等価性 gate であり、DW-G05 違反ではない。根拠: `s2-plan.md:31-55`。threshold 不在は問題ではなく、後述する成長比例構造の残存が問題である。

## B-4 成長比例構造の判定

- **real** — prefilter 後も `_discover_campaign_drivers` は全 `orchestrator/campaign/*.py` を glob/read するので、費用は `O(total source bytes + marker-hit AST bytes)` のままである。係数は下がるが傾きは消えず、repository 成長で再び同じ費用へ戻る。根拠: `test_p3_exploration_namespace.py:131-147`、`s2-plan.md:19-29`、`rulings-verbatim.md:21-43`。

- **real** — file mix・平均 size・marker hit 率が現在と同じという条件付き線形外挿では、`187 × 1.676 / 0.245 = 1279.2`、すなわち約 **1,280 file**（現在から約1,093増）で prefilter 後費用が現在の prefilter 前 1.676 秒へ戻る。全追加 file が marker-negativeならより遅く、marker-positiveや大型ならより早い。根拠: `measurements.md:28-35`。

- **real** — metagate (a) は全 `test_*.py` を glob/readし、hit fileをAST parseする新しい file/bytes 比例 test なので、D335 の直接違反である。明示的な user supersede がない限り must-fix。根拠: `s2-plan.md:164-172,276-280`、`rulings-verbatim.md:23-38`。

- **real** — metagate (b) も registry 全 row で parameterize し、row 数と requirements 数に比例して node・collection・実行費用が増える。D335 が明記する「台帳の分量」比例に当たる。根拠: `s2-plan.md:191-193`、`rulings-verbatim.md:23-24`。

- **real** — growth-hold 現物は50 entryで、`test_p3_exploration_namespace.py`、t189、t1434、B-10 2 file、新規 metatest のいずれも含まれない。しかも A の scan は module import 時に起き、hold marker は collection 後半で付くため、node hold を足しても scan 費用は消えない。根拠: `growth_test_holds.py:155-616,665`、`test_p3_exploration_namespace.py:147`、`conftest.py:1985-2032`。

## B-5 依頼への適合と配分

- **real** — 第3点の局所 guard は、外部資源消失時に全 wave が hard-red になる可用性障害を防ぐため、厚く扱う価値がある。ただし registry/metagate framework まで広げる配分は DW-G03/D335 に反する。根拠: `brief.md:10-22,79-80`、`brief-addendum.md:50-61`。

- **real** — 第1点に対する計算ノード上の certified 改善秒数は **未測定**。参考尺度にすぎないが、ログインノードで得た 1.431 秒は既知床 `126.13 + 56.3 = 182.43 秒` の0.78%、対象 collector 全体 3.437 秒でも1.88%である。実測最遅 shard 213.9 秒に対しても、この wave だけで5分リスクの主要因を解いたとは言えない。根拠: `measurements.md:30-32,44-54`。

- **real** — Unit B は通常の資源存在時には wall を短縮せず、存在しない場合の terminal outcome を fail/error から明示 skip へ変える可用性修復である。元 node の selection は維持され、追加 guard tests だけが universe と ledger を増やす。根拠: `brief.md:79-80`、`s2-plan.md:95-141`。

- **real** — brief の成果物は D312 に部分適合だが不十分である。「現況 wall」と訂正 insight はあるものの、必須の「何から何へ／残る律速／次に削る箇所」を明示していない。プランも禁止事項は列挙するが、最終材料レポートの三部形式を固定していない。根拠: `brief.md:83-87`、`s2-plan.md:250-268`、`rulings-verbatim.md:3-11`。

- **real** — 代替 scope は次が妥当である。

  1. 5つの固定既定値 consumer を module-local な内容 guard で修復する。
  2. `output_snapshot_ignores.py` の global excludes/info-exclude 依存を、checked-in 規則へ閉じるか明示契約化する。
  3. registry と2本の全体 metagateは作らない。
  4. 性能面は T-2243 の計算ノード48-worker分解と同条件 A/B を先に行い、その結果で prefilter、ledger圧縮、prewarm の順を決める。
  5. 材料レポートは before/after、残る126秒 node・collection、次の削減対象を記録する。

  根拠: `rulings-verbatim.md:135-154`、`measurements.md:48-54`。

## must-fix 一覧

1. **real** — `test_external_path_bindings.py` の全-tree gateと全-row parameter gateを削除または明示的な user supersede 待ちにする。根拠: `s2-plan.md:164-193`、`rulings-verbatim.md:21-43`。  
   **成果物影響:** acceptance universeから新規 metagate node群を除き、duration ledgerにもその未知keyを追加しない。既知 consumer の bounded module-local guard nodeだけを受理対象にする。

2. **real** — 「repo 外束縛は5 fileで全数」という成果物表現を修正し、動的 `info/exclude` / `core.excludesFile` と opt-in env rootを別区分で列挙する。根拠: `output_snapshot_ignores.py:73-111`、`test_sort_swo_dependency_material.py:329-338`、`test_s8b_floor_campaign.py:2623-2633`。  
   **成果物影響:** 材料レポートの値を「固定既定値5 module・3 root」へ限定し、動的Git入力の3 consumerと防護済みopt-in 2 consumerへの参照を追加する。

3. **real** — `27.4% × 85.4% = 23.4 pp` を効果見積りから削除し、計算ノード同条件 A/B がない限り acceptance wall 改善を未測定とする。根拠: `measurements.md:3-5,28-54`、`s2-plan.md:254-265`。  
   **成果物影響:** 材料レポートは `1.676 s → 0.245 s` を単一-process probe値としてのみ載せ、certified acceptance wall 値は空欄/未測定にする。

4. **real** — 単位 A を「成長比例問題の解決」として受理しない。D335準拠の import前 hold/非成長設計か、D872との衝突に対するユーザー裁定が必要である。根拠: `test_p3_exploration_namespace.py:131-147`、`conftest.py:1985-2032`、`rulings-verbatim.md:21-43,45-66`。  
   **成果物影響:** certified 選択結果では A を暫定最適化または裁定待ちとし、「liveness risk解決済み」集合へ入れない。

5. **real** — hold 数を61から50へ訂正し、D312の三部形式を成果物契約へ追加する。根拠: `growth_test_holds.py:155-616,798-810`、`brief.md:83-87`、`rulings-verbatim.md:3-11`。  
   **成果物影響:** insight の hold countを50へ変え、材料レポートに before/after、残存律速、次の削減対象を必須 fieldとして追加する。

## nit 一覧

- **real** — 新しい bounded guard testや単位 A の2 nodeは初回 acceptance では ledger unknown になる。初回実測後に ledgerを再生成しないと96番目既知値で仮配置される。根拠: `acceptance_duration_ledger.json:19523-19525`、`conftest.py:1584-1613`。
- **real** — 新 file追加で shard 割付は全体再計算されるため、「新 fileだけが空き shardへ足される」とは報告しない方がよい。根拠: `acceptance_shards.py:377-442`。
- **refuted** — 新 metatestへ `real-repo` groupを付けないこと自体は問題ではない。むしろ不要な group追加は既存巨大 componentへ連結し、shard balanceを悪化させる。根拠: `acceptance_shards.py:321-357`、`conftest.py:1993-2001`。