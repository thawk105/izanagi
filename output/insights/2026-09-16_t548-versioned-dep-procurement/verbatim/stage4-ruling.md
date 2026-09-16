# 段 4 裁定 — [T-548] gflags / glog の versioned な共通調達経路

親 (claude) が段 2 plan と段 3 の 2 レンズ (sol = 正しさ境界 / luna = 実効性・scope) を裁定した。
**本文書が plan v2 である。** 実装子はこの文書を正本とする。

---

## 0. 結論

**両レンズの核心所見を real として採る。段 2 plan の「1 consumer だけ結線し残りを T-585 へ残す」は
不採用。** 代わりに、**機体固有の絶対 path を repo から消し、versioned な調達経路を唯一の経路に
する**。旧経路を残す入口 (`--include-build-deps` のような opt-in) は作らない。

理由は 3 つ。

1. **旧経路を残す案は D1737 の明示的却下に当たる。** sol A7 と luna §3 が独立に同じ結論へ到達した。
   逐語は「floor 系が既に policy 経由で運んでおり、**同じ依存を 2 つの経路で pin することになる**」。
   pin 値の単一正本化では解消しない。記述は「経路」の併存を禁じている。
2. **T-548 の裁定は「[T-585] と同じ面なので同一 wave で閉じる」と書いている。**
   [T-585] の本文は「依存 source の所在を機体固有の絶対 path で repo に書く**結合そのものの除去**」
   である。tool の対象を広げるだけでは、旧 key を読む live consumer が残る限り結合は消えない。
3. **「裁定へ返す」は採らない** (ユーザーの恒久指示)。段 3 の 2 レンズで攻めさせた結果をもって
   親が決める。

### やらない理由の最も強い形 (記録)

**約 19 本の live job body を、この wave では実走で検証できない。**
`floor_campaign.sh` / `certify_calibration.sh` / `t126_qualification.sh` は計算ノード job の本体で、
正直な検証は計算ノード走行しかない。それを 19 本分は行えない。

この反論を退ける根拠:

- **失敗は fail-closed で大きい音を立てる。** 依存 source が無ければ configure は 0.31 秒で
  `Could NOT find gflags` で止まる (job 998862 の実測)。黙って誤った数値を出す経路ではない。
- **新しい入力を各 consumer へ足さない設計にする** (下記 2.3)。既定の staging root は
  `silo_ladder_rung1.py:943-946` で既に **repo 相対** (`output/env/pegasus/silo_ladder_rung1/
  job-staging/thirdparty-src`) に解決される。submit wrapper の argv も PBS の env allowlist も変えない。
- **各 job body は既存の静的契約テストが守る。** 変更の形はすべて同一なので、契約テストの更新も同型。
- **半数は既に hydrate 済み source root を受け取っている** (`certify_calibration.sh`、
  `mocc_trace_pilot.sh`、`p3_s4_loop_pegasus.sh`、`silo_ladder_rung1.sh`、`s3_mocc_lock_coverage.py`、
  `silo_ladder_rung1.py`、probes 2 本)。それらは同じ root に名前が 2 つ増えるだけである。

---

## 1. 所見の裁定

