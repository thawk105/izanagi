# 段 4 のための親の追加実測 その 2 (2026-08-26 02:30 JST)

## D. 公式契約 DW-M07 は inner-local を名指しで禁じており、理由は自壊である

`docs/dev-wave/mutation.md` の `DW-M07` は逐語で次を定める。

- 「本走は `--runner-mode dispatch` を既定とし、runner argv へ `--force-dispatch` を入れる。」
- **「runner の実行経路を変異させる local は runner が自壊し収集段が `rc=16` になる。」**
- 「`--attempt-out` と `--wrapper-attempt` は **dispatch 専用の同時指定必須ペア**で、
  片方のみ・local 指定は起動前に中止する。」

**段 2 プランの #2 は「local mode でも attempt sidecar を許可する」と提案しており、
この 3 行目と正面から衝突する。** プランはこの衝突を認識していない。

### なぜ単なる docs 更新では済まないか

2 行目が理由を述べている。**dispatch mode の存在理由は、収集段を「変異させられた runner」から
隔離することである。** dispatch では収集が `dispatch_compute.py --task tests` を通るため、
`run_tests.py` を壊す変異があっても収集は生き残る。local では収集が変異後の runner を
使うので自壊する。

**本 wave はまさに runner 経路 (`dispatch_compute.py`) を変異させる。**
したがって本 wave 自身の変異 matrix は dispatch mode を必要とする。
inner-local を既定にすると、自分の変異 matrix が自壊する。

### 段 4 の裁定方針 (親の暫定)

`mutation` task は **dispatch mode を置き換えるものではなく、並存させる**。
新 task が担うのは「wrapper 1 本を計算ノードの 1 job へ束ねる」ことであり、
内側の runner mode を local へ強制することではない。内側が何であるべきかは
変異対象が runner 経路を含むかどうかで決まり、それは spec 側の性質である。

この読みなら DW-M07 の 3 行は変更不要で、契約の受理集合を動かさない。
プランの「local attempt sidecar 許可」「wrapper 固定」「exact full-suite argv」は
いずれも採らない。

## E. 未解決のまま段 4 へ持ち込む論点

1. 内側を dispatch のままにすると、束ねの効果 (queue 回数削減) はどこまで出るのか。
   collection 1 + baseline 1 + 変異 N 回の qsub が、outer 1 + inner (1+1+N) になるだけなら
   **queue 回数は減らず増える**。ここを実測せずに「束ねた」と主張してはならない。
2. したがって T-360 の成果物影響そのものが再検討を要する。
   束ねが効くのは inner-local のときだけであり、inner-local は runner 経路変異で自壊する。
   **この 2 つは両立しない可能性がある。** 両立しないなら、それが T-360 への答えであり、
   裁定パッケージとしてユーザーへ返す候補になる。
