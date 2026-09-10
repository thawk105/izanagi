## 判定 (GO / NO-GO)

**NO-GO**。

静的検査のみ実施した。ファイル変更、pytest、`decide()` probe は実行していない。親報告の唯一の失敗に加え、採用済みの祖先防護に未被覆がある。

## must-fix

| # | 判定 | 内容 | file:line | 成果物影響 |
|---|---|---|---|---|
| 1 | real | T-956 の inode scan テストが、従来の hooks index だけを前提に `os.walk` の総回数を 1 と固定している。変更後の Bash 判定は hooks と authority の独立 index を作り、通常の hardlink ケースで両方を走査するため 2 回になる。各 index が一度だけ構築される、という契約と総回数 1 は同義でない。 | [guard_bash.py:2288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2288)、[guard_bash.py:2695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2695)、[guard_bash.py:2724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2724)、[test_hooks.py:1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1195) | 親の全走が 1 failed のままで、受入を緑として着地できない。 |
| 2 | real | 「祖先」判定は filesystem root `/` だけを捕捉しない。`_inside(path, "/")` が `path.startswith("//")` を評価するため、authority root に対して偽になる。結果として `rm -rf --no-preserve-root /` は authority trigger に乗らず fast path で許可され得る。テストは直上の `/work/1/SFC/tanab` しか検査していない。 | [guard_bash.py:2284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2284)、[guard_bash.py:2375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2375)、[guard_bash.py:2695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2695)、[guard_bash.py:2735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2735)、[test_hooks.py:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1364) | README が「祖先を対象にした削除を拒否」と主張する一方、authority subtree を含む `/` の破壊を許すため、防護成果物を消去できる。 |

## should-fix / nit

- **real — README 内で hardlink の説明が矛盾する。** 通常判定は authority 配下の regular file の inode を索引化し、外部 hardlink alias を捕捉する。その一方で残余一覧は「有効化前から存在する hardlink alias」を開いた面に含めている。元 file が現在も authority 配下にある pre-existing alias は索引で捕捉されるため、この記述は強すぎる。[README.md:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:160)、[README.md:405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:405)、[guard_write.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:182)、[guard_bash.py:2363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2363)

- **real — 祖先判定が mutator の方向を区別せず、正当な「祖先への格納」も拒否する。** 例えば `mv /tmp/result /work/1/SFC/tanab`、`install … /work/1/SFC/tanab`、`rsync src /work/1/SFC/tanab`、`tar -xf … -C /work/1/SFC/tanab` は、authority を破壊・上書きしない内容でも拒否される。S1 が採用したのは祖先そのものの破壊であり、R4 の archive/source-basename 解析は不採用だった。[s4-adjudication.md:44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2146-authority-guard/s4-adjudication.md:44)、[s4-adjudication.md:59](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2146-authority-guard/s4-adjudication.md:59)、[guard_bash.py:2411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2411)、[guard_bash.py:2622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2622)

- **real — fast path は重くなった。** token 化できる全 command で `_authority_command_hot()` を fast-return より先に走らせる。既存 regular file の token が一つあれば、authority と無関係でも `protects()` が authority subtree を一度 `os.walk` する。authority が小さい現状では主に固定 overhead だが、「文字列不在なら即許可」ではなくなった。[guard_bash.py:2335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2335)、[guard_bash.py:2387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2387)、[guard_bash.py:2695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2695)、[guard_bash.py:2729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2729)

- **refuted —「実 authority root が一度も検査されない」は成立しない。** direct Write/apply_patch/Bash、canonical alias、読取り、subprocess smoke は固定の実 root を使う。hardlink テストも実 root の inode index 構築を先に確認する。[test_hooks.py:1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1285)、[test_hooks.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1404)、[test_hooks.py:1480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1480)、[test_hooks.py:1593](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1593)

- **real — 合成 fixture へ逃げる箇所は限定されている。** 外部 hardlink を実 root の file に作れない `EXDEV`/権限環境では hardlink end-to-end 部分だけ synthetic authority に切り替える。canonical から独立した lexical 判定も、実 authority 内に escape symlink を作れないため synthetic である。妥当な逃がし方だが、実 mount をまたぐ hardlink 成立時の end-to-end は managed sandbox では走らない。[test_hooks.py:1430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1430)、[test_hooks.py:1496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1496)

- **real — scope 外 residual を acceptance bit として固定するテストは薄い。** T-2146 の正例は pure reader と symlink-entry 操作を検査するが、`pushd`/`env --chdir`、ANSI-C/brace、archive basename、`perf -oFILE`、fallback alias が未実装のままであることは固定しない。[test_hooks.py:1548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1548)、[test_hooks.py:1563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1563)、[s4-adjudication.md:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2146-authority-guard/s4-adjudication.md:56)

