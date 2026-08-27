## 総括

最重所見は、実 suite 全体を subprocess collection する 2 node が `REAL_REPO_ACCESS_BY_NODE` 外にあり、inner `--collect-only` でも node lock が発火しない閉包漏れである。  
提案された shard conflict gate は、全対象へ同じ `real-repo` marker を付ける設計上ほぼ恒真で、edge 削除変異を単独では殺せない。  
controller prewarm も node protocol より前に実 repo resolver を実行するが、plan の閉包対象にない。  
以下は指定 7 ファイルの静的全件検査であり、pytest・実測・書込みは行っていない。

## 所見

### 1. BLOCKER: whole-suite nested collection が分類外

- **所見:** `test_real_repo_group_collection_exactly_matches_canonical_nodes` と `test_shard_assignment_preserves_live_xdist_group_components_and_split_control` は実 `orchestrator/tests` 全体を subprocess で collect/import するが、inventory にない。plan の「live collection」検査も同じ穴を再生産しうる。

- **根拠 file:line:** `orchestrator/tests/test_real_repo_serialization.py:687-825,1252-1256,1416-1422`。一方、同ファイルから inventory に入る node は `orchestrator/tests/conftest.py:341-460` 中の `:346-350` の 3 本だけ。lock は `pytest_runtest_protocol` の `conftest.py:1826-1843` で初めて取られ、inner `--collect-only` では実行されない。

- **成果物影響:** import/collection 中の実 repo 観測が競合すると、certified 選択結果の pass/fail、shard report の `observed_universe`・group 集合、台帳の失敗・所要値が実装内容以外で変わる。

- **提案:** 既存 2 node と新設 live-collection node を少なくとも parent SH reader として登録する。同時に、下位 `conftest`・plugin・module import は node lock では覆えないため、pre-collection lock を置くか、全 import 面が実 repo 非接触である独立監査を追加する。

### 2. HIGH: `repository_scan` と CCBench writer の排他が未証明

- **所見:** plan 上、`repository_scan` consumer は retained `@real-repo`、既存 CCBench writer は suffix 除去された singleton となるため別 runtime scope で並走できる。前者は parent SH だけ、後者の 3 本も parent SH + ccbench EX なので、scan が `external/ccbench` を辿るなら排他されない。

- **根拠 file:line:** scan は実 working tree の tracked/untracked と source bytes を読むとされる `s2-plan.md:97-108`。writer は共有 submodule 管理領域を更新する `conftest.py:417-421`、access は `conftest.py:581-595`。runtime 分離は `s2-plan.md:153-157`。

- **成果物影響:** scan の hit 集合や source bytes が writer 窓を観測し、certified 結果とレポートの failure node、台帳の赤緑が走行順で変わりうる。

- **提案:** scanner が `external/ccbench` の内容・directory metadataを一切読まないことを実在 path の正負対照で証明する。証明できない場合は fixture access を `RealRepoAccess("read", "read")` とする。射影外の scanner 本体を読めないため、この対は「衝突確定」ではなく未解消の blocker である。

### 3. BLOCKER: shard conflict gate と edge 削除変異が恒真化する

- **所見:** 全 `REAL_REPO_SHARD_NODES` に同じ `real-repo` marker を付けるため、任意の conflict pair は marker だけで同一 union-find component になる。さらに conflict matrix から edge を削除すると、検査対象自体が減るので、独立 edge golden がなければ変異は赤にならない。

- **根拠 file:line:** 同一 marker 設計は `s2-plan.md:143-172,189-194`。提案検査と edge 削除変異は `s2-plan.md:270-277,297-298`。allocator は file と group を無条件に union する `tools/acceptance_shards.py:288-305`、既存 gate は file/group の一 shard 性だけを見る `:388-411`。

- **成果物影響:** access vector や fixture lock edge が欠けても検査が緑となり、別 worker で競合した結果を certified として受理し、report・台帳へ偽緑を記録できる。

