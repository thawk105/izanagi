## 偽赤の構成

小規模な通常履歴については、静的検査上の偽赤を確認できなかった。

- `I:[a]` から main を複数回取り込み、各 merge が親の和集合を保持する形は受理される。
- `R:none` から `I:[a]` と `S:none` が分岐し、`M(I,S):[a]` とする F600 型 merge も受理される。
- wave branch をそのまま ff-only land する場合、新しい履歴形は増えないので受理される。
- `P:[a,c] -> Q:[a,b,c]` という cherry-pick/rebase 型の中間挿入も部分列判定を通る。
- 台帳を変えない通常 commit の revert も受理される。批准行を落とす revert は確定契約どおり拒否される。

一方、次の正しい直線履歴は規模によって実行時の偽赤になる。

```text
C0:none
  -> C1:[d1]
  -> C2:[d1,d2]
  ...
  -> CK:[d1,...,dK]
```

全 commit が「1 commit 1 行追加」を満たす。しかし全世代の行 tuple を保持し、各 blob の重複検査がリスト線形探索なので、十分大きい K でメモリ枯渇または実用上の停止に至る。

もう一つは、`I:[a]` の後で台帳を変えず `hooks/` 配下の別ファイルだけを N 回変更する履歴である。各 commit は正当だが、異なる `hooks` tree ごとに別の Git process が起動される。

## テストの殺傷力

合成 merge はすべて `write-tree` と `commit-tree -p` で親を明示しており、porcelain merge の成否には依存しない。commit 日時は固定されていないため OID 自体は再現不能だが、検査対象の DAG 形状は決定的である。

追加 16 シナリオの評価は次のとおり。

| テスト | 評価 | この assert を通る主な誤実装 |
|---|---|---|
| pre-ledger branch merge | 弱点あり | 台帳なし親を含む merge の検査を丸ごと省略 |
| concurrent append merge | 他の拒否例との組合せで有効 | merge の親を無視して HEAD 集合だけ返す |
| single-parent middle insertion | 既存の並べ替え拒否との組合せで有効 | 順序検査を完全に除去 |
| opposite branch order | M-10 に有効 | 第一親だけの順序を見る実装は通るが、この操作では許容範囲 |
| octopus positive | 弱い | 3 番目以降の親を無視 |
| repeated pre-ledger merges | 弱点あり | 台帳なし親を含む merge の検査を省略 |
| independent introductions | 有効 | 導入数を数えない実装を殺す |
| merge omission | 2 親では有効 | 第一親だけを見る実装はこのテストで露呈する |
| unknown substitution | 有効 | 親和集合の部分集合検査を外す変異を殺す |
| merge adds two rows | 有効 | 新規行上限を 2 へ緩める変異を殺す |
| invalid middle transition | 弱い | 最新 2 遷移だけを検査する実装でも通る |
| CRLF | 有効 | `splitlines()` 復帰を殺す |
| symlink/gitlink | 有効 | 両種を実際の tree entry として作る |
| shallow | 有効 | `file://` と `--depth=1` なので実際に shallow clone になる構成 |
| effective graft | 有効 | graft guard 除去を殺す |
| empty graft + unrelated replace | 有効だが診断性は低い | 2 正例を一つにまとめているため失敗原因を分離できない |

特に [中間遷移テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:697) の不正 commit は `HEAD^` であり、全史検査を強く証明するほど深くない。

共有 [ratified_enforcement_source fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/conftest.py:191) は「初期 commit -> 1 行導入」で新規則を満たす。[T-671 の拒否例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_t671_source_binding.py:450) は台帳なし、[受理例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_t671_source_binding.py:472) は導入 1 件であり、静的には破綻を認めない。

## 実行時の破綻

以下を置く。

- N: 到達可能 commit 数
- E: 親 edge 数
- B: 異なる台帳 blob 数
- D: 台帳を持つ commit に現れる異なる `hooks` tree 数
- `r_j`, `L_j`: blob j の行数と byte 数

Git 呼出し回数は厳密に次となる。

