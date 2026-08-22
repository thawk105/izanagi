結論：段2 plan はそのまま採用できません。4 経路が通常の runner 形では封鎖されることは支持できますが、提案文言は guard の適用範囲を越えて一般化しています。

`enforce_held_functions` の分岐は次のとおりです。[growth_test_holds.py:631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/orchestrator/tests/growth_test_holds.py:631)

- `plain_runner="manual"` / `"none"` の `__main__` 実行は、既定の `import-and-call` なら 689 行で import-time 拒否される。
- `pytest --noconftest` / `--confcutdir` は enforcing session が無いため、通常は同じく 689 行で拒否される。
- 通常の直接 import は、既定 mode なら import-time 拒否される。`call-only` なら import は通り、wrapper の呼出し時に 605–606 行で拒否される。
- `plain_runner="pytest-delegating"` の `__main__` は 685–688 行の例外で import-time 拒否されず、`pytest.main(...)` へ委譲される。通常の conftest が enforcing session を作れば、import guard ではなく collection 側の保留になる。したがって、親の manual file で得た「4 経路すべてが同じ `GrowthTestHoldBypassRefused`」は、`none` と `pytest-delegating` へそのまま一般化できない。

また、`@wraps` により wrapper には `__wrapped__` が残ります。[growth_test_holds.py:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/orchestrator/tests/growth_test_holds.py:602) D360 自身も、同一 process 内の任意コードによる `__wrapped__` 呼出しや guard 再束縛は対象外と明記しています。[decisions.md:15699](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1456-hold-bypass-reclassify/docs/decisions.md:15699)

したがって、

- `known-resolved-bypass` は「登録された runner 起動形について解決」と限定しない限り、一切の回避不能という誤読を招く。
- `rejected-by-hold-guard` も、exact token、enforcing pytest session、`pytest-delegating` の委譲例外を明示すべき。
- `direct-test-function-call` の `import-test-module-and-call-function` は通常の import と canonical な関数呼出しだけを指し、`__wrapped__` や再束縛を含意しない。

推奨は `known-guarded-runner-path`、`blocked-on-registered-runner-path` のような限定的な値です。reason も「exact token 無しの登録 runner 経路」「in-process の `__wrapped__` / 再束縛は対象外」と書くべきです。

`tracking: "T-930"` は解決済み entry では active tracking と誤読されます。維持するなら `resolved_by` / `resolution_reference` に改名し、単なる履歴参照であることを明示してください。

## 総括

1. **P1: real** — 文言と reason が guard の保証範囲を過大申告し、4 経路の挙動も一様ではない。
2. **P2: refuted** — brief の要約どおり D347 は literal 値を pin しておらず、限定的な文言へ直せば D347 との構造的抵触はない。テストは実行していない。