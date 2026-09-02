## 1. gate 挿入位置

変更は [s8b_oracle_manifest.py:1198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1198) の `build_approved_manifest` だけとする。

挿入点は、現在の [load_ratified_freeze 呼出し直後:1205](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1205)、既存 `except` の直前である。現在の前後 3 行は次のとおり。

```python
1203    root = Path(root)
1204    try:
1205        ratified = s8b_ratified_freeze.load_ratified_freeze(root)
        # ここへ gate を挿入
1206    except s8b_ratified_freeze.RatifiedFreezeError as exc:
1207        reason = (
1208            "no-active-ratified-freeze"
```

実装後の形は次とする。新しい helper、理由、互換層は作らない。

```python
root = Path(root)
try:
    ratified = s8b_ratified_freeze.load_ratified_freeze(root)
    s8b_ratified_freeze.assert_g1_floor_selection_identity(ratified, root)
except s8b_ratified_freeze.RatifiedFreezeError as exc:
    reason = (
        "no-active-ratified-freeze"
        if exc.reason == "no-active" else exc.reason
    )
    raise ManifestCliError(reason, str(exc)) from exc
```

例外の写像は次の署名になる。

```text
RatifiedFreezeError(reason=R, detail=D, cause=C)
    -> ManifestCliError(reason=R, detail=str(exc)) from exc

R ∈ {
    "floor-selection-unverifiable",
    "floor-selection-eligibility-underivable",
    "floor-selection-rule-mismatch",
}
```

捕捉する型は `s8b_ratified_freeze.RatifiedFreezeError` のみ、送出する consumer 型は既存 `ManifestCliError` である。loader の `no-active` だけを `no-active-ratified-freeze` にする既存写像 [1206-1211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1206) は維持する。

新造しない 3 理由の出所は公開 callee 内に既にある。

- `floor-selection-unverifiable`: [s8b_ratified_freeze.py:3583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3583)、[3653](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3653)
- `floor-selection-eligibility-underivable`: [3646-3648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3646)
- `floor-selection-rule-mismatch`: [3649-3651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3649)

これは s8c の `load -> assert -> RatifiedFreezeError の reason を consumer 固有型へ保存` という先例 [s8c_result_judge.py:2075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8c_result_judge.py:2075) と同形である。`launch_validate` は呼ばない。

## 2. 既存 2 正例が赤になる経路

2 本とも、そのままでは実際に赤になる。

合成 fixture は [test_s8b_oracle_manifest.py:272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:272) で v1 文書を複製し、`v2_fixture.fill` により `floor` と `budget` だけを充填する。同 fixture の `fill` が変更する field は [s8b_v2_freeze_fixture.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/s8b_v2_freeze_fixture.py:61) の 2 件だけである。

したがって合成 `RatifiedFreeze` は次の状態になる。

- `generation_number=1`: [test_s8b_oracle_manifest.py:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:289)
- `generation_commit="b" * 40`: [291](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:291)
- 元の v1 文書に `floor_protocol`、`floor_source`、`env_tag` はなく、`fill` 後も追加されない。
- `floor` と `budget` だけは非 null になる。

実行経路は次のとおり。

1. exact `RatifiedFreeze` なので型検査 [s8b_ratified_freeze.py:3567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3567) は通る。
2. `generation_number == 1` なので非 g1 return [3572-3573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3572) には入らない。
3. `floor_protocol` の `_source_record_path_sha` [3577-3579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3577) が、record 不在を `source-record-schema` として拒否する [926-930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:926)。
4. 公開 callee がこれを `floor-selection-unverifiable` に畳む [3622-3628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3622)。
5. `build_approved_manifest` が同じ reason の `ManifestCliError` を送出する。spec 読込、manifest 構築、出力作成には到達しない。

