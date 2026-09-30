## 所見

1. **must-fix — template test が repo 外のファイルに依存する。** [test_silo_lock_order_template.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:24) は `/work/1/SFC/tanab/dev-wave-jobs/.../api-header-canonical.hh` を読み、85 行で一致を要求する。**影響:** land 後にそのファイルが無ければテストが失敗し、あっても成果物外の内容が合否を左右する。**対応:** repo 内の `silo_lock_order_api.hh` を比較元にする。

2. **must-fix — gate と実骨格 patch の結合が未検査。** [test_silo_lock_order_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_gate.py:25) は短い手製 source だけで `order_gate` を呼ぶ。一方、[template test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:143) は名前つき対照を手で再記述して hole に入れ、`order_gate` を通さない。**影響:** 実 patch の marker や hole が gate で拒否されても単体テストは緑になり、[T-2888] に渡す入口が成立しない。**対応:** 既存の module fixture の checkout で、実際の `version_desc.cpp` を `order_gate` に渡し、書込み後の hole と拒否時の不変性を検査する。実 Silo build・trace 判定・発火計数は単位 C に委ねてよい。

3. **should-fix — pin と件数の並走統合に弱い。** [template test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:22) は `68106660` を直書きし、40 行で submodule HEAD と比較する。md_12 の後継 commit や予定された pin 前進では、patch を更新してもテストが先に落ちる。また [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_condition_meaning_gate.py:3699) の 57→58、58→59 と文言の 75→76 は、他 wave の同じ加算を Git が一度に畳み得る。**影響:** main 取り込み後、実際の pin・macro 数と受領証の参照がずれる。**対応:** test の pin は軸の `PIN` に寄せ、統合時に patch 適用性と登録集合の実数を照合する。件数を機械的に再度 `+1` しない。

4. **nit — compile と template test に重複が残る。** [silo_lock_order_compile.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/campaign/silo_lock_order_compile.py:19) の一時 TU・compiler 呼出し・判定生成は既存 `silo_policy_compile.py` とほぼ同形で、[template test](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-lock-order-axis/orchestrator/tests/test_silo_lock_order_template.py:33) の clone と前処理も既存の関数方策 test に重なる。軸ごとの namespace と patch は異なるため、この wave で既存 file を広く共通化する利得は小さい。**影響:** 現時点で成果物の値・受理集合・参照が変わる証拠はない。**対応:** まず対照本文の手書き複製（134〜142 行）を削り、共有化は後続作業で判断する。

## 検査範囲と所要

差分上、patch は **267 行**で段 4 の 300 行上限内。文法の既存 file 変更は軸固有の表と参照先の切替に概ね限られ、既存 profile の回帰 corpus もある。ただし「既存 4 軸の受理集合不変」は、この静的レビューや実装子の自己申告だけでは実証できない。M1〜M6 の変異実走もこちらでは再確認していない。

新 template test は pytest では clone を module fixture で **1 回**に集約する。反面、4 通りの source identity 確認で複数回の前処理を行い、sort の C++ compile もある。**秒数と全体 5 分以内は実測が無く判定不能**。自走 `_run` があり、`test_plain_runner_coverage.py` の登録方式には合う。新しい production の subprocess 起動箇所は見当たらず、spawn inventory への追記は不要と判断する。

## 総括

**NO-GO。** 所見は **must-fix 2、should-fix 1、nit 1**。まず repo 外参照を除き、実 patch の hole に実際の名前つき対照を `order_gate` で挿入する test を足す。その後、単位 C の実 build・trace 判定を別の証拠として確認する。レビューではテストを実行していない。