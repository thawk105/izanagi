## 直したこと (file:line)

- [launch_promo_confirm.py:207](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:207): `INLINE_VERSION_OPT` を CMake には `CCBENCH_INLINE_VERSION_OPT_CICADA` として渡すよう修正。compile 時の `INLINE_VERSION_OPT` マクロ照合は維持した。
- [launch_promo_confirm.py:473](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:473): tip の対象全 file を CI image 内の `clang-format --dry-run --Werror` で検査し、image 内の version と結果を記録するよう変更。
- [launch_promo_confirm.py:221](/work/1/SFC/tanab/izanagi/.codex/worktrees/md32promo-x/md32-scratch/launch_promo_confirm.py:221): dry-run に本走と共通の configure 引数生成を使い、8 genome の argv を表示するよう変更。job dir で更新された正式 tip `16ad3eb8…` と bundle のハッシュも固定値へ反映した。

## 名前の突き合わせ表

| 対象 | 照合結果 |
|---|---|
| Cicada の CMake 軸 | `INLINE_VERSION_OPT` だけ指定名が異なり、今回修正。他の 6 軸は単位 D および CMake 定義と一致 |
| compile 時のマクロ | `INLINE_VERSION_OPT` のままで正しい。`-D` 照合を維持 |
| YCSB・TPC-C 実行 flag | 単位 D の job 本体および CCBench の flag 定義と一致 |
| 共通実行 flag | `thread_num`・`extime`・`group_commit`・`clocks_per_us` は単位 D と一致 |
| ASan 環境変数 | `ASAN_OPTIONS=detect_leaks=0:halt_on_error=0` は単位 D と一致 |

## login で行った検査と結果 (未実走の明記)

- 新 tip で **ycsb・tpcc・ci の dry-run は各 rc=0**。YCSB・TPC-C はそれぞれ 8 genome の configure argv を表示し、全件に `-DCCBENCH_INLINE_VERSION_OPT_CICADA=1` と `-DCCBENCH_INLINE_VERSION_PROMOTION=1` があることを確認した。
- Python 構文検査、`git diff --check`、`check_codex_agents.py`、`check_docs.py` は rc=0。
- build、判定器、ASan、CI image 内の format と全 protocol build は**未実走**。image 内 clang-format の実際の version も、計算ノードでの実行時に記録される。

## 総括

親の実測で停止した 2 箇所を修正し、現行 tip に対する 3 part の入力検査と configure argv 確認を通した。実走結果の判定は親の再投入後に必要。