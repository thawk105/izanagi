---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t793-pubcore-impl
seq: 1
title: 公表層の機械執行を D291 payload・台帳識別束縛・marker gate として入れた — 4 必須要件のうち (iii) と (i) の原子性は承認済み文書との衝突で返却 (コード + テスト、branch worktree-dev-wave-t793-pubcore-impl)
---

## 本文

- **[T-793] の 4 必須要件のうち、本 wave が閉じたのは (ii)・(iv)・(iv-b) と (i) の識別束縛だけである。**
  **(iii) source 側の本走 gate と (i) の原子性は、裁定時点で未見だった事実により閉じられない。**
  `DW-S04` に従い親が不採用にせず、新事実付きでユーザー再裁定へ返した。裁定パッケージは
  `output/insights/2026-08-11_t793-pubcore-impl/package.md` の R1〜R5。
- **`F_p` = `b13b7ea840ad51199f40b3a534c9d1cdb422af2e` を起動時に実測で再同定した。**
  この commit が `docs/decisions.md` へ追加する `## D` 見出しは D291 の 1 件のみである。
- **(iii) が閉じられない理由 (R1)。** 承認済みの公表 core v2 §10.2 は
  「`submit_pilot` / `submit_main` が本書の存在を要求するようにしてはならない」と明示的に禁じており、
  Q1 (a) の裁定条件「source 側の本走 gate を復元せよ」と正面から衝突する。加えて `submit_main` は
  repo に存在せず、land 2 が scope 外と宣言した所有物である。D291 の `operational_boundary` も
  「本 payload は source 本走および pilot の admission を保証しない」と書いている。
  **Q1 (a) の条件は本 wave では履行されていない。**
- **(i) の原子性が閉じられない理由 (R2)。** 同一 Git common directory を共有する worktree 間では
  file lock と inode で `(root, ordinal)` の一意性が成立しない。canonical main + land lock との
  一体化が要る。D291 の `operational_boundary` も予約の原子性を保証対象外と明記している。
- **承認済み文書の記述を覆す新事実 (R3)。** 公表 core v2 §8.1 は
  「`family_root` が primary 系列と同じ commit である」と断言するが、land 済みの primary 台帳
  `output/registry/t139-alpha-reservations.jsonl` の `family_root` は `dce4ae4f…` (事前登録承認の fold)、
  公表側は `88d68f91…` (D234 限定例外の fold) で**別 commit である**。親と段 3 レンズ A が独立に再現した。
  引き出される結論 (2 系列の互いに素性) は強まる方向なので blocker ではないが、実装は §8.1 の
  同一性主張を根拠にせず **(root, kind) の 2 軸**で互いに素性を課した。文書は D291 の承認 bytes
  なので編集していない。
- **本 wave は「公表層を機械執行した」と主張しない。** 公表 core v2 §10.4 の 11 変異のうち、
  **実成果物経路で拒否できるのは 0/11**、直接 parser の負例として拒否できるのは
  **#7 (`ledger_kind` 詐称) と #9 (追補 P の閉集合外 field) の 2/11** である。
  親・段 6 レビュー C・レビュー D が独立に導出して一致した。
- **予約 entry を 1 行も発行していない。** 台帳は 0 byte で、D292 の投入禁止は解除していない。
  本 wave の gate はすべて deny を増やす方向にのみ働き、report は成功時も
  `submission_authority = not_granted` と pilot / main の `forbidden` を必ず出力する。
- **段 2 プランと段 3 の 2 レンズがいずれも NO-GO を返した。** 親は自分の provisional 裁定 (P5)
  「`spool_fold.py` を変更しない」を**撤回した** — 変更しなければ (ii) が実効 gate にならない。
- **段 3 が親 brief の主張 2 件を実測で覆した。** (a)「新 package なので land 2 と file 非重複」は
  言い過ぎで、land 2 は共有の `preregistration/blobref.py`・`erratum.py`・
  `tests/test_t139_preregistration_binding.py` を変更している (本 wave はいずれも触っていない)。
  (b) 純増検出力の見積もりが過大で、JSONL の canonical 化・append-only・delete/recreate 拒否は
  `orchestrator/campaign/trial_registry.py` に既存である。publication 固有の純増分は
  固定 literal からの無引数 path 導出、0 byte と不在の区別、`ledger_kind` 閉集合、
  primary 空間との互いに素性に限られる。
