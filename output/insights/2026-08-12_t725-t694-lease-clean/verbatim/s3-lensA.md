# 所見

## 1. [must-fix] F191 点 1 は「より厳しい形」ではなく、未充足

- **[real の根拠]** F191 は「親 template へ、取得後の main SHA だけを待ち手が差し込む」と明記する。[現実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_wait.py:862) は取得後 SHA を読み捨て、message file を無変更で複製するだけである。最大 7,200 秒待った後の SHA を親が事前作成した message に正しく書く方法はない。また `_message_has_ai_agent` は `AI-Agent:` で始まる行の存在しか見ず、template の完全性を保証しない。
- **[成果物影響 1 行]** merge commit の message が実際に取り込んだ main SHA を欠く、または古い SHA を記録しても、現行検査は通過する。
- **[推奨: 裁定へ]** SHA placeholder の一箇所置換を実装するか、「commit parent が SHA 束縛を代替する」と F191 を正式に supersede するかを裁定する。「変更 byte が少ないから厳しい」という現 brief の裁定は採用不可。

## 2. [must-fix] F191 点 2 の provenance preflight は存在しない

- **[real の根拠]** 待ち手は `git commit --dry-run -F` と `_message_has_ai_agent` しか実行しない。[provenance 正本](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/ai-provenance.md:81) は `check_ai_provenance.py --message-file` の rc=0 を commit 前に要求する。`git commit --dry-run` は commit 内容の要約であり provenance checker ではない。実際の hooks directory にあるのも `.sample` だけである。例えば空の `AI-Agent:` 行は待ち手を通るが、checker の形式検査では拒否される。
- **[成果物影響 1 行]** provenance 不正な merge commit を作った後に受入を走らせ、land 時の履歴監査まで欠陥を遅延させて受入結果と lease 時間を浪費する。
- **[推奨: 採用]** 「残差は 3b だけ」を撤回し、merge 中の `--message-file` preflight と commit 後監査の帰結を scope／plan に戻す。競合 cleanup 部分だけは実装済み。

## 3. [must-fix] P2 は「tracked 木と HEAD の一致」を保証しない

- **[real の根拠]**
  - `--untracked-files=no` は新規 test、root の未追跡 `conftest.py`、未追跡 import shadow をすべて隠す。これらは pytest の収集・skip・import を変えられる。
  - Git 2.34.1 の local manual では `diff.ignoreSubmodules` の既定は `untracked`。さらに local/global config や `.gitmodules` の `dirty` / `all` で tracked submodule dirt も隠せる。対して [run_tests.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/run_tests.py:1552) と [dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_land.py:816) は明示的に `--ignore-submodules=none` を使う。
  - `assume-unchanged` / `skip-worktree` は Git 自身が worktree を一致扱いするため status が変更を隠す。現 checkout では特殊 bit は 0 件だったが、7,200 秒の待機中に設定されることを禁止する検査はない。
  - 通常の index-only dirt は porcelain の左列に出るため、この点だけは捕捉できる。
- **[成果物影響 1 行]** tip に存在しないテスト制御ファイル・submodule 内容・特殊 bit 配下の source で受入が緑になり、後で除去すれば land も通りうる。
- **[推奨: 裁定へ]** 「全 untracked を受理」「影響可能な未追跡入力だけ拒否」「完全 clean」のどれを保証するか先に裁定し、submodule は少なくとも `--ignore-submodules=none` で固定する。現述語のままなら成果物主張を大幅に狭める必要がある。

なお、偽赤の例に挙げられた `output/pegasus-dispatch/` は [.gitignore](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/.gitignore:25) 対象であり、`--untracked-files=all` でも通常は出ない。今回の acceptance が作る receipt は gate より後に生成される。したがって、この receipt は全 untracked 無視の根拠にならない。

## 4. [must-fix] 一回の status は同時 writer に対する境界にならず、P4 の前提も誤り

- **[real の根拠]** plan は status 後に二つの print を行ってから `run_unbounded` を呼ぶが、worktree writer を止める lock はない。[CLAUDE.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/CLAUDE.md:160) は待機中の独立な文書作業を許し、brief 自身も同じ tree への書込みを実運用根拠にしている。writer が status 前に書けば acquired lease を返して最大 7,200 秒待ち直し、status 後に書けば dirty のまま command が始まる。merge と commit の間に stage されれば、その編集を merge commit に吸収した後で status が空になる経路もある。
- **[成果物影響 1 行]** 同じ正規運用が、timing 次第で長時間の偽赤か、検査をすり抜ける偽緑のどちらにもなる。
- **[推奨: 採用]** waiter 開始から受入終了までの同一 worktree write-quiescence、または immutable な受入 worktree を契約に加える。単発 status だけで「投入瞬間の一致」を保証したと記録しない。

