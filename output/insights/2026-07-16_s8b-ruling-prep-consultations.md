# 8b 裁定準備セッションの敵対相談記録 (2026-07-16)

- 実行: codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only, cwd=worktree (基準 50b499b)
- 構成: C-A (§9 項 7/8 提示骨子) / C-B (floor env 案) / C-C (freeze v2 設計骨子) / C-D (プラン全体)。
  プロンプト全文と生出力はセッション job tmp から本ファイルへ相談完了ごとに凍結 (F20 恒久対応)
- 所見はデータであり、採否は親 (Claude) が現物裏取りのうえ裁定する

---

## C-D: プラン全体への敵対所見 (逐語)

# 総評

**このプランは現状のままでは reject。** 最大の欠陥は、裁定を得るための U1/U2/U3 と、裁定結果に依存する U4 を固定成果物として同列に置いたこと。さらに R5 が実質脱落し、文書正本・F20・完了検査の運用も破っている。

1. **U4 の着手順が正本と逆**

   `[critical] [real]`

   根拠: 再開手順は明確に「項 7〜8 裁定 → env 確定 → A3-3/A3-4 を含む設計」の順である。[docs/worklog.md:986](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/worklog.md:986)。特に項 8 の採否は resume 意味論と crash 後の block 運用を変えるため、R6・A3-3 の設計入力そのもの。[docs/worklog.md:974](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/worklog.md:974)

   「承認まで効力なし」は順序違反を解消せず、単に推測 draft を残すだけ。`親裁定` もユーザー裁定の代替ではない。

   修正案: U4 は固定成果物から外す。U1/U2 の提示後にユーザー裁定で停止し、次に U3 の env 選択で停止する。両方得られた場合だけ U4 を開始する。未回答なら U1〜U3 でセッションを閉じる。

2. **R5 が計画から脱落している**

   `[critical] [real]`

   根拠: 実実行前条件には「§6 量化 4 点の再凍結 + prediction/oracle 結合 judge 実装」が明記されている。[docs/worklog.md:935](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/worklog.md:935)、[docs/worklog.md:957](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/worklog.md:957)。しかし予定実装は verifier・R3・R6 だけ。項 7 の中央値集約は R5 の代用ではない。

   前提条件 (i)〜(v) の対応は、R6 と env は明示、A3-3/A3-4 は暗示、R1/A3-6 は曖昧、**R5 は欠落**である。

   修正案: U4 に混ぜず、R5 専用裁定として次を追加する。

   - swapped 成立を「両 holdout」か「いずれか」で判定するか
   - floor 差の符号・絶対値規則
   - prediction と oracle の同一 holdout 束縛
   - rationale の証拠基準
   - 結合 judge の実装・テスト

3. **U4 は異なる裁定層を一束にしすぎている**

   `[high] [likely]`

   根拠: A3-3 は共有予算台帳か 1-oracle/1-block かのトポロジー裁定、A3-4 は status/rc 意味論、A3-6 は verifier が検証済み object を単一利用するデータフロー要件であり、同じ種類の設計ではない。[third-wave-audit.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/insights/2026-07-16_s8b-third-wave-audit.md:38)、[third-wave-audit.md:49](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/insights/2026-07-16_s8b-third-wave-audit.md:49)、[third-wave-audit.md:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/insights/2026-07-16_s8b-third-wave-audit.md:70)

   R6 は採用したトポロジーと crash 境界に従属する。R3 はさらに別の exactly-once 実行面である。一つの「U4 承認」では部分採用・差し戻しの依存が追跡できない。

   修正案: 同じファイルに置くとしても、裁定単位を次の順に分離する。

   1. T: topology・共有 ledger・crash 方針
   2. C: A3-4 status/rc 契約
   3. S: freeze v2 schema・R1・R5・A3-6
   4. R3: prediction runner
   5. R6: resume/lock/marker

4. **「文書 4 点」では正本更新が足りない**

   `[high] [real]`

   根拠: 項 7〜8 の裁定結果は §9 の承認状態へ反映しなければ発効しない。[descriptor-design.md:269](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:269)。schema・budget・floor・選択規則の変更には、旧 freeze と変更理由を残した再凍結およびユーザー承認が必要。[descriptor-design.md:255](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:255)

   また `phase3.md` の checkpoint は現在、topology・R3・R6 を含む 5 段手順を表していない。[docs/phase3.md:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3.md:43)

   修正案:

   - U1/U2 は新規正本ファイルではなくユーザー向け裁定資料にする
   - 裁定後に既存 §9 の承認状態を更新する
   - v1→v2 の差分・理由・未発効状態を §8 契約に沿って残す
   - `phase3.md` checkpoint を 5 段手順と新設 doc へのポインタへ同期する
   - 最終状態は worklog へ吸収する

5. **新規 U4 は `check_docs` の監査網外に落ちる**

   `[high] [real]`

   根拠: living doc は明示列挙で、8b について登録済みなのは既存 `phase3-8b-descriptor-design.md` だけ。[tools/check_docs.py:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/tools/check_docs.py:21)、[tools/check_docs.py:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/tools/check_docs.py:35)。新規 `phase3-8b-freeze-v2-design.md` は lint 対象にならないため、`check_docs` が緑でも意味的には false-green になる。

   修正案: 既存の living design doc に §10/付録として置くか、新規 doc を `LIVING_DOCS` に追加して検査回帰も追加する。後者なら「成果物は文書のみ」という scope は撤回が必要。

6. **F20 対応の保存タイミングが再発条件そのもの**

   `[high] [real]`

   根拠: プランは相談・監査全文を「セッション末」に凍結するが、F20 は生成したセッション内で repo 配下へ保存し、handoff にパスを刻む規則である。[docs/handoff/README.md:18](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/handoff/README.md:18)。handoff は節目ごと・最低 10 分おきに更新する。[docs/handoff/README.md:10](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/handoff/README.md:10)

   修正案: 各相談・監査が返った直後に repo 配下へ保存し、handoff にパス・採否・未処理所見を書く。セッション末は「初回保存」ではなく、統合版の確定だけにする。

7. **開始・終了手順と検査順が規律違反**

   `[high] [real]`

   根拠: この作業は phase を変更するクラス 3 なので、開始時の残 handoff・`git status`、作業中 handoff が必要だが計画にない。[CLAUDE.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/CLAUDE.md:38)

   終了順も逆である。プランは provenance 監査を commit 前、`check_docs` を最終 worklog 更新前に置いている。provenance 監査は commit 後に行う規則で、`check_codex_agents.py` も欠落している。[AGENTS.md:26](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/AGENTS.md:26)、[CLAUDE.md:117](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/CLAUDE.md:117)

   修正案: `最終文書・phase・worklog・handoff 吸収 → 関連 pytest → check_codex_agents → check_docs → provenance trailer 付き commit → check_ai_provenance` の順にする。

