静的読解のみを行い、pytest と監査スクリプト本体は実走していない。したがってテストの緑や現行 repo での 0 件は確認していない。

### A-1 / nit

**主張:** 形式上、裁定された3条件の連言は実装されており、いずれかが恒真化・握り潰しされている事実はない。

- **判定:** real（欠陥主張は refuted）
- **根拠:** 到達不能集合だけを列挙する `tools/audit_dangling_commits.py:57-72,131`、main tree の path 除外 `:123,136-137`、全 local branch tip の和集合による除外 `:125-129,138-139`を通過した path だけが `:140-142` で報告される。
- **失敗シナリオ:** 他 branch がゼロなら第3条件は空集合上で真になるが、「他の branch tip が存在しない」という量化の正しい結果であり、条件の無効化ではない。
- **成果物影響:** この制御構造自体から余分な掃除判断は生じない。
- **最小対処:** なし。ただし以下のとおり、各条件の意味論そのものが不適切。

### A-2 / blocker

**主張:** path 名だけの判定は、既存ファイルの修正・削除、同名別内容、submodule gitlink 更新をすべて見逃し、監査の中心目的を満たさない。

- **判定:** real
- **根拠:** `changed_files()` は内容や blob ID を捨てて path だけを返す `tools/audit_dangling_commits.py:75-88`。main・branch 側も `ls-tree --name-only` の集合だけである `:91-94`。同名 path があれば内容を比較せず除外する `:136-139`。さらにテスト自身が、live branch の `"live\n"` と失われた `"unreachable revision\n"` が異なっていても非報告を正解として固定している `orchestrator/tests/test_audit_dangling_commits.py:123-133`。
- **失敗シナリオ:** 消えた branch が既存の `tools/foo.py` を重要修正していた場合、main に古い `tools/foo.py` があるだけで除外される。既存ファイルの未 land 削除も main に path が残るため除外される。`external/ccbench` は常設 path なので、別 gitlink commit への未 land 更新も同様に落ちる（`.gitmodules:1-4`）。
- **成果物影響:** cleanup が「取り残し 0 件」と誤判断し、既存実装の修正や submodule pin 更新が gc で失われうる。
- **最小対処:** path 存在ではなく、親ごとの変更 delta（blob/mode/gitlink、削除を含む）の同値性を main および生存 branch の到達可能履歴と比較する。少なくとも「既存ファイルの別内容」「削除」「同名別内容」「gitlink 更新」の positive control を追加する。

### A-3 / must-fix

**主張:** P-1 の「main の履歴に一度でも同 path があれば除外」は採用不可であり、現在より見逃しを広げる。

- **判定:** real
- **根拠:** 現行 predicate は現在 tree の集合 `tools/audit_dangling_commits.py:123,136-137`。これを main 全履歴の path 集合へ広げると除外集合は単調に増える。brief の I2 は一般の「未 land commit」を要求する一方 `s1-brief.md:50-51`、既存 positive control は新規 path 1件しか扱わない `orchestrator/tests/test_audit_dangling_commits.py:74-93`。
- **失敗シナリオ:** `old.json` が過去に main に存在して削除された後、消えた branch が同名 path に全く新しい仕事を追加する。P-1 案では「過去に現れた」だけで land 済み扱いになる。rotation 後の名前再利用や、一度削除された生成定義の復活も同じ。
- **成果物影響:** 再利用された path の新しい未 land 作業を cleanup が安全と誤認し、回収機会を失う。
- **最小対処:** P-1 の path-history 案を棄却する。観測された3件は「同 path があった」ではなく、到達可能履歴に同等の変更 delta があるかで消し込む。非 merge commit は stable patch-id 等、merge・binary・gitlink は明示的な tree delta 比較とし、判定不能は報告側へ倒す。

コスト面でも、候補 path ごとの `git log --all -- <path>` は候補数に比例して subprocess を増やすため不適切である。履歴情報が必要なら一括走査・キャッシュにするべきだが、一括 path 集合にしても意味論上の欠陥は直らない。

### A-4 / must-fix

**主張:** `docs/spool/` と `docs/archive/` の無条件除外は、fold 済み誤検出だけでなく、fold 前に本当に失われた記録も黙って捨てる。

