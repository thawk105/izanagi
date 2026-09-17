# [T-2632] 順序 (2) の precheck — B-4 事前登録 §5 の 2 欄 (校正済み `PerfConfig` / env_tag) は今日記入できない: 第一の理由は D1483 の順序、次に reps の出所と契約世代・確認者の未裁定

- authority: none
- default_effect: no-state-change

可変状態の正本ではない。可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。
本書は wave `dev-wave-t2632-b4-s5-precheck` (branch `worktree-dev-wave-t2632-b4-s5-precheck`、起点 local main `38353207f`) の
一次資料を凍結したものである。**実装面 (D95 決定 2) の差分は 0。§5 の値セルは 1 byte も変えていない。**

- 実測日時: 2026-09-17 JST、機体 `pegasus02` (login node)。計算ノードへの dispatch は行っていない (§「本書が閉じないこと」)。
- 依頼: [T-2632] 順序 (2) の precheck (P2)。§5 の 2 欄を今日記入できるかを確かめ、記入はせず条件と不足を報告する。
  floor 欄 (A-5 裁定待ち) と順序 (3) の campaign 起動には触れない。規律 2 を緩めない。

## 結論

1. **2 欄とも今日は記入できない。第一の理由は値の有無ではなく順序である。** D1483 (2026-09-02 ユーザー裁定、D1510 で
   再確認) は「§5 全欄の記入は、床値の 12 行裁定・測定・成果物の採用裁定が済んだ後に、順序どおり個別に閉じる。
   床値手番の担当者 3 者の指名は §5 全欄を解禁しない」と定め、解禁しない欄として「実行 site、較正済み `PerfConfig`」を名指し
   している。**この 2 欄の記入順序を解除する後続裁定は無い** (D1812 (a) は primary outcome 欄の既存記入の維持、D1871 は開始時刻
   だけの例外。段 3 レンズ A が D1641 / D1812 (c) / D1936 項 7 / D1986 / D2088 / D2089 を独立に確認)。床値の 12 行裁定は
   D1641 決定 3 で済んだが、**床値の測定 (A-5 の spec 凍結を含む) と成果物の採用裁定は未了**である。
2. **順序を除いても、`PerfConfig` 欄は較正だけでは閉じない。** accepted 較正 3 件は records / threads / workload (3 key) /
   env_tag / clocks_per_us を供給する。extime は較正の出力値ではなく取得構成 (tracked な取得 argv に `--extime` 無し → CLI 既定 3)
   からの復元で、D2088 が床値 spec 用に行った導出と同じ (`ycsb_max_ope=10` も同種)。**reps は較正にも取得構成にも無く、D2088 の
   `reps=5` は床値 spec 用の AI 選択であって B-4 本走への転用は認可されていない。** さらに、**§5 の pin を実走 `PerfConfig` へ
   束縛する既存経路が無い** — base CLI は `p3_s4_loop.py:2745` で無条件に `default_perf()` (records 100000 / threads 4 /
   extime 1 / reps 2) を使う (段 3 レンズ B の指摘)。§5.1 の「calibrator が決めた値へ差し替えるまで記入しない」の「差し替え」は
   実装を要する (本 wave 外)。記入者の担当範囲も未裁定。欄の書式 (複合値) は裁定不要 (D1854 / §0 / 先例)。
3. **env_tag の値 `pegasus` は site resolver から機械導出できる (実測)。** B-4 の sanctioned 起動経路 (`p3_b4_launcher.py:166`)
   が使う base driver の resolver (`p3_s4_loop._current_site` → `_admit_env_contract`、site→tag は literal 写像) と、registry
   属性 (`env_contract.lookup_required_attestation_contract()`) は現 checkout で同じ契約 object を返す (同値は現世代限り —
   写像の二重定義は残る)。**閉じないのは欄の併記要件の側**である — (a) B-4 本走の site の明文裁定 (D1641 決定 3 は床値の site)、
   (b) 「環境契約の artifact path と hash」がどの世代を束ねるか (active は g1 `e576e9cd…`、その calibration_ref は D1537 が
   自己整合しないとした較正。g2 `1346c20b…` は登録済み未発効で、D1484 が発効を鎖の末尾に置く)、(c) 確認者の担当範囲
   (identity は thawk105 だが、D1483 は 3 者指名の他欄への波及を明文で否定)。併記の形は裁定不要。
