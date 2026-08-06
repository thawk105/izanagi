# [T-454] テスト化 pass — 逐語と裁定パッケージ

2026-08-06、branch `worktree-dev-wave-t454-testification`、land 対象 tip は本 wave の記録 commit。

**この wave は `docs/dev-wave/**` を 1 byte も変更していない。回収実績は 0 bytes である。**
ユーザー指示「削除実施と新 D 発効はまとめ裁定へ返す」に従い、削除も D 発効も行っていない。

## 読む順

| # | ファイル | 内容 |
|---|---|---|
| 1 | `ruling-package-drafts.md` | **裁定パッケージの本体。** 逐語 draft と byte 会計、見送り 11 件、削除不適格 1 件 |
| 2 | `s6-fix-adjudication.md` | 段 6 fix 裁定。**段 4 裁定の訂正 3 件を含み、段 4 より優先する** |
| 3 | `s4-adjudication.md` | 段 4 裁定 (訂正前。E-1〜E-3 は上書きされている) |
| 4 | `brief.md`, `brief-addendum.md` | 段 1 brief と、走行中に親が見つけた新事実 4 件 |
| 5 | `s2-plan.md` | 段 2 プラン |
| 6 | `s3-lensA.md`, `s3-lensB.md` | 段 3 敵対レンズ (正しさ境界 / 整合・実効性) |
| 7 | `s5-impl.md`, `s6-fix1.md`, `s6-fix2.md` | 実装子の報告 3 本 |
| 8 | `s6-lensC.md`, `s6-lensD.md`, `s6-refocus.md` | 段 6 レビュー 2 本と焦点再レビュー |
| 9 | `mutation-spec-*.json`, `mutation-ledger-*.json` | 変異 6 走ぶん |

## 実測サマリ

- **実装差分**: `orchestrator/tests/test_mutation_harness.py` の 3 node (parametrize 込みで実 7 vector)・
  78 行だけ。production・docs・受理集合は不変。
- **変異 16/16 一致・MISMATCH 0。** 新側 8 KILLED / 旧 HEAD (`616ef5db` clone) 側 7 SURVIVED /
  正例 1 KILLED。
- **受入全走 6781 passed / 20 skipped / 0 failed** (request `892711.nqsv`)。
- **`docs/dev-wave/**` = 25,187 / 25,200 bytes (余白 13)。** 取り込み前後で不変。

## 変異台帳の対応

| 台帳 | anchor | 内容 |
|---|---|---|
| `mutation-ledger-new.json` | `198b246d` | MU-1 / MU-3 / MU-4 → 3 KILLED (fix 2 巡目**前**の anchor) |
| `mutation-ledger-old.json` | `616ef5db` | MU-2 / MU-6 / MU-7 → 3 SURVIVED (`DW-M08` 新旧差分) |
| `mutation-ledger-control.json` | `198b246d` | MU-5 正例 → KILLED |
| `mutation-ledger-new2.json` | `b3dc8deb` | MU-8〜MU-11 (正規化衝突 4 種) → 4 KILLED |
| `mutation-ledger-old2.json` | `616ef5db` | MU-12〜MU-15 → 4 SURVIVED |
| `mutation-ledger-final.json` | `b3dc8deb` | **MU-1F / MU-3F / MU-4F → 3 KILLED (`DW-M07` の最終 anchor 走行)** |
| `mutation-ledger-control-final.json` | `b3dc8deb` | MU-5 正例を最終 anchor で再走 → KILLED |

**`DW-M07` の最終 anchor 再検証が実際に効いた。** fix 2 巡目で parametrize case が増えたため、
MU-4 の実赤集合が初回登録 (1 node) の**真上位集合 (4 node)** になることを走行前に予測できた。
`mutation-ledger-final.json` で 4 node として登録し直し、うち 3 件は冗長 gate と明記した (`DW-M03`)。
初回台帳 `mutation-ledger-new.json` は消さずに残す — 当該 anchor では正しい記録である。

## 射程の限定 (誇大に読まないこと)

- 固定できたのは **7 vector だけ**である。未固定の弱化変異が他に無いことは示していない。
- 旧側 SURVIVED は「旧 57 node では生存し、node を追加した新 64 node では対応 node だけが殺した」
  という限定的な主張である。**一般的な検出力の証明ではない。**
- 正例 MU-5 は runner を 1 node へ絞ったため、他 59 node が常時 MISMATCH 変異でどう壊れるかは
  見ていない。「過剰拒否が全 consumer に無い」という主張には使えない。
- **「テスト化した」「予算を空けた」「T-454 を完了した」とは書けない。**
