# 段 4 裁定 — [T-139] 公表 core 段階 2 の承認 payload fold

段 3 は 2 レンズともに **NO-GO** (レンズ A = blocker 3、レンズ B = blocker 2)。
親は全 blocker を **real・採用**とし、plan v2 を以下に確定する。**実装差分ゼロは維持する。**

## 親が独立に再測した子の主張 (すべて一致 — 子の値を信用せず測り直した)

| 主張 | 出所 | 親の再測 |
|---|---|---|
| v2 2 件の三つ組 | 親→レンズ A が再検算 | 一致 (mode 100644、CR 0、末尾 LF あり) |
| 旧版 2 件の内容 commit | plan | `db5e8dfc…` / `8e9a5b4d…` 一致 |
| **同 path の中間 blob 3 件が実在** | レンズ A | **一致** — `44abd2fc:publication-core-v2.md` = `45d83e7ab471ef9db0aaf9705168a333a8c317de06674fa23ef9164428d03065`、`44abd2fc:addendum-b-v2.md` = `0ea71fff11c0f4c939cab213021487758bf6016db522ea29a3a527d2ee1c0658`、`66934dda:addendum-b-v2.md` = `2313a26151975fe65e6586dec5676df92da209c68126296b55592ec6ab8834df` |
| source core の canonical role 語彙 | レンズ A | 一致 — `main_admission: requires_addendum_a_and_b`、resolver の role 名は `addendum_b` |
| 新 core v2 の admission 語彙 | レンズ A | 一致 — `analysis_admission: requires_addendum_p` |
| 追補 A 再発行版の digest | レンズ A | 一致 — `f7db96ce…8cfec` |
| `F_r` = `39d760985a5e37d20464c394760bf65596156566` を land 2 が実装で pin | レンズ A | **本 wave では検証しない** (別 worktree の未 land 実装。scope 外の事実として記録のみ) |

## blocker 裁定

### A-1 / B-3. `forward_supersedes` は旧 exact blob の承認を捏造する → **real・採用**

段 2 プランは親の (P2) を倒して `forward_supersedes: worklog404.C-2/C-4` を置いたが、
**レンズ 2 本が独立にこれを過大と判定した。**worklog 404 にあるのは**未実行の手続き選択**であり、
旧 exact blob の authority ではない。canonical worklog 411 は C-2/C-4 を「実行していない」と記録し、
D262/D282 の `approved_blobs` に追補 B・公表 core は無い。

**裁定:** `decision_kind` から `supersession` を外す。旧版は
`prior_exact_byte_authority = none` を明記したうえで `historical_candidates_rejected_for_role`
として role 限定で拒否する。**worklog 404 の手続き選択は `procedural_history` として事実のまま残す**
(無かったことにしない)。親の (P2) は結論として維持し、プランの型付けだけを退ける。

*成果物影響:* このまま land すると、存在しない旧版 authority が台帳に生まれ、
履歴 resolver / 監査レポートが旧 blob を「一度承認済み」として扱う受理枝が増える。

### A-2. `document_relations` が canonical admission role への写像を欠く → **real・採用**

**裁定:** 次の 3 写像を payload へ書く。語彙は実文書から取る (親が実測済み)。

- `source_addendum_b` → source core の `main_admission: requires_addendum_a_and_b` の `addendum_b` role
- `future_publication_addendum_p` → 新 core v2 の `analysis_admission: requires_addendum_p` の `addendum_p` role
- 新 core v2 は**独立 core だが source study を片方向に pin する** — その入力同定は
  source core + **追補 A 再発行版**の三つ組 2 件で行う (新 core 自身が「core だけでは足りない」と書く)。
  よって payload に追補 A の三つ組を `source_study_inputs` として入れる (**再承認ではなく参照**)。

*成果物影響:* relation graph だけを読む resolver が追補 B を `main_admission` へ結線できないか、
別の追補 A を公表入力として受理し、`qualification_status`・試行台帳の参照が変わる。

### A-3. exact 照合義務の欠落 + 同 path の中間 blob → **real・採用 (最重要)**

`not_approved_*` は旧 path 2 件しか列挙しないため、**denylist では同 path の中間 blob 3 件を落とせない。**
親はこの 3 件の実在を独立に実測して確認した (上表)。

**裁定:** payload を **allowlist の閉集合契約**として書く。具体的に次を閉じる。

- `approved_blobs` は **exact 2 role・2 三つ組**。余剰 role も、同 path の別 digest も拒否する
  (**digest が一致しない限り path が同じでも承認対象ではない**)。
- 追補 P の承認済み value field は exact に `{p01, p02}`。`p03` と P の blob は `false` で固定。
- 後続 land が凍結する追補 P の `p01`/`p02` は、`F_p` の `docs/decisions.md` の値と exact 一致を要する。
- resolver は manifest を trust root にせず、`F_p` から本 payload を読んで exact 照合する
  (D282 と同じ自己拘束文)。

*成果物影響:* 閉じないと、後続 land が `p01`・`α_pub`・`p03`・同 path の中間 blob を差し替えても
自己整合だけで通り、公表候補 ordinal・Holm 棄却集合・材料レポート値・承認 blob 受理集合が変わる。

