## 所見

### A1

**主張** `enforce_closure=False` では、index に存在しない ignored file を CCBench 内へ追加してもプランの三者照合を通過できる。  
**根拠** プランの helper は index entry だけを列挙する (`plan.md:20-27`) 一方、filesystem allowlist は closure 有効時にしか走らない (`tools/codex_reasoning_ab.py:1427-1434,1685-1691`)。再現は initialized child、closure 無効、`payload.txt` を追加し、`.git/info/exclude` または既存 `.gitignore` で隠し、index と HEAD と indexed files を不変にする。  
**深刻度** blocker  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** gitlink と `submodule_manifest_sha256` が正しいまま、試行が列挙して読む追加ファイルを含む snapshot が受理集合へ残る。

### A2

**主張** closure 無効時は replacement ref により、child `HEAD` の表示値を pin に保ったまま index と worktree を別 tree に差し替えて三者照合を通過できる。  
**根拠** `rev-parse HEAD` は元の ref OID を返すが、通常の `git diff-index --cached HEAD --` は replacement object を参照する。悪性 commit を作り、`refs/replace/<pinned-HEAD>` をその commit へ向け、index と worktree を悪性 tree に合わせれば、HEAD/gitlink、index/HEAD、worktree/index が全て一致する。closure 有効時は `refs/replace` 検査 (`tools/codex_reasoning_ab.py:1347-1361`) が落とすが、無効時は inventory しか走らない (`:1690-1691`)。  
**深刻度** blocker  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** oracle 上の gitlink は正規 pin のまま、実際に読まれる全 tracked bytes を別 commit 由来へ置換できる。

### A3

**主張** path-aware `hash-object` は exact-byte gate ではなく Git clean-equivalence gate なので、本 wave の正しさ境界を満たさない。  
**根拠** プラン自身が CRLF worktree の受理を明記している (`plan.md:72,88,150`)。LF blob を CRLF へ置換しても `text/eol` clean が LF に戻すため index blob id と一致し、同じ回避は `ident`、`working-tree-encoding`、smudge/clean filter でも構成できる。  
**深刻度** blocker  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** `submodule_manifest_sha256` と oracle bytes が同じまま、試行が pin blob と異なる bytes を読む snapshot が受理される。

### A4

**主張** raw helper を採用しても、現行の検査順では内容検査より前に repository または system config が指定した外部 program を起動できる。  
**根拠** `verify_snapshot` は新 helper の予定位置より先に `git diff`、status、numstat を実行する (`tools/codex_reasoning_ab.py:1623-1636`)。`_clean_environment` は `GIT_*` と user config を排除するが repository config と system config は残す (`:255-280,1892-1905`)。`core.fsmonitor` は command であり、worktree 比較は active clean filter を起動しうるため、後段の filter/config 拒否では副作用後になる。  
**深刻度** blocker  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** 外部 program が検査後に bytes を改変し試行後に戻すことで、pre/post oracle が一致した悪性試行を作れる。

### A5

**主張** プランの `_git_dir(candidate) == admin_dir` は両辺を `resolve()` するため、期待 admin path の symlink 化と外部 common-dir を束縛できない。  
**根拠** 期待値も `admin_dir = (... / name).resolve()` で計算される (`tools/codex_reasoning_ab.py:934-940`)。したがって `.git/modules/deps/child` 自体を同一 snapshot 内の rogue admin への symlink にすれば、marker が字句上正規でも両辺が rogue に収束する。また closure は `--absolute-git-dir` の containment だけを検査し (`:1342-1346`)、`--git-common-dir` を検査しない。  
**深刻度** blocker  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** 正規 path の manifest rowを保ったまま、refs、objects、config を別 admin または snapshot 外の common-dir から供給できる。

### A6

**主張** final component の `lstat` と一時点の hash だけでは、intermediate directory symlink と外部 hardlink alias による時間差改変を防げない。  
**根拠** プランは各 index path の final component だけを `lstat` する (`plan.md:23-26`)。`dir/file` の `dir` を外部 directory への symlink にすると final file は regular file に見え、closure 無効時は path-set walk もない。正しい bytes の tracked file を snapshot 外の writable alias と hardlink し、pre-verify 後に変更して post-verify 前に戻す方法は raw hash でも通る (`tools/codex_reasoning_ab.py:2372-2389`)。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** pre/post oracle は同一なのに、試行中だけ異なる CCBench bytes が観測される受理状態が残る。

