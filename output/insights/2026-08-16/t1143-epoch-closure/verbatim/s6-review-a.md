### 所見 1: path-removal 変異が certified gate 到達前の fixture エラーで殺され、偽の検出力になる
- 深刻度: major
- 根拠: `orchestrator/tests/test_artifact_admission.py:317` と `:324` は fixture の作成対象を production の `CONTRACT_LOADER_RELATIVE_PATHS` から導く。一方、literal parametrize は `:1113`〜`:1121` に残るため、production tuple から対象 path を削除すると node は残るが、その file は作られない。結果、`:1137` の `verifier.read_bytes()` が `FileNotFoundError` となり、`:1139` の certified admission 呼び出しへ到達しない。
- 成果物影響: M1〜M4 で対象 path を閉包から外すと、実際の certified 受理集合はその verifier drift を受理する方向へ広がる。それにもかかわらず、テスト node は fixture 構築由来の赤となり、変異 matrix が `KILLED` を記録できる。現在は `orchestrator/tests/test_t671_source_binding.py:123` の独立 exact tuple testも削除を検出するが、新規 drift test が certified gate を検出したという証拠と単一理由性は成立しない。
- 提案: `_committed_closure_repo()` が作成・`git add` する 12 path を test-only の独立 literal にする。parametrize は現在の literal 4 path を維持する。これにより production tuple から path を外しても対象 file が存在し、`:1139` の `pytest.raises` が「gate が drift を受理した」ことを理由に赤になる。

## 総括

NO-GO  
実装本体は exact 12、既存 8 path の順序保持、domain `/v1`、scope exact 文字列を満たしている。  
部分一致・`>=`・skip・xfail・テスト削除はなく、scope assertion は完全一致へ強化されている。  
`orchestrator/verifier/**` は両端で同一 blob であり、変更は 0 byte、worktree も clean だった。  
`identity_preimage`、wire key、`E1:` prefix、hash 式に変更ハンクはない。未閉鎖経路の過大主張も見当たらない。  
ただし中心となる M1〜M4 の検出証拠が fixture エラーで偽緑化できるため、fixture 独立化と変異再走までは land 不可。pytest は未実走であり、緑には数えていない。