8. **U3 が工数比較だけなら env 裁定として不足**

   `[medium] [likely]`

   根拠: Cygnus は現行正式 env なので先行案自体は合理的だが、Pegasus を正式計測に使うには専用 env-tag、calibration/noise floor、ノード上の単独性確認、toolchain・pin・job script 追跡が必要。[docs/decisions.md:2282](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/decisions.md:2282)。異なる env-tag の throughput は混ぜられない。[docs/decisions.md:2290](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/decisions.md:2290)

   修正案: U3 は単なる時間見積もりでなく、「v2 の数値を束縛する唯一の env-tag」「他方で再現する場合は別 freeze/campaign とするか」「full pipeline 工数」「Pegasus 4 条件の追加費用」を裁定項目にする。

9. **文書レビューと既存 pytest だけでは実装可能性を検証できない**

   `[high] [real]`

   根拠: A3-3 は現行テストが単一 block しか扱わず、v2 verifier 開通後に初めて発火する欠陥。[third-wave-audit.md:40](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/insights/2026-07-16_s8b-third-wave-audit.md:40)。A3-6 も現状 gate が閉じているため実害経路へ到達していない。[third-wave-audit.md:72](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/insights/2026-07-16_s8b-third-wave-audit.md:72)。未変更コードの `pytest s8b` が通っても新設計の検証にはならない。

   修正案: 承認資料に最低でも状態遷移表と実行可能な受入ベクトルを付ける。対象は「2 block 共有予算」「各境界で crash」「全行 binding-refused」「output-root 変更」「truncated WAL」「verify/use 間差替え」「R3 の再試行禁止」。production 実装は裁定後でよいが、これを通していない draft を「実装可能」と評価してはならない。

10. **攻撃失敗した観点**

   `[none] [real]`

   - 裁定前に production 実装へ進まない判断は正しい。5 段手順も設計・承認を verifier 実装より前に置く。
   - floor の実測・数値充填を後段へ回すことも正しい。[descriptor-design.md:315](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:315)
   - 新規 design doc 自体は禁止されていない。§9/phase3 への正本ポインタ、§8 の変更手続き、lint 編入を満たせば従属文書として成立する。
   - `output/insights` への凍結先と、push をユーザー判断に残す境界は正しい。問題は保存時期である。

### C-D への親裁定 (現物裏取り済み)

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| 1 | U4 着手順が正本と逆 | real (修正採用) | U4 を正本設計 doc から**設計素材 (insights、非正本)** へ格下げ。裁定依存点 (項 7/8 採否・env) を明示した条件付き骨子とし、裁定はセッション末に一括提示。停止点はユーザー裁定のまま |
| 2 | R5 脱落 | 提示上は real | plan.md 原文には R5 含有 (C-D への要約が省いた)。ただし構造指摘を採用し R5 を独立裁定単位に昇格 |
| 3 | 裁定層の一束化 | real | T (トポロジー/台帳/crash) / C (status・rc 契約) / S (freeze v2 schema・R1・A3-6) / R3 / R6 / R5 の層別裁定単位へ分離 |
| 4 | 正本更新の不足 | real | U1/U2 は裁定資料 (insights + 最終提示)。§9 承認状態の更新は裁定後の次作業。phase3 checkpoint へは成果物ポインタのみ同期 |
| 5 | check_docs 網外 | real (tools/check_docs.py:25 で確認) | 新規 living doc は作らない。設計素材は insights (凍結族、lint 対象外が仕様) へ |
| 6 | F20 保存タイミング | real | 本ファイルを相談完了ごとに追記凍結する運用へ変更済み (このファイル自体が対応) |
| 7 | 開始・終了手順 | 終了順 = real / 開始欠落 = refuted | 開始手順 (worklog 末尾・handoff 列挙・git status) は実施済み (plan.md に記載略)。終了順を「docs → pytest → check_codex_agents → check_docs → commit → check_ai_provenance」へ修正 (AGENTS.md:26 で確認) |
| 8 | U3 の裁定項目不足 | real | 「v2 数値を束縛する唯一の env-tag」「他 env は別 freeze/campaign か」「full pipeline 工数」「Pegasus 4 条件費用」を裁定項目化 |
| 9 | 受入ベクトル欠落 | real | 設計素材に状態遷移表 + 受入ベクトル案 (2 block 共有予算 / 各境界 crash / 全行 binding-refused / output-root 変更 / truncated WAL / verify-use 差替え / R3 再試行禁止) を含める |

---

## C-B: floor 実測 env 案への敵対所見 (逐語)

# 敵対レビュー

結論: この骨子のままの「択 A 先行」は却下。A が最短になる可能性は残るが、現状の比較は共通設計費を A から隠し、対象外の既存 floor を再利用可能資産として数えている。推薦を支える見積りではない。

1. [重大] [real] **A/B の工数比較は、環境非依存の必須作業を A から落としている**

   `v2 数値充填`には、floor protocol と exact schema の事前承認、strict v2 verifier、複数 block と共有 budget 台帳の裁定が必要である。現行 driver は floor/budget が non-null になった freeze を明示的に拒否する。したがって A の工数は「計測時間 + Cygnus の空き」ではない。raw 値を取るだけなら可能でも、それは v2 充填ではない。

   根拠: [docs/phase3-8b-descriptor-design.md:315](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:315)、[orchestrator/campaign/s8b_oracle_driver.py:121](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:121)、[docs/worklog.md:986](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/worklog.md:986)、[output/insights/2026-07-16_s8b-third-wave-audit.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/insights/2026-07-16_s8b-third-wave-audit.md:38)

   修正案: 見積りを「共通必須作業」「Cygnus 差分」「Pegasus 差分」に分ける。共通欄には protocol/schema 承認、v2 verifier、block/budget topology、status/rc、resume 契約を入れる。

2. [重大] [real] **既存 floor driver は 8b の対象を一つも測っていない**

   8b holdout は rr80 と rr20。一方 `between_run_floor.py` は rr5/rr50/rr95 の三点、しかも単一 stock baseline しか測らない。§5.2 が要求する「holdout ごと・比較対ごと」の floor には転用できない。「既存 noise floor 資産が有効」は、動作点の参考になるという意味までであり、v2 数値として有効ではない。

   根拠: [output/s8b-freeze/holdout_freeze.json:40](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/s8b-freeze/holdout_freeze.json:40)、[output/s8b-freeze/holdout_freeze.json:307](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/s8b-freeze/holdout_freeze.json:307)、[docs/phase3-8b-descriptor-design.md:206](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:206)、[orchestrator/campaign/between_run_floor.py:49](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/between_run_floor.py:49)、[orchestrator/campaign/between_run_floor.py:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/between_run_floor.py:57)

   修正案: holdout freeze と封印済み比較対から target manifest を生成する専用 driver を作る。`POINTS` の手編集や既存三点の値コピーは禁止する。

