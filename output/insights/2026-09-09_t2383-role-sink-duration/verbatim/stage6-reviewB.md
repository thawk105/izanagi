## flake の種

結論は、path 分離は成立していますが、負荷依存の Git timeout による flake 経路が残っています。

- 各 worker の `run_root` は `tmp_path / f"wire-{wire}"` で32通りに分離されています。campaign ID が同じでも WAL、`campaign.lock`、raw、report は別 subtree です。`orchestrator/tests/test_p3_autonomous_workload_trial.py:1902-1913`
- `executor.map` は入力順で返すため、集約順は決定的です。実行順だけが非決定です。`orchestrator/tests/test_p3_autonomous_workload_trial.py:1959-1968`
- WAL の `flock` は wire ごとの異なる WAL file に掛かるため、4 worker 間で同じ flock を奪い合いません。`orchestrator/campaign/wal.py:1273-1283`
- PID だけを使う report tmp 名も親 directory が wire ごとに異なるため衝突しません。namespace marker は `tempfile.mkstemp` です。`orchestrator/campaign/p3_autonomous_workload_trial.py:2426-2436`、`orchestrator/campaign/layout.py:485-519`
- Git object database は共有されますが、この経路の Git は `rev-parse`、`ls-tree`、`cat-file` の読取りで、`GIT_OPTIONAL_LOCKS=0` です。固定 HEAD と不変 worktree の下では、並行読取り自体から bytes が変わる経路は見つかりませんでした。
- `ContextVar` は thread ごとの run scope を分離します。環境契約 cache は lock 付きです。replay capability の `issued` dict は lock 無しですが、裁定対象の CPython 3.10では個別の dict 書込みが GIL 下にあり、順序依存の consumer もありません。
- 一方、contract-loader Git には10秒の基本 timeoutがあります。4 worker と他47 pytest workerの負荷により同じ read が境界をまたぐと、同一 commit・入力でも成功と `ContractLoaderBindingError` に分かれます。発生確率は実測していません。`orchestrator/campaign/contract_loader_binding.py:17,293-310`

## 資源の数え上げ

成功経路の静的な数え上げです。

| 資源 | この node の総数 | この node からの最大同時数 | 根拠 |
|---|---:|---:|---|
| Git subprocess | 772 | 4 | contract-loader 516回と trial-registry 256回 |
| 明示的 `fsync` | 832 | 4 | 1 wire 26回を32 wire |
| live closure の明示的 `os.open` | 16,064 | open syscall は最大4、保持 fd は最大16 | 64 capture × 63 path、1 capture 251 open |

Git の内訳は次のとおりです。

- C1 前計算: 4回。
- 1 wire あたり contract-loader: 16回。32 wireで512回。前計算込み516回です。
- exploratory launch と finish 時の再導出: 1 wireあたり8回、計256回。
- 合計は `4 + 512 + 256 = 772`。親資料の516は `_run_git` 系だけであり、node 全体の Git process 数ではありません。

`fsync` は1 wireあたり、namespace 2、attempt journal 7、role rawとproposal 10、WAL 6、report 1の計26回です。

Git process 内部が開く pack、index、pipe、pytest 自身の fd は静的に正確には数えられません。したがって、計算ノード全体の同時 open 数は数えられません。他47 workerの負荷も不明なので、node 全体の同時 fsync、Git、open 数も数えられません。

`max_workers=1` と比べると総 Git 数と総 fsync 数は同じですが、瞬間並行数は最大1から4になります。他 workerの所要が何秒変わるかは実測していません。総 Git仕事量は旧版より124回減る一方、短時間の I/O burst は最大4倍になるため、全体効果の向きも静的には断定できません。

## 終端の判定

有限秒での終端保証はありません。

CPython 3.10の `Executor.map` は32 futureを先に submitし、`timeout=None` で順番に待ちます。iterator が例外を受けると未開始 futureは cancelされますが、実行中 futureは止まりません。context manager の `__exit__` は `shutdown(wait=True)` なので、実行中 workerが止まれば main threadも待ち続けます。`/usr/lib/python3.10/concurrent/futures/_base.py:585,648`

特に `trial_registry._git` は `subprocess.run` に timeoutを渡していません。`orchestrator/campaign/trial_registry.py:967-977`

`max_wall_s=3600` は hard timeoutではなく、workloadまたはgeneration開始前の協調的検査です。Git、flock、fsync、openの実行中処理を中断しません。また queued workerごとに開始時刻が異なります。`orchestrator/campaign/p3_autonomous_workload_trial.py:3575-3585,4061-4079,4624`

したがって、Git待ち、filesystem syscall待ち、または実行中 future待ちに入った場合、全体の上限秒数はありません。worker例外は吸収されませんが、別の実行中 workerが止まれば、その例外自体の伝播も終わりません。

## C1 の副作用

固定 HEAD、固定 activation stateでは、各 `campaign.lock` の bytes は変更前と同一です。

