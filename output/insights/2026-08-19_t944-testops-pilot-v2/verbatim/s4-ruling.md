# 段4 裁定 — dev-wave-t944-testops-pilot

親裁定。両レンズとも NO-GO (レンズA: blocker7・must-fix8、レンズB: blocker4・must-fix5)。
以下で全所見を real/refuted・scope 内/外に裁定し、plan v2 (`out/s2-plan-v2.md`) への修正を確定する
(以下 **plan v3** と呼ぶ = plan v2 + 本裁定の修正)。段5 はこの裁定を権威として進む。

## 0. 裁定前に確定した外部事実

- **`renameat2(RENAME_NOREPLACE)` は `/work` で使えない (EINVAL)。** `docs/pegasus-runbook.md:296-298`
  が 2026-08-04 実測済みで明記し、`docs/failures.md` F22 が独立に再発記録している。plan v2 の
  B2 staging publish (`no-replace rename`) はこのままでは動かない。既存 precedent (calibrator) は
  `os.mkdir` による排他予約 + `os.rename` を使う。plan v3 はこれに従う。
- **`/work` 配下は compute node から実体 path で見えると実測済み。** `docs/pegasus-runbook.md:267-268`。
  cross-node の **path 可視性**は既に確認済みであり、レンズB B2 が要求する「未証明」は撤回対象。
  未証明として残るのは、単一 job 内での write-then-read の即時一貫性と flock/fsync 保証であり、
  これは既存 `selfcheck` (D66 設計) が本来担う範囲。

## 1. 所見の裁定

### real かつ scope 内 (plan v3 で閉じる)

