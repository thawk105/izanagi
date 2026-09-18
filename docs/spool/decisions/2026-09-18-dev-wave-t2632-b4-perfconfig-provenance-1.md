---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-18
wave: dev-wave-t2632-b4-perfconfig-provenance
seq: 1
---

## {{D:b4-perfconfig-provenance}}. B-4 本走用 `PerfConfig` は較正の出力値・取得構成からの復元値・選択値の 3 種を出所で区別して固定し、site は Pegasus 計算ノード、環境契約は artifact 3 種を併記する — 第 22 回裁定の委任 (D1641 決定 3 と同型、thawk105 名義) の下で AI が確定し、§5 の記入は D1483 の順序後、実走認可を含めない

**決定 (第 22 回 /rulings 項 2 (2026-09-18、ユーザー「推奨通りで」) が D1641 決定 3 と同型の委任を B-4 本走の `PerfConfig` へ
明示的に拡張したことを受け、その委任の下で thawk105 名義で AI が確定):** B-4 事前登録 §5 の 2 欄 (校正済み `PerfConfig` /
env_tag) に将来書く値の**出所**を、結果を見る前に次のとおり固定する。本決定は値の出所を確定する裁定記録であり、§5 の記入・
床値の採用・本書の発効・実走の認可・B-4 の実施可否のいずれも変えない。裁定の正本は同日の rulings wave の決定 fragment
(fold 後に D 番号が付く) で、本決定はそれを名前で引く。

1. **site と tag (項 (1))。** B-4 本走の site は Pegasus 計算ノード (`site_policy.PEGASUS_COMPUTE`、queue gen_S)、env_tag は
   `pegasus`。床値の site を決めた D1641 決定 3 とは別の新規指定である。導出記録 (login node `pegasus02`、2026-09-18 JST、
   静的導出。計算ノードへの dispatch は行っていない):
   - **対象 checkout:** local main `24ede1d11cb33af8d2278cd6d48d29863225465b` (本決定を起草した worktree も同 SHA)。
   - **base の実 resolver 経路 (literal 写像):** B-4 の sanctioned 起動経路 `orchestrator/campaign/p3_b4_launcher.py` の
     `driver_kind == "base"` 枝が `p3_s4_loop._current_site()` (= `site_policy.current_site`。計算ノードの分類は hostname
     `^bnode[0-9]+$`) → `p3_s4_loop._admit_env_contract(site)` → literal dict `p3_s4_loop._SITE_ENV_TAGS`
     (`{site_policy.OTHER: "linux-baremetal", site_policy.PEGASUS_COMPUTE: "pegasus"}`) → `env_contract.lookup(tag)` の順で
     契約を引き、`_campaign_cfg_for_site` が同じ写像の tag を campaign config の `measurement_env` に書く。base driver の
     入口は解決済み site と契約の `env_tag` が同じ写像で一致しない場合を `ExecutionGuardError` で止める。Pegasus wrapper
     (`tools/pegasus/p3_s4_loop_pegasus.sh`) も `"$PY" -B -m orchestrator.campaign.p3_s4_loop` (`$PY` は同 script が選択・検査した
     Python 3.10) で base CLI を経るので解決は同じ。
   - registry 属性 `env_contract.lookup_required_attestation_contract()` は対象 checkout で `lookup("pegasus")` と同一 object を
     返す (同値は現世代限り。literal 写像と属性経路の二重定義は残り、本決定は解消しない)。
   - login からの導出は `current_site() = PEGASUS_LOGIN` を返す。計算ノード上での `PEGASUS_COMPUTE` 判定と単独性の admission は
     B-4 本走の driver 自身が起動時に行い、本決定はそれを証明しない。
