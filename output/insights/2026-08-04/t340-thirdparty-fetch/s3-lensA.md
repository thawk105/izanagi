親 brief と段2プランは全文読了した。以下は静的検査のみで、pytest は実行していない。

### 所見 1 — hydrate は fresh checkout を消し、Git が無視する未固定バイナリを campaign に混入させる

**深刻度**: blocker

**根拠**: `s2-plan.md:81-92` は cache を `shutil.copytree(..., symlinks=True)` で `.git` ごと複製する。これにより `submit_silo_ladder_rung1.sh:173-194` の `clone --no-checkout`、pin object の存在を確かめる `checkout --detach`、空 worktree からの展開がすべて skip され、残るのは `submit_silo_ladder_rung1.sh:196-223` と `silo_ladder_rung1.sh:370-377` の HEAD/status 再検査だけである。

`/home/SFC/tanab/github/masstree/.gitignore:1-3,8-12` は `*.a`、`config.h`、configure 生成物を無視する。`external/ccbench/cmake/ThirdParty.cmake:57-78` は、まさに無視対象の `libkohler_masstree_json.a` と `config.h` を custom-command の OUTPUT とし、`ThirdParty.cmake:84-87` でその archive をリンクする。`git status --untracked-files=all` は ignored file を列挙しない。プランの dirty test も `s2-plan.md:195-197` の tracked/untracked だけで、ignored artifact を含まない。

**壊れる具体例**: cache の masstree に HEAD==pin、tracked status 空のまま、将来時刻を付けた改竄済み `libkohler_masstree_json.a` と `config.h` を置く → hydrate が両方を保存して複製 → submit/job の全検査が通る → CMake が既存 OUTPUT を再生成せず改竄 archive をリンク → `third_party_heads` は正しい pin のまま任意コードが binary に入る。この攻撃入力は構成例であり、現環境での発生を観測したものではない。

**最小の直し方**: `copytree` を廃止し、hardening 済みのローカル clone を一時 directory に作って `checkout --detach PIN` し、ignored/untracked file が存在しない fresh worktree を公開する。alternates/hardlink 依存を避けるため `--no-local` 相当または clone 後の自己完結化を要求する。ignored `*.a` と `config.h` を入れた fixture を必須回帰にする。

### 所見 2 — HEAD==pin と porcelain 空は content proof ではない

**深刻度**: blocker

**根拠**: 新 verifier は `s2-plan.md:50-63`、既存 verifier は `submit_silo_ladder_rung1.sh:6-20`、driver は `silo_ladder_rung1.py:903-961` のいずれも、HEAD と porcelain を content identity として扱う。

repo 内の強い proof reader はこれを信用していない。`s8b_ratified_freeze.py:282-343` は replace refs を無効化・拒否して blob を commit object から読む。`t080_freeze_migration.py:619-632` は shallow、replace、grafts、alternates を拒否する。`submit_t126_qualification.sh:114-116` は assume-unchanged/skip-worktree index bit を拒否する。`git_state.py:77-80` は submodule を明示的に無視しない status と recursive submodule 検査を使う。

成立する抜け穴は次のとおり。

- `refs/replace/PIN` で別 commit を置けば、`rev-parse HEAD` は PIN を表示しつつ、checkout/object 読み取りは replacement tree を使える。
- assume-unchanged/skip-worktree、sparse checkout は、worktree の変更・欠落を porcelain から隠せる。
- clean/smudge filter は worktree bytes を変換し、clean filter が元 blob 相当を返せば status を空にできる。
- uninitialized submodule や `submodule.*.ignore=all` は、gitlink 配下の欠落・差替えを親 status から隠せる。
- `.git` が linked-worktree の file、または `objects/info/alternates` がある repo をコピーすると、staging が cache 外の admin/object store に依存したままになる。
- shallow/grafts は単独で同一 OID の blob を変えるものではないが、「その pin が指定 origin の履歴から得られ、自己完結している」という proof を失わせる。`orchestrator/tests/README.md:101-103` も `--reference` alternates を同じ理由で拒否している。

**壊れる具体例**: cache に `refs/replace/<policy-pin>` を作り replacement commit の tree に改竄 source を置く → HEAD は policy pin、status は replacement tree に対して clean → hydrate と frozen verifier がすべて受理 → pin と異なる tree が build 入力になる。攻撃構成であり未観測。

**最小の直し方**: shallow、replace、grafts、alternates、promisor/partial clone、`.git` file、sparse checkout、特殊 index bit、submodule 未初期化を fail-closed に拒否する。最終的な build tree は hardened Git から PIN の tracked blob を新しい自己完結 repoへ展開し、path・mode・blob OIDまたは内容 SHA-256 の manifestを作って consumer 側でも再照合する。

