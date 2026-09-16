## 所見一覧 (real / refuted、成果物影響つき)

行番号は job dir の [launcher](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-liveness/run_screening_liveness.sh) を指す。

| ID | 分類 | 所見・成果物への影響 |
|---|---|---|
| R1 | **real / must-fix** | **指定の投入形では `PBS_JOBID` が届かず、12行目で必ず rc=2。** generic は `env_mode="clean"`、環境 allowlist は空。基底環境にも `PBS_JOBID` はなく、子起動前の追加もない。影響：CLI 未起動、関門・WAL の証拠は得られない。 |
| R2 | **real / should-fix** | 102行目に `-u` がなく、CLI の通常 `print` はファイル出力時にバッファされる。影響：stderr・子 process 出力との時系列逆転、強制終了時の未 flush ログ消失があり、赤の到達位置の証拠が弱くなる。 |
| R3 | **real / 既知限界** | CLI が stock worktree を撤去できない場合、88行目の cleanup は実体だけを削除し、Git 登録を残す。影響：dangling 登録が残り、親の終了後検査と復旧が必要。 |
| R4 | **real / 既知限界** | 28行目の root 未存在検査は予約ではない。影響：検査後に同じ root が作られると、今回専用・新規という証拠条件を launcher 単独では保証できない。 |
| R5 | **real / 証拠上の限界** | 111–114行目の検査失敗も CLI rc を変えない。影響：rc=0 でも tree 状態が未確認の場合があり、親の再検査なしに緑とは判定できない。 |
| F1 | refuted | `pgrep` rc=1 を競合・実行失敗と誤認する：明示的に許容している。 |
| F2 | refuted | `ps \| head` の SIGPIPE：pipeline はなく、`ps` 全出力を保存してから here-string で `head` に渡している。 |
| F3 | refuted | EXIT cleanup が CLI rc を上書きする：`cli_rc` を直後に保存し、`exit "$cli_rc"`。trap は明示的な `exit` を持たず、`find` 失敗も吸収する。 |
| F4 | refuted | 未設定 `TMPDIR` から `/` を削除する：値の設定・専用 directory 作成成功後にだけ trap を登録する。`"$TMPDIR"` に危険な既定値展開もない。 |

R1 の根拠：[generic 定義](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/tools/pegasus/dispatch_compute.py:154)、[基底環境](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/tools/pegasus/dispatch_compute.py:349)、[子環境構築](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/tools/pegasus/dispatch_compute.py:1623)。以下の後段評価は、この阻害要因が解消された場合の静的評価である。

## 失敗の型と rc の表

| 分岐・失敗 | launcher rc | CLI 起動 |
|---|---:|---|
| 引数数不正、HEAD/pin の40桁形式不正 | 2 | なし |
| `PBS_JOBID` 未設定・形式不正 | 2 | なし |
| hostname 不適合 | 2 | なし |
| Git worktree でない、HEAD/pin 不一致 | 2 | なし |
| superproject/submodule の tracked dirty | 2 | なし |
| root が相対・既存・dangling symlink | 2 | なし |
| `/scr` が directory でない・書込不可 | 2 | なし |
| Python 候補の `command -v` 失敗 | 次候補へ | なし |
| Python 候補の版検査失敗 | 次候補へ | なし |
| 全 Python 候補不成立 | 2 | なし |
| 選定中の realpath 取得失敗 | 2、ERR trap | なし |
| `ps`・`awk` 等、前処理の未捕捉 command 失敗 | 2、ERR trap | なし |
| `pgrep` rc=1、0件 | 続行 | 後続次第 |
| `pgrep` rc>1 | 2 | なし |
| `USER` 未設定 | 2 | なし |
| ycsb 競合／他ユーザー `%CPU >= 50` | 3 | なし |
| PATH 固定後 Python 実体が実行不可 | 2 | なし |
| 必須 command の `command -v` 失敗 | 2 | なし |
| scratch が既存／権限等で `mkdir` 失敗 | 2、cleanup 未登録 | なし |
| dependency prefix 不在 | 2、cleanup 実行 | なし |
| CLI 通常終了・非ゼロ終了 | **CLI rc そのまま** | あり |
| CLI 実行不能／実体消失 | 通常126／127 | 正常起動なし |
| 終了後の `git`・`ls`・`date` 失敗 | CLI rc のまま | 済み |
| EXIT trap の `find` 失敗 | 元の終了 rc のまま | 状況次第 |
| CLI のみ SIGTERM／SIGKILL、shell 生存 | 通常143／137 | あり |
| launcher 自身も強制終了 | CLI rc 保持・終了記録は保証不能 | 状況次第 |

`set +e` に加えて ERR trap も解除しており、CLI 非ゼロを rc=2 に変換する欠陥はない。cleanup 内で `$?` を保存していないこと自体も、この実装では欠陥ではない。

## tree への副作用と復旧

通常終了・Python 例外では、`applied()` の `finally` が patch を revert し、外側の `checkout()` が stock worktree を撤去する。撤去失敗時には登録残留を検査して例外化する。

**CLI 終了 → tree 状態出力 → cleanup の順序は、残骸を記録する目的に適切。** 撤去漏れがあれば、114行目の一覧に `$TMPDIR/izanagi_wt_…/wt` が残るため親が検出できる。ただし、この時点で実体が存在すれば `prunable` 表示は必須ではない。cleanup 後に初めて dangling になる場合があり、一覧を「cleanup 後の clean 証明」と扱ってはいけない。

