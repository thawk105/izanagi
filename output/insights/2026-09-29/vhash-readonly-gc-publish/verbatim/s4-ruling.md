# 段 4 裁定 — md_22 [T-2911] (2026-09-29 22:2x JST)

入力: 段 1 brief (`s1-brief.md`)、段 2 plan (`codex/stage2/out.md`)、段 3 レンズ A (`codex/stage3a/out.md`、正しさ境界と整合)、レンズ B (`codex/stage3b/out.md`、実効性と過剰・削除)。
段 4 直前の実測: `probe-stack2.sh` → `probe-stack2.log` (repo 外の使い捨て)。裁定 inbox 再走査: 最新 `2026-09-29-interactive-evolution-verdicts.md` は本主題と無関係。local main は起点 `8fe87f852` のまま。

## 親の追加実測 (段 4 前)
- `node_map_.clear();` の直後・`return true;` の直前に挿入する 1 hunk (前文脈 2 行・後文脈 3 行) は、pin 単独・pin+trace・pin+vlife のいずれにも `git apply` (fuzz なし) で rc=0。→ 段 2 の「2 file 必須」(P4) は refuted、レンズ B 所見 6 は real。
- trace と vlife の相互適用は両順序とも**実適用**で rc=1 (transaction.hh:35 と transaction.cc:931/932)。→ レンズ A 所見 6 の「逆方向は --check だけ」は、今回の実適用で解消 (brief の主張自体は正しかった)。

## 所見の裁定
| 所見 | 判定 | 採否・扱い |
|---|---|---|
| A1 mainte() 全体は「公開を早める」と「GC 実行を早める」の 2 介入 | real | 実装は mainte() 全体 (P3 維持、Cicada の「ro commit も mainte を通る」の自然形)。小モデルは flag だけ / mainte 全体の 2 形を両方探索。一次資料で「公開と自 thread の GC 実行の両方を含む介入で、効果を両者に分解していない」と限界に書く。C++ での分解腕は作らない (G05: 分解が無くても (a) の結論は変わらない) |
| A2 正例は最短 witness まで要る、GC 安全判定を自己照合にしない | real | 採用。正例 (i)(ii) は具体的な最短 witness (step 列) を test で固定し、到達しなければ正例合格としない。GC 安全の oracle は「active tx が将来選びうる版 + 保持 pointer の版」を版鎖と tx の読み時刻から独立に導き、回収側の境界計算を使わない |
| A3・B3・plan P5 計器なし build で同じ ro 手続きを作れない | real | 採用。**workload patch を新設し、3 build すべて (計器・計器なし・trace) で同じ生成経路を使う** (下記 B-2)。vlife 自身の ro 書換えは使わない (`izanagi_ronly_pct=-1`、`izanagi_long_kind=0`、`worker1_insert_delay_rphase_us=0`)。代償: vlife の「長い tx」ラベル (D-C の種別・保持者種別の長短区別) は失われる。一次資料に書く |
| A4 分割 patch の同一性 | 解消 | 単一 patch にしたので分割照合は不要。代わりに 3 preimage への厳密適用と macro=1 の ro 分岐の前処理一致を smoke で記録 (非致命の観測ではなく、適用失敗は build 不能なので自然に fail) |
| A5 登録簿を条件付きにしない | real | 採用。閉包は下記 B-4 で全列挙し必須 |
| A7・B2 md_15 の値は局所的、headline を絞る | real | 採用。headline = 「公開停止の解除」(wait10msR の公開回数) と「公開頻度の条件内対差」。境界年齢・終了時生存版・throughput は別指標 (反復点付き)。md_15 の D-C は介入前の機会量としてのみ引用 |
| B1 S95 は既定 genome・skew 0 | real (blocker) | 採用。系列 S (既定 genome、skew 0) と T (最良設定、skew 0.9) の 2 系列にする。md_22 の土台 (md_11 最良) は T |
| B1 (b) の保持時間は現行計器で測れない | real | (b) を縮小: variant 腕の wait10msR と none の境界年齢差 (公開が再開した後に長い ro が境界を押さえる分の観測値) と、公開時の保持者 (ro) の割合で示し、「保持時間は未測定」と限界に書く。等間隔標本の新計器は作らない |
| B4 同時刻対照の組み方 | real | 採用。各条件の stock/variant を同一 job・同一 node で対にし、順序を事前固定の均衡配置 (6 反復: AB BA AB BA AB BA)。集計は条件内の対差・比。診断 job と性能 job は別系列として報告 |
| B5 反復・所要 | real | 採用。smoke で 1 run の所要を実測してから本計測の job 分割を確定し、smoke・build・verify・再走余地を含めて 2 node 時間判定。throughput は生点と範囲を示し、小差は「検出不能」と書く |
| B7 verify で variant 経路の発火を示す | real | 採用。**計数 macro `IZANAGI_CICADA_RO_GCFLAG_COUNT`** (先例 CICADA_FWD_COUNT、companion RO_GCFLAG=1) で「ro commit の mainte で flag を立てた回数」と「ro commit の回数」を終了時に 1 行出す。verify と smoke では非 0 を受入条件、性能 build では使わない |
| B8・plan P1 修正 | real | P1 を条件付きに改める (下記) |
| B 削除表: C++ 壊し正例 | 採用 (削除) | 作らない。根拠は小モデルの正例と md_14 の保持版変化の実測 (同型の slot 引上げ) |
| B 削除表: 時間平均生存版の新計器 | 採用 (削除) | 作らない。終了時の論理生存版 (vlife) を診断値として使う |
| B 削除表: 格子の縮小 | 一部採用 | gc 1 ms と gc 100 ms は外し、gc 10 µs のみ。ro 50% は残す (用量の形を見る。S50/T50 は md_15 で (b)=0.12〜0.21) |
| B 削除表: 図の縮小 | 採用 | 図は 2 枚 (公開回数と境界年齢の対照、throughput の反復点)。raw から再生成 |
| B 削除表: 小モデル独立 module | 同意 | 新 module 1 つ、J1 は adapter で流用、新しい汎用基盤は作らない |

