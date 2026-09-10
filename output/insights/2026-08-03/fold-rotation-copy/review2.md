静的検証のみ実施した。指定資料はすべて読了できた。実行場所は `pegasus02` であり、pytest・land・dry-run は実行しておらず、緑は主張しない。結論は現プランのままでは NO-GO。

### 1. must-fix — `remaining:` は構造 field ではなく、本文中の見かけだけで充足できる

**根拠:** プランは item 全体に対する正規表現と、`base:` との順序自由を提案している（[plan2.md:61](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:61)、[plan2.md:66](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:66)、[plan2.md:76](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:76)）。現行 parser は任意の 2-space continuation を許し（[tools/spool_fold.py:338](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:338)）、`base:` も block 全体への raw regex である（[tools/spool_fold.py:342](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:342)）。

**失敗シナリオ:** 完了 item に「初期処置だけ終了。後続作業は明日」と書き、2-space indent の fenced code 内に `remaining: none` を例示する。提案 regex はその行を field と数えて除去し、既存禁制語にも一致しないため完了を受理する。

**成果物影響:** 残件のある T が active 集合から消え、worklog の次タスク、後続 wave、最終的には certified 選択を支える作業集合が欠落する。T-352 の目的そのものを破る。

**推奨:** Markdown fence/comment 外の metadata trailer として認識すること。少なくとも field の位置を item 末尾の機械 field 群へ束縛し、fenced/comment 内の decoy を拒否する負例を追加する。「order-independent」を無条件には固定しない。

### 2. must-fix — 現存 fragment は安全だが、producer の移行閉包が閉じていない

**根拠:** ローカル branch tip 上の未 fold fragment は rulings branch の 5 件だけで、実物は `更新` / `新規` のみだった（例: [seq 3:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/rulings-2026-08-02-e/docs/spool/worklog/2026-08-02-rulings-2026-08-02-e-3.md:35)、[seq 4:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/rulings-2026-08-02-e/docs/spool/worklog/2026-08-02-rulings-2026-08-02-e-4.md:36))。過去の canonical 完了 block も、fold は最新 `次の一手` だけを active として解析するため再拒否されない（[tools/spool_fold.py:819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:819)）。一方 `/rulings` command、Rulings Skill、dev-wave 段7はいずれも author にトップレベル `docs/spool/README.md` だけを指す（[rulings.md:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/.claude/commands/rulings.md:8)、[Rulings SKILL.md:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/.agents/skills/rulings/SKILL.md:25)、[core.md:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/docs/dev-wave/core.md:84)）。exact action grammar は ledger 別 README 側にある（[worklog README:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/docs/spool/worklog/README.md:29)）。

**失敗シナリオ:** 将来の `/rulings` がタスクを `完了` にする際、明示されたトップレベル正本だけを読み、旧形式の `base:` 付き完了 fragment を生成する。新 validator はそれを拒否し、spool 全体の fold が止まる。

**成果物影響:** 当該 fragment だけでなく同時 pending の worklog、phase3 発火記録、receipt、rotation がすべて生成されない。

**推奨:** 現 scope 内では `docs/spool/README.md` に「各 ledger の README を必ず読む」dispatch と `完了` field の必須性を明記する。command／Skill／`docs/dev-wave/core.md` まで hard-link を追加するなら、scope 外の裁定パッケージとして返す。

### 3. must-fix — 複数行 item の「block 末尾」追記は Markdown を壊し得る

**根拠:** プランは複数行 item の最後の continuation 行へ suffix を連結するとしている（[plan2.md:148](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:148)）。実台帳にも複数行 item がある（[docs/phase3.md:599](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/docs/phase3.md:599)）。対する failures 再発は既存物理行へ連結せず、entry 境界に新しい block を挿入する（[tools/spool_fold.py:1264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1264)）。

