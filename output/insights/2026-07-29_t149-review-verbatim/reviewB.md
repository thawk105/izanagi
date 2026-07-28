# 判定: REJECT

must-fix 2 件。commit `4b4fb76` はこのまま受理不可。

## 所見

### [RB-1] must-fix — `coder.md` の review pin / Codex adapter 更新漏れ

file:line: [coder.md:13](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/.claude/agents/coder.md:13)、[review_ledger.py:19](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/codex_roles/review_ledger.py:19)、[coder.json:119](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/.codex/role-adapters/coder.json:119)

`coder.md` の SHA-256 は `bb215c…` から `5aac447…` に変わったが、以下が旧 byte のまま残る。

- `review_ledger.SOURCE_FILE_SHA256["coder"]`
- `.codex/role-adapters/coder.json` の埋込本文、`source_file_sha256`、`source.sha256`

実測で `python3 tools/check_codex_agents.py` は `reviewed SOURCE_FILE_SHA256 drift; ledger明示更新が必要`、rc=1。handoff の「coder.md は pin なし確認済み」は事実誤認であり、E5 の必要 closure が scope から落ちた DW-O12 型である。`coder.md` を戻すか、明示レビューの上で ledger と byte-stable adapter を同時更新する必要がある。

**成果物影響:** 必須完了検査が赤になり、static adapter も旧「backoff.hh のみ」を保持するため、この commit は受入不能。

### [RB-2] must-fix — S6 drift alarm は EBS の縮小を検出しない

file:line: [test_s6_proposal_rounds.py:212](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_s6_proposal_rounds.py:212)、[test_s6_proposal_rounds.py:213](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/tests/test_s6_proposal_rounds.py:213)、[s6_proposal_rounds.py:120](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t149-edit-surface/orchestrator/campaign/s6_proposal_rounds.py:120)

具体的反例は `EVOLVE_BLOCK_SOURCES` から `cc/silo/transaction.cc` を除く変更。

1. `_live_surface_pi()` は fake `git ls-tree` の `silo_listing` 自体を live EBS から作る。
2. 除去された `transaction.cc` は `silo_listing` と `edit_surface_map` の双方から消える。
3. production 側の凍結 `ebs` には `transaction.cc` が残るが、照合ループは `pi["edit_surface_map"]` しか走査しないため、その余剰要素を観測しない。
4. `regen == frozen_regions` も成立し、`freshness_check()` は `[]` を返す。

従って「将来 EBS が動くと本テストが赤」というコメントと段 4 の T2 裁定は偽。repo に EBS の append-only 契約もない。region universe を EBS と独立した凍結全集合で保持し、縮小 mutation も事前登録すべきである。

**成果物影響:** EBS 縮小後も旧 N1 packet の `transaction.cc: opened=true` を stale と検出せず、S6 の freeze/verify/run 開始ゲートが通り得る。

## 攻撃したが破れなかった軸

- **二重 runner:** 攻撃したが破れなかった。`test_campaign._run()` と `test_s1_known_axes_freeze._run()` は `globals()` の全 `test_*` を動的収集し、新設テストは fixture なし。`test_s6_proposal_rounds.py` は README の pytest 専用 allowlist に明記され、`monkeypatch` 利用は整合する。
- **import 回帰:** 攻撃したが破れなかった。`source_digest` は campaign package 文脈で import され、直接依存は `.model` のみ。循環・import-time I/O はない。pytest 専用ファイルなので自走 harness は不要。
- **coder の意味と Claude hook:** RB-1 の pin closure を除けば、攻撃したが破れなかった。`source_digest.EVOLVE_BLOCK_SOURCES` と `guard_write.py` の literal は一致し、`settings.json` は `Edit` を hook に配線済み。枝内限定が機械防壁でなく規律・レビューである点も本文に明記されている。
- **`p3_s4_loop.py:70` コメント:** 攻撃したが破れなかった。同 driver の `SOURCE_REL` は実際に `backoff.hh` 固定。sort は独立 `p3_s4_loop_sort.py`、trigger-gating は `axis_trigger_gating.SOURCE_REL` を取り込む別 driver である。
- **凍結 output pin:** 攻撃したが破れなかった。5 ファイルすべてについて exact path と変更前後 SHA-256 を `output/**/*.json{,l}` 等で照合したが、output の source pin はない。特に pin 済みなのは production の `campaign/s1_known_axes_freeze.py` や `p3_s4_loop_sort.py` であり、今回変更した同名 test / `p3_s4_loop.py` ではない。ただし `coder.md` の非-output review pin は RB-1。
- **裁定外 hunk:** RB-1 の closure 欠落を除けば、攻撃したが破れなかった。変更 5 ファイルは E1〜E6 に対応し、余分な production 挙動変更はない。

実測は `check_docs.py` rc=0、`check_codex_agents.py` rc=1、`git diff --check` rc=0。指定どおり pytest は実走していない。