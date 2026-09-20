# probe 仕様 v2 (段 4 裁定で確定。author の正本)

file: `tools/t2709_blob_transfer_probe.py` (1 file、標準 library だけ、python 3.10)。先例 `output/insights/2026-09-17/t2708-fixture-config-h-gap/probe-source.md` の `git_env` / `git` / `checked_git` / `require` / `hold_session` / `main` の骨格を流用してよい。

## 0. 起動と引数

```
python3 -B -m tools.t2709_blob_transfer_probe \
  --source-root <wave worktree 絶対> --work-parent <絶対 dir> --out <絶対 JSON path> \
  [--rounds 5] [--transfer-trials 3] [--subprocess-timeout 1200] [--keep-work] [--require-local-fs] \
  [--selftest | --hold-session-only]
```

- cwd は `--source-root` と一致していること。`--work-parent` の下に `tempfile.mkdtemp(prefix="t2709-", dir=work_parent)` で work-root を作る。`--out` は work-root の外 (job dir) でよい。work-root は source-root の内側でも source-root を含んでもいけない。
- 終了時 (正常・異常とも) に `--keep-work` が無ければ work-root を `shutil.rmtree` する (`--selftest` も同じ)。
- `--require-local-fs`: work-root の `os.statvfs` では fstype が取れないので `/proc/self/mountinfo` から work-root を含む最長 mount point の fstype を引く。`tmpfs` / `lustre` / `nfs` / `nfs4` なら拒否 (failures に記録して rc=1)。fstype は常に JSON に記録する。
- 環境整備は先例どおり: `GIT_*` と `PYTEST_XDIST_TESTRUNUID` を消す、`TMPDIR/TEMP/TMP` を `work/tmp` へ、`sys.path.insert(0, source)`、`sys.dont_write_bytecode = True`。
- hostname が `pegasus0` で始まるなら `measure` を拒否 (selftest / hold-session-only は可)。
- 全 subprocess は `--subprocess-timeout` 秒で `TimeoutExpired` → その試行を `failed` (理由 `timeout`) にし、次の試行へ進む。builder の timeout は 1800 秒。
- JSON は**試行ごとに** `--out` を上書き保存する (途中死でも部分結果が残る)。`ok` は failures が空のときだけ true。

## 1. git 呼び出しの共通形

- env = 先例の `git_env()` (`GIT_*` を除去 + `GIT_CONFIG_NOSYSTEM=1`、`GIT_CONFIG_GLOBAL=/dev/null`、`GIT_TERMINAL_PROMPT=0`、`GIT_OPTIONAL_LOCKS=0`)。
- **production 形 status** (以下 `status_prod`): `git -c core.useReplaceRefs=false -c core.fsmonitor=false -c core.untrackedCache=false status --porcelain=v1 -z --untracked-files=all --ignore-submodules=none`、cwd=root、env=上。stdout の bytes を記録 (空が clean)。
- commit metadata の固定: commit を作る subprocess (`commit`、`commit-tree`) には env に `GIT_AUTHOR_NAME=T080 E2E Human`、`GIT_AUTHOR_EMAIL=t080-e2e@example.invalid`、`GIT_AUTHOR_DATE=2026-09-20T00:00:00+0900`、`GIT_COMMITTER_*` も同値を加える (builder と同じ name/email)。message は `T080 migration basis` + 空行 + `AI-Agent: none` (builder と同じ)。
- timed 区間は `time.perf_counter_ns()` で subprocess の起動直前〜終了直後を計る。各 record に argv、cwd、rc、stderr (先頭 4 KiB)、`elapsed_s` を残す。pipe (pack-objects | index-pack) は両 Popen の起動直前から両方の `wait()` 完了までを 1 区間 `transfer_s` とし、両 rc/stderr と、`resource.getrusage(RUSAGE_CHILDREN)` の前後差 (utime/stime) も残す。

## 2. 土台 (1 回)

