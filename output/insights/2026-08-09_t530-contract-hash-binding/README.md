# [T-530] contract hash を campaign identity と WAL COMMIT へ束縛する — wave 一次資料

2026-08-09、branch `worktree-dev-wave-t530-contract-hash-binding`。
台帳の正本は worklog エントリと decisions / failures であり、本 directory は逐語と台帳を持つ。

## 成果と限界

実行契約の fingerprint を campaign identity の正準 pre-image
(`search_config.environment_contract_sha256`) と WAL COMMIT payload (`contract_sha256`) の
双方へ束縛し、campaign.lock 由来の期待値で全 COMMIT を照合する検査を、
tail repair の書込みより前に置いた。

**「proof chain が全経路で完結した」とは名乗らない。** historical 分類の campaign と、
照合を通らない raw reader 経由では、無束縛 COMMIT が依然 certified 入力へ到達しうる。
その閉包は 6 問の裁定パッケージとして返した (worklog の「次の一手」を参照)。

## 実測

| 対象 | 結果 |
|---|---|
| 受入全走 (統合後、merge 3 回目の後) | **7459 passed / 20 skipped、rc=0**、1203 秒 |
| 変異 matrix run 1 | 7 KILLED / 1 MISMATCH / SURVIVED 0 (erratum。MISMATCH は親の期待 node 不足) |
| 変異 matrix run 2 | **8/8 KILLED、SURVIVED 0、MISMATCH 0** (HEAD `899e91ad` 束縛) |
| 段 1 生死実験 (実装前) | identity preimage の top-level に key 追加 = 27 赤 / search_config 配下 = 4 赤 |
| 段 5 実装直後 → fix 5 巡 | 7 → 3 → 3 → 0 → 1 → **0** 赤 (identity 関連 16 file の subset) |

## ファイル

| ファイル | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief (scope、不変条件、生死実験、provisional 裁定 P1〜P3) |
| `s2-plan.md` | 段 2 プラン起草 (codex sol / reasoning=max / read-only) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対 2 レンズ (正しさ境界 / 整合・実効性・scope) |
| `s4-adjudication.md` | 段 4 裁定 (real/refuted、scope、plan v2、変異事前登録 8 件) |
| `s5-impl.md` | 段 5 実装報告 |
| `s5-measured-reds.md` | 親が計算ノードで実測した赤 7 件の逐語と診断 |
| `s6-revA.md` / `s6-revB.md` | 段 6 敵対レビュー 2 本 |
| `s6-fix1.md` 〜 `s6-fix5b.md` | fix 5 巡の報告 (`s6-fix5b` は codex 認証回復後の再投入) |
| `s6-refocus.md` | 焦点再レビュー (NO-GO 判定と C-01〜C-03) |
| `mutation-spec.json` / `mutation-ledger.json` | 変異 run 1 (erratum) |
| `mutation-spec-v2.json` / `mutation-ledger-v2.json` | 変異 run 2 (8/8 KILLED) |

## 逸脱の記録

- fix を 5 巡し、`DW-O16` の 3 巡上限を 2 度超えた。4 巡目は焦点再レビューが新規に見つけた
  実回帰 (Pegasus compute の正当な実行が拒否される) を閉じるため、5 巡目は 4 巡目が入れた
  テスト配線バグを閉じるため。争点の再 fix ではない。
- 段 3 は 2 レンズとも `gpt-5.6-sol` で走らせた。sol/luna 混成の規約は段 3 実行後に land した。
- wave 途中で codex のサブスクリプションログインが失効し、1 度 fail-closed で停止した。
