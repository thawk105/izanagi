---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-cicada-between-run-floor
seq: 1
title: [T-2915] Cicada の throughput の時間窓間ばらつきを関門の対象外の診断経路で日内 6 窓にわたって測った — 主 GC の A で Y5 0.69%・Y50 1.05%・Y95 0.70%、いずれも D19 の下限 3% より小さい (計測データ + insight、branch worktree-dev-wave-cicada-between-run-floor)
---

## 本文

- 依頼 md_35 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_35.txt`)。道の比較と裁定は {{D:cicada-window-cv-diagnostic-path}}、一次資料 `output/insights/2026-09-30/cicada-between-run-floor/README.md`。
- 段 3 相談 2 本 (A: 正しさ境界、B: 過剰・統計) の must-fix 5 件を含む 15 所見をすべて real と裁定した。中心は A1「関門を通らない値を f_T・floor と名乗らない」で、名前を「日内 6 窓・診断経路」とし、[T-2915] を完了でなく更新にした。
- 段 2 (codex の plan 起草) は省き、plan を段 1 brief と段 4 裁定に含めた。repo の実装面の差分はゼロ (driver は無改変、集計 script は Codex author が job dir に書いた) で、変異 matrix は免除。
- 実行した手順: 窓 1 を 15:18 JST に投入、以後 series script が 60 分おきに 20:19 まで投入。18 job すべて rc=0・検査合格、代替窓は使っていない。Elapse 合計 2,275 s。
- author の初回起動 (author-1) は起動器に `--max-attempts 2` を付けて dry-run 前に投入し rc=2 (workspace-write では不可)。起動前の失敗で、author-2 で正しく走った。DW-O01 の「dry-run の argv を先に検査」を省いた手順違反で、規則の不足ではない。
- 利用上限で 20:21〜21:41 JST に中断し、同じ session で再開した (計測は中断前に全窓完了)。
- 段 6 敵対レビュー 1 本: §4 の表は生データ 360 run から丸めまで再現。所見 6 件をすべて real と裁定し文言と置き場で直した。must-fix R1 は段 4 裁定の誤りの訂正で、「max(0.030, ·) があるので採否を緩める経路は無い」は誤り (δ_T を上げると「同等」は通りやすく「悪化」は出にくい、評価計画 §5.1)。fix 後の焦点再レビューが、δ_T は A/A 判定と job 間の停止条件 2δ (§8.1) にも効くこと (N1、must-fix) と、「0.030 以下なら f_T に代入してよい」が §8.3 の f_T = D145 の floor と食い違うこと (N2) を示した。{{D:cicada-window-cv-diagnostic-path}} を「本値は f_T に代入せず、D19 の下限で計算した δ_T の根拠として併記。下限を超える値を δ_T に入れるかは 4 箇所への影響を含めて別裁定」に改めた。今回の値はすべて 0.030 以下で δ_T は動かず、結論は変わらない。R3 (集計 script が実効 flags を照合しない) は partial のまま閉じた — レビュー 2 本が 360 run を照合して不一致 0、値は変わらないので script は変えず限界として記した (DW-O16 の親裁定)。
- 集計 script の自走検査は、親が repo 外の別の場所に置いたまま走らせると 9 件失敗した (検査が子の PYTHONPATH を script の親の親に上書きし `tools` を import できない)。author の木 (repo checkout の root 直下の `cfloor-scratch/`) で同じ bytes を走らせると 3 件 OK。配置の前提であって検査の欠陥ではない。一次資料 §8・§10 に手順を書いた。
- DW-S07 の三軸語走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`) は rc=1。hit (conjunction_hits) は rr80・rr20 とも既存の `output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の同じ 3 file (journal.jsonl・manifest.json・result.json) だけで、本 wave の file (一次資料・window-cv.json・計測データ・fragment) の hit は 0 (出力の `docs/paper-story/figures/` の列は走査器の正例 positive_control で hit ではない)。

## 次の一手差分

### 更新

- [T-2915] **P3・更新 (Y の 3 動作点は測定済み、残りは日を跨ぐ窓と他の cell)**: Cicada の throughput の f_T の判断材料として、関門 (D1373) の対象外の診断経路で「Cicada A の時間窓間 session-median CV (日内 6 窓・診断経路)」を測った (f_T には代入せず、D19 の下限で計算した δ_T の根拠として併記する) ({{D:cicada-window-cv-diagnostic-path}}、一次資料 `output/insights/2026-09-30/cicada-between-run-floor/README.md`)。主 GC の A で Y5 0.69%・Y50 1.05%・Y95 0.70% で、いずれも 3% より小さく、これらの署名では δ_T = ln 1.03 のまま (D19 の下限で決まる)。残り: (1) 日を跨ぐ窓 (同じ spec 形・起動器で別の日に数窓足す、1 窓 3 job で約 6 node 分)、(2) R・L-w・100 操作型の cell (R は性能用 build の ro 指定率の生成器が無い)。評価計画 §8.3 の二択 (下限だけで発効 / floor を待つ) は、発効の wave が本値を添えてユーザーに諮る。
  base: 50ca92f6addd27e6672fa3cc4dcf54a169f7d9984cbfe5c6d3353fbea1a2b944
