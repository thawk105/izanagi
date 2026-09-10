## 元の node が証明している命題

元の node は、同一の公開入力に対して秘密入力となる5 bit wire の全32値を昇順かつ逐次に実行し、実際の no-build rejection、WAL、campaign lock、certified-purpose admission、critic 再構築まで通したうえで、次を証明している。

- 各 wire は固有の fresh `run_root` を使い、planner、coder、auditor、critic の fixture が各1回だけ呼ばれる。`test_p3_autonomous_workload_trial.py:1845-1900`
- injected drive が常に `do_build=False` を受ける。`test_p3_autonomous_workload_trial.py:1866-1871`
- planner と coder の sink は32 wire 間で不変、auditor は宣言された `/working_diff` と `/diff_digest` だけが変化し、それを除けば不変である。`test_p3_autonomous_workload_trial.py:1942-1948`
- critic は宣言済み D selector を除けば関係同値であり、digest は文字列である。`test_p3_autonomous_workload_trial.py:1746-1793,1949`
- production が返した raw variant は各 wire の predicate から期待される variant と一致し、critic に渡す candidate label とは異なる。`test_p3_autonomous_workload_trial.py:1902-1912`
- campaign ごとに BUILD_START は1件だけで、その生の `build_attempt_id` は critic sink に混入しない。`test_p3_autonomous_workload_trial.py:1913-1923`
- trusted variant と、wire、predicate、diff、digest、token、variant、attempt ID、binding commitment は32値すべてで相異なる。`test_p3_autonomous_workload_trial.py:1924-1961`
- 途中の反復が例外または assert failure になれば、その逐次 loop は直ちに中断し、横断 assert へは到達しない。

## blocker

- 1. 実行順序の被覆は同値ではない。

  - (a) `executor.map` が保証するのは結果の取り出し順であり、`run_trial`、WAL、admission、provider invocation の実行順ではない。現行は wire 0 の全処理と per-iteration assert が終わってから wire 1 を開始するが、変更後は最大4 wire の副作用が交錯する。plan は collection 順を根拠に「従来順を維持」としており、実行順と結果順を混同している。
  - (b) 現行の逐次境界は `test_p3_autonomous_workload_trial.py:1845-1940`。並行化案は `stage2-plan.md:63-103`、順序維持の主張は同 `:116-118`、process cache の最終状態だけを論じる箇所は同 `:131`。plan 自身も「exact な現行構成だけが thread safe」と限定している。`stage2-plan.md:20`
  - (c) 現行 production では直ちに受理集合が変わる共有 race は見つからなかった。しかし変更後の node は、逐次呼出し間の process 状態汚染を決定的に検出する回帰試験ではなくなる。後続変異が逐次時だけ wire を planner、coder、critic payload や candidate label に混ぜる場合、実 campaign の report、critic 判断、最終的な certified 選択値が変わっても、新 node はその同じ実行面を検査しない。絶対規律2を文字どおり適用するなら、これは親が「入力と出力の関係だけを被覆対象とし、逐次履歴の被覆は対象外」と裁定しない限り採用不可である。

- 2. 新設される集約境界で、planner、coder、critic の32件収集が assert されない。

  - (a) exact な plan 骨格では、32 future を全消費し、全 role を無条件 append するため見かけの緑になる通常経路はない。worker 例外は `map` の反復時に再送出され、timeout、cancel、例外吸収もないので横断 assert へ進まない。一方、変更後は worker 内の「1 payload を得た」という検査と main thread の append が分離される。collector が planner、coder、critic の一部を落とす変異では、planner/coder は1件だけでも `len(set(...)) == 1`、critic も同値な1件だけで真になりうる。
  - (b) 現行は検査と append が同じ loop 内で直結している。`test_p3_autonomous_workload_trial.py:1898-1900`。plan は worker の検査 `stage2-plan.md:83-91` と main-thread append `:93-100` に分離する。横断検査は planner/coder の集合数だけを見る `test_p3_autonomous_workload_trial.py:1942-1943` と、任意の非空な同値部分集合でも真になる helper `:1792-1793,1949` である。
  - (c) collector が特定 wire の planner、coder、critic sink を落とすと、その wire だけに生じる秘密混入が検査対象から消える。実 report の role payload、critic digest、recommendation が変化しても node が緑になり、後続の選択値を誤って受理しうる。実装前に全 role について32件を明示保証するか、同等の exact-cardinality 構造へ直す必要がある。

