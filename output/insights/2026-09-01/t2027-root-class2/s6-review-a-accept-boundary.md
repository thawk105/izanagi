## 所見 (重い順)

1. [s8b_compiler_input.py:1053](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/campaign/s8b_compiler_input.py:1053)、[s8b_compiler_input.py:1203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/campaign/s8b_compiler_input.py:1203) — v3 で dependency root の解決が過剰必須化している。
   - 何が破れているか: manifest に `dependency-prefix` entry がなくても、または複数 prefix のうち有効な 1 根だけに対象 file が存在していても、root 列中の未作成・消失済み要素を `_strict_root()` が先に拒否する。既知 4 欠陥の「根解決の過剰必須化」と同型。
   - 根拠: `current_dependency_prefix_roots` は input tag を見る前に全要素が canonical directory として解決される。production では [buildcache.py:2410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/campaign/buildcache.py:2410) が実効 `CMAKE_PREFIX_PATH` 全要素を渡す。read-only probe でも、正しい snapshot-only v3 と不存在 prefix の組が `CompilerInputError: ... element is unavailable` で拒否された。
   - 影響: CMake が使用しなかった stale prefix が 1 要素あるだけで fresh collection、cache hit、receipt 発行が停止する。artifact 値は発行されず、v3 の受理集合が裁定より狭くなる。
   - 是正案: `None` の未提示拒否は維持しつつ、root directory の不存在を直ちに全体拒否にせず、各 entry に対する「file が存在する root」の照合で非 match として扱う。collector も外部 input の分類が必要になるまで root 解決を遅延させる。
   - scope 内。must-fix。

2. [test_buildcache_v2.py:3246](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/tests/test_buildcache_v2.py:3246) — 裁定 §4.5 で明示的に落とした shape B 由来 node が復活している。
   - 何が破れているか: `test_v3_dependency_prefix_hit_validation_failure_never_rebuilds` は、裁定が名前を挙げて不採用とした node そのもの。
   - 根拠: production に tree identity や `_dependency_prefix_cache_identity` は混入していないが、禁止された契約だけが test として追加されている。
   - 影響: 現在の artifact 値や受理集合は変えないが、scope 外の cache-hit 挙動を新契約として固定し、今後の是正可能性を裁定外に拘束する。
   - 是正案: この新規 node を除去する。既存テストの期待値変更は不要。
   - scope 内。must-fix。

3. [test_s8b_compiler_input.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/tests/test_s8b_compiler_input.py:753) — origin ambiguity 負例が単一理由になっていない。
   - 何が破れているか: `outer` と `inner` は重なるため [s8b_compiler_input.py:687](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/campaign/s8b_compiler_input.py:687) で先に拒否される。`match="overlap|ambiguous"` により、分類器の [s8b_compiler_input.py:1308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/campaign/s8b_compiler_input.py:1308) を削除しても緑のまま。
   - 影響: 現行受理集合は overlap gate が守るが、「filesystem fallback へ落ちない」分類分岐の検査証拠にはならない。
   - 是正案: この node を classifier 分岐の証拠として数えず、overlap node としてのみ扱う。期待値変更は提案しない。
   - scope 内。nit。

## 同意した箇所 (短く)

- manifest 自己申告で root が選ばれる箇所は、v3 shape 検査の [s8b_compiler_input.py:936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/campaign/s8b_compiler_input.py:936)、live validator の [s8b_compiler_input.py:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/campaign/s8b_compiler_input.py:1091)、portable 構造検証の [s8b_binary_admission.py:370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/campaign/s8b_binary_admission.py:370)。production collector は depfile の絶対 path から tag を導出し、buildcache と issuer は live validator を通る。別 root の同一 relative path・同一 bytes への再束縛は裁定 §3 が承認した弱さの範囲で、未承認の受理拡大は見つからなかった。
- `filesystem` tag の current dependency root 偽装拒否は [s8b_compiler_input.py:1130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2027-root-class2/orchestrator/campaign/s8b_compiler_input.py:1130) まで届いている。
- current root の 0 件、2 件、symlink、非 regular、bytes 差は拒否される。2 件条件は disjoint な 2 根に同じ relative file を置く入力で到達可能であり、恒真ではない。
- v3 の `None` は未提示として拒否され、dependency entry なしと空 tuple の組は受理される。
- `_V2_ROOTS` は不変。v1 分岐も不変で、v2 の `dependency-prefix` は shape 検査で拒否される。既存 v2 の 3 root の live 分岐も変更されていない。
- `_v2_identity()` の絶対 `dependency_prefix` 経路は不変。completion に新しい runtime root field はなく、durable receipt に絶対 root は入らない。既存の identity preimage 内絶対 prefix は D1220 に従って残っている。
- bridge test は `build_cells()` から実 issuer を通り、新規 file は自走 harness を持つ。動的 `test_*.py` 列挙にも含まれる。揮発絶対 path の期待値への焼込みはない。
- pytest は未実走。実施したのは上記 read-only validator probe のみ。

## 総括

production 経路で、裁定が許していない受理集合の拡大は見つからなかった。一方、dependency root の過剰必須化が既知欠陥を再発させ、裁定で削除された shape B node も復活している。したがって現状は受理不可で、上記 2 件が must-fix。