- **提案:** conflict edge の独立 exact golden を、実在する fixture名・consumer node・resource/mode の literal から作る。`matrix edge集合 == independent golden` を先に検査し、その後 component と実 flock contention を検査する。

### 4. HIGH: controller prewarm が node lock の外で実 repo resolver を実行する

- **所見:** receipt/oracle prewarm は collection hook で発火し、`pytest_runtest_protocol` より前なので `REAL_REPO_ACCESS_BY_NODE` の lock を受けない。plan は worker 重複費としてしか扱っていない。

- **根拠 file:line:** 実発火は `conftest.py:834-943,1846-1862,1932-1965`。node lock は `:1826-1843`。テスト自身も controller prewarm 発火を固定している `test_real_repo_serialization.py:3601-3642`。receipt resolver の実呼出し owner は `:4201-4225`。plan の扱いは `s2-plan.md:251-268`。

- **成果物影響:** 無 lock で作った memo snapshot が全 consumer に再利用され、certified 判定、failure report、台帳値が prewarm 時点の競合状態へ固定される。

- **提案:** 各 prewarm の実 access vector を独立分類し、実 `prewarm_*` 呼出し自体を SH lock 内へ置く。正例は fake helper ではなく controller hookから実 prewarm endpointへ到達したことまで記録する。

### 5. HIGH: fixture lock の正例が実 fixture 結線を要求していない

- **所見:** plan の behavioral test は lock の競合動作を述べるが、`repository_candidate_commit`、`repository_scan`、`current_commit_snapshot` という実呼び先を正例で名指ししていない。helper とテストの両方を正しく作り、fixture を未配線のままにする偽緑が可能である。

- **根拠 file:line:** factory と予定配線は `s2-plan.md:85-93,101-108,116-120`、負例の記述は `:270-275`。実 SUT の呼出しを記録する既存の強い型は `test_real_repo_serialization.py:1921-1995`。

- **成果物影響:** fixture consumer が無 lock で動いても新設検査が緑となり、candidate OID・repository snapshot・certified 判定値が並走順で変わる。

- **提案:** 各 fixture 名を独立 literal に固定し、実 fixture functionを実行して、builder/read/yield/teardown が期待 lock context 内にあることを記録する。fixture集合と resource node集合の disjoint 検査も加える。

### 6. HIGH: common-dir 移行は旧 lock namespace と共存できない

- **所見:** worktree-root hash から common-dir hash へ直接切り替えると、旧コードと新コードが異なる `/tmp` lock file を取る。rolling 中の同時 session は互いを排他しない。

- **根拠 file:line:** 現行 key は `conftest.py:989-1007`、変更案は `s2-plan.md:122-139`。既存テストは symlink と cwd 間の同値だけで、旧新 namespace の相互排他を検査しない `test_real_repo_serialization.py:1646-1686`。

- **成果物影響:** 旧 session の writer と新 session の readerが重なり、certified 結果と台帳が commit 世代の組合せで変わる。

- **提案:** 移行期間は legacy key と common-dir key の両方を、正規化した path 順で同じ mode により取得する。あるいは全旧 session 停止を明示的 cutover 条件にする。旧 holder が新 acquisition を阻止する回帰テストを追加する。

### 7. HIGH: shard 側の common-dir subprocess は Git authority env を継承する

- **所見:** plan の新 lock helperは `GIT_*` 除去を要求する一方、変更不要とした `acceptance_shards._git_common_dir()` は `env` を渡さない。`GIT_DIR` 等で shard artifact root と lock key が別 repo を指しうる。

- **根拠 file:line:** 無 sanitization の subprocess は `tools/acceptance_shards.py:149-174`、使用箇所は `:194-199,970-989`。plan の sanitization 要求は `s2-plan.md:131-137`、同 tool を変更不要とする判断は `:174-183,311`。

