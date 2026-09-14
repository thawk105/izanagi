# B-10 静的 backoff 右 tail 本走 — 投入と集団報告の手順

事前登録は `docs/b10-backoff-static-tail-preregistration.md`、本走 driver は
`orchestrator/campaign/b10_backoff_static_tail_formal.py` である。本書はその 2 つを
Pegasus の投入経路へつなぐ操作手順だけを持つ。格子・判定式・閾値は本書で定めない。

走行種別は `t2500-tail-formal`、成果物 stem は `t2500-backoff-static-tail-formal` である。
いずれも事前登録 §8.2 が定めた値であり、本書はそれを写しているにすぎない。

## 1. 投入前に満たしている必要があること

本走は 3 workload (write-heavy / balanced / read-heavy) を独立 job として投入し、
その 3 本を 1 集団として報告する。投入前に次がすべて成立していること。

1. **投入は repo root から行う。** job は `PBS_O_WORKDIR` を repo root として解決する。
   qsub は作業 directory を指定しないので、投入時の current directory がそのまま job の
   repo root になる。これは既存 3 系列と同じ条件である。
2. **事前登録 commit が、計算ノードから見える checkout の HEAD の祖先であること。**
   driver は `git rev-parse --verify`、`git merge-base --is-ancestor`、`git show <commit>:<文書>`
   をローカルで実行し、fetch はしない。
3. **作業ツリーの事前登録文書の bytes が、その commit の blob と一致すること。**
   一致しなければ driver は測定前に停止する。
4. **探索走 (`t2418-explore`) の campaign directory が実在すること。** 本走は正しさ検査の
   mode をこの campaign から読み、自分の mode と比較する。探索走の数値は本走の判定に入らない。
5. 出力親は repo の外にあり、repo を祖先に持たない絶対 path であること (既存 3 系列と同じ)。

## 2. 3 workload の投入

```
cd <repo root>
tools/pegasus/submit_b10_backoff_grid.sh \
  --run-kind t2500-tail-formal \
  --preregistration-commit <40 桁の commit hash> \
  --explore-campaign <探索走の campaign directory の絶対 path> \
  --output-parent <repo 外の絶対 path>
```

`--preregistration-commit` と `--explore-campaign` は `t2500-tail-formal` のときだけ受け付ける。
既存 3 系列 (`extended` / `t2266-tail` / `t2418-explore`) にこの 2 つを渡すと拒否される。
逆に `t2500-tail-formal` でどちらかを省いても拒否される。

投入に成功すると、出力親に `<group id>.submit.jsonl` が 1 本と、workload ごとの
出力 root・標準出力・標準エラーが作られる。3 本の job はこの group id で結び付く。

## 3. 完走の確認

各 job は、自分の出力 root 直下に `completion.json` を書いて終わる。本走ではこれが出るために、
その job の campaign に次の両方が要る。

- 相異なる 8 genome の commit 記録
- `<campaign>/reports/t2500-backoff-static-tail-formal-execution.json`

driver が非ゼロで終わったとき、および内部の締切で打ち切られたときは、job はここへ到達しない。
`completion.json` が無いことをもって「その job は本走として使えない」と判断してよい。

## 4. 3 本を 1 集団として報告する

3 job すべてに `completion.json` が出てから、repo root で次を実行する。

```
python3.10 -I -B \
  orchestrator/campaign/b10_backoff_static_tail_formal.py \
  --preregistration-commit <投入時と同じ commit hash> \
  report <write-heavy の campaign> <balanced の campaign> <read-heavy の campaign> \
  --explore-campaign <投入時と同じ探索走の campaign> \
  --output-root <集団報告の出力先 directory>
```

- 位置引数は job の出力 root ではなく、**その配下の campaign directory** を 3 つ、明示して渡す。
  glob で自動選択しない。同じ group id の 3 本であることを人が確かめて渡す。
- driver は 3 つの campaign lock 間で集団の同一性を突き合わせ、食い違えば集団全体を無効にする。
- 出力先には stem の `.json`、`.dat`、`-complete.json` が作られる。既存の出力先へは再実行できない。
- 判定が invalid のときも報告は作られ、終了コードは 1 になる。
  **成果物が在ることを valid の根拠にしてはならない。**

## 5. 本書が保証しないもの

- 本書は shell の wrapper を持たない。したがって wrapper の終了コード伝播という検査対象は無い。
  §4 の argv が driver の CLI と一致していることだけを検査で固定している。
- 計算ノード側の資源・混雑・queue の状態は本書の対象外である。
- 本走を実際に投入した実績は本書の作成時点では無い。手順は配線と CLI の実物から書いている。
