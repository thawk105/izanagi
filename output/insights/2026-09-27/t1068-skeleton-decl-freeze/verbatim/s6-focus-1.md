### 対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| A-1：buildcache の 7 件が `ValueError` | **closed（静的確認）** | 借用元は `Transaction::abort()` 形です。[元 fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_s1_direct_comparison.py:429)。修正後は検索に依存せず、クラスと関数全体を凍結形へ置換し、末尾も閉じています。[置換箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_buildcache_v2.py:5695)。 |
| F2：reflux の 3 件で `ADD_ANALYSIS` が未知マクロ | **closed（静的確認）** | 合成 checkout が cache 値と universal な TU 定義を供給します。[合成 Options.cmake](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_reflux_campaign_issuer.py:136)。供給形は[実 CCBench](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/external/ccbench/cmake/Options.cmake:14)と一致し、未知マクロ検査自体は維持されています。[検査箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/source_digest.py:1890)。 |

### 所見

新規の must-fix 所見はありません。差分では既存テストの受理・拒否、例外 message、件数の期待値は変更されていません。buildcache の 7 パラメータと依存 option の各 assertion も残り、観測点は `build_options` と configure 引数のままです。[観測・期待値](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_buildcache_v2.py:5747)。

`ADD_ANALYSIS` は fixture の実 TU 供給表へ追加されており、`source_digest` の許可集合や `CONTEXT_MACROS` を広げていません。他の未知マクロは引き続き拒否されます。[未知マクロ拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/campaign/source_digest.py:1905)。借用元の `_FAKE_GATE_TRANSACTION_CC` は変更されておらず、F1 の置換は当該テストの private checkout 内に限られます。[借用元](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1068-skeleton-decl-freeze/orchestrator/tests/test_s1_direct_comparison.py:596)。

## 総括

**GO** — 静的再レビューで新しい受理穴、過剰拒否、所有外テストへの波及は見つかりませんでした。  
A-1 の検索失敗原因は除去されています。  
F2 は実 CCBench と同じ経路でマクロを供給し、T-148 の検査を緩めていません。  
既存テストの期待値と buildcache の本来の観測は維持されています。  
この判定は静的検査に限ります。焦点走 10 件の実際の緑は、親による計算ノードでの再走結果で確定してください。