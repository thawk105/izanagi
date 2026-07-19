# 2026-07-20 B-004 wave — codex 敵対相談 逐語凍結 (F20) + 親裁定 + 裁定パッケージ

- 構成: codex exec, model=gpt-5.6-sol, reasoning=max, sandbox=read-only,
  cwd=worktree s8b-c22-launch-cert (branch approved-waves, 基準 e6834fb)
- 対象: B-004 wave プラン v1 (docs/handoff/2026-07-19-b004-experiment-numbers.md)。
  ユーザー裁定 (2026-07-19): 公式実験 extime=5 秒 / reps=5、floor と oracle は結合 (単一
  authority)、実装は一致検査。探索は 3 秒 3 回目安で検証器の対象外。隣接 3 穴
  (P_timeout_reason / P_build_reason / P_reason_type_crash) と oracle 側 reps も同 wave
- 相談 2 本 (並列): C-A = pin/authority + 駆動整合レンズ / C-B = report 閉表 + fixture/変異恒真レンズ
- 親裁定: 14 所見 (A=7, B=7) すべて real / refuted 0。in-scope 実装とユーザー裁定待ち
  (裁定パッケージ) の二分は下記。プラン v2 の正本 = handoff 同名節 (完了時 worklog へ吸収)

## 親裁定サマリ

**in-scope (プラン v2 へ反映、実装)**: A4/B2 (単一 authority の実配線 — 数値 leaf 新設 +
s8b_approved を import 束縛再輸出化 + module-qualified 参照 + monkeypatch 配線テスト)、
A7/B2 (floor_contract import 不変条件テストの許可リスト更新)、B1 (閉表は
s8b_abort_reason_contract へ。verify-inconclusive 重複 literal も統合)、B3 (fixture 更新は
9 ファイル。driver 予約期待値 25×行数化。golden SHA は実 serializer から再計算)、B4 (負例は
sole-abort 置換注入。N2/N3 分離。閉表全 reason の正例)、B7 (timeout 兼用分岐は共通 terminal
検査 + outcome→閉表 dict 選択)、A6 (docstring 限定注記のみ)

**裁定パッケージ (実装せず、ユーザー裁定へ。§5-(ix) 形式は下記)**: A1 (report→judge→verdict の
manifest 検証迂回 + 探索 namespace 隔離)、A2 (reps=5 の観測証拠件数意味論)、A3 (A1 に併合)、
A5 (gate-check preflight 偽緑)、B5 (段階順序 truth-table)、B6 (全 stage payload Mapping guard)

## 裁定パッケージ (§5-(ix) 形式、ユーザー裁定待ち)

1. **P-A1 (severity high): oracle 後処理の manifest 検証迂回。** report は run_contract 欠落
   manifest を legacy として receipt 検査なしで受理し (s8b_oracle_report.py `_receipt_expectations`
   の意図的文書化あり)、judge は manifest_sha256 の非空 str しか検査せず、combined verdict は
   verified manifest への再束縛をしない。探索成果物 (3×3) や未検証 manifest が公式 verdict schema を
   名乗れる (相談 A が read-only 再現)。**選択肢**: (a) report 入口で verify_manifest 必須化 +
   verdict の manifest hash 再束縛 + legacy 受理の廃止 or 明示 flag 化、(b) 探索成果物を別
   schema/namespace に隔離し official 側が型で拒否、(c) 現状維持 (legacy 受理は v1 移行期の意図的
   設計と追認)。**推奨 = (a)+(b) の段階導入** (まず (b) の namespace 隔離が小さく、(a) は C2-6 系の
   配線設計を要する)。A3 (探索隔離未実装) はここに併合
2. **P-A2 (severity medium): reps=5 は要求値で、観測証拠 5 点を保証しない。** generic pipeline は
   require_all_reps=False (calibrator/runner.py) で部分成功を採用し、report は tps 非空しか見ない。
   **選択肢**: (a) official oracle だけ require_all_reps=True、(b) report で len(tps)==reps を検査、
   (c) 部分失敗許容を明示裁定し「成功数 + 失敗証拠 = reps 完全被覆」を検査。**推奨 = 裁定で意味論を
   確定してから (b) 同形の検査** (report 側が証拠と突き合わせる現行様式に整合)
3. **P-A5 (severity medium): standalone gate-check の preflight 偽緑。** load_ratified_freeze は
   strict parse のみで floor protocol の数値検証をせず launch_validate も呼ばない。active v2
   generation に旧 extime=3 floor protocol + 5/5 oracle manifest の組で gate-check が allowed を
   返し得る (run-block 本線は後段で拒否するため誤実走はない)。**推奨**: v2 gate-check で
   launch_validate または floor protocol full validation を必須化し、floor=3/manifest=5 の負例
   fixture で allowed=False を固定
4. **P-B5 (severity medium): reason が正しければ producer 不可能な段階履歴を受理。** build-failed
   宣言 + verify_done(pass) 付き WAL、timeout 宣言 + bench_done 付き WAL が現行 _assess_window を
   通る (相談 B が in-memory 再現)。**推奨**: outcome ごとの段階 truth-table (build-failed:
   build_done=0 ∧ verify 両 missing ∧ bench 無し / timeout: build_done=1 ∧ bench 無し 等) を閉表と
   同様に leaf 化して検査。失敗 outcome のため直接の false-green ではないが「report が証拠 truth
   table を検証する」契約の欠落
5. **P-B6 (severity medium): abort 以外の stage payload 非 Mapping で report がクラッシュ。**
   build_start.payload=[] / bench_done.payload=[] が AttributeError で report 全体を落とす
   (相談 B が再現。CLI の例外捕捉にも AttributeError なし)。**推奨**: 全 PIPELINE_STAGES record の
   payload Mapping 検査を row-level protocol_violation 化 (P_reason_type_crash と同型の堅牢性穴)

## 運用注記

- 相談 A/B とも安全フィルタ発火なし (プロンプトを防御的表現で作成、F20/前回運用知見の適用)
- C-B は repo 内の未追跡 handoff (プラン v1) を読み、プロンプト版プランとの食い違い (閉表の配置) を
  所見化した — 相談へ渡すプランと handoff の同期は投入前に行うこと (今回は同期済みのため実害なし)
- identity-error は現行 oracle driver 経路では未発行 (pipeline の src_token=None 経路のみ) だが
  分類器契約として閉表に保持 (相談 B の到達性分析)


## C-A プロンプト (逐語)

