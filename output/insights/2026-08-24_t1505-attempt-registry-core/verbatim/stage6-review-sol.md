## 総括

- **must-fix — profile に追加された event が無条件に terminal として処理される。** event 表に存在するだけで `recovery` 等が terminal 分岐へ落ち、retry slot を解禁できる。canonical event bytes と 8c/8b の受理集合が変わる。scope 内。[attempt_registry_core.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:527)、[attempt_registry_core.py:920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:920)

- **must-fix — 8b genesis の `freeze_id` 引数が binding の freeze と結合されていない。** `freeze_id=A`、`binding.freeze_sha256=B` を受理し、成果物には B の root/reference だけが残る。freeze-wide registry の参照先が呼出し契約と異なる。scope 内。[attempt_registry_core.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1060)、[s8b_attempt_profile.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_attempt_profile.py:392)

- **must-fix — 8c facade の不正 genesis 入力で例外文言・検査順序が旧実装と変わる。** 旧実装は未検査 slot を先に canonicalize したが、新 core は先に codec parse する。同じ入力の拒否理由が変わり、D672 の例外同値契約を破る。scope 内。[attempt_registry_core.py:1073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1073)、[trial_registry.py:2330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2330)

- **should-fix — M1 の観測後 retry guard は実効的に kill されない。** 現 fixture は `observed` terminal のため、その前の「non-retryable」検査で落ちる。観測 guard だけを無効化してもテストは緑のままで、将来 retry 理由を入れた際の受理 attempt が増える。scope 内。[test_attempt_registry_core_s8b_profile.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:306)、[attempt_registry_core.py:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:827)

- **nit — synthetic rebinding test に恒真 assertion がある。** 対象関数を直前に全生成しているため FunctionDef の存在 assertion は常に真。後続の guard 検査は有効なので成果物影響はない。[test_attempt_registry_core_s8b_profile.py:555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:555)

## 詳細

### 1. 未実装 event が terminal に化ける

`_parse_row()` は profile の `event_keys` に名前があれば既知 event とみなします。一方、replay は `start`、`pre-observation-seal`、`classification`、`observation-start` 以外をすべて terminal とする `else` です。[attempt_registry_core.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:527)、[attempt_registry_core.py:797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:797)、[attempt_registry_core.py:920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:920)

したがって profile が `recovery` を terminal と同じ key set で登録すると、core は明示的な recovery policy を一切実装していないのに、その行を terminal として `terminals[slot_id]` へ登録します。その status が `retryable-failure` なら次 slot の開始条件も満たせます。[attempt_registry_core.py:824](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:824)、[attempt_registry_core.py:985](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:985)

さらに 8c profile の nested event map は通常の可変 `dict` です。frozen dataclass でも内部 mapping は凍結されていません。[trial_registry.py:2012](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2012)

修正条件は、少なくとも terminal 分岐を `elif event == "terminal"` とし、それ以外は semantic handler が明示実装されるまで拒否することです。8c の schema mappings も deep-immutable にする必要があります。

**成果物影響（未実装時）:** profile の拡張・誤変更後、`event:"recovery"` の canonical row が terminal として受理され、後続 attempt と registry hash chain が増える。

### 2. 8b genesis の freeze identity が引数と一致しない

共通 builder は `freeze_id` を字句検査しますが、生成後に profile から再導出した identity と比較しません。[attempt_registry_core.py:1068](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1068)、[attempt_registry_core.py:1110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1110)

8b genesis schema 自体には `freeze_id` がなく、`freeze_sha256` は binding から入ります。[s8b_attempt_profile.py:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_attempt_profile.py:277)  
また `freeze_id_from_genesis` はその `freeze_sha256` を返し、root path も同じ値から作られます。[s8b_attempt_profile.py:362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_attempt_profile.py:362)、[s8b_attempt_profile.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_attempt_profile.py:392)

このため A/B 不一致 genesis は作成時には通り、後の reservation で初めて B 以外を拒否します。builder の末尾で `_genesis_freeze_id(parsed) == freeze_id` を必須にすべきです。

