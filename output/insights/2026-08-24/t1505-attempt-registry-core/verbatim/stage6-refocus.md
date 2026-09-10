## 総括

`partial` は「一部は修正されたが、元所見の契約を完全には満たしていない」を表す。`regressed` に該当する所見はなかった。

### 1. 対応表

| ID | 判定 | 根拠 | 成果物影響 |
|---|---|---|---|
| sol-MF1: 未実装 event が terminal 化 | `closed` | 未実装名は semantic gate で拒否され、terminal 分岐も明示 `elif` になった。[attempt_registry_core.py:568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:568)、[attempt_registry_core.py:965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:965)。schema 表も再帰的に凍結される。[attempt_registry_core.py:84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:84) | profile-only event が terminal として registry/hash chain を増やす経路は閉じた。 |
| sol-MF2: 8b freeze identity 不一致 | `closed` | parsed genesis から再導出した identity と要求値を比較する。[attempt_registry_core.py:1155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1155)、[s8b_attempt_profile.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_attempt_profile.py:392) | freeze A を要求し、freeze B に束縛された genesis を生成する経路は閉じた。 |
| sol-MF3: genesis 拒否順序 | `partial` | raw slot の `dict()` 化→hash→schema parse は復元された。[attempt_registry_core.py:1124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1124)、[attempt_registry_core.py:1151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1151)。ただし `retryable_failure_reasons=None` は現行だけ既定集合へ置換される。[attempt_registry_core.py:1125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1125)、`5a4cbfa8:orchestrator/campaign/trial_registry.py:2700` | 抽出前が拒否した公開 builder 入力から、現行は 8c genesis を生成できる。 |
| sol-SF1: M1 fixture が観測 guard を単独で撃たない | `closed` | retryable terminal＋observation を構成し、guard 有効時の拒否と無効時の受理を同一 rows で確認する。[test_attempt_registry_core_s8b_profile.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:357)、[test_attempt_registry_core_s8b_profile.py:391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:391) | 観測後 retry guard 単独の退行を検出できる。 |
| sol-N1: synthetic test の恒真 assertion | `closed` | 現在は synthetic source に対する guard の失敗と exact message だけを検査する。[test_attempt_registry_core_s8b_profile.py:688](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:688) | nit。成果物影響なし。 |
| luna-MF1: recovery 拡張 seam 不在 | `partial` | terminal 誤解釈は閉じたが、semantic 名は core の固定集合で、`allow_recovered_abandonment` はデータ項のまま実行箇所がない。[attempt_registry_core.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:35)、[attempt_registry_core.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:127)、[attempt_registry_core.py:572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:572) | 今日の成果物は fail-closed だが、将来の recovery は profile/adapter だけでは追加できない。recovery 実装自体は指定 scope 外。 |
| luna-MF2: core genesis API が 8c manifest 契約を強制 | `partial` | `manifest_path`/`manifest_sha256` は依然必須。[attempt_registry_core.py:1111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1111)。8b genesis schema には両値がない。[s8b_attempt_profile.py:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/s8b_attempt_profile.py:277)。freeze 部分だけは結合された。 | 8b の manifest 引数は検査されるが genesis bytes に封印されない。production 未配線なので現行成果物への到達はない。 |
| luna-MF3: M1 未 kill | `closed` | sol-SF1 と同じ fixture が guard 削除時に拒否を消失させる。[test_attempt_registry_core_s8b_profile.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:357)、[attempt_registry_core.py:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:877) | M1 生存による観測後 attempt 増加を検出できる。 |
| luna-SF1: golden が production 定数を流用 | `closed` | registry path、receipt dir、公開6関数 signature を独立リテラルで固定した。[test_attempt_registry_core_equivalence.py:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:600) | path/signature が production と期待値で同時に動く偽緑を防ぐ。 |
| luna-SF2: facade namespace に2名追加 | `closed` | import は `_PurePosixPath` / `_attempt_core` となり、公開名不在も検査する。[trial_registry.py:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:24)、[trial_registry.py:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:43)、[test_attempt_registry_core_equivalence.py:665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:665) | 抽出で増えた公開 namespace は除去された。 |
| luna-SF3: docs/output の所有面超過 | `partial`（scope 外） | 段4の実装面は campaign/test に限定されている。[stage4-adjudication.md:104](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1484-floor-restart-registry/stage4-adjudication.md:104)。本依頼が inherited docs/output 差分を欠陥対象外としているため、現状態は再検査していない。 | registry bytes・受理集合への影響は指定上なし。コード上で閉じたとは判定しない。 |
| luna-N1: M3/M4/M5 の赤理由が複数 | `partial` | M3/M4 は2個の actual-source guard が反応する。[test_attempt_registry_core_equivalence.py:670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:670)、[test_attempt_registry_core_s8b_profile.py:655](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:655)。M5 も key 比較と予算挙動の2 node が反応する。[test_attempt_registry_core_s8b_profile.py:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:196)、[test_attempt_registry_core_s8b_profile.py:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:309) | nit。変異は kill されるが、段4の「赤理由が一つ」は未達。 |

