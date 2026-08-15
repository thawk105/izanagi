---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t338-rf-validator
seq: 1
title: [T-338] Q11 validator は発火条件 (ii)(iii) の不成立で実装できないと項目別に実測した — pilot の解禁条件が D320 で保留終端になった公表層を待っている連鎖を特定 (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t338-rf-validator)
---

## 本文

- **依頼 (背景 job、2026-08-15 23:33 JST) は「[T-338] の残件 = Q11 が指定した独立 validator を
  実装せよ。J の事後追加禁止が機械的に効くことをテストで固定せよ。[T-339] へ流す分は実装するな」
  だった。実装しなかった。** 段 2 プランと段 3 の敵対 2 レンズが**独立に NO-GO** を返し、
  親が一次資料で検算して成立を確認したため `DW-S04` に従い裁定パッケージへ返した。
  成果物 = `output/insights/2026-08-16_t338-rf-validator-trigger-audit/`
  (裁定パッケージは `package.md`、発火条件監査は `trigger-audit.md`)。
- **依頼が引く裁定 (2026-08-03、worklog (142)) は後発 2 件で上書きされていた。** D162 決定 (10) が
  機械化を 3 条件の**連言**に懸け (`DW-G04`)、D229 決定 (6) が着手順序を
  `producer → pilot → validator/consumer → 本走` に固定して「9 層原子的許可」と
  「D162 決定 (10) の書き換え」を両方却下している。依頼文はこの 2 件に触れていない。
- **発火条件を項目別に実測した (F157 の恒久対応が要求した粒度)。** (i) は成立 —
  request `892042.nqsv` と事前登録 `2026-08-05_t139-alt-x-probe/preregistration.md` (冒頭で
  実走前凍結を宣言、witness が `preregistration_sha256` で束縛)。(ii) は**不成立** — 4 項のうち
  `env_tag` と `attestation` が artifact dir 全体で **0 file hit**。checkout は `repo_head` /
  `ccbench_head` として、pin は 5 つの sha256 と `dependency-witness.tsv` の
  `expected_pin == observed_head` として実在する。(iii) も**不成立** — RF 判定を読む語 6 種の
  `orchestrator/` `tools/` 検索が **0 行** (head で切らず全件計数)。
  **この結論は F157 が 2026-08-07 に確定させた事実認定と一致する** — 9 日後の再監査で同じになった
  ことは、(ii)(iii) を動かす pilot がその間 1 本も実走していないことを意味する。
- **pilot が止まっている連鎖を特定した (本 wave の主産物)。**
  `validator 不可 ← (ii)(iii) 不成立 ← pilot 未実走 ← pilot_submission = forbidden ←
  追補 P 未凍結 ← 「公表台帳の実体の確定」待ち = 公表層実装 wave の裁定事項 ←
  公表層の残り実装 (R1/R2) は [T-793] で D320 により保留終端`。
  **最下段は「論文粒度の主張に不要」というユーザー裁定である。**
  ただし「公表台帳の実体の同定」が [T-793] R1/R2 に含まれるかは台帳から確定できなかった。
  連鎖が本当に閉じているかはこの 1 点で変わるため、断定せず裁定へ返した。
- **レンズが親 brief の誤りを 5 件倒した (すべて採用)。** (1) 後発裁定は 2 件でなく
  D264 / D282 / D291 / D292 も拘束し、親は「記録項目の裁定 gate」を D229 決定 (7) と取り違えていた
  (正しくは決定 (6) の中、決定 (7) は T-126 部品が再利用可能という見積り訂正)。
  (2) 「RF 実装 0 hit」の一般化が過大 — RF calculator と consumer は 0 だが、D282 parser・
  receipt schema・T-126 の試行台帳と投入束縛は実在する。(3) **J は「規則」と「選択済み値」を
  分けねばならない** — 規則 (`J_max=13`、候補集合、選択式、結果後の変更禁止、pilot slot `[1..8]`、
  main の slot 数と J の一致、予備の非算入) は D282 が digest 凍結済みで、未存在なのは pilot から
  導かれた選択済み J と、それを本走最初の qsub より前へ束縛する実 validator / admission だけである。
  (4) J の事後追加は 4 経路で迂回でき、再起票条件だけでは塞げない。(5) 「pilot 投入不可」は
  規範状態であって機械 gate ではない (親が挙げた `stress_check_simulation.py` の値は状態表示で、
  同 module 冒頭が admission gate でないと明記している)。
- **親自身の (i) 判定も誤っており、段 2 が倒した。** 親は中間報告で「事前登録は実走より後だから
  (i) 不成立」と述べたが、見ていたのは本走用の別文書 (`2026-08-07_t139-mainrun-design/`) だった。
