結論は **must-fix 2 件、nit 2 件**です。親の daemon=True 復帰は妥当ですが、新設正例の恒真化と隔離 meta-test 違反が残っています。

pytest は実行していません。mutation の緑・赤は提供された `mutation_matrix_v2.json` の記録です。隔離契約だけ AST で静的導出しました。

## 所見ごとの対応表

| ID | 判定 | 根拠・残存失敗シナリオ | 成果物影響 | 扱い |
|---|---|---|---|---|
| A-1 | **partial** | 新設正例は最初に helper を呼び、`False` なら SKIP する（[test_dev_waves_integration.py:942](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:942)）。helper が常に `False` へ退行すると正例と長 path node の両方が rc=0 の SKIP になり、検出対象へ到達しない（[同:967](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:967)）。 | M-B 等との複合退行を受理し、長 path では supervisor 起動不能・試行台帳 0 件の commit を certified 参照にし得る。 | **must-fix** |
| A-2 | **closed** | `socket.socket()` から `listen()` までが同一 `try/except OSError` に入り、socket 生成・bind・chmod・stat・listen の拒否はいずれも `False` になる（[同:913](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:913)）。本番列は [protocol.py:250](/home/SFC/tanab/github/izanagi/tools/dev_waves/protocol.py:250)。 | 元所見の socket EPERM による偽赤、chmod/stat/listen 拒否による偽赤は閉じた。 | closed |
| A-3 | **closed** | probe は本番と同じ `/proc/self/fd/<fd>/.s` を使う（[test_dev_waves_integration.py:908](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:908)、[protocol.py:128](/home/SFC/tanab/github/izanagi/tools/dev_waves/protocol.py:128)）。`.p`/`.s` policy の非同値は解消。 | basename policy による受理集合の不一致は閉じた。cleanup 衝突面は下記の別 nit。 | closed |
| B-1 | **closed** | thread は `daemon=True` に戻り、`join(30)` 後の生存 assert と serve 例外回収を維持（[test_dev_waves_integration.py:971](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:971)、[同:984](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:984)、[同:1002](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:1002)）。 | 無期限 thread が pytest worker の終了を妨げる型を除きつつ、停止退行は赤にできる。 | closed |
| B-2 | **partial** | 5 秒の偽赤面は 30 秒へ緩和されたが消えてはいない（[同:1000](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:1000)）。worker が 30 秒超停止・deschedule されれば正常 shutdown でも赤。逆に確定 deadlock も30秒待つ。 | 正常 commit の誤排除、または外部 timeout が短い環境で受入レポート未生成になり得る。現 runner 内には全走 timeout がないため現状は nit。 | **nit** |
| B-3 | **partial** | close 例外は抑止され、bind 失敗時に既存 socket を消す問題も `created` で閉じた（[同:911](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:911)）。ただし `unlink()` 例外は送出され、bind が実体を作ってから例外化した場合は `created=False` のまま残る（[同:915](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:915)、[同:927](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:927)）。 | fault injection や異常 sandbox で当該 node が偽赤、または SKIP へ逃げる。通常の実 socket 経路への影響は確認できない。 | **nit** |
| B-4 | **regressed** | 新設 node に marker がない（[同:933](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:933)）。一方、既存語彙は helper の `bind_repo_socket` を拾い、呼出しを推移させる（[test_dev_waves_isolation_contract.py:33](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_isolation_contract.py:33)、[同:66](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_isolation_contract.py:66)）。静的導出は `expected-only=[test_short_alias_bind_probe_reports_capability_loss_without_failing]`。 | integration 単独 matrix は通っても、受入全走の isolation meta-test が marker 欠落で赤になり、certified 選択・レポート・試行台帳の参照は旧 commit に留まる。 | **must-fix** |

## Must-fix 1: 新設正例は過剰拒否に対して依然恒真