追加すべきテストは、異なる `freeze_id` と `S8BAttemptBinding.freeze_sha256` を渡し、genesis 作成時点で exact gate/message により拒否される負例です。

**成果物影響（未実装時）:** requested freeze A の registry を作ったつもりでも、genesis の `freeze_sha256` と `root_path` は B になり、後続参照と budget は B に束縛される。

### 3. 8c の不正入力に対する例外順序が非等価

旧実装は slot を未検査のまま genesis value に入れ、先に event hash を計算していました。`5a4cbfa8:orchestrator/campaign/trial_registry.py:2701-2716`。新実装は hash 作成前に codec で全 slot を normalize します。[attempt_registry_core.py:1073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1073)

例えば exact keys を持つ slot の `arm` に `object()` を渡すと、

- 旧実装: canonical JSON 化が先に落ち、`[json] value is not canonical JSON: ...`
- 新実装: `_parse_attempt_slot()` が先に落ち、`[attempt-registry-schema] ...arm is outside the closed set`

となります。[trial_registry.py:1863](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:1863)

equivalence test は有効な単一 lifecycle と unknown event、slot skip しか比較しておらず、この builder error path を検査しません。[test_attempt_registry_core_equivalence.py:306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:306)、[test_attempt_registry_core_equivalence.py:343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:343)

**成果物影響（未実装時）:** artifact は作られないが、同じ拒否入力に対する exception/gate 文言が変わり、D672 の拒否理由 snapshot と呼出し側の失敗分類が変わる。

### 4. 変異 M1〜M6 の静的 kill 判定

| 変異 | 判定 | 根拠 |
|---|---|---|
| M1 | **不十分** | whole order block の除去は skip fixture が kill するが、観測 guard `[832:839]` だけの無効化は `observed` status の拒否 `[827:831]` に隠れる。 |
| M2 | kill | profile flag の assertion と mismatch terminal の exact rejection が赤になる。[test_attempt_registry_core_s8b_profile.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:439) |
| M3 | kill | 実 `def` 消失を actual-source guard が検出する。[test_attempt_registry_core_equivalence.py:428](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:428) |
| M4 | kill | actual-source guard と synthetic rebinding 負例の両方が検出する。[test_attempt_registry_core_s8b_profile.py:549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:549) |
| M5 | kill | repetition を budget key に戻すと3件目が受理され、期待例外が消える。[test_attempt_registry_core_s8b_profile.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:289) |
| M6 | kill | 8c/8b とも unknown-event の exact gate/message を要求している。[test_attempt_registry_core_equivalence.py:343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:343)、[test_attempt_registry_core_s8b_profile.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:337) |

M1 には、retryable reason を1件だけ持つ合成 profileで「classification → observation-start → retryable-failure terminal」まで作り、次 slot が observation guard だけで拒否される fixture が必要です。

**成果物影響（未実装時）:** 観測 guard 単独の退行を検出できず、理由集合が将来確定した時点で観測後の後続 attempt が受理集合へ入る。

## 絶対規律 2 と段 3 再発検査

8b の公式 profile では理由一致 flag が `True` で、core は null matrix より前に classification reason と terminal reason の不一致を拒否します。[s8b_attempt_profile.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_attempt_profile.py:425)、[attempt_registry_core.py:972](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:972)  
段3 A1 の「terminal で理由を付け替える」経路は、この state-machine 境界では再発していません。外部出力を classification 前に読んでいないこと自体は core では証明できませんが、8b production 配線は明示的 scope 外なので欠陥には数えていません。

段3の C03 rebinding 所見は actual-source guard で塞がれています。A4 の cell-wide budget も repetition 非依存 key で実装されています。一方、A18 の unknown-event 論証は現在の静的 profile 表では成立するものの、詳細1の semantic fallthrough があるため「profile を拡張しても安全」という境界までは成立していません。

pytest は制約どおり実走しておらず、緑は主張しません。