- **段 6 の敵対レビュー 2 本が blocker 5 件を出した。** 特に (a) `require_d291_projection_exact()` が
  caller の作った payload を権威として使い `F_p` を読まずに承認値を通せた、
  (b) marker gate が壊れた / 重複した triple を握り潰すため、marker 入り blob を pin しつつ
  同じ `sha256` 行をもう一度足すだけで gate が空集合になる fail-open、
  (c) gate が検査していたのは fragment であって実際に書かれる `after_bytes` ではなかった。
  fix 2 本で全件を閉じた。設計判断は {{D:publication-trust-root}} と {{D:marker-gate-scope}} に記録した。
- **変異 matrix は 4/4 KILLED、期待 node 完全一致、baseline 緑。** 第 1 走で M1 / M2 / M4 が
  MISMATCH となり、実測の完全集合へ再照準して第 2 走で一致させた ({{D:marker-gate-scope}} の裏取り)。
  **M2 は fold の 3 経路すべて (discover 2 件・resume・direct apply) を同時に落とした** — marker gate の
  全経路結線が実証された。M1 の再照準では、期待した 9 node のうち 6 件が
  **entry を定数から組み立てるため定数変更に追随し、この定数に対して非感受**であることが判明した。
  実際に落ちるのは literal を pin する 2 node と閉集合 gate の 1 node である。
- **変異の baseline が 1 度だけ偽の赤を出した。**
  `test_codex_worker_launch.py::test_check_receipt_rejects_unknown_and_duplicate_fields` が
  FAILED になったが、単独再走は rc=0 で再現せず、本 wave の差分から到達できない file であるため
  `DW-O18` に従い非帰属とした。中断台帳は `mutation/mutation-ledger-round1.json` の前段として
  job artifact に残した。
- **報告 — main 側に潜在的な脆さがある (本 wave の回帰ではない)。**
  `test_spool_fold.py` の real-repo 4 node は、`tools/spool_fold.py` が複製先の `check_docs.py` を
  importlib で読み、その `check_docs.py` が 2026-08-10 の commit `890fed05` で得た `dev_waves` の
  import を解決できないため、**焦点走 (file 選択走) では落ちる**。テスト helper
  `_copy_real_canonical_family` が `tools/dev_waves/` を複製しないためである。全走では
  `test_check_docs.py` などが module import 時に `sys.path` へ `tools/` を載せる副作用で通る。
  本 wave の差分は `check_docs.py` に一切触れていない。

## 次の一手差分

### 更新

- [T-793] **P2・(ii)・(iv)・(iv-b) と (i) の識別束縛は実装済み。残余は (iii) と (i) の原子性**:
  公表層の機械執行 (裁定 C-5 (a))。**land 2 の §S7 #7 を具体化して同じ producer 系列へ結線するもので、
  別 ownership の並行実装ではない。**
  実装済み = `orchestrator/publication/` の D291 payload resolver + deny-only report、
  公表台帳の識別束縛 (予約 writer なし・台帳 0 byte)、未確定 marker gate の fold 3 経路結線、
  追補 P の `p01`〜`p03` exact-key 検査。
  **残余 = (iii) source 側の本走 gate と (i) の原子性・`(root, ordinal)` 一意性・予約 writer。**
  いずれも承認済み文書・防壁との衝突があり、`output/insights/2026-08-11_t793-pubcore-impl/package.md`
  の R1〜R5 でユーザー裁定へ返している。**追補 P の凍結は R1 / R2 が決着するまで行えない。**
  base: 00bb68f49033be9ca39544841700b677066046b53280292c8f82023cb1222383

### 新規

- {{T:publication-reservation-writer}} **P2・新規**: 公表台帳の予約 writer を
  `tools/dev_wave_land.py` の land lock 内へ統合し、canonical main への取り込みと初出 commit の
  再導出を 1 transaction にする。**R2 の裁定が (a) の場合にのみ着手する。**
- {{T:pubcore-s81-root-erratum}} **P3・新規**: 公表 core v2 §8.1 の
  「`family_root` が primary 系列と同じ commit」という偽命題を canonical erratum / decision で正す。
  **文書は D291 の承認 bytes なので編集しない。** R3 の裁定が (a) の場合に着手する。
- {{T:approval-decision-machine-schema}} **P3・新規**: blob authority を与える canonical decision に
  機械可読な target schema を必須とするか裁定する。現状の marker gate が拒否できるのは
  `approved_blobs:` 形式で三つ組を宣言する fragment だけである (R4 の (b))。
- {{T:spool-fold-real-fixture-closure}} **P3・新規**: `test_spool_fold.py` の
  `_copy_real_canonical_family` が dependency closure を複製せず、焦点走で 4 node が落ちる。
  directory 複製だけでは不十分で、`spec_from_file_location()` が複製先 `tools/` を `sys.path` へ
  加えないため、import 経路を閉じるか rotate limit の読取を `check_docs` の全 module import から
  分離する必要がある (段 6 レビュー C の指摘)。
