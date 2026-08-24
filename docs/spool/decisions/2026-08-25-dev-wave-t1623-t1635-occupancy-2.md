---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1623-t1635-occupancy
seq: 2
---

## {{D:deleted-cwd-classification}}. 削除済み cwd は readlink の生値で判定し、対象外のときだけ非占有として数える

**決定:** `tools/check_worktree_occupancy.py` は `os.readlink("/proc/<pid>/cwd")` の成功と
`Path.resolve(strict=True)` の失敗を別々に扱う。非占有として数えるのは次の論理積が
すべて成立する場合だけとする。

1. `os.readlink` が成功した。
2. その**戻り値の文字列そのもの**が正確に `" (deleted)"` で終わる (正規化前に判定する)。
3. `resolve(strict=True)` だけが `FileNotFoundError` を投げた。
4. `/proc/<pid>` が実在する (pid 消滅ではない)。
5. 生綴りと suffix 除去綴りの**どちらも**全 target の外にある。

件数は `unreachable.cwd_deleted` へ出し、非ゼロのときだけ payload へ載せる。
どちらかの綴りが対象内なら `sources` へ `cwd` を積んで **occupant のまま**とする。
suffix の無い解決失敗は従来どおり `issues` へ残す。削除済み cwd の pid でも
cmdline 検査は続け、相対 argv の base には両綴りを使う。

`dev_wave_cleanup` の最終受理条件と `_is_disappeared_pid_issue` は変更しない。

**理由:**
- 削除済み directory に居るプロセスは、その directory が対象の外にあるなら対象を占有しえない。
  一方 `/proc/<pid>` は残り pid 消滅とも判定されないため、D705 の有界再試行では永久に解けなかった。
  実測ではこの型の生存プロセス 2 本があるだけで、誰も居ない空 directory ですら
  `indeterminate` / rc=2 になり、5 scan 連続で同一だった。
- suffix を正規化前に判定するのは、`" (deleted)"` が path の意味ではなく kernel が付ける
  文字列の目印であり、正規化がそれを保存しないためである
  ({{F:strict-suffix-defeated-by-normalization}})。
- 生綴りと除去綴りの or で照合するのは、実在の directory 名が文字どおり `foo (deleted)` で
  ありうる曖昧さを安全側 (偽陽性) へ倒すためである。
- 対象**内**の削除済み subdir を occupant のまま残すのは、そこを非占有へ落とすと
  fail-open になるためである。実測では現行実装がこれを `issue` として扱っており、
  素朴な修正だと黙って非占有へ落ちることを確認した。

**却下した選択肢:**
- 解決失敗をすべて非占有として数える — bind mount・pivot_root・別 mount namespace 由来の
  到達不能 spelling まで非占有へ落ち、撤去してよいと誤答する。
- `/proc/<pid>/cwd` を fd として開き `(st_dev, st_ino)` の祖先鎖で証明する — 本 wave の
  費用対効果に見合わず、mount namespace を跨ぐ保証も得られない。
- 撤去 tool 側だけで許容する — 共有 gate が壊れたままになる (D705 と同じ理由)。

## {{D:invoker-allowlist-by-measurement}}. cmdline 除外は確認済み祖先に限り、invoker allowlist は実測で決める

**決定:** cmdline 由来の占有から除外するのは、次の論理積がすべて成立する場合だけとする。

1. 走査対象 pid が**確認済みの祖先**である。祖先鎖は `/proc/<pid>/status` の `PPid` を辿り、
   `seen` 集合で循環を止め、読めない地点で打ち切り、各段で `starttime` の前後一致を確認する。
   走査時の `start_before` が snapshot の値と一致するときだけ祖先と認める (pid 再利用を弾く)。
2. `/proc/<pid>/exe` の basename が invoker allowlist に含まれる。
3. argv に**絶対 path の checker** が載っている。
4. その checker token より**後方**の token が対象を指す。

allowlist は既存の shell 5 種に加え、**実測で偽陽性を作ることを確認した**
`timeout` / `flock` / `time` / `strace`、および実測では発火しないが多重防御として
`nohup` / `env` / `stdbuf` / `xargs` / `setsid` / `nice` / `ionice` を含む 16 種とする。
後者 7 種の到達可能性はゼロであると裁定に記録する。

**理由:**
- 直接の親だけを見る従来の除外は、`timeout` 等の wrapper を挟むと外れ、
  wrapper の argv に載った対象 path 自体が占有の証拠として数え直されていた (F525)。
- exe 名の列挙が正しい形かを実測で確かめた。allowlist に載せるべき 4 種のうち
  当初案は 1 種しか覆わず、載っていた 5 種のうち 3 種は自分を exec で置き換えるため
  到達不能だった。`DW-O13` の「述語が要求する値の到達可能性を実測してから採用する」に従い、
  中身を実測で入れ替えた。
- exe 条件を撤去して「祖先なら無条件に除外」とする案は採らない。既存の負例 2 件は
  対象を明示的に親として渡したうえで occupant を要求しており、守っている性質は
  「非祖先は信頼しない」ではなく**「親であるだけでは信頼しない」**である。
  非祖先 fixture へ書き換えるのは検出力を弱めて緑にする変更に当たる。
- 呼び出し側の規律 (wrapper を挟まず絶対 path で呼ぶ) は緩めない。本決定は多重防御であり、
  allowlist 外の fork 型 wrapper 経由では偽陽性が残る。

**却下した選択肢:**
- 祖先鎖に居るなら argv 条件も exe 条件も無しで除外する — 既存の安全契約を緩める。
- `pidfd_open` で祖先 instance を保持する — 除外が消すのは cmdline 由来の証拠だけで、
  cwd 由来の判定は祖先にも適用されるため、`starttime` + `PPid` 照合で足りる。
- 祖先 edge を invoker ごとに証明する — allowlist の列挙を根本から不要にできる有力案だが、
  要追加検証で本 wave の scope を超える。

## {{D:invalid-target-status}}. 対象指定の誤りは status で区別し、rc は判定不能と同じにする

**決定:** 対象が**不在**または**directory でない**場合、`status` を `invalid-target` とし、
stderr へ固定 1 行 `check_worktree_occupancy: status=invalid-target` を出す。
rc は `indeterminate` と同じ 2 のままとする。`dev_wave_cleanup` の status→rc 写像にも
同じ entry を足す (欠けると `KeyError` になる)。

**理由:**
- 相対 path を渡すと走査対象が空になり、`occupants: []` だけを見た呼び手が
  「撤去可」と誤読する事故が起きた。`status` が `indeterminate` でなくなり
  stderr にも出れば、`scanned=0` を見落としても原因が分かる。
- 新しい rc を足しても**受理・拒否の集合は 1 bit も変わらない** (rc2 も新 rc も
  呼び手側では停止)。区別を必要とする実 consumer は現時点で存在しない。
- 一方で新 rc は command 入口・contract literal・whole-file hash・test 側の
  期待 hash と合成 fixture・負例 literal という 7 群以上の pin 同期を要求する。
  入口の byte 予算 headroom は実測 51 bytes しかなく、追随漏れは恒久的な検査赤になる。

**却下した選択肢:**
- 新しい rc を足す — 上記の pin 費用に見合う consumer が無い。
- 現状維持 (`indeterminate` のまま) — 呼び方の誤りと `/proc` 判定不能が区別できない。
