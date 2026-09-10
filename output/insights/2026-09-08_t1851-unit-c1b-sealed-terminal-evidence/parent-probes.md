# [T-1851] C1b やり直し — 段 1 の consumer probe (親の実測)

前 wave が固定した契約 v2 は、条項を束縛する consumer に 1 本も probe を通さずに固定したため
実体化できなかった (`output/insights/2026-09-07_t1851-unit-c1b-contract-v2-defects/`)。
本 wave では契約 v3 の各条項について、それが束縛する consumer に最小 probe を通してから固定する。

測定は `worktree-dev-wave-t1851-unit-a` の `8193eefdb` (local main `645d0d663` 取り込み後) で行った。
probe 本体は repo 外 (背景 job の scratch) に置き、repo へは入れていない。

---

## P-1 裁定 1 (観測後の理由を別 field に載せる) — core を通した

`attempt_registry_core.py` と `s8b_attempt_profile.py` へ DW-O19 の一時変異を当て、実 core の
`load_attempt_registry()` へ v2 台帳を通した。変異は測定後に `git checkout --` で復元し、
`git status --porcelain` が 0 行であることを確認した。

> **erratum (段 4 で追記、規律 7)。** 下の「4 点だけ」という記載は不完全だった。
> probe は同時に `dataclasses.replace(v2, terminal_row_validator=None)` を使い、
> **v2 の無条件拒否 hook `_reject_unsealed_s8b_v2_terminal` を無効化して測っている。**
> レンズ A の A-04 がこの欠落を突いた。
>
> **測定自体は有効である。** この hook は C1b が封印証拠 validator へ置き換える対象であり、
> probe が測ったのは「hook を置き換えたあと、その手前にある core の等値検査・null matrix・
> exact key 検査を 5 形が通るか」である。前 wave が「1 行も書けない」と測ったのは
> まさにこの手前の 2 検査なので、probe はその問いに答えている。
>
> **ただし一般化は取り消す。** 「5 形が consumer を端から端まで通った」とは言えない。
> probe は leaf・adapter・durable evidence 経路を測っていない。射程の正本は
> `contract-v3.1.md` の 5.2.1 である。

一時変異の中身は 4 点だけである。

- `DomainProfile` へ `retryable_reason_field: str = "failure_reason"` (keyword-only) を追加
- `_assert_null_matrix` へ `reason_field` を渡し、`retryable-failure` / `terminal-failure` の
  2 枝が照合する field を profile が選べるようにする
- `record_attempt_terminal` へ `measurement_retry_reason` / `terminal_evidence_sha256` を追加し、
  profile の terminal key 集合に含まれるときだけ行へ載せる
- v2 profile の terminal key 集合へ上記 2 key を追加、`S8B_V2_RETRYABLE_FAILURE_REASONS` に
  E2 の 4 語を投入、`retryable_reason_field="measurement_retry_reason"` を指定

### 正例 (5/5 通過)

| 場合 | 分類理由 (観測前) | `failure_reason` | `measurement_retry_reason` | 結果 |
|---|---|---|---|---|
| 観測前・競合 | `competing_process` | `competing_process` | `measurement_environment_conflict` | 通過 |
| 観測前・起動失敗 | `launch_failure` | `launch_failure` | `measurement_execution_unavailable` | 通過 |
| 観測後・標本不足 | null | null | `measurement_sample_incomplete` | 通過 |
| 観測後・分散超過 | null | null | `measurement_dispersion_exceeded` | 通過 |
| 観測成功 | null | null | null | 通過 |

**前 wave が「1 行も書けない」と測った状態が解消されている。** 分類語彙 (`competing_process` /
`launch_failure`) と E2 の 4 語が互いに素であることは変わらないが、両者が別の field に載るので
`require_terminal_reason_equals_classification` の等値検査と null matrix が同時に満たされる。

### 負例 (帰属つき)

| # | 壊し方 | 結果 | 拒否した検査 |
|---|---|---|---|
| N1 | `observed` 行へ retry 理由を載せる | **通ってしまう** | (無い) |
| N2 | `retryable-failure` へ E2 外の語を載せる | 拒否 | `attempt-null-matrix` |
| N3 | 観測前 echo を分類理由と違う値に改竄 | 拒否 | `attempt-classification` |
| N4 | `not-consumed` 行へ retry 理由を載せる | **通ってしまう** | (無い) |
| N5 | `terminal-failure` へ E2 語を載せる (observation-start あり) | 拒否 | `attempt-null-matrix` |
| N5b | `terminal-failure` を report なしで書く | 拒否 | `attempt-null-matrix` |
| N6 | `retryable-failure` の retry 理由を null にする | 拒否 | `attempt-null-matrix` |

