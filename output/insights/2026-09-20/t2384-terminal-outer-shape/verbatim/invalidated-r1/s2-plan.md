## 1. gate の実装案

行番号は変更前。変更対象は consumer とその test の 2 file とする。

consumer の **1133 行直前**に terminal 専用 helper を置き、**1142 行 `terminal = wal_records[-1]` の直後**で呼ぶ。`_wal_trigger` と定数を共有せず、同関数の bytes は変更しない。payload の **key 集合は閉じない**。commit / abort の既存判定式、reason code、`_wal_field` は保存する。

追加する helper の逐語案：

```python
def _wal_terminal_outer_shape(records: Sequence[dict]) -> bool:
    terminal = records[-1]
    if {"variant", "stage", "env_tag", "ts", "payload"} != set(terminal):
        return False
    if type(terminal["variant"]) is not str or type(terminal["env_tag"]) is not str:
        return False
    ts = terminal["ts"]
    if type(ts) not in (int, float) or (
        type(ts) is float and not math.isfinite(ts)
    ):
        return False
    if type(terminal["payload"]) is not dict:
        return False
    terminal_count = sum(
        record.get("stage") in (STAGE_COMMIT, STAGE_ABORT)
        for record in records
    )
    return terminal_count == 1 and terminal.get("stage") in (STAGE_COMMIT, STAGE_ABORT)
```

1142〜1144 行の配置：

```python
terminal = wal_records[-1]
_require(FormalReasonCode.FC07, _wal_terminal_outer_shape(wal_records))
attempt = physical["build_attempt_id"]
_require(FormalReasonCode.FC07, _wal_field(terminal, "build_attempt_id") == attempt)
```

検査順は **exact keys → variant / env_tag 型 → ts 型・有限性 → payload 型 → terminal 件数・末尾性 → 既存 attempt 一致 → 既存 outcome 別判定**。

- `records` が非空、各要素が exact dict であることは evidence resolver の 1632〜1635 行で保証される。
- terminal 件数は **root `stage`** で数える。payload の `stage` を探索しない。
- membership は set でなく tuple を使う。入力の `stage` が list / dict でも `TypeError` にせず拒否できる。
- 件数 1 と末尾の stage membership の積で P1 を満たす。途中の `build_start` 等へ外枠 gate は掛けない。
- `ts` の有限性は trigger と同じ式とし、巨大 int を不要に float へ変換しない。
- 末尾性の条件は既存 outcome 別 stage 判定とも重なるが、helper 自体に P1 の契約を持たせる。

## 2. test 一覧

追加位置は `test_reflux_formal_consumer.py` の **1680 行後、既存 terminal 形状 test 群の隣**。既存 helper は変更しない。

以下の共通手順 **R** を全新規 test に適用する。

1. `wal = _projection_records(case, 0)`。既定 terminal は必要な `reason` / `verify` を持つ rejected abort。
2. 表の変更を加え、`_rewrite_wal(case, 0, wal)`。
3. 負例は `_assert_reason(case, C.FormalReasonCode.FC07)`。正例は既存 commit test と同じく `P6Unavailable` の型・reason を検査する。

**共通の到達性 E：**

- `_rewrite_wal` が source bytes、byte range、projection hash、record 参照を整合させる。canonical-list 経路なので `wal.parse_line` の外枠検査を通らない。
- `_projection_attempt_id` が読む attempt は全 record で同じ。resolver の attempt 混在検査、source 一致検査、FC05B の非重複 range 検査を通る。
- provenance、physical campaign の binding、physical attempt は変えない。
- trigger はそのまま 1 件なので FC05C を通る。member / mask / topology は変えず FC06 を通る。
- verifier policy も不変。既存 FC07 attempt 式が読む値は正しい。新 gate が先に拒否する場合も、この attempt 式自体には違反を作らない。

