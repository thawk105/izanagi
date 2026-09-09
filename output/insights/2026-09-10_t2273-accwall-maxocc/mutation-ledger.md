# 変異台帳 — dev-wave-t2273-accwall-maxocc

- 対象 commit: `fa733057de473d9dd440046821486f2d29828d4f`
- harness: `tools/mutation_harness.py` (`--runner-mode dispatch --detached`)
- runner argv: `python3 tools/run_tests.py orchestrator/tests/test_p3_b4_material_report.py orchestrator/tests/test_p3_b4_raw_record_producer.py -rf`
- spec (4 件版) sha256: `090c4648d6ab25e9a4db4ec20c5580ecac8eca39774d497c8fdc5b75c6e8a4fc`
- **baseline は全走 rc=0 (緑)。**

## 走らせた 4 件

| id | 変異 | anchor 一致数 | rc | 観測 | 注入 diff sha256 |
|---|---|---|---|---|---|
| `MUT-T2273-M1-SIDECAR-HASH` | replay が書く sidecar の `launch_context_sha256` を `"0"*64` へ差し替える | 1 | **1** | errors=35 / failed=0 | `68dc9c3456f215d99524c747c8b1d0d863be93855ff674177ee2dab78306edf9` |
| `MUT-T2273-M2B-ATTEMPT-REPLAY-SKIPPED` | replay 分岐が `_append_replayed_attempt_with_writer` を呼ばない (sidecar だけ書く) | 1 | **1** | errors=35 / failed=0 | `a92f7068561580da18525abeb2a752419a8f6a7603bf59588313086179dd4a0a` |
| `MUT-T2273-M4-GENERIC-SELECTS-REPLAY` | `replay_non_commit_sidecar` の既定を `True` にして generic clone も replay させる | 1 | **1** | errors=1 / failed=0 | `667d0a80bde4e64221e278242f0311e90e3ed32fe396336796db9c24a245e590` |
| `MUT-T2273-M5-SIDECAR-NOT-WRITTEN` | replay 分岐が sidecar を書かない | 1 | **1** | errors=35 / failed=0 | `d7e662e3006069f4fa150996a620c1a10ea45709ebb1098afc64750a9cd108e5` |

- 4 件とも **anchor は file 内で一意** (`anchor_counts = {"0": 1}`)、注入 diff はすべて相異なる。
  注入が実在したことは diff digest で確認した。
- M4 の `errors=1` は段 3 レンズ A の予測と一致する。generic を replay にすると
  COMMIT fixture (`certified_publication_evidence`) が
  `live_commit_receipt is not None` guard で落ちる一方、absent fixture は
  copy された sidecar が seed と一致するため通る。

## 走らせる前に撤回した 2 件 (DW-M01 / F28 の再照準)

段 3 レンズ A と段 6 レビュー A が独立に SURVIVED と判定したため、登録から外した。
初回の判定は消さずここに残す (DW-M02)。

| 撤回した id | 変異 | SURVIVED の理由 |
|---|---|---|
| M2 (旧) | pair_id 生成式の `iteration` を固定値にする | exact oracle は start / terminal receipt と consumption の pair_id を placeholder へ正規化し、replica 相互の pair_id を比較しない。production の batch 一意性も `(campaign_id, iteration, arm)` だけで pair_id を含まない |
| M3 (旧) | `live_commit_receipt is None` guard を外す | material の唯一の replay 呼び出しが常に `live_commit_receipt=None` かつ non-COMMIT なので、単独削除は観測できない。矛盾入力を作っても残るもう 1 つの guard か `_append_replayed_attempt_with_writer` 内の stage/receipt assertion が拒否する |

この 2 つの guard は **現行 caller が踏まない fail-closed assertion** である。
保護として数えず、恒真な保証として謳わない。

## harness の制約 (本 wave で実測)

4 件の kill はいずれも **module / function scope fixture 由来の pytest ERROR** として出る。
`tools/mutation_harness.py` の `_failed_nodes` は `FAILED ` で始まる行だけを解析し、
`_observed_status` は `rc != 0 and not failed` を `PARSE_ERROR` と判定する。
したがってこの harness は **oracle が fixture の中にある変更の kill を `KILLED` として記録できない。**

本 wave の oracle (`_assert_replicas_match_real_except_identity`) は module scope fixture
`immutable_publication` の中で呼ばれるため、この経路は避けられない。
検出そのものは **baseline 緑 (rc=0) からの rc=1 と `errors=N`** で確定している。
`expected_status` を `KILLED` としたまま `status` は `PARSE_ERROR` と記録された。
これは実装の欠陥ではなく harness の解析契約の射程外である。