```text
G = 6 + D + B
```

固定 6 回は top-level、shallow、graft path、HEAD、log、batch-check である。その後、[tree cache 構築](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:462) が D 回、[blob 読み込み](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:496) が B 回起動する。

親実測では実 main の B=1 なので、この実装は D>=1 より最低でも 8 回である。したがって「0.244 秒、6 回」は probe_rule3 の値であり、この実装の値とは一致しない。実装の実測値は提示されていない。

[batch-check](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:385) は commit ごとに台帳 path と `hooks` directory の 2 query、合計 2N query を送る。入力と出力はともに O(N) で、`subprocess.run` が全量を同時に保持する。

直線 K 行追加履歴では次になる。

```text
B = K
D >= K
Git blob IO = sum(L_j) = O(K^2)
保持する全 row tuple = sum(r_j) = O(K^2)
_load_rows の重複検査 = sum(r_j^2) = O(K^3)
```

`digest in digests` が list 探索であることが三次量の原因である。[該当箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/campaign/enforcement_source_ratification.py:149)

10 秒 timeout は process ごとである。次のどれかが成立すると、正しい履歴でも明示的な履歴エラーになる。

```text
t_log(N,E) > 10
t_batch(2N) > 10
t_blob(max L_j) > 10
t_tree(max hooks-tree-size) > 10
```

Python 内の O(K^3) 処理には timeout 自体がなく、OOM または上位処理の停止条件まで走り続ける。

## 所見

- `must-fix` 全世代の row tuple 保持と list 重複検査により、裁定で閉じるはずだった二次メモリが残り、CPU は最悪三次量になっている。さらに Git 呼出しは `6+D+B` で、親の 6 回実測と一致しない。
  成果物への影響: 正当な台帳成長が timeout、OOM、長時間停止で拒否され、certified v2 lock が作られず、certified 選択と対応レポートが正しい台帳参照へ到達しない。

- `should-fix` 台帳を持つ親が 1 個、持たない親が 1 個の merge は正例しかない。`if any parent lacks ledger: skip validation` という誤実装が全追加テストを通りうる。`I:[a] + S:none -> M:[b]` または `M:[a,b,c]` の拒否例を足すべきである。[対象 fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:557)
  成果物への影響: 現実装の値は変わらないが、この回帰を逃すと本来拒否する履歴が受理され、返却台帳集合が `{a}` ではなく `{b}` などへ置換され、誤った digest の certified 選択が可能になる。

- `should-fix` octopus は受理例だけで、3 番目の親の行を落とす拒否例がない。親を最初の 2 件に固定する誤実装を殺せない。[対象テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1759-t1742-ratification-history/orchestrator/tests/test_enforcement_source_ratification.py:534)
  成果物への影響: 現実装の値は変わらないが、回帰時には 3 番目の親の批准 digest を落とした履歴が受理され、台帳参照集合と certified 判定が親 DAG と不整合になる。

- `should-fix` 不正中間遷移が `HEAD^` にあり、固定深度 2 程度しか見ることのできない誤実装でもテストが通る。不正遷移後に複数の正常 commit を置くべきである。
  成果物への影響: 現実装の値は変わらないが、全史検査の退行時には古い置換履歴が受理集合へ入り、HEAD の digest が不正な履歴を根拠に certified として選択される。

- `nit` 空 graft と unrelated replace ref は別テストへ分離すると、過剰拒否の原因を直接特定できる。
  成果物への影響: 受理集合、台帳値、レポート参照は変わらず、失敗時の診断粒度だけが変わる。

## 総括

実装の DAG 判定自体には、通常規模の main 反復 merge、ff-only land、台帳なし枝との merge、rebase 型挿入を拒否する明白な経路は見つからなかった。一方、性能設計は確定契約と親実測に一致せず、正当な長期台帳を二次メモリ、三次 CPU、線形 process 数へ追い込むため `must-fix` である。

pytest は実行しておらず、以上は指定 8 ファイルだけを用いた静的レビューである。