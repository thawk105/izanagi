# 段 A の試しの候補を 1 つに決め、骨格 API の仕様を固める — Q1〜Q8 の区分・選定・受理文法と骨格 API・小さいモデルの案・計算の見積り (gen-opt md_6、2026-09-29、計算なし)

- 依頼: `/work/1/SFC/tanab/tmp/gen-opt-2026-09-29/md_6.txt` と同じ directory の `common-2.txt` (repo の外。第 2 陣 md_5〜md_8 の 2 本目)。
- 種別: 設計だけ (docs-only)。実装・計算ノードの実行・プログラムの実行による測定は 1 つもしていない (§9)。
- 読んだ時点の main: `035fc11fa601547f5d68e54f5661c5daa70b93a5`。submodule `external/ccbench` の HEAD: `68106660686232781bca3be792a750d3e19d7a8a`。
- 入力にした一次資料 (いずれも main に着地済み):
  文献カード `output/insights/2026-09-29/gen-opt-literature-cards/` (以下「カード」)、
  正しさ関門の設計 `output/insights/2026-09-29/gen-opt-correctness-gate/README.md` (以下「関門」)、
  母集団型の探索の設計 `output/insights/2026-09-29/gen-opt-evolution-design/README.md` (以下「探索設計」)。
- 本文の「確かめた」は、コードと一次資料を読んで確かめた事実を指す。

---

## 0. 結論

| 問い | 結論 |
|---|---|
| 5 候補の区分 (関門 §5 の Q1〜Q8) | 上限つき施錠待ち・乱数つき指数 backoff・開始前の先送り・競合度順の施錠の 4 つは「そのまま足りる」。BCC は「意味の拡張が要る」(validation を置き換える Q6、版の識別子の形が決まらない Q3)。「記録の追加で足りる」に入る候補は無かった (§2) |
| 段 A の試しの 1 本 | **競合度順の施錠** (Cicada §3.5 の write set の競合度順の sort。カード `cicada-write-set-sort-by-contention`)。施錠の前に、write set の各 tuple の TID word を骨格が 1 回だけ読み、その写しから候補が各要素の優先度を返し、骨格が「優先度の降順 → storage → key」の全順序で並べてから施錠する (§3・§4) |
| 選んだ理由 | 区分が「そのまま足りる」、段階 F の LLM 方策 (待ち方) と重ならない、既存の sort 軸 (比較に使えるのは `storage_`・`key_`・`rcdptr_` だけ) の外にある、施錠順は正しさの入力でないことを sort 軸の先行実測 (32 点 + 再測 6 点がすべて certified) が支える、編集範囲が `cc/silo/transaction.cc` の `validationPhase` の sort 1 か所と TID word の読み 1 回で済む (§3.2) |
| 次点 | **開始前の先送り** (TsKD の TsDefer)。原典の性能根拠は 5 候補で最も強い (YCSB 高競合で throughput 平均 +111%、TsKD Fig. 5a) が、骨格を workload 側の driver (`include/ycsb.hh` の実行 loop。関門の D1・D2 の証人の置き場) に置く必要があり、worker 間の共有状態と予定 key 集合の観測と先送りの上限 (進行保証) を同時に開く。編集範囲が段 A の最初の 1 本には大きい (§3.3) |
| 効果の見込みの限界 | 原典の -12.7% (Cicada Table 2 の No-sort) は「競合度順の sort」と「sort しない」の比較で、Silo の既定 (key 順) との比較ではない。さらに izanagi の先行実測では、1M record・48 thread の動作点で key の並べ方を変えても差は揺れの床の内外で、再測で再現しない点もあった。**stock と差が出ず tie になる可能性は低くない** (§3.4)。段 A の主張 (正しく実装して workload 別に選べる) では、tie を正直に選ぶことも結果である |
| 受理文法と骨格 API | 候補は tool を持たない coder の提案文字列として受け、policy-C++ v1 の規則をそのまま使い、型・field・hook の表だけを新しい軸のものに差し替える。候補には pointer も handle も渡さず、骨格が読んだ TID word の値の写しだけを渡す。候補が返す決定は「この取引で並べ替えるか」(bool) と「各要素の優先度」(uint64) の 2 つだけ。tuple・集合・trace・counter の名前は許可リストに入れない (§4) |
| 小さいモデル | 仕組みの仕様を「Silo の commit 手順 + 任意の施錠順 + no-wait」とし、施錠順 (と同じ順の書き込み) を全順列の非決定的な選択にする。候補が並べ替えられるのは UPDATE だけの write set に限る (INSERT・DELETE を含む取引では骨格が順序を決める hook を呼ばず stock の sort に戻す) ので、優先度の関数によらず軸の全候補の振る舞いを 1 つのモデルで覆える。判定は依存グラフの閉路・書く時点の lock 被覆・abort 時の lock の解放漏れ。場面は関門 §4.3 の 3 層に、3 key の書き込み集合で全 6 順列を当てる場面を足す (§5) |
| 計算の見積り | 1 評価 = 候補と stock を同じ job で測る pair 1 本 = 0.206〜0.220 node 時間 (探索設計 §6.1 の実測)。名前つきの方策 1 本 × workload 3 点で 0.62〜0.66、LLM の候補 2 本を足した 3 本 × 3 点で 1.85〜1.98 node 時間。小さいモデルの 3 取引の層を計算ノードで流すと仮定付きの試算で約 1.6 node 時間が加わり、**どちらの構成でも合計が 2 node 時間以上になるのでユーザー確認が要る** (§6) |
| 前提条件 | 関門 §3.5・§7 のとおり、gen-opt の候補の評価は U1 (trace 拡張)・U1b (Silo の取引内の値の扱いの修正)・U2 (判定器) の後に始める。この軸にはさらに U3 (本書の仕様の実装)・U4 (小さいモデルの基盤)・U5 (driver 接続) と、この仕組みの小さいモデルの実行が要る。U1b の item [T-2885] は上流への還元判断がユーザー確認待ちで、採られなければ gen-opt の評価は始まらない (§7) |

---

## 1. 何を確かめ、何を確かめていないか

