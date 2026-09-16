# [T-2671] 段 4 裁定 — 層3 の bench-first screening 対応の現況確定

段 2 プラン 1 本と段 3 敵対相談 2 本 (レンズ A = 現況確定の当否、レンズ B = 裁定射程と scope) の
所見を real / refuted で仕分け、プラン v2 と変異事前登録を確定する。
**親が一次資料で裏取りした項目には「親実測」と付す。子の逐語をそのまま採らない。**

## real (採用)

### R1. 「6f169f90 は admitted」は親 brief の誤り (レンズ A 所見 3、must-fix)

親は `orchestrator/tests/test_artifact_admission.py:213` の定数名 `ADMITTED_HISTORICAL_CAMPAIGNS`
から「admitted」と書いたが、**定数名は receipt の値ではない。**

**親実測** — 生成したレポートの現物 field:

| field | 値 |
|---|---|
| top-level `admission_status` | `null` |
| top-level `classification` | `null` |
| `admission_decision.admission_status` | `historical-not-reclassified` |
| `admission_decision.classification` | `historical-pre-admission-schema` |
| `certifying_input` | `false` |
| `current_verifier_conformance` | `"unknown"` |
| `campaign_verifier_epoch.state` | `E0` (`reason_code: v1-authority-absent`) |

**裁定:** brief・docs・insight・worklog のすべてで「admitted」を使わない。正しい表現は
**「歴史閲覧用途で描画できる非 certifying の材料であり、現行の認証適合は `unknown`」**。
成果物影響: 放置すると、歴史資料 1 件を現行認証用途でも受理される 1 件として論文と台帳に数える誤記になる。

### R2. 「機構の対応」と「保存資料の追加」を同日に閉じない (レンズ A 所見 5 + レンズ B 所見 3、must-fix)

次の 3 つは別物であり、1 つの「対象 campaign 群」という語へ畳まない。

1. **記録済み 7 件について、生成当時に成立した双射。** 歴史的事実であり不変。
2. **現行 producer で描画可能な campaign 集合。** ①と一致しない (R4)。
3. **本 wave 後に材料レポートを保存している 8 件。**

**裁定:** 記録・docs・insight はこの 3 分割で書く。「7 件 → 8 件」とだけ書かない。

### R3. 負例を「producer が拒否する形」に限定したプランの判断は過剰 (レンズ B 所見 1、must-fix)

**親実測** — `orchestrator/campaign/layer3_report.py:251-265` の `_assert_bijection` は
(i) 入力 WAL/whiteboard の内容ハッシュ多重集合と report 本体一次配置の多重集合の一致、
(ii) `source_refs` 区画の一致、(iii) `runs`/`verifications`/`rejects`/`aborts` の各行の
`source_ref` が一次配置を指すこと、の 3 つだけを検査する。**view の値そのものは比較しない。**
したがってプランの「`screen` の key 欠落・`rejects` 行の欠落・架空 verification の混入は
既存検査で拒否されない」は正しい。

しかし親 brief が求めた「落とすと赤になる負例」は、producer の例外送出だけを指していない。
**負例は、正例 pin を赤にする変異検査 (DW-M08 の新旧両走) が担う。**

**裁定:** プランの 5 本 (正例 4 / 負例 1) をそのまま採用し、残る 3 点の負例は
**段 6 の変異 matrix** へ移す。**producer へ新しい拒否を足すことはしない** ([T-326])。

### R4. D170 を引く。既存 7 件の再生成不能は欠陥でなく裁定どおり (レンズ B 所見 2、must-fix)

**親実測** — `docs/decisions.md` の D170 (2026-08-05) 本文:
適用対象は「admission validator の歴史枝 (`historical-pre-admission-schema`) において、
`campaign.lock` の `search_config.axis` が **trigger 軸**であれば `admission_status` を
`legacy-unclassified` とし、raw view を発行しない」。決定 3 は
「本決定が拒否するのは新しい raw view の発行と、そこから新規に材料レポートを起こすことだけである」。

**親実測** — `output/campaigns/backoff-sweep-silo-read-heavy-sweep-6f169f90/campaign.lock` に
`search_config.axis` は**存在しない** (backoff-sweep であり trigger 軸ではない)。
だから admission は `historical-not-reclassified` を返し、描画できる。

**裁定:**
- 既存 7 件 (p3-s8a-trigger-sweep 系) が現行 producer で再生成できない
  (`campaign is legacy-unclassified`、rc=2) のは **D170 の適用結果であって欠陥ではない**。
  復旧タスクを起票しない (レンズ B 所見 8 と同じ結論)。
- **D170 は 6f169f90 には適用されない。** したがって本 wave の材料レポート生成は D170 に触れない。
- 記録には D170 を根拠として明記する。親 brief が根拠に挙げた D828 は schema 後方互換の裁定であり、
  この非対称を説明する裁定ではない。

### R5. README の「執筆時点で腐っている箇所は無い」を撤回する (レンズ B 所見 3、must-fix)