- **(a) 主張:** 文字どおり「どんな実装でも緑」ではなく、常時 `True` は mock assertion に殺される。しかし、検査目的そのものに反する「常時 `False`」は rc=0 の SKIP で生存する。
- **(b) file:line:** [test_dev_waves_integration.py:942](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:942)、[同:946](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:946)、[同:967](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:967)。
- **(c) 失敗シナリオ:** helper を `return False` に退行させ、同時に M-B を入れる。正例は最初の gate で SKIP、長 path node も本番を起動せず SKIPとなり、複合退行が rc=0 で通る。
- **(d) 成果物影響:** mutation matrix が probe の過剰拒否耐性を認証したように見える一方、長 path の受理試行は 0 件となり、壊れた commit を certified 参照へ入れ得る。
- **(e) 判定:** **must-fix**。

`mutation_matrix_v2.json` は正常 probe の baseline を記録するだけで、constant-False mutation は含みません（[mutation_matrix_v2.json:3](/tmp/claude-31609/-home-SFC-tanab-github-izanagi/96d62154-0f41-4a00-8132-05b75fe01ae1/scratchpad/wave-t137-t138/mutation_matrix_v2.json:3)）。

## Must-fix 2: 新設 node が隔離 meta-test を現在形で壊す

- **(a) 主張:** B-4 はもはや将来問題ではない。新 node は既存 AST 契約上 marker 必須と導出されるが、marker がない。
- **(b) file:line:** [test_dev_waves_integration.py:933](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:933)、[test_dev_waves_isolation_contract.py:108](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_isolation_contract.py:108)、[同:114](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_isolation_contract.py:114)。
- **(c) 失敗シナリオ:** 受入全走で `test_every_node_that_touches_process_external_resources_stays_serialised` が、余分なし・欠落 1 件として決定的に失敗する。integration ファイル単独の v2 matrix には meta-test が含まれないため見逃されている。
- **(d) 成果物影響:** 受入全走が赤になり、当該 wave は受理集合へ入らず、certified 選択・材料レポート・試行台帳の commit 参照を更新できない。
- **(e) 判定:** **must-fix**。

mock 自体については、通常経路で永続的な漏れはありません。`with mock.patch(...)` は例外時も復元し、xdist の別 worker は別プロセス、同一 worker では test body が並行しません。ただし patch 中は process-wide です。先行失敗 node が daemon thread を残した場合、その thread が同じ worker 内で `socket.socket`、`bind`、`listen` を呼ぶと一時 mock を観測し、実行順序依存の連鎖赤になります。

## probe `.s` cleanup の攻撃結果

- **(a) 主張:** 通常の実 socket 経路では本番との衝突を確認できなかった。一方、fault injection では偽赤・偽緑の両方が残る。
- **(b) file:line:** [test_dev_waves_integration.py:915](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:915)、[同:927](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:927)、[daemon.py:1593](/home/SFC/tanab/github/izanagi/tools/dev_waves/daemon.py:1593)、[protocol.py:255](/home/SFC/tanab/github/izanagi/tools/dev_waves/protocol.py:255)。
- **(c) 失敗シナリオ:**
  - bind 成功後の chmod/stat/listen 失敗では `created=True` なので unlink される。unlink の `PermissionError`、`EIO`、`FileNotFoundError` は元の `False` を上書きして例外となる＝**偽赤**。
  - mock socket の bind が成功を返すが実ファイルを作らない場合、chmod の `FileNotFoundError` 後に unlink も `FileNotFoundError` となる＝**偽赤**。
  - wrapper bind が実 bind を済ませてから `OSError` を投げると、`created=True` 代入前なので `.s` が残り、helper は `False`、長 path node は SKIP＝**偽緑**。
  - unlink が成功を返すだけの no-op mock なら `.s` は残る。ただしこの node では `serve_forever()` が有効な stale socket を先に削除するため、通常は `bind_repo_socket()` の `socket-path-exists` へ届かない。helper 直後に `bind_repo_socket()` を直接呼ぶ caller なら失敗する。
- **(d) 成果物影響:** 現在の実 socket 正常経路では値・参照への影響なし。fault injection 時は node の failed/SKIP が変わり、受理集合が過剰縮小または拡大する。
- **(e) 判定:** **nit**。

POSIX の正常な `unlink()` は pathname を同期的に namespace から外すため、「正常 unlink が単に遅れて本番と衝突する」経路は確認できません。

## join(30) と daemon=True

