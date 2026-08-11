静的レビュー結果は **NO-GO** です。pytest・build・実測は行っていません。

### 1. [severity: must-fix] critic の修正指示が「計算のみ」を保証してしまっている

根拠: [digest.py:691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/critic/digest.py:691) は、有限 denylist の検出項目を除けば hole が「計算のみ」になると読める文言を出します。これは scanner 自身が列挙する未検出残余 [coder_effect_gate.py:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:7) と矛盾し、テストもこの過大表現を固定しています（[test_p3_s4_loop.py:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:831)）。

成果物影響: critic の次手入力が、deny table 適合を「計算のみ」の affirmative security credit と誤認させます。

修正提案: 「有限 lexical policy が報告した identifier/loop 形を除く。通過は計算のみ・host 安全性を証明しない」と明記し、テスト期待値も更新してください。

### 2. [severity: must-fix] V-8 の未閉鎖層が docstring に列挙されていない

根拠: scanner の module docstring は lexical 検出残余だけで終わっています（[coder_effect_gate.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:4)）。`diff_quarantine.py` も capability/cache/replay を一般論で触れるだけです（[diff_quarantine.py:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/diff_quarantine.py:20)）。V-8 指定の `p3_s4_red.py`、手動 patch、直接 buildcache、`s5_permutation_coverage`、shell materializer、cache/WAL/COMMIT/freeze 非束縛は列挙されていません。`forbidden_identifiers` も依然固定空配列です（[p3_autonomous_workload_trial.py:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_autonomous_workload_trial.py:652)）。

成果物影響: hole seam の局所的拒否を、coder-derived build・cache・proof chain 全体の閉鎖と誤読できます。

修正提案: module docstring に V-8 の全項目を「scope 外・未閉鎖」として逐語的に列挙してください。

### 3. [severity: must-fix] V-1 の「scanner bytes＝materialized hole bytes」をテストが固定できていない

根拠: 実装は元の `implementation` を走査します（[p3_s4_loop.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:239)）。しかし結合テストは scanner/render の引数一致と、書込 source に `implementation` が部分文字列として存在することしか確認していません（[test_p3_s4_loop.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:237)）。renderer が未走査 bytes を追加・変換する変異でも、この検査は通り得ます。

成果物影響: scanner が通した bytes と build source の hole bytes が乖離しても、V-1 のテストが緑のまま残ります。

修正提案: materialized source から marker の hole を再抽出し、harness 所有のインデント変換を除いて scanner 入力と byte-exact に比較してください。

### 4. [severity: must-fix] V-6 の「全投影」テストが S6 provenance を検査していない

根拠: `test_candidate_value_literal_and_implementation_bytes_never_reflect_to_projections` は例外表現・WAL・critic render だけを連結しています（[test_p3_s4_loop.py:798](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/tests/test_p3_s4_loop.py:798)）。一方、S6 は例外を `str(e)` として provenance に保存します（[s6_sort_sweep.py:301](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/s6_sort_sweep.py:301)）。この経路はテストされていません。

成果物影響: candidate-triggered 例外の将来回帰で生成 bytes が provenance に残っても、非反射テストが検出できません。

修正提案: S6 の例外隔離から provenance 書込までを sentinel 付きで通し、`error`、ログ、永続化 JSON の全てで非反射を確認してください。

確認済み事項:

- 指定4ファイルに `advisory` は残っておらず、固定文言は入っています。
- V-7 の全残余と `while (true) { break; }` の保守的拒否は [coder_effect_gate.py:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/coder_effect_gate.py:7) に揃っています。
- backoff テストは synthetic seam contract と明記され、実路 E2E を主張していません。
- scanner には実 consumer があり（[p3_s4_loop.py:243](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-semantic-gate-impl/orchestrator/campaign/p3_s4_loop.py:243)）、sort driver の拒否・WAL consumer まで静的に配線されています。
- D127(6) の caller 自己分類・非意味境界という訂正は巻き戻されていません。

## 総括

NO-GO。blocker はないものの、must-fix が4件あります。  
特に critic の「計算のみ」は D-2 を直接越える affirmative security claim です。  
V-8 の未閉鎖層、V-1 の byte-exact binding、V-6 の S6 投影検査も裁定どおり固定されていません。  
これらを是正したうえで再レビューが必要です。