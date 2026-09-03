---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: rulings-selfimprove-20260903e
seq: 1
title: /rulings 全件 第 6 回 — 8 件を裁定し、索引案の 8 件が既裁定と判明した。うち 2 件は親の推奨が既裁定と逆向きで、相談が収集漏れも 1 件出した (docs のみ、branch worktree-rulings-selfimprove-20260903e、実装面の差分 0)
---

## 本文

- **収集は 455 項の実体解決から始めた。** 末尾エントリの「次の一手」は大半が持ち越し stub なので、
  archive 1002 file まで遡って全項の実体を解決した (欠落 0)。稼働 20 worktree / 66 branch を
  走査して未 land の spool fragment 35 件も集めた。
- **ユーザーが 8 件を一括裁定した (すべて推奨どおり)。**
  {{D:b10-historical-binding-per-series}}、{{D:axis3-core-rewritten-on-remaining-differentiators}}、
  {{D:s4-launch-layer-owns-classification-policy}}、{{D:no-approved-cmake-registry}}、
  {{D:job-termination-stays-disclosure}}、{{D:acceptance-wall-split-dominant-files}}、
  {{D:write-intent-pin-needs-materials-first}}、
  {{D:axis1-write-guard-and-old-epoch-freeze-declined}}。
- **親の索引案 24 件のうち 8 件が既裁定だった。** 別系統モデル 2 本 (どちらも `gpt-5.6-sol`、
  read-only、`reasoning=high`) が独立に指摘した。内訳は D1548 / D1578 / D1583 / D1469 / D320 /
  D1439 / D1379 / D782。**うち 2 件は親の推奨が既裁定と逆向き**だった —
  文法版の cache 束縛 (親は backoff 限定維持を推奨したが D1548 は sort 軸への局所適用を裁定済み)
  と、TRACE=0 前処理同一性検査の穴 3 件 (親は 1 件だけ直すを推奨したが D986 / D751 は
  すべて塞ぐを裁定済み)。**後者は絶対規律 1・2 に直接触れる false-green を残す向き**であり、
  相談を挟まなければそのまま出していた。
- **相談が引いた D 番号 16 件はすべて現物で検算した。** 実在・表題・本文とも一致し、捏造は 0 件。
- **収集漏れを 1 件実測した。** D1327 の再訪条件「受入 wall が再び実害として観測され、かつ
  frontier の構成が変わったとき」が**両方成立**していたのに索引案へ載らなかった。
  受入 wall は 388.3 秒 = 6.47 分で 5 分上限を 29% 超え、内訳も「97 秒以上の unit が 10〜11 本」
  から「2 file が 58% を占め最長 3 件が一方へ集中」へ変わっている。
- **自己改善 gate が発火し、収集手順 5 を直した。** 手順 5 は `docs/phase3.md` 見送り台帳の
  再訪条件だけを照合対象に挙げており、`docs/decisions.md` に書かれた再訪条件を見る指示が
  無かった。決定の再訪条件は台帳側にしか無いため、この経路を書かないと発火を取りこぼす。
  byte 予算が満杯 (上限 5,623 に対し 5,612) だったので D730 / D782 の手順を適用し、
  手順 4 が直前で `docs/phase3.md` を名指ししていることを根拠に手順 5 の file 参照を落として
  枠を作った (5,612 -> 5,621)。上限は引き上げていない。鏡像の
  `.agents/skills/rulings/SKILL.md` は本 file を全文読む dispatcher なので複製しなかった。
- **世代別台帳の裁定は本 wave では worklog へ書かない。** 対象 item を稼働中の別 wave の
  未 land fragment が同じ base digest で更新しており、両方が更新すると fold が base 不一致で
  止まる。裁定は decisions 側にだけ残し、item の更新は所有 wave に委ねた。
- **未 push commit は収集中に減った。** 収集開始時点で 187 commit 先行だったが、作業中に
  push が行われ、現在は 5 commit である。残る 5 件は並行 wave の着地でこの間に増えた分。
