# 段 1 brief — [T-598] claude_session_ledger の consumer 結線先

## scope

`tools/claude_session_ledger.py` の production consumer を**どこへ結線するか決める**。決定と、
決定を成立させる最小実装までが scope。**削減施策そのものは起票も実装もしない** ([T-598] の前提)。

## 確定済みユーザー裁定・不変条件

- **D206**: 消費観測は claude 台帳 + codex worker 台帳の閉集合。**第 3 の parser を作らない。**
  母集団を必ず報告に出す。raw token を費用・課金・枠消費と名乗らない。
- **D207**: effort 引き下げは観察値で決めない。本 wave は effort 契約に一切触れない。
- **D205**: プロトタイプ基準。最小で研究が進む選択肢を既定にする。
- **D66**: `output/task-runs/` は開発観測 namespace であり proof chain / fitness / benchmark の
  証拠ではない。`authority: development-observation-not-evidence` を必須で持つ。
  → 台帳結線は**証拠経路と接続しない**ことが不変条件。
- **規律 2/3**: 消費削減は最適化圧力。検出力を下げる変更を evidence なしに入れない。
  consumer は**観測だけ**を行い、開発フローの gate にしない (gate 化は `DW-O13` 対象)。
- **T-127**: docs 予算を上げない。

## 段 1 実測 (M1〜M9)

- **M1** `claude_session_ledger.py` の production consumer は 0 件。参照は自テスト
  (`orchestrator/tests/test_claude_session_ledger.py`) と docs の言及だけ。T-598 の記述は正しい。
- **M2** 姉妹台帳 `codex_worker_ledger.py` の唯一の production consumer は
  `tools/codex_reasoning_ab.py` (module を import して collect で使う)。「A/B endpoint 型」の結線は
  **先例が実在する**。
- **M3** 発見可能性の穴: `docs/README.md` の tools 地図に `codex_worker_ledger.py` はあるが
  `claude_session_ledger.py` は**無い**。`tools/README.md` にも無い。
- **M4 (新候補)** `output/task-runs/` = 既存の**開発観測台帳**。schema v1 は既に
  **token 4 区分 (input/output/cached/total)** の欄を持ち、非開示は `null` + `not-exposed`。
  pilot 最終 report が `token_field_missing` を coverage 欠落として明記している
  (`reports/20260720-20260722_task-efficiency.md`)。**欄は最初から空いていて、埋める producer が
  無かった。** → claude 台帳はこの欄の producer になれる。
- **M5** ただし pilot v1 は**凍結済み** (開始 2026-07-20、cap 10 run / 14 日、最終 report 発行済み、
  最終 run は 2026-07-21 で以後約 2.5 週間休眠)。新規 start は拒否され、
  「次 pilot の root 世代命名はその時に裁定」と README が明記 = **ユーザー裁定が要る**。
- **M6** wave 単位の帰属 seam は**既に存在する**。worktree に入った session の transcript は
  project slug `-work-1-SFC-tanab-izanagi--claude-worktrees-<worktree 名>` へ移る (本 session で実測:
  325KB が t598 slug 配下)。`--project=<slug>` で wave 単位に切れる。
- **M7** ただし `--cwd-contains` では切れない (main project 配下で `dev-wave-t503-...` を指定 →
  53,582 record 走査で model_calls 0 を実測)。切るのは project slug であって cwd filter ではない。
- **M8** 遡及は効かない。work-1 側の worktree slug は 10 件しか無く (旧 github checkout に 29 件)、
  ~100 wave 分の帰属は取れない。**before/after は前向きにしか取れない。**
- **M9** 走査コスト実測: 40 file / 93 MB / **3.9 s** (login node)。projects root 全体は 823 MB / 814 file。
  cron 等の無人常設は runbook §7.0 の分類 (量で判定) をやり直す必要がある。
- **M11** `--project` を外して `--cwd-contains <worktree 名>` だけで全 projects root を走らせると、
  discovery が**他 project で file 上限を食い潰して**目的の slug に到達しない (60 file / 50.6 MB /
  24,229 record 走査で model_calls 0 を実測)。→ **project slug 指定が事実上唯一の wave key**であり、
  cwd filter は補助にしかならない。M7 と合わせて、結線は slug 解決を避けて通れない。
