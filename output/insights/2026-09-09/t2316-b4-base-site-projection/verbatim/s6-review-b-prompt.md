単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site

## 必読事項の射影

次を読め。読めなければ即停止し、その旨だけを報告せよ。

- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s4-adjudication.md` — **段 4 裁定。実装の正本。**
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/parent-measurements.md` — 親の実測値。
- `/home/SFC/tanab/.claude/jobs/f8a552e6/tmp/t2316/s5-author.md` — 実装子の完了報告。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_launcher.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_launcher.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/test_p3_b4_closed_critic.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/tests/conftest.py`
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2316-b4-base-site/orchestrator/campaign/p3_b4_closed_critic.py`

レビュー対象の差分は commit `db95ffb3bd0b585a702ecbd9523a5aba790652f4` である。
`git show db95ffb3b` で読め。repo の path は上記 worktree のものだけを使う。

## 段の宣言

これは段 6 (敵対レビュー) である。sandbox は read-only で、書込可能な tmp は無い。
**pytest を実走して緑にすることは求めない。静的検査と読解だけでよい。**
実走していない検査を「通した」と書いてはならない。コードを編集してはならない。commit してはならない。

**実装を守るな。壊せ。** 所見が出ないこと自体が失敗である。
予算が尽きそうなら、その時点の途中結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
出力に結合文字 U+0300〜U+036F を使うな。

## あなたのレンズ: 受理集合の変化と scope 逸脱

次を順に攻撃せよ。所見ごとに **real / refuted** を判定し、根拠を file:line で示せ。

1. **受理・拒否集合が、裁定が許した以外の向きに動いていないか。**
   commit `db95ffb3b` の前後で、`_driver_configs` / `prepare_launch` / `launch_bootstrap` /
   `launch_continuation` の入力に対する受理集合がどう変わったかを driver_kind ごと・site ごとに
   表にせよ。裁定が意図したのは「PEGASUS_COMPUTE の base で launcher ID が driver ID と一致する」
   ことと「計測用 env bytes を作れない 2 site (PEGASUS_LOGIN / PEGASUS_SUSPECT) で base が
   早期 fail-close する」ことだけである。それ以外の変化があれば real 所見である。

2. **test が甘くなっていないか。**
   追加された 5 node が、既存 node の検査を実質的に置き換えたり、既存の厳しい検査を
   迂回可能にしていないか。既存 test の期待値が 1 文字でも変わっていないか
   (`git show db95ffb3b -- orchestrator/tests/test_p3_b4_launcher.py` の削除行を全部見よ)。
   fixture へ現行 hash を差し込む、揮発 payload を焼き込む、といった甘くする型が無いか。

3. **`site_policy.socket` の差し替えが他 test を汚染しないか。**
   追加 node は `monkeypatch.setattr(site_policy, "socket", ...)` を使う。
   - `conftest.py` の autouse 中立化と両方が効いたとき、teardown の順序で元に戻るか。
   - 同一 file 内の後続 test、および同一 xdist worker 上の他 file の test に漏れないか。
   - `mock.Mock(gethostname=lambda: ...)` は `socket` module の他の属性
     (`gaierror` 等) を参照するコードから見て壊れていないか。`site_policy` が
     `socket` の他属性を使っていないか実装まで確かめよ。

4. **N2 のループ構造。**
   N2 は 1 つの test 関数の中で 2 site を for ループで回し、ループ内で `monkeypatch.setattr` を
   繰り返す。2 周目の setattr が 1 周目の値を上書きするとき、`monkeypatch` の undo stack が
   期待どおりか。片方の site だけ検査して緑になる抜けが無いか。
   ループ内 assert が失敗したとき、どちらの site で落ちたか特定できるか。

5. **scope 逸脱。**
   commit が触った file は 2 つだけか。裁定が「触ってはいけない」と列挙した file に
   1 byte も入っていないか。無関係な refactor・命名変更・型注釈整理・
   新しい gate や台帳が紛れていないか。

6. **実装子の自己申告の裏取り。**
   実装子は「docs、台帳、既存 test の期待値は未変更」「commit、add、stash、branch 操作も未実施」
   と報告した。commit `db95ffb3b` の実体と照合せよ (この commit は親が作ったものである)。
   報告と実体が食い違えば real 所見である。

## 禁止

- 授権境界の比較を緩める案を出してはならない。
- 既存 test の期待値を変える案を出してはならない。
- 仮想リスク向けの新しい gate・検査・台帳・一般化を提案してはならない。
  scope 外だが real な所見は「実装せず裁定へ返す候補」として明記せよ。

## 出力形式

以下の H2 見出しをこの順で使え。所見には通し番号 RB1、RB2、… を振れ。

## 受理集合の変化 (表)
## 所見 (real)
## 所見 (refuted)
## scope 外だが real (裁定へ返す候補)
## 総括
