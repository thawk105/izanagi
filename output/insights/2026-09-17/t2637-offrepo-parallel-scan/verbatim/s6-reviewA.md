## 前提の検算

**レンズ A の結論は GO（nit あり）です。安定した入力に対し、findings・suppressions・scan_failures・rc を変える実装上の反例は見つかりませんでした。** ただし、OID 挿入順の完全再現には反例があり、A5 のテスト保証にも不足があります。

指定された射影資料、差分、適用後の現物、Python 3.10 の `os.walk` を確認しました。差分をメモリ上で逆適用して AST を比較し、次を確認しました。ファイル変更・pytest・変異実走・性能測定は行っていません。

- 差分の全 hunk が現物と一致。
- 旧 `test_initial_patch_contains_no_parallel_execution` を置換し、新設テストは12件。
- 残存する既存テスト関数の AST はすべて不変。
- tool の既存関数で変更されたのは `_enumerate_offrepo_candidates` のみ。

以下の略号を使います。

- **A**：[audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-parallel-scan/tools/audit_dangling_commits.py)
- **T**：[test_audit_dangling_commits.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2637-offrepo-parallel-scan/orchestrator/tests/test_audit_dangling_commits.py)
- **O**：[/usr/lib/python3.10/os.py](/usr/lib/python3.10/os.py)
- **S4**：[s4-adjudication.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/s4-adjudication.md)
- **F**：[s6-fix-prompt.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2637-offrepo-parallel-scan/s6-fix-prompt.md)

「155 passed」は親・fix 子の報告であり、本レビュー自身の実走結果ではありません。

## os.walk 意味論の等価性

| 点検対象 | 判定・根拠 | 成果物への影響 |
|---|---|---|
| scandir 開始時／途中の失敗 | **refuted**。O:355、371 は `onerror` を1回呼んで return し、O:408 の yield に到達しない。A:992 は `None` を受けて候補も子 task も返さない。 | 部分 entry の救済による候補増加はなく、失敗1回を維持する。 |
| `entry.is_dir()` の失敗 | **refuted**。O:376 は OSError を nondir 扱いにする。両経路とも本物の `os.walk` を使うため同じ分類となり、その後 A:933 の候補 lstat／regular 判定へ進む。 | 分類失敗自体を余分な scan failure にせず、従来の候補選別を維持する。 |
| symlink directory | **refuted**。O:383 で `dirnames` に入り、O:418 の再帰条件を A:1001 が再現する。A:921 の directory 計数は yield を処理したときだけ増える。 | symlink 自身を走査済み directory と数えず、リンク先の候補による抑止を追加しない。 |
| queue の完了条件 | **refuted**。A:1047 の lock 内で子を投入してから `pending += len(children) - 1`。子を別 thread が取得しても、その完了更新は同じ lock を待つ。 | 未処理・処理中 task が残る間の早期完了による候補欠落はない。 |
| root 間の重複走査 | **refuted**。A:1140 の root ループ内で queue を join まで完結し、物理 path の訪問済み除外を行わない。 | `(R, R/a)` による alias 2個、同じ deny directory の失敗2回を維持する。 |
| first-seen の代表 | **refuted**。A:965、999 の key と A:967、1105 の最小値選択は、file 全件→sorted 子 directory の前順 DFS に一致する。 | hardlink の代表 path・initial_stat・metadata を維持し、代表変更による比較結果の変化を防ぐ。 |

walk key の辞書順では、同じ directory の `(0, file)` はすべて `(1, child)` より前になります。別部分木では最初に異なる directory 名で順序が決まり、その部分木内の深さに依存しません。例えば `R/x.py` と `R/a/x.py` の hardlink の代表は、並列側でも `R/x.py` です。

ただし、**異なる OID が同じ file で初めて候補になる場合の同値 key** は、次節の例外です。

## 受理集合の不変

**refuted：代表・owners・aliases・失敗数の集約が抑止を増やす経路。**

A:1105 は worker 間の代表を最小 key で選び、A:1113 は owners／aliases を集合として union します。root 間の A:1178 は keys を渡さないため、既存代表と metadata を保持します。候補の basename・size・mode・regular 判定も旧実装から保持されています。

失敗数は以下の経路で一度ずつ加算されます。

- root の lstat／permission 失敗：A:1144、1152。
- root の onerror／候補 lstat 失敗：主 thread の `counts`。
- worker の onerror／候補 lstat 失敗：worker 固有の `local`。
- worker の最終累積値：A:1061 の公開後、全 join を経て A:1088、1091 で一度だけ加算。

待機中の `slot.read()` は表示用で、`counts` に加算しません。worker 例外時は A:1085 で再送出し、途中候補を正常結果として返しません。

