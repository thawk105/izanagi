**nodes=5の採用は、policy・pin・fixtureを同じ変更単位で整合させる方針で成立します。node-local lockは条件付き候補です。P1はhead間では妥当ですが、共通job bodyの変更だけでは全bencherの同一ノード排他を保証できません。**

指定資料と関連コードを静的に確認しました。書込み・pytest・計算ノード実測は行っていません。以下の行番号は変更前です。

**1. briefへの検証結果**

- **P1：job固有TMPDIRの不採用は成立。** `lock.py:49–54`は同じファイルへの`flock`で排他するため、jobごとに異なる`TMPDIR/bench.lock`では同一ノードの別jobが同時取得できます。既存b10/a5の設定は、この要件の正例にはなりません。
- **P1：同一user・同一node固定点は、A-2/A-6 head間の最小候補として成立。** 両policyは同じjob bodyを使用します。ただし`/scr`が計算ノード間で独立し、同一ノードの別jobには同じ名前空間として見えることは実測対象です。
- **P1の保証範囲は未成立。** `verify_fanout_worker.py:534–535`は継承値を`task_root/bench.lock`で上書きします。また、共有homeの既定lockを使う別launcherとは、新しいhead lockが分離します。後者は従来あった協調排他を失う可能性があるため、単なる既知制限として済ませず、対象運転で同居しない予約条件を確認する必要があります。確認できなければlock部分の採用を保留します。
- **P2：2ノードの実`bench_lock` probeは成立。** 機構・filesystemの直接確認には十分小さい案です。ただし、手で同じ環境変数を設定したprobeだけでは本番job bodyのexport漏れを検出できません。launcherから子processへの継承確認を追加します。
- 旧insightの共有homeによる直列化は、記述どおり時刻整合からの強い推測です。今回の直接probeは現在の機構を立証できますが、過去attemptの全待ち時間の原因まで確定しません。

**2. 変更候補と最小pin／fixture閉包**

| 変更候補file:line | 具体的な変更 |
|---|---|
| `orchestrator/campaign/paper_story_a2_certification.v2.json:132` | `scheduler.nodes`だけを1→5。 |
| `orchestrator/tests/test_paper_story_a2_certification.py:1864` | policy bytesのliteral pinを2箇所更新し、`nodes == 5`を明示。protocol pinは維持。nodesだけ1へ戻した文書とのprotocol preimage一致も確認する。 |
| 同file`:2066` | A-2も兄弟4hostを受理する正例へ変更。既存の不正host負例をA-2/A-6双方に適用する。 |
| 同file`:2094` | 単一ノード契約を残すため、このテスト内だけnodes=1のpolicy fixtureを明示的に作る。現行A-2へ1hostを渡して落ちるだけでは、名前に反して単一ノード契約を検証できない。 |
| 同file`:4908, 4930, 4969, 4991, 5223, 5518` | `run_workload()`呼出しへ妥当な兄弟4hostを渡す。必要なfixture hostnameも固定し、元のpin・source・condition検査へ到達させる。 |
| `orchestrator/tests/test_paper_story_a2_job_contract.py:754` | A-2の既定nodefileもhead＋兄弟4台にする。 |
| 同file`:1273` | submitterの正確なargv期待値を`-b 5`へ更新。 |
| 同file`:988` | nodefile不足・過剰・重複による一意host不足の負例をA-2にも適用。 |
| `tools/pegasus/paper_story_a2_certification.sh:340–368` | 実測候補として固定lock pathをexport。採用は局所実測後。 |
| `orchestrator/tests/test_paper_story_a2_job_contract.py:38, 733`付近 | exportの位置・子への継承・別jobでも同じpathとなることを検証。実排他はstubしない別process試験で確認する。 |

`run_workload()`は冒頭の`paper_story_a2_certification.py:3664`でhost数を検査します。したがって上記呼出しを空tupleのまま残すと、既存の負例が**本来の拒否理由へ到達する前に落ちる**ため、pin更新だけでは閉じません。

共通`_policy()`（テスト`:1035`）を一律nodes=1へ戻して赤を消す方法は採りません。出荷policyの5ノード化をfixtureが隠してしまいます。

静的なbytes計算とtracked検索で確認した値：

- 新policy SHA：`f8a7780600766e6c8e0248ae0e3aff70a2e1c28150f8932842cdbf67f988472c`
- 旧policy SHAのtracked参照：上記テスト`:1869,1871`のみ。
- 現job body SHAのtracked参照：なし。
- protocol SHA：`d99f08bcc50c605d24d443d387a2c3144c16b9e670c9b9e247227c5db1be7f9c`を維持。`paper_story_a2_certification.py:344`のpreimageにschedulerはありません。

既存receipt fixtureのqsub argv・job body SHA・reservation SHAは、テスト`:1471,1520,1578`でpolicy／実ファイルから生成されています。ここへ新literalを追加する必要はありません。A-6 policy、submitter本体、汎用`lock.py`、worker本体の変更は最小案に含めません。

**3. lock pathの実装方向**

最小候補は、既存の固定親directoryを使う次の配置です。

