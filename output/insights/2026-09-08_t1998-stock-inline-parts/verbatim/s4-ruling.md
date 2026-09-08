# 段 4 裁定 — [T-1998] balanced stock-inline 対照の最小 3 部品

基準: worktree HEAD `c5754d1f4b3d915f2e55615e69674190f48c69a8`。
wave 開始後に main は 13 commit 進んだが、いずれも B-4 floor 系で本 wave の変更面に触れない。
新しい裁定 (D1758 / D1759) も T-1998 に関係しない。

## 1. 所見の real / refuted と採否

### レンズ A

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A-1 | 診断 build 拒否が effective な `BACKOFF_NOINLINE=1` を証明できない (genome に key が無いので「明示 1 が無い」は恒真) | **real** | **採用**。第 3 部品の受理条件を変える |
| A-2 | launcher の script digest と実 repository commit が consumer まで束縛されない | **real** | **採用**。第 2 部品と第 3 部品の両方に反映 |
| A-3 | gitlink の exact 比較が実物で成立しない (result/reservation は 40 桁、lock/WAL は `pin.CURRENT_PIN` の 7 桁) | **real** | **採用**。比較規則を分ける |
| A-4 | 「source patch identity」の比較 field が未定義。実 WAL では `src_token` が arm ごとに正当に異なる | **real** | **採用**。B-2 と同じ直し方へ統合 |
| A-5 | `pair-cardinality` は genuine producer 出力の上で発火しない | **real** | **採用**。検査は残すが冗長 gate と明記し、変異の証拠から外す |
| A-6 | reject が code 文字列だけで、規律 3 に必要な原因を残さない | **real** | **採用**。拒否ごとに field / expected / actual / 対象 arm を持たせる |

### レンズ B

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| B-1 | 既存 A-5 launcher は balanced 成果物を安定して作れない。同じ checkout から 2 job を出し、先に終わった job の `git worktree prune --expire now` が後続を壊す | **real** | **採用**。第 2 部品は純増あり。プランの「純増ゼロ」を覆す |
| B-2 | consumer の identity 条件が共通 field と arm 固有 field を混同している。環境契約 digest は result にも reservation にも無い | **real** | **採用**。A-4 と統合 |
| B-3 | `BACKOFF_NOINLINE=0` は計画した入力から証明できない | **real** | **採用**。A-1 と同一の所見 |
| B-4 | `result.json` と job 成功を同一視し、sibling failure receipt を見ていない | **real** | **採用**。拒否条件に足す |
| B-5 | official perf 登録簿と Pegasus 登録簿の閉包がプランから漏れている | **real** | **採用**。同じ変更単位で登録する |
| B-6 | `admit_replay_evidence()` の追加呼出しは受理集合を狭めない | **real** | **採用**。受理条件から外す |

### refuted / 不採用

- **refuted:** 「A-5 job body 自体を balanced 専用へ直す」。A-5 の受理集合を変える。契約テストが
  2 workload fan-out と global prune を正例として pin している
  (`orchestrator/tests/test_a5_second_boot_job_contract.py:273-371`)。**scope 外・裁定パッケージ候補**。
- **refuted:** 「既存 A-5 submitter を checkout ごとに分ける」。これは F251 再発の対応として
  **既にユーザー裁定へ返されている項目**であり (`docs/failures.md` F251 の 2026-09-07 再発節)、
  本 wave が既成事実にしない。**scope 外**。
- **不採用:** 「full toolchain `--version` 本文を再構成できるよう schema を拡張する」。
  本 wave の受理条件は短い manifest と record digest の一致で足りる。限界として明記するだけにする。

## 2. 親 brief の誤りの訂正 (レンズ B が現物で指摘した分)

以下は brief のアンカー誤りとして訂正し、段 5 以降はこの訂正版を使う。

- `artifact_admission.py:1538` は certified view の**発行入口ではなく型 guard**である。実入口は `:1459-1513`。
- `backoff_sweep_report.py` の不適格性の核心は `:53-80` ではなく、argmax が `:89`、
  unstable が届かない旨が `:141-147`。
- `s1_expected_goldens.py:253-258` は source-layout 文字列を pin するだけで、`SWEEP_US` の
  値の直接 pin は `orchestrator/tests/test_s1_known_axes_freeze.py:546-549`。
- A-5 finalizer の toolchain / perf preflight / counter status は `:769-790` ではなく `:791-794`。
- **(P1-a) の「純増ゼロ」は撤回する。** B-1 により第 2 部品には純増がある。
- **(P1-c) の「schema 拡張不要」は条件付きで維持する。** A-1 / B-3 の解決を事前登録側の
  arm 別期待 source digest で行うため producer schema は拡張しないが、
  「拡張不要」だけを書くと誤りになる。第 1 部品の insight には解決手段を併記する。
