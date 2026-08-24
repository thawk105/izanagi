---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1431-floor-pilot-submit
seq: 1
---

## 新規

### {{F:heavy-work-guard-bypassed-by-shell-variable}}. ログインノードの重い処理防壁が shell 変数の間接で発火しない [権限逸脱]

- 事象: 床値 pilot の停止点を局所再現するため、ログインノードで gflags と glog を
  `CM=/system/.../cmake` に入れてから `"$CM" --build ...` と書いて実際にビルドした。
  直後に同じ処理を `cmake --build ...` と直書きしたところ初めて拒否され、
  先の 2 本が防壁を通り抜けていたことに気づいた。意図的な迂回ではなく、
  長い絶対 path を短く書くために変数へ入れた結果である。
- 根本原因: `hooks/guard_bash.py` の `_heavy_segment_violation` は
  `_heavy_head_and_args` が返す head を `os.path.basename(token)` の文字列一致で判定する。
  token が `$CM` のままなので `cmake` と一致せず、`cmake --build` の分岐に到達しない。
  guard 自身の `decide()` で実測した: `cmake --build /tmp/b -j 16` は拒否、
  `CM=/usr/bin/cmake; "$CM" --build /tmp/b -j 16` と
  `CM=/usr/bin/cmake; $CM --build /tmp/b -j 16` はどちらも通過する。
  なお `re.match(r"^\w+=", token)` による代入 token の読み飛ばしはあるので、
  代入自体は解析されているが、その値は head 解決に使われない。
- 恒久対応: 未実施。防壁本体の変更は正しさ防壁の改訂であり、
  `docs/skill-self-improvement.md` の段 8 契約に従って裁定パッケージへ送った
  ({{T:heavy-guard-variable-indirection}})。本エントリは事象と機序の記録である。
- 再発検知: `hooks/` のテストに、同じ command を直書き形と変数間接形の両方で
  `decide()` へ通し、判定が一致することを要求する positive control を足すこと
  (裁定後の実装対象)。

### {{F:unreachable-cmakecache-predicate-blocked-floor}}. floor sort_best の build 後検査が、現行 pin では出現しえない CMakeCache key を要求していた [恒真ゲート] [テスト代表性]

- 事象: 床値 pilot を 2 回投入し (request `940170.nqsv` / `944884.nqsv`)、
  どちらも 12 セル中 3 セル build 完了・計測到達セル 0 で停止した。
  2 回目に T-1578 の耐久診断が本文を残し、停止の実体が
  `BuildCacheError: CMakeCache.txt の masstree_SOURCE_DIR が一意な絶対 path でない`
  であることが確定した。コンパイル自体は通っていた。
- 根本原因: `orchestrator/campaign/buildcache.py` の
  `_masstree_source_root_from_cmake_cache` が、cell の build directory の
  `CMakeCache.txt` に `masstree_SOURCE_DIR` がちょうど 1 行あることを要求していた。
  CCBench (pin `511c9538e4e8efa54b45cda62e72389ed3b706ec`) の `cmake/ThirdParty.cmake` は
  1 引数形式の `FetchContent_Populate(masstree)` を使い、この形式は
  `<name>_SOURCE_DIR` を呼び出し scope の通常変数にしか設定せず CMakeCache へ書かない。
  したがって出現数は常に 0 で、述語は構造的に到達不能だった。
  この検査は floor の staged transport 経路 (`dependency_receipt` が非 None、
  すなわち sort_best cell) でしか呼ばれず、その経路は実 run で一度も通っていなかった。
  **到達不能性が露出しなかったのはテストが自己充足だったためである。**
  `orchestrator/tests/test_buildcache_v2.py` の `fake_run` は、実 CMake が書かない
  `masstree_SOURCE_DIR:STATIC=<...>` という行を合成 `CMakeCache.txt` へ自分で書き込んで
  いた (同 file の 2 箇所)。検査が要求する形を fixture 側が作っていたので、
  実環境の CMakeCache に同じ key が無いことをテストは検出しえなかった。
- 恒久対応: 述語を、CMakeCache に実在する key (`FETCHCONTENT_SOURCE_DIR_<UPPER>` と
  `FETCHCONTENT_BASE_DIR`) から CMake と同じ規則で実効 source root を導出する形へ
  張り替えた。束縛は弱めず、key が 0 件・複数件・非絶対のときは従来どおり fail-closed
  である。positive control は実環境と同じ形の CMakeCache を使う。