### 1.1 採用 (real)

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| R1 | sol A7 / luna §3・§5 | 旧経路併存は D1737 の却下に当たり、裁定の「同一 wave」にも反する | **real・採用。** scope を全 live consumer の付け替えへ拡張する |
| R2 | luna §6 | **[T-2625] は既に成立している** (job 999363、bnode001、`overall=true`、59 checks)。親 brief の「止まっている」は誤り | **real・採用。** brief を訂正する。下記 1.3 |
| R3 | luna §1 実測 2 | 残骸 prefix (`libgflags.a`) で通ったことは、新経路が建てる prefix で通ることを証明しない。finder は library と header を別々に探す | **real・採用。** 生死証拠は fresh prefix で library と header **双方の解決先**を記録する |
| R4 | luna §1 実測 3・4・7 | registry 件数・source の現存・DNS 成功は、その時刻・環境の観測にすぎない | **real・採用。** brief の断定を観測として書き直す。とくに「名前解決が通る」は「clone が通る」を含意しない |
| R5 | sol A1 | hydrate 時の強い検証と、job が使用直前に行う検証 (directory・HEAD・porcelain だけ) の受理集合が一致しない | **real・採用。** 新 2 依存の引渡し境界で `_verify_source` 相当を適用する |
| R6 | sol A2 | `submission._dependency()` は expected commit の object を解決するだけで、checkout の HEAD と dirty を検査しない | **real・採用。** 「同等検査」として数えない。brief の記述を訂正 |
| R7 | sol A3 | 不正 pin の変異は `_dependency_pins()` が先に拒否するため、新列挙の検出力に帰属しない | **real・採用。** 変異は url 側と列挙側へ再照準する (下記 4) |
| R8 | sol A4 | 「cache の ignored artifact が hydrate へ混入しない」は fresh clone が構成上運ばないので恒真 | **real・採用。** この候補を登録しない |
| R9 | sol A5 | job 側の拒否検査を上流から通すと cache/hydrate が先に拒否して到達しない | **real・採用。** job 側の変異は正常 hydrate 後の引渡し境界へ投入する |
| R10 | sol A6 | golden の導出手順が未確定で、実装子が作った bytes を親が後追いで承認する形になりうる | **real・採用。** 親が**実装前に**期待 bytes と sha256 を確定した (下記 2.2) |
| R11 | luna §4 | 「実 consumer の使用証拠」には計算ノードが要る。job は `bnode` 以外と `.claude/worktrees/` を拒否する | **real・採用。** 完了条件から「実 consumer の job 走行」を外し、下記 3 の形にする |
| R12 | luna §7 | 「密結合なので素集合に割れない」は成立しない。調達 / consumer / 統合に割れる | **real・採用。** 3 単位へ分ける (下記 5) |
| R13 | luna nit 3 | finder は探索後に cache 変数を `unset` するので、証拠を `CMakeCache.txt` だけに頼れない | **real・採用。** configure の stdout (`-- Found gflags: <path>`) を証拠とする |

### 1.2 部分採用

- **sol §4 の T-126 preimage** — 「policy.json へ key を足すだけで旧 preimage の継続が拒否される」は
  real。ただし **D200 が同じ影響を明示して受理済み**である (「旧 policy で作った preimage / receipt を
  新しい checkout で継続すると fail-closed になりうる」)。**先例どおり受理し、過去成果物は
  書き換えない。** brief の不変条件「名指し外 consumer の受理・拒否不変」は過大だったので、
  「**新 series identity は変わる (D200 の先例)。過去の成果物・歴史 binding は書き換えない**」へ訂正する。
- **sol §4 の T-316 receipt** — `output/env/pegasus/t316-sandbox-backend/0:999027.nqsv/receipt.json` に
  現行 SHA が残る。**更新対象に含めない** (過去 probe の実行入力の記録である)。

### 1.3 親 brief の訂正 (親自身の誤り)

1. **「`fetch_third_party.py` の命令は 3 つ」は誤り。** 4 つ (`fetch` / `hydrate` / `verify` /
   `verify-deps`、`:702`)。
2. **「段 4 loop は供給経路が無くて止まっている」は誤り。** `p3_s4_loop_pegasus.sh:409-463` に
   依存 build prologue が既にある (D1737 の対応は着地済み)。残る問題は locator だけである。
3. **「[T-2625] が止まっている」は誤り。** 成立している (job 999363)。
   **正しい研究前進の書き方はこう** — [T-2625] を通したのは、親が policy pin の source から
   gflags/glog を手で建て `env CMAKE_PREFIX_PATH=...` を generic argv に載せた**一回限りの回避**で
   ある (`output/insights/2026-09-15_t2625-sealed-snapshot-qualification/README.md:68`)。
   **これは 2026-08-16 の裁定が択 (c)「probe ごとの env seam」として却下した形そのもの**で、
   同 insight 自身が「事前検査は本番と同じ finder で行う」と書いている。
   本 wave は、その回避を恒久の共通経路へ置き換える。
