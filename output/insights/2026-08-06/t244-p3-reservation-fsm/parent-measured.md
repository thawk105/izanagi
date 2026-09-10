# 段 1 前提実測 — [T-244] P3 reservation FSM (U-5)

wave: `dev-wave-t244-p3-reservation-fsm` / branch: `worktree-dev-wave-t244-p3-reservation-fsm`
起点 local main: `cfda4abe`。行番号はこの起点 tip の実測値である。

すべて親がこの worktree の実コードを読んで確認した。docs の記述は根拠にしていない (F1)。

## N1 — 現 FSM の相と遷移

`orchestrator/campaign/reflux_origin_ledger.py:1063` `_apply_event` が唯一の遷移器。相は
`EMPTY → IDLE → BATCH_COMMITTED → RESULTS_PREPARED → IDLE → … → ORIGIN_SEALED` の 5 種。
genesis は `event=None` (`:1070-1075`)。`OriginSealed` は `phase != "IDLE"` を拒否 (`:1304`)。

## N2 — 予算消費点は `BatchCommitted` 受理時**だけ**である

`:1114-1119` — `Imax` 検査・`Qmax` 検査・`iterations_used += 1`・`queries_used += cardinality` の
4 つがすべて `BatchCommitted` の枝にある。他のどの event でも counter は増えない。
**したがって U-5 の裁定前提「(b) caller の制御流だけでは kill-before-commit を塞げない」は現コードで真である** —
候補生成後・commit 前に process を落とせば、消費された予算は 0 のままになる。

## N3 — 受理集合の正本は 3 関数 + 2 射影

| 面 | 位置 | 役割 |
|---|---|---|
| wire 出力 | `:725` `_event_payload` | event → (event_type, payload) |
| wire 入力 | `:785` `_event_from_payload` | (event_type, payload) → event。未知 type は `unknown event type` |
| 意味 | `:1063` `_apply_event` | 相遷移・予算・不変条件 |
| state commitment | `:992` `_semantic_object` → `:1023` `_semantic_sha` | CAS の対象 |
| pre-seal 射影 | `:1027` `_preseal_semantic_sha` | seal 前に漏らしてよい部分集合 |

event union は `:531-536` の 4 型。`__all__` は `:43-68`。

## N4 — query partition の不変条件

`:1039` `_assert_query_partition` は
`queries_used == sealed_queries + tombstoned_queries + pending` を要求し、
`pending = len(open_batch["members"])` である (`:1041-1042`)。
**予約 event は member を持たないため、この不変条件は必ず拡張を要する。** 拡張しないと
予約受理の直後に partition が破れて `_fail` する。

## N5 — repo 内 consumer は 3 つだけ

`grep -rn "reflux_origin_ledger" --include=*.py` の実測 (worktree 内、`.claude/worktrees` と
`external/` を除く) は次の 3 件のみ。

- `orchestrator/campaign/reflux_origin_ledger.py` (自身)
- `orchestrator/tests/test_reflux_origin_ledger.py` (2857 行)
- `output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py` (使い捨て probe、D183/D184)

**production caller は存在しない。** `read_origin` / `commit_event` / `read_sealed_batch`
(`:3100-3136`) を呼ぶ非テストコードは repo 内に無い。

## N6 — 凍結 bytes の pin は無い (DW-O09 / DW-O10 は不成立)

`FROZEN_MANIFEST` (`orchestrator/tests/test_frozen_artifacts.py:38`) の 23 key はすべて
`output/s1-freeze/`・`output/s8b-freeze/`・`output/insights/2026-07-16_*` 配下で、
ledger module も authority JSON も含まない。role 名 key の review ledger 側 pin も無い (F30 の
key 側検索も実施)。よって本 wave は凍結成果物の bytes を変えず、`DW-O09` / `DW-O10` は成立しない。

## N7 — D96 の境界テストは実在し、位置も特定済み

`orchestrator/tests/test_reflux_origin_ledger.py:658`
`test_v02_exact_five_phase_five_event_transition_matrix_and_no_legacy_tombstone` が
**5 相 × 5 event の受理/拒否行列を全数で固定している** (`allowed` 集合 `:675-681`)。
これが D96 が言う「その受理集合を固定している境界テスト」であり、同一変更単位で追随させる対象である。
加えて `test_v01_literal_manifest_event_state_and_receipt_goldens` (`:525`) が literal golden で
state commitment を固定しているため、`_semantic_object` の field を増やせば同時更新が要る。

## N8 — codec feasibility が batch あたり **3 frame** を前提にしている