### A7

**主張** 指定された攻撃面には実効回避、既存検査済み、単独では無効の三種があり、同列に扱うと必要な防壁を誤る。  
**根拠**

| 攻撃面 | 静的判定 |
|---|---|
| sparse-checkout | direct entry 検査では欠落 path が拒否されるため回避ではないが、正当な sparse checkout も拒否する。sparse-directory entry が露出すれば unsupported mode で拒否される (`tools/codex_reasoning_ab.py:1226-1235`)。 |
| skip-worktree / assume-unchanged | Git status を盲目化するが direct `lstat` と raw hash は静的改変を捕捉する。両 flag が copy 後も残ることは既存 test が固定している (`orchestrator/tests/test_codex_reasoning_ab.py:1650-1697`)。 |
| `.gitattributes` / `core.autocrlf` / filter | path-aware 案への実効回避であり、raw 比較なら拒否できる。 |
| `core.fsmonitor` | direct hash の静的回避ではないが、A4 の外部 program と時間差攻撃に使える。 |
| `index.skipHash` | 現行 Git 2.34.1 では利用面がなく、対応版でも index checksum の省略であり blob 同一性を変えない。 |
| submodule root symlink | 既存の `lstat` が拒否済み (`tools/codex_reasoning_ab.py:947-954`)。intermediate symlink は A6。 |
| hardlink | 静的に同一 bytes なら通り、外部 alias による A6 の時間差攻撃が残る。 |
| `core.worktree` | absolute 値は preflight (`:1098-1120`)、別 top-level は `--show-toplevel` (`:955-963`) で落ちる。 |
| `.gitignore` / `info/exclude` | closure 有効なら filesystem allowlist が ignored file も捕捉するが、closure 無効なら A1 が成立する。 |
| `extensions.worktreeConfig` | 単独では内容置換にならないが、`config.worktree` と common-dir という未検査 config 面を増やす。 |
| `objects/info/alternates` | closure 有効なら seal と verifier が除去・拒否する (`:831-836,1347-1361`) が、closure 無効なら replacement ref 等への object 供給に使える。 |
| `core.hooksPath` | 通常の verify 用 plumbing は hook を起動しないが、builder の checkout と submodule update (`:746-759,1480`) では別途考慮が必要である。 |
| `GIT_INDEX_FILE`、`GIT_WORK_TREE`、`GIT_CONFIG_*`、`GIT_ALTERNATE_OBJECT_DIRECTORIES` | `_clean_environment` が全 `GIT_*` を除くため無効 (`:1892-1905`) だが、repository/system config と `include.path` は残る。 |

**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** 無効な脅威へ不要な拒否を加える一方、closure 無効、config、alias の実効回避が受理集合へ残る。

### A8

**主張** 提案テストには、主要な新検査を外しても緑になりうる帰属穴が残っている。  
**根拠** named node 群 (`plan.md:141-157`) には、dirty initialized submodule と `enforce_closure=False` の組合せ、dirty な initialized grandchild、source marker/common-dir 改変がない。現行 closure 無効 test は uninitialized 判定だけで拒否される (`orchestrator/tests/test_codex_reasoning_ab.py:2139-2152`)。また CRLF 正例は path-aware の穴を仕様として固定し、P3 は clean-content の専用 node を実装しない限り A-C だけでは帰属しない。  
**深刻度** blocker  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** closure 無効呼出し、再帰適用、source 適用、P3 の各 mutation が生存し、「全 initialized depth へ適用」という成果物の主張が偽になる。

## プランへの反証

### A9