| 既存正例 | gate 後の結果 |
|---|---|
| `test_build_approved_valid_fixture_output_depends_only_on_spec_pin` の [1369](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1369) | 未捕捉の `ManifestCliError(reason="floor-selection-unverifiable")` で赤。なお pin 無し側の [1361-1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1361) は例外 reason を検査しないため、誤った gate 拒否でも緑になる。追随しないと「pin の一点だけ」という試験意図も壊れる。 |
| `test_build_approved_uses_one_active_snapshot_and_writes_valid_candidate` の [1395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1395) | loader は一度呼ばれた後、同じ selection error が未捕捉で赤。`calls == [root]`、出力、`verify_manifest` の assert には到達しない。 |

さらに、同じ g1 合成 fixture を使う [1328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1328) と [1410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1410) も、それぞれ期待 reason より先に `floor-selection-unverifiable` が出て赤になる。この 2 本も追随対象に含める必要がある。

仮に source record を後から合成しても、`generation_commit="b"*40` が実在 blob を束縛しないため、次は `_blob_at_or_fail` [3594-3597](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_ratified_freeze.py:3594) で拒否される。

## 3. 2 正例の追随案

選択肢は少なくとも次の 3 つある。

| 選択肢 | 方法 | 偽緑リスク |
|---|---|---|
| A、推奨 | 既存 4 consumer test の合成 freeze を明示的な `generation_number=2` にし、2 正例では公開 callee 属性を実 callee へ委譲する追跡 wrapper に差し替える。別に genuine g1 を使う実 callee 正例・負例を追加する。 | 既存 2 正例単独では g1 内部の弱体化を検出できない。これを genuine g1 の追加 2 test で閉じる。 |
| B | 既存 2 正例ごとに production-emitter 由来の genuine g1 と、それに完全一致する reviewed spec を構築する。 | freeze から spec を同じ test helper で自己導出すると、producer と consumer の相関した誤りが一致して緑になる。pin 用 2 構成 fixture と実 g1 の構成積も異なり、追随範囲と脆さが大きい。 |
| C、却下 | s8c test の `_patch_ratified_floor` [test_s8c_result_judge.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8c_result_judge.py:437) のように loader と公開 selection assert を両方 stub する。 | consumer が実 callee を呼ばない、誤った candidate/root を渡す、実 callee が同じ入力を拒否する、のいずれでも緑になり得る。P1 と D1371 が禁止する形なので採用しない。 |

推奨する A の file:line 計画は次のとおり。

- [test_s8b_oracle_manifest.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:22) 付近に `s8b_holdout_freeze` と、既存の production-emitter fixture module `test_s8b_ratified_freeze` を import する。後者を test helper として共有する先例は [test_s8b_ratified_verify.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_verify.py:46) にある。
- `_synthetic_ratified_freeze` [272-292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:272) に明示的な `generation_number` 引数を加え、constructor の固定 `1` をその引数へ置換する。
- 既存 `build_approved_manifest` test 4 本の synthetic active は `generation_number=2` を明示する。これにより D1370 の「非 g1 は document/root を観測せず返る」実 callee 経路を通し、各 test 本来の pin、単一 snapshot、cell product の主題を維持する。
- 2 正例では、差替え対象をモジュール object `ratified_freeze` の属性 `assert_g1_floor_selection_identity` とする。差替え前の実関数を保存し、wrapper は candidate identity と root を記録してから同じ引数で実関数へ委譲する。
- [1346 の test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1346) は pin 無し・pin 有りの両呼出しについて `[(active, root), (active, root)]` を assert する。gate を spec 読込後へ移す変異も殺せる。
- [1375 の test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1375) は loader と selection wrapper が各 1 回、同一 `active` と `root` を受けたことを assert する。

この wrapper は selection の stub ではない。保存した実 `assert_g1_floor_selection_identity` を同じ candidate/root で必ず呼ぶ。production が gate を呼ばなければ記録件数の assert が落ち、実 callee が拒否すれば例外を伝播するため、選択強制を通らない緑にはならない。

## 4. 実 callee を通る追加 test

[test_s8b_oracle_manifest.py:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1432) の既存 consumer test 群の直後へ、次の 2 本を追加する。

`test_build_approved_valid_real_g1_reaches_spec_after_actual_selection_gate`

