単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate

## 必読事項の射影

次の絶対パスだけを読む。**この節が列挙した file を読めなければ即停止する** (停止規則の射程は
この射影 file に限る。ここに無い path の不在は停止理由にしない)。

- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/applied.patch — **今回の実装差分 (レビュー対象)**
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/ruling-stage4.md — 親の裁定 (仕様の正本)
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D191.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D218.md
- /home/SFC/tanab/.claude/jobs/bf1ecf0e/tmp/verbatim-D155.md
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/cli.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrator/schema_v2.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/campaign/env_contract.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/campaign/execution_guard.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/tests/test_calibrator_certify.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/tests/test_effective_clock_policy.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/tests/test_pegasus_calibration_workload.py
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t559-preclock-publish-gate/orchestrator/calibrate.py

## 役割

**レンズ B = テストの検出力と波及。** 実装を守らない。
「緑なのに守れていない」「壊れているのに誰も気づかない」箇所を探す。

## 攻撃してほしい点

1. **テストの弱体化。** 実装子は既存 fixture・既存期待値を変えないと約束した。
   差分を読み、**既存テストの期待値・fixture・helper が実際に変わっていないか**を確かめよ。
   変わっているものがあれば file:line で名指しせよ。定数
   `_EARLY_CLOCK_NOT_EVALUATED` への 1 項目追加だけが許された変更である。
2. **新設テストの検出力。** 新設 3 test (`test_cli_pre_post_clock_rejects_high_outlier`、
   `test_cli_pre_post_clock_accepts_using_dynamic_pre`、
   `test_cli_pre_post_clock_rejection_mechanisms`) の各 assertion について、
   **どの実装欠陥を検出し、どれを検出しないか**を表にせよ。
   とくに「監視 wrapper が実物へ委譲している」ことを確かめ、
   機構を通らないまま緑になる経路がないかを見よ。
3. **monkeypatch の位置。** 差分は `cli.effective_clock_comparison_passes` を
   監視 wrapper へ差し替え、`cli.effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT` を
   benchmark 中に書き換える。この 2 つは
   **検査対象の機構を構成する呼び出しの差し替え**か、
   **その外側の既存定型 seam / 実物へ委譲する観測 wrapper** か。
   前者なら機構を通らない緑を作っていないかを具体的に示せ。
4. **波及。** 変更した production symbol
   (`_EARLY_CLOCK_REJECTION_NOT_EVALUATED` の内容、`_certify_main` の新ハンク) を
   参照する consumer を、**名前の推測でなく参照関係で**列挙せよ。射影に含まれる
   `orchestrator/calibrate.py`、`test_effective_clock_policy.py`、
   `test_pegasus_calibration_workload.py` の期待値が壊れないかを確かめよ。
5. **凍結 bytes と pin。** `orchestrator/campaign/env_contract.py` が束縛する登録済み較正 2 件と、
   それらの sha256 pin に、この差分が波及するかを実コードで確かめよ。
   波及しないと言えるなら、その根拠を file:line で示せ。言えないなら何が未確認かを書け。
6. **schema。** sidecar は `attempts/<job>/effective-clock-pre-post-comparison.json` に置かれる。
   この path を読む既存 consumer はいるか。attempt staging 全体を publish・複製・参照する
   経路はあるか。`schema_v2.py` の検証対象に入るか。
7. **名乗り。** 親は次の限定文を成果物へ書くと裁定した。この文は実装と**過不足なく**一致するか。
   強すぎる語、弱すぎる語、事実と違う語を指摘せよ。

   > 本 gate は、CLI が benchmark 直後に取得した post clock と凍結 pre profile の canonical 照合を
   > publish 前に課す。benchmark **中**に帯外へ振れて post 観測までに戻った変動は検出しない。
   > CLI 終了後に外側 wrapper が撮る `attestation-post.json` は本 gate の検査対象外であり、
   > その窓は残る。probe の観測者効果 (F108) は是正しない。

## 禁止

- file の作成・編集・削除、commit、git の状態変更。
- scope を広げる提案。必要と判断したら **裁定パッケージ候補**として
  「scope 外だが real」と明記して返す。
- 仮想リスク向けの防壁の新設提案。

## 実行環境

sandbox は read-only で書込可能 tmp が無い。**pytest を実走しなくてよい。静的検査でよい。**
走らせていないものを緑と書かない。予算が尽きそうなら途中までの結論を出力形式どおり書いて終わる。

## 出力形式

H2 見出しだけを使う。所見ごとに「real / 疑わしい」「must-fix / nit」「根拠の file:line」を書く。
must-fix には、放置したとき成果物 (certified 選択・レポート・台帳) の値・受理集合・参照が
どう変わるかを 1 行で書く。書けないものは must-fix にしない。最後に必ず次の節を置く。

## 総括

- must-fix を 3 件まで、各 2 行以内。
- 検出力が不足している assertion。
- このまま land してよいか (yes / 条件付き / no)。
