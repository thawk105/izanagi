pytest は実行していない。静的検査と read-only の Git config 解釈確認だけを用いた。

### 所見 1 — `commondir` / `config.worktree` が metadata 検査全体を迂回する

**深刻度**: blocker

**根拠**: [fetch_third_party.py:261-277](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:261) は常に `source/.git/config` と `source/.git/{shallow,objects/info/alternates,info/grafts,...}` を検査する。一方、直後の Git 呼出しは [fetch_third_party.py:278-287](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:278) の `git -C source` である。Git は `.git/commondir` があれば common dir 側の `config`、`shallow`、objects 等を使うが、`commondir` 自体を拒否していない。また `extensions.worktreeConfig=true` と `.git/config.worktree` も未検査である。metadata matrix [test_pegasus_thirdparty_fetch.py:481-525](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_thirdparty_fetch.py:481) に両者はない。

**壊れる具体例**: `source/.git` は実 directory、`source/.git/config` は安全な decoy とし、`.git/commondir` から外部 common dir を指す。common dir 側へ shallow/alternates/promisor config や `filter.x.clean` を置く。Python の生検査は decoy を通す一方、後続の Git は common dir を使用するため、拒否対象 metadata や外部 command が有効になる。

**最小の直し方**: 最初の Git 起動前に `.git/commondir`、`.git/config.worktree`、`extensions.worktreeConfig` を拒否する。通常 repository だけを受理する契約として回帰テストを追加する。

### 所見 2 — `.git/config` scanner は正当な Git 構文で回避できる

**深刻度**: blocker

