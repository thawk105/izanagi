単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s4-adjudication.md

## 前提 (read-only)

**書込可能な tmp が無いため pytest 緑を要求しない。静的検査でよい。** テスト実測は親が行う。
**file を書けないので、成果はすべて最終メッセージ本文に全文で書け。** 途中で予算が尽きそうなら、
そこまでの結論を出力形式どおり書いて終われ。無出力が最悪である。

## 必読事項の射影

作業 repository は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-c1b-review`
(detached HEAD、commit `d52b2f833`) である。すべてこの worktree の中で読む。
**読めなければ即停止**し、読めなかった path を報告して終われ。

1. `<repo>/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md` — **契約の正本**
2. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s4-adjudication.md` — 親の段 4 裁定と変異事前登録
3. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s1-brief.md` — 親 brief (5 節の不変条件)
4. `/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/refs/decisions-verbatim.md` — D1113 / D1341 / D1522

審査対象は commit `d03b26773` と `d52b2f833` の 2 本 (`git log -2 -p` で読める)。
変更 file は次の 9 本である。

- 新設: `orchestrator/campaign/s8b_terminal_evidence.py`、`orchestrator/tests/test_s8b_terminal_evidence.py`
- 改修: `orchestrator/campaign/attempt_registry_core.py`、`s8b_attempt_profile.py`、`s8b_attempt_registry.py`、
  `s8b_floor_attempt_launcher.py`、`orchestrator/tests/test_attempt_registry_core_s8b_profile.py`、
  `test_s8b_attempt_registry.py`、`test_s8b_floor_attempt_launcher.py`

## レンズ A — 正しさ防壁と capability 境界は本当に発火するか

**あなたの役割は「この機構が守ると称するものを、実際には守れていない箇所」を見つけることである。**
契約への字面の適合ではなく、**発火するか**を見る (レンズ B が字面の適合を担当する)。

契約 0 節が守ると宣言しているのは 1 つだけである — **「試行 proof chain に虚偽の terminal 事実が
入ること」を塞ぐ。** 正当な予約・分類・観測開始までを通常経路で作り、terminal builder だけが
任意の出力 bytes・状態・digest・主値・測り直し理由を返す攻撃を止められるか。

次を順に攻撃せよ。

1. **恒真な gate。** 追加された検査のうち、述語が候補集合に含意されていて常に真 (または常に偽) に
   なるものはないか。**特に `not-consumed` 枝と `terminal-failure` 枝**は、契約 5.1.1 / 5.3 が
   「恒真になりやすい」と名指ししている。置かれた正例が本当に**同じ枝**を通っているか確かめよ。
2. **冗長 gate による見かけの kill。** 親は変異 S1・S2・M1〜M12 を事前登録した。各変異について
   「同じ入力を拒否する層が前後にも内側にも無い」か。**前段の gate が先に拒否していて、
   実装子が数えた kill が実は別の層の赤である**箇所を探せ。
3. **capability の偽造経路。** `ValidatedTerminalEvidence` を adapter の私有 issuer を通さずに
   構築できる経路はないか。`require_sealed_terminal_evidence` の `_issuer_token` 検査は
   `type(...) is object` であり、素の `object()` なら誰でも作れる。**契約 6.4 は
   「reflection 操作」「private issuer の意図的な直接呼出し」を脅威から除外している**ので、
   除外の範囲内かどうかを判定し、**除外の外にある経路だけを所見にせよ。**
   特に「誤った production caller」(契約 6.4 が脅威に**含める**と明記) から到達できるかを見よ。
4. **test seam。** `_launch_floor_attempt_for_test()` に fake registry を注入して
   validated capability を得られないか。契約 6.2 は「adapter を経由させるだけでは塞がらない」と
   書いている。現行の handle 機構 (`_new_handle` / `_require_handle`) と同等の 5 点照合が
   効いているか。
5. **呼び手が値を選べる面 (D1113)。** 契約 1.2 の表と 1.5 (a) が「再導出して等値束縛する」と
   定めた field のうち、実装が**呼び手の与えた値をそのまま権威にしている**ものはないか。
   特に `records` / `threads` / `workload` / `cell_id` / `attempt_id` を durable claim から
   再照合しているか、`duration_s` と `finished_at` が terminal builder の選択値になっていないか。
6. **crash 後の権威 (契約 7)。** 行と file の全件等値 11 項目が実際に照合されているか。
   **`finished_at` が抜けると file 据え置きで行の時刻だけ改竄できる。**
   no-follow regular file の読み、filename・bytes digest・exact keys・canonical bytes・
   attempt binding の検査が root lock 下で行われているか。row あり file なしが拒否されるか。
7. **観測者効果と規律 2。** 追加されたどの検査も、既存の anomaly 検出を緩めていないか。
   v1 の受理集合が 1 bit も変わっていないか (event key 集合 exact 24、retryable reason 集合 空、
   `failure_reason` と classification の等値、observed / terminal-failure / rejection の既存行列)。

## 出力形式

節見出しはすべて `##` で統一する。所見ごとに次の 5 点を書く。

- (a) 所見の一文要約
- (b) **現物の file:line** (推測でなく読んだ行)
- (c) 失敗シナリオ — 具体的な入力・状態から、どういう誤った受理または見逃しに至るか
- (d) 修正案 (実装しない。方向だけ)
- (e) **重大度** — `blocker` (虚偽の terminal 事実が通る / 既存防壁が緩む) /
  `must-fix` (成果物の値・受理集合・参照が変わる) / `nit` (それ以外)

最後に `## 総括` を置き、次を書く。

- 判定: `yes` (この実装で契約 0 節の穴は塞がっている) または `no`
- blocker / must-fix / nit の件数
- **攻撃したが破れなかった箇所**も明記する (破れなかったこと自体が証拠になる)

## 制約

- 出力へ結合文字 U+0300〜U+036F を使わない。
- **`IZANAGI_RUN_GROWTH_HELD_TESTS` を設定して hold を解除するな。**
- 実装・編集・commit をしない。