- **判定:** real
- **根拠:** prefix は無条件に定義され `tools/audit_dangling_commits.py:19`、内容や fold 到達性を確認せず `:134-135` で除外される。CLI の既定も除外有効 `:158-164`。テストもこの挙動を固定している `orchestrator/tests/test_audit_dangling_commits.py:136-154`。
- **失敗シナリオ:** wave が新しい worklog/failures fragment を `docs/spool/` に作ったが fold 前に branch が消える。または rotation 用の新しい archive を作った branch が land 前に消える。いずれも常に非報告となる。
- **成果物影響:** 作業経緯・失敗記録・rotation 内容が回収されず、cleanup 後に復元不能になりうる。
- **最小対処:** prefix 除外をやめ、同一内容が fold 先の到達可能履歴にあることを証明できたものだけ抑制する。暫定的には別カテゴリの warning として報告し、人間が fold 済みを確認する。

### A-5 / must-fix

**主張:** 「到達不能 commit」を「消えた branch の失われた作業」と同一視しており、P-1 以外にも routine rebase・amend・一時 merge commit・意図的破棄を誤報する。

- **判定:** real
- **根拠:** `git fsck --unreachable --no-reflogs` の全 commit を起源・年齢・処分理由なしに候補化する `tools/audit_dangling_commits.py:57-72`。全候補を個別報告し、到達不能 graph の先端への集約もない `:131-143`。裁定の式も origin/disposition を持たない `s4-ruling.md:23-25`。
- **失敗シナリオ:** branch の rebase/amend 前 commit、レビュー用 candidate-merge、試行錯誤で意図的に破棄した commit が一意な path を持つと報告される。一般 path が cherry-pick 後に main から削除された場合も、P-1 と同じ誤報になる。複数 commit が同じファイルを順次編集した branch では各祖先が重複報告される。tracked `output/` は正本と再生成物が混在するため、意図的に捨てた生成物は誤報し、同名別内容の重要な WAL/report は A-2 により見逃す（`output/README.md:50-65`）。
- **成果物影響:** cleanup が不要な rescue を要求したり停止し、逆に同名の重要な output 作業を安全と誤認する。
- **最小対処:** 表示を断定的な「失われた作業」から「要確認の到達不能変更」へ変える。reachable 履歴との delta 同値性、到達不能 graph の frontier 集約、可能なら branch 削除時の tip/disposition 台帳を使う。I1 の「現行 repo で絶対0件」は、意図を持たない object 推論では保証不能なので、誤報ゼロではなく分類精度の invariant に改める。

### A-6 / should

**主張:** branch tip の snapshot と到達不能性の計算が非原子的で、並行 wave の増減時に一時的な見逃しが起きる。

- **判定:** real
- **根拠:** main tree、branch tip/tree を先に収集し `tools/audit_dangling_commits.py:119-129`、その後に別 subprocess の fsck を行う `:131`。前後で refs が変化したか検査しない。
- **失敗シナリオ:** tip の path を `other_tip_paths` に追加した直後、別 wave がその branch を削除する。続く fsck は commit を unreachable と返すが、その path は削除前 snapshot に残っているため `:138-139` で抑制される。
- **成果物影響:** 並行 cleanup が消した branch の作業を、その回の監査が 0 件と誤判断する。
- **最小対処:** 監査前後の refs/OID snapshot を比較し、変化していれば全体を再試行する。回数上限後は rc=2 とする。

### A-7 / nit

**主張:** I5 に反する repo 状態変更コマンドは実装本体には見つからない。

- **判定:** refuted（I5 違反の疑いを refute）
- **根拠:** subprocess の実行箇所は一元化され `tools/audit_dangling_commits.py:25-44`、呼び出す Git command は `fsck`, `diff-tree`, `ls-tree`, `for-each-ref`, `rev-parse`, `show` のみ `:57-109,119-129`。`fsck` に書き込みを行う `--lost-found` はない。`GIT_OPTIONAL_LOCKS=0` も指定される `:36`。
- **失敗シナリオ:** branch作成・削除、gc/prune、reflog/index/worktree/config 更新へ到達する呼び出し経路はない。テスト fixture の branch 操作は tmp repo の準備であり実装本体ではない。
- **成果物影響:** 監査自身が掃除対象や作業 tree を変更する副作用は認められない。
- **最小対処:** 現状維持。許可 Git command の固定テストを追加すると回帰防止になる。

### A-8 / must-fix

**主張:** 実行コストは現行 repo では小さそうだが未計測であり、Pegasus login node から直接実行させる入口はプロジェクトの admission 契約に反する。

