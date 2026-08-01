---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-02
wave: dev-wave-parallel-docs-spool
seq: 2
---

## {{D:parallel-doc-spool}}. 台帳への書き込みを land lock 内の fold へ一本化する

**決定:** `docs/worklog.md` / `docs/decisions.md` / `docs/failures.md` は wave が直接編集せず、
`docs/spool/` の fragment に書く。T/D/F の採番、台帳への追記、worklog のローテーションは
`tools/dev_wave_land.py` が ff-only 成功後、**同じ協調 lock を保持したまま** 1 回だけ行う。

**理由:**
- D70 決定 5 が「並行セッションは番号を予約したとみなさず統合直前に再走査する」と規定しており、
  採番は統合の瞬間にしか確定しない。fold はその瞬間の機械化である。
- 直近 40 merge の件名のうち 25 件が採番衝突の解消を明示し、うち 11 件はローテーションにも言及していた。
- 20 merge の反実仮想で、実衝突は 49 file-instance / 15 merge。spool だけでは 15→12 件にしか
  減らず、残る 18 file-instance の 94.4% が archive ローテーションだった。
  **ローテーションを直列 fold に含めると 15→1 件**になる (段 6 レビューが独立に追認)。
- lock の外で fold すると直列化されないため、衝突が「fold commit を破棄して再実行」へ移るだけになる。

**却下した選択肢:**
- `docs/tmp_*` — 破棄可能と誤読される。未 fold fragment は正本である。
- wave 側 fold (land 直前) — lock 外なので直列化せず、race 敗者に再 fold と再検査を強いる。
- 独立した rulings 台帳 — 裁定待ちの実体は worklog の T 項であり、二重管理になる。
- 全 active ID の明示遷移を要求する — fragment が 221 行の carry 列挙を含むうえ、他 wave が
  新 T を先に fold した瞬間に先行 fragment の fold が必ず失敗し、**並行 wave を畳めなくなる**。
  carry を暗黙の既定とし、保存則は「出力 active == 入力 active − 完了 − 見送り + 新規」の
  postcondition で機械検査する。
- `base:` を描画後 literal bytes に束縛する — carry 行に直前エントリ番号が埋まるため、
  無関係な wave が 1 回 fold しただけで 222/222 全部が失効する。carry を再帰解決した
  substantive content の digest に束縛する。

## {{D:dev-wave-budget-raise}}. dev-wave reference と rulings の byte 予算を小幅に引き上げる

**決定:** `docs/dev-wave/core.md` 9,000→9,600、`docs/dev-wave/operations.md` 8,000→8,400、
`docs/dev-wave/**` 合計 24,000→25,200、`.claude/commands/rulings.md` 4,500→5,000。
新しい dev-wave reference 文書は増やさない。

**理由:** 引き上げ前の余裕は dev-wave 合計で 10 bytes、rulings で 6 bytes しかなく、事実上の凍結状態
だった。その結果、段 2 のプランは `DW-S07` を net −1 byte で収める縮約案を出し、
**repo 全体でその節にしか存在しない義務 2 件**を落としていた —
「再走値は amend する」と「insights の逐語・**変異台帳**の記録」。
`grep -rn` で両方ともこの節にしか存在しないことを確認した。
予算が安全義務を削らせる状態は、予算自身の契約 (「予算のために安全義務を削除・弱化してはならない」)
と手段目的が逆転している。ユーザー裁定 (2026-08-02) を得て引き上げた。

**却下した選択肢:**
- 縮約して収める — 上記のとおり義務が消える。
- 開放する — 予算の規律そのものを失う。+5% に留め、義務を削らずに 1〜2 operation を足せる余地とした。