4. 本 wave は §5 を記入せず、実装も gate も台帳も足していない。成果物は本書と裁定パッケージだけである。

## 欄 1: 校正済み `PerfConfig` (records / threads / reps / extime) の artifact パスと hash

§5.1 の解除条件: 「`p3_s4_loop.default_perf()` は自ら『性能比較用 calibration ではない』と宣言している (配線規模)。
calibrator が決めた値へ差し替えるまで記入しない。」 実走前検査 (`p3_b4_admission_record.py`) は本欄に非空と予約 sentinel
不在しか要求しない (型・意味・参照先の実在は検査しない — §5.1 が明記)。

| `PerfConfig` の項目 | 今日供給できるか | 出所 (現物) | 種類 |
|---|---|---|---|
| `records` | できる | 較正 3 件の `saturation.records` = 1,000,000 (rr95) / 1,000,000 (rr50) / 2,000,000 (rr5) | calibrator の出力値 |
| `threads` | できる | 較正 3 件の `threads` = 48 | calibrator の出力値 |
| `workload` | できる (3 key) | 較正 3 件の `workload` = `{"ycsb_rmw": "0", "ycsb_rratio": "95"/"50"/"5", "ycsb_zipf_skew": "0.9"}` | calibrator の出力値 |
| `extime` | 復元はできる | 較正 JSON に key 無し。取得 argv (`output/env/pegasus/calibration/job-staging/{0:995805,0:892707,0:478}.nqsv/calibrate-argv.json`、tracked) に `--extime` 無し → `orchestrator/calibrator/cli.py` の既定 `--extime 3` | 取得構成からの復元 (D2088 と同じ導出。較正の出力値ではない) |
| `reps` | **できない** | 較正 JSON に反復数の key 無し (`reps` の文字列は cost formula の `sweep_reps(3)` / `noise_reps(10)` のみ)。取得 argv にも無い。D2088 の `reps=5` は床値 spec 用の AI 選択 | **出所なし。B-4 用の承認なし** |

較正 3 件 (いずれも tracked、`quality.status = accepted`、`env_tag = pegasus`、`clocks_per_us = 2100`):

| workload | path | sha256 |
|---|---|---|
| rr95 | `output/env/pegasus/calibration/registered/calibration-5c836a22eff9ab40.json` | `5c836a22eff9ab40cabb23cb597cd0b3c232979696c5784b6b3d358b92c789cc` |
| rr50 | `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json` | `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9` |
| rr5 | `output/env/pegasus/calibration/registered/calibration-2b7ba072b88023ae.json` | `2b7ba072b88023aecb4361781229bb5343dbfa489f4c7cc3dd8369c33bd3a067` |

これは T-2288 の A-4 セル (D2089) と同じ 3 件で、T-2288 が 8 件を `load_verified_calibration(pegasus, 2100, required)` へ通して
ADMITTED を確認している (本 wave は sha256 と field 値を再読しただけで admission は再走していない)。

**欄を埋めるために要るもの (順序 D1483 を満たした後):**

- **B-4 用 `PerfConfig` の採用範囲と承認主体。** 3 種を分ける — 較正の出力値 (records / threads / workload 3 key)、取得構成からの
  復元 (extime=3 / `ycsb_max_ope=10`。D2088 は「取得当時の source bytes まで検証したものではない」と限定)、設計上の選択 (reps)。
  §11.1 は「AI が起草した候補値を無裁定の既定値として凍結へ入れない」と定め、D1641 決定 3 の委任は逐語で「calibrator の出力を
  採り」なので、calibrator の出力に無い reps は委任の外にある (D2088 自身が「AI の選択であることを残す」と書いた理由)。
  承認対象は値だけでなく、復元値と選択値を §5.1 の要件にどう位置付けるかを含める。