**主張** 生 bytes 比較を選ぶべきだが、「正当な Git checkout は必ず blob bytes と同一」という親の前提は成り立たない。  
**根拠** `git checkout` と `git submodule update` (`tools/codex_reasoning_ab.py:746-759,1480`) は `eol`、`ident`、`working-tree-encoding`、smudge filter により blob と異なる正当な worktree bytes を生成できる。`copytree(copy2)` はそれをそのまま複製し (`:1545-1550`)、seal は worktree を戻さず (`:1123-1141`)、`_finish_snapshot_case` は root の golden/artifact だけを書く (`:1497-1508`)。現在の `git apply` も root の限定 path だけで CCBench を書き換えない (`:1483-1484`)。  
**深刻度** blocker  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** raw gate は Git として有効な変換 checkout を新規拒否し、path-aware gate は逆に exact-byte 契約違反を受理するため、受理集合の定義自体が不定になる。

正しい裁定は次である。

- 契約が「試行が読む bytes は pin blob bytes と同一」なら、変換 checkout は正当 snapshot ではなく、早期に attributes/config を制限した上で raw 比較する。
- 契約が「clean 後に pin と同値」なら path-aware が正しいが、CRLF 等を実際に読んだ証拠を pin と同一とは呼べない。
- Python の `sha1(blob-header + bytes)` を使うなら SHA-1 object format を明示的に検査する。一般化するなら `git --no-replace-objects hash-object --no-filters` または同条件の batch `cat-file` が object format を追従し、clean driver も起動しない。

### A10

**主張** source live worktree の full bytes 拒否は clone 入力を検証しておらず、source 側で締めるべき境界を取り違えている。  
**根拠** `_init_submodules_from_local_source` は source index から topology と local repository path を得た後 (`tools/codex_reasoning_ab.py:717-744`)、destination 自身の gitlink commit を `submodule update` で object database から checkout する (`:746-760`)。したがって source worktree が dirty または空でも、必要な pinned objects があれば destination bytes は同じである。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** strict 案は開発中 source を無益に拒否し、非 strict 案は admin/common-dir、alternates、object hardlink、config side effect を未検査のままにする。

source では marker、admin、common-dir、object locality、実行されうる config を検査し、最終的な内容同一性は生成された destination で raw 比較すべきである。

### A11

**主張** P3 の `submodule.*` 全拒否は内容同一性には冗長で、Git 実行の安全性には不足している。  
**根拠** raw content と全 filesystem path を直接比較すれば `ignore=all` に依存せず A-C を拒否できる一方、P3 は `core.fsmonitor`、`filter.*`、`core.autocrlf`、`extensions.worktreeConfig`、`include.path` を検査しない (`plan.md:45-50,183-190`)。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** harmless な post-seal config まで受理集合から除外しながら、外部 program と config indirection を許したまま「二重防壁」と誤記することになる。

P3 を残すなら「seal 後に section がない」という独立 invariant sentinel と位置付け、clean-content 専用 mutation testを必須にすべきである。

### A12

**主張** P1 reject-only は互換性には適切だが、新 gate を通った事実を oracle 自身には記録せず、中間 consumer の再検証も増やさない。  
**根拠** final replay は fresh `verify_snapshot` と canonical bytes 比較を行う (`tools/codex_reasoning_ab.py:4887-4892`) が、`collect_run` (`:3032` 以降) と `make_packets` (`:5057` 以降) は snapshot を再検証せず、プランも T-1263 の残件と認める (`plan.md:128`)。  
**深刻度** nit  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** oracle bytes は保たれるが、final replay 前の packet や receipt は旧 gate で受理された参照を区別できないため、改善範囲を proof chain 全体と表現できない。

## 親 brief への反証

### A13

**主張** M2 は実際の historical snapshot が使う CCBench commit を測っておらず、「偽拒否 0 件」を一般化できない。  
**根拠** M2 は live `external/ccbench @ 511c9538` を測定している (`measurements.md:16-23`)。一方、保存済み実 oracle `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos/runs/attempts/run-a5d39938e37b4630a6e338c42ac9572c/snapshot-before.json` の `external/ccbench` は `d706650cdb31e442bef45b9b4216951d4fb40969` である。real fixture は実際に `_build_snapshot_base` と `_derive_snapshot_from_base` を通す (`orchestrator/tests/test_codex_reasoning_ab.py:350-399`)。  
**深刻度** blocker  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** raw gate が historical POS/NEG snapshot を拒否する可能性が未評価のまま、「正常 oracle bytes 不変」と報告される。

### A14

