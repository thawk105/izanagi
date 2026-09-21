# 依頼の逐語 (dev-wave 引数、2026-09-21、背景 job 79c178af)

precheck: Codex 実装子 (author / fix) が sandbox で pytest を実走できず「実装済み・未実走」で返す (login hook が pytest を拒否)
  ため、親が焦点走を回してから fix 巡へ戻す往復が起きている ([T-2792] / [T-2796] の実測)。新 test file の __main__ self-run harness
  (PYTHONPATH=. python3 orchestrator/tests/<test>.py) を codex 子が login で実行できるか (hooks の拒否対象か、rc、所要) を実装差分ゼロの probe
  で実測し、可能なら author prompt に「返す前に self-run を 1 回」を足す案、不可能なら拒否の理由と代替を、裁定パッケージとして返す (着手直前の
  local main から fresh worktree、実装・docs 変更は本 wave でしない)。hooks の拒否を迂回しない、pytest の login 実走禁止 (D289 / rc=16)
  は動かさない、self-run は計測でも受入でもないことを明記する。規律 2 を緩めない。precheck だけ。gate・台帳・一般化の追加は scope 外。
