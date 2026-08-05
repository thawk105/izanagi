| 所見 | 判定 | 根拠 |
|---|---|---|
| レビュー A 所見 1 — M1 の偽 kill | **closed** | 比較偽装は専用 node [test_s1_known_axes_freeze.py:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:236) に分離され、他の無効名を先に走査しない。M1 で型検査 [s1_known_axes_freeze.py:156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:156) を削除すると、偽装 object は `g_none` の membership と mask 0 lookup を通り、専用 node の `pytest.raises` が成立しない。 |
| レビュー B 所見 1 — import 時 fail-closed | **closed** | import 時は cache を `None` に置くだけ [s1_known_axes_freeze.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:117)。index 構築は初回 helper 呼出し内 [同:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:127) まで遅延された。consumer import 後も `None`、衝突失敗後も `None` を検査する隔離 subprocess node がある [test_s1_known_axes_freeze.py:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:160)。 |

## 新規所見 1 — 非 str 拒否が `__repr__` を実行し、`FreezeError` 契約を破れる

- 種別: 構造化拒否境界の迂回
- 根拠: 正本は非 str を必ず `FreezeError` にする契約である [ruling.md:74](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t532-name-mask-binding/ruling.md:74)。しかし実装は次の順である [s1_known_axes_freeze.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:150)。

```python
raise FreezeError(
    f"... name={name!r} ...")
...
if type(name) is not str:
    reject()
```

`name!r` は `FreezeError` の生成前に `name.__repr__()` を実行する。したがって、`__repr__` が例外を送出する非 str／`str` subclass では、その例外が外へ出て `FreezeError` は送出されない。同じ穴が emitter の非文字列診断にもある [同:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:101)、[同:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:110)。

- 影響: 受理の fail-open ではないが、正本の例外型契約を破り、`FreezeError` だけを変換する consumer 境界を custom `Mapping`／helper 直呼び経路で抜ける。レビュー B が閉じようとした構造化診断も、この入力では維持されない。
- 重大度: **must-fix**
- 提案: 非 str 分岐では対象 object の `repr` を使わず、固定文言または安全な型名だけで直接 `FreezeError` を送出する。builder 側も型検査と重複検査を分離し、`repr` 爆弾の専用回帰 node を追加する。

この穴は fix 前 snapshot にも存在するため、今回の遅延化が新設した回帰ではない。ただし最終差分に残る正本違反である。

## キャッシュ・順序・テスト隔離

- 失敗はキャッシュされない。builder が完了するのは [s1_known_axes_freeze.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:127)、期待名 tuple の構築完了が同 128–135、global 代入はその後の [同:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:137) だけである。途中例外を捕捉して成功値へ変換する経路はない。
- 衝突注入は subprocess 内で行われ、失敗後の `None` と成功後の cache を逐語で検査する [test_s1_known_axes_freeze.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:168)。親 pytest process へ変更済み emitter/cache は漏れない。main process の衝突テストは cache ではなく local builder を直接呼び、patch context 終了時に復元される [同:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:144)。
- 診断順は正準述語 → mask 復元 → index 構築である [s1_known_axes_freeze.py:144](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:144)。従って「emitter 衝突＋非正準述語」の二重故障では非正準述語診断が先になる。これは fix 前 snapshot の import 衝突優先からは変わるが、HEAD 由来の既存正準述語診断を維持する順序であり、両経路とも拒否されるため新たな受理回帰とは判定しない。

## M1〜M7 の静的 kill 再確認

以下は実走結果ではなく、事前登録された最小 kill node の逐語判定である。

| 変異 | 静的に赤となる登録 node | 判定理由 |
|---|---|---|
| M1 | `test_trigger_name_mask_binding_rejects_comparison_spoof_name` [test:236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:236) | 専用 node は比較偽装 1 件だけ。型検査削除後は spoof lookup が mask 0 を返し、`pytest.raises` が不成立。subclass node も別途赤になるが、比較偽装 node を遮らない。 |
| M2 | `test_trigger_entries_rejects_coordinated_canonical_name_mask_tamper` [test:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:300)、`test_validate_schema_rejects_coordinated_canonical_name_mask_tamper` [test:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:352) | helper 先頭 `return` で両層の唯一の name-mask 拒否が消える。述語は正準、main/remeasure は同一。 |
| M3 | schema 層 node [test:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:352) | `_validate_schema` の呼出し [source:807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:807) を消すと、他の schema 条件を維持した正準 mask 0 改竄が通る。 |
| M4 | 生成層 node [test:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:300) | 呼出し [source:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:577)、[source:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:583) の対象側を消すと、同一 mock provenance のため後続 equality では落ちない。 |
| M5 | `test_current_six_frozen_trigger_predicates_pass_semantic_membership` [test:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:99) | alias 登録 [source:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/campaign/s1_known_axes_freeze.py:113) を消すと、最初の `ident_all` が index 非所属で過剰拒否される。 |
| M6 | `test_trigger_name_mask_binding_accepts_all_32_masks` [test:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_s1_known_axes_freeze.py:110) | `(4, 8, 31)` だけでは最初の mask 0／`g_none` が index に無く、正例が拒否される。 |
| M7 | `test_mask_for_canonical_predicate_recovers_all_32_masks[space/tab/crlf/vertical-tab/form-feed/nbsp/ideographic-space]` [test:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t532-name-mask-binding/orchestrator/tests/test_trigger_gate_binding.py:240) | 逆順列挙では mask 0 predicate の復元値が 31 になり、各 parameter node の最初の assert が赤になる。 |

登録変異の静的生存は見つからない。M1 の分割後 node は各々一入力であり、M2〜M4 の登録 node も正準述語・同一 provenance・不変 schema により name-mask 検査の有無だけへ帰属している。

## 凍結面

`git diff` の変更対象は次の 4 ファイルだけだった。

- `orchestrator/campaign/s1_known_axes_freeze.py`
- `orchestrator/campaign/trigger_gate_binding.py`
- `orchestrator/tests/test_s1_known_axes_freeze.py`
- `orchestrator/tests/test_trigger_gate_binding.py`

`output/s1-freeze/known_axes_freeze.json`、`orchestrator/campaign/s8a_trigger_sweep.py`、`orchestrator/campaign/axis_trigger_gating.py` に対する個別 `git diff` はすべて空。`git diff --check` は成功した。pytest は実行しておらず、緑は主張しない。

## 総括

**NO-GO**。  
レビュー A/B の元所見は closed、M1〜M7 の静的生存もない。  
ただし非 str の `repr` 実行により、正本が要求する `FreezeError` を送出しない経路が残る。  
安全な診断化と専用回帰 node を入れてから land すべきである。