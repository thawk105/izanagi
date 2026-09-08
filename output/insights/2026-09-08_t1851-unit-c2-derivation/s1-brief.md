# [T-1851] 単位 C2 — 段 1 brief

base `0cb90c592` (継承 tip `ebbae72ba` + local main 固定 SHA `cc9bba523` の merge)。
branch `worktree-dev-wave-t1851-unit-c2`。**land しない (D1341)。**

## 1. 研究前進

**土台。** 止めている研究は床値 (floor) campaign の certified 選択に試行台帳の proof chain を
束ねること (D1194 の前向き束縛)。D1661 が「単位 C = 起動層の実際の呼び手を台帳へ繋ぐ が主経路」と
書いている。C2 は、その呼び手が要求する値を実環境の campaign 側が実際に作れる状態にする段である。
**完了判定:** campaign の `exec_failures` が自然文 notes の regex ではなく構造化 field から導かれ、
rep observation が 7 key になり、その実値域を実 campaign 経路の実測として記録できていること。

## 2. scope の正本

`output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md` の 3 節・9 節。
C1b が射程外に切った 4 点:

1. runner の構造化 `execution_failure`
2. campaign の算出変更
3. rep observation の 6 key → 7 key 化とそれに伴う凍結 gate の pin 閉包
4. `launch_floor_attempt()` の実環境値域の供給

## 3. 確定済みユーザー裁定

- **land しない (D1341)。** 6 単位が揃うまで branch 上の checkpoint に留める。
- **D1703:** 単位 C の未裁定持ち越しは、単位が揃って land するまで個別に裁定しない。
  本 brief はそれらのいずれも前提にしない。
- **D1661:** journal の TOCTOU 窓は閉じない。閉じるなら単位 C か D2 へ同梱する形が自然、
  とだけ書かれている。**本 wave では閉じない** (再訪条件の実例 1 件が未観測)。
- **契約 3 節:** 「契約を現行の notes regex 算出に合わせる」案は却下済み。自然文を信頼経路に残さない。

## 4. 段 1 で実測した前提 (base `0cb90c592`)