## 確定した前提 (P1〜P5 改訂)
- **P1 (改):** YCSB (delete なし)・`group_commit=0`・`SINGLE_EXEC=0` で、ro の `rts_` と ThreadRtsArray を tx の間変えない限り、ro commit の参照解放後に mainte() を呼ぶ変更は版を誤回収しない。GC flag は境界の公開と回収の実行を**起動**するが、回収してよい版の範囲は slot の min で決まる。delete・group commit・全メモリ順序の形式証明は範囲外。
- **P2 (改):** 正例 = (i) ro の途中で slot を最新 MinWts−1 へ上げる、(ii) ro commit で slot を ∞ にし次の begin の store 前に公開が入る。(iii) flag だけを ro の途中で立てる版は**陰性対照** (発火しない予想、発火したら P1 が崩れるので段 6 で停止して再裁定)。md_22 の例示との対応表を一次資料に書く。
- **P3:** macro `IZANAGI_CICADA_RO_GCFLAG` (既定 0)、1 で ro commit の `node_map_.clear();` の後・`return true;` の前で `mainte();` を呼ぶ。挿入後に無条件 `#line` で stock の行番号へ戻す。
- **P4 (改):** variant は **1 file** `patches/cicada-ro-gcflag-variant.patch` (preimage = pin の `cc/cicada/transaction.cc`、pin+trace・pin+vlife にも厳密適用で当たる)。
- **P5 (改):** 下記 B-3 の条件表。

## プラン v2
### 単位 A (小モデル、Codex author A)
所有: `tools/vhash_forwarding_model/ro_gc_publish.py` (新規)、`orchestrator/tests/test_vhash_forwarding_model_rogc.py` (新規)。既存 file は編集しない (import のみ)。
- A-1 状態機械: plan §2 の表どおり (共有変数の load/store 1 回 = 1 step、begin の 3 手、leader の flag 判定・各 slot load・MinWts/MinRts store・flag reset・execute flag store を分離、GC の境界 load・鎖切断を分離)。worker 2〜3、key 1〜2、ro read 1〜2、手続き 2 回まで。状態数上限を持ち、上限到達は「未完探索」として失敗扱い (緑にしない)。
- A-2 腕: stock (ro commit で何もしない)、safe-flag (ro commit の参照解放後に timer 条件で flag だけ)、safe-mainte (参照解放後に GC 実行 → flag、Cicada の mainte 順)、neg-early-flag (ro の途中で flag だけ、陰性対照)、bad-raise-slot (P2 i)、bad-clear-slot (P2 ii)。
- A-3 判定: GC 安全 (独立 oracle、A2)、直列化可能性 (既存 J1 を adapter で)、公開の前進 (長い ro が active の間に MinRts の公開が起きる到達列の有無。同値公開は前進と数えない)。
- A-4 期待: stock と safe-* と neg-early-flag は GC 安全違反 0・閉路 0。stock は長い ro active 中の公開到達 0、safe-* は到達あり。bad-* は GC 安全違反の最短 witness を test で固定。neg-early-flag が違反を出したら test は赤 (P1 崩れの検出)。
- A-5 実行入口: module の `main()` (`python3 -m tools.vhash_forwarding_model.ro_gc_publish --out <json>` 相当、既存 cli.py は変えない)。結果 JSON に腕ごとの状態数・違反・witness・公開到達を出す。
- 規模上限: module 800 行、test 500 行。