| 確かめたこと (コードと一次資料を読んで) | 確かめていないこと |
|---|---|
| カードの本枠 2 候補・別枠 3 候補 (と別枠 1 に並ぶ Ding の thread-aware reordering) の該当カード (`cards.json` の `mechanism`・`prerequisites`・`correctness`・`silo_prereq`・`function_space`・`verifier`・`stage_a_notes`) | 原典そのもの (本 wave は原典を読み直していない。カードの記述を入力にした) |
| CCBench の Silo で、write set の sort は `validationPhase` の `sort(write_set_.begin(), write_set_.end())` 1 か所で、比較は `WriteElement::operator<` (storage → key)。`searchWriteSet`・`searchReadSet` は線形探索で並び順に依存しない。`lockWriteSet` の衝突時の既定は `NO_WAIT_LOCKING_IN_VALIDATION=1` で即 abort (`cmake/Options.cmake` の既定 1、`NO_WAIT_OF_TICTOC` は 0) | 並び順を変えたときに性能や abort 率が実際にどう動くか (実行していない) |
| Tidword の配置 (`cc/silo/include/tuple.hh`): lock 1 bit・latest 1 bit・absent 1 bit・tid 29 bit・epoch 32 bit | TID word の新しさが Silo 上で競合度の近似として働くか |
| 段階 F の LLM 候補 (`output/insights/2026-09-27/t2865-silo-policy-stage-f/verbatim/e2e/coder-output-1.json`) は、連続 abort で待ち幅を倍々にして乱数で散らし commit で縮める待ちと、施錠衝突で 20 回まで小さく待つ施錠方策の組合せで、施錠順には触れていない。その justification は「取得順も揃っているため、待っても循環待ちは起きない」と key 順を前提にしている | — |
| 既存の sort 軸の hole (`patches/silo-sort-variant.patch`) は `validationPhase` の同じ sort の行を置き換え、比較に使える名前は `storage_`・`key_`・`rcdptr_` (D46 の列挙空間) | — |
| sort 軸の先行 sweep (`output/insights/2026-07-10_s6-sort-sweep-preliminary.md`、D46) の記載: 32 本走点 + 6 再測点がすべて certified、balanced は全点が揺れの床の内、write-heavy の最良は再測で再現したが分解すると各成分は床の内 | その sweep の数値の再計算 (記載を読んだだけ) |
| policy-C++ v1 の検査器の作り: `orchestrator/campaign/silo_policy_grammar.py` は型 (`_TYPES`)・列挙 (`_ENUMS`)・field (`_FIELDS`)・hook の署名の表で名前を解決する。`silo_policy_compile.py` は API header を include した単独の翻訳単位を compile する | 表を差し替えるだけで新しい軸に流用できるか (U3 の実装 wave が確かめる) |
| 計算の単価 (探索設計 §6.1 の実測の表) | 新しい軸の候補の 1 評価の所要 (測っていない。§6 は単価を当てた試算) |

読み手への注意: 本書は「文献に無い」「新しい」を一切主張しない。候補は文献にある最適化であり、「CCBench に無い」はカードが pin の source で照合した内部の不在である。

---

## 2. Q1〜Q8 による区分 (手順 1)

問いは関門 §5.2 の 8 つ、区分の条件は関門 §5.3 に従う (Q1・Q2・Q3・Q5・Q6・Q8 のどれかが「変える」または答えが決まらなければ「意味の拡張が要る」、「変える」が Q4・Q7 だけなら「記録の追加で足りる」、全部「変えない」なら「そのまま足りる」。迷ったら重い区分)。

答えは仕組みの仕様 (カードの記述) から親が決めた。関門 §5.2 のとおり、候補を実装したら auditor が実コードから独立に答え直し、食い違えば重い方を採る。

| # | 問い | 1. 上限つき施錠待ち | 2. 乱数つき指数 backoff | 3. 開始前の先送り (TsDefer、Ding) | 4. BCC | 5. 競合度順の施錠 |
|---|---|---|---|---|---|---|
| Q1 | 読みが返す版を最新の commit 済み以外に変えるか | 変えない | 変えない | 変えない | 変えない | 変えない |
| Q2 | 未 commit の値を他の取引が読めるか | 変えない (待つのは commit 時の施錠で、値を見せない) | 変えない | 変えない | 変えない | 変えない |
| Q3 | 版の識別子が「書き手の commit の刻印・key ごとに一意・版の順序と一致」でなくなるか | 変えない | 変えない | 変えない | **決まらない** (全取引に TID を振り、TID word に書き手の thread の識別を持たせる。TID word は 64 bit を使い切っているので配置を変えることになる。カード `bcc-global-tid-vector-clock`) | 変えない |
| Q4 | 読み書きを tuple と自分の buffer 以外から返すか | 変えない | 変えない | 変えない | 変えない | 変えない (TID word の読みは順序の決定だけに使い、取引に値を返さない) |
| Q5 | 範囲読み・insert・delete の意味を変えるか | 変えない | 変えない | 変えない | 変えない | 変えない |
| Q6 | Silo の lock・validation を置き換え、X / P の証拠面が安全の根拠を表さなくなるか | 変えない (施錠衝突への応答だけを変える。関門 §5.3 の「lock 衝突の応答」の例) | 変えない (abort の後の待ち) | 変えない (CC の前段で、Silo の施錠・validation はそのまま) | **変える** (read set が変わっても essential pattern が無ければ commit する validation に置き換える。カード `bcc-essential-pattern-validation`) | 変えない (施錠順だけを変える。全要素を施錠してから validation し、書く時点の lock 被覆を X 行が、並べ替えの前後で要素が保たれることを P 行が見る仕組みはそのまま) |
| Q7 | writePhase を通らない commit の経路を足すか | 変えない | 変えない | 変えない | 変えない (read-only の snapshot 取引の同期点 `bcc-readonly-snapshot-sync-point` は、カードが「前提が合わない」とした部品で、ここでは含めない) | 変えない |
| Q8 | 1 取引の中間の値を他の取引に見せうるか | 変えない | 変えない | 変えない | 変えない | 変えない |
| **区分** | | **そのまま足りる** | **そのまま足りる** | **そのまま足りる** (区分は判定の意味について。編集範囲の問題は §3.3) | **意味の拡張が要る** | **そのまま足りる** |

補足:

- **1 と 5 の組合せ。** Silo が施錠衝突で待っても deadlock しないのは、write set を key 順に揃えて施錠するからである (カード §6.2、段階 F の候補の justification も同じ前提)。5 で順序を key 順から外し、1 のように待つ方策と組むと、互いに相手の lock を待つ状態が起きうる。上限つきの待ちなら上限で abort して抜けるので安全性 (直列化可能性) は変わらないが、上限まで空転しうる (カード `cicada-write-set-sort-by-contention` の `silo_prereq`)。これは区分を変えない (進行保証は判定の外、関門 §4.6) が、§4.1 の骨格の条件に反映する。
- **3 の Ding (thread-aware reordering)。** 取引を batch に束ねて worker に配る共有の入口が要る (CCBench の YCSB は worker ごとに取引を生成し、abort すると同じ操作列を再試行する)。区分は TsDefer と同じ「そのまま足りる」だが、編集範囲は TsDefer より大きい。
- **4 の BCC の判定器側の条件。** カードの `verifier` は「依存辺を版順 (書き手の commit TID) から作り、commit 順を直列化順と見なさないこと」を条件に置く。今の判定器は版から依存グラフを作るので読める見込みはあるが、それは仕組みごとの論証であり、Q3・Q6 の答えだけで重い区分に入る (関門 §5.3「迷ったら重い区分へ」)。
- **「記録の追加で足りる」は 0 件。** Q4・Q7 を変える候補は 5 つの中に無かった。

---

## 3. 選定 (手順 2)

### 3.1 観点ごとの比較