N5 は最初 observation-start なしで測ったところ `attempt-phase-order` で落ちた。これは E2 語の
検査が効いた証拠にならない冗長 gate による赤なので、observation-start を付けて測り直し、
`attempt-null-matrix` へ帰属することを確かめた。

**N1 と N4 は契約 v3 が閉じるべき穴である。** `_assert_null_matrix` の `observed` 枝と
`not-consumed` 枝は `measurement_retry_reason` を一切見ないため、観測に成功した行や未消費の行へ
「測り直しの理由」を載せても台帳が受理する。契約 v3 はこの 2 枝への null 要求を条項にする。

---

## P-2 訂正 C (証拠文書を平文と digest に分ける) — guarded writer を通した

`s8b_attempt_registry._write_staging` が呼ぶ `assert_holdout_safe_bytes()` は、
`s8b_holdout_freeze.holdout_conjunction_hits()` で holdout の三軸 (読み比率・偏り・read-modify-write)
の conjunction を走査する。現物の holdout は `rr80` (H1) と `rr20` (H2) の 2 つで、
三軸の値は `{ycsb_zipf_skew: 0.9, ycsb_rratio: 80|20, ycsb_rmw: 0}` である。

| 文書の形 | 走査結果 |
|---|---|
| 契約 v2 の literal (campaign_record と probe を exact に載せる) | **拒否**: `rr80` 汚染 |
| 契約 v3 の分離 (平文は判定が読む値だけ、運び手は digest) | 通過 |
| v3 に `workload` を平文で戻す | **拒否**: `rr80` 汚染 |
| v3 に `run_cmd` を平文で戻す | **拒否**: `rr80` 汚染 |

前 wave の X-4 (証拠は現行 root へ公開できない) が再現し、訂正 C がそれを解くことも確かめた。
負例 2 本が両方とも再び落ちるので、この条項は恒真ではなく実際に効いている。

平文で残してよい範囲も測った。三軸のうち **2 軸までなら通り、3 軸そろうと落ちる。**
`holdout_id` ("H1") と `cell_id` は単独では汚染しないので平文で残せる。

---

## P-3 訂正 E (`campaign_record` の key 集合) — 30 key で確定、前 wave の列挙は 1 語欠けていた

`s8b_ratified_freeze._JOURNAL_KEYS["session"]` を直接読んだ。**exact 30 key。**

```
attempt_id binary_sha256_at_measure cell_id configuration_id duration_s event
excluded_reason exclusion_class exec_failures holdout_id kind notes probe_after
probe_before records rep_integrity_failures rep_observations reps_expected retry
retry_ordinal round run_cmd seq session_cv session_median threads throughputs
trigger valid workload
```

前 wave の s1-brief (P2) が列挙した 29 語には **`binary_sha256_at_measure` が無い。**
件数 30 は前 wave の裁定どおりだが、列挙のほうが誤っていた。契約 v3 は上の 30 語を正本にする。

---

## P-4 訂正 F (非有限値の表現) — `assess_session` へ渡す形を測った

- `canonical_json_bytes` は NaN / Inf を拒否する (`allow_nan=False`)。列内の `null` は受理する。
- `assess_session(finite_only_4, reps=5, ...)` → `required_reason='nonfinite_or_partial_output'`、
  `median=None`。**訂正 F が要求する「finite-only 列 + 元の `reps_expected`」で意図どおり動く。**
- `assess_session(finite_only_4, reps=4, ...)` → `required_reason=None`、`median=1234.5`。
  **落とした本数の分だけ `reps` を減らすと、欠測が消えて健全な session に見える。**
  契約 v3 はこの短絡を明文で禁じる。
- 不変条件 `count(non-null) + nonfinite_count + exec_failures == reps_expected` は
  4 + 1 + 0 == 5 で成立する。前 wave が指摘した自己矛盾 (X-7) は解消している。

---

## P-5 訂正 B / 裁定 3 (封印の発行経路) — 現物の seam を測った

