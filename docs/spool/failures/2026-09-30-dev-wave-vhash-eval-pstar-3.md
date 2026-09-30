---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-vhash-eval-pstar
seq: 3
---

## 新規

### {{F:cleanup-stop-hook-ff-before-first-commit}}. 撤去を促す終了時 hook が、最初の commit の前に main へ ff した未 land の wave 木に「land 済み、撤去せよ」と出る [テスト代表性]

- 事象: 2026-09-30 の VHash md_34 wave (branch dev-wave-vhash-eval-pstar) で、段 6 の子を待つために turn を終えるたびに、`tools/dev_wave_cleanup_stop_hook.py` が
  「この worktree の branch は local main に land 済みの可能性がある。DW-O28 に従い子木と wave 木を撤去する」を 3 回出した。wave の commit は 0 本で、未 land だった。
  指示どおり撤去すれば、未 commit の草稿の変更と fragment を持つ作業中の木を消すところだった (親は未 land と 1 行書いて続けた)。
- 根本原因: hook は「branch の reflog の最古 (作成時点) が HEAD と同じなら黙る」「HEAD が main の祖先なら land 済みとみなす」で判定する。開始 gate が NG を出したとき
  `DW-O20` は `merge --ff-only main` で HEAD を揃えるよう求めるので、最初の commit の前に HEAD が作成時点から動き、しかも main の祖先のままになる。この状態は land 済みの木と区別できない。
  EnterWorktree が origin 基準で木を切り local main より遅れること (worktree 規律の既知の型) で、この順序は背景 job の wave で常に起きうる。
- 恒久対応: {{T:cleanup-stop-hook-ff-false-positive}} (hook の判定を「branch の reflog に commit 由来の項が 1 つ以上ある」などへ直し、ff だけの木を land 済みとみなさない)。それまでの運用は hook の文言にある
  「未 land なら 1 行書いて終えてよい」で止め、撤去しない。
- 再発検知: 直す wave が `orchestrator/tests/test_hooks.py` の `test_cleanup_stop_*` に「作成後に main へ ff しただけで commit 0 本の木では block しない」負例を足す。
