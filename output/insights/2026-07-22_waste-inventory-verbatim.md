# 戦略的無駄の棚卸し (2026-07-22) — 逐語 (codex)

実行: codex exec, model=gpt-5.6-sol, reasoning=high, sandbox=read-only。親 = claude-fable-5 (background job)。
発端 = ユーザーの指摘「AI は結構無駄をやってきた気がする」。防止規則 5 述語の採否は [T-084] 裁定待ち。

## プロンプト (逐語)

```text
あなたは izanagi プロジェクトの投資対効果を監査する外部レビュアーである。リポジトリは読み取り
専用で自由に調べてよい。出力はすべて日本語。忖度不要。

# 背景
オーナーの懸念: 「戦略に無駄はないか。AI は結構無駄をやってきた気がする」。既に別監査で
「07-19 以降のプロセス自己増殖」は確定済み (output/insights/2026-07-22_direction-audit-*.md を
参照してよい)。今回はそれ**以外**の、より戦略レベルの無駄を棚卸ししたい。プロセス増殖の再確認は
不要。

# タスク

1. **大型投資の棚卸し**: 2026-07-05 (Phase 3 kickoff 完了) 以降の大型投資を列挙し、各々について
   コスト (commit 数・追加行数・記録があれば wall 時間) と、roadmap §1 の最終成果物 (certified な
   選択結果 / proof chain 付き材料レポート / 再現可能な試行台帳) への寄与を評価せよ。最低限
   次を含める: S'/S-1 直接比較実験、sort-strategy 軸、8a trigger-gating 軸、8b selector/oracle/
   floor 実装、freeze 恒久設計、env_contract/pegasus 登録、bounded supervisor、WAL 堅牢化、
   層3 renderer、テスト衛生 wave 群。

2. **分類**: 各投資を次の 4 分類に振り分け、判断根拠を付けよ。
   (i) 必要だった (成果への寄与が明確)
   (ii) 正直な negative result (事前には知り得ず、やってみる価値があった — 無駄ではない)
   (iii) 事前に予見可能だった無駄 (その時点で入手可能な情報から回避できた)
   (iv) 必要だが量が過剰 (スコープ超過 — 最小版なら数分の一で済んだ)
   (iii) と (iv) については、どの時点のどの判断 (D 番号・裁定・worklog エントリ) で回避できたかを
   特定せよ。

3. **無駄の構造分析**: (iii)(iv) に共通するパターンはあるか。例えば「negative result が出た軸に
   追加投資してから撤退する」「防壁の必要が 1 箇所で示されると族全体へ一般化する」「実走前に
   完璧を求める」など。AI (Claude/codex) の作業様式に由来する構造的バイアスがあれば名指しせよ。

4. **再発防止の戦略規則**: 機械化またはチェックリスト化できる具体的な規則を最大 5 個提案せよ。
   盛らないこと (規則の増殖自体が今回の病理である点に自覚的であれ)。各規則に「その規則が過去の
   どの無駄を防いだか」の検証を付けよ。

出力: 構造化 markdown。投資一覧は表。各主張に根拠 (ファイル・行・commit・日付) を付け、
推測と実測を区別せよ。
```

## 出力 (逐語)

# 投資対効果監査

## 結論

2026-07-05以降の戦略全体が無駄だったわけではない。7月16日までに、certified variant、正直な negative result、材料レポート、試行台帳の各要素は実際に作られている。

ただし、プロセス自己増殖を除いても、次の3件は明確に回避可能だった。

1. sort-strategy を安価な機械 sweep より先に本格実装したこと
2. runtime blocked と判明後も Codex role adapter 全族を静的移植したこと
3. 8c の発火条件を満たさないまま bounded supervisor を作ったこと

この3件だけで、本監査帰属では非merge 12 commit、29,954追加行である。

また、8b strict/proof-chain、freeze恒久設計、テスト衛生は必要性自体はあるが、実走前の品質水準として過剰だった。最大の問題は「間違った研究テーマ」ではなく、**証拠を得る前に証拠管理基盤を完成させようとした順序**である。

