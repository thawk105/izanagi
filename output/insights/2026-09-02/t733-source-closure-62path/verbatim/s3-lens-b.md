## 総括

段2プランはそのままでは差し戻しである。明示 import の36 moduleという測定は再現したが、Pythonが必ず実行する package initializer 2本を落としており、実効的な第1層は38 module、合計62 pathである。  
推移閉包131 moduleは独立再導出でも集合差ゼロだった。一括収載は可能だが、変更頻度とテスト時間の代償が大きく、D1075が許す段階実装として62 pathで区切る方が妥当である。  
より重大なのは旧exact-24 E1 lockである。repo内は0件だが、直近の実測記録には外部official 5件があり、プランどおり旧24 mapをcodecで拒否すると歴史閲覧まで失う。ここは実装前の裁定が必要である。  
以下は静的読解とread-only再計算であり、pytestは実行していない。

## real な所見

1. **実効的な直接import frontierは36でなく38 moduleである。**

   - 根拠: `orchestrator/campaign/guided.py:47` が `orchestrator.critic.online_digest` をimportすると、先に `orchestrator/critic/__init__.py:12` が実行される。`orchestrator/campaign/pipeline.py:229` の `qualification.artifacts` も `orchestrator/qualification/__init__.py:7-19` を先に実行する。
   - 提供された36集合との差分は次の2本だけだった。
     - `orchestrator/critic/__init__.py`
     - `orchestrator/qualification/__init__.py`
   - **成果物影響:** 60 pathのままでは、この2本を差し替えても記録mapとE1値が変わらず、「直接委譲1段目まで収載」という`identity_scope`が偽になる。
   - 推奨対応: 新規suffixを辞書順38本にし、exact **62 path**、131中62、未収載69へ修正する。明示AST edgeだけを対象にするなら、文言を「明示import graphの1段目」と弱め、実効的閉包とは名乗らない。

2. **旧exact-24 E1 lockを一律拒否する計画は、既存official成果物との非互換を発生させる。**

   - 根拠: `campaign_lock.py:221-233`は目的判定より前にcurrent tupleとのexact key一致を要求する。段2は旧24 map拒否を明示している `s2-plan.md:88-97`。
   - repo内32 lockが全E0なのは再確認できた。一方、直近の外部実測記録にはexact-24 officialが5件、B10 3件とpaper-story A2 2件ある `output/insights/2026-08-28_t2008-d1163-closure-mismatch/verbatim/s3-lens-b.md:76,198-204`。
   - **成果物影響:** 5件が残っていれば、HISTORICAL_RAWを含む全経路でcodec errorとなり、B10/A2の参照と再描画が不能になる。
   - 推奨対応: 外部rootを再測後、少なくとも「旧24は歴史閲覧のみdecode可、現行certified適合は別判定」とするか、5件を失効させる裁定を得る。現状のpre-T733拒否テストを先に固定してはならない。

3. **順序検査のepoch oracleは独立known-answerではなく、fixture literalからの再導出である。**

   - 根拠: `test_artifact_admission.py:426-437`は`_EXPECTED_E1_CLOSURE_PATHS`とindexから期待E1をその場で再計算する。`test_t671_source_binding.py:23-55,180-206`もproduction tupleの別写しである。
   - **成果物影響:** production tupleと2個のtest literalを同時に並べ替えると、E1 preimageが変わっても検査が追随して緑になり、同じ記録mapから従来と異なるE1値を発行する。
   - 推奨対応: synthetic fixtureに対する固定known-answerを追加する。推奨62-path案なら期待値は `E1:78920efc47f4eb280b956a8fb92abed16b888495db544b62b1a15bf1f61004e9`、ordered-list SHA-256は `3a8bddc60b8ede29788c6628a88d33d7285735308c9f5d1d2fd4885f6e81cd27`。60-path案ならE1は `E1:171399b16ec64995560e0c9cce87606d610ec71162a7e821f67d4bcfff354c63`。

4. **D1075名指しの6種だけでは完了条件も理由部分も満たさない。**

   - 根拠: calibratorだけでも`execution_guard.py:22-23`と`pipeline.py:26-30`が`schema_v2`、`effective_clock_policy`、`perf_preflight`、`runner`、`stability`へ直接委譲する。さらに`pipeline.py:59-70`は`axis_trigger_gating`、`reflux_ir`、`trigger_gate_binding`へ委譲する。
   - **成果物影響:** 6種以外の直接委譲先を差し替えて拒否、trigger binding、holdout判定等を変えてもepochが変わらず、同じsource-bound参照の下で結果や受理判断が変わる。
   - 推奨対応: 6種案は「高リスク先行の中間段」としてのみ可。完了や直接frontier収載とは扱わず、62-path案を第1層の原則的境界にする。