2. **`PerfConfig` の 3 種 (項 (2))。** B-4 本走用 `PerfConfig` (`orchestrator/campaign/pipeline.py` の `PerfConfig`:
   `records` / `threads` / `workload` / `extime` / `reps`) の各項目を、次の 3 種の出所で区別する。承認の主体はいずれも本委任の下の
   AI (thawk105 名義) だが、**(c) は本決定では承認しない**。

   **(a) 較正の出力値 (calibrator の出力そのもの。本決定で採る):** accepted 較正 3 件 (いずれも tracked、`schema_version`
   `calibration/v2`、`quality.status = accepted`、`env_tag = pegasus`、`clocks_per_us = 2100`、`threads = 48`) から、workload ごとに
   `records` = `saturation.records`、`threads` = 48、`workload` = 較正の 3 key を**逐語** (`"0"` を `"false"` へ置換しない、D1854
   の exact 一致) で採る。

   | workload | `records` | `workload` (逐語) | 較正 (path / sha256) | 取得 job (allocation の証拠) |
   |---|---|---|---|---|
   | rr95 (read-heavy) | 1,000,000 | `{"ycsb_rmw": "0", "ycsb_rratio": "95", "ycsb_zipf_skew": "0.9"}` | `output/env/pegasus/calibration/registered/calibration-5c836a22eff9ab40.json` / `5c836a22eff9ab40cabb23cb597cd0b3c232979696c5784b6b3d358b92c789cc` | `0:995805.nqsv` (bnode027) |
   | rr50 (balanced) | 1,000,000 | `{"ycsb_rmw": "0", "ycsb_rratio": "50", "ycsb_zipf_skew": "0.9"}` | `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json` / `94a4b79fa31bba3c725bd9c18990ae60bea86dbcdb6eff19822a58a75fe5c5a9` | `0:892707.nqsv` (bnode048) |
   | rr5 (write-heavy) | 2,000,000 | `{"ycsb_rmw": "0", "ycsb_rratio": "5", "ycsb_zipf_skew": "0.9"}` | `output/env/pegasus/calibration/registered/calibration-2b7ba072b88023ae.json` / `2b7ba072b88023aecb4361781229bb5343dbfa489f4c7cc3dd8369c33bd3a067` | `0:478.nqsv` (bnode013) |

   これは床値 spec の 3 cell (D2089) と同じ 3 較正であり、値も同じである。本決定は再計算ではなく、B-4 本走用として同じ出所を
   採ることの確定である。較正 JSON には `extime` の key も反復数の設定 key も無い (`reps` の文字列は
   `acquisition_receipt.walltime.formula` の費用式 `sweep_reps(3)` / `noise_reps(10)` と、rr5 では同 formula の説明文にしか
   現れない。いずれも 1 測定の反復数を指定する field ではない)。

   **(b) 取得構成からの復元値 (較正の出力値ではない。本決定で採る。D2088 の復元限界を引き継ぐ):**
   - `extime = 3`。3 件の tracked な取得 argv (`output/env/pegasus/calibration/job-staging/<job>/calibrate-argv.json`、sha256
     `d66fb1e814675f0825749dddf7265262a8c1d0c52493e911b8c245784ebe0199` (0:995805) /
     `18f739a0a6c91cdb0b10cffe042851c93c447a5d19f819bbea88eb2e5261a5b9` (0:892707) /
     `a73d5f1c71a408b219e5746fafe2116b417dea49f1fbe7cac870c6094c866b80` (0:478)) に `--extime` が無く、calibrator CLI の既定は
     `--extime 3` (`orchestrator/calibrator/cli.py`)。runner は渡された extime を `-extime=<値>` として bench へ渡す。
   - `ycsb_max_ope = 10`。同じ argv の `--workload` は 3 key だけで、runner の固定 flags (`-thread_num` / `-ycsb_tuple_num` /
     `-extime` / `-clocks_per_us` + workload key) にも無いので、較正は CCBench の既定 `DEFINE_uint64(ycsb_max_ope, 10, …)`
     (`external/ccbench/include/ycsb.hh`) で走った。`PerfConfig.workload` は 3 key を逐語で保持し、4 key の exact 集合を要求する
     consumer (`pipeline.performance_correctness_workload`) へ渡すときにだけ `ycsb_max_ope = "10"` を加える。これは較正と同じ
     動作点を指すための復元値であって、較正の出力値でも 4 key 検査の一般発火の主張でもない。
   - **復元限界 (D2088 と同じ):** 現行 source と tracked argv による構成の復元であって、取得当時の source bytes まで検証した
     ものではない。

   **(c) 選択値 (較正にも取得構成にも無い。本決定では確定しない):**
   - `reps`。候補は 5 (`PerfConfig` の既定、床値 spec の D2088 と同値、median が実 rep を返す奇数) だが、**候補のままとし承認値に
     しない。** D2088 の `reps = 5` は床値 spec 用の AI 選択で、B-4 本走への転用はそれだけでは認可されない。確定は §5 記入の時点で
     本委任の下で AI が別の決定 (または本決定への追記) として行い、それまで候補を §5 にも実走にも使わない。CV や throughput を
     見て決める形は採らない (結果依存)。
