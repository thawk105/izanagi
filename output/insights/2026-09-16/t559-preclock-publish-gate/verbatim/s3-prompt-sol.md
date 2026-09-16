単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate

## 必読事項の射影

次の絶対パスだけを読む。**この節が列挙した file を読めなければ即停止する** (停止規則の射程は
この射影 file に限る。ここに無い path の不在は停止理由にしない)。

- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/brief-t559.md — 親 brief。**これも検査対象である**
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/artifacts/t559-preclock-publish-gate/stage2-plan.md — 段 2 plan。**検査対象**
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-T559-entry250.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-T559-entry944.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D191.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D218.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D155.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-F108.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/cli.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/effective_clock_policy.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/report.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/schema_v2.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/campaign/execution_guard.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/tests/test_calibrator_certify.py

## 役割

**レンズ A = 正しさ境界。** 親 brief と段 2 plan を守らない。壊しに行く。
plan を実装したとき「通ってはいけないものが通る」「発火すべき時に発火しない」経路を探す。

## 攻撃してほしい点

1. **恒真・恒偽。** 提案する pre→post 比較が、実装の形によって常に真 (何も止めない) または
   常に偽 (何も通さない) になる経路はあるか。canonical 述語
   `effective_clock_comparison_passes` の入力 shape 要件 (expected は 2 key、observed は 1 key) を
   満たさない渡し方をすると `input_valid=False` になり、述語は False を返す。これは
   「帯外だから落ちた」のか「入力が壊れているから落ちた」のか区別できるか。区別できないと
   何が起きるか。逆に expected/observed を取り違えても偶然通る入力はあるか。
2. **規律 2 (正しさゲートを緩めない)。** plan が既存の reason を消す、上書きする、
   統合する経路はないか。`reasons` list への追記順序が既存テストの期待値を壊さないか。
   既存の early 拒否経路 (`cli.py` の `_EARLY_CLOCK_REJECTION_NOT_EVALUATED` と
   `rejection_not_evaluated`) に新検査名を足すと、early 拒否の受理集合が変わらないか。
3. **親自身の実測値とその一般化を疑う。** 親は brief で「実 attempt 7 件のうち直近 6 件は
   post 48 標本すべてが厳密に 2101.0 MHz、乖離 0.000% なので新 gate は到達可能」と書いた。
   この一般化はどこまで正当か。F108 の逐語は 2026-08-04 時点で「重複を除いた 23 の標本列すべて」が
   帯外標本を持つと記録している。親の 7 件と F108 の 23 件はどういう関係にあるか。
   親は「計算ノードでは再現していない」と書いたが、これは何を根拠にでき、何を根拠にできないか。
   **この gate を入れた結果、次の取得 job が benchmark を全部走らせた後に落ちる確率について、
   親の実測は何を言えて何を言えないか。**
4. **比較時点の意味。** `static_post` は benchmark 直後に 1 回撮るだけである。
   benchmark 中にクロックが振れて戻った場合、この gate は何も検出しない。
   それでも「publish 前照合」という裁定を満たすか。満たすと言えるなら、この gate が
   **保証しないこと**を正確に 3 行以内で書け。誇張した名乗りになっていないか。
5. **入力の出所。** `profile["effective_clock"]["tolerance_pct"]` は attempt 開始時に
   policy 定数から焼いた値である。publish 直前の `_effective_clock_policy_matches_current`
   (`cli.py:1044` 付近) との関係で、新 gate が policy 再束縛の窓を開けたり塞いだりしないか。
6. **段 2 plan の負例設計。** plan が提案する
   `[2101.0]*47 + [2110.0]` という凍結 pre と、post の 1 標本 3079.456 という組み合わせは、
   本当に「既存 self を通り新 gate だけが落とす」か。中央値・帯の計算を自分でやり直して検算せよ。
   `execution_guard.py` の帯計算は expected の**中央値**を基準にする。標本数が偶数 (48) のとき
   `statistics.median` は中間 2 値の平均を返す。plan の数値でこれは成立するか。

## 禁止

- file の作成・編集・削除、commit、git の状態変更。
- scope を広げる提案 (別 process verifier、外側 wrapper の改修、observer effect の是正、
  publish 順序の変更、canonical 述語の改訂、benchmark 中の clock 検査)。
  これらが**必要だ**と判断した場合は、実装提案ではなく **裁定パッケージ候補**として
  「scope 外だが real」と明記して返す。
- 仮想リスク向けの防壁の新設提案。

## 実行環境

sandbox は read-only で書込可能 tmp が無い。**pytest を実走しなくてよい。静的検査でよい。**
走らせていないものを「緑」と書かない。予算が尽きそうなら途中までの結論を出力形式どおり書いて終わる。

## 出力形式

H2 見出しだけを使う。所見ごとに「real / 疑わしい」「scope 内 / scope 外」「根拠の file:line」を書く。
最後に必ず次の節を置く。

## 総括

- 最も重い所見を 3 件まで、各 2 行以内。
- plan をこのまま実装してよいか (yes / 条件付き / no) と、その条件。
