# tools/ — 実行場所の契約

このディレクトリのスクリプトを**追加・変更するとき**と、Pegasus 上で**実行するとき**に読む。
規範の正本は `docs/pegasus-runbook.md` §7 であり、数値・exact task 一覧をここへ複写しない。

## 発火する命令

0. **テストと provenance 履歴監査は `run_tests.py` / `check_ai_provenance.py` を通す。**
   両者が空きメモリと queue 可用性を見て実行場所を決める ([T-300]、runbook §7.0.0)。
   性能測定は対象外で常に計算ノード。場所を固定するなら `--force-dispatch`。
1. **`hostname` が Pegasus のログインノード (`pegasus0N`) なら、そのスクリプトの実行場所を
   決める前に分類する。** 分類は runbook §7.0 の 3 値 (`local-ok` / `dispatch-required` /
   `unknown`) で、判定量は「同時に生きる全子孫を含む cgroup の charged memory のピーク」である。
   per-process のピーク RSS を代理値にしてはならない。**実測はユーザー端末の手番で、
   AI・自動化は測らず依頼する** (§7.0)。これは registry の path 粒度 admission で、
   0 の動的判定とは別層である。
2. **`unknown` は `dispatch-required` と同じに扱う。** 測っていないもの、入力サイズに上限が無く
   実行ごとに変わるものを、軽い側へ倒さない。
3. **`dispatch-required` をログインノードで走らせない。** 自動 dispatch される exact task は
   runbook §7.0 の表が唯一の正本。表に無いものは `qsub` / `qlogin` で自分で確保し、
   sanctioned な経路が無ければ**走らせずに止める**。task を勝手に増やさない (D105 の supersede が要る)。
4. **新しいスクリプトを足すとき、または既存スクリプトの入力・並列度・依存を変えるときは、
   分類をやり直す。** 前回 `local-ok` だったことは今回の根拠にならない。

## なぜ場所でなく量で判定するか

ログインノードは共有で、per-user cgroup の上限は 1 つしかなく swap は無い。上限を超えると
OOM killer が同じ cgroup から犠牲を選ぶため、**上限を超えさせた張本人とは別のプロセスが死ぬ**。
閉じた列挙で持つと、載っていない新しい重い処理が他人のセッションを殺す。

**機械強制は 3 層で、どれも全経路は覆わない。** (1) registry gate
(正本 `tools/pegasus/admission_registry.json`、射程は runbook §7.0。[T-522] / [T-639])。
(2) path を問わない重量 command gate。
(3) entry point 自身の site gate。**3 層の外は緑のまま通り、人・cron・IDE・他 AI も止まらない。**

計算ノード側の資材 (certification / floor / 劣化梯子の job script と submitter) は
`tools/pegasus/README.md`、Pegasus 全体の操作は `docs/pegasus-runbook.md` を引く。
