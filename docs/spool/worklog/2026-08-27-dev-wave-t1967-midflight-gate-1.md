---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-27
wave: dev-wave-t1967-midflight-gate
seq: 1
title: [T-1967] 段 5 直前の main 乖離再測に --mode midflight を足す (コード + docs、branch worktree-dev-wave-t1967-midflight-gate)
---

## 本文

- **D1153 は依頼文の記述と違い既に land 済みだった。** 依頼は「未 land、branch
  worktree-rulings-all-20260827 の節」と書いていたが、着手時点で `docs/decisions.md` の D1153 と
  `docs/worklog.md` の [T-1967] 欄が local main 上に実在した。裁定待ちではないのでそのまま実装した。
- **本 wave 自身が D1153 の対象現象を踏んだ。** 起動検査をしている約 15 分の間に local main が
  40 commit 進み、段 6 に入る頃には 40 commit 遅れていた。
- **受理集合の設計は実測が決めた。** 稼働中の wave worktree 6 本へ既存 `--mode resume` を当てて
  測ったところ、赤になるのは包含と clean tree の 2 つだけで、branch・direct ref・進行中操作なし・
  submodule marker はすべて緑だった。落とす検査の集合はこの実測に一致する。自 commit 0 のまま
  段 5 相当まで進む wave も実在した ({{D:midflight-guarantee-is-remeasurement-not-freshness}})。
- **段 3 の敵対相談で親 provisional 1 件が覆った。** 親は graft 検査を midflight から外していたが、
  「graft を許すと測定結果が raw graph 上の値でなくなる」という指摘を採って検査に戻した。
- **段 6 のレビューが親の docs 圧縮を blocker として差し戻した。** 親は byte 捻出のため
  `workers.md` preamble の「入口が指定する leaf 節を worker 起動前に読む。」を「入口の読み込み
  契約と重複」として削ったが、独立レビューは義務の削除と判定した。単独段 dispatch では worker が
  入口本文を読まないため代替がない。復元し、予算は上限引き上げで閉じた
  ({{D:dev-wave-l1-5-budget-minimum-raise}})。**上限引き上げに至ったので D782 に従い報告する。**
- **段 6 レビューが変異 1 件の無効性を先に見抜いた。** 親が段 4 で登録した MU1「測定検査の呼出しを
  外す」は、逐語適用すると未定義変数で多数のテストが赤になり、dispatch wiring の検出力を証明しない。
  `= [], None` への置換に固定してから走らせた。
- **変異 matrix は全件 KILLED。** baseline PASSED (rc=0、失敗 0 件)、MU1〜MU6 の 6 件すべてが
  期待 node 完全一致で KILLED、anchor は各 1 箇所。probe 走 (全件 SURVIVED 期待) で観測 node を
  集めてから本走した。commit `39c1b1361` に対して実施。
- **変異 probe 走で `--out` を `--scratch-root` と別 device に置き、evidence 退避の rename が
  `Invalid cross-device link` で落ちた。** 結果 JSON 自体は完全に取れていたので判定には影響しない。
  本走では `--out` を scratch と同じ device に置いた。`DW-O19` に既記載の罠であり新規ではない。
- 子の工数: plan 1 本 / 敵対相談 2 本 / 実装 1 本 / 敵対レビュー 2 本 (最初の 2 本は F225 再発で
  rc=2 即死、同 prompt を新 path で再投入) / fix 1 本。すべて `gpt-5.6-sol`、`reasoning=xhigh`。
- **残余の裁定パッケージが 1 件ある。** 公開 CLI と Python API に midflight がある以上、wave 起動時に
  `--mode midflight` を明示すれば包含と clean tree を検査しない緑が得られる。D822 が確定した
  とおり checker は呼ばれた時点を観測できないため、診断と docs 以外では塞げない。

## 次の一手差分

### 完了

- [T-1967] `--mode midflight` を実装し、段 5 の発火点を `DW-S05-A` に、再走禁止の限定を
  `DW-O20` に書いた。変異 6 件全 KILLED、受入全走緑。
  remaining: none
  base: 31dede70fe8c19310b725b1bb15de8655ac31f9677516496826869b310e1c88b

### 新規

- {{T:midflight-startup-bypass-residual}} **P2・新規・ユーザー裁定待ち**: 起動時に
  `--mode midflight` を明示すると、包含と clean tree を検査しない緑が取れる。D822 が確定した
  とおり checker は呼ばれた時点を観測できず、診断と docs 以外では塞げない。択は (a) 段 5 launcher が
  生成する phase 束縛 attestation を必須にする、(b)「CLI の誤用は機械では防がず、入口契約と診断で
  禁じる」と保証範囲を明記して閉じる (D822 と同じ形)、(c) midflight を公開せず段 5 launcher の
  内部関数としてだけ持つ。親の推奨は (b) — (a) と (c) はどちらも最終的に「呼び手が正直である」
  ことに依存し (launcher 自体を直接呼べる)、防壁を増やした見かけの割に迂回可能性が残る。
