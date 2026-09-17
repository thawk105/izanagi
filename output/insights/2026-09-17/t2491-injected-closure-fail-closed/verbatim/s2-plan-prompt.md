単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s1-brief.md (親の段 1 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/D1882.md (裁定 D1882 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/D1869.md (裁定 D1869 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/F918.md (失敗の型 F918 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/t2154-mutation-ledger.md (F918 を実測した T-2154 の変異台帳。m04 の置換と当時の期待 node。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py (対象 test。1168〜1222 行の `_GateFlowState` と定数、1367〜1454 行の helper binding visitor、1499〜1600 行の `_PythonGateFlow.__init__`、1700〜1760 行の `_record_expression`、1766〜1900 行の `_flow_block` / `_flow_statement` (Try 分岐 1866〜1897)、2002〜2025 行の `_injected_result_name`、2147〜2190 行の `coverage_for_sink` (injected 分岐 2164〜2190)、2582〜2700 行の `_define_sink_cross_product_classification` / `_failures`、2693〜2698 行の閉包検査本体、2864〜3210 行の synthetic 正例・負例群と production 分類 pin (2966〜2991)。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_n_pilot.py (production。50〜56 行の import、996〜1030 行の `build_fn` sink と `require_returned_condition_evidence` の try/except。変更禁止、読むだけ。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s1_direct_comparison.py (production。113〜126 行の例外 class 階層、358〜400 行の helper 本体、1204〜1345 行の 2 つの injected sink と handler 群。変更禁止、読むだけ。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_driver.py (production。62〜69 行の import、1774〜1825 行の injected sink と handler 群。変更禁止、読むだけ。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2491] の段 2 プラン起草役 (read-only)。brief の scope 内で、file:line 粒度の実装プランを書け。
コードは書かず、変更する行・追加する helper・test の形・変異 matrix の anchor を特定せよ。pytest は走らせられない
(書込可能 tmp が無い)。静的検査だけでよく、緑を主張するな。テスト実測は親が行う。

**ユーザー依頼 (逐語):** 「閉包検査 test_define_sink_cross_product_has_no_unreviewed_ungated_member の injected-* 特殊経路について、
「sink 直後に名前 suffix が require_returned_condition_evidence に一致し第 1 引数が sink の代入名である call が 1 つある」だけでは
被覆済みに数えない形へ、名指しした判定だけを fail-closed 側へ寄せる (D1869: 族全体の共有機構は名指し分だけ変える)。F918 が実測した
「拒否を握り潰す変異 (except: pass) が閉包検査を通る」穴を負例として登録し KILLED を確認。着手直前の local main から fresh worktree を作る。
実装面は Codex author (D95)、変異事前登録要。規律 2 を緩めない。本題の判定修正だけ。追加の gate・台帳は scope 外。」

## 答えるべきこと

1. **判定の置き場 (brief の変更面表):** 「握り潰されていない」を `_record_expression` で call ごとに計算して `returned_evidence_checks` の 3 要素目に持つ案
   (Try 分岐で `statement.body` を flow する間だけ enclosing handlers を stack に積む) と、`coverage_for_sink` 側で AST を再走査して check call の enclosing Try を探す案の
   どちらを採るか。scope 境界 (入れ子関数は `self.bodies` ごとに別 flow)・handler body / orelse / finalbody の中の call・`with` body の中の call を各案がどう扱うかを file:line で書け。
   campaign 経路 (`returned_evidence_names`、`_campaign_checked_root`) の挙動が 1 bit も変わらないことを示せ。
2. **P1 の「捕まえうる handler」表:** brief の表 (bare / `BaseException` / `Exception` / `RuntimeError` / error class に束縛された名前) を実装するのに要る名前解決を列挙せよ。
   (a) module scope の `from <s1 module> import DriverError [as X]` (n_pilot 50 行・s8b_oracle_driver 62 行の形は複数行 import) の asname 解決、(b) helper を自 module で定義する module (s1 自身) では
   module scope の `class DriverError`、(c) tuple 型 (`except (A, B)`)、(d) `except*` (TryStar)。既存の `module_assignments` (1561〜1573 行) で module scope の alias 代入 (`X = S1DriverError`) を
   引けるか。**s1 1204-try の `_SortSwoOracleRejected` (DriverError の子 class、swallow) が「捕まえない」と判定されて 1208 sink が covered のままになる**ことを確認せよ。
3. **P2 の「再送出」定義:** handler body の最後の top-level 文が `ast.Raise` という定義で production 4 箇所 (brief の handler 順) がすべて通り、`pass` / `return` / 代入 / `if …: raise` が
   すべて落ちることを確認せよ。`raise` が `try/finally` の中にある handler、`with` の中にある `raise` は fail-closed (落とす) で構わないか。
4. **P3:** import 真正性・shadow を injected 経路へ足さない理由 (brief: `_has_unshadowed_returned_evidence_helper` は s1 自身で False) を 1367〜1454 行と 1615〜1632 行で確認せよ。
5. **P4 の前提 pin:** s1 source から helper 本体の raise 文と `class DriverError(RuntimeError)` を固定する assert の置き場と形 (既存 `_production_build_sources()` から s1 の source を引けるか)。
   D1869 の「名指し外の gate を足さない」に抵触するかどうかの判断も書け (抵触するなら落とす案を書け)。
6. **P5 の synthetic test:** 既存 2864〜2882 行 (`test_define_sink_cross_product_does_not_defer_unlisted_member`、injected-build_fn の synthetic) と 2900〜3210 行 (campaign 経路の synthetic) の形に揃えた
   正例・負例の source 文字列を各 1 本ずつ書け (relative path は `orchestrator/campaign/synthetic_t2491_*.py`)。injected sink が `_benchmark_build_sinks` で `injected-build_fn` と認識される条件
   (712〜830 行の `_INJECTABLE_NAMES` と引数名) を確認し、synthetic の関数引数名を合わせよ。期待する failures の形 (`("BACKOFF_FIXED", sink, "reachable")` か `"unresolved"` か) を
   2582〜2700 行の分類から導け。production pin (4 sink covered / 1 deferred) の test 形も書け。
7. **変異 matrix の anchor (file:line):** brief の M0〜M4 について、各変異の anchor を 1 箇所に定まる複数行 anchor で書き、期待赤 node を既存 node 名で列挙せよ。
   M1 (F918 m04 同一置換) で赤くなる既存 node は T-2154 台帳の 3 件 + 閉包検査 + 分類 pin (`test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` は `failures == []` を assert する) + 新 production pin。
   冗長 gate (`test_r33_successor_protocol_document_loads_from_repository`) は帰属証拠から外す旨を書け。
8. **波及と変更しない一覧:** production 3 file、繰延べ台帳 (`_DEFERRED_GATE_MEMBERS`)、campaign 経路の synthetic 群、docs。`returned_evidence_checks` の consumer は 1727 行と 2176 行だけか確認せよ。

## 制約

- brief の不変条件 (i)〜(v) を守る。特に (i) 受理形を増やす向きの変更は不採用、判定できない形は被覆に数えない。
- 追加 gate・helper の一般化 (campaign 経路への共通化)・docs 編集はプランに入れるな。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 変更面 (file:line 表)
## 1〜5 の判断と根拠
## synthetic test 案 (source 文字列と期待値)
## 変異 matrix 事前登録案 (anchor・期待 node)
## 波及と変更しない一覧
## 未確定事項
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
