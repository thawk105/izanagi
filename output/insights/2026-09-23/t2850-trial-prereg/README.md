# 探索の独立反復の試走の事前登録 — 起草の経緯 ([T-2850]、2026-09-23、計算なし)

- 位置づけ: 事前登録 `docs/search-repetition-trial-preregistration.md` (v1) の起草記録。規則の正本は事前登録、採用判断の正本は同じ wave の decisions fragment。
  可変状態の正本 (worklog 末尾・`docs/phase3.md`) にはしない。
- 作成: dev-wave `worktree-t2850-trial-prereg` (起点 local main `cadaf3805`、開始 gate rc 0 は 08:35 JST)。実装・build・計算投入はしていない。
- 一次資料: `output/insights/2026-09-21/vldb-direction/gap-analysis.md` §4 P3、同 dir `codex-consult-1.md` の優先 2。比較基盤の設計 = D2220 と
  `output/insights/2026-09-22/t2849-comparison-harness-design/README.md`。依頼の逐語は `verbatim/request.md`。
- 段の記録: 段 1 brief (`verbatim/s1-brief.md`)、段 3 の Codex 相談 2 本 (`verbatim/s3-consult-A.md` / `s3-consult-B.md`)、段 4 裁定 (`verbatim/s4-ruling.md`)、
  費用と系列数の試算 (`verbatim/cost-model-v2.md`)。段 6 以降は下の §2 に追記する。
- **性質の断り:** すべて静的調査と算術による。「試算」と書いた値は仮定を置いた模型の値で、上限の保証ではない。

## 1. 要点

1. **試走は Silo の S1 (backoff 値 1..1000 µs) × write-heavy / read-heavy × 5 手法 × 各 3 系列。** 一次資料の案 (2 protocol × 2 課題) から縮めた。
   起草時点で走らせられる空間が S1 だけだからである (MOCC は pin 承認済みで更新 wave の前、S3 は段階 D の前)。空間は生成開始前の追補で足す。
2. **B 10・A 30・初期点 2・N_eval 5 を、S1 の試走と本比較で同じにする。** 本比較で変えるのは課題の集合と系列数だけ。
3. **評価数を揃えた族 E_B と、経過時間を揃えた族 E_T を分ける。** E_T は「B ≤ 10 の探索を、非 LLM の手法が B を終える典型的な時刻 T_c で切った比較」で、
   追加の評価はしない。T_c は試走の所要から決め、試走では E_T の再計測をしない (段 3 相談 B の must-fix 1)。
4. **本比較の系列数は、試走の cell ごとの標準偏差から作る手法対の対差 SD の最大値で、2 段の計画半幅 (δ/2、ln 1.05) から決める。**
   pooled の分散は最も不安定な対を支えないので採らない (相談 A の must-fix 1)。算出できない・上限を超えるときは n を縮めずユーザーへ返す。
5. **費用 (試算):** 試走 128.7〜145.4 node 時間 (論理 600 session)、上限 200。本比較は S1 の 3 workload で n = 5 なら 343.8〜485.7 node 時間で、
   一次資料の 510 node 時間の中に同等を言える精度はほぼ入らない。

## 2. 本 wave の経緯

- 段 1 (親): 起点 `cadaf3805`、開始 gate rc 0 (08:35:17)。一次資料・D2220・基盤設計・B-5・転移登録・D2216/D2217/D2219/D2222 を読み、brief (P1〜P9) と草稿を書いた。
- 段 2: 省略 (docs のみ。brief と草稿を plan とした)。
- 段 3 (Codex read-only、reasoning medium): 相談 A (luna、統計設計・公平性・情報の漏れ) は must-fix 7 / should 5 / nit 1、相談 B (sol、実行可能性・費用の算術・
  既存規則との整合と過剰) は must-fix 7 / should 5 / nit 2。
- 段 4 (親): 27 件をすべて real と判定し採用した。段 4 直前の裁定 inbox の再走査で、/rulings 第 32 回 (2026-09-23 08:2x) の 2 件 (MOCC の pin 承認、B-5 本走の承認) を
  本文に反映した。brief の提案値 (P6 の 1 段の精度・P8 の 600 node 時間) は裁定で 2 段の精度・510 node 時間に改めた (brief は起草時の記録として残す)。