`:1883` `_feasibility_batch_frames` は 1 batch = `BatchCommitted` / `BatchResultsPrepared` /
`BatchSealed` の **3 frame** を返し、`:1923` `_affine_batch_bytes` がそれを batch 数と member 数の
アフィン式で origin 上限 bytes に積み上げる。この値は `_MAX_LEDGER_BYTES` (64MiB) との
feasibility 判定 (`:1964` `_check_budget_codec_feasibility`) に使われる。

**予約 event を足すと 1 batch あたりの frame 数が増えるため、この式を更新しないと上限 bytes を
過小評価する。** テスト側には独立実装の複製があり (`test_reflux_origin_ledger.py:193`
`_independent_worst_case_batch_frames`、`:242` `_independent_origin_ledger_upper_bytes`)、
こちらも同一変更単位の対象である。これは path 検索では出てこない consumer である。

## N9 — 正例を作れる artifact path は fixture store である (DW-G04)

本番 authority は `origins: []` で production 初期化は明示禁止 (D183)。したがって新 event の
**正例**は本番経路では作れない。作れるのは fixture store で、既存の実走経路が
`ledger._fixture_store_for_test(repo, "HEAD", initialize=True)`
(`test_reflux_origin_ledger.py:373-374`) として実在し、`_commit_locked` を直接叩く
`_commit` helper (`:382-399`) と full positive cycle
(`test_v16_commit_reveal_privacy_order_exact_class_and_positive_cycle`, `:1930`) がある。
**DW-G04 の「発火条件を満たす既存 artifact path」はこれを指す。** 本番 provisioning は開けない。

---

# erratum (段 2 プランの指摘を親が実コードで再確認して確定した訂正)

段 2 の read-only プランが N3 / N5 / N7 の誤りを 3 件指摘した。親が起点 tip の実コードで
1 件ずつ再確認し、**3 件とも指摘が正しい**と判定した。以下を正本とする。

## E1 — N3 の受理集合面は 5 面ではなく **6 面** である (N3 の訂正)

`_prepared_payload_projection` (`reflux_origin_ledger.py:2680`) が漏れていた。この関数は
**durable な pre-event record に載せてよい payload bytes だけを返す** 射影であり、
`origin-sealed` については key を明示列挙している (`:2697-2704`)。
したがって `OriginSealed` の payload を拡張するなら、ここも同じ変更単位で追随しないと、
新 counter が prepared record から落ちて `prepared operation request mismatch` になる。
**path 検索でも event_type 文字列検索でも見つかるが、親の N3 は列挙し損ねていた。**

併せて `__all__` の範囲は `:43-70` である (親は `:43-68` と書いた。末尾の
`RefluxOriginLedgerError` と閉じ括弧を含めていなかった)。実害のない範囲の誤りだが訂正する。

## E2 — consumer 閉包に **transitive consumer** が 1 件漏れていた (N5 の訂正)

`orchestrator/tests/test_t244_p3_liveness_probe.py:17` が
`output/insights/2026-08-05_t244-p3-liveness/liveness_probe.py` を **subprocess で起動**し、
rc=0・`stage: complete` 1 回・チェック `C-a`〜`C-e` の全 PASS を要求する。
この test は ledger module 名を一切含まないため、`grep "reflux_origin_ledger"` では出てこない。

probe 側は `BatchCommitted → BatchResultsPrepared → BatchSealed` を直接発行しているので、
**予約を必須にした瞬間にこの node が赤くなる。**

`DW-O09` の分類軸を当てると次のようになる。

| 出現 | 分類 | 本 wave での扱い |
|---|---|---|
| `liveness_probe.py` | **live copy** (tracked な pytest node が毎回実走する実行可能 probe) | FSM 変更へ追随させる。実装面なので Codex 実装子が書く |
| `receipt` / `preview-wire-11111.json` | **歴史記録** (2026-08-05 の測定結果と、その入力 wire) | **不変**。過去の測定を遡って書き換えない |

「production caller は存在しない」という N5 の結論自体は変わらない (この consumer は
テスト経路であって production caller ではない)。誤っていたのは**閉包の網羅性**である。

## E3 — V01 の state golden は field 追加では変わらない (N7 の訂正)

`test_reflux_origin_ledger.py:613` は `ledger._state_commitment(..., origin_states={})` を
渡しており、origin が 1 つも無い状態の commitment を固定している。よって
`_semantic_object` に field を足しても V01 の state preimage は変わらない。
親は「field を増やせば V01 golden の同時更新が要る」と書いたが、**因果が誤り**である。
手書き semantic object を持つのは V13 (`:1620` 付近) と V16 (`:2077` 付近) の方である。
V01 が変わるのは、schema ID を変えた場合の event/head/state domain 由来だけである。

