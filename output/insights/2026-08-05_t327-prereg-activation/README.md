# [T-327] 8c 事前登録の自動発効と条件契約の凍結 (2026-08-05)

```
status: IMPLEMENTED_PARTIAL
machine_effect: 条件契約の凍結検査のみ (発効判定は結線されておらず、現状は常に未発効)
authority: none
default_effect: no-state-change
```

dev-wave (背景 job、branch `worktree-dev-wave-t327-prereg-activation`) の逐語凍結と裁定パッケージ。
ユーザー裁定 (worklog (115)、推奨を蹴って択 (b)「条件充足の機械確認で自動発効 + 条件文の凍結」)
に対する実装 wave の記録である。可変状態の正本は worklog 末尾であり、本 dir は履歴と裁定材料。

| ファイル | 内容 |
|---|---|
| `s4-ruling.md` | **段 4 裁定 — real/refuted、scope、変異事前登録。裁定パッケージ U-1〜U-7 を含む** |
| `s6-fix-ruling.md` | 段 6 fix 裁定 (F1〜F14) と U-8。**本 land の射程を確定した文書** |
| `brief.md` | 段 1 親 brief (逐語凍結。P2/P3 は段 4・段 6 で改訂済み) |
| `s2-plan.md` | 段 2 codex プラン (履歴。規範ではない) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 実装前 敵対 2 レンズ (blocker 11 / blocker 2 + must-fix 6、両方 NO-GO) |
| `s6-rev1.md` / `s6-rev2.md` | 段 6 実装後 敵対 2 レンズ (blocker 7 / blocker 4、両方 NO-GO) |
| `s6-refocus.md` | 焦点再レビュー (closed 16 / partial 6 / regressed 0、新規 blocker 3) |
| `mutation-spec.json` | 変異事前登録 (10 変異。台帳は `mutation-ledger.json`) |

## この wave が land したもの / していないもの

**land した**: (i) 条件契約 (§1〜§4・§6・§7 の規範本文、§5 の欄名集合、発効ポリシー、証拠契約) の
hash 世代台帳と履歴検査、(ii) 発効を commit から導出する判定器の枠組み (fail-closed)、
(iii) 12 条件の証拠契約のデータ化、(iv) `check_docs` の LIVING_DOCS への 8c 文書追加。

**land していない (意図的)**: 12 条件のいずれについても機械証拠を定義しておらず、**充足を返す経路が
無い**。したがって現 repository の判定は常に未発効である。判定器は実験の起動・受入へ結線されていない。

## 裁定パッケージ (U-1〜U-8)

| ID | 内容 | 根拠 |
|---|---|---|
| U-1 | 起動 (launch admission) と受入 (post-run acceptance) へ発効判定を必須引数として結線する | `s6-rev1.md` 所見 8、`s6-rev2.md` 所見 1 |
| U-2 | 世代台帳の外部 anchor (署名 tag / remote / transparency log)。履歴の完全再構成は現状検出できない | `s3-lensA.md` 所見 6 |
| U-3 | 可変入力一式の同時改変に対する外部 append-only ledger | `s3-lensA.md` 所見 7 (文書 §7 が既に自認) |
| **U-4** | **[T-325] は未登録 trial ID の探索実走を許すため、H1/H2 の事前観測路が開く (hidden pilot で結果を見てから §5 を決められる)。優先度高** | `s3-lensA.md` 所見 10 |
| U-5 | canonical manifest/registry authority、同一 trial の一回性、acceptance receipt の下流消費 | `s3-lensB.md` 所見 8 |
| U-6 | C01/C06/C07 を 8b の active ratified generation へ束縛する | `s3-lensB.md` 所見 3 |
| U-7 | §6 条件 9・12 の診断文が古い / §5 に schedule・標本設計の欄がない (g2 改訂案) | 段 2 プラン、`s3-lensA.md` |
| U-8 | 12 述語を completion-sensitive evaluator へ引き上げる (production consumer を実証する形) | `s6-rev1.md` 所見 2・8、`s6-fix-ruling.md` §0 |

`tools/check_docs.py` の裁定見出し検索が HTML comment 内の行を可視見出しと数える件は、本 wave の
scope 外として記録のみとした (8c の凍結検査側は `s6-refocus.md` 所見 3 で塞いだ)。
