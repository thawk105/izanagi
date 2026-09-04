## 総括

- 所見 / 16:40 JST 時点で `t2228-20260904a` の rr5・rr50 双方に campaign WAL の `build_start` がある。helper は全 2 cell の arm 評価、family 判定、receipt 追加を終えてからしか yield しないため、A-2 の cell-1 以降は実体として発火済みであり、condition gate の追加層 4 は出ていない。
- 根拠 file:line / `orchestrator/campaign/paper_story_a2_certification.py:613-697,3111-3127`、`.../t2228-20260904a/jobs/rr5/campaigns/.../runs/wal.jsonl:1`、`.../jobs/rr50/campaigns/.../runs/wal.jsonl:1`
- 成果物への影響 1 行 / production 修正条件は成立しておらず、現時点で gate や driver を変えると受理集合を不必要に変える。
- real か nit か / real

- 所見 / 計画はそのまま author へ渡せない。正例と負例を「独立テスト」とする記述が D1522 の「同じテストに正例対照」と衝突し、production 相当 genome なら evaluator 回数も各 2 回ではなく各 4 回になる。
- 根拠 file:line / `s2-plan.md:60,68-70,76-90`、`verbatim-rulings.md:28-47`、`paper_story_a2_certification.py:564-569,613-668`
- 成果物への影響 1 行 / 修正しないと、別要因による拒否でも負例が通る、または NOINLINE receipt の退行を見ないまま certified な受理集合を支えるテストになる。
- real か nit か / real

- 所見 / pytest は実行しておらず、以下はコード、既存 duration ledger、進行中 attempt の durable artifact による静的検査である。
- 根拠 file:line / `brief.md:81`、`s2-plan.md:9`
- 成果物への影響 1 行 / 未実測の unit test を緑とは扱わず、親の実測結果だけを受入記録へ載せる必要がある。
- real か nit か / real

## 実走から何が言えるか

- 所見 / 完走後は各 workload の `jobs/{rr5,rr50}/scheduler/job.stdout` 最終 JSON 行を読む。`condition_gate_receipts[0]` が stock、`[1]` が adopted で、各要素の `supply_records`、`meaning_records`、`admission` が canonical な一次証拠である。現在 stdout はまだ materialize されていないため、個別 reason code は予測値を実測値として書けない。
- 根拠 file:line / `paper_story_a2_certification.v2.json:81-117`、`paper_story_a2_certification.py:686-697,3071-3082,3140-3142,4208-4215`、`tools/pegasus/submit_paper_story_a2_certification.sh:258-263`
- 成果物への影響 1 行 / stdout 完成前に予測 reason を転記すると、材料レポートと試行台帳が存在しない receipt を参照する。
- real か nit か / real

- 所見 / 現在ある両 WAL の 1 行目は campaign 到達の強い証拠だが、行内の `build_admission` は condition gate admission ではない。condition admission の payload は stdout の `condition_gate_receipts` だけに出る。
- 根拠 file:line / `.../t2228-20260904a/jobs/rr5/campaigns/.../runs/wal.jsonl:1`、`.../jobs/rr50/campaigns/.../runs/wal.jsonl:1`、`paper_story_a2_certification.py:686-695,4212-4214`
- 成果物への影響 1 行 / WAL の build admission を condition admission と誤認すると、材料レポートが異なる関門の receipt を根拠に certified と主張する。
- real か nit か / real

- 所見 / campaign が admission 後に例外終了した場合、`job.stdout` に残り得るのは `[campaign] ...`、`evaluate ...`、失敗 log という到達の間接証拠であり、`job.stderr` は未処理例外の traceback だけである。最初の campaign log より前に失敗すれば、明示的な admission 証拠はどちらにも残らない。
- 根拠 file:line / `paper_story_a2_certification.py:3013-3016,3111-3142`、`orchestrator/campaign/loop.py:410,529,613-614,652-653`、`tools/pegasus/paper_story_a2_certification.sh:303-310`
- 成果物への影響 1 行 / その場合、exact reason と admission receipt は欠落し、試行は driver failure として残せても condition admission の材料にはできない。
- real か nit か / real

