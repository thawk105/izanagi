## 1. gate の実装案

行番号は現行 worktree 基準。変更は consumer とその test の 2 file に限定する。

`orchestrator/campaign/reflux_formal_consumer.py:1133` の直前に専用 helper を追加する。key 定数は trigger と共有せず、terminal helper 内の literal とする。`_wal_trigger`、`_wal_field`、既存の outcome 別判定式は **bytes を変更しない**。

```python
def _wal_terminal_shape_valid(records: Sequence[dict]) -> bool:
    terminal = records[-1]
    if {"variant", "stage", "env_tag", "ts", "payload"} != set(terminal):
        return False
    if type(terminal["variant"]) is not str:
        return False
    if type(terminal["env_tag"]) is not str:
        return False
    terminal_ts = terminal["ts"]
    if type(terminal_ts) not in (int, float):
        return False
    if type(terminal_ts) is float and not math.isfinite(terminal_ts):
        return False
    if type(terminal["payload"]) is not dict:
        return False
    terminal_count = sum(
        record.get("stage") in (STAGE_COMMIT, STAGE_ABORT)
        for record in records
    )
    if terminal_count != 1:
        return False
    return terminal.get("stage") in (STAGE_COMMIT, STAGE_ABORT)
```

現行 `:1142` の `terminal = wal_records[-1]` 直後、`:1143` の `attempt = ...` より前に追加する。

```python
        _require(FormalReasonCode.FC07, _wal_terminal_shape_valid(wal_records))
```

判定順は、exact keys → variant → env_tag → ts 型 → ts 有限性 → payload 型 → terminal 件数 → 末尾性 → 既存 attempt 一致 → 既存 outcome 別 stage／payload 検査。

- records の非空・各要素 dict は resolver `:1632–1635` が保証する。helper に別の空入力 gate は足さない。
- 件数は **root stage** で数える。tuple membership により、canonical JSON で到達可能な list／dict stage でも hashability 例外を出さない。
- terminal payload の key 集合は閉じない。trigger 専用の `{build_attempt_id, trigger_gate_binding}` 検査は写像しない。
- 末尾性項は既存 outcome 別 stage 判定と過剰決定になる。ただし P1 を helper 内で明示するため残し、その項だけの除去は等価変異として登録する。
- key 集合を左辺に置くのは、変異 `!=` → `not <=` が正しく「余分 key 許容」になるため。逆向きでは欠落許容になってしまう。

## 2. test 一覧

追加位置は `orchestrator/tests/test_reflux_formal_consumer.py:1652` 付近、既存 FC07 terminal test 群。helper は既存 `:468` `_rewrite_wal`、`:507` `_projection_records`、`:688` `_assert_reason` を変更せず使う。

以下の **共通到達根拠 R** を各行に適用する。

1. `_projection_records(case, 0)` の複製を編集する。`_rewrite_wal` が source canonical list、projection、byte 範囲、参照 hash、record／ledger 側を同期する。
2. resolver は全 record の root 優先 attempt を確認する。canonical-list 経路なので `wal.parse_line` の外枠検査は通らない。
3. FC05B の内容参照・source 一致・範囲検査を満たす。execution provenance と campaign binding の入力・配置は変えない。
4. FC05A の physical attempt 群、FC05C の trigger 1 件と binding、FC06 の topology は変更しない。
5. verifier policy も変更しない。新 gate を仮に外した場合にも、既存 FC07 attempt 一致が成立するよう構築する。実装後は新 gate がこの attempt 判定より先にある。

表の名前は `test_` を含む実装予定名。parameter ID も固定する。