3. **環境契約の artifact 3 種 (項 (4))。** env_tag 欄へ併記する環境契約の証拠は次の 3 種で、混同しない。対象 checkout での値:

   | 種 | path | 値 (対象 checkout `24ede1d11`) |
   |---|---|---|
   | registry source の bytes | `orchestrator/campaign/env_contract.py` | sha256 `292bbed314a6824e0618da83d1d94253f0290e4db0b3e509200a79221508bc9a` |
   | activation artifact の bytes | `orchestrator/campaign/env_contract_activations/00000001.json` | sha256 `6a44b5b117d95539406d4d08b5f0f558424306b248574b16d7f92c04aceec34d` (`activation_serial` 1、active = pegasus g1 + linux-baremetal g1) |
   | generation + contract_sha256 (canonical JSON hash) | registry `GENERATIONS["pegasus"]` | **g1 `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` = active** (`calibration_ref` = `calibration-753f535a8d024727.json`、D1537 が床値に使わないとした較正)。g2 `1346c20b5519be4b4d3aef19adc5a93ce2804ad4e0428dc5095635f54187ad1c` = **登録済み・未発効** (`calibration_ref` = `calibration-94a4b79fa31bba3c.json`。`env_contract.resolve_by_contract_sha256` は ever-active でないとして拒否する) |

   - source hash 単独では active 世代を示せず、activation hash 単独では契約の全 field を示さず、contract_sha256 単独では発効を
     示さない。3 種を併記する。
   - **再導出条件:** §5 記入前と本書の発効前に、その時点の active 契約 (activation chain の末尾) と上表を照合し、世代・契約
     bytes (`env_contract.py`)・activation (serial または bytes) のいずれかが変わっていれば 3 種を再導出して併記し直す。上表の値を
     前方参照の pin にしない。g2 の発効は D1484 の順序 (予算承認 → 床値の正式測定 → 凍結世代の承認と pointer 発効 → g2) で
     行い、**登録済みを発効済みと扱わない**。自動監視や拒否機構は足さない (裁定の逐語)。
   - **attestation 用較正と動作点用較正は別の量である。** 本走時の attestation は `execution_guard` が契約の `calibration_ref`
     (g1 では 753f535a) に束縛し、項 2 (a) の 3 較正は動作点 (records / threads / workload) の出所である。両者が別 file を指す
     ことは機械的には矛盾しないが、本決定は g1 の健全性 (D1537) を保証しない。
4. **担当範囲 (項 (3))。** §5 の 2 欄 (校正済み `PerfConfig` / env_tag) の確認・記入は、identity `thawk105` (D1266 / D1641
   決定 1) の名義で本委任の下の AI が行う。人物の再指名でも §5 全欄の一括解禁でもなく、実走認可を含めない。
5. **順序と不変条件。** (i) §5 の記入は D1483 / D1510 の順序 (床値の 12 行裁定・測定・成果物の採用裁定の後) を守り、本決定を
   理由に前倒ししない。本決定の時点で床値の測定 (A-5 の凍結 spec は D2138) と採用裁定は未了である。(ii) B-4 は適格な赤 precursor
   0 件で実施不可のまま (D1986 項 4)。本決定は実施可否を変えない。(iii) §5 の pin を実走 `PerfConfig` へ束縛する既存経路は無い —
   base CLI は `p3_s4_loop.py` で `default_perf()` (records 100,000 / threads 4 / extime 1 / reps 2) を無条件に使う。差し替えは
   別の実装候補であり、本決定は実装しない。(iv) 規律 2 は緩めない。

