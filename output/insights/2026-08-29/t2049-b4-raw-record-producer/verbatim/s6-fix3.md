## 赤 3 件の原因と対応

### 1-a. 正例 2 件

原因は evidence bytes の破損ではありませんでした。

`_evidence_scope` 終了後に receipt を検証するため、既存 verifier が参照する campaign layout の fixture patch が解除されていました。その結果、verifier が別の campaign root を解決し、identity 検査で `B4PayloadSchemaError` になっていました。

[p3_b4_raw_record_producer.py:719](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/campaign/p3_b4_raw_record_producer.py:719) で verifier に request の campaign root を束縛し、receipt の `campaign_id` と root leaf も照合しました。role、executable、projection は従来どおり同じ no-follow snapshot bytes を使用します。

### 1-b. M05

判定は test 側の誤りです。production 回帰ではありません。

- on/off は [p3_b4_raw_record_producer.py:1056](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/campaign/p3_b4_raw_record_producer.py:1056) で別々に snapshot されています。
- 各 arm 内では同じ `lock_snapshot.data` が classification と COMMIT receipt hash に渡されています。
- 旧 test は bytes を保持せず `id()` だけ保存したため、on の bytes 解放後に off で同じ address が再利用されました。

[p3_b4_raw_record_producer.py:654](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/tests/test_p3_b4_raw_record_producer.py:654) を、bytes object 自体を保持して `is` で検査する形へ変更しました。同一 arm 内の同一性と、on/off 間の非同一性を両方要求します。

## production 差し替えの除去

`mock.patch.object(C, "projection_sha256", ...)` と関連 cache helper を全箇所から除去しました。201 block 正例は本物の `projection_sha256` を通ります。

許容された `REPOSITORY_ROOT` と `ROLE_FILE` の fixture 配線は維持しています。

## cProfile の実測

`/tmp/profile_b4_evidence_scope.py` に `_evidence_scope` を1回だけ実行する cProfile script を作成しました。

ただし次の2回とも scheduler preflight で停止しました。

- 通常 runner: `rc=16`, `child_started=false`
- `--force-dispatch`: `rc=16`, `child_started=false`
- scheduler 診断: `qstat -Q` が `Unknown user-id`
- profile sample: 0

したがって、上位20関数と累積時間は取得できていません。数字は推測で補っていません。

## テスト時間

変更前の親実測:

- file 全体: 451.33秒
- certified 正例: 447.33秒
- terminal-absent 正例: 447.24秒

変更後は runner が child を開始できず、wall time を測定できませんでした。120秒以下かは未確認です。

編集可能面で畳んだ計算は admission verification です。[test fixture:340](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/tests/test_p3_b4_raw_record_producer.py:340) で cache 配線を `_production_launch_context` より前へ移しました。これまで両正例とも、同じ admission に対する実 verifier を最初の2 context × 201 block、計402回繰り返していました。現在は exact `(record_path, repository_root)` ごとに実 verifier を1回だけ実行します。削減秒数は profile 未実走のため申告しません。

残る実処理は次です。

- 本物の projection 計算: [p3_b4_closed_critic.py:877](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/campaign/p3_b4_closed_critic.py:877)、[p3_b4_closed_critic.py:1157](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/campaign/p3_b4_closed_critic.py:1157)
- receipt 全検証: [p3_b4_closed_critic.py:1436](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/campaign/p3_b4_closed_critic.py:1436)
- A が要求する assembly 時の再導出: [p3_b4_raw_record_producer.py:1928](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/campaign/p3_b4_raw_record_producer.py:1928)

これらの時間内訳も profile 未実走のため未計測です。

## 実走した検査

動的 test は実走できませんでした。

- 赤3 node 合同走: `rc=16`, `child_started=false`
- 対象 file 全29 node: `rc=16`, `child_started=false`
- 内訳: 0 green / 0 red / 29未実行
- cProfile 2試行: いずれも child 未起動

実行できた静的検査:

- 2 file の AST parse: 成功
- production/test module import: 成功
- 公開 API に judgment field がないこと: 成功
- M01〜M18 が18個の一意 nodeへ対応: 成功
- projection 差し替えが残っていないこと: 成功
- self-run harness の存続: 成功
- 結合文字不在: 成功
- repo 差分: 指定2 fileのみ
- commit、add、stash、branch操作: 未実施

runner が生成した今回分の `output/pegasus-dispatch` 診断 directory は、各試行後に完全指定で除去しました。

## A〜H の後退がないことの確認

静的確認では次を維持しています。

- A: assembly の全 source 再導出と recorded bytes 完全一致検査
- B: checkpoint 未追従、lock 後 WAL 変化の deferred
- C: 4種類の赤詳細 entry 実体判定
- D: 終端試行の `evidence_issues` 記録と行の保持
- E: manifest、campaign、receipt の driver 照合
- F: role、executable、projection closure の no-follow snapshot
- G: M01〜M18 の一意対応と M10 逆向き負例
- H: batch/assembly 内の invariant snapshot cacheと、fixture admission verification の一回化

動的回帰確認は scheduler 障害により未完了です。

## 総括

赤3件へのコード対応、projection 差し替え除去、同一 admission の402回反復除去を指定2 file内で実施しました。M05 は production 回帰ではなく `id()` 再利用による test 誤判定です。

ただし scheduler が child を起動できず、cProfile 上位20、変更後時間、29 node の緑は確認できていません。現状は「実装修正済み、静的検査成功、動的検査と120秒目標は未確認」です。