```
あなたは独立した敵対的レビュアーです。以下の実装プランの設計欠陥を、repo を実際に読んで検証しながら指摘してください。プランを守る側に回らず、壊れ方を探す側に立ってください。

# 背景 (ユーザー裁定、確定済み)

s8b campaign (orchestrator/campaign/s8b_*.py) の公式実験パラメタが裁定された:
- **公式実験は extime=5 秒 / reps=5**
- **floor と oracle は結合 (単一 authority)。実装は一致検査**
- **試行錯誤 (探索) は 3 秒 3 回目安で、検証器の対象外**

現状: floor 側 (s8b_floor_contract.py) は `_APPROVED_REPS = 5` をローカル定数で pin 済みだが `extime_s` は `_pos_int` (任意正整数受理)。oracle 側 (s8b_oracle_manifest.py `_validate_run_contract`) は reps/extime とも正整数なら受理 (reps=999 / extime=999 も通る、実測済み)。

# プラン (この部分を攻める対象)

1. **数値契約 leaf 新設** `orchestrator/campaign/s8b_experiment_numbers.py` (stdlib-only、s8b_abort_reason_contract.py と同じ思想):
   `APPROVED_EXTIME_S = 5`、`APPROVED_REPS = 5`。docstring に裁定日・結合契約 (floor protocol と oracle run_contract の両検証器が同一 leaf を参照 = 単一 authority、探索は対象外) を明記
2. **floor 側** `s8b_floor_contract.py`: `extime_s` を `_pos_int` から `_pinned(…, APPROVED_EXTIME_S)` へ。既存ローカル `_APPROVED_REPS = 5` も leaf 参照へ移す (n_sessions 等の他定数は触らない)
3. **oracle 側** `s8b_oracle_manifest.py` `_validate_run_contract`: `reps == APPROVED_REPS`、`extime == APPROVED_EXTIME_S` の完全一致 pin (既存の bench_max_rounds==1 検査と同形)。凍結 protocol object を manifest 検査へ引き回す深い配線は採らない — 両検証器が同一 leaf に束縛されるため一致は transitively 成立し、可動部が少ない、という理屈

# 検証してほしい観点 (これ以外の欠陥発見も歓迎)

1. **leaf 共有 pin と裁定「一致検査」の意味的距離**: 裁定は「floor と oracle の一致検査」。leaf 共有 pin は time-of-check で両者が同じ定数に縛られるが、time-of-freeze と time-of-run の間に窓はないか。leaf を経由しない検証経路 (floor protocol や oracle manifest を検査する別のコード) が存在しないか、repo を grep して確認せよ
2. **駆動側との整合**: s8b_floor_campaign.py / s8b_oracle_driver.py / s8b_materialization.py 等の駆動側が extime/reps をどこから取りどう渡すか。pin と矛盾する経路 (駆動が 3 を渡してしまい公式検証が常に赤、あるいは逆に検証を迂回して非承認値の run が公式を名乗れる経路) はないか
3. **探索 3 秒経路の非干渉**: 探索 (3 秒 3 回) の実行経路が誤ってこの pin に当たって赤くならないか。逆に探索の成果物が公式検証を通ってしまう混入経路はないか
4. **scope 逸脱**: このプランが裁定されていない field (n_oracle、budget 秒、検定点等) まで束縛していないか
5. **consumer 取り残し**: 「extime_s は任意正整数」という現契約に依存しているコード・テストの取り残し

# 出力形式

所見ごとに: 番号、severity (high/medium/low)、壊れ方の具体シナリオ (どういう入力・状態で何が誤る)、根拠 file:line (実際に読んで確認したもの)、最小修正案。所見ゼロならその根拠 (何を確認して穴がなかったか) を列挙。日本語で。
```

## C-A 出力 (逐語)