## 監査方法

評価基準は roadmap §1 の3成果物に限定した。

- C: certified な選択結果
- R: proof chain 付き材料レポート
- L: 再現可能な試行台帳

追加行数は、本監査が件名・変更pathから各投資へ帰属させた非merge commitについて、`git show --numstat` の追加行を累計した実測値である。削除行は相殺せず、生成report・fixture・実測ログも含む。複数投資にまたがるcommitがあるため、表の行を単純合計してはいけない。

wall時間は、task-run/worklogに記録された値だけを採用した。「lead span」は専有作業時間ではなく開始から終了までの観測幅である。

## 大型投資一覧

| 投資・期間 | 実測コスト | C/R/Lへの寄与と現在の実収益 | 分類 |
|---|---:|---|---|
| S2/S4 consumer・auditor・自律loop基盤（07-06〜09） | 23 commit、7,677追加行。wall総計なし | correctness/liveness拒否、diff検疫、checkpoint、worktree隔離を実体化し、後続のcertified試行を可能にした。C=高、L=高、R=間接。段4は実LLM iteration 1〜4をcertifiedで完走している。[phase3.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:210) 主要commit `7df9ac0`、`9324024`、`24cd8a7`、`28e8f93` | **(i) 必要** |
| sort-strategy軸（07-09〜10） | 7 commit、3,944追加行。D41設計レビュー100 tool call・37.8万token。後続sweepは約40〜80分。[D41](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:1222) | iteration 1はcertifiedだが、後手のsweepでbalancedは差なし、write-heavyの見かけの差も成分別にはfloor内。最終選択には寄与せず、negative台帳だけが残った。[sort sweep](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-10_s6-sort-sweep-preliminary.md:31) | **(iii) 予見可能な無駄**。ただしD46の安価なsweep単体は正直なnegative result |
| 8a trigger-gating軸（07-10〜12） | 24 commit、7,195追加行。通算wallなし。campaign完了時刻spanは約4時間 | sweepをLLM loopより先に実施し、3 workloadで+61〜99%をcross-run再現。その後LLM iteration 1〜2もcertified。C=高、L=高、R=層3へ実流入。[8a実測](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-11_s8a-trigger-gating-recon.md:78) | **(i) 必要** |
| S-2/S-3提案ラウンド束（07-13） | 21 commit、30,867追加行。claude呼出約130本、60/60完走。$18〜46はAPI換算見積りで実課金額ではない。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0702-0713.md:2148) | S-2 p=0.115、S-3 p=1.0を凍結し、「発見再現性」「帰属依存」の主張を撤回した。C=間接、R/L=高。結果を隠さずheadlineを縮小した点に価値がある。[確定報告](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/insights/2026-07-13_s6-report-language.md:10) | **(ii) 正直なnegative result** |
| bench-first screening（07-14〜15） | 14 commit、2,713追加行。既存実測はverify 120〜250秒/variant対bench約18秒 | 明白な劣位候補に高価なverifyを払わず、certified到達候補のgateは維持。positive controlも実発火。将来のbounded searchコストを直接削る。[D58](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2250) | **(i) 必要** |
| S′/S-1直接比較（07-15〜16） | 18 commit、17,722追加行。計測wall 22,944秒=6.37時間 | S-1bのみ成立、S-1a/S-2不成立、S-3棄却、S′ headline不成立を確定。これはstock/tieを正直に返すという最終成果そのもの。C/R/Lすべて高。[最終報告](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/reports/s_prime_final_report.md:13) | **(ii) 正直なnegative result** |
| 層3 renderer（07-16） | 4 commit、893追加行。wall記録なし | WAL/whiteboardから決定論的に材料reportを生成し、入力とsource referenceの双射を検査。8a loop 1件とsweep 6件で実report生成済み。Rへの直接投資で、規模も小さい。[phase3.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:360) | **(i) 必要** |
| 8b core：descriptor・selector・oracle（07-16） | 14 commit、9,137追加行。wall総計なし | typed descriptor、holdout、予測凍結、schedule/manifest、judge、oracle driverまで実装。C/R/Lの主経路。ただしselector予測・oracle本走は未完で、収益はまだ「実行可能性」に留まる。[07-16 worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0714-0716.md:739) | **(i) 必要** |
| 8b floor/strict/freeze/launch lineage（07-16〜20） | 43 commit、40,275追加行。wall総計なし | false-green実例を多数閉じたため必要性は本物。しかしlaunch certificate、Git ancestry、42系統の検証鎖まで実走前に完成させ、まだ8b cycleは0。C/R/Lへの限界寄与はあるが、収益未実現。[07-18 worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0717-0718.md:431) | **(iv) 必要だが過剰** |
| env_contract / Pegasus登録（07-16〜19） | 20 commit、79,706追加行。実機run約15分、実装19単位。追加行の大半はcertification資材・試行記録 | 10回目でaccepted。9回のfail-closedからscheduler、依存、NFS、perf、host照合の実前提を確定。再現可能台帳には不可欠で、失敗群も事前には知り切れないintegration result。[07-19 worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0719.md:26) | **(i) 必要**。失敗attempt部分は(ii)相当 |
| Codex role adapter（07-14〜15） | 3 commit、12,501追加行。wall記録なし | active 0、runtime blocked 13。static schemaとcheckerは残ったが、研究pipeline、計測、C/R/Lを一切変えていないことをD56自身が明記。[D56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2225) | **(iii) 予見可能な無駄** |
| テスト衛生wave群（07-17〜21） | 12 commit、3,259追加行。07-19 reviewがstdin未closeで100分停止 | flake、偽緑、重複、実repo競合の修理は必要。ただし小規模cleanupに相談3・実装5・review3、mutation matrix、26-node収集監査まで投入。C/R/Lへの寄与は間接。[07-19 worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0719.md:120) | **(iv) 必要だが過剰** |
| freeze再発行失敗＋恒久設計（07-21〜22） | 10 commit、13,957追加行。観測lead合計約7.24時間。最終設計だけで9,105行 | 問題は実在するが、まだコード実装なし。7 wave、93 path、42 test node、49 mutation候補へ拡大し、floor前工程を10段にした。現在のC/R/Lには未寄与。[task-run集計](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/task-runs/reports/20260720-20260722_task-efficiency.md:37) [D76](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3027) | **(iv) 必要だが過剰** |
| bounded supervisor（07-21） | 2 commit、13,509追加行。lead 34,532秒=9.59時間、203 test node | real `claude -p`を起動できないfake層。C/R/Lへの寄与ゼロ。8b cycle前なので、roadmap上の8c発火条件も未成立。[task-run](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/task-runs/reports/20260720-20260722_task-efficiency.md:40) | **(iii) 予見可能な無駄** |
| WAL堅牢化 D68/D77（07-20、22） | 4 commit、5,763追加行。D68 lead約2.12時間。D77は9 Codex走、wallなし | duplicate-key、terminal位置、torn tail、short write、resume物理修復を実事故で確認。proof chainの入力が黙って消える経路を閉じた。Lへの直接投資であり、C/Rの信頼性にも必要。[D68](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2578) [D77](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3068) | **(i) 必要** |

