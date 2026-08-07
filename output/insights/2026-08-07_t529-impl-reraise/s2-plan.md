# 判定

**NO。現時点で land 可能な実装部分集合は存在しない。**

ただし、親が見落としている重要事実がある。`DW-G04` を満たし得る**正規 g2 の実在素材は既にある**。したがって「発火証拠がない」という保留理由は再実測対象だが、D215 の独立した入口面 blocker が残るため、今 wave で活性化権限を部分実装することはできない。

## 見落とされていた実在 g2 候補

Pegasus の publish 済み較正が実在する。

- [calibration-94a4…json:1568](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1568>) は `clocks_per_us=2100`、`env_tag=pegasus`。
- 同 artifact は [quality.status:1599](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1599>) が `accepted`、[schema_version:1637](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1637>) が `calibration/v2`。
- [publish.json:1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/attempts/0_892707.nqsv/publish.json:1>) は同ファイルへの publish を記録し、[job-result.json:1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/job-staging/0:892707.nqsv/job-result.json:1>) は計測 ID `892707.nqsv` と `calibrate_rc=0` を持つ。
- [published-self-comparison.json:1](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/attempts/0_892707.nqsv/published-self-comparison.json:1>) は content SHA `94a4…5a9` と `passed=true` を記録する。

現行 Pegasus g1 の [calibration_ref:265](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:265>) をこの path/SHA 対だけへ差し替えた契約は、変更可能 leaf をこの二つだけに限定する [is_valid_successor:202](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:202>) の正規後継になる。現在の admission も、path・bytes SHA・schema・env・clock・policy を [load_verified_calibration:1060](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:1060>) で検査し、別の final receipt は読んでいない。

したがって、`94a4…json` / job `892707.nqsv` を使う実 source g2 は、temp commit や module 属性 patch ではない発火正例候補である。親 brief の「正規 g2 が無い」という前提は再検証が必要である。

## それでも実装部分集合が存在しない理由

場合分けすると閉じる。

1. **g2 を production registry に追加しない場合**

   `GENERATIONS` は [linux-baremetal g1:237](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:237>) と [Pegasus g1:256](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:256>) の各一本だけで、historical index もその全 entry だけから作られる（[329](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:329>)）。この状態では A(b) を足しても受理する二つの g1 hash は変わらず、ever-active 検査を無視する実装と区別できない。

2. **実在 94a4 を g2 として追加する場合**

   module 初期化は [validate_generations:344](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:344>) を必ず通り、二世代列は [bootstrap fuse:316](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:316>) で拒否される。これを外すには activation record と receipt を production に結線する必要がある。

   しかし D215 は、Python 入口だけを部分実装する案を明示的に却下している（[docs/decisions.md:10160](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10160>)、[10171](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10171>)）。現状も floor は Python 起動前に stdout/stderr/marker を書き（[floor_campaign.sh:880](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/floor_campaign.sh:880>)）、T-126 は source-stage evidence を書いた後で driver を起動する（[t126_qualification.sh:719](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/t126_qualification.sh:719>)、[735](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/t126_qualification.sh:735>)）。

   C(a) はこの欠陥を別タスクへ送っただけで、コード上は閉じていない。したがって D215 の残存条件を満たさない。

## (P2) の精査

現在の「registry hash 集合 = current hash 集合」という狭い等式は正しい。一方、そこから「発火正例素材も存在しない」とする一般化は誤りで、上記 94a4/job 892707 が反例である。

また A(b) を将来実装する際は、一箇所だけ直してはならない。

- freeze 再検証は [_resolve_historical_contract_sha256:2783](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:2783>) を [reverify_published_freeze:3244](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:3244>) から使う。
- oracle observations は別途 [s8b_oracle_report.py:1640](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_report.py:1640>) で `env_contract.resolve_by_contract_sha256` を直接渡している。

共有 ever-active leaf を両経路へ配線しなければ、legacy/report 側に迂回が残る。

## A〜E と D215 の対応

| 裁定 | 解消するもの | 今日残るもの |
|---|---|---|
| A(b) | D215 の未裁定 R1（[10164](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:10164>)） | 実装・consumer 配線は未実施 |
| B(a) | `DW-G04` を上書きしない | 94a4/job 892707 により「実在正例なし」は反証候補。ただし親の実測確認が必要 |
| C(a) | shell 側を certified-writer 閉包タスクへ帰属 | floor/T-126 の pre-write は現存し、D215 は未解除 |
| D | skip/downgrade/no-op を防ぐ遷移規則 | 発火・入口被覆の blocker には効かない |
| E | 循環 import と CLI 前 root 不明を解消する設計 | `env_attestation → env_contract` の現行 import（[env_attestation.py:22](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:22>)）は要改修だが、shell pre-write には効かない |

したがって P1 の「発火正例が無い」という理由は崩れ得るが、「本 wave ではコード実装できない」という結論は C(a)/D215 により残る。

## [T-607] の境界

(P3) は正しい。freeze の candidate generation と activation は別権限である。

- v2 generation 導入 commit は非 merge・非 `none` の AI trailerを要求するため、AI が発行できる（[_assert_candidate_commit:552](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:552>)、[_collect_records:1092](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:1092>)）。
- approval・active pointer・revocation・cancellation は非 mergeかつ逐語 `AI-Agent: none` を要求する（[_assert_user_commit:537](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:537>)、[approval/pointer load:1104](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:1104>)）。
- live pointer が無ければ [resolve_active_generation:1253](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:1253>) が `no-active` を送出する。
- production report は `reverify_published_freeze` より先に `load_ratified_freeze` を呼ぶ（[s8b_oracle_report.py:1749](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_report.py:1749>)）。

現在の tracked inventory には v2 generation、approval、active pointer がいずれも無い。T-529 の env-contract activation recordを実装しても、これら freeze record は生成されないため、T-607 の `no-active` は解消しない。

テストは実行しておらず、緑は主張しない。

## 総括

1. **実装可能な部分集合は存在するか: NO。** 94a4/job 892707 という正規 g2 候補は実在するが、C(a) で外出しした入口閉包が未実装で、D215 が Python-only 部分実装を禁止している。

2. **誤りは P1 の「発火正例なし」部分と P2 のそこからの一般化。** 根拠は publish 済み 94a4 artifact/job 892707 と `is_valid_successor:202`。P1 の最終結論、P3、P4 は現状では維持される。

3. **親が次に実測すべきこと:** 94a4 を指す prospective Pegasus g2 に対し、`is_valid_successor` と `load_verified_calibration` を実測し、artifact path/job ID を `DW-G04` 正例として確定する。pytest を使う場合は必ず `tools/run_tests.py` 経由とし、その後 T-609 の入口閉包を先行させる。