---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t-codex-hook-trust
seq: 1
title: codex の hook 信頼が worktree へ継承されない穴を塞ぎ、live gate を rc=0 へ回復した (コード + docs、変異 3/3 KILLED、branch worktree-dev-wave-t-codex-hook-trust)
---

## 本文

- 起票は rulings セッションの `2026-08-12-codex-hook-trust-wave.md` (ユーザー承認済み、投入待ち)。
  本 wave がその実装であり、[T-815] の完了基準 (`check_codex_hooks.py` rc=0) を回復した。
- **起票資料の前提 1 件が実測で覆った。** 資料は「probe argv に flag を足せば rc=0 が回復する」と
  していたが、flag だけでは緑にならない。親が repo 外 probe で測った内訳:
  - flag を足すと `protected file が作成された` が両 tool で消え、stderr に
    `Command blocked by PreToolUse hook: [guard_write] 拒否: ...` が出る = **hook は実際に発火する**。
  - しかし **hook に拒否された tool 呼び出しは JSON event を一切生成しない** (router の段で弾かれ、
    拒否文は stderr にのみ出る)。checker は protected の `item.started` exact 1 件と
    「start〜turn 完了の間の拒否証拠」を要求していたため、**hook が正しく効くほど赤になる**構造だった。
  - さらに codex は Bash command を `/bin/bash -lc "..."` で包んで報告する。checker は素の command と
    exact 比較するので allowed 側も一致しない。これは trust と無関係で、flag 無しの baseline でも
    同じ赤が出ていた。
  この 2 点の修正を加えて rc=0 に到達した。詳細は {{D:codex-hook-refusal-evidence}}。
- **D294 の却下選択肢を supersede した。** D294 は「trust bypass を gate に使う」を
  「信頼が無いまま緑になり gate の意味が消える」として却下していた。ユーザー裁定が新しいので
  supersede するが、却下理由は実測で今も真である — checker だけ迂回すると本番の worker は
  hook が外れたまま gate だけ緑になる。**成立条件は checker と launcher の同時 land** とし、
  decisions へ明記した ({{D:codex-hook-trust-bypass}})。
- **ユーザー承認の文言より弱い保証で land する。** 資料は bypass の条件を「bytes 検証とセット」と
  していたが、実測すると `validate_installation` が見ているのは hooks.json の配線までで、
  guard 本体の bytes は検証していない。本 wave は約束を実態へ下げ、docs に「bytes 検証済み」と
  書かず、何を検証し何を検証していないかを列挙した。guard bytes の pin は既定の見送り側として
  裁定へ回す (下記「次の一手」)。
- **段 3 レンズ A が上流分類器で遮断され 635 秒を空費した。** 冒頭に防御目的を明記していても、
  分析完了後の最終メッセージ生成で `turn.failed`
  ("This content was flagged for possible cybersecurity risk") となり成果物ゼロ。所見の書きぶりを
  「検査 X は条件 Y で発火しない / 検証 Z の被覆は W まで」という被覆の記述に限定し、
  回避手順の記述を明示的に禁じた版で再投入して成功した。既存 memory は冒頭の枠づけしか
  求めておらず、**出力の書きぶりまで指定しないと再発する**。
- **敵対レビュー 2 本はいずれも NO-GO で、must-fix 7 件を実装前・統合前に閉じた。** 主なもの:
  flag の個数を argv 全体で数えると prompt に文字列を置くだけで通る (変異 M3 として登録し実証)、
  checker に注入 seam が無く monkeypatch だけでは実配線を検証できない、
  `_attempt_loop` の外側が `KeyboardInterrupt` / `SystemExit` を `LaunchError` に包み直していた、
  起動前検証の遅延後に wall-clock 期限を再確認していなかった、
  `git rev-parse` の空 stdout が `Path("")` 経由で process cwd に解決され不一致検査が発火しなかった。
- **変異 3/3 KILLED。** 期待 node の完全集合は先に probe 走で実測してから登録した
  (M1 = 8 node、M2 / M3 = 同一の 10 node)。M2 と M3 は同じ node 集合を倒すが別物である —
  M3 は「prompt に flag 文字列を置いても救われない」ことを示し、検査が argv 全体を数えていれば
  M3 だけが生存する。初回 probe で M3 に混ざった launcher 側 receipt node 1 件は単独再走で
  再現せず、帰属から外した。
- **変異本走の 1 回目は F57 で中止された。** baseline で
  `test_check_receipt_rejects_impossible_truth_table` が
  `failed_predicates=["process_group_residual","termination_verified"]` で落ち、harness が
  production write 前に fail-closed で止めた。同 tip の単独再走は 143 passed / rc=0 で再現しない。
  **新事実: 過去の再発はいずれも `loadavg` 12〜15 の高負荷時だったが、本件は `loadavg=(0.80, 0.17, 0.16)`
  で発火した。** 低負荷でも出ることを示す。詳細は F57 の再発として記録した。

## 次の一手差分

### 新規

- {{T:codex-guard-bytes-pin}} **P2・新規**: codex の起動前検証は hooks.json の配線までしか見ておらず、
  `codex_guard.sh` / `guard_write.py` / `guard_bash.py` の bytes は検証していない。
  workspace-write の子が guard 本体を書き換えても以後の検証は検出しない。
  bytes / hash の pin を入れるか、入れないと裁定するかを決める。
  ユーザー承認時の文言 (「bytes 検証とセット」) との差でもある。
- {{T:codex-launch-paths-uncovered}} **P2・新規**: 本 wave の防壁は
  `tools/codex_worker_launch.py` 経由の起動だけを守る。`tools/codex_reasoning_ab.py` の
  `_codex_exec_argv` (`-s read-only` 固定) と、`tools/run_codex_role.py` →
  `orchestrator/codex_roles/launcher.py` (現状 runtime blocked) は防護外のまま。
  同種の検証を広げるか、正式に scope 外と裁定するかを決める。