- 所見 / この一般的な耐障害性の穴を埋める campaign 前台帳は本 wave では追加しない。今回の attempt は既に両 WAL へ到達しているため「発火した」の立証には実効性欠陥がない。ただし stdout receipt なしで exact reason まで主張してはならない。
- 根拠 file:line / `brief.md:31,46-54`、`s2-plan.md:44-49`
- 成果物への影響 1 行 / 新台帳を足せば scope 外の producer 形変更になり、足さずに exact reason を推測すれば材料レポートの参照が虚偽になる。
- real か nit か / real

## 2 層目以降の解釈

- 所見 / P4 は「以前の cell-0 rejection より後の制御位置」という意味なら正しい。ただし「admission が未実行」は不正確で、以前も cell-0 の family 判定は実行され `admitted=False` を返した。正確には「cell-1 の両 arm、cell-1 の family 判定、全 cell admitted 状態、receipt append、context yield、campaign」が未到達だった。
- 根拠 file:line / `brief.md:21-27,67`、`paper_story_a2_certification.py:655-697`、`verbatim-rulings.md:122-124`
- 成果物への影響 1 行 / 曖昧なままだと、既に実行済みの cell-0 family を新規到達層として二重計上し、試行台帳の層判定を誤る。
- real か nit か / real

- 所見 / 腕の順序を「層」と解釈すると元欠陥は成立しない。各 macro について supply の直後に meaning が無条件実行され、過去 stderr も cell-0 の NOINLINE meaning rejection を含む。拒否理由の層と解釈するなら、判定対象は cell 番号ではなく「T-2226 後に出た次の実 reason と最終 admission」になる。
- 根拠 file:line / `paper_story_a2_certification.py:616-673`、`brief.md:21-30`、`verbatim-rulings.md:97-100`
- 成果物への影響 1 行 / 腕順序だけを検査すると元の cell-1 未到達を守れず、理由層だけを見ると cell-1 receipt の欠落を見逃すため、unit は両 arm と 2 cell 到達の双方を固定すべきである。
- real か nit か / real

## 既存 pin と test 時間

- 所見 / 既存 helper を変更せず新しい test 関数を追加する限り、3 個の source pin への反証なし。いずれも production helper または `run_workload` の source を数えており、test 本体の追加では値が変わらない。
- 根拠 file:line / `orchestrator/tests/test_paper_story_a2_certification.py:62-90,3242-3258`、`s2-plan.md:92-97`
- 成果物への影響 1 行 / pin の期待値変更は不要で、変更すれば関門順序や checkout 単一性を弱める不要な差になる。
- real か nit か / 反証なし、real

- 所見 / 正負例は一つの test 関数へ統合し、同じ real green records を使って先に正例、その後に issued red record の負例を通すべきである。cell-0 request は driver と同じ `default_value=-1`、`stock_comparison=True` まで照合し、単に request digest が supply/meaning 間で一致するだけでは足りない。
- 根拠 file:line / `condition_meaning_gate.py:839-871,903-917,3913-3919`、`paper_story_a2_certification.py:618-629`、`verbatim-rulings.md:34-47`
- 成果物への影響 1 行 / request 全 field を照合しないと、別 request 用の real record を返しても family が受理し、誤った receipt binding を certified 選択へ持ち込める。
- real か nit か / real

- 所見 / `acceptance_duration_ledger.json` は本 wave では触らない。新 nodeid が未登録でも scheduler は duration を `None` として扱い、既存 ledger の schema/count pinは壊れない。追加後の全実測による別の台帳保守とは分離する。
- 根拠 file:line / `orchestrator/tests/acceptance_duration_ledger.json:1396,19523`、`orchestrator/tests/conftest.py:1527-1547`、`orchestrator/tests/test_update_acceptance_duration_ledger.py:306-325`
- 成果物への影響 1 行 / 今更新すると本題外の所要時間台帳差が増えるが、更新しなくても certified 値、材料レポート、試行台帳は変わらない。
- real か nit か / nit

