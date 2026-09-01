## 1 正当な build

[severity: nit] 凍結済み 12 cell に、snapshot 自体への CMake 書込み経路は見つからなかった。

- top-level が到達するのは `cc/*` と opt-in の `microbench` だけで、checkout 内の `third_party/shirakami` CMake は通常 build graph に入らない (`external/ccbench/CMakeLists.txt:81-94`)。
- `file(WRITE)` は protocol matrix を `${CMAKE_BINARY_DIR}` へ出す (`external/ccbench/CMakeLists.txt:85-87`, `external/ccbench/cmake/ProtocolHelpers.cmake:138`)。
- `configure_file` は shirakami 内にあるが、出力先は `${CMAKE_CURRENT_BINARY_DIR}` (`external/ccbench/third_party/shirakami/CMakeLists.txt:98-105`) で、かつ通常 graph から未到達。
- source 側へ書く唯一の到達可能な custom command は masstree である。`config.h`、11 object、archive を `masstree_SOURCE_DIR` 内で生成する (`external/ccbench/cmake/ThirdParty.cmake:57-78`)。
- `stock_common`、`p2_2_flag_opt`、`backoff_fixed_best`、`system_gate`、`ident_all` は `FETCHCONTENT_BASE_DIR` を渡さず、実測済み completion では staging の `_deps/masstree-src` へ解決されていた (`output/insights/2026-09-01_t2027-root-class2/probe-d1192-conditions.md:35-38`)。
- `sort_best` は `FETCHCONTENT_BASE_DIR` と 3 個の `FETCHCONTENT_SOURCE_DIR_*` を外部 dependency treeへ渡す (`orchestrator/campaign/s8b_floor_campaign.py:4233-4263`)。その base は repo 内を明示的に拒否する (`orchestrator/campaign/s8b_floor_campaign.py:3090-3106`)。

したがって、現 freeze に「masstree が snapshot 内へ書く組合せ」はない。危険な一般形は `FETCHCONTENT_BASE_DIR=<snapshot内>` または `FETCHCONTENT_SOURCE_DIR_MASSTREE=<snapshot内>` であり、その場合は全 configuration で masstree build が EROFS になる。ただし現正式経路はその指定を作らない。

depfile も staging 側である。buildcache 自身が `.o.d` は staging lifetime 内にあると記述している (`orchestrator/campaign/buildcache.py:2637-2645`)。`-MD -MF` が snapshot 内へ出る経路は見つからなかった。

[severity: should-fix] ccache の環境依存はプランから落ちている。

CCBench は PATH 上に ccache があれば自動 launcher 化する (`external/ccbench/CMakeLists.txt:20-29`)。build subprocess は基本的に親環境を継承する (`orchestrator/campaign/buildcache.py:2604-2608`, `:3376-3389`)。現 login node には ccache も `CCACHE_*` 環境変数もなかったが、計算ノードで `CCACHE_DIR`、`CCACHE_TEMPDIR`、`CCACHE_LOGFILE` が snapshot 内を指せば正当な compile を壊す。計算ノード probe で実効 ccache 設定を保存し、snapshot 外であることを要求すべきである。

[severity: must-fix] tmpfs 容量の根拠が不足している。

現 worktree の `external/ccbench` は次の実測だった。

- apparent size: 12,213,725 bytes
- allocated blocks: 15,548,416 bytes
- `.git` 除外後: 1,438 files、267 directories、raw 11,111,504 bytes
- 4 KiB page 丸め後の file payloadだけで 14,434,304 bytes

従って `size=12M` 相当では copy 中に ENOSPC になりうる。さらにプランは全 node をコピーする一方、tree digest は `.git` を除外する (`orchestrator/campaign/s8b_expected_materialization.py:42-45`, `:225-251`) ため、digest 対象だけのサイズを上限根拠にできない。

