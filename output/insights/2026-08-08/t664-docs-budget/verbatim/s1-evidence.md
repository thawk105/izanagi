# [T-664] 親の独立実測 (段 1 併走) — 攻撃対象

`firing_evidence.py` (同ディレクトリ) を worktree で実行した生の出力。
**ID 文字列ではなく内容語による検索**で、L2 13 節の発火痕跡を数えた。
検索対象 = `docs/worklog.md` / `docs/archive/worklog-*.md` / `docs/failures.md` /
`docs/decisions.md` / `output/insights/**/*.md`。`docs/dev-wave/**` 自身は対象外
(自己参照を数えないため)。

```
節        bytes    worklog    archive   failures  decisions   insights
DW-O04     200          0         14          2          1         25
DW-O06     210          0          5          0          0         30
DW-O08     183          0         22          9          0         86
DW-O09     935          1         39         13         14        414
DW-O10     261          0          0          0          1         16
DW-O11     223          0          9          1          6         42
DW-O12     195          0          1          0          0          1
DW-O14     200          0         15          6         15        379
DW-O16     367          9        159         30         24        535
DW-O17     702          1         64         21         26        365
DW-O18     441         10        100         41          8        263
DW-O19     602          1         16         11          4         78
DW-O20     489          0         14         11          6        166
```

語別内訳:

- O04: `commit -F`=13, `message file`=9, `heredoc`=20
- O06: `index lock`=9, `submodule.*偽赤`=22, `sandbox 由来`=4
- O08: `submodule update --init`=39, `未初期化`=78
- O09: `FROZEN_MANIFEST`=325, `pin 閉包`=127, `durable manifest`=9, `凍結 snapshot`=20
- O10: `producer.*書く全ファイル`=1, `write-path`=16, `producer の出力 bytes`=0
- O11: `未 stage 削除`=31, `rc=15`=24, `削除を伴う`=3
- O12: `裁定予定を写`=0, `実際に実行した手順`=2, `逆の工程記録`=0
- O14: `monkeypatch`=334, `注入 seam`=58, `current_head`=23
- O16: `焦点再レビュー`=456, `対応表`=277, `closed / partial`=24
- O17: `trailer`=448, `--dry-run -F`=6, `full-history 監査`=23
- O18: `単独再走`=93, `repo root`=132, `偽赤`=157, `帰属しない`=40
- O19: `git checkout --`=64, `一時変異`=41, `復元 bytes`=5
- O20: `check_wave_startup`=155, `clean-tree`=36, `untracked handoff`=6

## 親の暫定解釈 (攻撃対象)

- **13 節すべてに発火痕跡がある。**明確に薄いのは `DW-O12` (合計 2、うち有効語 1) と
  `DW-O10` (`write-path` は一般語で誤検出を含む、専用語は 0〜1) の 2 節だけ。
- したがって**経路 A の理論上の解放量は 456 bytes 以下**であり、集約の空き 16 bytes に対しては
  効くが、`DW-G05` へ足したい 274 bytes (T-412 の動機) と `DW-O01` へ足したい 1 行を両方は賄えない可能性がある。
- さらに `DW-O12` は「裁定手順と実行手順が食い違ったときに実際の手順を書け」という**判断義務**であり、
  機械検査で代替できるとは考えにくい。D94 の条件 (iii) を満たさなければ削除候補にならない。
  この場合、経路 A の解放量は `DW-O10` の 261 bytes だけになる。
- **この検索は語の選び方に強く依存する。**語を変えれば O12/O10 の hit は増えうるし、
  一般語 (`write-path`, `repo root`, `trailer`) は他文脈の誤検出を含む。
  **数値を「発火実績なしの証明」として使ってはならない** — 反証が見つからなかったという弱い信号である。

## 検査側の事実

- 節の削除は `tools/check_docs.py` の `_OPERATION_NUMBERS` と `STAGE_DISPATCH_CONTRACT` /
  `REQUIRED_REFERENCE_SECTIONS` / 条件 dispatch 表の同時更新を要求する (3 面共用の閉包検査)。
  先例 = `DW-O07` (T-154(1), 2026-07-28)、`DW-O15` (T-450)。削除は機械的に可能で、痕跡もコメントで残る。
- `DEV_WAVE_AGGREGATE_BYTES = 25_200` が実効 gate。個別 cap 総和 26,750 は ceiling の 110%
  (27,720) 以内なので、**1 file の cap を上げても集約が先に落ちる**。
