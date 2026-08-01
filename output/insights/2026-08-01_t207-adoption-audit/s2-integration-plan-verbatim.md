## 結論

親案はそのままでは不足があります。

- P1「branch の worklog (61) を verbatim 追記しない」は妥当です。ただし、`T-179`〜`T-181` も main と衝突しているため、D 番号だけでなく T 番号の再採番が必要です。
- P2「phase3.md の auto-merge を採用」は構文上可能ですが、周辺に 8c 未着手を前提とする記述が残り、意味上の矛盾が生じます。
- P3「5 ファイルは純粋追加」は真です。現 HEAD には存在せず、branch tip `402086d` と byte-for-byte 一致し、合計 1,907 行の追加です。ただし branch 全体では `decisions.md`、`phase3.md`、`worklog.md` も変更されるため、「branch 全体が純粋追加」ではありません。
- 正しさ防壁の受理集合は拡大されません。ただし supervisor は既存 preview 処理を一部再実装しており、「既存 pipeline のみを通り再実装なし」という説明は不正確です。
- この統合を文書整合まで完了させるには、親 brief の想定 8 ファイル以外に、文書地図・worklog archive・runbook lint 対象の更新が必要です。

以下の行番号は、特記しない限り merge 前の現 HEAD 基準です。

## 1. D99 衝突の解消

現 main の [docs/decisions.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/decisions.md:4757) は次の構造です。

- D104 終端: 4668 行
- 区切り `---`: 4670 行
- D105 見出し: 4672 行
- D105 終端兼ファイル末尾: 4757 行
- D105 後には `---` がありません。

したがって `docs/decisions.md` の競合は ours を基底にし、末尾へ以下の形で追加します。

- 4758 行: 空行
- 4759 行: `---`
- 4760 行: 空行
- 4761 行: branch の見出しを  
  `## D99. [T-178] ...` → `## D106. [T-178] ...`
- 4763〜4821 行: branch `docs/decisions.md:4382–4440` の本文をそのまま移植

branch D99 本文中には追加の文字列 `D99` はないため、本文内の D 番号置換はありません。見出し以外の参照変更は次の2か所です。

- [2026-07-29_t178-autonomous-ycsb-abc-dry-run.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/output/insights/2026-07-29_t178-autonomous-ycsb-abc-dry-run.md:123): `D99` → `D106`
- 新しい worklog entry (79): branch (61) の `D99` を転記せず、統合結果を `D106` として記録

さらに、auto-merge 後の `docs/phase3.md` 8c 節の runbook 参照付近、概ね新 433 行へ `設計裁定: D106` を追加すると、phase から決定への逆参照も成立します。

## 2. T 番号衝突

insight 127 行の `T-179` は merge 後に壊れる参照です。現 main では既に別の意味で使用されています。

- `T-179`: worker resource ledger
- `T-180`: resource envelope
- `T-181`: reasoning A/B

branch の worklog (61) は同じ番号を次の作業に再利用しており、そのまま取り込めません。現 main の最大番号 `T-220` の後へ再採番します。

| branch 内の意味 | 新番号 |
|---|---:|
| A/B/C の live build→legacy+S2→bench pilot | T-221 |
| H1 rr80 / H2 rr20 の on/off/swapped formal series | T-222 |
| crash resume と bench-time budget accounting | T-223 |
| land 後の branch/worktree cleanup | T-224 |

したがって insight 127 行は `T-179` → `T-221` とします。main 側の既存 `T-179`〜`T-181` の意味は変更しません。

## 3. phase3.md の統合

branch の 8c hunk は現 main の 415〜422 行を置換し、merge 後は概ね 415〜448 行になります。しかし、hunk だけでは以下が矛盾したままです。

- 19 行: checkpoint 日付
- 21〜22 行: 全 loop が human-supervised との断定
- 27〜29 行: 8c は bottleneck 確認後だけ着手
- 81〜82 行: 同じ旧順序
- 364 行: 見出しが「8c は条件付き」
- 797〜804 行: 8c piping が入れば axis-proposer を機械検査できるとの記述

統合時には次の意味修正を行います。

1. 19 行の日付を `2026-08-01` に更新。
2. 21〜22 行は「planner/coder/auditor/critic の bounded supervisor は session-independent になったが、project-wide unattended completion ではない」と限定。
3. 27〜29、81〜82 行は、2026-08-01 のユーザー裁定によって旧条件順序が上書きされたことを記録。
4. 364 行の見出しを「bounded MVP 済み、formal H1/H2 と resume は未完了」へ変更。
5. 415〜422 行は branch 8c hunkを採用。
6. merge 後概ね433行に `D106` を付記。
7. 現797〜804行、merge後概ね823〜830行は、axis-proposer が今回の MVP から明示的に除外されているため、意味 gate は依然人間管理であると訂正。

