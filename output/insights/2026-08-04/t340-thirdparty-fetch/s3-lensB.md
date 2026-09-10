静的検査のみ。pytest・build・実 network fetch は実行していない。

### 所見 1 — T-340 の producer/consumer を取り違え、新ツールは実害を起こした probe に接続されない

**深刻度**: blocker

**根拠**: 実害は T-139 wave 中に、削除済み worktree の staging が消えた事象である。[worklog:345](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/docs/archive/worklog-phase3-0802-117-121.md:345) は三 source を手で `~/github` へ取り直したと記録する。その probe は `IZANAGI_THIRDPARTY_SOURCE_ROOT` を必須にし、そこから三本を copy する。[t139_positive_control_probe.pbs:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/probes/t139_positive_control_probe.pbs:25)、[同:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/probes/t139_positive_control_probe.pbs:35)。実装記録にも `qsub -v IZANAGI_THIRDPARTY_SOURCE_ROOT=...` が人間の手番として残る。[s5-impl.md:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/output/insights/2026-08-02_t139-positive-control-probe/s5-impl.md:45)。

一方、プランの `hydrate` は rung1 staging への固定配置だけである。[s2-plan.md:23](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:23)。probe を起動する wrapper も、新ツールを呼ぶ既存コードもない。

既存 `--prepare-third-party-only` は network clone・checkout・HEAD/clean 検証を既に行う。[submit_silo_ladder_rung1.sh:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:40)、[同:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:173)、[同:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:225)。新案との差は「repo 外 cache へ永続化する `fetch`」と「そこから offline copy する `hydrate`」だけであり、取得機能自体は重複している。その差分を利用する live caller がない。

**壊れる具体例**: `fetch` で永続 cache を作っても、人間が従来どおり probe を qsub すると環境変数が欠けて rc=2、または削除済み worktree の staging を指定して `realpath -e` で停止する。永続 cache は存在するのに consumer は一度も読むことがない。

**最小の直し方**: T-139 probe を scope に戻し、cache 検証後に `IZANAGI_THIRDPARTY_SOURCE_ROOT=<resolved cache>` を設定して probe を投入するコード上の wrapper を置く。probe を廃止済みと裁定するなら、その事実を明記し、T-340 の実害を閉じたとは主張しない。rung1 用にも `hydrate → frozen submitter` を一命令で実行する wrapper が必要。

### 所見 2 — hydrate の呼び忘れで「worktree を畳んだら消える」がそのまま再発する

**深刻度**: blocker

**根拠**: brief は「先に staging を埋めれば consumer 接続」とするだけで、呼び出しを強制していない。[brief.md:53](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/brief.md:53)。submitter は destination が無ければ無条件に GitHub clone へ戻る。[submit_silo_ladder_rung1.sh:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:143)、[同:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:152)、[同:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:173)。プラン自身も「新しい shell seam は不要」としている。[s2-plan.md:213](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:213)。

**壊れる具体例**:

1. `git worktree add <new-worktree> <branch>`。
2. submodule を初期化する。これは fresh worktree で別途必要と runbook に明記される。[pegasus-runbook.md:512](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/docs/pegasus-runbook.md:512)。
3. 人間が `hydrate` を忘れ、既存 submitter を直接実行する。
4. line 173 が真になり、三 repo を新 worktree の `output/.../job-staging` へ clone する。
5. worktree を削除すると三 repo も消える。repo 外 cache は一度も参照されない。

`--prepare-third-party-only` を使っても配置先は同じなので結果は変わらない。

**最小の直し方**: 日常の canonical entry point を `hydrate + submit` の合成コマンドにし、hydrate を独立した「覚えて実行する手順」にしない。受入テストでは worktree を二回作り直し、二回目は `git clone/fetch/pull` を poison した状態でも canonical submit が frozen submitter まで到達することを確認する。旧 submitter の直接実行を機械的に止められないなら、その残存 bypass を明記する。

