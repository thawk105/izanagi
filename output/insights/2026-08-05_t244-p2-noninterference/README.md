# [T-244] D121 P2 — payload 射影面の非干渉検査 (実装差し戻し、2026-08-05)

```text
authority: none
default_effect: no-state-change
```

本ディレクトリは dev-wave `[T-244] D121 P2 非干渉検査` の逐語成果物である。可変状態の正本は
worklog 末尾と現行 phase doc、採用済み判断の正本は本 wave の decisions エントリであり、
ここには凍結した逐語だけを置く。**本文書は可変状態の正本ではない。**

## この wave の結論 (先に読むこと)

**実装しなかった。** 段 3 の敵対 2 レンズが独立に NO-GO を返し、親が 19 件の所見を裁定した結果、
プランを設計メモとして凍結した。

- **実装差分ゼロ。** production 挙動・受理集合・certified 選択・材料レポート・proof chain・
  凍結 bytes はいずれも不変。変異 matrix と受入全走は対象外。
- **D121 P2 は依然 FAIL。** 無条件義務 8 件のうち充足は P10 の 1 件のみで、承認 generation 上限 1 も不変。
- **中心前提が反証された。** 現行 critic payload の variant は候補述語を preimage に含む 12 hex で、
  候補が 32 点しかないため wire へ可逆である。payload を変えずに書ける字面検査は
  この実漏洩に対して一度も発火しない。
- **ユーザー裁定待ちが 4 件ある。** 正本は `s4-adjudication.md` の裁定パッケージ節。

## ファイル

| file | 内容 |
|---|---|
| `README.md` | 本文書 |
| `brief.md` | 段 1 brief (親の provisional 裁定 (P1)〜(P4)。うち 3 件は反証された) |
| `s2-plan.md` | 段 2 プラン起草 (codex read-only, reasoning=max) |
| `s3-lensA.md` | 段 3 敵対相談 レンズ A = 情報フローと恒真性 (NO-GO、BLOCKER 4) |
| `s3-lensB.md` | 段 3 敵対相談 レンズ B = 実装整合・全層性・scope 逸脱 (NO-GO、BLOCKER 3) |
| `s4-adjudication.md` | 段 4 裁定 (実装しない) + 所見台帳 19 件 + 裁定パッケージ |

## erratum — 逐語 3 本への可逆最小正規化 (2026-08-05)

子出力 3 本が行末空白 (Markdown の強制改行、各 3 行) を含み `git diff --check` に抵触したため、
**可視文字を変えない最小正規化**として行末の空白のみを除去して凍結した。各ファイル 6 bytes の減少で、
文言・記号・改行位置はいずれも不変である。

| file | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 正規化後 bytes |
|---|---|---:|---|---:|
| `s2-plan.md` | `480a91e2e455a23583f54020f10948a9937335975025e7276bd5f54ce98ff9e9` | 28136 | `3dc4c4400f1bb501ea26d2661a2eb0d1da7f6fa5e9a7a27023cae173b1aeb9c2` | 28130 |
| `s3-lensA.md` | `7a9ba46b185016399d5186f6b8989a084032b847d8236a96c166d522fd2e3e10` | 14934 | `e85e628af6efce19559cf1769c13aec9fc9a57ee47682173b03a4bda65dd7346` | 14928 |
| `s3-lensB.md` | `f34f099cb5bfce38d8655bd9bd34879aff4c0dbc4064d4d77dfc77b3b168d45a` | 15056 | `b8a2205e73fa99820c6cd87fd041fd816b80df0bc764621c7b0bf758164a9b46` | 15050 |

**復元法:** 各ファイルで、原文が行末に 2 空白を持っていたのは総括節の 3 行である。
`s2-plan.md` は 198〜200 行目、`s3-lensA.md` は 158〜160 行目、`s3-lensB.md` は 108〜110 行目 (いずれも
正規化前の行番号) の行末へ 2 空白を戻すと原文 sha256 に一致する。

**凍結逐語の読み方:** `brief.md` / `s2-plan.md` / `s3-*.md` は各段時点の記録であり書き換えない。
したがって `brief.md` は反証された (P1) (P2) (P3)、正本違反の環境記述、および
「純増検出力」の見積りを含み、`s2-plan.md` は撤回された GO 判定と、流用してはならない変異 12 件を
含む。**現在の正本は `s4-adjudication.md` と本 wave の decisions エントリである。**