- **判定:** real
- **根拠:** branch tip ごとに全 tree を取得する `tools/audit_dangling_commits.py:125-129`、全 object を fsck する `:57-66`、到達不能 commit ごとに subprocess を起動する `:131-142`。未計測・入力無上限は `unknown` とし dispatch-required 扱いする契約が `tools/README.md:8-19`、`docs/pegasus-runbook.md:351-364` にある。一方、入口は場所判定なしに直接実行を指示する `.claude/commands/cleanup-branches.md:17`。
- **失敗シナリオ:** wave/rebase が増えて unreachable commit と branch 固有 path が増えると、時間は概ね `O(B × tree列挙 + U × diff-tree)`、メモリは全 tip の一意 path 和集合まで増える。数十 branch の各 tip が固有 `output/` tree を持つ場合に膨らむ。
- **成果物影響:** login node の資源規律違反で監査自体が実行できない、または他作業を圧迫し、安全確認が省略される。
- **最小対処:** 計算ノードの専用 cgroup で分類を実測し、入口に sanctioned な実行場所を明記する。候補 path ごとの追加 Git 呼び出しは避け、履歴/delta 情報を一括取得する。

静的棚卸しでは現在 11 branch tip、main 8,954 path、18,508 objects、pack 64.21 MiB＋loose 8.94 MiBだったため、12 GiBを超える可能性は低そうだが、これは charged-memory peak の実測ではない。規約上 `local-ok` の根拠にはできない。

### A-9 / must-fix

**主張:** スクリプト単体は通常の Git エラーを rc=2 に分離するが、cleanup 入口が rc=2 を削除停止条件にしておらず、運用上 fail-open である。

- **判定:** real
- **根拠:** Git 非ゼロは `RuntimeError` になる `tools/audit_dangling_commits.py:47-54`。Git 不在の `OSError`、非 repo・main 不在・fsck 失敗の `RuntimeError` は rc=2 になる `:165-169`。しかし入口は単に「§5で報告」とするだけ `.claude/commands/cleanup-branches.md:17` で、安全条件 `:19-25` に auditor rc=0 が含まれない。
- **失敗シナリオ:** Git 不在、壊れた object、main ref 不在などで rc=2になっても、agent がエラーを§5へ記載しただけで既存の ahead 条件に従い branch/worktree 削除を続けられる。
- **成果物影響:** 到達不能監査が一度も成立していない状態で cleanup が進み、取り残しの回収判断を欠く。
- **最小対処:** 入口に「rc=0 のときだけ削除工程へ進む。rc=1 は報告・救出判断、rc=2 は全削除停止」と明記する。

### A-10 / should

**主張:** 非UTF-8 path/subject では未捕捉のデコード例外がプロセス rc=1となり、「報告あり」の rc=1と衝突する。

- **判定:** real
- **根拠:** Git 出力を `text=True`・strict decode で受ける `tools/audit_dangling_commits.py:37-43` が、encoding/error handler を指定していない。`main()` が捕捉するのは `OSError, RuntimeError` だけ `:165-169`。Git の path は任意 byte を許すため `UnicodeDecodeError` が外へ漏れうる。
- **失敗シナリオ:** 到達不能 commit に UTF-8として不正な filename byte があると `diff-tree -z` の decode が失敗し、Python traceback と process rc=1になる。契約上は「取り残しあり」と同じ rcになる。
- **成果物影響:** cleanup が実行不能を検出結果と誤分類し、正しい救出対象を提示できない。
- **最小対処:** path 出力は bytes で扱うか `errors="surrogateescape"` を使い、`UnicodeError` は少なくとも rc=2へ変換する。rc=2 control も追加する。

### A-11 / should

**主張:** manual cleanup command だけでは、branch 消失から gc までに監査が必ず一度走る保証がない。

- **判定:** real
- **根拠:** 静的検索上の運用 caller は `.claude/commands/cleanup-branches.md:17` のみ。`fsck` は既に prune された object を復元・検出できない `tools/audit_dangling_commits.py:57-72`。
- **失敗シナリオ:** branch が別経路で誤削除され、その後 cleanup command を実行しないまま gc/prune が走る。次回監査時には commit object 自体が存在しない。
- **成果物影響:** 事故検出器が一度も観測しないまま未 land 作業が永久消失する。
- **最小対処:** branch削除・worktree prune・手動gcの前に必ず監査する規律を配線し、定期実行または削除 tip のdurable ledgerを設ける。

## 総括

**NO-GO。blocker 1件、must-fix 5件。**

3条件はコード上では成立し、I5と通常のrc=2変換も概ね実装されている。しかし判定単位が path 名であるため、一般的な「既存ファイルを修正した未 land 作業」を検出できない。P-1 の main 全履歴 path 案はこの欠陥を直さず、再利用 path の見逃しを増やすため採用不可である。内容/delta 同値性への再定式化、fold 除外の証明ベース化、入口の fail-closed 化、Pegasus 実行分類が済むまで land すべきではない。