- **成果物影響:** shard report・JUnit・dispatch intent の保存 rootが変わり、merge が infra redになるか、誤った運用領域の reportを台帳根拠にする。

- **提案:** shard側も同じ閉じた Git env builderを使い、`GIT_DIR`・`GIT_WORK_TREE`・`GIT_COMMON_DIR` 汚染の負例を追加する。

### 8. MEDIUM: semantic exact pin が更新対象から漏れている

- **所見:** direct `xdist_group` provenance 検査は `REAL_REPO_RESOURCE_NODES` だけを対象にする。新しい shard-only fixture node 15 本を `REAL_REPO_SHARD_NODES` に分離すると、手書き decorator で marker を補って hook 配線を欠く変異がこの検査を通る。

- **根拠 file:line:** helper は `test_real_repo_serialization.py:1141-1194`、呼出しは `:1613-1621`。plan の exact pin 更新一覧 `s2-plan.md:185-218` にこの面がない。

- **成果物影響:** collection report 上の group 値だけは正しく見える一方、canonical hook 正本が不完全なまま certified 選択と台帳が通る。

- **提案:** provenance 検査へ `REAL_REPO_SHARD_NODES` と独立 shard golden を渡し、resource/fixture双方で marker が hook 由来であることを固定する。

### 9. MEDIUM: brief の 258.92 秒を runtime 排他鎖へ一般化できない

- **所見:** erratum は合計を 258.92 秒へ直したが、これは marker付き node の ledger 合計であり、runtime 直列長ではない。plan の構造的反証は正しいが、plan 冒頭の数値は旧 258.73 秒のままである。

- **根拠 file:line:** 元の一般化は `brief.md:24-41`、訂正値は `brief-erratum.md:3-13`。suffix strip は `conftest.py:1702-1718` で、hook後に実行される `:1811-1814`。plan の反証は `s2-plan.md:3-18`。

- **成果物影響:** レポートへ「排他鎖 258.92 秒」または旧 258.73 秒を記録すると、A/B baseline、床の帰属、台帳の説明値が誤る。

- **提案:** marker合計、runtime loadgroup scope別合計、実 worker spanを別欄にする。wall 効果は plan どおり同一 commit A/B だけで主張する。

## fixture 生存期間の判定

列挙済み 15 consumerについては、fixture自身が `yield` 全体を lock 内に置き、全 consumerが同じ retained `@real-repo` に入るなら、session/module寿命と node protocol の非対称は扱える。`acceptance_shards.py:288-385` も同一 group と file を別 shardへ分割しないため、指定範囲からはこの15本に対する collection順反例は構成できなかった。

ただし、この評価は所見 5 の「実 fixture へ本当に結線されること」と、consumer golden の完全性が成立する場合に限る。controller prewarm と import/collection 面はこの結論の外であり、現状未閉包である。

## 裁定パッケージ候補

- **所見:** `/tmp` flock の保証は同一 host/filesystemに限定され、別 acceptance invocation・別 host は排他しない。

- **根拠 file:line:** `conftest.py:989-994`、単一 runner invocation限定の既決定は `decisions-verbatim.md:20-21`。

- **成果物影響:** 並行 acceptanceを別 hostで許す運用では、同じ実 repoに対する certified 結果が相互実行順で変わりうる。

- **提案:** 「保証は単一 invocation 内だけ」を維持するか、並行 acceptanceも保証対象として共有 filesystem lockまたは worktree隔離へ進むかを別裁定にする。

## 検査範囲

指定された 7 ファイル、合計 9,639 行を全文読んだ。さらに同じ 7 ファイルだけを対象に、`real-repo`／`@real-repo`、lock helper、session/module fixture、全 pytest hook、subprocess、`ROOT`／`HERE` と実 file read を行番号付きで全件検索した。射影外の下位 `conftest.py`、plugin、実 scanner/helper本体は指示に従い読んでいないため、それらに追加経路が「無い」とは認定していない。