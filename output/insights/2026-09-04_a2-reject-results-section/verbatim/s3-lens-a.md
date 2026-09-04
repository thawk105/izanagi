## 数値・凍結物の照合結果

数値の転記誤りは見つからなかった。WAL 生値からの再計算、親表、`certification.json` は一致する。

| cell | median | mean | sd | t95 CI 半幅 |
|---|---:|---:|---:|---:|
| rr5-stock | 2,527,542 | 2,554,948.8 | 96,482.1 | 119,798.3 |
| rr5-fixed10 | 1,355,011 | 1,359,769.6 | 16,867.7 | 20,944.1 |
| rr50-stock | 3,662,448 | 3,700,807.2 | 110,327.5 | 136,989.6 |
| rr50-fixed5 | 1,248,603 | 1,242,560.2 | 26,533.1 | 32,945.2 |

effect の向きも `adopted median / stock median − 1` で正しく、rr5 `−0.4639016878849095`、rr50 `−0.6590796647488237`、表示値 `−46.3902%` / `−65.9080%` は一致する。[certification.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/output/insights/2026-08-24_paper-story-a2-certification/certification.json:1)、[a2-stats-parent.md:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/a2-stats-parent.md:3)

外部 WAL 2 本・raw JSON 4 本の SHA-256 も `raw-manifest.json:/files` と一致した。実 WAL の workload 当たり stage 数は `build_start=2`、`build_done=2`、`verify_done=12`、`bench_done=2`、`commit=2` であり、plan の brief 訂正は正しい。

凍結物を直接変更する操作も plan にはない。`FROZEN_MANIFEST` は実際に 23 件で、A-2 insight、paper-story 図、fig5 は含まれない。[test_frozen_artifacts.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_frozen_artifacts.py:41)、[同:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_frozen_artifacts.py:234)

以下は、数値が現在一致していることとは別に、実装後も一致を強制できない箇所である。

## 所見

1. **結果節の数値面が手書きのままで、中心成果物だけ機械検査から外れる**

   - **(a) DW-G05:** `results/*.md` の表・本文だけを誤更新しても図・provenance の検査は緑のままになり、成果物の値が authority と異なる。
   - **(b) 根拠:** D12 は事実層を機械コンパイルし、LLM の作文を通さないと定める。[rulings-verbatim.md:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/rulings-verbatim.md:22) 一方、brief は親による docs 直接編集を許し、plan の integration test は fig5 closure と caption だけで、結果表の照合 node がない。[s1-brief.md:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/output/insights/2026-09-04_a2-reject-results-section/s1-brief.md:81)、[s2-plan.md:261](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:261) 現 draft は表外に旧効果と平均比 `−46.78% / −66.42%` まで置き、brief P4 の「本文は表の値だけ」にも反する。[results draft:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/paper-story/results/2026-09-04-a2-certification-reject.md:34)、[同:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/paper-story/results/2026-09-04-a2-certification-reject.md:87)、[s1-brief.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/output/insights/2026-09-04_a2-reject-results-section/s1-brief.md:65)
   - **(c) 修正案:** 同じ validated data から表の Markdown と数値文を生成するか、結果表・effect・CI・status を独立に parse して authority と exact 照合する専用 test を追加する。表外の平均比の数値は削除する。
   - **(d) real 確度:** **0.99**