```
結論は **NO-GO** です。`run-block` 本線は概ね fail-closed ですが、後処理と探索境界に pin を迂回できる経路があります。

### 1. severity: high — report→judge→combined verdict が manifest pin を迂回する

壊れ方: 3秒×3回の探索 manifest と対応 WAL を `s8b_oracle_report.py report` に渡すと、`_validate_run_contract` は一度も呼ばれません。さらに `run_contract` 自体を削除しても legacy として receipt 検査が外れます。その observations は judge を通り、combined verdict は manifest hash が「検証済み manifest のものか」を確認しません。したがって探索成果物が通常の oracle verdict schema を名乗れます。

読み取り専用再現でも、report は `run_contract` 欠落・999×999・3×3をすべて受理しました。judge も任意文字列 `not-a-verified-manifest` を manifest hash として `determinate / unique-best` を返しました。

根拠:

- [s8b_oracle_report.py:73](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:73) — manifest の部分検査だけ
- [s8b_oracle_report.py:516](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:516) — run_contract 欠落を legacy として許容
- [s8b_oracle_report.py:750](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:750) — CLI も raw JSON を直接使用
- [s8b_oracle_judge.py:130](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:130) — manifest hash は非空文字列しか要求しない
- [s8b_verdict.py:336](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:336)、[s8b_verdict.py:827](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_verdict.py:827) — oracle verdict を verified manifest に再束縛しない

最小修正案: report の入口で active freeze と manifest を読み、必ず `verify_manifest` を通した同一 document だけを射影する。observations/judge/verdictにも、その verified manifest hash と active generation の組を照合させる。探索成果物は別 schema・別 namespace とし、official report が受理しないようにする。

### 2. severity: medium — `reps=5` は要求値だけで、観測証拠の件数に結び付かない

壊れ方: manifest は reps=5 でも、5回中3回が失敗して throughput が2点だけ残った場合、generic pipeline は既定で部分成功を採用できます。report は `bench_done.tps` が非空なら受理し、judge も非空配列なら eligible にします。従って「5反復を要求した」ことは保証しても、「公式標本が5点ある」ことは保証しません。

根拠:

- [runner.py:390](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:390) — `require_all_reps=False`
- [runner.py:425](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/calibrator/runner.py:425) — 失敗 rep を除いて継続
- [pipeline.py:231](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:231) — official oracle も strict option を渡さない
- [s8b_oracle_report.py:413](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:413) — tps 件数を run_contract.reps と照合しない
- [s8b_oracle_judge.py:90](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_judge.py:90) — 任意の非空 bench_values を集約
- [test_s8b_oracle_report.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:85)、[同:151](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:151) — manifest fixture を reps=5へ変えても tps 既定は2点のまま通り得る

最小修正案: 「reps=5」が5成功点を意味するなら official oracle だけ `require_all_reps=True` にするか、report で `len(tps)==5` を要求する。5試行中の部分失敗を許す裁定なら、少なくとも成功数＋失敗証拠が5試行を完全被覆することを検査し、採否規則は別途明示する。

### 3. severity: medium — 3×3探索の隔離経路が実装されていない

壊れ方: floor の `pilot` も official と同じ `validate_protocol` を通るため、変更後は extime=3 が拒否されます。reps=3は既に拒否済みです。oracle は pilot/exploration mode 自体を持たず、唯一の full-pipeline 経路が verified manifest を要求します。したがって探索を s8b driver で行えば赤くなり、generic pipeline を使えば official 後処理との隔離保証がありません。

根拠:

- [s8b_floor_campaign.py:2287](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2287)、[同:2983](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:2983) — pilot も同じ validator
- [s8b_oracle_manifest.py:675](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_manifest.py:675) — manifest 発行時点で run contract 検証
- [s8b_oracle_driver.py:1227](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:1227) — oracle に mode 分離なし
- [pipeline.py:88](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:88) — generic PerfConfig は別途利用可能

最小修正案: 3×3探索は明示的な別入口・別 artifact schema/path に限定し、official manifest/report/judge が型・namespaceで拒否する。official validator に `mode=exploration` の bypass を足すのは避ける。

### 4. severity: medium — 新 leaf だけでは単一 authority にならない

壊れ方: protocol builder は引き続き `s8b_approved.APPROVED_REPS` の別 literal を使います。新 leaf が将来変更・訂正されると、builder は旧値を発行し validator が拒否するため全公式生成が停止します。また builder は extime を「自由値」と説明したままなので、利用者が3を指定して初めて拒否されます。

根拠:

- [s8b_approved.py:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_approved.py:27) — 別の `APPROVED_REPS = 5`
- [s8b_floor_campaign.py:330](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:330) — extime を自由値と明記
- [s8b_floor_campaign.py:390](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:390) — builder は `s8b_approved` から reps を発行
- [test_s8b_approved.py:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_approved.py:78) — 同値比較だけで同一源性を証明していない

最小修正案: `s8b_approved.APPROVED_REPS` は新 leaf からの再輸出にし、builder も extime/reps を新 leaf から導出する。引数を残すなら「承認値との一致確認用」と文書化する。validator 内の再 literal 化を殺す静的 driftguard も加える。

### 5. severity: medium — standalone `gate-check` は floor側 pinを実行しない

壊れ方: active v2 generation に旧 extime=3 の floor protocol がある状態で、oracle manifestだけ5×5なら、standalone `gate-check` は allowed を返し得ます。`load_ratified_freeze` は floor protocol を strict parseするだけで数値検証せず、`launch_validate` を呼ばないためです。実際の `run-block` は後で拒否するので誤実走には至りませんが、preflightが偽緑になります。

根拠:

- [s8b_ratified_freeze.py:901](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_ratified_freeze.py:901) — 静的 loader は数値検証をしないと明記
- [s8b_oracle_driver.py:186](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:186)、[同:228](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:228) — gate-check は `load_ratified_freeze` のみ
- [s8b_oracle_driver.py:787](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:787)、[同:844](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:844) — run-block本線は launch validation 後に manifest検証

最小修正案: v2 gate-check でも `launch_validate` または floor protocol の full validation を必須化する。floor=3 / manifest=5 の active fixtureで `allowed=False` を固定する。

### 6. severity: low — standalone floor artifact verifier は extimeを観測しない

壊れ方: 3秒pilotの自己整合 artifactを `verify_floor_artifact` に渡しても、expected/config射影に extimeが存在しないため、統計が一致すれば空エラーを返せます。full `launch_validate` は protocol/run_cmdを別途検査するので本線は安全ですが、このAPI単体を公式検証と解釈できません。

根拠:

- [s8b_floor_contract.py:55](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_contract.py:55) — artifact射影7項に extimeなし
- [s8b_floor_stats.py:403](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_stats.py:403)、[同:434](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_stats.py:434) — verifierの契約にも extimeなし

最小修正案: extime_sとprotocol hashをartifact照合へ含めるか、関数名・文書を「統計内部整合専用」に限定し、公式consumerには必ず `launch_validate` を要求する。

### 7. severity: low — import不変条件とfixture移行が取り残される

壊れ方: `s8b_floor_contract` が新 leaf をimportすると「他campaign moduleを一切loadしない」既存テストが即失敗します。また直接validatorを通るfixtureは想定7ファイルに加え、oracle driver/reportにも1×1・2×1があります。逆に低層helperの3や1まで一括置換すると、探索・汎用APIまで公式pinしたような偽テストになります。

根拠:

- [test_s8b_floor_contract.py:77](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_contract.py:77) — campaign module追加loadを拒否
- [test_s8b_protocol_builder.py:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_protocol_builder.py:43)、[同:132](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_protocol_builder.py:132) — goldenは3、pin mutation表にextimeなし
- [test_s8b_oracle_driver.py:162](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:162) — 1×1 manifest
- [test_s8b_oracle_report.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:85) — 2×1 manifest
- [test_s8b_materialization.py:491](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_materialization.py:491) — validatorを通らない低層assembly test

最小修正案: official validatorを通るfixtureだけ5×5へ更新し、低層command/materializationの任意正整数テストは維持する。leaf importテストは新leafだけを許可し、新leaf自身のstdlib-only性を別テストで固定する。

なお、`run-block` 本線では floor protocol再検証→oracle manifest検証の順序が同一プロセス内で実行されるため、そこでの単純な freeze/run間窓は確認できませんでした。また `s8b_materialization.py` 自体には extime/reps consumerはなく、n_oracle・budget・検定点を追加でpinするscope逸脱も、この3ステップ単体にはありません。
```

## C-B プロンプト (逐語)