一方、実 per-cell snapshot を作る `git worktree add` 経路 (`orchestrator/campaign/patchharness.py:346-372`) の HEAD は 404 blob、raw 2,352,405 bytes、page 丸め 3,321,856 bytesで、初期化済み nested submoduleを含む現在の物理 checkout より小さい。正式 configuration の build 中 snapshot 増分は、上記書込み追跡上は 0 bytes である。

実装では少なくとも「copy 対象全 nodeの page丸め値 + 固定余裕」を導出し、例えば 32 MiB・4,096 node 程度の明示上限を置くべきである。「約12 MBを十分含む」だけでは検査可能な契約にならない。

## 2 テスト所要

[severity: must-fix] 実 CMake canary の増設は、受入テストへ入れる形では採用できない。

正本は次のとおりである。

- D311: 「開発を進めれば進めるほどテスト時間が増えていって開発できなくなる状況を避ける」。非飽和で 1.1 倍なら land せず、並列化または仕事量削減を要求する (`docs/decisions.md:14266-14278`)。
- D678: 「main への着地は 1 タスクあたり 5 分以内」。超える設計は採らない (`docs/decisions.md:26752-26757`)。
- D289: 独立 job は並行投入し、直列は具体的な四理由に限定する (`docs/decisions.md:13201-13210`)。
- 実 repo writer は安全上 `real-repo` group へ直列化される (`docs/decisions.md:2398-2423`)。現 canary 3件もその group に登録済みである (`orchestrator/tests/conftest.py:343-350`)。

現 acceptance ledger は、該当 canary をすべて `0.0` 秒と記録している。

- legacy floor canary: `0.0`
- v2 floor canary: `0.0` (`orchestrator/tests/acceptance_duration_ledger.json:13722-13723`)
- oracle real-build canary: `0.0` (`:14321`)

これは速いという意味ではなく、skip 条件の値である。現環境には `gcc-13` / `g++-13` がなく、canary はそれらを要求する (`orchestrator/tests/test_s8b_floor_campaign.py:9413-9417`, `:9456-9460`)。

利用可能な同型実測は、D665 の cold CCBench build が単独 17.96〜18.16 秒、受入並列負荷下 42.90〜50.39 秒である (`docs/decisions.md:26329-26343`)。CCBench 側の記録も cold 30秒超、ccache warm 約3秒としている (`external/ccbench/docs/build_ja.md:39`)。

従って概算は次のとおりである。

- `stock_common` + `sort_best`: cold 下限約60秒、既存受入実測換算で約86〜101秒
- unique 6 configuration: 約180秒以上、受入実測換算約257〜302秒
- freeze の全12 cell: 約360秒以上、受入実測換算約515〜605秒

しかも `sort_best` は単純な parametrize では production 相当にならない。`prepare_cell` は外部 dependency rootを使って SWO oracle を通す (`orchestrator/campaign/s1_direct_comparison.py:870-908`)。現 canary の `_prepared_binding` だけでは production の共有 dependency prebuild、oracle receipt、source-dir transportを再現しない。

[severity: should-fix] 実 build なしで同じ継続保証を得られる。

- プランの別 Python process テストは `_build_v2_impl` を attacker subprocessで置換するため、実 CMake buildではない (`s2-plan.md:52-56`)。これは buildcache wrapper、実 context、実 owner write拒否、A→B→A 隔離を検査できるので、毎回の pytest にはこの形を残せる。
- CMake path 適合は、上記の静的 path 契約テストと、計算ノードで一度だけ行う descriptor-bound `stock_common` / `sort_best` qualification artifactに分離できる。
- 一度きりの artifact は CCBench pin、configuration、toolchain、source protection kind、実 build成功を固定する。受入のたびに cold buildを再実行しない。

正しさゲートは弱めず、繰返し費用だけを外せる。

## 3 受領証 v3

[severity: nit] v3 bump 自体の爆風は、現存成果物については小さい。

schema literal の実体は `RECEIPT_SCHEMA = "s8b-binary-admission/v2"` の1箇所だけである (`orchestrator/campaign/s8b_binary_admission.py:39`)。旧 v1 literal は拒否用テストだけにある (`orchestrator/tests/test_s8b_binary_admission.py:503-520`)。`source_protection_kind` は現 tree に0件だった。

