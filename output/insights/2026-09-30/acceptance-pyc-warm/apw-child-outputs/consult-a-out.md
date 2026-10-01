## 所見

1. **高 — P2 の「collection は tree と env の純関数」は成立しない。** pytest の collection は test module を import するため、`run_tests.py:1441–1475` の command だけから書込みが pyc に限られるとは証明できない。plan §5 は RuleOps 側の読取りを確認しているが、collection 側の import 時副作用を閉じていない。前倒しすると、その副作用が削除検査・RuleOps 検査より先に起きうる。**修正:** 実 suite の collection 時書込みを調べ、少なくとも tracked file・検査対象 ledger・submodule への書込みがないことを確認する。確認できなければ P2 の集合不変を主張しない。

2. **高 — 有効 marker 条件だけでは、観測する木の同一性を保証しない。** plan §1・§5 は submodule 初期化との競合を避けるが、collection の観測を preflight 前へ移すため、外部の tree 変更が入りうる時間窓は現行より広い。gate 3 は nodeid の多重集合だけを比較する（`acceptance_shards.py:514–515, 674–682`）。同じ nodeid のまま test の内容が変わる場合、集合一致は検出しない。受領証の前後 fingerprint は runner の前後であり（`dev_wave_wait.py:3929–3946, 4010–4031`）、走行中の往復変更も検出しない。**修正:** 「集合一致」と「同一 bytes の木を観測した」を区別して記録する。前倒しの前後に木の同一性を保証する仕組みがない限り、後者を採用理由にしない。

3. **中 — P3 の「pyc の量は現行と同じ」は赤経路で誤る。** 現行 collection は全 dispatcher worker の起動後に呼ぶ（`acceptance_shards.py:1470–1500`）。前倒し案では preflight 赤、session 作成失敗、dispatcher-start 失敗でも pyc が書かれうる。`git status` による受領証の清浄性は維持されても（`dev_wave_wait.py:361–364, 4010–4031`）、撤去 tool は ignored file を含めて status と file bytes を証拠化する（`dev_wave_cleanup.py:1733–1792`）。**修正:** P3 を成功経路に限定し、赤経路で増える pyc と撤去証拠量を計測対象に入れる。

4. **中 — 前倒し subprocess の失敗は新しい早期失敗面になる。** 現行は `run_parallel` が session と dispatcher worker を用意してから collection を起動する（`acceptance_shards.py:1415–1500`）。plan §2–§3 の早期 `Popen` が資源不足や一時 file 作成失敗で落ちると、従来なら先に出た preflight rc や dispatcher-start の診断を覆しうる。これは F1083 と同じく、性能用の先行処理が consumer 到達前に失敗する形である（`failures.md:28888–28893`）。**修正:** 早期起動失敗時は preflight を従来どおり完了させ、その後の既存 collection 経路で判定する設計を検討し、優先 rc をテストで固定する。

5. **中 — process 寿命の設計は方向として妥当だが、例外境界の test が不足する。** `run_parallel` は deadline 超過、session 作成失敗、worker 起動失敗では callback を呼ばない（`acceptance_shards.py:1415–1418, 1487–1500`）。plan §3 の `main` 所有と `finally` は必須である。一方、signal handler の設置前後、`Popen` 成功直後の所有権設定、group 停止時の猶予超過、一時 file の close・削除を検査する test が plan §6 に明示されていない。**修正:** 実 subprocess を使い、各境界で PID・子孫・一時 file の消滅を確認する。stdout/stderr 3 MB の test は pipe 詰まり検出に有効。

6. **中 — 5100 秒の起点を未決のまま実装できない。** 現行 deadline は `_dispatch_result` 内、`run_parallel` 呼出し直前に作る（`run_tests.py:2374–2382`）。前倒し起動時刻を起点にすれば preflight の 34.2／88.7 秒などを予算から引き、受理可能だった遅い走を rc 16 にしうる（`preflight_timing.out:3`、`preflight_timing-2.out:3`）。dispatch 起点を保つ場合は早期 collection の寿命を別途管理する必要がある。**修正:** brief の「deadline 5100 秒・rc 体系不変」に合わせ dispatch 起点を維持し、早期 process の停止条件を別に定義して test する。

7. **中 — 計測値は並走時の preflight timeout を反証しない。** RuleOps は 60 秒で赤になる（`run_tests.py:852–889`）。親の単独実測は 2.61／8.07 秒だが、同時 collection の CPU・memory・metadata 負荷は含まない（`preflight_timing.out:4`、`preflight_timing-2.out:4`）。`git ls-files --deleted` も 34.21／88.71 秒と振れている。**修正:** 段 4 の対照に RuleOps 所要・rc、login 資源使用量を記録し、混雑時にも preflight の赤が増えないことを採否条件にする。

8. **低 — test の一部は本体の流れを通さない。** 既存の shard 正例は `_dispatch_result` を丸ごとモックする（`test_run_tests_shards.py:386–417, 667–688`）。既存の順序 test は `run_parallel` の構文順序だけを見る（同 `2067–2087`）。plan §6 の追加 test も同じ形なら、起動済み process が実際に callback へ渡され、二重 collection されない変異を殺せない。**修正:** 一つは `main → _dispatch_result → run_parallel` を通し、偽 dispatcher と実 collection subprocess で起動回数、回収結果、log bytes を確認する。恒真 assert や helper 単体の検査を変異の根拠にしない。

## 反証できず

- plan の有効 marker 条件は、`_preflight_submodule` の自動初期化分岐を避ける（`run_tests.py:892–927, 967–986`）。
- command・env・除外 payload を共通 helper から作れば、現在の collection 入力との一致を保てる（`run_tests.py:1432–1460`）。ただし実装前なので一致は未検証。
- gate 3 と merge 関数を変えなければ、nodeid 集合に対する判定式自体は変わらない（`acceptance_shards.py:674–706`）。
- argv、`PYTEST_ADDOPTS`、site、internal shard spec、bounded membership による shard 適格性は resolver に集約されている（`run_tests.py:267–298`）。`--force-dispatch` は空の内部 argv へ正規化されるため、plan の起動条件で対象になる（同 `231–250, 2426–2439`）。
- RuleOps `check` に明示的な repo 書込みは確認できない（`ruleops.py:397–443, 2617–2635`）。

## 総括

現 plan のままの採用は保留を推奨する。特に collection の副作用、赤経路の pyc、早期起動失敗時の rc 優先順位、deadline 起点を実装前に固定する必要がある。gate 3 の nodeid 判定式は維持できるが、観測する木の同一性までは保証しない。