```
あなたは独立した敵対的レビュアーです。以下の実装プランの設計欠陥を、repo を実際に読んで検証しながら指摘してください。プランを守る側に回らず、壊れ方を探す側に立ってください。

# 背景 (ユーザー裁定、確定済み)

s8b campaign の oracle report (orchestrator/campaign/s8b_oracle_report.py) には、abort reason の閉表検査が bench-failed 分岐にしかない。裁定により隣接 3 穴の閉鎖が承認された:
- P_timeout_reason: timeout 分岐は reason 非検査 → timeout + `bench-no-throughput` が report を通る (実測)
- P_build_reason: build-failed 分岐も reason 非検査 → build-failed + `trace-timeout` が report を通る (実測)
- P_reason_type_crash: verify-inconclusive 分岐は reason が list 等 unhashable のとき `abort_reason in VERIFY_INCONCLUSIVE_REASONS` で TypeError → report 全体クラッシュ (実測。fail-closed 方向なので正しさ穴ではなく堅牢性欠陥)

併せて公式実験数値 (extime=5 秒 / reps=5) の pin により、テスト fixture の非承認値 (extime=3 等) の更新が必要。

# プラン (この部分を攻める対象)

1. **閉表 leaf 追加** `orchestrator/campaign/s8b_experiment_numbers.py` (新設、stdlib-only) に
   `TIMEOUT_ABORT_REASONS = frozenset({"trace-timeout"})`、
   `BUILD_FAILED_ABORT_REASONS = frozenset({"build-error", "identity-error"})` を追加。
   driver `s8b_oracle_driver.py` の `_outcome_for` (411 行付近) の literal をこの leaf 参照へ置換 (挙動不変)。既存 `s8b_abort_reason_contract.py` の BENCH_FAILED_ABORT_REASONS は既存のまま
2. **report 側** `s8b_oracle_report.py`: timeout / build-failed 分岐に bench-failed (453–462 行付近) と同形の単一連言 (abort 1 件 ∧ payload Mapping ∧ reason が str ∧ 閉表内) を追加。timeout は既存の兼用分岐 (`outcome in {"timeout", "bench-failed"}`、450 行付近) から分離しすぎない最小差分で
3. **verify-inconclusive 分岐** (477–487 行付近): membership 前に `isinstance(reason, str)` を追加。binary-mismatch は `==` 比較でクラッシュ面なし = 触らない
4. **テスト**: leaf の golden literal (数値 + 閉表、leaf 非依存の literal 比較)。floor extime 負例 (3/7 が reject)、oracle manifest extime/reps 負例 (3/999 が reject)、timeout/build-failed の閉表外・欠落・非 str 負例、verify-inconclusive の list reason 無クラッシュ負例。既存 fixture の extime 3→5 更新 (想定 7 ファイル: freeze_io / ratified_freeze / ratified_verify / floor_contract / protocol_builder / oracle_manifest / floor_campaign) + 追加疑い 4 か所 (test_s8b_oracle_report.py:98 の reps=2 extime=1、test_s8b_oracle_driver.py:167 の 1/1、test_s8b_materialization.py:495 の 3/1、test_s8b_floor_campaign.py:636 の 7/4)
5. **変異 matrix 事前登録** (実装後に親が全 KILL を確認する):

   | ID | 変異 | 期待して赤くなるもの |
   |----|------|--------------------|
   | N1 | floor extime pin を _pos_int へ戻す | floor extime 負例 |
   | N2 | manifest extime pin 削除 | manifest extime 負例 |
   | N3 | manifest reps pin 削除 | manifest reps 負例 |
   | N4 | leaf APPROVED_EXTIME_S を 3 へ | golden 数値テスト |
   | N5 | timeout reason 連言削除 | timeout 閉表外負例 |
   | N6 | build-failed reason 連言削除 | build-failed 閉表外負例 |
   | N7 | verify-inconclusive の str guard 削除 | list reason 無クラッシュ負例 |
   | N8 | leaf TIMEOUT 閉表へ偽 reason 追加 | golden 閉表テスト |

# 検証してほしい観点 (これ以外の欠陥発見も歓迎)

1. **timeout 兼用分岐の分離**: 既存 `elif outcome in {"timeout", "bench-failed"}` に timeout 用連言を足すとき、bench-failed 側の既存検査と二重発火・矛盾・取り違えは起きないか。「分離しすぎない最小差分」が具体的にどうあるべきか
2. **閉表の正当性**: driver が実際に生成し得る abort reason の全列挙 (s8b_oracle_driver.py を読む) と、提案閉表 {trace-timeout} / {build-error, identity-error} は過不足なく一致するか。timeout=trace-timeout 1 対 1 は本当か
3. **閉表 leaf の配置**: 数値 leaf (s8b_experiment_numbers.py) に閉表を同居させる設計は妥当か。既存 s8b_abort_reason_contract.py に足す方が一貫するか。issuer/verifier が同一 leaf を参照する契約 (parser 分裂の構造排除) が保たれるか
4. **fixture 更新の全列挙**: extime/reps の非承認値を使う全テスト・fixture 箇所を実際に列挙し (grep)、プランの列挙 (7 ファイル + 4 か所) と突き合わせよ。各箇所が validator 経由 (更新必須) か直接呼び (更新不要の可能性) かを判別せよ
5. **変異 matrix の恒真検査**: N1〜N8 それぞれについて、期待テストが実は赤くならない (恒真 survivor になる) 疑いはないか。特に N5/N6 は分岐の書き方次第で既存負例が別経路で赤くなり検出を偽装しないか
6. **テスト設計の欠落**: 負例の穴 (欠落 field、reason=None、payload 非 Mapping、abort 2 件等)

# 出力形式

所見ごとに: 番号、severity (high/medium/low)、壊れ方の具体シナリオ、根拠 file:line (実際に読んで確認したもの)、最小修正案。所見ゼロならその根拠を列挙。日本語で。
```

## C-B 出力 (逐語)