### 所見 3 — network fetch を規律どおり実行できる場所がない

**深刻度**: blocker

**根拠**: 新 `fetch` は hard cap のない full clone である。[s2-plan.md:67](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:67)、[同:72](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:72)。同型の既存 submitter clone は login-side `unknown` と既に分類されている。[pegasus-runbook.md:377](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/docs/pegasus-runbook.md:377)、[同:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/docs/pegasus-runbook.md:384)。

`unknown` は `dispatch-required` と同じ扱いで、sanctioned 経路がなければ停止する規律である。[tools/README.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/README.md:8)、[同:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/README.md:14)。自動 dispatch の閉じた task は tests/provenance の二本だけである。[pegasus-runbook.md:368](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/docs/pegasus-runbook.md:368)。計算ノードは外部 network を直接使えない。[tools/pegasus/README.md:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/README.md:28)。プランはこの矛盾を「実行前に分類」と後送りしている。[s2-plan.md:237](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:237)。

**壊れる具体例**: cache が空のとき、login node で `fetch` を実行すれば resource 規律違反。計算ノードへ移せば clone が network/DNS で失敗する。実装しても sanctioned な初回取得手順が存在しない。

**最小の直し方**: 段 4 で取得を走らせる実行面を先に裁定する。候補は、入力上限を機械化して login 実行を再分類する、共有 cache を見られる network-capable 外部 host 用手順を runbook に置く、または別の sanctioned fetch job を設計する、のいずれか。分類未決のまま CLI だけ置かない。

### 所見 4 — P1 の既定 `/home` では初回 publish が既知の EINVAL で必ず止まりうる

**深刻度**: blocker

**根拠**: 現 policy の gflags 親は `/home/SFC/tanab/github` である。[policy.json:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/policy.json:14)。Pegasus `/home` では `renameat2(RENAME_NOREPLACE)` が `EINVAL` になることが実測済みである。[pegasus-runbook.md:508](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/docs/pegasus-runbook.md:508)。

既存 calibrator はこのため link+unlink fallback を実装している。[cli.py:297](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/calibrator/cli.py:297)、[同:307](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/calibrator/cli.py:307)。ところがプランは同実装を「同型」と引用しながら、非対応 FS では fallback せず rc=2 とする。[s2-plan.md:103](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:103)、[同:108](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:108)。しかも既存 fallback の `os.link` は directory にはそのまま使えない。

**壊れる具体例**: `/home/SFC/tanab/github/masstree` が存在しない初回実行で、clone・checkout・stage 検証までは成功するが publish が `EINVAL`、rc=2 で終了する。現在三 repo が既に存在する環境ではこの失敗経路が隠れる。

**最小の直し方**: clone 前に FS capability を検査して非対応 root を拒否するか、directory 用の create-only lock/publish 方式を設計する。少なくとも `renameat2` へ `EINVAL` を注入するケースを追加し、既定 cache root で初回 publish 可能という前提を実機規範と突合する。

### 所見 5 — cache root を gflags の親から導く P1 は無関係な policy field に保存場所の意味を混入する

**深刻度**: must-fix

**根拠**: `gflags_source_path` は job が gflags の build source として直接読む field である。[silo_ladder_rung1.sh:443](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/silo_ladder_rung1.sh:443)、[同:473](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/silo_ladder_rung1.sh:473)。その親を masstree 等の cache namespace とする契約は policy に存在しない。brief が新しい意味を後付けしている。[brief.md:48](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/brief.md:48)。

ストレージ規範は、小さい source は `/home`、大きな永続データは `/work` を優先し、quota を確認するとしている。[pegasus-runbook.md:258](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/docs/pegasus-runbook.md:258)、[同:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/docs/pegasus-runbook.md:270)。環境固有手順の正本は専用 runbook である。[CLAUDE.md:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/CLAUDE.md:142)、[docs/README.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/docs/README.md:38)。

**壊れる具体例**:

- gflags を `/work/SFC/alice/deps/gflags` へ移すだけで、三 repo の cache も無関係に `/work/SFC/alice/deps` へ移動し、旧 cache を再利用しない。
- 別ユーザー・別 host では current literal `/home/SFC/tanab/...` が他人の領域になり、既定 fetch は書けない。
- policy が `~/github/gflags` になった場合、command substitution から得た `~` は shell で再展開されない。新 Python が `expanduser()` すれば shell consumer と意味が分裂し、しなければ cwd 相対の `~/...` になる。
- 「current repo の外」という検査だけでは、別の削除予定 worktree 配下を cache root にしても通るため、永続性を証明しない。
- full-history clone の将来サイズは hard cap がなく、gflags の場所から home/work の容量判断を導けない。

**最小の直し方**: cache root は絶対パスの必須 `--cache-root` または必須 site-local 環境変数にし、Pegasus での選び方と quota 確認を `docs/pegasus-runbook.md` に置く。repo-tracked policy にはユーザー固有 cache path を入れない。cache は `<root>/<name>/<pin>` の専用 namespace にし、pin 更新時に旧 clone の削除を要求しない。

### 所見 6 — 新 Python の強い検査は frozen consumer に届かず、shell 二本との drift は閉じない

**深刻度**: must-fix

**根拠**: frozen submitter と job の共通 verifier は directory、HEAD、status しか見ない。[submit_silo_ladder_rung1.sh:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:6)、[silo_ladder_rung1.sh:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/silo_ladder_rung1.sh:17)。receipt も三 HEAD だけを保存する。[submit_silo_ladder_rung1.sh:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:199)、[同:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:217)。

新 Python は repo root と exact-one origin まで要求する。[s2-plan.md:50](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:50)。しかし frozen 四本を変更しない scope である。[brief.md:31](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/brief.md:31)。したがって新検査は submit 時の authority ではなく、任意実行の preflight に留まる。

pin driftにも別穴がある。mimalloc は CMake ref が tag `v2.3.2`、policy pin は SHA で別 field である。[policy.json:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/policy.json:49)。`third_party_policy()` が ref/pin 一致を検査するのは ref が40-hexの場合だけである。[silo_ladder_rung1.py:893](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/silo_ladder_rung1.py:893)。

**壊れる具体例**:

- hydrate 後に `git remote set-url origin https://attacker.invalid/x.git` とする。.git/config の変更は worktree status を汚さないため、frozen submitter・job・receipt は全て受理する。
- 新ツールを飛ばして、別 repo の subdirectory を staging に置く。親 repo の HEAD が偶然 pin と一致すれば shell は `--show-toplevel` を検査しない。
- mimalloc の `pin` だけ B へ更新し `fetchcontent_ref=v2.3.2` を残すと、新 cache/rung1 は B、source override のない campaign は tag A を build するが、現行同期検査は通る。

**最小の直し方**: 新-file-onlyを維持するなら「最終 authority は shell の HEAD/clean だけ」と主張を格下げし、Pythonとの共通部分を同一 corpus で比較する conformance test を置く。origin/repo-root を受理条件にするなら frozen submitter・job・receipt を再版して共有 verifier または束縛済み verification receipt を消費させる必要があり、現 scope では構造的に閉じない。tag は解決 SHA を明示的に検査する。

### 所見 7 — rung1 以外の floor / certify / T-126 / probes は同じ FetchContent 穴を持つ

**深刻度**: must-fix

**根拠**:

| 層 | 実コードの source 経路 |
|---|---|
| certify | fresh CCBench worktree を作るが、CMake argv は gflags/glog prefix のみで三 source override がない。[certify_calibration.sh:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/certify_calibration.sh:503)、[同:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/certify_calibration.sh:506) |
| floor | `buildcache.build_v2` を呼ぶ。[s8b_floor_campaign.py:1003](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/s8b_floor_campaign.py:1003)。その configure argv に `FETCHCONTENT_SOURCE_DIR_*` はない。[buildcache.py:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/buildcache.py:481)、[同:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/campaign/buildcache.py:492) |
| T-126 qualification | CCBench だけを `/scr` へ archive し、三 source は staging しない。[t126_qualification.sh:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/t126_qualification.sh:524)。driver は通常 pipeline/buildcache を使う。[t126_driver.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/qualification/t126_driver.py:524) |
| T-139 probe | `IZANAGI_THIRDPARTY_SOURCE_ROOT` という consumer seam はあるが producer wrapper がない。[t139_positive_control_probe.pbs:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/probes/t139_positive_control_probe.pbs:25) |
| T-141 probe | CCBench copy を構築するが configure argv は gflags/glog prefix のみ。[t141_region_profile.sh:817](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/t141_region_profile.sh:817)、[同:1172](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/t141_region_profile.sh:1172) |

CCBench は configure 時に `ThirdParty` を無条件 include する。[external/ccbench/CMakeLists.txt:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/external/ccbench/CMakeLists.txt:37)、[同:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/external/ccbench/CMakeLists.txt:43)。三依存は `FetchContent` により取得される。[ThirdParty.cmake:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/external/ccbench/cmake/ThirdParty.cmake:42)、[同:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/external/ccbench/cmake/ThirdParty.cmake:106)、[同:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/external/ccbench/cmake/ThirdParty.cmake:130)。

**壊れる具体例**: fresh `/scr` で certify、floor、T-126、T-141 のいずれかを current CCBench に対して configure すると、三 source override がないため FetchContent が外部取得へ進む。計算ノードに network がなければ configure で停止する。rung1 だけ直しても同型事故は残る。

**最小の直し方**: 今 wave で全部直さないなら、少なくとも次を別裁定パッケージとして明記する。

- certify/T-141 の CMake argv へ verified cache projection を追加。
- floor/T-126 の buildcache 契約へ三 source identityとsource-dirを追加。
- T-139 の qsub wrapper を実体化。
- 各層で HEAD/clean/source-set を receipt または build argv に束縛。

### 所見 8 — CLI の rc・出力・`verify` 意味が tools/pegasus の慣習と整合しない

**深刻度**: must-fix

**根拠**: プランは `run_probe.py` を「例外を stderr 一行、rcを返す」先例として挙げるが、同ツールは成功・失敗とも JSON を stdout に出し、import/probe/write を rc=2/3/4 に分ける。[s2-plan.md:9](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:9)、[run_probe.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/run_probe.py:47)、[同:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/run_probe.py:103)。

最も近い subcommand 先例 `collect_t126_qualification.py` は引数を必須にし、失敗を rc=2、成功時に成果物 path を stdout へ出す。[collect_t126_qualification.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/collect_t126_qualification.py:12)、[同:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/collect_t126_qualification.py:47)。frozen submitterも source contract 違反を rc=2へ写像する。[submit_silo_ladder_rung1.sh:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:196)。

新案は source違反だけrc=1、運用失敗rc=2とする一方、成功時のstdout形式を定義していない。[s2-plan.md:113](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:113)。また `verify` は三 source cache と別 consumerであるgflags/glog readinessを混在させる。[同:94](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:94)。

**壊れる具体例**: wrapper が既存 Pegasus CLI と同じく rc=2 を「検証失敗」と扱うと、新ツールの rc=1 を未分類にする。stdoutにresolved cache pathや構造化結果がないため、probe wrapperは再び同じpathを別ロジックで導出する。別hostで三 cacheだけ検査したい場合も、無関係なtanab固定gflags/glog欠落で `verify` が失敗する。

**最小の直し方**: `verify-cache` と `verify-rung1-readiness` を分離する。成功時は versioned JSONまたはresolved rootをstdoutへ出し、stderr/rc契約を既存の近いCLIに合わせる。`tools/pegasus/README.md` の手順連鎖にも実コマンドと出力を記載する。

### 所見 9 — テスト一覧は主要事故を再現せず、各ケースの mutation oracle も未定義

