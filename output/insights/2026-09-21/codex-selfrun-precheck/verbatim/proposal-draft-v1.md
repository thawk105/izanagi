# 裁定パッケージの案 (草案 v1、段 3 の攻撃対象。採否は段 4 と、最終的にはユーザー)

前提: 本 wave は docs も実装も変えない。案 A を採っても、実装は「親が author / fix prompt に書く運用」であり、`docs/dev-wave/workers.md` `DW-S05-C` への収容は予算 (L1.5 満杯、記憶 codex-child-discipline の 2026-09-03 追記) の裁定が別に要る。

## 案 A (親の推奨): 「返す前に、自分が新設・変更した test file だけを自走 harness で 1 回走らせる」を author / fix prompt に足す

prompt に足す文 (草案):

> 返す前に、自分が新設・変更した test file **だけ**を `cd <repo root> && PYTHONPATH=. python3 orchestrator/tests/<file>.py` で 1 回走らせ、rc・passed / failed / skipped の件数・失敗 nodeid を報告に書く。`__main__` を持たない pytest 専用 allowlist file は走らせず「自走不可 (allowlist)」と書く。`python3 -m pytest` / `pytest` / `python3 -c "…pytest.main(…)"` / `tools/run_tests.py` は使わない (前 2 つは hook が拒否する。後 2 つは使わない)。赤が自分の差分に帰属するなら直してから返す (test を甘くしない、F27)。sandbox 起因の赤 (socket の `PermissionError`、`/run/user` 不可、git rc=128) は「sandbox 起因・未検証」と分類して報告し、test も production も変えない。**この自走は計測でも受入でもなく、親の焦点走 (計算ノード) と受入全走を代替しない。** 走らなかった test は「未実走」と書き、緑と書かない。

根拠: (1) hook 判定 rc=0 (静的)、(2) D2195 が親に許した観測法と同じ形、(3) 1 file の対照走は 1.5〜3.4 秒・35〜57 MB (login の天井 14 GiB に対し無視できる)、(4) `test_plain_runner_coverage.py` が自走 harness を全 test file に義務付けているので「新設 test file は自走できる」が契約上保証される (allowlist を除く)、(5) 記憶 (2026-09-05 に fix 子 5 本が実走) と本 probe。
期待効果: 子の新設 test 自身の fixture 誤り (F76 型、T-1851 で 2 度) と assert / literal の綴り誤りを、親の dispatch (queue 待ち込みで T-2796 の焦点走 attempt 2 = 7 分、D2195 の変異 probe 平均 20.7 分・最大 26.4 分) の前に子が直す。**減るのは往復 1 巡であって、焦点走 (DW-O26 の consumer + inventory) と受入全走は残る。** T-2810 の焦点走 1 の赤 (既存 consumer test) や T-2797 の受入赤 (inventory test) は self-run では出ない型。

## 案 B: 何も足さない (現状維持: 子は「実装済み・未実走」、親が dispatch)

根拠: self-run は admission (メモリ上限 scope) を通らない login 実行で、子に許す形を増やすと「login で走らせてよい量」の境界 (DW-M08 の「login 実行が許される file」) を暗黙に広げる。往復は 1 巡 7〜26 分で、wave 全体 (平均 154 分、記憶 dev-wave-wall-decomposition-facts) の 5〜17%。

## 案 C: T-2810 / T-2814 の形 (`python3 -c "…pytest.main([…])"`) を許す — 親の推奨は不採用

根拠 (不採用): guard の射程外 (D103 決定 5) で通るが、F121 が「pytest 拒否の迂回」として閉じた `-m pytest.__main__` と同族の綴り替えであり、依頼の「hooks の拒否を迂回しない」に反する。T-2814 では `test_check_docs.py` 全件 580 件 / 302 秒を admission 無しで login に載せた。T-2810 では既存回帰の全件走を sandbox で試みて socket `PermissionError` で「検査本体を通せていない」。allowlist file を子に走らせたい需要は親の dispatch で満たす。

## 案 D: `tools/run_tests.py` を sandbox 内で使えるようにする (admission 台帳の代替 path、socket 不要の判定)

根拠 (scope 外、記録のみ): 実装面・gate (admission) の変更で、依頼が「gate・台帳・一般化の追加は scope 外」と明記。裁定パッケージに「将来の択」として書くに留める。