5. **producer一覧はほぼ正しいが、出力影響の分類が不足している。**

   - 根拠:
     - `critic/digest.py:1202-1221`の文字列は単なる表示ではなく、`guided.py:161-175`でcriticに渡すstdoutになる。
     - `tools/plotting/plot_b10_extended_backoff.py:742-744,898-917,1179-1184`は入力datのepoch objectをprovenanceへ再出力する。
   - **成果物影響:** guided再実行ではcritic入力bytesが変わり、選択するgenomeとWAL列まで変わりうる。B10 plotterは同じ凍結入力なら不変だが、更新後datから再生成すればprovenance JSONが変わる。
   - 推奨対応: `guided.py`をcritic textの実consumerとして表へ追加し、`plot_b10_extended_backoff.py`を「直接変更なし、入力再生成時のみ変化する二次producer」と明記する。

## refuted な所見

1. **「131 moduleにも同種の相対import解決誤りがある」疑いはrefuted。**

   現行24 pathをseedに、相対level、`from . import x`、package initializer、repository内module解決を独立実装して固定点まで再計算した。結果はseed 24、新規107、合計131で、`closure-measure.txt:1-108`との集合差は両方向ゼロだった。文字列dynamic import 2件も既存seedへの参照だった `s8c_preregistration.py:1769-1810`。

2. **「1段目で止めること自体が完全に恣意的」という疑いはrefuted。**

   D1075は段階実装を明示的に許す `rulings-verbatim.md:240-254`。graph距離1は再現可能な中間境界である。ただし数は60でなく62で、閉包完成ではない。

3. **段2が列挙した以外に、24というclosure countを固定するproduction/current testは見つからなかった。**

   `rg`で確認したcurrent count面は`campaign_lock.py`、`contract_loader_binding.py`、`artifact_admission.py`、計画記載の3 test fileに閉じる。その他の`==24`はrow数、秒数等だった。`CONTRACT_LOADER_RELATIVE_PATHS`を動的参照する`test_bench_first_real_wal.py:171-177`、`test_s6_sort_sweep.py:671-677`、`test_s8a_trigger_sweep.py:882-888`等は自動追随する。

4. **凍結fig2b/fig2c/fig4を再生成する必要がある、という疑いはrefuted。**

   F712どおりcurrentとfrozenのgoldenは分離されている。fig2cのexact-24を含む既存provenanceは生成時記録として据え置ける。変更するのはcurrent goldenだけでよい。

5. **`autonomous_trial_completeness.py`がproducerであるという分類はrefuted。**

   `autonomous_trial_completeness.py:4981-5032`はpersisted/fresh/validator projectionを比較するだけで、この経路からepoch bytesを書かない。段2の比較器への再分類が正しい。

## 親 brief 自身の誤り

1. **frontier 30は誤り。** 親が確認済みの明示import漏れ6本に加え、実効Python importとしてpackage initializer 2本も漏れている。正しくは明示edge 36、実効edge 38、合計62 path。

2. **「閉包成長は受理集合を狭める方向だけ」は誤り。** `campaign_lock.py:221-233`のwire languageは旧exact-24拒否、新exact-62受理という非互換な置換であり、集合の単純な部分集合化ではない。

3. **「失効するcertified campaignは0件」はrepo内tracked 32件に限定すれば正しいが、既存成果物一般への一般化は誤り。** 直近実測には外部exact-24 officialが5件ある。現在も存在するか再測が必要である。

4. **first-party import推移閉包131は正しい。** 独立導出との差分はない。

5. **producer 9本一覧は誤り。** plotting 2本の不足と`autonomous_trial_completeness.py`の誤分類は段2の訂正どおり。加えてguided stdoutへの実利用とB10の二次伝播を明記すべきである。

## 変異事前登録の評価

1. **`runner.py`をtupleから削除**

   - 判定: **有効だがliteral依存、同時更新で無力化されうる**。
   - productionだけを変異すればexact tuple testが落ちる。test literalも同時変更すると落ちない。
   - 代替: test fixtureを変えないproduction-only mutationとして事前固定し、ordered-listの固定SHAも検査する。さらに対象を62 pathへ修正する。

2. **clean binding後に`buildcache.py`へ1 byte追加**

   - 判定: **有効**。
   - `test_t671_source_binding.py:518-543`はclean capture後のdisk/commit blob差を検査し、対象pathと`contract-loader-drift`まで要求する。literal一致だけではない。
   - 恒真性: 静的にはなし。無変異時は同一bytesなので例外条件に入らない。