**親実測** — `docs/paper-story/2026-09-14.md` で「bench-first screening campaign は対象外」を
主張する行は **259 / 546 / 856 / 1250 / 1464 / 1879** の 6 箇所 (レンズ B の列挙と一致)。
着地は 2026-08-25 なので、**6 箇所すべてが執筆時点で既に偽だった。**

**裁定:** 凍結物 (版・`claim-evidence/`) は 1 byte も編集しない。
`docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」節で、
(a) 「現在この節に積んでいる項目は 0 である」「執筆時点で腐っている箇所は無い」を撤回し、
(b) **2026-09-14 版への追補訂正**として 1 項を積み、6 箇所をまとめて指す。
既存の「前版を訂正した箇所は 4 つ」という履歴へ混ぜない (それは前版に対する訂正の記録である)。

### R6. 採番は D70 どおり母集団最大 +1 とし、段 7 直前に再走査する (レンズ B 所見 5、must-fix)

**親実測** — D70 は「並行セッションは番号を予約したとみなさず、統合直前に再走査して未統合側を
振り直す (`landed` = main へ統合された時点)」と定める。採番母集団 (現行 worklog +
`docs/archive/worklog-*.md` + 見送り台帳) の最大値は **2669**。
稼働中の別 wave が `dev-wave-t2670-...` という worktree 名を使っていることは、
**母集団に入らない** (worktree 名は ID ではない)。

**裁定:** 親 brief の「別 wave が使っているから 1 つずらす」は撤回する。
正式採番は**段 7 直前の再走査で決める**。本 wave の worktree slug `t2671-layer3-screening` は
識別子であって台帳 ID ではない。insight ディレクトリ名も slug のまま据え置く。

### R8. T4 の monkeypatch を正規の呼び出し境界へ差し替える (親の裁定、`DW-O14`)

段 2 プランは T4 で `layer3_report._variant_rows` を monkeypatch し、一次配置の abort event の
`ts` だけを変えて件数同一のまま双射検査を赤にする設計だった。

`DW-O14` は「対象実装まで読み、正規注入 seam がないか確認する。monkeypatch は最後の手段とする
(D78)」と定める。**親実測** — `orchestrator/campaign/layer3_report.py:251` の
`_assert_bijection(records, whiteboard, report)` は **module 直下の関数で、引数 3 つを
すべて呼び手から受け取る**。したがって seam は既に在り、monkeypatch は要らない。

**裁定:** T4 は `_assert_bijection` を**直接呼ぶ**形にする。

1. 合成 campaign から `build_report` が成功することを確かめ、その report を deep copy する。
2. copy の `variants[].events[]` にある abort event の `ts` だけを変える (**件数は変えない**)。
3. `_assert_bijection(records, [], mutated)` が
   `Layer3ReportError("source-ref multiset が入力 WAL/whiteboard と report 本体で一致しない")`
   を送出することを確かめる。
4. 同じ `records` と**無改変の** report では例外が出ないことを、同じ test 内で対に確かめる
   (恒真化の防止)。

`records` は生成後 WAL を独立に読んで組み立てる。report の `variants` から作らない。
monkeypatch fixture は使わない。production file は 1 byte も変えない。

### R7. 手順の不変条件 — 新規レポートは記録 commit に含め、受入は commit 後に投入する

**親実測** — `orchestrator/tests/test_artifact_admission.py::test_existing_campaign_tracked_bytes_match_git_head`
は `git diff --quiet HEAD -- output/campaigns` を実行する。untracked では発火しない
(親の焦点走 146 passed が実証)。**stage 済み・未 commit の窓でだけ赤になる。**

**裁定:** 新規レポートは段 7 の記録 commit に含め、受入全走は commit 後に投入する
(`DW-O12` の既定順序と同じ)。新しい作業は生じない。

## refuted (不採用)

| # | 所見 | 反証 |
|---|---|---|
| F1 | screening の schema 受理は副作用かもしれない (レンズ A 所見 1) | 意図的対応。`layer3_schema.json:128,145` に排他制約まで明示。着地は 2026-08-25 の T-1291 (commit `b8318b956`)。根拠は D828 (版据置 + optional property 追加) と D829 (実測値保持) |
| F2 | レポートに現れない payload key があるかもしれない (レンズ A 所見 2) | 欠落 0。WAL 9 レコード・payload 直下 52 key がすべて `variants[].events[]` へ保存される。`layer3_report.py:340` が event 全体を一次配置へ入れる |
| F3 | 自己参照で深い一致が永久に失敗する (レンズ A 所見 4 / レンズ B 所見 7) | **親実測** — `autonomous_trial_completeness.py:4674-4683` が fresh 側の `artifact_refs` から persisted report 自身の相対 path を除外している。加えて 6f169f90 は autonomous campaign identity の exact-key 検査で深い比較へ到達しない |
| F4 | `docs/phase3.md` の 66 行・560 行も直すべき (レンズ B 所見 4) | **親実測** — 両箇所は screening 機構そのもの (D58 の実装・positive control) の記述で、層3 の対象可否を主張していない。訂正は 660-667 行の層3 項のみ |
| F5 | (b) も新規起票すべき (レンズ B 所見 6) | 既存 [T-326] がある。ユーザー依頼の「台帳 ID が無いので起票から行う」という前提は、親の実測で訂正される。重複起票しない |
| F6 | 既存 7 件の再生成不能を復旧タスクとして起票すべき (レンズ B 所見 8) | R4 のとおり D170 の裁定どおりの挙動。復旧は D170 が閉じた発行集合を再び広げうる |

## scope 外 (実装せず、裁定パッケージへも送らない — 既に裁定で閉じているため)

- **(b) `layer3_report` 本体の深い一致強化** — [T-326] (2026-08-03 ユーザー裁定、択 b)。
  本体着手には択 (a) の再裁定が要る。**再裁定はユーザー手番であり、本 wave は求めない。**
- **(c) 機序仮説層 v3 の実装・`agent_outputs.jsonl` writer の新設** — DW-G04。
  発火条件を満たす既存 artifact が 0 件。起票のみ行い、実装は発効条件 (agent 出力が生まれる
  loop 再走) を待つ。

## プラン v2 (段 5 実装子へ渡す確定仕様)

段 2 プランをそのまま採用する。変更点は R3 の位置づけだけで、テスト設計は変えない。

`orchestrator/tests/test_layer3_report.py:1427` の空行へ、次の 5 本を追加する。
既存関数・assertion は変更しない。helper は `_record:779` / `_bench:783` / `_campaign:209` を再利用する。

| # | 関数名 | 種別 | 経路 |
|---|---|---|---|
| T1 | `test_named_screening_abort_preserves_complete_screen_payload` | 正例 | 実 artifact (`REAL_SCREENING_CAMPAIGN:63`) |
| T2 | `test_screening_abort_variant_is_listed_in_rejects` | 正例 | 合成 WAL |
| T3 | `test_screening_abort_participates_in_input_ref_multiset` | 正例 | 合成 WAL |
| T4 | `test_screening_abort_primary_mutation_fails_bijection_at_equal_count` | 負例 | 合成 WAL + `_assert_bijection` の直接呼び出し (**プランから変更**、下記 R8) |
| T5 | `test_screening_abort_without_verify_done_builds_without_verification` | 正例 | 合成 WAL |

**所要台帳 (`orchestrator/tests/acceptance_duration_ledger.json`) へは登録しない。**
**親実測** — `test_acceptance_schedule_order.py:713` の閾値は coverage >= 0.90、現行の登録は 23118 件。
5 node 追加で閾値を割らない。登録すると並行 wave との台帳競合で受入やり直しの risk が上がる。

## 変異事前登録 (DW-M01 / DW-M08)

**本 wave はテスト強化だけの wave である。** DW-M08 に従い、変異は
**新テストを含む tip** と **変更前 HEAD (`262c2993e`)** の双方へ走らせ、
**新テストだけが検出する差分**を示す。

| ID | 変異位置 (production) | 期待 (新 tip) | 期待 (変更前 HEAD) |
|---|---|---|---|
| M1 | `layer3_report._view_row` — abort の `screen` から key を 1 つ落とす | T1 が KILLED | SURVIVED |
| M2 | `layer3_report` の rejects 構築 — abort 由来の行を落とす | T2 が KILLED | SURVIVED |
| M3 | `layer3_report._variant_rows` — abort event を一次配置から落とす | T3 + 既存双射が KILLED | 既存双射だけが KILLED |
| M4 | `layer3_report` の verifications 構築 — `verify_done` 不在で例外を送出する | T5 が KILLED | SURVIVED |
| M5 | `layer3_report._assert_bijection` — multiset 比較を無効化する | T4 が KILLED | SURVIVED |

- **M3 は過剰決定である** (既存の双射検査も同時に赤になる)。`DW-M03` に従い
  **冗長 gate と明記**し、単独変異の証拠から外す。新テストの寄与は
  「abort event の multiplicity をテスト側で独立に数える」点であり、M3 の kill 単独では示せない。
- 期待 node は完全集合で登録し、同形式へ正規化した記録 node との完全一致だけを KILLED とする (F33)。
- 変異の実際の literal と行は段 6 の spec で確定する。`DW-M01` に従い、
  **各変異について赤理由が 1 つに絞れることを実装後に確認する**。絞れないものは登録から外す。

## 段 5・6 の分割

- 段 5: Codex `role=author` 実装子 1 本 (`sandbox=workspace-write`)。
  所有 path は `orchestrator/tests/test_layer3_report.py` のみ。
- 段 6: 変異 matrix (上表) + 受入。**review 子は変更面確定後に再評価する** —
  受理集合を変えず正しさ防壁に触らないテスト追加のみなので、軽量版 (review 子 1 本) を既定とする。