2. **D1074 の「検証済み凍結 report」への証拠鎖が plan 内で閉じていない**

   - **(a) DW-G05:** 実装時に選んだ任意の `certification.json` と同じ hash を生成器・テストへ書けば、その bytes の `status` が図・caption の判定として受理される。
   - **(b) 根拠:** D1074 は hash 束縛だけでなく検証済みであること、自己申告 hash だけで済ませないことを要求する。[rulings-verbatim.md:118](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/rulings-verbatim.md:118) Plan は生成器 literal と同じ変更内の「独立なテスト定数」を根拠にするが、既存 run README の生成時 hash や検証 receipt との機械的な連結を設計していない。[s2-plan.md:11](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:11) 既存 README には正しい SHA-256 がある。[run README:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/output/insights/2026-08-28_t2022-a2-certification-run/README.md:24) また legacy v3 materializer の validator は status/effects を evidence から再導出せず、型・identity を主に検査する。[paper_story_a2_certification.py:3896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/campaign/paper_story_a2_certification.py:3896)
   - **(c) 修正案:** 作図器は判定を再計算せず、事前に存在する run README または凍結 validation receipt が記録した certification hash と照合する。テスト定数の由来をその生成時 authority に固定し、「現行 bytes をその場で hash した値」を信頼根にしない。
   - **(d) real 確度:** **0.88**。現在の hash と status が正しいことではなく、plan がその正しさの由来を実効検査へ落としていない点を real とする。

3. **canonical certification/raw-manifest hash gate の発火を証明する負例と変異がない**

   - **(a) DW-G05:** CLI から canonical hash 検査を実装し忘れても全予定 test が緑になり、tracked authority の受理集合が任意 bytes へ広がる。
   - **(b) 根拠:** Plan は CLI の hash 検査を必須とするが、列挙 node は「現 bytes と独立 pin が一致する」正例だけである。tracked certification または raw-manifest の bytes を変え、CLI が拒否する負例がない。[s2-plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:71)、[同:242](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:242) 変異表にも external 6 file の hash 省略しかなく、2 tracked authority の pin 省略がない。[同:346](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:346)
   - **(c) 修正案:** certification と raw-manifest を各々 whitespace-only で変えた copy を `--certification` / `--raw-manifest` に渡し、CLI が非 0 かつ三成果物ゼロになる負例を追加する。両 hash gate の削除を別々の変異として登録する。
   - **(d) real 確度:** **0.99**

4. **landed provenance の generator hash を live source pin にする設計になりうる**

   - **(a) DW-G05:** 後日の生成器修正だけで既存 fig5 が不正扱いになり、凍結図・provenance の参照を更新する圧力が生じる。
   - **(b) 根拠:** Plan は provenance に generator hash を持たせ、`validate_repo_closure()` が generator を検証し、landed fig5 test から呼ぶ形を示す。[s2-plan.md:193](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:193)、[同:218](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:218) しかし plotting README は、図の generator hash は生成時 bytes の記録であり現行 source の pin ではないと明記する。[tools/plotting/README.md:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/README.md:76) fig4 の landed validator も生成時定数を照合し、live source を再 hash しない。[test_s1_9pair_figure_provenance.py:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_s1_9pair_figure_provenance.py:671)
   - **(c) 修正案:** 新規生成時だけ provenance generator hash と当時の source を一致させる。landed artifact test は生成時 golden を照合し、現行 source との一致を要求しないと明記する。
   - **(d) real 確度:** **0.94**

5. **durable root の部分欠落を fail にする設計と、引用した雛形が正反対**

   - **(a) DW-G05:** root が存在しても 1 file 欠ければ実データ検査全体が skip され、壊れた外部入力集合を「テスト赤なし」と数えられる。
   - **(b) 根拠:** Plan は「root が存在して一部だけ欠ける場合は failure」とする。[s2-plan.md:240](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:240) 直前に引用した B-10 helper は欠落が 1 件でも `skip()` し、専用 test も部分欠落時の skip を正例としている。[test_plot_b10_extended_backoff.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_b10_extended_backoff.py:60)、[同:369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/orchestrator/tests/test_plot_b10_extended_backoff.py:369)
   - **(c) 修正案:** root 自体が無い場合だけ skip、一度 root が存在すれば期待 6 file の欠落・非 file・hash 不一致は failure とする専用 helper を書く。B-10 helper をそのまま流用しない。
   - **(d) real 確度:** **0.99**

