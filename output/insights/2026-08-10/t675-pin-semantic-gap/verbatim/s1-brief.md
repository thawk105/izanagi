# 段 1 brief — [T-675] whole-file SHA-256 pin の意味欠落

## scope

[T-675] の裁定パッケージを作る。**実装差分ゼロ**で終端し `4→7→8→9` を通る (`DW-S04` の
「実装しない」裁定)。ユーザー指示「本番コードは編集しないでください」が確定済み裁定であり、
段 5・6 を起動しない。変異 matrix は同条項で免除、受入全走は免除しない
(`orchestrator/tests/test_check_docs.py` が実 repo の pin 定数を読む = 実走根拠 nodeid)。

成果物 = `output/insights/2026-08-10_t675-pin-semantic-gap/package.md` (裁定パッケージ) +
spool fragment (worklog / decisions は裁定後に必要な分だけ)。

## 不変条件

- 規律 2/3 (正しさゲートを緩めない・正しさシグナルを後付けにしない)。本件は「gate を通す
  bytes を差し替える」経路そのものなので、提案は検査を緩める方向へ倒さない。
- `DW-G05` 成果物影響: 本件を実装しない場合に変わるのは **certified 選択・レポート・試行台帳の
  値ではなく、AI 作業者向け手順書の受理集合**である。この点は正直に書き、
  [T-659] と同じ「機構を作らず手順で担う」への差し替え圧力を裁定の争点として明示する。
- `DW-G03` (族一般化には独立 2 例): 実害は **F173 の 1 件**であり、族全体への制度一般化を
  正当化する独立 2 例は現時点で無い。局所修復の側に既定を置く。
- `DW-O09` pin 閉包を着手前に列挙済み (下記 M1)。

## 実測 (段 1、すべて本 worktree の実 repo で実施。模擬なし)

環境: Pegasus。`check_docs` は login node、pytest は計算ノードへ dispatch
(`tools/run_tests.py --force-dispatch`、request `900462.nqsv`、queue `gen_S`)。

- **M1 pin 閉包 = 3 箇所** (`DW-O09` の grep で全列挙)。
  `tools/check_docs.py:389` `CLEANUP_COMMAND_SHA256` /
  `orchestrator/tests/test_check_docs.py:264` `_EXPECTED_CLEANUP_COMMAND_SHA256` /
  同 `:318` `_SYNTHETIC_CLEANUP_COMMAND` (command の**全文逐語コピー**)。
  test は 3 者の相互一致を assert する (`:6536-6547`)。
- **M2 pin は byte 変更を検知する。** 安全文「正本は `docs/failures.md` F26。」だけを削ると
  `check_docs` rc=1、違反はちょうど 1 件で、内容は
  「whole-file SHA-256 が契約と不一致」。**失われた義務を名指す検査はゼロ。**
  (3959 → 3924 bytes、35 bytes 減)
- **M3 3 箇所同時再 pin で全緑になる (F173 の穴の実証)。**削除 + 3 箇所再 pin の状態で
  `check_docs` **rc=0 / 違反なし**、`orchestrator/tests/test_check_docs.py` **357 passed /
  rc=0** (計算ノード実走)。**意味の欠落を含む bytes が「正しい bytes」として固定された。**
- **M4 対案 (意味検査) の生死確認 = 生きている。**`tools/check_docs.py` へ 2 レンズの probe を
  一時実装して実測した。(a) 必須 literal 集合 (正本ポインタ 3 本)、(b) 本文が挙げる `F<n>` が
  `docs/failures.md` に `### F<n>.` として実在するか。
  - clean tree → **rc=0 / 違反なし** (偽陽性なし)
  - M3 の攻撃状態 (削除 + 再 pin 済み) → **rc=1**、
    `安全義務への到達手段がない — '正本は `docs/failures.md` F26。'`
  - `F51` を `F901` へ差し替え → `F901 が docs/failures.md に実在しない` が追加で発火。
  - **probe は実装面なので repo へ入れず、実編集 → 即時復元** (`DW-O19`)。復元後の
    command の sha256 は `a92d960c…4722e3` で pin 定数と byte 一致、`check_docs` rc=0。
- **M5 機械化の置き場所には docs byte 予算が掛からない。**F173 の恒久対応は
  「機械化は `docs/dev-wave/**` の byte 予算に阻まれており」と書いたが、M4 の実装面は
  `tools/check_docs.py` (Python) にあり、`TextLimit` 予算の対象外である。
  **予算はこの形の機械化を阻んでいない。**
- **M6 pin と意味検査は repo 内で排他 (交差ゼロ)。**whole-file SHA-256 で pin されている docs は
  `.claude/commands/cleanup-branches.md` と `.agents/skills/cleanup-branches/SKILL.md` の
  **2 件だけ**で、両者とも `literals=()` = 必須 literal ゼロ。逆に literal 検査を持つ
  `docs/dev-wave/core.md` `workers.md` (`CODEX_FIRST_REFERENCE_LITERALS`)、dev-wave / rulings の
  Codex skill (`literals=` / `exact_literals=` / `forbidden_literals=`) は **sha256 pin を持たない**。
  必要な機構は既に repo 内に実在し、pin 対象へ適用されていないだけである。
- **M7 予算 headroom。** command は 3959 / 上限 4000 bytes、追記型テストが 17 bytes を要求するため
  実質上限 3983 = **headroom 24 bytes**。文書側で義務を厚くする案はこの枠に入らない。

## 判断が割れうる前提 (親の provisional 裁定。攻撃対象)

- **(P1)** 推奨は **(c) 両方**ではなく **(a) 機械化を主、(b) 明記を従**とする。(b) だけでは
  F173 の再発を止める力がゼロ (M2/M3 が実証) で、pin の役割を書き下しても検査は変わらない。
- **(P2)** 機械化の形は **`tools/check_docs.py` への必須 literal + ID 到達性検査**とし、
  新しい checker file・新しい台帳・新しい gate 段は作らない (M6 = 既存機構の適用拡大)。
- **(P3)** 適用範囲は **sha256 pin を持つ 2 artifact に限る** (M6)。`docs/**` 全体の
  正本ポインタ lint へ広げない — `DW-G03` の独立 2 例が無く、偽陽性面が跳ね上がる。
- **(P4)** path 到達性 (`tools/…` `docs/…` の実在) は (a) の第 3 レンズとして**入れない**。
  M4 では未実測であり、`<runbook §7.2 の dir>` のような placeholder path を含む行が
  偽陽性源になる。裁定パッケージには候補として残すが推奨に含めない。
- **(P5)** `DW-G05` の成果物影響が「手順書の受理集合」に留まる以上、実装は
  **[T-675] 単独の wave ではなく、次に cleanup-branches 系を触る wave へ相乗り**させる案も
  選択肢に残す (研究最優先 D205)。

## 並列分割方針

段 2 プラン起草 1 本 (sol)、段 3 敵対 2 レンズ (sol / luna) を並列。実装子は起動しない。