## (iii)(iv) の回避可能時点

### sort-strategy

D22は07-05時点で、lock順序をverifierが観測できない、no-waitなのでdeadlock仮説が誤り、workloadが競合を踏まない、という3点を既に記録していた。[D22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:385)

D41で再採用するなら、「条件7点の実装」より先にD46相当の40〜80分sweepを条件0にすべきだった。実際、07-10の裁定は「偵察が後手に回りiteration 1が先行した」と認めている。[worklog 07-10 (10)](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0702-0713.md:1454)

回避可能だった範囲は軸の観測そのものではなく、`ba37bf6`〜`c6e7fba`の本格機構とLLM iterationの先行である。

### Codex role adapter

D54の初版段階で、profileにはper-role tool allowlistがなく、read-onlyでも親のMCP/apps等を継承し得ることを把握していた。[D54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2051)

さらに同日D55でactive=0、runtime E2E=BLOCKEDが確定した。[D55](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2110) この時点で最小の「移植可否表＋再開条件」に止めるべきだった。D56の13 role全静的adapter、renderer、semantic validator、outer sandboxは、既知のblocked surfaceに対する先払いである。

### 8b strict化

07-16監査で、correctness red上書きやholdout全落ちでもdeterminateになるfalse-greenが見つかっており、strict化そのものは必要だった。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0714-0716.md:809)

