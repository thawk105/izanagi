# 段 1 brief — [T-401] racct 欠測の恒久対応 (設計案まで)

wave: `dev-wave-t401-racct-permanent` / worktree branch `worktree-dev-wave-t401-racct-permanent`
worktree root: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t401-racct-permanent`
対象コード: `output/insights/2026-08-03_t361-t362-cluster-probes/driver/run_probes.py` (5814 行)

## scope

ユーザー引数は「racct 欠測の恒久対応、**設計案まで**」。したがって本 wave は
probe controller 族の会計証拠経路について**設計案 (裁定パッケージ) を作るところまで**で終える。
コード・テストの実装差分は作らない (段 4 で「実装しない」を裁定する既定)。

## 確定済みユーザー裁定 / 既存凍結 (緩めない)

- **D161 (split-v2)**: attempt 判定は 3 分離。`accounting_available` は evidence 側、
  `accounting_integrity_valid` と `termination_cause_consistent` は観測 gate に残る。
  authoritative 選出は `observation_valid ∧ terminal_proven` だけで行う。
- **事前登録 erratum-1**: 欠測の下位分類は `permission` / `empty` / `error` の 3 語。
  判定式・閾値・語彙は不変。凍結文は書き換えず erratum を足す方式。
- **F92 恒久対応 (2)**: 終端実証は `qwait` / `racct` / **`.e` の NQSV 会計 block + `qstat` 不在**
  の論理和。**会計 block 単独では終端としない**。
- CLAUDE.md 規律 2: 正しさゲートを緩める変更は採用しない。受理集合を広げない。

## 段 1 実測 (2026-08-06、Pegasus ログインノード。すべて本 wave で実行)

1. `racctjob` / `racctreq` は引数なしでも `-I 889948.nqsv` 付きでも **rc=1**。stdout は
   `GROUP REMAIN ESTIMATE INITIAL` の header 行だけ、stderr は `sudo: パスワードが必要です`。
   (191) の真因判定を再現した。恒久的な permission gate である。
2. `ACCOUNTING_PERMISSION_MARKERS` (run_probes.py:151-160) に `パスワードが必要` が既に含まれ、
   欠測は正しく `permission` に分類される。分類語彙側の欠陥ではない。
3. 実 `.e` の NQSV 会計 block (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/
   meas-feasibility.sh.e889948`) が持つ field は Request ID / Request Name / Queue /
   Number of Jobs / User Name / Group Name / Created・Started・Ended Request Time /
   Elapse / Remaining Elapse。`_accounting_valid` が要求する 4 種
   (`Request ID:` `Started Request Time:` `Ended Request Time:` `Elapse:`) はすべて実在する (DW-O13)。
4. ただし `.e` は request 単位の block が 1 個だけである。`_collect_accounting`
   (run_probes.py:1765-1789) が `racctjob` へ期待する `expected = attempt.leg.nodes` 件の
   **job 単位 record は `.e` に存在しない**。`Number of Jobs: N` という総数の 1 行があるだけ。
5. `rbudgetcheck` は **sudo なしで rc=0**、`SFC 274.80 1.00 1000.00` を返す。driver は既に
   qsub 前後で capture 済み (`rbudgetcheck-before-qsub` / `rbudgetcheck-after-request`,
   run_probes.py:4121-4124, 5121, 5293) で、差分を `Decimal` で算出している
   (`decrease_point_raw`, run_probes.py:5543-5556)。ただし用途は初期 4 request の費用 gate であり、
   `point_conversion` は `"UNDETERMINED"` のまま。
6. `.e` は既に manifest 束縛 + sha256 + size 照合付きで保存・解析されている
   (`_saved_nqsv_stderr_accounting`, run_probes.py:1882-2010)。現用途は termination cause 証拠と
   終端実証 path 3 (`3_saved_nqsv_stderr_accounting_plus_qstat_absence`, run_probes.py:4616-4618)。
7. `REQUIRED_EXTERNAL_COMMANDS` (run_probes.py:183-192) は `racctjob` / `racctreq` を必須列挙する。
   これは PATH 上の**存在**検査であって利用可能性検査ではない。実際 `which` は通り実行は rc=1。
8. `_collect_accounting` は 2 command × 最大 5 attempt、失敗ごとに 2 秒 sleep する。恒久失敗下では
   1 attempt あたり subprocess 10 本 + sleep 8 秒を、結果が変わらないと分かっている経路へ払い続ける。

## 不変条件

- 受理集合を広げない。`.e` を採用することが「会計が取れた」ことになり観測 gate を素通りさせる方向は不可。
- D161 の 3 分離を後戻りさせない (2 field 化・単一連言への回帰はしない)。
- 会計 block 単独を終端実証にしない (F92)。
- 事前登録文は書き換えず、必要なら erratum を追加する形にする。
- 本 wave では `run_probes.py` を編集しない (設計案まで)。

## 親の provisional 裁定 — いずれも段 3 の攻撃対象

- **(P1)** `.e` は job 自身の stderr stream であり、job body が同形 block を書ける。外部 scheduler DB を
  引く racct とは信頼階層が違う。ゆえに「racct を捨てて `.e` を**正式な**会計証拠にする」は
  無条件では証拠強度の格下げであり、格下げを明示しないまま名前だけ昇格させる案は採らない。
- **(P2)** `rbudgetcheck` 差分は sudo 不要な唯一の**外部**会計信号だが group 単位であり、
  並行 job (本 wave 自身の dev-wave job を含む) が同時に消費するため request 束縛ができない。
  単独では会計証拠にならず、上界・下界としての利用可否が論点である。
- **(P3)** 「実装しない」と裁定しても、必須 command 列挙と 5 回 retry は恒久欠測を毎 attempt
  16 秒かけて再確認する死荷重である。設計案はこの扱い (据置 / 縮退 / 撤去) を明示的に含めるべきである。

## 成果物影響 (DW-G05)

本件は CC 合成の certified 選択・材料レポートへは流れない (probe controller は危険性 probe 専用で、
campaign の proof chain とは別系統)。影響するのは **T-361/T-362 危険 probe の attempt 台帳**の
`accounting_evidence` / `accounting_available` / `accounting_unavailable_reason` field と、
その台帳を根拠に書かれる危険性結論の**証拠強度**である。放置した場合、全 attempt が
`accounting_available=false, reason=permission` のまま確定し、会計側からの独立裏取りが恒久的にゼロになる。
観測 gate と authoritative 選出は D161 により不変なので、既存 authority の受理/拒否は変わらない。

## 成果物の形

`output/insights/2026-08-06_t401-racct-permanent/` に設計案 (択一・トレードオフ・推奨・不採用理由・
未解決点) を置き、worklog / decisions は spool fragment として書く。コード差分なし。

## 分割方針

段 2 = codex 1 本で設計案起草 (read-only)。段 3 = 2 レンズ並列 —
A: 信頼境界と受理集合の格下げを攻撃、B: 実効性・既存資産の見落とし・親実測の過剰一般化を攻撃。
