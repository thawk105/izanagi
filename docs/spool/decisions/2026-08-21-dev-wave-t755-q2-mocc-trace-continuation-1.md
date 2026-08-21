---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-21
wave: dev-wave-t755-q2-mocc-trace-continuation
seq: 1
---

## {{D:pegasus-admission-main-anchored}}. Pegasus admission registry は main 固定であり、新設 login-side 実行体は自 wave の land 完了まで実機投入できない

**決定:** 新規 Pegasus login-side 実行体 (submitter 等) を `tools/pegasus/admission_registry.json`
へ登録する wave は、同じ wave 内でその実行体を実際にログインノードから起動して実機検証すること
はできないと前提して計画する。実機検証は registry の変更が main へ land した**後**、別 wave
(または同一 wave の land 後の続き) で行う。

**理由:**
- `hooks/guard_bash.py` は `_repo_root()` で自身の `__file__` (`os.path.abspath(__file__)` の
  2階層上) から repo root を解決する。この経路は Bash tool 呼び出し側の cwd や worktree に
  依存しない。
- `tools/pegasus_admission_registry.py` の `load_admission_registry(repo_root)` は
  `<repo_root>/tools/pegasus/admission_registry.json` を読む。`guard_bash.py` の実体パスが
  `$CLAUDE_PROJECT_DIR` (primary checkout) に固定されているため、この repo_root は常に main の
  checkout を指し、dev-wave worktree 側の未 land な追加 entry を反映しない。
- 2026-08-21、T-755 Q2 継続 wave で実測: `tools/pegasus/admission_registry.json` へ
  `submit_mocc_trace.sh` (`local-ok`) / `mocc_trace_pilot.sh` (`dispatch-required`) を正しく
  追加・commit 済みの状態で `bash tools/pegasus/submit_mocc_trace.sh` を実行したが、
  「未登録 Pegasus 実行体」として guard に拒否された。

**却下した選択肢:**
- `$CLAUDE_PROJECT_DIR` や hook の repo root 解決を worktree 追従させる — hook 自体の改変は
  本 wave の scope 外であり、かつ「worktree 側で自己申告した registry をそのまま信用する」設計は
  wave が自分自身に実行権限を付与できてしまう安全性の後退になるため、そもそも採るべきでない。
- 手で `qsub` して registry gate を回避する — D141 が禁じる。

**位置づけ:** 実測に基づく運用制約の記録 (roadmap 改訂セレモニー対象外)。新規 Pegasus
login-side 実行体を扱う今後の wave は、brief 段階で「実装+land」と「実機初回検証」を
最初から2 wave (または1 waveの land前後) に分けて計画する。
