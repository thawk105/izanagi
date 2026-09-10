単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight

必読事項の射影: 次を読む。読めなければ即停止し、読めなかった絶対パスを報告して終わる。

- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/plan-v2.md` — 親の段 4 裁定。**実装が守るべき契約の正本**
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/verbatim.md` — 既裁定と契約文の逐語射影
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/author.md` — 実装子の申告。**申告を信じず現物で検算せよ**
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py` — 実装 (変更済み)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py` — テスト (変更済み)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md` — 契約の正本 (凍結)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md` — 旧登録 (凍結)。§7 完走述語・§8 停止条件と予算

差分を見るには作業 root で `git diff` を使え (変更は未 commit の作業ツリーにある)。

## 依頼

**レンズ A: 契約適合と正しさ境界。** 実装を守らず、壊しに行け。
実装子は 114 test 緑を申告しているが、**緑であることは正しさの証明ではない。**

## 特に攻撃してほしい点

1. **裁定どおりか。** `plan-v2.md` §3.1〜3.7 の 7 点それぞれについて、実装が実際にそうなっているかを
   file:line で検算せよ。特に:
   - limiter が記録する発行時刻が、本当に `transport.send` を呼ぶ**直前**の実時刻か。
     `acquire` 時点の時刻へ退行していないか。
   - 待ち (sleep) が本当に `begin_attempt` **より前**か。
   - 送信 (transport) 例外の経路で本当に `materialize_pending_attempt()` が呼ばれるか。
     **例外の型で分岐して一部の失敗を取りこぼしていないか。**
   - 予算・締切の検査が本当に状態を変えず、`begin_attempt` より前か。
   - `validate_preflight_report` が `observed_interval_seconds` の**値**で拒否しないか。
     間接的に (件数・順序・digest 経由で) 値が受理条件に入り込んでいないか。
   - 同一 stream の 4 回目 attempt が本当に拒否されるか。**3 回目までは受理されるか。**
2. **受理集合が動いていないか。** 非 200 → `unavailable`、未解決 factory → `blocked`、
   完走述語 (§7.1 条件 0〜6)、`declared_total` の導出、初回 OpenAlex 429 の exact-one stop。
   **inline retry の追加でこれらのどれかが動いていないか**を行単位で確かめよ。
   特に、retry によって「429 を受けた row が最終的に `ready` になる」経路が**新たに**生まれて
   いないか (§8.4 の潜脱)。
3. **テストが甘くなっていないか。** 既存期待値 (`wire_attempt_count == 1929`、`blocked == 193`、
   `rows == 2122`、`len(transport.calls) == 1929`) が実質的に維持されているか。
   条件を緩めた・skip した・fixture を差し替えて通した箇所が無いか。
   **新設テストが恒真 (どんな実装でも通る) になっていないか**を、述語の中身を読んで判定せよ。
4. **scope 外の実装が紛れ込んでいないか。** source の差分は 836 行ある。`plan-v2.md` §5 の
   scope 外項目 (pending intent の回復強度、body/wall-clock ceiling、resolver、control 評価器、
   DBLP 題名 lookup) や、要求外の gate・検査・一般化が入っていないか。
   **入っていれば real 所見として挙げよ。**
5. **凍結境界。** catalog bytes・query ID 集合・語・10 枝・cutoff・`request_factory` state が
   変わっていないか。`tools/run_axis3_search.py` と schema 4 本が無変更か。
6. **report v2 への版上げの影響。** v1 を前提にする consumer が repo 内に残っていないか。

## 出力規律

- 所見ごとに **real / refuted の判定を自分で下し、根拠の file:line を必ず添えよ。**
- **must-fix と nit を分けよ。** 放置したとき成果物 (preflight report・bundle・実行記録・
  受理集合) の値や参照がどう変わるかを 1 行で書けない所見は nit とせよ。
- 所見ゼロならそう書け。無理に見つけるな。

## 禁止

- 実装・編集・commit。read-only である。
- 最小間隔・retry 上限を緩める提案。

## 実行環境の注意

書込可能な tmp が無いため pytest 緑を要求しない。静的検査でよい。テストの実測は親が行う。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 出力形式

以下の H2 見出しをこの順で使う。結合文字 U+0300〜U+036F を使うな。

## 裁定 7 点の検算
## must-fix (real)
## nit
## refuted
## 総括