- 所見 / 5から15秒という見積りは既存実測より過大である。同種の supply、meaning、family を含む test は 0.32から0.44秒で、BF=-1 と BF=10 の二組に driver stub 部分を加えて約0.8から1.3秒、production 相当の NOINLINE 二組まで含めても保守的に1から2秒程度である。
- 根拠 file:line / `acceptance_duration_ledger.json:639,668,675-677,682-683`、`test_condition_meaning_gate.py:1524-1618`
- 成果物への影響 1 行 / A-2 test file の現 ledger 合計約8.44秒へ最大約2秒を足す程度で、5分上限や成果物の受理集合には影響しない。
- real か nit か / nit

## 差し替え集合の過不足

- 所見 / leaf の種類には反証なし。必要なのは checkout、applied、TemporaryDirectory、Masstree prebuild、capture、supply evaluator、meaning evaluator の7種であり、計画の集合と一致する。`make_define_request`、declaration 構築、`require_condition_gate_family`、canonical serialization は実体のまま残す。
- 根拠 file:line / `paper_story_a2_certification.py:589-612,618-668,669-695`、`s2-plan.md:64-70`
- 成果物への影響 1 行 / この境界を守れば、実 family と receipt schema を検査しつつ login node で full CCBench build を起動しない。
- real か nit か / 反証なし、real

- 所見 / call count は入力依存である。BF だけの縮小 genome を2個渡すなら evaluator は各2回だが、production の `_genome_for_cell` は controlled base から NOINLINE を加えるため各4回になる。目的に最も整合する代案は production 相当の2 genomeを使い、macro順も含め各4回を固定することである。
- 根拠 file:line / `paper_story_a2_certification.v2.json:45-50,81-99`、`paper_story_a2_certification.py:561-569,613-668`、`s2-plan.md:65-70`
- 成果物への影響 1 行 / 各2回の縮小 test だけでは NOINLINE の unestablished receipt と admission carryを driver-levelで守れず、将来の受理集合や材料レポートが変わり得る。
- real か nit か / real

- 所見 / real records は monkeypatch 前に生成しなければならない。特に標準 `tempfile` module の属性差し替えは condition evaluator 側にも見えるため、先に差し替えると「real g++/cmake record」という前提が崩れる。
- 根拠 file:line / `s2-plan.md:64-68`、`paper_story_a2_certification.py:595-597`、`condition_meaning_gate.py:2673-2684`
- 成果物への影響 1 行 / 順序を誤ると実体 record ではなく stub 環境由来の record を receipt 正例として固定し、証拠参照を弱める。
- real か nit か / real

- 所見 / brief の「漏れればすべて require_heavy_work_site に拒否」は過大である。prebuild の差し替え漏れは full configure/build から確実に拒否されるが、評価関数の内部 CMake/compiler は独自 `_run_process` 経路で、同 gate を通らない。それでも evaluator は必ず差し替えるべきである。
- 根拠 file:line / `brief.md:36`、`buildcache.py:2009-2076,3469-3482`、`condition_meaning_gate.py:1474-1489,1563-1593`
- 成果物への影響 1 行 / failure mode の説明だけの差で成果物値は変わらないが、漏れを拒否頼みで見逃すと login node で意図しない CMake が動く。
- real か nit か / nit

## 他 driver と限界の書き方

- 所見 / 「他3 driver の stock 比較が同じ中央 inert evaluator を通る」という記述には反証なし。backoff_sweep が BF=-1 を stock comparison にして evaluator と family を呼び、backoff_repro はその helper を使い、s1 は同じ request/evaluator/family を直接使う。
- 根拠 file:line / `backoff_sweep.py:105-167,361-373`、`backoff_repro.py:63-84`、`s1_direct_comparison.py:194-210,266-304`
- 成果物への影響 1 行 / 中央分類器のコード修正は3 driverにも届くが、A-2 実走だけでは各 driver 固有の root binding、到達、admission を追認できない。
- real か nit か / 反証なし、real

- 所見 / 記録には「T-2228 は A-2 の isolated variant/stock roots と4 cellだけを実測した。他3 driver は同じ evaluator の静的 consumer だが、driver固有経路は未実測であり、それらの既存または将来成果物を追認しない」と明記すべきである。
- 根拠 file:line / `brief.md:42,54`、`verbatim-rulings.md:97-100,118-120`
- 成果物への影響 1 行 / この限定がないと、他 driver の certified 選択や材料レポートが未実測の T-2228 receipt を誤って参照する。
- real か nit か / real