**根拠**: section regex [fetch_third_party.py:29-32](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:29) は旧式 `[filter.x]` を section 名 `filter.x` として保持するが、拒否側 [fetch_third_party.py:201-220](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:201) は `section == "filter"` 等しか見ない。また [fetch_third_party.py:177-197](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:177) は行末が `\` なら個数を問わず次行を捨てる。Git では末尾 `\\` は literal backslash であり、次行は別の設定として解釈される。read-only probe でも `[filter.x]`、`[remote.origin]`、`[url.file]` がそれぞれ canonical な `filter.x.clean`、`remote.origin.promisor/uploadpack`、`url.file.insteadof` になった。テスト [test_pegasus_thirdparty_fetch.py:424-441](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_thirdparty_fetch.py:424) は引用 subsection の通常形だけである。

**壊れる具体例**:

```gitconfig
[core]
benign = value\\
[filter "x"]
clean = <副作用を起こして pinned bytes を返す command>
```

scanner は `[filter "x"]` を continuation として捨て、`clean` を `core.clean` と誤認する。Git は filter として実行する。filter が改変 worktree を pinned bytes に正規化すれば `git status` は空になり、build は改変 bytes を読む。

**最小の直し方**: continuation を自作解釈せず、少なくとも continuation・旧式 dot subsection を全面拒否する。旧式 section、偶数個の末尾 backslash、コメント末尾 backslash、大文字・空白変種を実 Git fixture で固定する。

### 所見 3 — 既存 hydrate 先の ignored build artifact が成功扱いになる

**深刻度**: blocker

**根拠**: 既存 destination は [fetch_third_party.py:490-506](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:490) で `_verify_source()` 後、そのまま clone を省略する。clean 判定は [fetch_third_party.py:325-331](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:325) の `git status --untracked-files=all` だけで、ignored file は列挙されない。裁定自身も [s4-ruling-planv2.md:25-28](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s4-ruling-planv2.md:25) でこの性質を認定している。CMake は [ThirdParty.cmake:57-78](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/external/ccbench/cmake/ThirdParty.cmake:57) の archive/config を OUTPUT として使う。M2 テスト [test_pegasus_thirdparty_fetch.py:210-223](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_thirdparty_fetch.py:210) は cache 汚染＋初回 hydrate しか扱わない。

**壊れる具体例**: 初回 hydrate 後に build が `config.h` と `libkohler_masstree_json.a` を生成する、または同名の改竄 artifact を置く。二回目の hydrate は ignored artifact を見ず、fresh clone を作らず、成功 JSON を返す。凍結 submitter の検査 [submit_silo_ladder_rung1.sh:6-20](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/submit_silo_ladder_rung1.sh:6) も同じ `status` 判定なので、その artifact が build 入力になる。

**最小の直し方**: hydrated destination では `git ls-files --others --ignored --exclude-standard -z` も空であることを要求するか、既存 destination を再利用せず拒否する。cache 側は fresh clone で除外できるため、同じ禁止を一律適用する必要はない。

### 所見 4 — `verify-deps` は shallow だけでなく全 metadata 防壁を無効化する

**深刻度**: must-fix

**根拠**: [fetch_third_party.py:552-563](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:552) は gflags/glog を `hardened_metadata=False` で検査する。この値では config、sparse、index bit、promisor 等の検査が [fetch_third_party.py:299-340](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:299) ですべて飛ぶ。テスト [test_pegasus_thirdparty_fetch.py:551-563](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_thirdparty_fetch.py:551) が必要としている例外は shallow の受理だけである。

**壊れる具体例**: gflags を正しい HEAD の sparse checkout にし、必要な source を skip-worktree で欠落させる。HEAD と `git status` は正常なので `verify-deps` は readiness 成功を返す。また canonical な filter config も Git 起動前に検査されず、command 実行経路が残る。

**最小の直し方**: boolean を廃止し、`allow_shallow=True` のように拒否項目を個別化する。deps でも config、commondir、sparse、index bit は拒否する。

### 所見 5 — publish 失敗後に正式 destination が残る

**深刻度**: must-fix

**根拠**: [fetch_third_party.py:357-367](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:357) は `mkdir(destination)` 後に rename が失敗しても destination を片付けない。caller の cleanup [fetch_third_party.py:477-478](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/tools/pegasus/fetch_third_party.py:477) は stage parent だけである。さらに M15 [test_pegasus_thirdparty_fetch.py:444-479](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_thirdparty_fetch.py:444) は publish 後検証が例外になっても正式 destination が残ることを明示的に assert している。裁定 [s4-ruling-planv2.md:80-82](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s4-ruling-planv2.md:80) 自体が空 directory の残留を許しており、「partial tree を残さない」と両立しない。

**壊れる具体例**: `mkdir` 成功後に rename が EIO/ENOENT となると、CLI は rc=2 だが空の正式 destination が残る。次回はそれを source として検査し、`.git` 欠落の rc=1 で停止する。post-publish 検証例外では未承認 tree が正式名のまま残る。

**最小の直し方**: 正式 destination ではなく sibling の排他 lock を予約し、lock 保持中に destination 不在を再確認して rename する。現方式を残すなら、予約 inode が自分のものと一致し空である場合だけ rename 失敗時に `rmdir` する。別 inode の path は削除しない。

### 所見 6 — M6 テストは untracked file を作っていない

**深刻度**: must-fix

**根拠**: [test_pegasus_thirdparty_fetch.py:276-288](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_thirdparty_fetch.py:276) の line 285 は `(source / "untracked" / "payload").mkdir(parents=True)` で空 directory しか作らない。Git は空 directory を追跡・列挙しないため、`--untracked-files=all` の有無にかかわらずこの fixture は dirty 入力にならない。

**壊れる具体例**: 現行実装でも M6 変異後でも `git status` の stdout は空のままになる。したがって、この入力から line 287 の rc=1 と `"not clean"` は発火せず、事前登録した M6 の検出力を証明できない。

**最小の直し方**: directory ではなく `payload.write_text(...)` で実ファイルを作る。

### 所見 7 — 報告された `git diff --check` は新規 2 ファイルを検査していない

**深刻度**: nit

**根拠**: [s5-impl.md:39-47](/work/1/SFC/tanab/dev-wave-jobs/t340-thirdparty-fetch/s5-impl.md:39) は `git diff --check` を検査結果に数えるが、`git status` 上の変更は `??` の新規 2 ファイルだけである。read-only で同じ `git diff --check` を再実行すると rc=0・出力ゼロで、新規ファイルの bytes は diff に入らなかった。

**壊れる具体例**: 両新規ファイルへ trailing whitespace を入れても、未追跡のままなら同じ command は rc=0となり、報告だけが維持される。

**最小の直し方**: 各新規ファイルを `git diff --no-index --check /dev/null <file>` 相当で検査し、通常差分による rc=1と whitespace 診断を区別して記録する。

### 所見 8 — `sys.path` テスト末尾の assert は恒真

**深刻度**: nit

**根拠**: [test_pegasus_thirdparty_fetch.py:597-610](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t340-thirdparty-fetch/orchestrator/tests/test_pegasus_thirdparty_fetch.py:597) は `finally` の line 609 で `sys.path[:] = original` を必ず実行した直後、line 610 で `removed or sys.path == original` を assert する。右辺は代入によって常に真である。

**壊れる具体例**: `_driver_module()` が code root と一緒に別の sentinel entry を消しても、line 607 は code root 不在だけを確認し、finally が差を消した後の line 610 は通る。「自分の temporary entry だけを除去」は検査されない。

**最小の直し方**: sentinel を含む期待 `sys.path` を用意し、`finally` で復元する前に list 全体が期待値と一致することを assert する。恒真な末尾 assert は削除する。

## 総括

- 最重は所見 1（common-dir 迂回）、所見 2（config parser 回避）、所見 3（ignored artifact 再受理）。
- blocker は 3 件ある。
- 凍結 4 本は staged/unstaged diff なし、全 `hash-object == HEAD`。凍結境界違反はない。
- pytest は未実行。