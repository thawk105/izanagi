# output/task-runs — AI 開発作業の統計記録 (task-run 台帳)

**これは開発プロセスの観測台帳であり、campaign の correctness / fitness / benchmark の証拠 (proof
chain) ではない。** 全 task.json に `"authority": "development-observation-not-evidence"` を必須で
埋め込み、campaign WAL・`campaign.lock`・凍結 spec とはいかなる形でも接続しない (D66。D13 の二軸 =
実験証拠の置き場とは直交する開発運用 namespace)。

- 目的: AI エージェントによる開発 task の時間・テスト・レビュー・手戻り・token を追記型で記録し、
  遅延原因の監査と作業ループ改善の素材にする (handoff 2026-07-19 の設計、worklog 裁定)
- 記録値は観察データであり、モデルの優劣・作業者評価へ単独利用しない。「削れる工程」の自動推奨は
  report に含めない — 削減判断は必ずユーザー裁定へ回す (正しさ gate・negative control・独立 review の
  削減は CLAUDE.md 絶対規律 2/3 に反するため、そもそも候補にしない)

## pilot 契約 (v1)

- 規模: **10 task run または 14 日** の早い方で新規 start を拒否 (pilot.json の create-only manifest が
  authority)。全面強制はしない — 対象はクラス 2/3 の実装・統合セッション + 長時間 class-1 監査の opt-in
- 起動導線: worklog 次の一手の pilot 手順ポインタ (CLAUDE.md には配線しない。pilot 実証後にユーザー提案)
- 自動記録は test_run のみ (`tools/run_tests.py` の opt-in 配線 + `tools/task_run_check.py` の
  allowlist check wrapper)。stage/agent/wait/finding/commit/rework は親セッションが CLI で記録する
- git 追跡: `<task-run-id>/task.json`・`events.jsonl`・`reports/`・`pilot.json` を追跡する。**git 履歴に
  入った記録は事実上削除できない** — だから privacy 制約 (下記) は保存前に schema で機械強制する
- 保持: pilot 世代は最終 report 生成後に凍結 (新規 start 拒否)。次 pilot の root 世代命名はその時に裁定

## レイアウト

```
output/task-runs/
├── README.md            この文書 (詳細正本)
├── pilot.json           pilot manifest (create-only: 開始時刻・cap)
├── <task-run-id>/       YYYYMMDD-<slug>-<8hex> (主キー。commit SHA に依存しない)
│   ├── task.json        create-only。終了情報で書き換えない (終了は task_end event)
│   └── events.jsonl     append-only の event stream (連番 seq、tz 付き ISO 8601)
└── reports/             集計 report (atomic publish、上書き禁止)
```

## CLI (正本 = `tools/task_run.py --help`)

```
python3 tools/task_run.py init-pilot                         # pilot manifest 生成 (最初に 1 回)
python3 tools/task_run.py selfcheck                          # 実 FS canary (pilot 開始前必須、下記の限界参照)
python3 tools/task_run.py start --slug <slug> --objective <一行要約> --task-class {1,2,3} --task-kind <enum>
python3 tools/task_run.py event <id> {stage_start,stage_end,agent_run,test_run,wait,finding_summary,commit,rework} ...
python3 tools/task_run.py finish <id> --outcome {completed,blocked,abandoned,interrupted}
python3 tools/task_run.py validate [--all]                   # fail-closed 検査 (root 不在・未知 entry も赤)
IZANAGI_TASK_RUN_ID=<id> python3 tools/run_tests.py ...      # テスト実行の自動記録 (opt-in)
python3 tools/task_run_check.py {docs-check,provenance-check,static-check}   # 固定 argv の check 記録
python3 tools/task_run_report.py output/task-runs output/task-runs/reports/<period>_task-efficiency.md
                                                             # 集計 report 生成 (--diagnostic は破損時の診断、
                                                             # --final は publish と同時に pilot を凍結)
```

## 記録契約の要点 (機械強制の根拠は schema_v1.json + ledger.py)

- **writer が決める**: seq (1 始まり連番、gap も拒否)・timestamp (UTC、system clock)・event_id
  (16 hex、run 内一意)・measurement_source。caller はこれらを指定できない (自己申告の恒真化遮断)。
  強い source (`wrapper-observed`/`git-observed`/`monotonic-clock`) を名乗れるのは wrapper 専用経路のみ
- **git 実測**: base_commit は start が `git rev-parse HEAD` を実行して取得。commit event は
  `git cat-file -e` で実在確認してから記録
