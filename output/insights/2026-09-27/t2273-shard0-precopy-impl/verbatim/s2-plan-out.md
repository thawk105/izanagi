## 変更点

- `orchestrator/tests/conftest.py:2360,2388,2583` — 写し用の job 属性・`workerinput` key・待ち上限を追加する。`pytest_configure_node` で早期 memo の起動直後に一度だけ非 daemon thread を起こす。controller は `tempfile.gettempdir()` 下に `ROOT` と `testrunuid` の hash から決めた session 専用 dir を作り、その絶対 path を各 worker に渡す。thread 内で実関数を **実 repo に一回** `_copy_git_visible_output(ROOT, snapshot / "output")` と呼ぶ。成功時は `ready.json.pending` を `ready.json` へ rename、失敗時は `failed.json` を置き、例外を job に保存する。次の worker への `pytest_configure_node` は同じ job の path を渡すだけにする。
- `orchestrator/tests/conftest.py:2964,3381` — `_finish_memo_sessions` の独立した終了処理に写し job の finish を加える。既存の `_finish_early_memo_job` の後で thread を join し、worker 終了後に写しを削除する。複数の終了処理が失敗しても後続の片付けを試み、既存の「最初の例外を保持する」順序を守る。写し thread の例外は controller 終了時にも伝播させる。
- `orchestrator/tests/conftest.py:2979`、`orchestrator/tests/test_s8b_oracle_driver.py:1437,1458` — worker は `pytest_configure` で `workerinput` の path を process 内の専用 env 値へ渡す。builder は実 repo の `ROOT` を複製するとき、その値があれば `ready.json` を期限付きで待ち、`snapshot/output` から `shutil.copytree` する。値がなければ現行の `_copy_git_visible_output(ROOT, root / "output")` をそのまま呼ぶ。path を builder が env や run ID から再計算しない。単独走用の既存 cache、共有 base の key lock と `complete.json` は変えない (`test_s8b_oracle_driver.py:944-1033`)。

## import と発火条件

- `orchestrator/tests/conftest.py:2388` — 背景 thread **内**で `importlib.import_module("orchestrator.tests.test_s8b_oracle_driver")` し、返った module の実関数を呼ぶ。controller の主 thread で import すると collection 開始前の副作用を同期で負わせる。対象 test module は namespace package 内の module なので、この名前と pytest が collection で使う module 名が一致するかを実走で確認する (`test_s8b_oracle_driver.py:33-34`)。controller 自身は通常この test module を collection しないため、同 controller 内の二重 import は想定しない。
- `orchestrator/tests/test_s8b_oracle_driver.py:49-64,974-992` — import は temp root の検査と `sys.path` への追加を実行する。controller に `PYTEST_XDIST_TESTRUNUID` が無ければ `_t080_join_shared_bases()` は `None` を返し、`_T080_SHARED_BASES` も `None` になる。これを正例 test で確かめる。run ID を持つ異常な controller 環境では共有 base へ参加しうるため、実受入の環境でも値が無いことを確認する。
- `orchestrator/tests/conftest.py:2368,2613` — 実受入では `_early_memo_selected` と同じ条件で発火させる。ただし既存の memo test は模擬 config で本物の hook を直接呼ぶ (`test_real_repo_serialization.py:6423-6504`)。写し thread は `isinstance(config, pytest.Config)` も要件にし、その具体的なテスト干渉を防ぐ。worker の collection 後に shard が決まるので、controller は shard 0・1・2 のいずれでも写しを作る。`-n 0`、非 xdist、`-k` などの絞り込みでは `workerinput` に写し path が無く、従来経路になる (`conftest.py:2368-2385`)。

## 波及

- `orchestrator/tests/test_s8b_oracle_driver.py:847-899,1458` — 可視集合と除外規則は実関数の一回目の複製で確定する。二回目の `shutil.copytree` はその `output` 木を丸ごと複製する。既定の `copy2` が file と directory の mode・mtime を引き継ぎ、既定の symlink 処理も一回目と同じになる。元の可視集合には symlink file を入れない (`814-844`); 全件性の二つの検査は変更しない (`1899-1998`)。ctime・inode は従来も新規複製で変わる。
- `orchestrator/tests/test_s8b_oracle_driver.py:847,1437` — 読取り時点は builder ごとから configure 時の一時点へ移る。開始後の実 repo の可視 file の追加・削除・bytes・mtime の変更はその session の fixture に反映されなくなる。一方、開始時点で可視の未 commit file は含まれる。D2242 段 4 A1 と同じ意味の差として docstring に明記し、受理規則や期待値を変更しない。
- `orchestrator/tests/test_s8b_oracle_driver.py:1037-1217` — `t080_shared_cache_probe` は `_T080_SHARED_BASES` を差し替えるが、写しはそれと独立の controller 所有 dir に置く。`t080_small_cache_builder` と flock 観測 test は既存の shared base lock を引き続き検査できる。新しい正例は `_t080_stub_free_e2e_repo` や `_build_t080_active_v2_repo` を呼ばず、consumer AST の 14 function / 20 node を増やさない (`1346-1434`)。
- `orchestrator/tests/conftest.py:661`、`test_real_repo_serialization.py:1617` — 新 test は実 repo の builder を呼ばないため、`REAL_REPO_ACCESS_BY_NODE` と独立 golden への登録は不要。`test_campaign_import_invariant.py:48,1261` の import 検査にも新たな legacy import は加わらない。`acceptance_duration_ledger.json` は未知 node に既定値で対応する配線なので、新 test 一件のための手編集は不要 (`conftest.py:1587-1648`)。growth / flaky hold の登録も不要。波及が生じるとすれば、実走で module 名の二重 import が判明した場合に限り、その原因と必要な変更を再評価する。