3. [高] [real] **「floor 再実測」の実行量と独立性を過小評価している**

   現行 driver を一対象に使うだけでも、within 10 rep + between 8 session × 5 rep = 50 bench 実行である。EXTIME=3 秒ならベンチ本体だけで最低約150秒。しかも binary は一度しか build せず、session は back-to-back なので、実装自身が「fresh 下限」と認め、最終値は時間分離 cross-campaign データとの保守側統合を人間へ残している。これは「calibrator を一度回す」作業ではない。

   根拠: [orchestrator/campaign/between_run_floor.py:53](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/between_run_floor.py:53)、[orchestrator/campaign/between_run_floor.py:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/between_run_floor.py:157)、[orchestrator/campaign/between_run_floor.py:179](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/between_run_floor.py:179)、[docs/roadmap.md:205](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/roadmap.md:205)、[docs/phase3-8b-descriptor-design.md:207](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:207)

   修正案: 結果を見る前に、対象集合、n、reps、時間分離 block、別 process/build の扱い、算出式、cross-block 統合規則を承認・凍結する。それ以前の工数値は架空である。

4. [高] [real] **budget は floor 計測から自動的に得られる数値ではない**

   budget は事前に決める拘束上限であり、第一軸は累積 bench 秒、別途 wall time を記録する。実運用時間は build・複数 verify・再測・timeout を含む full pipeline で決まる。現行 floor driver は baseline を一度 build して `measure_point` を直接呼ぶだけで、verify、variant materialize、retry、LLM、queue を測らない。択 A/B とも budget 算出手順が欠落している。

   根拠: [docs/phase3-8b-descriptor-design.md:209](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:209)、[docs/roadmap.md:281](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/roadmap.md:281)、[orchestrator/campaign/between_run_floor.py:157](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/between_run_floor.py:157)、[orchestrator/campaign/s8b_budget.py:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_budget.py:14)

   修正案: `n × reps × extime × max_rounds` から bench 上限を事前導出し、既知 workload の full-pipeline pilot で人間向け wall-time 見積りだけを校正する。arm、holdout、total、LLM 回数、queue 待ちを別勘定にする。

5. [高] [real] **択 B は topology/binding と既存 hardcode の除去を落としている**

   Pegasus は 48 physical core・1 socket、Cygnus は 96 thread・2 NUMA。runbook は thread/process binding と node 数の固定を正式採用条件に含め、roadmap も環境ごとの再設計を要求する。しかし floor driver は `p2_2` の `ENV_TAG/NUMA/THREADS/RECORDS/CLK` を直輸入し、8b oracle も `numactl --interleave=all` を hardcode している。env-tag の命名だけでは Pegasus 対応にならない。

   根拠: [docs/pegasus-runbook.md:31](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/pegasus-runbook.md:31)、[docs/pegasus-runbook.md:248](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/pegasus-runbook.md:248)、[docs/roadmap.md:281](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/roadmap.md:281)、[orchestrator/campaign/between_run_floor.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/between_run_floor.py:44)、[orchestrator/campaign/s8b_oracle_driver.py:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:36)

   修正案: env contract に node class、threads、records、clocks、CPU/process binding、NUMA、perf events、module/compiler pin、job script hash を持たせ、floor/oracle driver の両方を同じ契約から駆動する。

6. [重大] [real] **F3 を「リスク」と書くだけで、現行 admission の穴を放置している**

   `between_run_floor` は session 間に pgrep しか呼ばず、load 静定を使わない。共通 `settle()` は timeout 後も `settled=False` で先へ進み、pipeline もその測定値を記録する。さらに pgrep は `build-variants/...` だけを検索するが、8b は `s8b-build-cache` を使うため孤児 8b bench を検出できない。Pegasus の `Exclusive submit=OFF` 以前に、現行コードが F3 の再発防壁を満たしていない。

   根拠: [docs/failures.md:36](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/failures.md:36)、[orchestrator/campaign/between_run_floor.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/between_run_floor.py:85)、[orchestrator/calibrator/runner.py:48](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/calibrator/runner.py:48)、[orchestrator/calibrator/runner.py:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/calibrator/runner.py:71)、[orchestrator/campaign/s8b_oracle_driver.py:466](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:466)

   修正案: binary path 非依存の競合検知、scheduler 上の同居確認、load/frequency/temperature 記録、`settled=False` の採用拒否、block 単位の破棄・再投入規則を実装する。

7. [中] [real] **Cygnus 資産の「鮮度・有効性」は証明されていない**

   既存 calibration は host/kernel/topology を持つが、artifact 内に計測日時・CCBench pin・compiler/toolchain がない。既存 floor JSON も env-tag・pin・日時を持たず、driver 自身が旧二点と現行点で pin が異なると説明している。これを「有効」と断言するには、現在の Cygnus が同一契約であることの照合が要る。

   根拠: [output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/env/linux-baremetal/calibration/calibration_t48_skew0p9_rr50_rmw0.json:1)、[output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/env/linux-baremetal/calibration/between_run_noise_t48_skew0p9_rr5_rmw0.json:1)、[orchestrator/campaign/between_run_floor.py:21](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/between_run_floor.py:21)、[docs/phase3-8b-descriptor-design.md:208](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:208)

   修正案: saturation calibration の無条件再走ではなく、hardware/kernel/microcode、clock policy、perf、toolchain、pin、binding の reuse qualification を先に作る。通れば動作点は再利用してよいが、rr20/rr80 の対象別 floor は別途必要。

8. [高] [real] **二者択一にしたため、実際の第三案を消している**

   ユーザー回答は明示的に Pegasus/Cygnus 併用である。一方 D59 は env-tag 間の throughput 混合を禁じる。したがって自然な構成は「共通 protocol/schema 実装」「第一 env の正式結果」「第二 env の独立 replication」の三レーンである。また selector prediction を性能値の前に封印できれば、floor を実際の on/off 比較対へ絞る案も検討できる。floor は argmax tie-break に使わないためである。

   根拠: [docs/worklog.md:981](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/worklog.md:981)、[docs/decisions.md:2290](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/decisions.md:2290)、[docs/phase3-8b-descriptor-design.md:301](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:301)、[docs/phase3-8b-descriptor-design.md:308](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:308)

   修正案: 数値充填を急がず、まず env-neutral schema/protocol と synthetic fixture 実装を進める案を正式な択 C にする。pair 縮小案は結果閲覧前の再凍結・承認を条件とする。

