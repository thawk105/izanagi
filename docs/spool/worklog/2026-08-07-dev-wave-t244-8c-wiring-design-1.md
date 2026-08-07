---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-07
wave: dev-wave-t244-8c-wiring-design
seq: 1
title: [T-244] 8c 結線の前提 5 点を設計した — 敵対 2 レンズの blocker 8 件を親が現物で裏取りして織り込み、発行 3 条件は依然 0/3 と確定した (docs のみ、実装差分なし、branch worktree-dev-wave-t244-8c-wiring-design)
---

## 本文

- **U-10 批准後に唯一起票できる設計 wave を実行した。** 正本は
  `docs/phase3-8c-wiring-design.md` (新規)。設計判断は {{D:wiring-preconditions-8c}}。
  **実装差分は無い** — 差分は docs 3 点と spool fragment だけで、変異 matrix と受入全走は対象外。
- **敵対 2 レンズは独立に NO-GO を返し、blocker 8 件・must-fix 8 件を挙げた。**
  親は主要 5 件を worktree の現コードで裏取りし、16 件すべてを real と裁定した。
  レンズの NO-GO は「プランのまま確定するな」であって「設計をやめよ」ではないため、
  所見を織り込んだ本文を land する形で閉じた。
- **親が現物で確認した新事実 3 件** (いずれも設計を書かなければ実装 wave の途中まで露見しなかった)。
  (a) **末尾の全 tombstone batch は certifiable seal を通る** — candidate 下限検査が
  `0 < sealed_distinct_candidate_count < minimum` なので 0 件の batch は検査に入らず、
  33 行成功後に 2 行の全 tombstone batch を足しても `aborted=False` を送れる。
  (b) **同一 mask の重複行は現 campaign ループが物理実行しない** — source の mask は validation
  sweep にも現れるが、1 run 内では variant identity で skip されるため `sealed_queries ≤ 32` となり
  floor 33 を割る。1 query = 1 campaign run が要件になる (費用 33 倍)。
  (c) **production runtime の初期化経路が存在しない** — 初期化は fixture 専用で production は
  明示拒否されており、発行 3 条件を満たしても最初の read/reserve が失敗する。
- **親の provisional 裁定 3 件を撤回した。** (P1) の「1 authority series 内」は過大 (正しくは
  同一 authority blob 内)、(P2) の「seal builder だけで閉じる」は不足 (formal consumer と双射と
  receipt 束縛が要る)、(P3) の「33 行を 4 batch 以下へ割る」は誤り (1 batch 33 行に強制される)。
  (P3) のうち「行数下限 2 は 32 mask sweep なら自然に満たされる」は成立したが、
  「V-3 の不整合は探索側にだけ残る」は誤りだった。
- **段 1 実測値の一般化 4 件も訂正した。** `batch_count=4` は codec 容量計算上の値で実 topology の
  batch 数ではない、brief の phase 列は happy path で FSM 全体ではない、sealed launch admission は
  同一 process 内の gate であって durable capability ではない、32 mask の正準集合は emitter の
  有限集合を示すだけで 32 物理 attempt producer の存在を示さない。
- **本番 authority は 1 byte も変えていない** (71 bytes・`origins: []`、sha256 `76fb551f…` を
  段 1 と段 7 の双方で実測)。段 1 の前提実測は repo 外の使い捨て probe で行い、repo へは
  書いていない。逐語と出力だけを insight へ凍結し、probe の `.py` 自体は実装面契約に従い commit しない。
- **裁定パッケージ 5 件 (V-6〜V-10) は未裁定**: V-6 末尾の全 tombstone batch を ledger 側でも
  拒否するか (推奨 = 拒否する) / V-7 production runtime の初期化経路 (推奨 = 人間承認 provisioning と
  同じ手続で人間が一回だけ実行) / V-8 物理実行を 1 query = 1 campaign run にするか (推奨 = する。
  費用 33 倍) / V-9 `imax` `qmax` の再批准 (推奨 = 内訳を差し替えて `4/68` を維持) /
  V-10 evidence writer の権限分離 (推奨 = 作らず保証限界として明記)。
- 一次資料 = `output/insights/2026-08-07_t244-8c-wiring-design/`
  (段 2 プラン + 敵対 2 本 + 段 4 裁定を全文凍結)。

## 次の一手差分

### 更新

