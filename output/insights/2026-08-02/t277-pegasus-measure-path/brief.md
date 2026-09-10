# 段 1 brief — [T-277] Pegasus 計測パスを開く

**確定済みユーザー裁定 (worklog (102) / archive (96) 択一 2 = (a) 採用):**
`_site_admits_measurement` の Pegasus 拒否を D96 手続で開き、build identity を是正し
(compiler realpath/version・CMake 版・dependency prefix・site・env contract)、`/scr` へ fresh
namespace を切る。**8c は Pegasus 側の厳しい隔離契約 (attestation required / single_process /
allow_resume=false) に従わせ、linux-baremetal の緩い側へ寄せない。**
運用制約 (command 引数): P2、A と並行可、**land は [T-276] の後**。

## scope と成果物影響 (DW-G05)

- **S1 受理集合**: `p3_s4_loop_trigger_gating._site_admits_measurement` を `PEGASUS_COMPUTE`
  だけ受理へ広げる (LOGIN/SUSPECT は拒否のまま)。D96 手続 = 新 D + 境界テスト同時更新。
  *未実装なら*: live 計測が構造的に不可能で、Pegasus 由来の実測値が certified 選択の材料に 1 件も入らない。
- **S2 env 契約の site 解決**: driver 固定の `ENV_TAG="linux-baremetal"` (`:76`) を site 由来解決へ。
  compute → registry の `pegasus` 契約 (clk=2100 / numactl=() / attestation required /
  single_process=True / allow_resume=False)。
  *未実装なら*: Pegasus の数値が `env_tag="linux-baremetal"` として台帳に載り、別環境値と混載して
  レポートの比較が不能になる (規律「計測層の値だけ・環境タグ付き」に抵触)。
- **S3 build identity**: `loop.run_campaign` → `pipeline.evaluate` へ `env_contract` を通し、
  admit された Pegasus 経路を `build_v2` (contract namespace + toolchain manifest) にする。
  v2 pre-image へ **dependency prefix と site** を追加し、configure へ `-DCMAKE_PREFIX_PATH` を渡す。
  `pipeline.py:579-580` の `DEFAULT_CC/CXX`(gcc-13) 固定も site 解決へ (Pegasus に gcc-13 は不在)。
  *未実装なら*: legacy `cache_key` (`buildcache.py:121-135`) の貧弱な pre-image により別環境 cache が
  同 key で hit し、台帳の数値と実バイナリが食い違う (D108 決定 5)。
- **S4 `/scr` fresh namespace**: compute では cache_root を `/scr/<job>` 配下の fresh namespace にする。
  *未実装なら*: 共有永続領域の cache が跨ジョブで再利用され、build 起源と単独性が台帳から読めない。
- **S5 8c 隔離契約**: 計測前に `attestation_mode=="required"` を実発火させ、`single_process` /
  `allow_resume=False` を強制する。
  *未実装なら*: attestation なしの数値が proof chain に載り、受入が恒真な保証になる。

## 不変条件 (緩めない)

- `env_contract.py` の registry と `contract_sha256` を変えない (凍結 bytes 0 変更、pin 閉包は S3 で再確認)。
- LOGIN/SUSPECT の重処理拒否・`buildcache._run` の site gate を緩めない。
- OTHER site の既存 legacy 経路 (cache key・build namespace・受理集合) を変えない。
- verifier / diff 検疫 / auditor gate / 構文契約 grep を一切緩めない (規律 2・3)。
- push しない。land は共通段 9 operation のみ、かつ [T-276] land 後。

## 親の provisional 裁定 (= 攻撃対象)

- **(P1)** S3 の「build identity 是正」は legacy `cache_key` の pre-image 拡張ではなく **v2 経路への
  routing** で満たす。根拠: D108 決定 (5) 自身が「v2 (`_v2_identity`) は `toolchain_manifest_sha256`
  を持つので同じ穴ではない」と書く。裁定文の字面 (「cache key pre-image へ入れる」) との差はここ。
- **(P2)** S1 の受理は `PEGASUS_COMPUTE` のみ。LOGIN/SUSPECT は拒否のまま。
- **(P3)** 生死確認 (DW-G01) は既存 artifact を根拠とし、使い捨て driver を作らない —
  `tools/pegasus/certify_calibration.sh:494-517` が compute node で gflags/glog を `/scr` に build し、
  `-DCMAKE_PREFIX_PATH=<gflags>;<glog>` + system gcc realpath で CCBench `ycsb_silo.exe` を build 済み。
- **(P4)** D108 の残 blocker (i) `PIN` 不一致・(ii) 依存 staging の自動化・(iv) `default_perf` の
  Pegasus calibration は **scope 外** (裁定文が挙げていない)。S3 の dependency prefix は
  「外から与えた prefix を identity と configure に通す」までで、Python が gflags/glog を build しない。

## 前提実測 (brief 前、DW-S01)

- 現在地 `pegasus02` = `PEGASUS_LOGIN`。`_site_admits_measurement` は OTHER のみ True、
  COMPUTE/LOGIN/SUSPECT すべて False (実行して確認)。
- `loop.run_campaign` は `evaluate(...)` を `env_contract` なしで呼ぶ (`loop.py:136-141`) → legacy build。
- `_v2_identity` (`buildcache.py:219-234`) の pre-image は genome/ccbench_commit/trace/src_token/cc/cxx/
  toolchain_manifest_sha256 のみ。**dependency prefix と site は入っていない。** toolchain manifest は
  cc/cxx/cmake の realpath + version 先頭行を持つ (`:176-215`)。
- `buildcache` に `CMAKE_PREFIX_PATH` の入力経路はゼロ (grep 0 件)。
- Pegasus login に gcc-13/g++-13 は不在 (`/usr/bin` は 9/11/12)。module にも gcc なし。
- 既存被覆 (純増検出力の分母): S1 の境界は `test_p3_s4_loop_trigger_gating.py:363-369` と AST 契約
  `:709-710` が固定済み。S5 の attestation は p3 経路に呼び出しがゼロ (grep: `env_attestation` の
  consumer は s8b 系のみ) = 純増。S3 の prefix/site は pre-image に無い = 純増。
- 凍結 pin 閉包: `contract_sha256` を pin する consumer は s8b oracle/floor と env_contract test のみで、
  registry を触らない限り不変。v2 build digest は cache namespace (repo 外) にしか現れない。

## 成果物の形

コード + テスト + 新 D (受理集合変更の D96 手続) + worklog + insights 逐語 + 変異台帳。

## 並列分割方針

所有素集合の 2 単位。**A** = `buildcache.py` / `pipeline.py` / `loop.py` (build identity・prefix・site・
cache_root)。**B** = `p3_s4_loop_trigger_gating.py` / `p3_autonomous_workload_trial.py`
(site 解決・受理集合・8c 隔離契約) + それぞれのテスト。B は A の signature に依存するため、
A を先行させて所有パス限定 patch を展開してから B を投入する。

## 受入・実測環境

受入全走は Pegasus gen_S 計算ノード (所在の正本は worklog)。login node で重処理を走らせない。
機体固有情報は `docs/pegasus-runbook.md`。