```
結論は「このまま実装開始は不可」です。閉表の値自体は `_outcome_for` と一致しますが、authority 配置、fixture 更新、変異テストの作り方に欠陥があります。

発行 reason の確認結果は次のとおりです。

| driver outcome | `_outcome_for` が分類する reason |
|---|---|
| build-failed | `build-error`, `identity-error` |
| binary-mismatch | `bench-binary-mismatch` |
| timeout | `trace-timeout` |
| verify-inconclusive | `trace-run-nonzero-exit`, `trace-empty`, `trace-no-abort-counts`, `trace-parse-error`, `verify-competing-tenant` |
| bench-failed | `bench-competing-tenant`, `bench-no-throughput`, `bench-cv-undefined` |

根拠は [s8b_oracle_driver.py:411](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:411) です。したがって、分類器契約としては `{trace-timeout}` / `{build-error, identity-error}` は過不足ありません。timeout と `trace-timeout` は通常 issuer 経路では 1 対 1 です。

ただし `identity-error` は pipeline が `src_token is None` の場合だけ発行しますが、oracle driver は常に確定済み `src_token` を渡します。[pipeline.py:398](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:398)、[s8b_oracle_driver.py:1066](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_driver.py:1066)。つまり production 到達性では余分、classifier/verifier 契約では正当な互換 reason、という位置づけです。

## 所見

1. severity: high — 閉表 leaf の配置が既存契約および repo 内 handoff と矛盾する

壊れ方: 提供プランどおり abort reason を `s8b_experiment_numbers.py` に置くと、bench reason は `s8b_abort_reason_contract.py`、timeout/build reason は数値 leaf、verify reason は report/driver の重複 literal、binary reason は report-local、という四分裂になります。将来の reason 追加時に issuer/verifier の片側だけが更新されます。

既存 module は明示的に「issuer と verifier が同じ leaf を参照し parser 分裂を排除する」ためのものです。[s8b_abort_reason_contract.py:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_abort_reason_contract.py:2)。さらに作業ツリーの未追跡 handoff は、数値だけを experiment leaf に置き、reason は abort contract に追加すると記載しており、提供プランと食い違います。[handoff:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-b004-experiment-numbers.md:22)、[handoff:32](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/docs/handoff/2026-07-19-b004-experiment-numbers.md:32)。

最小修正案: `s8b_experiment_numbers.py` は `APPROVED_EXTIME_S` / `APPROVED_REPS` のみにする。timeout/build の閉表は既存 `s8b_abort_reason_contract.py` に追加し、driver/report の双方がそこを参照する。少なくとも実装前に handoff と確定プランを同期する。可能なら verify-inconclusive と binary-mismatch の reason も同 leaf へ移す。

2. severity: high — 「単一 authority」をテストが証明できず、切断された leaf が全変異を通り得る

壊れ方: floor/oracle validator がそれぞれ literal `5` を使い、新 leaf が誰にも参照されていなくても、N1～N4 と golden literal は通せます。N4 は leaf の値しか検査せず、consumer との辺を検査しません。既存の「single sourced」テストも値の等値比較だけなので、同じ literal の重複を識別できません。[test_s8b_approved.py:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_approved.py:78)。

さらに `s8b_approved.APPROVED_REPS = 5` が残り、builder はそこから reps を発行します。[s8b_approved.py:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_approved.py:27)、[s8b_floor_campaign.py:380](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:380)。`extime_s` も builder の「自由値」と説明されたままです。[s8b_floor_campaign.py:330](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_floor_campaign.py:330)。

また floor contract が新 leaf を import すると、現在の「他の campaign module を一つも load しない」テストは確実に失敗します。[test_s8b_floor_contract.py:77](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_contract.py:77)。

最小修正案:

- `s8b_approved.APPROVED_REPS` を新 leaf からの再輸出にする。
- floor/oracle は module-qualified に同じ leaf を参照する。
- builder の `extime_s` を削除して approved 値を焼くか、少なくとも「自由値」という docstring を撤回する。
- floor leaf import テストは、許される唯一の依存を `campaign.s8b_experiment_numbers` として明示する。
- 「consumer の leaf 参照を literal 5 に戻す」配線変異を追加する。

3. severity: high — fixture 更新は 7 ファイルでは足りず、driver は単純置換するとテスト意図が消える

`rg` と呼出し先を追った分類は以下です。

| 判定 | 場所 | 理由 |
|---|---|---|
| 更新必須 | [test_s8b_floor_contract.py:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_contract.py:39) | `validate_protocol` の基底 fixture |
| 更新必須 | [test_s8b_floor_campaign.py:163](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:163)、[:275](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:275) | protocol と記録 run command を一致させる必要がある |
| 更新必須 | [test_s8b_freeze_io.py:234](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_freeze_io.py:234) | 後段で `run_campaign` → validator |
| 更新必須 | [test_s8b_ratified_freeze.py:279](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:279)、[:374](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_freeze.py:374) | protocol validator と run command の双方 |
| 更新必須 | [test_s8b_ratified_verify.py:386](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_ratified_verify.py:386) | 直接 `validate_protocol` |
| 更新必須 | [test_s8b_protocol_builder.py:43](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_protocol_builder.py:43)、[:53](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_protocol_builder.py:53)、[:62](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_protocol_builder.py:62) | `_G_EXTIME`、golden bytes、golden SHA の直書き |
| 更新必須 | [test_s8b_oracle_manifest.py:83](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_manifest.py:83)、[:216](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_manifest.py:216)、[:516](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_manifest.py:516) | `build_manifest` / `_validate_run_contract` |
| 更新必須 | [test_s8b_oracle_report.py:85](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:85) | `_manifest()` が `build_manifest()` を通るため 2/1 は拒否される |
| 更新必須 | [test_s8b_oracle_driver.py:137](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:137) | `_write_manifest()` が `build_manifest()` を通るため 1/1 は拒否される |
| 据置 | [test_s8b_materialization.py:491](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_materialization.py:491) | 純粋な `assemble_manifest()` 直接試験。validator 非経由 |
| 据置 | [test_s8b_floor_campaign.py:629](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:629) | 7/4 は予約式の純粋算術試験 |
| 据置 | [test_s8b_floor_contract.py:173](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_contract.py:173) | 3/1 は portable command 単体試験 |
| 据置 | [test_s8b_protocol_builder.py:132](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_protocol_builder.py:132)、[test_s8b_floor_campaign.py:770](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_floor_campaign.py:770) | reps=4/3 は意図的な pin 負例 |

したがって更新必須は「7 ファイル + oracle_report + oracle_driver」の9ファイルです。

driver は 1×1 から 5×5 になるため、予約量は行数ではなく `25 * 行数` になります。現在の期待値は行数だけです。[test_s8b_oracle_driver.py:869](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:869)、[:998](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:998)。また `bench_wall_s=1.5` は新しい per-row 枠 25 秒を超えないため、予約超過テストが発火しなくなります。[test_s8b_oracle_driver.py:1004](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_driver.py:1004)。

最小修正案: 予約期待値を `25 * len(rows)` にし、超過 fixture を例えば 26 秒へ変更してコメントも更新する。materialization の 3/1 と予約式の 7/4 は変更しない。protocol builder の SHA は extime byte だけを 3→5 にした場合 `03b7393a00f4e161475fa7142e0c4ed58a4d83d46bd653d3133a6de5b5bd3f9f` になります。

4. severity: high — N5/N6/N7 は既存 helper の使い方次第で survivor になる

壊れ方: 現在の `_trial()` は build/timeout/verify-inconclusive reason を内部で固定発行し、payload 注入点は bench-failed にしかありません。[test_s8b_oracle_report.py:151](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:151)。

新しい負例を「既存 `_trial()` の後に別 abort を append」して作ると abort が2件になります。report は reason 検査より前に terminal 重複で拒否します。[s8b_oracle_report.py:427](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:427)。その結果:

- N5/N6で reason 連言を削除しても重複 abort で拒否され、テストは緑のまま。
- N7では `len(abort_records) != 1` のため `abort_reason=None` になり、list membership 自体が発火せず、guard 削除 mutant が生存。

最小修正案: `_trial(..., abort_payload=...)` のような全 outcome 共通注入点を追加し、「既定 abort を置換」させる。各負例で abort が正確に1件であること、違反理由が `abort reason 証拠` であり `terminal event 重複` ではないことを確認する。

変異判定は次の条件付きです。

| ID | 判定 |
|---|---|
| N1 | 3/7 を別々の valid-base mutation にすれば kill |
| N2/N3 | 必ず別テストにする。extime=3 と reps=999 を同時に壊すと、片方の pin 削除をもう片方が拒否して survivor |
| N4 | exact literal golden なら kill。ただし consumer 配線は証明しない |
| N5/N6 | sole abort の reason 置換なら kill。追記方式では survivor |
| N7 | sole abort の list reason を返し、protocol_violation を確認すれば kill |
| N8 | exact frozenset 比較なら kill。ただし report/driver が leaf を使うことまでは証明しない |

5. severity: medium — 正しい reason さえあれば producer 不可能な履歴を受理する

壊れ方: 提案した reason 連言を追加しても、次の forged WAL は受理されます。

- `build_start → verify_done(pass) → abort(build-error)` を `build-failed` と宣言。
- `build_done → legacy pass → s2 pass → bench_done → abort(trace-timeout)` を `timeout` と宣言。

現行 `_assess_window()` への in-memory レコード投入で、前者は `legacy_verify=pass`、後者は bench 値付きのまま、双方 `status=completed` を再現しました。build 分岐は build_done/abort/commit の件数しか見ず、timeout 分岐は abort/commit しか見ていません。[s8b_oracle_report.py:446](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:446)。

実 producer では trace-timeout は verify 中にしか起きず、payload に workload tag も載ります。[pipeline.py:494](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/pipeline.py:494)。

最小修正案:

- build-failed: `build_done=0`、verify は両方 missing、bench 無し。
- timeout: `build_done=1`、bench 無し、red 無し、少なくとも対象 verify が missing。
- `abort.payload.workload.tag` を legacy/s2 に限定し、tag と verify 状態を対応させる。
- bench-failed も `build_done=1`、bench_done 無しを明示する。

失敗 outcome なので直接 false-green にはなりませんが、report が証拠 truth table を検証するという契約は破れています。

6. severity: medium — abort payload だけ直しても report の非 Mapping クラッシュは残る

壊れ方: `build_start.payload=[]` は `build.payload.get(...)`、`bench_done.payload=[]` は `payload.get("tps")` で `AttributeError` になります。双方とも in-memory `_assess_window()` で再現しました。[s8b_oracle_report.py:388](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:388)、[:413](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:413)。

CLI の例外捕捉にも `AttributeError` はありません。[s8b_oracle_report.py:750](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/campaign/s8b_oracle_report.py:750)。

最小修正案: abort だけでなく、全 `PIPELINE_STAGES` record に対して payload が `Mapping` であることを先に検査し、非 Mapping は row-level `protocol_violation` にする。単に CLI で `AttributeError` を捕捉するだけでは、全 report が落ちる問題を隠すだけです。

7. severity: medium — timeout 兼用分岐の安全な最小形と positive coverage がプラン上未確定

壊れ方: timeout の検査を共有分岐へ無条件に置くと、bench-failed が timeout 閉表でも検査されて全拒否になります。逆に分岐を完全複製すると共通 terminal 条件が将来 drift します。

最小修正案は、共通 terminal 条件を維持したまま outcome から閉表を一意選択する形です。

```python
elif outcome in {"timeout", "bench-failed"}:
    if not (counts["abort"] == 1 and counts["commit"] == 0):
        issues.append(...)

    allowed_reasons = {
        "timeout": _abort_reason_contract.TIMEOUT_ABORT_REASONS,
        "bench-failed": _abort_reason_contract.BENCH_FAILED_ABORT_REASONS,
    }[outcome]
    if not (
        len(abort_records) == 1
        and isinstance(abort_records[0].payload, Mapping)
        and isinstance(abort_records[0].payload.get("reason"), str)
        and abort_records[0].payload.get("reason") in allowed_reasons
    ):
        issues.append(...)

    if outcome == "bench-failed":
        # 既存 verify pass 条件
