## 総括

結論は実装0 byteです。ただし、plan v2の最終裁定は妥当でも、「安全な構造候補すら存在しない」という論証は過剰です。

実際には、T-080の2 variantにprocess内の共通構築prefixが存在します。また、無変更が証明済みの区間でのsnapshot再利用は検出力を必然的に落としません。しかし、どちらも現行制約下で86.57秒の最長nodeを短縮する実益が立証されていません。したがってauthorへ進む根拠にはなりません。

Web、書込み、test実走は行っておらず、新たな緑は報告しません。

## real findings

1. `共通prefix再利用 = variant統合` は成立していません。

   process cacheのkeyは`distinct_basis_blob`を含みますが、両variantの構築は分岐点まで同一です。[test_s8b_oracle_driver.py:909](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:909) [test_s8b_oracle_driver.py:1015](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1015) [test_s8b_oracle_driver.py:1078](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1078)

   最小反例は、分岐前のbasis repoをprocess内に保持し、2つの独立実体へcopyした後、片方だけdescriptorを変えて別commit、別receiptを作る構成です。現行helper自身も各consumerへ独立treeとdeepcopy済みdocumentを渡しています。[test_s8b_oracle_driver.py:925](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:925)

   これはworker/session跨ぎcacheでも、2 variantを同じbasisへ潰す統合でもありません。したがってplan v2の「共通prefixはvariant統合なので除外」は分類として強すぎます。[plan-v2.md:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-acceptance-longest-node/resume-20260828-0725/s2/plan-v2.md:23)

   成果物影響はplan文書の根拠訂正です。実装候補としては後述の効果gateを通りません。

2. 固定argvでは既存process cacheに同一key hitがありません。

   actual受理集合は、floor snapshot、`ccbench-current` 1 case、distinct-basis draft-finalize、T-080 snapshotの4 nodeだけです。[baseline-argv.md:6](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-acceptance-longest-node/resume-20260828-0725/baseline-argv.md:6)

   `ccbench-current`はdefault key、次のdraft-finalizeは`distinct_basis_blob=True`です。[test_s8b_oracle_driver.py:1371](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1371) [test_s8b_oracle_driver.py:1471](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1471) よってfresh processでは2回ともcache missです。

   helper全体の「6 function / 11 node」や過去の同一引数7回構築という説明は、この固定sliceの効果量へ一般化できません。[test_s8b_oracle_driver.py:895](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:895) [test_s8b_oracle_driver.py:930](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:930)

   成果物影響は効果説明です。0 byte裁定を弱めるのではなく、むしろ既存cache拡張では固定sliceを短縮できない根拠になります。

3. 無変更区間の再利用について、安全性と実益が混同されています。

   例えばT-080 snapshotの626行目から629行目まで、対象treeを変える処理はありません。[test_s8b_oracle_driver.py:626](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:626) 状態が変わっていないことまで独立に証明できるなら、同じrules値の再利用は観測結果を変えません。したがって「再利用そのものが検出力低下」は過剰です。

   一方、無検証memoは明確に危険です。rules helperは毎回、規則sourceだけでなく実在するignored pathを`git ls-files -o -i`で再観測します。[output_snapshot_ignores.py:206](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/output_snapshot_ignores.py:206) [output_snapshot_ignores.py:244](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/output_snapshot_ignores.py:244) 実際、path作成後にprefix集合が変わるcontrolもあります。[test_s8b_oracle_driver.py:690](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:690)

   安全な再利用には規則source、index、tracked例外、ignored実在treeの再検証が必要で、その確認は現在のGit照会の大半を再実行します。成果物影響はありません。安全だが実益が消える候補です。

## refuted findings

- optimized/reference間でrules値を共有する案は棄却します。両実装は別々にrulesを取得し、walkとdigestも独立しています。[test_s8b_floor_campaign.py:1647](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_floor_campaign.py:1647) [test_s8b_floor_campaign.py:1676](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_floor_campaign.py:1676) 値源共有は禁止条件そのものです。[authority-v2.md:23](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-acceptance-longest-node/resume-20260828-0725/s2/authority-v2.md:23)

- T-080共通prefixを直ちに実装すべきという攻撃も棄却します。Git-visible outputの複製はuntracked増減を隠さないためmemoを明示的に避けています。[test_s8b_oracle_driver.py:879](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:879) また、variant固有のchild finalize、verify、gateと、その後のheld/released検証は共有できません。[test_s8b_oracle_driver.py:1240](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1240) [test_s8b_oracle_driver.py:1383](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1933-acceptance-longest-node/orchestrator/tests/test_s8b_oracle_driver.py:1383)

- 親P1を「acceptance全体最長がscope内」と読む主張は棄却します。全体最長140秒はscope外です。[brief.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-acceptance-longest-node/resume-20260828-0725/brief.md:11) P1が成立するのは「固定owned slice内最長」を意味する場合だけで、その値は現在86.57秒です。[baseline-argv.md:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1933-acceptance-longest-node/resume-20260828-0725/baseline-argv.md:19)

- snapshot短縮が最長nodeを動かすという攻撃も棄却します。snapshot 2 nodeの全消去でも上限は6.79秒で、86.57秒nodeもscope外140秒nodeも変わりません。

## plan攻撃

plan v2は結論を維持できますが、次の形へ根拠を修正すべきです。

- 「安全候補がない」ではなく、「受理集合、live再観測、独立oracle、D104を維持し、かつ86.57秒のcritical nodeを下げる候補がない」と限定する。
- snapshot案を、無検証memoはunsafe、optimized/reference共有は禁止、変更確認付き再利用はsafeだが実益なし、の3件へ分離する。
- T-080案では、process-local共通prefixは構造上残るが、live source再検証と独立copyが必要で、production履歴走査を減らさず、最初の86.57秒nodeへcopy overheadを追加し得るため不採用、と記録する。
- actual受理4 nodeと順序を明記し、helper全体11 nodeや過去の7回重複を固定sliceへ一般化しない。
- 「単一原因が安全性gateと効果gateの両方を通らない」ではなく、候補ごとに落ちるgateを明記する。

## 推奨裁定

実装0 byte、段5 authorへ進まない、を推奨します。

理由は恐怖による停止ではありません。構造上安全化できる候補は残りますが、live再観測に必要な再検証コストを除けず、独立oracleやheld/released、single exact reasonを共有できず、production履歴走査も残ります。したがって、現時点で4条件とcritical-node短縮を同時に満たす候補はありません。

plan v2の結論は採用し、上記の過剰な分類とactual sliceの説明だけを裁定記録で訂正するのが最小です。
