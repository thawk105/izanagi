静的検査のみです。pytest・build・実競合試験は実施していません。以下の「未確認」は実走結果ではありません。

### A-1 — publish 競合が create-only ではない

重大度: must-fix

主張: `lexists` の事前検査と `os.rename` は原子的な「存在しなければ作成」ではない。v2 は同一実装の競合を一方拒否するだけで、legacy には claim がない。

根拠: `orchestrator/campaign/buildcache.py:776` と `:851`、`:988` と `:992`。既存テストも v2 について「一方だけ成功・一方は claim error」を期待している (`orchestrator/tests/test_buildcache_v2.py:964`, `:997`)。`os.link(..., follow_symlinks=False)` を使う create-only 実装は `orchestrator/qualification/atomic_publish.py:100` にある。

成果物影響: 競合順序により候補が abort されるほか、空ディレクトリ・通常ファイル・symlink が publish 先なら参照先が変わり、受理集合・binary 参照が競合依存になる。

提案: legacy にも per-digest claim を導入し、publish は `renameat2(RENAME_NOREPLACE)` 相当または create-only link 手順にする。衝突時は既存 entry の manifest・bytes を検証して cache hit に倒す。

### A-2 — 同一 FD の検査保証が実行時まで届かない

重大度: blocker

主張: hash・fsync・実行が同じ inode に束縛されていない。現行コードは path を開き直し、`BuildResult` は文字列 path だけを返す。

根拠: `full_sha256()` は通常の `open(path)` (`orchestrator/campaign/buildcache.py:87`, `:94`) で、v2 も hash と fsync が別 path 操作 (`:826`, `:830`)。返却値は path (`:864`) であり、pipeline は後段でその path を実行する (`orchestrator/campaign/pipeline.py:931`, `:1091`, `:1192`)。expected SHA も既定では未配線で、渡された場合も保存済み hash との比較だけ (`orchestrator/campaign/pipeline.py:896`, `:902`)。

成果物影響: WAL が記録する `perf_bin_sha256` と実際に verify/bench した bytes が異なり、誤った binary が certified commit・レポートへ入る。

提案: 実行まで FD を保持して `fexecve`/`/proc/self/fd` 経由で起動するか、実行直前に nofollow open・hash・実行対象を同一 FD に束縛する。少なくとも公開後 binary を read-only にする。

### A-3 — 親ディレクトリの path-based 作成が dir-fd 防壁を迂回する

重大度: blocker

主張: leaf を `O_NOFOLLOW` で開いても、親 namespace が path-based のままなら中間ディレクトリの symlink 差し替えを防げない。

根拠: v2 は `os.makedirs(parent, exist_ok=True)` (`orchestrator/campaign/buildcache.py:739`)、legacy も同様 (`:944`)。fsync も path を再 open している (`:318`)。同リポジトリ自身も root identity 検査後の path open に TOCTOU が残ると明記している (`orchestrator/campaign/durable_root.py:67-70`)。

成果物影響: cache entry が予定 namespace 外へ publish され、別場所の binary が manifest・ledger の digest と結び付く。

提案: 承認済み root FD から各 component を `openat`/`mkdirat` 相当で辿り、各段階を `O_NOFOLLOW|O_DIRECTORY` で検査する。rename と fsync も保持した parent FD に対して行う。

### A-4 — leaf の symlink・FIFO・hard link・mode 検査が不十分

重大度: blocker

主張: 現行 cache hit は binary leaf の symlink や特殊ファイルを十分に拒否しない。計画の `O_NOFOLLOW` は binary、manifest、cleanup の全経路に適用し、open 後の `fstat` を基準にしなければならない。

根拠: v2 は `binary = os.path.join(...)` 後に通常の hash open を行う (`orchestrator/campaign/buildcache.py:477-481`)。legacy は `os.path.exists(binary)` で hit と判定する (`:920`)。`nm` も path を直接開く (`:1105`)。stale cleanup は `os.path.isdir`/`os.path.exists` が symlink を追跡し (`:1071`)、`shutil.rmtree(ignore_errors=True)` 後の判定も path-based (`:1082`)。実行 bit を確認する direct builder とは対照的に (`orchestrator/campaign/t152_write_intent_coverage.py:396-398`)、buildcache は通常ファイル・nlink・execute bit・setuid/setgid/sticky を検査していない。

成果物影響: host binary・FIFO・hard-linked inode の bytes が検査対象となり、ハングまたは別 bytes の認証・実行を引き起こす。

提案: `O_NONBLOCK|O_NOFOLLOW` で開いてから `fstat`、regular file・所有者・`st_nlink == 1`・privileged mode bit を検査する。コピーは byte copy に限定し、destination は restrictive/read-only mode にする。

### A-5 — Python 3.10 と Linux 固有 flag を混同している

重大度: must-fix

主張: Python 3.10 であることだけでは `O_DIRECTORY`、`O_NOFOLLOW`、`dir_fd`、`follow_symlinks` の組み合わせは保証されない。計画が Linux 固有実装を採るなら、実行環境契約として明示的に fail-closed すべきである。

