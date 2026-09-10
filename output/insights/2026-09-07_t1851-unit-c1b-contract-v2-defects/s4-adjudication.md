# [T-1851] C1b 段 4 裁定 — 契約 v2 は実体化できない。本 wave は実装しない

base `9c1951179`。branch `worktree-dev-wave-t1851-unit-a`。**land しない (D1341)。**
段 2 plan (`s2-plan.md`)、段 3 レンズ A (`s3-lensA.md`) / B (`s3-lensB.md`)、親検算
(`refs/parent-verification.md`) を突き合わせて裁定する。

## 0. 裁定 (DW-S04)

**本 wave は実装しない。段 5・6 を飛ばし `4 → 7 → 8 → 9` とする。**

理由は 1 つである。**C1a の段 4 が固定した「契約 v2」を literal に実体化すると、v2 台帳の
terminal 行は 1 行も書けない。** これは設計の好みではなく、3 者 (親・レンズ A・レンズ B) が
独立に測って一致した事実である。契約の欠陥を直さずに実装子を起動すれば、
「動かないと分かっているコード」を 3,000 行積むことになる。

段 2 plan の判定も、段 3 の 2 レンズの判定も、いずれも **no** である。

**本 wave の成果物は「契約 v3 (訂正版)」と、下記 4 件の裁定パッケージである。**

## 1. 実測で確定した契約 v2 の欠陥 (7 件)

| # | 契約 v2 の記述 | 現物 (実測) | 判定 |
|---|---|---|---|
| X-1 | 「exact field (**24**)」 | 表が列挙する distinct な field 名は **23**。1 行が `report_sha256` / `observation_sha256` の 2 つを書いている | real。訂正が要る (2 節 A) |
| X-2 | `campaign_record` は `_finish_session` と同じ **27 key** | exact **30 key**。独立 trust root `s8b_ratified_freeze._JOURNAL_KEYS["session"]` と集合等値 (親が AST とインポートの両方で確認、レンズ B も一致) | real。**30 に確定**。裁定不要 |
| X-3 | issuer は `seal_terminal_evidence(reservation, opened, terminal)` の 3 引数 | `attempt_binding` が要る 3 digest (`classification_receipt_sha256` / `classification_event_sha256` / `observation_start_event_sha256`) は launcher の 3 型のいずれにも無い。持つのは adapter の `_AttemptState` だけで、綴りも `observation_event_sha256` と不一致 | real。3 案あり (2 節 B) |
| X-4 | 証拠に `probe_before` / `probe_after` / `campaign_record` を exact に載せる | 三軸 literal の運び手が **5 field 以上**。`campaign_record` の `workload` (実体は `{"ycsb_rratio":"80", ...}` の mapping)、`run_cmd`、`notes`、`probe_before`、`probe_after`。outer 側も `failure.message`、`launch_failures[].message`、`perf_preflight_receipt.candidates[].path`。guarded writer (`s8b_attempt_registry.py:1176`) が**必ず**拒否する | real。**証拠は現行 root へ公開できない** (2 節 C) |
| X-5 | E1 の 6 枝は campaign `_run_session` と同順 | **一致しない。** campaign の実 precedence は `probe_after.competing` → `measure_error` → `exec_failures >= reps` → `exec_failures > 0 かつ derived_reason is None` → `rep_integrity > 0 かつ derived == partial` → `derived_reason` (`s8b_floor_campaign.py:6311-6327`)。契約の枝 3 は「`0 < exec < reps` なら無条件で launch_failure」だが、実測では 4/5 有限 + `exec_failures=1` のとき `assess_session.required_reason == nonfinite_or_partial_output` になり、campaign は枝 4 を**通らず** partial へ落ちる | real。契約が誤り (2 節 D) |
| X-6 | `exec_failures` は私有 sink の非 zero rc / 起動失敗から数える | campaign は `notes` の regex からしか算出しない (`s8b_floor_campaign.py:1879-1890,1926-1970`)。レンズ A の実測では rc=1 が 2 本・notes 空で campaign は `exec_failures=0` / `rep_integrity_failures=2` を出す | real。「全件等値」が実データで破れる (2 節 E) |
| X-7 | 非有限 throughput は null へ正規化し `nonfinite_count` に数える。かつ `len(throughputs) + nonfinite_count + exec_failures == reps_expected` | **自己矛盾。** 5 本中 1 本を null 化すると長さは 5 のままで `nonfinite_count=1` なので左辺 6。さらに canonical JSON は NaN/Inf を拒否し、`assess_session` は `None` を非数値として拒否する | real。契約が誤り (2 節 F) |