```

これなら二重発火はありません。build-failed は既存の独立枝に同形の reason 連言を置けます。

テストは負例だけでなく、timeout の1 reasonと build-failed の2 reasonすべての正例が必要です。現在の正例 fixture は build-error しか発行しないため、report が誤って `identity-error` を拒否しても検出できません。[test_s8b_oracle_report.py:166](/home/SFC/tanab/github/izanagi/.claude/worktrees/s8b-c22-launch-cert/orchestrator/tests/test_s8b_oracle_report.py:166)。

最低限、各 outcome について「閉表外、reason 欠落、None、空文字、payload 非 Mapping、list/dict reason」を sole-abort で試し、duplicate abort は共通 terminal 検査のテストとして別に保つべきです。
```

## 実行・レビュー・fix (標準ループ後半) の記録

- 実行: codex exec (gpt-5.6-sol, reasoning=high, workspace-write) 並列 2 単位。
  E1 = 数値 pin @ worktree b004-e1 (targeted 448 passed)、E2 = 閉表 + report @ b004-e2
  (targeted 106 passed)。git commit は親が統合側で実施 (exec 子は commit しない運用)
- レビュー: codex 並列 2 本 (gpt-5.6-sol high)。E2 所見 1 (med real: verify-inconclusive 正例
  1/5)、E1 所見 3 (med real 2: floor reps re-literal 変異が生存 / s8b_approved 再輸出の等値
  テスト恒真、low 1: 全走 fail 数の固定値報告)。全 real、fix を codex へ再投 (medium) → 全解消
- golden SHA 三重独立一致: 相談 B 予測 = E1 実 serializer 再計算 = E1 レビュアー独立再構成
  (03b7393a00f4e161475fa7142e0c4ed58a4d83d46bd653d3133a6de5b5bd3f9f、旧版との差は offset 321 の
  extime_s 3→5 の 1 byte)

## 変異 matrix v2 実測 (B-057。事前登録 12 + レビュー起因 2)

N1〜N14 **全 KILLED / survivor 0** (harness = mutation_gate_b004.py、PYTHONDONTWRITEBYTECODE=1、
各変異で復元後 green 確認)。killer は全変異で事前登録どおりの期待テスト (N5 は timeout 閉表外
負例 — terminal 重複でない、N9 は timeout 正例、N10〜N13 は monkeypatch 配線テスト、N14 は
subprocess 伝播テスト)。レビュー起因 N13/N14 は fix 前は実測 survivor (E1 レビュー所見 1・2) で、
fix 後に KILL — 「0-findings は変異で裏取りするまで緑と数えない」の再実証

## B-056 coverage 観測 (final、gate にしない)

floor_contract 85% / oracle_manifest 83% / oracle_report 78% / oracle_driver 83% /
experiment_numbers 100% / abort_reason_contract 100% (baseline 86/83/78/83 — 分岐追加に
テストが追随し同水準)

## 受入実測 (統合 branch approved-waves) と flake 真因

- E1+E2+fix 統合後の全走で `test_real_repo_serialization.py::
  test_protocol_builder_repo_tree_guard_is_wired_to_real_root` が間欠赤 (2/3) →
  真因 = **D63 の REAL_REPO_SERIAL_NODES 列挙漏れ**。この meta-テスト自身が実 ROOT で
  builder を実走し repo tree snapshot を取る reader なのに直列 group 外で、writer
  (test_p3_s4_loop 系の ccbench patch 窓) と並走し得た。E1/E2 のテスト追加 (~30 node) で
  xdist 分配が変わり潜在穴が顕在化 (baseline の連続緑は分配の偶然)
