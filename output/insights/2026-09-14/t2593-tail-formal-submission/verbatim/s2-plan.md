## 方針と読解結果

変更は投入・job の新系列分岐と、集団報告の操作入口に限定する。事前登録と driver 本体は変更しない。本段は静的読解のみで、ファイル変更・テスト実行・投入は行っていない。必読6ファイルはすべて読めた。

P1-b（job は8 genome と execution receipt を確認）、P1-c（旧種別への新 flag 指定は rc=2）を採用する。P1-a の独立 script 新設には、既存 inventory 検査との衝突を理由に反対し、既存 driver の直接呼出しを文書化する代案を推す。

以下の行番号は現在の worktree における番号。表では `S`＝`tools/pegasus/submit_b10_backoff_grid.sh`、`J`＝`tools/pegasus/b10_backoff_grid.sh` とする。

## 変更面の表

| file:line | 現在の内容 | 置換・追加する内容の骨格 |
|---|---|---|
| `S:6–9` | usage は旧3種別 | `t2500-tail-formal` と新2 flag を追記。新系列限定の必須入力と明示 |
| `S:11–34` | 初期値と引数 loop | 新2値と「flag が指定されたか」の変数を追加。空文字指定も未指定と区別し、既存引数の処理は維持 |
| `S:36–40` | run-kind の受理・export | 新種別を追加。旧種別では新 flag の指定自体を rc=2 で拒否 |
| `S:42–69` | output-parent の実在・文字集合・正規化・repo 外検査 | 既存検査を変更せず、新系列だけ explore path に対応する検査を追加。`REPO_ROOT` 解決後に位置関係を検査 |
| `S:184–188` | 共通4環境値、旧tail/exploreだけ run-kind を追加 | 既存分岐を保持し、新系列だけ run-kind と `B10_PREREGISTRATION_COMMIT` / `B10_EXPLORE_CAMPAIGN` を追加 |
| `J:186–189` | 旧3種別の受理 | 新種別を追加。新系列だけ新2環境値の必須・形式検査 |
| `J:239–251` | repo/output-root の位置検査 | 新系列だけ explore の実在・正規化・repo 外検査。scratch 作成開始の `J:260` より前に完了 |
| `J:579–594` | stage 選択と旧 driver の argv | `t2500_tail_formal_sweep` と新 driver 用配列を追加。旧3種別の argv は維持 |
| `J:595–609` | sweep timeout、extended 限定の追加解析・report | timeout と extended 限定条件を保持。新系列は追加解析・旧reportを呼ばない |
| `J:624–662` | campaign が1個、旧tail/exploreの commit 数と成果物検査 | 旧分岐の後へ新系列専用 `elif` を追加。8 distinct commit と所定 execution receipt を要求 |
| `orchestrator/tests/test_backoff_extended_sweep.py:1705,1842` | cache/worktree引数の出現回数が各2 | 新 argv を独立記述する場合は各3へ更新。後述の旧系列 argv 完全一致テストも追加し、回帰検出を保つ |
| 同 `:1714–1789` | 旧2系列の構文・文字列による配線検査 | 原則維持。分岐追加で文字列の位置・字下げが変わる場合だけ追従し、旧系列の期待値は緩めない |
| `docs/b10-backoff-static-tail-submission.md:新規` | 集団操作の専用手順なし | 新2入力を渡す投入形式、3 campaign の選び方、既存 `report` CLI の直接呼出しを記載 |
| 新規テスト2ファイル | なし | U1用 submit/集団入口テスト、U2用 job テストを分離 |

親表の主要アンカーは合っている。ただし引数 loop は実際には `13–34`、QSUB分岐は `188` まで、旧完了検査は `624–662`。`663–665` は成果物 hash の収集である。入力検査面と既存テストの出現回数 assertion が親表から抜けている。

## 新2入力の検査規則