### 所見 3 — verify 自体が cache/global Git config 由来の任意 command を実行する

**深刻度**: blocker

**根拠**: production 設計の clone/checkout/status/config 呼出し (`s2-plan.md:50-76`) には閉じた環境も hardening option もない。一方、テスト設計自身が `s2-plan.md:179-183` で `url.*.insteadOf` により、policy の HTTPS URLを保持したまま実 transport を local file に変えられることを利用している。したがって `remote.origin.url` の raw 一致は取得元を証明しない。

`test_dev_wave_land.py:805-843` は filter、included config、worktree config、promisor を攻撃面として扱い、`test_dev_wave_land.py:846-870` は `core.fsmonitor` が command を実行することを確認する fixture を持つ。既存の安全側実装は `t080_freeze_migration.py:541-556` で全 `GIT_*` を除去し、system/global config、replace、fsmonitor、untracked cache を止めている。`docs/ruleops.md:27-34` はさらに `GIT_NO_LAZY_FETCH=1` を固定する。

**壊れる具体例**: cache の `.git/config` に `core.fsmonitor=/path/payload` を置く → hydrate/verify の `git status` が検査前に payload を実行する。別例として global config の `url.*.insteadOf` で HTTPS を SSH に書き換え、`core.sshCommand` に payload を置く → raw origin は policy URL のまま clone transport だけが差し替わる。

**最小の直し方**: 全 Git 子 process を、既存の `_git_env()` と同等の閉じた環境、`core.hooksPath=/dev/null`、fsmonitor/replace/lazy-fetch 無効で実行する。任意 cache は Git command を起動する前に `.git/config` を no-follow・`--no-includes` 相当で読み、`include.*`、`filter.*`、hooks、fsmonitor、sshCommand、promisor/partial-clone、外部 upload-pack 等を allowlist 外として拒否する。

### 所見 4 — 取得経路は receipt/provenance に一切漏れず、「由来を台帳から追える」は偽

**深刻度**: blocker

**根拠**: `brief.md:24-27` は値を変えず由来の追跡可能性を改善すると主張する。しかし submit receipt の exact keys は `silo_ladder_rung1.py:2394-2424` の既存 hash 群と `third_party_heads` だけで、新 helper、cache root、取得方式を含まない。`_runtime_module_paths()` も `silo_ladder_rung1.py:252-267` の閉集合であり、プランは `s2-plan.md:166` で helper を意図的に除外する。

`third_party_sources` は `silo_ladder_rung1.py:954-960` の policy値、`resolved_path`、HEAD/statusだけである。`resolved_path` は job/campaign 内の staging/scratch pathであって cache 取得元ではなく、correctness/gap identity比較からも `silo_ladder_rung1.py:1577-1590` で除外されている。evidence testも `test_silo_ladder_rung1_evidence.py:665-681` で origin、cache、helper hash、source manifest、`resolved_path` を検査しない。成果物自身も `silo_ladder_rung1.py:4695-4699` で third-party rederivation を `sha256-chain-consistency-only` と明記する。

したがって、取得経路の変更は値として漏れない。`third_party_heads` が不変なのは事実だが、traceability 改善も証明されない。また helper を必須工程と解釈すれば、origin exact-one 等を追加するため、frozen verifierなら受理する pinned-clean mirrorを helperは拒否し、end-to-end の受理集合は変わる。helperを任意と解釈すれば直接 staging を埋めて迂回できる。この二つを同時に「受理集合不変かつ由来追跡可能」とはできない。

**壊れる具体例**: HTTPS fetch、`insteadOf` 経由の local clone、手作業コピー、改竄 cache hydrateのいずれでも、最終 HEAD/statusとscratch pathが同じなら同一の submit receipt/provenanceになる → evidence から実行経路を再構成できない。

**最小の直し方**: helper bytes/version、operation種別、canonical cache identity、実 transport、Git hardening状態、各 source snapshot manifestを acquisition receipt に記録し、その hashを submit/campaign-root/provenanceへ束縛する。これは frozen evidence contract の再発行を要する。4本を凍結したままなら、「operator convenienceであり proof chainには含まれない」と scopeを縮める。

### 所見 5 — cache の path 検査と atomic publish は TOCTOU を閉じていない

**深刻度**: blocker

**根拠**: `s2-plan.md:44-48` は事前の `resolve(strict=False)`、`s2-plan.md:52-60` は final component検査、`s2-plan.md:81-92` は path指定の `copytree` である。`renameat2(RENAME_NOREPLACE)` は `s2-plan.md:103-110` の destination公開だけを原子的にし、source directory、親 component、`.git` 内部、copy中の名前解決は固定しない。

