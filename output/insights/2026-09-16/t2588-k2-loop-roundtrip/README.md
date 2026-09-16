# [T-2588] 段 4 合成ループを 1 巡閉じた — 新提案を 1 回評価し、その実測を次の提案へ戻した (2026-09-16)

wave: `dev-wave-t2588-k2-loop-roundtrip` / branch `worktree-dev-wave-t2588-k2-loop-roundtrip`
基点 main: `d97c423bdd14e0b416cb4f585d350e6c2b251287`。**実装面の差分ゼロ** (実測と記録だけの wave)。
裁定: `docs/decisions.md` D2044 項 9 (2026-09-16 ユーザー裁定)。逐語
「新しい機構は足さず、既存経路だけで行う」。

## 一行で

**role が新しく作った提案が既存経路で terminal verdict を得て、その実測が次の提案の入力になった。**
往復は閉じた。ただし**閉じたのは「実測の還流」であって「critic 診断の還流」ではない** — 後者へ届く
型付き入力の経路は現行ハーネスに存在しない (下の「閉じていないもの」)。

## 依頼が指した blocker は、着手時点で既に解消していた

依頼は「段 4 loop が literal 保持する CCBench 凍結 pin `028f34d` と現行 verifier が要求する trace
形式の版が食い違う」を段 1 で現物確認せよと指示した。**現物では解消済みだった。**

| 対象 | 現物 | 値 |
|---|---|---|
| 段 4 loop の pin | `orchestrator/campaign/p3_s4_loop.py:112` | `PIN = "511c9538e4e8efa54b45cda62e72389ed3b706ec"` |
| 前進 commit | `git log -L112,112` | `55d0f239945d34eaf39de500f076f332dc7e20b3` (2026-09-10 12:46:54 JST) |
| submodule gitlink | `git ls-tree HEAD external/ccbench` | 同一 `511c9538…` |
| 授権 | D1936 項 1 | 「項1はD38の段4固定pinを新規試行について改める。歴史的な028f34dの記録は保持する。」 |
| verifier | `orchestrator/verifier/parse.py:321-330` | v1 (5 field) 拒否 / v2 (7 field) 要求。**無変更** |

さらに T-2581 が 2026-09-10 に terminal verdict へ到達済みだった
(`output/insights/2026-09-10_t2581-k2-pin/README.md`)。ただしそれは**既存 proposal の値 20 の
再評価**であり、role が新しく提案を作りその結果を次提案へ戻す往復は一度も閉じていなかった。
**本 wave が埋めたのはそこである。**

## 1 巡の中身

実行した run-card は `output/insights/2026-09-10_cc-next-precheck/run-card.md`。同カードの
「最小の未充足事項」2 件 (fresh Claude session での role 登録確認、実走の新規指示) は本 wave で満ちた。

### 入力の固定 (run-card の逐語を現物で検算した)

知識 manifest は `knowledge-manifest-wal-only.json` (bytes sha256
`68eb3d5f4bcdab1e91a379868d188493bda548c5f26d6c3965a00dc5c9a70977`)。
**現行 resolver で解決し直し、digest が run-card の固定値
`396cd5594c3f22fb0d52476aa3eec51e62f26c5d3e81b1e25a5935697b73588e` と一致することを実測した。**
知識源は測定記録 1 件 (commit `2fa13a262a53b7f4e610a40a7a7af7f86fc9d621`、
path `output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl`、sha256
`2163b794fa3b1fce4de76a1b69262cadfc095bd986225a7266d6eacb6210a611`、6687 bytes / 15 行)。

初期測定入力も**現物の WAL で検算した**。最後の `bench_done` は variant `dad58f9f9000`、
ts `1783560370.5855775`、`throughput_tps=487088.5` / `abort_rate=0.072` /
`llc_miss_rate=0.3229014422247246` / `ipc=0.7387153219395488`。run-card の 4 値と完全一致する。
**この記録は `settled=false` で、`env_tag` は `linux-baremetal`** — 本走の機体 (pegasus) とは別である。
配線規模だけは同じ (`-thread_num=4 -ycsb_tuple_num=100000 -extime=1 -ycsb_rratio=50
-ycsb_zipf_skew=0.9 -ycsb_rmw=false`)。**この 2 点は role への射影に明示した。**

`planner_context_payload` は login node で呼べた (計測 site gate を通らない経路)。初期 whiteboard は
`[]`。driver CLI の `--emit-planner-context` は `_admit_env_contract` が `PEGASUS_LOGIN` を拒むため
login では使えず、harness 関数の直接呼び出しで代替した。

