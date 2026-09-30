## 所見の対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| RA1 | **裁定の理由は不成立** | `foo` は実 patch の `#if` では 0 と解釈され得る（[patch:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/patches/silo-lock-order-variant.patch:9)）。しかし Phase 3 の前処理は `-Werror=undef` を使い、失敗時は identity を確定せず停止する（[source_digest.py:1686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/source_digest.py:1686)、[source_digest.py:1697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/source_digest.py:1697)）。反例は `SILO_ORDER_VARIANT=foo` を渡す場合で、**STOCK として記録されるのではなく、未定義の `foo` により resolve が失敗する**。正常に resolve した token は WAL の `src_token` と variant ID に記録される（[pipeline.py:1994](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/pipeline.py:1994)）。「driver は整数値を与える」という限定は妥当だが、裁定文の STOCK identity という説明は訂正が必要。 |
| RB1 | **closed** | 比較元は repo 内の `axis_silo_lock_order.API_HEADER` に変更された（[test_silo_lock_order_template.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:26)、[同:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:88)）。 |
| RB2 | **closed** | pinned clone に実 patch を適用し、実物の `version_desc.cpp` を gate 経由で書く受理テストと、文法拒否時の source 不変テストが追加された（[同:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:40)、[同:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:150)、[同:170](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:170)）。期待 bytes は `render_hole` を呼ばずに組み立てている。 |
| RB3 | **closed（fix 対象の pin 部分）** | test の pin は軸の `PIN` を参照する（[同:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:24)）。件数 literal の統合時照合は親の裁定に残る。 |
| RB4 | **closed（裁定された範囲）** | 手書きの対照本文は実物 file の読込みに置き換わった（[同:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:137)）。compile 処理の重複は裁定どおり残る。 |

## 新しい所見

- **should-fix・一次資料の記述:** RA1 を「`foo` build は STOCK identity で記録」と説明すると、前処理失敗による停止を誤記する。上記 [source_digest.py:1686](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/source_digest.py:1686) の挙動に合わせて書き直す必要がある。成果物のコードへの影響は確認されない。
- **should-fix・所要時間の記述:** 指定された [result.json:439](/work/1/SFC/tanab/tmp/lock-order-2026-09-30/runs/live-2/result.json:439) の合計は **75.875 秒**であり、`7 s + 81 s` の両項はこの原データから照合できない。88 秒をこの結果の実測合計として記載しないこと。

fix commit に限れば、repo 外参照、揮発値の焼き込み、期待値の恒真化は見当たらない。追加した受理テストは `finally` で共有 fixture の source を復元する（[test_silo_lock_order_template.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:160)）。拒否テストは source 不変を直接検査する。静的検査のみで、テストは実行していない。

## 生死確認と派生値

`multi_write_non_stock_key_order` は、committed trace の UPDATE のみ・複数 write の取引について、W 行の key 列が key 順と異なる件数と読める。計数器はその条件を明示している（[launch_lock_order_liveness.py:88](/work/1/SFC/tanab/tmp/lock-order-2026-09-30/launch_lock_order_liveness.py:88)）。`writePhase` は `write_set_` 順に W 行を出し（[transaction.cc:611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/external/ccbench/cc/silo/transaction.cc:611)）、`lockWriteSet` も同順に施錠する（[同:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/external/ccbench/cc/silo/transaction.cc:155)）。これは**施錠順の観測**であり、`order_enabled` の呼出件数そのものではない。

| run | 原データによる計算 | 発火率 |
|---|---:|---:|
| W-blind | 98,433 ÷ 251,307 | **39.1684%** |
| W-rmw | 77,538 ÷ 197,620 | **39.2359%** |

両 build の configure/build は rc=0、両 verifier は rc=0、symbol check は passed（[result.json](/work/1/SFC/tanab/tmp/lock-order-2026-09-30/runs/live-2/result.json:241)）。判定器 JSON の `certified: true` は**その 1 回の判定器結果**として読めるが、結果自身の note は D1・D2 照合による certified ではないと明記している（[同:251](/work/1/SFC/tanab/tmp/lock-order-2026-09-30/runs/live-2/result.json:251)）。一次資料で後者の認証根拠へ格上げする余地はない。

## 総括

**NO-GO（予定された一次資料の記述に対して）。** fix 後のコードに新たな blocking 欠陥は見つからない。RA1 の STOCK identity 説明と `7 s + 81 s` の実測根拠を訂正すれば、コード側は GO と判断する。