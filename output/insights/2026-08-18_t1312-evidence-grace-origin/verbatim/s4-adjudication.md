# 段 4 裁定 + plan v2 — [T-1312] D498

## 所見の裁定

| ID | 判定 | 採否 | scope | 理由 |
|---|---|---|---|---|
| S1 / L1 (spawn 区間に時間差が無く `preflight` 起点の変異が通る) | **real** | 採用 | 内 | 両レーンが独立に同一欠陥を指摘。恒真ゲートになる。 |
| S3 (attempt 2 を判別していない) | **real** | 採用 | 内 | F57 の実機序は attempt 2。attempt 1 だけの検査では退行を殺せない。 |
| L4 (猶予 1.0 秒固定 fixture が起点移動で max-wall 側へ倒れうる) | **real** | 採用 | 内 | 本変更が**新しいフレーク形態を導入する**経路。[T-1298] の修理は D498 の実装で閉じる以上、ここで閉じる。 |
| L2 / S4 (F57 赤が消えるという主張が過大) | **real** | 採用 (文言) | 内 | コード変更ではなく記録の是正。段 7 で親が書く。 |
| S5 (P3 の根拠が path 検索のみで `DW-O09` の禁止形) | **real** | 採用 (文言) | 内 | sol の追加監査結果へ差し替える。 |
| S2 (`max_wall_clock_s` は物理的総所要を有界化していない) | **real** | **不採用** | **外** | D498 は `max_wall_clock_s` に触らないと明記。裁定パッケージでユーザーへ返す。 |
| L3 (既定 90 秒で max-wall との発火順が変わる) | **real だが欠陥ではない** | 不採用 | — | D498 が「総所要は `max_wall_clock_s` が有界化する」と定めた帰結そのもの。受理集合は広がらず (先に max-wall が止める) 絶対規律 2 に抵触しない。段 7 に帰結として記録する。 |
| L5 (D286 の文言との相互参照が無い) | real | 不採用 (nit) | — | canonical 台帳の直接編集はしない。段 7 の worklog に 1 行残す。 |

## 不変条件の是正 (S2 を受けて)

親 brief の「総所要の有界化は `max_wall_clock_s` が担う」は、
**receipt の admission bound** (`actuals.wall_clock_s <= limit` を checker が再検査する
`tools/codex_worker_launch.py:3268-3284`) の意味で読む。物理的な launcher 総所要の hard cap では
ない。この読み替えは D498 の意味を変えない。

## plan v2 (段 2 プランからの差分)

段 2 プラン (`plan.md`) を基礎とし、次を差し替える。

### v2-1. 本体変更 (プランどおり、変更なし)

`tools/codex_worker_launch.py:1793-1800` を次の形にする。

```python
spawn_completed_ns = _monotonic_ns()
if attempt_diagnostics is not None:
    attempt_diagnostics.note_boundary("spawn_completed", spawn_completed_ns)
evidence_deadline_ns = (
    spawn_completed_ns
    + decimal_seconds_to_nanoseconds(args.evidence_grace_s)
)
```

`state.started_ns` は attempt wall clock (`:2004`) の起点として据え置く。
`AttemptState` / 診断 / receipt / sidecar の schema と field 集合を増やさない。

### v2-2. 判別テストの是正 (S1 / L1)

論理時計を **preflight 区間と spawn 区間の両方**で進める。両区間に**異なる正の値**を入れる。

- preflight 区間: `+0.10` 秒 (`validate_installation` の wrapper で進める)
- spawn 区間: `+0.02` 秒 (`Popen` から `read_pid_identity` 完了までの間で進める)
- 猶予: `0.05` 秒
- poll 区間: 1 poll あたり `+0.01` 秒

これにより 3 つの起点が分離する。

| 起点 | `supervision_drain` |
|---|---|
| `spawn_completed_ns` (正) | `0.05` |
| `preflight_now_ns` (誤) | `0.03` |
| `state.started_ns` (旧) | 最初の poll で満了済み |

テストは `phase_duration_s["attempt_preflight"] == 0.10`、
`phase_duration_s["spawn"] == 0.02`、`phase_duration_s["supervision_drain"] == 0.05` を
すべて assert する。前 2 者は時計注入が実際に効いたことの自己検査であり、
効かなければ黙って通らず声を上げる。

spawn 区間へ時間を注入する seam は実装子が実在を確認して選ぶ。候補は
`LAUNCHER.read_pid_identity` の monkeypatch (実値を返しつつ論理時計を進める wrapper)。
実在しない seam を前提にしてはならない。

### v2-3. attempt 2 の判別 (S3)

