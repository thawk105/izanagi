---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: worktree-dev-wave-t2865-r2-replay
seq: 1
title: [T-2865] 系列 C の certified 候補 3 本を R2 で 2 回ずつ測り直し、同じノードの stock 比 2.10・2.10 / 1.92・1.85 / 2.54・2.61 で元の水準と並びが再現した (計測 + insight + runbook 1 文、branch worktree-dev-wave-t2865-r2-replay)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`): 系列 C の iteration 2〜4 の候補を R2 で候補ごとに 2 回、同じノードの stock と並べて測り直す。記録 `output/insights/2026-10-01/t2865-r2-replay/README.md`。
- 段 1 で実コードから、R2 の campaign identity が候補を含まず、Pegasus では同じ checkout の 2 本目の R2 が claim で止まること (runbook §3.1 の「terminal skip」は誤り) と、replay に同じ job の stock 対照が無いことを確かめた。driver は並行 wave (t2867-contrast-run) が編集中だったので変えず、(候補, round) ごとに新しい submit checkout を作り、repo 外の親専用 wrapper job が同じ allocation で job 本体を replay → stock の順に 2 回呼ぶ形にした。段 3 は read-only codex 1 本 (2 レンズ、P1 支持・P2〜P4 修正・P5 条件付き支持)、段 4 で採用 (実装なし、4→7→8→9)。
- 計測: 6 wrapper job (40205・40213・40214・40215・40219・40220)、Elapse 合計 4,642 秒 (約 1.29 node 時間、smoke 後に積算して 2 node 時間の線の下)。12 attempt すべて serializable・anomaly 0、候補 6 回 certified、stock 6 回 certified-stock。比は iteration 2 = 2.10・2.10 (元 2.17)、iteration 3 = 1.92・1.85 (元 1.86)、iteration 4 = 2.54・2.61 (元 2.64)、並びは 3 観測とも同じ。stock に対する比の再現であって、最高水準に対する優位の証明ではない。
- 運用の実測: submit checkout 1 本 (`trees/c3r2`) は `git worktree add` と `lock` の間に管理 dir が外から消えて孤児になった (この wave は prune・撤去を打っていない)。以後は `add --lock` で作り直した。`qstat` は存在しない request にも rc=0 を返す。
- 受入: 未実施 (この記録の commit 後に行う)。

## 次の一手差分

### 更新

- [T-2865] **P1・系列 C の候補 3 本の R2 再測定で比の水準と並びが再現した → 次は新しい系列か、比の帰属に要る計数 (AI)**: silo-function-policy 軸 (D2214、段階 F = D2270) の系列 C (記録 `output/insights/2026-09-29/t2865-silo-policy-series-c/README.md`) の certified 候補 3 本を R2 (runbook §3.1、LLM なし) で候補ごとに 2 回、同じノード・同じ job の stock と並べて測り直した (記録 `output/insights/2026-10-01/t2865-r2-replay/README.md`)。同じ job の比は iteration 2 = 2.10・2.10 (元 2.17)、iteration 3 = 1.92・1.85 (元 1.86)、iteration 4 = 2.54・2.61 (元 2.64) で、候補ごとの 3 観測の範囲は重ならず並びも同じ。12 attempt すべて serializable・anomaly 0。これは既定の CCBench Silo に対する比の再現で、最高水準 (調整済みの stock・既知最良の手書き方策・他の CC 手法) に対する優位は示していない。R2 を反復するには (候補, round) ごとに新しい submit checkout を作り、同じノードの stock は repo 外の wrapper job で同じ allocation に replay → stock を続けて呼ぶ (手順と script の所在は同記録 §2)。単価は wrapper job 705〜855 秒。次は新しい系列で iteration を重ねるか、critic が求めた施錠競合時の方策の発火回数・abort 要因別の件数 (v1 に無い) を足して比の帰属を調べる。LLM 対 非 LLM の対照は [T-2867]、固定文面の改訂は [T-2870]、予算の数え方は [T-2881]。
  base: 5321c49b9e66550950d6b220774668ea42aaaa4c14543d04c4d41a2f15e1279d