- **稼働 wave の fragment が「裁定待ち」として運んでいる項が 12 件、台帳では既に決着していた**
  (D1563 / D1564 / D1565 / D1566 / D1567 / D1570 / D1571 / D1572 / D1526 / D1539 / D1432 ほか)。
  fragment 側の記録が台帳より古いだけで、各 wave は着地時に台帳へ合わせれば進める。
- 検査は `python3 tools/check_docs.py` rc=0、`python3 tools/check_ai_provenance.py` rc=0
  (新規違反なし)。実装面の差分は 0 なので Codex author は要さない。

## 次の一手差分

### 更新

- [T-2280] **P1・裁定済み ({{D:axis3-core-rewritten-on-remaining-differentiators}}、2026-09-03
  /rulings 全件 第 6 回、推奨どおり) → 書き直し待ち**: 軸 3 の核は、対象がトランザクションの
  並行性制御であること・action space の拡張・正しさゲートを毎反復回すことの 3 点で書き直す。
  説明の忠実性・proof chain・試行 provenance は核でなく補助に置く。`docs/paper-story/` は
  凍結物なので、書き直しは所定手続きに従う。根拠は
  `docs/related-work/claim-survey/2026-09-03-sysinsight-adjudication.md` §4.2。
  base: fd03aea1433e6598220e1360358b781a2955fdac82cb9b09925e3c7b37e00eb2
- [T-2285] **P1・裁定済み ({{D:b10-historical-binding-per-series}}、2026-09-03 /rulings 全件
  第 6 回、推奨どおり) → 次系列で適用**: 歴史的な束縛を持つ campaign の再利用は、系列ごとに
  有限な内容 digest 集合へ exact に閉じる。一般規則は作らない。driver を編集するたびに
  同じ形の限定受理を新しく書く。
  base: 0abc9a1f6af99aae0e4fb93cdf8748840b1a1718a16bda4c6c99a0daa10117b4
- [T-2237] **P2・裁定済み (D1548、2026-09-03) → 実装待ち**: 文法の版を identity・WAL・
  build cache の三脚へ束縛する規則は、**sort 軸へ局所適用する** (任意軸への一般化はしない)。
  束縛は D1411 と同じ campaign 由来の明示引数で渡す。**本項が「ユーザー裁定待ち」のまま
  運ばれていたのは記録の遅れである** — 第 6 回の別系統相談が指摘し、親が台帳で裏を取った。
  起草時の推奨 (backoff 限定のまま維持) は D1548 が名指しで却下している。
  base: b04af75f85b41874bfa15e76420cc963e42e0f4fe2a94c0b83884fa318a93831

### 新規

- {{T:acceptance-wall-worker-map-revisit}} **P2・裁定済み
  ({{D:acceptance-wall-split-dominant-files}}、2026-09-03 /rulings 全件 第 6 回、推奨どおり)
  → 実装待ち**: 受入所要の内訳を出す計装 (nodeid から worker への対応表) は作らず、
  仕事量の 58% を占める支配的な 2 file の分割を直接進める。**D1327 の再訪条件は両方
  成立していた** — 受入 wall 388.3 秒 = 6.47 分で 5 分上限を 29% 超過 (実害) と、frontier が
  「97 秒以上の unit が 10〜11 本」から「2 file が 58%」への構成変化。本項が第 6 回まで
  索引に現れなかったのは、収集手順が decisions の再訪条件を見ていなかったためである。
  一次資料は worklog の A-1 pilot 分割エントリ。
- {{T:write-intent-pin-materials}} **P2・裁定済み
  ({{D:write-intent-pin-needs-materials-first}}、2026-09-03 /rulings 全件 第 6 回、推奨どおり)
  → 材料 3 点の収集待ち**: write-intent 被覆違反の検査を pinned producer が出せるようにする
  gitlink の pin 前進は、候補 commit・D297 の同一性検査結果・承認済み定数への波及範囲の
  3 点を揃えてから改めて提示する。揃えば前進してよい。設計上の決着は D1360 で付いており、
  残るのは実装である。一次資料は `patches/README.md` の write-intent shadow の節。
