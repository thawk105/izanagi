## 所見対応表 (所見 ID、closed/partial/regressed、根拠)

**修正対象だった実装・docs の欠陥は解消。全受入・変異実走の成立は未証明です。** 指定資料のみを静的に確認しました。pytest・変更操作は行っていません。

以下、`Δ` は `s6-fix-v2.diff`、`報告` は `s6-fix-1.md`。`closed` は当該所見の解消を意味し、全受入完了を意味しません。元から refuted の項目は、その判定を覆す変更がないことを示します。

| 所見 ID | 判定 | 根拠 |
|---|---|---|
| A-1 死亡後テストの stderr | closed | Δ `test_dev_wave_wait.py` hunk `@@ -5152,7 +5152,12 @@`。空または当該 PID の既存診断1行のみ許容し、未知の診断を拒否。後続の commit・receipt 検証を維持。報告:18–26 に直接呼出し成功と `NG:` 添加時の赤化。pytest 成功とは扱わない。 |
| A-2 docs の運用境界 | closed | `docs/dev-wave/workers.md:25–26`。「投入先全残差」「呼出側指定」「記録のみ」を明示。直後に workspace-write 指定がある。 |
| A-3 `dir=None` の配置問題 | closed | `tools/dev_waves/git_state.py:253,311–317`。Git が返した git-dir に配置し、TMPDIR 依存を除去。通常の linked worktree で作業木内一時ファイルを作る原因は解消。配置の回帰検出力は下記 N-1。 |
| A-4 patch 比較範囲 | closed | Δ `test_dev_waves_git_state.py` hunk `@@ -1345,10 +1345,10 @@`。前処理を `add -A`、比較を固定 base から全差分に変更。fixture の編集・追加・削除すべてが比較対象となる。 |
| A-5 拒否・延期・失敗、rc 合成 | closed | 元は refuted。`git_state.py:249–274,320–322` の分類を維持。Δ に launcher の rc 合成変更なし。 |
| A-6 対象外経路・待ち手終端配線 | closed | 元は refuted。Δ に launcher／waiter 本体の変更なし。非 author/fix の skipped stdout という裁定済み例外も変更なし。 |
| A-7 provenance | closed | 元は refuted。`git_state.py:285–307` の優先順位・正規化・固定 trailer を維持。実データ:12 に適合する trailer。 |
| A-8 全走・変異実走の成立 | partial | 報告:18–29 は直接呼出し3件と限定的反実仮想のみ。pytest 全走・M0〜M14 の較正結果はない。旧走の赤が局所修正されても、M13 の有効な KILLED 判定までは証明しない。 |
| B-削除候補1 必須削除なし | closed | Δ は局所修正で、新しい保存 framework・gate は追加していない。不要になった `tempfile` import を削除。 |
| B-削除候補2 unknown 検証の重複 | partial | Δ に該当ケースの削除なし。ただし「receipt 指定なし」と「指定先不存在」は異なる入口であり、元の任意整理 nit のまま。 |
| B-不足：本体欠落なし | closed | `git_state.py:249–322` と Δ に、元の refuted 判定を覆す欠落なし。docs 不足は以下で個別判定。 |
| B-テスト：赤1件の是正 | closed | A-1 と同じ hunk。B の局所修正案どおりで、stderr 全体を無視していない。 |
| B-テスト：正例が実体を検証 | closed | Δ は実 Git／実 producer を代替せず、観測 assertion を修正。報告:20–24 の直接呼出しは pytest の代替証拠にはしない。 |
| B-テスト：失敗検証3層 | closed | Δ で helper・launcher・waiter の各契約検証を削除していない。helper には失敗後の message file 不在確認を追加。 |
| B-テスト：待ち手失敗テストの妥当性 | closed | Δ に削除・弱化なし。保存失敗時の receipt 公開抑止を検証するという元の評価を維持。 |
| B-テスト：check-only＋opt-in | partial | 直接固定するテストは今回も追加されていない。通常待機への配線も変更なし。実害未確認の nit。 |
| B-テスト：旧ログでは後続 assertion 未到達 | partial | 報告:18–24 の直接呼出し成功で局所的な証拠は増えたが、修正後の pytest 実走証拠はない。 |
| B-docs：保存範囲 | closed | `workers.md:25` の「投入先全残差」で所有 path 限定保存との混同を解消。 |
| B-docs：引数・指定責任 | closed | 同行の「待ち手は呼出側指定 `--commit-worktree <abs>`」。直前の author/fix と同じ投入対象を指す文脈として読める。 |
| B-docs：記録の位置付け | closed | 同行の「記録のみ (D2044 項 16)」。採用・land・撤去を成立させる意味を持たせていない。 |
| B-docs：固定 base の明確化 | partial | `workers.md:21` は引き続き「子作成 SHA」。「子作成時の固定 SHA」への任意明確化は未実施。nit のまま。 |
| B-docs：その他の義務保持 | closed | Δ docs hunks。別 worktree・所有 path・依存順・起動確認を保持。B/C の義務も保持。「INFO 除外」は削除されたが、`:24` は引き続き「NOTE≠0」が条件で、INFO まで対象に広げていない。 |

