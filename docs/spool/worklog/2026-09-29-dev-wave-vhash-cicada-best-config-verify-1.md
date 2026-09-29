---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-cicada-best-config-verify
seq: 1
title: [T-2902] VHash 比較相手 Cicada の観測最良設定を判定器に掛け、実走した 30 条件 32 run の stock がすべて巡回なし (上限 indeterminate)、inline slot の版の記録は 3 点比較で食い違い 0、同じ設定の正例 3 本は検出・帰属 (insight のみ、repo 外の起動器と診断 patch、branch worktree-dev-wave-vhash-cicada-best-config-verify)
---

## 本文

- 依頼: 並行 VHash wave の md_20 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_20.txt`)。一次資料 `output/insights/2026-09-29/vhash-cicada-best-config-verify/README.md`、判断は {{D:cicada-best-config-verify}}。
- 段構成: 全 9 段 (md_20 が段 3 と段 6 を省かないと指定)。段 3 相談 2 本、段 6 レビュー 2 本・fix 1 巡・焦点再レビュー 1 本、一次資料の独立レビュー 1 本。Codex author は repo 外の起動器 (md_17 の起動器の写しを拡張) と診断 patch を書いた。repo の実装面の差分は無く、変異 matrix は免除 (DW-S04)。
- 素材: 最良設定の INLINE_VERSION_OPT=1 では、inline slot の版が読みの 5.2〜59.4%・書きの 4.7〜36.9% を占めた。md_3 の `READ_WTS_MISMATCH` は登録時と commit 時しか比べないので、版を選んでから登録するまでの slot の再利用を見逃す (段 2・段 3 で指摘)。選んだ瞬間・登録・commit の 3 点比較の診断を足し、全 35 run で 0。
- 素材: 同じ設定に既存の壊し (read set の再検査を飛ばす) を重ねると、BEST の rr50 thread 4・48 と BEST100 の 100 操作型 thread 4 のいずれも non-serializable で、witness の rw 辺が事象の読んだ版と相手の W 行の版に一致した。
- 棄却・訂正: 段 1 brief の「経路が分かれないので inline の件数を数えれば足りる」(P2) は段 2・3 で撤回 (件数は到達の証拠にすぎない)。段 6 の所見のうち B1 (正例 job の対照の再走)・B4 (J2 の投入判断を起動器に持たせる) は不採用、B2 (W4 の第二尺度の欠落) は W4 の commit が最少 19,701 で発動条件に当たらず影響なし。焦点再レビューの C1 (分類に第 5 の「不合格」) は偽の緑を作らないので直さず、結果前に「巡回以外の検査が外れた失格」と扱いを固定した (該当 0)。
- 親の訂正: 一次資料の初稿で inline の割合を「読み 1〜59%・書き 5〜18%」「書き 4.6〜33.4%」と書いていた (計算前の見込み) のを、原本 JSON から計算し直して 4.7〜36.9% に直した。「32 条件」は重複 2 組を含むので「32 run (異なる条件は 30)」に直した。
- 計算: 計算ノード 8 job、合計 1,165 s (約 19 node 分)。L0 は fix 前の起動器で 1 度走らせ、fix 後に取り直した。
- 異常: worktree の checkout が Lustre の混雑で 1 本あたり 9〜14 分かかり、`システムコール割り込み` の警告が多数出た (作成は成功、clean)。最初の submodule 初期化は `update-no-fetch` で 1 度落ち、再走で通った。

## 次の一手差分

### 完了

- [T-2902] Cicada の観測最良設定 (BEST と BEST100) と既定を、md_3 の trace と repo 外の忠実性診断で判定器に掛け、実走した 30 条件 32 run で巡回なし (上限 indeterminate)、同じ設定の正例 3 本は検出・帰属した。md_11 の主比較条件 (走行 3 秒以上) は未検査として一次資料 §7 に記した ({{D:cicada-best-config-verify}})。
  remaining: none
  base: ecbb63c53552886fce9e8c0cf0947b0373877998534492b7b078bee36a53455b