| 名前 | 組み立て | 期待 | 手前で落ちない根拠 |
|---|---|---|---|
| `test_fc07_rejects_terminal_root_attempt_shadow` | R。末尾 root `build_attempt_id` に正しい attempt、payload 同名値に `"fixture-shadow-attempt"` | FC07 | E。resolver と既存 FC07 attempt 式は root 優先。`_rewrite_wal` 474〜476 行の `continue` により payload の別値は保存される。exact keys で拒否 |
| `test_fc07_rejects_terminal_extra_root_key` | R。末尾に `extra=1` | FC07 | E。attempt / trigger は無傷。exact keys で拒否 |
| `test_fc07_rejects_terminal_missing_root_key[env_tag]` | R。末尾の `env_tag` を削除 | FC07 | E。resolver はこの field を読まない。exact keys で拒否 |
| 同 `[ts]` | R。末尾の `ts` を削除 | FC07 | E。同上 |
| 同 `[variant]` | R。末尾の `variant` を削除 | FC07 | E。同上 |
| `test_fc07_rejects_terminal_outer_value_type[ts-bool]` | R。末尾 `ts=True` | FC07 | E。bool は canonical JSON に載る。数値型 gate で拒否 |
| 同 `[ts-str]` | R。末尾 `ts="1788580082.583126"` | FC07 | E。文字列は canonical JSON に載る。数値型 gate で拒否 |
| 同 `[variant-int]` | R。末尾 `variant=1` | FC07 | E。resolver は terminal variant を型検査しない |
| 同 `[env_tag-null]` | R。末尾 `env_tag=None` | FC07 | E。null は canonical JSON に載り、attempt に影響しない |
| `test_fc07_rejects_payload_only_terminal_stage` | R。`terminal["payload"]["stage"] = terminal.pop("stage")`。既存 abort payload を保存 | FC07 | E。attempt は payload に残る。新 gate は missing root stage で拒否。gate 無効時も旧 stage 式は拒否し、gate 無効化＋M5 のときだけ通る直接 witness |
| `test_fc07_rejects_duplicate_terminal_stages[abort-abort]` | R。abort を deepcopy して挿入し `[trigger, abort, abort]` | FC07 | E。全 attempt 同じ、trigger は増えない。projection 内 record 増加は range 同士の重複ではない。件数 2 で拒否 |
| 同 `[commit-abort]` | R。挿入 record は exact 外枠の commit、payload は `{build_attempt_id: attempt, verify_configs: ["legacy", "s2"]}`。末尾 abort は保存 | FC07 | E。physical outcome は rejected のまま。末尾の既存判定は通るため件数検査を露出できる |
| `test_fc07_rejects_terminal_before_last_record` | R。abort の後に exact 外枠の `build_start` を追加。payload に同じ attempt | FC07 | E。末尾にも attempt がある。terminal 件数は 1 だが末尾性が偽 |
| `test_fc07_accepts_float_timestamp_abort_terminal_shape` | R。abort の `ts=1788580082.583126` | P6Unavailable | E。既存 abort の `reason` / `verify` を保存し全既存判定を通す |
| `test_fc07_accepts_nonterminal_record_without_exact_outer_shape` | R。途中へ `{"stage": "build_start", "payload": {"build_attempt_id": attempt}}` を追加 | P6Unavailable | E。resolver の attempt 条件を満たし、trigger / terminal 件数は各 1。P5 の境界を固定する |
| 既存 `test_exact_fixture_contract_reaches_only_p6_unavailable` | 無変更 | P6Unavailable | 既定 fixture の integer ts abort が引き続き通る |
| 既存 `test_fc07_accepts_production_commit_terminal_shape`（1654〜1679 行） | 無変更 | P6Unavailable | physical / member を accepted に同期済み。exact 外枠・verify 順序が適合 |

**追加は 9 test 関数・15 node（負例 13、正例 2）**。既存正例 2 node も明示的に回す。

非 dict payload と非有限 ts は、新 gate の独立した end-to-end 負例にしない。

- exact 外枠＋非 dict payload は attempt を取得できず resolver で FC05B。root attempt を足して上流を通すと exact keys が先に拒否する。したがって **payload 型述語を単独で露出する入力は到達不能**。
- 非有限 ts は strict JSON / canonical serialization で拒否され、FC07 へ到達不能。
- JSON 重複 key も strict JSON で拒否される。P1 の record 重複とは分ける。

## 3. 変異 matrix 候補

以下は**静的予測**。追加行については §1 の逐語案を old とする。表中の `K` は KILLED、`S` は SURVIVED＝等価予測。全変更は consumer 内に限定する。

