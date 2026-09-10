# T-1933 受入最長nodeのprocess-cache仮説をpaired K=3で反証した

- authority: none
- default_effect: no-state-change
- wave: `worktree-dev-wave-acceptance-fastest`
- 最終net implementation diff: 0 byte（対象2fileはtested main `dcf9224a`とbytes一致）

本書は可変状態の正本ではない。タスク状態はworklog、設計判断はdecisionsを正本とする。

## 結論

T-080 stub-free E2Eのdefault cache keyを共有する3関数/6 nodeを既存`real-repo` loadgroupへ寄せる案は、実際に同一worker化とcache共有を成立させたが、full K=3 acceptance wallを短くしなかったため不採用にした。

pre中央値244.810秒、post中央値245.707秒、差+0.897秒/+0.37%。D357の10%未満は改善にも退行にも数えないため、分類は**変化なし**である。実装commit `2ffb32a0e`はremoval commit `1bafd884a`でtested mainのbytesへ戻した。改善を主張しない。

## 対象を11 nodeから6 nodeへ縮めた理由

最初のplanはhelper direct consumer 6関数/11 nodeをまとめた。敵対実効性レンズは、single-use key 4 nodeがcache hitを増やさず178 ledger秒相当をcritical unitへ足すと指摘した。そこでdefault keyを共有する次の3関数/6 nodeだけへ縮小した。

- `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5`（4 node）
- `test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5`（1 node）
- `test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28`（1 node）

新group、新cache、param-aware selector、K>3、allocator変更、skip/deselect/timeout緩和は採らなかった。

## 生死確認と焦点実測

実装前に現行helperを1 workerで実走し、6 passed/76.03秒（request `954341.nqsv`）だった。実装後は`-n2 --dist loadgroup`で6 passed/75.77秒（request `954356.nqsv`）。worker数を2へ増やしてもwallが同じなので、対象6 nodeの同一runtime unit化は成立した。

変更test fileはfix前56 passed/1 skipped/41.66秒、冗長golden 14行の削除後56 passed/1 skipped/42.22秒。skip 1件は既裁定のexplicit-user-command-only growth holdである。

## full K=3 paired結果

両armはexact 18,598 items、18,536 passed/62 skipped、全shardでselected=finished、effective scheduler=`loadgroup`、赤0。queue待ちはmetricへ含めず、各JUnitのsession timeだけを使った。

| arm | fixed commit | run 1 | run 2 | run 3 | median |
|---|---|---:|---:|---:|---:|
| pre | `dcf9224a` | 244.810 | 241.432 | 284.232 | **244.810** |
| post | `2aa85c45` | 252.175 | 239.061 | 245.707 | **245.707** |

逐次値と全3 shard値は`paired-runs.json`。post run 1は通常waiterのauthoritative receipt v5で`child-green`、tested main=`dcf9224a`、tested tip=`2aa85c45`。run 2/3とpre 3走はfixed tipを保つ性能対照なのでdirect `run_tests.py --force-dispatch`を使い、land authorityとは扱わない。

## なぜworker duration総和を採用理由にしないか

shard-0のworker duration総和中央値はpre 6456秒、post 4864秒へ下がった。しかし同じ48-core nodeを同じ約245秒だけ占有し、D357は共走競合を含むnode秒を仕事量代理に使えないと定める。wall短縮もnode-hour削減も成立しないため、この値だけで配線を残さない。

## 変異とレビュー

実装commit `2ffb32a0e`に対しbaseline PASSED、production member、process-memo合成、独立goldenの3変異は全てKILLED。期待失敗node完全一致、SURVIVED/MISMATCH/TIMEOUT 0、使い捨てworktree復元済み。これは案が正しく配線された証拠であって、案が速い証拠ではない。

段2 planは初回model-call上限で出力前停止し、r2を再実行した。read-only plan 1、敵対consult 2、author 1、review 2、minimality fix/focus 2、paired反証後のremoval fix/focus 2がaccepted。golden側の冗長14行はfull測定前に削除し、最終的にno-effect配線全体も削除した。

## job分割との関係

現行K=3でcount均等でもshard-0が律速なのはrealである。ただしduration重み割付はD1019が「完璧な予言者でもcritical chainを動かせず利得0.0秒」と既に不採用にしている。今回も対象fileを含むconflict componentは同一shard必須で、jobを増やしても固定成分を分けられない。既裁定を再実装しない。

次はT-1933の目的どおり、full artifact上のcritical workerで実際にwallを決める単体処理そのものを短くする。process-local cacheやallocator一般化を先に増やさない。

## 実行上の非成果

- 最初のplan childは`max_model_calls=12`で出力前停止。成果物不採用、r2をfresh再実行。
- author/fix sandbox内のdispatchはsocket作成拒否で`child_started=false/rc=16`。親の同一runner経路は計算ノードで成功し、実装赤には数えていない。
- acceptance waiterの直起動はpermission `rc=126`、次はlease-dir省略でclaim前`rc=2`。どちらもmerge/test/receipt前で、正規python入口+canonical lease-dirへ是正した。

## 証拠索引

- `paired-runs.json`: 3×3 paired値
- `mutation-spec.json` / `mutation-report.json` / `mutation-wrapper-receipt.json`
- `acceptance-receipt.json`: post run 1のauthoritative receipt
- repo外逐語・worker receipts: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-acceptance-fastest/`
