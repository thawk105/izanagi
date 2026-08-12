---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t949-951-branch-land
seq: 1
title: 取り残し branch 3 本の成果を内容判定で回収した — 追補 B の段 6 終端裁定を追記型で救出し、cleanup 側は反証済み前提を除いて観測 1 件だけを移し、t657 は裁定へ返した (docs のみ、branch worktree-dev-wave-t949-951-branch-land)
---

## 本文

- **ユーザー依頼 (2026-08-12 22:56 JST の実測に基づく)。** 生きた worktree も担当セッションも無い
  未 land branch 3 本 — `worktree-cleanup-submodule-recurrence` / `worktree-dev-wave-t657-t660-g2-activation` /
  `worktree-dev-wave-t139-addendum-b` — の成果を内容で判定して回収する。**branch の削除はしない**
  (削除はユーザー指示があるときのみ)。3 本はいずれも `[T-951]` / `[T-949]` / `[T-950]` として
  起票済みであり、本 wave はその 3 件を閉じにいった。
- **担当の重複を起動直後に実測して外した。** `dev-wave-t952-residue-sweep` は branch が main の祖先
  (land 済み) で該当 process 0 本、`dev-wave-t139-a12-stress-check` は生存 (受入 lease 待ちの
  pid 716186) だが handoff の scope は `stress_check_simulation` の land だけで追補 B を含まない。
  **どちらも本 wave の 3 件を所有していない。**
- **`[T-950]` (追補 B) は追記型でしか回収できないことを実測で確認した。** main の
  `output/insights/2026-08-09_t139-addendum-b/` は branch より**新しい** — `package.md` は
  2026-08-10 の裁定 Q-B を反映済みで、branch 版は反映前 (B7 を「未裁定」と書いている)。
  `s4-adjudication.md` も両者で分岐しており、main 版は誤りを「erratum 1 (原文は変更しない)」として
  別節に積む形、branch 版は原文を直接書き換える形だった。**branch 版で上書きすると main の後続修正と
  erratum の規律の両方が退行する。**そこで main 版を base に、branch 固有の
  `s6-refocus2.md` / `s6-refocus3.md` を byte 保存で足し、`s4-adjudication.md` へは
  「段 6 の終端裁定」節だけを回収の断り書き付きで追記した。
- **回収した節が持っていた情報は他のどこにも無かった。** 固有語 (`README が blocker の閉鎖数を過大表示`、
  `3 巡かけて収束させた` 等) の grep が `docs/` `output/` 全体で 0 hit。中身は
  段 4 の D-1 / D-4 / D-6 が段 6 で倒れたという supersede 表と、3 巡目の所見 3 件の裁定表である。
  **これが失われると、追補 B を将来再提出する wave が「なぜ `b03` の foreign key を落としたか」を
  再導出できない。**
- **`[T-951]` (cleanup) は逐語 land が不可能だった。**branch の fragment 本文のうち main に無いのは
  運用観測 2 件だけで、そのうち 1 件「ahead>0 の branch を検査なしに消した経路が別に存在する (未特定)」は
  **後の実測で前提そのものが誤りと判明している** (archive の 2026-08-06 エントリ「起票時の前提
  『検査なしに消した』は誤りだった」)。逐語で畳むと、既に台帳が否定した主張を台帳へ入れることになる。
  **fragment を cherry-pick せず、生きた観測 1 件だけを出典付きで本エントリへ移した** (次項)。
- **移した観測 (出典 = branch `worktree-cleanup-submodule-recurrence` の
  `docs/spool/worklog/2026-08-05-cleanup-submodule-recurrence-1.md`、tip `3570935b`)。**
  背景 job が `/cleanup-branches` を 6 回反復実行した (2026-08-03 22:5x 〜 08-05 11:4x) 結果、
  削除できたのは孤立 branch 10 本 (`wt-t361-*` 9 本と `worktree-dev-wave-t337-qualification-authority`)
  だけで、他は毎回すべて稼働中または未コミット差分ありだった。
  **並行 wave が常時 5〜26 本走っている間は、掃除の余地はほとんど無い。**
  掃除の頻度を上げても回収量は増えない、という運用上の見積りとして残す。
