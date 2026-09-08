## 総括

静的検査では plan は未着手状態に戻すべきです。must-fix は 5 件です。特に、必須 field 化と shape 検査は D1647 の「受理集合には触れない」と正面から矛盾します。

親の ledger 測定と xdist の `start` / `stop` 保存確認は妥当でした。file 編集、commit、pytest 実行は行っていません。

## must-fix

1. **必須 field 化と shape 検査が D1647 の受理集合を変更する。**

   D1647 は gate・判定・受理集合を変えないと明記していますが、plan は `session_timeline` の欠落・型不正・非有限値を `report-invalid` にします。[verbatim-rulings.md](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/verbatim-rulings.md:3)、[plan.md](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:175)、[acceptance_shards.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:618)

   `validate_report_evidence` が 6 gate より前で呼ばれるため、「第 7 gate ではない」という説明では回避できません。さらに plan 自身が、受理する report の形が変わると認めています。[brief.md](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief.md:71)

   同じ `.../v1` を維持する判断も不整合です。旧 14-key v1 を厳密に読む実在 consumer があり、新 report を同じ v1 と称したまま拒否します。[prepare_inputs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/output/insights/2026-08-24_t1618-xdist-controller-cost/prepare_inputs.py:501)

   放置時: 以前受理された v1 report が `report-invalid` へ変わり、新 v1 report は既存 consumer から拒否され、受理集合と schema 参照が変わる。

2. **`collection_finished_epoch_s` の採取位置が collection 終了ではない。**

   acceptance plugin の `pytest_collection_modifyitems` が戻った後、外側 conftest wrapper は suffix 除去と duration LPT 並べ替えを実行します。[conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/conftest.py:2065) plan の時刻はその前であり、plan 自身も「選別完了にすぎない」と認めています。[plan.md](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:250)

   D1647 の理由は collection、deselect、LPT 並べ替えを分解することなので、「わずかに早い」と一般化できません。少なくとも worker 側 `pytest_collection_finish` まで進め、LPT 完了後を採る必要があります。

   放置時: report の collection 終了値が実際より早まり、collection/LPT と最初の test 前待機の帰属が入れ替わる。

3. **worker 異常終了で lock 観測が失われ、crash report は偽の `"serial"` epoch 0 を作る。**

   正常終了時は worker の `pytest_sessionfinish` 中に payload が追加され、その後 xdist が `workerfinished` を送るので問題ありません。[remote.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/remote.py:141)

   異常終了時は `worker_errordown` が直接 `pytest_testnodedown` を呼び、custom workeroutput は届きません。[dsession.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:238) 現行 `_controller_state` は payload 件数を configured worker 数と照合せず、gw0 の full payload が 1 件あれば通るため、非 gw0 が作業完了後に落ちた場合は test bounds が残っても、その worker の lock interval は消えます。[acceptance_shards.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/tools/acceptance_shards.py:928)

   また xdist が controller 上で作る crash `TestReport` は `worker_id` を持たず、`start` / `stop` は既定値 0 です。[dsession.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:432)、[reports.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/reports.py:318) plan の無条件集計ではこれを `"serial"` worker として採ります。真正な setup/call/teardown report だけを集計し、欠落 payload を空配列と同一視しない設計が必要です。

   放置時: 実際に取得された lock が `[]` と記録されるか report finalization が失敗し、crash 時には存在しない `"serial"` worker と epoch 0 が report に混入する。

4. **通常 run の no-op 設計が既存 synthetic Item を壊す。**

   plan の疑似コードは `item.config` を直接評価します。[plan.md](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:130) 一方、既存の real-repo protocol 契約テストは `config` を持たない `SimpleNamespace` を渡し、lock/stamp の順序を固定しています。[test_real_repo_serialization.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/test_real_repo_serialization.py:2081)

   `getattr(item, "config", None)` 相当を no-op 条件に含めない限り、lock context に入る前に `AttributeError` になります。plan の新規テスト一覧にもこの既存契約がありません。

   放置時: 通常 run の既存テストが赤になり、受入全走は certified 結果を出せない。

