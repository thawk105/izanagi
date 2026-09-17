---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-18
wave: dev-wave-t2724-freeze-g1-gen
seq: 2
---

## 再発

### F862

- **再発: 2026-09-18** — [T-2724] 候補生成 wave の一次資料 §8 と裁定パッケージ (d) が、chain (official 床値 result) を main に載せる帰結を growth hold 登録簿にある実 repo 走査 test 2 本だけで数え、登録簿に無い実 root consumer (実 root の git-visible output を fixture へ複製する T-080 fixture 10 node、実 committed HEAD を clone して official clean scan を通す 5 node、`run_block(root=ROOT)` で T-080 receipt を解決し process 内 memo で共有する契約 test 29 node、公開 gate の v1 verify 1 node) と production の oracle gate (`_make_gate_decision` が receipt refusal を無条件 merge、`_campaign_t080_value` が invalid receipt を拒否) への波及を列挙しないまま D2120 項 2 (a)(d) が裁定された。世代導入 G の wave が X1' を含む木で焦点走を実走して 45 failed / 967 passed、runbook §2 P3 `gate-check` の refusals に `holdout-freeze-verify: [holdout.unknownness_layer2]` が混入することを観測 (`output/insights/2026-09-18/t2724-freeze-g1-gen/README.md` §4)。恒久対応の追加: memory `chain-consequence-enumerate-real-root-consumers` (2026-09-18 作成) — 凍結 / official 成果物を tree に入れる帰結は hold 登録簿でなく `ROOT` 参照 (複製・clone・`root=ROOT` 解決) を grep で列挙し、その成果物を含む木で当該 file を `tools/run_tests.py` で 1 走し、production gate (runbook P3) も同じ木で 1 回叩いてから裁定材料に書く。
