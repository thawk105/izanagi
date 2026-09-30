# 段 4 裁定 — dev-wave-codex-astra-ultra (2026-09-30 16:20 JST)

入力: s1-brief.md、s2-plan.md、s2-parent-measurements.md、s3-consult-a.md (レンズ A 正しさ境界・実効性)、s3-consult-b.md (レンズ B 過剰・削除)。
裁定 inbox 再走査: 2026-09-30 full40/41 に本件 (codex model・effort) の項目なし。

## 中心裁定: 委任は受理しない (P1' 採用)。effort は全段 ultra のまま

- **採用 P1'**: ultra の委任 (spawn_agent) は prompt で禁じ、root rollout に spawn_agent 呼び出しの記録がある attempt を起動器が拒否する
  (新しい致命 evidence reason、online 検査と sealed 再検証の両方)。委任先の会計 (P1) はしない。
- 理由: (1) P1 は A-1 (全履歴 fork で子 rollout に親の meta/context が複製され、現行の session_meta 1 件規則に落ちる)、A-3 (manifest V2 が
  1 attempt = 1 session を強制)、A-4 (子の完了・seal 後追記が閉じない) を実物で抱え、V6 receipt・manifest 新世代・ledger まで波及する (700〜1,100 行)。
  (2) 委任先に guard が効くことは未確認 (A-6、L8)。依頼は「委任が guard の外へ出るなら規律 6 の問題として止め」と言う。未確認の面で走った仕事を受理しない
  のが規律 6 に沿う。(3) L5 の実在欠陥 (委任が見えずに素通り) は、検出して拒否すれば閉じる。「検査を黙って緩めない・受理規則を明文化する」も満たす。
- 却下 P1'' (権威段だけ max): ユーザー裁定「全段 ultra」と非同値。max が委任しない証拠もない (B-1)。
- 却下「prompt で禁じるだけ」: 素通りが残る (B-1)。
- 受理・拒否の含意: (受理) root rollout に spawn_agent の function_call が無い attempt は従来どおり判定される。例: brief L1 の PONG 実行、wait_agent を
  空振りしただけの実行。(拒否) root rollout に spawn_agent の function_call が 1 件でもある attempt は、他の検査が緑でも accepted にならない。例: liveness/deleg1。
- 残る限界 (報告に書く): 事後拒否は委任先の実行・書込みを防ぐ機構ではない (B-1)。workspace-write の author/fix で委任が起きた場合、子 worktree に
  guard 未確認の書込みが残りうる。拒否された attempt の子 token は会計されない。next_tasks_consult.sh は起動器を通らないので検出なし (prompt 禁止のみ、
  read-only sandbox は L7 で子に継承を確認)。

## 所見の裁定