- **(a) 主張:** 30 秒化は 5 秒偽赤を緩和するが、timeout の根本的な二律背反は残る。daemon=True 復帰そのものは親裁定を支持する。
- **(b) file:line:** [test_dev_waves_integration.py:1002](/home/SFC/tanab/github/izanagi/orchestrator/tests/test_dev_waves_integration.py:1002)、[tools/run_tests.py:377](/home/SFC/tanab/github/izanagi/tools/run_tests.py:377)、[mutation_matrix_v2.json:33](/tmp/claude-31609/-home-SFC-tanab-github-izanagi/96d62154-0f41-4a00-8132-05b75fe01ae1/scratchpad/wave-t137-t138/mutation_matrix_v2.json:33)。
- **(c) 失敗シナリオ:** M-A2 のような確定退行でも赤まで30秒待つ。反対に worker の SIGSTOP、極端な oversubscription、共有ノード starvation が30秒を超えれば正常 shutdown を偽赤にする。
- **(d) 成果物影響:** repository runner は pytest subprocess に全走 timeout を設定していないため、通常は「赤が約30秒遅れる」だけ。外部の受入 ceiling が30秒増分を許さなければ、レポートや試行記録自体が未生成になる。
- **(e) 判定:** **nit**。外部 ceiling が判明して30秒増分を吸収できなければ must-fix へ昇格。

v2 の記録では以下が確認できます。

- M-A2 は新テストで単 node `rc=1 / 32.25s`、whole file `rc=1 / 44.26s`（[mutation_matrix_v2.json:37](/tmp/claude-31609/-home-SFC-tanab-github-izanagi/96d62154-0f41-4a00-8132-05b75fe01ae1/scratchpad/wave-t137-t138/mutation_matrix_v2.json:37)）。
- M-B は単 node・whole file とも `rc=1`（[同:71](/tmp/claude-31609/-home-SFC-tanab-github-izanagi/96d62154-0f41-4a00-8132-05b75fe01ae1/scratchpad/wave-t137-t138/mutation_matrix_v2.json:71)）。
- M-D は daemon=True で約31秒後に `rc=1` を返し、非 daemon 版は外部90秒 timeout まで終了しない（[同:92](/tmp/claude-31609/-home-SFC-tanab-github-izanagi/96d62154-0f41-4a00-8132-05b75fe01ae1/scratchpad/wave-t137-t138/mutation_matrix_v2.json:92)、[同:107](/tmp/claude-31609/-home-SFC-tanab-github-izanagi/96d62154-0f41-4a00-8132-05b75fe01ae1/scratchpad/wave-t137-t138/mutation_matrix_v2.json:107)）。

したがって、現在の production 退行で「非 daemon 版だけが検出し、daemon=True 版が緑になる」型は確認できません。非 daemon が追加で捕まえるのは、生存 assert 自体が削除された場合の interpreter hang、または本来すでに赤になっている途中例外後の残留 thread です。いずれも有用な赤ではなく全走 hang へ悪化させます。M-D は親裁定を強く支持します。

## 親が測るべき実測

1. 隔離契約の現在形:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 tools/run_tests.py \
  orchestrator/tests/test_dev_waves_isolation_contract.py::test_every_node_that_touches_process_external_resources_stays_serialised -q
```

期待: 新設 probe node の marker 欠落で `rc=1`。

2. helper constant-False mutationの positive control:

```bash
python3 tools/run_tests.py \
  orchestrator/tests/test_dev_waves_integration.py::test_short_alias_bind_probe_reports_capability_loss_without_failing \
  orchestrator/tests/test_dev_waves_integration.py::test_socket_roundtrip_works_beyond_108_byte_repository_path -rf
```

一時的に helper を `return False` とする変異を適用・復元して測る。現状予想は **2 skipped / rc=0**。期待すべき修正後結果は少なくとも正例が failed / rc=1。

3. 30秒偽赤の昇格判定:

```bash
for i in $(seq 1 20); do
  python3 tools/run_tests.py -n 32 --dist=loadgroup \
    orchestrator/tests/test_dev_waves_integration.py \
    orchestrator/tests/test_dev_waves_isolation_contract.py || break
done
```

期待: 20/20 完走し、`shutdown() が serve ループを止めていない` が発火しないこと。発火すれば B-2 を must-fix に昇格します。