しかし07-18 (10)では、launch lineage検証がmulti-waveになることまで判明していた。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0717-0718.md:554) ここで初回cycle用の一回限りmanifest・hash照合に縮め、Git introduction topologyや完全fixtureは1 cycle後へ送るべきだった。

07-19には正本が「protocol凍結→予測→floorの前提は全充足」と明記している。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0719.md:61) したがって、少なくともこの時点以後の追加hardeningをfloorより優先した判断は過剰である。

### テスト衛生

07-19 (5)で見つかった問題は、重複1件、弱い契約数件、独立flake1件だった。それに対して相談・並列実装・敵対レビュー・mutation matrixのフルwaveを適用し、レビュー自体が100分停止した。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/archive/worklog-phase3-0719.md:120)

D63時点では既知の実repo接触nodeだけを直列marker化する最小版で十分だった。26-node closure、独立golden、collection hook完全検査は、再発後の第2段でよかった。[D63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2380)

### freeze恒久設計

最も明白である。D71は既に最小解を示していた。

> 一回限りのreceiptを作り、新hashとreceipt hashをliteral pinへ再登録する。

[D71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2747)

ここで一回限りの移行を実施すればよかった。代わりにD75/D76で、単一の自己hash問題を9 blob・7 anchorの族へ一般化し、generation、approval、revocation、pointer、173 reason registry、49 mutation候補まで設計した。[D75](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2989) [D76](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:3034)

回避点はD71。遅くとも07-22 worklog (2)で「実装なし・設計だけ」と確認した時点で、第2設計段へ進まず止めるべきだった。[worklog](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:741)

### bounded supervisor

roadmap戦術は明確に、8cを「8b前向き設計と層3最小E2Eを1 cycle回し、なお反復運営が律速なら」としている。[phase3.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:352)

D74はこの発火条件を満たさないまま、fake-only機械層を実装した。[D74](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2937) 回避時点は07-21 worklog (4)の設計提案時。設計を保留台帳へ1ページ残し、8b cycle後まで実装しないのが正しかった。

## 無駄の構造

### 1. 「安価な生死判定」が後手になる

sortでは、軸に地形があるかを測る前に、正しさ防壁、兄弟driver、auditor gate、LLM iterationを作った。その後の40〜80分sweepで撤退した。

8aでは順序を逆転し、先に機械sweepを行って成功した。この比較から、問題は結果論ではなく投資順序だったと判断できる。

### 2. 単発事故を族全体の制度へ一般化する

F27の自己hash破損は実在した。しかし「一回限りの移行」で閉じず、freeze全族の世代管理・承認・失効・取消し・consumer移行へ拡張した。

これはAIに典型的な**防壁一般化バイアス**である。局所反例を見つけると、類似名を持つ全対象へ同じ不変条件を適用したくなる。

### 3. 実走前のゼロリスク志向

8bは07-16にselector/oracle骨格があり、07-19には環境前提も満ちた。それでも実走より、launch lineage、freeze topology、WAL、reader、exact reason、mutationの完全化を優先した。

これは**pre-run perfection bias**である。実走で初めて得られる情報より、静的に閉じられる穴の方がAIには扱いやすい。

### 4. 敵対レビューのラチェット

