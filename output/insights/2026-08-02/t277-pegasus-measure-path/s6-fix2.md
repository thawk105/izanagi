実装を完了しました。コード・テストのみ編集し、docs 編集・commit はしていません。

## F1〜F10 対応表

| 所見 | 状態 | 今回の確認 |
|---|---|---|
| F1 | closed | 公開 API の `site` は復活していない。旧 `site=` を残していた5テストを contract 渡しへ追随 |
| F2 | closed | authoritative `campaign_id` / `layout_root` 経路は不変 |
| F3 | closed | 8c の COMPUTE build 拒否は不変 |
| F4 | closed（方式変更） | `run_campaign` 一括拒否から、実 build／trace subprocess sink の拒否へ移動 |
| F5 | closed | dependency prefix identity は変更なし |
| F6 | closed | explicit contract の照合・attestation・receipt は `run_campaign` に維持 |
| F7 | closed | no-resume の書込み前検査は不変。入口停止テストを OTHER fixture に分離 |
| F8 | closed | `env_tag=contract.env_tag` anchor は変更なし |
| F9 | closed | 8c CLI の事前拒否順序は変更なし |
| F10 | closed | fresh build と cache hit の behavioral 負例を追加。既存 golden／M14 sink 検査は維持 |

状態が変わった所見はありません。F4 だけ実装位置を変更しました。

## 赤21件の内訳

親の実測ログを直接確認したところ、依頼文の「全件が `test_campaign.py` の loop 系」とは異なりました。

- 13件: `run_campaign` の過広な入口拒否
- 1件: `screening_driver` の同型の入口拒否
- 5件: F1 で削除した private helper の `site=` をテストが渡し続けていた
- 1件: no-resume 対象外の入口停止テストが実 COMPUTE site を拾った
- 1件: LOGIN/SUSPECT gate テストが実 COMPUTE 防壁に先取りされた

後半7件も個別に fixture／caller を修正しました。

## 採った方針

方針 (a) の sink 寄せを採用しました。

- [loop.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/loop.py:54): legacy の配線確認は入口で拒否しない
- [buildcache.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/buildcache.py:852): fresh legacy build を実 CMake subprocess の直前で拒否
- [pipeline.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/campaign/pipeline.py:208): cache hit 後も実 trace subprocess の直前で拒否

これはテスト用の逃げ道ではありません。環境変数、`if TESTING`、fixture 名判定はなく、「実 subprocess sink に到達したか」だけで分岐します。

[test_campaign.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t277-pegasus-measure/orchestrator/tests/test_campaign.py:2695) には以下を固定しました。

- fake evaluator の配線確認は COMPUTE でも通る正例
- fresh legacy build は subprocess poison に未到達
- legacy cache hit も trace／bench subprocess poison に未到達

各負例は対応する sink 防壁を削ると poison 呼出しが観測されるため、恒真ではありません。

## 検査結果

計算ノード dispatch を2回試みましたが、いずれも以下で停止しました。

```text
Pegasus dispatch infrastructure failure: qstat -Q preflight rc=1
runner rc=16
```

実走 nodeid は0件です。pytest 緑は主張しません。試行した selector は次です。

- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py`
- `orchestrator/tests/test_build_site_gate.py`
- `orchestrator/tests/test_buildcache_v2.py`

通過した静的検査:

- 全変更 Python の `python3 -m py_compile`
- `git diff --check`
- `python3 tools/check_codex_agents.py`
- `python3 tools/check_docs.py`

## OTHER と所有外への波及

OTHER では sink の actual-site 検査が no-op となり、subprocess argv・env・campaign identity・WAL値は変更されません。静的確認上、1 bit の変更もありません。

波及可能性は次のとおりです。

- private `buildcache._run` の v2 monkeypatch は新しい `env_contract=` keyword の受理が必要
- private `pipeline._run_trace` には optional `env_contract` が追加された
- COMPUTE legacy campaign は layout／拒否 WALを残す可能性があるが、build・trace・bench subprocessは起動しない
- `screening_driver` の terminal skip／fake evaluator は COMPUTEでも処理できるが、実評価は共通 sink で拒否される
- 兄弟 raw driver の個別 COMPUTE 防壁は変更していない
- `/scr`、claim、reservation、lease、8c COMPUTE運転、依存bytes content hashは実装していない

## 総括

- 過広な campaign 入口防壁を実測 subprocess sink へ移しました。
- fresh build と cache-hit trace の双方で legacy COMPUTE 実測を拒否します。
- 一次ログで判明した別原因7件も個別に修正しました。
- F1〜F10 は静的にはすべて closed を維持しています。
- 静的検査は通過しましたが、pytestはscheduler preflight障害で未実走です。