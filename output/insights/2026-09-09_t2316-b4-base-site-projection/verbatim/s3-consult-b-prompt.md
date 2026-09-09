単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site

## 必読事項の射影

次を読め。読めなければ即停止し、その旨だけを報告せよ。

- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/brief.md` — 親の段 1 brief (逐語)。**検査対象である。**
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s2-plan.md` — 段 2 プラン (逐語)。**検査対象である。**
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/parent-measurements.md` — 親の実測値 (逐語)。**検査対象である。**
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_closed_critic.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_s4_loop_sort.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/campaign_lock.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_closed_critic.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/conftest.py`

repo の path は上記 worktree のものだけを使う。親 checkout の path を使ってはならない。

## 段の宣言

これは段 3 (敵対相談) である。sandbox は read-only で、書込可能な tmp は無い。
**pytest を実走して緑にすることは求めない。静的検査と読解だけでよい。**
実走していない検査を「通した」と書いてはならない。コードを編集してはならない。commit してはならない。

**プランを守るな。壊せ。** 同意を求められていない。所見が出ないこと自体が失敗である。
予算が尽きそうなら、その時点の途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
出力に結合文字 U+0300〜U+036F を使うな。

## あなたのレンズ: 波及・整合・scope の実在

[T-2316] は `p3_b4_launcher._driver_configs` という**共有 helper** を変える。
このレンズは「変更が想定外の consumer へ波及しないか」「scope の切り方が実在の根拠を持つか」だけを見る。

次を順に攻撃せよ。所見ごとに **real / refuted** を自分で判定し、根拠を file:line で示せ。

1. **既存 consumer 8 箇所の波及。**
   親の実測 4 (parent-measurements.md) が `_driver_configs` の呼び手 8 箇所を挙げている。
   `test_p3_b4_closed_critic.py` の各呼び出しについて、base 射影が入った後も緑のままか静的に判定せよ。
   - `conftest.py` の hostname 中立化が**その test に確実に効いているか**を fixture の
     scope・autouse・適用対象 module まで辿って確かめよ。効かない test が 1 つでもあれば real 所見である。
   - `_marked_driver_configs(driver_kind="base")` を通る test が、射影後の config を
     **凍結された期待値**や **hash / ID の literal** と突き合わせていないか。
     突き合わせているなら、その期待値は OTHER 前提で書かれているか確かめよ。
   - 親の列挙自体が漏れていないか。`_driver_configs` を間接的に呼ぶ経路
     (`prepare_launch`、`launch_bootstrap`、`launch_continuation` 経由) の呼び手も数えよ。

2. **closed critic と proof chain への波及。**
   `launch_continuation_impl` は `_driver_configs` の返り値を
   `p3_b4_closed_critic.create_b4_closed_critic_pair(on_cfg=..., off_cfg=...)` へ渡す。
   base 射影が入ると、PEGASUS_COMPUTE では渡る config が変わる。
   - critic の receipt / proof chain / identity projection に記録される bytes が変わるか。
   - 変わるなら、それを pin している凍結成果物・golden・台帳が repo 内に在るか。
     `p3_b4_closed_critic.py:640-660` の enforcement source 列と
     `campaign_lock.py:80-113` の source 一覧も見よ。
   - 親は `p3_b4_launcher.py` の blob sha と sha256 を検索して 0 件と実測した。
     しかし **path 以外を key にする pin** (role 名、xdist group 名、schema 版、
     campaign ID の literal、`measurement_env` の値) が在りうる。key 側でも探せ。

3. **scope の切り方に実在の根拠があるか。**
   - プランは `p3_s4_loop.py:1896` (公開 `run_one_iteration` の授権境界) の条件付き不一致を
     「正式 launcher 経路外」として scope 外にした。**この主張を実測で反証せよ。**
     repo 内にこの公開関数を直接呼ぶ caller は在るか。test は。tools/ は。
     在るなら「経路外」は誤りで、real 所見である。
   - `sort` を巻き込まない設計だとプランは言う。`p3_s4_loop_sort.py` に
     site helper が本当に無いか、別名 (`compilers_for_current_site` など) で
     等価の機能を持っていないかを確かめよ。
   - `[T-2317]` の `_assert_layout_matches_campaign` / `_with_campaign_location` を
     移植しないことで、base の layout 照合が**今回の修正後に**破れる面が生じないか。
     生じるなら scope 外だが real として返せ。

4. **親 brief と plan の前提の読み違い。**
   親は `classify_site` を 2 値と読み違えていた (訂正済み)。同種の読み違いを他にも探せ。
   特に次を疑え。
   - brief の「OTHER では ID 不変」は D125 / D261 と整合するか。
     D261 は「OTHER の campaign_id は 1 bit も変えない」を**前向きに失効**させている。
     brief の主張は現行 decisions と食い違っていないか。
   - brief の「実装面は単一ファイル 1 関数 + test 1 ファイル」という分割方針は、
     所見 1 の波及を踏まえて成り立つか。
   - plan の「変更後の関数の完全な形」を写経したとき、`import` や module alias
     (`p3_s4_loop` を `L` として使う等) の実在が launcher 側で満たされているか。

5. **受入台帳と新 node。**
   `orchestrator/tests/acceptance_duration_ledger.json` は test の nodeid ごとに所要を持つ。
   新 node を足すとき、この台帳の更新契約 (誰が・いつ・どの producer で書くか) を
   `conftest.py` と `test_update_acceptance_duration_ledger.py` から読み取り、
   plan の「親が main 取り込み後に運用追記」で足りるかを判定せよ。足りないなら real 所見である。

## 禁止

- 授権境界の比較を緩める案を出してはならない。
- 未知 site の fail-closed を広げる案を出してはならない。
- OTHER の campaign_id を変える案を出してはならない。
- `sort` の挙動を変える案を出してはならない ([T-2318] の scope)。
- 仮想リスク向けの新しい gate・検査・台帳・一般化を提案してはならない (依頼の明示 scope 外)。
  scope 外だが real な所見は「実装せず裁定へ返す候補」として明記せよ。

## 出力形式

以下の H2 見出しをこの順で使え。所見には通し番号 B1、B2、… を振れ。

## 所見 (real)
## 所見 (refuted)
## scope 外だが real (裁定へ返す候補)
## 総括