1. `hold_session` (先例逐語) で `orchestrator.tests.test_s8b_oracle_driver` を enforcing pytest session の中で import する (`-k t2709_no_such_node_zzz`、rc 0/5 を許容)。
2. `builder._build_t080_stub_free_e2e_repo(work / "base", issue_receipt=False)` を 1 回呼ぶ (timeout 1800 秒、所要 `build_s` は参考値)。root = 返り値の root。
3. 参照値の抽出 (root の `.git` から、timed 外): `ref_tree` = `rev-parse HEAD^{tree}`、`ref_commit_builder` = `rev-parse HEAD` (参考)、`ref_index` = `ls-files -s -z` を parse した list of (mode, oid, stage, path)、`ref_reachable` = `rev-list --objects HEAD` の OID 集合から `ref_commit_builder` を除いた集合、`ref_count_objects` = `count-objects -v`、`ref_config_bytes` = `.git/config` の bytes。
4. `.git` を `work / "git-ref"` へ `os.rename`。**以後 root 直下に `.git` 以外の隠し dir や余分な file を置かない** (`add -A` が拾う)。
5. 移送に関する集合 (timed 外、参照側):
   - `ref_blobs` = `ref_index` の mode 100644/100755/120000 の OID を重複除去。
   - source repo (`--source-root`、cwd=source) で `cat-file --batch-check` に `ref_blobs` を流し、`present` / `missing` を分ける。`missing` の件数と対応 path を記録 (期待: `.gitmodules` など fixture 固有 bytes の少数)。
   - `in_repo_sources` と `real_basis`: builder と同じ導出 — `json.loads((source / builder.migration.KNOWN_AXES_REL).read_text())` から `path`+`sha256` を持つ dict の `path` を集め、`external/ccbench/` 始まりを除く。`real_basis` = `json.loads((source / builder.migration.RECEIPT_REL).read_text())["migration_basis_commit"]`。
   - `recorded_commits` = source の receipt JSON の値のうち 40 hex の文字列すべて (再帰的に集める)。
   - source の概況: `git -C source count-objects -v`、`rev-parse --git-common-dir`、`rev-parse HEAD`。
   - `fixture_paths` = `ref_index` の regular file (100644/100755) の path 一覧 (C1 の選定入力。production では builder が複製した集合として既知)。
   - `hash_paths` = 同上 (symlink・gitlink を除く)。総 bytes を `os.stat` で合計して記録。

## 3. 再初期化 (試行ごと、timed 外)

```
os.rename(root/".git/modules", work/"modules-keep")   # 初回は git-ref から: os.rename(work/"git-ref/modules", work/"modules-keep") を土台の直後に 1 回
shutil.rmtree(root/".git")                              # 初回は存在しない
git init -q  (cwd=root)
(root/".git/config").write_bytes(ref_config_bytes)      # gc.auto=0 / user.* / submodule.* を含む
os.rename(work/"modules-keep", root/".git/modules")
```

再初期化後に `git config --int --get gc.auto` が `0` であることを確認 (failures)。

## 4. 方式 (timed 区間)

### A (現行)
1. `add -A` → `add_s`
2. `commit -q -m "T080 migration basis" -m "AI-Agent: none"` (metadata 固定 env) → `commit_s`
3. `status_prod` → `status1_s` (stdout bytes を記録)
4. `status_prod` → `status2_s`
`total_s` = add + commit + status1。

### C1 (採用候補形)
1. **選定** `select_s` (1 区間、内訳も記録):
   - `git -C source ls-files -s -z -- orchestrator output` → dict path→(mode, oid)
   - `git -C source ls-tree -r -z <real_basis> -- <in_repo_sources の path 群>` → dict で上書き (basis 復元された file)
   - `fixture_paths` の各 path について候補 OID = 上書き後の dict[path] (無ければ候補なし)
   - 候補 OID (重複除去) を `git -C source cat-file --batch-check` に流し `missing` を除く → `transfer_oids`
   - 候補が無い path 数、missing 数、`transfer_oids` 件数を記録
2. **移送** `transfer_s`: `git -C source pack-objects --stdout <chosen_pack_args> --delta-base-offset` (stdin = `transfer_oids` 改行区切り) | `git index-pack --stdin -v` (cwd=root)。pack bytes (`.git/objects/pack/*.pack` の size) を記録。
3. `add -A` → `add_s`
4. `commit` → `commit_s`
5. `status_prod` → `status1_s`、`status2_s`
`total_s` = select + transfer + add + commit + status1。