| 観点 | 1. 上限つき施錠待ち | 2. 乱数つき指数 backoff | 3. 開始前の先送り | 4. BCC | 5. 競合度順の施錠 |
|---|---|---|---|---|---|
| 区分 | そのまま | そのまま | そのまま | **意味の拡張** → 段 A の最初の 1 本から外す | そのまま |
| 段階 F の LLM 方策との重なり | **重なる** (施錠衝突で 20 回まで小さく待つ方策を書いて certified) | **重なる** (連続 abort で倍々 + 乱数、commit で縮める) | 重ならない (取引の開始を扱う) | 重ならない | 重ならない (段階 F は待ち方だけ。既存の sort 軸の IR は TID word を見られない) |
| 今の検査器と D1〜D3 で見られるか | 見られる | 見られる | 見られる。ただし先送りで取引の実行順が入れ替わるので、D1 の `A` 行は実際に commit した取引の手順列から書く必要がある (骨格の条件) | 条件付き (前提 A8 の証拠面の設計が別に要る) | 見られる。並べ替えは骨格が行い、P 行の検査はそのまま効く |
| YCSB で効きそうな workload を作れるか | 作れる。ただし根拠は 2PL の値で、Silo では NoWait が元の Silo を上回ると CCBench §6.1 が書く (Fig. 10c) | 作れる (zipf 0.99・thread 数最大) | 作れる (zipf 0.7〜0.99・max_ope 大・rmw あり。実行前に key が分かる workload に限る) | 作れる (zipf 0.9 以上・rratio 50〜80%) | 作れる (Cicada の条件: 16 要求/取引・読み書き半々・zipf 0.99。max_ope・rratio・zipf・thread 数で書ける) |
| 編集範囲 (骨格の関数・候補が触れる状態) | v1 のまま (拡張なし) | v1 のまま | 大: workload 側の実行 loop に骨格 (全 protocol 共有の `include/ycsb.hh`)、worker ごとの実行中 key 集合という共有状態、予定 key 集合の観測、先送りの上限 | 大: validation・共有状態 (thread ごとの最新 TID の配列・他 thread の read set 履歴)・TID word の配置 | 小: `validationPhase` の sort 1 か所を骨格の並べ替えに置き換え、TID word を 1 要素につき 1 回読む。候補の状態は worker ごとの scalar だけ |
| 原典の性能根拠 | Abyss Fig. 5 (2PL) | STOv2 Fig. 4 (数値は本文に無い) | TsKD Fig. 5a (YCSB 高競合で平均 +111%) | BCC Fig. 9 (YCSB の 32 thread で OCC 比 1.99 倍) | Cicada Table 2 の No-sort (外すと -12.7%) |

### 3.2 選定: 競合度順の施錠

区分で 4 を外し、段階 F との重なりで 1・2 を外すと、3 と 5 が残る。どちらも「そのまま足りる」で重なりも無いので、編集範囲で決めた。5 は骨格の変更が `cc/silo/transaction.cc` の中の 1 か所で済み、関門 §3.1 の F3 (独立な証人を生成コードの到達範囲の外に置く) を崩さない。3 は骨格を D1・D2 の証人と同じ `include/ycsb.hh` に置くことになり、共有状態と進行保証の問題も同時に開く (§3.3)。

5 の正しさの見通しには、既存の実測がある。sort 軸の先行 sweep は、key の昇順・降順・辞書式の組合せ 12 点と順序を決めない退化点を含む 15 候補 + stock を balanced・write-heavy で走らせ、32 点と再測 6 点がすべて certified だった (D46、`output/insights/2026-07-10_s6-sort-sweep-preliminary.md`)。記載は「施錠順序は correctness の入力でない (D41 の読み替え) が全順序・逆順・順序不定の全域で実測裏付けされた」としている。競合度順は実行時の値で順序が変わる点が違うが、順序を決めるのは骨格で、sort の比較は並べ替えの間は変わらない値の上で行う (§4.3) ので、この実測と同じ種類の変更に収まる。

### 3.3 次点: 開始前の先送り (TsDefer)

次点に残す理由は、原典の効果の根拠が最も強く (YCSB の θ 0.7〜0.9 で DbCC の throughput 平均 +111%、retry 49.8% 減、TsKD Fig. 5a)、正しさは Silo が担う (カードの `correctness`: TsDefer は追加の CC 規則を持たない) ことである。段 A の 2 本目以降に開くときに要るもの:

- **骨格の置き場。** 先送りは「取引を始める前」の口なので、workload 側の実行 loop (`include/ycsb.hh` の `run`。今は `makeProcedure` で操作列を作り、abort したら同じ操作列を再試行する) に worker 局所の queue を持つ骨格が要る。そこは関門の D1・D2 が `A` 行と値の刻印を書く場所でもある。骨格は hole の外の固定コードにし、hole は `cc/silo/transaction.cc` 側に置いて決定 (先送りするか) だけを返させる必要がある。`include/ycsb.hh` は全 protocol が共有するので、骨格の呼び出しを Silo だけに限る仕組みも要る。
- **共有状態。** 他 worker の実行中の取引の key 集合を読む表 (TsDefer の lock-free probing、カード `tskd-tsdefer-lockfree-probing`)。候補には表を渡さず、骨格が数えた「重なりの数」だけを渡す形が F2 に合う。
- **予定 key 集合の観測。** 実行前に key が分かる workload (CCBench の YCSB は該当) に限るという限定が付く。
- **進行保証。** 先送りを無限に繰り返すと取引が始まらない。骨格が先送りの回数に上限を置く必要がある (判定器は進行保証を見ない)。
- **D1 の束縛。** 先送りで実行順が入れ替わっても、`A` 行は実際に commit した取引の手順列から書く。

### 3.4 選んだ候補の危うさ (効果の見込み)

- **原典の比較相手が違う。** Cicada Table 2 の -12.7% は、競合度順の sort を外したときの低下 (No-sort) である。Cicada は timestamp による優先で deadlock を起こさないので、比較相手は「並べない」であって「key 順に並べる」ではない。Silo の既定 (key 順の全 sort) との差を示した図表はカードに無い。
- **izanagi の先行実測では、施錠順の違いは小さかった。** sort 軸の sweep (1M record・48 thread・zipf 0.9・max_ope 10) で、key の並べ方を変えた差は balanced で全点が揺れの床 3% の内、write-heavy の最良 +3.55%・+4.12% は分解すると各成分が床の内だった (D46)。ただしこの sweep の順序は key の値だけで決まり、実行時の競合の情報を使っていない。競合度順が同じく小さい差に留まるかは分からない。
- **Cicada と Silo の違い。** Cicada は多版で、Table 2 の条件は 28 thread・skew 0.99・16 要求/取引である。Silo は単版の no-wait で、早く失敗させる効果 (競合の強い tuple を先に施錠して、他の lock を握る前に abort する) は、施錠の数が多い取引ほど出やすい見込みである (推論、未実測)。
- したがって、**段 A の試しの結果が「stock と tie」になる可能性は低くない。** 段 A の主張は「文献にあるが CCBench に無い最適化を、正しく実装して workload 別に選べる」であり、効かない workload で stock や tie を正直に選ぶことはその主張の一部である。効かないことが分かった場合も、「正しく入れられた (certified)」ことと「どの workload で効かなかったか」は記録に残る。

---

## 4. 受理文法と骨格 API の仕様 (手順 3、関門 §3.1・§7 の U3)

### 4.1 軸の形