- **承認済み設定を base CLI が消費する経路 (code、本 wave 外)。** `floor_pair_driver._bind_checkout_inputs` は較正と「既に作られた
  perf」を比較する binder、`p2_2` は手書き定数との比較であり、較正から B-4 設定を生成する経路ではない。base CLI は
  `default_perf()` を無条件に使う。§5 に pin を書いても、それを実走が読む道が無い。専用 producer の新設が必須という意味ではない。
- **完全な `PerfConfig` の組み方。** 較正の workload は 3 key で `ycsb_rmw="0"`。`performance_correctness_workload` は 4 key
  (`ycsb_max_ope` 含む) を要求するが、その呼出しは `loop.py` の performance verify mode に限る (全 B-4 本走で必ず発火するとは
  一般化しない)。3 key は逐語保持し、`ycsb_max_ope` の追加規則と 3 workload ↔ 設定の対応を別に示す。
- **記入者の担当範囲。** identity は thawk105 (D1266 / D1641)。D1483 は 3 者指名の他欄への波及を否定しているので、今回 2 欄の
  記入まで AI 委任を及ぼすかが未確定 (新規人物の指名ではない)。
- 欄の書式は裁定不要。D1854 は「本欄が 1 セルであることは意味上の個数を 1 件に固定しない」と確定し、確定値の `key=value; `
  複合値は対象 driver 欄と model snapshot 欄に先例がある。書式の自由は reps や消費経路の不足を補わない。

## 欄 2: env_tag (実測環境)

§5.1 の解除条件: 「選択した driver と実行 site が確定し、その site の環境契約の exact tag と一致することを同じ site resolver から
機械導出して確認してから記入する。同一 driver でも site によって tag が分かれるため、driver・site・tag の 3 つ組で固定し、環境契約の
artifact path と hash、確認者を発効版へ併記する。」

**機械導出 (親の実測、login node、checkout `38353207f`):**

| 項目 | 実測 |
|---|---|
| `site_policy.current_site()` (login) | `PEGASUS_LOGIN` (live の計算ノード判定は login では出ない。compute の分類は hostname `bnode[0-9]+` による — `site_policy.py:40`、NQSV marker は login / suspect の分類に効く) |
| B-4 sanctioned 経路の resolver | `p3_b4_launcher.py:166` → `p3_s4_loop._current_site()` → `p3_s4_loop._admit_env_contract(site)` (`p3_s4_loop.py:138`)。`_SITE_ENV_TAGS = {OTHER: "linux-baremetal", PEGASUS_COMPUTE: "pegasus"}` (literal dict、`p3_s4_loop.py:117`) → `env_contract.lookup(tag)`。Pegasus wrapper (`tools/pegasus/p3_s4_loop_pegasus.sh`) も base CLI 経由で同じ解決 |
| `_admit_env_contract(PEGASUS_COMPUTE)` | env_tag `pegasus`、contract_sha256 `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01`、clocks_per_us 2100、attestation_mode required |
| registry 属性 `lookup_required_attestation_contract()` (`p2_2.resolve_site_runtime` / `floor_pair_driver._machine_env_tag_for_site` が使う経路) | 現 checkout では同一 object (`is` で True)。**同値は現世代限り** — required 契約の追加・属性変更では属性経路が拒否または別契約を選ぶ一方、base は literal の tag を引き続ける (写像の二重定義) |
| 較正 3 件の `env_tag` | いずれも `pegasus` (一致)。ただし較正 argv の `--env-tag pegasus` は明示入力であり、acquisition receipt の hostname (bnode027 / bnode048 / bnode013) は allocation の証拠であって「B-4 resolver が計算ノードで `pegasus` を返した記録」ではない |

**契約世代 (現物):**

| 世代 | contract_sha256 | calibration_ref | 状態 |
|---|---|---|---|
| pegasus g1 | `e576e9cd…` | `calibration-753f535a8d024727.json` (D1537 が「自己整合しない較正」とした record) | **active** (`env_contract_activations/00000001.json`、sha256 `6a44b5b117d95539406d4d08b5f0f558424306b248574b16d7f92c04aceec34d`) |
| pegasus g2 | `1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c` | `calibration-94a4b79fa31bba3c.json` (T-2288 C 群が rr50 で採用した record) | 登録済み・未発効 (D1484: 発効は「予算承認 → 床値正式測定 → 凍結世代の承認と pointer 発効 → 本項目」の末尾) |