| 名前 | 組み立て | 期待 | 手前で落ちない根拠 |
|---|---|---|---|
| `test_fc07_rejects_terminal_root_attempt_shadow` | terminal root に正しい attempt、payload attempt に `"fixture-shadow-attempt"` | FC07 | R。`_rewrite_wal:474–476` は root を更新して `continue` するため payload の別値が残る。resolver と既存 FC07 attempt は root の正値を読む |
| `test_fc07_rejects_terminal_extra_root_key` | terminal に `extra=1` | FC07 | R。attempt は payload の正値。extra は resolver・FC05C・FC06 の入力判定に影響しない |
| `test_fc07_rejects_terminal_missing_root_key[env_tag/ts/variant]` | 3 parameter node。指定 root key を `del` | FC07 | R。いずれも attempt 解決に使われない。canonical-list 経路で欠落を保持できる |
| `test_fc07_rejects_terminal_invalid_outer_type[ts-bool/ts-str/variant-int/env-tag-none]` | 4 node。順に `True`、`"1788580082.583126"`、`1`、`None` | FC07 | R。すべて canonical JSON 値で、attempt と trigger は不変 |
| `test_fc07_rejects_payload_only_terminal_stage` | `terminal["payload"]["stage"] = terminal.pop("stage")` | FC07 | R。payload attempt と既存 verify は保存。root stage を使う上流検査は trigger 判定だけで、この record は trigger にならない |
| `test_fc07_rejects_duplicate_abort_terminals` | terminal を deepcopy して `[trigger, abort, abort]` | FC07 | R。両 abort の attempt は同一。projection 内の record 増加は、異なる projection 間の byte 範囲重複ではない |
| `test_fc07_rejects_commit_before_abort_terminal` | 中間に exact 5 key の commit を追加。payload は正 attempt と `verify_configs=["legacy","s2"]`。末尾 abort は保存 | FC07 | R。commit は trigger family に属さず、resolver は stage と outcome の対応を検査しない。末尾 abort の attempt・witness は正常 |
| `test_fc07_rejects_nonterminal_after_abort` | `[trigger, abort, build_start]`。最後は abort の deepcopy の root stage だけ `"build_start"` に変更 | FC07 | R。末尾も正 attempt。terminal count は 1 であり、末尾性を明示的に検査する例になる |
| `test_fc07_accepts_float_timestamp_abort_terminal_shape` | fixture abort の root ts を `1788580082.583126` に変更 | P6_UNAVAILABLE | R。既存 witness payload を保存し、有限 float を新 gate が通す |
| `test_fc07_accepts_nonterminal_extra_root_key` | `[trigger, build_start, abort]`。中間 record に payload attempt と `extra=1` を持たせる | P6_UNAVAILABLE | R。中間 stage は trigger／terminal のどちらでもない。P5 の「非 terminal に外枠 gate を広げない」を固定する |
| 既存 `test_fc07_accepts_production_commit_terminal_shape` | `:1654–1679` を維持 | P6_UNAVAILABLE | accepted の record／member を既存 helper で同期し、commit payload の verifier 順序も正常 |
| 既存 `test_exact_fixture_contract_reaches_only_p6_unavailable` | 無変更 | P6_UNAVAILABLE | fixture 全体の既存正例。整数 ts の受理も残る |

新規は **15 node＝負例13＋正例2**。欠落と型違いを parameter 化すると、新規 test 関数は10本となる。

負例は `_assert_reason(case, C.FormalReasonCode.FC07)`、正例は既存 commit test と同じく `type(result) is C.P6Unavailable` と reason code の両方を検査する。

**terminal payload 型述語を単独で露出する負例は到達不能なので追加しない。**

- 非 dict payload・root attempt 無し：resolver の attempt 混在検査で FC05B。
- 非 dict payload・root attempt 有り：exact outer keys で FC07。payload 型述語だけを弱めても通らない。
- 非有限 ts：strict canonical JSON 検査より後に到達不能。FC07 負例として作らない。
- JSON 重複 key：strict parser が拒否するため、P1 の record 重複とは別。

float abort 正例は **production の外枠に対応する fixture 正例**と呼ぶ。rejected payload 全体の production producer が存在する証明にはしない。

## 3. 変異 matrix 候補

以下の `old`／`new` は consumer の1行単位。インデントは元の行を維持する。M02 のみ2行の置換を同一 mutant 内で順に適用する。