| id | old | new | 期待 | 殺す test の予測 | 等価なら理由 |
|---|---|---|---|---|---|
| M1：B-057-M5 | `_require(FormalReasonCode.FC07, terminal.get("stage") == STAGE_ABORT)` | `_require(FormalReasonCode.FC07, _wal_field(terminal, "stage") == STAGE_ABORT)` | S | — | gate が先に root stage の存在を保証する。`_wal_field` は必ず root を返す |
| M2：gate 無効化＋M5 | M6 の old と M1 の old、計 2 行 | M6 の new と M1 の new | K | `test_fc07_rejects_payload_only_terminal_stage` | — |
| M3：superset 許容 | `if {"variant", "stage", "env_tag", "ts", "payload"} != set(terminal):` | `if not {"variant", "stage", "env_tag", "ts", "payload"} <= set(terminal):` | K | `test_fc07_rejects_terminal_extra_root_key`、`test_fc07_rejects_terminal_root_attempt_shadow` | — |
| M4：bool 許容 | `if type(ts) not in (int, float) or (` | `if type(ts) not in (int, float, bool) or (` | K | `test_fc07_rejects_terminal_outer_value_type[ts-bool]` | — |
| M5：件数検査除去 | `return terminal_count == 1 and terminal.get("stage") in (STAGE_COMMIT, STAGE_ABORT)` | `return terminal.get("stage") in (STAGE_COMMIT, STAGE_ABORT)` | K | `test_fc07_rejects_duplicate_terminal_stages[abort-abort]` / `[commit-abort]` | — |
| M6：gate 無効化 | `_require(FormalReasonCode.FC07, _wal_terminal_outer_shape(wal_records))` | `_require(FormalReasonCode.FC07, True)` | K | root shadow、余分 key、欠落 3、型 4、重複 2 の各 test | — |
| M7：payload 型述語無効化 | `if type(terminal["payload"]) is not dict:` | `if False:` | S | — | root attempt なしなら resolver で FC05B。root attempt ありなら先行 exact keys で FC07 |
| M8：有限性述語無効化 | `type(ts) is float and not math.isfinite(ts)` | `False` | S | — | 非有限値は strict JSON / canonicalization が先に拒否する |

**8 変異、KILLED 予測 5、等価予測 3。**

M1 の等価性は単なる未被覆ではない。新 gate より後では `"stage" in terminal` が真なので、1096〜1097 行により `_wal_field(terminal, "stage") == terminal.get("stage")` が成立する。

M2 では missing root stage の gate 拒否を無効化し、abort 比較だけ payload fallback に変える。attempt、`reason`、`verify` は全て既存の正常値なので P6Unavailable へ進み、FC07 を期待した test が殺す。M6 単体では同 test は旧 root stage 比較で FC07 のままなので、**その test を M6 の kill 予測へ数えない**。

kill node の完全一致集合は事前に断言しない。前 wave と同様、全 paired record の走査による追加 kill があり得るため、親の probe 実測で確定する。

## 4. pin 閉包

| 対象 | 独立確認・依存関係 | 本 wave の扱い |
|---|---|---|
| 変更 2 file の SHA-256 / Git blob SHA-1 | 現物 bytes から算出し、`git grep -l -F` で tracked 全域を検索。両 file とも一致 0 件。tracked `output/` を含む | 同期先なし |
| 行数 | 現物は consumer 1544 行、test 2390 行。確認した参照に exact 行数 assertion はない | 追加で行数は増えるが pin 更新は不要 |
| `reflux_origin_fixture_baseline.json` | builder 出力の canonical hash / byte length。`test_reflux_origin_fixture_builder.py:107` 以降が独立再計算 | builder と生成入力は不変なので変更不要 |
| result evidence golden | `test_reflux_result_evidence.py:39–42` の 4 hash と、517 行の 1848 bytes | fixture record の生成依存に今回の consumer gate / test 追加は入らない。変更不要 |
| consumer source の構造検査 | `test_reflux_formal_consumer.py:2285` 以降。production file 集合 15 本、AST の禁止構築等を検査 | file 追加や禁止構築をしないため更新不要。焦点走で検証 |
| `acceptance_duration_ledger.json` | nodeid→時間の配分用台帳。`acceptance_shards.py:397–404` は未登録 node を 1 秒として扱う。台帳 test は `nodeid_count == len(durations)` を検査 | 新規 15 node の追加だけでは更新不要。時間値を推測して追加しない |
| tests README の file 一覧 | 既存 test file 名の列挙 | file を増やさないため更新不要 |