既存 collector は `collector.py:104-124` で全親 componentを lstatする。より強い実装は `dev_wave_land.py:220-271` で dirfd、`O_NOFOLLOW`、open前後のinode一致を使う。`check_docs.py:567-602` も finalだけでなく親symlinkを拒否する。

**壊れる具体例**: cache sourceを検査後、同一UID processが親directoryをrenameして、同じHEAD/statusだがignored archiveを持つdirectoryへ差し替える → path-based copyが別inodeを読む → 再検査時には同じ弱いHEAD/statusが成立 → publish成功。copy中にdirectory entriesを差し替えれば複数時点のhybrid snapshotにもできる。攻撃構成であり未観測。

**最小の直し方**: cache rootから各componentをdirfd＋`O_DIRECTORY|O_NOFOLLOW`で開き、inode identityを保持したままsnapshotする。`.git`管理面を外部cacheから丸ごと複製せず、private stagingにfresh展開してmanifestを再計算する。same-UID adversaryまで境界に含めるなら、通常のownership/modeだけでは閉じないため、consumer直前のcontent再照合をreceiptへ束縛するか、そのadversaryを明示的にtrust boundary外へ裁定する必要がある。

### 所見 6 — gflags の親を cache root にする根拠は一時点観測だけで、管理境界も機械化されない

**深刻度**: must-fix

**根拠**: P1 は `brief.md:48-52` と `s2-plan.md:23-27,211-212` で、凍結された `gflags_source_path` の親を5 repo共通cacheとみなす。実体は `policy.json:14-17` の `/home/SFC/tanab/github/{gflags,glog}` という特定UID・machineの絶対pathである。「新しいmachine固有literalを増やさない」だけで、既存literalへの依存は残る。

現環境では `/home/SFC/tanab/github/gflags/.git/shallow:1` と `glog/.git/shallow:1` が存在し、gflagsには `.gitmodules:1-4` もある。少なくともgflags/glogは、三つの新規managed cloneと同一のself-contained管理形態ではない。さらにプランは `s2-plan.md:63` でgflags/glogのoriginを検査しないため、親briefの「origin一致」という一時点観測は将来のgateにならない。

**壊れる具体例**: 別machineでgflagsだけを `/vendor/gflags` に置く → その親に無関係な `masstree` directoryが存在 → default cacheとして解釈されverify停止、または新規repoを他管理主体のdirectoryへ作る。policyの絶対pathを持たない利用者にはdefault自体が成立しない。

**最小の直し方**: `--cache-root` を必須にするか、専用cache rootを環境/policyで明示し、ownership・用途・lifecycleを裁定する。gflags/glogのreadiness pathと三sourceのmanaged cacheを同じ管理単位として推論しない。

### 所見 7 — 凍結4本の静的束縛は存在するが、新規test追加だけで別gateに捕まる

**深刻度**: must-fix

**根拠**: `test_silo_ladder_rung1_evidence.py:1172-1207` は driver、PBS job、submitter、verifier module、policyの5 pathとruntime module集合を実bytesから再hashする。read-onlyのSHA-256計算では現在bytesとcommitted bindingが一致した。したがって凍結4本を変更すれば静的assertionが不一致になる。ただし、親が実行したという測定runのlogはbrief/planに無く、「実測した」という履歴自体は裏取りできない。

逆方向では、新規 `orchestrator/tests/test_pegasus_thirdparty_fetch.py` に自走harnessを付けなければ、`test_plain_runner_coverage.py:44-74` が全 `test_*.py` を走査してoffenderにする。規約は `orchestrator/tests/README.md:114-120` に明記されているが、`s2-plan.md:168-207` のtest設計にはharnessがない。これは凍結4本を触らず、新規file追加だけで成立するgate経路である。

一方、`test_pegasus_policy_registry.py:410-427` は `tools/pegasus/policies/` だけをscanし、新helperは対象外。`tools/check_docs.py:33-63` に `tools/pegasus/README.md` はなく、`tools/README.md:28-31` は新scriptの分類registry/gateが存在しないと明記する。`hooks/README.md:15-18` によりCodex hookも未配線である。つまりhelper本体をproof bindingへ入れる自動gateはない。

**壊れる具体例**: planどおりtest fileを追加するが `__main__` を付けない → 凍結4本とevidence hashは不変でもplain-runner閉集合assertionが新fileを拒否する。これは条件分岐の静的帰結であり、test実行結果の主張ではない。

