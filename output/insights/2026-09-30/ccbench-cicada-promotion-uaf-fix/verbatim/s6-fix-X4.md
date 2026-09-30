## 直したこと (file:line)

- [launch_promo_confirm.py:293](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:293): M2 を、最初の `heap-use-after-free` 報告の連続 frame で `writeSetClean` の直後の呼出し元が `abort` の場合だけ成立する判定に変更。
- [launch_promo_confirm.py:396](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:396): 単位 D の diag-4 を土台・代表 promotion の対照として束縛。[同:447](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:447) で土台既定 ASan M×1、修理後既定×1、修理後代表×2を実行し、4 組合せを `asan_matrix` に記録する構成に変更。
- [README.md:5](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/README.md:5): 数え上げを **26 build＋CI、67～70 走行**に更新し、4 組合せの表と diag-4 の出典を記載。

## login で行った検査と結果 (未実走の明記)

- 実物の `ASAN-M-r1.stderr` の `#1 writeSetClean` → `#2 abort` は成立、順序を入れ替えた fixture は不成立。diag-4 対照の土台 SHA・genome・argv・計装なし Debug ASan も照合済み。
- 修理後 tip `16ad3eb8…` で **ycsb・tpcc・ci の `--dry-run` は各 rc=0**。Python 構文検査、`git diff --check`、`check_codex_agents.py`、`check_docs.py` も rc=0。
- build・走行・判定器・ASan・CI image は今回 **未実走**。

## 総括

焦点レビューの新所見 1・2 に対応しました。土台代表の ASan だけが単位 D の既取得結果で、残る3組合せの結果は計算ノードでの実走待ちです。