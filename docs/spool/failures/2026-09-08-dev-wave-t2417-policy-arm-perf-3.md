---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-08
wave: dev-wave-t2417-policy-arm-perf
seq: 3
---

## 新規

### {{F:preregistered-byte-identity-unsatisfiable}}. 事前登録が bytes の同一性を要求し、正常な成果物が 1 件も受理されなかった [テスト代表性] [恒真ゲート]

- 事象: 18 block の測定が完走した直後、事前登録した解析を当てた 1 回目が
  `artifact-invalid: source bytes differ between policy arms` で拒否した。原因は事前登録の
  identity 要求 2 件が**原理的に成立しえない**こと。(a) 処置が compile-time の source 置換なので
  腕をまたぐ source bytes の一致は起こりえない。(b) build が job 固有の一時領域で行われ
  path が成果物へ入るため byte 再現的でなく、block をまたぐ binary の一致も起こりえない。
  実測では source と genome が完全に一定の腕でも binary は 18 block すべてで異なった。
- 根本原因: 事前登録の起草時に「同じ program が走ったこと」を **bytes の同一性**で表現し、
  それが現行の build 経路で満たせるかを**測らずに凍結した**。文書内でも矛盾していた —
  同じ事前登録の別節が「seed は genome と binary を変える」と書いていた。
- 恒久対応: {{D:identity-binding-is-meaning-not-bytes}}。identity は source bytes と genome に
  束縛し、binary の bytes を要求しない。弱めた分は「腕が互いに異なる (define が inert でない)」
  という正の対照で埋める。訂正は追補の別文書で行い、旧版は凍結したまま残す
  (成果物が旧版の digest を束縛として記録しているため)。
- 再発検知: 実 producer の出力をそのまま consumer へ通すテスト。手作り fixture では、
  producer が出さない field を fixture が補ってしまい非互換が隠れる。本 wave では**同じ型の
  隠蔽が 2 度起きた** — 1 度目は build 証拠の欠落、2 度目は腕ごとの source hash。
- 備考: 拒否は構造検査であり、**この時点で outcome の値は 1 つも観測していない。**
  訂正が結果を見た後の後付けでないことを保証するのは Git 履歴と追補の記述だけである。
  repo 内の検査は、gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な防壁ではない。

### {{F:qsub-reply-is-a-sentence-not-a-job-id}}. scheduler の返答を job ID として読めず、投入済み job が孤児になった [手順漏れ] [計測汚染]

- 事象: 18 block の投入 script が rep 0 で `qsub returned an invalid job id` を出して中止した。
  **その時点で job は実際に投入されており**、script は ID を台帳へ積む前に中止するので、
  投入済み job が台帳にも `qdel` 候補にも載らない孤児になった。親が `qstat` で見つけて `qdel` した。
  同時に、`-o` / `-e` を渡していなかったため job の出力が投入元の作業ツリーへ落ち、
  script 自身の clean 検査で 2 回目の投入が失敗する状態も作った。
- 根本原因: scheduler の `qsub` が job ID だけを返すと仮定した。実際は
  `Request <ID> submitted to queue: <queue>.` という文を返す。同じ repo の既存 submitter は
  正しい正規表現を持っていたが、新しい script はそれを写さなかった。
- 恒久対応: 既存 submitter と同じ正規表現で request ID を抽出し、抽出できないときは
  **raw 出力を台帳と stderr へ残してから**中止する。「投入したが ID を読めなかった」を
  「投入していない」と扱わない。`-o` / `-e` を repo 外の絶対 path へ向ける。
- 再発検知: 偽 `qsub` を PATH の先頭に置く正例と負例。**この 2 件はテストでも変異走行でも
  捕まらなかった** — どちらも scheduler の実挙動に依存し、偽 scheduler を使う負例が
  無かったためである。実投入して初めて出た。

### {{F:codex-sandbox-cannot-run-git-merge}}. sandbox 子が共有 Git 管理領域へ書けず merge を実行できない [手順漏れ]

- 事象: 実装面の merge 競合を解決させるため codex 子へ `git merge --no-ff --no-commit` を
  指示したところ、`cannot lock ref 'ORIG_HEAD': ... Read-only file system` で merge が
  開始すらできなかった。子は 1 file も変更できずに戻り、1 本を無駄にした。
- 根本原因: 「merge / add / commit は親、競合解決は子」という契約を、子が `git merge` を
  実行できる前提で読んだ。子の sandbox は worktree の作業領域へは書けるが、
  共有 `.git/worktrees/<name>/` へは書けない。
- 恒久対応: **親が merge を開始して競合マーカーを出し、競合中の file を子の worktree の
  同じ相対 path へ配置して、子には「マーカーを消して正しい 1 つの内容にする」だけを指示する。**
  解決後に親が file を回収し、自分の merge へ適用して commit する。契約の分担は保たれる。
- 再発検知: 子の prompt へ「`git` を一切使わない」と明記し、配置済み file の一覧を渡す。
- 備考: 子の worktree は merge 前の周辺 file を持つため、子が走らせるテストは意味を持たない。
  **最終判定は親が統合後の木で行う。** 本 wave では子が「周辺 file が古いことによる非帰属」と
  判定した赤 1 件を、親が統合後の木で実走して全緑になることを確認した。
