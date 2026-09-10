# [T-2349] A-1 driver の qstat 判定を実機 NQSV 書式へ合わせた wave (2026-09-07)

- `authority: none` / `default_effect: no-state-change` — 可変状態の正本 (worklog 末尾・現行 phase doc)
  ではない。
- 直接の前提: 失敗型 F852、`output/insights/2026-09-05_t2074-a1-pilot-run/README.md` (逐語)、
  既裁定 D805 (NQSV の状態語彙は共有 leaf 1 箇所に置く)。
- **本 wave は性能測定を 1 点も取っていない。** A-1 pilot の再投入 (attempt-0002) は依頼どおり行っていない。

## 1. 依頼と実施範囲

依頼は「`orchestrator/campaign/paper_story_a1_paired.py` の `_observe_qstat_visibility` と
`_parse_qstat_terminal` を実機 NQSV 書式へ合わせ、`tools/pegasus/dispatch_compute.py` が持つ実証済みの
`Current State` parser へ揃え、実機 `qstat -f` の逐語を fixture にした正例・負例を同じ commit に足す。
状態語の閉集合 `NQSV_QSTAT_STATES` は実書式の語へ写像する形にし、未知語の拒否は残す。Codex author 必須。
本題の実装だけ」。

実施したのは実装 1 commit と本記録である。bench・complete・materialize・sizing・再投入は行っていない。

## 2. 着手前に実測した前提

| 項目 | 値 |
|---|---|
| 固定 checkout | `.claude/worktrees/dev-wave-t2349-a1-qstat-format`、着手時 HEAD `dcf053f1c` (= 当時の local main) |
| 起動 gate | `tools/check_wave_startup.py --mode fresh --external-handoff <job dir>` rc=0 |
| 同名 wave | ListAgents・worktree 一覧・`dev-wave-jobs/` に T-2349 の同名なし |
| 編集面の重複 | `paper_story_a1_paired.py` に未 commit 差分を持つ worktree は `t1819-author` / `t1819-fix1` の 2 本のみ。mtime 2026-08-29 で 9 日 stale、稼働 session なし、hunk は `_exclusive_write` / `run_submit` 周辺で qstat 関数に触れない。重複 0 |
| 着手条件 | [T-2301] は着地済み (branch 消滅、insight commit `5e7390b7d` / `b0327dcbc`) |
| pin 閉包 (DW-O09) | driver の bytes を pin する golden は無い。`test_legacy_frozen_bytes_have_independent_literal_goldens` の literal 一覧に不在、whole-file sha256 `704e4468…` と blob oid `4b20e5b3…` の `git grep` も 0 件、pilot 事前登録は policy だけを pin |

## 3. 実機 `qstat -f` の実測 (2026-09-07 08:55 JST、Pegasus login node)

逐語 bytes は `orchestrator/tests/fixtures/paper_story_a1/` に fixture として収録した。

- 実行中 (`980043.nqsv`): `Current State           = Running`、`Previous State          = Pre-running`、
  `Queue = gen_S@nqsv (Execution Queue)`。
- 実行直前 (`980062.nqsv`): `Current State           = Pre-running`、`Previous State          = Queued`。
- 待ち (`978193.nqsv`): `Current State           = Queued`、`Previous State          = Staging`。
  これは 2026-09-05 の A-1 pilot 投入時に記録された実機逐語である。本 wave の採取時点では
  cluster 全体の待ち件数が 0 (`qstat -Q` で gen_S は RUN 25 / HLD 14 / QUE 0) だったため
  新規採取できず、repo に既に記録されていた実機観測を fixture 化した。
- **不存在 request は rc=0 で返る。** stdout は 51 bytes の 1 行
  (`Batch Request: 900001.nqsv does not exist on nqsv.` + 改行)、stderr は 0 bytes。
  この事実は依頼にも F852 にも書かれていなかった。

### 欠陥の再現と、直し先が既に在ること

同じ実バイトに対する着手前の挙動 (親が実測):

| 対象 | 結果 |
|---|---|
| A-1 の `_QSTAT_STATE_RE` | `[]` (state = None) |
| A-1 の queue 正規表現 | `None` |
| A-1 の `_qstat_mentions_request` | `True` |
| 共有 leaf `target_bound_qstat_state_result` | `RUN` / `RUN` / `QUE`、いずれも `reason='ok'` |

**state と queue が同時に外れる**のが F852 の本体である。共有 leaf は同じ bytes で正しく判定していた。
`GATE_STATE_FIELD_RE` が実バイトで一致するのは `Current State` だけで、`Previous State` と
`State Transition Time` / `State Transition Reason` には一致しない (実測)。