**real／nit：OID 挿入順は、同値 walk key で逐次順と異なり得ます。**

根拠：A:967、1105、1176。反例は次です。

```text
R/
  a/deep/same.py
  b/other.py        # same.py と hardlink
```

候補 metadata を次の順序とします。size・mode はすべて一致させます。

```text
same.py → OID A
same.py → OID B
other.py → OID B
```

逐次 DFS は `a/deep/same.py` を先に処理するため、OID 挿入順は `A, B` です。

並列側では、同じ worker が queue 順に `a`、`b`、`a/deep` を処理できます。`b/other.py` で B の group/key を先に作り、`a/deep/same.py` で A を追加して B の key を小さく更新すると、keys の挿入順は `B, A` のまま、両 key が同値になります。A:1176 の安定ソートは `B, A` を保持します。

代表・metadata・identity 順・owners・aliases は正しいままです。**比較段は A:1193 で OID をソートするため、現行の findings・suppressions・scan_failures・rc への影響はありません。** F:28 の内部順序仕様との差として nit とします。

最小是正は、同じ file に対応する候補列内の順番を同値 key の tie-break に使うことです。OID 文字列順では逐次順を再現できません。

## test の恒真化

| テスト | 判定・根拠 |
|---|---|
| enumeration | **refuted**。T:1220 の期待 group・owners・aliases は手書き。inode 等だけを fixture から取得しており、列挙結果から期待集合を作っていない。 |
| multiple_threads | **refuted**。T:1318 で保存した本物を T:1329 で呼ぶ。queue／thread は置換せず、timeout 付き Barrier と thread ID 集合を検査する。 |
| report | **refuted**。T:1269 の stub は Git 入力・metadata・cat-file・landed 参照。列挙、実 file 比較、抑止集約を通し、T:1295 の非空の独立期待 report と比較する。 |
| first_seen | **refuted**。T:1431 で代表 path、metadata、identity 挿入順、OID 挿入順を直接 assert。単なる両経路の相互一致ではない。ただし同値 key の複数 OID は含まない。 |
| deep_and_wide | **refuted**。T:1457 で保存した本物を T:1464 で呼び、T:1479 の集合一致と件数一致で重複0・欠落0を検査する。 |
| 既存 heartbeat | **refuted**。T:1020、1041 の期待値は不変。flat tree は A:1170 の条件により queue を作らず、既存の pulse 回数を維持する。 |
| その他の新設テスト | **refuted**。symlink の独立期待値、例外オブジェクト同一性と thread 終了、caller thread の callback、正の timeout、設定値、空候補の trap、実 permission 失敗をそれぞれ検査している。 |

**real／nit：A5 の3 witness のうち、「同じ worker 内の複数 onerror」は保証されていません。**

T:1340 の deny directory は2個、workers は4です。directory 単位の queue へ変えたため、それぞれ別 thread に割り当てられ得ます。逐次側の複数 onerror は、並列側の worker 固有累積値の証拠にはなりません。

他の2 witness は成立しています。

- 入れ子 root：T:1361、1363 が同じ失敗の重複計数を期待する。
- root scandir 途中失敗：T:1382 が1 entry 後に例外を出し、T:1391 が `({}, 1, True)` を期待する。

現実装の累積加算は正しく、現在の成果物差はありません。ただし worker ごとに onerror を1回へ丸める回帰を、割当て次第で見逃します。最小是正は、同じ root 内の deny directory を worker 数より多くすることです。例えば5個なら、workers=4 で少なくとも1 thread が複数 onerror を経験します。

## 変異の帰属

以下は静的予想です。**KILLED／SURVIVED の実測判定ではありません。**

| ID | 判定・帰属と注意点 |
|---|---|
| M0 | **refuted**：A:1123 の docstring 言い換えは等価。SURVIVED 予想で整合する。 |
| M1 | **refuted**：A:1091 の合算除去は T:1363 の失敗6件を下回る。worker の失敗に到達し、root 検査で mask されない。 |
| M2 | **refuted**：A:1000 を `iteration[1][:-1]` にすると root の末尾 `z` が落ち、T:1230 の固有候補が欠落する。末尾 symlink／空 subtree による等価化はない。 |
| M3 | **refuted**：root の filenames を空にすると T:1221 の `direct.py` が欠落する。別 subtree の候補で代替されない。 |
| M4 | **real／再照準済み**：`followlinks=True` 単独は最初の yield まで同じで、独自の A:1001 が追跡を阻む。A:1001 の除去ならリンク先の `hidden` が入り、T:1512 が赤になる。 |
| M5 | **一部 refuted／一部 unknown**：A:967 と1105の両方を反転すれば、root の代表を `b/alias.py` に変更し、T:1431 が赤になる。一方、A:967 **だけ**の反転について、この test は worker 内で同じ group を複数 task から更新する状況を保証しない。 |
| M6 | **unknown／変異文面の具体化が必要**：「保存せず続行」の実装次第で `pending` が残り、例外 assertion より先に hang する。`errors.append(error)` だけを除去し、`stopped.set()`／`done.set()` を保持すれば、同型例外が再送出されないことへ帰属できる。 |
| M7 | **refuted**：worker の A:1045 後へ無条件に `heartbeat.pulse(...)` を追加すれば、間隔0の T:1557 が caller thread 不一致で赤になる。worker 例外は親へ伝播するため mask されない。 |
| M8 | **refuted**：16→0 は T:1574 の独立期待値で赤。env override／空候補による mask はない。 |
| M9 | **refuted**：早期 return 前の Queue／Thread 生成は T:1608、1609 の trap で赤。列挙関数を直接呼んでいる。 |

