## (P0) への攻撃

- **real:** 「到達可能な test file は 6 本」は exact な閉包ではない。実行時に consumer へ到達するのは次の 4 本だけである。

  - `orchestrator/tests/test_reflux_formal_consumer.py:698-767`
  - `orchestrator/tests/test_reflux_origin_client.py:352-528`
  - `orchestrator/tests/test_p3_autonomous_workload_trial.py:6561-6737`
  - `orchestrator/tests/test_reflux_originless_compatibility.py:581-594`

  `test_reflux_origin_ledger.py:931-994,1775-1840` は signature 検査と subprocess 内の `read_origin` だけで、`test_trial_registry.py:888-904,1792-1840` は projection の直列化だけである。親の 6 本は安全側の過大集合であり、「6 本が exact closure」という断定は false。

- **real。ただし P0 の反例ではない:** `terminal_operation_id` の値を新規導出する式は `test_p3_autonomous_workload_trial.py:6494-6497` の 1 箇所だけである。一方、オブジェクトの構築点という字義なら `dataclasses.replace` が `:6537-6541` で二つ目の `OriginProducerInputs` を作る。また replay cache の key は `test_reflux_origin_client.py:359-523` の直接指定や `test_reflux_formal_consumer.py:168,704-763` からも来る。従って「1 箇所」を cache key 全体の閉包根拠には使えない。

- **refuted:** 6 本外からの間接呼出し、`getattr`、動的 import、consumer の monkeypatch、alias 呼出しは見つからなかった。全 test AST 上の関連 call は上記 4 file に閉じている。`test_p3_autonomous_workload_trial.py:6591-6595` の fake `_finish_trial` は本物を呼ぶが、既に数えた `:6561` の経路である。`test_reflux_origin_client.py:365-371` の fake ledger commit も、本物の consumer が先に走る `reflux_origin_client.py:247-269` の既知経路である。

- **refuted:** relevant な parametrize は `test_reflux_origin_client.py:429-455` の 2 case だけで、ID は `wrong-projection-{field}` と別値になり、consumer より前の projection 検査で止まる。同一 ID の複数回使用は `:507-528` の exact replay と `test_reflux_formal_consumer.py:743-767` の意図した REPLAY 検査だけである。

- **refuted:** production formal module を `importlib.reload`、`spec_from_file_location`、`sys.modules` 差替えで別実体化する test はない。`orchestrator/tests` 自体は package ではないため P3 test helper が別 test-module 名で二重 import される余地はあるが、両方とも同じ `orchestrator.campaign.reflux_formal_consumer` を参照し、cache と lock は分裂しない。

- **refuted:** `_ISSUED_RECEIPTS` の writer も同じ 4 file に閉じる。seal は receipt ごとに新規 `object()` で作られ (`reflux_formal_consumer.py:219-237`)、dict が key を強参照するため identity の再利用はない。`_REPLAY_LOCK` は `:278,1044` 以外から取得・差替えされず、例外も `with` を抜けるので locked 状態の test 間残留経路はない。

従って、現 HEAD に同一 ID・異 payload の成功書込みが残るという **P0 の反例自体は見つからなかった**。

## 親の実測と一般化への攻撃

- **real:** 「pytest-randomly が無いので全走はファイル順で決定的」は false。`pytest_collection_modifyitems` は marker と skip を付けるだけ (`orchestrator/tests/conftest.py:391-435`) だが、`_prioritize_real_repo_items` と `pytest_collection_finish` は real-repo node を実際に並べ替える (`:449-472`)。

- **real:** `tools/run_tests.py:394-399` は並列時に `--dist loadgroup` を付ける。現在の xdist 3.8.0 は scope を test 数の降順へ並べるため、worker 列が常に元の直列順の部分列になる、という一般命題は成り立たない。さらに次の work unit を受け取る worker は完了時刻で決まるため、pytest-randomly 不在でも worker への同居は非決定的である。

- **refuted、現対象に限定:** replay 関連 node は `REAL_REPO_SERIAL_NODES` に無く、`xdist_group` marker も無いので全て size 1 の work unit である。同率 sort は相対順を保ち、conftest の並べ替えも関連 node 同士を動かさない。従って現対象だけなら各 worker の関連 node 列は相対順を保った部分列になる。

- **real:** 一般に「直列緑なら任意の部分列も緑」は、途中の clear/reset を部分列が落とせるため導けない。ただし現行では唯一の clear は `test_reflux_formal_consumer.py:196-202` であり、同 file を丸ごと外した 5-file 走はこの反例を狙った検査になっている。さらに現行成功 writer の ID は `typed-terminal`、`terminal-replay`、および test ごとの `P(tmp_path)` で互いに異なるため、現在の結論は静的にも維持される。

- **real:** 親の 5/6-file 指定走と受入全走は収集集合が異なる。既定受入は `orchestrator/tests` 全体 (`tools/run_tests.py:53-55,391-399`) を収集する。ただし全 source の call closure では追加 consumer は見つからなかった。

