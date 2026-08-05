静的読解のみで判定した。pytest・監査スクリプトの実走は行っておらず、緑は主張しない。レビュー中に更新された `s4-ruling.md` は70行の現行版を再読した。

### B-0 / nit

**主張:** positive control が恒真・自己オラクルである、という疑いは反証された。

- **判定:** refuted
- **根拠:** `orchestrator/tests/test_audit_dangling_commits.py:74-93` は実装から期待値を生成せず、fixture が返した commit ID、固定 subject、固定 path の完全一致を要求する。ブランチは `:65-67` で ref ごと削除され、実装は `tools/audit_dangling_commits.py:61-65` の `--no-reflogs` により残存 reflog を到達根から外す。
- **失敗シナリオ:** `lost_paths` の追加を無効化すれば `:87-89` が失敗するため、壊れた検出器が恒真で通る構造ではない。
- **成果物影響:** この点単独では掃除判断への悪影響はない。ただし検出できるのは「新規 path 追加」の狭い正例だけである。
- **最小対処:** 現行 positive control は残し、B-1 の内容差分正例を追加する。

### B-1 / blocker

**主張:** path が存在するだけで「作業は land 済み」と扱うため、既存ファイルへの未 land 変更を確実に見逃す。

- **判定:** real
- **根拠:** `tools/audit_dangling_commits.py:133-139` は blob・patch・内容を比較せず、同名 path が main または任意の branch tip にあれば無条件で除外する。段4の裁定自体も `s4-ruling.md:23-25` で path 存在だけを安全述語としている。さらに `orchestrator/tests/test_audit_dangling_commits.py:125-133` は live branch の内容 `"live\n"` と dangling commit の `"unreachable revision\n"` が異なるのに、報告ゼロを要求しており、実際の見逃しを negative control として固定している。
- **失敗シナリオ:** 既存の `tools/x.py` を修正した未 land commit のブランチを削除する。main に旧版 `tools/x.py` があるため `:136-137` で除外され、監査は0件になる。同様に、別の生存ブランチに同名だが異なる内容がある場合も `:138-139` で消える。
- **成果物影響:** cleanup 実行者が「取り残し0件」と誤認し、既存実装への修正・バグ修正・実験設定変更が約2週間後の gc で失われうる。
- **最小対処:** path 存在ではなく、少なくとも blob 同一性または patch 同値性が main／生存 branch に確認できた場合だけ抑止する。同名・異内容は positive control として必ず報告させる。

### B-2 / must-fix

**主張:** 全 unreachable commit の `--name-only` を個別判定するため、最終状態では破棄済みの中間ファイルや削除操作を「失われた作業」と誤検出する。

- **判定:** real
- **根拠:** `tools/audit_dangling_commits.py:75-88` は add/modify/delete/rename の status を捨て、`:131-142` は unreachable graph の全 commit を一件ずつ報告する。旧ブランチ tip や net tree 差分を復元していない。
- **失敗シナリオ:** 削除済みブランチ上で commit A が `scratch.txt` を追加し、commit B が意図的に削除した後にブランチを消す。A・Bとも unreachable で、path は main／全 tip にないため両方が検出対象になる。path が main 履歴に一度もないので、提案中の「履歴に現れたか」条件でも直らない。
- **成果物影響:** 実行者が救出不要な中間物を「失われた未 land 作業」と判断し、掃除を不必要に停止・救出する。I1の誤検出ゼロ性も満たせない。
- **最小対処:** delete/rename status を保持し、unreachable graph の最大 tip ごとの最終 tree／net delta を評価する負例を先に追加する。単なる履歴上の pathname 検索では代替しない。

### B-3 / must-fix

**主張:** M1〜M5 は「唯一の赤理由」に束縛されておらず、P-1向け第4条件を入れるとM1〜M3は安全 gate の変異ですらなくなる。

- **判定:** real
- **根拠:** `mutation-spec.json:13-14,29-30,45-46,61-62,77-78` とテスト本体を照合した結果は次のとおり。

| 変異 | 静的判定 |
|---|---|
| M1 | **不成立。** `rev-list --all` は unreachable commit を追加せず、逆に候補から落とす。`test_positive...:87`、reachable負例 `:106`、fold test の include 正例 `:149-155` が別理由で失敗する。 |
| M2 | 現行実装では main-path 負例だけが失敗する。ただし B-1 の誤った path-only 意味論を固定する。 |
| M3 | 現行実装では一つに絞れるが、同名・異内容を「安全」とする誤ったオラクルを固定する。 |
| M4 | 一つに絞れる。fold負例 `:148` が既定除外の喪失だけで失敗する。 |
| M5 | **不成立。** positive control に加え、fold test の include 正例 `:149-155` も失敗する。 |

さらに `s4-ruling.md:53-56` の `git rev-list --all ... <path>` は条件1〜3を意味論的に包含する。reachable commit の変更 path は必ず reachable history にあり、main／branch tip の path も同様である。したがって修正後はM1〜M3を単独で外しても第4条件が mask し、意図した負例は赤くならない。`:64-68` の「SURVIVEDなら両層同時変異」は、`:31-33` の単一理由要件を満たさない。また、段4で登録されたM6は現行 `mutation-spec.json:1-88` に存在しない。
- **失敗シナリオ:** 第4条件が粗い pathname 抑止として残り、M1〜M3がすべて survival／別理由 kill なのに、matrix上は3条件が独立に保証されたと記録される。
- **成果物影響:** 「3条件と履歴条件が独立に発火する」という誤った保証の下で、B-1の既存ファイル変更が失われうる。
- **最小対処:** M1〜M3を安全結果の単独変異から取り下げる。prefilter維持は call-count 等の性能テストへ分離し、内容同値性の実効 gate を二方向のcontrolsで変異する。M5はCLI側の `if not findings` を常真にするなど、positive CLI assertionだけが失敗する位置へ再照準する。M6はspecへ実体化する。

