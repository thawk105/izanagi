# 段 4 再裁定 — codex は B に反対。条件が満たされていない

## ユーザー裁定と条件

「推奨 B で進めて。ただ、codex に相談し、賛成をもらったらね。」

**賛成は得られなかった。** codex の総括 1 行目は `反対: B`。したがって B は実行しない。

## codex が B に反対した理由 (親が実体で裏取りした)

**B を着地させる「一度きりの land 認可」が現行機構に存在しない。**

- main 側 launcher が runner 不等値を suite 起動前に拒否する。
- land も main/tip の runner object ID 等値を要求する。
- 受入受領証は必須で、その検証は merge より前に無条件で走る。
- D388 が受領証欠落時の flag・環境変数・互換 bypass を**明示的に禁止**している。
- 認可を表す consumer を B の wave 自身へ足すと、**その機構を着地させるために同じ例外が要る**。
- 人間が `git merge --ff-only` を直接叩くのは技術的には可能だが、受領証・provenance・fold・
  postcondition をまとめて迂回するので「安全な一度きり認可」ではない。

## codex の対案 (親が独立に同じ形へ到達していた)

**三段ブリッジ P → Q → R。**

- **P (準備 wave):** `tools/run_tests.py` を **byte 不変**のまま、main 側 launcher から
  `{tested_main, runner の SHA-256}` を閉じた経路で渡し、計算ノード側の子が
  `tested_main:tools/run_tests.py` の blob を読み hash 照合してから実行する機構を入れる。
  この段では等値要求を**残す**。実行器を触らないので通常の受入・land で着地できる。
- **Q (撤去 wave):** P が main に入った後、launcher と land の等値だけを外す。
  Q も実行器を触らないので、P 後の main launcher の旧等値検査を通る。
- **R (実行器 wave):** ここで初めて実行器を編集し、[T-1932] の既定 shard 変更を行う。
  R の受入は P/Q の main 束縛 launcher・dispatcher が判定する。

**等値を外したのに束縛が無い時点が存在しない。一度きりの受領証 bypass も要らない。**

親は codex の出力を見る前に、環境変数の伝播経路 (`_run_blob` が `env=` を渡さないので
launcher の環境が実行器へ継承され、`_dispatch_environment` が `os.environ` を複製する) から
同じ「実行器を触らずに束縛できる」という結論へ独立に到達していた。**二経路の独立一致。**

## codex が親の実測を補正した点 (2 件・いずれも real)

1. **dispatch しない経路にも同じ欠陥がある。** queue 不可用で local budget が得られると
   bounded local 実行になるが、これも `systemd-run ... <worktree>/tools/run_tests.py` と
   pathname 再実行する。親の「必ず dispatch する」は言い過ぎで、正しくは
   「dispatch でも bounded local でも tip 側 file が二段目を駆動する」。
   この経路の是正は実行器の編集を伴うので R の担当になる。
2. **dispatcher 自身も束縛対象である。** 外側の実行器は
   `from tools.pegasus import dispatch_compute` を worktree から import し、
   計算ノードの job script も `DISPATCHER=<worktree path>` を使う。
   runner だけ束縛しても dispatcher は tip 側のままである。

## 親が新たに見つけた未解決点 (P→Q の健全性に直接効く)

**P の束縛を執行するコードが tip 側にある。**

外側の実行器が dispatcher を worktree から import する以上、その import 先を main へ束縛するには
実行器の編集が要る (= R)。したがって P で入れた「計算ノード子の main 束縛」は、
**tip 側の `dispatch_compute.py` が実行するコードによって執行される。**

- 実行器だけを編集した wave は捕まる (P の目的どおり)。
- **実行器と dispatcher の両方を編集した wave は捕まらない。**

D387 の事故モデル (防御対象は事故であって偽造ではない) の下では前者が現実的な母集団なので
P には価値がある。しかし「実行元を tested main の blob に固定する保護を維持する」という
ユーザーの条件を、**Q の時点で完全には満たさない**。満たすのは R の後である。

したがって Q をいつ実行するかは、次のどちらを採るかの判断になる。

- **Q-early:** P の直後に等値を外す。実行器を編集する wave が解禁され [T-1932] が進む。
  ただし「実行器 + dispatcher を両方触る wave」に対しては無防備な期間が R まで続く。
- **Q-late:** R まで等値を維持し、R の中で等値撤去も同時に行う。
  ただし R は実行器を編集するので、**結局 B と同じ一度きり認可が要る**。

**この二択はユーザー裁定に返す。** 前者は規律 2 に対する残余を一定期間受け入れる判断、
後者は D388 の land 権威に例外を作る判断であり、どちらも親が単独で決めてよい種類ではない。

## 親の推奨

**P を先に実装する。** P はどの経路 (Q-early / Q-late / B そのもの) でも必要であり、
実行器を触らないので通常の受入・land で着地でき、後戻りしない。
Q の時期の裁定は P の実装中または着地後に受ければ間に合う。