- **real:** `-p no:xdist` は受入形ではない。`_is_acceptance_run` は `-p` と `PYTEST_PLUGINS` を拒否する (`tools/run_tests.py:519-579`)。`-n0` は受入形として許され、全 target を指定しなければ収集集合は同じだが実行 process 数だけが変わる。

- **real:** 受入判定は `--confcutdir` を許している (`tools/run_tests.py:85-93,563-575`)。suite root より下を指定すれば共通 conftest を迂回できることも既知である (`tools/hold_inventory.py:125-132`)。これは現在の P0 を覆さないが、共通 conftest fixture を「全受入形で必ず効く」と一般化することはできない。

## 不変条件を壊す経路

- **refuted:** plan の最終推奨 (a)「何も実装しない」は state を変更しないため、二つの replay 不変条件を壊さない。

- **real:** brief の P1/P2 または plan (b) の共通 `.clear()` autouse fixture には、同一 test の途中で state を消す経路がある。`test_pytest_failure_digest.py:32-42` は conftest を別 module として読み、`:953-964` で外側 test の途中から `pytest.main(..., plugins=[C])` を再入する。共通 autouse fixture は内側 session にも登録されるため、内側 test の setup/teardown で canonical formal cache を clear する。外側 test が内側呼出しの前後で同じ operation を扱えば、「同一 test 内の replay 状態を途中で消さない」を破る。

  現在の当該外側 test 自体は formal consumer を使わないので、これは現 HEAD の赤ではなく、共通 clear 案に対する実装上の反例である。

- **未確定:** 既存 file-local fixture は `_REPLAY_LOCK` を取らず dict を clear する (`test_reflux_formal_consumer.py:196-202`)。現在の関連 test は同期的なので race は見つからないが、これを全 suite へ広げると test teardown を越えて残る thread と consumer の lock 内処理が競合し得る。

- **refuted:** terminal ID の pin assertion 案は cache や lock を変更せず、両不変条件を壊さない。ただし安全な別 namespace 実装まで拒否する実装形 pin である。

## 変異の帰属

- **real:** plan に確定した事前登録変異はなく、旧定数 `"public-origin-terminal"` への巻戻しが条件付きで挙げられているだけである。

- **real:** この巻戻し変異は wave 成果物だけの killer にはならない。brief 自身の前提どおり各 payload が異なるなら、既存の `test_origin_public_path_preserves_capability_identity_and_projects_terminal` (`test_p3_autonomous_workload_trial.py:6561-6646`) と `test_origin_public_result_distinguishes_partial_from_completed` (`:6720-6737`) が同一 process に載る既存直列走だけで衝突を殺せる。

- **real:** xdist ではこの 2 node が別 worker に分かれると変異が survive し、同じ worker なら既存検査が kill する。従って受入全走での mutation verdict は worker 分配に依存し、新 assertion 固有の kill と記録できない。

- **refuted:** 単一 node の focus だけなら、新 pin assertion 有りで kill・無しで survive を示せる可能性はある。しかしそれは限定 focus での帰属であり、「wave 成果物が無いと殺せない」という suite 全体の帰属条件は満たさない。

- **real:** production の replay 拒否を緩める変異は、既存 `test_reflux_formal_consumer.py:743-767` が既に殺す。これも本 wave の新成果物へ帰属させてはならない。

## 未確定として残すもの

- pytest は実行していない。親が報告した pass 件数・時間を再検証しておらず、本回答は静的結論だけである。
- 現環境で自動 load される pytest plugin は hypothesis、pytest-cov、xdist 系だけだったが、dispatch 先の暗黙 plugin 在庫は repository に pin されていない。pytest-randomly 不在だけでは将来の順序 plugin 不在を保証しない。
- 旧定数変異で各 request bytes が必ず異なることは、fixture Git commit の時刻依存まで含めると syntax だけでは証明できない。ただし親 brief 自身が異 payload と断定しているため、その前提を採用する限り変異帰属は成立しない。
- SHA-256 で異なる `tmp_path` を ID 化する方式は実用上十分だが、数学的な injectivity の証明ではない。現実的な collision 経路は見つからなかった。

## 総括

現 HEAD で P0 を覆す到達経路は見つからず、plan の「実装しない」は正しさ上維持できる。ただし根拠は修正が必要である。

- 実行到達閉包は 6 本ではなく 4 本。
- pytest-randomly 不在は xdist の順序・worker 同居を決定的にしない。
- 共通 conftest の `.clear()` fixture は nested `pytest.main` により同一外側 test の途中で発火でき、さらに `--confcutdir` で受入形から迂回できる。
- 旧定数巻戻し変異は既存検査が先取りして殺し得るため、新 pin への排他的帰属は不成立。

production 変更へ返すべき所見はない。pytest は実走しておらず、緑は報告していない。