### 射影の事故と是正 (親の手で起こしたもの)

**planner の 1 回目を、知識源本文を省略記号で切った射影で投げた。**
出力を見る前に停止し、**全文のまま取り直した**。省略側にあったのは cmake の完全 path・
`cv_history`・`rep_notes`・`run_cmd` の前置きで、genome 値・verdict・commits/aborts・
leading indicators・workload フラグは省略側に入っていない。それでも source は sha256 で束縛された
成果物であり、加工した射影を「解決済み manifest を渡した」と記録すると provenance が濁る。
**出力未読で破棄したので候補の選り好み (再抽選) には当たらない。**

### role の出力 (逐語は `verbatim/`)

- **planner-v4**: `direction=decrease` / `magnitude=medium`。値も機序も出していない。
  不確実性として機体差・`settled=false`・`reps=2`・contention 未判定を自分から挙げた。
- **coder-v4-autonomous-k2**: `value=20`、`implementation="double now_backoff = 20;"`、
  `confidence=medium`、`classification=known_result_conditioned_derivative`。
  **親は自己申告 5 key を 1 つも代筆していない。** coder は初回で `confidence` まで揃えた
  (2026-09-09 の走行では欠落して差し戻しが要った)。

**値 20 は run-card が名指しする既知値である。** run-card の規定どおり「既知値の再提案」と記録し、
**未評価値生成の成功には数えない。新しい値が出るまで再抽選する操作もしていない。**
ただし coder の入力にあった値は 40 と 30 だけで、20 は入力に存在しない。coder は
「CV を大きく超えて分離できた既知の刻み幅 10 を踏襲して 30 -> 20」と外挿して到達した。
その 20 は fixture 既定値であり、T-2581 が現行 pin で既に評価済みの値でもある。
**「入力に無い値へ外挿した」ことと「未評価の値を作った」ことは別である。**

### 投入前に login で通した production 検査 3 本

1. `assert_closed_proposal_schema(..., require_auditor=False, require_coder_value=True,
   coder_contract=CODER_CONTRACT_K2)` → OK
2. `backoff_hole_grammar.validate_backoff_preflight("double now_backoff = 20;")` → `accepted=True`
3. `load_proposal_file(..., knowledge_input=<解決済み射影>, coder_role="coder-v4-autonomous-k2")`
   → OK (planner=decrease/medium、coder value=20、prior=None)

負例も同じ場で確かめた — `validate_backoff_implementation("double now_backoff = 25 + 1;")` は
`accepted=False` / `rule_id=backoff-grammar.initializer-literal.v1` で拒否する。
**これらの緑は login の静的検査であって、計算ノードの帰属照合・検疫・verifier の代わりにはならない。**

## 実測 — job `1216.nqsv`

固定 SHA の専用 submit-tree
(`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/submit-tree`、
HEAD `d97c423bd`、tracked clean、CCBench `511c9538…`) から、`tools/pegasus/README.md` §7 の
9 変数で 1 本投入した。third-party は同 checkout へ `fetch_third_party.py hydrate` で offline 供給
(cache-root `/work/1/SFC/tanab/izanagi-thirdparty-cache`)。