| 項目 | 仕様 |
|---|---|
| 軸の名前 (仮) | `silo-lock-order-policy`。marker ID も同じにする (実装 wave が既存の命名に合わせて決めてよい) |
| 候補の受け取り方 | 関数方策の軸と同じ。coder は tool を持たず `{"proposal": {"axis", "implementation", "justification", "confidence"}}` だけを返す。driver が検疫・文法検査の後に hole へ書く (関門 §3.1 の F1)。Edit で file を直接書く `coder` role は使わない |
| hole | `cc/silo/transaction.cc` の file scope に置く 1 つの EVOLVE-BLOCK。中身は `namespace izanagi_silo_order` の本体だけ (関数方策の軸の `namespace izanagi_silo_policy` と同じ作り) |
| 骨格 | hole の外の固定コード。(a) API header、(b) worker ごとの `thread_local` 状態の保持と hook の呼び出し (noipa の wrapper)、(c) `validationPhase` の sort の置き換え。いずれも patch の固定部分で、検疫の `outside-region`・`frame-altered` が守る |
| build の切り替え | 新しいマクロ (仮に `SILO_ORDER_VARIANT`)。0 = stock (前処理後の bytes が元と一致する inert な形、D18/D23 の sentinel の約束)、1 = hole の候補を使う |
| 他の軸との関係 | `patches/silo-sort-variant.patch` と同じ sort の行を置き換えるので、両方を同時に当てない (patch の排他を軸の定義に書く)。関数方策の軸 (`SILO_POLICY_VARIANT`) とは技術的には併用できるが、段 A の試しでは 0 (stock の即 abort) に固定する (§2 の補足: key 順から外した順序と待つ方策を組むと空転しうるため、効果の帰属を 1 つにするため) |
| build の前提 | `SILO_ORDER_VARIANT=1` のとき `NO_WAIT_LOCKING_IN_VALIDATION=1` かつ `NO_WAIT_OF_TICTOC=0` を要求し、そうでなければ `#error` で build を止める。`NO_WAIT_OF_TICTOC=1` の経路は取得済みを全部外して上限なく取り直すので、key 順から外すと互いに譲り合って進まない状態を上限なしで繰り返しうる |

### 4.2 骨格 API (header の案)

```cpp
namespace izanagi_silo_order_api {
enum class AbortReason : uint32_t { unset, lock_conflict, update_absent, read_tid, read_locked, node_validation, insert_node, scan_node };
struct TxnContext   { uint32_t write_count; uint64_t rand; };
struct EntryContext { uint32_t epoch; uint32_t tid; bool locked; };
struct AbortContext { AbortReason reason; uint64_t rand; };
struct CommitContext { };
}
namespace izanagi_silo_order {
struct OrderState;
bool     order_enabled(OrderState&, const izanagi_silo_order_api::TxnContext&) noexcept;
uint64_t order_priority(OrderState&, const izanagi_silo_order_api::EntryContext&) noexcept;
void     order_after_abort(OrderState&, const izanagi_silo_order_api::AbortContext&) noexcept;
void     order_on_commit(OrderState&, const izanagi_silo_order_api::CommitContext&) noexcept;
}
```

| 要素 | 仕様 | 理由 |
|---|---|---|
| **handle** | **候補には渡さない。** 骨格は write set の要素を内部の添字で持ち、候補には 1 要素ずつ値の写し (`EntryContext`) を渡す。添字・pointer・key は渡さない | 関門 §3.1 の F2 は「pointer でなく不透明な取っ手と候補の一覧」を定めた。この候補は tuple の読み書きの経路を持たず、決定は順序だけなので、取っ手すら要らない。最小の API から始める (F2) |
| **骨格が持つ読みの関数** | 並べ替えの前に、骨格が write set の各要素の TID word を `loadAcquire` で **1 回だけ** 読み、`epoch`・`tid`・`lock` の値を写しに入れる。候補はこの関数を呼べない (骨格が呼んでから hook を呼ぶ) | 候補が読みを繰り返せると、並べ替えの間に値が変わり、比較が厳密弱順序でなくなる (`std::sort` の未定義動作。sort 軸の D42 の非 SWO の hang と同じ型)。読みの回数と時点を骨格に固定すれば、候補の書き方によらず比較は一定の値の上で行われる |
| **骨格が持つ書きの関数** | **無い。** 候補は tuple・write set・read set・trace・counter のどれにも書けない | この候補の決定は順序だけ |
| **観測** | 取引: `write_count` (write set の要素数)、`rand` (骨格の乱数)。要素: 読んだ時点の `epoch`・`tid` (TID word の版)、`locked` (読んだ時点で他者が lock を握っていたか)。abort: `reason` (関数方策の軸と同じ付け方)、`rand` | Cicada の近似 (最新版の wts が大きいほど競合が強い) を Silo の TID word で書けるようにする。`locked` は「いま握られている」という、より直接の競合の印。`write_count` は小さい write set で並べ替えを省く (Cicada が低競合で省く理由と同じ費用の判断) ために渡す |
| **候補が返す決定** | `order_enabled`: この取引で並べ替えを使うか (false なら骨格は stock の `sort(write_set_)` をそのまま行う)。`order_priority`: 要素ごとの優先度 (大きいほど先に施錠) | 決定だけを返す (F2)。優先度から全順序を作るのは骨格 |
| **状態** | `OrderState` は worker ごとに 1 つ (`thread_local`、骨格が保持し reset しない)。`order_after_abort`・`order_on_commit` で更新できる (Cicada の「直近の連続 commit で省く」適応を書くため) | 関数方策の軸の `PolicyState` と同じ扱い |
| **呼ぶ回数の上限** | `order_enabled` は validation 1 回につき 1 回、`order_priority` は `write_count` 回 (YCSB では `max_ope` 以下)。hook は loop を書けないので、1 回の所要は有界 | 取引の所要を候補が延ばせる量を抑える |

### 4.3 骨格の処理順 (validation の sort の置き換え)

```text
validationPhase の先頭 (P 行の pre-sort snapshot は今どおり hole の外で先に取る):
  if SILO_ORDER_VARIANT == 0:            sort(write_set_)               # stock と同じ
  else:
    if write_set_ に INSERT か DELETE の要素がある:
                                         sort(write_set_)               # stock と同じ。順序を決める 2 hook を呼ばない
    elif !order_enabled(state, TxnContext{write_set_.size(), 骨格の乱数}):
                                         sort(write_set_)               # stock と同じ
    else:
      for i in 0..n-1:                                                  # 骨格だけが読む
        w = loadAcquire(write_set_[i].rcdptr_->tidword_)                # 1 要素 1 回
        prio[i] = order_priority(state, EntryContext{w.epoch, w.tid, w.lock})
      並べ替え: 添字 i を (prio[i] の降順, storage_ の昇順, key_ の昇順) の全順序で sort し、その順に write_set_ を並べ直す
  (P 行の post-sort 検査は今どおり hole の外)
  lockWriteSet()                                                        # 今どおり (no-wait)
abort 時: order_after_abort(state, AbortContext{reason, 乱数})
commit 時 (writePhase の後): order_on_commit(state, CommitContext{})
```