**深刻度**: blocker

**根拠**: プランはケース名と説明だけで、assert・実 consumer・一行変異を定めていない。[s2-plan.md:185](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s2-plan.md:185)。既存 rung1 テストには、flag文字列と成功messageがsource中に存在するだけを検査する例がある。[test_silo_ladder_rung1_driver.py:2246](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_silo_ladder_rung1_driver.py:2246)、[同:2251](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_silo_ladder_rung1_driver.py:2251)。同型にすると呼び出し不能でも通る。

新規ファイルは未在なので行番号は捏造しない。実装後、少なくとも次の一行変異で対応テストが失敗する設計が必要である。

| プランのケース | 検出すべき一行変異 |
|---|---|
| missing CMake | `third_party_policy()` 失敗時に raw policy へ fallback する |
| policy/CMake drift | `third_party_policy(repo_root)` を raw JSON load に置換する |
| default cache | `.parent` を `.parent.parent` に変える。ただしこれは不適切なP1を固定するだけで安全性テストではない |
| cache inside repo | repo containment 条件を常に偽にする |
| fetch publish | stage検証より前にpublishする |
| existing never network | 既存repo分岐へ `git fetch` を一行追加する |
| HEAD mismatch | `observed_head != pin` を常に偽にする |
| tracked/untracked dirty | `--untracked-files=all` を落とす。tracked/untracked双方のfixtureが必要 |
| origin mismatch | origin比較条件を常に偽にする |
| symlink | final-component symlink拒否を削る |
| failure/collision | no-replace publishを `os.rename` に置換する。既存空directoryのinodeを保持できるかで見る |
| frozen staging path | destinationを別directoryへ変える。定数比較でなくactual frozen submitterをclone-poison下で実行する |
| offline commands | hydrate/verifyへ `git fetch` を一行追加する |
| existing destination | 検証分岐を `rmtree + copy` に置換する。marker/inode不変を検査する |
| copy failure | copy完了前にpublishする。途中で例外を注入し正式destination不在を検査する |
| invalid gflags/glog | 検査loopをgflagsだけに縮める。dependencyだけでなくHEAD/dirty/symlinkも分岐させる |
| gitignored | [.gitignore:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/.gitignore:24) を除去し、actual `git status --porcelain --untracked-files=all` を見る |

**壊れる具体例**:

- `test_hydrate_uses_frozen_submit_staging_path` が tool と同じ imported constantを期待値にすれば、toolと期待値が同時に誤る恒真テストになる。
- pin不一致・dirty・origin差し替えはlocal Git fixtureで再現できるが、actual submitterを呼ばなければconsumer接続は証明しない。
- worktree消滅のケース自体が一覧にない。real `git worktree add/remove/add` と外部cacheを用いて再現可能。
- partial cloneも一覧にない。bare upstreamでfilterを許可し、`file://`・`--no-local --filter=blob:none`、promisor設定、`GIT_NO_LAZY_FETCH=1`を使えば再現できる。ただし現プランは「partialを拒否するか」「HEAD到達objectだけ完備なら許すか」のoracle自体を定義していない。

**最小の直し方**: 上表を段4のmutation事前登録にする。さらに、二つのreal worktreeを順に作成・破棄し、二つ目でnetwork verbを拒否してもcanonical wrapperからactual frozen submitterまで通るE2Eを追加する。partial cloneは受理意味を先に裁定し、拒否するならpromisor設定とHEAD到達object欠落を検査する。

## 総括

- 最重は、実害のconsumerであるT-139 probeにもrung1 submit経路にも新ツールのlive callerがないこと。
- hydrate忘れで既存submitterが再cloneするため、worktree消滅事故は同じ手順で再発する。
- `/home`の既知`renameat2=EINVAL`と、network fetchを走らせるsanctioned host不在も初回取得を阻む。
- blockerあり（所見1〜4・9）。現プランのまま段5へ進めない。