### 2. 変異 M1〜M6 の kill 判定

- **M1 — kill。** `test_retryable_terminal_after_observation_hits_only_observation_guard` が、同一 rows を guard 無効時には受理できるところまで示す。[test_attempt_registry_core_s8b_profile.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:357)

- **M2 — kill。** `test_strict_8b_reason_match_rejects_input_that_8c_still_accepts` の mismatch 拒否が消える。[test_attempt_registry_core_s8b_profile.py:572](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:572)

- **M3 — kill。** `test_six_facades_are_unrebound_real_functions` が `reserve_attempt_slot` の実 `def` 消失を検出する。[test_attempt_registry_core_equivalence.py:670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:670)

- **M4 — kill。** `test_trial_registry_six_facades_have_no_top_level_rebinding` が実 source の再束縛を検出する。[test_attempt_registry_core_s8b_profile.py:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:682)

- **M5 — kill。** `test_budget_is_cell_wide_and_does_not_reset_for_each_repetition` で3件目が受理され、期待例外が消える。[test_attempt_registry_core_s8b_profile.py:309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:309)

- **M6 — kill。** 8c/8b の exact unknown-event 検査がともに赤になる。[test_attempt_registry_core_equivalence.py:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:455)、[test_attempt_registry_core_s8b_profile.py:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:408)

kill されない変異はない。以上は静的判定であり、pytest の緑は主張しない。

### 3. 新規所見

**must-fix — 8c genesis facade が明示 `retryable_failure_reasons=None` を新たに受理する。**

抽出前は公開引数を無条件に `list()` 化するため、`None` は genesis 構築前に拒否された。`5a4cbfa8:orchestrator/campaign/trial_registry.py:2679-2700`。現行 facade は値をそのまま core へ渡し、core は `None` を profile の既定集合へ置換する。[trial_registry.py:2309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2309)、[trial_registry.py:2330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2330)、[attempt_registry_core.py:1115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1115)、[attempt_registry_core.py:1125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1125)

既存 differential test は理由集合を固定し、slot の5変異しか生成しないため、この差を検出しない。[test_attempt_registry_core_equivalence.py:138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:138)、[test_attempt_registry_core_equivalence.py:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:479)

**成果物影響:** 抽出前に拒否された公開 API 入力から、現行は canonical 8c genesis を作成でき、D672 の受理集合不変契約に反する。

これは `8d2d7f43` にも既に存在した残存抽出回帰であり、fix が新たに導入した `regressed` ではない。期待 test node は例えば  
`test_attempt_registry_core_equivalence.py::test_genesis_builder_explicit_none_retry_reasons_matches_pre_extraction`。

これ以外の新規所見はない。F1 の event gate、列挙された追加入力型、F4 の単独性、M1〜M6、`8d2d7f43→10903ad7` の production 差分を検査し、別の受理集合縮小や fix 後回帰は反証されなかった。

## F1 — 8c 受理集合と unknown event

8c v1 の正常 event は `start`、`classification`、`terminal` の3種、v2 はそれらに `pre-observation-seal` と `observation-start` を加えた5種である。[trial_registry.py:2020](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2020)

この8種の列挙はすべて core の5種の semantic 名に含まれる。[attempt_registry_core.py:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:35)。したがって既存 v1/v2 row が新設 semantic gate に落ちる経路はない。replay も start、seal、classification、observation、terminal を個別に分岐する。[attempt_registry_core.py:842](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:842)、[attempt_registry_core.py:965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:965)