- **候補が並べ替えるのは UPDATE だけの write set。** `lockWriteSet` は INSERT の要素を施錠せずに飛ばし、`writePhase` は INSERT・DELETE を別の分岐で書く。これらを含む取引では、順序を決める 2 つの hook (`order_enabled`・`order_priority`) を呼ばない。通知の 2 つの hook (`order_after_abort`・`order_on_commit`) は取引の種類によらず呼ぶ (状態の更新は後の取引の順序の決め方にだけ効き、その取引の施錠・書き込みの順は変えない)。こうして候補が変えうるのは「UPDATE の要素を施錠し、書き込む順」だけになり、§5 の小さいモデルの範囲と一致する。CCBench の YCSB の書きは `update` を通るので、YCSB ではこの制限で失うものは無い。
- **比較は構成上つねに厳密弱順序。** 比較の鍵は (uint64 の優先度, storage, key) の辞書式で、並べ替えの間は変わらない配列 `prio` から取る。write set の中で (storage, key) は重複しない (YCSB の書きが通る `TxExecutor::update` は、同じ key が既に write set にあれば新しい要素を足さずに戻る。`insert` も `searchWriteSet` で同じ key を拒む) ので、この順序は全順序になる。候補は比較関数を書かないので、sort 軸の SWO 検査器 (`sort_swo_oracle` ほか) に当たる仕組みはこの軸には要らない。
- **並べ替えは要素の集合を変えない。** 添字の並べ替えを骨格が行い、既存の P 行 (大きさと `rcdptr_` の多重集合の比較) がそのまま検査する。
- **TID word の読みは read set に載せない。** 値は順序の決定にしか使わず、取引に返らない (Q4 は「変えない」)。この読みは関門 §2.4 の 1 (集合に載らない読みが検証にも trace にも映らない) には当たらない。その懸念は「取引が値を読んで使う」読みについてであり、ここでは値も版も取引の結果に入らない。
- **発火の証拠。** 「並べ替えを使った取引の数」と「key 順と違う順で施錠した取引の数」を数える。性能 build には入れず (規律 1)、既存の `instr-*` patch と同じく計数専用の build で取る。検証の trace (`#if TRACE`) の書式は変えない (判定器の parse を触らないため)。発火が 0 の評価は、効果の有無の根拠に使わない (関門 §3.4 の発火の計数と同じ考え方)。

### 4.4 受理文法

**土台は policy-C++ v1 の規則をそのまま使う** (`orchestrator/campaign/silo_function_policy_coder_spec.md`: pointer・配列・loop・可変の static / thread 記憶域・例外・template・マクロ・前処理指令・`static_cast` 以外の cast・増減演算子・コンマ式・コメント・文字列・文字 literal・`__` を含む識別子・代替綴り・digraph を拒否。整数 literal は `u` / `ul` 付き。除算・剰余の右辺は 0 でない literal。shift 量は literal で幅未満。状態は 16 field 以下の scalar でそれぞれ literal の初期化。helper は先に定義したものだけを呼べ、再帰しない。単独の翻訳単位を C++17 `-Wall -Wextra -Werror -fsyntax-only` で compile)。

差し替えるのは名前の表だけ:

| 表 | 新しい軸の中身 |
|---|---|
| 型 | `uint32_t`・`uint64_t`・`bool`・`void`・`OrderState` |
| 列挙 | `AbortReason` の 8 値 (上の header) |
| field | `TxnContext {write_count: uint32_t, rand: uint64_t}`・`EntryContext {epoch: uint32_t, tid: uint32_t, locked: bool}`・`AbortContext {reason: AbortReason, rand: uint64_t}`・`CommitContext {}` |
| 定義を要求する hook (ちょうど 1 つずつ) | `order_enabled` (bool, TxnContext)・`order_priority` (uint64_t, EntryContext)・`order_after_abort` (void, AbortContext)・`order_on_commit` (void, CommitContext) |
| 呼べる外部関数 | `std::min`・`std::max` だけ |
| 状態 | `struct OrderState` をちょうど 1 つ |

**名前は許可リスト方式なので、表に無い名前はすべて拒否される。** 次は拒否されることを文法の test に正例として置く (関門 §3.1 の F4 と §3.4 の B8・B9 に、この軸の固有の名前を足したもの):

| 群 | 名前 |
|---|---|
| trace | `izanagi_trace` (と `stream`・`record_lock`・`clear_shadow`)、`TRACE` |
| counter・結果 | `result_`・`local_commit_counts_` |
| 集合・索引 | `read_set_`・`write_set_`・`node_map_`・`Masstrees`・workload の `pro_set_` |
| tuple と要素の中身 | `Tuple`・`TupleBody`・`WriteElement`・`ReadElement`・`rcdptr_`・`tidword_`・`Tidword`・`storage_`・`key_`・`body_` |
| 実行器と同期 | `TxExecutor`・`this`・`loadAcquire`・`storeRelease`・`compareExchange`・`std::atomic` |
| 並べ替え | `sort`・`std::sort` |
| 他の軸と骨格 | `izanagi_silo_policy`・`izanagi_silo_api` (関数方策の軸の namespace)・`izanagi_silo_skel` と、この軸の骨格の namespace |

**受理されるべき形の正例** (文法の test に置く。候補の書き方の指示ではなく、受理集合の境界を示す例):

```cpp
struct OrderState { uint32_t streak = 0u; };
bool order_enabled(OrderState& s, const izanagi_silo_order_api::TxnContext& c) noexcept {
  return c.write_count >= 2u && s.streak < 8u;
}
uint64_t order_priority(OrderState&, const izanagi_silo_order_api::EntryContext& e) noexcept {
  if (e.locked) { return 18446744073709551615ul; }
  return (static_cast<uint64_t>(e.epoch) << 29u) | static_cast<uint64_t>(e.tid);
}
void order_after_abort(OrderState& s, const izanagi_silo_order_api::AbortContext&) noexcept { s.streak = 0u; }
void order_on_commit(OrderState& s, const izanagi_silo_order_api::CommitContext&) noexcept { s.streak = std::min(s.streak + 1u, 64u); }
```

その他の検査:

- **既存の 3 つの policy 系の受理集合を変えない** (関門 §7 の U3 の test)。関数方策の軸の文法の表と、この軸の表を別の定数にし、v1 の既存 test をそのまま通す。
- **UB の検査。** 関数方策の軸の `run_ubsan_harness` と同じく、hook を代表の入力で UBSan 付きで呼ぶ。`order_priority` には `epoch`・`tid` の端の値 (0 と最大) を入れる。
- **効果の字句検査** (`coder_effect_gate.DENY_TABLE`) はそのまま通す (この軸でも文法が先に閉じる)。
- **auditor の型。** 関門 §6 の追加候補の型 27〜30 のうち、この軸で意味があるのは型 30 (仕様の規則とコードの対応の欠落) と、「優先度の計算が乱数だけに依存し、観測を使っていない」ような仕様とコードの食い違いである。型 27・28・29 (骨格の読み書き関数の迂回・値の食い違い・counter への到達) は、この軸では文法が名前を持たせないので構造上起こらない。

### 4.5 名前つきの対照 (lookup 対照)