## 親 brief の (P) と scope 外

- 所見 / P1 は賛成、反証なし。production 入口の実 attempt は actual CCBench、patch済み variant、campaign build の同一木をまとめて立証でき、専用 probe は同等の4-cell結果を出さない。4-cell rejectとの比較まで行う以上、full campaignにも目的がある。
- 根拠 file:line / `brief.md:46-47,64`、`paper_story_a2_certification.py:589-612,697,3111-3139`、両 workload の `wal.jsonl:1`
- 成果物への影響 1 行 / probeへ置換すると campaign結果と旧4-cell比較が欠け、材料レポートの主要参照を失う。
- real か nit か / 反証なし、real

- 所見 / P2 の核は賛成、反証なし。ただし適用案は D1522 に合わせ、real positive と issued-red negative を同じ test 関数に置き、各 phase の差し替え発火回数を別々に固定する。
- 根拠 file:line / `brief.md:48-51,65`、`condition_meaning_gate.py:963-988,3837-3882,3885-3947`、`verbatim-rulings.md:28-47`
- 成果物への影響 1 行 / この形なら SimpleNamespace 偽装や別要因の拒否を排除し、family の受理集合と receipt detail を直接守る。
- real か nit か / 反証なし、real

- 所見 / P3 は現在の実走結果に照らして不採用。両 campaign WAL が作られた時点で condition gate の追加層は出ていないため、production 修正はゼロに確定すべきである。後の campaign failure は condition gate 層4とは別件である。
- 根拠 file:line / `brief.md:58-60,66`、`paper_story_a2_certification.py:613-697,3111-3127`、両 workload の `wal.jsonl:1`
- 成果物への影響 1 行 / gate本体やdriverを今変更すると、実測で必要性が示されていない受理集合変更が新 attempt と certified 結果へ混入する。
- real か nit か / real

- 所見 / P4 は条件付き賛成。「cell-0 後の制御位置」と定義し、「admission」を「cell-1 family 判定と全 cell admitted 状態」に言い換える。腕順序または拒否理由層という別解釈も報告に併記する。
- 根拠 file:line / `brief.md:67`、`paper_story_a2_certification.py:613-697`、`verbatim-rulings.md:122-124`
- 成果物への影響 1 行 / 用語を直せば、unit assertion と試行台帳が実際の未到達位置を同じ意味で参照する。
- real か nit か / real

- 所見 / 禁止 scope に触れるのは、実走前に列挙した仮想的な classifier 修正と追加 gate test である。今回は層4が出なかったので `s2-plan.md:51-56,119-120` を author scope から削る。pre-campaign台帳、新 probe、他driver実測、一般 helper、duration ledgerも追加しない。必須のdriver正負例とその変異確認は明示命令そのものなので残す。
- 根拠 file:line / `brief.md:10-15,54,58-60`、`s2-plan.md:49,51-56,116-129,131-139`
- 成果物への影響 1 行 / 削除により certified 値と既存台帳を変えず、追加されるのは要求済みの unit 防壁と実走材料レポートだけになる。
- real か nit か / real

- 所見 / 親 brief の変更面アンカー `condition_meaning_gate.py:3707-3770` は誤りで、そこは meaning evidence validator である。実 `require_condition_gate_family` は `:3885-3947` にある。
- 根拠 file:line / `brief.md:89-91`、`condition_meaning_gate.py:3707-3770,3885-3947`
- 成果物への影響 1 行 / 放置すると材料レポートと review が admission規則ではない行を参照し、受理集合の根拠が不正確になる。
- real か nit か / real

## 4-cell reject の位置づけ

所見 / 新 attempt が admitted なら T-2022 reject は当時の事実として残し、現行結果は一致でも不一致でも別測定として併記する。層4なら旧 reject は残すが、現行の関門通過や正しさの根拠には使わない。  
根拠 file:line / `brief.md:20,58-60`、`verbatim-rulings.md:16-18`、`s2-plan.md:99-103`  
成果物への影響 1 行 / 旧 certification bytesを上書きせず、新 attempt の受理状態と参照を別 leafへ記録する。real か nit か / real