よって、**実装変更 2 file のまま成立する**。fixture builder を変更しないことが golden 不変の根拠であり、旧 hash literal の不在だけを根拠にしていない。

hash 検索の不在証明は tracked file の範囲。未追跡 output 全体や将来生成物まで「pin 0 件」と一般化しない。実行時の焦点走・受入による確認は未実施。

## 5. 焦点走 file 集合

`git grep` による現行 tracked `*test*.py` の参照数：

| 検索語 | 参照 test file 数 |
|---|---:|
| `reflux_formal_consumer` | 4 |
| `reflux_origin_fixture_builder` | 11 |
| `_validate_wal_outcomes` | 0 |
| 上記の和集合 | 11 |

consumer を直接参照する 4 file は formal consumer、origin client、trial registry、P3 autonomous workload trial。builder 参照 11 file に全て含まれる。

親 brief の 11 file には **`test_reflux_campaign_issuer.py` が不足**する。同 file は 56〜59 行で builder を import し、243 行で `build_launch_admission_inputs`、290 行で `build_result_evidence_record` を利用する。

間接利用は `test_reflux_originless_compatibility.py:134` → P3 test の `_origin_public_inputs` → `build_fixture_repository` が確認できる。これは親の集合に含まれている。

追加で見つかった `test_autonomous_trial_completeness.py` の P3 test 利用は `_coder_authority()` のみで、今回の consumer / origin fixture 経路ではない。文字列参照だけの file も追加対象にしない。

したがって焦点走は以下の **12 file** とする。全て `orchestrator/tests/` 配下。

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

親が `tools/run_tests.py --force-dispatch` で実測する。今回 pytest、collection、変異走は実行していない。

## 6. 親 brief への異議

1. **P3 は誤り。** exact 外枠により死ぬのは `build_attempt_id` / `verify` 等の **root shadow 経路**。これらの field は root に存在できなくなるので、`_wal_field` の **payload fallback は必須となる**。stage だけは root に必ず存在し、fallback が到達不能になる。定義・既存呼出しを保存する結論は正しい。

2. **P4 は条件付きで正しい。** 非 dict payload が常に FC07 より前に落ちるわけではない。正しい root attempt を持たせれば resolver と既存 attempt 式を通る。その場合は新 exact-key 検査が先に拒否する。payload 型述語の単独変異が等価という結論は、この二分で説明する必要がある。

3. **P1 の gate 定義は採用するが、producer 全経路の一意性は未実証。** 射影された producer 箇所は外枠と payload の出所を示すが、active-attempt / recovery 全経路の terminal 一意性までは証明しない。本 plan では承認済み入力契約として件数 1 を実装する。

4. **P2 は正しい。** stage 比較の前に exact gate を置けば M5 は等価。直接 witness は gate 無効化との合成変異で検出する。

5. **P5 は採用。** 中間 nonterminal の外枠を閉じないことを正例で固定する。projection 全 record の外枠検査への拡張はしない。

6. **「焦点走 11 file で閉じる」は現行参照に対して不足。** campaign issuer を追加して 12 file とする。

7. **正例と production の到達性を混同しない。** float ts abort 正例は production と同じ外枠に既存 fixture の正常 `reason` / `verify` を載せたもの。全 production abort 経路が FC07 を通るという証明ではない。また前 wave 資料の witness field 名と現行 consumer は異なり、現行 1155〜1263 行は `reason` / `verify` を検査する。test は現行 fixture を保存して作る。

8. **不変条件の pin 結論は支持するが、実測範囲を限定する。** tracked hash pin 不在と生成依存の静的確認は済み。変更後の緑、正確な kill 集合、受入成功は親の実測待ち。

## 総括

terminal 専用 helper を既存 attempt 判定前に挿入し、exact 外枠・terminal 1 件・末尾性を FC07 で閉じる。
追加 test は 9 関数・15 node、変異候補は 8 本（kill 5、等価 3）。
fixture golden・duration 台帳は変更不要。焦点走は campaign issuer を加えた 12 file。
P3 を訂正し、P4 の到達不能理由を補正する。
ファイル変更・テスト実行なし。kill 集合と回帰・受入結果は親の実測で確定する。