- **(P1-d) の「到達可能」は狭める。** complete な現物は write-heavy 1 件だけで、
  balanced の正例は実環境でまだ到達していない。

## 3. プラン v2 — 実装する内容

### 第 1 部品 — producer evidence の read-only 到達性監査 (docs、親が段 7 で書く)

新規 insight に次を書く。実装面の差分は無い。

- 6 種 evidence (repository commit / gitlink、CCBench source、環境契約 digest、
  trace-disabled 性能 build、診断 knob、toolchain、verifier receipt) の
  「どの成果物のどの field から再検証できるか」の対応表。
- **どの field がどこに無いか**を明記する。環境契約 digest は `result.json` にも
  `reservation.json` にも無く、`campaign.lock` と WAL にしか無い。
  診断 knob の effective 値はどこにも単一 field として無い。
- 到達性の限界 2 件 (full toolchain 本文は再構成不能、`BACKOFF_NOINLINE` の effective 値は
  arm 別 source digest の事前登録でしか束縛できない)。
- 結論: **producer schema は拡張しない。ただし事前登録が arm 別の期待 source digest と
  期待 script digest を持つことが前提である。**

### 第 2 部品 — 薄い sanctioned launcher (実装する。純増あり)

**新規 `tools/pegasus/submit_t1998_balanced_stock_inline.sh`** を作る。

- **balanced 1 workload だけを 1 job 投入する。** fan-out しない。これにより B-1 の
  「同じ checkout の兄弟 job を prune が壊す」経路が構造的に成立しない。
- job body は**既存の `tools/pegasus/a5_second_boot_backoff_sweep.sh` を 1 byte も変えずに
  再利用する。** 新しい job body も新しい汎用 driver も作らない (D1244)。
- 既存 A-5 の submitter・job body・契約テスト・登録簿 entry を変更しない。
- 既存 submitter が持つ投入前検査 (queue 状態、`check_quota`、`pegasusinfo`、
  出力 parent が repo 外であること、job-unique 出力、submit receipt の atomic 追記) は
  同じ強度で持つ。**弱めない。**
- 出力 parent は既定を持たず、絶対 path を必須にする。
- **もし job body を無改変で balanced 単独起動できないと実装中に判明したら、そこで止めて
  親へ報告する。** job body を書き換えて回避してはならない。

**親が現物で確かめた job body の投入契約** (`tools/pegasus/a5_second_boot_backoff_sweep.sh:188-207`)。
新 submitter はこれを `qsub -v` で満たす。

- `A5_WORKLOAD` — `write-heavy|balanced` のみ受理。**balanced 単独投入は job body 側で成立する。**
- `A5_OUTPUT_ROOT` — 絶対 path、未作成、repo 外、repo 祖先に `.git` が無いこと。
- `A5_SUBMISSION_NONCE` — 小文字 hex 32 桁。
- `A5_EXPECTED_HEAD` — 小文字 hex 40 桁。job body が `PBS_O_WORKDIR` の HEAD と exact 比較する。
- `JOB_SCRIPT_SHA256` — 小文字 hex 64 桁。
- 加えて `PBS_JOBID` / `PBS_NODEFILE` / `PBS_O_WORKDIR` が要る (PBS が与える)。

登録の同時更新 (B-5):

- `tools/pegasus/admission_registry.json` に新 submitter を `local-ok` として足す。
- `orchestrator/tests/test_hooks.py` の Pegasus 分類表と 4-field registry に足す。
- `docs/pegasus-runbook.md` の投影に足す。
- 新規契約テスト `orchestrator/tests/test_t1998_launcher_contract.py` を作る。

### 第 3 部品 — 事前登録固定 2 点だけを読む consumer (実装する)

**新規 `orchestrator/campaign/t1998_stock_inline_pair.py`。**

比較点は module 内 immutable 定数に固定する。`backoff_sweep._BASE` / `SWEEP_US` / `genomes()` を
import しない。argmax を使わない。

- baseline: `NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0, BACK_OFF=0, BACKOFF_FIXED=-1`
- target: 同 base で `BACK_OFF=1, BACKOFF_FIXED=5`
- workload: `balanced` だけ

**事前登録 identity の型を、共通と arm 固有に分ける (A-4 / B-2):**

