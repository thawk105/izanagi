単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-ruling.md (親の段 6 裁定 = 本 fix の正本。R3a〜R3c、追加 test p8 / n13〜n17、変異 matrix。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s4-ruling.md (段 4 裁定 = plan v2 (R0〜R4)。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-reviewA.md (段 6 レビュー A。所見 (a)(b)(c) と非 blocking 所見。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-reviewB.md (段 6 レビュー B。変異の帰属と追加登録案。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s5-author.md (段 5 実装子の最終報告。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py (**唯一の編集対象**。1218〜1232、1577〜1620、1728〜1812 (`_injected_check_unswallowed`)、1835〜1845、1981〜2020、2300〜2320、3043〜3280 (新 test)。読めなければ即停止)

## 依頼

あなたは dev-wave [T-2491] の段 6 fix 子 (Codex author、D95)。段 5 実装子の契約 (`DW-S05-A/B/C`) を全文継承する: **編集してよいのは
`orchestrator/tests/test_ccbench_spawn_sites.py` だけ**、production・他 test・docs は編集しない、commit しない (統合 commit は親)。
**既存テストの期待値を変更しない** (反転・緩和・skip・削除を禁じる。赤なら実装側が誤り。期待値が誤りだと思うなら実装を変えず報告して止める — ただし「止める」は
その項目についてであり、他の項目は続ける)。指示外の受理集合変更をしない。

## やること (s6-ruling.md の逐語が正本)

1. **R3a:** `_injected_check_unswallowed` の変換再送出判定 (現 1802 行付近 `elif name in self.module_class_counts:`) を、「本 file の module scope ClassDef (件数 1) かつ `module_assignments` に無く、かつ局所束縛名 (R3b) に無い」に締める。満たさなければ「その他」(False)。
2. **R3b:** `local_names` を「現 scope + 字句的親関数 scope (`self._lexical_scopes(scope)` の `<module>` 以外) の各 body の `_potentially_bound_names` ∪ 各 scope の引数名 (posonlyargs / args / kwonlyargs / vararg / kwarg) ∪ `global_nonlocal_names`」へ広げる。
3. **R3c:** `raise <as 名>` を bare とするのは、handler body (入れ子 def/class/lambda の本体を除く) で as 名が束縛されないときだけ。束縛されれば「その他」(False)。
4. **R4 comment:** 保証限界の comment に「型名・as 名の再束縛は本 file の module/局所/引数の束縛だけを見る」「finalbody 内の check 自身の拒否は追跡しない」「変換後の例外の外側での扱い、MAYBE 型が実際に E を捕まえて bare 再送出する経路、with の `__exit__`、条件 guard、代入名の再束縛、TryStar 規則は Python 3.10 では実走検証されない」を簡潔に足す。
5. **追加 test:** 正例 p8、負例 n13〜n17 (裁定の逐語どおり、各 1 理由)。既存 parametrize へ `pytest.param(..., id="...")` で追加する (id は ASCII 英小文字・数字・ハイフン)。n14 は `except*` なので n10 と同じ skipif。
   正例 group の source は module scope に `class PilotErr(RuntimeError)` と `class ChildError(X)` を既に持つ (sink 8 行目)。負例 group は持たない (sink 6 行目) — n15/n16/n17 は module scope の class/代入が要るので、
   負例 group の source 構成を変えずに済むよう、必要な module scope 行を含む **別の負例 test 関数** (例: `test_define_sink_cross_product_t2491_rejects_injected_rebinding`、sink 行は source に合わせる) を作ってよい。
   既存 n1〜n12 の source・期待値・id は変えない。
6. **production 4 check の当て直し** (R3a〜c を加えた後も covered のまま): s1 1218 / 1295、s8b_oracle_driver 1801、n_pilot 1018 について、対象関数とその字句的親の引数・Name store・module Assign に
   `DriverError` / `S1DriverError` / `_SortSwoOracleRejected` / `PilotError` / `OracleDriverError` の束縛が無いことを AST で確認して報告する。
7. **変異 anchor:** s6-ruling の M0〜M13 について、fix 後の実 bytes で old (file 内 1 箇所の複数行) と new を Python 文字列リテラルで書き出し、各変異の期待赤 node (新負例の nodeid) を予測する。
   old の出現数が 1 であることを確認する。M11 は「局所再束縛判定除去」の実 anchor (R3b 実装後の形) で、n13 と n16 の両方が赤になるかを予測する。

## 検査・報告 (必須、DW-S05-C)

- 実走できるなら `python3 tools/run_tests.py -q -rf orchestrator/tests/test_ccbench_spawn_sites.py` を走らせ、緑には実走 nodeid・件数を併記する。実走不能なら「実装済み・未実走」と理由 (非帰属赤の本文) を書く。
- 制約 meta-test (台帳 exact / node 数 / 行番号 pin) を自ら洗い出す。テストを甘くして緑にしない。揮発 payload を焼き込まない。
- 波及の静的列挙 (所有外 caller・共有 fixture・consumer)。

## 出力形式 (見出しは全部 `##`)

## 変更の要約 (file:line)
## R3a〜R3c と comment の実装
## 追加した test (nodeid と期待値、各 1 理由の根拠)
## 実走結果 (nodeid・件数、または「実装済み・未実走」と理由)
## production 4 check の当て直し
## 変異 matrix の anchor (M0〜M13、old/new 文字列、期待 node)
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
