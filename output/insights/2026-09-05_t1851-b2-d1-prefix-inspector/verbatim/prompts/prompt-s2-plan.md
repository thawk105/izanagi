単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md

## 必読事項の射影

次を上から順に読む。いずれも絶対パスである。**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/s1-brief.md` — 親 brief (scope、不変条件、provisional 裁定 (P1)〜(P6)、実アンカー表)
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/decisions-verbatim.md` — 確定裁定 11 件の逐語 (D1113 / D1114 / D1194 / D1336 / D1337 / D1340 / D1341 / D1342 / D1522 / D1530 / D1533)
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/s2-plan-v2.md` — 設計 wave の plan v2。「単位 B: admission 層」「単位 D: 契約・consumer 層」節が本 plan の土台
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/s4-adjudication-r2.md` — 設計 wave の終端裁定。13 blocker (特に B2-1 / B2-3 / B2-4 / B2-7 / B2-8) の採否と 6 段分割の根拠
5. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/t1946-proof-chain-s4-adjudication.md` — proof chain の設計凍結 (択一 1〜4 とその後の裁定 D1336〜D1342)
6. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/a2alpha-README.md` と `refs/a2alpha-s4-adjudication.md` — 直前の実装 wave (A2α)。v2 世代・claim v3・capability 消費・v2 terminal の二層拒否 (S5 / S6) の現状
7. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/a2beta-README.md` — 継承元の正本。7 節 (裁定 3 件) と 8 節 (次段 = B2 / D1 の非 terminal 部分)
8. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/a1-README.md`、`refs/a1-s4-adjudication.md`、`refs/b1-README.md` — A1' / B1 の成果と閉じていない窓
9. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-05_t1851-b2-d1/refs/brief-v2.md` — 設計 wave の親 brief (共有 admission root の現物調査を含む)

作業 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-a` である。コードはすべてこの worktree の中を読む。base commit は本 branch の HEAD `50dbf9158` であり、B1 / A1' / A2α の実装と local main `61bc6ac69` の両方を含む。

## 依頼

6 段分割 `B1 → A → B2 → D1 → C → D2` のうち、**B2 (admission 層 read-only inspector) と D1 (契約・proof 型) の terminal 証拠に依存しない部分**の実装プランを file:line 粒度で起草せよ。単位 C / D2 と、B2 / D1 の terminal 依存部分 (coverage の全単射、sealed terminal 集合との照合、`finished_at`、attempts projection の `attempt_id`) は**実装しない**。それらは境界 (symbol・引数・戻り型) だけを固定する。

出力は 3 部構成にする。**規模の実測 (依頼 1) を先に出せ。**

## 依頼 1 — 規模の実測と分割判定

親 brief の (P5) は「1 wave に収まる」と暫定裁定しているが、B2-a / D1-a〜d 単体の規模は誰も測っていない。各群について次を実測して表にせよ。

- 変更する production file と、その file 内で変更・新設する関数・定数の実名と現行行番号。
- 追加・変更・削除される production 行数の見積もり。推測なら推測と書き、根拠にした現物の行数を添えろ。
- 更新・新設が必要な test node 数。**名前の推測でなく現物を数えろ。** 既存 test file の中で、変更する production symbol を参照している node を実際に列挙せよ。特に `result_keys_for_mode` の 22 呼出しと、`RESULT_SCHEMA` を参照する production 6 file / test 5 file (brief の DW-O09 節) を現物で数えろ。
- その群を単独で実装したとき、他の群を実装しないままでも production が壊れず既存 test が緑を保てるか。保てないなら、どの群と束ねる必要があるかを名指しせよ。

そのうえで判定せよ。**1 wave (実装子 1〜2 本 + fix 3 巡以内) で安全に実装し 1 commit へ統合できるか。** できないなら分割案を 1 つに絞れ。分割の必須条件は「前半だけを積んだ状態で production が整合し、既存 test が緑を保ち、後半との境界の symbol・引数・戻り型を今この plan で固定できること」である。

## 依頼 2 — 実装プラン (file:line 粒度)

実装子へそのまま渡せる粒度で書け。各項目に現行の file:line を付けろ。次を必ず含めること。

