# fix Unit E 報告

## 1. F-E1 の是正内容と、漏洩走査の実測結果（rr80 / rr20 の conjunction_hits）

[test_ccbench_spawn_sites.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_ccbench_spawn_sites.py:318) の合成 workload から `ycsb_zipf_skew` と `ycsb_rmw` を除去し、保護比率だけを渡す形にしました。他ファイルへの三軸移動はありません。

指定 API による実測結果は次のとおりです。

```text
files_scanned = 12661
rr80: conjunction_hits = []
rr20: conjunction_hits = []
```

## 2. F-E1 で検出力を落としていない根拠

- `ratio` のパラメータ値 `20`、`80` は変更していません。
- `backoff_profile.profile_point()` は比率だけでも `assert_holdout_observation_admitted()` を呼び、保護比率を build 前に拒否します。
- `_genome` が呼ばれていないことを確認する既存の `assert effects == []` は維持しています。
- テスト名、期待例外、期待値は変更していません。

## 3. F-E2 でどちらを採ったか（claim 移動 / docstring 是正）と理由

[s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:4227) の docstring 是正を採りました。

`_validate_live_admissions()` が検査する holdout capability は claim と ledger の確定後に発行されます。claim を検査後へ移すには admission authority の段階分割が必要となり、限定 fix の範囲を超えるためです。

実体どおり、次を明記しました。

- `runner.run()` 外側の preflight と manifest sealing は claim 前
- live admission 再検査、host provenance、process identity、session competition probe は claim 後

隣接する英語コメントも同じ射程へ合わせました。

## 4. 実走したテスト（nodeid・範囲・結果） / 実走できなかったもの

実装済み・pytest 未実走です。

試行した範囲:

```text
orchestrator/tests/test_ccbench_spawn_sites.py
orchestrator/tests/test_s8b_floor_campaign.py
```

`--force-dispatch`、自動資源判定、spawn-site 単独の全試行が、テスト開始前に次の基盤障害で終了しました。

```text
rc=16
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
```

直接 pytest への迂回は行っていません。補助検査は次のとおりです。

- 変更 2 ファイルの AST parse: 成功
- `git diff --check`: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 成功

## 5. 所有外への波及可能性

- F-E1 の production caller は `backoff_profile.profile_point()` です。入力から不要な二軸を除いただけで、production コードへの変更はありません。
- F-E1 の fixture は当該テスト関数内だけで、共有 fixture への波及はありません。
- テスト名と parametrized nodeid は維持されるため、nodeid を参照する harness への変更はありません。
- F-E2 の consumer は `run_campaign()`、CLI、`test_s8b_floor_campaign.py`、`test_s8b_freeze_io.py` です。docstring とコメントだけの変更で実行経路、受理集合、成果物に波及しません。

## 6. 気づいたが直していない点（報告のみ）

新規の範囲外問題は見つけていません。親裁定で scope 外とされた N1、N2、N3、N5、および `test_s8b_freeze_io.py` の合成 fixture は変更していません。

F-E2 は説明の誇張のみを閉じたため、claim 後の検査失敗で一回性 key が消費される実挙動自体は残ります。

## 総括

F-E1 の三軸同居を解消し、12,661 files の走査で rr80、rr20 とも 0 hit を確認しました。  
保護比率 20、80 の拒否と build 前拒否の期待値は維持しています。  
F-E2 は限定範囲を守り、実体に一致する docstring とコメントへ是正しました。  
pytest は dispatch 基盤障害により未実走であり、緑は主張しません。  
変更は指定された 2 ファイルだけで、docs 編集と commit は行っていません。