探索設計 §4.3 の「カードの仕組みを手でそのまま書いた方策を同じ関門で評価する対照」として、Cicada の近似をそのまま書いた方策を 1 本置く: `order_enabled` は常に true、`order_priority` は `(epoch << 29) | tid` (版が新しいほど先に施錠)。Cicada の「直近の連続 commit で省く」(§3.5) と「先頭 k = 8 だけの部分 sort」はこの対照に入れない (前者は閾値が原典の本文に無く、後者は sort の費用の削減で順序の意味を変えない)。置き場は既存の手書き方策の置き場 (`orchestrator/campaign/silo_function_policy_hand/`) に倣い、実装 wave が決める。

---

## 5. 小さいモデルの案 (手順 4、関門 §4)

### 5.1 何をモデル化するか

仕組みの仕様を「**Silo の commit 手順 + 任意の施錠順 + no-wait の施錠**」とする。

| 要素 | モデルでの形 |
|---|---|
| 共有状態 | key ごとに TID word (lock bit と版番号。版番号は key ごとに単調増加) と値 (書き手の取引 ID と版) |
| 取引の局所状態 | 手順列 (読み・書きの並び)、read set (key と読んだ版)、write set (key と書く値)、施錠済みの集合、段階 |
| 読み (`read_internal` に合わせる) | TID word を読む (lock なら、外れるまでこの step は進めない) → 値を読む → TID word を読み直す → 一致すれば read set に登録、不一致なら最初から。自分の write set・read set にある key は local から返す |
| commit | (1) **施錠順を write set の全順列から非決定的に選ぶ** (2) 選んだ順に 1 key ずつ CAS で施錠。lock 済みなら取得済みの前半を外して abort (3) read set の各 key の TID word を読み、版が変わったか、自分以外が lock を握っていれば、全 lock を外して abort (4) commit の版を決め (読んだ版と書く key の現版の最大 + 1)、(1) で選んだ順に key ごとに値と TID word を書いて lock を外す (`writePhase` は並べ替え後の write set の順に書くので、書き込みの順も同じ順列になる) |
| 対象の操作 | 点の読みと UPDATE の書きだけ。INSERT・DELETE を含む取引は骨格が stock の key 順に戻す (§4.3) ので、候補の振る舞いとしてはモデル化しない。stock の key 順の INSERT・DELETE は範囲外 (§8) |
| 原子 step | 1 回の load・store・CAS を 1 step にする (関門 §4.2 の 3。実装の共有メモリ操作より粗くしない)。メモリは逐次一貫 |
| 選択肢 O1 | 施錠衝突で N 回 (N = 1〜2) まで待ってから abort する (関数方策の軸と組むときの形) |

**施錠順を全順列の非決定的な選択にする理由。** この軸の候補どうしの違いは優先度の関数だけで、優先度が変えるのは UPDATE だけの write set の施錠と書き込みの順だけである (INSERT・DELETE を含む取引では順序を決める hook は呼ばれない、§4.3)。全順列を探索に含めれば、TID word の写しに何が入っていても、どの候補の順序も探索の中に現れる。したがって**モデルは仕様の単位で 1 つ作れば、点の読みと UPDATE だけの取引について軸の全候補を覆う** (関門 §4.2 の 1 の「値だけが違う候補は検査済みの値域に入るときだけ結果を共有する」は、ここでは値域を「全順列」と取ることで満たす)。stock の key 順も全順列の 1 つなので、stock の Silo もこのモデルで同時に検査される。

### 5.2 判定

| # | 判定 | 中身 |
|---|---|---|
| J1 | 依存グラフの閉路 | commit した取引の wr・ww・rw の辺で閉路を探す。orchestrator/verifier を import しない独立の判定器 (関門 §4.2 の 4) |
| J2 | 書く時点の lock 被覆 | 値を書く各 key を、書く取引が lock している (実装の X 行に当たる) |
| J3 | lock の解放漏れ | 取引が abort・commit で終わった時点で、その取引の lock が残っていない |
| 不変条件 | 版の一意性 | 同じ key の同じ版を 2 つの取引が書かない。破れたらモデルの欠陥として探索を止める (判定の違反と混ぜない) |
| 別記 | 全員待ちの状態 | O1 で、全ての生きた取引が lock を待っている状態に到達したか。進行保証は判定しない (関門 §4.6) ので、失格の根拠にせず数えて報告する (§2 の補足の空転の見積りに使う) |

### 5.3 場面の範囲 (結果を見る前に登録する)

関門 §4.3 の 3 層に従い、L2 にこの仕様の規則ごとの窓を置く。登録は実装 wave の一次資料で、実行の前に行う。

| 層 | 場面 | 窓を通った証拠 (witness) |
|---|---|---|
| L1 | 2 key の write skew、lost update、3 取引の read-only 異常、abort した取引の版を読む (G1a)、取引内の中間の値を読む (G1b) | 関門 §4.3 と同じ |
| L2-1 施錠順 | 2 取引がともに {A, B} を書き、施錠順が逆 | 双方が 1 つずつ lock を握った状態に到達する |
| L2-2 no-wait の前半解放 | 2 つ目以降の施錠で衝突して abort する | 1 つ以上の lock を握ったまま衝突した状態に到達する |
| L2-3 validation の lock 検査 | 読み手の validation の時点で、読み手の read set の key を書き手が lock している | その状態で読み手が validation の step を実行する |
| L2-4 版の検査 | 読んでから validation までの間に、読んだ key の版が変わる | その状態で読み手が validation の step を実行する |
| L2-5 3 要素の順列 | 2 取引がともに {A, B, C} を書く (各取引 6 順列、組で 36 通り) | 36 通りのそれぞれで、両取引がその順列を選んで施錠を始めた状態に到達する。加えて、先頭の key が違う 24 組では双方が 1 つ以上の lock を握ったまま相手の lock に衝突する状態に到達する (先頭の key が同じ 12 組は、no-wait の下では後から来た取引が最初の施錠で衝突して何も握らずに abort するので、この重なりは到達不能。そちらは「最初の施錠での衝突」を witness にする) |
| L3 | 2 key・取引 2 個・1 取引の操作 1〜2 個・key ごとの初期版 1〜2 個の全組合せ (1,600 構成)。加えて取引 3 個の層 (32,000 構成) | 関門 §4.3 と同じ (全列挙なので場面ごとの witness は要らない) |

**検査器の強さ (関門 §4.2 の 6):** 規則を 1 つだけ崩した危ない版を作り、どれかの場面で反例が出ることを確かめる。

| 危ない版 | 崩す規則 | 出るはずの判定 |
|---|---|---|
| a | 並べ替えで要素を 1 つ落とし、その key を施錠せずに書く | J2 (と J1) |
| b | 施錠衝突の abort で、取得済みの前半を外さない | J3 |
| c | validation で「自分以外が lock を握っている」検査を省く | J1 |
| d | 全要素の施錠が終わる前に validation を始める | J1 |
| e | 値を書いてから validation する | J1 (か G1a の形) |
| f (O1 の対照) | 施錠衝突で上限なく待つ + 任意の施錠順 | 全員待ちの状態に到達する (別記。J1〜J3 の違反ではない) |

反例が出ない危ない版は、別の規則が遮っていることを実行で示すか、等価として理由を書く (vhash §5.3 と同じ)。

