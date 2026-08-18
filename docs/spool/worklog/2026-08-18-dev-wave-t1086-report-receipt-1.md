---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1086-report-receipt
seq: 1
title: oracle 実走後の store 再読を報告 receipt で塞いだ — 防御が実際にどの層で効いているかは変異が 2 度覆した (コード + テスト + 記録、branch worktree-dev-wave-t1086-report-receipt、変異 matrix = baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

2026-08-15 /rulings 全件の裁定 (報告の receipt で塞ぐ) を実装した。設計判断は
{{D:post-run-store-receipt}} と {{D:receipt-outer-state-rederived}}。

**起動時の重複検査:** 引数の指示どおり [T-1103] の現状を台帳で確認した。`docs/phase3.md` の
見送り棚に「(b) 現状維持」で確定済みであり、二重着手は無い。

**親の実測が brief を 2 箇所訂正した。**

- brief は成果物影響を「certified 選択の proof chain」と書いたが、`layer3_report.py` が
  「No certified-selection consumer exists in this checkout」と明記している。現 checkout で
  本 wave が実際に変えるのは observations report / oracle verdict / combined verdict までで、
  certified 選択値と台帳行は変わらない。裁定と commit message はこの限定形で書いた。
- brief の「post-run の store 再読は repo 全体に 0 件」は不正確だった。floor campaign の
  `_verify_resume_store` は store を再読するが、それは resume の**実走前** gate である。
  正しくは「実走終了〜report 生成の窓については 0 件」。

**敵対レビューが親の DW-O09 判定を覆した。** 親は「凍結 bytes の pin 閉包は 0 件」と判定して
いたが、これは成果物 bytes の pin についてのみ正しかった。段 3 レンズ B が
generator source hash の pin 系統を指摘し、親が一時変異で実測したところ、
`s8b_oracle_report.py` を 1 byte 変えるだけで `test_s8b_oracle_manifest.py` の 100 件中
ちょうど 2 件が赤になることが確定した (F226 と同型)。production 側は
`APPROVED_SPEC_SHA256 = None` のため未発火で、赤くなるのは test golden だけである。
この実測を段 5 prompt へ入れ、実装子が golden の埋め込み literal を再同期した。
以後 report / judge へ触るたびに親が独立に再計算して照合している。

**段 3・段 6 の裁定 (real / refuted)。** real で採用したのは、恒真性の負例不足、
symlink escape の killer 不成立、`O_NOFOLLOW` の実効性を検査するテストの不在、
CLI baseline の条件不足、source hash pin の見落としである。**refuted は 2 件** —
legacy manifest 経路が黙って緑になるという疑いは既存の `manifest-kind` 理由で
indeterminate になるため成立せず、期待 SHA が run の自己申告に退化しているという疑いも
`reverify_published_freeze` 経由で独立していることを確認して反証した。
`judge_oracle` の集約 gate から store 理由を外す変異 (旧 M7) は、`unknown = bool(top_reasons)`
により受理集合が変わらないため事前登録から外した。

**変異 matrix が「どこで防御しているか」の親の理解を 2 度覆した。** 詳細は {{F:layered-defence-mutation-misattribution}}。
最終結果は baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0 で、
attempt 1 と attempt 3 は erratum として残した。

**フレーク 2 件** (いずれも本 wave の差分から到達不能、単独走で非再現):
`test_t126_pegasus_tools.py::test_submit_rejects_symlink_component_hidden_drift_and_skip_worktree`
(attempt 2 の M6 に混入)、
`test_campaign_claim.py::test_two_real_processes_racing_acquire_have_exactly_one_winner`
(attempt 3 の baseline を落とし、その attempt を丸ごと無効にした。単独走は 26 件全緑)。

**main 取り込みの順序を入れ替えた。** merge base から見て local main と本 wave が同じ実装面 file
(`orchestrator/tests/test_s8b_oracle_driver.py`) を触っていたため、通常 merge では 3 方向結合の
結果が両親と異なり来歴 checker が merge 自体を実装面の著作と判定する。F226 の直前に記録された
恒久手順どおり、Codex 実装子が main 側の 3 行を先に wave branch へ取り込んでから merge した。

**wave 途中で子の起動契約が main 側で変わった。** 本 wave が子を投入した時点の
`docs/dev-wave/operations.md` は model を段 3 だけ 2 lane (`gpt-5.6-sol` / `gpt-5.6-luna`)、
他段を `gpt-5.6-sol` と定めており、`docs/dev-wave/workers.md` は実装子と段 6 レビューを
`reasoning=high` と定めていた。受入直前に取り込んだ main では全段 `gpt-5.6-luna`・
`reasoning=max` へ変わっている。本 wave の receipt が記録する model / effort はいずれも
**投入時点の契約に一致**しており、後から現行 docs と突き合わせると食い違って見える。
読み込み契約は操作直前の節を正本とするため巻き戻しはしていない。

**scope 外として裁定パッケージへ回した 2 件** — (1) 実走前 gate 側の
`s8b_oracle_driver._store_sha256` も symlink を辿り regular file を確認せず全体を一括読みする。
同じ穴だが本 wave の変更面ではなく、族一般化に必要な独立 2 例が揃っていない。
(2) store と receipt を同時に改変されると determinate へ到達できる。これは [T-1103] が
明示的に見送った偽造耐性の面と同一である。

**nit として残したもの:** `test_s8b_oracle_report.py` の `_judge` ヘルパは official observations に
receipt が無ければ正常 receipt を自動挿入する。同 file の既存 report→judge テストが
「direct API は非 certifying」を検査しなくなるが、専用の欠落対照と実 v2 E2E が別にあるため
成果物影響を書けず、must-fix にはしなかった。

## 次の一手差分

### 完了

- [T-1086] oracle 実走後の store 再読を報告の receipt で塞いだ。report が
  `ReverifiedFreeze.binaries_by_cell` を権威源として各 store を読み直し、
  `store_reverification` を observations へ載せる。judge は独立な closed schema で
  再検査し、欠落・矛盾・不一致・不在を indeterminate にする。judge API と judge CLI は不変。
  恒真にならない負の対照 (空・部分集合・重複・outer と cell の矛盾・symlink escape・
  stat と open の競合・receipt 欠落・combined verdict への伝播・production caller の一意性) を
  同じ land に含めた。変異 matrix = baseline PASSED・12/12 KILLED・SURVIVED 0・MISMATCH 0。
  remaining: none
  base: b6d97cfd36b9e2d114787c2b9c281e54d158996bf337e494f1f9323db42ee0e2

### 新規

- {{T:prerun-store-read-hardening}} **P3・新規**: 実走前 gate の
  `s8b_oracle_driver._store_sha256` を no-follow / regular-file 確認 / chunk 読みへ揃える。
  本 wave の report 側と同じ穴だが変更面が異なり、族一般化に必要な独立 2 例が揃っていない。
  着手条件 = 同型の実害 1 件、または driver 側を触る別 wave への相乗り。