## 4. 段 4 の裁定 — 受理面は狭めない

段 3 の敵対レビューは「A-1 だけ `Current State` 形式に限定する surface profile を持て」と提案した。
**不採用。** D805 が同じ提案を 2 つの理由で明示的に却下している。

- 「`Current State` 専用の parser を新設する — dispatcher と語彙が食い違い」= 語彙の二重化。
  A-1 専用 profile は共有 leaf・dispatch_compute・A-2 に次ぐ 3 つ目の受理面になる。
- 「実測値だけを受理集合にする案 (`Current State ∈ {Staging, Running}`) は過学習だった。
  本走 2 回目は `Current State = Queued` で待機しており、その案なら**正常運用で fail-closed していた**」。
  本 wave の親も生きた標本は 2 件しか持たない。同じ誤りを繰り返さない。

したがって raw 受理面は共有 leaf のものをそのまま使い、**絞るのは canonical 側だけ**とした。

その他の裁定:

- receipt へ書く値は正規化後の canonical。投入直後に許すのは `QUE` / `RUN` だけ
  (`HLD` / `END` は投入直後には異常)。既存 fixture が既に `"state": "QUE"` を書いており整合する。
- reader の `NQSV_QSTAT_STATES` 12 語は変更しない。依頼の文言 (閉集合を残し未知語を拒否) と、
  `test_nqsv_qstat_state_allowlist_is_exact` の exact pin の両方に従う。
- `_parse_qstat_terminal` の受理は広げない。この機体は終了済み request を `qstat -f` に出さないので、
  `Current State = completed` 等を足すことは D805 が却下した「実形式の証拠を持たない受理枝」の新設になる。
  代わりに**実機の可視出力が終端と判定されないことを試験で固定**した。これが本 wave における
  「終端側を実機書式へ合わせる」の中身である。
- disappearance は A-2 と同じ 1 行 fullmatch + 対象 ID 束縛で締める。byte 完全一致にはしない。
- `stderr == ""` は producer-only invariant とする。A-1 の `scheduler_terminal` schema は
  `qstat_stderr` を持たず consumer は再検査できない。schema 変更は scope 外。

## 5. 親が実測で覆した子の所見 2 件

子の主張をそのまま採らず、親が独立に確かめて **refuted** にしたもの。

1. **「共有 leaf が A-1 の source closure に入らないのは provenance の欠落」** →
   closure は 9 path だが、driver が実際に import する orchestrator module は
   `buildcache` / `condition_meaning_gate` / `p2_2` / `patchharness` / `pin` / `site_policy` /
   `build_admission` / `durable_root` / `layout` / `model` / `reservation` など 10 件以上が closure 外
   (`paper_story_a1_paired.py:40-74` vs `:161-180`)。
   **closure は transitive dependency closure ではなく意図的な部分集合**であり、共有 leaf を
   外すことは新しい種類の欠落を作らない。足すには所有外の job shell の配列と、件数 pin (9 / 10) を
   持つ meta test を同時に変える必要があり、依頼の scope と実装子契約に反する。**closure は変更しない。**
2. **「job body の allocation-qstat parser が PBS-Pro 型で実機 NQSV に対応していない」** →
   `tools/pegasus/paper_story_a1_paired.sh:835-853` は `Execution Hosts(JSVNO):` の fallback と
   `Started Request Time` を持ち、実機出力
   (`Started Request Time = Mon Sep  7 08:33:11 2026`、`Execution Hosts(JSVNO):` → `bnode006(6)`)
   に一致する。**実装は対応済みで、非代表なのは test fixture だけ**である。

## 6. 段 6 で見つかり閉じた must-fix 1 件

敵対レビュー A が「execution queue 行の全体一意性が裁定より弱い」と指摘し、親が実測で real と確認した。

- 原因: `_NQSV_EXECUTION_QUEUE_RE` が候補行の識別と書式検証を兼ねていた。`@nqsv` 以外の server を持つ
  2 本目は候補として数えられず、`len(queue_matches) == 1` を満たしてしまう。
- 親の実測: 実機 RUN 全文 + `    Queue = other@other (Execution Queue)` → **受理された**。
  同 + `Queue = other@nqsv (Execution Queue)` → 拒否 (候補 2 本と数えられるため)。
