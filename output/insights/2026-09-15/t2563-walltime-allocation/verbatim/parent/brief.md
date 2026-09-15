# 段 1 brief — [T-2563] 認定較正 job の walltime 予約式を再凍結する

## 研究前進

Phase 3 の認定較正 (certified calibration) は、job の予約式 `walltime.required_s` を receipt へ
凍結し、proof chain の一部として残す。現在この式は job script の実体と食い違い、
「要求 7200 秒はこれを上回る」という主張が成り立たない。閉じないと、較正 receipt の
`required_s` が何を保証する数なのか定義されないまま論文の材料になる。
完了判定 = 予約式・policy 値・PBS directive・期待 test が同じ 1 つの定義で一致し、
その定義が script の逐次 timeout 上限から導出できること。

## scope (本題の実装だけ)

`tools/pegasus/certify_calibration.sh` の予約式 (冒頭 comment / `frozen_required_s` /
`walltime_formula` / `#PBS -l elapstim_req`)、`tools/pegasus/policies/calibration_v1.json` と
`tools/pegasus/policy.json` の `certify_walltime(_s)`、および逐語 pin を張る
`orchestrator/tests/test_pegasus_tools.py`。アンカー表は別紙。

**scope 外:** 並行化の再提案 (撤回済み)、他 job script (`silo_ladder_rung1` /
`ss2pl_lock_study` / `floor_campaign`) への一般化、新規 gate・検査・台帳、較正対象の拡大、
T-2564 / T-2565、`finalize_reserve_s` の値、CLI 側 `RESERVATION_FORMULA` の意味変更。

## 確定済みユーザー裁定

- **D1936 項38:** 食い違いを「既存逐次処理の上限を使う同じ式」へ揃える。関連 protocol 値・
  PBS 要求・期待 test を同じ変更で整合する。
- **D1971:** 要求時間増加を**既定解としない**。timeout・標本数は変えない。短縮効果を示せない
  実装は残さない。
- **今回引数:** 効果帰属できない並行化は再提案しない。規律 2 を緩めない。Codex author = D95。
  仮想リスク向けの gate・検査・台帳・一般化は scope 外。

## (P1) 親の provisional 裁定 — 攻撃対象

式を script の実体から導いた真値へ直し、`certify_walltime` を必要分だけ上げる
(02:00:00 → 03:00:00 = 10800 秒。真値 8760 秒を 2040 秒上回る)。
根拠: D1971 は要求時間増加を「既定解としない」であって禁止ではなく、同 wave の文脈は
「先に短縮策を探せ」だった。短縮策は実測で効果帰属不能として撤回済みで、timeout も標本数も
動かせない。残る整合手段は要求枠を実体へ合わせることだけである。
攻撃対象: (a) 式の意味を「予約配分」と再定義して 7200 を据え置く対案との比較、
(b) 真値 8760 の項の数え方 (計測予算を 4930 と 4990 のどちらで積むか、post probe 120 を
finalize_reserve 600 の内に数えるか)、(c) 03:00:00 か 02:30:00 か。

## 不変条件

- 規律 1: trace-disabled build の `nm` 検査、trace/perf 分離を 1 文字も緩めない。
- 規律 2: 受理集合を広げない。標本数 (points 5 / sweep_reps 3 / noise_reps 10)、cooldown 閾値
  (load1<=1.0・30 秒間隔・3 回連続・20 分)、各 command の `timeout` 値、
  `--effective-clock-tolerance-pct` の禁止はすべて据え置く。
- 既に凍結された receipt (`output/env/pegasus/calibration/attempts/**`) の bytes を書き換えない。
  過去の判定は追記でのみ訂正し、新しい式で遡って再解釈しない。
- `finalize_reserve_s` は 600 のまま。test が式中の `finalize_reserve(N)` と policy の一致を検査する。
- 式の各項は script に実在する `timeout` か CLI 定数から導けること。存在しない項を書かない。

## 成果物

code / test の差分 (Codex author)、式の導出表を載せた insight、worklog、decisions。

## 並列分割方針

編集面が 1 つの束に集中するため実装子 1 本。段 2 plan 1 本、段 3 敵対相談 2 本 (レンズ =
「要求枠を上げる判断が D1971 を踏み越えていないか」/「真値 8760 の導出と受理集合の不変性」)、
段 6 レビュー 2 本。