契約は JSON artifact ではなく `orchestrator/campaign/env_contract.py` の registry と activation artifact で定義される。
**hash は 3 種あり混同しない** (段 3 レンズ B が独立に再計算し親と一致): source file の bytes sha256
(`292bbed314a6824e0618da83d1d94253f0290e4db0b3e509200a79221508bc9a`)、activation artifact の bytes sha256 (`6a44b5b1…`)、
契約の canonical JSON hash (`contract_sha256`、g1 `e576e9cd…` / g2 `1346c20b…`)。source hash 単独では active 世代を示せず、
activation hash 単独では契約の全 field を示さない。未発効の contract_sha256 は `env_contract.resolve_by_contract_sha256`
(`env_contract.py:901`) が「ever-active でない」として拒否する。

**attestation 用較正と動作点用較正は別の量である。** g1 で本走すると `execution_guard.py:601` が attestation profile の較正を
`contract.calibration_ref.sha256` (= 753f535a) に束縛するが、これは records / threads / workload の出所を別の accepted 較正
(5c836a22 / 94a4b79f / 2b7ba072) に置くことと機械的には矛盾しない (動作点側の照合は別処理)。ただし g1 の健全性 (D1537) を
保証するものではない。

**欄を埋めるために要るもの (順序 D1483 を満たした後):**

- (a) **B-4 本走の driver・site・tag の確定。** D1641 決定 3 が固定したのは床値測定の site (Pegasus 計算ノード gen_S) である。
  床値は「対象動作点で再実測」されるので、B-4 本走が別 site・別 tag なら floor 欄が対象動作点を指さなくなる — したがって
  Pegasus が整合する候補だが、一致要件から本走 site の指名済みまでは導けず、名指した裁定は現物に無い。
- (b) **契約の世代と artifact の同定。** 今の導出証拠は g1。発効版には、その時点で実際に有効な契約と整合する証拠 (source path +
  bytes sha256、activation path + bytes sha256、generation + contract_sha256) を併記し、世代・契約 bytes・activation が変われば
  記入前 / 発効前に再導出する。g2 発効 (D1484、床値正式測定の後) までに g1 の併記値は陳腐化しうる。g2 の登録を activation 済みと
  読まない (前方参照 pin にしない)。model snapshot 欄の陳腐化検査が env_tag 欄にも実装済みとは書かない。
- (c) **確認者の担当範囲。** identity は thawk105 (D1266 / D1641 決定 1)。D1641 決定 1 の 3 者は床値の手続き用であり、D1483 が
  「§5 の他欄を解禁しない」と明文化している。未確定なのは今回 2 欄の確認まで AI 委任を及ぼすかであり、新規人物の指名ではない。
  §5.1 の「確認者を発効版へ併記」は明示要件で、code からは自動適用を証明できない。
- (d) 併記の形は裁定不要。§0 は値セルに説明文・条件を禁じるが、確定値の `key=value; ` 複合値は対象 driver 欄 (`記入者 =
  レビュー者 = thawk105 (D1266、D1638)`) と model snapshot 欄 (固定文法) に先例がある。実走前検査 (`p3_b4_admission_record.py:663`)
  は改行や `|` を含まない複合値・複数 sha256 を拒否しないが、path 実在・hash 一致・設定への適用・確認者の授権は検査しない —
  機械検査の通過を意味的充足の根拠にしない。
- (e) **live 判定の要否。** site が既決なら login からの静的導出 (site → tag → 契約) で「同じ resolver から機械導出」は満たせる
  (§5.1 は記入前確認を計算ノード上で行うとは定めていない)。live の site admission・単独性・将来の active 世代は証明しない。
  計算ノード上での `current_site() = PEGASUS_COMPUTE` は B-4 本走の起動時に driver 自身が行う。本 wave は dispatch していない。

## 既裁定との関係

