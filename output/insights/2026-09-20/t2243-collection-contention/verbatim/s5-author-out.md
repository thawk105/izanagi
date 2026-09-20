## 実装した内容

所有する 2 ファイルだけを新規作成しました。commit はしていません。

- [probe.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2243-probe/tools/t2243_collection_contention_probe.sh)：裁定 §3 の順序、環境設定、計測、集合比較、C skip、結果回収・終了処理。
- [aggregate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2243-probe/tools/t2243_collection_contention_aggregate.py)：標準 library のみ。指定順の Markdown・JSON、導出値、判定、欠測を出力。

cache-references は指定イベントに含まれないため、通常の cache-miss rate は `n/a`、補助値として cache-misses/instructions を出します。

## 実走した検査 (command と出力の逐語)

```bash
bash -n tools/t2243_collection_contention_probe.sh
printf 'bash-n rc=%s\n' "$?"
```

```text
bash-n rc=0
```

```bash
PYTHONDONTWRITEBYTECODE=1 python3 /tmp/t2243-author-synthetic/check.py
```

```text
positive: cells=12 missing=19
negative: cells=12 missing=115
no-contention: positive C=no-contention; negative C=cpu-time-inflation: PASS
wait-dominant: positive L=wait-dominant; negative L=no-contention: PASS
cpu-time-inflation: positive R=cpu-time-inflation; negative R=wait-dominant: PASS
H-supported: positive=H-supported; negative=H-not-supported: PASS
H-not-supported: positive=H-not-supported; negative=H-supported: PASS
metrics, Lustre count/sum, perf IPC/misses-per-instruction, delta and residual: PASS
boundary-0: cells=12 missing=115
boundary-1: cells=12 missing=115
boundary-2: cells=12 missing=115
boundary-3: cells=12 missing=115
boundary-4: cells=12 missing=115
threshold boundaries (1.15; H 5,10,15): PASS
cells=6 missing=74
C skip, failed cell excluded, missing halves/perf/Lustre, X rc=5, ref drift: PASS
cells=0 missing=31
empty input: PASS
ALL SYNTHETIC CHECKS PASSED
```

```bash
git status --short --untracked-files=all
```

```text
?? tools/t2243_collection_contention_aggregate.py
?? tools/t2243_collection_contention_probe.sh
```

## 合成入力での正例・負例

全腕の N=1 は wall=10、CPU=5 秒。両半で同じ値を与え、N=48 を以下にしました。

| label | 正例 | 負例 |
|---|---|---|
| no-contention | C: wall=11、CPU=5 | C: wall=20、CPU=8 |
| wait-dominant | L: wall=20、CPU=5 | L: wall=11、CPU=5 |
| cpu-time-inflation | R: wall=32、CPU=8 | R: wall=15、CPU=5 |
| H-supported | Δbc=12 秒 | Δbc=4 秒 |
| H-not-supported | Δbc=4 秒 | Δbc=12 秒 |

各 label の出現・非出現を、実際の CLI 出力 JSON に対して検査しました。依存先の stub はありません。

[検査コード](/tmp/t2243-author-synthetic/check.py)、[正例出力](/tmp/t2243-author-synthetic/positive.md)、[負例出力](/tmp/t2243-author-synthetic/negative.md)を残しています。

## 実装済み・未実走のもの

計算ノードの probe 全体は**実装済み・未実走**です。collection、30 cell の測定、clone・rsync、実機 perf/Lustre、異常終了時の回収処理は未検証です。

pytest nodeid の実走はありません。今回の検査範囲は Bash 構文と集計の合成入力のみで、親の全走を代替しません。

## 波及の静的列挙

所有外 caller・共有 fixture・consumer test への変更は**無し**。既存ファイル、受理集合、conftest、docs は変更していません。

## 総括

2 ファイルの実装と許可された検査を完了しました。親による wave 専用ディレクトリへの複製・計算ノード実走に引き渡せます。