### C2 (参照 index を使う下限模型)
1. **移送** `transfer_s`: `present` (参照 blob のうち source に在るもの) を同じ pipe で。
2. **不足 blob 生成** `generate_s`: `missing` の path 群を `git hash-object -w --stdin-paths` (cwd=root、stdin = path 改行区切り) → 出力 OID が参照 OID と一致しなければ失格 (`failed`、理由 `generated-oid-mismatch`)。missing が 0 件なら区間 0 で記録。
3. `update-index -z --index-info` `index_info_s` (stdin = 土台で取った `ls-files -s -z` の生 bytes をそのまま。形式 `"<mode> <oid> <stage>\t<path>\0"` は index-info の第 3 形式と同一。gitlink 160000 を含む)
4. `write-tree` `write_tree_s` → tree OID
5. `commit-tree <tree> -m "T080 migration basis" -m "AI-Agent: none"` (metadata 固定 env) `commit_tree_s` → commit OID
6. `update-ref HEAD <commit>` `update_ref_s`
7. `update-index --refresh` `refresh_s` (rc は 0 を期待。非 0 なら失格)
8. `status_prod` → `status1_s`、`status2_s`
`total_s` = transfer + generate + index_info + write_tree + commit_tree + update_ref + refresh + status1。

## 5. 各試行後の検査 (timed 外。1 つでも落ちれば `failed=True`、理由の list を残す。数値は残すが判定から外す)

- (i) `rev-parse HEAD^{tree}` == `ref_tree`
- (ii) `rev-parse HEAD` == 同一 wave 内の最初の成功試行の commit OID (全方式共通、metadata 固定なので一致するはず)。最初の試行はこの値を定義する
- (iii) `status1` の stdout == b""
- (iv) `rev-list --objects HEAD` の OID 集合 (HEAD commit を除く) == `ref_reachable`
- (v) `fsck --connectivity-only` rc == 0
- (vi) `objects/info/alternates` が不在 (`.git/objects/info/alternates` の lstat が FileNotFoundError)
- (vii) 移送した pack (C1/C2) の object が全部 blob: `verify-pack -v <pack .idx>` の出力の型列に `blob` 以外が無い、object 数 == 移送 OID 数
- (viii) `recorded_commits` のそれぞれが fixture で `cat-file -e <oid>` rc != 0 (missing)
- 記録: `count-objects -v`、`du -s .git/objects` 相当 (`os.walk` で bytes 合計と file 数)、`.git` の `shutil.copytree(root/".git", work/f"gitcopy-{n}", symlinks=True)` の wall (timed、副次量) → 直後に rmtree

方式ごと 1 回 (その方式の最初の成功試行の直後):
- (ix) 独立性: `work/"git-ref"` を一時的に `work/"git-ref-hidden"` へ rename した状態で、fixture root 全体を `shutil.copytree(root, work/"fixture-copy", symlinks=True)` (wall を `copy_fixture_s` に記録) → 複製先で `status_prod` を 2 回 (timed、`copy_status1_s`、`copy_status2_s`、stdout bytes) → 複製先で `cat-file --batch-check` に `ref_blobs` 全件 → missing 0 → 複製先を rmtree、rename を戻す
- (x) 変更検出 (root で、status_prod を使う): (a) `fixture_paths` の先頭の regular file に 1 byte 追記 → status に ` M <path>` を含む → 元 bytes に戻す → status 空、(b) 同 file の mode を `chmod +x` → status に ` M` → 戻す → 空、(c) `external/ccbench` 内の tracked regular file 1 つ (submodule 内で `git ls-files | head -1`) に 1 byte 追記 → status に ` M external/ccbench` を含む → 戻す → 空。いずれかが期待と違えば failures に記録 (方式の検査失敗として `variant_checks[方式]` に残す)

## 6. 事前実験と設定選択

main 試行の前に (再初期化した空 `.git` に対して、`present` 集合で):
1. 「初回移送」: 既定設定で 1 回。`initial_transfer` に記録し、`cold_guaranteed: false` を付ける。
2. 交互 × `--transfer-trials`: {`[]` (既定), `["--window=0", "--depth=0"]`} を交互に (既定, w0, 既定, w0, …) 合計 2×N 回。各回: 再初期化 → 移送 → pack bytes、外側 wall、CPU 差分、両 rc。
3. `chosen_pack_args` = 外側 wall の中央値が小さい方 (同点は既定)。根拠 (両中央値) を JSON に記録。

## 7. 順序

round r = 1..`--rounds`: 方式の順は `[A, C1, C2]` を r−1 だけ左回転 (r1: A C1 C2、r2: C1 C2 A、r3: C2 A C1、…)。各 round の先頭で `hash_pass`: `git hash-object --stdin-paths` (cwd=root、stdin = `hash_paths` 改行区切り、書込なし、timed) — path に改行があれば `-z`… ではなく `--stdin-paths` は改行区切りなので、改行を含む path があれば hash_pass を skip して記録。

## 8. JSON の構造 (キー名は自由だが、次の情報を欠かさない)

