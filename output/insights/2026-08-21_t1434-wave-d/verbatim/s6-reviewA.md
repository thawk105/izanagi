## 所見一覧

1. **arm/model pair 判定** — `[refuted / blocker]`  
   [tools/codex_reasoning_ab.py:5227](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5227) の `len(arm_model_pairs) != 2` は正しい。同一 arm・異なる model、異なる arm・同一 model は受理し、同一 tuple は拒否する。両方が異なる場合も裁定の「片方だけ違う分には問わない」に形式上適合する。

2. **両軸同時変化の扱い** — `[unclear / major]`  
   異なる arm・異なる model は現在受理される。preregistration は同時 model 軸比較を主解析にしないが、schema で拒否するかは未裁定である。実装欠陥というより、schema と解析規約の境界が未定義である。

3. **blind verdict の manifest union** — `[refuted / blocker]`  
   [tools/codex_reasoning_ab.py:6992](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:6992) は manifest 全体の union を使い、`append_verdicts` も [tools/codex_reasoning_ab.py:7071](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:7071) で task を絞っていない。task-specific 検査は reveal 後の [tools/codex_reasoning_ab.py:5808](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5808) に分離されており、盲検漏洩経路は見つからない。

4. **axis tuple の `None`** — `[refuted / minor]`  
   [_AXIS_FIELDS](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5557) の固定順序に従い、[tuple key 構築](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5718) は `(task, stage, model, cache, price, arm)` となる。`stage=None` と `cache_condition=None` は値が同じでも位置が異なるため混同しない。

5. **`legacy_projection` 境界** — `[refuted / major]`  
   [tools/codex_reasoning_ab.py:5913](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5913) は、非 POS/NEG task が混在すれば subset 条件で `False` になり、POS/NEG だけでも stage/model/cache/price が共有されなければ `False` になる。cache/price の非 null 値は [tools/codex_reasoning_ab.py:5118](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5118) で fail-closed されるため、受理済み結果が誤って legacy 扱いになる経路は確認できない。  
   ただし `<=` なので、POS のみ・`max` のみでも legacy 分岐に入る境界は `[unclear / minor]`。full legacy schedule だけを意味するなら `==` の要否を明記すべきである。

6. **schedule なし `make_packets` の cardinality** — `[real / major]`  
   [tools/codex_reasoning_ab.py:6848](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:6848) で `schedule_descriptor is None` の場合、期待件数・slot 集合・非空性の検査がないまま進む。1 slot、9 slot、11 slot の manifest でも packet 化できる。既存テストも [test_mapping_custodian...:7588](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/orchestrator/tests/test_codex_reasoning_ab.py:7588) でちょうど10件を使うだけで、過少・過多を検査していない。

7. **schedule 付き legacy descriptor の互換性** — `[real / major]`  
   `_validate_schedule` は schema 欠落を v2 としてコピー補完する一方、`make_packets` は [tools/codex_reasoning_ab.py:6862](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:6862) で元の未補完 `schedule` を `expected_schedule_from_manifest` に渡す。同 helper は schema 欠落を v2 と認識せず拒否するため、schema なし schedule descriptor は validator を通過した後に失敗する。

8. **`by_arm_case` の生成条件** — `[real / minor]`  
   [tools/codex_reasoning_ab.py:5737](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1434-wave-d/tools/codex_reasoning_ab.py:5737) は task ID だけで判定する。POS/NEG のまま requested model が複数ある schedule では `by_arm_case` を出すが、`legacy_projection` は `shared_dimensions` が複数になるため `False` である。主判定は壊さないが、legacy projection と token observation の出力契約が不一致になる。

## 総括

- arm/model pair と blind union の最重要変更は正しく実装されている。  
- tuple key の `None` も、固定フィールド順により混同しない。  
- `legacy_projection` の混在検出と null fail-closed も妥当である。  
- 実害のある問題は、schedule なし `make_packets` の cardinality 検査欠如と、schema 欠落 schedule の再正規化漏れである。  
- `by_arm_case` は model 軸を見ないため、軸集計と互換出力が不整合になる。  
- 静的検査のみ実施し、編集・pytest・Web検索は行っていない。