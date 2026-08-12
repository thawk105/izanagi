---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t905-guard-bytes-pin
seq: 2
---

## {{D:guard-bytes-pin-authority}}. 防壁本体の bytes pin は local HEAD blob を権威とする改変検出器にする

**決定:** codex の起動前検証 (`validate_installation`) は、防壁の transitive trust set 5 本
(`hooks/codex_guard.sh`, `hooks/guard_write.py`, `hooks/guard_bash.py`,
`tools/pegasus_admission_registry.py`, `tools/pegasus/admission_registry.json`) の working bytes を、
**検証対象 repo の同一 HEAD commit の blob** と SHA-256 で照合し、不一致・比較不能・0 byte・
symlink component・repo 外解決をすべて fail-closed にする。逃がし道 (flag・環境変数・警告化) は
作らない。**この機構は改変検出器であって封じ込め境界ではなく、独立 trust root は作らない。**
docs では検証した範囲だけを主張し、残余リスク (HEAD の co-mutability、TOCTOU、
被覆外の起動経路、検査実装自身の trust root) を列挙する。

**理由:**
- 防壁本体が書き換えられても以後の起動前検証が素通しする穴を、実編集で実測した (findings 0 件)。
- pin 対象を guard 3 本に限ると実効ポリシーが pin 外に残る。`guard_bash` は import 時に
  admission registry の source を compile/exec し、失敗時は静的 fallback 集合へ落ちるためである。
- 期待値の権威を local HEAD に置くと、保守コストが 0 で、正当な guard 編集は commit により
  自己修復し、故障が当該 worktree に局所化する。
- repo 内のどの trust root も repo へ書ける主体には可変であり、独立性を得るには新機構が要る。
  粗い provenance 基準 (2026-08-12) に照らし、その新設は既定で見送り側とする。

**却下した選択肢:**
- repo 内または worktree 外の manifest に digest を宣言する — 期待値が版管理とレビューの外へ出る。
  guard の正当編集ごとに手更新が必要で、忘れると全 worktree の codex 起動が止まる大域故障を持つ。
  fresh clone や別マシンでは manifest 不在で全停止する。
- wave が凍結した authority commit を launcher へ渡す — dev-wave が渡す base commit は起動時の
  HEAD そのものであり、独立した権威にならないことを実測した。
- hardlink 検査 (`st_nlink == 1`) を足す — 検査後の改変は scope 外の TOCTOU に吸収され、
  偽陽性源になる。
- `.codex/hooks.json` 自体の bytes pin を足す — parse 後の exact 構造一致が既に意味を固定しており、
  保守コストだけが増える。
