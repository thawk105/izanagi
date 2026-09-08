# [T-1851] 単位 C2 — 段 4 裁定と変異事前登録

base `0cb90c592`。branch `worktree-dev-wave-t1851-unit-c2`。**land しない (D1341)。**
段 2 plan = `s2-plan.md`、段 3 レンズ A = `s3-lensA.md`、レンズ B = `s3-lensB.md`。
親は以下の判定をすべて**現物の file:line を自分で開いて**行った。

---

## 1. 裁定の要約

- **本 wave の scope は契約 4 点のうち 1〜3 に確定する。4 点目は本 wave では達成しない。**
  達成しない理由は実測に基づく (5 節)。**「供給済み」とは書かない。**
- 1〜3 は段 3 が出した blocker をすべて閉じた形で実装する。閉じない実装は採らない。
- 6 単位の分割に手を入れる必要が生じたので、**裁定パッケージとしてユーザーへ返す** (8 節)。
  本 wave は返答を待たずに 1〜3 を完了させる。

---

## 2. 親 brief の訂正 (レンズ 2 本の指摘はすべて正しかった)

親は行番号の一部を **main の checkout** で測っており、main 取り込み後の worktree と 1 行ずれていた。
訂正後の値は次のとおり (すべて `0cb90c592` の worktree で親が再実測)。

| brief の記載 | 正しい値 |
|---|---|
| `s8b_floor_stats.py:63` = `_REP_OBSERVATION_KEYS` | `:63` は `PERF_EVENTS`。定数は **`:64-67`** |
| `s8b_floor_stats.py:486` = exact 比較 | `:486` は `continue`。比較は **`:487`** |
| `s8b_floor_attempt_launcher.py:158-160` = `_PRODUCTION_DEPENDENCIES` | `:158-160` は `OpenedFloorAttempt` の field。実体は **`:210-213`** |
| launcher の capture 呼出し `:435` | `:435` は `_failure_evidence()` の引数。呼出しは **`:730`** |
| `_launch_floor_attempt` の呼出し `:940/1189/1218` | `:940` は def。**呼出しは `:1203` と `:1248`** |
| runner の rep observation 生成は 2 箇所 | **4 箇所**。初期化 literal `:940` `:1106` と最終代入 `:990` `:1203` |
| `backoff_counterfactual_analysis.py` が consumer | **consumer ではない** (`rep_observations` も `missing_perf_events` も参照しない)。真の consumer は **`pipeline.py:2794-2866`** |
| `FROZEN_MANIFEST` は figure 23 path のみ | **誤り。** `output/s8b-freeze/floor_protocol.json` と `holdout_freeze.json` の digest を直接 pin している (`test_frozen_artifacts.py:44-49`) |

**この訂正は 6 節の B6 に直結する。**

---

## 3. provisional 裁定 (P1〜P4) の確定

| # | 判定 | 根拠 |
|---|---|---|
| **P1** | **refuted** | レンズ 2 本が独立に否定。親も裏取りした (5 節)。 |
| **P2** | **採用 (訂正つき)** | 7 番目の key は `execution_failure`、exact `bool`、全 rep に必ず存在。**ただし carrier 欠落の padding へ `False` を書く部分は採らない** (B3)。 |
| **P3** | **採用** | `_EXEC_FAIL_RE` (`s8b_floor_campaign.py:1879`) と `_count_exec_failures` (`:1882-1891`) を唯一の呼び手 (`:1965`) ごと除去する。契約 3 節の確定裁定。 |
| **P4** | **採用** | runner の 2 公開面をどちらも直す。レンズ 2 本とも支持。将来 launcher が使う capture 面を 6 key のまま残すと terminal evidence が受理できない (レンズ B)。 |

---

## 4. 段 3 所見の real / refuted

### real・採用 (scope 内。6 節へ blocker として繰り入れる)

