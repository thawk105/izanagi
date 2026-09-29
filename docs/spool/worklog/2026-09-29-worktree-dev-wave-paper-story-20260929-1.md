---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: worktree-dev-wave-paper-story-20260929
seq: 1
title: 論文ストーリー 2026-09-29 版を作った — 起点 1887f56e4 までの正典 (entry 1897〜1914、D2272〜D2282) を反映し、MOCC の read-heavy を比較に使って stock の G2 3/109 を事実として書き (非直列化可能とは書かない)、D2275 の判定を C2' 40a7f4ac に限り TPC-C の certified を名乗らず、方策 loop の複数 iteration 化と R2 fig8b (合成しない別 attempt) を入れた (docs のみ、台帳 ID 未起票、branch worktree-dev-wave-paper-story-20260929)
---

## 本文

- 依頼 (ユーザー起動の `/dev-wave`、next-tasks の codex 相談で起票、台帳 ID なし): D2277 項 2 (MOCC read-heavy は比較に普通に使い stock の G2 3/109 を事実として書く、原因未分離なので「MOCC は非直列化可能」とは書かない)、D2275 (C → C2' pass、TPC-C の certified は名乗らない)、[T-2871] の方策 loop の複数 iteration 化、[T-2853] R2 fig8b (原 cohort と合成しない別 attempt)、前版の起点以降に着地した entry 全体、§8 の A / B 群の状態の更新。計算投入なし、docs/paper-story-vhash/ は触らない。
- 起点 = local main `1887f56e4` (2026-09-29 08:56 JST)。`EnterWorktree(name)` が filter drivers の読み取りエラーで失敗し、手動 `git worktree add` (並走 2 本と重なり約 10 分) → `EnterWorktree(path)` は `git worktree list` の 10 秒上限で失敗 → 絶対 path で作業した。開始 gate rc=0 (`/work/1/SFC/tanab/tmp/paper-story-20260929/startup-gate.log`)。軽量版 (段 2・3・5 の Codex なし、実装面の差分ゼロで変異 matrix は免除)。
- **親の provisional 裁定 (段 1):** (P1) 反映集合は entry 1897〜1914 (1899 は前版) と D2272〜D2282 の全体。VHash 系列 (D2279・D2280・D2282 ほか) は別の論文ストーリー系列なので存在だけを指し、ComSys の改訂 (entry 1898) は扱わない。(P2) R2 の wave が insight に残した fig8 形の図 2 枚を §8 B-10 に相対 path で埋め込む (論文図ではない、`figures/README.md` の一覧外、README 規則 5 の読み) — 段 6 のレビュー 2 本がともに退けたので撤回し、path で指すだけにした。(P3) 新しい値の図は作らない。
- 版の作り方: 前版を複製して時点語を機械置換 (「前版」→「2026-09-26 版」330 件、「この版」「本版」→「前版」232 件、かな・漢字の直後の日付に空白 89 件。中黒の後ろに空白が入る 3 件は結合後に戻した)、10 部分に分けて §1〜§9 を fork 子 8 本が改稿、冒頭・§0・§8 冒頭の状態図・§10・README は親が書いた。
- **前版の執筆時点の誤り 0 件** (子 8 本とも、古くなった文を「前版の起点で真・後続が古くした」型と判定)。§5 の古い版の素材一覧にある「[T-2766] … 採用 wave は未着地」は時点を補うだけにした (境界事例)。0 件は誤りが無いことの証明ではない。
- 図の数: 本文の埋め込み 28 か所・13 図 (前版と同数)、Mermaid 17 (前版 14)、行頭の「図なし: 理由」7 行、本文の「図の候補:」12 か所。Mermaid の箱・矢印に件数と結果語が残っていないことを走査で確かめた (残る「certified」1 件は前版と同じく出力の種類名。§6 の図の書いてはならない主張の名指しは段 6 で構造語へ直した)。
- 段 6 (Codex `gpt-6-sol` read-only、medium): 差分が約 600 KB あったので review を冒頭〜§5 (A) と §6〜§10 + README 等 (B) の 2 本に分けた (各 2〜3 分)。A は NO-GO (must-fix 2 = §1 の TPC-C の v2 trace の未確定と abort の一括、本版の Mermaid の箱に観測結果、should 2)、B は NO-GO (must-fix 1 = R2 の insight 図の埋め込みは用途を一覧で確かめられない、should 1 = §6 の図の箱の certified)。すべて real と裁定して直した (§1 の既存図の経路の語は前版の決着どおり残した)。
- 焦点再レビュー 2 巡 (各 2〜3 分): 1 巡目 NO-GO (§6 の図の箱の観測語・§4 の表に埋め込まない R2 の行 → 直した。§8 状態図の A-4 の状態語は規則 4 どおり残した)、2 巡目 NO-GO (前版から運んだ図の状態語・項目名を結果語とする F2-M1 → 不成立と裁定、fix の新規誤りは 0)。3 巡目は回さず親が全 17 図を走査して閉じた (GO は得ていない)。
- 工数: Claude の fork 子 8 本 (節の改稿、各 3〜7 分)、Codex 子 = review 2 本・focus 2 本。

## 次の一手差分