freeze、supervisor、8bはいずれも、レビューがNO-GOを返すたびにscopeが増え、次のレビュー面を新設している。レビューの所見が「受理集合や科学的結論を変えるか」ではなく「論理的にrealか」で採用されるため、正しいが低価値な修正が無制限に累積した。

これは**finding最大化バイアス**である。AI reviewerは「問題を見つける」ことで成功し、親AIは「全所見を閉じる」ことで成功する。誰も限界費用を最適化していない。

### 5. 可視成果代理への偏り

commit、追加行、test node、schema、manifest、逐語台帳は進捗として数えやすい。一方、「floorを投入して12時間待つ」「negative resultを受け入れて止める」は成果が薄く見える。

この**artifact-count bias**が、科学的1 cycleより203 test nodeや93 path ownershipを魅力的にした。

## 再発防止規則

新しい制度を作らず、既存のphase/worklogチェックに次の5述語だけを足すべきである。

### 規則1: 新しい軸は最安の生死実験を先に行う

LLM driver、専用role、汎用防壁を作る前に、既存driverまたは100行以内の使い捨てdriverで、floor超が2 run再現することを要求する。

- 防げた無駄: sort-strategyのD41〜D43先行分
- 過去検証: D46は40〜80分で地形不足を示した。一方8aはこの順序で成功した

### 規則2: 「初回1 cycle前」は受理集合を変える欠陥だけをblockerにする

次のhardeningが許されるのは、欠陥が correctness判定、selected/tie、数値、proof参照、試行欠落のいずれかを実際に変える場合だけ。それ以外は1 cycle後へ送る。

- 防げた無駄: 8b launch lineageの多段化、test hygieneの完全collection監査
- 過去検証: 07-16のcorrectness-red上書きは許可されるが、Git introduction topologyの完全化は延期対象になる

### 規則3: 単発事故の族一般化には独立2例を要求する

同じ欠陥が異なるproducerまたはconsumerで2件再現されない限り、局所修復または一回限りのmigrationを既定とする。

- 防げた無駄: freezeの7 wave・93 path化
- 過去検証: D71の一回限りreceiptで元事故は閉じられた。D75/D76の世代・失効・取消しは第2例なしに一般化された

### 規則4: phaseの発火条件をcommit gateにする

条件付き機能のcommitには、発火条件を満たす既存artifact pathまたは計測IDを必須にする。無ければ文書設計だけで停止する。

- 防げた無駄: bounded supervisor 13,509行
- 過去検証: 8cに必要な「8b＋層3の1 cycle」と律速測定は存在しなかったため、D74は機械的に拒否される

### 規則5: reviewer所見は成果物への影響を1行で示せない限り次段へ送る

各must-fixは「これを放置するとC/R/Lのどの値・受理集合・参照がどう変わるか」を要求する。説明できなければnitまたはbacklogとし、追加review waveを起動しない。

- 防げた無駄: freeze exact schemaの反復、supervisorの複数NO-GO/fix巡、test hygieneの過剰儀式
- 過去検証: WAL torn-tailや8b correctness-red上書きは説明可能なので残る。一方、fake-only supervisorのtrust-root完全化は現時点のC/R/Lを変えないので延期される

## 最終評価

投資判断を三群に分けるべきである。

- 維持すべき中核: 8a、S-1、S-2/S-3 negative result、層3、8b core、Pegasus、WAL
- 授業料として認めるもの: sortの安価なsweep、Pegasusの9失敗、S′不成立
- 明確に止めるべきだったもの: sort本格実装の先行、blocked Codex adapter全族、8c前倒し
- 縮小すべきもの: 8b strict、freeze恒久設計、テスト衛生

要するに、IzanagiのAIは「役に立たない実験」を大量にしたのではない。より深刻なのは、**役に立つ実験を始める直前に、将来の失敗をすべて先回りで封じようとして止まる**ことである。今後のROI改善で最も効くのは精度を下げることではなく、局所防壁を保ったまま実走順序を前へ戻すことである。