## 指摘1 — §6 の12条件を「欠落」と「未充足」で一括している

対象の主張 → brief/plan は「正式条件が未成立」とする一方、足場の不存在まで含むように読める。

論理の欠陥 → `phase3-8c-preregistration.md:303-317,328-337` が示すのは「7条件は評価器へ到達するが、充足を返さない」「5条件は機械検査対象外」という状態であり、全機構が未実装という意味ではない。個別確認は次のとおり。

| 条件 | 実際に読めた状態 | 修正すべき表現 |
|---|---|---|
| C01 | `FORMAL_WORKLOADS` と1m/48のscale検査は存在する (`p3_autonomous_workload_trial.py:218-242,710-793`)。ただしformal profileは拒否される (`:883-896`)。 | 「定義なし」ではなく「足場あり・formal admission未成立」 |
| C02 | arm digestの足場はあるが、C02の充足証明はない (`phase3-8c-preregistration.md:204-212,388-402`)。 | 「binding実装済み」ではなく「binding到達可能・充足未証明」 |
| C03 | genericなmanifest/registry処理はある (`p3_autonomous_workload_trial.py:1123-1199`)。6-cellのP/C束縛は未証明。 | `schedule.v1.json` 不在だけで「registry機構なし」としない |
| C04 | p3のresume/state machineは8bのfreeze-wide attempt registryと不一致 (`phase3-8c-preregistration.md:218-225`)。 | 未整合を明記 |
| C05 | seed・schedule・arm順序の正式固定は確認できない。 | 未登録・未証明 |
| C06 | registered-effective branchには予算consumerが存在する (`p3_autonomous_workload_trial.py:1740-1803`)。formal admissionから到達できない。 | 「consumerなし」ではなく「到達不能」 |
| C07 | 評価器はdispatchされるが、judge条件・パラメータを満たす充足経路はない (`phase3-8c-preregistration.md:231-239,328-337`)。 | 「評価器なし」ではなく「充足なし」 |
| C08 | reportにはP/C両commit欄がある (`p3_autonomous_workload_trial.py:3270-3297`)。実行全体が二段束縛を消費する証明はない。 | 「欄あり」と「意味的束縛成立」を分離 |
| C09 | layer3検査は任意CLIに留まる (`phase3-8c-preregistration.md:246-247,442-460`)。 | acceptance配線未成立 |
| C10 | supervisorはpath/hashを持つが、対象bytesのcross-bindingは未成立 (`phase3-8c-preregistration.md:248-250,456-465`)。 | path/hash保有をproof chain成立としない |
| C11 | generation上限2と複数入口のvalidatorは存在するが、下限G=2は強制しない (`p3_autonomous_workload_trial.py:138-139,464-472`)。 | 「上限あり」と「exact G=2」を分離 |
| C12 | reservation consumer自体は存在するが、8c launch経路から到達しない (`phase3-8c-preregistration.md:257-265,419-423`)。 | 「consumerなし」ではなく「production reach未成立」 |

なぜ問題か → 足場を欠落と数えると、実装済みの機構を再実装する誤った次の一手になり、逆に正式な受理証明がまだ無いことも曖昧になる。

修正案 → blocker tableにC01〜C12を個別掲載し、各行を「足場」「到達可能性」「充足証明」「正式受理」の4段階で記録する。

## 指摘2 — P2の根拠を独立証拠として重複計上している

対象の主張 → brief:38-39、s2-plan:21-25は、§5未記入、§6充足経路ゼロ、§7明記、8b仕様のみ発効、コード拒否をP2の複数根拠として並べる。

論理の欠陥 → §5未記入・§6の非充足・§7の明記は、同じ未発効状態の異なる記述であり、独立した一次事実ではない。8b §10.6の実装待ちは別の下流blockerだが、p3の拒否理由そのものとは別である。

なぜ問題か → 根拠数を増やすことで、同じ状態を複数回数えた過大な確信に見える。

