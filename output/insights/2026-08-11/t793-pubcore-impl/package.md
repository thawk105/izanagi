# 裁定パッケージ — [T-793] 公表層の機械執行 (dev-wave-t793-pubcore-impl)

本 wave は 4 必須要件のうち **(ii)・(iv)・(iv-b) と (i) の識別束縛**を実装した。
**(iii) と (i) の原子性は、裁定時点で未見だった事実により本 wave では閉じられない。**
`DW-S04` に従い、親が不採用にせず**新事実を添えてユーザー再裁定へ戻す**。

**本 wave は「公表層を機械執行した」と主張しない。**
公表 core v2 §10.4 が挙げる 11 変異のうち、**実成果物経路で拒否できるのは 0/11**、
直接 parser の負例として拒否できるのは **#7 (`ledger_kind` 詐称) と #9 (追補 P の閉集合外 field) の 2/11**
である。この判定は親・レビュー C・レビュー D が独立に導出して一致した。

---

## R1 — (iii) source 側の本走 gate。Q1 (a) の裁定条件が承認済み文書と正面衝突する

**未見だった新事実 (すべて実測):**

1. 承認済みの公表 core v2 §10.2 は
   「本書は source study の `pilot_admission` にも `main_admission` にも条件を足さない。
   **`submit_pilot` / `submit_main` が本書の存在を要求するようにしてはならない**」と明記する。
   一方、Q1 (a) の裁定条件は「source 側の本走 gate (旧 `b03` (v) の投入前 admission) を復元せよ」である。
2. **`submit_main` は repo に存在しない。** `orchestrator/preregistration/` の全 module の
   docstring が「`submit_pilot` / `verify_receipt` は本 wave では実装しない」と書いており、
   land 2 session 2 も `submit_pilot` / `submit_main` の本体を明示的に scope 外と宣言している。
   **結線先が無い gate は孤児であり、「機械執行した」と書けない。**
3. D291 自身の `operational_boundary` が
   「本 payload は source 本走および pilot の admission を保証しない」と明記する。

**帰結: Q1 (a) の条件は本 wave では履行されない。**

**選択肢:**

- **(a) 新 canonical decision で「ledger-only の送信前 deny」として授権する。**
  source core の科学的 `main_admission` の定義は変えず、公表 core / 追補 P の存在も要求せず、
  「canonical 公表台帳に予約が一意に成立しているか」だけを投入直前に検査する運用 precondition と
  位置づける。**gate の規範的授権は公表文書ではなく Q1 (a) と新 D に置く。**
  → §10.2 に抵触しない。ただし `submit_main` の所有 wave が結線するまで
  「active gate 完成」とは書けない。
- **(b) §10.2 を明示的に supersede する canonical decision を出す。**
  公表文書の存在を source 投入の条件にしてよいと定める。
  → 承認済み文書の規範を覆すため、影響範囲が広い。
- **(c) Q1 (a) の条件を「記載のみで足りる」と読み替える。**
  → D291 が「**これは要件の記載であって gate の実装・検証ではない**」と既に明記しており、
  読み替えは D291 の文言と衝突する。

**親の推奨 = (a)。** 実害の非対称性が根拠である。(a) は deny を 1 つ足すだけで、
誤って止めた場合の害は「投入が遅れる」に留まる。(b) は承認済み文書の規範を覆し、
以後 source study の admission に公表側の都合を持ち込める前例を作る。
(c) は D291 の明文と衝突し、「要件の記載を gate の完成と書かない」という D291 の理由づけを崩す。

---

## R2 — (i) の原子性・`(root, ordinal)` 一意性・予約 writer

**未見だった新事実:**

同一 Git common directory を共有する worktree 間では、**file lock と inode では一意性が成立しない**。
`/work/1/SFC/tanab/izanagi` と `.claude/worktrees/<wave>` をそれぞれ repository root にすれば、
物理 path・inode・lock がすべて別になり、双方が同じ `(family_root, individual_publication, 1)` を
取得できる。D291 の `operational_boundary` も
「本 payload は公表台帳の実体・予約の原子性・`(root, ordinal)` の一意性を保証しない」と明記する。

**本 wave が実装したもの:** 固定 literal からの**無引数**の canonical path 導出、
0 byte 台帳と file 不在の区別、`ledger_kind` の閉集合、primary 空間 (`dce4ae4f…`, `alpha_reservation`)
との互いに素性、canonical JSONL、`(root, kind, ordinal)` 重複拒否、
committed history の delete/recreate 拒否。**予約 writer は 1 行も書いていない。**

**選択肢:**

- **(a) 予約 writer を `tools/dev_wave_land.py` の land lock 内へ統合する後続 wave を起票する。**
  canonical main への取り込みと初出 commit の再導出を 1 つの transaction にする。
- **(b) 本 wave の識別束縛だけで足りると認め、予約は当面手動運用にする。**
- **(c) 予約 writer を library 層に置き、cross-worktree の競合は運用で回避する。**

**親の推奨 = (a)。** (c) は「呼び手が選べない台帳で原子的に」という公表 core §8.2 の
規範を満たさない — library 層の lock は上で述べたとおり worktree を跨げない。
(b) は ordinal を人手で管理することになり、create-only と非解放を機械で守れない。
(a) は既存の land lock (すでに fold の直列化に使われている) を再利用でき、追加の防壁を作らない。