**理由:**
- 第 22 回裁定項 2 は「3 種を出所で区別し、D1641 決定 3 と同型の委任を明示的に拡張して確定する。結果を見る前に固定する。実走
  認可は含めない」と命じた。D1641 決定 3 の委任は逐語で「calibrator の出力を採り」であり、calibrator の出力に無い復元値と選択値は
  その外にあった (D2088 が「AI の選択であることを残す」と書いた理由)。本決定はその外側を、出所の種別ごとに明示して埋める。
- §11.1 が禁じるのは「AI が起草した候補値を無裁定の既定値として凍結へ入れる」ことであり (D2120 項 4 の読み)、新裁定の委任の下で
  出所を区別して確定・記録する形はそれに当たらない。`reps` を候補のまま置くのは、較正にも取得構成にも出所が無い値を「確定」
  の語で既定値化しないためである。
- 較正 3 件と復元値の現物 (sha256・field 値・argv・CLI 既定・CCBench 既定・契約世代・activation bytes) は precheck
  (`output/insights/2026-09-17/t2632-b4-s5-precheck/README.md`、段 3 の 2 レンズが独立再計算) と本決定の再実測で全項目一致した。
- site を Pegasus 計算ノードにするのは、床値が対象動作点で再実測される以上、別 site・別 tag では floor 欄が対象動作点を指さなく
  なるからである (precheck 欄 2 (a))。D1641 決定 3 は床値の site を定めただけで本走の site を導かないため、新規指定として書く。
- 環境契約を 3 種併記にするのは、hash が 3 種あって単独では世代・field・発効のどれかを示せないためである (precheck 欄 2、
  段 3 レンズ B が独立に再計算)。再導出条件を書くのは、g2 発効 (D1484) までに g1 の併記値が陳腐化しうるためで、model snapshot 欄の
  陳腐化検査が env_tag 欄にも実装済みとは主張しない。
- 対象 checkout と resolver 経路を残すのは、literal 写像と registry 属性の同値が現世代限りであり、後続が「どの checkout の
  どの経路で `pegasus` を導出したか」を再現できなければ §5.1 の「同じ site resolver から機械導出」を確認できないためである。

**却下した選択肢:**
- `reps = 5` を本決定で承認値にする — 出所の無い値を委任の名で既定値化する形で、裁定の「候補のまま」に反する。
- 復元値 (extime / `ycsb_max_ope`) を「較正の出力値」と記す — artifact にその field は無い (D2088)。
- 環境契約の証拠を contract_sha256 だけ、または source hash だけにする — 発効・全 field・世代のいずれかを示せない。
- g2 (`1346c20b…`) を「次に発効する世代」として前方参照で pin する — 登録を発効と読む形で D1484 に反する。
- 本決定と同時に §5 の 2 欄を記入する — D1483 / D1510 の順序に反する。
- 承認済み `PerfConfig` を base CLI が読む経路 (`default_perf()` の差し替え) を本 wave で実装する — 依頼は D 起草だけで、実装候補は
  別 wave。
- 出所照合の自動検査・台帳・gate を足す — 裁定の逐語 (併記書式は裁定不要、自動監視や拒否機構は足さない) に反し、依頼の scope
  (仮想リスク向けの gate・検査・台帳・一般化は scope 外) の外である。

**本決定が主張しないこと:** §5 の記入・本書の発効・実走の認可・B-4 の実施可否・床値の採用のいずれか。計算ノード上での live な
site 判定・単独性・将来の active 世代。取得当時の source bytes の検証。g1 契約の健全性。admission (`load_verified_calibration`)
の通過が意味する protocol・測定設定・対象集合の意味的一致 (D1696 の人手責任 9 項目のまま)。literal 写像と registry 属性の恒久
一致。base CLI が §5 の pin を読むこと。
