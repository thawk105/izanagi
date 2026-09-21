/dev-wave 引数 (ユーザー、2026-09-21 起動、逐語):

mocc 第 2 例 (D2114、クロスプロトコル) の certified 系列に要る X/P 計装を pin 候補へ載せる。T-2294 (D1686) で patch
  水準まで済んでいる mocc の X (lock 被覆) / P (permutation 保存) 計装 (RWLOCK と CLL を真実源とする、entry 1240) を、現行 pin e9e477ca の G2
  read-from witness hook 系統の ccbench submodule branch へ統合する (D579 の AI 限定 authoring)。あわせて positive / negative control と D1603
  の材料 3 点 (候補 commit・D297 同一性検査・波及範囲) を揃える。冒頭で patch と hook branch の合流関係を確かめる。I (write-intent) 面
  ([T-2295]) を同時に閉じられるかは未確認なので完了条件にせず、残れば不足として明記する。push・gitlink と CCBENCH_FULL_SHA の更新・pin
  再承認の提示・探索の開始 (D2134 項 9 の別判断) は含めない。push は人間が行い、再承認は D2114 項 3 の見送り台帳経路で諮る。先例は D2150 と out
  put/insights/2026-09-17/t2757-mocc-mutation-proof-design/README.md、output/insights/2026-09-19/t2773-mocc-template-wave2/README.md。CCBench
  の改変は D16 / D18 / D20 に従う。実装は Codex author (D95)。規律 2 は緩めない。着手直前の local main から fresh
  worktree。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
