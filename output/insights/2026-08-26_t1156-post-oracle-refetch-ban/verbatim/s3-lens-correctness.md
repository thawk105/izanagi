**所見 1**: argv に ON が 1 本あっても、CMake 内部の実効値は OFF に上書きできる

**具体的失敗**: [`buildcache.py:2101`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:2101) と [`buildcache.py:2613`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:2613) は、floor configure に `CMAKE_TOOLCHAIN_FILE` を含む環境を継承する。例えば環境で指定された toolchain file が `set(FETCHCONTENT_FULLY_DISCONNECTED OFF CACHE BOOL "" FORCE)` を実行すれば、提案された argv 本数検査は通る一方、実効値は OFF になる。事前検査直後に `masstree-src` を消せば configure は再 populate できる。floor postflight も新 flag の実効値を検査しない。

**成果物影響**: 再取得禁止を実行していない build が、flag 付き `configure_argv` としてレポート、台帳、completion manifest に残る。再取得後の tree を build が使い、その後に元 tree を戻せば既存事後照合も通り、汚染 binary の TPS が床値と certified 選択へ入る。

**区分**: must-fix。CMake 注入面を明示的に空へ固定し、configure 後かつ build 前に `CMakeCache.txt` の実効値も独立照合する必要がある。

---

**所見 2**: 提案された事前検査は oracle が判定した内容権威の一部しか比較しない

**具体的失敗**: oracle は `SHA256SUMS` の固定 hash、全 regular file 集合、各 file hash を検証するが、`_FloorOracleDependencyBinding.cache_receipt()` は HEAD と `config.h` hash しか渡さない。oracle PASS 後に `compiler.hh` など ycsb が include する tracked header を変更しても、HEAD、`config.h`、archive が同じなら提案 helper は通る。`FULLY_DISCONNECTED` はこの変更済み tree をそのまま使わせる。build 後に header を戻せば tracked-clean postflight も通る。

**成果物影響**: oracle private copyと異なる header で binary が生成されるのに、completion manifest の receipt、archive hash、floor の oracle receipt はすべて元の値を保持する。binary hashと TPS だけが変更され、certified 下限の根拠が分裂する。

**区分**: must-fix。oracle の manifest authorityまたは検証済み snapshotを build 境界まで持ち回る必要がある。HEADを worktree bytes と同値に扱ってはならない。

---

**所見 3**: 別 process の late prebuild と検査直後の差し替えを止める排他境界がない

**具体的失敗**: 2 job が同じ明示 base `B` を使う場合、J1 の oracle PASS 後に J2 が [`prepare_masstree_fetchcontent()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:1601) を呼べる。この prebuild configure には新 flagを付けない計画なので、J2 は J1 の baseを再 populateまたは再生成できる。J1 の helper returnから `_run(configure)` までにも path-based windowがある。phase markerは記録であり、baseを共有する別 processが検査する不可逆 gateや lockではない。

**成果物影響**: J1 が oracle で判定した inodeと build が開く inodeが異なり得る。J2 が J1 の build終了後、postflight前に元 directoryを戻せば、source inode、HEAD、config、archiveの事後値は元へ戻る一方、binaryと床値は中間 tree由来になる。

**区分**: must-fix。P3を現行 callsiteの順序テストだけで閉じてはならない。共有 baseを許すなら process間の不可逆 phase gateが必要で、完全に閉じるには private snapshotを build入力にする必要がある。

---

**所見 4**: mimallocとgoogletestはflagで切断されるのに、内容を一度もbuild境界へ束縛していない

**具体的失敗**: staged modeはoracle前に3依存をclean検査するが、提案 helperと [`_verify_floor_build_dependency()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:3379) が再観測するのはmasstreeだけである。oracle PASS後に `mimalloc-src` のtracked sourceを変更すると、masstree事前検査は通り、flagによりCMakeは変更済みmimallocを取得し直さず使用する。ycsb targetは [`ProtocolHelpers.cmake:36`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/external/ccbench/cmake/ProtocolHelpers.cmake:36) でmimallocへ直接linkする。googletestの `CMakeLists.txt` もconfigure時に実行されるが再検査されない。

**成果物影響**: 変更済みmimalloc由来のbinaryが、masstree receipt、archive hash、transport modeだけのcache identityでpublishされる。そのcache entryは後のclean runでもhitし、汚染binaryのTPSが継続して床値へ入る。captured pinは期待値の記録であって、build後のlive tree観測ではない。

**区分**: must-fix。少なくともmimallocのlive HEAD、clean状態、source identityを事前、事後、cache identityへ束縛する必要がある。googletestもconfigure入力として同様に扱う必要がある。

---

**所見 5**: policy IDを追加してもcache hitのconfigure provenanceは引き続き虚偽になる