- fix: 広い候補 regex で stdout 全体から数える段と、唯一候補を厳格書式で検証する段を分離した。
- fix 後の親の実測: 上記 2 つとも拒否。実機 RUN / PRR / Queued の 3 逐語は引き続き受理。

敵対レビュー B の must-fix は 0 件。

## 7. 変異 matrix — 11/11 KILLED、SURVIVED 0

- 最終: `mutation-spec-final.json` / `mutation-final-ledger.json`。
  `repo_head=a18501d6a62fb121a33695783b5323de4c8b5f7e`、baseline PASSED (rc=0)、
  `KILLED 11 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0`。
- 初回 (erratum、DW-M02 に従い消さず残す): `mutation-spec-erratum-run1.json` /
  `mutation-erratum-run1-ledger.json`。`KILLED 7 / MISMATCH 4 / SURVIVED 0`。
  **4 件の MISMATCH はいずれも gate の欠陥ではなく、親の `expected_nodes` の精度の問題**だった。

| 変異 | 初回の食い違い | 是正 |
|---|---|---|
| M2 (queue 位置) | 登録 2 件のうち `M2-queue-before-id` が落ちなかった | 同 fixture は queue 行を**前置**して 2 本にするため候補数 gate でも落ちる**冗長 gate**。DW-M03 に従い単独変異の証拠から外し、位置だけで落ちる `queue-position-before-id` (単一の queue 行を ID より前へ**移す**) だけを登録した |
| M5 (消失の ID 束縛) | 期待外に `M10-other-request` も落ちた | helper `_is_target_nqsv_disappearance` を producer と completion validator の 2 consumer が使うため。単一理由が 2 か所で現れる。両方を登録 |
| M6 (終端 signature) | 期待外に `M5-other-request` も落ちた | producer の guard 撤去により両負例が通過するため。両方を登録 |
| M8 (共有 parser を旧実装へ) | 期待外に `test_submit_runs_real_qsub_call_from_repository_root` も落ちた | 同テストの**入力 fixture を実機 RUN 逐語へ差し替えたため**。差し替えが実機代表性を持たせたことの証拠として登録に含めた |

## 7.1 fix 後の焦点再レビューと、その所見の決着 (DW-O16)

逐語は `verbatim/s6-rereview.md`。対応表は「レビュー A 所見 1 = closed、既存テストの assertion 変更なし、
規律 2 への混入なし、変更禁止 path に diff なし」とし、**レビュー A 所見 8 (M1〜M10 の kill 対応) を
regressed** と判定した。理由は「fix で marker 要求が候補 regex と厳格 regex の 2 箇所に重複したため、
M4 は単一箇所の変異では殺せない」。

**この指摘は正しく、かつ本 wave では既に処置済みである。** 親は fix 直後の再 anchor 時点で M4 を
`category: both-layers` の複合変異 (両 regex の marker 要求を同時に外す) へ変更し、DW-M04 が要求する
kill 期待を本走前に登録していた。最終台帳で M4 は KILLED (期待一致) である。
再レビュー子には裁定 §8 の**旧登録**しか射影していなかったため、更新後の spec を見ていない。
**親の prompt の射影漏れであり、実装の欠陥ではない。**

同じ再レビューは M2 の kill 元を `M2-queue-before-id` と静的に推定しているが、実走では
この node は落ちない (§7 の表)。**静的推定より実走の観測が正しい**例である。

## 8. 親が実走した検査

- 焦点走 (fix 後): `test_paper_story_a1_job_contract.py` + `test_paper_story_a1_paired.py` +
  `test_pegasus_dispatch_compute.py` + `test_paper_story_a2_certification.py` = **794 passed**、rc=0。
- 親の正例・負例 (実機 raw bytes を production 関数へ通す):
  RUN → `state=RUN, queue=gen_S`、PRR → `state=RUN`、Queued → `state=QUE`、
  不存在 → 拒否、実機 RUN を終端観測へ → `visible scheduler request is not terminal` で拒否。
- `git diff --check` rc=0、`python3 tools/check_ai_provenance.py` (全史) rc=0 / 8358 件・新規違反なし。
- **実装子と fix 子は pytest を実走できていない** (`tools/run_tests.py` が
  `NQSconnect: [API EACCTAUTH] Unknown user-id` で rc=16)。上記は親の実走結果である。

## 8.1 受入全走で 1 件赤 — 行番号 pin の閉包漏れ (親の手順ミス)

初回の受入全走は **21044 passed / 1 failed** で rc=70 (`reason=child-verdict`) になった。
落ちたのは
`orchestrator/tests/test_ccbench_spawn_sites.py::test_deferred_gate_ledger_is_exact_and_every_entry_names_a_live_sink`。