```bash
scratch_base=/scr/${USER}/paper-story-a2-certification
scratch=$scratch_base/${pbs_jobid_path_component}
# 既存の mkdir -p "$scratch_base" の後
export IZANAGI_BENCH_LOCK="$scratch_base/bench.lock"
```

A-6も同じjob bodyを使うため、同一user・同一nodeのA-2/A-6 headは同じファイルを開きます。job ID、attempt、workload、worktreeをlock pathへ含めません。親から継承したjob固有lock値もここで置き換えます。

lockファイルを終了時にunlinkせず、固定親directoryもjob scratchの後片付け対象にしません。保持中のファイルを削除・再作成すると、別inodeを取得できて排他が破れます。既存の`finish()`（job body`:64`）はscratchを削除していません。

`pipeline.py:1386,2399`の排他区間、競合process検査、認証・anomaly拒否条件は維持します。特にheadはfan-out完了までlockを保持するため、排他範囲の短縮はこの変更へ混ぜません。

**4. 親が行う局所実測**

既存runbookのbatch運転（`docs/pegasus-runbook.md:94`）を使い、短い2ノード予約を取得します。親が投入直前にqueue状態を再確認し、request ID、割当nodefile、stdout/stderr、終了会計を保存します。briefの「ACT確認済み」は将来の投入可否の保証には使いません。

probeはwave専用の小さいscriptとし、既存`bench_lock()`を直接呼びます。新しいgateや汎用frameworkは不要です。

1. **環境確認**：両nodeの実hostname、USER、PBS_JOBID、`/scr`とhomeのmount、解決済みlock pathを記録。同一nodeの別processでは同じinodeを開くことも確認する。
2. **同一node・別process／別job-scratch**：Aが取得済みと通知してからBを起動。異なる`TMPDIR`でもBの非blocking取得は`BenchBusy`。A解放後は取得成功。blocking取得も解放通知後に進む。
3. **別node**：node Aが保持したままnode Bの同一文字列pathを非blocking取得し、成功を確認。release指示はBの結果取得後に送る。node間の時計差や単なる短い所要で同時取得を推定しない。
4. **旧配置の対照**：同じ順序で共有home lockを使い、別nodeのBが拒否されるか確認する。候補pathとの差を直接示す。
5. **launcher継承**：A-2/A-6の実job bodyから起動した子が候補pathを見ることを確認する。既存compute harnessはmkdir/cpをstubし、失敗経路も扱うため、それだけで本番の排他成立とは数えない。

同一予約内で異なるjob-scratchを与える試験が証明するのは、**別process・別scratch間の排他**です。独立したscheduler jobの名前空間共有までは証明しません。別job間まで主張する場合は実job境界を跨ぐ観測を追加し、schedulerが同一node同居を許さないなら、その予約条件を適用範囲として記録します。

継承確認を実launcherで行っても、性能workload全走や「約8分」の再現は不要です。予約条件や継承が確認できない場合は、nodes=5の整合変更を進め、lock採用だけ保留できます。

**5. 正負例・変異の帰属**

| 対象 | 必要な確認／殺す変異 |
|---|---|
| policy | nodesを1へ戻すとliteral pin／nodes期待値が失敗。nodesだけの変更ではprotocol不変。 |
| host契約 | 兄弟4台は受理。空・不足・過剰・重複・head混入・不正hostは既存理由で拒否。 |
| 既存負例 | pin不一致・staged source失敗・source role不一致が、それぞれ従来の理由まで到達する。host数エラーで代用しない。 |
| submitter | `-b 1`への変異をexact argv試験が検出。nodefile 1台への変異はcompute bodyが拒否。 |
| lock配置 | `$scratch/bench.lock`／`$TMPDIR/bench.lock`への変異は同一node競合試験が検出。 |
| export | export削除・`run-workload`より後への移動は継承試験が検出。probe自身の環境設定で隠さない。 |
| 別node独立 | 共有homeへ戻す変異は、A保持中のB取得成功条件を満たさない。 |
| 排他本体 | `bench_lock`を無効化する変異は同一nodeの`BenchBusy`条件を満たさない。 |

既存`test_campaign.py:2957`は同一process内の取得・解放確認です。今回必要な別process／別nodeの証拠には置き換えられません。

親の実走対象は変更した認証・job contractテスト、既存lock試験、fan-out回帰を中心とし、正規`tools/run_tests.py`経由で行います。過去の凍結artifact・attemptは改変せず、新policy/job bodyのbindingは新attemptで生成します。追加の遠隔総timeoutは保留を維持します。

## 総括

- **成立**：nodes=5の実装方向、policy新SHA、protocol不変、最小変更候補4ファイルと主要fixture閉包。
- **条件付き成立**：固定`$scratch_base/bench.lock`によるA-2/A-6 head間の排他と別node独立。計算ノードでの直接実測・launcher継承確認が必要。
- **未成立**：全launcher／兄弟workerを含む同一node全体の排他、独立job間の名前空間共有、node-local化の実所要改善。
- **実測の限界**：約50分→12分08秒、node秒+16%、検査24件・遠隔16件の受理は既存1 attemptの根拠です。一般的な倍率、将来のqueue待ち、約8分への短縮は保証しません。今回の静的検査だけでテスト合格・lock採用完了とは報告しません。