- 再発検知: `DW-O13` が既に「field の実在では足りない。その field が実環境で取りうる値を
  実測し、要求する値が到達可能か確かめてから述語を採用する」を課している。
  本件はその未適用例である。加えて実環境形の CMakeCache を使う positive control を
  テストへ常設した。

### {{F:git-status-is-not-a-tracked-absence-proof}}. untracked 一括除去の確認に `git status` を使い、別 wave の tracked file を消した [手順漏れ]

- 事象: 床値 pilot が `output/` 配下へ残した untracked 成果物を repo 外へ退避してから
  `rm -rf` する前に、`DW-O11` の求めるとおり
  `git status --porcelain -- <path>` を走らせた。返ったのは `??` 行だけで、
  `grep -cv '^??'` は 0 だった。これを「対象は全て untracked」と読んで除去したところ、
  同じ directory にあった**別 wave の tracked かつ無変更**な submission receipt 3 件
  (`5f1d4eccaafd8c5bcce86d042eafb521` / `e587c22d7588e5aea760754e88092142` /
  `f29f559a81afd2d3ba5dde05000a3471`、計 51 file) まで消えた。
  除去直後の `git status --porcelain` に ` D` が 51 行現れて発覚し、
  `git checkout -- <path>` で全件復元した (`git diff HEAD` が空であることを確認済み。実害なし)。
- 根本原因: **`git status` は tracked かつ無変更の file を 1 行も出さない。**
  したがって「`git status` の出力が `??` だけ」は「tracked file が無い」ことの証明にならない。
  `DW-O11` は「対象が untracked だけと個別確認してから行う」と定めるが、
  その確認手段として `git status` を使うと、不在の実測にならない検査を実測と誤認する。
- 恒久対応: 不在は tracked 集合そのものを数えて確かめる。
  `git ls-files -z -- <path> | wc -c` が 0 であることを確認してから除去する。
  `git status` は差分の列挙であって在籍の列挙ではない。
- 再発検知: 除去の直後に `git status --porcelain` を必ず読み、` D` 行が 1 行でもあれば
  即座に `git checkout -- <path>` で復元する (本件はこの手順で検出・復旧した)。

### {{F:umask-in-launcher-corrupts-merged-worktree-modes}}. 受入 launcher の `umask 077` が merge 済み作業ツリーの mode を壊し、受入を 32 件赤にした [計測汚染] [手順漏れ]

- 事象: 受入全走 attempt 1 が `18 error, 14 failed, 15359 passed, 60 skipped` で落ちた。
  赤はすべて `orchestrator/tests/test_codex_reasoning_ab.py` に集中しており、
  本 wave が 1 度も触っていない file である。junit の本文は
  `ValidationError: st_mode mismatch docs/decisions.md: 0o100600 != 0o100644` 等で、
  distinct な first-line は 11 種、すべて `st_mode mismatch` か
  それを含む assertion だった。
- 根本原因: 受入を起動する launcher script に `umask 077` を書いていた。
  `tools/dev_wave_wait.py acceptance` は claim 後に **自分で local main を merge する**ため、
  git がこの umask のまま作業ツリーへ file を書き、
  **incoming の 47 file すべてが 0600 (実行可能 1 件は 0700) になった**。
  `test_codex_reasoning_ab.py` は repo snapshot の `st_mode` を検査するため、これを拒否した。
  **git は実行ビット以外の permission を追跡しないので、この破損は
  `git status` にも `git diff` にも現れず、index からも復元できない。**
  修正した file 数 47 が merge の incoming file 数 47 と完全一致し、因果が閉じた。
- 恒久対応: **git 操作を含む走行の launcher で `umask` を触らない。**
  job artifact の permission を絞りたい場合は、作成した artifact だけを個別に `chmod` する。
  受入 launcher の正本は `docs/pegasus-runbook.md` の受入 lease 待ち手の節であり、
  同節の定型に `umask` は含まれていない — 定型へ勝手な行を足したことが直接の原因である。
- 再発検知: 赤が `st_mode mismatch` を含むなら本件型である。
  `git ls-files -s` の記録 mode と作業ツリーの実 mode を突き合わせて差分を数え、
  0 でなければ `chmod` で戻してから再投入する。差分件数が直前の merge の
  incoming file 数と一致するかも併せて確かめる。
- 補足: 単独再走 (`test_codex_reasoning_ab.py` だけ) は 454 passed / 2 skipped で緑だった。
  この時点で一部の mode が既に戻っていたためであり、**「単独で緑なら非帰属フレーク」という
  読みは本件では誤り**である。`DW-O18` の単独再走は必要条件であって十分条件ではない。
  junit の assertion 本文まで読んで初めて帰属が確定した。