**実装との対応 (関門 §4.5):** 実装側では、名前から対応しそうな既存の壊し patch — `patches/broken-silo-permutation-erase.patch` (a に近い)、`patches/broken-silo-lockskip-validation.patch` (c に近い)、`patches/broken-silo-early-unlock-validation.patch` — が trace の判定器で赤になるかを、この軸の骨格を当てた build で確かめる。patch の中身と危ない版の対応は本 wave では確かめていない (名前からの見込み)。

### 5.4 規模 (仮定付きの試算)

- 全順列の選択で状態が増えるのは、2 つ以上の key を書く取引だけである。L3 の 2 key の層では、1 取引の操作列 20 通りのうち write set が {A, B} になるのは (書 A, 書 B)・(書 B, 書 A) の 2 通りで、それぞれ順列 2 通り。1 取引あたりの平均の倍率は (18 + 2 × 2) / 20 = 1.1 になる。
- 関門 §4.3 の仮定 (1 構成あたりの所要が vhash の最大 6.6 秒と同程度) を当てると、取引 2 個の層は 1,600 × 1.1² × 6.6 秒 ≈ 3.5 CPU 時間、取引 3 個の層は 32,000 × 1.1³ × 6.6 秒 ≈ 78 CPU 時間 (1 node で 48 並列と仮定すると約 1.6 node 時間)。L2-5 は 36 通りで小さい。
- **これは上限ではなく仮定付きの試算である。** Silo の commit 手順のモデルが vhash のモデルより小さいか大きいかは分からない。実装 wave で L1・L2 を先に流して 1 構成あたりの所要を測り、L3 の既定の大きさと取引 3 個の層を計算ノードで流すかを決める。

---

## 6. 段 A の試しの計算の見積り (手順 5)

### 6.1 単価

- **1 評価 = pair job 1 本** (候補と stock を同じ job で測る) = **0.206〜0.220 node 時間**。探索設計 §6.1 の実測 (関数方策の軸、write-heavy、job の Elapse 741・793 秒)。依頼の「1 評価 0.21〜0.22 node 時間」と一致する。
- 注意: カード §6.4 は同じ単価を「pair = 2 評価」と数えて約 2.5〜2.6 node 時間 (6 job) を出している。探索設計 §6.1 の実測では pair job 1 本の Elapse が 0.206〜0.220 node 時間で、候補と stock の両方を含む。本書は実測の pair job 単価を使う。
- 単価が上がりうる要因 (探索設計 §6.1): 検査 1 本の所要は trace の commit 数と同じ向きに動き、速い候補ほど 1 評価が重い。workload の重さの比は backoff 軸で write-heavy : balanced : read-heavy = 1 : 1.39 : 3.86 で、方策軸では未測定。max_ope 16 の workload は 1 取引が長く、単価が変わりうる (未測定)。

### 6.2 workload の案

| # | 構成 (CCBench の YCSB の引数) | 狙い |
|---|---|---|
| W1 | `ycsb_max_ope=16`・`ycsb_rratio=50`・`ycsb_rmw=0`・`ycsb_zipf_skew=0.99`・`ycsb_tuple_num=1000000`・`thread_num=48` | Cicada Table 2 の条件 (16 要求/取引・読み書き半々・skew 0.99) に寄せた点。thread 数は原典の 28 でなく izanagi の確定動作点の 48 |
| W2 | 既存の write-heavy (`p2_2.py` の `ycsb_zipf_skew=0.9`・`ycsb_rratio=5`・`ycsb_rmw=0`、max_ope 10・48 thread) | sort 軸の先行 sweep・関数方策の軸と同じ動作点で比べられる |
| W3 | W1 の skew を下げた低競合の対照 (例えば `ycsb_zipf_skew=0.6`) | 低競合で費用と効果を測る対照 (カードは、低競合では sort が無駄な費用になりうるとし、省いたときの測定値は示していない) |

W1〜W3 の具体値は、試しの wave が結果を見る前に事前登録で固定する。

### 6.3 構成ごとの node 時間 (試算)

| 構成 | 評価数 (pair job) | node 時間 | 2 node 時間との比較 |
|---|---:|---:|---|
| A. 名前つきの対照 (Cicada の近似) 1 本 × W1〜W3 | 3 | 0.62〜0.66 | 未満 |
| B. A + LLM の候補 2 本 (計 3 本 × W1〜W3) | 9 | 1.85〜1.98 | 未満 (境界に近い) |
| 小さいモデルの取引 3 個の層を計算ノードで流す場合 (§5.4、48 並列の仮定) | — | 約 1.6 | — |
| **A + 小さいモデル** | | **約 2.2〜2.3** | **以上 → ユーザー確認が要る** |
| **B + 小さいモデル** | | **約 3.5〜3.6** | **以上 → ユーザー確認が要る** |

- 1 タスクの job 合計が 2 node 時間以上になるなら、投入前に見積りを示してユーザーの確認を取る (D2212 項 4、roadmap §5)。開発の検査 (受入・焦点走・変異) も同じ線で数える (common-2 §4)。構成 B は評価だけで 2 に近く、発火の計数 build や再測を足すと 2 を超えうる。
- 含まないもの: 待ち行列、品質の再測定、機械故障の再走、関門の前提の単位 (U0 ≈ 0.4〜0.5、U6 ≈ 2.3〜2.9 node 時間。関門 §7。それぞれの wave で数える)、LLM の所要 (coder + auditor + critic で 1 本 231〜280 秒、探索設計 §6.1)。
- **小さいモデルの取引 3 個の層は省かず、評価の前に流す。** 関門 §4.3 は「vhash の反例は 3 取引を要したので 3 取引の層を省かない」と定め、関門 §4.2 の 9 は小さいモデルの検査を計算ノードの build・実行より前に置く。したがって、取引 3 個の層の結果 (反例なし) が揃うまで候補の評価と certified を始めない。2 node 時間の線を下回るために検査の範囲を削ることはしない。取引 3 個の層を login の CPU で流せる規模だと実測で分かれば計算ノードの分は減るが、それは実装 wave で L1・L2 の所要を測ってから決める。

---

## 7. 前提条件の連鎖と、段 A の試しの起票に要るもの

段 A の試し (競合度順の施錠) の評価を始める前に、次が要る。

| 単位 (関門 §7 の名前) | この候補での中身 | worklog の item (2026-09-29 の main `035fc11fa` の「次の一手」) |
|---|---|---|
| U0 生死確認 | `A` 行と刻印の最小形で、stock が緑・迂回の変異が赤になることを測る | [T-2883] |
| U1 trace 拡張・U2 判定器 | gen-opt の certified は D1・D2a・D2b (全 key)・D3〜D5 を通すことを要求する (関門 §3.5 の 4)。この候補は読み書きの経路に触れないが、関門は軸によらずこれを要求する | [T-2884] |
| U1b Silo の取引内の値の扱いの修正 | 同上の前提。**item は「還元判断はユーザー確認待ち」で、採られなければ gen-opt の評価を始めずにユーザーへ判断を返す** | [T-2885] |
| U3 受理文法と骨格 API | 本書 §4 | [T-2886]。本書が仕様の所在 |
| U4 小さいモデルの基盤 + この仕組みのモデル | 本書 §5。モデルを書くのは loop の coder と別の主体 (dev-wave の Codex author) | 基盤は [T-2887]。この仕組みのモデルは [T-2896] (段 A の試し) の中か、その前の wave で作る |
| U5 driver 接続 | 仕様の digest ごとの小さいモデルの結果を build 前に要求する。この軸では「全順列」の 1 つの結果が全候補に効く | [T-2888] |
| U6 迂回の変異の本走・U7 auditor | 関門の検出力の確認と auditor の拡張 | [T-2889] (計算はユーザー確認が要る)・[T-2890] |
| 名前つきの対照 | §4.5 | [T-2896] |

