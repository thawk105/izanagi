## 所見

- [B] collection が次に止まる。`tools/check_acceptance_reds.py:277,493-498` は collection に `timeout=120` を継承するが、実測は queue 待ち込み 211–213 秒（`evidence-collect-small.txt:31-35`, `evidence-collect-truncated.txt:62-66`）であり、receipt 前に `InvalidInput`、rc=2、checker receipt 未生成となる。`subprocess.run` の timeout は dispatch 子を kill するため qdel も失う可能性がある。

- [B] cleanup が literal に実装されると probe fingerprint で再停止する。`plan.md:50-52` は nonce directory と fallback receipt だけを消すが、`tools/check_acceptance_reds.py:364-391` は ignored path も検査し、`.gitignore:25` の `output/pegasus-dispatch/` は実際に `!! output/pegasus-dispatch/` と出る。放置時は rerun 後 rc=2、status/receipt 未生成となる。

- [M] `PYTEST_ADDOPTS` が collection の選択集合を汚染できる。`tools/check_acceptance_reds.py:280-285` が環境を継承し、`run_tests.py:916-923` と `dispatch_compute.py:56-68,584-596` が `PYTEST_ADDOPTS` を子へ渡す一方、receipt binding は argv だけ。`PYTEST_ADDOPTS=--deselect=...` で target を残した部分 collection と footer が整合し、`non-attributable-only` または `attributable-red` の受理集合・nodes・report が変わる。

- [M] `--force-dispatch` は安定性を保証しない。`tools/run_tests.py:1825-1827` は admission を飛ばして一回 dispatch するだけで、queue/scheduler/compute の rc=16 に retry がない。collection は `tools/check_acceptance_reds.py:499-502`、rerun は `:735-738` で rc=2 に倒れ、certified 選択も checker receipt も増えない。

- [M] 赤 10 件は file 単位でなく node 単位に 10 回 collect する。`tools/check_acceptance_reds.py:693-734` は各 reference ごとに fresh worktree、collection dispatch、rerun dispatch を直列実行するため 20 dispatch。実測の約 211–213 秒/dispatchなら約 70 分、queue timeout 900 秒なら最大約 5 時間であり、実用性を失う。受入 report と台帳の確定が遅延する。

- [M] M2 は size 検査の検出力を証明しない。`plan.md:185-188` の fixture は `omitted_bytes>0` だけを主欠陥にするため、`omitted_bytes=0` かつ `size != len(tail.encode())` の size gate 変異は生存しうる。放置時は不整合 receipt の tail から nodes を作り、status・attributable 集合・receipt 値が変わる。

- [N] M0 は wave 前の実コード形を含む。`tools/check_acceptance_reds.py:503-510` の `result.stdout.splitlines()` への回帰で、receipt は有効、relay 側だけ欠落、footer 件数不一致という単一理由になる。これを外すと旧実装の検出力証明にならない。

- [N] M1、M3、M4 はそれぞれ footer 件数、request binding、receipt location の単独 gate を狙えている。各 fixture で他の schema・selector・rerun 条件を有効に固定できるなら、無効化時の受理集合反転は一つに絞れる。

- [N] M5 は必要な positive control である。`1 test collected` を `tests` と誤認する変異だけを赤にし、過剰拒否時の受理集合縮小を検出する。

## 層の網羅

scope 内に残る層は、受入 log parsing（`tools/check_acceptance_reds.py:169`）、dispatch receipt の検証、collection footer gate、selector、probe worktree、cache-only submodule、単独 rerun、classification、checker receipt 書込である。

scope 外に残る層は、dispatch producer の relay/log 上限と queue retry、`tools/run_tests.py` の環境・admission、受入 waiter/land の checker 呼び出し、acceptance receipt/report/台帳への反映、T-1019 の log hash binding である。

## 裁定パッケージ候補

- [B] `tools/dev_wave_wait.py` または `tools/dev_wave_land.py` から checker を呼び、`rc=0` かつ `status=non-attributable-only` の場合だけ受入 receipt を成立させる。現在は `rg` で両ファイルに caller がなく、checker は `tools/check_acceptance_reds.py:984-1028` の standalone CLI に留まる。
- [M] dispatch wave で、relay ではなく容量制限のない collection artifact を提供し、`PYTEST_ADDOPTS` など選択環境を receipt に束縛する。
- [M] checker wave で path ごとの collection cache または file 単位の再利用を導入し、10 件で 20 dispatch になる構造を改める。

## 総括

receipt 経路自体は既知の 12,098 bytes collection を復元できる見込みだが、現計画の collection timeout が先に実測 queue 待ちへ負ける。  
cleanup と環境汚染にも fail-closed または誤受理の穴が残る。  
最大の実効性欠落は、修正後 checker を呼ぶ production consumer が無いことである。  
pytest と実 checker は実行しておらず、以上は静的所見である。