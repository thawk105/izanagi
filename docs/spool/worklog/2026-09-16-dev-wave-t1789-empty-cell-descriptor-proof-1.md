---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t1789-empty-cell-descriptor-proof
seq: 1
title: [T-1789] complete を名乗る trial が実行 descriptor なしで受入 receipt 検証を通る穴を、反例の実走再現のうえで塞いだ (コード + テスト、branch worktree-dev-wave-t1789-empty-cell-descriptor-proof、変異 matrix = baseline PASSED・5/5 KILLED・等価 1/1 SURVIVED・MISMATCH 0・期待 node 完全一致 6/6)
---

## 本文

- **依頼どおり、まず反例を実走で再現した。** [T-1789] の原文は 2026-08-26 の [T-1726] wave 段 3 レンズ A の
  静的所見で、未実走だった。probe は Codex `role=author` に書かせ (repo へは入れず job dir に保全、
  逐語は insight の `verbatim/probe-script.md`)、親が login node で走らせた。
  `status="complete"` の report の cells を空にして C02 を残すと v2 / v5 とも verified になり、
  v5 は `require_current_verified_receipt` まで届いた。期待と食い違う descriptor を持つ report は
  拒否されるのに、cells を消して C02 を足す (v5 は参照 hash・cross-binding・attempt registry も
  整合させる) と受理へ変わることも実測した。止まるのは `layer3_report.build_accepted_report` の
  certifying 検査だけで、現在の certified 成果物への到達は確認していない。
- **欠陥を「complete を名乗る trial に descriptor 証明が無い」に限定し、それだけを直した。**
  partial + cells 空 + C02 保持 (D519 の部分 report、producer が正規に発行する形) は正例として残した。
  legacy が任意の非空 status を受ける点は静的に real だが、実在・被害を再現しておらず、
  値域 gate も台帳項目も足していない。設計判断は {{D:complete-trial-needs-descriptor-proof}}。
- **段 2 plan 1 本 + 段 3 敵対 2 レンズ (A = 正しさ境界、B = 整合・実効性)。real 9 / refuted 7、
  2 レンズは割れず plan を支持。** 最重要は B の「正例は fixture に C02 が無く明示追加が要る
  (無いと mandatory-reasons で落ちる)」。次に A・B 共通の「(P3)『実行を名乗らない』は過大で、
  v5 の status 束縛が保証するのは完了・観測成功の不主張まで」。
- **子が親 brief の誤りを 5 つ訂正させた。** (1) 再現 case が「全部 do_build=False」は C4 を除く。
  (2) 上の P3。(3) driver の status 式だけでは空 selected を排除できず、登録 trial の workload
  singleton 束縛が要る。(4)「検証器は status を見ない」は不正確で、欠けていたのは complete と
  descriptor 証明の対応。(5) DW-G05 の「certifying 世代で B-3 の選択が乗る」は断定できない
  (`build_accepted_report` は certifying 後も campaign 対応・admission・E1 epoch を要求する)。
- **refuted の主なもの。** 共通適用が D1757 に反する (D1757 の却下理由は legacy の失われた campaign
  現物の追加要求で、本件は既に hash 済みの report bytes しか見ない)。新条件が既存 gate の含意
  (D949) — 修正前に verified を実測している。duration 台帳への新 node 登録が必須 (conftest は
  未登録を None、shard は 1 秒を割り当てる。受入で実測確認)。
- **DW-O13:** 実在する trial report は `output/` 全域で 0 件 (探索役、find 完走)。status の値域は
  producer 式と producer テストの読解で決めた。
- **段 6 敵対レビュー 2 本とも must-fix 0。** B の nit 1 件 (commit message の「cells を消して C02 を
  足すだけ」は参照 hash 等の整合を省略) は amend せず insight §2 で正確化した。所見ゼロは
  変異 matrix で裏取りした (DW-M02)。
- **変異 matrix:** m1 判定削除・m2 status 反転・m3 literal 差替え・m4 v5 限定化・m5 ブロック順序
  (診断順 pin、新規検出力に数えない)・m6 等価 (被演算子交換、SURVIVED の正例)。
  baseline PASSED (43 node)、KILLED 5・SURVIVED 1・MISMATCH 0、期待 node 完全一致 6/6。
  台帳と spec は insight に同一 bytes で複製 (spec sha256 84b71d4b…)。
- 焦点走 (v2 / v1 receipt・trial_registry・layer3_report・ccbench_spawn_sites・plain_runner_coverage
  の 6 file、計算ノード request 1582.nqsv) は 603 passed。
- 子の工数: codex 8 本 (probe author 1・plan 1・consult 2・author 1・review 2)、いずれも
  `launcher_rc=0`・`gpt-6-astra`。子は pytest を実走できず、実走はすべて親が代替した。
- 逐語と実測は `output/insights/2026-09-16/t1789-empty-cell-descriptor-proof/`。

## 次の一手差分

### 完了

- [T-1789] `cells=[]` と C02 reason 保持の組み合わせで実行 descriptor が不在のまま expected digest の
  自己申告を verified receipt にできる構造を、反例の実走再現のうえで塞いだ。complete を名乗る trial に
  限定し、部分 report の C02 保持 (D519) は変えていない。
  remaining: none
  base: 0da690016b9b789c0320bd35f73cecf1cfe9742867aa00807147f3010dc39d8a