4. **「28 file」は根拠にしない** (検索条件が再現しない)。編集対象は下記 2.4 の実名で確定する。

### 1.4 不採用 (refuted)

なし。段 3 の所見はいずれも real として採った。段 2 plan の推奨 (1 consumer 結線 + opt-in 入口) だけを
不採用にした。

---

## 2. plan v2

### 2.1 設計

**versioned な調達記述を共有 policy に置き、機体固有の絶対 path を repo から消す。**

- `tools/pegasus/policy.json`
  - `gflags_source_path` → `gflags_source_url` = `https://github.com/gflags/gflags.git`
  - `glog_source_path` → `glog_source_url` = `https://github.com/google/glog.git`
  - `gflags_expected_head` / `glog_expected_head` は**そのまま**。pin の正本は 1 つのまま。
  - `silo_ladder_rung1.dependency_pins` も**そのまま**。
- `tools/pegasus/fetch_third_party.py`
  - gflags / glog を **既定で** cache / hydrate の対象に含める。opt-in flag を作らない。
  - 列挙は FetchContent 3 本とは**別の権威**にする。`silo_ladder_rung1.third_party_policy()` は
    `ThirdParty.cmake` との literal 同期を要求するので、そこへ 2 本を足してはならない
    (`silo_ladder_rung1.py:875-930`)。新しい小さい列挙関数が policy の
    `*_source_url` / `*_expected_head` から `{name, source_name, url, pin}` を作る。
    url は既存 3 本と同じ規約 (`https://github.com/` 前置・`.git` 終端・pin は 40 hex) を課す。
  - `verify-deps` は**廃止する**。旧 locator を検証する命令であり、旧経路そのものである。
    その検出力 (HEAD 一致) は新 cache 経路の `_verify_source` が既定で `allow_shallow=False` の
    まま担う — **これは強化であって弱体化ではない** (旧 `verify-deps` は
    `expected_url=None` / `allow_shallow=True`、`:686-692`)。
- **consumer** は全員、source の所在を「hydrate 済み third-party source root 配下の
  `gflags` / `glog`」として解決する。新しい argv も新しい env も足さない。
  既定 root は `silo_ladder_rung1.THIRD_PARTY_STAGING_RELATIVE`
  (`output/env/pegasus/silo_ladder_rung1/job-staging/thirdparty-src`) で、
  `IZANAGI_THIRDPARTY_SOURCE_ROOT` による上書きは既存どおり効く。

### 2.2 policy.json の golden — 親が実装前に確定した (D200 / sol A6)

**実装子はこの 2 行だけを書き換える。他の byte を変えてはならない。**

- 変更前 bytes の sha256 = `a8806c4a4da81f2cbadcb5cbeee54ce7c1106bd0d291c1a2725f86b8b8a8032a`
  (現行 `EXPECTED_CURRENT_PEGASUS_POLICY_SHA256` と一致)
- 変更 (行 15 と行 17、前後の空白・末尾カンマを含めて逐語):

```
-  "gflags_source_path": "/work/SFC/tanab/github/gflags",
+  "gflags_source_url": "https://github.com/gflags/gflags.git",
-  "glog_source_path": "/work/SFC/tanab/github/glog",
+  "glog_source_url": "https://github.com/google/glog.git",
```

- **変更後の期待 sha256 = `3a3c7d607de77e23368f9ce382b41e6e524de3ee1e2809e7c6d890ada95a6c90`**
  (親が変更前 bytes に上記置換だけを適用して算出。実装子は編集後 file から算出してはならない)
- `orchestrator/tests/pegasus_policy_expected_goldens.py` の
  `EXPECTED_CURRENT_PEGASUS_POLICY_SHA256` をこの値へ更新する。
- `EXPECTED_HISTORICAL_PEGASUS_POLICY_SHA256` (`b1c42e49…`) は**変更しない**。
- 凍結 evidence (`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` 等)、
  過去の receipt (`t316-sandbox-backend/0:999027.nqsv/receipt.json` を含む) は**変更しない**。