M5 の局所選択と merge 選択をそれぞれ検証するなら、局所側には「同じ worker が、同一 group の後順 task→前順 task を処理する」witness が必要です。現状の両箇所同時変異だけでは、局所側の検査能力まで証明できません。

## 裁定・fix 指示との差

**満たしている事項：**

- env は A:1126 で列挙時に読み、空候補はその前に return。
- workers=1 は A:1155 の root 全体 walk で、thread を作らない。
- 待機は A:1070 の正の `POLL_CEILING_SECONDS`。
- worker の最初に記録された例外を保持し、非 daemon thread 全件を join してから同じオブジェクトを再送出。
- 重複除去は dict／set。追加実装に `x not in list` はない。
- CLI・報告関数・比較段・境界 helper・alias 配布・rescue は差分対象外。
- 既存テストの変更は、指定された旧禁止テストの置換のみ。

**差が残る事項：**

1. **real／nit**：F:28 の OID 挿入順の完全再現は、同値 key の反例で満たさない。現行の監査成果物には影響しない。
2. **real／nit**：S4:14 の同一 worker 内複数 onerror witness は、T:1340 の2 directory では保証しない。現在の scan_failures は正しいが、回帰検知の保証が弱い。

実根での逐語一致と D958 の性能受理は本レビューの対象外です。S4:42、43 の条件を、本レビューの GO で代替することはできません。

## 所見一覧 (real / refuted / unknown、must-fix / nit)

| ID | 判定 | 根拠 | 放置時の成果物への影響・最小是正 |
|---|---|---|---|
| A1 | **real／nit** | A:967、1105、1176；F:28 | OID 挿入順が変わり得るが、A:1193 のソートにより監査成果物は不変。同値 file key に候補列順の tie-break を付ける。 |
| A2 | **real／nit** | T:1340、1358；S4:14 | 現成果物は不変。同一 worker の複数失敗を丸める回帰の検知が割当て依存になる。deny 数を workers より多くする。 |
| A3 | **unknown／nit** | A:967；T:1412、1431 | M5 の局所比較だけの変異が確実に赤になるとは示せない。現実装の成果物差はない。局所更新の witness を固定する。 |
| A4 | **unknown／nit** | A:1054；fix報告:60 | M6 の具体的差分次第で hang が赤理由を覆う。停止・完了通知を保持して例外保存だけを除く。 |
| A5 | **refuted／修正不要** | O:355、371、418；A:988、1001 | scandir／分類／symlink 意味論による候補・失敗数の差は見つからない。 |
| A6 | **refuted／修正不要** | A:1047、1083、1091、1178 | task 欠落、失敗の二重加算、入れ子 root の省略による成果物差は見つからない。 |
| A7 | **refuted／修正不要** | T:1220、1295、1329、1464；差分AST比較 | 独立期待値と本物の処理関数を使い、旧禁止テスト以外の既存期待値は不変。恒真化は認めない。 |

**成果物が変わると示せた must-fix は0件です。**

## GO / NO-GO

**GO — レンズ A の実装レビューとして、nit 付き。**

安定入力で監査の受理集合を増やす経路、scan_failures を変える集約不良、正常結果として途中成果を返す例外処理は見つかりませんでした。

内部 OID 順と A5 witness の不足は修正を勧めます。変異検査は M5・M6 の帰属を上記の範囲に限定してください。wave の最終受理は、親の逐語一致・変異実走・性能判定に残ります。

## 総括

directory 単位の queue は、`os.walk` の列挙規則、hardlink 代表、alias 集約、失敗計数を静的には維持しています。残る所見は、同値 key の OID 挿入順とテスト・変異の保証範囲です。監査成果物を変える must-fix は確認していません。
