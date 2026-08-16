## 対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| 欠陥1: runtime record を portable exact-key gateへ直接投入 | partial | runtime exact-key判定後、runtime専用keyを除いた射影だけをcentral validatorへ投入。手動smokeは4/4成功、pytestはinfra障害で未実走 |
| 欠陥2: `_fixed_prepare` が存在しない `configuration_id` を参照 | partial | `configuration`から判定するよう修正。sort/non-sort手動smokeは2/2成功、pytest未実走 |
| inspectorへreservation用cell射影を渡す形状不一致 | partial | inspectorには`holdout_id`を持つ元cellを渡し、reservationだけ`freeze_holdout_key`射影を維持 |
| legacy manifest fixtureのCCBench pin不一致 | partial | receiptと同じ固定pinへ修正。対象関数の直接smoke成功 |
| ratified正常系assertionの不一致テスト内への誤配置 | partial | assertion値は変更せず正常系テストへ戻した。pytest未実走 |
| regressed | 0件観測 | 構文・NFC検査と手動smokeは成功。ただしpytest全走不能のため回帰なしとは確定していない |

## 直した内容

- [s8b_floor_campaign.py:4274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:4274)
  - fresh runtimeとresume由来resolved runtimeのexact集合を明示。
  - 余分key、sort receipt欠落、非sortのFetchContent baseを拒否。
  - runtime専用keyだけを除き、portable central validatorのreceipt・identity検査を維持。
- [s8b_floor_campaign.py:5383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5383)、[同:5527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/campaign/s8b_floor_campaign.py:5527)
  - finalize-pending、通常finalize、live自己検査へ元のfloor cell列を渡すよう修正。
- [test_s8b_ratified_freeze.py:403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_freeze.py:403)
  - `_fixed_prepare`を`cell["configuration"]`へ修正。
- [test_s8b_floor_campaign.py:516](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_campaign.py:516)
  - test live inspectorにも元cell列を使用。
- [test_s8b_floor_campaign.py:3396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_campaign.py:3396)
  - legacy fixtureのpinをreceiptの固定pinへ一致。
- [test_s8b_floor_campaign.py:7039](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_floor_campaign.py:7039)
  - fresh/resolved runtime正例2件、余分key・sort receipt欠落の拒否2件を追加。
- [test_s8b_ratified_verify.py:787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1155-t1178-floor-receipt/orchestrator/tests/test_s8b_ratified_verify.py:787)
  - `lv`/`topology` assertionを本来の正常系へ戻した。期待値自体は不変更。

## 実走結果

- `python3 -m pytest orchestrator/tests/test_s8b_ratified_verify.py -q -rf -p no:randomly`
  - 実行防壁によりpytest起動前に拒否。nodeid実走0件。
- `python3 tools/run_tests.py orchestrator/tests/test_s8b_ratified_verify.py -q -rf -p no:randomly`
  - rc=16、`qstat -Q preflight rc=1`。nodeid実走0件。
- 新規runtime nodeidを対象にした`tools/run_tests.py ... -k 'live_admission_accepts_both_exact_runtime_views or live_admission_runtime_exact_keys_fail_closed'`
  - rc=16。緑・赤とも未測定。
- 指定13ファイルすべてを列挙した最終`tools/run_tests.py ... -q -rf -p no:randomly`
  - rc=16。13ファイルすべて未実走。
- `python3 -m py_compile`による変更4ファイル検査
  - rc=0。
- git・build・計測を伴わないhere-doc手動smoke
  - `test_legacy_resume_manifest_without_perf_preflight_is_not_backfilled`
  - runtime fresh/resolved正例2件
  - runtime余分key/sort receipt欠落拒否2件
  - `_fixed_prepare`のsort/non-sort 2件
  - 合計7件成功、赤0件。
- NFC・結合文字検査
  - 変更4ファイル成功。

## 残赤

修正後のpytest残赤nodeidは判定不能です。直接pytestは環境防壁、wrapperは`qstat`障害で、いずれもnodeid実行前に停止しました。

親ログに存在した既知2原因以外の例外型は、inspector cell形状、legacy pin不一致、`lv`未定義の3件で、すべて修正しました。ただし修正後の192件再測定がないため、全緑とは申告しません。

## 受理集合

受理集合は緩めていません。

- runtime recordはportableまたはruntimeのいずれかのexact集合に完全一致しなければ拒否されます。
- 余分keyは`runtime binary record ... exact key 集合が不一致`で拒否されます。
- sort receipt欠落もsort用exact集合不一致で拒否されます。
- exact集合通過後も`validate_portable_binary_record`がreceipt、identity、binary SHA、contract、CCBench pinを検査します。
- 非sort recordの`_fetchcontent_base_dir`は引き続き明示拒否です。

docs、`freeze_verification_hold.py`、`output/`、git、commitには触れていません。

## 総括

全緑か否か: **未確認**。pytestは全走・焦点走とも実行基盤障害で0 nodeid実走です。

残赤: 件数不明。親ログで確認できた全失敗型は修正し、構文検査と手動smoke 7件は成功しました。

受理集合: runtime exact-key gateとportable central validatorを直列に維持し、余分key・sort receipt欠落の拒否controlを追加しています。