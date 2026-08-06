| 所見 | closed / partial / regressed | 根拠 (file:line) |
|---|---|---|
| F1 — 例外境界 | closed | finalizer は回復境界外の [producer:1445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1445)、pending critic 全体は [producer:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1450) の `try` 内で、例外は [producer:1458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1458) から `supervisor-error` へ回復する。専用テストも terminal suffix を固定する [test:2348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2348)。<br>放置時の成果物影響: 同じ入力が partial report ありから report 不在・formal lifecycle `indeterminate` へ変わる。 |
| F2 — pending 残留 guard | partial | guard は [producer:1523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1523)、test seam は消費済み pending を意図的に戻す [test:2396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2396)。kill は成立するが、「現 producer 非到達の人工状態」という限界の docstring/comment はない。<br>放置時の成果物影響: guard の mutation evidence は成立するが、proof chain が producer 到達性まで証明したと誤読し得る。後者は nit。 |
| F3 — direct test / AST pin | closed | direct helper 呼出しは [test:2230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2230)、M2′/M3′ の別 assert は [test:2239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2239)。AST pin は helper call 数と `status` の AST 行位置を固定する [test:2245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2245)。<br>放置時の成果物影響: mutation 台帳が producer assertion ではなく completeness の別 gate を kill node と誤記する。 |
| F4 — 値固定 | partial | 多世代順・generation、pending 5 keys、実 finalizer no-op は固定されたが、build invalid-critic の positive admission 削除 mutant が生存する。原因は非永続 fake render [test:2098](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2098) と再-finalize fallback [producer:1477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1477)。<br>放置時の成果物影響: admission rollback mutant により実運転の report が消え lifecycle が `indeterminate` になっても、proof chain は当該 mutant を kill 済みと誤記できる。 |
| R1側 R1 — guard 発火不能 | partial | F2 と同じ。実 helper は先頭で key を pop する [producer:1258](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1258) 一方、人工 seam により guard 削除を単独で殺せるようになった [test:2391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2391)。限界の明記だけ残る。<br>放置時の成果物影響: private pending と raw variant が report に混入する将来退行を proof chain が検出済みと偽装し得る。 |
| R1側 R2 — M2/M3 の単一理由性 | closed | completeness を通さない direct test で `fixed-generation-budget` と `converged` を個別に投入し、両方を `role-invalid` に固定する [test:2199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2199)。<br>放置時の成果物影響: proof chain の kill reason と実際の第一失敗 gate が食い違う。 |
| R1側 R3 — critic phase が回復境界外 | closed | F1 と同じ。digest・admission lookup・provider lookup・`_invoke` は一つの helper [producer:1249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1249) にあり、その呼出し全体が回復対象 [producer:1450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1450)。<br>放置時の成果物影響: partial report の受理集合が report 不在へ縮小する。 |
| R1側 R4 — 多世代 reflux と先行材料 | partial | adjudication どおり scope 外で未修正。`prior_reverse` は `None` のまま [producer:1685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1685)、次世代 proposal に入る [producer:1843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1843)。<br>放置時の成果物影響: cap-lift 時、generation 2 proposal/WAL が critic 1 の reflux を欠き、report 不在でも proposal・Layer 3 が残る。 |
| R1側 R5 — partial と positive Layer 3 | partial | adjudication どおり scope 外で挙動は維持。Layer 3/admission は critic より先に確定 [producer:1214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1214)、critic invalid は stop reason だけを変更する [producer:1315](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1315)。<br>放置時の成果物影響: certified 選択は partial filter で不変だが、材料レポート/proof chain は critic-invalid cell の positive Layer 3 を参照できる。 |
| R2側 R1 — pending critic の例外契約 | closed | F1 と同じ。missing critic provider が partial report、`fatal_error=KeyError`、terminal suffix を生成することを固定 [test:2351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2351)。<br>放置時の成果物影響: report/lifecycle の受理集合が `partial` から `indeterminate` へ変わる。 |
| R2側 R2 — M5 が kill されない | partial | 人工 seam により guard 削除時は当該 test が赤になる。ただし人工状態の限界が明記されていない [test:2391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2391)。<br>放置時の成果物影響: runtime 値は直ちに変わらないが、mutation proof の到達性説明を過大評価し得る。nit。 |
| R2側 R3 — M2/M3 の別 gate kill | closed | direct test は `assert_autonomous_trial_completeness` を経由せず helper の戻り値を直接検査する [test:2230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2230)。<br>放置時の成果物影響: mutation evidence の参照先が producer から consumer gate へすり替わる。 |
| R2側 R4 — M4 の位置非一意 | closed | AST は `_finalize_cell_admission` と `_run_pending_critics` を各2回要求 [test:2272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2272) し、唯一の `status` 代入が全 call より後であることを構造 pin する [test:2276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2276)。文字列一致ではない。<br>放置時の成果物影響: status の早期算出 mutant を kill 済みとする proof chain が偽になる。 |
| R2側 R5 — 実 finalizer / build admission | partial | 実 finalizer を残す順序 test は閉じた [test:1989](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:1989)。一方、positive admission 削除は fallback により test 内で復元され得る [producer:1477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1477)。<br>放置時の成果物影響: 実運転の report/lifecycle を変える rollback mutant がテストを生存する。 |
| R2側 R6 — 多世代/direct の値不足 | closed | journal tuple は exact [test:2453](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2453)、critic generation は `[1,2]` [test:2467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2467)、pending は exact 5 keys と全既知値 [test:2503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2503)。<br>放置時の成果物影響: attempts 順・critic 世代・pending contract が変わっても proof chain が緑になる。 |
| R2側 R7 — 復元 cell の terminal 順序 | closed | v5 の誤記は後続 adjudication が明示訂正している [adjudication:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/output/insights/2026-08-07_t244-p3-u8-critic-after-admission/s6-adjudication.md:58)。実 consumer も terminal を `run-finish` 直前に要求する [consumer:552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:552)。<br>放置時の成果物影響: cap-lift 復元 trial を partial report と誤記し、実際の report 不在・lifecycle `indeterminate` と proof chain が食い違う。 |