| 所見 | 出所 | 親の裏取り |
|---|---|---|
| terminal の本数式が 2 量を再結合する | A | **確認。** `s8b_terminal_evidence.py:856` の `len(throughputs) + nonfinite_count + exec_failures != reps_expected`。非 zero rc の rep は integrity failure だが exec failure ではないので式が破れ、逆に偽の `execution_failure=True` なら通る |
| `execution_failure=True` と成功 throughput の同居を受理する | A | **確認。** plan は「valid evidence だが qualified ではない」としか書いておらず、矛盾条件を置いていない |
| padding の `False` は未観測事実の捏造 | A | **確認。** carrier 欠落時に「runner が例外を捕捉しなかった」は観測できない |
| `_derive_rep_integrity()` の返値 consumer 取り残し | A, B | **確認。** `s8b_terminal_evidence.py:1030` が 3 値 unpack。test は `test_s8b_terminal_evidence.py:468`/`:479` |
| 真の consumer `pipeline.py:2794-2866` が表に無い | B | **確認。** `measure_point()` の observation を読む |
| 変異 M5 / M7 / M10 が複数変異を 1 ID に束ねている | B | **確認。** DW-M01 の単一理由性を満たさない |
| M6 / M7 / M9 / M10 が前段拒否で恒真化する | A, B | **確認。** 現行の exact 6-key gate が先に拒否するため、新述語の発火証拠にならない |
| M8 は等価変異 | B | **確認。** `bool` は継承不能なので `type(x) is bool` と `isinstance(x, bool)` の受理集合は同じ |
| 「既存 positive control が M1-M6 の複合陽性対照」は偽 | B | **確認。** 同 test は `measure_point()` しか通さず capture 面へ届かない |
| baseline 14 file の外に consumer test がある | B | **確認。** ratified 2 本は plan の編集対象なのに親の baseline に無かった |
| **FORMULA_ID の版境界** | A | **確認、かつ親が更に踏み込んだ (6 節 B6)** |

### real だが格下げ

- **「exact 7-key 化そのものが受理集合を広げる」(A の blocker 1)。**
  親の裏取り: レンズ A の反例は、**7 番目の key を持つ入力**が今日は拒否され改訂後は受理される、
  という形である。7 番目の key は本 wave で新設するもので、**改訂前にこれを出す producer は
  存在しない**。よってこれは既存 gate の穴ではなく schema 拡張である。
  ただし「拒否集合の単純な縮小ではない」という指摘自体は正しい。
  **対処は B6 (版境界) と、旧 6-key 入力が改訂後に拒否されることの負例で行う。**
  なお旧 6-key artifact の受理を前向きに廃止する向きは **D1660 の確定裁定と同じ**である
  (「旧世代の受理を前向きに廃止する。受理集合は狭まる方向にしか動かない」)。
  本 wave はこれを踏襲し、resume 経路で旧 journal が fail-closed になることを**限界として明記する**。

### refuted

- 「plan は親が `s8b_floor_campaign.py:1039-1045` を complete 述語とした」という plan 側の異議は、
  **旧版 brief への攻撃**であり現行 brief には当たらない (レンズ 2 本とも同じ判定)。

### scope 外 (real だが本 wave では実装しない → 8 節へ)

- 契約 9 節を満たす campaign→launcher 配線 (plan 見積り 5 file / 350-550 行)。

---

## 5. なぜ 4 点目を本 wave で達成しないか (実測)

1. `launch_floor_attempt()` の production 呼び手は **0 件**。
   launcher module の import 元は repo 全体で **1 件、自分の test file だけ**。
2. **実 campaign の値域が記録された成果物は repo に存在しない。**
   親が `output/` 全体を `rep_observations` で走査した結果、hit は変異台帳と入力 manifest だけで、
   実 floor campaign の result / journal は 0 件。したがって
   「記録済みの実値を launcher の gate へ通す」という配線なしの近道は取れない。
3. 配線は plan 見積りで 5 file / 350-550 行。**しかも 7-key schema が先に存在しないと組めない**
   (launcher の terminal evidence が `exec_failures` を束縛するため)。依存順は 1〜3 が先である。
4. D1341 は「配線と proof chain 束縛は同じ変更単位で land する」と縛る。本 branch は 6 単位が
   揃うまで land しないので、配線を別単位に置いても D1341 に反しない。

**したがって本 wave の成果物には「実環境の値域を供給した」と書かない。**
書くのは「producer 側が実値を構造化して産出する状態にした。launcher の gate へ通してはいない」である。

---

## 6. 確定 scope (plan v2)

### 実装する

- **S1** runner の 4 literal 箇所 (`:940` `:990` `:1106` `:1203`) を 7 key にし、
  例外捕捉 4 箇所 (`:965` `:978` `:1170` `:1184`) で `execution_failure=True` を立てる。
  例外の型名・message は新 key に載せない。診断 note は残すが算出の入力にしない。
- **S2** `_EXEC_FAIL_RE` と `_count_exec_failures` を唯一の呼び手ごと除去する。
  `_project_scalepoint` は `execution_failure is True` の本数を `exec_failures` とし、
  `complete` に `execution_failure is False` を加える。