6. **実寸 fixture に production WAL が出さない偽 field を追加する設計**

   - **(a) DW-G05:** stage selector の検査が実在しない WAL 形に依存し、production では起きない赤または恒真な緑を作る。
   - **(b) 根拠:** Plan は `verify_done` / `build_done` に巨大な偽 `tps` や abort 値を置く。[s2-plan.md:238](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:238) 実 WAL では `build_done.payload` に `tps`/abort はなく、`verify_done.payload` は `aborts` を持つが `abort_rate` は持たない。`commit.payload` には既存の `fitness_tps` がある。§10 は値だけでなく production 入力と同じ形を要求する。[FIGURE_CONVENTIONS.md:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/tools/plotting/FIGURE_CONVENTIONS.md:98)
   - **(c) 修正案:** 全 stage の key set を実 WAL と同一にする。無視を観測する sentinel には既存 field の `commit.payload.fitness_tps`、`verify_done.payload.aborts` などを使う。
   - **(d) real 確度:** **0.99**

7. **変異 10 件は現状の表では単一理由・一意注入・完全 node 集合を満たさない**

   - **(a) DW-G05:** 変異が冗長 gate に kill されたり、production 等価なのに KILLED と集計されたりし、検査の実効性に関する結論が変わる。
   - **(b) 根拠:** [s2-plan.md:346](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:346) の表には次の問題がある。
     - #4 は raw 1 field を変えるだけでは、その前段の manifest hash gate に拒否され、WAL/raw identity gate の単一理由にならない。loader 順は hash が先である。[同:75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:75)
     - #2 も samples だけを 4 件にすると raw/certification/median/CV の冗長照合に mask されうる。
     - #4、#8、#10 は「A または B」と一行に複数の置換候補を持ち、注入位置が一意でない。
     - #7 の `"reject"` 固定は canonical CLI 入力が必ず `reject` なので production 等価であり、内部 sentinel への propagation 検査は kill ではなく diagnostic sensitivity pin が妥当。
     - #1、#8、#9 は共通正常 fixture・CLI・landed closure も通る経路を変えるため、期待 node を singleton と断定できない。DW-M08 は失敗 node の完全集合を要求する。[mutation.md:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/dev-wave/mutation.md:56)
   - **(c) 修正案:** #4/#8/#10 を一置換一変異へ分割する。#2/#4/#5/#6 は前段 hash・冗長投影を整合させ、狙う一条件だけ不正な fixture を事前構築する。#7 は diagnostic 枠へ移す。全件を probe は SURVIVED 期待で走らせ、観測した完全 node 集合を本登録する。
   - **(d) real 確度:** **0.99**

8. **`source_commit` が二つの repository を指す衝突を provenance schema が解消していない**

   - **(a) DW-G05:** provenance の source commit が Izanagi `639c1d…` でなく CCBench `511c953` として記録され、入力参照が別 repository の commit へ変わる。
   - **(b) 根拠:** Plan は measurement conditions に generic な `source commit` と `CCBench pin` を置くだけで source field の取り方を指定しない。[s2-plan.md:198](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:198) `certification.json:/source_commit` は Izanagi の `639c1dbad4…`、`/current_pin` は CCBench `511c953` だが、raw JSON の `/build_evidence/source_commit` は CCBench `511c953` である。
   - **(c) 修正案:** provenance field を `izanagi_source_commit` と `ccbench_pin` に分ける。前者は certification、後者は certification `current_pin` から取り、raw `build_evidence.source_commit == current_pin` を明示的に照合する。
   - **(d) real 確度:** **0.95**