[docs/roadmap.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/roadmap.md:124) の session-independent checkpoint/budget/resume 要件や、287行の「API direct」移行は満たしていません。したがって「8c 完了」や「自律完走」とは記載せず、「CLI を使う bounded MVP」と位置付けます。そうすれば roadmap 自体の裁定変更は不要です。

## 4. 参照整合の全数調査

### D/T・設計識別子

| 識別子 | 出現箇所 | merge 後の判定 |
|---|---|---|
| D99 | insight:123 | 壊れる。main の D99 は T-143 RuleOps。D106へ変更 |
| D106 | 新 decisions、phase、worklog、insight | 新設すれば実在 |
| T-178 | insight:1、D106、phase | 実在する過去作業 anchor。重複なし |
| T-179 | insight:127 | 壊れる。main では別作業。T-221へ変更 |
| T-221〜T-224 | 新 worklog | 新規採番が必要 |
| `8b-v1` | runbook:17 | schema/descriptor 実装に実在 |
| `silo-backoff-trigger-gating` | runbook:4、insight:8 | descriptor/trigger 系に実在 |
| H1 / H2 | runbook:134、phase 8c | 計画識別子として整合。まだ実測未完了 |
| legacy+S2 | runbook、phase | 既存 campaign pipeline に実在 |
| bench pipeline | runbook、phase | 既存 pipeline に実在 |

### ファイル・runbook・campaign パス

| 参照 | 出現箇所 | 判定 |
|---|---|---|
| `docs/phase3-8c-autonomous-trial-runbook.md` | phase、insight、D106 | 今回追加され実在 |
| `output/insights/2026-07-29_t178-autonomous-ycsb-abc-dry-run.md` | D106 | 今回追加され実在 |
| `orchestrator/campaign/claude_projected_provider.py` | D106、test import | 今回追加され実在 |
| `orchestrator/campaign/p3_autonomous_workload_trial.py` | runbook、D106、test import | 今回追加され実在 |
| `orchestrator/tests/test_p3_autonomous_workload_trial.py` | D106 | 今回追加され実在 |
| `docs/phase3-8b-descriptor-design.md` | runbook:11 | 実在 |
| `.codex/agents/README.md` | runbook:46 | 実在 |
| `tools/check_codex_agents.py` | runbook:47 | 実在 |
| `docs/related-work/README.md` §7.2 | phase 8c | 実在 |
| `orchestrator.campaign.p3_autonomous_workload_trial` | runbook:59,72,86 | 新 module として実在 |
| `output/campaigns/<campaign-id>/` | runbook:115 | 親ディレクトリ実在。既存正式 campaign 出力 |
| `output/autonomous-trials/<trial-id>/` | runbook:106、insight:112 | 現在は不存在だが supervisor:869–877 が実行時に作成する template。壊れた参照ではない |
| `/tmp/izanagi-t178-live*` | insight:108–110 | 現ホストには3件実在。ただし repo 外で非永続。正式証跡として扱えない |
| commit `436a3af` | insight:127 | git object として実在 |
| CCBench `d706650` | insight:127–128 | 現 submodule HEAD と一致 |

### role 名

| role | 実体 | 判定 |
|---|---|---|
| planner | `.claude/agents/planner-v4.md` | 実在。supervisor:100–108 で束縛 |
| coder | `.claude/agents/coder-v4-autonomous-trigger-gating.md` | 実在。supervisor で束縛 |
| auditor | `.claude/agents/auditor.md` | 実在 |
| critic | `.claude/agents/critic.md` | 実在 |
| axis-proposer | `.claude/agents/axis-proposer.md` | 実在するが今回の MVP 対象外 |
| `claude-headless` | runbook:32、provider | provider 名として実装済み |
| Codex provider | runbook:129 | 意図的に対象外。`.codex/agents/README.md` の runtime blocked 状態と整合 |

### trial ID と receipt

| trial | report / attempts SHA | 判定 |
|---|---|---|
| `claude-abc-g1` | insight:37–40 | `/tmp/izanagi-t178-live.rPCkGR` の実体と一致 |
| `claude-abc-g1-v2` | insight:52–55 | `/tmp/izanagi-t178-live-v2.Cf7D0M` と一致 |
| `claude-abc-g1-v3` | insight:68–71 | `/tmp/izanagi-t178-live-v3.kkVtgu` と一致 |