**失敗シナリオ:** 対象 item の最後の continuation が fenced code の閉じ `` ``` `` 行なら、そこへ suffix を連結して閉じ fence を破壊する。現存 T-190 でも、ID のある先頭行ではなく説明の最終行へ発火記録が付く。

**成果物影響:** `docs/phase3.md` の後続節がコードブロック扱いになるなど、見送り台帳と参照表示が壊れる。regex ベースの checker は物理見出しをなお拾い、破損を見逃し得る。

**推奨:** block 最終行への連結は採らない。既存慣行を優先するなら「item 先頭行の行末」、構造安全性を優先するなら専用 2-space continuation 行、と stage 4 で決める。1行・複数行・fenced 終端の3例を固定する。

### 4. must-fix — spool と `check_docs.py` で「top-level item」の意味が一致していない

**根拠:** spool の既存 `_split_top_items` は raw 行頭 regex である（[tools/spool_fold.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:300)）。独立 checker は fence／HTML comment を不可視化してから top-level item を抽出する（[tools/check_docs.py:1001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/check_docs.py:1001)）。プランは `TASK_HEAD_RE` を使うとのみ書き、可視性規則を定義していない（[plan2.md:150](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:150)）。

**失敗シナリオ:** 見送り H3 内の HTML comment に `- [T-058] example` があり、実 item にも T-058 がある。`check_docs.py` は comment を無視して正当とする一方、新 helper が raw splitter を使うと duplicate として fold を拒否するか、comment 内へ追記する。

**成果物影響:** 既存 checker が受理する canonical に対し fold の受理集合だけが縮み、全台帳 fold が停止する。または発火記録の参照先が不可視領域になる。

**推奨:** spool 側で fence/comment-aware な canonical item tokenizer を明示する。`check_docs.py` 本体の変更が必要とは限らないが、両 parser の fenced/comment decoy 整合テストは必要。

### 5. must-fix — 「既存 bytes を削除・並べ替えない」という中心不変条件に byte oracle がない

**根拠:** プランは exact insertion だけだと主張する（[plan2.md:213](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:213)）が、18テストには phase 全 bytes の保存 oracle が明記されていない（[plan2.md:327](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:327)）。既存 N11 は新規見送り payload を1回除去して before bytes と比較するが、見送り追記は対象外である（[test_spool_fold.py:584](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:584)）。

**失敗シナリオ:** helper が対象 item を再構成して空行・末尾空白・改行を正規化する。suffix の位置と active 集合だけを調べる新テストは通る。

**成果物影響:** `docs/phase3.md` の許可外 bytes が変わり、台帳の hash、レビュー対象、参照される原文が変化する。

**推奨:** 1対象、同一対象への複数追記、複数対象、複数行対象について、`after == before[:offset] + exact_payload + before[offset:]` の byte-exact oracle を置く。

### 6. must-fix候補 — 「fold 開始時点から存在」の限定は追加の受理集合縮小である

**根拠:** 裁定本文は「既存項目へ追記」とだけ定める（[brief2.md:44](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/brief2.md:44)）。現行 worklog fold は fragment 順に active 遷移と新規見送りを反映する（[tools/spool_fold.py:1489](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1489)）。プランは全追記を原 phase へ先に適用し、同 fold 内で先行作成された項目を拒否する（[plan2.md:163](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:163)、[plan2.md:344](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:344)）。

**失敗シナリオ:** key の早い fragment A が T-001 を見送り台帳へ移し、遅い fragment B が同 T-001 の発火記録を追記する。B の処理時には項目が存在するのに、提案は `deferred-append-missing` で全 fold を拒否する。

**成果物影響:** worklog、phase3、receipt、rotation が全て未生成になり、正当に順序づけられた入力の受理集合が狭まる。

**推奨:** `Fragment.key` に従う逐次意味論を既定候補にする。pre-fold-only を選ぶなら「既存」の解釈として stage 4 で明示裁定し、先にテストへ固定しない。

### 7. must-fix — receipt は内容変更 replay と意味のない追記を止めない

**根拠:** プランは wrapper bytes が変わった同一 payload の再投入を新記録として受理すると明記する（[plan2.md:207](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:207)）。現行 replay gate は fragment 全体の content SHA と、allocation を持つ symbol identity しか照合しない（[tools/spool_fold.py:1435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1435)、[tools/spool_fold.py:1522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1522)）。

**失敗シナリオ:** 初回 fold 後、同じ wave/seq/path と同じ T-058 suffix を持つ fragment を、title または本文だけ変えて再投入する。append は新 symbol を持たないため identity gate もなく、同じ発火記録が二重挿入される。別経路として、suffix が空白だけでも「非空文字」と解釈すれば、receipt/GC だけ進んで実記録が残らない。

**成果物影響:** T-058/T-059 の発火回数・履歴が過大または欠落し、見送り台帳の値が誤る。

**推奨:** T-358 内で安定した append operation identity、または対象 item 内の exact suffix 重複拒否を設ける。一般 receipt schema の改訂へ広げるなら scope 外裁定にする。changed-wrapper replay、空白 suffix を追加テストする。自己適用例の `2026-08-03` も、D125/D127/D128 の実日付が全て 2026-08-02 であるため訂正する（[docs/decisions.md:6081](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/docs/decisions.md:6081)）。

### 8. must-fix — fragment 順序の分析は正しいが、`wave-fold-rotation-copy` は安全策として未証明

**根拠:** sort key は `(wave, seq, ledger rank, path)` である（[tools/spool_fold.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:89)）。rulings seq 3 が T-352 を更新し、seq 4 が T-358 を作るため（[seq 3:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/rulings-2026-08-02-e/docs/spool/worklog/2026-08-02-rulings-2026-08-02-e-3.md:55)、[seq 4:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/rulings-2026-08-02-e/docs/spool/worklog/2026-08-02-rulings-2026-08-02-e-4.md:64)）、本 wave の完了 fragment は後順が必須である。`wave` は branch 名由来とする文書契約がある（[docs/spool/README.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/docs/spool/README.md:24)）一方、validator は slug 構文と filename 一致しか見ない（[tools/spool_fold.py:603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:603)）。

**失敗シナリオ:** 慣例どおり `worktree-` だけ落とした `dev-wave-fold-rotation-copy` は rulings より前となり、T-358 は未作成、T-352 は後続更新が non-active となる。`wave-fold-rotation-copy` は機械検査を通るが、現 branch `worktree-dev-wave-fold-rotation-copy` との導出関係・既存慣例が説明されていない。

**成果物影響:** fold 全体が失敗して成果物ゼロになるか、receipt の wave provenance が branch identity と曖昧になる。

**推奨:** 安全順は次のいずれか。

1. 同 fold が必須なら、全 ledger fragment に実 branch 名そのものの `worktree-dev-wave-fold-rotation-copy` を使う案を stage 4 で明示裁定する。構文・filename 検査を通り、rulings より後になる。
2. provenance 慣例を変えないなら、本 wave では T-352/T-358 を完了にせず先に実装だけ landし、rulings 5 件の fold 後に別 fragment で完了させる。
3. いずれも dry-run の `plan.fragments` 順を exact assertion する。

`wave-fold-rotation-copy` の黙示採用と、seq での回避は不可。

### 9. must-fix — 変異 matrix に偽 kill、到達不能 operator、診断文字列 kill が混在する

**根拠:** プランの「保存則分離」は append を `_Operation` へ混ぜる変異を挙げる（[plan2.md:391](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:391)）が、T-050 は active でないため、保存則より前の `transition-target` が拒否する（[tools/spool_fold.py:1137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1137)）。resume は stored plan の `after_bytes` を使い（[tools/spool_fold.py:1711](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1711)）、after target は skip する（[tools/spool_fold.py:1730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1730)）。また `_raises` は exact error code を受理 oracle にしている（[test_spool_fold.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:160)）。

**失敗シナリオ:**

- append-as-operation mutant は `transition-target` で赤になり、保存則へ到達しない偽 kill。
- after target に同じ stored `after_bytes` を再書込みする mutant は suffix を増やさず、`single_insert` test が緑のまま。
- `deferred-append-missing` を別 error ID に改名するだけで受理集合不変なのに負例テストは赤。
- append collection は既に sort 済み fragment を受けるため（[tools/spool_fold.py:687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:687)、[tools/spool_fold.py:719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:719)）、「filesystem 列挙順へ変更」は局所 mutant として成立しない。set iteration は `PYTHONHASHSEED` により kill/survive が揺れる。

**成果物影響:** mutation レポートが、未検証の保存則・resume・順序 gate を KILLED と誤認し、受入証拠の値が不正になる。

**推奨:** 第一失敗 code を事前登録する。分離は parse 結果の `operations` / `deferred_appends` を直接検査し、resume は `resumed_paths` と phase への write 非発生を検査する。診断 ID 契約は受理集合 mutation と別枠にする。順序は exact `(wave, seq, item index)` oracle、固定 `fold_date`、実 FS 順や hash seed に依存しない fixture にする。

### 10. must-fix候補 — P6 の単一実装子は実装と oracle の誤りを相関させる

**根拠:** brief は同じ Python file を触ることだけを理由に実装子1本としている（[brief2.md:80](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/brief2.md:80)）。実際の所有面は実装ファイルとテストファイルに分離できる（[plan2.md:267](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:267)、[plan2.md:295](/home/SFC/tanab/.claude/jobs/3a897f63/tmp/wave-fold-rotation-copy/plan2.md:295)）。

**失敗シナリオ:** 同一 worker が raw regex の `remaining` helper と、同じ helper が生成する正常入力だけのテストを書く。所見1の fenced decoy は双方から同時に漏れ、18本が緑でも欠陥が残る。

**成果物影響:** T-352 の誤受理がテスト・変異レポート双方で認証され、active 台帳から残件が消える。

**推奨:** `tools/spool_fold.py` と `orchestrator/tests/test_spool_fold.py` を別 worker 所有にするか、少なくとも adversarial fixture 契約を実装前に別担当が凍結する。同じファイルへの並行編集は不要なので、P6 の衝突理由は成立しない。

## 総括

must-fix 候補:

- 構造 field を fence/comment 外の metadata として定義する。
- producer が ledger 別 README を必ず読む導線を閉じる。
- block 最終行追記を廃し、複数行 item の挿入位置を再裁定する。
- spool／`check_docs.py` の top-level item 意味を一致させる。
- phase3 の exact byte-splice oracle を追加する。
- pre-fold-only の受理集合縮小を stage 4 で明示裁定する。
- changed-wrapper replay、空白 payload、自己適用日付を閉じる。
- rulings より後になる provenance-valid wave slug、または別 fold を確定する。
- mutation matrix の偽 kill・診断 kill・resume 恒真性・順序フレークを是正する。
- 単一実装子 P6 を、少なくとも実装／oracle 所有分離へ改める。

scope 外の裁定パッケージ候補:

- `/rulings` command、Rulings Skill、`docs/dev-wave/core.md` 自体へ ledger README hard-link を追加する案。
- 一般 receipt schema／identity の改訂。T-358 固有の重複防止で閉じられない場合だけ送る。
- `tools/check_docs.py` の共有 tokenizer 化。spool 側の同型実装と整合テストで閉じられない場合だけ送る。

`tools/check_docs.py` の validator 伝播は既存 dynamic import 経路に載り、`hooks/` には spool grammar consumer を静的には確認できなかったため、現時点で両者を無条件に実装 scope へ広げる根拠はない。T-347 と凍結ソース閉包を要する提案は含めていない。

nit:

- なし。上記はいずれも受理集合、worklog、phase3 台帳、receipt、または mutation レポートの値に具体的な影響がある。