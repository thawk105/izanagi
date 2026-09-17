単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s1-brief.md (親の段 1 brief。末尾の「v1.1 訂正」が最新の P1/P2。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s2-plan.md (段 2 plan。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/D1882.md (裁定 D1882 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/D1869.md (裁定 D1869 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/F918.md (失敗の型 F918 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/t2154-mutation-ledger.md (F918 を実測した T-2154 の変異台帳。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py (対象 test。696〜830 (sink 認識)、878〜890 (`_production_build_sources`)、1168〜1222、1499〜1600、1700〜1760、1766〜1900、2002〜2025、2147〜2190、2582〜2700 (分類)、2693〜2790 (閉包検査と繰延べ台帳)、2864〜3210 行。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_s8b_oracle_n_pilot.py (T-2154 の負例 2 件 `test_build_binaries_uses_binding_flags_and_prepared_records_independently` / `test_injected_build_fn_without_condition_records_is_rejected` と `test_r33_successor_protocol_document_loads_from_repository`。grep で位置を探し、その test だけ読む。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_n_pilot.py (production。50〜56、996〜1030 行。変更禁止、読むだけ。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s1_direct_comparison.py (production。113〜126、1151〜1153、1204〜1345 行。変更禁止、読むだけ。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_driver.py (production。62〜69、1655〜1665、1726〜1734、1774〜1825、1836〜1862 行。変更禁止、読むだけ。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2491] の段 3 敵対相談役 **レンズ B (誤拒否 / scope 逸脱 / 変異の帰属)**。plan を守らず検査せよ。親 brief 自身も検査対象である
(親の実測値とその一般化、file:line、所有範囲、変異の帰属不成立を疑え)。pytest は走らせられない (書込可能 tmp が無い)。静的検査だけでよく、緑を主張するな。

## 答えるべきこと

1. **誤拒否:** brief v1.1 の P1/P2 を production 4 箇所 (s1 1218 / 1295、s8b_oracle_driver 1801、n_pilot 1018) へ**自分で**静的に当て直し、covered に残るかを handler ごとに追跡して示せ。
   親の追跡 (brief v1.1 の「production 4 箇所の判定」) と食い違う点を挙げよ。特に (a) s1 1204-try の `_SortSwoOracleRejected` が NONE (module scope ClassDef) になるか、
   (b) s8b 1730-try の WAL tuple handler が MAYBE で末尾 bare `raise` か、(c) 1151-try (handler なし、finally のみ) の扱い、(d) `with` の中の check を stack が引き継ぐか (plan 1 節)。
2. **scope 逸脱 (D1882 / D1869):** v1.1 の規則 (handler 型の分類表・alias chain・変換再送出の追跡停止) は D1882 が却下した「import 真正性・shadow・支配関係まで静的に検査する族全体の新機構」に
   踏み込んでいないか。名指しの判定 (`coverage_for_sink` の injected 分岐 + それが依存する `returned_evidence_checks` の記録) の中で閉じているか。plan の「try stack を `_flow_statement` に足す」は
   campaign 経路の共有機構への変更に当たるか (campaign の計算結果が不変でも、共有 method に手を入れること自体が D1869 に触れるか)。
   P4 (前提 pin の assert) を落とす親の判断、新 production pin test (`test_define_sink_cross_product_classifies_t2491_injected_production_sinks_exactly`) を足すことが
   「追加 gate」に当たるかも判定せよ。
3. **変異の帰属 (DW-M01 / M03 / M08):** M1 (F918 m04 同一置換) で赤くなる node の完全集合を静的に予測せよ (閉包検査、`classifies_t2155_production_sinks_exactly`、`t2520_certify_entry_removal`、
   新 production pin、T-2154 の負例 2、冗長 gate `r33` digest pin、他に `failures == []` を assert する node)。M2〜M4 について既存 test が既に落とすものがないか
   (既存 synthetic 群 2864〜3210 行の assert を assertion 単位で確認)。「新テストだけが検出する差分」を示す新旧両走 (旧 = main 38353207f の test file で M1 を走らせ、閉包検査が**緑のまま**であることを示す) の
   spec 形と runner argv (T-2154 と同じ `-q -rf orchestrator/tests/test_s8b_oracle_n_pilot.py orchestrator/tests/test_ccbench_spawn_sites.py`) の妥当性。
4. **synthetic test の実在条件:** plan の source 文字列が `_benchmark_build_sinks` で `injected-build_fn` として認識されるか (712〜830 行: `_INJECTABLE_NAMES`、`from ... import (DriverError as X, require_returned_condition_evidence,)` の
   複数行 import が `callable_aliases` に入って sink 認識を妨げないか)、`orchestrator/campaign/synthetic_t2491_*.py` の relative path が分類の対象 root に入るか、`marker = 'BACKOFF_FIXED'` で
   `reachable` になる根拠 (2554〜2557 行)。正例の `except ChildError: pass` (未知名 → v1.1 では MAYBE → bare raise でないので**被覆に数えない**) は plan の期待 (covered) と矛盾する — どちらが正しいか、
   正例の source をどう直すか (例: `class ChildError(X): ...` を module scope に置いて NONE にする)。
5. **推奨:** 誤拒否・scope 逸脱・帰属不成立のうち real なものを最大 3 件、file:line と是正案で示せ。残りは裁定パッケージ候補として列挙せよ。

## 制約

- 出力は file に書かず、最終メッセージの本文に全文を書け。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 誤拒否の追跡 (production 4 箇所、handler ごと)
## scope 逸脱の判定 (D1882 / D1869 / 追加 gate)
## 変異の帰属 (M1 の完全集合予測、M2〜M4 の既存 test 重複、新旧両走)
## synthetic test の実在条件
## 推奨 (real 最大 3 件、裁定パッケージ候補)
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
