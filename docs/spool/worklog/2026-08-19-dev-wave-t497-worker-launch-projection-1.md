---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t497-worker-launch-projection
seq: 1
title: 単独段 worker/reviewer の起動をクラス1相当へ分岐した (コード + docs、branch worktree-dev-wave-t497-worker-launch-projection、変異 matrix = baseline PASSED・9/9 KILLED・SURVIVED 2 (probe)・MISMATCH 0)
---

## 本文

- 段2プランで真因を実測した結果、command 引数が想定した `.claude/commands/dev-wave.md` ではなく
  `.agents/skills/dev-wave/SKILL.md`(Codex 向け skill 定義) と、Codex CLI が全起動時に
  自動注入する `AGENTS.md`「作業開始」節だったと判明した。段2 codex 自身の rollout ログで、
  宣言なし prompt が自発的に「dev-wave スキルを使用します」と宣言し CLAUDE.md 全文(163行)を
  読んだことを客観的に確認した (agent_message・world_state 実測)。
- 段3敵対相談 2レンズがそれぞれ独立に致命的所見を出した: レンズA「SKILL.md だけでは AGENTS.md
  自動注入経路を塞げない」、レンズB「宣言の `stage=2|3|5|6`/`kind=...` が実 launcher の
  `--stage` 語彙と不一致」。両方採用し AGENTS.md にも例外を追加、宣言語彙を launcher に一致させた。
- 段6敵対レビュー2本 → fix 3巡 (DW-O16 上限) で収束。1巡目 fix 後の焦点レビューが NO-GO、
  2巡目 fix 後も NO-GO (射影必須要素の中身未検査・tab-indent decoy見落とし)。**3巡目 fix が
  絶対パス正規表現を厳密化した結果、AGENTS.md 自体 (規約説明文であり実パスの実例を含まない)
  が新規に違反判定される回帰を招いた** — 親が AGENTS.md へ実例パス `/work/...` を追記して是正した
  (実装子のバグではなく、検査の厳密化に対して docs 側の記述が追いついていなかった)。
- **authority dirty-tree 検査 (`working tree が authority commit と異なる`) を、段5・段6・
  変異spec作成の投入ごとに計4回踏んだ** — 親が `docs/dev-wave/operations.md` を直接編集した
  状態のまま子を dispatch すると即 rc=2 で拒否される。都度「退避 (`git diff` → `git checkout --`)
  → dispatch (prompt bytes を変えて新 job-id) → 完了後 `git apply` で復元」を繰り返して解決した。
  既存 F225 (merge 文脈での同型罠) への再発として failures fragment に記録する。
- 変異harness本走で罠2件: (1) runner argv に `-rf` (DW-M08) が必須と気づかず初回拒否、
  (2) runner entrypoint は絶対パスでなく相対パス `tools/run_tests.py` を渡すのが正解
  (`_resolve_command_path` が絶対パス以外だけ内部 repo (使い捨て worktree) と結合するため)。
  plan-only 見積り 11変異×90秒/1080秒のため `--detached` で nohup setsid 経由起動した。
- 実地検証: 単独段dispatch宣言付き prompt で実際に Codex `--stage plan` 子を起動し、
  出力冒頭の自己申告(「経路: 例外」)と rollout の客観的挙動 (射影対象ファイルのみ操作、
  CLAUDE.md/AGENTS.md/worklog/handoff 読み取りゼロ、model_calls=4、段2の宣言なし実行では
  33 model calls・CLAUDE.md 163行読了) の両方で新設分岐の実効性を実証した。
- 棄却した所見: 段6焦点レビュー2巡目が要求した「宣言と射影見出しの直後性」「射影各項目ごとの
  path/停止指示の1対1対応」の追加厳密化は D85 (意味全体を逐語 pin しない) 境界により却下し、
  文書契約 (fail-closed 規律) の範囲に留めた。fallback の runtime 側完全機械強制も次 wave 課題
  として見送った。
- エージェント工数: 段2プラン1本、段3敵対相談2本、段5実装1本(dirty-tree罠で1回再投入)、
  段6敵対レビュー2本・fix3巡・焦点レビュー2巡・変異spec作成1本・実地検証1本、計 15 Codex 呼び出し。
- 設計判断は {{D:single-dispatch-class1-projection}} を参照。
- 既知の申し送り (段2プランが指摘、対応不要と裁定): Codex CLI の skill 自動選択・複数 skill
  同時注入の仕様は repo 外一次資料が要るため未解明のまま。`AGENTS.md` を decoded 検査対象へ
  加えたことで land-helper scan の適用範囲が広がったが実害未確認 (次 wave 申し送り)。
  L1.5 byte 予算は残り 4 bytes まで枯渇 (次 wave が dev-wave docs へ 1 行でも足すと即赤)。

## 次の一手差分

### 完了

- [T-497] 単独段 worker/reviewer の起動を分岐し、親から dispatch 済みの子をクラス1相当 +
  親 prompt の必読事項の射影だけに従わせる設計を実装・検証・実地実証した。
  真因は `.agents/skills/dev-wave/SKILL.md` と `AGENTS.md` の両方だった
  (command 引数が想定した `.claude/commands/dev-wave.md` は無変更で足りた)。
  remaining: none
  base: c9d27801d1c213ff333aae25b73c843be630af43e8e638eb282ab2632abefa0c
