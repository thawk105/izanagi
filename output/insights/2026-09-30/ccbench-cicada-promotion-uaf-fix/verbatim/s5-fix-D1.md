## 直したこと (file:line)

- [launch_promo_diag.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/launch_promo_diag.py:47): Y0/Y1 を **BASE → promotion 診断変種 → TPC-C 計装 →（Y1 のみ ronly）→ counters** に修正。診断変種を実際に `git apply` し、SHA256 束縛と dry-run の patch 列表示を更新した。
- [diag-counters.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/diag-counters.patch:1): 正しい前像から再生成した。計数とイベント出力の変更であり、判定器・既存テストは変更していない。
- [README.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-d/md32-scratch/README.md:15): 適用順を訂正した。

## 親の実測への対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| 診断変種は標準 trace の置き換え | closed | Y0/Y1 から標準 trace を除き、診断変種を直接適用 |
| counters が正しい前像に当たらない | closed | パッチを再生成し、Y0/Y1 の両列で順次適用を確認 |
| 対照 patch は BASE に単独適用可能 | closed | T1～T3 の列を clone で再確認 |

## login で行った検査と結果 (未実走の明記)

BASE `aa8e36f1669001e75a6d6da9609287dcc9f9d29b` の使い捨て clone で、Y0/Y1、T0～T3、Debug、ASan の全 patch 列が順次適用 **rc=0**。Y0/Y1 の `transaction.cc` は指定 genome・`TRACE=1` で `g++-11 -std=c++20 -fsyntax-only` **各 rc=0**。`py_compile`、dry-run、`check_codex_agents.py`、`check_docs.py` も **rc=0**。clone は削除済み。

`git diff --check` は、パッチファイル内の空白だけの *context 行* 4 行を警告した。計算ノードでの全 build・走行は**未実走**。

## 総括

親が指摘した適用順と前像の不一致を解消した。変更は `md32-scratch/` の既存 3 ファイルに限り、commit は作成していない。