---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-23
wave: dev-wave-t2863-silo-policy-stage-d
seq: 3
---

## 再発

### F37

- **再発: 2026-09-23** — [T-2863] wave の親が、前方 merge の commit message の事前検査 (`check_ai_provenance.py --message-file`) と `git commit -F` を**同じ応答の並列 tool call** で投げた。検査は赤 (両親と異なる実装面 `orchestrator/tests/test_ccbench_spawn_sites.py` に Codex `role=author` なし) だったが、並列 call は互いの rc を待たないので commit が走った。未 land のうちに気づいて `git reset --hard` で取り消し、3 版 (共通祖先・wave・main) を Codex author に合成させ、git の自動 merge の staged blob と sha256 一致を確かめてから、検査 rc=0 を単独 call で見て commit し直した (near miss、main 不変)。DW-O17 の「同じ shell なら `set -e`、無ければ tool call を分ける」は、並列 call を「分けた」と読む余地を残していた。恒久対応は F37 既存のとおり (検査を単独 call で走らせ rc を見てから commit)。