- **token 4 区分** (input/output/cached/total): 非開示は null + `not-exposed` (0 にしない)。概算は v1
  禁止。非 null ペアに cached≤input・total=input+output 等を強制。集計は (product, model) cohort 内のみ
- **privacy**: 自由文は objective (単一行 ≤240 字、`://` 禁止) のみ。他の全 string field は enum または
  safe slug。prompt 本文・session URL・raw command・selector/node 名・料金は記録禁止 (schema が拒否)
- **fail-open / fail-closed の境界**: 記録の失敗は作業本体を止めない (run_tests は child rc を絶対に
  置換しない)。読む側 (validate / report) は fail-closed — 壊れた台帳は必ず赤くする。report は damaged
  run が 1 件でもあれば既定で生成拒否 (`--diagnostic` で破損一覧つき「不完全」診断 report のみ可)

## 既知の限界 (v1 で明示的に受け入れたもの)

- **append-only は writer 局所の crash-consistency 契約であり、改竄検出ではない** (外部 anchor は git
  履歴に委ねる。hash chain は持たない)
- 台帳へ書けなかった event は台帳内から検出できない — report の欠測率は「観測可能な下限」である。
  記録実施の有無自体が task 間で非ランダムに偏り得る
- 台帳 root は checkout (worktree) 局所。並行 worktree では別台帳になり、merge 後の union で cap 超過が
  起き得る (report が検出・開示する)
- 時間分解 (lead / Σstage / Σwait / unclassified) は排他的分解ではない。負の unclassified は
  inconsistency として flag され、率は null になる
- tmpfs 上のテスト green は Lustre 等の実 FS の flock/fsync 保証にならない — pilot 開始前に実 root で
  `selfcheck` を実行する
- `recording_duration_s` は append 前処理 (root/pilot 読取・既存 stream 検証・git 確認・serialize・
  lock 待ち) の実測で、最終 write/fsync 以降を含まない (計装 overhead としては下限側の近似)

## 母集団の区別 (混同しない)

- worklog: task_run_id・異常・裁定のみを載せる (集約値は report 側)
- D53 `AI-Agent:` trailer: **採用に実質寄与した構成のみ**。台帳の agent_run event は failed /
  cancelled / 不採用も数える — 両者の母集団は一致しない (どちらかからどちらかを再構成しない)
- 開発 task-run 台帳と campaign WAL: validator も置き場も別。campaign WAL の「末尾壊れ行を捨てて
  読む」contract はこの台帳に存在しない (truncate は damaged)

## report の読み方

report header に主張範囲 (記録された event のみ / 自動観測は pytest + check wrapper / 他は手動記録) を
明記する。task_kind 層内でのみ比較し、層に completed run が 1 件しかなければ比較 KPI を出さない。
task_end のない run は右打切りの別表 (下限値) にのみ載る。red→green は pytest rc 1 のみを red と数え、
rc 2-5 等は infra として別掲する。published run 数と pilot cap の関係 (worktree union による超過を含む)
は通常・診断どちらの report でも必ず表示する。10 run または 14 日到達時に `--final` で最終 report を
生成し (pilot 凍結)、pilot の継続・縮小・撤去 (計装 overhead に見合う便益がないなら撤去) をユーザー
裁定へ回す。

## 欠測率の式 (コード正本 = `tools/task_runs/aggregate.py` の `RATE_DEFINITIONS`。report 本文にも同表を埋め込む)

| rate | 適用集合 | 分子 | 分母 |
|---|---|---|---|
| task_end_missing | 同一 task_kind 層の validated run | task_end の無い run | 層内 validated run |
| lead_unclassified | lead 正値かつ分解が整合する completed run | lead − Σstage − Σwait | lead_time_s |
| stage_id_missing | run 内の agent_run/test_run/finding_summary/rework | stage_id が null の該当 event | 該当 event 数 |
| test_count_missing | run 内 test_run の count 4 field | null の count field | test_run 数 × 4 |
| token_field_missing | run 内 agent_run の token 4 field | null の token field | agent_run 数 × 4 |
| trigger_unspecified | run 内の test_run | trigger=unspecified の test_run | test_run 数 |
| source_not_exposed | run 内の not-applicable を除く source field | not-exposed の field | 該当 source field 数 |
| finding_effective | real + refuted finding | real | real + refuted (0 なら null) |
| recording_overhead_coverage | 記録された event | recording_duration_s を持つ event | 記録された event 数 |

分母 0 は必ず null (0% と表示しない)。これらは「台帳内で観測可能な欠測率の下限」である (書けなかった
event 自体は数えられない)。