`contract_loader_binding.py`、`artifact_admission.py` の間接迂回は見つからなかった。plan は既存と同じ `allow_unregistered_exploratory=True`、provider、preview、drive を渡し、monkeypatch、環境変更、`sys.modules` 操作、cache、admission 省略を導入していない。`test_p3_autonomous_workload_trial.py:1885-1897`。2回の admission も helper の `:213-216` と production の `p3_autonomous_workload_trial.py:3363-3366` に残る。

## should-fix

- 失敗 wire の診断を明示する。

  - (a) worker 例外は握り潰されないため被覆は失われないが、`executor.map` の呼出側には失敗した入力値が直接現れない。特に production 深部の例外では、通常の pytest 出力だけから wire を一意に読める保証がない。
  - (b) plan の集約は `stage2-plan.md:93-100`。現行でも `run_trial` 呼出しは `test_p3_autonomous_workload_trial.py:1885-1897` で、wire を例外文に付けてはいないため、これは既存より弱いという blocker ではない。
  - (c) artifact 値と受理集合は変わらないが、どの一時 campaign、WAL、admission が赤の原因か特定しにくくなり、段6の変異結果を誤帰属しやすい。

- 被覆等価性の説明を「結果順」と「実行順」に分ける。

  - (a) `map` は入力順に tuple を返すため、`sink_bytes[role][i]`、`trusted_variants[i]`、`secret_records[i]` の対応は保たれる。ただし現行横断 assert はすべて集合ベースで、そもそも index 対応には依存しない。
  - (b) planner、coder、auditor、trusted は `test_p3_autonomous_workload_trial.py:1942-1950`、critic は `:1792-1793,1949`、secret fields は `:1951-1961`。per-wire の対応検査は worker 内へ移す予定の現行 `:1902-1923`。
  - (c) 現行実装どおりなら artifact 値は対応したままだが、plan の現在の記述では、将来 sequence 比較を追加した場合にも production の実行順まで維持されるとの誤解を招く。

## 親 brief の誤り

- 横断 assert の範囲は `1941-1955` ではなく `1942-1961`。brief は `src_token` の後半、`variant`、`build_attempt_id`、`trigger_gate_binding_commitment` と実際の assert 行を範囲外にしている。`brief.md:15-20`、`test_p3_autonomous_workload_trial.py:1942-1961`
- per-iteration assert は5 source statement ではなく6。`assert do_build is False` が漏れている。`brief.md:21-22`、対象 file `:1870`
- `payload_bytes` の assert はsource上1行だが、4 role それぞれについて実行される。`test_p3_autonomous_workload_trial.py:1898-1900`
- critic 横断検査の内部にも `critic_digest` が文字列であることを要求する assert があり、brief の列挙にない。`test_p3_autonomous_workload_trial.py:1746-1750`
- planner/coder が「32回とも」存在することは `len(set(...)) == 1` 単独では証明されず、現行の逐次制御と無条件 append に依存する。`test_p3_autonomous_workload_trial.py:1845,1898-1900,1942-1943`
- `secret_records` のうち wire、predicate、working diff、diff digest、src token は production artifact から回収した値ではなく、test が wire から再計算した対照値である。production 出力に直接由来するのは variant、build attempt ID、binding commitment。`test_p3_autonomous_workload_trial.py:1902-1940`
- 暗黙の不変条件として、wire ごとの固有 fresh root、各 worker 固有の provider object、fixture の mutable list 非共有、coder response の wire 差替え前に sink payload を記録する順序がある。`test_p3_autonomous_workload_trial.py:295-304,348-361,1847-1850,1890`。`run_trial` 側の fresh-root 拒否は `p3_autonomous_workload_trial.py:4807-4812`。
- brief の待ち「96%」は `user + sys` を wall から引く計算では約91.5%。`brief.md:26-28`。plan はこの点を修正済みである。`stage2-plan.md:13`

