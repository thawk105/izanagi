結論として、親の (P1)/(P2)/(P3) はすべて採用できます。変更対象は新規 2 ファイルだけです。新規ファイルにはまだ実在する行番号がないため行番号を捏造せず、以下では内部ブロックの配置順と、接続先の既存 `file:line` を示します。

## 変更対象

- `tools/pegasus/fetch_third_party.py`（新規、実行可能 Python CLI）
- `orchestrator/tests/test_pegasus_thirdparty_fetch.py`（新規）
- docs は親の所有。既存 shell・policy・driver・evidence は変更しない。

CLI の書式、`main(argv)`、例外を stderr に 1 行で出して rc を返す形は [run_probe.py:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/run_probe.py:103) と [make_acquisition_receipt.py:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/make_acquisition_receipt.py:51) に合わせます。

## `fetch_third_party.py` の設計

### CLI 表面

```text
fetch_third_party.py fetch   [--repo-root PATH] [--cache-root PATH]
fetch_third_party.py hydrate [--repo-root PATH] [--cache-root PATH]
fetch_third_party.py verify  [--repo-root PATH] [--cache-root PATH]
```

共通引数は次のとおりです。

| 引数 | 既定値 |
|---|---|
| `--repo-root` | `Path(__file__).resolve().parents[2]` |
| `--cache-root` | 省略時は `policy.json["gflags_source_path"]` の親 |
| hydrate の配置先 | override を設けず、`repo_root / THIRD_PARTY_STAGING_RELATIVE` に固定 |

`THIRD_PARTY_STAGING_RELATIVE` は既存 driver の [silo_ladder_rung1.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:54) を使います。`--policy`、`--force`、`--update`、対象名による部分選択、環境変数 override は設けません。合成 policy のテスト seam は `--repo-root` です。

### ファイル内の配置順

1. shebang、docstring、imports
2. repo 内 driver の安全な import
3. `SourceVerificationError` と `OperationalError`
4. policy・path 解決
5. Git 実行と source 検証
6. atomic create-only publish
7. `fetch` / `hydrate` / `verify`
8. parser、`main(argv)`、`sys.exit(main())`

### policy のロード

- 三依存の列挙・名前・URL・pin・CCBench CMake 同期は再実装せず、[third_party_policy():844](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:844) を呼びます。
- gflags/glog の pin は同じ module の `_dependency_pins(repo_root)` を使います。同関数は nested pin、top-level expected head、40 hex を同期検査しています（[silo_ladder_rung1.py:825](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:825)）。
- `gflags_source_path` / `glog_source_path` は strict JSON loader の結果から読む。実 policy のフィールドは [policy.json:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/policy.json:14) と [policy.json:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/policy.json:16) にあります。
- policy/CMake 検査を全て終えてから directory を作る。policy 異常時に cache/staging を残さない。
- `cache_root.resolve(strict=False)` が `repo_root.resolve()` 以下なら rc=2 で拒否し、「repo 外の永続 cache」を機械化します。

### 共通 source 検証

三依存について各検査点で次を実行します。

1. `os.path.lexists(path)` を使い、broken symlink も「既存」と扱う。
2. final component が実 directory で symlink でないこと。
3. `git rev-parse --show-toplevel` が source 自身を指すこと。
4. `git rev-parse --verify HEAD` が policy pin と完全一致。
5. `git status --porcelain --untracked-files=all` が空。
6. `git config --local --get-all remote.origin.url` が 1 個だけで、policy URL と完全一致。

origin には `git remote get-url` を使いません。`url.*.insteadOf` 展開後の URL ではなく clone 時に保存された生の `remote.origin.url` を検査するためです。

gflags/glog は同じ directory/HEAD/status 検査を行いますが、policy に期待 URL が存在しないため origin 一致は主張しません。

### `fetch`

`fetch` だけを network-capable subcommand とします。

1. policy 全体を検査し、cache root を解決する。
2. 既存の三 source を先に全件検査する。1 件でも不正なら何も取得せず rc=1。
3. 欠けた source ごとに cache root 内へ `.NAME.XXXXXX/repo` を作る。
4. `git clone --no-checkout -- URL STAGE/repo`。
5. `git -C STAGE/repo checkout --detach PIN`。
6. stage の HEAD/clean/origin を検査。
7. atomic create-only publish。
8. publish 後の destination を再検査。
9. stage 親を片付ける。

既存 destination に対して `clone`、`fetch`、`pull`、checkout、削除、自動修復は一切しません。不正なら人間に返します。