- 修正 = conftest 正本 + 独立 golden の両側へ node 追加 (片側のみの変更は監査テストが実測で
  検出 — 恒真化防止の二重台帳が設計どおり機能)
- 修正後 **全走 7 連続緑 (2019 passed / 19 skipped)**。failing node ID はログ保存
  (fullrun_*.log、worklog (8) 異常 (ii) の教訓を適用)

## E1 実行報告 (逐語)

```
実装完了。commit は作らず、変更を worktree に残しています。

### 変更ファイル

Campaign:

- [s8b_experiment_numbers.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/campaign/s8b_experiment_numbers.py)
- [s8b_floor_contract.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/campaign/s8b_floor_contract.py)
- [s8b_approved.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/campaign/s8b_approved.py)
- [s8b_floor_campaign.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/campaign/s8b_floor_campaign.py)
- [s8b_oracle_manifest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/campaign/s8b_oracle_manifest.py)

Tests:

- [test_s8b_experiment_numbers.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_experiment_numbers.py)
- [test_s8b_floor_contract.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_floor_contract.py)
- [test_s8b_approved.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_approved.py)
- [test_s8b_oracle_manifest.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_oracle_manifest.py)
- [test_s8b_protocol_builder.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_protocol_builder.py)
- [test_s8b_freeze_io.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_freeze_io.py)
- [test_s8b_ratified_freeze.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_ratified_freeze.py)
- [test_s8b_ratified_verify.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_ratified_verify.py)
- [test_s8b_floor_campaign.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_floor_campaign.py)

### 実装結果

- 公式値 `extime=5 / reps=5` の stdlib-only leaf を新設。
- floor/oracle 両 validator を module-qualified leaf 参照へ結合。
- `s8b_approved` から両値を重複 literal なしで再輸出。
- builder docstring、validator 経由 fixture、run command、予約時間 golden を更新。
- protocol golden SHA を実 serializer から再計算:
  `03b7393a00f4e161475fa7142e0c4ed58a4d83d46bd653d3133a6de5b5bd3f9f`
- golden、leaf 性、monkeypatch 配線、独立した負例を追加。
- 指定された据置値と E2 編集禁止ファイルは未変更。

### テスト結果

- 指定 targeted suite: `448 passed / 2 skipped`
- 補助検査: `14 passed`
- `check_codex_agents.py`: OK
- `check_docs.py`: OK
- `git diff --check`: OK
- 全走: `1907 passed / 21 skipped / 92 failed`

全走の失敗は主に、編集禁止の E2 oracle driver/report fixture が新しい 5/5 pin に未追随なことによる連鎖です。ほかに read-only submodule の復元失敗と並列 `__pycache__` copy race を各1件観測しました。テストが汚した submodule は clean に復旧済みです。

逸脱提案: なし。

隣接問題: 親統合時に E2 側 fixture 更新を取り込まない限り、全走は緑になりません。
```

## E2 実行報告 (逐語)

```
実装完了です。指定5ファイルのみ変更し、コミットは作成していません。

変更ファイル:

- [s8b_abort_reason_contract.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e2/orchestrator/campaign/s8b_abort_reason_contract.py:1)
  - timeout / build-failed / verify-inconclusive の閉表を追加
  - `identity-error` の現行発行経路について docstring に明記
- [s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e2/orchestrator/campaign/s8b_oracle_driver.py:411)
  - `_outcome_for` の分類 literal を共有 leaf 参照へ置換。挙動は不変
- [s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e2/orchestrator/campaign/s8b_oracle_report.py:442)
  - timeout / bench-failed の閉表検査を共通化
  - build-failed に sole-abort 閉表検査を追加
  - verify-inconclusive の reason 型検査を追加し、unhashable 値のクラッシュを防止
  - binary-mismatch 等の対象外分岐は未変更
- [test_s8b_oracle_report.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e2/orchestrator/tests/test_s8b_oracle_report.py:152)
  - 全 abort outcome 共通の payload 差し替え注入点を追加
  - 指定された sole-abort 負例、全閉表 golden、`identity-error` 正例を追加
  - manifest fixture を reps/extime = 5/5 に更新
- [test_s8b_oracle_driver.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e2/orchestrator/tests/test_s8b_oracle_driver.py:162)
  - manifest fixture を 5/5、予約期待値を `25×行数` へ更新
  - 予約超過 fixture を 26秒へ更新

テスト結果:

- 対象テスト: **106 passed, 1 skipped**
- 全走: **2000 passed, 21 skipped, 1 failed**
  - 唯一の失敗は `test_drive_iteration_checkpoint_survives_across_calls`
  - Codex sandbox で submodule gitdir が read-only のため、後処理の `git checkout -- .` が `index.lock` を作れず失敗
  - テストが残した submodule 2ファイルの差分は逆適用し、submodule は clean に復旧済み
- `check_codex_agents.py`: OK
- `check_docs.py`: 違反なし
- `git diff --check`: OK

逸脱提案: なし。

隣接問題: 上記 real-repo テストは read-only submodule gitdir の Codex 環境では完走不能です。製品コードの変更は行っていません。
```

## E1 レビュー出力 (逐語)

