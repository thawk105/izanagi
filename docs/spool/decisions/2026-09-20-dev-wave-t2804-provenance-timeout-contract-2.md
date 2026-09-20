---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-20
wave: dev-wave-t2804-provenance-timeout-contract
seq: 2
---

## {{D:provenance-outer-deadline-contract}}. land の provenance 監査は外側 480 秒を固定し、絶対 monotonic 期限を checker へ渡して dispatcher の締切をそこから導く (契約 C-2804、D2148 項 8 の実装ではない)

**決定:** `tools/dev_wave_land.py` の `_run_provenance_checker` は外側 timeout `_PROVENANCE_AUDIT_TIMEOUT_S = 480` (値不変) を持ち、spawn 直前に
`IZANAGI_PROVENANCE_OUTER_DEADLINE_MONOTONIC = time.monotonic() + 480` を env へ置く (継承値は上書き)。`tools/check_ai_provenance.py` は dispatch 直前
(`_default_dispatch`) でだけこの env を読み、未設定なら現行と同一の kwargs で dispatcher を呼ぶ。設定済みで有限数以外なら ValueError → 既存の一義化で rc=16。
設定時は `deadline_at = K − 32`、`queue_wait_timeout_s = min(D612 明示値または既定 900, remaining − 32 − cleanup 90 − 60)` を dispatcher へ渡し、導出 queue 予算が
16 秒未満なら qsub せず理由行 1 本と rc=16 で返す。dispatcher を呼んだ経路の終端では観測可能値 (残余・queue 締切・`deadline_margin_s`・rc) だけを stderr に 1 行出す。
queue 待ち・RUN 区間の権威は dispatcher の receipt。dispatcher・`_dispatch_timeout_overrides`・login bounded scope 経路・land の reject reason と分類・D2170 の判定は変えない。
実装 commit `aa81e3c64445055dbf8088b47c47f22b39a63571`、fix1 `62ed683aba12dd98e17f040d701fe5390cbab4cc` (Codex author)。一次資料
`output/insights/2026-09-20/t2804-provenance-timeout-contract/README.md`。

**理由:**
- 起点 (worklog entry 1722、D2170) の「timeout の延長は裁定なしに行わない」により外側 480 秒は動かせない。動かせるのは内側だけで、内側を外側から導けば
  「queue 待ちだけで外側に SIGKILL され、投入後・pending 解除前なら job と pending hold が残る」構造を、dispatcher 自身の回収 (queue 超過なら cleanup 予算付きの qdel、
  receipt 保存、rc=16) へ置き換えられる。
- 絶対 monotonic 期限を渡すのは、land の spawn から checker の main 到達までの遅延 s を式に入れずに済ませるため (相談 A3)。同一 host の CLOCK_MONOTONIC は process 間で
  共通で、`repr(float)` → `float` は無損失。
- 定数の根拠 (DW-O13): 60 秒 = 2.87 × (前段 max 15.9 秒 + poll 5.0 秒、T-2484 の receipt 3,849 件、harness regime)、16 秒 = 3 × queue 待ち観測 min 5.1 秒 (n=85、運用閾値)、
  32 秒 = 後段の代理値 (実走 L1 で h ≈ 0.03 秒)。harness の M_pre=180 秒を写すと queue 待ち 278.7 秒の既知成功例を落とすため採らない (相談 A8 / B6)。
- 段 1 の受領証 85 件 (残存 worktree に限る) で queue 待ち中央値 5.2 秒・最大 716.5 秒、RUN 中央値 30.7 秒・最大 475.9 秒、合計 480 秒超 2 件。
- 本契約は D2148 項 8 (外側が前段・queue 待ち・walltime・grace・回収・cleanup を覆い、内側は維持) の実装ではない。dispatcher の定数は不変でも、この呼出しの実効期限は
  短縮される (相談 A5 / B2)。成功集合は (i) queue 待ちが導出締切を超える帯、(ii) 完了が最後の 32 秒の帯で縮み、retryable (rc=29) 集合がその分増える。同じ返却 rc に対する
  land の写像 (rc=1 = 違反・release_safe) は不変。RUN / collection 中に `deadline_at` へ達した場合は cleanup 予算 0 で hold latch が残る (dispatcher 不変の限界)。
  receipt の永続化は保証しない。

**却下した選択肢:**
- 外側を区間和 (P180 + Q900 + W3,600 + G300 + A60 + C90 = 5,130 秒) や中間値へ延ばす (項 8 型) — 延長は裁定なしに行わない。裁定パッケージ (insight §7) へ。
- D612 の上書き env (queue 待ち・grace) だけで内側を縮める — walltime 3,600 秒の区間を覆えず、明示上書きの意味 (opt-in) を呼び手が自動選択する形に変える。
- `M_pre = 180` 秒 (harness の値の写し) — 外側を延ばす側の余裕であり、固定 480 秒から queue 予算を削る側では過大 (Q ≈ 168 秒)。
- 投入前拒否の閾値を qsub 後合計の観測最小値 16.6 秒に置く — queue 締切の下限に合計所要を流用する区間違い。queue 待ちの観測 min × 3 に置き換えた。
- `main(dispatch_fn=...)` の注入 seam を `**kwargs` 受けへ改訂して既存テスト 7 箇所を触る — 不要。新規テストは末端 `dispatch_compute.dispatch` を monkeypatch する。
- 不正 env を無視して既定 900 秒で dispatch する — 外側に殺される job を作る。拒否 (rc=16) が fail-closed。
