---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t244-p3-u3-ever-issued
seq: 1
title: P3 の ever-issued cell 台帳 (U-3) は実装しないと裁定した — repo 内台帳が単調にならず、批准済みの U-2 (b) と両立しないため択一 3 件を再裁定へ返す (docs のみ、実装差分なし、branch worktree-dev-wave-t244-p3-u3-ever-issued)
---

## 本文

- **本 wave の射程。** ユーザー裁定 U-3 (a) の実装可否を段 2・3 で検証し、**実装しないと裁定した**。
  実装差分が無いため、変異 matrix と実装後の受入全走は対象外である。名乗ってよいのは
  「実装可否を検証して裁定と択一を返した」までで、P3 充足・provisioning 解禁・多世代開放・
  cap-lift・certified 選択は名乗らない。「全世代重複拒否を実装した」とも名乗らない。
- **段 3 の 2 レンズが独立に同じ迂回路を構成した。** repo 内に置く台帳は authority と同じ
  捕捉 commit から読むため、新しい authority を書く主体が同じ commit で台帳の該当 entry を
  新 origin へ**置換**でき、gate を素通りする。すなわち実装できるのは「1 commit 内の
  2 ファイルの整合」であって「ever-issued」ではない。設計判断は {{D:u3-ever-issued-not-monotone}}。
- **裁定時点で未見だった新事実を 2 件記録する。** (i) U-3 が前提にした「世代」は実装のどこにも
  存在しない — authority document の key は 2 つだけで、ledger 本体に epoch / generation の
  綴りは 0 件、production runtime 初期化は明示禁止のままである。(ii) 単調性を与える 2 手段
  (外部 append-only anchor / 検証可能な predecessor chain) は、前者が **U-2 で却下されて (b) が
  批准済み**、後者が未実装で設計 wave 送りである。**U-2 (b) と U-3 (a) は現状の実装面で両立しない。**
- **親の provisional 裁定 4 件のうち 3 件を自分で撤回した。** 「世代」を「同一 series の連続する
  authority document」と読み替える案 (continuity を表現する field が無い)、repo 内 commit 済み
  artifact を substrate にする案 (上記の置換で破れる)、既存の同型検査をもって DW-G04 の発火 gate を
  満たすとした判断 (既存の単一 blob 内 cell 重複検査は新 gate の発火経路ではない) の 3 件である。
- **親の段 1 実測に誤りが 1 件あり、両レンズが独立に指摘して訂正した。** authority の
  `duplicate authority origin` の枝は、その手前の厳密昇順検査が同じ入力に対して必ず先に発火するため
  **到達不能**である。既存テストが固定しているのは cell 4-tuple 重複の正負例だけで、
  origin 重複と digest 衝突の専用入力は持たない。erratum は逐語の `parent-measured.md` に入れた。
- **プランの事実誤認を親が実測で潰した 1 件。** 段 2 プランは過去 wave の liveness probe を
  「歴史 artifact なので非互換を記録するだけでよい」としたが、これを subprocess 実行して
  `returncode == 0` を要求する現役の受入テストが実在する。実装していれば受入全走が赤になっていた。
- **ユーザー再裁定へ返す択一 3 件。** (W-1) U-3 の substrate を clone common-dir の耐久単調台帳 /
  predecessor chain 同梱 / 単独実装取り下げ (epoch router 設計 wave へ吸収) から選ぶ。推奨は取り下げ。
  (W-2) U-2 (b) と U-3 (a) の非両立を、U-3 の弱化 / U-2 の再裁定 / U-3 の凍結のどれで解くか。
  推奨は凍結。(W-3) 同一 commit の authority ↔ registry 整合だけを別名の防御部品として今入れるか。
  推奨は入れない (発火経路が無く、現役 consumer を壊し、D205 の防御的堅牢化の見送りに当たる)。
- **実測の順序 (`DW-O12`)。** 段 1 前提実測 → brief → 段 2 プラン → 段 3 敵対 2 本 → 段 4 裁定の順で
  実行した。段 5・6 は裁定により実行していない。段 2・3 の途中で local main が進んだため、
  記録前に `--ff-only` で取り込んでから base digest を採り直した。
- **成果物の所在。** brief・前提実測 (erratum 込み)・段 4 裁定は
  `output/insights/2026-08-07_t244-p3-u3-ever-issued-cell/`。段 2 プランと段 3 の 2 レンズの逐語は
  repo 外の wave job dir。

## 次の一手差分

### 更新