これら SHA は現ホスト上では照合できますが、raw bundle は main に land されません。insight は「探索 receipt」であり、正式 campaign proof chain ではないことを維持します。

### 逆方向の参照不足

次を同 wave で補います。

- [docs/README.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/README.md:42): 現在の地図は `phase3-s*.md` と `phase3-8b-*.md` だけです。`phase3-8*-*.md` などに広げ、8c runbook を地図へ含める。
- [output/README.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/output/README.md:5): `autonomous-trials/` を追加し、exploratory supervisor journal であって `output/campaigns/` の正式 proof chain ではないと明記。
- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/tools/check_docs.py:66): runbook lint が `phase3-s*-runbook.md` だけを列挙しており、8c runbook が検査外です。DW-O13 に従い `phase3-*-runbook.md` へ一般化し、対応する checker test を追加する。
- `orchestrator/README.md` は `p3_*` の一般案内で既に包含するため変更不要。
- `orchestrator/tests/README.md` は新 test の `__main__` guard が既存条件を満たすため allowlist 変更不要。

このため親の「取り込み対象5ファイル＋競合3 docsだけ」という変更面は修正が必要です。

## 5. worklog (61) の扱い

branch の entry (61) を追記しない方針は正しいです。

理由は次の通りです。

- main archive に別内容の entry (61) が既にあり、D35 の一意な索引を破る。
- branch (61) の `T-179`〜`T-181` が main の既存 task と衝突する。
- branch の巨大な「次の一手」は分岐時点の状態であり、現在の保存則へそのまま接続できない。

ただし現 [docs/worklog.md](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t207-p3-trial-adopt/docs/worklog.md:12) は約95,116 bytesで、`check_docs.py` の100,000 byte上限に近いため、entry (79) の単純追記では赤になる可能性が高いです。

統合手順は次の通りです。

1. 現 entry (73)、worklog 53〜342行を byte-for-byte で新規  
   `docs/archive/worklog-phase3-0731-73.md` へ移す。
2. `docs/archive/README.md` の末尾、現在の `(72)` の次に archive を登録。
3. current worklog から entry (73) を除き、entry (74) から開始させる。
4. 新 entry は `(79)` とする。
5. entry (79) 本文に以下を記録する。
   - `[T-207] 完了`: `436a3af..402086d` の merge、D106、phase3 8c、5ファイルの採用
   - `[T-178] 完了・T-207へ吸収`: runbook、insight、D106への索引
   - `[T-174] 部分`: projection receipt は得たが mechanism transfer は未達
   - `/tmp` receipt は非永続で、正式証跡ではない
6. D70 の保存則の source は前 entry (78) の「次の一手」、現1215〜1372行です。この全 top-level ID を entry (79) の本文で sink するか、次の一手へ同じ main 上の意味で保持します。省略せず全件を移すのが安全です。
7. branch 由来の follow-up は新しい「次の一手」へ `T-221`〜`T-224` として追加。
8. 検査結果、commit hash、request ID は段6の実測後にだけ記入し、事前に緑と書かない。

## 6. 正しさ防壁の検証

product の受理集合を変更しないという親の結論は、限定付きで成立します。

- supervisor:442–450 は既存 descriptor validation を利用。
- supervisor:783–800 は既存 `trigger.drive_iteration()` を authoritative path として呼ぶ。
- trigger:359–401、439–489 が既存 campaign path を通す。
- trigger:276–313 が DiffQuarantine、禁止識別子 gate、auditor digest照合を再実行。
- `loop.py:43–60` が legacy+S2 を選択し、`pipeline.py` の verify/bench pathへ入る。
- buildなしでは `dry-pass` しか返さず、正しさ・性能の正式証明にならない。
- official/certified selector への登録はなく、oracle の受理集合にも追加されない。

ただし以下は明記が必要です。

- supervisor:453–471 の `_preview()` は、既存 trigger:494–506 の preview と quarantine/forbidden gate の一部を再実装しています。
- authoritative `drive_iteration()` が後段で再検査するため受理集合を広げませんが、drift により余分に reject する可能性はあります。
- supervisor は formal oracle gate を通っていません。したがって「oracle gate を既存 pipeline 経由で通る」のではなく、「探索 path なので oracle の受理集合へ参加しない」が正確です。
- supervisor:370–397 の `AttemptJournal` は campaign WAL の代替ではありません。
- supervisor:479–501 の metric projection は critic 用で、acceptance 判定ではありません。

