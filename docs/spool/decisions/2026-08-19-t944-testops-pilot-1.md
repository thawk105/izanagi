---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-19
wave: t944-testops-pilot
seq: 1
---

## {{D:t944-testops-pilot-v2}}. 有界 task-run 観測 pilot v2 — D341 の実装を確定する

**決定:** D341 (Q1〜Q3=(a)(a)(a) 確定) の制約下で、`tools/task_runs/generation.py` を新設し、
`tools/run_tests.py` の実行を repo 外の repo 兄弟 (git-common-dir 由来) へ自動記録する
series/generation manager を実装した。既存の `task-run/v1` schema は変更しない。以下の設計判断を
本 wave で確定させた。

1. **記録先の導出は digest 方式を採らない。** `git rev-parse --git-common-dir` の realpath の
   親を repo root とし、`<親>/<repo名>-task-runs/` を既定 base にする。repo 兄弟は親ディレクトリ内で
   既に一意 (別 clone は親が違うので自然に分離) であり、D341 が言及した precedent
   (`izanagi-thirdparty-cache` 等) の解決アルゴリズムを踏襲する digest 方式は不要と判断した。
2. **B4 (bounded scope の非 CHILD_RC outcome) は診断のみへ scope 縮小する。** 段2 plan は
   route/outcome/child_started を record するため schema field 追加を伴う設計だったが、
   `task-run/v1` の exact-key 契約を変更しない brief の不変条件を優先し、CAP_OOM・timeout・
   dispatch infra 失敗では task_run event を作らず固定 diagnostic 1 行のみにする形へ縮小した。
3. **explicit-only な次世代生成の強制は call-graph meta-test で行い、opaque capability は
   採用しない。** 本機構の脅威モデル (dev-only observability tool、単一マシン、無敵対者) では
   Python レベルの呼出し規約保護で十分であり、暗号学的な capability 機構は D205 のプロトタイプ
   基準に照らして過剰と判断した。
4. **damaged/unknown な root への `start_run()` は拒否しない (pre-existing v1 互換を維持)。**
   段5〜6 で「damaged 時に拒否すべきか」の往復があったが、既存テスト
   `test_validate_root_classifies_damaged_and_unknown` が pre-existing v1 の意図的な設計
   (診断専用の `validate_root()` と書込み可否は独立) を明示していたため、これに合わせた。
   cap 判定の分母を published+incomplete+damaged の合計にすることで、damaged を使った
   cap 突破という実害は別途閉じている。
5. **sidecar は専用 0700 lease directory + 固定 basename** (`pytest-stats.json`)。
   既存 `tools/task_runs/pytest_stats.py` の `_create_sidecar()` は basename 完全一致と
   `O_EXCL` (未存在必須) を要求するため、generation.py 側は directory だけを予約しファイル自体は
   子プロセス側 (pytest_stats.py) に作らせる設計にした (既存の manual 経路
   `_private_sidecar()` と同型)。

**理由:**
- D341 は Q1〜Q3 (再開の形・記録先・被覆範囲) を確定させたが、実装レベルの技術選択
  (schema 変更の可否、TOCTOU 対策の強度、cap 計算式) までは決めていなかった。本 wave はこれらを
  段4裁定と段6の敵対レビュー・fix サイクルを通じて確定させた。
- 段6 の2レンズによる敵対レビューが、cap 判定の迂回 (damaged/incomplete が cap を消費しない)
  という最重要のバグを独立に検出した。これは D66/D341 が意図した「有界 pilot」という前提を
  直接損なうものであり、最優先で修正した。

**却下した選択肢:**
- schema 世代を増やして route/outcome/child_started を record する (B4 の当初案) —
  `task-run/v1` の exact-key 契約を変更することになり、D66 の privacy-by-simplicity 設計と
  brief の不変条件に反する。
- opaque capability token による explicit-only 生成の強制 — 本機構の脅威モデルに対して
  過剰な複雑性。
- damaged/unknown な root への `start_run()` を拒否する設計 — pre-existing v1 の既存テストが
  明示的に禁じている挙動であり、cap 分母修正で実害は既に閉じている。

6. **変異matrix検証専用に、`run_tests.py` の dispatch walltime を環境変数
   (`IZANAGI_DISPATCH_WALLTIME_OVERRIDE`) で上書き可能にした。** hang_risk 変異
   (m04) の検証で PBS 既定 walltime (1時間) 固定のまま毎回待たされる非効率をユーザーが
   指摘し、`dispatch_compute.dispatch()` が元々公開している `walltime` kwarg へ
   `run_tests.py` から到達できなかった構造的欠落を解消した。未設定時は従来どおり挙動不変。
   本体コードでなくテスト・運用専用の逃げ道であり、ユーザー向け機能としては文書化しない。

**未閉鎖として記録する残件 (段7時点):**
- **m04 (lock timeout保護を外す変異) は変異matrixから除外した。** 3回の実dispatch観測
  (各30分以上ノータイムアウト、うち2回はPBS壁時間まで完走を確認) により「保護を外すと
  無限にblockする」という被験対象の性質自体は十二分に実証済みだが、`dispatch_compute.py`
  が「PBS強制終了されたjobは正常完了マーカーを残せない」ため、walltime値に関わらず
  毎回 orphan-hold に落ちる構造的非互換がある。これは `tools/mutation_harness.py` /
  `tools/pegasus/dispatch_compute.py` 側のtooling限界であり、本waveの実装コードの
  問題ではない。次にhang_risk変異を使うwaveで再発した場合の改善候補は
  handoffの自己改善候補3を参照。
- 実 dispatch (Pegasus compute node) での sidecar 往復は、テストとしては実装済みだが
  `IZANAGI_RUN_REAL_DISPATCH_TEST=1` を明示しないと skip される。親が受入検証時に実測できたかは
  worklog 本文を参照。
- signal (KeyboardInterrupt/SystemExit) 発生時の lease cleanup は主要経路で `finally` により
  保証したが、一部の稀な例外経路 (admission/queue/Popen wait 中) では未保証のまま残る。
  D205 の脅威モデル (単一マシン、無敵対者) に照らし許容できる残存リスクと判断し、追加の fix
  ラウンドは行わなかった。
