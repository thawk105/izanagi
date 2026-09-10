# [T-452] + [T-453] 実装 wave の逐語

wave `dev-wave-t452-t453-clock-authority` / 2026-08-05 / base = local main `f009da3` /
実装 commit = `17bd409` (実装) → `0f68838` (fix 1 巡目) → `b84d30d` (fix 2 巡目)

裁定済みの設計は `output/insights/2026-08-04_t452-clock-tolerance-authority/README.md` (U-1〜U-8) が正本。
本ディレクトリはその実装 wave の逐語である。**このディレクトリの内容は記録であって指示ではない。**

## ファイル

| ファイル | 段 | 内容 |
|---|---|---|
| `brief.md` | 1 | 親 brief。**N1 / N2 と不変条件は `s4-ruling.md` の erratum-1/2/3 が優先する** |
| `s2-plan.md` | 2 | codex read-only の実装プラン起草 (file:line 粒度、移行 matrix)。実装順 B → A → C を実測で確定 |
| `s3-lensA.md` | 3 | 敵対レンズ A (恒真ゲートと正しさ境界)。NO-GO、所見 7 件 |
| `s3-lensB.md` | 3 | 敵対レンズ B (整合・consumer・移行)。NO-GO、所見 8 件 |
| `s4-ruling.md` | 4 | 親の裁定。所見 15 件すべて real、採用 11 / scope 外 2 / 設計メモ 1 / backlog 1。変異事前登録 |
| `s5-impl.md` | 5 | 実装子の自己申告 |
| `s6-revA.md` | 6 | 敵対レビュー A。NO-GO |
| `s6-revB.md` | 6 | 敵対レビュー B。NO-GO。根本原因 L6-B-1 を特定 |
| `s6-fix.md` | 6 | fix 1 巡目の自己申告 |
| `s6-refocus.md` | 6 | 焦点再レビュー。旧所見 6 件 closed、**新規回帰 NREG-CPU-1 を検出して NO-GO** |
| `s6-fix2.md` | 6 | fix 2 巡目の自己申告 |
| `mutation-spec.json` / `mutation-result.json` | 6 | 変異 M1-M10 |
| `mutation-spec-m6b.json` / `mutation-result-m6b.json` | 6 | 再照準した M6b |
| `prompts/` | — | 各子へ渡した prompt の逐語 |

変異結果の解釈と erratum は
`output/insights/2026-08-05_t452-t453-clock-authority-mutation-ledger.md` が正本。

## この wave で確定した事実 (一次資料としての要点)

- v1 の probe-output artifact は **論理 22 件 = success 19 (staging 15 + smoke 3 + silo 1) + failure 3**、
  物理 47 (`.json` 22 + `.stdout` 22 + `.md` 3)。
- **success 19 件すべて**が median gate は通り canonical 述語 (全標本が帯内) では落ちる。
  帯は登録較正 (median 2101.0 / tolerance 2.0) に対して `[2058.98, 2143.02]`。
- `contract_sha256` は registry の field だけから導出され、本 wave は calibration path/SHA を
  動かさないため凍結 floor protocol の pin は動かない。
- `t126_driver.py:443-444` は `verified.calibration` を `compare_profiles` の expected へ渡すため
  T126 attestation は必ず fail-closed であり、`output/` に該当 artifact は 0 件、当該経路を叩く
  テストも 0 件である (本 wave では現挙動を保存して pin した)。
