指定 6 ファイルをすべて読了しました。以下は静的検査です。pytest と probe 本体は実走しておらず、既存 receipt を緑の実測として数えていません。preview の `working_diff` SHA-256 と `diff_digest` の一致だけ、読み取り専用で再計算しました。

## 総括

### (1) must-fix 候補

- **A-1 [恒真ゲート] [テスト代表性] [誤前提] [捏造/幻覚] — wire と preview evidence が束縛されていない。**  
  [liveness_probe.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:116) は `--wire` と `--preview-json` を独立入力として受け、[同:120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:120) は `passed` と digest の形式しか検査しない。driver 出力自体にも入力 wire field はない（[p3_s4_loop_trigger_gating.py:778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/orchestrator/campaign/p3_s4_loop_trigger_gating.py:778)）。したがって wire A の preview JSON と任意の正準 wire B を組み合わせても C-a〜C-e が全 PASS しうる。現在の `preview-wire-11111.json` は、静的再計算では `working_diff` と digest が一致し、diff も `11111` の既存 golden と整合するため、今回の具体値が偽造されたとは判定していない。ただし、その対応関係を probe 自身は証明しない。  
  **成果物影響:** receipt の `wire`、`sealed.evidence_digest`、`checks.C-c2=true` が無関係な組を記録でき、レポート上の「実 E driver → ledger 結線」という参照の受理集合が、対応する組から直積全体へ拡大する。

### (2) nit

- **C-c1 は独立 oracle ではない。** [liveness_probe.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:97) は、ledger が [reflux_origin_ledger.py:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/orchestrator/campaign/reflux_origin_ledger.py:1051) で使う同じ `reflux_ir.parse_wire/encode_wire` を再呼出ししている。共有 canonicalizer の変異には共動するため、C-c1 単独の純増検出力はない。ただし `11111` は既存の全 32 wire golden で独立に固定済みなので、今回の具体値の生死は無効にならない。  
  **成果物影響:** 共有 parser の受理集合が誤って拡大した場合、receipt の `checks.C-c1` も真のままになりうる。

- **出力 artifact の scope 限定が自己完結していない。** docstring は [liveness_probe.py:4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:4) で fixture・非 production を明記する一方、[同:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:99) の receipt と [同:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:108) の stdout には fixture/placeholder 限定がない。  
  **成果物影響:** receipt 単体を参照したレポートが、fixture 生死を production/P3 証拠として誤読しうる。既存 docstring と `outcome_semantics` があるため must-fix ではなく nit とした。

- [liveness_probe.py:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:1) は 129 行で、段4裁定の 100 行以内に違反する。成果物値・受理集合・参照への影響を書けないため `DW-G05` に従い nit。

- **fixture 乖離:** [liveness_probe.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:26) の manifest は架空 hash・存在しない evidence ref・実験用 budget を持ち、現在の production authority は `origins=[]`。機械的には authority schema を満たすが、統治上 production provisioning 可能な manifest ではない。これは明示済みの fixture 生死を無効にしないが、production への一般化は完全に無効。

### (3) M-1〜M-4 の静的判定

- **M-1: 赤になる。** 負例は cardinality=2、query=2/3、iteration=1、未使用 batch/operation ID、現行 CAS、`imax=2`・`qmax=4` を満たす（[liveness_probe.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:90)）。distinct 項だけを恒偽化すると [ledger:1102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/orchestrator/campaign/reflux_origin_ledger.py:1102) 以後の拒否理由はなく commit が受理され、`duplicate_rejected=False` となり C-d が FAIL。受理集合が変わるため F113/F126 型の偽 kill ではない。

- **M-2: 赤になる。** 同一 wire の opened member は replicate 0/1（[liveness_probe.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:76)）。期待値を常に 0 にすると二件目が [ledger:1234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/orchestrator/campaign/reflux_origin_ledger.py:1234) で拒否され、positive transaction 自体が不受理になる。後段 mask はない。

- **M-3: 赤になる。** probe は [liveness_probe.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py:46) で member preimage を独立生成している。ledger 側だけ wire field を落とすと、seal 時の再計算値が prepared commitment と一致せず [ledger:1250](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-liveness/orchestrator/campaign/reflux_origin_ledger.py:1250) で拒否される。登録済み M-1〜M-3 に関する I6 の実質破れは静的には認めない。

- **M-4: 赤にしない、rc=0 見込み。** 現行経路では C-a〜C-e を満たす。既存 receipt も全 true だが、これは今回の実走結果ではなく参考 artifact に留める。

C-d の broad catch は将来別理由を mask しうるが、現行 fixtureについては別拒否理由をコード上すべて排除できるため、**[変異帰属] は一意**。C-e は独立した before/after replay snapshotを固定値 `(0,2,0,1)` と比較しており、自分で書いた値の読み直しだけではない。

### (4) 純増検出力の1行結論

既存テストは positive 3-event cycle、duplicate commitment、同一 wire R=2、counter、seal 読出しを既に被覆しており、純増は「凍結 preview の具体的な `11111` と `7919…dc6` が fixture ledger を通る」一点だけ。ただし A-1 により両値の同一 driver invocation への機械的束縛までは証明していない。

### (5) 名乗り過剰

docstring 本文には production/P3/outcome の過剰主張はない。一方、A-1 の未束縛のまま「実 E driver の wire と digest の結線」と名乗ること、および fixture 限定を持たない receipt/stdout 単体には名乗り過剰の余地がある。P3 充足、production provisioning、候補 batch、実行 outcome、kill-before-commit、科学的有効性を直接名乗る記述は見つからなかった。