- **`[T-951]` の branch には land できるコードが無い。**`e8d0c44c` の実装 (2 段判定監査 148 行) は、
  D95 が provenance で land を止めたあと Codex 実装子が現行 main の上に書き直しており、
  main の `tools/audit_dangling_commits.py` は 26,485 bytes の上位版である。**branch 版を入れると退行する。**
- **`[T-949]` (t657-t660) は land せず裁定へ返した。**先行するユーザー裁定「旧 branch は残してよいが
  **main へ merge しない** (14 commit すべて再利用不可、再導出のこと)」があり、`[T-949]` は
  この裁定が insights docs まで含むかが一意でないとして**ユーザー裁定待ち**で起票されている。
  `DW-STOP` の「ユーザー裁定待ちなら進まず停止」に従い、本 wave は判断を代行しなかった。
  本依頼の「未着地なら land へ」は branch 名を挙げた一般指示であって、この merge 禁止裁定を
  名指しで覆してはいないと読んだ。
- **`[T-949]` について本 wave が足した実測。** (i) branch の
  `output/insights/2026-08-09_t657-t660-g2-activation/` 20 ファイルは main に 1 つも無い。
  (ii) main の `2026-08-10_t657-restore-redesign/` は裁定を受けた**後続の再設計文書**であって
  同一物ではないため、「再導出のこと」は package.md については未履行である。
  (iii) `git diff main <branch>` は archive を大量に `D` と表示する — branch が 3 日古く main が
  進んだためで、**branch の merge は main の archive と decisions を巻き戻す。**回収するなら
  insights の cherry-pick 以外に道はない。
- **branch 版 `package.md` にだけ残る未提示の案を 1 件見つけた。**裁定 B4 の第 5 案
  「core §10・§16 への承認済み erratum で公表手続きを固定する」で、main の landed 版 B4 の
  4 択には無い。ユーザーはこの選択肢を提示されたことがない。**親が裁定パッケージの選択肢集合を
  勝手に増やさない**ため main の `package.md` へは入れず、起票して返す
  ({{T:addendum-b-b4-erratum-option}})。
- **子は使っていない。**実装面 (コード・テスト・script・機械設定) ゼロの docs-only で、
  正しさ防壁に触れず受理集合も変えないため `DW-C00` の軽量版 (子ゼロ) で実施した。
- **`DW-O09` の pin 閉包を docs 面でも取った。**
  `output/insights/2026-08-09_t139-addendum-b/` を pin するのは
  `orchestrator/publication/approval_d291.py` の `addendum-b.md` に対する歴史 BlobRef
  (commit + sha256) 1 件だけで、`s4-adjudication.md` と新規 2 ファイルに pin は無い。
  **`addendum-b.md` は 1 byte も触っていない。**
- **docs-only 受入免除の判定証拠。**tracked 変更は `docs/spool/` の fragment 1 本と
  `output/insights/2026-08-09_t139-addendum-b/` の 3 ファイルのみで、実装面ゼロ・該当 nodeid 不存在。
  加えて `dev-wave-t139-a12-stress-check` を含む 4 wave が受入 lease を争っており
  (lease 1 + 待ち ticket 3)、docs-only の wave がその窓を奪わない方が全体の待ち時間が短い。
- **計算ノードへの焦点走も意図的に投入しなかった。**login node では `pytest` が guard に拒否され、
  計算ノードへ回すには dispatch が要る。しかし**受入 lease が保持中 = 他 wave が受入全走の最中**であり、
  dispatch receipt が `output/` 検査を赤にして他 wave の受入を壊す事故型が既知である。
  機械証拠は `python3 tools/check_docs.py` rc=0 と `python3 tools/spool_fold.py --dry-run` rc=0 の 2 本、
  および回収ファイルの blob oid 一致 (`9176796d`) とした。

## 次の一手差分

### 完了