5ファイルの SHA を参照する既存 trust/pin root はなく、既存 frozen byte列にも変更はありません。

## 7. merge の具体手順

1. 現在 staged されている5つの inspection copy が branch tip と一致することを再確認。
2. merge 前に、その5パスだけを対象指定して index/worktree を clean に戻す。無関係なユーザー変更には触れず、`reset --hard` は使わない。
3. 次を実行する。

   ```bash
   git merge --no-ff --no-commit codex/p3-autonomous-trial
   ```

4. `docs/decisions.md`:
   - ours を全面採用
   - 末尾4758行以降へ branch D99 を D106 として追加
5. `docs/worklog.md`:
   - ours を全面採用
   - branch (61) は破棄
   - entry (73) を archive へ移し、entry (79) を新規作成
6. `docs/phase3.md`:
   - auto-merge された branch 8c hunkを保持
   - 前述の周辺矛盾と D106 参照を修正
7. 新規5ファイル:
   - 原則 theirs を保持
   - insight:123 の D99→D106
   - insight:127 の T-179→T-221
8. 文書地図と検査面を更新:
   - `docs/README.md`
   - `output/README.md`
   - `docs/archive/README.md`
   - 新 archive
   - `tools/check_docs.py` と対応 test
9. `git diff --cc` と `git diff --cached --stat` で、競合 marker、意図しない既存コード変更、欠落ファイルがないことを静的確認。
10. merge commit として確定し、cherry-pick/squash はしない。

この方法なら `436a3af` と `402086d` は merge commit の第2親側の祖先として残り、両 commit の `AI-Agent: ... role=author` trailer が保存されます。統合者は実際の merge commitへ適切な provenance trailer を付けます。

もし `tools/check_docs.py` など実装ファイルを merge resolution commit 内で変更するなら、それは両親との差分になるため merge commit 自体に Codex author provenance が必要です。より明確にするなら、まず docs 競合だけで merge commitを作り、checker一般化を直後の別 Codex-author commitに分けます。

## 8. 段6の受入・検査と赤の予測

親は Pegasus 規律に従い、pytest を直接ログインノードで走らせず、計算ノードへ dispatch します。

### `python3 tools/check_docs.py`

赤になりうる箇所:

- D99 を双方残した場合の decision ID 重複
- D106 参照だけ追加し、decision 本体をstageし忘れた場合
- entry (78) の task IDを entry (79) で sinkし忘れた場合
- worklogをrotateせず100,000 byteを超えた場合
- runbook glob一般化後、新runbookに既存lint違反が見つかった場合

なお、insight の誤った D99/T179 は現在の checker 対象外なので、checker緑でも意味整合を保証しません。

### `python3 tools/check_codex_agents.py`

AGENTS.md が要求する追加検査です。今回 role ファイル自体は変えませんが、runbook が Codex providerを対象外とする説明と現 blocked 状態の一致を確認します。

### `python3 tools/check_ai_provenance.py`

赤になりうる箇所:

- 原2 commit の trailer/ancestryを失う squashまたはcherry-pick
- merge commitで両親と異なる実装コードを作ったのに `role=author` がない
- trailer形式不正
- provenance rangeの指定ミス
- Pegasus dispatch の `rc=16`。これは監査不合格ではなく dispatch失敗

### `python3 tools/run_tests.py` 全走

重点的に赤になりうる範囲:

- 新規 `test_p3_autonomous_workload_trial.py` の5テスト
- plain-runner / `__main__` 契約
- s8b repo scanの禁止組合せ検査
- `check_docs.py` のrunbook globを変えた場合のchecker tests
- merge provenance fixture
- CCBench/toolchain/site依存、および今回と無関係な現 main 由来の失敗

過去の focused 実測があっても、今回の merge 後全走が緑とは主張できません。段6で得た request ID、失敗した最初の node、終了コードを entry (79) に記録します。

## 総括

採用すべき統合は「branch を履歴付き mergeし、D99をD106へ、branch-local T179〜181をT221〜223へ再採番する」形です。worklog (61) は破棄し、main の保存則を継ぐ entry (79) を作成します。

5ファイルは純粋追加で、既存 product の正しさ受理集合も広げません。ただし phase3 周辺記述、文書地図、output地図、worklog archive、runbook lint対象まで直さないと、機械検査または意味上の参照整合が不完全です。pytestを含む実測結果は本プランでは未確認であり、親が段6で計算ノード上から取得する必要があります。