---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-mocc-witlight-arm-run
seq: 1
title: mocc 軽量 witness を hook branch に実装し 4 arm × 60 走を実測した — on 0/60・0/60、off 1/60・1/60、discriminator 未発火 (submodule commit + docs、branch worktree-dev-wave-mocc-witlight-arm-run)
---

## 本文

- ユーザー決定 (2026-09-19): 軽量 witness を hook branch に実装し、4 arm (witlight on/off × BACK_OFF 0/1) × 各 60 走を計算ノードで取る。非 certifying、昇格・pin 前進・変異探索は認可しない。
  一次資料 = `output/insights/2026-09-19/mocc-witlight-arm-run/README.md` (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/`)。
- brief 前の実測で覆した前提 3 つ: T-2779 §3 案の `#include <vector>` は identity checker の include 行完全一致契約で拒否される (transaction.hh 経由で不要)、
  hook commit を pin にすると repo の X/P patch の `#line` と runner v5 の discriminator 条件 (`pin != e9e477ca` で not-run) が壊れる → 測定は pin e9e477ca + [X/P, 測定 patch] で runner 無変更、
  認可枠 60/arm の検出力は観測率 0.042 対 0 で 0.105 (「80%」は率 0.119 の条件付き計算)。認可枠を超えず上限として明記した。
- 段 2 plan 1、段 3 敵対相談 2 (A 観測意味論・identity、B 実験設計・収集)、author 1、レビュー 2、fix 子 0。全 codex 子 accepted。
  段 3 must-fix 6 件全件 real・採用: 合成 source の TRACE=0 identity は未担保 → TRACE=1 観測専用と明記、brief の「非 certifying ⇒ 成果物影響なし」撤回、
  変異免除を outer repo の差分ゼロ範囲に限定 (W / 測定 patch / smoke wrapper の挙動検査 V1〜V7 を登録)、smoke 合格集合を結果前に固定 (rc=0 と整合 G2 の rc=1)、
  S 第 5 値の被覆 (静的 data flow + smoke 正例、runtime 注入は未実施と限定)、4 投入元の開始条件固定。refuted: S 遅延の意味論・parser・TLS 残留・INSERT/DELETE・検出力表・回転。
- 段 6 レビュー A must-fix 2 (identity 説明から policy digest を分離、W の trailer に codex reviewer 行) → W を message だけ amend (`e0905b3d` → `5b02546f`、tree 不変) し identity 2 本 + 負例を再走 (同結果)。
  レビュー B must-fix 2 (投入直前 `ps` 実測の保存証拠が無い → 未確認範囲を insight に明記、smoke 合格集合の保留条件の脱落 → 復元)、should 3、nit 1。独立再計算は全項一致で再走・補充なし。fix 子 0。
- W (`5b02546f`、branch `izanagi-t1943-mocc-g2-witlight`、e9e477ca の子) は wave worktree の submodule で親が commit し、段 9 で主 checkout の submodule git dir へ fetch、bundle は job dir。gitlink 511c9538 不変、GitHub push は人間手番 (D16)。
- 結果: on 0/60・0/60、off 1/60・1/60、片側 Fisher p=0.500 (両比較)、on に G2 なしで discriminator 未発火 (問い ii 未到達)。off の 2 件は G2・長さ 2・両辺 rw。
  commit 数は on が off の約 86% (曝露量の記録、性能主張ではない)。smoke は 1 回 (再試行なし)。生 trace 96 file / 603 MB を manifest 照合の上 job dir に保全。
- 隔離 session の作法で実測した罠 (改善候補として段 8 で裁定): `bash <script>` / `setsid $VAR` は harness が拒否し `nohup setsid /abs/script.sh` だけ通る、submodule path 文字列と heredoc の同居は guard が拒否するので job dir の file は Write tool で作る、
  codex sandbox は submodule の git dir (cwd 外) へ書けないので submodule commit は親が自分の worktree の submodule に一時 worktree を切って作る。

## 次の一手差分

### 新規

- {{T:mocc-witness-on-g2-acquisition}} **P3・ユーザー裁定待ち**: 軽量 witness on で G2 を 1 件以上得て discriminator を実例で試す設計を選ぶ。
  候補 = (a) 同設計で各 arm 120 以上 (完全抑制の検出力 0.5 超、off 率 0.017 なら更に多い)、(b) 曝露量を増やす cell (extime 延長、事前登録の再設計)、
  (c) 残る観測者効果 (L 行・reserve・E 行) を更に軽くする設計。いずれも非 certifying で結果を見て標本を増やさない。本 wave の on 0/60 は不在証明ではない。