### 単位 B (patch・driver・登録簿、Codex author B)
所有: `patches/cicada-ro-gcflag-variant.patch`、`patches/cicada-ro-gcflag-workload.patch` (新規 2)、`orchestrator/campaign/vhash_ro_gc_publish.py` (新規)、`orchestrator/tests/test_vhash_ro_gc_publish.py` (新規)、`tools/plotting/plot_vhash_ro_gc_publish.py` (新規)、
`orchestrator/campaign/condition_meaning_gate.py`、`orchestrator/tests/test_condition_meaning_gate.py`、`orchestrator/campaign/screening_driver.py`、`orchestrator/tests/test_screening_driver.py` (要るなら)、`orchestrator/tests/test_p3_s4_loop.py`、`orchestrator/campaign/materializer_admission.py`、`orchestrator/tests/test_p3_build_authority_cli.py`、`orchestrator/tests/test_ccbench_spawn_sites.py`、`orchestrator/tests/README.md` (単位 A の新 test file も登録する)。
編集しない: vlife patch・trace patch・forwarding/interval patch・`vhash_cicada_vlife.py`・`external/ccbench`・`patches/ledger.json`・`patches/README.md` (entry は親が段 7 で書く)・単位 A の所有。
- B-1 variant patch: P3・P4 どおり。`IZANAGI_CICADA_RO_GCFLAG_COUNT` (companion RO_GCFLAG=1) の計数 2 つと終了時 1 行を同じ patch に入れる (owner TU = transaction.cc、終了時出力の置き場は先例 CICADA_FWD_COUNT に倣い owner TU 側)。
- B-2 workload patch: macro `IZANAGI_CICADA_ROGC_WORKLOAD` (既定 0)。手続き生成時 (retry では変えない) に実行時 flag の確率で全 op を READ・ro に、非 ro は少なくとも 1 op を write にする (vlife の意味と同じ)。worker 1 の手続きを長い ro に固定し、読み終えて commit 処理に入る前に実行時 flag の µs だけ待つ (vlife の commit 冒頭の待機と同じ位置の意味)。乱数は YCSB の既存系列を乱さない別系列。pin・pin+trace・pin+vlife に厳密適用で当たり、variant patch とも重なる置き場にする (候補: `include/ycsb.hh` の run() と、flag 定義を持つ `cc/cicada/ycsb_cicada.cc`。meaning gate は owner TU の前処理だけを見るので分岐は owner TU とその include header に置く)。実現した ro 試行率・commit 数と長い ro の件数を終了時 1 行で出す (計数は安い整数加算。性能 build でも使うので最小に)。
- B-3 driver `vhash_ro_gc_publish.py`: vlife を import で再利用 (編集しない)。subcommand は `smoke` (3 build の適用・短走・計数行・1 run 所要の実測)、`verify` (pin+trace+workload+variant で判定器)、`measure` (pin+vlife+workload+variant、VLIFE=1)、`throughput` (pin+workload+variant、計器・trace なし。VLIFE・TRACE・COUNT を拒否)。
  条件表: 系列 S (既定 genome、skew 0) と T (md_11 最良 genome、skew 0.9) × ro 指定率 {0, 50, 95} × 長い ro {none, wait10msR} × gc_inter_us 10 × arm {stock (RO_GCFLAG=0), variant (=1)} × 6 反復 (AB BA AB BA AB BA)。YCSB 10 ops、update tx の op は読み 50%、48 worker、1M 件、3 秒 (md_15 と同じ)。
  verify: default genome と最良 genome、ro 50%/95%、長い ro 有無、gc 10 µs、小走行 (md_3 の小走行の規模) × 3 seed。判定器 rc: 巡回 = 失格、indeterminate を上限、`READ_WTS_MISMATCH=0`、COUNT の ro flag 立て回数 > 0 を必須。最良 genome (OPT=1/PROM=0) の trace 網羅は md_20 未着なので未確認と記録。
  全 raw に patch sha256・pin・genome・flags・arm・rep・順序・build macro・計器有無・hostname・開始終了時刻。