9. **新しい `results/` lifecycle は本依頼を越える未裁定の一般化**

   - **(a) DW-G05:** A-2 の一成果物だけでなく、将来の paper-story 文書の置場・append-only 性・再導出単位・参照規則が変わる。
   - **(b) 根拠:** 親自身が P1 を provisional とし、D1013 の直接適用ではないと認める。[s1-brief.md:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/output/insights/2026-09-04_a2-reject-results-section/s1-brief.md:45)、[s2-plan.md:13](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:13) D1013 が裁定したのは `claim-evidence/` 系列であり、一般の `results/` 系列ではない。[rulings-verbatim.md:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/rulings-verbatim.md:79) Plan はこの未裁定系列を実装前提にしている。[s2-plan.md:302](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-a2-reject-results-section/codex/a2-reject-results-section/s2-plan.md:302)
   - **(c) 修正案:** 下記の裁定パッケージへ返し、裁定前は新系列を既定採用しない。
   - **(d) real 確度:** **0.98**

10. **brief の「pin 閉包ゼロ・稼働 wave 5 本・重複ゼロ・T-2228 稼働中」は一次資料で再現できない**

   - **(a) DW-G05:** 隠れた pin または並行所有 path が存在すれば、fig5 の参照検査や他 wave の未 commit 編集を衝突させる。
   - **(b) 根拠:** brief は結論だけを記す。[s1-brief.md:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/output/insights/2026-09-04_a2-reject-results-section/s1-brief.md:41) DW-O09 は path hit だけでなく role/key、source hash pin、schema、review ledger まで検索・分類することを要求する。[operations.md:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/dev-wave/operations.md:60) 現 worktree の一次資料で確認できるのは、FROZEN_MANIFEST 非包含、T-2226 の着地、T-1999 が A-2 後の 2026-09-01 に着地したこと、T-1647 の本文が実走前で stale なことまでである。T-2228 は worklog 上では carry stub のみで、稼働 receipt・所有 path・5 wave の集合が brief に添付されていない。[worklog.md:498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-a2-reject-results-section/docs/worklog.md:498)
   - **(c) 修正案:** pin 検索の query と全 hit 分類、稼働 worktree の path 集合と取得時刻を insight に残す。残せない場合は「FROZEN_MANIFEST には非包含」までに命題を狭め、T-2228 と重複ゼロは実装前に再確認する provisional 事実と書く。
   - **(d) real 確度:** **0.97**。重複が実在すると断定する所見ではなく、brief の一般化を裏付ける証拠がないことを real とする。

## 裁定パッケージ候補

`docs/paper-story/results/` を独立した恒久系列として新設するか。

- **案 A、推奨:** A-2 のような完走済み個別結果の材料レポート専用系列として明示的に裁定する。対象、append-only、再導出単位、版履歴へ入れないこと、数値 block の機械生成を一体で定める。
- **案 B:** 新系列を作らず、本 wave の insight に結果材料を置き、paper-story README から指す。将来複数件が必要になった時点で系列を裁定する。

案 A を採る場合でも、現 plan の「親が数値表を手書きする」形は D12 と分離して修正する必要がある。

## 総括

- 所見件数: **10 件**
- real と主張する件数: **10 件**。現在の数値誤りではなく、検査・provenance・scope の実欠陥として数えた。
- 静的検査のみ。pytest は実走していない。
- 最重要 3 件:
  1. 中心成果物の結果表が機械照合されず、D12 と「一つの主張に一つの数値」を守れない。
  2. tracked certification/raw-manifest の canonical hash gate に負例・変異がなく、D1074 の実効性を証明できない。
  3. 変異表が mask、等価変異、一意でない注入、完全 node 集合未確定を含み、10件 KILLED を有効な証拠にできない。
- brief に対する訂正候補:
  - P4 の「本文は表の値だけ」と現 draft の旧効果・平均比を整合させる。
  - P5 の stage 数を「workload 当たり」と「全 fixture 合計」に分ける。
  - D1074 の根拠を「現 bytes の literal pin」ではなく生成時 authority・検証 receipt へ結ぶ。
  - `source_commit` を Izanagi と CCBench に分ける。
  - 「pin 閉包ゼロ」「重複ゼロ」「T-2228 稼働中」は証拠 receipt を添えるか provisional に狭める。
  - `results/` 系列新設は P1 のまま実装せず、ユーザー裁定へ返す。