- 共通: repository commit (40 桁)、CCBench gitlink (40 桁)、環境契約 digest、
  期待 launcher script digest。
- arm 固有: canonical genome、期待 source digest (`source_bytes_sha256`)。baseline と target で
  異なるのが正常であり、両者の一致を要求してはならない。
- **本 wave では実値を確定しない。** 型と seam だけを land し、値の固定は人間手番 (D1244)。

**読む入力:**

1. `<root>/result.json` — schema / status / workload / target_fixed_us / pair samples / median /
   ratio / campaign id / 2 つの sha256 / repository commit / gitlink / toolchain / node 証拠。
2. `<root>.failure.json` (sibling) — **存在したら拒否する** (B-4)。
3. `<root>/reservation.json` — `node_boot_evidence` / `source_binding` / script digest。
4. `<root>/campaigns/<campaign_id>/campaign.lock` — CCBench pin、環境契約 digest、
   `authority.contract_loader_commit`。
5. 公開 admission 経由の `CertifiedCampaignView` の records — exact 2 arm の
   `build_start` / `build_done` / `verify_done` / `bench_done` / `commit` だけ。
   他の 6 点は stage と abort の有無だけを見て、TPS も median も順位も読まない。

**受理条件 (訂正済み):**

- result が `a5-second-boot-result/v1`、`status=complete`、`workload=balanced`、`target_fixed_us=5`。
- sibling failure receipt が**無い**。
- result の lock/WAL sha256 が admitted view の値と一致。
- **gitlink の比較規則 (A-3):** result と reservation の 40 桁は事前登録値と exact 一致。
  lock / WAL の短縮形は事前登録値の**接頭辞であること**を要求する。
  接頭辞一致は full identity ではないと戻り値に明記する。
- **launcher 束縛 (A-2):** `reservation.binding.script_sha256` が事前登録の期待 script digest と一致し、
  `result.repository_commit` が `campaign.lock` の `authority.contract_loader_commit` と一致する。
  **親が現物で確かめた限界:** `binding.script_sha256` は**job body 自身の digest** であり
  (実物 = `0ef4d41ee1ddf8ecd7a86a32a3b9dbaf128279125ef4820c54421973ee281d84`)、
  どの投入器から出したかは成果物から復元できない。第 2 部品が job body を再利用する以上、
  consumer が束縛できるのは job body までである。**投入器の同一性を成果物から束縛しようとしない。**
  投入器の provenance は新 submitter が書く submit receipt に残す。この限界は戻り値と insight に明記する。
- **診断 build の拒否 (A-1 / B-3):** 「明示 1 が無い」を根拠にしない。
  各 arm の記録済み `source_bytes_sha256` が事前登録の arm 別期待値と一致することを要求し、
  一致しなければ `source-identity-unbound` で拒否する。
  加えて genome と configure command に `BACKOFF_NOINLINE=1` が現れたら `diagnostic-build` で拒否する。
  **後者だけでは診断 build を排除できないことを戻り値と insight に明記する。**
- 性能 build が trace-disabled であること、bench executable が性能 build receipt と対応すること。
- 両 arm の環境契約 digest / env tag / toolchain manifest と record digest が一致。
- baseline と target がそれぞれちょうど 1 attempt。
- 両 arm の bench samples / median / COMMIT fitness / result の projection が一致。
- 両 arm が `unstable is False` のときだけ `accepted`。片方でも true なら `inconclusive`。
- **`admit_replay_evidence()` を受理条件として呼ばない (B-6)。** receipt ID は
  admitted COMMIT の persisted payload から取る。

**拒否の構造 (A-6):** 拒否は code 文字列だけにせず、
`field` / `expected` / `actual` / 対象 arm (baseline か target か) を必ず持たせる。
`pair-identity-mismatch` のような複数原因を 1 code に畳まない。

**冗長 gate の明記 (A-5):** `pair-cardinality` と `producer-rejected-variant` は
上流の finalizer と `require_admitted_campaign` が先に拒否するため、
**単独では発火しない冗長 gate である**と source の comment と insight に書く。
検査は fail-closed として残すが、変異の証拠に数えない。

### テストの必須事項

- 新規 test file には `_run()` と `__main__` の自走 harness を足す
  (`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` の末尾と同型)。allowlist へ逃がさない。
- 負テストは**自己整合な producer root を組み立ててから 1 箇所だけ変異させる。**
  WAL を変えたら result の sha256 も作り直す。上流 gate で先に赤になる fixture は、
  狙った拒否の証拠にならない (A-5 / 両レンズの帰属指摘)。
