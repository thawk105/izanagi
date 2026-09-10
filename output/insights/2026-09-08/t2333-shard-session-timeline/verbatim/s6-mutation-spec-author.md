## 総括

[mutation-spec-t2333.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2333-author/mutation-spec-t2333.json) を作成しました。M1〜M11 をすべて収録し、他の repository file は変更していません。commit も作成していません。

## spec の schema をどう確かめたか

`tools/mutation_harness.py::_load_spec` と既存 spec を照合しました。

- schema: `izanagi-dev-wave-mutation-spec/v1`
- category: `negative` / `positive` / `both-layers`
- root と mutation、replacement の field 集合は loader の厳密一致に準拠
- loader による読込み成功
- 全変異後 source の `compile()` 成功
- M4〜M6 は変異後 source の module 実行による import 相当検査にも成功
- U+0300〜U+036F は不在

## 各変異の old が一意であることの根拠

harness 自身の `_mutated_sources` を全11変異へ適用し、累積置換時を含む全 replacement の anchor count が正確に `1` であることを確認しました。

## expected_nodes をどう導いたか

レビュー表を起点に、各対象実装とテスト assertion を照合しました。

M1〜M6、M8、M9、M11はレビュー表どおり各1 nodeです。M7は `_reports()` の全 report が schema mismatch になる波及を追跡し、赤になる14 nodeを登録しました。M10は直接の serial 集約テストに加え、同じ分岐を使う sessionfinish テストも赤になるため2 nodeを登録しました。

## 単一理由性が疑わしい変異

- M7: schema gate の一理由に収束しますが、共通 fixture の `session_timeline` が extra key となるため、意図した必須-keyテスト以外にも広く波及します。
- M10: config-local 分岐を除くことで、直接テストは不正な worker payload、sessionfinish は payload 欠測として赤になります。根は同じですが外向きの失敗形が2種類です。

## 書けなかったもの

なし。M1〜M11をすべて収録しました。

実走による probe は、`tools/run_tests.py` の Pegasus queue preflight が rc=16で停止したため未実施です。生成された receipt directory は repo 外の `/tmp` へ退避済みで、最終 `git status --short` は spec 1 fileだけです。