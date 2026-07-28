判定: **REJECT**。現 HEAD は `a01857d`、worktree は clean。`closed` 5件、`partial` 2件、`regressed` 0件。pytest は未実走。

| 所見 | 判定 | 実コードでの検証 |
|---|---|---|
| RB-1 | closed | `coder.md` の SHA-256 は `5aac447a…f5c34`。ledger、adapter の `review_ledger.source_file_sha256`、`source.sha256` がすべて一致し、埋込本文も exact 1回、adapter 全体も renderer 期待 byte と一致する。[review_ledger.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/codex_roles/review_ledger.py:19) / [coder.json](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/.codex/role-adapters/coder.json:119) |
| RB-2 | partial | live EBS の単独拡張は追加要素が `opened=True`、production 凍結 EBS では false となり赤。単独縮小は `_S6_FREEZE_TIME_SURFACE` が除去要素を母集団に残し、false/true 不一致で赤。ただし凍結 literal 自身と live EBS の同時・二段階縮小は全通する。RR-1。 |
| RA-1 | closed | `include/backoff.hh` を `opened=False` にする逆方向 control が追加済み。述語を `opened and region not in ebs` にすると問題列が `[]` になり、期待値と不一致で確実に死ぬ。[test_s6_proposal_rounds.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_s6_proposal_rounds.py:260) |
| RA-2 | closed | 3 driver を個別 literal pin。sort の `SOURCE_REL` を backoff にする V9 は所属検査以前の等値 assert で死ぬ。他の within-EBS 取り違えも同様。[test_campaign.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_campaign.py:3030) |
| RA-3 | partial | `.hh` probe は有効で、`.hh` フィルタ削除時に `regen` から probe だけ消えて領域集合不一致になる。一方 cmd assert は先頭4要素と末尾しか固定せず、`-r`、`--name-only`、`HEAD`、中間順序、`capture_output/text/check` を検査しない。int/bool 境界も未解決。[test_s6_proposal_rounds.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_s6_proposal_rounds.py:231) |
| RA-4 | closed | harness 冒頭で主張を「focused node 集合内の期待一致」に限定済み。V1/V5について全 suite の完全一致を主張していない。[mutation_harness.py](/home/SFC/tanab/.claude/jobs/35817947/tmp/t149-wave/mutation_harness.py:4) |
| RA-5 | closed | T4 を NODES に加え、`_PROTOCOL_CMAKE` を壊す V6 を登録。V7＝EBS縮小、V8＝片方向述語、V9＝sort軸取り違えも登録済み。[mutation_harness.py](/home/SFC/tanab/.claude/jobs/35817947/tmp/t149-wave/mutation_harness.py:77) |

RB-1 の checker 経路は、`check()` → `validate_inventory()` → `load_role_specs()` で source bytes と ledger を比較し、続いて `expected_adapters()` の正準 render と実 adapter を全文 byte 比較、さらに埋込 `source.body` の exact 1回を検査する。[spec.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/codex_roles/spec.py:582) / [check_codex_agents.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/tools/check_codex_agents.py:223)

### [RR-1] must-fix — 凍結母集団 literal 自身が無検査で、lockstep 縮小を全通する

`F=_S6_FREEZE_TIME_SURFACE`、`L=live EBS`、母集団を `F ∪ L` としている。[test_s6_proposal_rounds.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_s6_proposal_rounds.py:208)

`transaction.cc` をまず F だけから除いても、L が補うため全テスト緑。その後 L からも除く、または同一変更で F/L 双方から除くと、`transaction.cc` は母集団から消え、production の旧凍結 EBS を照合するループに一度も現れない。通常・外側 positive control・逆方向 control の3件すべて期待どおり通る。V7 は L だけを変異するため、この反例を攻撃していない。

N1 正本では `transaction.cc` は依然 `opened=true` である。[N1 provenance](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/output/insights/2026-07-10_s8a-n1-provenance.json:200)

**成果物影響:** EBS 縮小後も旧 N1 の `transaction.cc: opened=true` を stale と判定せず、誤った編集面を60本の凍結 payloadへ流して S6 実走を開始できる。