---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-cicada-between-run-floor
seq: 1
---

## {{D:cicada-window-cv-diagnostic-path}}. Cicada の throughput の時間窓間ばらつきは、D1373 の関門の対象外の診断経路で日内の複数時間窓にわたって測り、評価計画の f_T へは δ_T を大きくする向きにだけ入れてよい量として渡す

**決定:**

1. VHash 評価計画の草稿 (§8.3・§11 P2) が求める Cicada の throughput の f_T について、道を 3 つ並べて比べ、「関門の対象外の別手続き」を採った。md_11 の診断 driver `tools/vhash_cicada_tuning/driver.py` を無改変で使い、比較相手 A (md_11 の最良設定) と control を、日内 6 時間窓 (1 窓 = 1 投入束、窓の間は 60 分以上) × Y5・Y50・Y95 で測った。
2. 得た量は「Cicada A の時間窓間 session-median CV (日内 6 窓・診断経路)」と名乗る。floor artifact (`output/env/*/calibration/between_run_noise_*`)・izanagi の compare・採否には接続しない。D1373 の関門を通った floor とも、D145 項 5 が要求する真正な floor の標本設計を裁定した値とも呼ばない。
3. 評価計画の式 δ_T = ln(1 + max(0.030, f_T)) では、この値を f_T に入れても δ_T は D19 の下限 0.030 より小さくならない。発効の wave がこの値を f_T に代入してよいのは、値が 0.030 を超えて δ_T を大きくする向きのときに限る。0.030 以下なら判定は D19 の下限で行い、「日内の窓間 CV はそれより小さかった (日を跨ぐ変動は未測定)」と読む。§8.3 の二択 (下限だけで発効 / floor を待つ) はユーザーの判断として残す。
4. 測った結果 (主 GC の A): Y5 0.69%・Y50 1.05%・Y95 0.70%。すべて 0.030 より小さい。一次資料 `output/insights/2026-09-30/cicada-between-run-floor/README.md`。

**理由:**

- 関門を通す道 (Cicada の hook を CCBench に入れて pin を進める、D2083 項 5 と同じ条件) は、CCBench・pin・patches を本 wave の所有外とした依頼の範囲を超える。関門の受理を「patch 適用後の source」へ広げる案は、現行述語が checkout の compiled SOURCES を読む契約を変えて受理集合を広げるので、依頼が禁じた「関門を緩める道」に当たる。
- D2291 項 1 は「関門の射程は floor artifact の生成で、診断値として一次資料に書くのは迂回でない」とした。本決定はその経路で、D145 項 2 (estimand を名乗り compare へ配線しない) と項 4 (動作点署名ごと) を守る。
- max(0.030, ·) の形により、関門を通らない値が判定の閾値を下げる経路は存在しない。D1373 の趣旨 (検査できない protocol に採否を緩める floor を与えない) は、この形では破れない。Cicada の各構成の正しさは評価計画 §7 の門が別に要求する。
- 1 投入束の値 (md_11 の 0.43〜0.81%) は D145 により floor の代わりにならない。複数の時間窓を持つ計測を、既存 driver で安価に (18 job・約 0.63 node 時間) 取れた。

**却下した選択肢:**

- 関門の受理を patch 適用後の source へ広げる — 受理集合の拡大で、関門の緩和に当たる。patch 後の source を厳密に束縛する設計の余地は別裁定に残る。
- `between_run_floor.py` の BASELINES に cicada を足す — 関門で止まり測定は開通しない (D2291・D2083 と同じ)。
- 計測せず D19 の下限だけを使う — Cicada の窓間の揺れが 3% を超えるかどうかを知らないまま下限を使うことになる。
- 得た値を「floor 取得済み」「f_T 確定」と書く — 日を跨ぐ変動を含まず、関門も通っていない。段 3 相談 A1 の指摘どおり、名前で過大に主張しない。
- 前日の md_11 J2 を 7 番目の窓として混ぜる — 反復数と job の構成が違い、A の選択に使った測定でもある。参考行として別掲するだけにした。
- 正規性を仮定した CV の信頼上限を出す — 標準偏差の χ² の係数は CV の厳密な区間にならない。
