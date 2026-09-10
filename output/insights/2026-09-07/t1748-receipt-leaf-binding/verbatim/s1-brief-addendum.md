# 段 1 brief 補遺 — (P1-b) の悲観は親の実測で反証された

段 2 起動後に親が発行側を辿って実測した。brief の (P1-b)「build mode の leaf は report + events
だけでは再導出できない。完全な再導出は不可能」は**誤り**である。段 4 の裁定はこの補遺を正とする。

## 実測

`verify_s8c_cross_binding` の 4 引数は、すべて追跡済み受領証だけから復元できる。

| 引数 | 発行側での決まり方 | 受領証からの復元 |
|---|---|---|
| `report` | `item.report` = `report_path` の JSON | `trial.report_path` を再読 (verifier は既に再読・再ハッシュしている) |
| `events` | `attempt_journal_path` の JSONL | `trial.attempt_journal_path` を再読 (同上) |
| `run_root` | `item.journal_path.resolve().parent` (`trial_registry.py:6081`) | `attempt_journal_path` の親 directory。受領証に記録済みの path から機械的に決まる |
| `output_root` | `campaign_roots[0].parent.parent`。かつ `run_root.parent.parent` と一致することを `trial_registry.py:6133-6137` が要求する | `run_root` の親の親。`campaign_root` は report の `cells[].campaign_root` にあり、report は再読される |

`trial_registry.py:6133-6137` の一致要求が効いているので、`output_root` を `run_root` から導いても
発行時と同じ値になる。つまり **standalone verifier は発行時とまったく同じ引数で
`verify_s8c_cross_binding` を呼び直せる。**

## 裁定への含意

- brief の (P1-c) (leaf の preimage を別成果物として永続化する) は不要である。schema を変えずに
  完全な再導出が可能なので、成果物を増やす案は最小限を超える。
- 採るべき形は **(P1-a) の素材で (P1-b) が不可能と決めつけた再導出を実際に行う**こと、すなわち
  verifier 内で `verify_s8c_cross_binding` を呼び直し、返る `receipt_sha256` を
  `trial.cross_binding_receipt_sha256` と照合する。左辺は現物 (report・journal・campaign 実体) から
  導かれ、右辺は受領証の宣言値なので、恒真ではない。
- 残る論点は 2 つ。段 3 の攻撃対象とする。
  1. **現物が消えている受領証の扱い。** campaign 実体は `run_root` 配下にあり、受領証とは別に
     消えうる。消えていれば再導出は失敗する。これを拒否とするか、別の理由コードとするか。
     発行済み受領証が 0 件なので、既存成果物を invalidate する危険は無い。
  2. **副作用の大きさ。** `verify_s8c_cross_binding` は多数の file を読み subprocess を呼びうる。
     `test_ccbench_spawn_sites.py:230` の起動点 pin と、standalone verifier の所要時間に効く。

## この補遺の位置づけ

段 2 プランはこの補遺を見ずに起草されている。段 2 が (P1-b) を根拠に「再導出は不可能」と結論して
いたら、その結論は前提の誤りに由来するので段 4 で採らない。段 3 の 2 本にはこの補遺を渡す。
