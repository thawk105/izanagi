## 所見

### R1. 項目 1 の 7 node は母集合を閉じていない

**主張**: プランの 7 件は不正確である。`test_any_native_discovery_toml_is_rejected` は `_fixture()` 使用で実 `_REPO` を読まず、逆に実 `_REPO` を読む 3 node が抜けている。

**根拠**: `s2-plan.md:30-44`、`parent-measurements.md:36-53`、`orchestrator/tests/test_codex_agents.py:519`、`:914-918`、`:1306`。実 `_REPO` 参照は 9 node、`load_role_specs` 直呼びは 5 node。ロール集合の実体は `orchestrator/codex_roles/spec.py:320-331`、`:500-548`。

**帰結**: 7 件を受理集合の分母にすると、実 `_REPO` を読む 3 防壁が監査・変異・完了判定から落ち、「11 node を維持した」という値が成立しない。

**深刻度**: blocker

### R2. `neither` は D463 の比例分類を置き換えない

**主張**: 項目 1 は「非比例」ではなく、D463 の第三分類「比例だが設計上限のある固定用途集合」である。`neither` は成長分類ではなく、修正対象側がないという処置分類としてのみ成立する。

**根拠**: `docs/decisions.md:19302-19320`、`s2-plan.md:16-24`、`output/insights/2026-08-16_t1222-growth-hold-sweep/README.md:21-23`、`:98-105`。一方、件数 7 と総数 11 は `docs/archive/worklog-phase3-0816-606.md:547-549`、`docs/archive/worklog-phase3-0817-611.md:495-503` に残っている。

**帰結**: `neither` を「非比例」と記録すると、D463 の分類、hold 判定、次 wave の受理集合が混線する。件数も 9 node / 合計 13 node に訂正しない限り台帳の分母が変わる。

**深刻度**: must-fix

訂正は過去の archive を書き換えず、`docs/spool/worklog/` に追補を置く。内容は次の 3 点とする。

- 旧記録の 7 / 11 は母集合未閉包時の暫定値。
- 現在の静的監査では項目 1 の実 `_REPO` 参照は 9、全項目の実参照候補は 13。
- 項目 1 は「D463 第三分類、処置分類は `neither`」であり、「非比例」ではない。

`output/insights/.../README.md:21-23` と `:98-105` は第三分類を正しく記録しているため、上書きせず追補で意味を明示する。もし `neither` を非比例の意味で書くなら、これらの行も誤記になる。

### R3. 項目 2 の変異 anchor は D452 と isolation meta-test に同時違反する

**主張**: プランが期待赤 node とする新 test は、同じ `test_dev_waves_integration.py` に置く限り `xdist_group` が必要になる。しかし D452 (c) は期待赤 node の `xdist_group` を禁止する。

**根拠**: `s2-plan.md:66-85` は新 test を no-group としている。現行の child 起動 node は `orchestrator/tests/test_dev_waves_integration.py:2050-2058`、`:2165-2167` にあり、後者は `@pytest.mark.xdist_group("dev-waves-runtime")` を持つ。runtime 呼出しを AST で伝播判定する検査は `orchestrator/tests/test_dev_waves_isolation_contract.py:33-41`、`:102-126`。

**帰結**: 同じファイルに no-group の期待赤 node を置くと isolation 検査で失敗し、group を付けると D452 で変異登録が無効になる。したがって mutation の killed 判定を受理できない。

**深刻度**: blocker

代替は、巨大 integration module を親で import しない別の `test_*.py` に child import closure の契約検査を置くか、期待赤 nodeを登録せず親側の直接計測にすることである。

### R4. 項目 3 の `LIVING_DOCS` 縮小では比例源を除去できない

**主張**: `LIVING_DOCS` を `[PREREG_DOC]` に絞っても、`check_docs.main()` は archive、worklog、output、handoff、spool などを全走査する。

**根拠**: プランは `s2-plan.md:89-130`。`main()` の全体処理は `tools/check_docs.py:5217-5327`、archive/output の列挙は `:1589-1691`、placeholder は `:1716-1833`、backlog は `:1839-2140`、handoff は `:5403-5426`。成長源も `output/insights/.../README.md:66-67` に記録されている。

**帰結**: docs/archive/output が 10 倍になると、修正後もこの node は概ね 10 倍のままで、減るのは living-doc loop の定数だけである。目的の受理コスト上限は変わらない。

**深刻度**: must-fix

`main()` 全体を呼ばない局所負例検査へ分離し、別 node で全体 main path の防壁を維持する必要がある。

### R5. 項目 4 は受理集合を変える

**主張**: selected commit が 1 件のときだけ selected commit から policy epoch を探す変更は、現在の off-head 判定を変える。また `None` は安全な一値ではない。

**根拠**: resolver は `tools/check_ai_provenance.py:1170-1184`、呼出しは `:1605-1607`。`scope_epoch is None` では scoped finding が追加されず `:1492-1497`、`implementation_epoch is None` では author/waiver 検査が省略される `:1500-1515`。ledger visibility は `:1589-1593`、stale violation の rc2 化は `:1720-1729`。

既存の `test_known_violation_off_head_policy_guard_is_stale_rc2` は `test_check_ai_provenance.py:2446-2492` にあり、現行は HEAD に epoch がないため rc2 になる。プランの 1 件経路では target 祖先の epoch を発見し、missing Codex author が finding として消費され、rc0 になり得る。さらに同じ target を含む 2 件範囲では `HEAD` を使うため、再び rc2 になり得る。分岐は `s2-plan.md:157-166`。