| # | 出典 | 要旨 | plan v3 での扱い |
|---|---|---|---|
| R-TOCTOU | レンズA B1 | namespace 検査後の create/open が TOCTOU | 祖先 component も含め `openat`/`mkdirat` を検査済み parent fd から行う。`git-common-dir` が相対値なら abs 化してから使う |
| R-RENAME | レンズB B1 (裏取り済み) | `renameat2(NOREPLACE)` 不使用 | `os.mkdir` 排他予約 + `os.rename` (calibrator precedent) |
| R-STAGING | レンズB B1 | staging crash が永久停止を作る | 各境界 (mkdir/init/fsync/rename) で kill 後、次回起動時に「pilot bytes 検証 → 正常なら rename 完了、異常なら quarantine (`.staging.damaged-<ts>` へ改名し series entry から除外、削除はしない) → 到達不能なら diagnostic」の3分岐にする。無限リトライにしない |
| R-CLOSEORDER | レンズA B2 | damaged/unknown と pilot-closed の優先順位不明 | `validate_root()` を closure 判定より**先**に呼ぶ。damaged/unknown/incomplete は無条件で `series-invalid` diagnostic とし `PilotClosedError` に変換しない。final marker 自体も内容検証 (schema valid か) してから信用する |
| R-INCOMPLETE | レンズA B2 | task marker 前 crash の `incomplete` run が cap 判定で扱われない | `incomplete` (task.json はあるが正常終了イベント欠如) を series-invalid の一種として扱い、cap 判定からは除外せず publish 済みとして数える (B1 と同じ理由: cap 回避に使われうるため) |
| R-EXPLICIT | レンズA B3/B7 | explicit-only 生成・repo_root が Python の呼出し規約止まり | 「オペーク capability」は本 wave の脅威モデル (D205、対象は将来の実装ミス再発防止であり悪意ある内部者対策ではない) には過剰。**call-graph meta-test** (grep/AST ベース、既存 pin 慣習と同型) で `open_next_generation` の呼び出し元が CLI 手動 handler 1 箇所だけであること、`start_run(repo_root=...)` の呼び出し元が `generation.py` 内の automatic recorder 1 箇所だけであることを機械的に pin する |
| R-SERIESREADER | レンズA B4 | series reader が既存 consumer (report/aggregate/CLI) に未結線 | `validate-series` を新設するだけでなく、automatic path の generation open 判定と CLI `validate --all` の両方が内部で `validate_series()` を経由するよう配線する。個別 generation の report 生成は残すが、report header に「series 全体の健全性は別途 `validate-series` で確認」と明記し、series-valid を自称しないようにする |
| R-SIGNAL-WIDE | レンズA B5、レンズB M3 | signal 監査範囲が bootstrap/record/finish の4点だけでは不足 | 監査対象を admission・queue fallback・dispatcher setup・scope bind/release・sidecar read・record append・finish・cleanup の全 call site に拡張する。`dispatch_compute.py` が `BaseException` を捕捉している箇所は、記録処理に閉じた範囲だけ `Exception` に狭める (dispatcher 自身の既存 infra 契約には触れない — 触れると受理集合が変わり scope 外) |
| R-ORDER | レンズA B6、レンズB B4 (独立2件) | preflight と recording 開始の順序が経路依存で不一致。現行 main の login local bounded scope は preflight より**先**に `_launch_local_scope()` を起動する | 「session 初期化は preflight 後」という一律ルールを撤回する。経路ごとに**現在の実際の gate/preflight/起動順**を先に truth-table 化し (段5 実装前の静的検査として必須)、各経路で「child が実際に起動される直前」に lazy session を置く。経路間で挿入点が異なってよい (むしろ挿入点を揃えることが目的ではなく、「child 起動 = 記録対象」という不変条件を揃えることが目的) |
| R-LEASE | レンズA M1、レンズB B2 (残り) | sidecar lease / dispatch transport が Unit A/B interface に無い | `AutomaticRun` に `sidecar_path: Path \| None` を追加する。生成は Unit A (`generation.py` 配下の transport 一時領域)、消費・転送は Unit B。cross-node の実証は §0 の通り path 可視性は確認済み、即時一貫性は段6 で**実 dispatch (mock でない)** テストにより検証する (下記 §3) |
| R-MULTIEVENT | レンズA M2 | 同一session・一度だけfinishがAPIに無い | `AutomaticRun` に scope 結果と finish 済みフラグを持たせるのではなく、**B4 の scope を診断のみへ縮小したため (下記 R-B4SCOPE) 本項は大幅に単純化される**。fallback 後も `finish_automatic_test_run()` は一度だけ呼ぶという契約だけを維持すればよい |
| R-PRIVACY-WIDE | レンズA M3 | objective/suite_id blocklist が不十分、Python検査とJSON Schemaの同期未検証 | `/`・`\`・`::`・改行に加え `.py`・`.pyc`・既知 test prefix (`test_`) を含む語を拒否する追加検査を入れる。両 validator (schema.py と schema_v1.json) を同じ pattern 文字列から生成するか、双方に対する同一 negative fixture セットで固定する |
| R-DIAG-LEAK | レンズA M4 | 固定diagnostic以外 (CLI raw exception, dispatch receipt/request) に漏洩経路 | **task-run が新設する範囲 (task.json/events.jsonl/sidecar/新設1行diagnostic) に限り** raw exception text を diagnostic code へ射影する。CLI の raw exception 表示は task-run 新設面が使う経路にだけ適用し、CLI 全体の既存エラー表示規約は変更しない (scope 外、下記2章)。dispatch request/receipt の raw argv/repo path は **pre-existing の dispatch 汎用契約であり本 wave が新設した漏洩ではない** — 新設する sidecar/auto-off marker が dispatch request/receipt へ**追加で**argv/path を持ち込まないことだけを検査する |
| R-TRIGGER | レンズA M5 | P3 (既存 `IZANAGI_TEST_TRIGGER` を使う) と M3 (automatic は unspecified 固定) が矛盾 | **automatic 経路は継承された環境値の有無に関わらず常に `unspecified`。** manual ID 経路 (既存の `IZANAGI_TASK_RUN_ID` 明示) だけが `IZANAGI_TEST_TRIGGER` を読む。理由: automatic run は session 単位の意図を持たないため、親 session が manual 用に設定した trigger を誤って継承させない |
| R-LOCKSCOPE | レンズA M6 | series lock の timeout が既存 root flock (blocking) を覆わない | `init_pilot()`/`start_run()` の root flock も同じ bounded-wait 契約に揃える (timeout → `recording-unavailable:series-lock-timeout` 系の診断)。manual CLI 経路の blocking 挙動は変更しない (scope 外、manual は人間が待つ想定) |
| R-CLIREJECT | レンズB M2 | managed generation の CLI 拒否条件が未定義 | 「managed」の判定は **realpath 比較**で行う: `--root` の realpath が series base の realpath 配下 (symlink 解決後) にあれば managed とし拒否する。判定はどの byte も作る前に行う。無関係な同名 directory は series base 配下でなければ managed 扱いしない |
| R-COVERAGE | レンズB M4 | 被覆の分母・event 定義があいまい | R-B4SCOPE (下記) により non-CHILD_RC outcome は task_run event を作らず診断のみになるため、「infra event と test event の混同」自体が構造的に起きなくなる。README は「event は child が実際に起動した wrapper invocation にのみ存在する」で統一する |
| R-ESTIMATE | レンズA M8、レンズB M5 | 見積りに未計上項目がある | 下記 §4 で再見積りする |

### real だが判断で scope 縮小 (最重要)

- **R-B4SCOPE (レンズB B3 blocker) — `task-run/v1` を維持する以上、B4 (全 outcome を task_run event
  として記録する) は成立しない。** schema に `route`/`outcome`/`child_started` field を足すことは
  schema 世代を増やすか既存 exact-key 契約を破ることになり、brief の不変条件・D66 の設計判断に反する。
  **裁定: B4 を「診断のみ」へ縮小する。** `CHILD_RC` 以外の outcome (`CAP_OOM`・timeout・
  `DISPATCH_INFRA`・setup failure) では task_run event を作らず、固定 diagnostic
  (`recording-unavailable:scope-outcome-<code>` 系) を 1 行出すだけにする。「pytest child が
  実際に起動していない」ケースを test_run として偽装しない、という A10/B5 の regression 防止にも
  直接資する。旧 B4 の「全 outcome 記録」という closure 目標は、この縮小形で達成したとみなす
  (README にその旨明記)。これにより M2 (同一session複雑化) の必要も消え、production 見積りが
  縮む。

### refuted

なし。両レンズの所見はすべて real (方向性の当否はあるが指摘自体は成立) と判定した。

### real だが scope 外 (裁定候補として記録するが実装しない)

- **レンズA 候補1 (Q1明示の実体) — 採用済み (R-EXPLICIT で call-graph meta-test を採用)。** opaque
  token/manual command という強い形は不採用。理由は上記 R-EXPLICIT。ユーザー裁定を新たに要しない
  (D341 は「以後の実装は制約下で別waveが担う」と明記しており、実装強度の選択は本 wave の裁量内)。
- **レンズB R3 (D205/D220に合わせた縮小案) — 部分採用。** R-B4SCOPE で最大の縮小レバーを引いたため、
  series reader・managed CLI write policy・sidecar lease を追加で削る必要はないと判断する
  (これらは元の insight の A5/M2/B3 を閉じるために必須で、D341 が既に「blocker 9・must-fix 11 を
  閉じる」ことを制約として確定させている)。

## 2. 不変条件の追補 (brief からの変更点)

- brief は「schema世代を増やさない」としていたが、根拠が曖昧だった。**本裁定で明示的に確定する:**
  `task-run/v1` の exact-key 契約 (task.json/events.jsonl の field 集合) を一切変更しない。
  違反する変更は実装せず親へ差し戻す。
- CLI の一般的なエラー表示規約 (task-run 以外の既存コマンド) は本 wave の scope 外。privacy 強化は
  task-run が新設する経路にだけ適用する。
- dispatch の汎用 request/receipt format (既存の argv/repo_root 保持) は本 wave が新設した漏洩では
  ないため是正しない。本 wave が追加する field (sidecar path、auto-off marker) だけを privacy 検査
  対象にする。

## 3. 段5 実装契約への反映

Unit 分割は plan v2 の P1 (条件付き採用形) を維持する。

- **Unit A**: `tools/task_runs/{ledger,generation,schema,cli,__init__}.py` +
  `tools/task_runs/schema_v1.json` + `orchestrator/tests/test_task_run_ledger.py` + 新規
  `orchestrator/tests/test_task_run_generation.py`。R-TOCTOU/R-RENAME/R-STAGING/R-CLOSEORDER/
  R-INCOMPLETE/R-EXPLICIT/R-SERIESREADER/R-PRIVACY-WIDE/R-LOCKSCOPE/R-CLIREJECT を閉じる。
- **Unit B**: `tools/run_tests.py` + `tools/pegasus/dispatch_compute.py` (sidecar transport 部分のみ) +
  `orchestrator/tests/test_run_tests_task_run.py` + 新規
  `orchestrator/tests/test_run_tests_testops_observation.py` + `orchestrator/tests/test_pegasus_dispatch_compute.py` +
  `output/task-runs/README.md`。R-SIGNAL-WIDE/R-ORDER/R-LEASE/R-MULTIEVENT(簡素化済)/R-DIAG-LEAK/
  R-TRIGGER/R-B4SCOPE/R-COVERAGE を閉じる。Unit A 完了後、所有パス限定 patch を適用してから投入する
  (`DW-S05-A`)。

Unit A の実装子には、着手前に **経路別 gate/preflight/child起動順の truth-table を先に静的に書き出す**
ことを明示的に指示する (R-ORDER)。これを飛ばして「preflight後」と仮定した実装をしない。

段6 の受入テストに、`tools/run_tests.py --force-dispatch` を使った **実 dispatch (mock でない)** の
sidecar 往復確認テストを最低1本含めることを実装契約に追加する (R-LEASE の cross-node 実証)。
これは `DW-G01` の生死実験に相当する検証を、実コードが存在する段6 まで遅らせる判断であり、
理由は「今 probe を作っても後で実コードの経路が変わり書き直しになる」ため。

## 4. 見積り再算定

plan v2: production 455–663 行 (+README 35–55)。本裁定の影響:

- **削減方向**: R-B4SCOPE (multi-event lifecycle・route/outcome表現の撤去) で `run_tests.py` 側が
  30–50 行程度減る見込み。
- **増加方向**: R-TOCTOU (fd chain)・R-STAGING (quarantine分岐)・R-SIGNAL-WIDE (call site 8箇所)・
  R-CLIREJECT (realpath判定)・R-EXPLICIT (meta-test 2本)・R-PRIVACY-WIDE (denylist拡張+同期検査)
  で `generation.py`/`ledger.py`/`cli.py`/meta-test が計 60–100 行程度増える見込み。

**改訂見積り: production 480–700 行 (+README 35–55、+meta-test 20–40)。** brief の 320–505 行より
大きいが D220 が不採用にした 645–816 行 (別機能) と同程度〜やや下回る水準。行数を理由に安全面を
削らない、という plan v2 自身の姿勢 (M5) を継承する。実測は段5 実装後に `git diff --stat` で確定する。

## 5. 変異事前登録方針 (DW-M01)

コードが未着手のため、B-057 形式の bytes-exact spec は段5 実装直後に確定する (DW-M07 の
「fix後の最終commitでanchorを再検証」と同型で、まず段5 直後に一次登録し、段6 fix 後に再検証する)。
本裁定時点では、plan v2 の新規・更新テスト表 (約40 nodeid、各々「殺す変異」列を持つ) を**基礎登録**
として確定し、以下を追補する。

- R-RENAME: `os.mkdir`排他予約を`renameat2`相当へ戻す変異 → `test_staging_generation_recovers_after_crash_between_init_and_publish`が検出
- R-CLOSEORDER: `validate_root()`呼出し順を closure判定の後へ入れ替える変異 → 新規
  `test_damaged_generation_is_checked_before_closure_reason`
- R-B4SCOPE: non-CHILD_RC outcomeでtask_run eventを作ってしまう変異 → 既存
  `test_bounded_scope_records_all_outcomes`を「eventでなくdiagnosticのみ」を検査する形へ改名・改修
- R-EXPLICIT: call-graph meta-testそのものが変異対象 (自己言及にしない) — 呼び出し元を1箇所追加する
  変異を新規 production コードへ注入して赤になることを段6のfix後に確認する
- R-SIGNAL-WIDE: admission/queue fallback/dispatcher setupでのKBI握り潰し変異 → 新規
  `test_recording_signal_is_re_raised[admission]` 等をtable 7.2へ追加

段6 で親が変異 matrix を実走し、KILLED/SURVIVED/MISMATCH を worklog へ記録する。

## 総括

plan v2 は骨格として維持しつつ、20 所見のうち **1 件 (B4) は scope を診断のみへ縮小**、残り全件は
real として plan v3 (本裁定の修正込み) で閉じる。refuted はゼロ。段5 実装へ進む。