| id | old | new | 期待 | 殺す test | 等価なら理由 |
|---|---|---|---|---|---|
| M01：B-057-M5 | `_require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_ABORT)` | `_require(FormalReasonCode.FC07, _wal_field(terminal, "stage") == STAGE_ABORT)` | SURVIVED＝等価 | — | exact keys 通過後は root stage が必ず存在し、fallback と直接参照は同値 |
| M02a：合成の gate 無効化 | `_require(FormalReasonCode.FC07, _wal_terminal_shape_valid(wal_records))` | `_require(FormalReasonCode.FC07, True)` | M02全体で KILLED | `test_fc07_rejects_payload_only_terminal_stage` | M02b と合成 |
| M02b：合成の M5 | `_require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_ABORT)` | `_require(FormalReasonCode.FC07, _wal_field(terminal, "stage") == STAGE_ABORT)` | 同上 | 同上 | gate 全体を外すと payload stage を読み、既存 attempt・verify が通って P6Unavailable に至る |
| M03：superset 許容 | `if {"variant", "stage", "env_tag", "ts", "payload"} != set(terminal):` | `if not {"variant", "stage", "env_tag", "ts", "payload"} <= set(terminal):` | KILLED | extra root key、root attempt shadow | — |
| M04：ts bool 許容 | `if type(terminal_ts) not in (int, float):` | `if type(terminal_ts) not in (int, float, bool):` | KILLED | `test_fc07_rejects_terminal_invalid_outer_type[ts-bool]` | — |
| M05：件数検査除去 | `if terminal_count != 1:` | `if False:` | KILLED | duplicate abort、commit before abort | — |
| M06：gate 無効化単体 | `_require(FormalReasonCode.FC07, _wal_terminal_shape_valid(wal_records))` | `_require(FormalReasonCode.FC07, True)` | KILLED | root shadow、extra、欠落3、型違い4、重複2 | — |
| M07：payload 型検査除去 | `if type(terminal["payload"]) is not dict:` | `if False:` | SURVIVED＝等価 | — | root attempt 無しは上流 resolver、root attempt 有りは先行 exact keys で拒否 |
| M08：有限性検査除去 | `if type(terminal_ts) is float and not math.isfinite(terminal_ts):` | `if False:` | SURVIVED＝等価 | — | 非有限値は上流 strict JSON が拒否 |
| M09：末尾性項除去 | `return terminal.get("stage") in (STAGE_COMMIT, STAGE_ABORT)` | `return True` | SURVIVED＝等価 | — | 後続の accepted→COMMIT／rejected→ABORT 判定が同じ末尾条件を要求する |
| M10：variant 型検査除去 | `if type(terminal["variant"]) is not str:` | `if False:` | KILLED | `test_fc07_rejects_terminal_invalid_outer_type[variant-int]` | — |
| M11：env_tag 型検査除去 | `if type(terminal["env_tag"]) is not str:` | `if False:` | KILLED | `test_fc07_rejects_terminal_invalid_outer_type[env-tag-none]` | — |

**11 mutant、12置換操作**。予測は KILLED 7、等価 SURVIVED 4。

M01 は既存 B-057-M5 の式 `terminal.get("stage") == STAGE_ABORT` → `_wal_field(terminal, "stage") == STAGE_ABORT` をそのまま含む。payload-only stage は新 gate の key 集合だけでなく件数／末尾性にも抵触するため、M02 は key 検査だけでなく **helper 呼出し全体**を無効化する。

一意性については、提案行は次のように trigger の同文を避けている。

- key 検査は literal 左辺・`terminal` 右辺。
- ts は `terminal_ts`。
- variant／env_tag／payload は `terminal[...]`。
- 件数は `terminal_count`。
- gate 呼出しと abort `_require` はそれぞれ専用の1行。

新規 helper に `terminal.get("stage") == STAGE_ABORT` は追加しない。M02a 適用後も M02b の old は変わらない。他の mutant は修理後 baseline から独立に作成する。実装後、各適用時点の累積 source で `source.count(old) == 1` を確認する。

殺す test 名は静的予測であり完全 kill 集合ではない。paired 全件を走査するため、既存 test も追加で kill し得る。親の probe 走で完全集合を確定する。

## 4. pin 閉包

| 対象 | 独立確認と結論 |
|---|---|
| 変更2 file 自身の hash | 現物の SHA-256 と Git blob hash を計算し、tracked file 全体を `git grep -F` で検索。両 file とも一致0件。既存 hash literal の更新は不要 |
| `reflux_origin_fixture_baseline.json` | builder 出力の canonical hash／byte length の pin。builder は consumer を import せず、今回 builder と生成入力を変更しないため不変 |
| `test_reflux_origin_fixture_builder.py:107–119` | baseline 全 entry を builder 出力から再計算する検査。入力不変なので期待値の変更不要 |
| `test_reflux_result_evidence.py:39–42` | raw record、ledger digest、salted commitment、wrong-domain の4 golden は fixture 出力に依存する。consumer helper 追加と test 内の一時的な WAL 編集には依存せず、不変 |
| 同 test `:517` の `len(actual) == 1848` | canonical fixture record の byte length。fixture builder 不変なので不変 |
| consumer test `:32–48`、`:2286` の15 production file 閉集合 | module を追加しないため、本数・集合とも不変。既存 AST 検査の対象に helper が加わるが、禁止構文を導入しない |
| `acceptance_duration_ledger.json` | nodeid→所要時間の履歴。source hash／行数 pin ではない。新規15 node の履歴は無いが、`conftest.py:1739–1760, :1800–1827` に未知 node の扱いがあるため本 wave で更新しない |
| ソース行番号・過去の passed 本数 | 今回の追加で現物の行数と collected 数は増える。過去の実測記録を更新する対象ではない。新しい実測本数は親が取得する |