| 項目 | 値 |
|---|---|
| request / `pbs_jobid` | `1216.nqsv` / `0:1216.nqsv` |
| queue 待ち | ほぼ 0 (投入直後に RUN) |
| `driver_rc` | **0** |
| campaign | `p3-s4-loop-s4-autonomous-409e13f8` |
| variant | `8a84a7b00103` |
| genome | `silo|BACKOFF_FIXED=20,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| verdict | **`serializable` / `certified=true`** |
| commits / aborts / anomalies | 469618 / 83034 / **0** |
| bench | median **719324.5 tps**、2 反復 `[727985, 710664]`、run 内 CV 1.70%、`settled=true` |
| latency | 5494.6187 ns |
| `llc_miss_rate` / `ipc` | **null (欠測)** |
| 終端 | `1 committed / 0 aborted / 0 skipped`、`outcome=certified`、`iteration=1` |
| 停止判定 | **`continue`** |
| trace / perf 実行体 | `bb53c9b29b700bb1` / `c2fab12ed5edafad` |
| verifier result sha256 | `45b9681225cb7927d24a0f2494c4109868b55fd8e188ca8b1655ae6f2a6535a1` |

**`llc_miss_rate` と `ipc` が null なのは、この計算ノードで `perf` が使えないためである。**
`perf_observation.preflight` は `status=unavailable` / `rc=2` / `reason=nonzero-rc` を記録し、
`claim_scope` は `throughput=eligible` / `perf_required=unsupported` である。
**欠測であって 0 でも「差なし」でもない。推定で埋めていない。**

`build_start` の `knowledge_provenance` が候補と知識を同一レコードで束縛している —
`knowledge_level=K2`、`knowledge_manifest_sha256=396cd559…`、source は commit `2fa13a26…` /
path / sha256 `2163b794…`。

知識受領証 (`knowledge_manifest_receipt.json`) は**計算ノードの production job 内で生成された**。
source の `verification` は `method=git-blob-at-commit-path` / `observed_sha256=2163b794…` /
`status=verified`。`claim_boundary` は呼び手宣言どおり
`classification=known_result_conditioned_derivative` / `de_novo_claim=false` /
`pilot_comparison_eligible=false`。受領証自身が
「`data_boundary` と `claim_boundary` は記録上の宣言であり強制機構ではない」と書いている —
**この宣言を強制機構と読まない。** なお driver は proposal の `classification` を読み捨てるため、
role の自己申告 (`known_result_conditioned_derivative`) と呼び手宣言は照合されない。
今回は両者が一致したが、**一致は機構が保証したものではない。**

**campaign ID は T-2581 と同じ `409e13f8` である。** identity の 5 key (`spec_content` /
`ccbench_commit` / `search_tag` / `search_config` / `trial`) に proposal の値・superproject HEAD・
submit-tree path は入らないので、同じ設定なら同じ ID になる。段 3 の相談が投入前に再導出して
これを予告し、`loop.py` の recovery が**渡された layout の WAL だけを replay する**ことも現物で
確認した。新規 submit-tree なので過去 terminal による skip は起きなかった (実測: `1 committed`)。
**新しい走行の識別は submit-tree・実行 commit・request・証拠 root の組で行い、
「新しい campaign ID」とは主張しない。**

## 規律 6 の実測

`coder-v4-autonomous-k2` は知識源 15 行の全文を走査し、`instruction_like_content_detected=false`
を返した。`details` には走査範囲と、**判定の付記**が書かれている — 本文には
`perf_configure_cmd` / `perf_build_cmd` の cmake コマンド列、`run_cmd` の numactl + perf stat 起動列、
絶対 path が含まれるが、これらは「campaign が実行したコマンドの記録 (過去形の観測データ)」であって
宛てられた指示ではないと分類した、と自ら書いている。planner も同じ判断を返した。

**2026-09-09 に走行を止めたのは `campaign.lock` の `spec_content` という自由文であり、
今回の知識源 (測定記録の WAL 1 件) には含まれない。** gate は 1 行も触れていない。

## 還流 — 2 巡目の提案 (評価していない)

停止判定が `continue` だったので、裁定 R2 に従って critic と次提案へ進んだ。

### critic (1 回、逐語は `verbatim/critic-1.md`)

attribution は**「どの設計選択についても効いた / 効かないは言えない」**。理由は 3 つで、
いずれも構造的である — campaign 内に 1 点しかない (digest の「フラグ軸の限界効果」節は
同じ 1 点を 3 回書き写したもので水準差がゼロ個)、stock 対照が無い (digest 自身が
「比は計算不能」と書く)、別機体との比較は機体差・配線差・campaign 差が分離できない。
digest に指示混入は無いと報告した (規律 6)。

**critic は親の開示に無かった所見を 2 件出し、親が現物のコードで検算して両方とも確認した。**

| # | 所見 | 親の検算 |
|---|---|---|
| (a) | `latency_ns` は throughput の恒等変換で独立な指標ではない | `external/ccbench/common/result.cc:52-56` の `displayTps` が `result = commits/extime` から `latency[ns] = powl(10,9)/result*thread_num` と `throughput[tps] = result` を続けて出す。**確認** |
| (b) | reps が偶数だと `abort_rate` / `latency` は**速い側の反復**から取られる | `orchestrator/calibrator/runner.py:1053-1055` が `median = throughputs[len(throughputs)//2]` を取り、`reps=2` では上側になる。本走の 2 反復 710664 / 727985 に対し `1e9*4/727985 = 5494.6` が記録値 `latency_ns=5494.6187` と一致するので**代表 rep は 727985 側**。一方 `median_tps=719324.5` は 2 点の真の中央値で別の量。**確認** |

**(b) の帰結:** 本走の headline `719324.5 tps` と `abort_rate 7.75%` は**同じ反復の値ではない**。
偶数 reps では代表反復が系統的に速い側へ偏るので、軸の効果が noise floor 近傍のとき誤帰属を生む。
**この 2 件は本 wave では直していない** (実装面の差分ゼロが不変条件)。次の一手へ送る。

### planner-v4 (2 回目) と coder-v4-autonomous-k2 (2 回目)

**本走の実測を `current_perf` / `leading_indicators` / whiteboard へ入れて起動した。**
`throughput_ops_sec=719324.5`、`abort_rate_pct=7.75`、`cache_miss_rate_pct=null`、
`IPC_overall=null`、`contention_level="未判定"`、`last_delta_pct=null`、
whiteboard は iteration 1 の 1 件 (`decrease` / `medium` / `success` / `delta_pct=null`)。
**(b) の集約のずれも射影の散文で開示した。**

- **planner-2**: `direction=decrease` / `magnitude=small`。**実測を根拠に使った** —
  「本 campaign の現行 abort 率 7.75% は (知識源の) 帯の上端にほぼ一致」「iteration 1 は
  decrease/medium で success」。刻みを縮めたのは「転回の有無を跨がずに 1 点で判別できる」ため。
  親が開示した集約のずれ・欠測・機体差を自分から不確実性へ挙げた。
- **coder-2**: `value=25`、`implementation="double now_backoff = 25;"`、`confidence=medium`、
  `classification=known_result_conditioned_derivative`、`instruction_like_content_detected=false`。
  知識源の最良点 30 から刻み 5 で 1 段下げた、と説明する。留意点として (a) 機体差で絶対 tps は
  転移させず方向の符号だけ使った、(b) whiteboard が抽象なので iteration 1 の実値は不明、
  (c) 集約が揃っていないので 1 点の差分を過大に読まない、(d) 欠測の 2 指標は機序の裏取りに
  使っていない、の 4 点を自分から書いた。

**`value=25` は 20 / 30 / 40 のいずれでもない未評価の値である。** run-card の「既知値の再提案」には
当たらない。ただし**これを「新しい CC 構造の合成」とは呼ばない** — 固定 backoff の初期値である。

proposal-2 も production の検査 3 本を通した (`assert_closed_proposal_schema` OK /
`validate_backoff_implementation` accepted=True / `load_proposal_file` OK、
planner=decrease/small、coder value=25、`prior_critic_reverse=False`)。
**run-card の予算どおり評価していない。**

`prior_critic_reverse=false` は**親の解釈**である。critic は逆方向 (increase) を推奨していない —
主眼は R0 (対照を先に作る) と R1 (BACK_OFF 軸へ移る) で、R2 の log 間隔 3 点 (5/20/80) は
R1 の結果に条件づけられた副次案である。`_fold_critic_reverse` では reverse counter が 0 のままになり、
挙動は現状と同じである。**この bool が planner/coder の方向生成器へ渡らないことは下節のとおり。**

## 閉じていないもの (段 3 の敵対相談 2 本が独立に指摘した)

**critic の診断は、次の生成の型付き入力へ届かない。**
`planner_context_payload` が射影するのは whiteboard・knowledge_input・任意 policy_hint だけで、
whiteboard は 5 field (iteration / direction / magnitude / result / delta_pct) しか持たない。
`prior_critic_reverse` の機械 consumer は `_fold_critic_reverse` と停止判定だけで、
planner/coder の方向生成器には渡らない。しかも proposal-2 は評価しないので、保存した bool は
本 wave 内では消費すらされない。

したがって本 wave が示したのは**実測の還流**である。critic 出力と親が解釈した
`prior_critic_reverse` は**保存した**とだけ書く。「診断を次提案の入力にした」とは書かない。
診断を whiteboard や知識源へ足す対応は run-card の固定入力契約から外れるので**採らなかった**
(D2044 項 9 逐語「新しい機構は足さず、既存経路だけで行う」)。

## 段 3 の所見と裁定

段 2 plan (codex read-only) と段 3 相談 2 本 (sol / luna、異なるレンズ) を回した。全文は `reviews/`。
裁定は `ruling.md` 相当の内容を本節へ要約する。

**real として採用 (4 件):** critic 還流の欠落 (上記)、停止時の分岐の明示
(`stop_reason == "continue"` のときだけ critic と次生成へ進む — 本走は `continue` だった)、
「主張しない」の 6 件追加、親の不在主張を確認範囲へ限定。

**refuted (7 件):** 正しさの受理集合を広げる経路は無い / 知識源に指示混入は無い (相談 B が本文と
sha256 を自分で照合) / repo 内の新規実装 file は不要 / [T-304] の owned-path 侵犯は無い /
実測から型付き入力への写像と単位は現物と一致 / 同一 campaign ID でも skip は起きない /
pin・verifier の修正は不要。

段 2 plan の参照行は 12 箇所ずれていたが、成果物の値も受理集合も変えないため nit とし、
本記録には相談 A が照合した正しい行を使った。

## 独立の所見 — `src/coder-leakproof-context.md` の配線規模が現物と食い違う

同 file の "Measurement Setup" 節は `1m_records / t48_threads / extime3 / 3 runs` と書くが、
現物 `orchestrator/campaign/p3_s4_loop.py` の `default_perf()` は
records=100000 / threads=4 / extime=1 / reps=2 である。**逐語で射影すると coder に誤った
workload 像を渡す。** 本 wave の K2 射影 (`materials/leakproof-context-k2.md`) では現物へ訂正し、
K0/K1 向けの知識禁止条項 (K2 契約と衝突する) も射影から外した。

**同 file 自体はこの wave では直していない。** role への入力文書を実験の途中で書き換えると
他アーム (K0/K1) の実験条件が黙って変わるため、裁定を経るべき変更だと判断した。
次の一手へ新規項目として立てる。

## 主張しないこと

- **1 巡が閉じたことは、合成による改善や探索の有効性の実証ではない。**
- 新しい数値が出ても、**固定 backoff の初期値変更であって新しい CC 構造の合成ではない。**
- proposal-1 の `certified` は**候補間の certified な選択ではない**。proposal-2 は未評価である。
- `knowledge_use` は role の自己申告であり、**K2 の利用因果を証明しない。**
- critic 診断の「保存」「入力への投入」「改善効果」は**それぞれ別である。**
- 歴史測定 (487088.5 tps、`linux-baremetal`) と本走 (719324.5 tps、pegasus) の差は
  **性能優越の根拠にならない。機体が違う。** `last_delta_pct` は null のまま維持した。
- **本経路は legacy critic を使うため B-4 ablation には非適格である。** 新 CC 構造の合成・
  B-4 正式実験には数えない。
- `job rc=0` だけを成功の根拠にしていない。verdict と WAL の terminal record を見ている。

## 証拠の所在

repo 内 (本 dir):

- `evidence/` — `job.stdout` / `job.stderr` / `compute-result.json` / `reservation.json` /
  `masstree-prebuild-receipt.json`
- `materials/` — `proposal-1.json`、`proposal-2.json`、`leakproof-context-k2.md`
- `verbatim/` — role の逐語出力
- `reviews/` — 段 2 plan と段 3 相談 2 本

**可逆最小正規化 (DW-S07):** `job.stdout` は行末空白 2 行が `git diff --check` に抵触するため
行末の空白 / tab を除去した (可視文字不変)。原文 sha256
`fa9c19cce4525acf79ec4b561bd4e3d2af5befde8693bd1b63cacb11d2d582b8` (12370 bytes)、
正規化後 `a1f02eb32efc9319dc39187e578ea3540566bec5b7dce06bb44c8edc4b3e907a` (12366 bytes)。
`diff -w -B` で原文と一致する (実測 rc=0、2026-09-16)。他の 4 file は無変更の複製で、
原文 sha256 は `job.stderr`=`5f0561326d17494795b04fd8842cd809e56e97dd64ae21245d2f553b8ea5846d`、
`compute-result.json`=`d4814391429067033a30ac57ed57edfdd3b4174fb249b6f6c6b22f935d8ad06b`、
`reservation.json`=`eead3864b381bc843d715de96400313daca6a2bf43f3fd46be4e6e27cf57757a`、
`masstree-prebuild-receipt.json`=`c81f494f5cf6aff547aef48749145e73808aa82a7cea4456dd9753b211f4f2db`。

**campaign WAL・`campaign.lock`・`s4_loop_digest.txt` は repo へ複製していない** — これらは
`guard_bash` の防護対象である。原本は repo 外 job root
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2588-k2-loop-roundtrip/` の下に残る:

- WAL: `submit-tree/output/exploration/campaigns/p3-s4-loop-s4-autonomous-409e13f8/runs/wal.jsonl`
- checkpoint: 同 `loop_state.json`、digest: 同 `s4_loop_digest.txt`
- 知識受領証: 同 `knowledge_manifest_receipt.json`
- job 出力の原本: `evidence/attempt-0001/`