- B-4 登録簿の閉包 (必須): condition gate に 3 macro (RO_GCFLAG・RO_GCFLAG_COUNT・ROGC_WORKLOAD) の DefineSpec と分岐目印・件数・companion、同 test の件数 pin、`screening_driver._CONDITION_DEFAULTS` (鍵集合 == DEFINE_SPECS)、`test_p3_s4_loop.allowed_non_variant_tokens` (裸 `IZANAGI_*` macro の patch)、`"--build"` を字面に持つ新関数の materializer 登録と `test_p3_build_authority_cli` の `MANUAL_BUILD_FILES`・`EXPECTED_NON_ADMISSIBLE`、新 subprocess site の `test_ccbench_spawn_sites` 分類、`orchestrator/tests/README.md` の新 test file 2 本の登録。子は先例 commit (`7a4f9a592`・`a3bc64e3b`) の変更 file 一覧を起点に外部交点表を作り報告する。
- B-5 作図: 図 2 枚 (公開回数・境界年齢の条件内対照、throughput の反復点)。raw から再計算、入力 sha256 を provenance に。
- 規模上限: driver 900 行、test 600 行、patch 各 200 行。

### 親
計算ノード投入 (generic dispatch で `python3.10 -m orchestrator.campaign.vhash_ro_gc_publish`、md_15 の run-dispatch 型、job ごとに別 checkout)、受入、変異、一次資料、spool fragment、patches/README.md の entry。
md_18・md_20・md_21 の job と同じノード・同じ時刻にしない (投入前に qstat でノードを確認、事後に receipt の hostname と時刻で照合)。

## 変異の事前登録 (DW-M01、単一理由性は実装後に確認し、できなければ登録から外して再照準)
| ID | 位置 | 変異 | 殺すはずの test (node 名は実装後に確定) |
|---|---|---|---|
| MA1 | ro_gc_publish.py の GC 安全 oracle | 常に違反なしを返す | bad-raise-slot / bad-clear-slot の witness test |
| MA2 | bad-raise-slot 腕 | slot 引上げを消す (stock と同じ) | bad-raise-slot の witness test |
| MA3 | leader 公開 | flag を見ずに公開する | stock の「長い ro 中の公開到達 0」test |
| MA4 | safe-mainte 腕 | ro commit の flag 立てを消す | safe の「公開到達あり」test |
| MA5 | safe-mainte 腕 | 参照解放の前に GC 実行 (順序入替) | 実装後に発火を確認 (P1 どおりなら不発の可能性 → 不発なら等価変異として記録し登録から外す) |
| MA6 | J1 adapter | rw 辺を落とす | adapter の閉路検出 test |
| MB1 | variant patch | `#if` を外し無条件 mainte() | 既定 macro の inert / 前処理一致 test |
| MB2 | variant patch | mainte() を `read_set_.clear();` の前へ | 挿入位置 (参照解放後) の構造 test |
| MB3 | condition gate | RO_GCFLAG の inert 値を変える | gate の spec test |
| MB4 | driver throughput | VLIFE=1 を拒否しない | throughput の計器拒否 test |
| MB5 | driver | 反復の順序を均衡配置でなくする | 条件表・順序 test |
| MB6 | driver verify | 巡回 (rc=1) を受理 | verify の失格 test |
| MB7 | driver verify | COUNT の ro flag 立て回数 0 を受理 | verify の発火必須 test |
| MB8 | workload patch | 非 ro の write 1 op 保証を消す | workload patch の構造 test |
| EQ-1 | 等価変異 (category=positive) | driver の無関係な docstring 1 字 | 生存が期待 |

## 研究前進への影響 (G05)
- workload patch なし → throughput と診断の workload が違い、(a) の費用 (throughput) を同条件で言えない。
- COUNT なし → 判定器を通した build で variant の経路が踏まれた証拠が無く、「variant で巡回 0」が空の主張になりうる。
- 系列 S なし → md_15 の最大効果条件を追試できない。