brief の「behind>0 は merge commit 直後なので構造上 clean、値があるのは behind==0 だけ」も誤りである。concurrent writer や、main の gitlink 更新後に未同期の submodule があれば behind>0 でも発火する。

## 5. [must-fix] テスト更新数は正しいが、負例の証拠が不足する

- **[real の根拠]** `_FakeEffects` の exact queue を持ち command へ到達する既存テストは、plan 記載どおり 7 定義・8 cases で過不足なし。`_RoutingAcceptanceEffects` は [全 status を clean と返す](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/orchestrator/tests/test_dev_wave_wait.py:354)ため機械的には壊れない。`_STAGES` の追加方針も、行 1343/1411 の単独条件まで到達集合へ含める限り妥当である。一方、新規負例は fake に dirty stdout を手渡すだけで、実 Git が untracked・submodule config・index bit をどう扱うかを一度も検証しない。また dirty の `held-self` が command を止めつつ release しない専用例もない。
- **[成果物影響 1 行]** Python 分岐は殺せても、実 argv の受理境界や P3 の二つの ownership 帰結を誤実装した変異が生存しうる。
- **[推奨: 採用]** 実 Git の tracked-dirty 負例を最低 1 本追加し、P2 裁定後の untracked/submodule/index-bit 境界と `held-self + dirty` を固定する。既存 7 定義の更新一覧自体は採用可。

## 6. [裁定パッケージ候補] 待ち手を迂回する受入経路は実在する

- **[real の根拠]** [run_tests.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/run_tests.py:505) は引数なし直接起動を acceptance shape と判定する。さらに 2026-08-12 の [worklog 実測](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/docs/archive/worklog-phase3-0812-447-448.md:5) に、T-813 wave が waiter deadlock を迂回して裸の `run_tests.py` を投入した事例がある。
- **[成果物影響 1 行]** waiter-only gate を land しても、プロジェクトが acceptance と認識する実在経路の一部には clean 検査が掛からない。
- **[推奨: 裁定へ]** scope 拡大は本レビューでは勧めない。候補は「waiter 経由だけを権威ある dev-wave 受入と定義し、直接走の結果は記録不可」とする案と、「run_tests acceptance shape に同等 gate を置く」案の択一。

## 7. [nit] land 被覆の説明は不正確だが、純増検出力はゼロではない

- **[real の根拠]** brief は wave 側を tested-tip SHA だけとするが、land の locked preflight は [wave worktree の完全 clean](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t725-t694-lease-clean/tools/dev_wave_land.py:1286) も検査する。ただし編集を受入後に除去すれば status も SHA も一致する。`run_tests.py` の fingerprint 比較も CAP_OOM 時だけで、通常成功では比較せず返る。
- **[成果物影響]** nit — 既存被覆の説明だけが誤りで、受入時にだけ存在して後で消える編集への純増検出力は残る。
- **[推奨: 採用]** brief の land 説明だけ訂正する。「純増ゼロ」という反例は確認できなかった。

## P3 の結論

P3 は現状のまま採用が妥当である。新規取得した `ACQUIRED` を失敗後も保持すると、守る受入処理が無いのに他 wave 全体を TTL 2,400 秒止める。`held-self` の renew には累積上限がなく、実質的にはさらに延長できる。release は当該 wave に最大 7,200 秒の再待機を課すが、他 wave を進めるための fairness と cleanup authority を保つ。`HELD_SELF` を保持する現行例外も、別 invocation の lease を消さないため正しい。

## 総括

must-fix は **5 件**。

1. F191 点 1 は未充足
2. F191 点 2 の provenance preflight 不在
3. P2 が untracked・submodule・特殊 index bit を見逃す
4. 単発 status の TOCTOU と現行 workflow との衝突
5. 実 Git／held-self 負例の不足

親 brief で誤りと判断した主張は、**「残差は 3b だけ」**、**点 1 の“より厳しいため充足”**、**点 2 の provenance 部分が実装済み**、**既知 receipt が全 untracked 無視を正当化する**、**behind>0 は構造上常に clean**、**land は wave 側を SHA だけで見る**、および waiter-only gate が受入層全体を覆うかのような成果物主張である。