- **S3** `s8b_floor_stats.py:64-67` を 7 key にし、`:487` の exact 比較を維持する。
  `_derive_rep_integrity()` を 4 値へ拡張し、`exec_failures` を独立に再導出する。
  `:897` 近傍と `s8b_floor_campaign.py:8368-8389` の resume gate で top-level 値との等値を検査する。
- **B1** **terminal の本数式を作り直す** (`s8b_terminal_evidence.py:856`)。
  `exec_failures` を「欠格 rep の代理」に使わない。sink の各 rep の分類から
  finite / nonfinite / execution-failure / その他 integrity failure を**別々に**数え、
  非 execution の integrity failure が sealed terminal へ運べるようにする。
- **B2** `execution_failure is True` の rep が qualified / complete になれない条件を置く。
  producer が実際に保証する関係 (例外を捕捉した rep は throughput を持たない) を**署名で書き**、
  **通る正例を 1 つ添える** (DW-S04)。
- **B3** **carrier 欠落 padding に `False` を書かない。** 未観測を表す扱い
  (既存の unavailable projection と同じ向き) にし、fail-closed にする。
  「carrier が無いのに例外は無かった」と読める値を作らない。
- **B4** `_derive_rep_integrity()` の返値 arity 変更の閉包を閉じる。
  `s8b_terminal_evidence.py:1030`、`test_s8b_terminal_evidence.py:468`/`:479`。
- **B5** `pipeline.py:2794-2866` を subset consumer として確認し、変更不要なら
  **7 key でも壊れないことを test で固定する** (取り残しを口頭で済ませない)。
- **B6** **FORMULA_ID の版境界を実装時 gate にする。**
  `s8b_floor_stats.py:16-19` は「式を変えるときは FORMULA_ID を改版する」と書き、式には
  **セルの有効性契約が含まれる**。`FORMULA_ID = "s8b-floor-stats/v2"` は
  `s8b_floor_stats.py:51` と `s8b_floor_contract.py:44` にあり、`:476` が一致を要求し、
  `s8b_floor_campaign.py:1310` が protocol へ書き込む。その protocol は
  **`output/s8b-freeze/floor_protocol.json` として凍結され、`FROZEN_MANIFEST`
  (`test_frozen_artifacts.py:44-49`) が sha256 を pin している。**
  よって **FORMULA_ID を改版すると凍結成果物の bytes が変わる。**
  **gate:** 実装子は、**producer が実際に出しうる入力すべてで**
  `exec_failures` / `rep_integrity_failures` / qualified throughputs / session median が
  改訂前後で**一致する**ことを test で示す。示せた場合だけ FORMULA_ID を据え置く。
  1 つでも値が動く入力があれば **そこで止め、親へ報告する**。
  親は凍結成果物の再発行をユーザー裁定へ返す。**実装子が独断で FORMULA_ID を書き換えない。**
- **B7** 旧 6-key 入力が改訂後に**拒否される**ことの負例を置く。resume 経路で旧 journal が
  fail-closed になることを限界として記録する (D1660 と同じ向き)。

### 実装しない (scope 外)

- campaign→launcher の配線と、実 campaign 走行による実値域の実測 (5 節)。
- journal の TOCTOU 窓 (D1661 が閉じないと裁定済み)。
- schema error を既に返す key 不一致を、さらに integrity failure count へ加えること
  (レンズ B が「受理集合を変えない冗長」と判定。nit へ落とす)。
- `type(...) is bool` 様式の強化主張 (等価)。

---

## 7. 変異事前登録 (DW-M01 — 単一理由性)

**DW-M01 に従い、赤理由が 1 つに絞れることを実装後に probe で確認する。**
確認できない変異は**登録せず実効 gate へ再照準する**。前段拒否で恒真化する形
(F28 / F820 / F900) を避けるため、各変異には
**「新しい前段をすべて通り、対象述語だけを外すと受理される入力」**を対で置く。