5. **3-file 限定では ledger coverage gate が赤になる。**

   権威テストは各 `session.items` について production consumer key を直接取り、独立 key との一致も検査しています。[test_acceptance_schedule_order.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2333-shard-timeline/orchestrator/tests/test_acceptance_schedule_order.py:696) serial collect-only の表示 nodeid を数えた親の方法とは、現構成では同じ集合です。ledger の `nodeid_count=19521` も静的に一致しました。

   親の算術も正しく、余裕は 7 node です。plan は最低 12 node を追加するため、ledger 未更新なら `19419 / 21581 = 89.9819%` となります。parametrize 展開分を含めればさらに下がります。[plan.md](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/plan.md:208)

   放置時: G5 coverage gate が失敗して受入全走が certified にならず、plan の成果物が完成しない。

## nit

- コスト見積りは I/O 面では妥当ですが、通常経路にも約 21,569 回の追加 helper context enter/exit と guard が入る点を数えていません。canonical K=3 では collection clock 約 144 回、TestReport 更新は約 43,000〜65,000 回、lock clock は 10^2 回級です。追加 file I/O、worker message、flock/open/close は増えないため、388 秒級 wall に対して小さいという定性的結論は妥当です。
- 親の「blob SHA が見つからない」は事実でも、「内容への束縛が無い」への一般化は過大です。conftest の protocol 順序を直接実行する検査、acceptance source 全体を AST/string 走査する検査、旧 v1 の exact field 集合を持つ historical consumer が存在します。ただし、動的に conftest を copy して同じ live bytes と比較する検査は frozen pin ではありません。
- [brief.md](/home/SFC/tanab/.claude/jobs/9b50de3a/tmp/artifacts/t2333-shard-timeline/brief.md:61) の「直後または同 dict の中」は、837〜850 行を触らない制約と矛盾します。plan 本文の「閉じた `setattr` の直後」だけに限定すべきです。

## plan の前提のうち実物と食い違う点

| 前提 | 静的判定 |
|---|---|
| P1-a: 必須 field と shape 検査を足しても D1647 を守る | 不成立。欠落・malformed timeline が merge verdict を変える。 |
| P1-b: controller の TestReport だけで test bounds を採れる | 正常 report に限れば成立。controller 生成 crash reportと workeroutput 欠落経路には成立しない。 |
| P1-c: epoch float を使う | 成立。pytest の `start` / `stop` 自体も epoch 秒。host clock skew は plan 記載どおり残る。 |
| P1-d: conftest から recorder を呼び、通常 run は no-op | 依存方向は成立。`item.config` 不在を含めない no-op 契約は不成立。 |
| 変更は 3 file に限定できる | 12 node 以上を維持するなら不成立。ledger も対象になる。 |
| 対象 file の内容に束縛された consumer は無い | 不成立。runtime/source scanner と旧 v1 exact consumer がある。 |

また、依頼文にある「xdist controller と worker の両方で `pytest_collection_modifyitems` が走る」という前提は installed xdist 3.8.0 と一致しません。DSession は controller collection を明示的に禁止しています。[dsession.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/dsession.py:102) xdist 時の採取主体は worker であり、custom workeroutput が必要という plan の結論自体は正しいです。

## 攻撃したが破れなかった点

- pytest 9.1.1 は `report.__dict__` を複製し、復元時に dict 全体を `TestReport` へ渡します。`start` / `stop` は明示引数、xdist が追加する `worker_id` は `**extra` から復元されます。[reports.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/_pytest/reports.py:596)、[remote.py](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/remote.py:280) repo 内に serialization hook の上書きもありません。
- serial 実行では controller/worker 分離がなく、通常の TestReport から `"serial"` の min start/max stop を採れます。
- 正常 xdist 終了では全 worker payload に timeline を追加しても、既存 digest 一致と「gw0 full payload ちょうど 1 件」は維持できます。追加 key は現在の検査対象外です。
- projected test file で report dict を直接作るのは `_reports()` だけです。`_write_parallel_success_artifacts()` もそれを再利用するため、helper 更新で既存 report fixture は全て追随します。
- collection/lock は既存 workerfinished message、report は既存 create-only write を使うため、per-item I/O と追加 message は生じません。
- `setattr(...state...)` が閉じた後だけ追記するなら、並行 wave の 837〜850 行を変更せずに済みます。
- receipt、`dev_wave_wait.py`、`MergeResult` を触らない方針なので、D1620 の canonical wall の測定面そのものは変わりません。