## test と変異候補

- `orchestrator/tests/test_s8b_oracle_driver.py:1037` 近傍に小さい git repo を使う正例を一件置く。controller job を実関数の spy 付きで二つの worker node に設定し、呼出し一回・同一 path 配布・ready 前の builder 待ちを確かめる。生成後に source を変更し、写しからの二回の複製が同じ集合・bytes・mode・mtime・symlink 状態を持ち、変更後の source を読まないことを確かめる。実 repo の巨大な builder は使わない。
- 変異候補と期待 kill nodeは次のとおり。**いずれも正例一件**を期待 node とし、各変異を単独で入れる。

| 位置 | 変異 | 単一の赤理由 |
|---|---|---|
| `conftest.py:2613` | thread を起こさない | ready 前に開始した待ちが完了しない |
| `conftest.py:2388` | worker ごとに実関数を呼ぶ | 実関数 spy が一回を超える |
| `test_s8b_oracle_driver.py:1458` | builder が実 repo から直接複製する | source 変更後の bytes が混入する |
| `test_s8b_oracle_driver.py:1458` | 写しから `copy_function=shutil.copy` で複製する | mtime が一致しない |
| `conftest.py:2388` | ready marker を作らない | 待ちが期限超過になる |
| `conftest.py:2388` | 実関数の代わりに output 全件を写す | spy が零回、ignored file も混入する |

  最後の変異は spy の零回だけを kill 判定に使えば理由が一つになる。ready 欠落の変異は実際の 180 秒待ちを避け、test 内で待ち定数を短く差し替える。実受入でのみ起きる collection・memo 競合はこの正例の判定に混ぜない。

## 待ち上限と失敗時

- `orchestrator/tests/test_s8b_oracle_driver.py:1458` — 待ち上限は probe と同じ **180 秒**とする。診断では写し生成が 80.8〜103.3 秒、builder 開始が写し開始の 65.7〜70.7 秒後、実際の待ちは 5.6〜27.1 秒だった (`output/insights/2026-09-26/t2273-shard0-precopy-ab/README.md:11`)。上限は最大観測待ちの約 6.6 倍で、同じ受入計算ノード regime に限った値である。
- `orchestrator/tests/conftest.py:2388`、`test_s8b_oracle_driver.py:1458` — `failed.json` を見た worker は理由を含む例外で赤にし、期限超過も赤にする。写しを指定された builder は実 repo への直接複製へ黙って戻さない。生成 thread の元例外は controller の終了処理でも伝播する。marker 発行前の例外でも worker が無期限に待たない。

## 効果の見込み

- `output/insights/2026-09-26/t2273-shard0-precopy-ab/README.md:8-14` — 対照診断の shard 0 は三対すべて短縮し、対率中央値は 18.0% だった。今回の形はその「collection と複製を重ねる」経路を移すので、同方向の効果を見込める。
- `orchestrator/tests/conftest.py:2613` — 実受入では shard 1・2 にも背景 I/O が増え、早期 memo と同時に動く。診断では memo 待ち超過は無く、memo 所要中央値は A 61.8 秒、P 64.2 秒だったが、実受入の三 shard 同時実行は測っていない。5 分達成、実受入の W_max、shard 1・2 への影響は診断値から主張できず、事前登録する実受入の隣接三対で別々に判定する。

## 未決の設計択一

- `orchestrator/tests/conftest.py:2979`、`test_s8b_oracle_driver.py:1458` — worker への process 内受け渡しは専用 env 値を推奨する。`workerinput` から worker の `pytest_configure` で設定し、終了時に復元する形なら、test module から conftest を別名 import せずに済む。実装前に、controller 背景 import と worker の pytest collection が同じ module 名を使うこと、および通常の controller に `PYTEST_XDIST_TESTRUNUID` が無いことを静的・焦点実走で確定する。

## 総括

`conftest.py:2613` で実受入 controller が session 一回の写しを collection 中に開始し、`test_s8b_oracle_driver.py:1458` の builder が完成を待って局所複製する。
可視集合の実関数と全件性検査は `test_s8b_oracle_driver.py:814-899,1899-1998` のまま維持する。
変更は指定の二 file に収め、新規正例は一件とする。実測効果と 5 分上限は実受入の隣接三対で判定する。