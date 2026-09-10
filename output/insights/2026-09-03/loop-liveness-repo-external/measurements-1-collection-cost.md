# 親が取った実測値と再現手順

測定機: ログインノード pegasus02、単一 process、loadavg は高い。
**比率だけを使い、絶対値を計算ノード 48 並列へ転移しない。**
走ごとのばらつきが大きいので best-of-5 を採った。

## 1. 成分分解

再現: `python3 probe-collect-split.py <worktree>/orchestrator/campaign 5`

```
files                     : 187
read_text  (best of 5)   : 0.090 s
ast.parse  (best of 5)   : 2.522 s
ast.walk   (best of 5)   : 0.703 s
ast.walk prefiltered      : 0.074 s
walk saved by prefilter   : 0.629 s
lexical marker hits       : 13
ast discovered drivers    : 7
read+parse+walk total     : 3.315 s
read+parse+walk w/ prefil : 2.686 s
```

## 2. prefilter を parse の前へ置いた場合

再現: `python3 probe-prefilter-before-parse.py <worktree>/orchestrator/campaign 5`

```
files                       : 187
current  (parse all 187)    : 1.676 s
prefilter BEFORE parse      : 0.245 s
saved                       : 1.431 s  (85.4%)
discovered sets identical   : True
discovered count            : 7
```

1 と 2 で絶対値が違う (3.315 秒 対 1.676 秒) のは、1 が 187 本の tree を全部メモリに保持したまま
測っており GC 圧が違うためと、ログインノードの負荷変動のためである。**両者を足し引きせず、
それぞれの中の比率だけを読む。**

## 3. 既存一次資料 (親が読んだもの)

- `output/insights/2026-09-02_acceptance-collection-internals/collect-per-file.json`:
  warm 14.36 秒の collection で、`orchestrator/tests/test_p3_exploration_namespace.py` の
  collector が 3.437 秒。全 file collector 合計 12.542 秒の 27.4%。次点は
  `test_t316_sandbox_probe.py` の 0.542 秒で、6.3 倍の外れ値。
- 同 README: この費用は 48 worker x 3 shard + login の collect-only、合わせて 145 回払われている。
- `output/insights/2026-09-01_t2097-acceptance-floor-decomposition/README.md`:
  最遅 shard の pytest wall 213.9 秒 = 最長単体 node 126.13 秒 + 全 shard 共通の report 外費用
  約 56.3 秒 + shard-0 固有 約 21.9 秒 (未計測)。
- `output/insights/2026-09-02_t2097-residual-breakdown/README.md`:
  共通 report 外費用の 95% が「48 worker の全 collection」約 51.7 秒。worker 起動は約 3.2 秒。
  テスト 0 件の較正走 (Z-S1) の pytest wall は 55.73 秒。
  D711 (2026-08-23) の同型測定は 12.86 秒だった。node は 14479 → 19572 (1.35 倍) なのに費用は 4.33 倍。

## 4. 保留機構の射程 (親が現物で確認した)

- `orchestrator/tests/conftest.py:2027-2030` が `pytest_collection_modifyitems` の中で
  `pytest.mark.skip` を付ける。module import の**あと**である。
- `orchestrator/tests/growth_test_holds.py` の登録は現在 61 entry。
  `test_p3_exploration_namespace.py` は載っていない。

## 5. repo 外束縛の現況 (親が実測した)

- `ls /home/SFC/tanab/.codex/sessions/2026` → `08` と `09` だけ。`07` は消えたまま。
  それでも `_require_pinned_rollouts` が内容単位で skip するため緑。
- `ls -d /work/1/SFC/tanab/dev-wave-jobs` → 実在、直下 1000 entry。
  よって 2 と 3 の束縛は現在緑だが、防護は上表のとおり穴がある。