9. [高] [real] **「今は Pegasus」を実行 handoff に落としていない**

   Cygnus 先行を推すなら、「アクセス可能か」だけでは足りない。誰が、どの committed HEAD/pin を、いつ、どの command で、どの preflight 後に走らせ、成果物をどう現在の Pegasus worktree へ戻すかがない。D59 はマシン固有手順を専用 runbook へ閉じると決めているが、文書地図にあるマシン runbook は Pegasus だけである。

   根拠: [docs/worklog.md:981](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/worklog.md:981)、[docs/decisions.md:2286](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/decisions.md:2286)、[docs/README.md:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/README.md:28)、[docs/pegasus-runbook.md:234](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/pegasus-runbook.md:234)

   修正案: 推薦には実行責任者、開始可能時刻、正確な revision、preflight、停止条件、artifact sync、失敗時の再投入手順まで添える。これが埋まるまで「A が最短」は未証明。

10. [情報] [real] **攻撃不成立だった観点**

   択 B は D59 の四条件そのものは大枠で読み違えていない。欠陥は条件の脱落ではなく、binding・consumer・schema・運用判定まで分解していない点である。また「現在 Pegasus にいるから Cygnus 計測は矛盾」という攻撃も成立しない。D59 は `linux-baremetal` を正本として残し、ユーザーも併用を指示している。`Exclusive submit=OFF` も Pegasus の正式計測を禁止しない。外乱回避・検知・再測定を成立させれば採用可能である。さらに Cygnus が実際に陳腐化した証拠もなく、2026-07-16 に現行 pin `d706650` の verify 校正が記録されている。

   根拠: [docs/decisions.md:2282](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/decisions.md:2282)、[docs/decisions.md:2291](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/decisions.md:2291)、[docs/pegasus-runbook.md:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/pegasus-runbook.md:41)、[docs/phase3-main-experiment.md:308](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-main-experiment.md:308)

   修正案: これらを却下理由に使わない。却下理由は 1〜9 の、対象不一致・共通工数隠し・未実装 gate・実行責任不在に限定する。


### C-B への親裁定 (現物裏取り済み)

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| 1 | A/B 比較が共通必須作業を隠す | real | U3 を「共通必須 (protocol/schema 承認・v2 verifier・topology 裁定) / cygnus 差分 / Pegasus 差分」の 3 欄構造へ再編 |
| 2 | 既存 driver は rr80/rr20 を測っていない | real (Explore 子の独立収集と一致) | 「既存資産が有効」を撤回 — 動作点参考まで。holdout freeze から target manifest を生成する専用 driver を設計素材へ |
| 3 | 実行量・独立性の過小評価 | real | floor protocol (対象集合・n・reps・時間分離 block・別 process/build・算出式・cross-block 統合) の凍結を計測の前提に。工数値は桁感として提示し「protocol 凍結前は未確定」と明記 |
| 4 | budget は floor から自動で出ない | real | bench 上限の事前導出式 + full-pipeline pilot での wall 校正を設計素材 (数値再凍結手順) へ |
| 5 | 択 B の binding/hardcode 落ち | real | Pegasus 差分欄に「driver の env contract 化 (NUMA/threads/binding の hardcode 除去)」を計上 |
| 6 | F3 admission の穴 | real (競合検知の検索パターンが従来ビルド木固定であることを現物確認、8b は専用 build cache 配下で走る) | **新規潜在ギャップとして採用**。binary path 非依存の競合検知を floor 実測の前提作業に含める (env 選択に関わらず必要) |
| 7 | cygnus 資産の鮮度未証明 | real (ただし攻撃不成立欄のとおり陳腐化の証拠もない) | reuse qualification (契約照合) を cygnus 差分欄の前提作業に |
| 8 | 第三案の消失 | real | 択 C = env-neutral な共通実装を先行し、env 裁定は「v2 数値を束縛する env-tag の選択」として分離提示 (worklog 再開手順 (3)(4) が先行するのと整合) |
| 9 | cygnus 実行の具体性不足 | real (部分) | 実行計画テンプレート (revision・preflight・停止条件・artifact 回収) を U3 に含める。実行責任者・時刻はユーザー裁定側 |
| 10 | 攻撃不成立 (D59 読解・cygnus 陳腐化・Exclusive OFF) | - | 却下理由に使わないことを確認 |

---

## C-A: §9 項 7・項 8 提示骨子への敵対所見 (逐語)

# 敵対レビュー結果

攻撃成功。項 7 は「集約コードがある」以上の完成度を主張できず、項 8 は拒否分岐こそ実在するものの、テスト済み・実走後という説明が過大。現状の骨子のまま裁定へ出すべきではない。

## 所見

### 1. [重大度 high] [確度 real] 不安定 trial・部分欠測 rep が oracle winner に混入する

根拠:

- pipeline は `unstable` を「採否の分布比較から呼び手が除外する」前提で WAL に残す。[pipeline.py:601](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/pipeline.py:601)
- 部分 rep 失敗は意図的に成功扱いされ、例えば 3 rep 中 2 rep だけでも throughput が残る。[test_calibrator.py:324](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/tests/test_calibrator.py:324)
- report は `tps` だけを取り、`unstable`、`high_variance`、`rep_notes`、期待 reps 数を observations へ渡さない。[s8b_oracle_report.py:383](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_report.py:383) [s8b_oracle_report.py:437](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_report.py:437)
- judge は `bench_values` が非空・有限なら rep 数不足も unstable も知らず eligible にする。[s8b_oracle_judge.py:90](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:90)

したがって、既知の不安定測定や 2/5 rep だけ成功した trial が、完全な 5/5 trial と同じ重みで winner を決め得る。中央値は非ランダムな欠測を救済しない。

提示文への修正案:

> 集約式は実装済みだが、`unstable/high_variance` と部分 rep 欠測の採否規則、および expected/observed reps の束縛は未実装。これらを再凍結し report→judge へ伝播するまで oracle 集約全体を「実装・テスト済み」とは呼ばない。

---

### 2. [重大度 high] [確度 real] 「exact tie は判定不能」は現行 judge の状態値と一致しない

根拠:

- tie 時は `verdict="tie"`、`winner=None` になるが、overall は `status="determinate"` のまま。[s8b_oracle_judge.py:226](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:226) [s8b_oracle_judge.py:243](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:243)
- 実際の fixture でも `determinate / tie / None` となった。
- tie テストは winner と tied IDs だけを検査し、overall status を検査しない。[test_s8b_oracle_judge.py:72](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/tests/test_s8b_oracle_judge.py:72)
- §6 の「oracle 非一意→判定不能」へ写像する結合 judge は未実装と worklog 自身が認めている。[worklog.md:938](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/worklog.md:938)

提示文への修正案:

> exact tie は oracle judge では「データとして確定した tie (`status=determinate`, `winner=null`)」になる。将来の §6 結合 judge がこれを oracle-floor 条件の判定不能へ写像する。この写像は未実装・未テスト。

---

### 3. [重大度 high] [確度 real] median-of-medians のテストは平均への変異を検出できない

根拠:

- fixture は `n=2`、各 trial も 2 値で、値が対称的。[test_s8b_oracle_judge.py:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/tests/test_s8b_oracle_judge.py:23) [test_s8b_oracle_judge.py:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/tests/test_s8b_oracle_judge.py:29)
- unique-best／tie テストとも集約値や `trial_medians` を数値検査していない。[test_s8b_oracle_judge.py:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/tests/test_s8b_oracle_judge.py:64)
- 読み取り専用の変異確認で、内外両方の `statistics.median` を `statistics.mean` に置換しても unique-best と exact-tie の両テストが PASS した。

これは、tie 処理のテストは存在するが「median of medians をテスト済み」という主張は false-green ということ。

提示文への修正案:

> 集約実装は存在するが、その統計量を固定する回帰テストは未整備。

加えて、外れ値を含む非対称 fixture を作り、`trial_medians`、最終値、winner を厳密に assert すること。

---

### 4. [重大度 high] [確度 real] 「1 スパイクに頑健」は n/reps 未凍結の現状では偽

根拠:

- n/reps は後日充填とされている。[phase3-8b-descriptor-design.md:315](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:315)
- manifest は reps を正整数としか制限しない。[s8b_oracle_manifest.py:298](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_manifest.py:298)
- 現行テストの 2 trial × 2 reps では、各中央値も外側中央値も二値の平均になるため、二重中央値は全 4 値の平均と同値。1 個の巨大スパイクで無制限に動く。

さらに、共有環境の外乱が trial 内の過半数、または trial の過半数に相関して出れば、奇数標本でも破れる。clean な対称ノイズでは平均より効率が落ちる代償も未提示。

提示文への修正案:

> 独立で少数の外れ値には頑健。ただし保証は凍結する n/reps、部分欠測規則、外乱の相関範囲に依存する。少なくとも両段の最小有効標本数を確定するまで「1 スパイク耐性」は主張しない。

---

### 5. [重大度 high] [確度 real] resume 拒否の committed test は存在しない

根拠:

- 指定された driver テスト全体に `resume`、`_ensure_campaign`、既存 WAL での二回目 `run_block` は存在しない。
- 内部実行テストは将来 gate を mock している。[test_s8b_oracle_driver.py:224](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/tests/test_s8b_oracle_driver.py:224)
- 現行 production path は non-null floor/budget を v2 verifier 未実装として先に拒否するため、通常経路では line 359 へまだ到達できない。[s8b_oracle_driver.py:121](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:121)
- consultation は有効 WAL なら例外が発火すると記録するが、再現可能なテスト成果物ではない。[2026-07-16_s8b-freeze-consultations.md:233](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/insights/2026-07-16_s8b-freeze-consultations.md:233)

line 359 は本物の条件付き `raise` であり恒真 assert ではない。しかし「実発火確認済み」を「回帰テスト済み」と読ませる骨子は過大。

提示文への修正案:

> 同一 output-root／campaign の有効 WAL に対する拒否分岐は実装済みで、相談時に関数レベル確認済み。ただし repo 内回帰テストと production E2E 到達確認は未実施。

---

### 6. [重大度 high] [確度 real] 実装の拒否境界は「実走後」ではなく「任意の有効 WAL 作成後」

根拠:

- `_ensure_campaign` は holdout 結果の有無を見ず、parsed record が一件でもあれば拒否する。[s8b_oracle_driver.py:344](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:344)
- 最初の `campaign-start` は budget ledger 作成より前に書かれる。[s8b_oracle_driver.py:391](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:391)
- holdout の実条件が canonical な形で現れるのは、成功 bench の `run_cmd` を含む `bench_done` 以後。[pipeline.py:282](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/pipeline.py:282)
- A3-3 は bench 前の ledger 失敗だけで campaign が焼失することを確認済み。[2026-07-16_s8b-third-wave-audit.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/output/insights/2026-07-16_s8b-third-wave-audit.md:38)

つまり「結果を見た可能性があるから拒否」だけでなく、「結果も holdout 条件もまだ WAL に出ていない初期化失敗」まで拒否する。クラッシュ代償の説明だけでは不足。

提示文への修正案:

> 現行実装は安全側に、結果露出後ではなく最初の有効 WAL record 作成後から再開を拒否する。そのため bench 前の初期化・台帳失敗も block を焼失させる。

---

### 7. [重大度 medium] [確度 real] 強化案の「lock」は現行 `campaign.lock` ではない

根拠:

- 現行 `campaign.lock` は identity ファイルで、`exists` 確認後に通常の `"w"` で書く非原子的実装。相互排他 lock ではない。[wal.py:146](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/wal.py:146)
- WAL 空確認から最初の `campaign-start` append までを覆う排他区間もない。[s8b_oracle_driver.py:352](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:352)
- marker を oracle 全体に置けば後続 block を遮断し、block 単位なら全体の cherry-pick 防止範囲が曖昧。A3-3 の topology が未裁定のままでは scope を決められない。

提示文への修正案:

> 強化は未実装案。ここでいう lock は現行 identity 用 `campaign.lock` ではなく、同時起動を排除する原子的・耐久的な one-shot/session lock を意味する。marker のキーと scope は A3-3 の topology 裁定で確定する。

---

### 8. [重大度 medium] [確度 real] floor の用途説明が §6 の二つの条件を混同している

根拠:

- on/off 予測差は choice ID が異なるかというカテゴリ条件で、floor は使わない。[phase3-8b-descriptor-design.md:227](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:227)
- floor を使うのは、on/off が選んだ二構成の oracle 実測性能差が floor を超えるかという別条件。[phase3-8b-descriptor-design.md:229](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:229)
- 現行 oracle judge は floor を入力に持たない。[s8b_oracle_judge.py:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:110)

提示文への修正案:

> floor は「on/off 予測 ID が異なるか」には使わず、両予測が選んだ構成間の oracle 実測性能差を評価する §6 第3条件にのみ使う。この結合判定は未実装。

---

### 9. [重大度 medium] [確度 real] exact tie 限定の代償が抜けている

根拠:

- tie 判定は float の厳密な `==` のみ。[s8b_oracle_judge.py:226](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:226)
- floor は tie-break／実用同等帯に使われない。[s8b_oracle_judge.py:113](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:113)

したがって `100.0` 対 `100.0000001` は、差が noise floor より桁違いに小さくても unique-best になる。これは意図可能な設計だが、「救済しない」だけではユーザーに代償が伝わらない。

提示文への修正案:

> practical tie band は置かないため、floor 内の微小差でも point-estimate の oracle winner は一意になり得る。ただし §6 の効果条件は別途 floor で不成立になり得る。

---

### 10. [重大度 medium] [確度 real] `trial_medians 全件記録` は eligible cell にしか成立しない

根拠:

- unknown は常に `trial_medians=[]`。[s8b_oracle_judge.py:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:29)
- correctness disqualified も空配列。[s8b_oracle_judge.py:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:78)
- 全値を sorted 保存するのは完全 eligible cell だけ。[s8b_oracle_judge.py:102](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:102)

また sorting により trial/block/time の対応を失い、双峰性を自動検出する gate もない。raw reps は observations に残るが、それは line 105 の「全件記録」とは別の証拠である。

提示文への修正案:

> eligible cell では全 trial median をソート保存し、raw reps は別 observations に保持する。unknown/disqualified cell の derived median は judge 出力から落ちる。双峰性は機械 gate ではなく事後監査材料にすぎない。

## 攻撃失敗した観点

- `s8b_oracle_judge.py:104` は実際に trial 内 median → trial medians の median を計算している。集約実装そのものの読み違いはなかった。
- 行番号 104、105、359 は現行 worktree と一致する。
- oracle judge は floor を入力に取らず、argmax の tie-break に使わない。
- exact tie テストは実在し、`winner=None` と tied IDs を検査している。
- docstring に「再凍結未」と明記されている。
- 有効な parsed WAL があれば line 359 の例外分岐は本物であり、単なる発火不能 assert ではない。
- `--output-root` 変更と truncated-only WAL の二迂回はコード上とも実在する。
- A3-3 とクラッシュ再開不能の相互作用は骨子に明示されており、その点自体は提示漏れではない。


### C-A への親裁定 (全 10 所見 real 採用 — 主要 4 件は親が独立再現)

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| 1 | unstable/部分欠測 rep が winner に混入し得る | real (judge の eligibility 検査範囲を現物確認) | U1 提示を「集約式は実装済みだが rep 採否規則・expected/observed reps 束縛は未実装」へ修正。rep 採否規則の凍結を設計素材 S 層 (freeze v2) の項目に追加 |
| 2 | exact tie は determinate/tie であり「判定不能」は結合 judge の未実装写像 | real (judge overall 判定を現物確認) | U1 提示を「tie はデータとして確定した tie。§6 判定不能への写像は R5 結合 judge が担い未実装」へ修正 |
| 3 | median→mean 変異でテストが PASS する false-green | real (**親が in-process 変異で再現**: tie/unique-best とも PASS) | 「実装・テスト済み」を「実装済み・統計量固定の回帰テストは未整備」へ修正。非対称 fixture + 数値 assert のテスト追加を実装段 TODO に |
| 4 | 「1 スパイク頑健」は n/reps 未凍結では偽 | real | 提示を「独立少数外れ値に頑健。保証は凍結する n/reps・欠測規則・外乱相関範囲に依存」へ弱める |
| 5 | resume 拒否の committed test 不在 + production 経路は :359 に未到達 | real (親も独立にテスト不在を確認済み) | U2 提示を「関数レベル確認済み、回帰テストと E2E 到達確認は v2 verifier 実装後」へ修正 |
| 6 | 拒否境界は「実走後」でなく「最初の有効 WAL record 以後」 | real (campaign-start が台帳生成より先 = 既読コードと整合) | U2 提示に「実装は凍結文言より安全側に広い。bench 前の初期化失敗でも block 焼失 = A3-3 との結合が本質」を明記 |
| 7 | 強化案の lock は現行 campaign.lock と別物 | real (wal.py:146 の非原子的 identity 書込みを現物確認) | U2 提示で「原子的 one-shot lock の新設」と明示。marker の scope は A3-3 topology 裁定に従属することを裁定順序に反映 |
| 8 | floor 用途説明が §6 の 2 条件を混同 | real | 提示を「floor は §6 第 3 条件 (両予測構成間の oracle 実測差) にのみ使用」へ精密化 |
| 9 | exact tie 限定の代償 (practical tie band なし) 未提示 | real | 「floor 内微小差でも point-estimate winner は一意になり得る (第 3 条件が別途 floor で締める)」を代償として提示 |
| 10 | trial_medians 全件記録は eligible cell 限定 | real | 「eligible cell のみソート保存、unknown/disqualified は空。raw reps は別 observations。双峰性検出の機械 gate はない」へ精密化 |

攻撃失敗欄 (集約実装の実在・行番号一致・tie テスト実在・迂回 2 経路の実在・A3-3 相互作用の明示) は骨子の正しい部分の裏書きとして記録。

---

## C-C: 実行トポロジー + freeze v2 + R3/R6 設計骨子への敵対所見 (逐語)

# 裁定

**承認不可。** 最大の破綻は、R6 が freeze 単位なら crash 再走を拒否し、campaign 単位なら新 `campaign_id` で迂回できることだ。累積予算も現状の debit 順序では物理消費を捕捉できず、cherry-pick 防止を「コストが掛かる」に置き換えている。

1. **[重大] [real] 「1 campaign = 1 block」は現行 invariant の言い換えで、A3-3 を直さない**

   根拠: manifest は既に block と campaign ID の一対一を要求する（[s8b_oracle_manifest.py:483](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_manifest.py:483)、[同:655](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_manifest.py:655)）。一方、schedule は複数 block を正式に許し、テストも `early`/`late` を正例にしている（[test_s8b_oracle_manifest.py:41](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/tests/test_s8b_oracle_manifest.py:41)）。

   修正案: 「1 manifest に block は正確に1件」「その block に予定全行（n=1なら12行）を含む」と schema で明記し、build/verify の双方で `len(blocks)==1` を強制する。単なる campaign↔block 一対一なら却下案と同じである。

2. **[致命的] [real] R6 マーカーと新 campaign 再走は二値論理上両立しない**

   根拠: §9 項8は実走後の新 process を拒否し、許可への変更は再凍結事項としている（[phase3-8b-descriptor-design.md:311](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:311)）。さらに verifier は実走 WAL により未既知性が失効する設計である（[s8b_holdout_freeze.py:590](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_holdout_freeze.py:590)）。worklog も crash 後は再開不能と説明している（[worklog.md:974](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/worklog.md:974)）。

   freeze 単位の marker なら新 ID も拒否する。campaign ID 単位なら ID を変えるだけで迂回できる。marker を WAL より先に作るほど、marker 作成直後の crash でこの矛盾が確定する。

   修正案: 次のどちらかを裁定する。

   - marker 後は再走なし。途中 crash は実験全体を判定不能。
   - §9 項8を改訂し、freeze-wide の事前割当 attempt registry、最大再走数、再走許可条件、未既知性 verifier を代替する launch certificate を再凍結する。