根拠: 現行コードは `O_DIRECTORY` を `getattr` で扱う (`orchestrator/campaign/buildcache.py:320`)。別実装は `O_NOFOLLOW` 不在時に明示拒否している (`orchestrator/campaign/durable_root.py:109-117`)。`atomic_publish` も flag を条件付きで追加している (`orchestrator/qualification/atomic_publish.py:77-79`)。

成果物影響: 非対応環境で publish 全体が突然 abort するか、unsafe fallback が残れば受理 binary の namespace 保護が消える。

提案: `os.name`、必要な constants、`os.supports_dir_fd`、`os.supports_follow_symlinks` を起動時に検査し、不足時は必ず拒否する。Linux-only なら policy とテスト対象を明記する。

### A-6 — allowlist は既存 cache hit に遡及せず、consumer 主張も全体では未確認

重大度: must-fix

主張: manifest の field 集合は検査するが、entry directory の実体メンバー集合は検査していない。したがって旧実装が生成した `CMakeCache.txt` 等を含む entry は、そのまま cache hit できる。

根拠: manifest field の検査は `orchestrator/campaign/buildcache.py:424-430`、binary の検査は `:477-481` で、directory enumeration がない。通常の buildcache は fresh staging を使う (`:948`、v2 は `:781`)ため、CMake incremental rebuild の喪失は通常は費用であり、正しさの後退とは静的には読めない。一方、floor は binary だけを保存する (`orchestrator/campaign/s8b_floor_campaign.py:1225`, `:1247`)、report は WAL の build command だけを読む (`orchestrator/campaign/p2_2_report.py:70-77`)。`t152` の CMakeCache 読み取りは独自の direct build directory (`orchestrator/campaign/t152_write_intent_coverage.py:283`, `:388`) であり、buildcache consumer とは未確認である。

成果物影響: 隠れた cache-tree consumer があれば再現用 metadata 欠落で build/report が壊れ、なければ主に再 configure 費用だけが増える。全 output・shell・外部 consumer の不存在は未確認。

提案: cache contract を「binary + generated manifest/sidecar」と明文化し、hit 時も許可 member を列挙検査する。旧 entry は拒否または clean namespace へ再発行し、`build_dir` を外部 API として扱わない。

### B-1 — registry は分類であって隔離ではない

重大度: blocker

主張: `materializer_admission` の登録は downstream の拒否を起こさない。登録済みの direct builder は、診断 payload を作った後も実際に build している。

根拠: `non_admissible_materializer()` は辞書を返すだけ (`orchestrator/campaign/materializer_admission.py:86-99`)。s5 は登録後に `_build_broken` を実行する (`orchestrator/campaign/s5_permutation_coverage.py:187`, `:207`)、t152 も direct CMake build を行う (`orchestrator/campaign/t152_write_intent_coverage.py:382-398`)。`s8b_materialization` は registry の projection に留まる (`orchestrator/campaign/s8b_materialization.py:41-44`)。

成果物影響: `non-admissible` がレポートに表示されるだけで、WAL・selection・proof chain への混入を防げず、受理集合は変わらない。

提案: buildcache/pipeline の実行境界で registration を必ず消費し、unknown site と `NON_ADMISSIBLE` を fail-closed にする。shell・arbitrary binary path を対象外にするなら、全体隔離とは主張しない。

### B-2 — coder authority が entrypoint/quarantine に束縛されていない

重大度: blocker

主張: coder token は parser 発行 nonce でしかなく、entrypoint 名や quarantine receipt を含まない。同じ `coder-authored` receipt を複数 driver・低レベル caller が使える。

根拠: token は nonce のみ (`orchestrator/campaign/build_admission.py:117-126`, `:253-260`)。`build_run_context` に site 引数がなく (`:292-312`)、`derive_build_admission` は authority nonce だけで coder class を生成する (`:462-481`)。validator も `authority_kind` の検査に留まる (`:542-547`)。kickoff/red は同じ generic context を使う (`orchestrator/campaign/p3_kickoff.py:89-118`, `orchestrator/campaign/p3_s4_red.py:142-175`)。

成果物影響: 未登録 caller が同じ `coder-authored` receipt を得て、通常の pipeline・COMMIT (`orchestrator/campaign/pipeline.py:1170-1177`) まで到達できる。

提案: authority/context/receipt に canonical site と quarantine digest を含め、pipeline の build boundary で両方を必須化する。generic token だけでは `buildcache` を呼べない構造にする。

### B-3 — AST closure は alias・dynamic call・将来 surface に弱い

重大度: must-fix

主張: 現行 AST 制御は generic helper の存在と direct attribute call を見るだけで、site の正しさ・alias・`getattr`・動的 import を証明しない。autonomous driver も現行テスト列挙から抜けている。