- `test_s8b_ratified_freeze.build_production_emitter_g1` [966](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_freeze.py:966) で genuine g1 repository を構築する。
- loader は monkeypatch せず、`build_approved_manifest` 自身に実 `load_ratified_freeze(root)` を呼ばせる。
- 公開 selection 属性には、前述の実 callee 委譲 wrapper だけを置く。
- approved spec pin は明示的に `None` とし、期待結果を `ManifestCliError.reason == "no-approved-spec"` とする。
- wrapper が exact `RatifiedFreeze`、`generation_number == 1`、同じ `root` を 1 回受け、実 callee が正常 return したこと、および output が無いことを assert する。
- gate が無ければ wrapper 回数が 0、gate が過剰拒否すれば `no-approved-spec` へ到達しない。

`test_build_approved_real_g1_rule_mismatch_preserves_selection_reason`

- 同じ builder で genuine g1 を作る。
- selected run より早い同一 namespace の official-shaped result path を追加して commit する。既存の組立例は [test_s8b_ratified_verify.py:834](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_verify.py:834) にある。
- monkeypatch するのは `s8b_holdout_freeze` module object の属性 `_derive_floor_selection_eligibility` だけとし、追加した earlier result に `True` を返す。公開 loader と公開 `assert_g1_floor_selection_identity` は差し替えない。
- `build_approved_manifest` が `ManifestCliError` を送出し、`reason == "floor-selection-rule-mismatch"`、`__cause__` が同じ reason の `RatifiedFreezeError`、eligibility callee の呼出しが `[earlier_rel]`、output 不在であることを assert する。

この lower seam は選択機構を迂回しない。real public callee が namespace を列挙し、earlier result を eligibility 導出へ渡さなければ、期待例外も呼出し列も成立しない。既存の同じ攻撃形は [test_s8b_ratified_verify.py:872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_verify.py:872)、real callee の正常系は [952](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_verify.py:952) にある。

## 5. 変異事前登録候補

実装後の新 gate 行を概ね `s8b_oracle_manifest.py:1206` として、5 件を登録候補とする。

| 変異 | 変異する行 | 期待 KILL test node |
|---|---|---|
| gate 呼出しを削除、または `pass` に置換 | 新 `1206` | `orchestrator/tests/test_s8b_oracle_manifest.py::test_build_approved_real_g1_rule_mismatch_preserves_selection_reason`。2 正例の selection 呼出し回数 assert も KILL。 |
| `ratified` の代わりに `ratified.document` を渡す | 新 `1206` | `::test_build_approved_valid_real_g1_reaches_spec_after_actual_selection_gate`。期待 `no-approved-spec` より先に `floor-artifact-invalid` になる。 |
| `root` を省略、または module `ROOT` に置換 | 新 `1206` | `::test_build_approved_valid_real_g1_reaches_spec_after_actual_selection_gate`。tmp genuine g1 ではなく実 repository を探索するため正常 return しない。既存 g2 正例だけではこの変異を殺せない。 |
| gate を `load_approved_spec` の後へ移動 | 新 `1206` を現在の `1213` 以後へ移動 | `::test_build_approved_valid_fixture_output_depends_only_on_spec_pin`。pin 無し呼出しでも gate が 1 回必要という assert が落ちる。real g1 負例も `no-approved-spec` が先行して落ちる。 |
| `exc.reason` の passthrough を固定 `"floor-selection-unverifiable"` に潰す | 実装後の reason 選択行、概ね `1209-1212` | `::test_build_approved_real_g1_rule_mismatch_preserves_selection_reason`。期待 `floor-selection-rule-mismatch` と不一致になる。 |

登録する 5 件は、上記追加 test を含めれば恒真ではない。

一方、次は有効な KILL 証拠に数えない。

- fixture 未追随の現行 1369/1395 は正しい gate 自体で元から赤になるため、変異試験の baseline として無効。
- `root` 省略変異を synthetic g2 test だけで検査しても、公開 helper は root を観測する前に return するため生存する。これを genuine g1 正例で殺す。
- `ManifestCliError` の detail 文言だけを変える変異は reason と fail-closed 挙動を変えず、計画した assert でも赤にならない。gate 無効化変異ではないので事前登録しない。

