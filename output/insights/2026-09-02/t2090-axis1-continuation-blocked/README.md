# 2026-09-02 — 軸 1 OpenAlex の継続取得は、無償枠ではなく完走条件 1 に塞がれている

- **wave:** dev-wave-t2090-axis1-openalex-continuation (T-2090)
- **入力 commit:** `dd5fddf04e7d876cee9ff9a87849cdf60d07080b` (local main)
- **登録 commit:** `d0ba65c01ab7319bd20393a55d21bccbf3716a5f` (変更していない)
- **HTTP 発行数:** 0。**本 wave は 1 件も取得していない。**
- **実装面の差分:** ゼロ。既存 bundle の bytes も変えていない。

## 何を確かめたか

依頼は「発行済みの再開点から、無償枠の窓ごとに OpenAlex 78 leaf を継いで取り切る」だった。
その前提が現物と食い違っていたので、取得も実装もせずに裁定へ返す。

## 1. 実行環境はコード変更なしに再構成できる

実行器は 2 つの束縛を持つ。

- `orchestrator/axis1_search/validator.py` の `verify_registration` が
  **`HEAD == 登録 commit`** を要求する。local main から作った作業ツリーでは `head_mismatch` で全面拒否される。
- `tools/run_axis1_search.py` の checkpoint 検査が、再開点の `bundle_root` と
  `--bundle` の **`Path.resolve()` 一致**を要求する。再開点が記録している絶対 path
  (`.codex/worktrees/dev-wave-t2033-axis1-retake/...`) の作業ツリーは消滅していた。

登録 commit を detach した作業ツリーを**同じ絶対 path** へ作り直し、証拠 bundle を復元したところ、
登録検査は `passed: true` を返した。復元した `manifest.json` の SHA-256 は
凍結記録 (`2026-08-30-axis1-search-execution.md` §2) の
`e74deb222df4f04899029e07bc771ed77d1cfc66bfea188f01c17f8293368214` と byte 単位で一致した。

**検査器だけは main 側を使う必要がある。** 登録 commit 時点の validator は部分 bundle を
途中で打ち切る。D1317 を実装した `2617eee02` 以降の validator でなければ最後まで通らない。

> **運用の要点 (次のセッションへ):** 実行器 = 登録 commit の作業ツリー、
> 検査器 = main の作業ツリー、bundle = 再開点が記録した絶対 path。この 3 点セットで実行も検査も成立する。
> ただし**次の窓で増える証拠は登録 commit に含まれない**ので、作業ツリーを作り直すだけでは
> 最新 bundle は復元できない。窓ごとに bundle を独立に永続保存する手順が要る。

main の検査器が返した baseline は `bundle-baseline-mainchecker.json` に置いた。
`bundle_validation_complete = true` / `exact_identity_map = true` / `axis_complete = false` /
`incomplete_checkpoint_counts = {missing: 79, not_run: 77, present: 0}`。

## 2. 無償枠のゲートが窓をまたいで自己施錠する

`orchestrator/axis1_search/runner.py` は無償枠の観測を bundle 内の
`state/runtime.json` へ持続化し、`QuotaObservation.permits_next` が
`remaining - 30 >= credits_per_request` を要求する。現在の持続値は
`remaining: 10` (観測 2026-08-29T23:54 JST) なので偽になり続ける。

**`x-ratelimit-reset` は記録されるだけで、失効判定にどこでも使われていない。**
したがって一度枠を使い切ると、その bundle では二度と request を発行できない。

実測: 登録済み leaf `AX1-20260829-E1-Q2@openalex` を起動したところ
`{"state": "paused_quota", "reason_code": "quota_reserve", "request_count": 0}` (rc=3) で、
**1 件も発行せずに終了した。** そのとき発行された再開点を `probe-checkpoint-000170.json` に残す
(bundle 自体は pristine へ戻し、manifest SHA の再一致を確認済み)。