- 原因: 同 file の deferred gate 台帳が `paper_story_a1_paired.py` の
  `<module>.run_measurement` 内 campaign sink を **行番号 7103 で pin** していた。本 wave の driver 変更は
  net +43 行で、同じ sink (`summary = run_campaign(`) は 7146 行へ動いた。sink 自体は同一である。
- **本 wave の変更に帰属する赤であり、非帰属赤ではない。**
- **なぜ着手前の DW-O09 pin 閉包で拾えなかったか:** `git grep 'paper_story_a1_paired\.py'` は
  この参照を含んでいたが、親が出力を `| head -40` で打ち切っており、
  `acceptance_duration_ledger.json` の多数 entry に押し出されて視野に入らなかった。
  **件数を確かめずに検索結果を切ったこと**が原因である。path 検索そのものは正しかった。
- 対処: Codex `role=author` が台帳 literal と同テストの期待集合の 2 箇所を 7146 へ更新した
  (親が別に実測した値と一致)。行番号以外 (owner / reason / sink_kind / sink_scope / 他 entry) は
  変更していない。焦点走 `test_ccbench_spawn_sites.py` 44 passed。その後に受入を取り直した。

## 9. 本 wave が主張しないこと

**「A-1 が bench へ到達する」とは主張しない。** 閉じたのは F852 の投入 blocker と、
終端の消失判定の過剰受理だけである。3 job fan-out、group receipt 待機、bench barrier、
reservation、compute runtime は実機未通過のまま残る。差の符号・大きさについては何も述べない。

## 10. 申し送り (本 wave では実装しない)

1. A-1 の allocation-qstat **テスト fixture** が PBS-Pro 型 (`exec_host = compute01`)。
   実装は実機対応済みなので機能欠陥ではないが、F852 と同じ「テスト代表性」の型である。
2. reader の 12 語を実在 receipt の棚卸しに基づいて縮小するか (受理集合の縮小を伴う別変更単位)。
3. submission / completion receipt へ qstat の raw stdout / stderr / rc を保存する schema migration。
   これが無い限り `stderr == ""` は consumer 側で再検査できない。
4. fix 着地後の attempt-0002 投入は fresh wave で行う。投入元 checkout は記録を書かない別 worktree にする。

## 10.1 段 8 (skill 自己改善) — 候補 3 件、本 wave では実装しない

いずれも本 wave で実測した手順の欠落だが、**docs の byte 予算が塞いでいる**ため実装せず報告する。
`DEV_WAVE_L2_SECTION_BYTES_MAX = 1000` に対し `DW-C01` は現に 996 bytes で、残りは 4 bytes しかない。
収めるには既存の安全義務を含む本文を書き換える必要があり、自己改善契約が禁じる
「予算のために安全義務を削除・弱化する」に触れる恐れがある。依頼の scope (本題の実装だけ) にも入らない。

1. **隔離 worktree の guard が拒否する定型は `DW-C01` の記載 (detach) より広い。** 本 wave の実測で
   `nohup setsid bash ...` の直叩き、`python3 - <<PY` heredoc、変数を含む `sed` / `python3 -c`、
   backtick を含む長い heredoc が拒否された。とくに **`cd` で他 worktree へ入ると、以後すべての
   Bash が拒否されて `cd` で戻ることもできなくなる** (復帰は EnterWorktree に自分の worktree の
   path を渡す)。これは 1 回踏むと session が進めなくなる型である。
2. **子 prompt の `## 総括` は見出し literal を厳密に指定しないと全損する。** `DW-O01` は
   「prompt に `## 総括` 必須」と書くが、親が「最後に `## 総括` 節を置き、推奨と未解決の論点を書く」と
   説明形式で渡したところ、子は `## 推奨と未解決の論点` という別名見出しを出し `f43_fragment` で
   不採用になった (段 2 初回、約 10 分と 1 回分の model call が失われた)。
3. **login node の高負荷で launcher の authority snapshot 取得が git timeout し `launcher_error` になる。**
   段 3 の初回 2 本は load 144 のとき `git show` / `git rev-parse` が 10 秒で timeout し rc=2。
   子は完走し `validator_rc=0`、`authority_snapshot` も receipt に載っていたが、`launcher_rc=2` の
   ため不採用。負荷が 68 まで下がってから投げ直して成功した。infra 起因の再投入導線が要るか。

## 11. 還元判断

CCBench 本体への還元候補は含まない。
