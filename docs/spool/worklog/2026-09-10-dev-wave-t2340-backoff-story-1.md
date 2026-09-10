---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2340-backoff-story
seq: 1
title: [T-2340] backoff単独論文の日本語ストーリーを全面再導出する（docsのみ）
---

## 本文

- 入力は8ca260c3dの既着地正典。D1637・D1936項28/36とT-2340の発火条件を確認し、旧版は不変のまま全面再導出した。
- 滞在分布による混合の支持、旧歩行modelの失敗の射程、方向的中率の解釈訂正、異なるcohortの局所ITT、動的化の優越仮説棄却を論旨へまとめた。
- 計装なしの部分認証を計装入り試験へ転用せず、旧解析未移行と900us超の定数外挿を明記した。高域比率はD1936項36の3.1%とT2188本文の15.1%を出所別に示し、新たな補正値を作っていない。
- 起動時の同名worktree/handoff重複は検出されなかった。insights-date-layoutの中断handoffを読み、資料移動ゼロと未採用差分を確認して非接触を維持した。
- T2417は入力時点では未land。作業中にe4e5fe053で実landしたため、凍結本文を保持しREADMEの入力後注記で着地と未認証・条件付き結果の所在を指した。
- D95のdocs-only契約で子ゼロ、実装面差分ゼロ。変異matrixはDW-S04で免除。新規測定・tail解析移行・追加認証・英訳・図昇格は行っていない。
- 本文commit a0306c51eとphase完了項を同居させた。共有phaseの追記競合は固定main0de9d75ecをmergeし、双方の項を保持するdocsのみの解消で閉じた。
- 記録前のcheck_docs/check_codex_agents/diffチェックはrc0。全史provenanceは本文後9449件、merge後9459件、新規違反0・known56。
- 受入1は1f7f21dc9で22488 passed /68 skipped /1 failed。SIGTERM無視childの10秒timeoutはF273型。同tipの単独再走991516は1passed/7.53秒、job Elapse13Sで非再現。制限値・期待値・除外は変更していない。
- 受入2はmain取り込みの文書競合でテスト未開始。受入3は59b932731で22563 passed /68 skipped /28 setup error。全28件はt1259のautouse fixture内Git走査30秒timeoutで、同tipの単独再走991541は51passed/15.45秒、job Elapse21Sで非再現（{{F:t1259-git-snapshot-timeout}}）。
- 両失敗は本文の判定・コードへの変更によらず、単独非再現を確認してDW-O18の受入再走へ進めた。最終受入はこの記録を含むtipで行い、その受領証をlandへ渡す。先行の赤を緑に読み替えない。
- 専用handoffとraw検査ログはrepo外 /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2340-backoff-story/。待機のRUN略記はPre-runningを含んでいたため、実行時間はrunnerとscheduler会計を使った。
- dev-wave改善候補はなし。自己改善契約を終端で再読し、既存DW-O18/O23で扱える実測失敗と競合の記録に留める。改善実装・次wave起動・pushは行わない。

## 次の一手差分

### 完了

- [T-2340] 既着地正典から日本語ストーリー次版2026-09-10.mdを全面再導出した。支持・反証・限界と旧版の到達差を整理し、旧版不変・診断性能非昇格・別紙の境界を維持した。
  remaining: none
  base: 5f66ecbff50a9bdd1529f090e9bc4cc14d1e09b8b86177821fe1005857c8f15c
