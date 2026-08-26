# [T-1721] A-1 対測定の投入 blocker — 一次資料

wave: `worktree-dev-wave-t1721-a1-paired-submit` (base `9463bcbc`)
実装差分ゼロ。qsub は 1 度も投げていない。

## 何を確かめたか

依頼の前提「A-1 は正式 certification ではないので批准 (D905) の gate は適用されない。
装置と事前登録は凍結済みで投入だけが残る」を実測した。前提は 2 つの独立した理由で偽だった。

## 親の実測 (main 9463bcbc、read-only)

```
capture_contract_loader_binding()          -> commit 9463bcbcb1541625db59abb97cf6a76934b4c80c
verify_live_contract_loader_binding()      -> OK
verify_ratified_contract_loader_binding()  -> ContractLoaderBindingError:
    enforcement-source-ratification: ratification history is not a strict prefix extension
```

- 現行 closure digest: `6d497998c4b80a186cd9ee3fc98154e29ddd0aa23f82f7da215558b90e32bf5a`
- 批准台帳の唯一の行: `db511c3d841128bfdbf5ba7c6bbdb2ce4da1fe0fdefe8d52aaacb0906ddeea44`
- 台帳の path 履歴: 17 commit (開設 1 + merge 16)。全 commit で blob は 112 bytes 不変。
  wave 971 当時の main `f4c2c5de` では 16 commit で同型。
- 批准行を作った commit `6188a8d4` の A-1 は study ID が旧版で policy v2 が無い。
- 批准検査の単体テスト: 計算ノードで 12 passed (request `948874.nqsv`)。
  production では値を返さないのにテストは緑。履歴がすべて直列で merge DAG を通していない。
- `paper-story-a1-paired-submission/v1` を書く実装は tracked file に 0 件。
  他の dispatch 必須 job body には `tools/pegasus/submit_*.sh` が 6 本あるが A-1 には無い。

## 一次資料

- `verbatim/s1-brief.md` — 段 1 brief (commit 数の訂正後)
- `verbatim/s2-plan.md` — 段 2 codex plan (read-only)。経路の全数列挙
- `verbatim/s3-consult-sol.md` — 段 3 敵対相談 sol レンズ (正しさ境界と規律)
- `verbatim/s3-consult-luna.md` — 段 3 敵対相談 luna レンズ (機構と実効性)

段 2・段 3 はいずれも read-only sandbox で pytest を実走しておらず、緑を主張していない。

## 関連

- 批准履歴検査の壊れ自体は F600 として記録済みで、修理は並行 wave
  (branch `worktree-dev-wave-t1759-t1742-ratification-history`) が所有する。本 wave は同じ面を触らない。
- 批准 gap そのものは F498 の再発として記録した。
