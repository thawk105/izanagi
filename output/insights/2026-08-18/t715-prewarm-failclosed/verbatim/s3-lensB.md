結論: `s2-plan.md` はそのままでは land 条件を満たさない。xdist の「test 実行前」barrier は成立するが、「worker 起動前」は成立せず、時間上限の計算も誤っている。CLI 子プロセスと infrastructure failure も射程外に残る。

## 所見

1. [Critical] xdist worker 側の `pytest_collection_finish` が未防御

`xdist/dsession.py:83-91` は `pytest_sessionstart` 内で worker process を起動する。したがって prewarm は OS worker 起動前には完了しない。

一方、worker 側でも `pytest_collection_finish` は発火する。`xdist/remote.py:256-262` が実際に collection 終了イベントを送っており、現在の `orchestrator/tests/conftest.py:468-480` は controller/worker を区別していない。

controller 側の `pytest_xdist_node_collection_finished` なら、`dsession.py:287` の hook 呼出しが `sched.add_node_collection()` と scheduling (`:298-306`) より前なので、test 本体が prewarm より先に走る 1 ms 窓はない。しかしこれは「OS worker 起動前」ではなく「test scheduling 前」である。

worker 側 hook に明示的な `workerinput` guard がなければ、worker ごとに prewarm が走り、重複解決または cache 競合になる。`s2-plan.md:202-207` の fake hook test はこの worker 側実発火を検査していない。

成果物影響: 48 worker での重複 payer、または prewarm 失敗時の大量赤を防げず、P1/P2 の主張が一致しない。

2. [Major] memo singleton の module identity は現在実際に分裂する

`test_s8b_oracle_driver.py:28-34` と `test_s8b_binding_driftguards.py:31-44` は `real_repo_receipt_memo` を非修飾 import している。計画は `orchestrator.tests.real_repo_receipt_memo` へ揃えるとしている (`s2-plan.md:152`) が、これは実装方針であって実行時 identity の検査ではない。

`real_repo_receipt_memo.py:144-149` の `lru_cache` は module object ごとに別物である。conftest が canonical module を prewarm し、consumer が非修飾 module を読むと、consumer 側は miss する。新設 fail-closed なら赤、現行実装なら `real_repo_receipt_memo.py:147-163` の fail-open fallback で再解決する。

既存の `test_s8b_binding_driftguards.py:376-408` は driver の patch 先を検査するだけで、conftest と consumer の memo module が `is` 同一であることを検査していない。

成果物影響: prewarm が成功しても consumer だけが赤または再解決し、singleton 一回性の証跡が偽装される。

3. [Critical] production CLI 子プロセスは prewarm の対象外

親 brief は CLI の二回目解決を明示的に scope 外としている (`s1-brief.md:22-24`)。実際、`test_s8b_oracle_driver.py:3729-3760`、`3700-3723`、`2947-2955` は新しい Python process で `driver.main()` を直接呼ぶ。pytest conftest も memo patch も継承しない。

この経路は `s8b_oracle_driver.py:116-132` の production resolver を直接使う。memo miss として赤にはならず、例外は通常の `ReceiptResolution(state="invalid")` に変換される。

したがって「全 execution route」という S3 の表現は成立しない。CLI を含めるなら R-e も必要で、含めないなら brief の主張を狭める必要がある。

成果物影響: CLI 側の二重解決、実 working tree の再走査、実行ごとの certified selection 差分が残る。

4. [Critical] 時間上限の静的証明が誤っている

`s2-plan.md:235` は `q = 15.3 秒`を使っているが、受入対象の計算ノード実測は `m8-q-compute.md:9-16` の `q = 19.70 秒`である。

基準値は `m5-baseline.md:12-18` の 173.10 秒、閾値は 190.41 秒である。計画の worst-case 加算を正しい q で計算すると、

`173.10 + 19.70 = 192.80 秒`

で、比率は約 `1.114`。1.1 倍を超える。`m9-critical-path.md:23-31` も prewarm の q は critical path に丸ごと乗ると明記している。

M8 の `147 + 19.70 = 166.70 秒`は改善見込みであって証明ではない。CLI の scope 外解決も残る (`s2-plan.md:240-242`)。

成果物影響: 誤った 188.40 秒上界で land 判定し、実測時に S4 を落とす危険がある。

5. [Major] `-p no:xdist` の runner 経路が欠落している

素の `pytest -p no:xdist` は serial hook に入れる可能性があるが、xdist option が存在しない状態で `config.option.testrunuid` を直接参照すれば config error になる。計画 (`s2-plan.md:14`) は absent option の guard を要求していない。

さらに `tools/run_tests.py -p no:xdist` は、runner が `-n` と `--dist loadgroup` を自動付与する可能性がある (`tools/run_tests.py:380-399`, `:1907-1916`)。`-p` は acceptance shape 自体も除外する (`:94-96`, `:519-535`)。

これは memo の fail-closed 赤ではなく、pytest usage error または runner infrastructure failure である。計画の経路表 (`s2-plan.md:141-148`) には含まれていない。

成果物影響: 「素の pytest なら全経路で効く」という検証が、xdist 無効化時だけ未検証になる。

