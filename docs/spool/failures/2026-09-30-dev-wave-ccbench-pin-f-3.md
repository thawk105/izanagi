---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-30
wave: dev-wave-ccbench-pin-f
seq: 3
---

## 新規

### {{F:isolated-session-compound-command-rejected}}. 隔離 session で複合 command を書き、guard の「分類不能」拒否を形を変えて 8 回踏んだ [手順漏れ]

- 事象: 背景 job の worktree 隔離 session (md_15、2026-09-30) で、同じ理由の拒否を 8 回受けた。拒否されたのは次の形だった。`git -C <path>`、`cd <dir> && git …`、変数を引数に取る `sed`/`python3` (`sed -n … $J/x`、`python3 -c "…'$J/…'"`)、`bash <script> > log 2>&1; echo rc=$?; cat log` の連結、`.git` を path に含む for loop、防護 path (`external/ccbench`) と `$()` やheredoc の同居。1 回ごとに形は変えていたので同一 command の再試行ではない。ただし「隔離 guard は command の形を静的に分類し、読めない形は拒否する」という同じ原因に、8 回とも事前に気づかなかった。
- 根本原因: 隔離 guard (「worktree 外へ git を向けない」の静的検査) と guard_bash (防護 path と不透明構文の同居の禁止) は、実行内容ではなく command の字面を分類する。変数・連結・redirect・heredoc があると分類不能として fail-closed になる。読むだけの command でも拒否される。DW-O03 は防護 path と不透明構文の同居だけを書いており、隔離 guard の「変数を引数に取る command」「`cd && git`」「`-C`」の拒否は書いていない。
- 恒久対応: 未実施。提案 = `docs/dev-wave/operations.md` の DW-O03 に「隔離 session では、job dir の file を読む command に変数を使わず絶対 path を直書きする。git は `-C` も `cd … &&` も使わず単独 command にする。複数手順は Write で script file を作り、`bash <絶対 path>` 単独で起動する (log は script 内の `exec > log` で書く)」の 1 行を足す (本 wave の段 8 ではなく、調整役への提案として送った)。
- 再発検知: 隔離 session で Bash を書く前に、command に `$`・`&&`・`;`・`|`・`>`・`-C`・`.git` が入っていないかを見る。入っているなら script file にする。

### {{F:parallel-preflight-and-commit}}. provenance の事前検査が赤なのに、並列に出した commit が通った [手順漏れ]

- 事象: md_15 の停止明け (2026-10-01 09:4x) に、main の取り込み merge の commit message を `check_ai_provenance.py --message-file` で検査する呼び出しと、`git commit -F` の呼び出しを同じ応答で並列に出した。検査は rc=1 (「実装面に Codex role=author がない」、自動 merge で両側の変更が入った 4 file) を返したが、commit は検査の結果を待たずに通った (`54e16402f`)。commit 後の範囲監査 (`--range 5b859814b..HEAD`、55 件) は違反なしだった。衝突の無い自動 merge は combined diff (`--cc`) では自明で、commit 後の監査の対象 path に残らないためである。
- 根本原因: DW-O17 の「検査 rc をパイプへ渡さず赤で停止する」「preflight と commit を同じ shell で行うなら先頭を `set -e` にし、無ければ tool call を分ける」を、並列の tool call で破った。依存のある 2 手 (検査 → commit) を独立とみなした。
- 恒久対応: DW-O17 (既存の規定) をそのまま守る。検査と commit を同じ応答で出さない。
- 再発検知: commit を出す前に、同じ応答内に検査の呼び出しが無いかを見る。あれば commit を次の応答へ送る。
- 付記: message-file の事前検査 (index と各親の差の積集合) と、commit 後の監査 (combined diff) とで、衝突の無い自動 merge の判定が食い違う。事前検査だけを見ると、自動 merge にも Codex author が要るように見える。

## 再発

### F810

- **再発: 2026-09-30** — md_15 の wave worktree と実装子 worktree の 2 本とも、`tools/dev_wave_submodule_init.py` の 1 回目が `runtime-io-failure: detail={'label': 'submodule', 'kind': 'update-no-fetch'}` の rc=1 で、同じ argv の 2 回目で rc=0 だった (実装子側は作成 script が `||` で 1 回だけ再実行する形にしてあった)。worktree 作成時に `.gitattributes` の「システムコール割り込み」warning も出ていた。恒久対応は引き続き未実施。