- [T-244] **P3 の 8c 結線は前提設計まで完了 (実装は不能のまま、D201)。U-10 は批准済み (値確定、
  発行は 3 条件成立後だが 3 条件は 0/3)。U-8 は実装済み (D217)。U-3 は凍結 (W-1〜3 裁定済み)。
  P2 は critic 境界の pseudonymization まで。P4 は ledger 側適合、P5 残余は U-2、未着手は P7・P9**:
  **8c 結線の前提設計: 2026-08-07 に完了** — source closure / result-evidence の exact 化 /
  32 mask producer topology / origin binding capability / 失敗・crash の event 対応を
  `docs/phase3-8c-wiring-design.md` に設計した ({{D:wiring-preconditions-8c}})。
  **設計しただけで発行 3 条件は 0/3 のまま** — V-2 は artifact と consumer が未存在、
  topology は 33 物理 attempt を生む producer が未存在、許可経路は **production runtime の
  初期化経路そのものが存在しない**。本番 authority は entry 0 を維持する。
  **裁定パッケージ 5 件 (V-6〜V-10) が未裁定**: 末尾の全 tombstone batch を ledger 側でも拒否するか /
  production runtime 初期化経路の作り方 / 物理実行を 1 query = 1 campaign run にするか (費用 33 倍) /
  `imax` `qmax` の再批准 (内訳が変わり post-commit crash 余裕が無い) / evidence writer の権限分離。
  **V-6〜V-10 が裁定されるまで結線の実装 wave は起票しない。**
  正本 = `output/insights/2026-08-07_t244-8c-wiring-design/s4-adjudication.md` §6。
  **U-8: 2026-08-07 に実装済み** — 8c 自律 trial の critic 呼び出しを workload ごとの
  cell Layer 3 admission 確定後へ後置した。**U-8 は完了していない** — ledger seal・proof 書き込み・
  proposal と raw response の seal 後公開はいずれも未実装で、critic は依然 seal より前に metrics を
  受け取る。名乗ってよいのは「8c 非認定 pilot の critic 呼び出しを cell の Layer 3 admission
  確定後へ後置した」までである。
  **U-8 wave のパッケージ 3 件は 2026-08-07 の /rulings で裁定済み**: (1) 残余は 8c 前提設計
  wave の後に **ledger seal → proof 書き込み → seal 後公開の順**で D96 分割起票する (証拠の
  型の確定 → 永続化 → 公開の依存順。**本 wave で前提設計は完了したので、この順序の先頭が
  起票可能条件に入るのは V-6〜V-10 の裁定後である**) / (2) cap-lift 前提条項を追認 —
  `MAX_APPROVED_GENERATIONS` を 2 以上へ上げる将来の裁定は、後置により多世代 journal 順が
  completeness と食い違い fail-closed になる事実を前提にし、critic 還流の成立を同時に裁定する /
  (3) `partial` trial と positive Layer 3 material の quarantine 境界は現状追認 — partial は正規
  terminal のまま F4 の検出力で監視し、certified 選択へ partial 由来材料が入る経路の実装時に再訪 (D205)。
  正本 = `output/insights/2026-08-07_t244-p3-u8-critic-after-admission/s4-adjudication.md` §6。
  **U-3 (ever-issued cell 台帳): 2026-08-07 に実装しないと裁定済み (D211)** — repo 内台帳が
  単調にならず、批准済み U-2 (b) と実装面で両立しない。**W-1〜W-3 は 2026-08-07 の /rulings で
  推奨どおり裁定済み** — W-1 単独実装は取り下げ epoch router 設計 wave へ吸収 / W-2 U-3 は
  epoch router 実装後まで凍結 (U-2 (b) は動かさない) / W-3 同一 commit 整合の別名検査は入れない。
  正本 = `output/insights/2026-08-07_t244-p3-u3-ever-issued-cell/s4-adjudication.md`。
  **U-10: 2026-08-06 に批准済み** — 択一 8 件 (甲 1・2・3・5・6・8 / 乙 4 / 丙 7・丙-較正) と
  値を推奨どおり確定:
  `imax=4 / qmax=68 / kmax=1 / batch_member_row_count_min=2 /
  batch_distinct_candidate_count_min=1 / floor=(base 1, per_round 32, rounds 1, evidence_min 0)`、
  `F=33`。`R=1` は形式下限であり科学的十分性は主張しない。**逸脱 2 点も是**: 較正を根拠に
  使わない起草を是とし、**authority record の実発行は「V-2 evidence 正本 + producer topology +
  許可された実行経路」の 3 件成立後の人間承認 provisioning で行う** — それまで本番 authority は
  entry 0 のまま。正本 = `output/insights/2026-08-06_t244-u10-budget-values/README.md`。
  **値の批准も設計の完了も結線の許可ではない。**
  **今 fireable な P3 分割 wave は無い** — U-3 は凍結、8c 結線は V-6〜V-10 待ち。
  残るのは epoch router 設計 wave (W-1 吸収先)。U-7 は確定済み (Pegasus で新規測定)。
  **P2**: critic recipient 境界の候補識別子を campaign-local な不透明ラベルへ射影済み (D192)。
  名乗りの上限は pseudonymization までで、origin-scope ID・non-interference・P2 充足・
  U-1〜U-3 の完了は名乗らない。
  **閉じた成果層は 0 / 11** で、certified 選択・材料レポート・試行台帳・proof chain の
  現在値と参照はすべて不変である。
  **P1**: 変わらず機械部品のみで未充足。**P4**: ledger 側実装済み (D166)、充足は名乗らない。
  **P5**: 残余は U-2 のみ。**未着手**: P7・P9。P3 は依然 FAIL、cap-lift FAIL、D114 上限 1 不変
  base: d1f0e4cb6fc5ea5ff1dd029c4ff5a11e6e7d30607deb159eb2bc33c68d7246d1