- [T-244] **P3 の 8c 結線は実装不能 (D201)、U-3 の ever-issued cell 台帳も実装しないと裁定 ({{D:u3-ever-issued-not-monotone}})。U-10 は批准済み (値確定、発行は 3 条件成立後)。P2 は critic 境界の pseudonymization まで。P4 は ledger 側適合、P5 残余は U-2、未着手は P7・P9**:
  **U-3 (ever-issued cell 台帳): 2026-08-07 に実装しないと裁定し、択一 3 件を再裁定へ返した。**
  repo 内に置く台帳は authority と同じ捕捉 commit から読むため、新 authority を書く主体が
  同じ commit で台帳 entry を置換でき、狙った再発行が素通りする (段 3 の 2 レンズが独立に構成)。
  単調性を与える外部 append-only anchor は U-2 で却下済み、predecessor chain (epoch router) は
  未実装で設計 wave 送り。**U-2 (b) と U-3 (a) は現状の実装面で両立しない。**
  台帳を書く issuer も無く、DW-G04 の発火 gate を満たす既存 artifact path も書けない。
  返した択一は (W-1) substrate の選択 (推奨 = 単独実装を取り下げ epoch router 設計 wave へ吸収)、
  (W-2) 非両立の解き方 (推奨 = U-3 を epoch router 実装後まで凍結)、
  (W-3) 同一 commit 整合だけを別名で入れるか (推奨 = 入れない)。
  正本 = `output/insights/2026-08-07_t244-p3-u3-ever-issued-cell/s4-adjudication.md`。
  **今 fireable な分割 wave は critic 後置 (U-8) の 1 本だけになった。**
  **U-10: 2026-08-06 に批准済み** — 択一 8 件 (甲 1・2・3・5・6・8 / 乙 4 / 丙 7・丙-較正) と
  値を推奨どおり確定:
  `imax=4 / qmax=68 / kmax=1 / batch_member_row_count_min=2 /
  batch_distinct_candidate_count_min=1 / floor=(base 1, per_round 32, rounds 1, evidence_min 0)`、
  `F=33`。`R=1` は形式下限であり科学的十分性は主張しない (上げるなら R=1 の実走再現性を
  測ってから)。**逸脱 2 点も是**: 較正を根拠に使わない起草を是とし、**authority record の
  実発行は「V-2 evidence 正本 + producer topology + 許可された実行経路」の 3 件成立後の
  人間承認 provisioning で行う** — それまで本番 authority は entry 0 のまま。値の変更が要る
  場合の再計算規則は正本 §6。乙 (択一 4 = V-2 の方向: 物理実行点で trusted harness が
  create-only の result-evidence record を発行) の exact 化は設計 wave へ。
  正本 = `output/insights/2026-08-06_t244-u10-budget-values/README.md`。
  **値の批准は結線の許可ではない** — D201 の 3 阻害要因は 0/3 件しか解けず、次に起票できるのは
  結線の実装 wave ではなく設計 wave (source closure / V-2 の exact schema と outcome 対応 /
  32 mask producer / launch binding / 失敗と crash の event 対応)。
  **8c パッケージ 5 件は 2026-08-06 の /rulings で裁定済み** — V-1 発火経路は U-10 裁定まで
  設計メモに留める (値確定により以後は上記 3 条件が gate) / V-2 と V-3 は本値案の択一 4・5 に
  取り込んだ / V-4 束縛は launch admission が発行する capability / V-5 crash 回収と receipt
  喪失照合は結線の前提として先に設計する。U-7 は確定済み (Pegasus で新規測定)。
  **P2**: critic recipient 境界の候補識別子を campaign-local な不透明ラベルへ射影済み (D192)。
  名乗りの上限は pseudonymization までで、origin-scope ID・non-interference・P2 充足・
  P2 の U-1〜U-3 の完了は名乗らない。前 wave のパッケージ V-1〜V-5 は裁定済み (正本 =
  `output/insights/2026-08-06_t244-p2-noninterference/rulings-package.md`)。
  **閉じた成果層は 0 / 11** で、certified 選択・材料レポート・試行台帳・proof chain の
  現在値と参照はすべて不変である。
  **P1**: 変わらず機械部品のみで未充足。**P4**: ledger 側実装済み (D166)、充足は名乗らない。
  **P5**: 残余は U-2 のみ。**未着手**: P7・P9。P3 は依然 FAIL、cap-lift FAIL、D114 上限 1 不変
  base: 58fb0706bf1f2c6bae02f29d03df26f0236ecda6e76f26ae5d05fda5a92272f6