## 新規所見 (あれば。real/refuted/unverified、must-fix/nit、成果物影響)

**N-1 — real / nit：追加 assertion は配置先の回帰を検出しない。**

根拠は報告:27、および Δ の成功後 clean・message file 不在確認です。旧 `dir=None` でも正常終了時に削除されれば通ります。

**成果物影響：旧配置へ退行して作業木内に message file が残れば、後続の `add -A` が本文を成果物へ混入させ得ます。ただし現実装でその退行・混入は確認していません。**

DW-G05 に照らし、現状の追加 must-fix とはせず、検出限界の申告を受け入れます。配置保証をテスト済みと記録することは不可です。追加するなら、TMPDIR を作業木内にした subprocess で、**message file が存在している commit 実行中の配置**を観測する検査が適切です。終了後の untracked 不在だけでは同じ穴が残ります。`git_dir /` というソース表記の静的 assert は実装表現を固定するため、優先しません。

**N-2 — refuted / nit：通常の linked worktree で git-dir 配置が壊れるという疑い。**

`git_state.py:253,311` は `.git` をディレクトリと決め打ちせず、Git が返した絶対位置を使用します。通常の linked worktree では `.git/worktrees/<name>/izanagi-worker-commit.msg` となり、worktree ごとに分離されます。Git の通常の管理ファイル名との衝突は示されていません。

別形態については次の評価です。

| 形態 | 静的評価 |
|---|---|
| 分離 git-dir を持つ通常 checkout | git-dir と common-dir が等しければ `:255–256` で拒否され、message file を作らない。 |
| bare repository 自体 | 作業木 root の取得段階で進めず、message file 作成へ到達しない。bare repository に属する linked worktree とは区別する。 |
| 別配置の管理領域に属する linked worktree | 名前や親ディレクトリを固定せず、返された git-dir を使用する。分離位置そのものは障害原因にならない。 |
| 管理領域を別の追跡対象ディレクトリ内へ特殊配置 | `:253` は resolve のみで、任意の作業木外であることを一般には検証しない。今回の実データはこの配置を証明しておらず、無条件の「全 repo 外保証」までは主張できない。 |

**N-3 — real / nit：同名既存ファイルを上書きし、その後削除する。**

`git_state.py:312` の `write_text` は既存通常ファイルを切り詰めます。`:317` はそのファイルを削除します。

**成果物影響：同名ファイルを他用途で使用していた場合、その内容は失われます。今回、そのような既存用途・衝突は確認されていません。**

以前の中断による残置なら、次の dirty commit で新本文に上書きして削除する動作になります。ただし **clean 判定は `:273–274` で先に return するため、clean 時には既存残置を清掃しません**。同名パスがディレクトリ等なら失敗になり、固定名は同一 worktree の同時実行に対する排他も提供しません。これらを理由に、裁定対象外の排他・清掃機構を今回追加必須とはしません。

**N-4 — refuted / nit：実データの終端 commit が要求形式を満たさないという疑い。**

[s6-inspect-child-commit.txt](/home/SFC/tanab/.claude/jobs/13a9bd13/wave/s6-inspect-child-commit.txt:1) の記録は、提示された §2.1 契約に適合しています。

| 確認項目 | 証拠・判定 |
|---|---|
| 件名・本文 | :2–10。固定件名、指定の本文7項目、段落区切りに適合。 |
| trailer | :12。最終段落に AI-Agent が1本。値に `none` なし。`stage: fix` に対する `role=author` は固定 trailer の仕様どおり。 |
| stdout | :26。`worktree-commit: committed` と完全 SHA `5a99d99d0c253a5e5d0cde52ff7a1ead8e4b3a31`。 |
| 保存内容 | :17–20。fix の所有3ファイル、16追加・7削除で Δ と整合。 |
| clean | :21–22。親が記録した status 件数は0。 |
| message file 不在 | :23–24。親が記録した残置件数は0。 |

`receipt outcome: accepted` は receipt の値の記録で、保存 commit の採用宣言ではありません。実データから追加の real 欠陥は見つかりません。この1件は launcher 成功経路の証拠であり、失敗経路・全テストの証拠には拡張できません。

## 総括

**焦点再レビューとして、A-1・A-2・A-3 の修正と A-4 の補強を受理できます。新規 must-fix、確認された regressed はありません。**

DW-S05-A v2 は、節内の workspace-write 指定と合わせて、保存範囲・呼出側指定・記録のみの3点を短い文で満たします。さらなる説明追加は必須ではありません。

配置先 assertion の検出限界は nit として受け入れます。一方、**A-8 は partial のまま**です。直接呼出し3件と実 commit の成功を、pytest 全受入・M0〜M14 の成立に読み替えず、受入完了判定は保留してください。