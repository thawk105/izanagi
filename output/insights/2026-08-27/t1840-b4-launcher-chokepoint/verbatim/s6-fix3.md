## 裁定 1

- [`p3_b4_launcher.py:196`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:196): `_new_context` を module 属性から削除し、context 生成を launcher closure 内へ移動。
- [`test_p3_b4_launcher.py:344`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_launcher.py:344): 旧 7 名の不在検査を、全 module 属性を列挙して実 context と context factory の戻り値を production validator へ投入する検査へ置換。

## 裁定 2

- [`p3_b4_launcher.py:250`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:250): 未知 seal、test seal、production evidence の拒否を分離し、M14 と M16 の重複拒否を解消。
- [`p3_b4_launcher.py:460`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:460): campaign id を専用束縛だけで検査し、後段全体一致は残りの field を検査。受理条件は同値。
- [`test_p3_b4_launcher.py:94`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_launcher.py:94): 有効な commit receipt を生成する共通 helper を追加。
- [`test_p3_b4_launcher.py:140`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_launcher.py:140): M11〜M16 の入力を単独帰属形へ変更。assertion は緩和していない。

## 裁定 3

- [`test_p3_b4_launcher.py:573`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_launcher.py:573): `is` による object identity 検査を削除。3 driver と `wal.py` の AST を走査し、識別語 literal の不在と `p3_b4_protocol` からの定数 import を検査。

## M11〜M16 の帰属

- M11: `test_p3_b4_launcher.py::test_m11_real_wal_commit_requires_launch_sidecar`
  - 生きた production context 内で sidecar だけを削除。有効 receipt もあるため、実在関門を外せば COMMIT まで進む。
- M12: `test_p3_b4_launcher.py::test_m12_real_wal_commit_rejects_sidecar_for_another_campaign`
  - sidecar の campaign id だけが不一致。context、他 field、receipt は有効で、後段全体一致は campaign id を重複検査しない。
- M13: `test_p3_b4_launcher.py::test_m13_real_wal_commit_rejects_sidecar_for_other_live_context`
  - sidecar の実在と campaign 束縛は正しい。別の実受理記録から得た生きた context と sidecar の一致だけが拒否し、receipt も有効。
- M14: `test_p3_b4_launcher.py::test_m14_real_production_pair_factory_requires_launch_context`
  - campaign、driver、arm、受理記録が一致する未知 seal context。未知 seal 関門だけが拒否する。
- M15: `test_p3_b4_launcher.py::test_m15_real_production_pair_factory_rejects_cross_driver_context`
  - 実 verifier 由来の production seal、同一 campaign id、arm、受理記録を使用。driver 種別だけが `sort` と `base` で異なる。
- M16: `test_p3_b4_launcher.py::test_m16_test_seal_cannot_be_promoted_by_evidence_class`
  - exact test seal に production 表示、正しい campaign、driver、arm、受理記録を付与。test seal 専用分岐を外すと一般分岐を通る。

6 件とも静的には単独帰属形へ作り直せた。

## 置き換えた検査が弱くないことの提示

- 裁定 1: 旧検査は固定された 7 名しか見なかった。新検査は `vars(B4L)` の全値を列挙し、直接値を validator へ投入するほか、全値を seal 候補として context を構築し、module 定義の context factory も実際に呼ぶ。単なる改名では回避できない。
- 裁定 3: intern に左右される `is` を廃止。別 module に同じ literal を複製する変異は AST の文字列定数検査で失敗し、定数 import を外す変異も独立に失敗する。

## 非保証の記述

[`p3_b4_launcher.py:41`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/campaign/p3_b4_launcher.py:41) の `_TRUST_NON_GUARANTEES` に、同一 process の closure 内省と module 属性書換えへの耐性を保証しないと明記した。closure 内省経路を閉じたとは扱っていない。検査の対象外であることも [`test_p3_b4_launcher.py:345`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1840-b4-launcher/orchestrator/tests/test_p3_b4_launcher.py:345) の docstring に記載した。

## 受理集合の変化

保証対象の受理集合差分は空集合。

- production seal の真理値表は変更前後で同じ。
- campaign id は専用検査、context 側検査の双方で exact 一致を維持。
- marker、protocol 値、campaign identity、WAL schema、receipt 一回消費には変更なし。
- module 属性からの任意 context constructor という素直な経路だけを除去。closure 内省を含む経路は非保証のまま。

## 実走した検査

pytest nodeid は実走できていない。

- launcher 単体: runner が `qstat -Q preflight rc=1`、`rc=16`、`child_started=false`。
- 指定された 6 ファイルの全コマンド: 同じく `rc=16`、`child_started=false`。
- AST 構文解析、import smoke、識別語 AST 検査、`git diff --check`: 成功。これらは pytest の緑とは数えていない。

## 総括

must-fix 3 件を、許可された 2 file のみで修正した。  
M11〜M16 は各対象関門だけへ静的に帰属する入力になった。  
内省耐性は保証せず、素直な module 属性経路だけを除去した。  
commit、add、merge、rebase、push は実行していない。