PBS による終了では次が残りうる。

- Python が SIGTERM/SIGKILL されると、context manager の `finally` は保証されず、投入元 patch と stock 登録が残る。
- launcher も SIGTERM を受ければ、最終状態出力・EXIT cleanup の完遂は保証できない。SIGKILL では trap 自体が走らない。
- scratch、Git lock file、途中の official output/WAL が残りうる。逆に cleanup が走れば、一時調査資料だけ消える場合もある。

段4の不変条件 (iii) に従い、親が終了確認後に HEAD/pin・tracked status・worktree 一覧を再実測する必要がある。計算ノードの `/scr` は login から同じ実体が見えるとは限らないため、欠落表示だけで稼働中の worktree を prune しない。終了を確定してから、対象を限定した復旧を記録する。今回のレビューでは復旧操作は行っていない。

## official root と stdout

root の28行目は「絶対・末端が未存在」を検査するだけで、`..`、祖先 symlink、`.git` 祖先、所有者を検査しない。これらは `layout.py:323–367` が後で検査するため、検査を迂回して受理する仕組みではない。ただし、不正入力が CLI 起動後まで持ち越され、今回の赤を消費する可能性がある。

所有者検査は、検査時に root が存在する場合に適用される。layout は既存 root 自体を禁止しないので、新規性の TOCTOU は残る。親確認済みの `.git` 祖先不在と attempt 専用名は有効だが、原子的な予約ではない。

`exec 2>&1` は冒頭、CLI の `2>&1` も起動 command に付いており、launcher 配下の stderr は stdout と同じ出力先に流れる。位置の誤りはない。ただし、同じ FD でも各 process のバッファリングによる順序逆転は防げない。**`-I -B -u` とする修正を推奨する。** `-I` 下では `PYTHONUNBUFFERED` の環境設定に頼れない。

stdout だけでは段2の赤を全部分類できない。traceback による prepare/gate の区別は可能な場合があるが、build/correctness/bench の詳細には WAL が必要で、dispatch 障害には result・receipt・scheduler stderr が必要。破棄された arm detail は復元できない。`-u` を加えてもこの限界は残る。

## 環境の罠

| 項目 | 判定 |
|---|---|
| `PBS_JOBID` | **確定不成立。** generic の clean 環境から落ちる。scheduler が親に設定することでは解決しない。 |
| module 由来 Python | 絶対 realpath で起動するので PATH 固定だけでは失われない。ただし版検査後に `LD_LIBRARY_PATH` 等を消すため、それに依存する interpreter は本起動で失敗しうる。該当実体の有無は**未実測**。 |
| `numactl` | 固定 PATH 下の `command -v` で存在を検査する。計算ノードでの実在・実行能力は**未実測**。 |
| `/scr` の `:` | `0:980676.nqsv` は受理し、`0_980676.nqsv-t2228-screening` に変換する。入力に `/` を許さず、安全に一成分へ収める。 |
| bench lock の親 | scratch 作成後に設定するため親 directory は存在する。 |
| `HOME` / `~/.izanagi` | `lock.py` は明示された `IZANAGI_BENCH_LOCK` を先に返すため、この bench lock 経路で `~/.izanagi` は作らない。Git 等の HOME 依存設定・可読性は**未実測**。 |
| userns と `safe.directory` | dispatcher は外側 root mapping 後、内側で元の数値 uid/gid に再 mapping する。同じユーザー所有 tree が必ず別所有者になる、との主張は **refuted**。実ファイル所有者・Git 設定・計算ノードでの成否は**未実測**。不一致なら前提 Git 検査で停止する。 |

## 禁止事項

launcher は **117行**。`bash -n` 成功、SHA-256 は author 報告と一致する。

```text
66f28ca8a1b75e447252ddd1db2a62d201837424f3b43a492d7ceab5ff47557c
```

launcher 自身に clone・build・監視・sleep loop・network probe・関門改変はない。正規 CLI は1回だけ起動する。CLI 内の既存 build・patch・worktree 操作は段4で認められた挙動である。

指定4ファイルと関連コードを静的に確認した。実走・pytest・編集・commit・job 投入は行っていない。

## must-fix / should-fix / nit

- **must-fix：R1。** launcher の必須入力を generic の実際の子環境と整合させる。production dispatcher を変更せず、launcher 内で安全な一意 scratch を確保し、実 job ID の帰属は dispatcher 証拠で保持する形などを author が具体化する。架空の PBS ID で補わない。
- **should-fix：R2。** CLI argv に `-u` を追加する。
- **should-fix：** Python の版・起動検査は、実行時と同じ環境消去後にも成立させる。
- **nit：** 終了後の各 tree 検査 rc を明示すると、「clean」と「検査失敗」を読み分けやすい。CLI rc は保持する。

R3〜R5 は段4の親による再検査・証拠照合で扱える。clone 隔離、監視機構、関門への介入は要求しない。

## 総括

**現状の投入は不可。指定の generic dispatch では `PBS_JOBID` 不在により CLI 前で rc=2 となる。** 本題未実行と判定できる阻害要因なので、author 修正後に静的再確認する。

その先の rc 保持と cleanup の基本構造は成立している。緑の判定には CLI rc だけでなく、WAL・会計照合・親による終了後 tree 検査が必要である。