### B-1. Q1 条件を「履行済み」と扱うのは誤り → **real・採用 (親の誤りを訂正)**

親は brief と handoff に「Q1 (a) の条件は既に履行されている」と書いた。**これは強すぎる。**
正しくは「**[T-793] への必須要件追記は確認済み。source 側の本走 gate は未実装・未検証**」である。
追補 B v2 自身が旧 gate の削除を明記し、現時点で active gate は存在しない。

**裁定:** payload と worklog の両方へ、要件追記の確認と gate 未実装を**書き分けて**記録する。
「条件充足済み」という 1 語に畳まない。

*成果物影響:* 実装済みと誤記したまま fold すると、source 本走 admission が閉じていないのに
条件充足として扱われ、試行台帳・certified primary・公表 entry の受理集合が誤る。

### B-2. Q3 (b) の遷移条件が固定されていない → **real・採用**

**裁定:** `operational_state_on_fold` に、追補 P 凍結の**前提条件**を遷移として書く —
「追補 P の凍結は [T-793] が公表台帳の実体を確定した後に限る。pilot もそれまで投入しない」。
現状の「P blob 未承認・pilot 禁止」だけでは、後続 actor が実体確定を確認せず P を fold できる。

*成果物影響:* 固定しないと、公表系列の root・ordinal・累積 spending の受理集合が変わる。

## must-fix 裁定

### B-4. `authority: none` のまま残る誤読経路 → **real・採用 (payload 側で処置)**

対象文書は編集禁止 (編集したら承認した bytes でなくなる)。よって**文書は直さない。**
代わりに payload へ「**fold 後も両文書の bytes は `authority: none` のままである。
承認状態の正本は本 decision であり、文書内の envelope ではない**」と明記する。
これは先行 source core も `authority: none` のまま発効している事実と整合する。

*成果物影響:* 書かないと、report の approved role 集合が空になるか v2 blob を未承認として除外する。

### B-5. (P1)「1 decision にまとめる」は未裁定 → **親裁定として維持、ただし連結を解く**

Q4 と Q5 は別問だが、payload を 2 decision に割ると `F_p` が 2 つになり、
追補 P の `core_ref.commit` がどちらを指すか二義化する。**(P1) は維持する。**
ただしレンズ B の「不要な連結」は正当なので、payload 内に
「**`source_addendum_b` の承認は `publication_core` の承認に依存しない。両者は独立した role である**」
と明記して、束ねたことによる意味の連結を解く。

*成果物影響:* 割ると後続 P の core lineage が曖昧化する。連結を解かないと source B の承認状態が
公表 core の承認へ不要に従属する。

### (P5) の撤回を plan v2 へ明示反映 → **採用**

D282 の `operational_boundary` は予約台帳を含むため逐語継承しない。
公表系列は台帳も gate も producer も作らないので、境界を
「Git 上の承認 identity だけを保証し、台帳・gate・投入可否は保証しない」へ縮小する。

## scope 外 real (実装しない。worklog へ記録する)

いずれも [T-793] の責務であり、本 wave は**実装したふりをしない**。

1. source 側本走 admission の復元 (Q1 条件の実体)。要件は記載済み、実装・検証は未了。
2. 根から唯一の公表台帳実体への束縛、原子予約、重複拒否、ordinal 非再利用 (Q3)。
3. 追補 P の未確定 marker と `p01`〜`p03` exact-key を検出する機械 gate。現状は規律だけが止めている。
4. **fold 後の `authority: none` を canonical decision の approved role へ解決する resolver / report 層。**
   レンズ B が新たに挙げた層。[T-793] の「公表 validator・consumer」に含まれると解釈し、
   worklog へ**明示**して取り残しを防ぐ。

## 変異事前登録

**免除。**`DW-S04` の「実装差分ゼロの『実装しない』裁定」に該当し、kill を観測する実装面が無い。

## plan v2 (確定)

成果物は **2 fragment のみ**。

1. `docs/spool/decisions/2026-08-11-dev-wave-t139-pubcore-approve-1.md` — 承認 payload。
   `decision_kind = t139-publication-core-approval/v1` (supersession を外した)。
   構成: `prior_exact_byte_authority` / `procedural_history` / `source_core` / `source_study_inputs` /
   `document_relations` (admission role 写像つき) / `approved_blobs` (exact 2 件) /
   `approved_values_for_future_addendum_p` (values_only) /
   `historical_candidates_rejected_for_role` / `exact_closure` (allowlist 契約) /
   `operational_state_on_fold` (Q3 (b) の遷移条件つき) / `operational_boundary` (縮小版) /
   `authority_field_note` (B-4)。
2. `docs/spool/worklog/2026-08-11-dev-wave-t139-pubcore-approve-1.md` — 記録。
   Q1 条件は「要件追記を確認・gate 未実装」と書き分ける。scope 外 real 4 件を明記。

**検査:** `check_docs.py` → `spool_fold.py --dry-run` (rotation 発火の有無を `rotation_path` で確認) →
commit → 全史 provenance → 受入全走 (lease claim 後)。