6. [Major] `--forked` と worker crash 再起動の実効性が未検証

`tools/run_tests.py:232-273` は pytest-xdist だけを導入・検査し、pytest-forked を扱わない。この環境でも `pytest_forked` は import できないため、未導入なら hook より前に option error になる。導入済み環境で fresh process になる場合の memo/cache 継承も未固定である。

worker crash 後は `xdist/dsession.py:238-267` が再起動し、`:383-397` が replacement worker を作る。UID は同じ NodeManager から渡される想定だが、再起動後に cache を読むこと、worker 側 hook が再度 payer にならないことを検査する meta-test はない。

成果物影響: crash recovery だけが fail-open、重複解決、または cache miss の赤へ分岐する。

7. [Critical] infrastructure failure と test failure を結果レベルで区別できない

brief は構造化 failure を要求している (`s1-brief.md:56-57`)。計画も `ReceiptMemoError` の JSON field を想定する (`s2-plan.md:107-129`)。しかし runner は最終的に pytest の rc と test output を扱うだけで、memo infrastructure failure を別の結果型へ分類しない。

具体例:

- full acceptance の未初期化 submodule は `tools/run_tests.py:699-711` の rc14 で区別できる。
- targeted run は `:721-725` で警告後に続行する。
- 素の pytest は preflight を通らず、production resolver が `s8b_oracle_driver.py:116-132` で欠落を通常の invalid refusal に変える。期待された refusal test が通る可能性すらある。
- `/tmp`、lock、cache store の新設赤は pytest test error と同じ非ゼロ rc になる。
- bounded local は `tools/run_tests.py:1417-1430` で pytest 未実行の infrastructure failure になる。F362 (`docs/failures.md:9103-9123`) も rc16 は緑にも test 赤にも扱えないと明記している。

成果物影響: clone/submodule/一時領域障害を、test の失敗または正常な product refusal と誤分類する。

8. [Major] shared FS と同時 session で「一回だけ」が証明されていない

cache path は `tempfile.gettempdir()` と `run ID + HEAD`だけで決まる (`real_repo_receipt_memo.py:89-104`)。controller と worker が異なる `/tmp` を見る環境では、controller の cache が worker から見えず、worker の strict get は全て赤になる。

逆に shared FS が `flock` を受理しても、ノード間で lock semantics を保証しなければ複数 payer が同時に走る。明示 UID を再利用する同時 session では同じ HEAD の cache を共有し、worktree や未commit 差分は key に含まれない。

さらに `_prune_stale_caches()` は prefix 全体を glob する (`real_repo_receipt_memo.py:129-141`)。古い lock file を unlink して別 process が同名 lock を作ると、lock が分裂する。

成果物影響: 共有 FS では偽赤、lock 非保証では重複解決、同一 UID 再利用では別 working tree の結果混入が起きる。

9. [Major] mutation の期待 node と runner 範囲が対になっていない

M7/M8/M10 の期待 node は実質一つの fake wiring test (`s2-plan.md:218-229`)だが、実 hook を削除した場合に full consumer range を走らせれば、32/35 consumer node が fail-closed で落ちる。

mutation harness は失敗 node 集合の完全一致だけを KILLED とする (`tools/mutation_harness.py:1904-1920`)ため、期待一件と実際の多数赤は MISMATCH になる。逆に `s2-plan.md:202-207` の fake hook だけを走らせれば、実際の consumer route の検出力を証明しない。

M4 は既存の `test_s8b_binding_driftguards.py:417-438` がすでに cache corruption を検査しており、wave 新設分だけを殺すとは限らない。M10 の UID 検査も実 worker environment ではなく fake node である。

F367 (`docs/failures.md:9247-9266`) のとおり runner 自身を変異対象にする local 走行は rc16 で自壊する。mutation 本走は `DW-M07` (`docs/dev-wave/mutation.md:42-52`)どおり dispatch/`--force-dispatch` が必要である。

成果物影響: KILLED を過剰決定または MISMATCH とし、wave 新設分の検出力を証明できない。

## 経路の数え上げ