加えて、**封印そのものが偽造できる**という所見が 2 件ある。

| # | 所見 | 実測 |
|---|---|---|
| X-8 | plan の「issuer table + private API」方式は防壁にならない。table への直接 insert、private issuer の直接呼出し、`__reduce_ex__` 経由の private issuer 呼出しが、いずれも accepted になった (現行の同型実装 `s8b_attempt_registry.py:42-50,258-316` に対するレンズ A の直接評価) | real (blocker) |
| X-9 | `_launch_floor_attempt_for_test()` は production 本体と同じ `_launch_floor_attempt()` を呼び、probe・registry・capture・classification authority・terminal builder を全部注入できる。3 引数 issuer を共通本体から呼ぶと、**test seam が fake fact から production の封印を発行できる** | real (blocker) |

## 2. 親が確定させる訂正 (契約 v3。ユーザー裁定を要しない)

規律 7 に従い、C1a の裁定を**追記で訂正**する。過去の判定を遡って無効化しない。

- **A (X-1):** outer field の**計数は 23 が正**。ただし 24 番目として `failure_reason` を足すか
  `self_report` を 4 key にするかは 3 節 (1) の裁定に従属するので、ここでは確定させない。
- **B (X-3):** issuer は **`seal_terminal_evidence(reservation, opened, terminal)` の戻り値を
  未完成 `SealedTerminalEvidenceDraft` とし、adapter が exact `CapturedObservation` から
  3 digest を足して初めて `ValidatedTerminalEvidence` を発行する**形にする (レンズ A の A-11 案)。
  公開 signature を変えず、X-9 の test seam 経路も塞ぐ。launcher だけでは validated capability を得られない。
- **C (X-4):** 証拠文書を **再導出面 (平文) と束縛面 (digest)** に分ける。平文に載せるのは
  E1 の 6 枝と cross-field 不変条件が実際に読む値だけ。probe は `competing` と null 性のみ。
  `campaign_record` は identity と計測値のみで、`workload` / `run_cmd` / `notes` / probe 生値は
  canonical digest で束縛する。`failure` は stage と非 null 性のみ、message は digest。
  perf receipt も判定 projection と full digest に分ける。**最終 canonical bytes は既存の
  holdout-safe gate を必ず通す。** これは launcher が pre-output 証拠へ既に使っている規律
  (`_external_evidence_sha256 :414-433`) と同型で、新しい逃がし道を作らない (規律 2 を緩めない)。
  **trust boundary を広げる専用 bypass は採らない。**
- **D (X-5):** **E1 は campaign の実 semantics を正本にする。** 枝 2 を
  「`failure` 非 null **または** `exec_failures >= reps_expected`」、枝 3 を
  「`0 < exec_failures < reps_expected` **かつ** assessed reason が null」に訂正する。
  枝 2 と枝 3 が同じ E2 語を返すこと自体は契約の意図どおりで、full / partial の排他 fixture を
  使う限り変異 M6 / M7 は互いを殺さない (レンズ A が確認)。
- **F (X-7):** 非有限値の表現を一意にする。**列内に null を残す**なら不変条件を
  `count(non-null) + nonfinite_count + exec_failures == reps_expected` かつ
  `nonfinite_count == count(null)` に訂正し、E1 の `assess_session` へは finite-only 列と
  元の `reps_expected` を渡す。
- **G (X-8):** capability の唯一の実データを **immutable canonical bytes** にする。
  `document` と `projection` は毎回その bytes から再生成し、table には bytes digest と
  identity fingerprint だけを保存する。**table membership を権威にしない。**
- **H (scope):** plan が「必要」とした **claim v4 の新設、`_AttemptState` への `mode` 追加、
  core API 8 surface への keyword 伝播は契約が要求していない自発的拡張**であり、採らない
  (レンズ B の B05 / B06 が既存 claim に `mode` があることを実測)。