receipt bytes を固定する面は次のとおりである。

- exact shape: `_RECEIPT_KEYS`、`_PROOF_KEYS`、`_SUBJECT_KEYS` (`orchestrator/campaign/s8b_binary_admission.py:48-69`)
- issuer bodyとouter SHA: `:258-287`
- schema、outer SHA、proof exact validator: `:317-389`
- test fixture生成面:  
  `orchestrator/tests/test_s8b_binary_admission.py:142`、  
  `orchestrator/tests/s8b_v2_freeze_fixture.py:297`、  
  `orchestrator/tests/test_s8b_floor_campaign.py:10934`、  
  `orchestrator/tests/test_s8b_floor_stats.py:206`、  
  `orchestrator/tests/test_s8b_ratified_verify.py:328`、  
  `orchestrator/tests/test_s8b_predicate_build_proof.py:203-210`、  
  `orchestrator/tests/test_s8b_dependency_prefix_bridge.py:86-137`
- receipt は `manifest.json` と `result.json` の `binaries` に埋め込まれ、manifest raw hashに束縛される (`orchestrator/campaign/s8b_floor_campaign.py:7442-7451`)。holdout freeze は sibling manifest hashと result の binaries完全一致を要求する (`orchestrator/campaign/s8b_holdout_freeze.py:1527-1565`)。

中央 validator の production consumer は全9箇所である。

- floor portable projection: `s8b_floor_campaign.py:4640`
- store preflight: `:5555`
- resume store: `:5649`
- pre-measurement live admission: `:6280`
- resume binary: `:7893`
- oracle preflight: `s8b_oracle_driver.py:1034`
- ratified freeze: `s8b_ratified_freeze.py:1808`
- holdout freeze: `s8b_holdout_freeze.py:1513`
- historical floor stats: `s8b_floor_stats.py:1141`

[severity: should-fix] 発行済み v2 の実測件数は 0 件である。

現在の worktree `output/`、main の `output/`、既知 mainprobe の `output/` に `s8b-binary-admission/v2` を含む永続 manifest/result はなかった。test が tmp_path 内で作る fixture receipt は永続発行物に数えていない。

従って現在失われる正式成果物はない。ただし v2 が存在した場合は、schema比較 (`s8b_binary_admission.py:318-319`) により以下がすべて止まる。

- floor resume
- binary store再検証
- 実測直前 admission
- oracle実走
- ratified freeze
- holdout freeze
- `expected_policy=None` の historical floor stats

現状は再発行対象が0なので、freeze、campaign lock、事前登録契約の再発行は不要である。

- `holdout_freeze.json` と `floor_protocol.json` は receiptを含まない。
- campaign lock の exact 24 closureに今回の3 moduleは含まれない (`orchestrator/campaign/campaign_lock.py:47-74`)。
- C10 の13 fieldは `campaign_wal.build_records` 等で、S8b binary receiptの内部 schema fieldを pinしていない (`orchestrator/campaign/s8c_preregistration_evidence.py:2223-2252`)。

[severity: nit] v3を使わない代案はあるが、より広い。

既存 v2 receiptを不変に保ち、v2の `receipt_sha256` を subjectにする別の `s8b-source-protection/v1` companion receiptを追加し、正式 consumerが二つの論理積を要求する形なら同じ保証を記録できる。ただし portable record、manifest、全9 consumerへ新しい sibling fieldを通す必要があり、v3 bumpより変更面が広い。

既存 `_PROOF_KEYS` は exactでouter SHAも全bodyを覆うため、schema名を v2 のまま fieldだけ追加する案は不可である。旧 v2 bytesを結局拒否しながら版名だけ偽ることになる。現存 v2 が0件である以上、v3 bumpのほうが妥当である。

## 4 既存の呼び手