未知 event は profile lookup 失敗で先に拒否され、semantic gate へは到達しない。[attempt_registry_core.py:568](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:568)。したがって文言は引き続き、

```text
[attempt-registry-schema] attempt registry line 2.event is unknown
```

である。[test_attempt_registry_core_equivalence.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_equivalence.py:471)

**結論:** F1 修正による 8c の受理集合縮小は静的にはない。

## F3 — 抽出前 builder との順序比較

確認結果は次のとおり。

- slot が Mapping でない場合、抽出前の `[dict(slot) ...]` と現行 `_S8CSlotCodec.to_json()` の `dict(slot)` は同じ変換面である。[trial_registry.py:1912](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:1912)、`5a4cbfa8:orchestrator/campaign/trial_registry.py:2709`
- 空 slots は両方とも event hash 計算後、layout 検査で同じ `[attempt-registry-genesis] genesis must close a non-empty slot set` に落ちる。[attempt_registry_core.py:326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:326)、`5a4cbfa8:orchestrator/campaign/trial_registry.py:1918`
- builder の `slots` は元から `Sequence` なので、tuple 等は双方とも list へ投影して受理する。保存済み genesis の `slots` が list でない場合は、双方とも `...slots is not an array` で拒否する。[attempt_registry_core.py:545](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:545)、`5a4cbfa8:orchestrator/campaign/trial_registry.py:2009`
- freeze_id 非文字列は facade の同じ位置で拒否される。[trial_registry.py:2326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2326)、`5a4cbfa8:orchestrator/campaign/trial_registry.py:2696`
- manifest_sha256 不正も facade の同じ gate/message で拒否される。[trial_registry.py:2324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:2324)、`5a4cbfa8:orchestrator/campaign/trial_registry.py:2694`

ただし、上記の明示 `None` 差に加え、複数箇所が同時に不正な場合の順序も完全には復元されていない。抽出前は理由集合を先に `list()` 化し、その後 slot を `dict()` 化する。現行は slot を先に serialize し、その後理由集合を処理する。[attempt_registry_core.py:1124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1124)、`5a4cbfa8:orchestrator/campaign/trial_registry.py:2700-2709`。したがって二重不正入力では Python 例外の発生元・文言が変わり得る。

**成果物影響:** 単独の `None` では genesis 受理集合が広がり、二重不正では artifact は作られないが拒否理由同値が破れる。

## F4 — fixture の単独性

fixture は test-only profile に理由を1件だけ追加し、次の状態を構成する。

1. classification reason が `scheduler-timeout`
2. observation-start 済み
3. terminal は同じ理由の `retryable-failure`
4. report は非 null、observation/primary は null

[test_attempt_registry_core_s8b_profile.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:357)

このため previous-terminal 検査と retryable-status 検査は通過し、拒否点は observation guard だけになる。[attempt_registry_core.py:861](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:861)、[attempt_registry_core.py:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:877)

さらに同じ rows と profile から `forbid_retry_after_observation=False` だけを変更すると次 slot が受理される。[test_attempt_registry_core_s8b_profile.py:396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/tests/test_attempt_registry_core_s8b_profile.py:396)。したがって fixture は過剰決定ではなく、guard 削除で確実に期待拒否が消える。

## 回帰判定

`8d2d7f43→10903ad7` の production 変更は、semantic fail-closed、schema deep-freeze、8b freeze identity 検査、8c slot canonicalization 順序復元、private import 化に限られる。

8c の正常 event は semantic 固定集合の内側にあり、freeze identity は8c builder自身が同じ値を genesisへ入れるため追加拒否にならない。[trial_registry.py:1987](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/trial_registry.py:1987)、[attempt_registry_core.py:1158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1484-floor-restart-registry/orchestrator/campaign/attempt_registry_core.py:1158)

したがって、fix 前に受理されていた正規の8c v1/v2 lifecycle、8b test profile lifecycle、公開 facade signature/path が fix 後に壊れた静的経路は見つからなかった。`regressed` は0件である。

pytest は制約どおり実行していない。上記の kill・受理・拒否判定はすべてコードと履歴の静的検査による。