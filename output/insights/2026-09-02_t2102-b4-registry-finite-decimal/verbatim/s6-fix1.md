## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| M12 第2段の実効発火未確認、および正例対照の欠落 | partial（実装済み・未実走） | 独立 root の正常 publication を `_assert_write` で確認する対照を復元。mock を保持し、manifest row の `reference_tps` による1回の呼出しを固定。既存の直接検査と issue 全項目の期待値は維持。pytest は環境制約で開始できていないため closed とはしない。 |

## 変更した file と行

- [orchestrator/tests/test_p3_b4_raw_record_producer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2102-fix1/orchestrator/tests/test_p3_b4_raw_record_producer.py:1147)

  - 1147–1148: `tmp_path / "control"` への正常 publication と `_assert_write` を追加。
  - 1157–1161: mock を `fraction_token` として保持し、`assert_called_once_with(publication.manifest.rows[0].reference_tps)` を追加。
  - 第1段および artifact / field / code / detail の期待値は変更なし。

最終差分はこの1 fileのみです。commit、index、docs、production、`output/` への変更は残していません。`git diff --check` は緑です。

## 実走した検査

指定コマンドを2回起動しました。

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_raw_record_producer.py -p no:randomly -q
```

- 対象範囲: `orchestrator/tests/test_p3_b4_raw_record_producer.py` 全 node
- 実際に開始した nodeid: なし
- 緑: 0
- 赤: 0
- 結果: いずれも `rc=16`。pytest child の開始前に `qstat -Q` preflight が socket 作成不可で失敗しました。
- local fallback: user slice の空きが記録済み peak に基づく bounded budget を安定して満たさず、ランナーが compute dispatch を選択しました。

したがって、指定テストは実装済み・未実走です。

## 波及可能性

- Production caller: `_derive_b4_attempt_data` の `_fraction_token(row.reference_tps)` が今回の assertion 対象です。呼出しを直接 `raise ArithmeticError` に置換する変異は mock 未呼出しとなり、M12 が赤になります。
- 別 caller: final assembly にも `_fraction_token` 呼出しがありますが、今回の patch 範囲外で挙動変更はありません。
- 共有 fixture: `certified_evidence` を同一 test 内で2回読むため実行時間は増えますが、publication と result の root は `control` と `publication-case` に分離されています。
- 共有 helper: `_publication`、`_publish`、`_assert_write` 自体は未変更なので、他 consumer test の契約は変わりません。
- Mutation consumer: node 名と `MUTATION_NODE_IDS["M12"]` は維持されています。

## 残る不確実性

pytest child が開始できなかったため、正例 publication の実書込み、mock の実呼出し回数、既存全 node の回帰有無は動的には未確認です。静的には production の対象 publish 経路で `_fraction_token` は1回呼ばれ、`ArithmeticError` 後は rejection に巻き戻る構造です。

## 総括

must-fix の正例対照と mock 実効発火 assertion を追加しました。
既存の第1段と issue 全項目の固定は維持しています。
変更は指定されたテストファイル1件だけです。
指定テストは環境上の dispatch 障害により未実走のため、判定は partial です。