| 対象 | 実測 | 出所 |
|---|---|---|
| runner の rep 実行例外捕捉 | **4 箇所**。`n_exec_fail += 1` と自然文 note の append で閉じる | `orchestrator/calibrator/runner.py:965`、`:978`、`:1170`、`:1184` |
| runner の rep observation 生成 | **2 箇所**。それぞれ別の公開関数の中にある | `runner.py:990` (`capture_measure_point()`、def `:803`)、`runner.py:1203` (`measure_point()`、def `:1057`) |
| 集約 note の産出 | `f"{n_exec_fail}/{reps} reps failed to execute"` が **2 箇所** | `runner.py:1029` (capture 側)、`runner.py:1247` (measure 側) |
| campaign の算出 | `_EXEC_FAIL_RE = re.compile(r"(\d+)/\d+ reps failed to execute")` を `notes` へ当てる | `s8b_floor_campaign.py:1879` (regex)、`:1882-1891` (`_count_exec_failures`) |
| rep observation の現 key 集合 | exact 6 key (`rep_index` / `returncode` / `counter_status` / `missing_perf_events` / `perf_raw` / `throughput`)。`complete` 述語が `set(observation) == {6 key}` を要求 | `s8b_floor_campaign.py:1947-1950` (述語)、`:1898-1913` (証跡 carrier 欠落時の padding) |
| `rep_integrity_failures` の算出 | `_project_scalepoint` (def `:1893`) の `failures` counter。`exec_failures` とは別量 | `s8b_floor_campaign.py:1893-1975` |
| `launch_floor_attempt()` の production 呼び手 | **0 件** (`_launch_floor_attempt` を呼ぶのは同 module 内の `:1203` と test 専用 `:1248` のみ) | `s8b_floor_attempt_launcher.py:940/1189/1218` |
| launcher module の import 元 | **repo 全体で 1 件、`orchestrator/tests/test_s8b_floor_attempt_launcher.py:24` だけ** | 実装面 2 tree の走査 |
| campaign から attempt_registry への参照 | **0 件** | `s8b_floor_campaign.py` の走査 |
| **床値 campaign が実際に呼ぶ runner 入口** | **`measure_point` (def `runner.py:1057`)。`capture_measure_point` は呼ばない** | `s8b_floor_campaign.py:93` (import)、`:7865`、`:7871` |
| **launcher が使う runner 入口** | **`capture_measure_point` (def `runner.py:803`)**。ただし launcher 自体に production 呼び手が無いので、この経路は現在動いていない | `s8b_floor_attempt_launcher.py:158-160` (`_PRODUCTION_DEPENDENCIES`)、`:435` |
| **6 key の exact 集合 gate は 2 本ある** | (a) campaign の `complete` 述語 `s8b_floor_campaign.py:1947-1950`、(b) **有効性判定側の `s8b_floor_stats.py:63` (`_REP_OBSERVATION_KEYS` frozenset) + `:486` (`set(observation) != _REP_OBSERVATION_KEYS` で errors へ)**。(b) は brief 初版で見落としていた | 実装面の exact 集合比較の走査 |
| その他の rep observation consumer (production) | `floor_pair_driver.py:331`/`:1605`/`:1617`/`:1794-1828`、`backoff_extended_sweep.py:547-609`、`backoff_counterfactual_analysis.py:256-257`/`:322`。いずれも **exact key 等値ではなく個別 key の読み取り** | 3 file の走査 |
| 6 key を参照する file | 12 本 (production 3 / test 8 / fixture 1) | `missing_perf_events` の走査 |
| 凍結 fixture の 6 key が hardcode digest へ伝播するか | **伝播しない** (親の独立読解)。`test_s8b_oracle_manifest.py:55-64` の 64hex は schedule / spec の digest、`:71-100` の raw bytes literal は configuration / holdout entry で rep observation を含まない。`test_s8b_holdout_freeze.py:130-145` は rep observation を書き換えたうえで digest を**その場で再計算**する | 4 consumer の走査 |

## 5. pin 閉包 (DW-O09。C2 の変更面で引き直した)

- **whole-file SHA-256 golden は 0 件。** 変更しうる 7 file
  (`runner.py` / `model.py` / `s8b_floor_campaign.py` / `s8b_floor_stats.py` /
  `s8b_terminal_evidence.py` / `s8b_floor_attempt_launcher.py` / `s8b_v2_freeze_fixture.py`)
  の現 hash を repo 全体で検索して 0 hit。
- **`FROZEN_MANIFEST` は対象外** — output 23 path の figure 束縛のみ
  (`orchestrator/tests/test_frozen_artifacts.py:41`、件数 23 を
  `test_s1_9pair_figure_provenance.py:617` が固定)。
- **`test_official_perf_closure.py` の semantic inventory は残る (契約 9 節)。**
  `_REVIEWED_PERF_FILES` (`:44`) は exact frozenset で、`runner.py` /
  `s8b_floor_campaign.py` / `s8b_floor_stats.py` / `s8b_floor_attempt_launcher.py` は
  **既に登録済み**。既存 file の編集では集合は動かないが、
  **新しい production file を足すと `_production_perf_files()` (`:533`) の AST 走査で集合等値
  (`:905`) が落ちる。**
- **`test_t671_source_binding.py` の path 表は `runner.py` を含む 63 path の exact tuple。**
  `:267-269` が `24` / `39` / `63` の件数を assert する。**contract loader の source 表へ
  新 path を足すと必ず赤になる。**
- **凍結 fixture が 6 key を字面で持つ:** `orchestrator/tests/s8b_v2_freeze_fixture.py:155-163`。
  consumer は `test_s8b_holdout_freeze.py` / `test_s8b_oracle_driver.py` /
  `test_s8b_oracle_manifest.py` / `test_s8b_oracle_report.py` の 4 本で、
  うち oracle driver に 64hex literal 46 件、oracle manifest に 19 件がある。
  **これらが fixture 由来の bytes に依存するかは段 2 で file:line 粒度で確定させる。**