### `hydrate`

`hydrate` は network を使わない offline 操作です。

1. cache の三 source を全件 HEAD/clean/origin 検査。
2. staging に既存 destination があれば全件先行検査。不正なら上書きせず rc=1。
3. 欠けた destination ごとに staging root 内の一時 directory へ `shutil.copytree(..., symlinks=True)` で `.git` ごと複製。
4. cache source を再検査し、copy 中の変化を検出。
5. copy を HEAD/clean/origin 検査。
6. atomic create-only publish。
7. publish 後 destination を再検査。
8. 最後に三 destination を全件再検査。

### `verify`

`verify` は network を使わず、次の 5 本を検査します。

- `cache_root/{masstree,mimalloc,googletest}`: directory、repo root、HEAD、clean、origin
- policy の `{gflags,glog}_source_path`: directory、repo root、HEAD、clean

staging を単独で再検査したい場合は `hydrate` を再実行します。既存 destination は copy せず検査だけになるため、別の CLI option は不要です。

### atomic 化

一時 directory を publish 先と同じ親に作り、同一 filesystem 内 rename とします。create-only 性は repository 内の既存例 [orchestrator/calibrator/cli.py:282](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/calibrator/cli.py:282) と同型の Linux `renameat2(RENAME_NOREPLACE)` を薄く実装します。

- destination 出現時は `EEXIST` を rc=2 に翻訳し、勝者を自動採用しない。
- `renameat2` 非対応 filesystem では、directory を上書き得る `os.rename` へ弱めず rc=2。
- crash/copy 失敗時にも正式な destination から partial tree は見えない。
- atomicity の単位は source 1 本。三本全体の transaction ではないが、各完成済み source は再実行時に検証されるため安全に再開できる。
- cleanup 対象は自身が `mkdtemp` で作った path だけとし、既存 destination は削除しない。

### exit code

| rc | 意味 |
|---:|---|
| 0 | 対象全件が検査・取得・hydrate 済み |
| 1 | source contract 違反。欠落（offline 操作時）、非 directory、symlink、repo root 不一致、HEAD、dirty、origin 不一致 |
| 2 | argparse usage、policy/CMake 異常、submodule 未初期化、cache path 違反、Git 起動不能、clone/checkout/copy/publish 失敗、publish race |

`KeyboardInterrupt` と signal は通常の process 終了へ委ねます。

## shell verifier との対応

現行 verifier は [submit_silo_ladder_rung1.sh:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:6) と job 側の [silo_ladder_rung1.sh:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/silo_ladder_rung1.sh:17) で同型です。

| 契約 | 現行 shell | 新ツール | 強弱 |
|---|---|---|---|
| 実 directory・final symlink 拒否 | `-d && ! -L` | `lstat`/`is_dir` | 同値 |
| HEAD | `rev-parse --verify HEAD` と pin 比較 | 同じ | 同値 |
| clean | `status --porcelain --untracked-files=all` 空 | 同じ | 同値 |
| repo root | 未検査 | `--show-toplevel` が source 自身 | 新ツールが強い |
| origin URL | 未検査 | local config の exact-one URL を policy と比較 | 新ツールが強い |
| 既存 repo の更新 | clone 分岐を通らず検査のみ（[submit:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:150)） | 検査のみ。fetch/pull なし | 同値 |
| 新規 publish | temp clone 後 `os.rename`（[submit:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:173)） | stage 検査後 `RENAME_NOREPLACE` | 新ツールが強い |
| policy/CMake 同期 | `third_party_policy()` を呼ぶ（[submit:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:154)） | 同じ関数 | 同値 |
| 検査後の変更 | submit 内で直後に receipt 化 | 新ツール単独では後続変更を防げない | 新ツール単独は弱いが、submit の再検査で閉じる |

origin 検査は「local config が policy URL を保持する」ことまでで、その remote から object が実際に届いたことの暗号学的証明ではありません。

## frozen submitter との接続

hydrate の既定先は submitter の `RUNTIME` [submit_silo_ladder_rung1.sh:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:143) と `THIRD_PARTY_ROOT` [同:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:152) に完全一致します。

hydrate 成功後は各 `destination` が実 directory として存在するため、[同:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:173) の `[[ ! -e "$destination" && ! -L "$destination" ]]` は偽となり、clone 部分だけを通りません。その直後の frozen verifier は必ず実行されます（[同:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:196)）。

