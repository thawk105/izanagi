---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1175-cell-admission-report
seq: 1
title: cell admission が失敗しても診断可能な partial report が残るようにした — 免除の根拠を自己申告から独立再導出へ移した (コード + テスト + docs、branch worktree-dev-wave-t1175-cell-admission-report、変異 matrix = 10/10 KILLED)
---

## 本文

**閉じたもの・閉じなかったものを先に書く。** 本 wave が閉じるのは
`_finalize_build_cell_admission` の**契約上の `AutonomousTrialError`** が
`report.json` を消す経路だけである。`_write_json_atomic` 自身の I/O 失敗、
journal の永続化失敗、`KeyError` 等の予期しない例外は**従来どおり report を残さない**。
「admission 失敗一般を閉じた」と読める記述をしてはならない。

- **親の実測が前提を裏付けた。** [T-1112] の 2 走
  (`live-abc-g1-20260816a` / `...b`) はいずれも `report.json` が 1 バイトも無く、
  `attempts.jsonl` に `run-finish` 事象も無かった。走 a は coder の JSON parse 失敗で
  `role-invalid` (supervisor-error 事象 0 件)、走 b は `KeyError: 'build_start'` 経由の
  supervisor-error である。**同じ関数の別々の呼び出し点**から同じ型が出ていた。
- **親 brief の関門数え上げ (4 つ) は過小だった。** 段 3 の 2 レンズが独立に、
  pending critic 検査・workload coverage・generation accounting・status projection・
  journal hash 再検査・writer 自身を追加で挙げた。F332 の恒久対応が 6 面同時だったのと同型で、
  **1 面だけ直して閉じたと見なす型がこの同じ関数で 2 度目**である。
- **段 3 の敵対 2 レンズはいずれも NO-GO**、段 6 の敵対 2 レンズもいずれも NO-GO だった。
  段 3 の決定打は「failure decision が自己申告で証拠に束縛されないため、
  **admission 成功後に positive decision を failure 形へ置換する変異が生存し
  Layer 3 chain 検査を不正に免除できる**」である。親はこれを real と裁定し、
  免除の根拠を**独立再導出**へ移した ({{D:cell-admission-failure-report}})。
- **親の DW-G03 「独立 2 例」主張は撤回した。** `docs/dev-wave/core.md` の族一般化は
  異なる producer/consumer での 2 件を要求するが、走 a と走 b は同一 consumer の
  2 呼び出し点にすぎない。台帳には「同一 consumer の正常復帰側と supervisor-error 側を
  確認した」までしか書かない。段 3 レンズ B の指摘による訂正である。
- **親が段 4 裁定を段 6 で 1 件改裁定した。** 裁定 2-3 は「failure 経路で accounting event を
  追加 append しない」と書いたが、実装は pending critic の未確定 accounting を
  `partial-generation` で確定していた。段 6 の 2 レンズが独立に食い違いを指摘した。
  親がコードで裏を取ると、`_pending_critics` は harness 成功時にだけ push され、
  その時 `active_accounting` が pending へ移って `finally` が append しなくなるため、
  **確定しなければ accounting bijection が落ちて report は publish されない**。
  「一切 append しない」と読むと harness 成功後の admission 失敗だけが救えなくなる。
  裁定へ addendum を書き、代償として disposition の `count` が指す最終 generation の
  accounting へ `partial-generation` 完全一致を要求する拘束を足した。
  **走 a・走 b はいずれも pending を持たないため、この経路は一度も回らない。**
- **正例 (positive control) が実際に赤を出した。** 段 6 の敵対レビュー B が
  「事前登録した正常 3 workload build の正例が無い」を real で挙げ、fix 第 1 巡が追加したところ
  **親の実測で 1 failed** になった。真因は正例 fixture が campaign を git 管理外の `tmp_path` へ
  置いたため renderer の HEAD 取得が失敗し、cell が failure 扱いになっていたことで、
  **production は正しく fail-closed に倒れていた** (新設 gate がこの不整合を捕まえた)。
  fix 第 2 巡が `_git_head` seam にだけ固定値を与えて閉じた。renderer と chain は実処理のまま。
- **段 6 の焦点再レビューが残存穴を 1 件出した。** verifier の campaignless fallback 述語が
  disposition の `count in {0, 1}` をそのまま許すのに、producer の fallback は空 cell 起点で
  破棄件数が必ず 0 だった。producer が作れない形が chain 単体の受理集合に入っていた。
  fix 第 3 巡で `count == 0` を明示要求し、拒否ケースを 1 件足した。
- **変異 matrix は 2 走した。** 走 1 は probe で、baseline PASSED・
  **SURVIVED 0 / TIMEOUT 0 / PARSE_ERROR 0**、KILLED 5 / MISMATCH 5。
  MISMATCH はすべて**期待 node 集合の不足**であって検出力の欠如ではない (`DW-M08` の
  probe + 再登録経路)。走 2 (権威走) は baseline PASSED、**KILLED 10 / MISMATCH 0 /
  SURVIVED 0 / TIMEOUT 0** で、**10 変異すべてで登録した期待 node が 1 件も欠けずに落ちた**。
  過剰拒否検出用の正例 P1 (chain の positive 判定に到達不能条件を足す) も KILLED で、
  **正例に検出力があることを実証した**。