- 実 admission / receipt 経路を使い、`require_admitted_campaign` や WAL parser を stub しない。
- 既存テストの期待値を変えない。**ただし登録簿・inventory への追加登録は「期待値の変更」ではなく
  必須の追加である** (B-5)。閾値を下げる・pin を緩める・skip する変更は禁止。

## 4. 段 5 の所有分割

| 単位 | 所有 path | 内容 |
|---|---|---|
| A | `orchestrator/campaign/t1998_stock_inline_pair.py`、`orchestrator/tests/test_t1998_stock_inline_pair.py`、`orchestrator/tests/test_official_perf_closure.py` | 第 3 部品 consumer + テスト + official perf 登録 |
| B | `tools/pegasus/submit_t1998_balanced_stock_inline.sh`、`tools/pegasus/admission_registry.json`、`orchestrator/tests/test_t1998_launcher_contract.py`、`orchestrator/tests/test_hooks.py`、`docs/pegasus-runbook.md` | 第 2 部品 launcher + 登録 + 契約テスト |
| C | `orchestrator/tests/acceptance_duration_ledger.json` | A と B の着地後に、新規 test node を実 collection から足す |

A と B は素集合なので並列投入する。C は A・B の後に逐次で投入する。

## 5. 変異事前登録 (DW-M01)

実装後に anchor を確定し、DW-M07 に従って最終 commit で再検証してから本走する。
各変異は**同じ入力を拒否する層が前後にも内側にも無い**ことを実装後に確認し、
確認できなければ登録せず実効 gate へ再照準する。

| ID | 変異位置 | 期待 | 単一理由性の根拠 |
|---|---|---|---|
| M1 | consumer の arm 別 source digest 比較を無条件 true にする | KILLED | 事前登録 digest を見る層は他に無い |
| M2 | sibling failure receipt の存在検査を削る | KILLED | 上流は failure receipt を読まない |
| M3 | gitlink の接頭辞検査を無条件 true にする | KILLED | 短縮形を見る層は他に無い |
| M4 | `unstable` の分岐を `accepted` 側へ倒す | KILLED | 上流 admission は unstable を拒否しない |
| M5 | target の選択を fixed-5 固定から argmax へ変える | KILLED | 上流は 8 点全部を通す |
| M6 | 拒否 payload から `expected` / `actual` を落とす | KILLED | 規律 3 の証拠投影はこの層だけ |
| M7 | `reservation.binding.script_sha256` (job body digest) の比較を削る | KILLED | 事後に script digest を見る層は他に無い |
| M8 | launcher の投入 workload を balanced 1 本から 2 本 fan-out へ変える | KILLED | 契約テストがこの層だけを見る |
| M9 | launcher の出力 parent が repo 外であることの検査を削る | KILLED | 新 submitter 固有の検査 |

**変異に登録しないもの (冗長 gate、DW-M03):** `pair-cardinality`、
`producer-rejected-variant`、`admit_replay_evidence` の二重呼出し。
理由は上流 gate が先に同じ入力を拒否するためであり、この判断は insight に残す。

## 6. 裁定パッケージへ返す (本 wave では実装しない)

1. **A-5 job body の global `git worktree prune --expire now` と、A-5 submitter の 2 job fan-out。**
   F251 の 2026-09-07 再発として既にユーザー裁定へ返されている項目であり、本 wave は触れない。
   本 wave の第 2 部品は「T-1998 専用に 1 job だけ投入する新しい submitter」を足すだけで、
   A-5 側の構造は直さない。
2. **2026-09-07 に取れた balanced の生値 (none 3,803,883 / fixed-5 4,294,095) の扱い。**
   commit `0ade09d5e` に束縛され、finalizer 前に rc=1 で落ちたため `result.json` が無く、
   3 部品 land 後の prospective 事前登録より前の測定である。新 consumer は
   `producer-artifact-missing` で拒否する。T-1998 の主張へ転用してよいかは人間手番。
3. **事前登録の実値 (期待 commit / gitlink / 環境契約 digest / script digest / arm 別 source digest) の固定と
   正式測定の認可。** D1244 のとおり 3 部品 land 後に人間手番へ返す。

## 7. 不変条件 (段 5・6 で緩めない)

- 規律 2 を緩めない。anomaly を出した variant を通す経路を作らない。
- 診断 build 値と headline 値を混ぜない (D20)。
- D1137 の IPC 帯・散布・bar は入力にも判定にも使わない。別命題である。
- 本 wave で測定・build・benchmark を 1 回も走らせない。
- 既存 A-5 の受理集合を 1 bit も変えない。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない。