根拠: `test_p3_build_authority_cli.py:103-120` は `add_coder_build_authority_argument` の存在しか確認しない。manual inventory は top-level `glob("*.py")` と `"--build"` literal に依存する (`:369-380`)。別の AST gate も direct qualified call と literal keyword を対象にするだけ (`orchestrator/tests/test_s8b_floor_campaign.py:1667-1703`)。実コードには `importlib.import_module` と `getattr` による動的解決がある (`orchestrator/campaign/s8c_preregistration.py:1541`, `:1566`)。また autonomous は authority flag を受ける (`orchestrator/campaign/p3_autonomous_workload_trial.py:2260`, `:2286`)が、現行 `_DRIVERS` 列挙にはない (`orchestrator/tests/test_p3_exploration_namespace.py:37-43`)。

成果物影響: 新規・alias・dynamic caller が registry/AST closure をすり抜け、quarantine なしの coder build が certified selection に混入する。

提案: runtime registry を一次防壁にし、AST は補助監査に限定する。authority path の dynamic import/getattr は拒否し、全 intended roots を `rglob` で走査して canonical site の完全一致を検査する。

### T-1 — 正負テストの帰属が後段検査に先取りされる

重大度: must-fix

主張: 現行 buildcache fixture は `_run`、source evidence、nm を差し替えるため、同一 FD・特殊 file・publish exact set を証明しない。B の既存正例は flag があれば全 driver を build spy まで通すため、red/kickoff の拒否変異を直接検査していない。

根拠: fake build は固定 payload を通常の `write_bytes` で作り、observer gate を monkeypatch する (`orchestrator/tests/test_buildcache_v2.py:195-223`)。manifest hash 自体は独立検査しているが (`:816-849`)、race hook と final member set の検査はない。B の正例は全五 driver の flag 付き到達を期待する (`orchestrator/tests/test_p3_exploration_namespace.py:76-137`)、無 flag 例は parser の明示 opt-in error だけで終了する (`:56-69`)。red は先に flag 検査で落ち得る (`orchestrator/campaign/p3_s4_red.py:146-151`)。fixture trace 自体も固定 payload である (`orchestrator/campaign/p3_s4_red.py:103-123`)。

成果物影響: mutation ledger が「A/B の防壁を殺した」と誤帰属し、実際には hash/nm/flag/parser の別検査が先に発火しただけでも、受理集合と計画の実効性を誤認する。

提案: A は copy helper 単体を対象に symlink/FIFO/hardlink/race を検査し、source/nm はそのテスト内だけ明示的に固定する。B は flag を渡した上で unrelated gate を stub し、red/kickoff の `run_campaign`・layout・WAL が一切発生しないことを確認する。診断 payload は digest/構造フィールドだけを比較する。

### M-1 — 親の「実測」は静的読解と混同されている

重大度: must-fix

主張: consumer 限定性と P4 の実効性を裏付ける repo 内の実走 receipt は、今回の静的検査では確認できない。現存する根拠は AST inventory と fake/unit fixture であり、runtime consumer・shell・output 全体の測定ではない。

根拠: AST closure は `orchestrator/tests/test_s8b_floor_campaign.py:1667-1736`、manual inventory は `orchestrator/tests/test_p3_build_authority_cli.py:369-385` にある。いずれもコード走査であって実行結果の receipt ではない。pytest/build/real campaign は本 worker では実施していない。

成果物影響: P1/P4 が「測定済み」と台帳へ記録されると、未検査 consumer や生き残った mutation があるまま certified selection を広げる。

提案: 「静的 inventory」と表記を改め、runtime consumer trace または完全な静的 surface inventory を別成果物として添付する。実走していない値は acceptance ledger に入れない。

## 総括

blocker:

- A-2: hash/publish と実行 bytes の非束縛
- A-3: path-based parent namespace
- A-4: symlink・特殊 file・hardlink 境界
- B-1: registry が隔離を起こさない
- B-2: coder authority が site/quarantine に未束縛

判定は **NO-GO**。少なくとも上記 blocker を runtime 防壁へ落とし、A の create-only publish と B の downstream enforcement を実装・測定するまで、計画の実効性は成立しない。

| 親の主張 | 判定 |
|---|---|
| P1 | 支持（buildcache の二つの publish 点と主要 binary consumer に限定）／全 repo・runtime consumer は未確認 |
| P2 | 支持（通常 buildcache は fresh staging で、incremental loss は主に費用）／外部 consumer については未確認 |
| P3 | 反証（registry は分類のみで、全 artifact isolation にはなっていない） |
| P4 | 未確認（テスト seam はあるが、実走・mutation attribution は未確認） |

単一理由の変異:

- A: allowlisted binary の open から `O_NOFOLLOW` だけを外し、regular target への symlink fixture を置く。copy helper 単体で「leaf symlink を拒否しない」理由だけで落ちる形にする。
- B: `p3_s4_red` の registry status を `NON_ADMISSIBLE` から `QUARANTINE_GATED` に変更し、flag 付き・他 gate stub 済みで `run_campaign`/WAL/layout が発生しないことを期待する。