順序の要点: U3 (本書の仕様) は U0〜U2 と並行して実装できる。評価は U1b ([T-2885]) と U2 の後で、この軸の小さいモデルの結果 (反例なし) が揃ってから始める。したがって段 A の試しの開始は、[T-2885] のユーザー判断にも依存する。

---

## 8. 限界

- **区分は親の判断である。** 関門 §5.2 のとおり、実装後に auditor が実コードから独立に答え直す。本書の答えは仕様 (カードの記述) からのもので、実装がその仕様どおりかは別の問題である。
- **原典を読み直していない。** 候補の機構と根拠はカードの記述 (段 6 の独立レビュー済み) を使った。Cicada の効果が Silo に転移するかは分からない (§3.4)。
- **骨格が TID word を読むことの費用。** 並べ替えを使う取引では、施錠の前に write set の tuple の cache line を 1 回ずつ余分に読む。直後に施錠で同じ line に触れるので費用は小さい見込みだが、測っていない。
- **優先度の同点。** 同じ優先度の要素は (storage, key) の順になる。候補が全要素に同じ値を返せば key 順 (stock と同じ順) になる。
- **INSERT・DELETE を含む取引は対象外。** 骨格はそれらの取引で順序を決める hook を呼ばず stock の key 順に戻す (§4.3)。小さいモデルも点の読みと UPDATE だけを扱い、INSERT・DELETE の経路 (node validation を含む) は範囲外である。YCSB 以外 (TPC-C など) へこの軸を広げるなら、モデルと骨格の両方を広げ直す。
- **関数方策の軸との併用は段 A の試しの外。** §2 の補足のとおり、待つ方策と組むと空転しうる。併用を試すなら、小さいモデルの O1 と全員待ちの状態の数え方を先に登録する。
- **D387 の限界** (関門 §8) はこの軸にもそのまま当てはまる。文法・骨格・検査を同じ主体 (AI の開発 wave) が変えられる限り、意図的な弱体化への完全な防壁ではない。
- **見積りは試算である。** 単価は関数方策の軸の write-heavy の実測で、この軸・W1・W3 では測っていない。小さいモデルの規模は vhash の最大の所要と 48 並列の仮定に立つ。

---

## 9. 何を確かめ、何を確かめていないか (まとめ)

**確かめたこと:** §1 の左列。いずれもコードと一次資料を読んで確かめた。

**確かめていないこと:**

- **プログラムを 1 つも実行していない。** 競合度順の施錠の効果、TID word の読みの費用、小さいモデルの所要、単価、いずれも未実測。
- 受理文法を既存の検査器の表の差し替えで作れるか (U3 の実装 wave)。
- 既存の壊し patch の中身と、§5.3 の危ない版の対応 (名前からの見込み)。
- 次点 (TsDefer) を開くときの骨格の具体形 (§3.3 は要るものの列挙だけ)。
- 「文献に無い」「新しい」の判定 (依頼の scope 外。本書はどの候補についても新しさを主張しない)。

---

## 10. 次の一手

- **U3 の実装 wave** は本書 §4 を仕様として、新しい軸の API header・文法の表・骨格の patch・検疫の分岐を作る (Codex author)。文法の test に §4.4 の拒否の名前と受理の正例を置き、既存の policy 系の受理集合が変わらないことを確かめる。
- **この仕組みの小さいモデル** は §5 を案として、U4 の基盤の上で dev-wave の Codex author が書く。場面の登録は結果を見る前に行う。
- **段 A の試しの wave** は、U1b・U2・U3・U5 とこの仕組みのモデルの結果が揃ってから、§6 の見積りを取り直し、2 node 時間以上ならユーザーの確認を取ってから投入する。

---

## 11. 段 6 の独立レビューと訂正

read-only の Codex レビュー 1 本 (3 レンズ: 一次資料との照合 / 設計の敵対検査 / 過剰・削除) が NO-GO で所見 4 件 (must-fix 3・should-fix 1) を出し、親は全件を real と裁定して直した。レビューは Q1〜Q8 の区分、カードからの引用 (Cicada の -12.7%、TsKD の +111%)、sort sweep の記載、段階 F の方策の中身、U0〜U7 と worklog の item の対応、§5.4・§6.3 の算術について、読んだ資料との不一致を見つけなかった。原典 PDF と sort sweep の生 report は照合していない。

| # | 所見 | 裁定 | 直したもの |
|---|---|---|---|
| 1 | L2-5 (3 key の全順列、36 組) の witness「施錠の途中どうしが重なる」は、先頭の key が同じ 12 組では no-wait の下で到達不能 | real (`lockWriteSet` は lock 済みに当たると取得済みを外して abort する) | witness を「36 組すべてで順列を選んで施錠を始めた」と「先頭の key が違う 24 組での重なり」に分け、12 組は最初の施錠での衝突を witness にした (§5.3) |
| 2 | モデルは write set の全 key を施錠する形だが、実装は INSERT を施錠 loop で飛ばし別経路で書く。候補が `insert` を観測して順序を変えられるので「全候補を覆う」が成り立たない | real (`writePhase` も INSERT・DELETE を別の分岐で書く) | 候補が並べ替えるのを UPDATE だけの write set に限り、INSERT・DELETE を含む取引では骨格が候補を呼ばず stock の sort に戻す形にした。`EntryContext` から `insert` を外し、モデルの書き込みの順も同じ順列にし、主張を「点の読みと UPDATE だけの取引について」に限った (§0・§4.2〜§4.4・§5.1・§8) |
| 3 | 「取引 3 個の層を後回しにすれば構成 A は 2 未満」は、2 node 時間の線のために検査範囲を削る選択肢に読める | real (関門 §4.3 は 3 取引の層を省かないと定める) | 取引 3 個の層は省かず評価の前に流し、結果が揃うまで評価と certified を始めないと書き直した (§6.3) |
| 4 | W3 を「stock または tie を選ぶはずの点」と結果を予断していた | real | 「低競合で費用と効果を測る対照」に直した (§6.2) |

焦点再レビュー (Codex read-only 1 本) は所見 1〜4 をすべて closed とし (36・12・24 組を数え直して一致、`delete_record` が DELETE の要素を登録し `lockWriteSet` が INSERT だけを飛ばすことを現物で確認)、GO を出した。新しい should-fix 1 件 (所見 5: INSERT・DELETE の取引で「候補を呼ばない」と書きながら、abort・commit の通知 hook は無条件に呼ぶ形だった) を親が real と裁定し、「順序を決める 2 つの hook だけを呼ばず、通知の 2 つの hook は取引の種類によらず呼ぶ」と明記した (§0・§4.3・§5.1・§8)。3 巡目のレビューは起動していない。
