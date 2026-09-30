## 総括

**NO-GO。** 静的検査では、追加した K 別の「楽観的候補率」が、一次資料で登録した分母と異なります。S6-7 は未完了です。raw schema の接続などは修正されていますが、S6-1 の結合 test は実際の driver 出力と作図全体を検証していません。テストの通過件数は親の報告によるもので、この再レビューでは実走していません。

## 対応表

- **S6-1 — partial。** 作図器は最上位 schema 1 を受理し、各 run に schema 3 を要求する（`tools/plotting/plot_vhash_workload_space.py:109,157-158`）。結合 test は `main()` と表出力を通すが、設計を 1 点に差し替え、両作図関数を無処理にしている（`orchestrator/tests/test_plot_vhash_workload_space.py:238-262`）。fixture の `summary` も driver が実際に追加する項目を欠く（同`:68`、`orchestrator/campaign/vhash_cicada_vlife.py:585-589`）。
- **S6-2 — closed（裁定上）。** driver 内の旧 smoke 見積りは残るが、段 6 裁定は親の別 job による W 条件の実測と見積りを採用し、driver の変更を不要とした（`stage6/ruling-s6.md:5`）。その親の実施内容自体は本レビューの検証対象外。
- **S6-3 — closed。** abort 名は driver の定義を参照し、出力にも使う（作図器`:21-24,126-135,574-575`）。
- **S6-4 — closed。** H4 は通過率、停止を無限大とする lag 中央値、live 中央値の順で並ぶ（作図器`:327-345`、README`:143-145`）。
- **S6-5 — closed。** 定型の機構・用途文は候補から除去され、候補表の列にもない（作図器`:353-355,562-567`）。
- **S6-6 — closed。** MB2 test は 2 反復を `_validated_run()` から `evaluate()` へ渡し、状態を検査する（test`:103-119`）。無処理 helper も削除済み。
- **S6-7 — partial。** site 別、bytes、鎖長などの列と反復・平均列は追加された（作図器`:218-238,519-559`）。ただし K 別候補率の分母が登録定義と食い違う。指定された三つの不要部分は差分上、削除済み。
- **F-A2 — closed（静的確認）。** owner TU の pin は両箇所とも 44、header は 12（`orchestrator/campaign/condition_meaning_gate.py:594-595,640-642`、`orchestrator/tests/test_condition_meaning_gate.py:115-119`）。patch の `+#if IZANAGI_CICADA_VLIFE` も当該ファイルで 44・12 箇所と実読した。

## 新しい所見

1. **must-fix — K 別候補率の分母が違う。** 作図器は `candidate_k*_rate = candidate / read_update 全件` とする（`tools/plotting/plot_vhash_workload_space.py:228-232`）。README §1.3 が引く md_2 は「位置 ≥ K の update read のうち」の割合と定義し、driver の `candidate_rate` も `candidate / deep` である（`output/insights/2026-09-29/vhash-cicada-version-measure/README.md:73`、`orchestrator/campaign/vhash_cicada_vlife.py:379-390`）。H2 専用の `h2` は README §1.4 どおり全 update read 分母でよい（README`:129-130`）。**放置時の影響:** 全点表の K 別候補率を、登録した測定値として誤報告する。

2. **should — 欠測を含む「平均」が有効な 1 反復だけで作られる。** `numeric_keys` と平均は存在する数値だけを集める（作図器`:519-526`）。無効 run は `{"status": "判定不能"}` となる（同`:197-200`）。**放置時の影響:** 2 反復の平均に見える列が、実際には 1 走の値になる。

3. **should — 分母 0 が全点で続く列は表から消える。** `_ratio()` は分母 0 を `None` にし、列名は数値が一度でも現れた場合だけ収集する（作図器`:193-194,519-526,555-559`）。**放置時の影響:** 「測定したが定義不能」と「列を作っていない」を CSV 上で区別できない。