さらに submitter は HEAD/status をもう一度読み、`third-party-heads.json` を作ります（[同:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:199)）。計算ノード側も receipt と policy を照合し、persistent と scratch の双方を検査してから copy します（[silo_ladder_rung1.sh:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/silo_ladder_rung1.sh:348)、[同:368](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/silo_ladder_rung1.sh:368)）。

配置先は [.gitignore:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/.gitignore:24) で ignore 済みです。したがって submitter の whole-tree clean 検査も壊しません。submit 側は 1 byte も変更不要です。

## `third_party_policy()` の import

再実装せず import する案を推奨します。この関数は次を既に閉じています。

- 三 source の固定順・exact keys・安全な source name: [silo_ladder_rung1.py:849](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:849)
- GitHub HTTPS URL と 40 hex pin: [同:861](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:861)
- CMake の repo/tag literal 一意性と一致: [同:870](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:870)
- SHA ref の場合の ref/pin 一致: [同:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:893)

sys.path は、ツール自身のコード root を import 中だけ先頭へ挿入し、`finally` で自身が追加した要素だけを外します。ユーザー指定の `--repo-root` は絶対に import path に入れず、policy/CMake のデータ root としてだけ渡します。driver 自身も import 時に code root を追加する実装ですが（[同:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:34)）、先に一時挿入しておけば driver は追加せず、永続的な sys.path 汚染を残しません。

import の副作用は module・定数・正規表現と in-memory env registry の構築です（[env_contract.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/env_contract.py:197)）。import 時の subprocess、network、filesystem write はなく、CLI 実行も `__main__` guard 内だけです（[silo_ladder_rung1.py:4842](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:4842)）。

submodule 未初期化時は `external/ccbench/cmake/ThirdParty.cmake` の `read_text()` が [同:870](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:870) で `FileNotFoundError` を上げます。ツールはこれを rc=2 とし、cache directory を作らず停止します。raw policy だけへ fallback したり、ツール内で `git submodule update --init` を実行したりしません。

新ツールは attempt の実行 module ではなく submit 前 helper なので、[_runtime_module_paths():252](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:252) には追加しません。追加すると closed-set test [test_silo_ladder_rung1_driver.py:745](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_silo_ladder_rung1_driver.py:745) と frozen driver hash の双方を壊します。

## テスト設計

既存の module loader は [test_pegasus_tools.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_tools.py:84)、local Git 初期化・user 設定・commit の書式は [同:882](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_tools.py:882)、parameterize の命名は [test_silo_ladder_rung1_driver.py:823](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_silo_ladder_rung1_driver.py:823) に合わせます。

fixture は `tmp_path` に次を作ります。

- 合成 repo root
- `tools/pegasus/policy.json`
- 最小 `external/ccbench/cmake/ThirdParty.cmake`
- masstree/mimalloc/googletest 用 local upstream Git repo 3 本
- gflags/glog 用 pinned-clean Git repo 2 本
- fake URL `https://github.com/fixture/NAME.git`
- temp Git config の `url."file:///...".insteadOf`
- `GIT_CONFIG_NOSYSTEM=1`、temp `GIT_CONFIG_GLOBAL`、`GIT_ALLOW_PROTOCOL=file`

これにより policy の GitHub URL validation を保ったまま、clone transport は必ず local `file` になります。rewrite が効かなければ HTTPS は protocol allowlist で即座に拒否されるため、network へ出ません。

ケースと primary invariant は 1 対 1 にします。

| ケース | pin する不変条件 |
|---|---|
| `test_missing_thirdparty_cmake_fails_before_git_or_writes` | 未初期化 submodule を fallback しない |
| `test_policy_cmake_drift_fails_before_acquisition` | imported `third_party_policy()` の同期 gate が実効 |
| `test_fetch_defaults_cache_to_gflags_parent` | P1 の既定 cache root |
| `test_cache_root_inside_repo_is_rejected` | cache は repo 外 |
| `test_fetch_publishes_complete_source_contract` | 新規 clone は pin/clean/origin を満たしてから公開 |
| `test_fetch_existing_sources_never_clone_fetch_or_pull` | 既存 clone は network/update しない |
| `test_verify_rejects_head_mismatch` | HEAD == pin |
| `test_verify_rejects_tracked_and_untracked_dirt` | porcelain が完全に空。tracked/untracked を parameterize |
| `test_verify_rejects_origin_mismatch` | origin URL の exact match |
| `test_verify_rejects_symlink_source` | source は実 directory |
| `test_fetch_failure_or_collision_never_publishes_partial_source` | clone failure/race の atomic no-replace |
| `test_hydrate_uses_frozen_submit_staging_path` | submitter の `destination` 分岐へ接続 |
| `test_hydrate_and_verify_issue_no_network_git_commands` | offline subcommand の network 分離 |
| `test_hydrate_existing_destination_is_verified_not_replaced` | 既存 staging を修復・上書きしない |
| `test_hydrate_copy_failure_leaves_destination_absent` | partial copy を公開しない |
| `test_verify_rejects_invalid_gflags_and_glog` | P3 の verify-only 拡張。2 dependency を parameterize |
| `test_default_hydrate_root_is_gitignored` | hydrate が tracked tree を汚さない |

