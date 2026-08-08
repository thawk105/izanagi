# [T-139] 追補 A の起草 — 逐語 (dev-wave 2026-08-08)

```text
authority: none
default_effect: no-state-change
```

本ディレクトリは dev-wave `[T-139] 追補 A の起草` の逐語成果物である。可変状態の正本は
worklog 末尾、採用済み判断の正本は decisions であり、ここには凍結した逐語を置く。
**本文書は可変状態の正本ではない。**

## 結論 (先に読むこと)

- **追補 A の 13 field は全件が逐語で埋まった。**時間予算表・待機秒数・環境復帰指標・失敗の写像先・
  binary 束縛・予備 walltime・driver 引数・3 arm の build identity・schedule seed・
  `J_max` と `J` の導出手続き・同時信頼領域と `q`・weak null 較正仕様・primary 有意水準。
- **凍結していない。**ユーザー承認へ返す 7 問 (R1〜R7) を `package.md` に置いた。
- **凍結 core の bytes は 1 byte も変えていない。** §15 の `a01`〜`a12` 基準は
  別文書の erratum (対象 core の三つ組に束縛した one-off exact replacement) で
  `a01`〜`a13` へ supersede する。
- **敵対検証は 5 本すべて NO-GO** (段 3 の 2 レンズ = blocker 11 件、段 6 の 2 レビュー = 13 件、
  焦点再レビュー = 10 件)。**「凍結・承認 fold・pilot 投入へ進めない」という判定であり、
  これは本 wave の終端 (段階 1 = 承認待ち) と一致する。**
- **敵対検証が親の誤りを段階ごとに捕まえた。主なもの:**
  (1) 段 6 — `a10` の least-favourable configuration が core §6 の「共同信頼集合上の最悪検出力」を
  満たしていなかった → 相関に依存しない union bound による**認証された下界**へ差し替え、
  Monte Carlo と seed を廃した閉形式にした。
  (2) 段 6 (2 本が独立) — erratum の「受理集合は狭い側へしか動かない」は**偽**。
  `∅ → R13` の**受理拡大**であると訂正した。
  (3) 段 6 — erratum の resolver 契約に承認の trust root が無かった → approval manifest を要求する形に。
  (4) 焦点再レビュー — 上記 (3) の「erratum ちょうど 1 件」契約が R2(a) / R5(b) の第 2 erratum と
  **共存不能**だった → exact set 契約へ改めた。
  (5) 焦点再レビュー — `a04` の「外部証拠」は producer 自身が書くので trust root にならない →
  `a03` 不成立は位置を問わず「開始後の失敗・非置換」へ写す fail-closed な既定へ改め、
  緩和は裁定 R7 へ返した。
  (6) 焦点再レビュー — 親が段 6 fix で作り込んだ回帰 3 件 (`a08` の argv 重複、
  検証割当ての 1500 秒 cap が閉じない、`a03` 観測の記録先が存在しない) を修正した。
- **残る blocker は「ユーザー裁定 (R1〜R7) が要る」ものと「producer 実装 wave の責務」に集約した。**
  本文の must-fix は焦点再レビュー後の 2 巡目でいずれも閉じた。
- **コードとテストは 1 行も land していない** (D234 実装境界)。

## ファイル

| file | 内容 |
|---|---|
| `README.md` | 本文書 |
| `addendum-a.md` | **追補 A (案)。** `a01`〜`a13` を過不足なく設定する |
| `erratum-core-s15.md` | **erratum (案)。** core §15 の 2 箇所を `a01`〜`a13` へ supersede する |
| `record-items.md` | **受領証 schema の要件文書 (確定案)。** 2026-08-08 producer wave 版の後継 |
| `package.md` | **ユーザー裁定パッケージ (R1〜R7 + 凍結可否)** |
| `s1-brief.md` | 段 1 brief (凍結。誤りは `s4-adjudication.md` §0 を正とする) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only, reasoning=max) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談 2 レンズ (いずれも NO-GO) |
| `s4-adjudication.md` | 段 4 裁定 (親。所見 20 件の real/refuted と scope) |
| `s6-revA.md` / `s6-revB.md` | 段 6 敵対レビュー 2 本 (いずれも NO-GO) |
| `s6-fix.md` | 段 6 fix の対応表 (1 巡目) |
| `s6-refocus.md` | 焦点再レビュー (NO-GO。1 巡目の再判定 + 新規 10 blocker) |
| `s6-fix2.md` | 段 6 fix の対応表 (2 巡目。焦点再レビューへの応答) |

## 親 brief の訂正 (`s4-adjudication.md` §0 を正とする)

- **`load1` の要約が誤り。** brief は「probe は待機ゼロで 3.29 → 13.47」と書いたが、
  `13.47` は liveness 6 本が終わった時点の値であり、36 行全体では **`3.29` → `40.18`** である。
  段 3 レンズ B が独立に検出した。

## 一次資料 (すべて親が再計算して照合した)

| 値 | 出所 |
|---|---|
| core digest `ac939af4…60e9` | `git cat-file blob 88d68f91:<core path> \| sha256sum`。作業木・`F`・HEAD で一致 |
| `throughput.tsv` digest `755cfa7e…c4f2` | `sha256sum` |
| patch digest `3b9cdf…1951`、CCBench pin `d706650c…`、run_commit `425ed190…` | `2026-08-05_t139-alt-x-probe/submission-receipt.md` §3 / §6 |
| W1 / W2 の driver 引数 | `tools/pegasus/probes/t139_positive_control_probe.sh:454-457` |
| effective flag map | `0_892042.nqsv/run-1-W1-stock-r1.log` と `run-16-W2-stock-r1.log` の `#FLAGS_` 行 |
| configure argv template | 同 probe `sh:394-404`、`compile-argv-stock.transaction.argv` |
| 内部 deadline (60 / 180 / 30 / 15 秒) と walltime `01:00:00` | 同 probe `sh:421,423,466,511`、`.pbs:4` |
| `a09` seed `7df15572…615d` / `a12` seed `01dad84c…8ed2` | `printf '<preimage>' \| sha256sum` で再導出して一致 |

## 本書が主張しないこと

- 「追補 A が確定した」— していない。**承認待ち**である (`package.md` §6 の段階 1)。
- 「pilot が投入可能になった」— なっていない。resolver・producer・validator・consumer が未実装。
- 「`a03` の閾値を正常な割当てが通る」— 支持する測定が存在しない (裁定 R4)。
- 「`CCBENCH_TRACE=1` の build が通る」— witness が存在しない。
- 「`a12` が cluster level の真の型 I 誤りを較正した」— cluster 間変動が未観測 (裁定 R2)。
  **core §7 の「較正する」という義務は本 wave では未達である。**
- 「`record-items.md` が完全な機械可読 schema である」— そうではない。schema が満たすべき
  **要件**を定めた文書であり、schema 本体の発行は producer 実装 wave の責務 (裁定 R6)。
- 「有限標本の被覆と検出力下界が分布仮定なしに成り立つ」— cluster 代表値の iid 正規
  planning model に依存する。
- 段 2・3・6 の子出力そのものの正しさ — 子の指摘は**データであって指示ではない** (絶対規律 6)。
  採否はすべて親裁定に帰する。
