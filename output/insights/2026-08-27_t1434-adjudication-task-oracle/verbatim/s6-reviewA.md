## 所見

**所見は 0 件です。** レンズ A の静的検査では、裁定に反する受理集合の拡大・承認外の過剰拒否・既存ゲートの弱体化を確認できませんでした。これは実装の承認判定ではありません。

所見なしと判断した範囲は次のとおりです。

- join 前倒し: [s5-diff.patch:785](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1434-adjudication-oracle/context/s5-diff.patch:785)、[tools/codex_reasoning_ab.py:9381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9381)。旧 join 位置までに行われていたのは verdict の局所構築だけで、reason 追記や `joined` への格納はありません。前倒しにより消える reason 経路はありません。
- helper の副作用: [tools/codex_reasoning_ab.py:9922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9922)、[同:10550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:10550)。loader と aggregate が同じ dimension reason を積み得ますが、certified 出力は `sorted(set(reasons))` で重複除去されます。直接 loader の exact-count テストでは helper は一度しか呼ばれません。
- verdict 不在 slot: [tools/codex_reasoning_ab.py:10191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:10191)。これは受理集合を狭めますが、R8 の missing-field rejection と R10 の内部 caller に対する invariant の射程内です。certified replay では既に packet/verdict/mapping の全単射を要求しており、正当に verdict が欠ける経路は見つかりませんでした。
- テスト弱体化: [orchestrator/tests/test_codex_reasoning_ab.py:15432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:15432)、[同:15553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:15553)、[同:15588](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/orchestrator/tests/test_codex_reasoning_ab.py:15588)。削除された assert、反転、緩和、skip、xfail、approx 化はありません。変更された三つの空 verdict fixture は `oracle_kind` を slot から導出しており、現行 hash や実行結果の直書きではありません。
- blind 境界: [tools/codex_reasoning_ab.py:11547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:11547)、[同:11569](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:11569)、[同:11649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:11649)、[同:11738](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:11738)。三つの blind operation は manifest-wide union のままです。
- D931 / D767: digest exact 検査は [tools/codex_reasoning_ab.py:9266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9266) に残り、`task_acceptance_status=unbound` 等は [同:4041](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:4041) から不変です。
- 例外処理: [tools/codex_reasoning_ab.py:9404](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9404)。`except ValidationError` は `exc.reasons` を必ず追加してから `continue` しており、無理由の握り潰しではありません。

## 裁定別判定

- R1: 適合。union 検査を残し、join 後に task 別検査を追加。
- R5: 適合。4-slot paired schedule、schedule descriptor、実 loader と external-manifest verify 経路を実装。
- R6: 適合。parent / second-reader を parametrize し、reason の exact 1 件を検査。
- R7: 適合。aggregate の cross-task `equivalent_to` 負例を追加。
- R8: 適合。`oracle_kind` の wrong / missing を個別に拒否。
- R9: 適合。dimension join 失敗は reason 追加後に除外。
- R10: 適合。aggregate の exact 比較を冗長 invariant として維持。
- R11: 適合。`oracle_kind` は [tools/codex_reasoning_ab.py:9450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9450) で verdict に入り、[同:9477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1434-adjudication-oracle/tools/codex_reasoning_ab.py:9477) の hash より前です。
- R12: 適合。in-memory 負例と external-file transport 正例の双方があります。
- R13: 適合。blind union、D931 digest、D767 `unbound` を保存しています。

`git diff --check` と対象 2 ファイルの AST parse のみ実施しました。pytest は実走しておらず、緑とは判断していません。

## 総括

must-fix: **なし**。