## 6. 焦点走の file 集合

`build_approved_manifest` の test caller は repository 全体の参照検索で [test_s8b_oracle_manifest.py の 5 箇所](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:1340) だけである。したがって変更機能の最小焦点は同 file である。

production module 自体への直接 import/reference を基準にした焦点走集合は次の 11 test files になる。

- [test_s8b_oracle_manifest.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest.py:22)
- [test_s8b_oracle_manifest_contract.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_manifest_contract.py:13)
- [test_s8b_oracle_driver.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_driver.py:83)
- [test_s8b_oracle_report.py:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_report.py:42)
- [test_s8b_oracle_judge.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_oracle_judge.py:23)
- [test_s8b_verdict.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_verdict.py:26)
- [test_s8b_oracle_materialization.py 相当の test_s8b_materialization.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_materialization.py:337)
- [test_s8b_binding_driftguards.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_binding_driftguards.py:37)
- [test_s8b_holdout_admission.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_holdout_admission.py:22)
- [test_s8b_experiment_numbers.py:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_experiment_numbers.py:18)
- [test_s8b_ratified_freeze.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/tests/test_s8b_ratified_freeze.py:41)

`s8b_oracle_spec_fixture.py` も module を直接 import するが test node file ではないため、独立した焦点走対象には数えない。`test_s8b_oracle_artifacts.py` など、generator record の文字列として filename だけを持つ test は直接 consumer ではないため除外する。

## 7. (P1) への賛否

| provisional 裁定 | 賛否 | 根拠 |
|---|---|---|
| P1-a | 同意 | public load-only 入口である `build_approved_manifest` の load 直後が、選ばれた active snapshot と同じ object を検査できる最狭点。`build_manifest_from_ratified` の唯一の production caller は [1244](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_manifest.py:1244) であり、lower builder に gate を置くと loader を持たない構築 primitive へ I/O policy を持ち込む。 |
| P1-b | 同意 | module 属性 seam は使うが、loader と selection assert の二重 stub は使わない。既存 2 正例は実 callee 委譲 wrapper、機構証明は実 loader・実 public callee の genuine g1 正例と負例で担う。 |
| P1-c | 同意 | 本 wave で driver を変更しない結論に同意する。ただし観察は一部補正が必要。line [496](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_driver.py:496) は load-only の可能性が残る一方、line [644](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_driver.py:644) で得た candidate は直後の [launch_validate:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-oracle-manifest-selection/orchestrator/campaign/s8b_oracle_driver.py:663) へ渡るため、その経路は既に selection 強制を含む。いずれも oracle manifest 群の production 変更には含めない。 |

D1370 の g1 限定、非 g1 無観測、新理由禁止は [rulings-verbatim.md:40](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/rulings-verbatim.md:40)、test 専用抜け道の禁止は [D1371:101](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-t2067-oracle-manifest-selection/rulings-verbatim.md:101) と整合する。

静的検査のみで、書き込みと pytest 実走は行っていない。したがって緑とは報告しない。

## 総括

gate 挿入位置: `build_approved_manifest` の `load_ratified_freeze(root)` 直後、同じ `RatifiedFreezeError` catch 内。  
2 正例の追随方針: synthetic を明示 g2 にし、実 callee 委譲 wrapper の呼出しを assert、別途 genuine g1 統合 test を置く。  
偽緑を防ぐ正例・負例: actual loader/callee で valid g1 が spec 段へ進む正例と、earlier eligible run を real selection が `floor-selection-rule-mismatch` で拒否する負例。  
変異候補数: 5 件。元から赤の未追随正例と、g2 だけでは殺せない root 変異は証拠に数えない。  
(P1) への賛否: P1-a、P1-b、P1-c すべて同意。ただし P1-c の driver:644 は直後に `launch_validate` があると補正する。