全失敗ケースで rc=1/2 の区別と、既存 HEAD・destination marker が不変であることも確認します。

## P1 / P2 / P3 の裁定推奨

**(P1) 採用推奨。** cache root の既定を `gflags_source_path` の親にします。既存 policy の [policy.json:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/policy.json:14) から導出でき、新たな machine 固有 literal や環境変数を増やしません。非 Pegasus・テストでは `--cache-root` を明示できます。新 policy は registry 編集まで必要になり、`--cache-root` 必須だけでは日常運用の再現手順が毎回引数依存になるため、いずれも劣ります。

**(P2) 採用推奨。** hydrate の exact destination が frozen submitter の root と一致し、存在分岐だけをスキップして直後の pin/clean 検査と receipt freeze は維持されます。さらに job 側の persistent→scratch copy と再検査も残るため、consumer 接続に新しい shell seam は不要です。

**(P3) 採用推奨。** gflags/glog の path 直参照は frozen policy と job が現在の consumer です。job は [silo_ladder_rung1.sh:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/silo_ladder_rung1.sh:443) で path を読み、[同:473](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/silo_ladder_rung1.sh:473) で pin/clean を検査しています。今回は `verify` へ同じ readiness 検査を加えるだけにし、portable path 化や origin URL 束縛は policy/consumer の再凍結を伴う別 wave とします。

## 触ってはいけないファイル

絶対 no-touch は次の 4 本です。

| ファイル | 赤になる gate |
|---|---|
| `orchestrator/campaign/silo_ladder_rung1.py` | evidence の `binding["driver"]` hash |
| `tools/pegasus/silo_ladder_rung1.sh` | `binding["pbs_job"]` hash |
| `tools/pegasus/submit_silo_ladder_rung1.sh` | `binding["submitter"]` hash |
| `tools/pegasus/policy.json` | `binding["policy"]` hash |

照合は [test_silo_ladder_rung1_evidence.py:1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1195) から各実 file bytes を SHA-256 再計算しているため、1 byte でも変えると `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` が赤になります。

併せて次も編集しません。

- `_runtime_module_paths` とその closed-set test。追加すれば [test_silo_ladder_rung1_driver.py:745](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_silo_ladder_rung1_driver.py:745) が赤。
- `tools/pegasus/policies/*.json` と `registry_v1.json`。新 policy だけを置くと discovered/registered 閉集合照合 [test_pegasus_policy_registry.py:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_policy_registry.py:410) が赤。
- `external/ccbench/cmake/ThirdParty.cmake`。値を変えると `third_party_policy()` が drift を上げ、evidence の provenance 照合 [test_silo_ladder_rung1_evidence.py:665](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_silo_ladder_rung1_evidence.py:665) へ到達できない。
- README/docs は親の所有であり、段 5 worker の編集対象外。

なお新しい `fetch` は、現行 runbook が既に `submit_silo_ladder_rung1.sh` の外部三 repo clone を `unknown` と分類している経路と同族です（[pegasus-runbook.md:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/docs/pegasus-runbook.md:377)）。実 network fetch を login node で走らせる前に resource 分類が必要です。`hydrate` / `verify` も新規 script のため、[tools/README.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/README.md:18) に従って分類します。

pytest は read-only worker では実走しておらず、緑とは報告しません。今回の確認は静的読み取りのみで、作業木に変更はありません。

## 総括

- 新規 CLI は `fetch`（network）と `hydrate` / `verify`（offline）を分離し、各 source を atomic create-only で公開する。
- hydrate は frozen submitter の既存分岐と再検査へそのまま接続し、4 本の binding 対象を変更しない。
- 最大の未解決点は、実 network fetch が現行 Pegasus resource 規範では `unknown` のままであること。