| 入力 | 提案する規則 |
|---|---|
| `--preregistration-commit` | 新入口では完全長40桁の小文字16進文字列 `^[0-9a-f]{40}$`。空、短縮SHA、branch名、`HEAD` は拒否。投入者が選んだ固定commitをそのまま伝播 |
| `--explore-campaign` | 非空の絶対パス、実在directory、末端がsymlinkでないこと。入力文字集合を `^[A-Za-z0-9._/-]+$` に限定し、`realpath -e` で正規化 |
| 正規化後の explore | 正規化後も同じ文字集合を検査。対象repoと同一、その子孫、その祖先を拒否し、対象と祖先に `.git` がある場合も拒否 |
| 旧3種別への新 flag | 片方だけ、両方、空文字のいずれも rc=2。queue照会・receipt作成・qsubより前に拒否 |
| jobへの入力 | 新系列だけ新2環境値を検査する。旧系列で任意の同名環境変数が存在しても、新しい拒否条件を課さない |

explore の実在・位置検査は `S:42–69` の output-parent と同じ強度にする。正規化後の文字集合再検査だけは追加する。既存 output-parent は正規化前にしか検査しないため、安全文字の親symlinkからコンマ等を含む実パスへ解決され得る。新しい伝播値にはこの穴を持ち込まず、既存 output-parent の受理集合は変更しない。

commit の実在・祖先関係・事前登録bytes一致は driver の `load_preregistration()`（`orchestrator/campaign/b10_backoff_static_tail_formal.py:232–242`）に委ね、shellへ複製しない。探索campaignの admission、`t2418-explore`、correctness mode 一意性も既存の `load_explore_correctness_mode()`（同 `351–358`）が検査する。

## job の argv と完了確認

新系列の配列は次の順序にする。global option は `run` より前に置く。

```bash
"$PY" -I -B \
  "$REPO_ROOT/orchestrator/campaign/b10_backoff_static_tail_formal.py" \
  --preregistration-commit "$B10_PREREGISTRATION_COMMIT" \
  run "$WORKLOAD" \
  --explore-campaign "$B10_EXPLORE_CAMPAIGN" \
  --output-root "$OUTPUT_ROOT" \
  --cache-root "$B10_BUILD_CACHE_ROOT" \
  --ccbench-dir "$CCBENCH_WORKTREE"
```

新 driver に `--run-kind` は渡さない。既存の `timeout "$SWEEP_CAP_S"`、scratch cache、detached worktree、freeze検査をそのまま使う。

新系列の正常完了には次を要求する。

1. `$OUTPUT_ROOT/campaigns/` の directory がちょうど1個。
2. その `runs/wal.jsonl` に、`stage=="commit"` の異なる `variant` が8個あり、`None`を含まない。行数8では判定しない。
3. `<campaign>/reports/t2500-backoff-static-tail-formal-execution.json` が通常ファイルとして存在し、symlinkでない。
4. 以上が通ってから既存の `$OUTPUT_ROOT/completion.json` を書く。

8は事前登録 `:553–556,571–575,618` の境界参照1000＋tail7点に対応する。shellで測定格子や判定式を再実装しない。

| 成果物 | 実際の生成主体・位置 | jobの必須条件 |
|---|---|---|
| `…-execution.json` | driverの `run_workload():732` が内容を `767–772` で組み、`773` で `_create_json():639–642` を呼ぶ。campaignの `reports/` 配下 | 必須 |
| `…-<workload>-perf-preflight.json` | `run_workload():749` でoutput-root直下のpathを組み、`:761` で `run_campaign()` のwriter経路へ渡す | P1-bどおり追加必須にはしない |
| stemの `.json` / `.dat` / `-complete.json` | `materialize_report():645–660` が指定report出力directory直下に作成 | 集団報告側の成果物 |

既存2系列は `J:638–644,656–662` で **campaignの `reports/<旧stem>-<workload>.dat/.json`** を要求する。新系列にこの検査を流用しない。新系列では集団reportがまだ無くてもjob完了になる。

execution receipt の内容をshellで再判定する条件は追加しない。正常なdriver終了は `main():799` が全cell commit・abortedゼロを要求し、集団reportのloaderが内容を検証する。