**具体的失敗**: 新policy下でbase Aからfresh buildした後、同じreceipt、archive、transport modeを持つbase Bで呼ぶと、base pathはidentityに入らないためhitする。その後 [`_v2_result()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/buildcache.py:1680) が現在のBを使ってargvを再生成する。返される `configure_argv` はBを指すが、binaryを実際に作ったconfigureはAを指していた。既存テスト [`test_buildcache_v2.py:752`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_buildcache_v2.py:752) がこのcross-base hitを明示的に許している。

**成果物影響**: runtime manifest、portable report、台帳のconfigure参照がhistorical executionではなく現在の再構成recipeになる。mimallocなど未束縛材料がAとBで違う場合、記録されたBの材料とbinaryが実際に使ったAの材料も食い違う。

**区分**: must-fix。実行時argvをcompletion manifestへ保存してhit時に返すか、fieldをhistorical commandではなくrecipeと明示して別の実行証跡を保持する必要がある。

---

**所見 6**: `cmake --build` のmasstree再生成は同じ受理破りを残す

**具体的失敗**: helper通過後、configureとbuildの間にarchiveを削除すると、[`ThirdParty.cmake:66`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/external/ccbench/cmake/ThirdParty.cmake:66) のcustom commandが`bootstrap.sh`、`configure`、`make`、`ar`を共有source tree内で再実行する。変更したsourceからarchiveを生成してbinaryへlinkし、build終了後に元source、config、archiveを戻せば、既存postflightは元の値を観測する。

**成果物影響**: certified binaryはoracleが判定したarchiveと異なる一時archiveを含むが、台帳のarchive sha256とdependency receiptは元の値になる。TPSとcertified下限だけが変更される。

**区分**: 裁定行き。題名をfetchだけへ狭めても、この残存経路がある状態で「oracle判定後の材料変更を禁止した」とは主張できない。今回閉じないならcertificationを止める依存waveが必要である。

---

**所見 7**: `base束縛ならpost-oracle` という同値化が既存の正常入力を拒否する

**具体的失敗**: canonical baseに正しい`masstree-src`、receipt、config、archiveがあるが、`mimalloc-src`と`googletest-src`はまだないbase-only `build_v2` 呼出しは、現APIの検査を満たす。現在は`FetchContent_MakeAvailable`が不足依存をpopulateしてbuildできる。提案後はmasstree helperが通った後、baseがあるという理由だけでglobal disconnected flagが付き、mimallocのpopulateが禁止され、`mimalloc-static` target不在によりconfigureが失敗する。

**成果物影響**: oracleと無関係な既存base-bound APIの受理集合が縮み、従来生成できたbinaryとcache entryが作れなくなる。これは「baseとreceiptの同時指定」という構文条件を「oracle PASS後」という意味条件と同値にしたF325型の誤りである。

**区分**: must-fix。post-oracle専用のcapabilityまたはpolicy引数をfloor bindingから渡し、その値でflagを有効化すべきで、baseの有無を代理条件にしてはならない。

---

**所見 8**: 提案positive controlは実際の再取得禁止も実際のfloor CMake版も検査しない

**具体的失敗**: 追加予定テストはproduction helperと`_v2_commands()`を直接呼び、既存fixtureは [`test_buildcache_v2.py:236`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/tests/test_buildcache_v2.py:236) で`_run`をfake化している。したがって、定数とテストが同じ綴り間違いを共有しても、本数検査とA/B同一生成器テストは通る。さらに実floorは [`_bind_current_toolchain()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1156-post-oracle-refetch-ban/orchestrator/campaign/s8b_floor_campaign.py:3712) により登録済みCMake 3.25.0へ束縛されるが、親probeはlogin nodeの3.22.1である。

**成果物影響**: テストは緑でもactual compute configureがflagを無視、上書き、または別の欠落挙動を示し得る。レポートにはflagが記録されるため、禁止が発火したように見える恒真証拠になる。

**区分**: must-fix。production定数を使わないliteral oracle、実CMakeによるsentinel非変更試験、実効cache値の照合、登録版3.25.0でのpositive controlが必要である。A/B同一生成器テストは配線確認にしかならない。

## 総括

段2プランはflag単独の穴をmasstree事前検査で補うが、禁止の実効値、oracleの全内容権威、他のFetchContent依存、process間排他、configure後の再生成、cache hitのhistorical provenanceを閉じていない。特に、変更済みmimallocの永続cache化と、masstree treeを一時差し替えてpostflight前に戻す経路は、最終的なcertified binaryと台帳の材料参照を直接分裂させる。

また、base束縛をpost-oracleと同値化する条件は正常なgeneric `build_v2` 入力を拒否する。専用capabilityと検証済みprivate snapshotをbuild側へ渡す設計を優先すべきである。

read-onlyの静的検査のみを行った。pytest、CMake configure、buildは実走していない。