- {{T:axis1-write-guard-and-freeze}} **P2・裁定済み
  ({{D:axis1-write-guard-and-old-epoch-freeze-declined}}、2026-09-03 /rulings 全件 第 6 回、
  推奨どおり) → 実施しない**: 軸 1 の改訂契約 §8 の未決 2 件 (書込み先の防護と、旧 epoch
  凍結物を登録 preflight の凍結集合へ加える案) はいずれも見送る。後者は追加分
  2,130 file / 99,925,266 bytes で既存 18 秒の検査が数百秒規模になり D335 に触れる。
  番号を付けるのは、契約文書にしか無い未決が次の棚卸しで索引から落ちるのを防ぐためである。
  再訪条件 = いずれも同型の実害 1 件。一次資料は
  `docs/related-work/claim-survey/2026-09-02-axis1-search-amendment.md` §8。

### 見送り

#### 正しさ・防壁系

- [T-2281] 承認済み CMake identity の権威の新設 — 理由: 裁定 2026-09-03 第 6 回
  ({{D:no-approved-cmake-registry}}、推奨どおり): 登録簿・更新手順・機体差の扱いは新設せず、
  判定器が解決した実体の identity を green record へ束縛する現行形 (記録であって拒否ではない、
  D1586) を維持する。2026-08-12 の粗い provenance 方針に従う。
  再訪条件 = 未承認の CMake による測定が実害を出した 1 件。
  base: ad462ebcc1763d3bd31259f87a128d98ad8dd0f40d6cd49bd7f19cadf577fc9a
- [T-2274] repo 外束縛の全数走査 gate の新設 — 理由: 裁定 2026-09-03 第 6 回 (推奨どおり):
  D1583 が既に新設せず局所修復に留めると決めており、本項はその再確認である。構造が
  `O(file 数)` で D335 に触れる。全数性は人手の走査に依存し続ける。
  再訪条件 = 一括読み出しへの設計変更が別の理由で入ったとき。
  base: b8b5dadb9e4de53a78c82b1bce23230b808fc8a364a2cacc2a05102959637fb4
- [T-2270] 承認 commit の predecessor 無制約の穴 — 理由: 裁定 2026-09-03 第 6 回 (推奨どおり):
  D1578 のとおり正本の部分適合に留め、`A^ == Q` の代替述語は発明しない。Q は permanent family
  の構成要素で未実装であり、世代導入 commit を代替に据えると正本どおりの完全列を逆に拒否する。
  再訪条件 = Q を含む permanent family の実装。
  base: ebec98d6a36181ed01f9b5180f85f95b2e1c51bf035338a50ca5c8f0ecadbbf1

#### 研究・計測系

- [T-2286] 集約が全ジョブの終端を機械的に確かめる経路の新設 — 理由: 裁定 2026-09-03 第 6 回
  ({{D:job-termination-stays-disclosure}}、推奨どおり): D1590 の「完全性は開示であって
  受理規則にしない」境界を維持する。block record 側の検査は現に効いている。
  再訪条件 = 未終端ジョブの部分結果が集約へ入った実害 1 件。
  base: 06f0ef9f8eaf2fc7d6889887ed958110ea5cd7c19484aeea994c2365b7d564ef
- [T-2196] archive の独立期待権威の他 consumer への展開 — 理由: 裁定 2026-09-03 第 6 回
  (推奨どおり): D1469 が既に対象 file の所有解消まで保留と決めており、本項はその再確認である。
  実害の観測がない。再訪条件 = D1469 と同じく対象 file の所有解消、または実害 1 件。
  base: 9f4e1eb6f38fab42ec53cc37e9da222eee47241b4914197df875e50c2d569ada
- [T-2282] calibration の依存道具の内容 hash を receipt へ束縛する — 理由: 裁定 2026-09-03
  第 6 回 (推奨どおり): D320 の粗い provenance 方針と、同じ面で cmake の realpath 束縛を
  見送った先例に従う。絶対 path 固定と path / version の記録までで止める。
  再訪条件 = 対外公開で当該 proof chain の提示が必要になったとき。
  base: ae9b46ff1bdd6c2bef24abbc1546f0b3fe0f59773d142a6d583a4e0870f66b66