## 集団入口と P1-a への代案

**投入scriptから独立させる責務分割には賛成だが、独立scriptの新設には反対する。**

`orchestrator/tests/test_hooks.py:4392–4418` は `tools/pegasus/` の全実行体とregistryの集合一致を要求する。新しい `.sh` は実行bitがなくても対象になる。`:4385–4389` には未登録入口の拒否テストもある。したがって、この場所への新設は親表にない登録変更を伴う。置き場所をずらして検査を回避する案も採らない。

代案は、新規の操作文書 `docs/b10-backoff-static-tail-submission.md` に、既存driverを使う集団入口を置くこと。repo rootからのargvは次とする。

```bash
python3.10 -I -B \
  orchestrator/campaign/b10_backoff_static_tail_formal.py \
  --preregistration-commit "$PREREGISTRATION_COMMIT" \
  report "$WRITE_CAMPAIGN" "$BALANCED_CAMPAIGN" "$READ_CAMPAIGN" \
  --explore-campaign "$EXPLORE_CAMPAIGN" \
  --output-root "$COHORT_REPORT_ROOT"
```

3引数は各jobのoutput-rootではなく、**その配下の実campaign directory**。globで自動選択せず、同じ投入集団の3本を明示する。新しい台帳や集団判定器は設けない。

driverの `main():789,800–803` が3入力を読み、既存のcohort検査とreport生成を行う。`invalid` はreportを残してrc=1となるため、成果物の存在をvalid判定に使わない。既存出力への再実行は `materialize_report():651` のcreate-only条件に従う。

login側での実行可否・必要資源は親が実際の入口で確認する。「文書化したのでlogin実行可能」とは扱わない。

## 既存3系列の不変性とテスト計画

既存2系列のshell配線テストは別ファイルではなく、`orchestrator/tests/test_backoff_extended_sweep.py:1714–1789` にある。`test_hooks.py` にも同scriptの登録・境界テストがある。ファイル名検索だけでなく内容検索が必要だった。

既存作法は、`subprocess.run(["bash", "-n", path])` とソース読解に加え、実ソースから抜いたshellを `bash -c` で実行する方式（同 `1848–1879`）。新テストもこれに合わせる。job全体のPBS・build・測定は起動しない。

| 所有・配置 | テスト関数名 | 検査内容／赤になる変更 |
|---|---|---|
| U1、新規 `orchestrator/tests/test_b10_backoff_grid_submit.py` | `test_submit_legacy_qsub_argv_unchanged` | 未指定extended・明示extended・旧tail・旧exploreを実行。qsub stubで全argvを記録し、可変ID等だけ正規化して比較。extendedへrun-kind追加、新2env漏出、workload順序・3回fan-out・出力名変更で赤 |
| 同 | `test_submit_formal_forwards_both_inputs_to_three_jobs` | 新2値が3本すべての `-v` に一度ずつ一致。片方欠落、値の変更、workload間の取り違えで赤 |
| 同 | `test_submit_rejects_invalid_formal_inputs_before_submission` | 欠落・空・不正commit、相対／不存在／file／symlink／repo内・祖先のexplore、空白・コンマ・`=`・改行、正規化後不安全path。rc=2とqsub未呼出しを要求 |
| 同 | `test_submit_legacy_rejects_formal_flags` | 旧3種別×片方／両方／空flag。無視・受理への変更で赤 |
| 同 | `test_submit_unknown_kind_still_rejected` | 未知の種別が通る変更で赤 |
| 同 | `test_documented_cohort_entry_reaches_report_cli` | 文書のargv骨格を既存 `main()` へ通す。runではなくreportへ3 campaign・explore・出力先が届くこと、2本／4本はargparse拒否を確認 |
| 同 | `test_cohort_entry_preserves_invalid_report_exit` | CLI下位のloader等を制御し、report生成とinvalid時rc=1を確認。存在だけで成功扱い、report迂回で赤 |
| U2、新規 `orchestrator/tests/test_b10_backoff_grid_job.py` | `test_job_legacy_commands_unchanged` | `J:579–609` の実shellを抜いてtimeout stubへ渡す。旧3系列の全呼出し列・stage・argvを比較。extendedの3呼出し、他2系列の1呼出しが変わると赤 |
| 同 | `test_job_formal_command_uses_run_cli` | 新module・global option順序・run・新2値・cache/worktreeを完全一致検査。旧driver、新系列への`--run-kind`、AA/report呼出しで赤 |
| 同 | `test_job_formal_inputs_checked_before_work` | 新系列の欠落・不正envを実検査断片へ渡し、後続到達前のrc=2を確認。旧系列に新env必須条件が漏れると赤 |
| 同 | `test_job_legacy_finalizer_contract_unchanged` | 実finalizerをfixture campaignに対して実行。旧tailは8、旧exploreは5、各旧stem2本が必要。欠測・wrong stem・root直下への誤配置・symlinkを通す変更で赤 |
| 同 | `test_job_extended_finalizer_does_not_require_tail_artifacts` | 従来の1campaign条件だけを満たすfixtureで成功。新しいcommit数・tail成果物条件が漏れると赤 |
| 同 | `test_job_formal_requires_eight_commits_and_execution_artifact` | 8distinct＋正しいreceiptのみで成功。7／9、重複行で水増し、null variant、receipt欠落・誤位置・symlink、campaign 0／2個を通す変更で赤 |
| 同 | `test_job_formal_completion_does_not_require_cohort_report` | 集団report3本なしで成功。旧 `.dat/.json` 必須条件の流入で赤 |
| 同 | `test_job_finalizer_failure_does_not_write_completion` | 上記負例で非ゼロかつ `completion.json` 不在。失敗を成功receiptへ変える変更で赤 |