- `s8b_ratified_freeze.py:265-266` の session row key 表は rep observation の key 集合とは別物。
- `attempt_registry_core.py` は `test_reflux_formal_consumer.py` の AST 走査下。
  `aborted=False` の keyword 呼び出しと `OriginSealed(False, ...)` を書かない (契約 9 節)。

## 6. 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1) 4 点目「実環境値域の供給」は、campaign→launcher の配線そのものではない。**
  provisional 裁定: C2 は 1〜3 で campaign 側が実値を構造化して産出する状態を作り、
  その実値域を**実 campaign 経路の実測として記録する**ところまでを持つ。
  `launch_floor_attempt()` を実際に呼ぶ配線は別単位に残す。
  **根拠:** launcher の import 元が自分の test 1 本しかなく、campaign は attempt_registry を
  1 度も参照していない (4 節の実測)。配線は D1341 が「束縛の検査と同じ変更単位」と縛った
  対象そのもので、C2 に混ぜると単位境界が崩れる。
  **反対の読み:** 「実値域」は呼び手が無ければ測れないので、配線まで C2 が持つ。段 3 で攻撃させる。
- **(P2) 構造化 `execution_failure` は rep observation の 7 番目の key として運ぶ。**
  根拠: 契約が「6 key → 7 key 化」と明記している。別 carrier は契約から外れる。
- **(P3) `_count_exec_failures` の notes regex は呼び手ごと除去する。**
  根拠: 契約 3 節が自然文を信頼経路に残さないと決めている。自然文 note 自体は
  診断用に残してよいが、**算出の入力にしない**。
- **(P4) runner の 2 入口はどちらも直す。**
  `measure_point` (床値 campaign が実際に呼ぶ、production live) と
  `capture_measure_point` (launcher が使う、現在 production 呼び手なし) は、
  rep observation の組み立てと集約 note を**それぞれ別に持っている**。
  片方だけ直すと、契約 3 節の等値束縛が経路によって成立したりしなかったりする。
  provisional 裁定: **両方を同じ形へ直す。** 実値域の実測は
  **`measure_point` 側 (live な方)** から採る。
  反対の読み: 動いていない `capture_measure_point` を今直すのは規律 5 (盛らない) 違反。
  段 3 で攻撃させる。

## 7. 不変条件 (破ったら止める)

- `exec_failures` と `rep_integrity_failures` は**別の量**。同じ rep で両方立ちうる。
  片方をもう片方から導かない。
- **正しさゲートを緩めない (絶対規律 2)。** 受理集合を広げる変更を「7 key 化のついで」で入れない。
- **新しい production file を足さない** (5 節の 2 つの exact inventory が落ちる)。
  実装は既存 file の中で閉じる。
- v1 (非 v2) 側の event key 集合・受理集合を 1 bit も変えない (契約 1 節)。
- 段 5 以降で `orchestrator/tests/acceptance_duration_ledger.json` を触るのは、
  **main 取り込み後に 1 回だけ**、正本 producer 経由で行う。

## 8. 成果物の形

- コード + テスト (実装面はすべて Codex `role=author`)。
- 変異 matrix と受入全走の receipt。
- `output/insights/2026-09-08_t1851-unit-c2-*/` に brief・plan・敵対レンズ・裁定・逐語・変異台帳。
- **land しない。** branch 上の checkpoint で終える。

## 9. 分割方針

段 2 の plan が file:line 粒度で確定させるまで固定しない。現時点の想定は 2 本・直列
(runner + campaign の算出 → 凍結 gate の pin 閉包と fixture 追随)。
段 2・3 は**流用しない** — C1b の変更面 (leaf / core / launcher) と C2 の変更面
(runner / campaign / freeze fixture) は骨格が違う。
設計択一が割れ (P1)、正しさ防壁 (凍結 gate) に触り、受理集合 (`complete` 述語の exact key 集合) が
変わるので、**軽量版にはしない。** 段 2・3 と段 6 の敵対レビューを省かない。