### 2.3 consumer の付け替え — 対象の実名

`gflags_source_path` / `glog_source_path` を読む tracked file を全件付け替える。
**shell の付け替えは、policy から絶対 path を読む 1 箇所を、staging root 配下の名前の解決へ
置き換えるだけにする。** HEAD 照合・dirty 拒否・build/install・prefix 供給の既存検査は**残す**。

- shell / pbs: `a5_second_boot_backoff_sweep.sh`、`b10_backoff_grid.sh`、`certify_calibration.sh`、
  `floor_campaign.sh`、`floor_scoping.sh`、`mocc_trace_pilot.sh`、`oracle_n_pilot.sh`、
  `p3_s4_loop_pegasus.sh`、`paper_story_a1_paired.sh`、`silo_ladder_rung1.sh`、
  `t126_qualification.sh`、`t141_region_profile.sh`、
  `probes/t1683_rr5_cost_probe.pbs`、`probes/t2187_adaptive_const_probe.pbs`、
  `probes/t2228_driver_gate_liveness_probe.pbs`
- Python: `orchestrator/campaign/s3_mocc_lock_coverage.py`、
  `orchestrator/campaign/silo_ladder_rung1.py`、`orchestrator/qualification/identity.py`、
  `orchestrator/qualification/submission.py`
- data: `tools/pegasus/mocc_trace_v1_policy.json`
- docs: `tools/pegasus/README.md` (新しい準備手順。旧 locator と 3 source を説明する
  `:336-346` も対象 — luna nit 2)

**実装子が上記に無い読み手を見つけたら、勝手に広げず報告して止める。**

### 2.4 やらないこと

- `external/ccbench/` の改変 (D1737 が `find_package` の optional 化を却下済み)。
- fallback・互換層・env の逃がし道・旧経路を選べる入口。
- 仮想リスク向けの gate・検査・台帳・一般化 (D1736)。
- 過去成果物・歴史 binding・凍結 evidence の書き換え。
- 汎用 dependency framework 化。対象は gflags / glog の 2 本に固定する。

---

## 3. 完了条件 (生死証拠)

**計算ノード job の走行は完了条件に含めない** (R11)。次を login node で取り、insight へ逐語で残す。

1. 新経路で `fetch` → 永続 cache に `gflags` / `glog` が pin どおり入る。HEAD を記録。
2. `hydrate` → staging root に 5 本が並ぶ。5 本の HEAD を記録。
3. hydrate した gflags / glog から **fresh な build / install** を行い prefix を作る
   (残骸 prefix を使わない。`CMAKE_PREFIX_PATH` を明示的に空から組む)。
4. **本番と同じ finder で実 CCBench configure を通す。** 証拠は configure の stdout の
   `-- Found gflags: <path>` / `-- Found glog: <path>` と、その path が 3 の prefix 配下であること。
   **library と header の双方**が新 prefix から解決されたことを示す (R3、R13)。
   `~/.cmake/packages` の残骸から解決していないことを、path の一致で示す。
5. 否定側の対照 — prefix を与えない同じ configure が
   `Findgflags.cmake:9` → `CMakeLists.txt:33` で rc=1 になること。

**この証拠の射程を限定して書く。** 「login node の 1 時刻・1 host で、この pin・この build option・
この install layout で成立した」。計算ノードでの job 完走、driver 本走、T-2625 の再取得、
walltime 充足はいずれも**含意しない** (R4)。

---

## 4. 変異の事前登録 (DW-M01)

実装前に登録する。各変異は位置と、同じ入力を拒否する層が前後にも内側にも無いことを
**実装後に確認**する。確認できなければ登録を外し、実効 gate へ再照準する (DW-M02)。
期待 node は完全集合とし、同形式へ正規化した記録 node との完全一致だけを KILLED とする (DW-M08)。

