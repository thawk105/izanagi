## 所見

1. **知見の `README.md` が一律に縮小受入から外れる。重大度: must-fix。**
   **根拠:** [tools/scoped_acceptance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/scoped_acceptance.py:108) は変更 path の basename `README.md` を鍵に含め、同 file の 221–225 行で production file の引用文字列と照合する。[tools/dev_waves/checker.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/dev_waves/checker.py:607) には、別用途の `"README.md"` がある。
   **再現入力:** tested main に対し `output/insights/2026-09-30/scoped-acceptance/README.md` だけを追加した tip。分類は `production-reference` で不適格となり、縮小受領証は発行できない。
   **放置時の影響:** 知見 wave の主要な成果物である `README.md` を含む tip は land の縮小受領証受理集合に入らず、全受入待ちが残る。
   **推奨:** plan v2 の basename 規則を親で再裁定し、無関係な汎用 basename 参照と、その path を実際に読む参照を区別する。実 repo の知見 `README.md` 正例と、実際の reader に当たる負例を追加する。

2. **縮小集合の固定 file は既に大きい。重大度: nit。**
   **根拠:** [tools/scoped_acceptance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/scoped_acceptance.py:18) の固定 8 file には、静的な `def test_` 数だけで計 1,030 関数がある。S1 の [conftest.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/conftest.py:262) は 148 node。parametrize 分を含めない概数であり、plan v2 の「148 node／139 秒」はこの実装全体の所要を示さない。
   **再現入力:** `docs/notes/story.md` だけの適格 tip でも固定集合を全選択する。受領証の `selection.files` に 8 file が入る。
   **放置時の影響:** land の受理集合は変わらないが、縮小受入の実行時間が見込みより長ければ短縮幅が小さくなる。
   **推奨:** 親の同時刻比較で pytest・直接 gate・queue を別々に測る。固定集合の削減は検出力の代替を示してから判断する。

3. **新テストの合成 repo 構築が受入全走へ継続的に加算される。重大度: nit。**
   **根拠:** [test_scoped_acceptance.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/test_scoped_acceptance.py:23) は関数 scope の fixture で git repo と基底 commit を作り、[test_scoped_acceptance_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/test_scoped_acceptance_land.py:120) も各ケースで合成 worktree を作る。実装子報告では計 50 ケース。
   **再現入力:** この commit を含む tip の通常の全受入。新ケースごとに repo 構築が走る。
   **放置時の影響:** main に入る変更は変わらないが、今後の全受入所要が増える。
   **推奨:** 親の所要測定で寄与を確認し、必要なら独立性を保ったまま基底 repo の作成を共有する。テスト削除は D747 に従い採らない。

## 変異の実効性

`tools/` の land 側拒否は分類器から独立した MS6 の防壁なので残すべきである。[tools/dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/dev_wave_land.py:1231) の照合を削ると、分類器の誤許可時に実装面 tip の縮小受領証を拒否する独立根拠がなくなる。`run_tests.py` の変更も、選択走へ恒久除外と受入形の規則を適用するために必要である。

直接 gate 2 本と対応する test file は実行面が異なるため、単純な重複とは判定できない。queue 待ちは残り、短縮対象は主に pytest の走行量である。現在の `README.md` 判定は、その効果を知見 wave の典型的な tip に届かなくしている。

## 総括

**must-fix は `README.md` の過剰除外 1 件。** plan v2 の規則自体に由来するため、親で規則を再裁定してから修正する必要がある。静的レビューのみ実施し、テスト・実走・所要測定は行っていない。