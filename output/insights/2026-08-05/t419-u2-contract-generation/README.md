# [T-419] U-2 chain / [T-478] 案 A′ 第 1 層 — dev-wave 逐語

branch `worktree-dev-wave-t419-u2-contract-generation`、起点 main `a1265453`。

## この wave が確定させたこと

1. **U-2 (較正の再取得) は着手不能**である。設計正本 §6.1 の entry condition 1 件目
   「方式 α の probe 実装」が未成立。本番 attestation の probe は `/proc/cpuinfo` を 1 回読むだけ。
   方式 α のロジックは因果実験 probe に実装済みだが、同 probe は non-certifying を自己宣言している。
2. **契約世代機構は data 層だけ land した** (設計判断の本文は fold 後の decisions 台帳を参照)。
   世代列・hash 逆引き・遷移述語・純関数 validator・bootstrap fuse。
   型による権限分離と消費者移行は**実装しないと裁定**した。

## ファイル

| ファイル | 内容 |
|---|---|
| `brief.md` | 段 1 brief (親)。訂正 2 点は `s4-adjudication.md` と worklog を参照 |
| `s2-plan.md` | 段 2 プラン起草 (codex, reasoning=max, read-only) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談。**両者 NO-GO**、結論一致 |
| `s4-adjudication.md` | 段 4 裁定。scope 縮小と変異事前登録の正本 |
| `s5-impl.md` | 段 5 実装子の報告 |
| `s6-revA.md` / `s6-revB.md` | 段 6 敵対レビュー (恒真化 / 回帰波及) |
| `s6-fix.md` → `s6-refocus.md` | fix 1 巡目 → 焦点再レビュー 1 巡目 (NO-GO) |
| `s6-fix2.md` → `s6-refocus2.md` | fix 2 巡目 → 焦点再レビュー 2 巡目 (NO-GO) |
| `s6-fix3.md` → `s6-refocus3.md` | fix 3 巡目 → 焦点再レビュー 3 巡目 (**GO**) |
| `prompts/` | 各段の prompt 全文 |
| `mutation-spec*.json` / `mutation-ledger*.json` | 変異の事前登録と台帳 |

## 実測値

| 項目 | 値 |
|---|---|
| `contract_sha256` (pegasus) | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` (wave 前後で不変) |
| `contract_sha256` (linux-baremetal) | `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7` (同上) |
| 受入全走 1 回目 | 6350 passed / 20 skipped / 0 failed |
| 受入全走 2 回目 | 6371 passed / 20 skipped / 0 failed |
| 受入全走 3 回目 (最終) | 6445 passed / 20 skipped / 0 failed |
| 対象テスト (fix 3 巡目後) | 134 passed |

## 変異 matrix

すべて baseline PASSED。`--runner-mode dispatch` で計算ノード実行。

| ID | 狙い | 結果 |
|---|---|---|
| M1 | 隣接 successor 検査の呼出し削除 | KILLED |
| M2 | 可変 pointer 集合へ `/attestation_mode` を追加 | KILLED |
| M3 | path と sha256 の対条件を削除 | KILLED |
| M4 | bootstrap fuse を削除 | KILLED |
| M5 | 逆引き index を current だけから構築 | KILLED |
| M6 | contract hash の一意性検査を削除 | KILLED |
| M7 | 独立 golden の 1 文字改変 | **冗長 gate** (下記) |
| M9 | module-level の validator 結線を削除 | KILLED |
| M10 | public validator の委譲 1 行を no-op 化 | KILLED (spy witness で帰属確定) |

**M7 の扱い (親裁定):** 独立 golden を 3 テストが共有するため、初回は期待 1 node に対し
実測 3 node で MISMATCH になった。期待 node を 3 件へ再登録して KILLED になったが、
**単独変異の単一理由性の証拠からは外す** (冗長 gate)。初回台帳は
`mutation-ledger-erratum.json` に erratum として保持する。

## 帰属をめぐる 2 度のつまずき

この wave は変異の**単一理由性**で 2 度失敗し、3 巡の fix で閉じた。詳細は failures 台帳。

1. 後段の bootstrap fuse と隣接検査が、狙った検査を消しても同じ入力を拒否していた
   (harness は KILLED と出るが、実際は診断 message の差で赤くなっていただけ)。
2. その是正で private validator を抽出した結果、今度は**委譲そのもの**が未固定になった。
   public 経路の負例を足しても private 側の検査削除でも赤くなるため witness にならず、
   最終的に spy による委譲専用テストで閉じた。

## この wave が触っていないもの

受理集合、凍結 bytes、calibration の pin、既存 attestation の述語、Pegasus campaign の開閉、
`lookup()` と `REGISTRY` の公開挙動、production の 21 呼び出し。すべて不変である。