**帰結**: selected 件数だけで同じ target の rc0 / rc2 が変わり、missing-author の受理集合と stale violation の値が変わる。これは性能最適化ではなく監査意味の変更である。

**深刻度**: blocker

selected revision を使うなら off-head の権威境界を明示し、`None` を「検査省略」と「policy 不在」に兼用しない設計とテストが必要である。受理集合を変えるなら新しいユーザー裁定が要る。

### R6. 項目 4 の resolver 引数化は既存 monkeypatch を取りこぼす

**主張**: resolver に `revision` 引数を必須として渡す実装は、zero-argument lambda を使う既存検査を壊す。

**根拠**: `test_check_ai_provenance.py:3654-3661` は resolver を `lambda: None` 形式で差し替えている。プランが更新対象として挙げるのは主に 2 target test である `s2-plan.md:169-179`。main の例外捕捉も `tools/check_ai_provenance.py:2579-2621` で、一般の `TypeError` は対象外である。

**帰結**: `test_forward_correction_merge_base_rc128...` の期待 rc128 が、意図した guard 判定ではなく TypeError に置き換わり、node の受理集合から外れる。

**深刻度**: must-fix

全 monkeypatch caller を列挙して引数対応するか、zero-argument wrapper を残したまま revision-aware resolver を別 seam にする必要がある。

### R7. 費用対効果の軸が逆転している

**主張**: 項目 1 の no-op 方針は D451 に沿うが、項目 4 は 0.4 秒未満の低コスト node に受理意味変更を持ち込み、複数 selected の重い経路は残す。約 9 秒の項目 2・3では、項目 3の改修が比例源を除けていない。

**根拠**: `parent-measurements.md:90-99`、D451 `docs/decisions.md:18866-18887`、項目 4 の分岐 `s2-plan.md:157-166`、現行 resolver 呼出し `tools/check_ai_provenance.py:1605-1607`。

**帰結**: 軽い node の意味だけが変わり、複数 commit の full-history cost は 10 倍成長し得るまま残るため、性能改善値と監査受理集合の両方が計画値からずれる。

**深刻度**: must-fix

## 各項目の比例判定の検算

| 項目 | 分類 | 10 倍成長時の倍率 | 根拠 |
|---|---|---:|---|
| 1 | `neither`。ただし D463 第三分類であり、非比例ではない | 通常の repository 成長では約 1 倍。role 集合の意図的追加時だけ段階的に増える | `spec.py:320-331`、`:500-548`、`review_ledger.py:10-13`、insight `:41-56` |
| 2 | `test-side` | 現状は巨大 integration test corpus に対して約 10 倍。完全な child helper 分離後は約 1 倍 | `test_dev_waves_integration.py:2050-2058`、child workload `:1685-1814` |
| 3 | `test-side` | 提案された singleton patch 後も約 10 倍。living-doc 部分の定数だけ減る | `check_docs.py:1589-1691`、`:1839-2140`、`:5217-5327` |
| 4 | `target-side` | selected 1 件の修正経路は約 1 倍だが、selected 複数件は HEAD 探索が残り約 10 倍 | `check_ai_provenance.py:1170-1184`、`:1605-1607`、`s2-plan.md:157-166` |

`neither` は、D463 の固定用途集合であることを入力集合の根拠付きで示し、hold を追加しない場合に限り裁定への回答になる。単に安い、または修正が難しいという理由で `neither` にするのは裁定の回避である。

## 親 brief への反論

- P1 の「項目 1 は比例でない」は不正確で、正しくは D463 第三分類である。ただし no-op 方針自体は妥当である。
- P1 の 7 node / 総数 11 は母集合未閉包であり、実 `_REPO` 参照 9 nodeを再棚卸しすべきである。
- P2 の target-side 判定は正しいが、selected revision の導入は off-head の rc と finding 受理を変えるため、そのまま受理できない。
- P3 の test-side 判定は正しいが、`LIVING_DOCS` だけの縮小では比例源を除去できない。
- P4 の child self-import は test-side の実問題であり、helper 分離の方向は妥当。ただし予定した期待赤 nodeは D452 と isolation 検査に抵触する。
- `hold_inventory.py` の誤報と未閉包の母集合は brief の scope 外 `brief.md:19-20` であり、本 wave に混入させる根拠はない。

## refuted

- 新しい `_dev_waves_serve_child.py` 自体が file-set meta-test を赤にする、という懸念は確認できない。pytest の対象は `pytest.ini:12-14` の `testpaths` と `test_*.py` 命名であり、`test_plain_runner_coverage.py:44-86` も `test_*.py` だけを列挙する。`_dev_waves_serve_child.py` は collection 対象でも direct test ledger 対象でもない。
- exact な `orchestrator/tests/` file 集合を pin する meta-test は確認できなかった。`test_pytest_collection_config.py:94-120`、`:167-187` が pin するのは collection option と scoped collection であり、全 file 集合ではない。
- `hold_inventory.py` の false report は既存の scope 外事象であり、insight `README.md:140-150` の記録どおり本 wave の原因ではない。
- 項目 1 に実装差分がないこと自体は問題ではない。D463 第三分類と no-hold を明記し、7/11 の台帳値だけを追補訂正すればよい。

## 総括

blocker は、項目 1 の母集合不一致、項目 2 の D452 不能な期待赤 node、項目 4 の受理集合変更である。項目 3 は singleton 化では成長比例を直せず、項目 4 は caller 互換性と複数 commit 経路も未解決である。項目 1 の `neither` は D463 第三分類に対する処置分類としてのみ成立し、archive は改変せず spool と insight 追補で 9 / 13 と意味を訂正すべきである。pytest は実走していないため、緑とは判定していない。