- [T-950] 追補 B の branch 固有 2 件を回収した。`s6-refocus2.md` (5,735 bytes) と
  `s6-refocus3.md` (7,052 bytes) を byte 保存で追加し、`s4-adjudication.md` へ
  「段 6 の終端裁定」節 (3,866 bytes) を回収の断り書き付きで追記した。main 側の後続修正と
  erratum 節は 1 byte も変えていない。branch 版 `package.md` の第 5 案は
  {{T:addendum-b-b4-erratum-option}} へ分離した。
  remaining: none
  base: 406b12fd807d6411ebd24596a0b48e02c48219cc94965c9bbbc5e25c323d9379
- [T-951] cleanup 側の判定を閉じた。branch の実装は main の再著述版が上位で land 不要、
  fragment の運用観測 2 件のうち 1 件は後の実測で前提が誤りと判明済みのため逐語 land は不可、
  残る 1 件 (掃除の回収量の見積り) を本エントリへ出典付きで移した。**branch に land すべきものは
  もう無い。**削除の可否は本 wave の scope 外として {{T:orphan-branch-deletion-ruling}} へ移す。
  remaining: none
  base: c4706f3d10c2b77cf1b57af0c8436df45bbae571c18005afb2f6e56ba5d8cdd1

### 更新

- [T-949] **P1・ユーザー裁定待ち (実測を追加。択一は不変)**: land 済みの archive worklog が
  `worktree-dev-wave-t657-t660-g2-activation` 上の `package.md` を「正本」と引用しているが、
  同 branch は未 land で参照が解決しない。既存裁定「main へ merge しない (14 commit すべて
  再利用不可)」が insights docs まで含むかが一意でない。択一 = (a) insights docs だけを
  cherry-pick -x で land し実装 commit は入れない、(b) 据え置いて main 側の引用を「参照不能」と
  訂正する、(c) branch を削除し引用も撤回する。**2026-08-12 の追加実測**: branch の insights 20
  ファイルは main に 1 つも無く、main の `2026-08-10_t657-restore-redesign/` は後続の再設計文書で
  あって同一物ではない (「再導出」は package.md については未履行)。また branch の merge は main の
  archive を巻き戻すため、採るなら cherry-pick 以外に道はない。推奨は引き続き (a)。
  base: 38010074e09a35e02aed647f3fe75e131380f701a63ee4ae6120cb602a716a93

### 新規

- {{T:addendum-b-b4-erratum-option}} **P2・新規・ユーザー裁定待ち**: 追補 B の裁定 B4 に、
  停止した branch `worktree-dev-wave-t139-addendum-b` (`84217161`) にだけ残る第 5 案
  「core §10・§16 への承認済み erratum で公表手続きを固定する (現 study を維持したまま)」がある。
  main の landed 版 B4 の 4 択 (新 core の別 study / producer 実装 wave / 追補 B / 記述的な表のみ)
  にはこの道が無く、**ユーザーへ提示されたことがない**。ただしこの案は承認 manifest に従属する —
  承認済み erratum は manifest 不在での適用を禁じ、D262 が `erratum_application_order` と
  `composed_sha256` を固定しているため、erratum を 1 本足すと合成が変わる。**採るには manifest
  第 1 波の R1 (「同一 land」の再解釈) を先に裁定する必要がある。**提示するか否かの裁定を求める。
- {{T:orphan-branch-deletion-ruling}} **P3・新規・ユーザー裁定待ち**: 成果の回収が済んだ
  取り残し branch の削除可否。`worktree-cleanup-submodule-recurrence` は本 wave で回収を終え
  land すべきものが無い。`worktree-dev-wave-t139-addendum-b` も branch 固有 2 件を回収済みで、
  残るのは第 5 案の提示判断だけ ({{T:addendum-b-b4-erratum-option}})。
  `worktree-dev-wave-t657-t660-g2-activation` は `[T-949]` の裁定が先。
  **branch 削除はユーザー指示があるときのみという規律に従い、本 wave は 3 本とも残した。**
  tip SHA は本エントリに無いので、削除時は `git branch --no-merged main -v` の実測から採ること。
