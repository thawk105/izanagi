## 直したこと (file:line)

- [壊し patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/patches/broken-cicada-promotion-ronly-stale-recheck.patch:45): promotion が成功した read 要素の位置を保持し、その要素で再検査起点が食い違ったまま commit した場合だけ event を出すようにした。
- [確認 job](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:100): tip の `cc/cicada/` と土台＋fix1〜fix4 の byte 一致、4 patch の SHA-256 を検査する。[M1 の witness 辺照合](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:240)、M2・M3、flags、D297、修理後失敗の合否を実装した。
- [README](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/README.md:5): 追補 2 の条件表と単位 D の実測に合わせて更新した。

## レビュー所見への対応表 (closed / partial / open)

| 所見 | 状態 | 対応 |
|---|---|---|
| A-3、A-4/B-4、A-5、A-6 | closed（実装） | event の read 要素への帰属、M1/M2 の kill と M3 感度の合否、異常終了時の flags、D297 の期待拒否を実装。実走による成立確認は未了。 |
| B-1、B-3、B-5 | closed（実装） | 土台の再走と適用検査を縮小し、OPT=1・PROMO=0 の TPC-C trace を追加。 |
| M3 の発火 | open | fix2 逆適用木に D の `diag-counters.patch` が fuzz なしでは当たらないことを login で確認した。job は `not_reached` を記録し、全体を fail にする。 |

## 数え上げと見積り

YCSB は **10 build・35～38 走行**、TPC-C は **15 build・30 走行**、別に CI 全 protocol build が 1 回。合計 **25 build＋CI、65～68 走行**。単位 D の 250 秒・280 秒を踏まえた X の概算は **1,800～3,600 秒**。M3 の patch 不適用時は build・走行が各 1 減る。

## login で行った検査と結果 (未実走の明記)

fix1〜fix4 を当てた使い捨て clone で、壊し patch は標準 trace、TPC-C 計装を重ねた trace、promotion 診断変種の各順序に `git apply --check` **rc=0**。Python 構文、M1/M2・flags・D297 の fixture、CI shell 構文、`git diff --check`、`check_codex_agents.py`、`check_docs.py` も通った。clone は削除した。

`clang-format-14` は既存 trace 計装の行で失敗した。1 TU 構文検査は login に Masstree の `config.h` がなく完了していない。正式 tip bundle がまだないため、job の正式 `--dry-run`、全 build・走行・判定器・ASan・CI は**未実走**。commit と index 操作は行っていない。

## 総括

追補 2 の合否と縮小条件を job に反映した。計算ノードでの結果は未確定であり、現状の M3 は `not_reached` として全体 fail になる。