---

## R3 — 公表 core v2 §8.1 の偽命題

**未見だった新事実 (親・レンズ A が独立に再現):**

承認済みの公表 core v2 §8.1 は
「`family_root` が primary 系列と同じ commit であることは意図どおりである」と断言する。
しかし land 済みの primary 台帳 `output/registry/t139-alpha-reservations.jsonl` の
`family_root` は **`dce4ae4f…`** (事前登録承認の fold) であり、
公表側の `family_root` = **`88d68f91…`** (D234 限定例外の fold) とは**別 commit**である。

**この命題が引き出す結論 (2 系列の互いに素性) は強まる方向なので blocker ではない。**
本 wave の実装は §8.1 の同一性主張を互いに素性の根拠にせず、
**(root, kind) の 2 軸**で互いに素性を課している。

**選択肢:**

- **(a) canonical erratum / decision で「literal `88d68f91…` と実 primary `dce4ae4f…` を正とし、
  §8.1 の同一 commit 文は conformance の根拠に使わない」と記録する。**
- **(b) 文書を編集して修正する。** → **不可。** D291 が exact bytes を承認しており、
  編集すれば承認した bytes でなくなる。
- **(c) 記録せず放置する。**

**親の推奨 = (a)。** (b) は D291 が却下した選択肢そのものである。
(c) だと、将来 conformance report が「承認済み文書の命題が偽のまま適合と報告する」状態が残り、
根の provenance を proof chain として使えない。

---

## R4 — marker gate の保証範囲

本 wave の marker gate が拒否できるのは、**`approved_blobs:` 形式で三つ組を宣言する
decision fragment だけ**である。散文で「この path/commit/sha256 の追補 P を承認する」と述べる
fragment は検査対象が空集合になり素通りする。

**選択肢:**

- **(a) 保証範囲を `approved_blobs:` 形式に限定して記録し、それ以上を主張しない。**
- **(b) blob authority を与える decision に機械可読な target schema を必須とする裁定を出す。**
  → gate の保証が全承認へ広がるが、canonical decision の書き方に新しい制約を課す。

**親の推奨 = (a) を今すぐ記録し、(b) は独立の起票にする。**
(b) は decisions の書式そのものを縛る規範であり、本 wave の scope で決めるべきでない。
(a) を記録しないと「marker gate があるから承認は安全」という過大な読みが残る。

---

## R5 — 予約 entry の発行 (ordinal 1 の消費) — 報告のみ、裁定不要

**本 wave は予約 entry を 1 行も発行していない。** 台帳 file は **0 byte** である。
理由は D292 が pilot / 本走の投入禁止の解除を canonical decision に限定しており、
「実装が済んだから ordinal 1 を予約する」という推論が成立しないためである。

`D291` の `operational_state_on_fold` は現在も `pilot_submission = forbidden` /
`main_submission = forbidden` であり、**本 wave の gate はいずれも deny を増やす方向にのみ働く。**
report は成功時にも `submission_authority = "not_granted"` と両 `forbidden` を必ず出力する。

---

## 本 wave が返す報告 (裁定不要)

1. **main 側に既存の赤 4 件がある。**
   ```
   test_spool_fold.py::test_n37_real_repo_canonical_family_requires_archive_active_history
   test_spool_fold.py::test_failure_supersede_real_final_entry_eof_is_byte_exact
   test_spool_fold.py::test_failure_supersede_real_f196_f197_boundary_is_byte_exact
   test_spool_fold.py::test_failure_supersede_real_f1_boundary_without_blank_line_is_byte_exact
   ```
   `tools/spool_fold.py:1871` が複製先の `check_docs.py` を importlib で読むが、
   その `check_docs.py:27` は 2026-08-10 の commit `890fed05` で `dev_waves` の import を得た。
   テスト helper `_copy_real_canonical_family` (`test_spool_fold.py:2943`) は
   `tools/check_docs.py` を複製するが **`tools/dev_waves/` を複製しない**。
   レビュー C は「directory の複製だけでは不十分で、`spec_from_file_location()` は複製先 `tools/` を
   `sys.path` へ追加しないため、import 経路も閉じるか rotate limit の読取を
   `check_docs` の全 module import から分離する必要がある」と指摘した。
   **本 wave の差分は `check_docs.py` に一切触れていない。**

2. **land 2 (`worktree-dev-wave-t139-manifest-w2`) との二重実装は無い。**
   land 2 の `approval_payload.py` は D282 専用 (`decision_kind =
   t139-preregistration-approval-supersession/v1`、10 top-level key、6 role) で、
   D291 (14 top-level key、承認 2 role、relation 3 subtree) とは grammar が別物である。
   本 wave は新規 package `orchestrator/publication/` に置き、
   `orchestrator/preregistration/` を 1 file も変更していない
   (land 2 が変更中の `blobref.py` / `erratum.py` / `test_t139_preregistration_binding.py` を含む)。
   共有の `BlobRef` / `read_pinned_blob` は import のみである。