**主張** M1 の合成 snapshot は実 builder の object、config、attribute、relocation 条件を再現しておらず、F29 の模擬と実の差が残る。  
**根拠** synthetic fixture は単一 `child.txt` の fresh repo を init、update、seal するだけである (`orchestrator/tests/test_codex_reasoning_ab.py:2004-2101`)。実経路は pack transfer、古い BASE checkout、live source からの再帰 submodule 初期化、repack/seal、`copytree(copy2)` relocation を含む (`tools/codex_reasoning_ab.py:1462-1488,1511-1552`)。この差には実 CCBench の 404 files、mode、`.gitattributes`、未初期化 Shirakami、admin/object layout、保存された index flags が含まれる。  
**深刻度** blocker  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** synthetic では通る正例が実 POS/NEG で拒否される、または実 admin/config 経路だけの回避を見逃す。

### A15

**主張** M3 は path-aware 実装も反復 verifier 総費用も測っていないため、0.199 秒や 1 秒未満を比較値または上限として使えない。  
**根拠** measurements は Python raw hash を 0.199 秒と記録するが `hash-object` の全 file batch 値を持たない (`measurements.md:25-33`)。verify は snapshot finish、supervisor precheck、各試行の pre/post、final replay で反復され (`tools/codex_reasoning_ab.py:1508,2372-2389,2478-2486,4887-4892`)、custom filter の費用は無界である。プラン自身も P5 未確定としている (`plan.md:192-194`)。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** worklog の「1 秒未満」という性能値と timeout 余裕が根拠なしになり、実行可能な trial 集合を誤って見積もる。

### A16

**主張** M4 の「copy2 が index stat cache を必ず無効化する」は誤りである。  
**根拠** 同一 filesystem への copy では device は変わらず、`core.checkStat=minimal`、`core.trustctime=false`、`core.ignoreStat`、fsmonitor により inode/ctime が判定材料にならない構成がある。さらに既存 test は skip-worktree と assume-unchanged が copy 後も保存されることを明示している (`orchestrator/tests/test_codex_reasoning_ab.py:1650-1697`)。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** `diff-files` または status へ依存する実装では B の改変が受理されうるのに、stat cache 非依存と誤って記録される。

### A17

**主張** M5 の「pin 閉包 2 件」は repo 内 schedule だけを数えた値であり、保存済み実行証拠の閉包ではない。  
**根拠** `rg -l 'submodule_manifest_sha256' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-certified-rerun/bench/pos | wc -l` は 21 件で、schedule 1 件に加え 10 組の before/after oracle がある。oracle canonical hash は launch、schedule、attempt ledger、receipt、manifest からさらに参照され、replay は byte 完全一致を要求する (`tools/codex_reasoning_ab.py:4868-4892`)。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** schema 変更案の波及先を 2 件と過小評価し、実際には oracle 20 件とその間接参照全体を再発行または失効させる。

### A18

**主張** brief §3 の「純増検出力 = 4 vector」は四つの再現例を受理差集合の全体または独立機構数と誤認している。  
**根拠** A と C は同じ index/HEAD predicate、B は worktree/index、D は admin binding であり、独立機構は三系統である。逆に raw 採用時の CRLF、ignored extra、replacement ref、intermediate symlink、post-seal config など `A_old - A_new` は四要素を超える。A も `ignore=all` なしでは既存 gate が既に拒否する (`brief.md:20-27`)。評価順を固定しない純増主張の危険は `docs/failures.md:7464-7484` の F293 に該当する。  
**深刻度** must-fix  
**これを直さないと成果物のどの値・受理集合・参照がどう変わるか** worklog の検出 vector 数、mutation 帰属、`A_old - A_new` の説明が全て過少または二重計上になる。

## 総括

- 現プランには closure 無効時の ignored extra と replacement ref という独立 blocker がある。
- exact-byte 契約では path-aware CRLF 正例を削除し、attributes/config を先に制限して raw bytes を照合すべきである。
- admin/common-dir、intermediate symlink、hardlink、外部 program は内容 hash とは別の境界として塞ぐ必要がある。
- 実 CCBench `d706650...` を通る real builder path で互換性と費用を再測定するまで、M2、M3、F29 は根拠にならない。
- read-only 静的検査のみであり、pytest を実行した、または緑であるとは主張しない。