修正案 → 「決定的な直接根拠は `_preflight_workload_profile()` の明示拒否 (`p3_autonomous_workload_trial.py:883-896`)。§5/§6/§7は同じ未発効状態の corroboration。8b §10.6は別系統の受理・測定blocker」と整理する。P2自体は維持できるが、根拠を独立根拠として列挙しない。

## 指摘3 — P3の重複・稼働中判定がworklogからは導けない

対象の主張 → brief:41-43は、T425/T972(×2)/T1371/T1438/T1458が稼働中または未クローズで、H1/H2前提部品と重複するとする。

論理の欠陥 → worklogの該当箇所は各IDのcarry行だけであり、例えば `docs/worklog.md:2858-2865,2944-2947,3093-3096,3301-3304,3346-3349,3394-3397` は未クローズの持ち越しを示すだけで、稼働中・担当・実装対象を示さない。`T-972(×2)`の二重性も射影資料では確認できない。ListAgentsの実測結果も射影されていない。

なぜ問題か → タスク名やcarryだけで重複作業と判断すると、無関係な作業を実験blockerとして扱う。

修正案 → P3は「carry-forwardは確認済み、active statusとcomponent overlapは未確認」とする。重複を主張するには、各タスクの現行scope、所有者、対象ファイル、H1/H2部品との対応を個別に示す。

## 指摘4 — 「次の一手」の実行主体が曖昧

対象の主張 → blocker tableは「calibration登録」「g2 activation」「paired parameter確定」「v2 approval」「human review receipt」を次の一手として並べる。

論理の欠陥 → brief:21-22自身がD356により、人間承認の人間性は機械強制できないと明記している。それにもかかわらず、誰が実行するかが行ごとに明示されていない。

なぜ問題か → Codexが承認bytes生成、activation、裁定代行を行えるように誤読される。

修正案 → 「Codex: receipt・欠落・到達性のread-only確認」「人間: calibration登録、閾値決定、再凍結承認、D145再訪、staged diff review」と主体を分離する。人間操作が未実施なら「未証明」と記録し、代替receiptを生成しない。

## 指摘5 — draft・履歴文書を現行状態へ一般化している

対象の主張 → briefは第8世代/v4やv2 producer不在を現時点の状態として扱う。

論理の欠陥 → prereg文書は「発効前 draft」であり、発効状態はcommitごとに判定器が導出する (`phase3-8c-preregistration.md:1-10`)。さらにcondition recordは8b本文のbytesを束縛しない (`:347-360`)。restart runbook自身も「状態の正本ではない」と明記する (`phase3-8b-restart-runbook.md:6-7`)。

なぜ問題か → 現在のactive epochや後続実装を確認せず、古いv4・v2不在記述を2026-08-21時点の断定にできない。

修正案 → blockerごとに測定HEAD、active condition-freeze世代、DECIDER_VERSION、観測時刻を束縛する。解決できない場合は「epoch未確定」とし、v4を現行と断定しない。runbookは手順、worklog/code/artifactは状態確認用と明記する。

## 指摘6 — 構造的な受理拒否を将来結果の予測に読める

対象の主張 → restart runbook:189-191の「certified選択の結果が1件も出ない」。

論理の欠陥 → 読めた資料が示すのは、現行gateではcertified outputを発行できないという現在の構造であり、rr80/rr20の性能傾向や将来の選択結果ではない。

なぜ問題か → 現行のadmission拒否と、正式実験後に何がcertifiedになるかを混同する。

修正案 → 「現行gateではcertified outputを受理できない」と書き換え、「rr80/rr20の性能・勝者・certified選択は未観測」と明記する。

## 総括

論理的欠陥は6件（第1項は§6全12条件の横断再点検を含む）。  
最重要は、実装足場と正式充足を分離すること、P2の根拠を重複計上しないこと、P3とhuman lockstepを未確認・未承認のまま断定しないこと。  
read-onlyで確認し、コード変更・commit・pytest実走は行っていない。