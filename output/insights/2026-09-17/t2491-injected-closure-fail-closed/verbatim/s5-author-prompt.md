単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s4-ruling.md (親の段 4 裁定 = plan v2 の正本。「plan v2」節の R0〜R4 と「synthetic test」節を実装する。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s1-brief.md (親の段 1 brief。末尾の v1.1 訂正まで。裁定と食い違う箇所は裁定が優先。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s2-plan.md (段 2 plan。変更面の file:line 表と synthetic の source 形。裁定で変わった点は裁定が優先。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/D1882.md (裁定 D1882 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/F918.md (失敗の型 F918 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py (**唯一の編集対象**。1168〜1222、1263〜1366 (`_PotentialBindingVisitor`)、1499〜1600、1700〜1760、1766〜1975、2002〜2025、2147〜2190、2582〜2700、2864〜3210 行。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_n_pilot.py (production。50〜56、95、996〜1030 行。**変更禁止**、読むだけ)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s1_direct_comparison.py (production。113〜126、358〜404、1151〜1153、1204〜1345、1380〜1390 行。**変更禁止**、読むだけ)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_driver.py (production。62〜69、104、1655〜1665、1726〜1734、1774〜1825、1836〜1862 行。**変更禁止**、読むだけ)

## 依頼

あなたは dev-wave [T-2491] の段 5 実装子 (Codex author、D95)。**編集してよいのは `orchestrator/tests/test_ccbench_spawn_sites.py` だけ**。production・他 test・docs は編集しない。
commit しない (統合 commit は親)。裁定 (s4-ruling.md) の plan v2 R0〜R4 を実装し、同「synthetic test」節の正例 p1〜p7・負例 n1〜n12・production pin を追加せよ。

**現行の受理・拒否挙動 (scope 前):** `coverage_for_sink` の injected 分岐 (2164〜2190 行) は、sink の代入名を第 1 引数にもつ suffix 一致 call が sink 行と次の injected sink 行の間に 1 つでもあれば
patch macro 全件を被覆済みに数える。握り潰し (`except: pass`) を検査しない (F918)。**変更後:** 同じ一致条件に R0〜R3 の `unswallowed` を AND する。受理集合は現行の真部分集合になる。
指示外の受理集合変更をしない (campaign 経路 `returned_evidence_names` / `_campaign_checked_root`、既存 synthetic 群、繰延べ台帳は不変)。

## 実装の要点 (裁定 R0〜R4 の逐語が正本、ここは補足)

- R0: `_record_expression` の 1723〜1730 行で、`returned_evidence_checks` へ積むのは `call is returned_evidence_call` のときだけにし、3 要素目に `unswallowed` (bool) を入れる。
  既存の `returned_evidence_call` は `_flow_statement` (1920〜1940 行) が Expr の値 / 単一 Name target の Assign・AnnAssign の値に対してだけ非 None を渡している。これをそのまま使う。
- R1: `_flow_statement` の Try 分岐 (1866〜1897 行) で、`statement.body` を flow する間は `(try_node, "body")`、handler body の間は `(try_node, "handler")`、orelse の間は `(try_node, "orelse")` を
  stack に積み、finalbody の間は積まない。`try/finally` で必ず pop する。stack は `__init__` (1586〜1588 行) の scope ごとの `_flow_block` 呼出しの直前に空にする。
- R2/R3: `_record_expression` から呼ぶ helper (例: `_injected_check_unswallowed(scope) -> bool`) を `_PythonGateFlow` の method として 1700 行の直前に置く。名前分類 (MAYBE / DEFINITE / NONE の優先順位)、
  handler body 条件 (Return/Break/Continue の不在 + 末尾 `ast.Raise`)、raise 文の形 (bare / 変換 / その他)、追跡の停止条件は裁定の逐語どおり。「入れ子 def/class/lambda の本体を除く」走査は
  `ast.walk` でなく、FunctionDef / AsyncFunctionDef / ClassDef / Lambda に入らない自前の走査で書く。
- 定数: 1218〜1222 行の隣に `_RETURNED_EVIDENCE_ERROR = "DriverError"` と組込み catcher の frozenset を置き、前提 (helper の明示的な拒否 raise は base `DriverError`、
  `class DriverError(RuntimeError)`) と保証限界を comment に書く。assert は置かない (D1869)。
- module scope の情報: `self.tree.body` から (a) `ImportFrom` (module ∈ `_RETURNED_EVIDENCE_MODULES`、alias.name == "DriverError") の束縛名、(b) `ClassDef` の名前と件数、
  (c) helper が module scope で定義されているか (`"<module>.require_returned_condition_evidence" in self.bodies`) を `__init__` で 1 回集める。既存 `module_assignments` (1561〜1573 行) を再束縛判定に使う。alias chain は引かない。
- 局所再束縛: 関数 scope では `_potentially_bound_names(tuple(self.bodies[scope].body))` と `self.global_nonlocal_names` に含まれる名前を MAYBE にする。`<module>` scope ではこの検査をしない。
- R4: 2175〜2187 行の一致条件へ `and unswallowed` を AND し、comment を裁定 R4 の保証と限界へ書き換える。
- 新 test は既存 synthetic 群 (2864〜3210 行) の形に揃える (`_assert_single_synthetic_campaign_sink` は campaign 用なので使わず、`_benchmark_build_sinks(sources) == {sink}` を直に assert)。
  負例は各 1 理由 (他の条件では落ちない形) にし、正例は各条件が受理する形にする。parametrize する場合は id を ASCII 英小文字・数字・ハイフンだけにする (変異 harness の制約)。
  production pin は 4 sink を path 末尾・scope・lineno・kind で名指しし、`Counter({"covered": len(patch_sources)})` の形で literal を焼き込まない。

## 検査・報告 (必須)

- 実走できるなら `python3 tools/run_tests.py -q -rf orchestrator/tests/test_ccbench_spawn_sites.py` を走らせ、緑には実走 nodeid・範囲 (件数) を併記する。子の実走は親の全走を代替しない。
  実走不能なら `closed` と申告せず「実装済み・未実走」と書く。sandbox で dispatch が拒否される・tmp が無い等の非帰属赤は本文をそのまま報告する。
- テスト新設の単位は、親の名指しを網羅と見なさず、同 file 内の制約 meta-test (例: 台帳の exact 検査、node 数を数える test、行番号 pin) を自ら洗い出して走らせる (F42)。
- fixture へ現行 hash を差し込む・期待値を観測値へ合わせるなど、テストを甘くして緑にしない (F27)。機構の正例・負例は実体 (production の 4 sink と synthetic の形) を名指しし、依存先を stub しない (F649)。
- 期待値へ揮発 payload (working tree hash 等) を焼き込まない。
- 完了報告に、所有外 caller・共有 fixture・consumer test への波及可能性を静的に列挙する (特に `returned_evidence_checks` の 3 箇所、`_flow_statement` の Try 分岐を通る全 scope、campaign 経路の既存 test)。
- production 3 file の 4 check について、実装した規則を自分で当て直し、`run_role` / `run_block` / `build_binaries` の body で `DriverError` / `S1DriverError` / `_SortSwoOracleRejected` が局所束縛されないことを報告する。
- 変異 matrix の anchor (裁定 M0〜M7) を実 bytes で書き出す: 各変異の old 文字列 (file 内で 1 箇所に定まる複数行) と new 文字列、期待赤 node (新 synthetic の nodeid)。

## 出力形式 (見出しは全部 `##`)

## 変更の要約 (file:line)
## 規則の実装 (R0〜R4 と裁定の対応)
## 追加した test (nodeid と期待値)
## 実走結果 (nodeid・件数、または「実装済み・未実走」と理由)
## production 4 check の当て直し
## 波及の静的列挙
## 変異 matrix の anchor (M0〜M7、old/new 文字列、期待 node)
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