test による `_rewrite_wal` は個別 case の一時成果物を再生成するだけで、凍結 baseline を再生成する変更ではない。**pin 同期のための第三 file は不要**と判断する。

## 5. 焦点走 file 集合

実行した検索：

```text
git grep -n -E 'reflux_formal_consumer|reflux_origin_fixture_builder|_validate_wal_outcomes' -- '*test*.py'
```

直接参照は **11 test file**。`_validate_wal_outcomes` の名前による直接 test 参照は無く、consumer 公開入口経由で検査される。

さらに `test_reflux_originless_compatibility.py:13` が `test_p3_autonomous_workload_trial` を import する間接経路を確認した。したがって親の原文11 fileでは不足し、追補どおり以下の **12 file** とする。全て `orchestrator/tests/` 配下。

```text
test_reflux_formal_consumer.py
test_reflux_origin_fixture_builder.py
test_reflux_result_evidence.py
test_reflux_origin_client.py
test_reflux_origin_artifacts.py
test_reflux_origin_binding.py
test_reflux_origin_topology.py
test_reflux_source_closure.py
test_trial_registry.py
test_p3_autonomous_workload_trial.py
test_reflux_originless_compatibility.py
test_reflux_campaign_issuer.py
```

この参照閉包では、追補からの追加不足は見つからなかった。親が `tools/run_tests.py --force-dispatch` で12 file、変異 probe／本走、受入を実行する。本段では collection を含め pytest を実行していない。

## 6. 親 brief への異議

- **P1：採用。ただし観測の一般化に限界がある。** root stage の terminal が1件かつ末尾、という定義で実装する。DW-O13 の attempt 世代16件は全て commit であり、abort の attempt 単位一意性を実測したとは書けない。重複 key と record 重複は分ける。
- **P2：採用。** M5 単体は gate 後に等価。直接 witness は payload-only stage と gate 全体無効化＋M5 の合成で得る。gate 無効化単体ではこの witness は既存 root stage 判定に落ち続ける。
- **P3：原文は誤り、追補を採用。** 死ぬのは stage fallback。`build_attempt_id`、`verify_configs`、`reason`、`verify` の payload fallback は必要である。
- **P4：原文の「非 dict payload は常に FC07 以前」は誤り。** root attempt がある場合は resolver を通り、新 exact key gate に落ちる。payload 型述語単独の除去が等価という結論は正しい。有限性述語も上流 canonical JSON により等価になる。
- **P5：採用。** 全 record を走査するのは件数だけ。中間 build_start の外枠まで閉じない。これを正例1本で固定する。
- **末尾性の変異：KILLED を要求しない。** helper の末尾性項は outcome 別判定と過剰決定になる。単独除去を殺すために既存判定式を変更すると D1730 の scope を越える。
- **正例の名乗りを限定する。** float abort test が示すのは外枠と既存 fixture witness の受理であり、rejected production 系列の開通ではない。DW-O13 も実 WAL の観測であり、8c ordered projection の実成果物の観測ではない。
- **不変条件(iv)は検査した範囲で支持。** hash pin と生成物 pin は区別して確認した。新 node に所要時間の推測値を付けて duration ledger を更新する必要はない。
- **完了条件の11 file表記は12 fileへ訂正する。** テスト本数・kill 集合・実行時間は未実測であり、静的予測を実績として登録しない。

## 総括

terminal 専用 helper を現行1142行直後から呼び、exact外枠・件数1・末尾性をFC07で要求する。
新規 test は15 node（負例13、正例2）、既存 commit／fixture 正例は維持する。
変異は11本（KILLED予測7、等価予測4）。M5は単体等価、gate無効化との合成で検出する。
pin更新は不要、焦点走は12 file。変更・pytest実行は行っていない。
未確定は親による実走結果と完全kill集合。