**最小の直し方**: 新testに実際にpytestを起動する `__main__` harnessを付ける。helperをproofの一部とするならruntime/acquisition bindingを別裁定で追加し、凍結再発行を受け入れる。

### 所見 8 — fetch/hydrate/verify はいずれも未分類で、規律上実行できる場所がない

**深刻度**: blocker

**根拠**: `tools/README.md:8-19` は新scriptを必ず再分類し、unknownをdispatch-requiredとして扱い、sanctioned経路がなければ停止すると定める。`docs/pegasus-runbook.md:377-384` は既存submitterの外部repo cloneを既にunknownと列挙する。計算nodeは `tools/pegasus/README.md:23-30` のとおり直接外部networkを使えない。プラン自身も `s2-plan.md:237` で三subcommandすべて未分類と認めている。

fetchはclone規模、hydrateはcache tree全体、verifyはunbounded worktreeのstatus走査であり、入力上限がない。したがって規範上は三つともunknownである。

**壊れる具体例**: login nodeでfetch → unknown/dispatch-required実行となり規律違反。計算nodeへ送る → GitHubへ直接到達できず機能しない。hydrate/verifyも「offlineだから軽い」とは分類できず、cacheに巨大ignored treeがあれば上限不明のままである。

**最小の直し方**: 実装前にhard capとcgroup charged-memoryを含むresource分類を裁定する。network取得をlogin側の上限制御された転送、snapshot生成をcompute側へ分けるなど、network制約とresource規範の双方を満たすsanctioned経路を先に作る。

### 所見 9 — このwaveが接続するのはrung1だけで、他campaignとprobeは取得gateを迂回する

**深刻度**: must-fix

**根拠**: 実効層を数えると、scope内は login operatorのfetch/hydrate/verify、frozen submitterの存在分岐、compute jobのpersistent→scratch copy、変更されないdriver/evidence、helper単体のlocal fixture testの5層である。

scope外のconsumerは次のとおり。

- certify: `certify_calibration.sh:495-516` はfresh CCBenchを直接CMake configureし、三source overrideがない。
- floor: `between_run_floor.py:159-167` はgeneric `buildcache.build()`を使い、`buildcache.py:481-502` はdependency prefixしか渡さない。
- t126 qualification: `t126_qualification.sh:513-575` が明示的にstageするのはgflags/glogだけである。
- t139 probe: `t139_positive_control_probe.pbs:25-40` は別途 `IZANAGI_THIRDPARTY_SOURCE_ROOT` を要求し、`t139_positive_control_probe.sh:20-28` がoverrideするが、新helperとの呼出し接続はない。
- t141: `t141_region_profile.sh:1172-1180` のdirect CMakeに三source overrideがない。
- t152: `t152_write_intent_coverage.py:341-378` のfresh direct-CMakeにもoverrideがない。
- generic CMake/CI: `external/ccbench/CMakeLists.txt:37-43` は常にThirdPartyをincludeするため、上記すべてがFetchContent経路へ入る。

さらに `policy.json:52-53` はmimallocを `fetchcontent_ref=v2.3.2`、pinをcommit SHAと分離する。`silo_ladder_rung1.py:893-899` はrefが40 hexの場合しか両者を照合しない。現cacheのread-only Git照会では `v2.3.2` はannotated tag object `ed34…` から現在pin `02a2…` へ解決したが、この対応はgateではない。`ThirdParty.cmake:106-112` のoverride外consumerは今後動いたtagを取得できる。

**壊れる具体例**: rung1用hydrateを完了してcertify/floor/t141を実行 → それらのCMakeにはsource overrideがなく、計算nodeでFetchContent network failure、または別cache・可変tagを利用 → 新gateは存在しても実験層には効かない。

**最小の直し方**: 裁定パッケージを作り、T340を「rung1専用operator helper」と明記して certify/floor/t126/t139/t141/t152/CI を後続waveへ列挙するか、共通source-root契約を全CMake consumerへ接続する。後者はfrozen fileとevidenceの再発行を伴う。annotated tagもcommit pinへ統一するか、tag objectとpeeled commitの対応を取得receiptへ束縛する。

## 総括

- blockerあり。最重は ignored build artifact の混入、Git metadata/configによるpin・command実行の偽装、取得経路がproof chainから完全に消える点。
- 外部cacheのTOCTOUと、規律上実行可能な場所がない点もblocker。
- 凍結4本のbytes束縛は静的に存在するが、新規testのplain-runner gateとhelper非束縛は別問題として残る。
- 現プランの実効範囲はrung1だけであり、他campaign/probeは裁定パッケージが必要。