**4ファイルの局所案は妥当です。nodes=5は再裁定不要。lock候補は実測へ進めてよいものの、採用判断には「候補同士」だけでなく「既存default consumerとの混在」の最小反例が必要です。** 書込み・pytest・実測は行っていません。

以下、`plan.md`と`brief.md`は指定された親ディレクトリ内の資料です。

1. **must — 全bencher懸念を、既存制限と今回の退行に分ける。**
   `plan.md:9,65–68`、`orchestrator/campaign/lock.py:29–34`、`orchestrator/campaign/verify_fanout_worker.py:534–535`。

   | 組合せ | 今回の変更の意味 |
   |---|---|
   | 更新後A-2/A-6 head同士 | 共通job bodyの固定pathに揃う。同一node排他・別node独立を直接検証できる |
   | 更新後headとdefault consumer | 従来共有していたhome lockから分離する。**同居時の協調排他喪失は具体的退行** |
   | headとfan-out worker | workerのtask固有lockは既存挙動。今回新しく生じる欠陥とは扱わない |
   | headと既存b10-grid/a5のTMPDIR lock | 既にlockが分離している。今回失う保護の例にはならない |

   default consumerの具体例は`tools/pegasus/b10_backoff_shape_campaign.sh:362`から呼ばれる`orchestrator/campaign/b10_backoff_shape_sweep.py:2679`です。環境でoverrideしなければ既定home lockを使用します。競合process検知は残りますが、`pipeline.py:1386`以降の取得後検査だけでは、別lockを取得した双方の同時開始を直列化できません。

   **最安の反例**：同一計算node・同一userで、Aが候補pathを保持した通知後、Bは`IZANAGI_BENCH_LOCK`をunsetして実`bench_lock(blocking=False)`を呼ぶ。候補では双方取得でき、旧default同士ではBが`BenchBusy`になる対照を取る。性能binaryの実行は不要です。これは機構上の退行を示し、scheduler上の実同居可能性は別途区別します。
   **成果物影響**：probe結果と採用範囲の記録。別launcher改修や新gateは不要。

2. **must — 変異が狙った理由で失敗するよう、launcher継承試験の到達点を明示する。**
   `plan.md:26,82–85`、`orchestrator/tests/test_paper_story_a2_job_contract.py:815–849,988–1014`。

   現harnessにはmkdir/cpのstubと早期拒否経路があり、単に非zero終了しただけではlock変異を殺した証拠になりません。`run-workload`の子まで到達したことと、その子が観測したpathを確認する必要があります。

   - 継承試験は親のlock環境をunsetした場合と、異なる値を設定した場合を分ける。
   - `$scratch`／`$TMPDIR`変異では、異なるscratchとTMPDIRを与え、両pathの親directoryを用意する。`ENOENT`を排他失敗の検出に数えない。
   - export削除・後置変異は、子の環境観測で落とす。probe側で候補pathを再設定しない。
   - nodefile負例の`tracked_dirty=True`は既存の順序検査には有効。ただし「node数だけの変異」の証拠には、source正常のfixtureを使う。

   **成果物影響**：既存job-contractファイル内の試験と変異結果の帰属。新しい試験frameworkは不要。

3. **should — 「全launcherの保証が未成立」を、局所試行を止める条件にしない。**
   `brief.md:3–4,10`、`plan.md:9,70–72,95`。

   予約条件の確認は採用判断には必要ですが、候補を試す前提にするのは過剰です。候補同士の排他・別node独立・default混在を短いprobeで測り、局所変更では規律を維持できないなら**lock候補を不採用と記録してnodes=5だけをland**できます。

   `brief.md:10`の「共有home全clusterロックには戻さない」は、候補不採用時に現状維持まで禁止する意味にはしないこと。共有homeとの二重lock追加では別node直列化が復活し、研究目的を失います。
   **成果物影響**：briefの完了条件とinsightの採否記録。全campaign再測定・他launcher一般改修は増やさない。

4. **should — 4ファイル閉包は成立方向。既存負例の理由を維持する。**
   `plan.md:17–39`、`orchestrator/campaign/paper_story_a2_certification.py:3664`。

   policy、認証テスト、job-contractテスト、共通job bodyの4ファイルで、確認した直接依存は収まります。列挙された6か所の`run_workload()`呼出しへの兄弟host補充は必要です。追加で確認した同テスト`:5394`は既に`verify_fanout_hosts`を渡しており、補充対象ではありません。

   pin負例はmessage、staged-source負例はcauseとevents、source-role負例はpredicate呼出しまで検査しています。これらを維持すれば、host数エラーへのすり替わりは検出できます。共通`_policy()`をnodes=1に戻す回避は不可です。

   必須検証は、変更した2テストファイル、既存lock試験、関係するfan-out回帰と、短い計算node probeで十分です。単一node fixtureは専用テスト内に限定し、新policy SHAを実ファイルから取得するだけの自己比較へliteral pinを弱めないこと。
   **成果物影響**：4ファイル内で閉じる。A-6 policy、submitter、汎用lock、worker本体の編集根拠はありません。

5. **nit — 過去の時短値は、単一attemptという限定だけでなく比較条件の差も添える。**
   `plan.md:96`、`output/insights/2026-09-18/t2489-a2-nodes5-probe/README.md:203–207,219–244`。

   元資料では比較attempt間でprotocol・job body・adopted source bytesも異なります。「約50分→12分08秒」をnodes変更だけの統制された因果効果と読ませないこと。今回のlock probeが示すのも同時取得・排他の成立であり、「約8分」や一般的な速度向上ではありません。planの非一般化方針自体は適切です。
   **成果物影響**：新insightの主張上限だけ。規律2、既存認証条件、付随性能値を採用値へ昇格させない境界は維持します。

静的hash再計算用コマンドは自動実行ガードに拒否されました。理由は、読み取り対象のjob bodyをPegasus上のdispatch必須実行体として検出したためです。新SHAの独立再計算は未完了で、plan記載値の検証済みとは報告しません。

## 総括

**nodes=5の4ファイル閉包を進め、lockは短い局所実測で採否を決める方針を支持します。** 必須の補強はdefault consumerとの混在反例と変異の理由帰属です。局所変更で排他を維持できなければ、不採用の実測記録も研究前進として成立します。