`partial` のうち、R1-R4/R1-R5 は明示的な scope-out、F2系は documentation nit である。land blocker は F4/R2-R5 に対応する新所見 N1。

### F1 の分岐監査

| 分岐 | journal/report の静的結果 |
|---|---|
| finalizer 例外 | finalizer は `try` より前なので伝播。critic・`run-finish`・report write へ到達せず、registered formal trial は [producer:2226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:2226) で `indeterminate`。 |
| critic valid | admission → critic role-attempt → `run-finish`。supervisor terminal event はない。 |
| provider/parser の通常例外 | `_invoke` 自身が invalid role-attempt に正規化する [producer:994](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:994)。cell は `role-invalid` partial。journal/report に error event が残るため黙示 publish ではない。 |
| digest・`require_admitted_campaign`・provider lookup・`_invoke` から外へ出た例外 | 共通 catch が `fatal_error`、cell error、`supervisor-error` を設定し [producer:1458](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1458)、直後が `run-finish`。partial publish は明示的な回復契約。 |
| `_run_workload` 復元、pending なし | 先に `supervisor-error`、fallback admission の後に新 journal event はなく、`run-finish` 直前という要求を満たす。cap=1 の実到達形。 |
| `_run_workload` 復元、pending あり | `supervisor-error → critic → run-finish` となり completeness が拒否する。critic 準備も失敗すれば terminal が2件になり、[consumer:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:542) で拒否。いずれも report は publish されない。cap-lift 限定の既裁定 fail-closed。 |
| workload 前 wall | `supervisor-wall-budget` が [producer:1383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1383) に書かれ、その後は `run-finish`。 |

したがって、F1 が新しく「critic 失敗を無記録で partial publish」する経路は見つからない。build cell の positive Layer 3 を保った `role-invalid`/`supervisor-error` partial は明示的に記録される既存・scope-out 条件である。

### F2 / F3 の殺傷力

F2 seam は実 producer の正常な後状態ではない。producer は pending を作り [producer:1904](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1904)、helper が key 全体を pop するため、test が消費後に戻した状態だけが guard へ到達する。

guard 削除時は completeness が cell の未知 key を閉集合検査しておらず [consumer:943](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/autonomous_trial_completeness.py:943)、report write まで進む。その結果、指定 test の `pytest.raises` だけが失敗する。他に同 guard 文言・残留 seam を使う test はなく、静的には単一理由である。

F3 direct test は completeness 非経由である。M2′の代入削除は最初の assert、初期 `converged` を後勝ちにする M3′は二番目の assert が殺す。AST pin も source text 検索ではなく、唯一の `status` assignment、両 phase の call 数、AST上の配置を固定しており、指定された単純な M4′移動を殺せる。

### 新しい所見

N1 — must-fix: build invalid-critic の positive-admission 削除 mutant が生存する。

critic invalid 分岐に、例えば `cell.pop("admission_decision", None)` を加える mutation を考える。

1. test の fake render は positive dict を返すだけで、Layer 3 ファイルを作らない [test:2098](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2098)。
2. mutant が admission key を消す。
3. fallback が「admission 未確定の復元 cell」と誤認して finalizer を再実行する [producer:1477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1477)。
4. fake render が再び positive decision を返し、pending は既に空なので test の最終 assertion [test:2161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/tests/test_p3_autonomous_workload_trial.py:2161) は静的には通る。
5. 実 render は Layer 3 をリンクして永続化する [layer3_report:591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/layer3_report.py:591)。実運転の二度目の finalizer は既存 report 検査 [producer:1211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p3-u8-critic/orchestrator/campaign/p3_autonomous_workload_trial.py:1211) で送出し、report 不在・formal lifecycle `indeterminate` になる。

成果物影響: 現行の「positive Layer 3 を持つ `role-invalid` partial report」が「Layer 3 は残るが trial report 不在・lifecycle `indeterminate`」へ変わる mutation を、proof chain が false-green で見逃す。

N2 — nit: F2 test には、seam が現 producer 非到達の人工状態であるという明記がない。runtime 成果物値や受理集合は変わらず、test evidence の説明品質だけの問題である。

### 退行確認

fix 前の新設6テストについて、assert 削除・値緩和・fixture の甘化はない。

- 順序 test は fake finalizer から実 finalizer＋fake render へ強化。
- no-build invalid、harness 優先、finalizer failure の assertion は維持。
- 多世代 test は call 数だけから exact journal tuple＋generation `[1,2]` へ強化。
- direct test は長さだけから exact 5-key/value contract へ強化。

逆順 critic、pending key 1件削除、finalizer no-op はそれぞれ赤になると予測する。positive admission 削除だけが N1 のとおり生存する。

## 総括

(a) **NO-GO** — 実装の例外境界は正しいが、F4 の build invalid-critic pin が要求された admission rollback mutation を殺せず、mutation proof が false-green になる。

(b) 残る must-fix: **F4 / N1（R2側 R5 の positive-admission pin）**。

(c) 新しい所見: **N1（must-fix）、N2（nit）**。

(d) 全走で赤くなると予測する現行 nodeid: **なし**。pytest は実走しておらず、親実測の 214 passed を前提事実として扱った。