- 変更前の `binding=None` は helper 内で `_binding_from_recorded_head()` を呼びます。変更後は同じ値を1回先に作って渡しています。`orchestrator/tests/campaign_lock_test_support.py:23-47`
- encoder は同じ `identity_preimage` と authorityをcanonical JSON化します。`orchestrator/campaign/campaign_lock.py:697-717`
- authorityは identity preimageとは別 fieldなので、campaign identityとcampaign IDは変わりません。
- acceptanceは同じ recorded commitと63 blob digestを検証するため、固定 checkoutでの受理集合も変わりません。
- 各 lockの凍結 pinは同じ初期 recorded HEADへ揃います。途中で HEADが動く環境だけは、従来の「各 campaign 書込み時の HEAD」から「test開始時の HEAD」へ意味が変わります。

引数省略 callerは1個ではなく2個あります。

- `orchestrator/tests/test_p3_autonomous_workload_trial.py:244`
- `orchestrator/tests/test_p3_autonomous_workload_trial.py:3463`

どちらも `binding` を省略し、既定値 `None` から従来どおり内部計算へ進みます。

## 他 test への波及

- `test_p3_build_authority_cli.py` の AST visitor は入れ子関数も function stackへ積みますが、新しい `run_wire` 内に authority helper callはありません。allowlist対象の唯一の callは従来どおり `_coder_authority` 内です。したがって `(file, function, helper, count)` は変わりません。`orchestrator/tests/test_p3_build_authority_cli.py:480-516,620-678`
- `test_reflux_originless_compatibility.py` は対象moduleを importします。追加されたのは標準ライブラリ importと整数定数で、executorは test function実行まで生成されません。import時副作用による破壊は見つかりませんでした。`orchestrator/tests/test_reflux_originless_compatibility.py:12-13`
- duration ledgerの nodeidは変わらず、coverage testも維持されます。ただし記録値は依然140秒です。`orchestrator/tests/acceptance_duration_ledger.json:9062`
- `test_acceptance_schedule_order.py` は durationから順序だけを作り、worker数16、32、48でcollectionとdequeue順の不変性を検査します。対象実装の入れ子関数や thread数は直接走査しません。`orchestrator/tests/test_acceptance_schedule_order.py:1250-1276,1347-1372`
- 並行度定数は定義 `orchestrator/tests/test_p3_autonomous_workload_trial.py:56` と使用 `:1960` の1組だけです。値を1行変えて1、2、4、8を測れます。`=1` はmain thread直列版ではなく「executor 1 thread」ですが、親裁定の比較条件は測定可能です。

本レビューでは pytest、solo計測、48 worker受入を実測していません。

## must-fix

1. (a) 4並行の自己負荷により、10秒 Git timeoutをまたぐかどうかが走行時負荷依存になります。  
   (b) 根拠: `orchestrator/tests/test_p3_autonomous_workload_trial.py:1959-1962`、`orchestrator/campaign/contract_loader_binding.py:17,293-310`  
   (c) 成果物影響: 同一 commit・入力の受入全走が、走行ごとに緑または赤へ分かれ得ます。

2. (a) executorに全体 hard timeoutがなく、timeout無しの trial-registry Gitまたは filesystem待ちに入った実行中 threadを `shutdown(wait=True)` が無期限に待ちます。  
   (b) 根拠: `orchestrator/tests/test_p3_autonomous_workload_trial.py:1959-1968`、`orchestrator/campaign/trial_registry.py:967-977`、`orchestrator/campaign/p3_autonomous_workload_trial.py:4061-4079`  
   (c) 成果物影響: 対象 node、shard、受入全走が完了せず、採否用 junitも生成されない経路があります。

## should-fix

- C4の診断要件は満たしていません。`wire` は workerが全 assertを通過した後の返り値にしか含まれず、worker内部の例外には付与されません。`orchestrator/tests/test_p3_autonomous_workload_trial.py:1860,1916-1942`。失敗成果物から wireを一意に判定できない場合があります。
- C2を採る場合、solo実測後に duration ledgerの140秒を更新すべきです。現状でも test自体は壊れませんが、古い高コストとして早期配置され、重い workerとの I/O重複を残します。

## nit

- 親裁定と実装報告は「既存の他 caller」を単数扱いしていますが、実体は引数省略 callerが2個です。挙動はどちらも後方互換なので文書上の数え違いです。

## scope 外の real 所見

対象 nodeは実 checkoutの HEAD、Git common object database、63 pathのlive closureを読む一方、`REAL_REPO_RESOURCE_NODES` に登録されていません。`orchestrator/tests/conftest.py:258-260,514-564`

これは旧逐次版から存在する分類漏れであり、本 waveの編集範囲を広げる must-fixにはしません。ただし、real-repo writerと同時実行されるとHEAD移動やlive file driftを観測できるため、裁定パッケージ候補です。

free-threaded runtimeでの replay capability `issued` dictのlock不在も実在しますが、親裁定どおり本 waveのCPython 3.10限定外です。

## 総括

C1は固定 checkoutでは lock bytes、identity、受理集合を変えません。  
指定3 consumerに直接の構造破壊はありません。  
C2は総 Git仕事量を減らしますが、I/Oの瞬間並行数を1から4へ増やします。  
負荷依存timeoutと無期限shutdown待ちがあるため、現状のC2は安全な終端を保証しません。  
pytestと性能は実測しておらず、本結論は静的検査です。