- **事前登録の変異を段 6 で 2 件是正した。** (i) M4 は共通 gate に遮蔽される等価変異だったので
  M9 (共通 gate 直撃) へ統合した。(ii) M6 (status) は artifact gate に遮蔽されるため
  producer・verifier・artifact gate の**両層 3 箇所同時変異**へ再照準した。
  焦点再レビューが両方を独立に指摘した。
- **親が provenance 違反を 1 件出し、自分で除去した。** 14:40 の main 取り込み merge の trailer を
  環境既定の `AI-Agent: claude-opus-5[1m] (Claude Code)` で書いてしまい、規約の
  `product=...; model=...; reasoning=...; role=...` 形式に違反した。
  `AI-Agent-Correction` の枠は消費済みで新規に使えないため、**未 land の自分の wave branch を
  main から作り直して実装を線形に載せ直した** (検査の迂回ではなく欠陥 commit の除去)。
  再監査は新規違反ゼロ。
- **段 5 実装子と 3 巡の fix 子はいずれも pytest を 1 件も実走できなかった**
  (`qstat -Q` preflight rc=1 / runner rc=16)。全員「実装済み・未実走」と正しく申告しており、
  緑の偽申告はない。実測はすべて親が計算ノードの dispatch で行った。
  login node の bounded local は輻輳で
  「bounded scope の memory.max / memory.oom.group を走行中に attest できない」を返し続けた。
- **背景 task の完了通知がこの session で 6 回以上先走った** ({{F:fabricated-task-notification}})。
  待ち手・until ループ・Monitor のいずれの形でも起き、いずれも成果物実在の照合で誤進行を防いだ。

### 工数

codex 子 10 本、合計 5,961 秒 / 448 model call / CLI reported 2,117,323 token
(receipt.json の実測)。

| 段 | 子 | model / effort | wall s | calls | outcome |
|---|---|---|---|---|---|
| 2 | plan | gpt-5.6-sol / max | 953.0 | 38 | accepted |
| 3 | consult sol | gpt-5.6-sol / max | 1083.2 | 64 | accepted (NO-GO) |
| 3 | consult luna | gpt-5.6-luna / max | 982.6 | 44 | accepted (NO-GO) |
| 5 | author | gpt-5.6-sol / high | 1102.4 | 76 | accepted、pytest 実走 0 |
| 6 | review A | gpt-5.6-sol | 536.7 | 53 | accepted (NO-GO) |
| 6 | review B | gpt-5.6-sol | 495.9 | 23 | accepted (NO-GO) |
| 6 | fix 1 | gpt-5.6-sol / high | 738.0 | 66 | accepted、pytest 実走 0 |
| 6 | fix 2 | gpt-5.6-sol / high | 418.9 | 36 | accepted、pytest 実走 0 |
| 6 | fix 3 | gpt-5.6-sol / high | 151.0 | 14 | accepted、pytest 実走 0 |
| 6 | focus | gpt-5.6-sol | 502.0 | 34 | accepted (NO-GO → 3 巡目へ) |

## 次の一手差分

### 完了

- [T-1175] cell admission が失敗しても診断可能な partial report が残るようにした。
  免除の根拠を verifier の独立再導出 (persisted layer3 不在かつ独立 admission 失敗) へ移し、
  run-finish への exact projection と report の完全一致照合を足した。
  certifying 経路の `admission_status == "admitted"` 完全一致要求は 1 文字も変えていない。
  変異 matrix 10/10 KILLED、対象 2 test file で 320 passed。
  remaining: none
  base: d585a989b9d96336a3b6d5b204b3b5d4f5e83f81e9947a9820dc30aa30eca54e

### 新規

- {{T:build-start-keyerror}} **P1・新規**:
  `p3_s4_loop_trigger_gating._wal_binding_commitment` が `records[STAGE_BUILD_START]` を
  直接 indexing しており、`build_start` を持たない WAL shape で `KeyError` になる。
  [T-1112] 2 走目の実失敗原因そのもので、本 wave の report 化とは独立である
  (report は残るようになったが、次回も同じ地点で止まる)。実装面のため Codex author が要る。
- {{T:invalid-event-raw-response-ref}} **P2・新規**:
  role の invalid event の `error_artifacts` に payload/envelope の path と hash は入るが、
  **raw response の path と hash が入らない**。raw 自体は保存されているのに、
  report から失敗した coder の生応答を直接指せない。journal event schema の変更なので
  受理集合の変更を伴う。実装面のため Codex author が要る。
- {{T:partial-report-formal-receipt}} **P2・新規**:
  `trial_registry` は完全性検査を通した後、status を単なる文字列として受け入れるため、
  本 wave が新たに publish するようになった failure partial report も
  formal acceptance receipt に載る。現行 receipt は構造的に `certifying=false` で
  certifying Layer 3 は `true` を要求するため昇格はしないが、
  「partial を formal acceptance に載せるか」は未裁定の consumer 変更である。
- {{T:failure-only-report-standalone-verify}} **P2・新規**:
  `verify_autonomous_trial_files` は非空 build report に `campaign_output_root` を要求するため、
  failure-only の build report を root 引数なしで独立検証できない。
  runtime の report 発行と「単独検証可能な診断成果物」の契約が一致していない。