## README の主張と実物の照合

主たる実装主張は一致している。固定 module 定数、lexical/canonical 境界、inode alias、apply_patch 全 directive、source-side `resolve_final=False`、Bash の ancestor/glob/cwd/perf/builder 分離はいずれも実装に存在する。[README.md:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:155)、[guard_write.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:47)、[guard_write.py:336](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:336)、[guard_bash.py:2363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2363)、[guard_bash.py:2713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2713)

R1〜R9 の照合結果は次のとおり。

| 裁定 | 判定 | README / 実装 |
|---|---|---|
| R1 読取り・署名能力 | real、記載あり | 公開鍵だけでなく秘密鍵読取りも通り、D906 完了を主張しない。[README.md:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:392) |
| R2 cwd 状態模型 | real、記載あり | `pushd`、`env --chdir`、subshell、条件実行を残余として列挙。実装が追うのは `cd` の直列状態だけ。[README.md:407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:407)、[guard_bash.py:2705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2705) |
| R3 ANSI-C quote | real、記載あり | `$'…'` による分割を明記。[README.md:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:408) |
| R4 archive/source basename | real、記載あり | 親 directory からの生成・上書きを明記。[README.md:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:408) |
| R5 `perf -oFILE` | real、記載あり | 実装も `-o FILE`、`--output`、`--output=` のみを専用認識する。[README.md:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:409)、[guard_bash.py:2781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2781) |
| R6 fallback alias | real、記載あり | 両 main の fallback は境界付き exact literal だけで、canonical/hardlink alias は見ない。[README.md:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:409)、[guard_write.py:447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:447)、[guard_bash.py:2883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2883) |
| R7 別 surface・同一 uid | real、記載あり | script、変数、`python3 -c`、persistent shell、別 process、cron、IDE、MCP/apps/plugins/子、設定面、path-free Git、同一 uid を列挙。[README.md:401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:401) |
| R8 copy-out 非対称 | real、記載あり | `cp`/`rsync`/archive backup は拒否され、`cat` は通ると明記。[README.md:411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:411) |
| R9 保守的偽陽性 | real、記載あり | 実行されない `cd` と opaque command のデータ表示を明記。[README.md:413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:413) |

ただし、閉じない面の列挙には二つ不足がある。

- **real — brace expansion が未記載。** `_glob_prefix()` が扱うメタ文字は `*?[` だけで、`dev-wave-{auth,foo}ority` のような brace expansion は authority path と認識されない。段3レンズBは brace を残余に含めていた。[s3-lens-b.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2146-authority-guard/artifacts/dev-wave-t2146-authority-guard/s3-lens-b.md:9)、[guard_bash.py:2254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2254)、[guard_bash.py:2393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2393)

- **real — directory bind alias は未記載。** inode index は既存 regular file を捕捉するが、別 path に bind された authority directory を通じた未存在 file の作成は lexical、realpath、既存 inode のどれにも一致しない。README は open fd は挙げるが、この directory alias を挙げない。[guard_write.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:129)、[guard_write.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:182)、[README.md:405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:405)

R1〜R9 の scope 外機構がこっそり実装された形は **refuted**。shell 状態模型、quote/brace 展開、archive 内容解析、`perf -oFILE`、alias-aware fallback、別 tool surface は入っていない。R8/R9 は「修正」されず、README どおり残っている。[guard_bash.py:1295](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:1295)、[guard_bash.py:2598](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2598)、[guard_bash.py:2781](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2781)、[guard_bash.py:2883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2883)

2 guard の authority 固有設計は概ね一貫している。

- **refuted — 定数・境界・inode 判定の片側欠落はない。** `_AUTHORITY_ROOT`、`_AUTHORITY_LITERAL_RE`、`_inside`、`_HooksInodeIndex`、`_authority_path_violation` は同名・同じ境界規約である。[guard_write.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:47)、[guard_write.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:79)、[guard_bash.py:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:108)、[guard_bash.py:2284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2284)

- **refuted — `resolve_final` の事故的な不一致はない。** Write guard は apply_patch の Delete/Move source、Bash guard は rm/rmdir/unlink、mv source、git rm/mv source、find destructive sourceだけで final を解決しない。surface 固有の同じ意味である。[guard_write.py:356](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:356)、[guard_bash.py:2563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2563)、[guard_bash.py:2622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2622)

- **refuted — Bash だけにある ancestor/glob/cwd/perf/fast-path 判定は意図的。** Write 系 API は単一 destination path を直接受ける一方、Bash は command の方向・cwd・globを解析する必要がある。片側欠落ではない。[guard_write.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:384)、[guard_bash.py:2363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2363)、[guard_bash.py:2713](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2713)