## 3. しかし本当の塞ぎはその先にある — これが本 wave の主要な発見

`runner.py` は頁ごとに完走条件を評価し、`failure_result` に最初の失敗を取る。
無償枠による停止を優先した後、**失敗が 1 つでもあれば `blocked_on_ruling` を返して leaf を終える。**
次 cursor へ進む分岐には到達せず、**後継 checkpoint も書かない。**

OpenAlex の条件 1 は全枝で落ちる。索引が `or` グループ内とグループ間の順序を正規化して返すのに対し、
登録値は登録順のままだからである。前走行の診断は **92 頁すべてで、順序を除いて完全に同一**であることを
実測している (凍結記録 §5.1)。

> **帰結: 無償枠を直しても、OpenAlex の各枝は最初の 1 頁で止まり、再開点も残らない。**
> 窓を何回重ねても継続取得の経路が存在しない。T-2090 は T-2091 の裁定なしには着手できない。

段 3 の 2 レンズが独立にこの停止を指摘し、親が `runner.py` の当該分岐と
`failure_result` の生成箇所を現物で追認した。

## 4. 段 2 の案には弱体化の反例があった

段 2 は「登録 commit を張り替え、bundle 内の checkpoint 束縛を artifact 単位へ緩める」案を採った。
段 3 (正しさ境界のレンズ) が次の反例を出した。

1. 既存の checkpoint・page・ledger を一切増やさない。
2. `manifest.registration_commit` だけを新 commit にし、manifest と自己 digest を再生成する。
3. checkpoint↔ledger と page↔ledger はすべて旧 commit のまま一致する。

**3 束縛はすべて成立するが、新 commit で生成された成果物はゼロである。** これは内部の自己整合であって、
外部の登録事実への束縛ではない。規律 2 により、この形では実装しない。

`reset_seconds` の 0・小さすぎる正値・型混同で失効が即成立して予約が素通りする経路、
失効判定と HTTP 発行が原子的でないため「1 request だけ」を保証できない経路も
同レンズが指摘した。いずれも将来の実装時に閉じる必要がある。

## 5. 予算の訂正

- 1 窓の上限は 96 ではなく **97 request**。`remaining = 1000 - 10n` で 96 件後は 40 であり、
  `40 - 30 >= 10` が真なので 97 件目を発行できる。ただし契約 §4.1 は request 数による運転を
  禁じているので、この数字を停止条件に使ってはならない。
- OpenAlex 78 枝のうち **74 枝が独立 2 走を必須**とする (catalog の `independent_pass_required`)。
  最低でも `Q1 残り 3 + 単走 3 + 複走 74 × 2 = 154 request`、**2 窓以上**を要する。
- 契約が言う「5 日以上」は、現存する 92 頁の実測と 74 本の 2 走義務からは支持されない。
  桁違いではないが 2 窓推定の 2 倍以上大きい。

## 6. この記録の限界

- **軸 1 の成熟度を動かしていない。`RW1` のままである。**
- **不在について何も言っていない。** record を 1 件も判定していない。
- **本 wave は HTTP を 1 件も発行していない。** 上の観測は既存証拠と静的検査、
  および 0 request で終了した 1 回の起動から得たものである。
- 条件 1 が全枝で落ちるという主張の根拠は、前走行の診断が観測した 92 頁である。
  API 仕様の恒久契約としては断定しない。

## 収録物

| file | 中身 |
|---|---|
| `stage2-plan.md` | 段 2 のプラン (逐語) |
| `stage3-review-correctness.md` | 段 3 レビュー・正しさ境界のレンズ (逐語) |
| `stage3-review-coherence.md` | 段 3 レビュー・整合と実効性のレンズ (逐語) |
| `bundle-baseline-mainchecker.json` | main の検査器が返した bundle 全体の状態 |
| `probe-checkpoint-000170.json` | 0 request で終了した起動が発行した再開点 |