| 裁定 | 本題への効き |
|---|---|
| D1483 / D1510 | §5 全欄の記入は床値の鎖 (12 行裁定・測定・採用裁定) の後。**今日の記入を塞ぐ第一の理由** |
| D1641 決定 1〜3 | 3 者は床値用。env_tag は resolver から機械導出、PerfConfig は calibrator の出力を採り AI が承認 — いずれも床値の凍結 12 行 |
| D1812 (c) / §11.1 追記 | 「校正済み PerfConfig の承認と成果物の採用裁定を同じ委任の下で AI が行う」は床値の文脈 |
| D2088 / D2089 / D2090 | 床値 spec の perf_config と較正の選択。reps=5 は AI 選択で床値 spec 用 |
| D1854 | §5 PerfConfig 欄の 1 セルは意味上の個数を固定しない (3 較正 pin を置ける) |
| D1484 / D1537 | g2 発効は鎖の末尾。g1 の calibration_ref は自己整合しない較正 |
| D1060 | 2026-08-27 時点では較正が無く記入できなかった。較正 3 件は以後に取得され、値の側は前進した |
| D924 | 器具は対象と同じ pin・同じ env contract で走らせる。env_tag は literal で写さず resolver から引く |

## 裁定パッケージ (ユーザーへ返す。本 wave では何も実装・記入しない)

**既裁定で閉じる (返さない):**

- 記入の順序 — D1483 / D1510 (§5 全欄は床値の鎖の後)。g2 発効の順序 — D1484。本 precheck を理由に前倒しを求めない。
- 床値の担当者・床値用 PerfConfig の承認・床値 3 cell と較正の選択 — D1641 / D1812 (c) / D2088〜D2090。再裁定へ返さない。
- 複数較正を 1 セルに置けること・確定値の複合表記・部分記入禁止 — D1854 / §0 / 対象 driver 欄と model snapshot 欄の先例。
  書式案は AI が作る。

**返す (いずれも順序 D1483 が解けた後に効く。今日の記入を求めるものではない):**

1. **B-4 本走の driver・site・tag の確定。** 床値の D1641 決定 3 と区別して、B-4 本走の site を Pegasus 計算ノード (gen_S) と
   確定するか。推奨: 確定する (床値が対象動作点で測られる以上、別 site・別 tag では floor 欄が対象動作点を指さない)。導出記録には
   対象 checkout と base の実際の resolver 経路 (literal 写像) を残す。
2. **B-4 用 `PerfConfig` の採用範囲と承認主体。** 3 較正の出力値 (records 1M / 1M / 2M、threads 48、workload 3 key 逐語) を
   採ること、取得構成から復元した extime=3 / `ycsb_max_ope=10` を採る読み、B-4 用 reps (候補 5 — `PerfConfig` 既定・床値 spec と
   同値、**AI 候補**) の承認。推奨: D1641 決定 3 と同型の委任 (thawk105 名義で AI が承認し D に残す) を B-4 本走の PerfConfig へ
   明示的に拡張する。「reps=5 でよいか」だけに縮めない (復元値・選択値の位置付けを含める)。
3. **確認者・記入者の担当範囲の追加。** identity は thawk105 (D1266 / D1641)。未確定なのは、今回 2 欄の確認・記入まで AI 委任を
   及ぼすか。推奨: 及ぼす (新規人物の指名でも床値担当の再裁定でもない)。実走認可は含めない。
4. **環境契約の artifact の読み。** 併記候補 = `orchestrator/campaign/env_contract.py` (path + bytes sha256)、
   `orchestrator/campaign/env_contract_activations/<serial>.json` (path + bytes sha256)、generation + contract_sha256。発効時点の
   active 契約と照合し、世代・契約 bytes・activation が変われば記入前 / 発効前に再導出する。推奨: この 3 種併記を採る。
   新 producer は前提にしない。

**次の一手候補 (裁定ではなく実装 T の候補。本 wave では開かない):**

- 承認済み `PerfConfig` を base CLI が消費する経路 (`p3_s4_loop.py:2745` の `default_perf()` 無条件使用の差し替え)。§5.1 の
  「差し替え」の実体。専用 producer の新設が必須という意味ではない。
- literal 写像 (`p3_s4_loop._SITE_ENV_TAGS`) と registry 属性 (`lookup_required_attestation_contract`) の二重定義の解消 —
  恒久一致を求めるなら。

