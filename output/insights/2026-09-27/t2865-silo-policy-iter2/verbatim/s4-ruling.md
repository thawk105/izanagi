# 段 4 裁定 — [T-2865] silo-function-policy 軸 2 iteration 目以降 (2026-09-27)

入力: brief、段 2 plan (`codex/s2-plan.md`)、段 3 相談 A (`codex/s3-consult-A.md`、7 件: must 2・should 4・nit 1)、相談 B (`codex/s3-consult-B.md`、6 件: must 1・should 3・nit 2)。段 4 直前に local main を再走査 (339d7c188 から前進なし、T-2865 / T-2870 の新裁定なし)。

## 裁定 (依頼の「段 3 で決める」への答え)

**骨格の乱数初期値は直す (plan・相談 A・B が一致)。** 理由: 旧系列 A は walltime 予算で閉じており (P1、real)、2 iteration 目以降はどのみち新系列 B になる。修正の追加費用は Codex author 1 本と検査だけ。直さないと B の方策評価と critic 診断が、worker 間で同期した jitter の影響を受ける。正しさには影響しない (hole の外、`#if SILO_POLICY_VARIANT` 内、受理集合・hook 呼出し点・上限は不変)。

## 所見の裁定

| 所見 | 判定 | 採否・内容 |
|---|---|---|
| A1 hunk ヘッダを一律 N ずらす説明は誤り | real | 採用。hunk ごとに累積更新し、pinned CCBench 上の `git apply --check` と実適用、適用後の marker・hook 位置を author が確認する |
| A2 「初回だけ」は thread 単位で、同一 thread に別 thid の executor を順に置く一般形は保証しない | real | 採用 (記録の限定)。保証は現行 worker (1 thread = 1 executor) の寿命に限ると insight に書く。複数 executor 対応は scope 外 |
| A3 / B3 抜き出し TU の動作試験だけでは M3 (begin の呼出し削除) を素通りし、M4 は通常の thid で発火しない | real | 採用。test は 1 本の焦点 test に、(i) 適用後 source から実 seed 関数と `next_random()` を抜いた単独 TU で「異なる thid → 初回値が異なる、同じ thid → 一致、begin 相当の再呼出しで巻き戻らない」、(ii) 適用後 source の `begin()` の variant 分岐が `thid_` で seed 関数を呼ぶ結線、を持たせる。compiler は `silo_policy_compile.find_compiler` に合わせ、不在で skip したら緑と数えない。**0 の代替分岐は置かず `splitmix64(thid) \| 1ul` 型で構造的に非 0 にする** (分岐と M4 を不要にする) |
| A4 / B1 P3 bootstrap 再使用 | real (手順との食い違い) | **B 専用の bootstrap stock を測る** (runbook §1(0) と D2270 項 3 のとおり、段階 F 単価 300 秒)。「条件が混ざる」という plan の理由は採らない (stock は骨格 patch を使わない)。再測の理由は手順どおりにすることと同時期の値を得ることだけ |
| A5 / B4 P5 critic 入力 | real | 採用 (最小添付)。critic には B campaign の `silo_policy_loop_digest.txt` 本文、当該 iteration の候補実装 (`policy_history.jsonl` の `implementation`、justification は除く)、当該 pair の同 job stock の値 (job stdout JSON) だけを親が抽出して prompt に貼る。他 file を読まないよう指示するが、閲覧を機械的に防いだとは主張しない。critic の入力は逐語で job dir と insight に残す。出力は 4 見出し各 1 回を明記。runbook §1(g) の範囲内 (critic 入力を digest に限定していない)。role 本文は触らない |
| A6 / B5 見積りが楽観的 (最大 4 iteration、変異費) | real | 採用。目標は 2 iteration、3 回目は開始前の残 walltime で判断 (予算停止前に投入しない)。検査の見積りは段階 F 実績を基準にする (下表) |
| A7 同じ campaign ID が別 checkout に 2 つ | real (記録) | P4 のまま。各結果に checkout 絶対 path・HEAD・骨格 patch SHA-256・campaign dir を併記し、ID 単独で結合しない |
| B2 seed は直すべき | real | 上の裁定 |
| B6 runbook 追記の重複 | real | 採用。追記は critic の最小入力と 4 見出し、骨格を変えたときの条件の分け方 (新 checkout・bootstrap・記録項目) に絞る。walltime 予算の既存記述は重複させず、1 系列あたりの実績 iteration 数だけ 1 行足す |

## plan v2

- **実装単位 1 (Codex author):** `patches/silo-function-policy-variant.patch` (`transaction.cc` の既存 hunk 内: thread_local の seed 済み印 + `seed_random(thid)` 関数、`TxExecutor::begin()` の variant 分岐で初回だけ呼ぶ) と `orchestrator/tests/test_silo_function_policy_template.py` (焦点 test 1 本、既存 test は変えない)。規模上限: patch の追加 20 行以内、test 80 行以内。touch set・axis 定数・hole・api・受理契約・hook 呼出し点・上限・`#if SILO_POLICY_VARIANT` の外の bytes は不変。
- **親 (docs):** runbook §1(0)(g)・§3 の追記、insight、decisions / worklog fragment。
- **実走:** 実装 commit (段 6 後) の HEAD から新 submit checkout (`<job dir>/trees/b`) → B bootstrap stock job → iteration 1 (emit → coder → preview → auditor → proposal → pair) → critic → iteration 2 (`--critic-output`) → 残 walltime があれば iteration 3。pair の `elapstim_req` は 00:30:00、stock は 00:20:00。

## 変異の事前登録 (DW-M01)

runner: `tools/run_tests.py --force-dispatch orchestrator/tests/test_silo_function_policy_template.py`。

| id | 壊す箇所 (patch 内) | 期待して落ちる test |
|---|---|---|
| M1 | seed 関数の `thid` を定数 0 にする | 新焦点 test の「異なる thid → 初回値が異なる」 |
| M2 | 初回だけの印を外し毎回 seed する | 新焦点 test の「再呼出しで巻き戻らない」 |
| M3 | `begin()` の seed 呼出しを削る | 新焦点 test の結線検査 |

単一理由性は実装後に確認し、できなければ登録せず再照準する。

## 計算の見積り (job Elapse 単価、2 node 時間の線)

| 項目 | 単価の出所 | 見積り |
|---|---|---|
| B bootstrap stock 1 | 段階 F 300 秒 | 300 秒 |
| pair 最大 3 | 段階 F 765 秒 | 2,295 秒 |
| 焦点走 3 回 | 段階 F 87〜140 秒 | 420 秒 |
| 変異 probe + final (3 本 × 2) | 段階 F は 25 本で harness 所要 1,644 秒 (上限) | ≤ 1,644 秒 (保守側に段階 F の全量) |
| 受入 2 回 | 過去実績 ≈ 900 秒 / 回 | 1,800 秒 |
| 合計 | | ≤ 6,459 秒 ≈ 1.79 node 時間 (< 2) |

→ ユーザー確認なしで投入する。取り直し・4 本目の pair などで線を越えそうなら、投入前に止めて確認する。
