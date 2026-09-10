単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight

必読事項の射影: 次を読む。読めなければ即停止し、読めなかった絶対パスを報告して終わる。

- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/brief.md` — 親の段 1 brief。**これ自身が検査対象である**
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/verbatim.md` — 既裁定と契約文の逐語射影
- `/home/SFC/tanab/.claude/jobs/1a05f945/tmp/t2028-artifacts/t2028-axis3-live-preflight/plan.md` — 段 2 のプラン。**これも検査対象である**
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/related_work_search.py` — 軸 3 実行器
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/tools/run_axis3_search.py` — 軸 3 CLI
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/axis1_search/runner.py` — 軸 1 実行器 (`HostLimiter` の移植元)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/orchestrator/tests/test_related_work_search.py` — 軸 3 の consumer test
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2028-axis3-live-preflight/docs/related-work/claim-survey/2026-09-01-axis3-registration-preflight.md` — 直近の実行記録 (凍結)

## 依頼

**レンズ B: 実効性と運用整合。** 親の brief と段 2 プランを守らず、壊しに行け。
「設計としては正しいが、実際に流すと止まる／壊れる／終わらない」経路を見つけるのが仕事である。

## 特に攻撃してほしい点

1. **(P2) 親の provisional 裁定を攻撃せよ。** 親は pacing 定数 (arXiv 3.0 / OpenAlex 1.0 /
   DBLP 45.0 秒) を軸 1 の実測下限からそのまま継承した。**軸 3 固有の事情でこれが不十分または
   過剰でないかを判定せよ。** 軸 1 と軸 3 で request の形 (page size、query 長、応答サイズ)、
   本数、host あたりの集中度がどう違うかを実際に読んで比較せよ。
   継承が誤りなら、**どの向きに誤りか**を示せ。
2. **所要時間の現実性。** 親の見積りは DBLP 1533×45s + arXiv 373×3s + OpenAlex 23×1s ≈ 19.5 時間。
   この計算に入っていない項 (接続時間、応答待ち、retry、cooldown、finalize、bundle 書き込み) を
   洗い出し、**現実的な上限**を出せ。30 暦日の deadline (`RUN_DEADLINE`) と 20 万 request 上限に
   対する余裕も見よ。本走まで含めた総所要が deadline に収まるかを判定せよ。
3. **中断・再開の実効性。** `_resume_preflight_from_wal` は本当に残り行を継続するか。
   `unconfirmed_attempt_intent` の袋小路に入る窓はどれだけあるか。プランが「sleep を
   `begin_attempt` より前に置く」で本当にその窓を閉じられるか。**閉じられないなら、
   19.5 時間の走行中に process が死んだとき何が起きるかを具体的に書け。**
4. **seal と HEAD closure の順序。** `preflight --live` は `enforce_head=True` で、closure 8 file の
   作業ツリー bytes と `HEAD:<path>` の一致を要求する。実装 commit → `register` 再実行 →
   `preflight --live` → 記録 commit という順序が本当に成立するか。**記録 commit が HEAD を動かすと
   途中で再開できなくなる経路**が無いかを確かめよ。resume が `registration_commit` に固定される
   実装なら、その固定先が何になるかを読んで示せ。
5. **bundle の置き場所。** 親は repo 外の恒久 path に置くと決めた。`--bundle` が checkpoint へ
   絶対 path で焼き込まれるか、`validate_bundle` が検証先 path との一致を要求するかを実装で確かめ、
   worktree 撤去後に検証・再開できるかを判定せよ。
6. **OpenAlex 無償枠。** 軸 3 の live preflight は OpenAlex 23 request。1 request あたりの
   credit 消費を実装と軸 1 の観測から導き、1 日の窓 (limit 1000) に収まるかを示せ。
   **同一ノードから軸 1 の走行が並行していた場合**に何が起きるかも書け。
7. **test 計画の実効性。** プランの test が実時間 sleep を走らせないか。受入全走の所要
   (`orchestrator/tests/acceptance_duration_ledger.json` を見よ) を伸ばさないか。
   新規 test file を足す計画なら、自走 harness と所要台帳の両方が要ることを指摘せよ。

## 出力規律

- 所見ごとに **real / refuted の判定を自分で下し、根拠の file:line を必ず添えよ。**
- 数値の主張には導出過程を書け。「遅い」「危ない」だけは不可。
- 成果物 (実行記録・bundle・preflight report・台帳) の値・受理集合・参照がどう変わるかを
  1 行で書けない所見は、nit として分離せよ。
- scope 外だが real な所見は、実装案ではなく**裁定パッケージ候補**として返せ。

## 禁止

- 実装・編集・commit。read-only である。
- プランの穴を自分で埋めた改訂版を書くこと (それは段 4 の親の仕事)。
- 最小間隔を緩める提案。速度のための弱体化は禁止。

## 実行環境の注意

書込可能な tmp が無いため pytest 緑を要求しない。静的検査でよい。テストの実測は親が行う。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 出力形式

以下の H2 見出しをこの順で使う。結合文字 U+0300〜U+036F を使うな。

## pacing 定数の判定 (P2 への回答)
## 所要時間と deadline の判定
## real 所見
## refuted 所見
## nit
## 裁定パッケージ候補
## 総括
