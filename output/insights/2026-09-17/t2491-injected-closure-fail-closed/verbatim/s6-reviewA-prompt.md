単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s4-ruling.md (親の段 4 裁定 = plan v2 (R0〜R4) の正本。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s5-author.md (実装子の最終報告。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-diff.patch (実装差分 = 統合 commit の `git show`。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s6-focus1.log (親の焦点走 log: test file 全 node の実走結果。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/s3-lensA.md (段 3 レンズ A の所見。裁定表で採否済み。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/D1882.md (裁定 D1882 の逐語。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/aeda5aca/tmp/wave/verbatim/F918.md (失敗の型 F918 の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/tests/test_ccbench_spawn_sites.py (実装後の対象 test。1218〜1232 (定数)、1577〜1620 (module 情報・stack 初期化)、1728〜1812 (`_injected_check_unswallowed`)、1835〜1845 (R0)、1981〜2020 (Try 分岐)、2300〜2320 (R4)、3043〜3280 (新 test)。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s1_direct_comparison.py (production。113〜126、358〜404、1151〜1153、1204〜1345、1380〜1390 行。読むだけ)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_driver.py (production。62〜69、104、1655〜1665、1726〜1734、1774〜1825、1836〜1862 行。読むだけ)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2491-injected-closure-fail-closed/orchestrator/campaign/s8b_oracle_n_pilot.py (production。50〜56、95、996〜1030 行。読むだけ)

## 依頼

あなたは dev-wave [T-2491] の段 6 敵対レビュー **レンズ A (規律 2 / 実装が裁定 R0〜R4 を正しく実装しているか、fail-closed の穴)**。
実装を守らず攻撃せよ。pytest は走らせられない (書込可能 tmp が無い)。静的検査だけでよく、緑を主張するな。親の焦点走 log が実走の証拠である。

## 答えるべきこと

1. **裁定との一致:** `_injected_check_unswallowed` (1728〜1812 行) が R2 (TryStar・finally 脱出を先に検査)、R3 (名前分類の優先順位 MAYBE→DEFINITE→NONE、tuple 集約、
   handler body の脱出禁止 + 末尾 Raise、raise 文の形 bare / 変換 / その他、追跡の停止と継続) を逐語どおり実装しているか。ずれを file:line で挙げよ。
   特に: (a) 変換先の判定 `name in self.module_class_counts` は「本 file の module scope ClassDef」だが、同名が module scope で再代入されている (`module_assignments`) 場合を除外していない。
   (b) `local_names` は現 scope の body だけで、字句的な親関数 (`_lexical_scopes`) での再束縛・関数引数 (`args`) での束縛を見ない。(c) `raise <as 名>` を bare とするが、handler body 内で as 名が
   再代入される形。(d) `classify(raised.func) == "definite"` で E 名を bare 扱いする経路。(e) `kind == "definite"` で `break` した後、外側の try で position が "handler"/"orelse" の要素を skip する経路。
   これらが穴 (被覆に数える) か fail-closed (数えない) か、production 4 sink に影響するかを判定せよ。
2. **R0 の実装:** `call is returned_evidence_call` の限定で lambda / 内包表記 / 短絡 / 入れ子式の call が記録から外れるか。`_flow_statement` が `returned_evidence_call` を非 None にする条件
   (Expr の値 / 単一 Name target の Assign・AnnAssign の値) を確認し、production 4 check (n_pilot 1018 Expr、s1 1218 Assign、s1 1295 Expr、s8b 1801 Expr) が記録されることを示せ。
3. **R1 の stack:** Try 分岐の push/pop が body / handler / orelse で正しく、finalbody では積まれないこと。`with` body・`if` 分岐・`match` 等の他の分岐で stack が保たれること。
   入れ子関数の body は別 scope で空から始まること (`__init__` の初期化位置)。`_record_expression` が定義時式 (decorator / default) を親 scope で評価するとき stack が親のものであること。
4. **新 test の単一理由性 (DW-M01 / M03):** 負例 n1〜n12 がそれぞれ 1 つの規則だけで落ちるか (他の規則でも落ちるなら過剰決定)。正例 p1〜p7 が各規則を実際に通るか。
   n7 (`except ChildError: pass`、ClassDef 無し) と p4 (`class ChildError(X)` あり) の対が NONE 分類を単独で検証するか。n11 が「外側 try の DEFINITE swallow」を単独で検証するか。
5. **regression:** campaign 経路 (`returned_evidence_names`、`_campaign_checked_root`) と既存 synthetic 群の挙動が 1 bit も変わらないこと。`returned_evidence_checks` の 3 要素化で他の consumer が壊れないこと。
6. **must-fix / nit の判定:** 各所見に DW-G05 (放置時に閉包検査の受理集合がどう変わるか) を 1 行で添え、示せないものは nit にせよ。must-fix には修正案 (file:line、差分の形) を書け。
   既存テストの期待値を変える提案は禁止 (赤なら実装側が誤り)。

## 制約

- 出力は file に書かず、最終メッセージの本文に全文を書け。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式 (見出しは全部 `##`)

## 裁定 R0〜R4 との一致 (ずれの file:line 表)
## 穴 / fail-closed の判定 ((a)〜(e) と追加の形)
## 新 test の単一理由性
## regression
## must-fix と nit (DW-G05 の 1 行付き、修正案)
## 総括

最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