### B-4 / must-fix

**主張:** 4本の negative control は名目上の条件対応は揃うが、P-1修正と内容同一性を固定していない。

- **判定:** real
- **根拠:**

| control | 固定しているもの |
|---|---|
| `:96-107` | 条件1: main到達可能 commit を候補にしない |
| `:110-120` | 条件2: main現在treeに同じpathがある |
| `:123-133` | 条件3: 生存branch tipに同じpathがある。ただし内容が異なるためオラクルが不正 |
| `:136-155` | fold既定除外。後半は除外解除時のpositive assertion |

条件の名目上の空白はない。しかし `s4-ruling.md:62-63` の新規負例だけでは「その pathname が履歴に一度でもあれば抑止」という粗い実装も通る。しかも現行 `mutation-spec.json` にはM6がまだない。
- **失敗シナリオ:** main履歴で過去に `config.json` が存在した後、dangling commit が同じpathへ全く新しい内容を追加する。提案条件は「履歴にあった」として抑止し、未 land 内容を見逃す。
- **成果物影響:** 再利用された filename 上の実装・設定変更を「過去にland済み」と誤判定し、gcで失いうる。
- **最小対処:** P-1修正には対のcontrolsを置く。(1) 過去にlandした同一内容／同一patchは現在削除済みでも報告しない、(2) 同じpathが履歴にあっても内容／patchが異なるdangling作業は報告する。後者なしで履歴条件をlandしない。

### B-5 / must-fix

**主張:** 追加行は読まれ実行される導線にあるが、非zero rc時の安全行動が不足している。

- **判定:** real
- **根拠:** `.agents/skills/cleanup-branches/SKILL.md:14-15` は dispatcher全文を読みそのまま実行するため、`.claude/commands/cleanup-branches.md:17` の呼び出し自体は発火する。一方、toolは `tools/audit_dangling_commits.py:7,165-180` で rc=1/2 を区別するのに、入口は「§5で報告する」としか書かず、削除停止・救出・実行不能時のfail-closed処理を定めない。
- **失敗シナリオ:** `git fsck` 障害でrc=2になっても棚卸しを続行する。またはrc=1のOIDを報告するだけでrefへ固定せず、後続運用のgcまで放置する。
- **成果物影響:** 実行不能を0件相当として掃除を続ける、または検出済みcommitを保全しない判断になり、まさに対象の未 land 作業が失われうる。
- **最小対処:** 入口に「rc=0のみ続行、rc=1/2は掃除を止めて§5報告。rc=1は救出判断までOIDを保全しgcしない」を明記する。byte予算は安全文言以外から確保する。

### B-6 / nit

**主張:** 今回の3箇所の削除が§2〜§5の安全義務を摩耗させた、という疑いは反証された。

- **判定:** refuted
- **根拠:**
  - (a) 「事象と原因の」の削除後も `.claude/commands/cleanup-branches.md:36-37` に復元手順とF26正本が残り、行動は同じ。
  - (b) 親heticalの4手順は `:32-34` に直前列挙され、`:39-40` の「本節の手動手順」が一意に参照する。
  - (c) F26は節見出し `:28` と正本参照 `:37` に残る。
  - §2 `:21-26`、F26/F51 `:30-43`、§4 `:45-50`、§5 `:52-56` は安全行動を保持している。
- **失敗シナリオ:** 削除前後でdetach、`branch -d`、directory削除、prune、F51縮退、事後検査、push引き渡しの選択は変わらない。
- **成果物影響:** この3削除による誤った掃除判断は確認できない。
- **最小対処:** なし。B-5のrc規律を追加する際も、これらの安全記述はさらに削らない。

### B-7 / nit

**主張:** 「既存経路と重複し、純増検出力がゼロ」という疑いは反証された。

- **判定:** refuted
- **根拠:** 既存 `git cherry` は `.claude/commands/cleanup-branches.md:14-16` の現存branchだけが対象。§4 `:47-50` は構造・submodule・status検査だけである。`check_docs` の backlog guard は `tools/check_docs.py:1377-1383` の文書ID保存則で、Git objectを見ない。新監査だけが `tools/audit_dangling_commits.py:57-72` でref外commitを列挙する。
- **失敗シナリオ:** 新規pathを追加したcommitのbranchが既に削除済みなら、`git branch`にも`git cherry`対象にも出ず、§4もcleanに見えるが、新監査はobjectがgcされる前なら検出できる。
- **成果物影響:** この入力では新規実装ファイルが既存経路をすべて素通りして失われうるため、監査には純増検出力がある。
- **最小対処:** 監査自体は維持する。ただしB-1〜B-5を塞ぐまでlandしない。

## 総括

**NO-GO。blocker 1件、must-fix 4件。**

親既知のP-1そのものは件数に含めていない。最大の問題は、親brief・段4・実装・negative controlが一体で「同じpath名がある＝作業がland済み」という誤った安全述語を固定している点である。提案中の「reachable履歴に一度でも現れたpathを除外」はこの欠陥をさらに広げ、M1〜M3も実効変異ではなくする。