[severity: nit] `admitted_build_snapshot` の production caller は `buildcache.py` の1箇所だけである (`orchestrator/campaign/buildcache.py:2977-3003`)。ほかは test direct callまたはmonkeypatchである (`orchestrator/tests/test_s8b_expected_materialization.py:466,505,551,593,624`; `test_buildcache_v2.py:2891,2965,3033,3510`)。

[severity: must-fix] namespace の爆風が build 区間で終わらない。

プラン自身が「元 user namespaceへ戻れず、processごとに一度だけ unshareする」としている (`s2-plan.md:11-12`)。従って context終了時に tmpfsを unmountしても、Python parentは新 user/mount namespace内に残る。

正式 floor は build後に同じ processで以下を続行する。

- store、manifest publish (`orchestrator/campaign/s8b_floor_campaign.py:7415-7451`)
- holdout reservation、live admission、process/host probe (`:7649-7688`)
- benchmark runner (`:7690-7710`)

つまり影響対象は compiler子孫だけでなく、binary store、perf、numactl、benchmark、journal、後続全 subprocessである。少なくとも計算ノード qualification は「実 build成功」で止めず、build後の store、one-rep benchmark、perf availability、journal publishまで同じ processで通す必要がある。ここが未証明のままでは、buildだけ成功して正式 campaign全体を壊す可能性が残る。

[severity: must-fix] no-op seam の形を固定する必要がある。

プランは既存 unit testで低レベル contextをno-op化するとしている (`s2-plan.md:58`)。許されるのは test側の `monkeypatch` で module symbolを差し替える形だけである。

以下は禁止すべきである。

- `admitted_build_snapshot(..., protection=False)`
- optional context factory引数
- 環境変数によるoff
- production module内のpytest検出

これらは正式経路から防護を外せる knobになる。別 process統合テスト以外の既存 direct-call 5件は test fixtureで明示 monkeypatchし、production signature不変を `inspect.signature` で固定すべきである。現在も「Callable注入なし」を検査している (`orchestrator/tests/test_s8b_expected_materialization.py:399-411`)。

[severity: should-fix] 先行 TypeError 型は回避可能だが、実装規則として明記が要る。

`build_v2`、`admitted_build_snapshot`、共有 `pipeline` の必須引数は増やす必要がない。D1134も「証拠を共有 build 器の必須引数にする」案を却下している (`docs/decisions.md:38133-38134`)。

`source_protection_kind` を issuer の新必須引数にすると、production 1箇所に加え、上記7 test/fixture面を壊す。固定 literalを issuer内部で生成するか、S8b専用の exact valueから導出し、共有 APIへ必須引数を広げないこと。これを守れば、`pipeline` 4箇所や `b10_backoff_shape_sweep` へ TypeErrorを波及させる同型事故はない。

## 5 判定

**要修正。**

core の private tmpfs案と v3 receiptは採用可能だが、次を修正条件とする。

1. process-wide user namespaceが build後の store・perf・benchmarkへ与える影響を、計算ノードの同一 process qualificationで閉じる。
2. tmpfs byte/inode上限を実測値とpage丸めから明示する。「約12 MB」は不可。
3. ccache実効設定がsnapshot外であることを計算ノードで確認する。
4. recurring pytestから実 CMakeの `stock_common` / `sort_best` / 全configuration parametrizeを外す。
5. pytestには別processの実防護・attacker subprocess正負例だけを残し、実 CMakeは一度きりのqualification artifactへ分離する。
6. no-op化はtest monkeypatchだけとし、production off knobと共有APIの新必須引数を作らない。

scopeを削るべき部分は、`s2-plan.md:64` の「最低でも stock_common と sort_best、可能なら全configurationをpytestで実build」である。これは今回やらない形へ切り分けるべきで、防護自体を弱める必要はない。

pytest、実 CMake build、計算ノードprobeは今回実行していない。緑とは判定していない。

## 総括

判定は **要修正**。最大の懸念は、不可逆な user namespace が build後の正式campaign全体へ残ることと、実 CMake canary増設が受入の直列所要を約1〜10分増やすことである。  
v3 receiptの既発行物は0件で、凍結成果物・campaign lock・C10の再発行は不要。