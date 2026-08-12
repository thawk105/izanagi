# 2026-08-11 toolchain 束縛 ([T-783] + [T-747] (B))

wave `dev-wave-t783-toolchain-binding`。床値 build の compiler 解決を site 依存へ寄せ、
同じ land で registered calibration の `acquisition_receipt` を derived authority とする
toolchain 束縛検査を build 前に置いた。環境・世代をまたぐ床値の混用は build 前に止まる。

## 構成

| path | 内容 |
|---|---|
| `package.md` | 裁定パッケージ (返す 4 件、W-2 が投入できない理由、親 brief の訂正) |
| `mutation-spec.json` / `mutation-ledger.json` | 変異 14 件の事前登録と第 1 走 (12 KILLED / 1 SURVIVED / 1 MISMATCH) |
| `mutation-spec-erratum.json` / `mutation-ledger-erratum.json` | M03 の mask を裏取りする両層同時変異 |
| `mutation-spec-m03.json` / `mutation-ledger-m03.json` | 単一理由テスト追加後の M03 再照準走 (KILLED) |
| `verbatim/` | 段 1〜6 の逐語 (brief / plan / 敵対 2 本 / 裁定 / 実装 2 本 / レビュー 2 本 / fix 5 本) |

## 変異の要点

登録 14 件のうち 12 件が第 1 走で KILLED。残る 2 件の扱いは次のとおり。

- **M07 = MISMATCH**。gate 呼び出しそのものの消去で、予測 1 node に対し実測 63 node。
  予測が狭すぎただけで、殺されたことは決定的である。
- **M03 = SURVIVED → 冗長ゲートによる mask と判明 → 単一理由テスト追加後に KILLED**。
  注入は実在していた (anchor 1 件一致、injection diff hash 記録あり) ので等価変異ではない。
  両層同時変異 (`mutation-ledger-erratum.json`) で検出力の実在を確認し、
  内部整合ゲートを通したまま authority 照合だけを破る単一理由テストを足したうえで
  再照準走 (`mutation-ledger-m03.json`) が KILLED を返した。
  初回の SURVIVED は消していない (`DW-M02`)。
