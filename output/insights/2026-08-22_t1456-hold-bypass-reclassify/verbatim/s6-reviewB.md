結論：段3の「import-time 一律拒否」という過大申告は解消されています。ただし、段4裁定が求めた `T-930` の解決済み明示は、段5 diff では未反映です。

- `plain_runner="manual"/"none"` は token 無しで import 時に拒否されます。`pytest-delegating` は [guard実装](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/orchestrator/tests/growth_test_holds.py:671) の通り `pytest.main(...)` へ進みますが、wrapper が token 無しの本体実行を阻止します。したがって `blocked` は「held 関数が実行されない」という outcome として正確で、import-time 拒否とは断定していません。[s5 diff](/home/SFC/tanab/.claude/jobs/81b7b7c8/tmp/dev-wave-t1456/artifacts/s5-diff.patch:14)
- `pytest --noconftest`、`--confcutdir`、通常の直接関数呼出しも、登録された経路では token 無しで guard に止められます。[wrapper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/orchestrator/tests/growth_test_holds.py:602)
- plain-runner の D360 文言は正確です。D360 は runner 起動形を対象とし、同一 process 内の任意コードによる `__wrapped__` 呼出しや guard 再束縛を保証対象外としています。[D360](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/docs/decisions.md:15699)
- `known-guarded-bypass` も、`known-unresolved-bypass` と区別して「既知の経路だが現在は guard 済み」と読めるため、実質的な混乱はありません。
- ただし、4 entry すべての `reason` は「token 無しでは blocked」と述べるだけで、`T-930` により解決済みであることを明示していません。これは「reason 側で解決済みを明示する」という段4裁定への不充足です。[裁定](/home/SFC/tanab/.claude/jobs/81b7b7c8/tmp/dev-wave-t1456/artifacts/ruling-s4.md:24)

pytest は実行していません。

## 総括

**real**

- `T-930` の解決済み明示が全 entry の reason に欠落。段4裁定未達。

**refuted**

- `pytest-delegating` を含む `blocked` 表現の outcome 解釈。
- D360 適用範囲との矛盾。
- `known-guarded-bypass` の分類上の重大な混乱。

**nit**

- `Running a test file directly is blocked` は、より厳密には「held test execution is blocked」とすると import-time 拒否との混同をさらに避けられます。