```
レビュー結果は medium 2件、low 1件です。製品実装そのものの pin 配線は現時点では正しく、主な欠陥は mutation guard の不足です。

1. severity: medium — floor の `reps` 再リテラル化をテストが検出できない

壊れ方: floor validator の `_experiment_numbers.APPROVED_REPS` を literal `5` に戻すと、将来 leaf が変更された際に oracle と floor の authority が分裂します。しかし monkeypatch 配線テストは floor の `extime`、oracle の `extime/reps` しかなく、floor の `reps` edge がありません。

根拠:

- 現実装の正しい module-qualified 参照: [s8b_floor_contract.py:170](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/campaign/s8b_floor_contract.py:170)
- floor は extime のみ monkeypatch: [test_s8b_experiment_numbers.py:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_experiment_numbers.py:87)
- oracle は extime/reps の両方: [test_s8b_experiment_numbers.py:99](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_experiment_numbers.py:99)

実測: floor の reps 参照だけを literal `5` に置換した in-memory mutant に対し、新設ファイルの全5テストは `5 passed`。つまり当該変異は生存します。

最小修正案: `test_floor_validator_reads_reps_pin_from_leaf` を追加し、leaf reps を7に変更した状態で floor が reps=7を受理し、reps=5を拒否することを確認する。

2. severity: medium — `s8b_approved` の「single sourced」テストが literal 再導入に対して恒真

壊れ方: `s8b_approved.APPROVED_EXTIME_S` と `APPROVED_REPS` を literal `5` に戻しても、現在値が5である間は equality テストが通ります。将来 leaf が変更されると、builder は stale な reps を生成し、validator と自己不整合になります。

根拠:

- 現実装は正しく leaf から再輸出: [s8b_approved.py:27](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/campaign/s8b_approved.py:27)
- テストは値の等価性しか確認しない: [test_s8b_approved.py:93](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_approved.py:93)
- builder は再輸出値を使用: [s8b_floor_campaign.py:392](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/campaign/s8b_floor_campaign.py:392)

実測: 上記2代入を literal `5` にした mutant でも、`test_experiment_numbers_are_single_sourced_from_leaf` は `1 passed`。

一方、現実装については fresh interpreter で leaf を7にしてから各 module を import すると、approved、campaign、floor、oracle の全てが7に追随しました。現在の配線自体は正しいです。

最小修正案: fresh subprocess 内で leaf を7へ変更してから `s8b_approved` と consumer を importし、再輸出値と campaign の reps が7になるテストを追加する。これなら literal 再導入を殺せます。

3. severity: low — 「全走92 fail」という実装報告は再現しない

壊れ方: 固定の失敗数を根拠にすると、非決定的な infra failure と fixture failure の増減により、E1由来の新規失敗が紛れても見落とす可能性があります。

実測:

- 全走: `90 failed, 1909 passed, 21 skipped`
- E2範囲の旧 fixture 連鎖: 89件
  - `test_s8b_binding_driftguards.py`: 2件
  - `test_s8b_oracle_driver.py`: 44件
  - `test_s8b_oracle_report.py`: 43件
- submodule read-only `index.lock`: 1件
- `__pycache__` race: 0件

fixture は実際には driver が reps/extime=`1/1`: [test_s8b_oracle_driver.py:165](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_oracle_driver.py:165)、report が `2/1`: [test_s8b_oracle_report.py:95](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_oracle_report.py:95) で、すべて新しい manifest pin で先行拒否されていました。これは明示されたE2 scope外と整合し、E1自身の失敗は確認されませんでした。

最小修正案: 報告には固定総数ではなく、実行コマンド、ファイル別件数、決定的fixture失敗と非決定的infra失敗を分離して記録する。

その他の確認結果:

- 対象9ファイル: 実測 `448 passed, 2 skipped`
- 負例は別検査でなく意図した pin が発火:
  - floor extime=3/7 → `protocol.extime_s が承認凍結値と不一致`
  - oracle extime=3 → `run_contract.extime が承認凍結値でない`
  - oracle reps=999 → `run_contract.reps が承認凍結値でない`
- golden SHA: 独立に18-key文書を標準JSONで再構成し、`03b7393a00f4e161475fa7142e0c4ed58a4d83d46bd653d3133a6de5b5bd3f9f` と一致。
- golden bytes は775 bytesで、旧版との差は offset 321 の `extime_s: 3→5` の1 byteだけ。
- leaf は import なし、floor contract は stdlib + `campaign.s8b_experiment_numbers` のみ。循環importなし。
- 公式S8b文脈の製品コードで値 literal `5` が残るのは新leafの2定数だけ。
- materialization、指定された純算術・負例・portable command、E2製品/テストには差分なし。
- 全走が一時的に汚した submodule 2ファイルはHEADへ復元済みで、最終 `git status` はレビュー開始時のE1差分と一致しています。
```

## E2 レビュー出力 (逐語)

```
1. **medium — verify-inconclusive 閉表の正例が 5 件中 1 件しかない**

   - 壊れ方: report が将来 `trace-empty` だけを受理するよう誤って変更されても、正例テストは通過し得ます。`trace-run-nonzero-exit`、`trace-no-abort-counts`、`trace-parse-error`、`verify-competing-tenant` の正当な WAL が `protocol_violation` になる回帰を検出できません。
   - 根拠: 閉表は 5 値です（[s8b_abort_reason_contract.py:18](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e2/orchestrator/campaign/s8b_abort_reason_contract.py:18)）。しかし明示的な正例パラメータは timeout/build-failed だけで、verify-inconclusive がありません（[test_s8b_oracle_report.py:386](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e2/orchestrator/tests/test_s8b_oracle_report.py:386)）。既存の共通 outcome テストが間接的に通すのも `trace-empty` のみです（[test_s8b_oracle_report.py:188](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e2/orchestrator/tests/test_s8b_oracle_report.py:188)）。
   - 最小修正案: `test_terminal_outcomes_accept_closed_abort_reason` に verify-inconclusive の 5 reason をすべて追加する。

実測・その他の確認結果:

- 追加・更新された負例 13 件はすべて sole-abort。専用 violation 文言まで assertion しており、実測でも reason 連言の文言で失敗しました。terminal 重複や counts 不一致による恒真化はありません。
- 対象テスト: `106 passed, 1 skipped`。報告の 106 passed は再現しました。
- 全走: `2000 passed, 21 skipped, 1 failed`。唯一の failure は `.git/worktrees/.../modules/external/ccbench/index.lock` が read-only で作れない既知の submodule revert failureで、報告どおりです。
- `_outcome_for` は旧 literal 全値について同じ outcome を返すことを実測。未知 reason も引き続き `_UnknownAbortReason` です。
- E2 の manifest fixture は driver/report とも 5/5。E1 担当ファイルへの差分はなく、binary-mismatch も不変です。
- 全走が一時的に残した submodule 2 ファイルの変更は、テスト前の HEAD 内容へ復旧済みです。現在の未コミット差分は元の 5 ファイルだけです。
```

## E1 fix 報告 (逐語)

```
最小修正を実装しました。

追加テスト:

- `test_floor_validator_reads_reps_pin_from_leaf`
  - leaf の `APPROVED_REPS=7` に追随
  - `reps=7` を受理、`reps=5` を拒否
- `test_approved_reexports_read_pins_from_leaf_on_import`
  - fresh interpreter で leaf を先に変更
  - `s8b_approved` の再輸出値が reps/extime ともに `7` へ追随

変更先: [test_s8b_experiment_numbers.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/b004-e1/orchestrator/tests/test_s8b_experiment_numbers.py)

テスト結果:

```text
26 passed in 1.77s
```

追加検査も成功:

```text
check_codex_agents.py: OK
check_docs.py: 違反なし
git diff --check: OK
```

コミットは作成していません。
```

## E2 fix 報告 (逐語)

```
`test_terminal_outcomes_accept_closed_abort_reason` に以下の verify-inconclusive 正例を追加しました。

- `trace-run-nonzero-exit`
- `trace-empty`
- `trace-no-abort-counts`
- `trace-parse-error`
- `verify-competing-tenant`

既存 fixture により s2 verify 証拠が missing の WAL 形です。timeout/build-failed param は未変更です。

テスト結果:

```text
60 passed in 1.68s
```

`check_codex_agents.py`、`check_docs.py`、`git diff --check` も成功しました。コミットは作成していません。
```
