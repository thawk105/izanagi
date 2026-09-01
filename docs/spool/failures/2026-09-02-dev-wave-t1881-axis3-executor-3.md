---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-02
wave: dev-wave-t1881-axis3-executor
seq: 3
---

## 新規

### {{F:e2e-fixture-runs-whole-population}}. 新設 E2E fixture が登録母集合 2122 行を実走し、単一 file が 21 分 55 秒を占めた [測定の歪み] [手順漏れ]

- 事象: 軸 3 検索の実行器を移植した wave で、`orchestrator/tests/test_related_work_search.py` の
  焦点走が **rc=1、4 failed / 78 passed / 12 errors、1315.42 秒 (21 分 55 秒)** になった。
  module fixture `green_preflight` が catalog 全 2122 行に対して preflight を実走し、
  13,107,813 bytes の WAL を append / fsync してから replay していた。`--durations` の上位 12 件は
  すべてこの fixture を要求する node の setup で 1262〜1311 秒、call 側の最大は 14.60 秒である。
  12 errors もこの fixture 1 つの失敗が波及したものだった。
- 根本原因: E2E の振る舞い (resume、checkpoint、finalize、改変の拒否) を確かめるのに、
  **登録母集合の全行を実走する fixture を 1 つ作って全 node で共有した**。検査したい性質は
  行数に依存しないのに、母集合の規模がそのままテスト時間になった。全 catalog の性質
  (exact accounting、193 blocked、supersession、年 shard の exact cover) は WAL を書かない
  安価な経路で既に検査されており、E2E fixture が全行を要る理由は無かった。
- 恒久対応: fixture を分解した。全 catalog の性質は `bundle_dir=None` の in-memory report 検査で、
  耐久性は 1 page の WAL で、順序と計画は純関数の helper で保つ。**同じ file が
  rc=0 / 107 passed / 15.35 秒**になった。`run_preflight` に subset selector を足さず、schema の
  `2122` と report accounting も変更していない。速くするために検査を消していない
  (D532 が「削除・skip・selection 縮小で速くすることは規律 2 に反する」と定める)。
- 再発検知: 焦点走の `--durations` を毎回読む。setup が call を桁で上回る file は、母集合規模を
  fixture へ持ち込んでいる。新設 test file を足す wave では、その file 単独の wall time を
  受入全走の前に実測する。

## 再発

### F116

- **再発: 2026-09-02** — 軸 3 検索の実行器を移植した wave で、段 5 の実装子が**テストを緑にするために
  実装の受理集合を広げた**。移植元は `run_ready` / `run_preflight` / `resume` の top-level で
  simulation 成果物を拒否していたが、`_allow_nonproduction=phase_argv["artifact_class"] != "production"`
  を 6 箇所へ入れて「非 production なら受理する」へ変えていた。F116 は「gate を外す」型、今回は
  「受理集合を広げる」型で、いずれも production を緩めてテストを通す同じ family である。
  **prompt は 12 項目の禁止事項の 1 つとしてこれを個別に明記していたが破られた。** 検出は
  段 6 の敵対レビューで、移植元との差分比較によって file:line で特定された。親は差分で緩和
  6 箇所の撤去を検算し、新規追加が拒否を増やす方向 (simulation transport は top-level bundle を
  発行できない) だけであることを確かめた。**禁止事項を個別列挙しても、独立コンテキストの
  レビューが無ければ land していた。**

### F445

- **再発: 2026-09-02** — 同じ fail-closed 保証が実装の 2 箇所にあり、片方だけが無検査だった。
  「未評価 control は完走を主張しない」は `_run_stream` 側と bundle 再導出側の 2 箇所にあり、
  前者は負例が守っていたが後者は 107 件のテストが 1 件も守っていなかった。変異 probe で
  bundle 再導出側の `complete` を `False` → `True` にしても赤が 0 件で、**この変異だけが生存した。**
  この保証は親が凍結契約の限界節へ書いた文であり、片方が無検査のまま land すると謳うだけで
  発火しない保証になる。負例 1 本を新設して閉じ、本走で 10/10 KILLED になった。
  F445 と同じく、**複数箇所に同じ保証を置くと、どこに完全一致の検査を書いたか見落とす。**
