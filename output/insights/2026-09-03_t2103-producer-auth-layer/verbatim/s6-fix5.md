## 総括

F15〜F17 をすべて closed としました。

- 手書きの producer SHA 定数を全廃しました。
- prereg を v7、shard を v4、comparison を v7 に更新しました。
- 新 producer に合わせ、raw prototype の guard 挿入先を同じ `assemble_b4_raw_analysis` 入口へ再照準しました。
- 期待 matrix、採否規則、201 block、floor=0、fail-closed は変更していません。
- commit、git add、stash、branch 操作、docs 編集は行っていません。
- 変更は許可された範囲内の 3 ファイルです。rogue support は変更不要でした。

## 所見ごとの対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F15 | closed | runtime HEAD を base commit として固定し、`git cat-file blob <base>:<producer-path>` から期待 bytes を取得。候補別 post-prototype SHA を shard と comparison に記録し、読込時にも同じ base blob から再導出して検査します。 |
| F16 | closed | prereg v7 を再発行。producer 固有 SHA の凍結を廃止し、base commit blob、SHA-256、prototype 後かつ rogue 前という解決契約を凍結しました。D1531 の approved prereg と executable registry の完全一致検査は維持しています。 |
| F17 | closed | C0/C1 の全 6 変異で exact old bytes の出現数は 1。停止対象なしです。 |

## anchor の解決元と検出力

測定 base commit は従来どおり実行時の HEAD、今回は `fb79e633e73df3578363de1b96a7213239da85d9` です。

その commit の producer blob から得た anchor は次のとおりです。

- issuer: `6399e5e3b467bfa36cf9e7fe8db64f6e2dbb4268bf8c8a1e515d5024de6e71b0`
- raw assembly: `5da3184e9483a2b444de0115fcd9138ed922d0cbb14277ececf4cc550a0dfa41`
- temporary 6-member prototype: `6399e5e3b467bfa36cf9e7fe8db64f6e2dbb4268bf8c8a1e515d5024de6e71b0`

raw assembly だけは base blob に producer 向け prototype patch を順番に適用してから SHA-256 を計算します。これにより段 4 §2.2 の「prototype 適用後、rogue 変異前」という意味を維持しています。

guard が観測するのは scratch tree の実ファイルまたは closure receipt です。rogue 変異はこれらを変更しても base commit の git blobを変更できないため、期待 SHA との不一致として検出されます。記録済み comparison の検査も現在の作業ツリーや現在の HEAD ではなく、comparison 自身が記録した base commit の blob を参照します。

## 変異 anchor の出現数

| 変異 ID | 出現数 |
|---|---:|
| C0-P | 1 |
| C0-T | 1 |
| C0-C | 1 |
| C1-P | 1 |
| C1-T | 1 |
| C1-C | 1 |

## 6 shard の起動 command

command と combine argv は前巡から変わっていません。

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate issuer --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/issuer-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/issuer-baseline.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate issuer --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/issuer-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/issuer-prototype.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate raw_assembly --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/raw-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/raw-baseline.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate raw_assembly --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/raw-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/raw-prototype.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate temporary_6_member_expanded_closure_prototype --phase baseline \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/frozen-baseline \
  --output /work/1/SFC/tanab/t2103-scratch/shards/frozen-baseline.json

python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py measure-candidate \
  --candidate temporary_6_member_expanded_closure_prototype --phase prototype \
  --scratch-root /work/1/SFC/tanab/t2103-scratch/frozen-prototype \
  --output /work/1/SFC/tanab/t2103-scratch/shards/frozen-prototype.json
```

```bash
python3 orchestrator/tests/test_p3_b4_producer_auth_experiment.py combine \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/issuer-baseline.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/issuer-prototype.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/raw-baseline.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/raw-prototype.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/frozen-baseline.json \
  --shard /work/1/SFC/tanab/t2103-scratch/shards/frozen-prototype.json \
  --output output/insights/2026-09-03_t2103-producer-auth-layer/comparison.json
```

## 実走した node と結果

pytest node の完了はありません。以下の 9 node を `tools/run_tests.py` へ投入しましたが、rc=16、`qstat -Q preflight rc=1`、`child_started=false` でした。

```text
test_each_prototype_patch_anchor_is_unique_and_anchor_is_post_prototype
test_comparison_report_is_canonical_and_has_no_volatile_payload
test_w01_fixed_anchor_accepts_regular_and_rejects_rogue
test_w05_frozen_predicate_is_digest_equality_only
test_w07_every_exact_replacement_requires_one_occurrence
test_w08_preregistration_is_rederived_from_content
test_w09_pos_1_is_accepted_by_every_candidate
test_candidate_shards_require_all_39_pairs_before_decision
test_recorded_anchor_is_checked_against_base_blob_not_worktree
```

補助的な合成検証はすべて通過しました。

- AST parse、prereg canonical 完全一致
- 全 3 prototype の適用と post-prototype anchor 一致
- synthetic 6 shard の serialize、parse、combine
- 39 result、decision 再導出
- 正規 producer の受理、rogue producer の拒否
- 作業ツリー変更後も記録済み base blob 検査が通過
- 記録 anchor 改変の拒否
- `git diff --check`
- U+0300〜U+036F なし

## 従えなかった項目

pytest node と 6 shard 本走は Pegasus dispatch infrastructure failure のため実装済み・未実走です。

この worktree には既存 `comparison.json` がないため、記録済み成果物必須 node も実装済み・未実走です。combine 実行時には新しい anchor field を含む comparison が生成されます。