| 経路 | prewarm の実態 | miss / 障害時 | 根拠 |
|---|---|---|---|
| `tools/run_tests.py` + xdist | worker ID 到着後、controller hook で実行。OS worker 起動後だが test scheduling 前 | 新設設計なら赤。runner が先に停止すれば test 未実行の infra failure | `dsession.py:287-306`, `s2-plan.md:20-26` |
| 素の `pytest -n N` | 同じ controller hook。runner の submodule preflight はない | cache 不可視なら赤。欠落 submodule は production invalid へ変換され得る | `remote.py:256-262`, `s8b_oracle_driver.py:116-132` |
| `tools/run_tests.py -n0` | serial `pytest_collection_finish` | prewarm miss は新設なら赤、現行は L1 fallback | `conftest.py:468-480`, `real_repo_receipt_memo.py:147-149` |
| 素の `pytest` | serial hook。`pytest` 直叩きなので runner preflight なし | memo failure は pytest error。submodule は通常 refusal になり得る | `_pytest/main.py:864-880`, `run_tests.py:699-725` |
| 素の `pytest -p no:xdist` | serial hook。ただし xdist option の absent guard が必要 | config/usage error または strict memo 赤 | `s2-plan.md:14`, `conftest.py:616-620` |
| `tools/run_tests.py -p no:xdist` | runner が xdist argv を足す可能性があり、計画対象外 | runner/pytest usage failure。prewarm まで到達しない | `run_tests.py:380-399`, `:519-535` |
| bounded local | child pytest を起動せず終了する場合がある | rc16 の infrastructure failure。test 赤ではない | `run_tests.py:1396-1430`, F362 |
| dispatch | dispatch 自体は prewarm しない。compute 側 child が上記 xdist/serial route に入る | compute 側 `/tmp` と controller 側 cache が非共有なら赤 | `run_tests.py:1747-1830`, `:1864-1916` |
| `--forked` | plugin の存在・fresh process semantics とも未固定 | plugin 不在なら option error。存在時も memo 継承未検証 | `run_tests.py:232-273` |
| worker crash/restart | replacement worker が同じ UID の cache を読む想定 | cache 不可視、worker hook 二重 payer、strict miss の可能性 | `dsession.py:238-267`, `:383-397` |
| production CLI subprocess | pytest conftest/memo を通らず直接 `driver.main()` | memo の赤ではなく通常 resolver。R-e の二回目解決が残る | `test_s8b_oracle_driver.py:3729-3760`, `s8b_oracle_driver.py:116-132` |
| nested `pytest.main()` | `test_s8b_binding_driftguards.py:540-544` は同一 Python process 内で新 session | module-level `lru_cache` (`real_repo_receipt_memo.py:144-149`) が session をまたいで残る可能性 | `conftest.py:616-620` |
| `memo_receipt=False` の opt-out 2 node | prewarm 対象外。直接 resolver を二回呼ぶことが仕様 | memo の fail-closed は効かない。意図的な scope 外 | `s1-brief.md:58-59`, `test_s8b_oracle_driver.py:2510-2572` |
| mutation harness collection | `--collect-only` では prewarm しない | collection failure は mutation の test result ではなく harness failure | `mutation_harness.py:1287-1318`, `:1365-1375` |
| mutation baseline / each mutant | 各 subprocess が新 pytest session。consumer を含めば毎回 prewarm | fail-closed 赤の集合が expected nodes と違えば MISMATCH | `mutation_harness.py:1743-1801`, `:1904-1920` |
| 同時 session | UID が異なれば各々 q を支払う。同一 UID なら cache collision | shared lock 不全で重複解決または stale result 混入 | `real_repo_receipt_memo.py:89-104`, `:129-168` |

現行実装のままなら、L1〜L5 (`real_repo_receipt_memo.py:147-163`) は fail-open のままである。計画実装後は想定上赤になるが、CLI、opt-out、runner 未起動、production invalid refusal は memo の赤にはならない。

## 時間見積りへの反論

計算ノードの q は 19.70 秒である。

| ケース | 条件付き prewarm が正しい場合 | 条件が壊れた場合 |
|---|---:|---:|
| 全走、48 worker | M8 の理想値は `147 + 19.70 = 166.70 秒`。ただし静的 worst は `173.10 + 19.70 = 192.80 秒`で閾値超過 | strict fail-closed なら最初の consumer で赤。現行 fallback なら worker 数に応じて解決 work が増える |
| consumer なし 1 file | 例 `3.9 秒`のまま | 無条件 prewarm なら `3.9 + 19.70 = 23.60 秒`、約 `6.05 倍`。計画の q=15.3 なら約4.92倍だが、受入 site の値ではない |
| consumer あり 1 file | `19.70 + 約0.03 = 約19.73 秒`。lazy から prewarm へ移るだけ | worker 側でも prewarm すると最大で解決 work が二重化し、約 `39.43 秒`相当 |
| 1 mutant | consumer を含む新 session ごとに約19.70秒 | 30 mutant なら q だけで `31 × 19.70 = 610.70 秒`、50 mutant なら `1004.70 秒`。fake meta-only なら q=0だが実経路を検証しない |
| consumer file + CLI child | memo prewarm 1回に加え CLI 側の scope 外解決が残る | 実解決 work は概算 `2 × 19.70 = 39.40 秒`分残る |

全走の 166.70 秒見込みは、既存の flock 待ち 909.9 秒分を除けるという M8 の仮説に依存する。これは段 6 の実測が必要であり、計画中の 188.40 秒は q の取り違えで受入証明にならない。

## 総括

判定は差し戻し。

最低限、次を land 前に閉じる必要がある。

- worker 側 `pytest_collection_finish` の明示的除外と crash restart の実経路検査
- conftest と全 consumer の module identity `is` 検査
- CLI 子プロセスを scope に含めるか、S3 の「全経路」主張を撤回
- 計算ノード q=19.70 秒での同一経路 wall/CPU 実測
- infrastructure failure の test failure からの構造的分類
- mutation の runner 範囲、期待 node 完全集合、dispatch 実行の固定

pytest は実行せず、指定どおり静的監査のみ行った。