`max_attempts=2`、`FAKE_SEQUENCE` で attempt 1 を retry させ、attempt 2 で evidence を欠く走を
組む。既存の同型は `orchestrator/tests/test_codex_worker_launch.py:3415-3417`
(`FAKE_SEQUENCE="retry_reject,normal"`)、`:4453-4458`
(`FAKE_SEQUENCE="retry_reject,retry_wait"`)。
attempt 2 でも新起点が使われることを sidecar の `attempts[1]` で検査する。

これがないと「attempt 1 は新起点、retry は旧起点」の変異が生き残る。F57 の実機序は attempt 2 で
あり、この変異は**成果物へ到達しない実装**である。

### v2-4. 既存 evidence fixture の hardening (L4)

`_base_command` の新 kwarg を使い、evidence 関門を検査する既存テストの猶予を `1.0` から
`0.3` へ下げる。対象は次の 3 本 (実装子が実際の node を確認して確定する)。

- `test_rollout_missing_after_grace_is_stopped_and_not_accepted`
- `test_thread_missing_after_grace_kills_process_group`
- `test_evidence_forced_stop_propagates_unknown_residual_to_sidecar`

理由: 起点移動後の evidence deadline は `attempt 開始 + preflight + spawn + 猶予` に位置する。
F57 実測の preflight 上限 1.11 秒と猶予 1.0 秒では、`max_wall_clock_s=3` の余裕が
0.9 秒まで縮む。負荷が重い日には max-wall が先に発火し、`evidence_forced_stop` を検査する
これらのテストが**別の理由で赤くなる**。猶予を 0.3 へ下げれば余裕は 1.6 秒へ戻る。
これは fixture の hardening であり、production の受理集合を触らない。

**猶予を下げた結果、既存 assertion が別の理由で落ちないことは親が実走して確かめる。**
落ちるなら値を上げ直す。実装子は落ちた事実を隠さず報告する。

### v2-5. `tools/dev_wave_codex.py` (P2 維持)

help 文言に「子の起動完了時を起点とする」を明記する。既定値導出・上限検証・argv 転送は変えない。
`orchestrator/tests/test_dev_wave_codex.py` の help block assertion に新文言を足す。

## 変異事前登録 (DW-M01)

| ID | 変異位置と内容 | 殺す node | 単一理由性の根拠 |
|---|---|---|---|
| M1 | `codex_worker_launch.py` deadline 起点を `spawn_completed_ns` → `state.started_ns` (**wave 前の実コードの形**) | 新設 spawn 起点判別テスト | 前後に同じ入力を拒否する層は無い。`evidence_forced_stop` の発火時刻だけが変わる。 |
| M2 | 同起点を `preflight_now_ns` へ | 同上 (`supervision_drain == 0.05` が `0.03` になる) | 同上。S1/L1 が指摘した誤起点。 |
| M3 | `spawn_completed_ns` の取得を `attempt_diagnostics is not None` の中へ戻し、外では `state.started_ns` へ fallback | 診断なし経路の直接 `_attempt_loop` テスト | 診断有無でしか分岐しない。他層に同じ判定は無い。 |
| M4 | `attempt_index == 1` のときだけ新起点、retry は `state.started_ns` | attempt 2 判別テスト | attempt 1 側の検査は通るため、赤理由が attempt 2 の起点に一意化する。 |
| M5 | 診断境界と deadline で `_monotonic_ns()` を別々に呼ぶ | `test_launcher_diagnostics_production_phase_wiring_has_exact_durations` | 既存 exact duration テストが 1 サンプル増を検出する。 |

M1 は変更前 main の実コードの形そのものであり、必ず含める。

正例 (過剰拒否の検出) は登録しない。本 wave は受理集合を**縮小しない**ため `DW-M01` の
正例要求は発火しない。

## scope 外 real 所見 — ユーザーへ返す裁定パッケージ候補

**S2: `max_wall_clock_s` は物理的な launcher 総所要を有界化していない。**

- 事実: 最初の wall 検査より前に各 5 秒 timeout の preflight が走り、limit 到達後も
  termination grace と reap が続く。成功経路でも最終 latch 後の receipt 公開に wall 再検査が
  無い。receipt 自身は scope を `launcher_start_to_receipt_fields_finalized` と宣言している。
- 現状の意味: `max_wall_clock_s` は **receipt の admission bound** であり、
  process の物理的 hard cap ではない。
- 択一: (a) 現状の意味を docs へ明記して閉じる。(b) 物理的 hard cap を要求し、
  外部 watchdog まで scope に入れる。
- 親の推奨: **(a)**。D498 は起点の意味是正であり、総所要の意味論変更は別問題。
  (b) は外部 watchdog という新機構を要し、絶対規律 5 (盛らない) に抵触する。