- **M12** 全 projects root には実データとして `message_id_collision` / `request_id_collision` が
  多数存在する (旧 checkout の `subagents/*.jsonl` 群と `-home-SFC-tanab` の 2 session)。
  これらは台帳の `STRICT_ISSUES` に含まれる。→ 無人 consumer が `--strict` を既定にすると
  **母集団全体では必ず赤になる**。project scope を切るか、strict を既定にしないかの設計選択が要る。
- **M13** pilot 凍結の実体を file:line で確認: `tools/task_runs/ledger.py:548` (final marker で凍結)、
  `:553` (max_task_runs 到達)、`:557` (max_days 到達)。**3 つとも独立に発火する。**
  pilot 開始 2026-07-20 + 14 日 = 2026-08-03 で、日付だけでも既に超過している。
  → (d) は**コード変更なしには新規 run を作れない**。
- **M10** `docs/dev-wave/*` の aggregate 予算は 25,187 / 25,200 = **残 13 bytes** (実測)。
  結線の契約文を dev-wave 4 文書へ書く案は今日は取れない ([T-597] が並行して捻出先を検討中)。

## 候補と親の provisional 裁定 (= 攻撃対象)

- **(P1) 推奨 = (d) task-run 台帳の token 欄へ結線する。** M4 が示すとおり、この欄は
  「AI 開発 task の token を追記型で記録し、作業ループ改善の素材にする」ために最初から設計され、
  producer 不在で空だった。claude 台帳を producer にすると新 namespace も第 3 parser も要らない。
  M6 の slug seam が run と session を結ぶ鍵になる。**ただし M5 により pilot 世代の再開はユーザー裁定**
  であり、本 wave は「結線設計 + 裁定パッケージ」で終わる可能性が高い。
- **(P2) (b) wave 記録への添付は (d) の劣化版。** 添付先を worklog にすると docs 予算を食い、
  3 台帳の直接編集禁止にも触れる。insights へ添付すれば安いが、集計可能な系列にならない
  (自由書式・wave ごとに書式が揺れる)。
- **(P3) (a) 定期観測は却下。** cron 基盤が repo に無く、home を汚さない規約と §7.0 の再分類 (M9) を
  要求する新機構である。かつ workload 量と交絡し、それ単独では before/after を支えない。
- **(P4) (c) A/B endpoint は今回は作らない。** claude 側に paired 装置が無く、新設は D205 の最小性に
  反する。ただし D207 の原則 (因果主張は A/B だけ) は維持し、(d) の出力を因果証拠と呼ばない。
- **(P5)** M3 の発見可能性の穴は本 wave で塞ぐ (`docs/README.md` へ 1 行。予算対象外を実測済み)。

## 成果物の形

1. 結線先の決定 (decisions の新 D、または (P1) が裁定待ちなら裁定パッケージ)。
2. 決定が実装可能な範囲での最小 consumer + テスト (実装面は Codex author が書く)。
3. `docs/README.md` の tools 地図 1 行 (P5)。
4. worklog fragment / 変異 matrix (実装があれば)。

## 成果物影響 (DW-G05)

放置した場合: claude 側消費は観測されるが**どこにも系列として残らない**ため、以後どの削減施策も
before/after を出せず、[T-598] の但し書きにより削減施策が永久に起票できない。certified 選択・
レポート・試行台帳の**値は変わらない** (開発観測 namespace は proof chain と非接続、D66)。
すなわち本 wave の成果物影響は「開発運用の観測可能性」に限定され、証拠経路には及ばない。

## 分割方針

- 段 2: codex read-only plan 1 本 (file:line 粒度)。
- 段 3: 敵対 2 本。レンズ A =「この結線は before/after を実際には支えない」(M8 の遡及不能、
  wave 間の非比較可能性、交絡)。レンズ B =「規約・予算・admission・凍結 pilot との衝突」
  (D66 の非証拠境界、M5 の裁定要否、M9 の §7.0 分類、M10 の予算)。
- 段 5 以降: 実装面は 1 所有単位 (consumer + そのテスト)。
