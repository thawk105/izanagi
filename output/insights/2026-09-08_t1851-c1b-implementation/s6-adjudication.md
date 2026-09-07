# [T-1851] C1b 段 6 裁定 — 敵対レビュー 2 本の所見を real/refuted で裁く

対象 commit は `d03b26773` (leaf) と `d52b2f833` (統合)。
逐語は `verbatim/s6-review-a.md` (レンズ A = 機構が発火するか) と
`verbatim/s6-review-b.md` (レンズ B = 逐条適合と波及)。

**両レンズとも判定は `no`。** A が blocker 5 / must-fix 1、B が blocker 2 / must-fix 2 を出し、
重複を除くと **blocker 6 件・must-fix 2 件**である。**全件を real と裁定し、全件 fix する。**

## 1. なぜ全件が scope 内か (DW-G05)

契約 0 節が守ると宣言した対象は 1 つだけである — **「試行 proof chain に虚偽の terminal 事実が
入ること」**。所見はすべて、その 1 点を実際に破る経路である。成果物への影響は
「certified 選択の根拠になる試行台帳へ、測定していない値・改竄された identity・
緩めた閾値による `observed` 判定が載る」であり、`DW-G05` の要求を満たす。

**6 件の blocker は 1 つの型に集約する** — **launcher が可変で呼び手所有のオブジェクトを
未信頼の terminal builder へ渡し、その後で権威として読み直している。**
したがって fix も 1 つの構造変更に集約する (5 節)。

## 2. blocker (6 件・全件 real)

| # | 出所 | 内容 | 親の裏取り |
|---|---|---|---|
| R-1 | A-1 | **test seam が real registry への委譲を塞いでいない。** capture と probe だけ偽装した fake を渡すと reserve / classify / begin は real adapter が発行するので handle の 5 点照合を通過し、`record_sealed_attempt_terminal()` が偽 terminal を公開する。reflection も private issuer 直呼びも不要 | 契約 6.2 が「adapter を経由させるだけでは塞がらない」と名指しした箇所そのもの。**契約が明示的に塞げと要求している以上、6.4 の除外 (private issuer の直接呼出し) には当たらない** |
| R-2 | A-2 | **terminal builder の後に `reservation.protocol` を読み直すので、builder が `session_cv_max` を緩められる。** 分散超過の session が `observed` になる | **親が現物で確定した。** launcher `:608` で digest 検査 (副作用前・1 回) → `:1004` builder 実行 → `:1022` seal → leaf `:727/:731` が `reservation.protocol` を再読し `_assess_finite_throughputs` へ渡す。D1113 の直接違反であり、**規律 2 (正しさゲートを緩める変異を許さない) にも抵触する** |
| R-3 | A-3 | **可変な probe / rep sink を builder へ渡してから権威として再読している。** 分類 receipt 内の `external_evidence_sha256` と照合しないので、観測していない probe bytes が封印される | R-2 と同型。`repetition_evidence` の tuple 内側も通常の dict |
| R-4 | A-4 | **duck-typed な `Mapping` が launcher gate と leaf に別の値を返せる。** `get()` に正値、`__iter__`/`__getitem__` に偽値を返す exact 30-key record で偽 `duration_s` と binary digest が通る | launcher `:838/:850` と leaf `:223/:745` が同じ record を別々に読む。TOCTOU |
| R-5 | A-5 / **B-1** | **`configuration_id` / `holdout_id` / `retry_ordinal` が real slot へ再束縛されていない。** leaf は呼び手が渡す `reservation.slot_id` と照合するだけ | **親が現物で確定し、2 レンズが独立に到達した。** leaf `:713-718` が `slot_id[0]/[1]/[4]` を権威にし、adapter `_assert_terminal_durable_identity` の `expected_values` (`:1332-1338`) と `key_expected` (`:1341-1343`) のどちらにも証拠側 3 field の照合が無い。契約 1.5 (a) 違反 |
| R-6 | B-2 | **`failure.stage == "capture"` かつ `launch_failures_count > 0` の矛盾を受理する。** 契約 1.2 は capture failure なら count 0 と明記 | B が副作用なしの直接 probe で受理を実測 (capture failure / count 1 / exec 3 / reps 3)。leaf `:500-527` の相互整合に該当検査が無い |

## 3. must-fix (2 件・全件 real)

| # | 出所 | 内容 | 裁定 |
|---|---|---|---|
| R-7 | A-6 / **B-4** | **`OSError` のサブクラスが正規化されない。** launcher は `except OSError` で `FileNotFoundError` を捕捉するが `type(exc).__name__` が具体名を残し、leaf の exact 3 語集合が拒否する | 2 レンズが独立に到達。**契約 4.2 の「launcher の捕捉集合が E1 の入力値域」を満たしていない。** v2 経路で `subprocess.TimeoutExpired` / `OSError` / `RuntimeError` の順に `isinstance` で基底カテゴリ名へ正規化する。**v1 経路の綴りは変えない** |
| R-8 | B-3 | **pre-probe 競合の正当な枝が terminal 化前に落ちる。** 競合時は capture を省くので measurement が `None` になるが、launcher `:963-977` が `failure is None` で `None` の座標を検査して例外を投げる | 契約 4.1 の枝 1 と 5.2 の「観測前・競合」行が**到達不能**になっている。座標検査を「capture を実行した failure 無しの経路」に限定する |

