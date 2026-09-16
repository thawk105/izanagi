## 所見一覧 (real / refuted、成果物影響つき)

**判定: must-fix あり。現行の投入形では CLI に到達しない。**

以下、L は [launcher](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-liveness/run_screening_liveness.sh) の行番号。

| ID | 分類 | 所見と成果物への影響 |
|---|---|---|
| R1 | real / must-fix | **generic dispatch は `PBS_JOBID` を子へ渡さないが、L12 が必須としている。** 指定の投入形では rc=2 で終了し、screening の record は生成されない。 |
| R2 | real / must-fix | **L57 の文字列 `"root"` 除外は userns 内でホスト root の除外を保証しない。** unmapped UID が `nobody` 等に見えると、高 CPU の root process も rc=3 の原因になり、拒否を「別ユーザーの job 同居」の証拠にできない。実ノードでの表示は未実測。 |
| R3 | real / should-fix | **`PBS_JOBID` 自体を stdout に出していない。** L86 の TMPDIR は `:` を `_` に置換するため、正確な実行 identity は stdout 単独で復元できない。 |
| R4 | real / should-fix | **L56–57 は幅20のユーザー表示と完全な `$USER` を比較する。** 長いユーザー名の省略・数値表示では自ユーザーを他者扱いし、不要な rc=3 を起こしうる。今回の `tanab` にはこの長さ問題はない。 |
| R5 | real / 解釈上の限界 | **nqsv・nobody 等も L57 の「他ユーザー」に含まれる。** 段4の述語には忠実だが、その高 CPU だけで「別 job の同居」と README に断定できない。 |
| F1 | refuted | `pgrep` 自己一致を無条件に拒否する、という指摘。L53 は結果先頭の PID と `$$` を比較して自 PID を除外する。 |
| F2 | refuted | CPU が文字列比較になる、という指摘。L59 の `$3 + 0 >= 50` は数値比較。 |
| F3 | refuted | `head` の SIGPIPE で `pipefail` が落ちる、という指摘。L48で全結果を取得し、L49は here-string を読むため、`ps | head` の問題はない。 |
| F4 | refuted | `-I` が `IZANAGI_*`・prefix・proxy・TMPDIR を消す、という指摘。これらの環境変数は保持される。 |
| F5 | refuted | CLI の非ゼロ rc が ERR trap に奪われる、という指摘。L104–107で ERR trap と errexit を解除し、L117で CLI rc を返す。 |

## 仕様 1〜6 の逐条対応

共通設定は L2–7 にあり、`set -Eeuo pipefail`、`umask 077`、stderr の stdout への統合、段名・日時出力を満たす。

| 仕様 | 対応行 | 判定 |
|---|---|---|
| 1. 前提検査 | L9–29 | HEAD・pin・両 tracked-clean・絶対かつ未存在の `$1`・書込可能な `/scr`・GIT_* 消去を網羅。L28は dangling symlink も拒否する。**PBS_JOBID 必須検査は仕様通りだが dispatch 契約と矛盾する。** |
| 2. Python 選定 | L31–42 | 候補順、`(3, 10)` 判定、`-I -B`、実行ファイルの realpath 出力を満たす。 |
| 3. 単独性 | L44–67 | 指定観測、pgrep rc=1 の正常扱い、自 PID 除外、数値 CPU 比較、理由出力、CLI 前の rc=3 を実装。userns とユーザー表示の問題は残る。 |
| 4. env | L69–99 | PATH、コマンド検査、unset 群、scratch、lock、official root、prefix、proxy は指定通り。 |
| 5. CLI 1回 | L101–107 | 配列で exact argv を出力し、指定 CLI を1回だけ起動。追加 timeout なし。 |
| 6. 終了後出力 | L109–117 | 両 tracked status、submodule worktree list、存在時の root 一覧、日時、CLI rc を出力。dirty でも rc を変えない。 |

env の詳細照合結果:

- L75–85 の unset 群は A-5 L221–231 と一致する。
- L70 の PATH 固定後、L71で絶対パスの `$PY` の実行可能性、L72–74で指定8コマンドを確認する。Python が PATH 内にある必要はない。
- L86–89 は指定 TMPDIR、`mkdir -m 0700`、作成成功後の EXIT cleanup を実装する。
- L90–96 の bench lock・official root・prefix 2本・proxy 2本は仕様と一致する。
- Python 選定は PATH 固定より前。これは author prompt の段順通りだが、PATH を先に固定する A-5 L199–200 とは異なる。**同じ Python binary を選ぶ保証はなく、realpath の記録で区別する必要がある。**
- L11 の40桁検査、L13の PBS_JOBID 文字種制限、L55の USER 非空検査は追加の入力防御。今回の通常入力について過剰拒否を示す根拠はない。

## 単独性述語

L51 の pgrep は production の `runner.py:403` と同じパターンを使う。L53 の PID 除外も意図に合う。今回の `bash <script-path> <args>` ではスクリプト本文は launcher の cmdline に入らず、「本文にパターンがあるから必ず自己一致する」は成立しない。祖先や別 process の argv に一致文字列があれば残るが、祖先まで除外する仕様ではない。