## 段 3 敵対相談と段 4 裁定

軽量版 (docs-only) だが、事前登録の解除条件と既裁定の読みが本題そのものなので、段 3 相当の敵対相談を 2 レンズ (read-only codex、
`reasoning=medium`、`--lane luna` × 2、レンズの違いは prompt 本文) で回した。plan と実装子は無い。所見 20 件 (A1〜A10、B1〜B10)
の判定と反映は `verbatim/stage4-ruling.md` に置く。要点:

| 所見 | 判定 | 反映 |
|---|---|---|
| A1 「D1483 以後改訂なし」は広すぎる | real | 「この 2 欄の記入順序を解除する後続裁定は無い」に限定 |
| A6 確認者の不足は identity でなく委任の担当範囲 | real | 裁定パッケージ 3 を「担当範囲の追加」へ改めた |
| A7 / B4 契約の世代と hash 3 種の区別 | real | 欄 2 の記述と裁定パッケージ 4 を改めた |
| A8 複合セルの書式は裁定不要 | real | 裁定パッケージから外した |
| B1 literal 写像と registry 属性の同値は現世代限り | real | 欄 2 の表と次の一手候補に記した |
| B2 compute 分類は `bnode*` hostname | real | 親の記述を訂正 |
| B7 較正からの供給と B-4 CLI への供給経路は別 | **real (親 brief の落ち)** | 結論 2 と欄 1 に追加。実装 T の候補 |
| B8 3 key workload は完全な PerfConfig ではない | real | 欄 1 に組み方の要件を追加。4 key 検査の発火は performance verify mode に限ると限定 |
| A2 / A3 / A5 / A9 / A10 / B3 / B5 / B6 / B9 / B10 | refuted (親の読み・実測を維持) | 反論不成立、または親と一致 |

親の較正値・sha256・契約世代・key 再計数は両レンズが独立に再現し、誤りは見つからなかった (静的検査。pytest・測定・記入は行っていない)。

## 本書が閉じないこと

- §5 の 2 欄の記入そのもの (D1483 の順序が解けるまで着手しない)。
- 床値 (A-5) と campaign 起動 (順序 (3)) — 依頼の範囲外。
- 計算ノード上での live な site 判定の再実測 — 本 wave は login からの静的導出だけを行った。
- 前 wave README が挙げた 12 field の不足のうち `calibrated_workload_member` / `reference_*` は、2 欄を記入しても
  precursor へ結合する証拠が別に要る (前 wave の所見どおり)。2 欄の記入はその必要条件であって十分条件ではない。

## 収録物

| file | 内容 |
|---|---|
| `verbatim/stage1-brief.md` | 親の段 1 brief (P1〜P5 の攻撃対象) |
| `verbatim/stage3-lens-a-rulings.md` | 段 3 敵対相談 (裁定整合と実効性) |
| `verbatim/stage3-lens-b-derivation.md` | 段 3 敵対相談 (機械導出の正しさと現物の再計数) |
| `verbatim/stage4-ruling.md` | 親の段 4 裁定 (所見の real / refuted、裁定パッケージ) |
| `verbatim/parent-resolver-and-calibration-probe.txt` | 親の実測 (resolver 導出・契約世代・較正 key・取得 argv・PerfConfig 型) の逐語 |

### 逐語の可逆最小正規化 (`git diff --check` 抵触分、可視文字不変)

| file | 原文 sha256 | 原文 bytes | 正規化後 bytes | 復元法 |
|---|---|---|---|---|
| `verbatim/stage3-lens-a-rulings.md` | `418dc8aa23eff1b63f6a993aec13aef218ac067a95b61427ca907450e8ad9d5b` | 10,228 | 10,226 | 行 44 (空白 2 個だけの行) の空白 2 個を除去。行 44 に空白 2 個を戻す (原文は job dir `wave/stage3-lens-a.md`) |
| `verbatim/parent-resolver-and-calibration-probe.txt` | `71a48ac3d844c512c4ff74432908d90f6ade78c56583417094e368ae32c74f36` | 8,355 | 8,354 | 末尾の空行 1 行 (`\n\n` → `\n`) を除去。末尾に `\n` を 1 つ戻す |
