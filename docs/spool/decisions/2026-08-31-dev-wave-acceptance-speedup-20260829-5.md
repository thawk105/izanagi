---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-31
wave: dev-wave-acceptance-speedup-20260829
seq: 5
---

## {{D:land-stale-main-retries-in-place}}. land の stale/busy で wave を止めず、その場で landed まで再試行する

**決定 (ユーザー裁定):** `tools/dev_wave_land.py` が `stale-main` / `busy` を返しても
**wave を停止しない。** 既存 branch のまま、新 main 監査・固定 SHA の wave-side merge・
条件再評価をやり直し、`landed` に到達するまで再試行する。
DW-O23 の「fresh context で再開する」要求は撤回する。

**理由:**

- `stale-main` は**失敗ではなく競合の通知**である。実測した戻り値は
  `main_before == main_after` で main を 1 bit も変えておらず、`release_safe: true`、
  成果は branch 上に完全に残っていた。受入も `child-green` で通っていた。
  **止める理由が無い状態で wave が止まっていた。**
- 並行 wave が常時 land している環境では、受入と land の間に main が動くのは
  例外でなく通常である。停止を既定にすると、緑の成果が着地しないまま滞留する。
- `retryable_same_request: false` は「その request object をそのまま再送できない」意味であって
  「再試行してはならない」ではない。新しい merge を作れば新しい request になる。
- 再試行が発散しない構造がある。`--landing-wave-tip-sha` は受入済み tip からの
  **前方 main merge 列**を受け付け、topology (first-parent が exact、second parent が
  tested main の子孫で単調) と tree を検査する。したがって main が動くたびに
  前方 merge を足して land し直せばよく、**受入を取り直さずに収束させられる。**
- fresh context を要求していた理由は context 衛生であって正しさではない。
  正しさに要るのは「新 main を監査し、固定 SHA で merge し、条件を再評価する」ことであり、
  それは同一 context でも実行できる。

**却下した選択肢:**

- **停止して fresh context へ引き継ぐ (従来)** — 緑の成果を着地させずに人手を挟む。
  競合が通常である以上、恒常的な滞留を生む。
- **land を lock 内で自動再試行させる** — lock 保持時間が伸び、他 wave の land を塞ぐ。
  再試行は lock の外で、監査と条件再評価をやり直してから行う。
- **rebase / force / 他 session 所有物の変更で解消する** — DW-O23 の既存禁止に反する。
  本決定はこの禁止を一切緩めない。

**適用範囲:** 本決定が変えるのは stale/busy の扱いだけである。
`postcondition failure` は従来どおり停止する。fold が赤なら `landed` を返さない。
受入受領証の要件、監査 commit 列、ff-only、`--landing-wave-tip-sha` の topology 検査は不変である。