L59 は数値比較であり、L67の rc=3 は L106の CLI 起動より前に確定する。load average は拒否条件にしていない。

問題は所有者判定である。

- 幅20の `user` 表示は UID identity として使えない。今回の短いユーザー名では顕在化しなくても、一般には `$USER` との比較が崩れる。
- root 以外の system user は仕様上も拒否対象である。これは実装の逸脱ではなく、述語から「別 job」を断定する際の限界。
- userns 内ではホスト root も名前 `"root"` で見えない可能性があり、こちらは裁定の root 除外そのものを損なう。

なお `%CPU` は瞬間負荷そのものではない。通過が示すのは指定スナップショットの述語を満たしたことまでであり、全実行期間の単独性ではない。

## dispatch 環境との整合

**PBS_JOBID の欠落は静的に確定できる。**

`dispatch_compute.py:154–159` の generic は `env_mode="clean"`、`env_allowlist=frozenset()`。L349–359 の保持キーに PBS_JOBID はなく、L1442–1452で除去される。L1623–1633にも再注入はない。外側の job script が PBS_JOBID を marker に記録していても、子環境への継承とは別である。

したがって指定の `--task generic -- bash <launcher> ...` は、launcher L12で終了する。通常の request env overlay も generic の空 allowlist では解決にならない。

`USER` と `HOME` は、外側環境にあれば保持されるが、新規生成はされない。launcher は USER の非空を L55で確認する。HOME は launcher 自体では参照しない。

cwd は dispatcher L1622、L1671で repo root に設定され、今回それが対象 worktree なら整合する。request dir の read-only 化を worktree 全体の read-only 化と解釈する必要はない。

userns は外側で呼出 UID を0へ写し、内側で0を元の数値 UID に戻す構成（L297–300）。自ユーザーの数値 UID は復元される一方、ホストの他 UID 全体が写されるわけではない。unmapped UID は overflow UID として扱われ、名前解決次第で `nobody` や数値に見える。

このため単独性述語は**恒真でも恒偽でもない**。ただしホスト root と他ユーザーの識別が失われ、root 除外が機能しない経路がある。実ノードの `/proc`・NSS・`ps` 表示は**未実測**。

`-I -B` による env 消失の指摘は棄却する。

- official root: `backoff_sweep.py:238` が `os.environ` から読む。
- prefix: `buildcache.py:2629–2630` が読む。
- TMPDIR: `patchharness.py:116,362` が読む。
- proxy: `buildcache.py:887–898` の取得用環境にも保持される。
- `IZANAGI_BENCH_LOCK` も `-I` によって環境から削除されない。

探索時に `orchestrator/patchharness`、`tools/patchharness.py`、`orchestrator/calibrator/lock.py` は存在しなかった。patchharness は実在する `orchestrator/campaign/patchharness.py` を確認した。

## 出力の十分性

前提検査を通過して CLI が戻る場合の出力は次の通り。

| 値 | stdout |
|---|---|
| hostname | L45 |
| PBS_JOBID の原値 | **欠落** |
| Python realpath | L42 |
| 設定した7環境変数 | L97–99 |
| exact CLI argv | L102–103 |
| CLI rc | L110 |
| 終了後の両 tracked status・worktree list | L111–114 |
| official root 一覧・終了日時 | L115–116 |

HEAD・pin の値、cwd、USER・HOME も明示出力されない。HEAD・pin は照合成功で制約されるが、stdout 単独で実行 identity を読むには不足する。

また、段4裁定3の6条件は stdout だけでは完結しない。campaign.lock、WAL、build-done、dispatch result、receipt、会計、各ファイルの hash との照合は親の成果物回収責務であり、launcher に追加実装すべき欠落とはしない。

**現行経路では L12で止まるため、上表の後続出力は一切得られない。**

## must-fix / should-fix / nit

**must-fix**

1. 実際の割当 job の PBS_JOBID を launcher に届ける契約を確定する。検査の削除や架空値の設定では scratch 名と実行 identity の根拠を失う。
2. userns 内の名前比較では満たせない root 除外を解決する。幅を広げる、`nobody` を除外するだけでは解決しない。後者は他ユーザーも同時に隠す。

**should-fix**

- PBS_JOBID 原値を stdout に出す。
- 表示幅に依存する自己ユーザー判定を解消する。
- README では system process による拒否と別 job の同居を同一視しない。Python を含む A-5 との同一実行環境も断定しない。

**nit**

- HEAD・pin・cwd・USER・HOME を記録すれば identity の照合が容易になる。

## 総括

**投入不可。仕様1〜6の局所実装は概ね忠実だが、dispatch との接続で PBS_JOBID が消え、必ず前提検査で止まる。** その解消後も userns による root 除外の不成立が残る。

`bash -n` は成功。117行で、SHA-256 は author 報告の `66f28ca8a1b75e447252ddd1db2a62d201837424f3b43a492d7ceab5ff47557c` と一致した。実走・pytest・編集・commit・job 投入は行っていない。