## 4. refuted / 不採用

**なし。** 両レンズの所見はすべて real と裁定した。

**両レンズが攻撃して破れなかった箇所** (証拠として記録する):

- S1 (`terminal-failure` 枝) と S2 (old / candidate replay) は恒真でも冗長 gate による見かけの
  kill でもなかった。`not-consumed` も同じ枝の正例・負例が対で存在する
- `ValidatedTerminalEvidence` へ素の `object()` token を入れる偽造は adapter 側の identity 検査で
  停止する。成功には reflection か private issuer の直接呼出しが要り、**契約 6.4 の除外内**
- 契約 7 の行と file の全件等値 11 項目は `finished_at` を含めて実装されている。no-follow
  regular file、filename、bytes digest、exact keys、canonical bytes、binding、row あり file なしの
  再検査も存在する
- `records` / `threads` / `workload` / `cell_id` / `attempt_id` / `mode` の durable claim 再照合は
  有効で、単純な terminal record 改変では破れない
- v1 の受理集合は静的に不変 (event key exact 24、retryable 集合 空、既定
  `retryable_reason_field="failure_reason"`)

**B が独立に再導出して親の段 1 実測と一致した数値** (規律 7 の裏取り):

- `campaign_record` は証拠側 30 / `_JOURNAL_KEYS["session"]` 30 で集合等値
- draft binding exact 9、3 digest key との積集合は空 (null ではなく欠落)、validated exact 12
- v1 terminal 24 key / v2 terminal 27 key、差集合はちょうど指定の 3 key
- E1 の枝順は契約どおり。`assess_session` へ元の `reps_expected` を渡している
- 触る 8 file の whole-file SHA-256 golden hit は base・HEAD とも 0 件
- perf semantic inventory は実測 43 file 対 reviewed 43 file で集合等値。**新 leaf は inventory に
  入っていない** (契約 9 節の要求どおり)
- reflux AST 走査に対し `aborted=False` keyword 0 件、`OriginSealed(False, ...)` 0 件
- 契約 8 節「採らないもの」(claim v4 / `_AttemptState.mode` / core 公開 API への capability 伝播) は 0 件
- 既存 test の意味変更は親が許可した 2 箇所だけ。skip・xfail・golden 更新・期待値緩和は無い

**呼出し閉包の 6 対 7 の食い違いは解消した。** 親の段 1 実測 (`_atomic_update` caller 6) は
**統合子が実装する前の木**を測った値であり、統合が 1 本足した結果 7 になった。B の独立計数は
実装子の報告値と全項目一致 (`_atomic_update_locked` 2 / `_atomic_update` 7 /
`_atomic_update_with_consumption_marker` 2 / transition callable production 7 + test 4 = 11 /
`record_attempt_terminal` production 4 + test 6 = 10)。

## 5. fix の方針 — 1 つの構造変更へ集約する

R-1〜R-4 と R-6 は「未信頼の builder に可変参照を見せ、後でそれを権威として読み直す」型である。
**個別に潰さず、次の 1 つの構造で閉じる。**

**副作用前に private canonical snapshot を作り、sealer はその snapshot だけを読む。**

- `protocol`、`perf_preflight_receipt`、`probe_before` / `probe_after`、`failure`、
  `launch_failures`、rep sink、`campaign_record` を、それぞれ**副作用より前に一度だけ**
  canonical bytes へ固める
- builder には**深い複製または read-only view** を渡し、snapshot 自体は渡さない
- `seal_terminal_evidence()` は snapshot から構築する。`reservation` を読み直さない
- `campaign_record` は**一度だけ** strict canonical snapshot へ変換し、launcher の facts 検査と
  sealer が**同一の snapshot** を見る (duck-typed Mapping の二重読みを無くす)
- 分類 receipt の `external_evidence_sha256` と terminal evidence の各 source digest を再照合する

R-5 は adapter に 3 行の明示検査を足す。R-7 は launcher の v2 発行経路で正規化する。
R-8 は座標検査の適用条件を狭める。

**変異の追加登録 (DW-M01。fix 前に登録する):**

| ID | 変異 | 期待する単一理由 |
|---|---|---|
| F1 | snapshot でなく `reservation.protocol` を再読する形へ戻す | R-2 の負例だけが拒否 |
| F2 | builder へ深い複製でなく元の可変 sink を渡す | R-3 の負例だけが拒否 |
| F3 | `campaign_record` の snapshot 化を外して二重読みへ戻す | R-4 の負例だけが拒否 |
| F4 | adapter の 3 identity 検査のうち 1 つを削除 (3 変異) | R-5 の各負例だけが拒否 |
| F5 | capture stage の `launch_failures_count == 0` 検査を削除 | R-6 の負例だけが拒否 |
| F6 | 例外名の正規化を削除 | R-7 の正例が赤になる |
| F7 | test seam の launcher-origin capability 検査を削除 | R-1 の負例だけが拒否 |

## 6. 停止条件

- 既存テストの期待値を変更しない。反転・緩和・skip・削除を禁じる。**赤になったら実装側が誤り。**
- 親が段 5 で許可した既存期待値の意味変更 2 箇所を超えない。
- 所有外 file に変更が要ると判明したら実装せず報告する。
- 契約の条項が実体化できないと判断したら、回避策を自作せず止めて報告する。