| # | 変異位置 | 変異内容 (1 ID = 1 変異) | 殺す test | 単一理由性の担保 |
|---|---|---|---|---|
| M1 | `runner.py:956-1002` | capture 面の捕捉例外で flag を立てない | 新設 (capture 面専用) | capture 面は既存 positive control が届かないので専用 test を作る |
| M2 | `runner.py:1130-1215` | direct 面の捕捉例外で flag を立てない | 新設 (direct 面専用) | 入口別に分ける |
| M3 | `s8b_floor_campaign.py` の算出 | structured flag を無視し notes regex へ戻す | 新設 | **notes と flag が食い違う入力**で差を出す (同数だと差が出ない) |
| M4 | 同上 | `exec_failures = rep_integrity_failures` とする | 新設 | **非 zero rc のみの rep** で 2 量を分離させる |
| M5a | `s8b_floor_campaign.py` の padding | padding を `True` にする | 新設 | 3 変異を 1 ID に束ねない |
| M5b | 同上 | padding の key を落とす | 新設 | 同上 |
| M6 | `_project_scalepoint` の complete | `execution_failure is False` を外す | 新設 | **returncode=0・counter complete・flag True** の入力を使い、他条件で赤にならない形にする |
| M7 | `s8b_floor_stats.py:64-67` | exact 集合を 6 key へ戻す | 新設 | 正常な 7-key 入力が広く赤になることを確認し、**diagnostic sensitivity と区別して記録** |
| M9 | stats の top-level 等値 | `exec_failures` と再導出値の等値検査を外す | 新設 | **integrity 側は一致・exec 側だけ食い違う**入力で他 gate を通す |
| M11 | `s8b_terminal_evidence.py:856` (B1) | 本数式を旧式へ戻す | 新設 | 非 zero rc の rep を含む sealed terminal で赤になる |
| M12 | B2 の矛盾条件 | `execution_failure=True` + 成功 throughput を受理する | 新設 | 他 gate を通る形にする |

**M8 は等価変異なので登録しない** (`bool` は継承不能)。
**M10 は「count 無視」と「schema error 無視」に分割し、probe で単一理由性を確認してから登録する。**
probe で前段拒否が確認されたものは matrix から外し、理由を台帳へ書く。

---

## 8. 裁定パッケージ (ユーザーへ返す。本 wave は待たない)

**問い: 契約 v3.1 の 9 節「実値域は C2 が供給する」をどう満たすか。**

実測: `launch_floor_attempt()` の production 呼び手 0 件、launcher の import 元は自分の test 1 本、
実 campaign の値域を記録した成果物は repo に 0 件、配線の見積りは 5 file / 350-550 行。

- **案 1 (親の推奨):** C2 は producer 側 (1〜3) を持ち、**配線と実値域の実測を新しい単位 C3 へ分ける。**
  6 単位が 7 単位になる。理由: 配線は 7-key schema が先に無いと組めず、依存順が固定されている。
  D1341 は同じ branch で揃えば満たされるので、単位を割っても違反しない。
- **案 2:** C2 を延長して配線まで持つ。1 wave では収まらず、7-key の受入と配線の受入が混ざる。
- **案 3:** 契約 9 節の「供給」を「producer schema の準備」へ弱める erratum を出す。
  契約は AI が敵対検査で v3→v3.1 へ訂正した先例があるが、
  **単位分割はユーザー裁定の対象なので親の独断では変えない。**

**本 wave は案 1 の前半 (1〜3) を完了させ、4 点目を未達成として明記する。**
案の確定はユーザーへ返す。

---

## 9. 実装子の分割 (段 5)

plan の 3 本直列を採るが、所有と作業項目を裁定に合わせて確定する。

1. **子 1 — carrier producer**
   所有: `orchestrator/calibrator/runner.py`、`orchestrator/tests/test_calibrator.py`、
   `orchestrator/tests/test_calibrator_deferred_output.py`
   作業: S1。両公開面の 4 literal 箇所と 4 例外箇所。入口別の正例・負例。
2. **子 2 — 算出と信頼 gate**
   所有: `orchestrator/campaign/s8b_floor_campaign.py`、`orchestrator/campaign/s8b_floor_stats.py`、
   `orchestrator/campaign/s8b_terminal_evidence.py`、および対応する 3 test file
   作業: S2、S3、B1、B2、B3、B4、B6、B7。**B6 の gate に触れたら止めて親へ報告する。**
3. **子 3 — fixture と consumer pin**
   所有: `orchestrator/tests/s8b_v2_freeze_fixture.py`、`test_s8b_attempt_registry.py`、
   `test_s8b_floor_attempt_launcher.py`、`test_s8b_ratified_freeze.py`、
   `test_s8b_ratified_verify.py`、`test_backoff_extended_sweep.py`
   作業: 全 observation literal の 7-key 追随、B5 の pin。

直列順は 1→2→3。**新しい production file を作らない** (`test_official_perf_closure.py:44/533/905` と
`test_t671_source_binding.py:67/267-269` が落ちる)。

## 10. 焦点走の file 集合 (DW-O26)

親の baseline 14 file に次を加える。

`test_calibrator_deferred_output.py`、`test_backoff_extended_sweep.py`、`test_campaign.py`、
`test_holdout_observation.py`、`test_frozen_artifacts.py`、`test_s8b_floor_contract.py`。