## 過剰拒否の所見

- **refuted — 名前が近い path は巻き込まれない。** `…-copy`、`…2`、同じ親の無関係 directory、job dir、当該 worktree を Write/apply_patch/Bash の三面で許可するテストがある。branch 名中の `authority-guard` も固定 absolute root と path component が一致しない。[guard_write.py:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_write.py:79)、[guard_bash.py:2375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2375)、[test_hooks.py:1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1521)

- **refuted — pure read と検証器の公開鍵読取りは壊れない。** `cat`、`grep`、`sha256sum`、`stat` は実 authority public key で許可され、subprocess smoke も rc=0 を要求する。process 内部の `O_RDONLY` はそもそも Write/Bash PreToolUse の外である。[guard_bash.py:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:135)、[test_hooks.py:1548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1548)、[test_hooks.py:1611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1611)、[s3-lens-b.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2146-authority-guard/artifacts/dev-wave-t2146-authority-guard/s3-lens-b.md:30)

- **real — copy-out は拒否される。** `cp <authority>/public-key /tmp/x` は source が `protected_hits` に入り、`cp` が reader allowlist 外なので拒否される。README が明記する既知の偽陽性で、今回こっそり生じた未記載変更ではない。[guard_bash.py:2183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2183)、[guard_bash.py:2831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2831)、[README.md:411](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/README.md:411)

- **refuted —別 job dir の掃除、個別 worktree の撤去、job/worktree 内への成果物移動は ancestor 判定に当たらない。** 拒否される祖先は `/work`、`/work/1`、`/work/1/SFC`、`/work/1/SFC/tanab`。`/` は前述の欠落で通る。`dev-wave-jobs/...` と `izanagi/.claude/worktrees/...` は authority の兄弟側 subtree なので拒否されない。[guard_bash.py:2375](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2375)、[test_hooks.py:1528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1528)

- **real — exact ancestor を destination にする操作だけは巻き込む。** 上記のとおり、共有親 `/work/1/SFC/tanab` へ無関係な file を `mv`/`install`/`rsync`/`tar` する操作も拒否される。[guard_bash.py:2586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2586)、[guard_bash.py:2622](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2622)

受入 command 形については次の結論となる。

- **refuted — `git diff --cached --output=` は通常出力先なら許可される。** output option の値だけを防護判定し、protected source を読むこと自体は許可する既存正例がある。[guard_bash.py:1947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:1947)、[test_hooks.py:1961](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1961)

- **refuted — `git worktree` と worktree path の `rm -rf` は authority と重ならない限り許可される。** `git worktree` は authority-specific destroy subcommand 集合に含まれず、個別 worktree path は境界判定で兄弟となる。[guard_bash.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:173)、[guard_bash.py:2586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2586)、[test_hooks.py:1531](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1531)

- **refuted（条件付き）— 成果物の `mv` は job/worktree 内なら許可される。** exact authority root、その子孫、または上記の祖先そのものを operand にした場合だけ新規拒否になる。[guard_bash.py:2563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2563)、[guard_bash.py:2662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/hooks/guard_bash.py:2662)

- **real — 受入全走は別経路で既に赤である。** caller command の拒否ではなく、must-fix #1 の scan-count assertion が変更後の二 index 構造に追随していない。[test_hooks.py:1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2146-authority-guard/orchestrator/tests/test_hooks.py:1195)

## 裁定パッケージ候補

1. shell expansion 全体を防護対象間で一般化するか。brace expansion、ANSI-C quote、`pushd`/wrapper cwd、subshell/条件制御、`perf -oFILE` を authority 専用でなく全防護 tree 共通の parser/state model として扱う候補。

2. path の方向モデルを一般化するか。copy-out 非対称と ancestor destination の偽陽性を解消するには、`cp`/`mv`/`install`/archive/rsync の source、destination、内容由来 basename を共通に区別する必要がある。

3. bind mount、既存 fd、別 process、同一 uid を含む OS 境界を設けるか。D906 の真正性を主張するなら hook parser ではなく、別 principal/host または hardware signer を trust boundary とする候補。

## 総括

実装の中核は段4裁定どおりで、兄弟・job・worktree path、pure read、公開鍵 verification を巻き込まない。R1〜R9 の scope 外機構が隠れて実装された形も見つからなかった。

一方、受入は inode scan-count テストで現に赤く、さらに `/` が ancestor 防護から漏れる。この2件のため **NO-GO**。加えて、exact ancestor への無関係な格納操作の過剰拒否、fast-path 前の authority inode scan、README の hardlink 矛盾と brace/bind residual の記載漏れが残る。