1. **B2-a の read-only prefix inspector の置き場所と signature。** 親の (P2) (`s8b_attempt_registry` に公開 API を置き admission / stats が呼ぶ) を現物の import 関係で検証し、採用か却下かを理由付きで書け。producer capture 入口と verifier inspection 入口の 2 つの signature を固定し、戻り型 (N と head を運ぶ object) の exact key を書け。lock は `_locked_readonly(root)` (`s8b_holdout_admission.py:730`) を使うか、既存 `read_attempt_registry` (`s8b_attempt_registry.py:1631`) が使う write lock か、根拠付きで選べ。current protocol generation の解決 (`_registry_generation_paths_locked` :649、`_peek_registry_genesis` :637、`_profile_and_binding_for_generation` :727) をどう再利用するか、genesis から profile を構築する経路と v1 (1 段 path) を対象外にする根拠を書け。
2. **verifier inspection の意味論。** live 全行を replay した後だけ `len(rows) >= N` と `rows[N-1]["event_sha256"] == reported head` を比較する (D1337)。N 以後の壊れた tail (parse 失敗・chain 切断) を拒否し、正当な append を許す。拒否理由は構造化 (規律 3) し、既存の `_fail(category, reason)` の語彙に揃えろ。
3. **D1-b の proof object。** exact 7 field、各 field の型検査、`chain_head_sha256 == rows[N-1].event_sha256` の意味限定、validator の置き場所 (`attempt_registry_core.py` の `_assert_chain` :449 / `load_attempt_registry` :1454 の近傍) と signature。
4. **D1-a の契約。** legacy v4 / v5 / readable 集合、schema 別 exact key 集合、`result_keys_for_mode` の signature。親の (P1) (producer は v4 のまま、v5 は別名定数) と (P4) (`schema` は kw-only default = legacy v4、D2 の file を触らない) を現物で検証し、採用か却下かを書け。`test_s8b_floor_contract.py:180` の v4 pin と `test_s8b_floor_stats.py:596,1323-1325` の v4 pin を変えない設計であることを確認せよ。
5. **D1-c / D1-d の verifier。** `verify_floor_artifact` (:682) の v4 / v5 分岐、v4 で `attempt_registry` を拒否する exact key の経路、v5 の proof shape・binding・正の N・nonzero head の検査と、live wrapper (:1036) から渡される独立 proof との比較の向き。live wrapper の v5 分岐が B2-a の inspection 入口を呼び、v4 では registry を読まないこと。expected binding (freeze / protocol / schedule digest) をどの既存引数から取るか。
6. **境界の固定 (実装しない部分)。** coverage の signature (result attempt identity 集合 ↔ prefix 内 sealed terminal 集合)、producer capture が単位 C からどう呼ばれるか、`finished_at` の置き場所 (B2-8)、D2 の consumer 3 箇所。
7. **赤になる既存 test の列挙** (直接赤と fixture 経由の transitive 赤を分ける) と、supersede してよい pin / してはならない pin。
8. **テスト計画。** 正例 (v4 不変、v5 の正常 proof、正当 append 後の受理)、負例 (v4 に `attempt_registry` が現れる、proof field 欠落、head 改竄、N 行内 chain 改竄、N 行以後の破損 / chain 切断、N > len(rows)、別 freeze / protocol / schedule binding、row_count 0 / 非整数、hex 不正)。負例は「他の gate が同じ入力を拒否しない」ことを 1 行で示せ (変異 matrix の観測 node にする)。D1522 に従い、上流が拒否する形でも下層の実体を名指しする直接検査を置け。新規 test file は作らず既存 file へ足せ。
9. **(P3) の検証。** v2 世代が現在持てる行 (genesis + reservation) だけで prefix inspector の正例が組めるか、`reserve_attempt_slot` (`s8b_attempt_registry.py:1657` 付近) と capability 消費経路を現物で確かめよ。組めないなら何が足りないかを書け。

## 依頼 3 — 変異事前登録の候補

各候補に (変異位置 file:line、変異内容、KILLED を期待する test node、その test が他 gate に遮られない理由) を書け。8〜14 件。plan v2 の M5〜M9 のうち本 wave の scope に入るものは再照準して含めよ。

## 制約

- 読取専用である。書込可能 tmp が無いので pytest の実走は要求しない。静的検査でよい。実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ。無出力が最悪である。
- 出力へ結合文字 U+0300〜U+036F を使わない。
- 各主張に [実測] (現物を読んだ) か [推測] を付けろ。
- 出力の最後に `## 総括` 節を置き、分割判定・(P1)〜(P6) の採否・実装子の本数・規模を 10 行以内で書け。