## 3. ユーザーへ返す裁定パッケージ (4 件)

これらは「読み方が変われば作る物が変わる」ため、親が決めない。

### (1) core の等値検査と E2 語彙の衝突 — 最重

**事実:** `attempt_registry_core.py:1388-1394` は `row["failure_reason"] == classification の
pre_observation_failure_reason` を要求し、`:1402-1406` の null matrix は
`failure_reason` が retryable 集合 (v2 では E2 の 4 語) に入ることを要求する。
launcher の分類語彙は `competing_process` / `launch_failure` で E2 と互いに素。
検査 hook `:1407-1408` は両方より**後**なので、封印証拠をどれだけ強くしても解けない。
レンズ A が E2 の 4 語を直接投入したところ、**全件が等値で落ち validator 呼出しは 0 回**だった。

**親の当初案は否定された。** 「v2 では分類語彙を E2 の 4 語にする」案は、
`measurement_sample_incomplete` と `measurement_dispersion_exceeded` が `open()` の**後**にしか
判明せず、分類は `open()` の**前**に起きるため、4 語のうち 2 語に適用できない。

**選択肢:**
- (1-a) 契約を追記訂正し、**「観測前に分類された理由」と「観測後に導出された理由」を別の軸**として
  明文化する。core は echo 等値を常時維持し、exact official v2 profile かつ row 束縛済み
  capability があるときだけ、E2 再導出を直接等値の代替とする。証拠検査が先に成功する限り
  規律 2 の緩和ではない、というのがレンズ A の判定
- (1-b) v2 の transition policy 自体を変え、`require_terminal_reason_equals_classification` を
  観測前失敗にだけ掛ける
- **どちらも「正しさゲートの形」を変えるので、親が単独で決めない。**

### (2) `exec_failures` の出所 — 計測の意味論に触る

契約は私有 sink 由来、campaign は `notes` の regex 由来で、実測値が食い違う (X-6)。
- (2-a) C2 で campaign の `_project_scalepoint` を sink 由来へ変える (**計測の意味論の変更**)
- (2-b) 契約側を campaign の現行算出に合わせる (証拠の主張が弱くなる)

### (3) 封印の信頼境界をどこに引くか

X-8 が示すとおり、同一 process 内の任意 module 改変まで脅威に含めるなら、Python module の中だけでは
封印できない。issuer を別 process に隔離するか、**その攻撃を除外する信頼境界を明文に書く**か。
明文化しないまま「封印した」と主張することは規律 3 に反する。

### (4) C1b の単位をどうするか

レンズ B の実測により、**production 効果のある分割は存在しない**。
`leaf + launcher` は呼び手 0 件の module と早期 gate で止まる launcher を積むだけで、
v2 terminal を 1 行も増やさない (DW-G05 の成果物影響を満たさない)。
- (4-a) 契約 v3 確定後、leaf + launcher + profile + core + adapter を**縦に 1 単位**で実装する
  (plan 見積りで production +1,228〜1,717 / test +1,775〜2,465、C1a の約 3.6〜5.1 倍)
- (4-b) branch には契約 v3 (文書) だけを積み、実装は次 wave へ送る

## 4. 変異の事前登録 (DW-M01)

**実装面の差分が 0 なので変異 matrix は免除される (DW-S04)。受入全走は免除されない。**

次 wave のために、レンズ B が判定した変異候補の可否だけ記録する。
plan の M4 / M5 / M6 / M7 / M9 / M12 は軽い具体化で成立する。
M1 / M2 / M3 / M8 / M10 / M11 は再照準が要る。M13〜M18 は分割上 C1b の集合に入らない。

## 5. 段 3 所見の裁定表

- レンズ A: real 10 件 (うち blocker 6)、refuted 2 件。A-01 / A-02 / A-06 / A-07 / A-08 / A-09 / A-10 / A-11 を採用。A-03 / A-12 は refuted として記録。
- レンズ B: real 25 件、refuted 6 件。B01〜B13 と S01〜S04 を採用。M1〜M18 の帰属判定を 4 節へ。
- **親の V3 は撤回した。** `workload` の実型を取り違えた誤りで、plan の元の帰属が正しかった。
  レンズ A の A-10 が正しい。V6 で足した運び手は有効で、集合はむしろ広がる。