3. **[致命的] [real] 全 attempt 報告と経済的拘束だけでは cherry-pick は閉じない**

   根拠: 全件報告規則は manifest 内 campaign を落とさないことを要求する（[phase3-8b-descriptor-design.md:141](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:141)）。しかし現行 report は block ごとに一つの manifest-owned campaign しか射影できず（[s8b_oracle_report.py:583](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_report.py:583)）、judge は追加・重複行を不一致にする（[s8b_oracle_judge.py:193](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:193)）。

   予算内で「悪い途中結果なら crash、新 ID で再走」を繰り返せる。全件公開は透明性であって、選択規則ではない。

   修正案: attempt を入れ子で全件保持し、事前に次を固定する。

   - 結果を持つ WAL 発生後の crash は原則再走不可。
   - 再走するなら人手判断なしで自動発火し、上限 K を凍結。
   - 最初の authorized completed attempt だけを採用。
   - correctness-red は全 campaign 横断で吸収的に disqualify。
   - 複数 completed attempt は選択せず protocol violation。

4. **[致命的] [real] 累積台帳は、現状の順序では累積した「物理消費」を記録しない**

   根拠: driver は台帳を読み予算確認した後に evaluate し（[s8b_oracle_driver.py:441](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:441)）、完了後に初めて debit する（[同:535](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:535)）。lock は append の間だけである（[s8b_budget.py:291](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_budget.py:291)）。実測後の debit 拒否で、物理的に1.5秒走ったのに ledger が空のままになることをテストが正例化している（[test_s8b_oracle_driver.py:358](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/tests/test_s8b_oracle_driver.py:358)）。

   並行 campaign は双方が preflight を通って同時に消費できる。crash が append より前なら全消費が消える。

   修正案: evaluate 前に freeze-wide lease 下で最大 bench 枠を予約する。terminal 後に実測へ精算し、crash 時は予約を解放しない。`actual_bench_s` と gate 用 `charged_bench_s/reserved_bench_s` を分離し、並行 campaign は禁止または reservation まで直列化する。

5. **[重大] [real] 予算枯渇時には「全数再走」が成立しない**

   根拠: §5.2 は予算不足を判定不能へ倒す契約であり、途中成績による停止を禁じる（[phase3-8b-descriptor-design.md:209](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:209)）。現行 driver は行単位で不足を検出し、残行を skip する（[s8b_oracle_driver.py:445](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:445)）。

   crash 消費後の残額が全 block 最大費用未満なら、再走開始は途中停止を予定する行為になる。緊急増枠は結果閲覧後の予算変更であり禁止。6セルの予測は残っても、oracle が揃わず§6結論は不能になる。

   修正案: attempt 開始前に全予定行の最大 reservation を一括確保する。確保不能なら一行も走らせず `budget_exhausted_before_attempt` として全体を判定不能にする。完走を保証したいなら、restart contingency と最大 attempt 数を実走前の予算へ含めて再凍結する。

6. **[重大] [likely] 「単一 path」は freeze identity でもグローバル排他でもない**

   根拠: CLI は任意の `--budget` を許す（[s8b_oracle_driver.py:618](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:618)）。現行 ledger header に freeze hash はなく（[s8b_budget.py:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_budget.py:14)）、read は manifest hash と内部再集計しか照合しない（[同:212](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_budget.py:212)）。別 worktree・別 host の同名 path は別台帳である。

   修正案: ledger/marker の identity を v2 freeze byte hash から導出し、header に generation hash、budget-policy hash、schedule hash、limits を固定する。open 時に検証済み freeze と完全一致させる。CLI path override は削除するか、freeze が凍結した canonical shared URI との一致を要求する。共有不能なら execution site を一台へ固定する。

7. **[重大] [real] R3 の「外部 agent 呼出し exactly once」はローカル ledger だけでは実現不能**

   根拠: 現行 module は agent を実行せず（[s8b_selector_freeze.py:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_selector_freeze.py:2)）、fresh・一回・再利用なしは定数宣言にすぎない（[同:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_selector_freeze.py:64)）。provenance verifier も `fresh_context=true` 等の自己申告値を検査するだけである（[同:221](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_selector_freeze.py:221)）。これはF14型である（[failures.md:125](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/failures.md:125)）。

   call 前に ledger を書けば「claim 後・call 前 crash」でゼロ回、call 後に書けば「call 後・記帳前 crash」で再走による二回呼出しになる。

   修正案: provider の idempotency key/receipt がない限り、契約を「各 agent cell は at-most-once。結果不明 crash は missing 固定」に落とす。claim を durable に先行し、canonical payload、実 invocation receipt、raw bytes を同じ append-only journal に束縛する。off 2セルは invocation record を持たず static terminal record のみとする。

8. **[重大] [real] `selector_basis` は世代跨ぎ契約として約定漏れがある**

   根拠: basis は workload、variant binding、derangement、choice mapping だけを hash する（[s8b_selector_freeze.py:306](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_selector_freeze.py:306)）。descriptor projection/schema、実カタログ機構語彙、role/model、parser、runner policy は含まれない。さらに `sources` verifier はラベル付き任意 path/hash を受理し、正本 path を要求しない（[同:381](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_selector_freeze.py:381)）。

   修正案: basis を「4 agent cell の実送信 payload bytes/hash + catalog bytes + descriptor projection/schema + role + resolved model/effort + parser + execution policy + choice mapping + target binding」の versioned preimage にする。正本 path はコードまたは freeze で逐語固定する。世代差分として許すのは列挙済み floor/budget field だけにする。

9. **[中] [real] `completed = evaluate 到達` は終端条件として弱すぎ、rc の優先順位も未定義**

   根拠: 現行 driver は `completed_trials` を debit 前に増やす（[s8b_oracle_driver.py:535](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:535)）。したがって evaluate 到達後の WAL欠落、cleanup crash、budget debit拒否でも「到達」は満たせる。CLI は現在、completed 以外をすべて rc 2 に潰している（[同:622](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:622)）。binding mismatch テストも evaluate が1行少ない事実だけを確認し、campaign status を検査していない（[test_s8b_oracle_driver.py:322](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/tests/test_s8b_oracle_driver.py:322)）。

   修正案: completed は「全行に、report が受理できる一意の terminal outcome と対応 budget terminal record が耐久化済み」とする。優先順位を `internal-error(rc1) > protocol_violation(rc3) > budget-refused(rc2) > completed(rc0)` のように固定し、gate-refused の rc も別途明記する。JSON schema と CLI subprocess テストを追加する。