- **実装候補 6 件はすべて却下された** — validator / consumer 本体、D229 決定 (2)〜(5) の純粋統計核
  (実体は Q11 が [T-339] へ置いた RF calculator で、未結線 leaf になる)、既存 `verify_floor_artifact`
  の流用 (RF を floor 閉表へ混載することは D162 決定 (9) と Q11 推奨 2 に反する)、
  既存自己申告経路の先行硬化 (修正対象の consumer が 0)、J 禁止の prereg 機構への結線
  (固定できるのは文書 bytes までで追加 qsub と結果後の slot 追加を止めない)、
  `892042` を fixture にした拒否テスト (accept 枝のない deny-only leaf)。
- **レンズ B が親の「実装可能 slice 0 件」を部分的に倒した (real・採用、ただし scope 外)。**
  権威を持たない producer / attempt 台帳の前段は D229 が禁じていない (決定 (6)(7))。
  ただしこれは依頼が除外した [T-339] 前段であり、本 wave では実装しない。
- **J の事後追加を塞ぐ 4 変異を必須 kill として事前登録した** (D229 決定 (8) の 3 件に追加) —
  不利な系列を捨てて新 `parent_series_id` / `family_root` を自己申告する、pilot raw を見た後に
  erratum を「本走前」として追加する、不利な pilot receipt を出さず新 study で pilot を再走する、
  同一 allocation・node・時間窓を複数 cluster ID へ分割する (または block を cluster へ読み替える)。
  いずれも成功すれば正例の `not_certifiable` が `partial_recovery` へ反転する。
- **[T-339] 境界 (依頼が明記を求めたもの):** 本 wave が実装しなかったのは
  計測 producer / attempt registry / schedule validator / RF calculator / [T-337] の適格性権威 /
  層 3 の次版 (`trial × candidate × workload × contrast` を key とする別区画) /
  selector・材料レポートの consumer / 双射・変異検査。本 wave が確定させたのは
  発火条件の項目別現況、実装候補 6 件の却下理由、J の規則と選択済み値の分離、4 必須 kill 変異。
- **規律 2 の扱い:** 報告値を採る経路を新設していない。現状は RF を消費する経路そのものが 0 件で、
  producer 自己申告から正例へ昇格する経路は存在しない。規律 2 は「緩めなかった」のではなく
  「緩める対象がまだ無い」状態のままである。
- **受入全走 1 走目は緑** — tested_main `7a7c41a2`、tested_tip `fbc07918`、request `912408.nqsv`、
  **11159 passed / 65 skipped**、rc=0、`verdict = child-green`、赤 nodeid 0 件、テスト実行 147.57 秒。
  実装差分ゼロだが `DW-S04` は受入全走を免除しないため実走した。記録後検査は
  `check_docs.py` rc=0、`spool_fold.py --dry-run` rc=0 (status=planned)、provenance 監査
  3424 件で新規違反なし。
- 子は段 2 プラン 1 本 (`reasoning=max`、17 分) と段 3 敵対 2 本 (sol / luna、並列、
  それぞれ約 9 分 / 16 分)。3 本とも `check_codex_output.py` rc=0。実装子と fix 子は起動していない。
  実装差分ゼロのため変異 matrix は `DW-S04` の免除条項の対象。

## 次の一手差分

### 更新

- [T-338] **P1・裁定完了 (11/11) だが実装は発火条件待ち → ユーザー裁定待ち (択 A/B/C/D)**:
  Q11 の validator は D162 決定 (10) の発火条件 (ii)(iii) が不成立のため実装できない
  (項目別実測は 2026-08-16 wave)。(i) は request `892042.nqsv` で成立。
  塞いでいるのは pilot であり、その解禁は
  `pilot_submission = forbidden → 追補 P 未凍結 → 公表台帳の実体の確定待ち →
  公表層の残り実装は [T-793] で D320 により保留終端` という連鎖にある。
  **親推奨は D1 (発火条件 (ii) から attestation を落とす。環境タグは D320 対象外なので残す) +
  D2 (pilot 解禁条件から公表層実装を切り離す) を先に裁定し、その上で B (全順序を 1 scope へ戻す)**。
  択 C (validator を pilot より先に置く) は依頼の文字通りだが、raw receipt を出す producer が
  無いため合成 fixture だけの未結線 leaf になり親は推奨しない。
  正本 = `output/insights/2026-08-16_t338-rf-validator-trigger-audit/package.md`。
  base: d859fdea8841af71561db2d09ccfa7d4dc74467bda5df411506a4197b14eb08e