3. **authority検査をsubset許容へ弱化して旧24 mapを受理**

   - 判定: **検出力は有効だが、現時点では誤った仕様を固定する危険がある**。
   - 提案テストは緩和変異を落とすが、外部official 5件の歴史閲覧も拒否する仕様を固定する。
   - 代替: 旧24 mapのHISTORICAL decode正例、現行certifiedでの明示的な適合判定負例を分離し、そのcertified gate削除を変異にする。

4. **live verify loopを`[:-1]`へ短縮**

   - 判定: **有効**。
   - 最後の`qualification/series.py`をdirtyにするcaseだけが例外を得られず落ちる。loopの実効性を直接検査しており、literalだけの検査ではない。
   - 62 pathにしても辞書順suffixの末尾は同じである。

5. **追加path 2本を入れ替える**

   - 判定: **production-onlyなら有効、fixture同時更新で無力化されうる**。
   - 現在案のepoch期待値はfixture tupleから再計算されるため、productionとfixtureを一緒に並べ替えると追随する。
   - 代替: 上記固定E1 known-answerとordered-list SHAを追加する。通常のtuple equality、固定list hash、固定epoch hashの3面で検査する。

静的評価上、5件のうち「変異なしでも必ず落ちる」恒真テストはない。ただし1と5は独立な意味論検査ではなく、policy literalの鏡写しである。

## 見積り

- source量:
  - 現行24: 21,699行、905 KB
  - 段2の60: 41,597行、1.78 MB
  - 推奨62: 60案から45行、1.4 KB増
  - 全131: 107,741行、4.67 MB
  - 62から全131へ追加する69本相当は約66,100行、2.89 MB規模

- 編集量:
  - 62-path案: production 3 fileとtest 4 fileで概ね170から230変更行。
  - worklog、decision fragment、insightを含めると追加30から80行程度。
  - 全131案は3個の独立tupleへさらに約207行のpath literalが必要で、合計380から450変更行程度。

- test数:
  - 60案: path全数5 familyで180 case増、旧24 rejection 1件を加えて約181件増。
  - 推奨62案: 約191件増。
  - 全131案: 約536件増。

- test時間:
  - duration ledger上、現在のGit-heavyな4 familyは24 pathで合計約10.96秒。
  - path数に対して概ね二乗で増えるため、60で約68.5秒、62で約73秒、131で約326秒と推定する。
  - 他の動的v2 fixtureも1 testあたりの`git cat-file`回数が増える。受入全走の直列時間増分は62で約1から2分、131で少なくとも6分前後を見込む。実走値ではない。

- production実行:
  - `capture`、live verify、committed verifyはpathごとに別の`git cat-file` subprocessを起動する `contract_loader_binding.py:348-400`。
  - 24から62は約2.58倍、24から131は約5.46倍のper-call path処理になる。
  - lock内blob mapは約2.6 KBから62で約6.6 KB、131で約14.4 KBなので、保存容量よりprocess起動回数が主な代償である。

- 追加71 moduleの高頻度面:
  - 2026-08-01以降の非merge commit数上位は、`s8b_floor_campaign.py` 47、`p3_s4_loop.py` 38、`p3_s4_loop_trigger_gating.py` 31、`p3_s4_loop_sort.py` 21、`critic/digest.py` 18、`s1_direct_comparison.py` 16、`s8b_holdout_freeze.py`と`silo_ladder_rung1.py`各15、`s8b_holdout_admission.py`と`s6_sort_sweep.py`各14である。
  - 同期間に60集合を触った非merge commitは180、全131なら298。追加層だけでさらに118 commit、約66%多くepochを動かす履歴だった。

- 分割:
  - 旧24を一律拒否する現プランだけなら、code/testの密結合からauthor 1子で足りる。
  - 歴史互換を維持するなら、低層tuple/codec/bindingと、purpose別legacy admission/producer consumerを分けるべきである。reason enumやschemaまで増える可能性があり、production 3 + test 4には収まらない。

## nit / 裁定パッケージ候補

- **裁定必須:** 外部exact-24 official 5件を、歴史閲覧のみ残すか、現行certifiedにも残すか、完全失効させるか。
- **裁定候補:** closure edgeを「明示AST import」「Python package initializer込み」「dynamic/data/subprocess込み」のどこに置くか。今回の推奨はpackage initializer込み62 pathである。
- **裁定候補:** 全131一括収載は、追加118 epoch-changing commit相当の運用負担を受け入れるか。現時点では62を第1段、その後を別waveにする方を推す。
- **scope外候補:** admission overlay JSON、Pegasus policy、qualification schema、external Git、subprocess binary等の非import material。段2が列挙したとおりsource-import closureとは別のbinding判断が必要である。
- **nit:** 新規約191 nodeはduration ledger未登録になるが、coverage閾値90%を割る規模ではない。 correctness blockerではない。