- `_AttemptState` (`s8b_attempt_registry.py:165`) が持つ digest は
  `classification_receipt_sha256` / `classification_event_sha256` / `observation_event_sha256`。
  契約 v2 が書いた `observation_start_event_sha256` とは**綴りが違う**。X-3 が再現した。
- `_launch_floor_attempt_for_test()` は production と同じ `_launch_floor_attempt()` 本体を呼び、
  `registry` と `capture_measure_point` を注入できる。**adapter を経由させるだけでは seam は閉じない** —
  注入された偽 registry も adapter の位置に立てる。
- ただし現行の handle 機構 (`_new_handle` / `_require_handle`) が使える前例になる。
  handle は module 私有の token object を `_seal` に持ち、`_require_handle` が
  厳密型・token 表・weakref 同一性・state fingerprint・attempt key の 5 点を照合する。
  **偽 registry が interface を真似ただけでは validated capability を作れない**形はこれで作れる。
- 裁定 3 が脅威から除外した「同一 process の module 改変・private issuer の直呼び・reflection」は
  この前例でも閉じない。契約 v3 は D387 と同じく**主張せず明記する**。

---

## P-6 訂正 D (E1 の枝順) — campaign の実 semantics を読み直した

`s8b_floor_campaign.py` の `_run_session` は次の順で `excluded_reason` を決める。

1. `probe_after["competing"]` → 競合
2. `measure_error is not None` → 起動失敗
3. `exec_failures >= self.reps` → 起動失敗
4. `exec_failures > 0 and derived_reason is None` → 起動失敗
5. `rep_integrity_failures > 0 and derived_reason == partial` → 部分出力
6. それ以外 → `derived_reason` (null / partial / performance)

前 wave の X-5 の測定と一致する。契約 v3 はこの 6 枝を正本にする。

---

## P-7 pin 閉包 (DW-O09) と gate 入力の実在 (DW-O13)

> **erratum (段 4 で追記、規律 7)。** 下の列挙は identifier / path / whole-file hash の
> 3 種類しか引いておらず、**閉包として不完全だった。** レンズ B の B-07 が
> `test_official_perf_closure.py` の semantic inventory を見つけた。
> `:44` の `_REVIEWED_PERF_FILES` は exact frozenset で、`:531` の `_production_perf_files()` が
> production を AST 走査し、`:903` が集合等値を assert する。**新しい leaf に perf 述語の分岐を
> 置くと `unreviewed:` で落ちる。** 名前でも path でも hash でも掛からない型の pin である。
>
> また下の「変更予定 7 file」は、段 2 plan が確定させた 8 file (test 4 本を含む) を覆っていない。
> レンズ B が 8 file すべてで whole-file hash を独立再検索し、0 件を確認した。
> 対応は `contract-v3.1.md` の 9 節と `plan-v2.md` の 8 節にある。

- 新しい識別子 (`terminal_evidence_sha256` / `measurement_retry_reason` /
  `retryable_reason_field` / `s8b_terminal_evidence` / `SealedTerminalEvidence` /
  `ValidatedTerminalEvidence`) を repo 全体で検索した。hit は docs と insight だけで、
  test・凍結台帳・trust root の pin は 0 件。
- `terminal-evidence` の文字列は `floor_liveness.py:446` と `dispatch_compute.py:2128` に
  あるが、いずれも別語彙 (job が終端証跡を残さない場合の理由コード) で衝突しない。
- 変更予定 7 file の sha256 を計算し、その値を repo 全体で検索した。**file 全体 hash の
  golden pin は 0 件。**
- `floor-attempt-registry-receipts` を pin するのは `s8b_attempt_profile.py` と
  `test_s8b_attempt_registry.py` だけで、凍結 manifest 側の pin は無い。
- **`attempt_registry_core.py` には生きた source 走査がある。**
  `test_reflux_formal_consumer.py` の `WAVE_PRODUCTION_FILES` (15 file、件数 assert つき) が
  AST を読み、`aborted=False` の keyword 呼び出しと `OriginSealed(False, ...)` を禁じている。
  C1b の変更はこの 2 形を書いてはならない。
- `launch_floor_attempt()` の production 呼び手は **依然 0 件** (自 module と test seam のみ)。
  したがって本単位の gate 入力は fake 由来の値域しか実測できない。E1 の枝は campaign の
  実 semantics へ静的に照合するに留め、「実環境の値域」を主張しない。