- `environment`: hostname、`git --version`、python、`os.cpu_count()`、`os.sched_getaffinity(0)` の数、loadavg (開始/終了)、work-root と fstype、temp env、`source_head`、`source_common_dir`、`source_count_objects`、probe file の sha256。
- `parameters`、`build_s`、`hold_session`。
- `reference`: tree、builder commit、index entries 数、regular/symlink/gitlink 件数、bytes 合計、`ref_blobs` 件数、present/missing 件数と missing の path、`in_repo_sources` 件数、`real_basis`、`recorded_commits` 件数、`ref_reachable` 件数、count-objects。
- `initial_transfer`、`transfer_pretrials` (各回)、`chosen_pack_args` と根拠。
- `hash_pass` (round ごと)。
- `trials` (list、順序どおり): round、position、variant、各区間の秒と argv/rc/stderr、`total_s`、tree/commit、検査結果 (`checks` dict と `failed`、`fail_reasons`)、count-objects、objects bytes/file 数、pack bytes、`gitcopy_s`。
- `variant_checks`: 方式ごとの (ix)/(x) の結果と `copy_fixture_s`、`copy_status1_s`、`copy_status2_s`。
- `summary`: 方式ごとの `total_s` の中央値/min/max (成功試行のみ)、round ごとの `d_r = C1 − A` と median、事前登録規則 (`改善候補` / `悪化観測` / `未確定`) の適用結果、失格件数。**規則の版**: `median(d) <= -1.0 and count(d<0) >= 4 → 改善候補; median(d) >= +1.0 and count(d>0) >= 4 → 悪化観測; else 未確定` (成功 round 数が 5 未満なら閾値は「成功 round 数 − 1」)。
- `failures`、`limitations` (先例と同じ list)、`ok`、`started_at`/`finished_at`。

## 9. selftest (login で走る、合成 repo、時間で assert しない)

`work/selftest/` に: source repo (regular file 6 個、そのうち 1 個は後で「basis 復元」用に履歴 2 版、symlink 1 個、1 個の tracked file を `.gitignore` 対象にして `add -f` 済み、submodule は無し) を作り、fixture 相当 dir へ複製 (1 file は source index と違う bytes = missing 相当)。次を正負例で確認し、結果を `selftest` dict と failures に残す:
- (a) A / C1 / C2 の tree と commit が一致 (metadata 固定)。
- (b) C2: `update-index --index-info` 直後、`git ls-files --debug` の全 entry の ctime/mtime/size が 0 → production 形 status を 2 回 → index file の bytes が不変 (書き戻し無し) → `update-index --refresh` → ctime/mtime/size が非 0 になり index bytes が変わる。
- (c) C1: pack 既在の blob について `add -A` 後に `count-objects -v` の `count` (loose) が「missing 相当の 1 件 + tree/commit の件数」以下。対照: pack 無しで `add -A` すると loose が全 blob 分増える。
- (d) 失格判定の負例: `.git/objects/info/alternates` を置いた試行が (vi) で失格 / 参照と違う tree の試行が (i) で失格 / blob 以外 (commit) を混ぜて移送した pack が (vii) で失格 / `recorded_commits` に fixture 内の commit を入れると (viii) で失格。
- (e) 変更検出 (x) の 3 経路のうち (a)(b) が正例で通り、production 形 status がそれを報告する。
- (f) `--require-local-fs` の fstype 判定が `/proc/self/mountinfo` から値を返す (値は記録のみ)。
selftest の各項目は `require(...)` で failures に積む。

## 10. 書かないこと・してはいけないこと (逐語で守る)

- source-root へ 1 byte も書かない (`pack-objects` は読むだけ)。`IZANAGI_RUN_GROWTH_HELD_TESTS` を設定しない。`GIT_*` を継承しない。
- 「選定・移送・不足 object の生成・index の検証と保存に必要な処理を timed 外へ移して、自己完結経路の総費用と記述してはならない。production の status 引数・環境・変更検出を弱めてはならない。失格・timeout・欠測を黙って除外または再試行し、成功分だけで事前登録判定を満たしたと報告してはならない。main 初回を cold と断定し、per-base の差を受入 wall の改善へ読み替えてはならない。」
- `--assume-unchanged` / `--skip-worktree` / `core.checkStat` / `core.trustctime` を使わない。
- 試行の前に「無料の refresh」(status や refresh を timed 外で走らせる) をしない。再初期化直後の最初の git 操作が方式の 1 手目である。