| ID | 位置 | 変異 | 期待 | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | 新列挙関数の url 検査 | `.git` 終端の要求を外す | KILLED | `_dependency_pins()` は url を見ない (`silo_ladder_rung1.py:850-866`)。既存 3 本の検査は別関数。前段でマスクされない |
| M2 | 新列挙関数の pin 検査 | 40 hex の `fullmatch` を `search` へ緩める | KILLED | 同上。pin 形式の検査は新関数にしかない |
| M3 | 新 cache 経路の `_verify_source` 呼出し | `allow_shallow=True` を渡す | KILLED | 旧 `verify-deps` を廃止済みなので、shallow を許す層は他に無い |
| M4 | `fetch` / `hydrate` の対象列挙 | gflags を対象から落とす (4 本にする) | KILLED | 列挙は 1 箇所。落とせば staging に現れない |
| M5 | consumer 1 本 (`p3_s4_loop_pegasus.sh`) の source 解決 | staging root 配下でなく `$HOME` 配下の固定 path を指す | KILLED | job body の静的契約テストが fragment と順序を pin する |
| M6 | `pegasus_policy_expected_goldens.py` | `EXPECTED_CURRENT_PEGASUS_POLICY_SHA256` を旧値に戻す | KILLED (診断でなく受理集合) | policy bytes の照合 2 node が直接読む |
| M7 | 引渡し境界の検証 (R5 の是正箇所) | 新 2 依存の使用直前検証を削る | KILLED | 正常 hydrate 後に境界へ注入するので上流は拒否しない (R9 の設計) |

**登録しない候補** — 「cache の ignored artifact が hydrate へ混入しない」(R8、fresh clone が構成上
運ばないので恒真)、「列挙名が gflags / glog の 2 つである」(R9、固定 2 名列挙では構成上成立)、
不正 pin を共有 `*_expected_head` 側で壊す変異 (R7、`_dependency_pins()` が先に拒否)。

---

## 5. 並列分割 (R12)

編集 path が素集合になる 3 単位。**A を完了させてから B と C を並列投入する** (B・C は A が
定める解決 API に依存する)。

| 単位 | 所有 path |
|---|---|
| **A 調達** | `tools/pegasus/policy.json`、`tools/pegasus/fetch_third_party.py`、`orchestrator/tests/test_pegasus_thirdparty_fetch.py`、`orchestrator/tests/pegasus_policy_expected_goldens.py` |
| **B shell consumer** | `tools/pegasus/*.sh`、`tools/pegasus/probes/*.pbs`、`tools/pegasus/mocc_trace_v1_policy.json`、`tools/pegasus/README.md`、および対応する `orchestrator/tests/test_p3_s4_loop_job_contract.py` / `test_pegasus_tools.py` / `test_pegasus_floor_tools.py` / `test_paper_story_a1_job_contract.py` / `test_backoff_extended_sweep.py` |
| **C Python consumer** | `orchestrator/campaign/s3_mocc_lock_coverage.py`、`orchestrator/campaign/silo_ladder_rung1.py`、`orchestrator/qualification/identity.py`、`orchestrator/qualification/submission.py`、および `orchestrator/tests/test_t126_pegasus_tools.py` / `test_silo_ladder_rung1_evidence.py` / `test_silo_ladder_rung1_driver.py` |

B と C で同じ test file を触る必要が出たら、その file は **C の所有**とし、B は報告して止める。

---

## 6. 不変条件 (訂正版)

- **規律 2 を緩めない。** HEAD 完全一致・dirty 拒否・fail-closed は新経路でも同等以上。
  既存テストの期待値を反転・緩和・skip・削除しない。赤なら実装側が誤り。
- 事前検査は**本番と同じ finder**で行う。最小 cmake project の config mode probe を証拠にしない。
- `external/ccbench/` を改変しない。
- 過去成果物・歴史 binding・凍結 evidence を書き換えない。
- policy bytes の golden は**親が与えた値**を使う。編集後 file から算出しない。
- **新 series identity と新 campaign binding は変わる。** これは D200 が先例として受理済みの影響で
  あり、本 wave はそれを追認する。旧 preimage を新 checkout で継続する試行は fail-closed になる。