| ID | 判定 | 採否 | 扱い |
|---|---|---|---|
| A-1 fork 複製 meta | real | P1 不採用で moot | insight に記録 |
| A-2 孫・別 job | real | P1 不採用で moot | spawn_agent は root rollout でだけ見る。孫は子が居なければ生じない |
| A-3 manifest 1 attempt 1 session | real | P1 不採用で moot | 記録 |
| A-4 子の完了・追記 | real | P1 不採用で moot | 記録 |
| A-5 sandbox 照合 | real (P1 前提) | moot | 子を受理しないので不要。root の sandbox 検査の追加はしない (scope 外) |
| A-6 子の guard 未確認 | real | 採用 (記述の限定) | 報告・insight は「root の guard 拒否は観測、委任子の guard は未確認・保証しない」。直接 probe はユーザー許可待ちの項目として報告 |
| A-7 テスト契約 | real | 採用 (P1' 版) | 下の変異事前登録 |
| A-8 raw と CLI-reported | real | 採用 | 週枠記録は root/子/拒否分と raw・CLI-reported を分ける |
| A-9 段 6 の repo-root | real | 採用 | 段 6 は A+B+workers ultra を統合した wave worktree を `--repo-root` にして起動 |
| A-10 rulings | real | 採用 | `.claude/commands/rulings.md` 58 行に `--reasoning ultra` と DW-S03 参照 (親、docs) |
| A-11 digest | real | 採用 | land 直前に daemon 稼働 0 件を再確認。digest 固定値テストは足さない |
| B-1 P1' 推奨 | real | 採用 | 上記 |
| B-2 拒否頻度未知 | real | 採用 | 初回実測で更新。黙った再試行・effort 低下はしない |
| B-3 削るもの | real | 採用 | test_dev_wave_codex の max を一括 ultra にしない。ultra 転送正例を最小追加 |
| B-4 完了証拠一覧 | real | 採用 | 段 7 insight に表で残す |
| B-5 全 9 段は読み過ぎ | real (一部) | 採用 | 独立検証・段 6 review 2 本・変異・受入は残す。fix/focus は所見があれば |
| B-6 L6〜L8 の一般化 | real | 採用 | 記録は「このCLI・exec 経路・明示 spawn 依頼で試した 3 設定」等へ限定 |
| B-7 週枠 | real | 採用 | token 実測と残量を分けて書く |
| plan: P2 誤り | real | 採用 | A-10 |
| plan: ledger 漏れ | real (P1 前提) | moot | |

## plan v2 (段 5)

単位 A (Codex author、所有 = tools/check_docs.py、orchestrator/tests/test_check_docs.py、orchestrator/tests/test_dev_wave_launch_authority.py、
tools/dev_waves/effort_levels.py、orchestrator/tests/test_effort_levels.py、orchestrator/tests/test_dev_wave_codex.py、一時 file `tmp-next-tasks/next_tasks_consult.sh`):
1. s2-plan「単位 A」の表どおり model literal を astra、effort pin 5 節を ultra へ (check_docs 本体・finding 表示値・独立 literal・負例の置換元・decoy の「正しい値」役)。
   旧 medium を拒否する負例を 5 節分 (小さい parametrize で)。合成 fixture の意図的な medium/high/low、V1/V2 過去形式 fixture、`REASONING_XHIGH_*` の名前は変えない。
2. `CODEX_REASONING_EFFORTS` に "ultra" を追加、docstring に「ultra は luna 系が非対応 (依頼が指定した事実。本 module は model×reasoning 互換を保証しない)」。
   `CLAUDE_EFFORTS` 不変。test_effort_levels は Claude の厳密 tuple を維持し Codex だけ ultra を期待。
3. test_dev_wave_codex の plan/consult 転送 matrix に ultra の正例を最小追加 (既存の max 等は残す)。
4. `DEV_WAVE_L1_5_BYTES_MAX` を 9_696 → 9_788 (D782 に従う最小増分。親の DW-O01 1 文追加と workers.md の medium→ultra 後の実 footprint)、
   test_check_docs の pin 3 箇所 (2777・3504・4017 付近) を意味を確かめて追随。
5. 外部 script 改訂原稿を worktree 内 `tmp-next-tasks/next_tasks_consult.sh` (commit しない) に全文で書く: 原本
   /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/next_tasks_consult.sh.orig を基に、24 行 `CONSULT_EFFORT` 既定 high→ultra (コメント更新)、
   codex 分岐に `-m gpt-6-astra`、prompt の GUARD 節に「sub-agent を spawn しない (collaboration tool を使わない)」1 行。締切 1800 秒は維持。

単位 B (Codex author、所有 = tools/codex_worker_launch.py、orchestrator/tests/test_codex_worker_launch.py):
1. root rollout の response_item `function_call` で name が `spawn_agent` のものを検出したら、新しい致命 evidence reason (名前は既存命名に合わせて author が決め、
   報告する。例 `delegation_detected`) を記録し、attempt を accepted にしない。online (`_consume_rollout_event`) と sealed 再検証 (4384・4499・4700 行付近)
   で同じ判定関数を共有する。
2. reason 集合が閉じている箇所 (150 行付近ほか) へ追加し、既存 receipt (V1〜V5) の読取互換を確認して報告する。schema 世代は上げない方針だが、
   上げないと互換が壊れる場合は実装せず報告して止まる。
3. `test_codex_worker_launch.py:3667` の許可語彙 parametrize に ultra を追加。
4. テスト: 正例 (spawn_agent 無し、wait_agent だけの空振りを含む) accepted、負例 (spawn_agent 1 件) rejected with 新 reason、sealed 再検証でも同じ拒否。
   fixture は実 rollout (/home/SFC/tanab/.codex/sessions/2026/09/30/rollout-2026-09-30T15-38-48-01a0f109-8530-7910-8c0e-e99685287eb1.jsonl) の
   function_call 行の形を写す (account 等の識別子は写さない)。
5. 早期停止は既存機構で schema を変えずにできる場合だけ。できなければ終了時拒否でよい (報告)。

親 (docs、段 5 と並行または統合後):
- `docs/dev-wave/operations.md` DW-O01 に 1 文 (実施済み・未 commit): 「ultraの委任(spawn_agent)はpromptで禁じ、委任したattemptは起動器が拒否する。」
- `docs/dev-wave/workers.md` 5 箇所 medium→ultra (**段 5 統合後**。段 5 の author は medium で起動するため)。
- `.claude/commands/rulings.md` 58 行に `--reasoning ultra` と `DW-S03` 参照。
- 段 6 の prompt 全部に委任禁止 1 行。

## 変異事前登録 (DW-M01、実装後に位置と単一理由性を確認)

| id | 位置 | 変異 | 期待 |
|---|---|---|---|
| m1 | tools/check_docs.py DW-O01 literal | astra → sol | KILLED (literal 期待・drift 負例) |
| m2 | tools/check_docs.py effort pin の期待値 (DW-S05-A) | ultra → medium | KILLED (旧 medium 負例 / 現行 docs 正例) |
| m3 | tools/dev_waves/effort_levels.py | "ultra" を削除 | KILLED (test_effort_levels / launcher choices の ultra 正例) |
| m4 | codex_worker_launch.py 検出関数 | spawn_agent 検出を常に False | KILLED (委任負例) |
| m5 | 同 sealed 再検証側の呼び出し | 再検証で検出を呼ばない | KILLED (sealed 負例) — online と冗長なら両層変異として登録し直す |
| m6 | 同 検出関数 | 名前比較を collaboration namespace 全体 (wait_agent 含む) へ広げる | KILLED (wait_agent 空振り正例、過剰拒否の正例) |
| m7 | tools/check_docs.py DEV_WAVE_L1_5_BYTES_MAX | 9_788 → 9_787 | KILLED (実 docs が予算超過) |
