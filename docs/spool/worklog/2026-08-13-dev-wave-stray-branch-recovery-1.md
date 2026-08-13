---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-13
wave: dev-wave-stray-branch-recovery
seq: 1
title: 取り残し branch 3 本を内容と blob で再監査し、全て掃除対象と判定した (docs のみ、branch worktree-dev-wave-stray-branch-recovery)
---

## 本文

- ユーザー指定の 3 branch を、branch 名の worklog/archive 検索、`git cherry -v main`、patch-id、main 全履歴の blob 到達性、後続回収 commit との差分で再監査した。branch 削除は行っていない。`worktree-dev-wave-t907-t908-t910-acceptance-integrity` と `worktree-dev-wave-t657-t660-g2-activation` は指定どおり対象外とし、稼働中 branch 4 本と backup 2 本にも触れていない。
- `worktree-dev-wave-known-red-octopus` (`05279797`) は掃除対象。`git cherry` の非 merge 3 commit は全て `-` で、実装 `238d4096` と landed `ff41d6c0`、記録 `86e3a9ce` と landed `44b0538b` はそれぞれ patch-id が一致した。branch tip が持つ 9 path の blob は全て main 履歴から到達可能で、s8c 履歴契約の 2 blob は現行 main とも一致する。checker と DW-O18 は後続 v2 (`8d645ee4`) で実環境欠陥を修正済みのため、旧 branch の再 land は退行になる。land を推さないので、稼働中 `worktree-dev-wave-t1027-acceptance-reds-checker` との merge 試行は行っていない。
- `worktree-dev-wave-t139-addendum-b` (`84217161`) は掃除対象。初稿 13 blob のうち 8 blob は main 現在値と exact 一致し、残る主要文書は `worktree-dev-wave-t139-addendum-b2` が byte 保存して blocker と裁定を反映した後継へ更新した。branch 固有だった `s4-adjudication.md` と `s6-refocus2.md` / `s6-refocus3.md` も `d19ead8f` で回収済み。旧 `package.md` にだけ残った第 5 案は 2026-08-11 のユーザー裁定で不採用終端し、T-962 でも「今は足さない」と確定している。したがって `git cherry` の `+ 84217161` は未 land 成果ではなく、修正・分割回収・不採用を含む旧草案である。
- `worktree-cleanup-submodule-recurrence` (`e8d0c44c`) は掃除対象。旧実装は Codex author provenance を欠くため直接 land せず、ユーザー裁定どおり Codex author が `cc1c2af4` で再著述して main へ着地した。後継は同じ「到達不能 commit かつ main/全 local branch tip に path が無い」の二段判定に加え、環境変数の遮断、root/merge commit、fail-closed な git error、既知限界表示、負例を強化している。旧 blob は exact 不一致だが、これは未回収でなく意図的な再著述と堅牢化であり、旧 2 commit の取り込みは退行になる。過去の T-963 で同 branch は削除可のユーザー裁定も記録済みだが、本 wave の指示どおり削除しない。
- 3 branch とも分類は「不要と判断して掃除対象として報告する」。新しい裁定待ち、実装差分、変異対象はない。path の不在/実在だけを根拠にせず、内容・blob・裁定を併用した。
- 受入全走は Pegasus request `909181.nqsv` (`bnode012`) で 36 failed / 10,555 passed / 58 skipped、赤は全て `orchestrator/tests/test_codex_worker_launch.py` の 3 秒 wall-clock 系だった。48 workers・全 10,649 items 同居時の load average は約 30 で、launcher subprocess が `codex_exit_code=-9` または `max_wall_clock_s` になった。同 file を同じ force-dispatch 形で単独再走すると request `909187.nqsv` で 114/114 passed、代表 node も request `909185.nqsv` で 1/1 passed。今回の変更は docs fragment だけで同 file へ到達せず、赤は差分へ帰属しない負荷フレークと実測判定した。最初の受入投入は新規 worktree の submodule 未初期化で rc=14 となり、local modules cache を明示して初期化後に再投入した。

## 次の一手差分
