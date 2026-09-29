## 総括

**NO-GO。** fix 1〜3 で前回の集計・終端・stock 停止の主要箇所は直っている。ただし、LLM の不正な coder／auditor 出力を A の却下として確定できない経路と、親を別プロセスで再開すると保存済み attempt dir に衝突する経路が残る。生死確認 3 系列の実 job・評価は未実施で、静的には投入先 checkout の条件も満たす必要がある。指定の焦点走は **1018 passed / 1 failed**。赤 1 件はテストが追記前の台帳オブジェクトを読み直していない箇所である。

## 対応表

| 項目 | 判定 | 根拠 |
|---|---|---|
| F2 | **closed** | [台帳](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_contrast.py:150) が既存 `series-end` を確認し、stock 不成立・retry 枯渇・score／参照完了を分類する。同 [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:883) と [launcher](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_launch.py:159) が呼ぶ。 |
| F4 | **closed** | [親](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_parent.py:43) は既存の確定終端を先に返し、正常終了で終端が無ければ `empty` を追記する（同:66–78）。 |
| F8 | **closed** | [report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_contrast_report.py:83) は最終 attempt の score 行について固定 endpoint の variant・source digest を照合する。 |
| F14 | **partial** | [親の指示](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_parent.md:7) は役割出力の再利用を指示するが、別プロセスでの親再開は後述の attempt dir 衝突で止まる。 |
| F15 | **closed** | 裁定 3 の N3 に従い、[親](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_parent.py:54) が各 attempt の `out.json` を保存する。proposed／rejected への model ID 追記は裁定で不要となった。 |
| N1 | **closed** | [report](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_contrast_report.py:43) が論理 slot ごとの最大 attempt に射影し、参照・score・件数の判定に用いる（同:67,78）。 |
| N2 | **partial** | [親](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_parent.py:43) と [round](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/silo_policy_contrast_round.py:130) の確定終端確認は入った。未終端での別プロセス再開は後述の衝突が残る。 |
| N3 | **closed** | 裁定 3 どおり。各 attempt の [JSON 出力保存](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_parent.py:54) から model ID を監査できる。 |
| N4 | **closed** | [driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:871) は stock が certified でなければ seed 前に抜け、[台帳](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/silo_policy_contrast.py:164) は stock 不成立を直ちに終端化する。焦点走の赤は [テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/tests/test_p3_s4_loop_policy.py:128) の古い `ledger.events` 参照による。 |
| N5 | **refuted** | 計画どおり通常の submit checkout なら [job body](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/p3_s4_loop_pegasus.sh:287) の AI worktree 拒否を避けられる。この worktree 自身を指定すれば停止する。 |

## 新しい所見

1. **must-fix — 不正な LLM 出力が A の却下にならない。** [round の `check`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/silo_policy_contrast_round.py:136) は不正な coder 入力でも preview を呼び、driver が schema 例外で JSON を出さない場合に `json.loads(preview.stdout)`（同:141）で止まる。`finalize` の不正な auditor 入力も同様（同:184–190）。[親](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_parent.py:79) はこれを役割失敗の retry として扱う。**成果物への影響:** 草稿 §3 の「不正出力は A のみ消費」から外れ、系列が分類不能欠測になり得る。**最小の直し:** schema 不合格を構造化した preview 拒否として返し、同じ a の `rejected` を一度だけ記録する。

2. **should-fix — 未終端の 429 後に親を別プロセスで再開できない。** [親](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_parent.py:41) は毎回 `launches = 0` から始め、同じ `out` に `attempt-0001` を `exist_ok=False` で作る（同:46–48）。既存終端が無い保留状態で再起動すると衝突する。**成果物への影響:** 保存済み role 出力を使う再開に進めず、機会 a が止まる。**最小の直し:** 保存済み attempt 番号から次番号を決め、既存の役割出力を持つ `out` で再開する。

3. **should-fix — 生死確認の投入条件は実 checkout 側で未確認。** [launcher](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/silo_policy_contrast_launch.py:130) は ledger の submit checkout を job に渡し、[body](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/pegasus/p3_s4_loop_pegasus.sh:287) は AI worktree を拒否し、[driver](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:751) は HEAD 一致を要求する。**成果物への影響:** LLM×C++・LLM×IR・random×IR の job 1 と評価 1 は、この作業ツリーを submit checkout にすると body で止まる。**最小の直し:** 裁定 N5 の通常 checkout に実装 commit・依存物を揃えてから投入する。

auditor 付き完成 proposal は [finalize](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/tools/silo_policy_contrast_round.py:187) で再 preview され、[共通 gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2867-silo-contrast-impl/orchestrator/campaign/p3_s4_loop_policy.py:249) の veto・digest 照合を通る。機械・初期点以外の auditor 省略、anomaly の certified 扱い、`fixed10=False` の既存 stock 経路の変化も、読んだ分岐からは確認しなかった。