10. **[重大] [real] R5 はまだ判定定義ではなく、free-text rationale は証拠にならない**

   根拠: §6 は存在量化の対象と符号を規定していない（[phase3-8b-descriptor-design.md:225](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:225)）。一方 parser は rationale が非空なら受理するだけである（[s8b_selector_output.py:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_selector_output.py:110)）。

   修正案: user 裁定で逐語的な truth table を凍結する。

   - swapped は両 holdout 必須か。
   - floor は `oracle(on)-oracle(off)>floor` か絶対差か。性能改善を主張するなら前者。
   - on/off差とfloor超を同一 holdout に要求するか。
   - invalid/tie/excluded の三値伝播。
   - rationale は診断材料に限定し、成立を真へ昇格させる証拠には使わない。候補ID列挙は「消費した証明」にならない。

11. **[致命的] [real] §8 の承認境界を越えている。R1 のアーカイブ手続きも現行 generator と矛盾する**

   根拠: 予算、gate、選択規則、判定基準の変更は旧 freeze・変更理由・再凍結・ユーザー承認を要する（[phase3-8b-descriptor-design.md:255](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:255)）。項7〜8は依然承認待ち（[同:269](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/docs/phase3-8b-descriptor-design.md:269)）。現行 generator は再生成に旧 freeze の明示削除を要求しており（[s8b_holdout_freeze.py:519](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_holdout_freeze.py:519)）、R1 の並置保存と反対である。旧 freeze の source verify も現行 path の bytes を見るため、本文更新後は独立再検証できない（[同:550](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_holdout_freeze.py:550)）。

   修正案:

   - **裁定・再凍結必須:** 項7/8、restart 許可条件、crash charge、最大 attempt、contingency budget、単一block化、R5量化、数値 floor/budget。
   - **実装既定でよい:** 単一read object、atomic create、strict parse、freeze-wide reservation、改竄検出、既承認規則を弱めない rc。
   - generation-specific immutable filename、`supersedes_sha256`、変更理由、承認者・時刻・承認対象を記録する。旧世代を再検証可能にするなら、現行 path ではなく `frozen_at_head` の Git blobへ束縛する。

12. **[情報] [real] 攻撃失敗した観点**

   - crash の実 bench 消費を `B_total` に算入すること自体は§5.2と整合する。枯渇後を判定不能にする限り矛盾ではない。
   - A3-6 の「検証した bytes を一回だけ strict parseし、同一 object を全 consumerへ渡す」は正しい対策。ただし現行 driver/manifest はまだ複数回読む（[s8b_oracle_driver.py:366](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_driver.py:366)、[s8b_oracle_manifest.py:592](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_manifest.py:592)）。
   - SHA-256 の衝突は現実的攻撃ではない。問題は basis の投影漏れである。
   - rc 3 と衝突する既存 repo consumer は確認できない。衝突するのは現行 CLI 実装と不足テストであり、rc 3 自体の却下理由にはならない。
   - A3-5 は現状も false-green にならない。`verify-inconclusive` は judge が必ず unknown にする（[s8b_oracle_judge.py:64](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-ruling-prep/orchestrator/campaign/s8b_oracle_judge.py:64)）。強化候補のままでよい。


### C-C への親裁定 (全所見 real/likely 採用 — 主要 3 件は親が現物確認)

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| 1 | 「1 campaign = 1 block」は現行 invariant の言い換え | real | schema 強制へ具体化: manifest の blocks は正確に 1 件 + 予定全行含有、build/verify 双方で len(blocks)==1 |
| 2 | R6 マーカーと新 campaign 再走が二値論理上両立しない | real (**骨子の内部矛盾**) | 中心裁定点へ昇格: 択 (a) marker 後再走なし = crash で実験全体判定不能 / 択 (b) §9 項 8 改訂 + 事前割当 attempt registry (最大 K 凍結・自動発火・launch certificate) の再凍結。裁定 2 (項 8) の提示に統合 |
| 3 | 全件報告 + 経済的拘束では cherry-pick が閉じない | real | 採用: first-authorized-completed 採用規則 / K 凍結 / 人手なし自動発火 / correctness-red の吸収 disqualify / 複数 completed = protocol violation |
| 4 | 累積台帳は debit 順序が物理消費を捕捉しない | real (debit が evaluate 後であることを親確認) | 採用: freeze-wide lease 下の事前 reservation → 実測精算、crash 時は予約非解放。actual/charged 分離。並行 campaign 禁止 or reservation 直列化 |
| 5 | 予算枯渇時に「全数再走」が不成立 | real | 採用: attempt 開始前の全行一括 reservation。確保不能なら budget_exhausted_before_attempt で全体判定不能 (§5.2 の対称性維持) |
| 6 | 「単一 path」は freeze identity でもグローバル排他でもない | likely (設計要件として採用) | ledger/marker identity を v2 freeze byte hash から導出、header に generation/policy/schedule hash。CLI --budget override は廃止 or canonical 一致要求。実行 site 単一化 |
| 7 | R3 の exactly-once はローカル台帳では実現不能 (F14 型) | real | **骨子の主張を撤回・修正**: 契約は at-most-once + 結果不明 crash = missing 固定。durable claim 先行 + invocation receipt + append-only journal。off arm は invocation record なし |
| 8 | selector_basis の約定漏れ | real | 採用: versioned preimage へ拡張 (実送信 payload bytes / catalog bytes / projection・schema / role / resolved model・effort / parser / execution policy / mapping / binding)。世代差分は列挙 field 限定 |
| 9 | completed = evaluate 到達は弱すぎ、rc 優先順位未定義 | real | 採用: completed = 全行の一意 terminal outcome + 対応 budget terminal record の耐久化。rc 優先順位 (internal-error 1 > protocol_violation 3 > budget-refused 2 > completed 0) + JSON schema + CLI subprocess テスト |
| 10 | R5 は判定定義に未達、free-text rationale は証拠にならない | real | 採用: 逐語 truth table を裁定項目に (swapped 両 holdout 要否 / floor 方向差 / 同一 holdout 束縛 / invalid・tie・excluded の三値伝播 / rationale は診断限定で成立昇格に使わない) |
| 11 | §8 承認境界の越境 + R1 が現行 generator と矛盾 | real (generate の既存時 raise と _verify_source の現行 path 参照を親確認) | 採用: 裁定必須 (項 7/8・restart 条件・crash charge・最大 attempt・contingency・単一 block 化・R5 量化・floor/budget 数値) と実装既定 (単一 read object・atomic create・strict parse・reservation・改竄検出・rc) の切り分け表を D1/D2 の構造に。R1 は世代別不変 filename + supersedes_sha256 + frozen_at_head の git blob 束縛へ修正 |
| 12 | 攻撃失敗欄 (crash 消費の B_total 算入は §5.2 整合 / A3-6 対策の方向は正 / rc3 消費者衝突なし / A3-5 は現状 fail-closed) | - | 設計素材の前提として記録 |