## 変異候補の追補

plan の6候補だけでは不十分である。特に `do_build`、role 呼出回数、BUILD_START 件数、future 例外伝播、新しい collector を個別に攻撃していない。

| 追補変異 | 期待する検出 | 期待赤 node |
|---|---|---|
| 新 `run_wire` で wire 17 だけ例外を送出 | future 例外が吸収されず、横断 assert へ進まないこと | `orchestrator/tests/test_p3_autonomous_workload_trial.py::test_role_sink_bytes_vary_only_at_declared_declassifications` |
| `p3_autonomous_workload_trial.py:2360` で injected drive に `True` を渡す | `do_build is False` の liveness | 同上 |
| `_WireRecordingFixture.invoke` で1 role の `payload_bytes` を二重記録する | 各 role が各 wire でexact 1回であること | 同上 |
| `p3_s4_loop.py:734` の BUILD_START を二重記録する | BUILD_START exact 1件または admission の fail-closed | 同上 |
| `p3_s4_loop.py:727` の attempt ID を固定値にする | 32 campaign 間の生 attempt ID 非衝突 | 同上 |
| target drive の binding commitment を固定値にする | commitment 32種の assert が生きていること | 同上 |
| 新 collector で critic を先頭1件だけ append する | critic sink 32件収集 | blocker 2 を直した後は同上。現 plan のままでは緑になりうる |

最後の変異が現 plan の不足を直接示す。`range(31)` 変異は auditor、trusted variant、secret fields の32 distinct条件を赤にするが、planner、coder、critic の collection 完全性を独立には証明しない。

新たな恒真 assert は生じないが、secret fields のうち test 自身が wire から算出する5 field は元から入力生成に強く依存する。critic relation も1件の同値部分集合では自明に真になる。この性質を「production secret artifact の32件検査」と説明してはならない。

## scope 外の real 所見

- `_AUDITOR_D_POINTERS` は target file 内の test-local 定数で、exact 集合自体を pin する assert がない。`test_p3_autonomous_workload_trial.py:1719-1722,1945-1948`。production annotation は別 node が exact に検査するが、relation normalizer との一致は束縛されていない。`test_p3_autonomous_workload_trial.py:1616-1688`。本 wave で一般 gate を増設せず、両者を将来束縛するかの裁定パッケージ候補とする。
- `artifact_admission.py` の説明文字列が exact 62 path のままなのに、実 closure は63 pathである。`stage2-plan.md:12`。production file 変更禁止に従い、本 wave では触らず別裁定候補とする。
- free-threaded Python では replay capability の private `issued` dict に明示 lock がない。`artifact_admission.py:95-128`。現行 CPython 3.10.12 の対象では blocker にしないが、interpreter 移行時の再分類事項である。

## 総括

現 plan の exact な `executor.map` には、worker 例外の握り潰し、timeout 打切り、未submit future による見かけの緑はない。  
結果の集約順と各 tuple 内の wire 対応も維持され、production admission の迂回もない。  
ただし実行順は逐次から並行へ変わり、元 node の逐次履歴被覆とは同一でない。  
さらに新 collector は planner、coder、critic の32件収集を明示保証せず、critic 切詰め変異が緑になりうる。  
絶対規律2を維持するには、この2点を解消または裁定するまで実装案は不採用と判断する。  
pytest と性能測定は実行しておらず、緑は報告しない。