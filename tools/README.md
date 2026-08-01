# tools/ — 実行場所の契約

このディレクトリのスクリプトを**追加・変更するとき**と、Pegasus 上で**実行するとき**に読む。
規範の正本は `docs/pegasus-runbook.md` §7 であり、数値・exact task 一覧をここへ複写しない。

## 発火する命令

1. **`hostname` が Pegasus のログインノード (`pegasus0N`) なら、そのスクリプトの実行場所を
   決める前に分類する。** 分類は runbook §7.0 の 3 値 (`local-ok` / `dispatch-required` /
   `unknown`) で、判定量は「同時に生きる全子孫を含む cgroup の charged memory のピーク」である。
   per-process のピーク RSS を代理値にしてはならない。
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
OOM killer が同じ cgroup の中から犠牲を選ぶため、**上限を超えさせた張本人とは別のプロセスが
死ぬ**。したがって「重い処理の一覧」を閉じた列挙で持つと、列挙に載っていない新しい重い処理が
他人のセッションを殺す。判定を実測量に置けば、一覧を更新しなくても**判定の対象**にはなる。

**ただしこれは prompt 規律であって機械強制ではない。** 分類 registry も、実行直前に未分類を
拒否する gate も存在しない。`tools/check_docs.py` が検査するのは runbook の exact task 表と
dispatcher の `TASKS` の同期だけで、新しい高メモリスクリプトを追加しても緑のまま通る。
**この文書を読まなかった人・cron・IDE・他 AI は止まらない。**

計算ノード側の資材 (certification / floor / 劣化梯子の job script と submitter) は
`tools/pegasus/README.md`、Pegasus 全体の操作は `docs/pegasus-runbook.md` を引く。
