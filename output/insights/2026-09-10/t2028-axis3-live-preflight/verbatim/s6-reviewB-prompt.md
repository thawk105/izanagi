単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight

必読事項の射影: 次を読む。読めなければ即停止し、読めなかった絶対パスを報告して終わる。

- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/plan-v2.md` — 親の段 4 裁定。**実装が守るべき契約の正本**
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/verbatim.md` — 既裁定と契約文の逐語射影
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/author.md` — 実装子の申告。**申告を信じず現物で検算せよ**
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py` — 実装 (変更済み)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py` — テスト (変更済み)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/axis1_search/runner.py` — `HostLimiter` の移植元
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/tools/run_axis3_search.py` — CLI (無変更のはず)

差分を見るには作業 root で `git diff` を使え (変更は未 commit の作業ツリーにある)。

## 依頼

**レンズ B: 機構の実効性。** この実装は、これから **19.5 時間・1929 本の live 走行**に使われる。
「テストは緑だが実走で効かない」経路を見つけるのが仕事である。

## 特に攻撃してほしい点

1. **機構の正例・負例が実体を名指ししているか。** 新設テストが、性質だけを検査して
   **両層 stub で機構を通らない緑**になっていないか。pacing・retry・cooldown・
   materialize の各テストが、production が実際に通る呼び出し経路 (`LiveSearchSession` /
   `_send_with_raw_commit` / `run_preflight` / `resume_bundle`) を通っているかを確かめよ。
   fake sleeper が呼ばれた回数だけを見て、**実際の送信順序を検査していない**テストは弱い。
2. **変異が本当に殺されるか。** `plan-v2.md` §3.7 の 6 つの変異それぞれについて、
   **どのテストのどの assert が落ちるか**を file:line で示せ。落ちないものがあれば real 所見。
   1. 最小間隔を 0 にする
   2. limiter の発行時刻を `acquire` 時点へ戻す
   3. retry 上限を 3 から 4 へ上げる
   4. 送信失敗経路の `materialize_pending_attempt()` を消す
   5. 予算検査を `begin_attempt` の後へ戻す
   6. `observed_interval_seconds` の値で拒否する gate を足す (「通る正例」が落ちるはず)
3. **19.5 時間走行の現実性。** 実装後の live preflight で、次の各場面に何が起きるかを
   コードから追え。
   - DBLP が 1415 本連続の途中で接続を切ったとき (retry 3 回 → cooldown → 次の row)。
     **cooldown 後も切れ続けたら何が起きるか。残り全 row が `unavailable` になるか。**
   - retry の backoff 中に process が死んだとき。pending intent は残るか。
   - `resume --live` したとき、limiter の永続状態は本当に引き継がれるか。
     **cooldown の途中で落ちた場合、resume は cooldown を尊重するか。**
   - OpenAlex が 2 本目以降で 429 を返したとき (初回 429 の exact-one stop は別経路)。
4. **所要時間が伸びていないか。** retry と cooldown の追加で、最悪時の所要はどうなるか。
   `RUN_DEADLINE` (30 日) と 20 万 request 上限に対する余裕を数値で出せ。
   **cooldown 2700 秒が最悪何回発火しうるか**を上限で示せ。
5. **受入所要台帳。** 追加された 6 node の値が正本 producer 由来の実測か。`0.0` や
   placeholder が無いか。全体の受入所要が 5 分の壁を壊していないか
   (`orchestrator/tests/acceptance_duration_ledger.json`)。
6. **並行性。** limiter の状態 file は `flock` を使うと申告されている。
   同一 bundle への 2 process 同時起動、および**別 bundle からの同一 host 送信**で
   何が保証され何が保証されないかを明示せよ。

## 出力規律

- 所見ごとに **real / refuted の判定を自分で下し、根拠の file:line を必ず添えよ。**
- **数値の主張には導出過程を書け。**
- **must-fix と nit を分けよ。** 成果物の値や参照がどう変わるかを 1 行で書けない所見は nit。
- 所見ゼロならそう書け。無理に見つけるな。

## 禁止

- 実装・編集・commit。read-only である。
- 最小間隔・retry 上限を緩める提案。

## 実行環境の注意

書込可能な tmp が無いため pytest 緑を要求しない。静的検査でよい。テストの実測は親が行う。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 出力形式

以下の H2 見出しをこの順で使う。結合文字 U+0300〜U+036F を使うな。

## 変異 6 件の帰属 (どのテストのどの assert が殺すか)
## 19.5 時間走行の場面別追跡
## must-fix (real)
## nit
## refuted
## 総括
