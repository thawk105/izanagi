# tools/ — 実行場所の契約

このディレクトリのスクリプトを**追加・変更するとき**と、Pegasus 上で**実行するとき**に読む。
規範の正本は `docs/pegasus-runbook.md` §7 であり、数値・exact task 一覧をここへ複写しない。

## 発火する命令

1. **`hostname` が Pegasus のログインノード (`pegasus0N`) なら、そのスクリプトの実行場所を
   決める前に分類する。** 分類は runbook §7.0 の 3 値 (`local-ok` / `dispatch-required` /
   `unknown`) で、判定量は「同時に生きる全子孫を含む cgroup の charged memory のピーク」である。
   per-process のピーク RSS を代理値にしてはならない。**実測はユーザー端末の手番で、
   AI・自動化は測らず依頼する** (§7.0)。
2. **`unknown` は `dispatch-required` と同じに扱う。** 測っていないもの、入力サイズに上限が無く
   実行ごとに変わるものを、軽い側へ倒さない。
3. **`dispatch-required` をログインノードで走らせない。** 自動で計算ノードへ送られる exact task は
   runbook §7.0 の表が唯一の正本である。表に無いものは自動化されていないので `qsub` / `qlogin` で
   自分で計算ノードを確保する。sanctioned な経路が無ければ**走らせずに止める**。
   dispatcher の task を勝手に増やさない — 追加には D105 の supersede が要る。
4. **新しいスクリプトを足すとき、または既存スクリプトの入力・並列度・依存を変えるときは、
   分類をやり直す。** 前回 `local-ok` だったことは今回の根拠にならない。

## なぜ場所でなく量で判定するか

ログインノードは共有で、per-user cgroup の上限は 1 つしかなく swap は無い。上限を超えると
OOM killer が同じ cgroup から犠牲を選ぶため、**上限を超えさせた張本人とは別のプロセスが死ぬ**。
重い処理を閉じた列挙で持つと、載っていない新しい重い処理が他人のセッションを殺す。判定を
実測量に置けば、一覧を更新しなくても**判定の対象**にはなる。

**機械強制は 3 層で、どれも全経路は覆わない。** (1) path ごとの registry gate は `tools/pegasus/`
配下だけ (正本 `tools/pegasus/admission_registry.json`、[T-522])。(2) path を問わない重量 command
gate (`pytest` / `cmake --build` 等)。(3) entry point 自身の site gate。`check_docs.py` は task 表と
`TASKS`、registry と docs の投影一致を検査する。
**3 層の外は緑のまま通り、人・cron・IDE・他 AI・`python3 -c` も止まらない。**

計算ノード側の資材 (certification / floor / 劣化梯子の job script と submitter) は
`tools/pegasus/README.md`、Pegasus 全体の操作は `docs/pegasus-runbook.md` を引く。
