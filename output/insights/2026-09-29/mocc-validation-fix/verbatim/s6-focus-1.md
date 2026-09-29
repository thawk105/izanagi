## 対応表

| 項目 | 判定 | 根拠 |
|---|---|---|
| S6-1 | **closed（静的確認）** | 全 arm の `CCBENCH_TRACE` を `1`/`0` にし、build 後・benchmark 前に対象 TU の実 compile 命令から TRACE と計器 define を照合する。[moccfix_probe.py](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:419)、[同:608](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:608)、[同:620](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:620)。対象命令が 0 件でも例外で止まり、恒真ではない。[同:408](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:408)。提示された旧 smoke の T_X/N_X は実際に `True`/`False` で、新検査なら拒否される。[T_X](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/evidence/smoke/compile-commands-T_X.json:279)、[N_X](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/evidence/smoke/compile-commands-N_X.json:279)。fix 後の実 build は未確認。 |
| S6-2 | **partial** | 両 compiler の期待した失敗時だけ「意図した修理差分」とする点は修正された。ただし両方 rc=0 の枝は、裁定が「その他」として指定した「理由未確定」ではなく「D297 合格」と表示する。[run_judge.sh](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:130)、[同:135](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:135)、[S6 裁定](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/s6-ruling.md:8)。 |
| S6-3 | **closed** | F→X の全文 diff を保存し、変更 path 数と hunk 数を report に記録する。[run_judge.sh](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:75)、[同:133](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:133)。diff が修理 hunk だけかの内容照合は、保存された diff を読む必要がある。 |
| S6-4 | **closed** | F 対照は R0・verifier とも判定可能な走だけから集計し、無効走を arm 別の `F_invalid_runs` に分けた。[moccfix_probe.py](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:329)、[同:351](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:351)。X の成功式、2 job × 14 batch、6 arm と反復数は維持されている。[同:23](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:23)、[同:333](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:333)、[同:340](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:340)。 |
| S6-5 | **closed** | 削除されたのは未使用の `legacy_selftest()`。呼び出される `selftest()` の既存期待値は差分上維持され、2 ケースが追加された。[moccfix_probe.py](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:714)、[同:751](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:751)、[同:814](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/moccfix_probe.py:814)。 |

## 新たな所見

- **should — D297 の結果名に裁定外の「合格」枝。** 両 compiler が rc=0 なら `expected=false` で終了コード 1 を返す一方、report の `result_name` は「D297 合格」になる。[run_judge.sh](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:131)、[同:135](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:135)、[同:143](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/tools/run_judge.sh:143)。放置すると失敗扱いの実走を成果物の名前だけで合格と読める。期待した失敗以外の枝を裁定どおり「D297 不合格 (理由未確定)」にする。[S6 裁定](/work/1/SFC/tanab/tmp/mocc-validation-fix-2026-09-29/s6-ruling.md:8)。

ほかに、fix 差分から成立する新たな攻撃は見つからなかった。

## 総括

S6-2 の結果名だけ修正が残る。ほかの 4 項目は静的検査で対応を確認した。fix 後の build・benchmark・テストは、このレビューでは実行していない。