submitは `subprocess.run(["bash", script, ...])` で実scriptを起動し、schedulerコマンドをテスト専用PATHのstubに置く。実qsubへの到達を防ぎ、stubが受けたargvを観測する。jobは既存作法どおり実ソース断片を `bash -c` で起動し、finalizerのheredocも実ソースから使用する。判定ロジックをテスト側へ複製しない。

親の変異事前登録は、表の「赤になる変更」を対象にする。エラーメッセージだけでなく、受理／拒否、起動argv、成果物生成の変化で検出する。

## 段5の所有分割と親による確認

| 所有者 | 所有ファイル |
|---|---|
| U1 | submit script、新規操作文書、新規 `test_b10_backoff_grid_submit.py` |
| U2 | job script、新規 `test_b10_backoff_grid_job.py`、既存 `test_backoff_extended_sweep.py` の必要な追従 |
| 変更しない | 事前登録、driver本体、既存driverテスト、hooks・registry |

この分割ならファイルの重複所有はない。既存テストにはsubmit/job双方を読む関数があるため、**編集権限はU2に一本化**する。U1は期待する差分を渡し、自分では同ファイルを変更しない。

実装前に親が確認すべきなのは、既存shellテストの基準結果、書込可能なテスト領域とstub起動方法、集団report直接入口の実行可否である。実装後は新2ファイル・既存shellテスト・既存formal driverテストを所定harnessで実行し、変異による赤を確認する。いずれも本走の投入は不要である。

追加検索時の `hooks/pegasus*`、`tools/check_pegasus*` は該当パスがなく読めなかった。必読対象外なので停止条件には該当しない。inventoryに関する所見は、実際に読めた `test_hooks.py` に基づく。

## 総括

- **プランの骨子**：新系列だけ入力検査・qsub伝播・driver起動・8commit＋execution receipt確認を追加する。集団報告は既存CLIの直接入口を文書化する。
- **親briefの訂正点**：入力検査面と既存の引数出現回数テストが変更表から欠落。独立Pegasus script新設はinventory登録変更を伴い、提示された所有範囲だけでは閉じない。
- **実装前に親が実測すべきこと**：既存テストの基準、stub付きshellテストの実行環境、report直接入口の実行可否。本段ではテスト成功も本走可能性も実測確認していない。