# 依頼の逐語 (/dev-wave の引数、2026-09-21、job 57f119fa)

変異 matrix の probe 走 (dispatch、全件 SURVIVED で期待 node を観測) を login の self-run に置き換える手順を DW-M08
  (docs/dev-wave/mutation.md) へ収容する (docs + pin 追随、着手直前の local main から fresh worktree)。手順 = 各変異を登録 worktree
  の生成器へ注入 → 新 test file の __main__ harness を PYTHONPATH=. python3 で自走 → 原 bytes へ復元し sha256 一致を assert → git status clean
  を確認 → 観測 node (\S+?::[A-Za-z0-9_]+ で抽出し orchestrator/tests/ を前置) で dispatch final を 1 回。実測 = 2026-09-20 fig13 wave (20 変異
  1 分、final 20/20 完全一致、混雑時は probe+final 2×20 run で 3〜4 時間の差)。parametrize / skip を持つ test や self-run と pytest の node
  が食い違う疑いが 1 件でもあれば dispatch probe に戻す条件を残す。byte 予算は D782 手順 1 段目 (既存記述の削減)
  で収容し上限は動かさない、check_docs / test の pin literal の追随は Codex author (D95)。final の完全一致要件 (DW-M08、F33) と KILLED
  判定は変えない。規律 2 を緩めない。手順の収容だけ。gate・台帳・一般化の追加は scope 外。
