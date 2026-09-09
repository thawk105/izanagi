# [T-1851] 単位 C3b — 史上初の official 床値 campaign を投入し、止めた gate を実値で特定した

branch `worktree-dev-wave-t1851-unit-c2`、base `8fbcb70a5` (単位 C3a の tip)。
実装面の差分は 0。本 wave が repo へ足したのは docs (本 insight と台帳 fragment) だけである。

## この記録の射程 — どこが main の事実で、どこが未 land branch の事実か

**§4 と §5 の欠陥 2 件は main のコードに実在する。** 走行は wave の checkout で行ったが、
**main から official 床値を投入しても同じ場所で止まる。** 実測した対応は次のとおり。

| 事実 | main 側の所在 |
|---|---|
| allowlist が resolved protocol の hash を legacy 固定 path へ束縛する | `orchestrator/campaign/s8b_floor_campaign.py:5323` (`_FLOOR_PROTOCOL_REL: protocol_sha256`) |
| 停止文言 `launch certificate: freeze allowlist hash 不一致` | 同 `:5488` |
| 凍結 hold の分岐 `s8b-floor.protocol-bytes-expected-pin` | 同 `:5251` |
| 投入器・job body・凍結成果物 | `tools/pegasus/floor_campaign.sh`、`tools/pegasus/submit_floor.sh`、`output/s8b-freeze/` は **wave と main で同一** (差分 0) |

**一方 §1 が言う配線 (campaign → certified launcher → attempt registry → result v5) は
単位 C3a の成果で、branch `worktree-dev-wave-t1851-unit-c2` 上にあり main には無い。**
その branch は D1341 と D1703 (どちらもユーザー裁定) により、単位 D2 (consumers/fixtures) が
揃うまで land しない。branch は 4 単位 (C1b / C2 / C3a / C3b) を載せており、2026-09-02 以降の
実装が未 land のまま溜まっている。**この branch を失うと 4 単位分の実装が失われる。**

---

## 1. 何をしたか

C3a が配線した `campaign → certified launcher → attempt registry → result v5` の経路を、
**Pegasus の sanctioned 投入経路で実際に 1 本走らせた**。official 経路の床値 campaign が
実投入されたのは本 run が初めてである (過去の実投入 2 件 `873200` / `873225` はいずれも rc=2、
12 セル完走した `945229` は pilot で D811 により発効しない)。

**結果は完走ではない。** 走行は launch certificate で fail-closed に停止した。
本 insight はその停止を「失敗」ではなく**実測結果**として記録する — 段 4 で
「別 gate で止まっても、どの gate がどの実値で止めたかは C3b の実測である」と事前に裁定してある
(`s4-adjudication.md` §2.5)。

## 2. 走行の実測値

| 項目 | 実測値 |
|---|---|
| request ID | `988501.nqsv` |
| submission nonce | `36d9eff14306849bb3221f6649c19119` |
| source commit | `8fbcb70a5f4f5c098c13026c425ade66a4d6db23` |
| job script sha256 | `9a7cd1f80ccec6a15b6f0e3fd842e4e5a9ad382907d4fbb5d4fdf1c94af6c62d` |
| 投入 | 2026-09-09 22:09 JST、`qsub` rc=0、`Request 988501.nqsv submitted to queue: gen_S.` |
| RUN 観測 | 2026-09-09 22:10:31 JST (`qstat` STT=`RUN`) |
| 実行ノード | `bnode030` (boot_id `e6bee8e3-32b2-48a2-b469-ca15d52eff9b`) |
| 予約 | `requested_s=36000`、`scheduler_started_epoch=1788959419`、`deadline_epoch=1788995419` |
| driver 終了 | `driver_rc=1`、`completed_epoch=1788959463` (RUN から約 26 秒) |
| mode | `official` |
| 投入前検査 | `check_quota` / `pegasusinfo` / `qstat_Q` / `rbudgetcheck` すべて rc=0 |

**通過した gate (checkpoint の `stage` 遷移):** `policy` → `submit-binding` → `source-identity`
→ `allocation-reservation` → `gflags-build` → `glog-build` → `protocol-resolution` → `floor-driver`。

D926 の承認束縛 (`IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` と `IZANAGI_SUBMISSION_NONCE` の exact 一致) と
source identity 照合は**実機で通った**。`executing_script_sha256` と `job_script_sha256` は一致した。

## 3. 止めた gate と、その入力の実値

停止文言は 2 行である。

```
FloorCampaignError: launch certificate: freeze allowlist hash 不一致: output/s8b-freeze/floor_protocol.json
IZANAGI_FREEZE_HOLD {"check_id": "s8b-floor.protocol-bytes-expected-pin", "decision": "freeze-verification-hold", "release_condition": "explicit-user-command-only", "ruling": "rulings-4th-batch-2026-08-12"}
```

gate の入力の実値は次のとおりである。

| gate 入力 | 実測値 |
|---|---|
| resolver が選んだ protocol path (`job-result.json` の `protocol_path`) | `output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json` |
| その file の sha256 (= 実行時の `protocol_sha256`) | `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a` |
| allowlist が期待 hash を要求した file | `output/s8b-freeze/floor_protocol.json` (legacy 固定 path) |
| その file の実 bytes sha256 | `261cec1c7f423b3eebff41ee716d2bfe2c6fa9a10a9dd86d91eaf71612e74aac` |
| 2 file の内容差 | **`ccbench_pin` 1 field のみ** — legacy `d706650cdb31e442bef45b9b4216951d4fb40969` / versioned `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| 現行 `external/ccbench` gitlink | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| 共有 freeze | 両 protocol とも freeze `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688` を共有 |

## 4. 欠陥 1 — allowlist が resolved protocol の hash を legacy 固定 path へ束縛している

`_floor_preflight_freeze_allowlist()` は allowlist を次の形で作る
(`orchestrator/campaign/s8b_floor_campaign.py:5313-5315`)。

```
allowlist = {
    _HOLDOUT_FREEZE_REL:  freeze_sha256,
    _FLOOR_PROTOCOL_REL:  protocol_sha256,
    ...
}
```

`_FLOOR_PROTOCOL_REL` は legacy 固定 path `output/s8b-freeze/floor_protocol.json` である。一方
`protocol_sha256` は**実行時に resolver が選んだ protocol の canonical sha256** である
(`s8b_floor_campaign.py:8671` の `_canonical_sha256(protocol)`)。

`_assert_freeze_allowlist()` は allowlist の各 entry について
`sha256(file bytes) != expected` を検査する (`同:5471-5482`)。したがって
**resolver が versioned protocol を選ぶ限り、legacy file の bytes hash が resolved protocol の
canonical hash と一致することは構造的にありえない。**

これは consumer 取り残しである。versioned protocol の resolution は D1111 の解決
([T-1945] の択 (iii)、台帳を protocol 世代ごとに分ける複合形) として正当に land しているが、
**launch certificate の allowlist はその改版に追随していない。**
official 床値走行が一度も成功していない事実は、これで説明がつく。

## 5. 欠陥 2 — ユーザー明示解除が条件の凍結 hold が、同一比較の二重化で無効化されている

`s8b-floor.protocol-bytes-expected-pin` は `freeze_verification_hold.HELD = True` により保留中で、
解除条件は「explicit-user-command-only」である (2026-08-12 第 4 束の裁定)。実装は次のとおり
(`s8b_floor_campaign.py:5242-5248`)。

```
if _freeze_hold.HELD:
    held_checks.append(_freeze_hold.held_marker("s8b-floor.protocol-bytes-expected-pin"))
elif sha256(captured[_FLOOR_PROTOCOL_REL]) != protocol_sha256:
    raise FloorCampaignError("launch refusal: floor protocol bytes sha256 が expected と不一致")
```

**保留されるのは `elif` 側だけである。** ところが §4 の `_assert_freeze_allowlist()` が
**同じ 2 値の同じ比較**を無条件に行う。したがって `HELD=True` でも走行は同じ条件で止まる。
文言が変わるだけで、hold は結果を 1 bit も変えていない。

**この所見は「hold が不要だった」ことを意味しない。** 意味するのは、
hold が守ろうとした受理の向きが、別経路の恒等な検査によって打ち消されている、ということである。
どちらを正とするかは正しさ gate の設計判断であり、ユーザー裁定へ返す (`ruling-package.md`)。

## 6. 走行が消費したもの — ゼロ

共有 admission root
(`<git-common-dir>/izanagi/s8b-holdout-admission-v1`) の投入直前と走行後の snapshot は
**完全に一致した** (`admission-snapshot-presubmit.txt` / `admission-snapshot-post.txt`)。

| 項目 | 投入直前 (22:09:59) | 走行後 (22:15:19) |
|---|---:|---:|
| `claims` | 36 | 36 |
| `consumed` | 228 | 228 |
| `measurement-generation-claims` | 36 | 36 |
| `measurement-generation-consumed` | 288 | 288 |
| `floor-attempt-registries` | 1 | 1 |
| `ledger.jsonl` 行数 | 72 | 72 |
| `attempt-ledger.jsonl` 行数 | 516 | 516 |

**凍結世代は焼けていない。** 走行は claim / marker / registry のどれも作る前に停止した。
§4 と §5 が解けたあとに、同じ世代で改めて走らせられる。

## 7. gate 入力の実値域 — 何が測れて何が測れなかったか

契約 9 節が要求する「実環境の値域」は、**attempt registry 側の gate については供給できていない。**
走行が計測段へ到達しなかったためである。測れたもの・測れなかったものを分けて書く
(`DW-O13` の「field の実在では足りない」を、逆向きに誤読しないための書き分け。段 3 レンズ A の
A-9 / A-10 を採用した 4 分類)。

### (1) 動的に観測した値

| 述語 / gate | 消費 field | 観測値 |
|---|---|---|
| submission nonce 束縛 (D926) | `IZANAGI_SUBMISSION_NONCE` / `IZANAGI_CONFIRM_OFFICIAL_FLOOR_RUN` | 両者 exact 一致 `36d9eff1…`。approval bit が立った |
| source identity | `executing_script_sha256` / `job_script_sha256` / committed blob | 3 者一致 `9a7cd1f8…` |
| reservation preflight | `requested_s` / `scheduler_started_epoch` / `deadline_epoch` / `host` / `boot_id` | `36000` / `1788959419` / `1788995419` / `bnode030` / `e6bee8e3-…` |
| protocol resolution | resolved path と canonical sha256 | versioned path / `2c8cf9be…` |
| launch certificate freeze allowlist | `sha256(file bytes)` と expected | `261cec1c…` ≠ `2c8cf9be…` → 拒否 |
| 凍結 hold | `check_id` / `decision` / `release_condition` / `ruling` | 上記 §5 の 4 値 |

### (2) 静的に宣言された closure (観測ではない)

- attempt registry の genesis は protocol の `n_sessions=8` と `retry_slots_per_cell=2` から
  12 cell × 8 × (1 planned + 2 retry) = **288 slot** を宣言する。**本 run はこれを 1 件も
  実体化していない。** 宣言値であって観測値ではない。

### (3) artifact に所在が無い入力

- 封印 pre-probe の exact type、issuer state membership、owner identity、post-probe origin seal、
  one-shot の `used` は process 私有の weak map の状態であり、**どの artifact にも key が無い**。
  直接観測は原理的に不能で、下流の classification / terminal 成立が間接証拠になるだけである。

### (4) 未発火の枝 (未観測であって到達不能ではない)

- `probe_before.competing = true` と `probe_after = null` (競合分岐)。
- `retry_ordinal = 1..2` (retry 発火時のみ)。
- cut-6 replay 系 (resume 経路。fresh default run の適用域外)。
- `attempt_ordinal > 0` (production gate が明示的に拒否する値)。

**本 run はこれらのどれにも到達していない。** 計測段へ入っていないので、
`probe_before` の 4 key (`rc` / `stdout` / `stderr` / `competing`) すら 1 件も観測していない。

## 8. receipt の限界文言

> 本 receipt は、記載した commit `8fbcb70a5f4f5c098c13026c425ade66a4d6db23`、Pegasus job
> `988501.nqsv`、環境 tag `pegasus`、mode `official`、resolved protocol
> `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a`、freeze
> `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688` による fresh default
> production campaign **1 回の投入で、実際に観測された入力値だけ**を記録する。
> 列挙値はこの run の観測集合であり、launcher または consumer が受理しうる全値域、未発火分岐、
> 他環境、他 mode、他 commit、将来 campaign の母集合または許容 bound を示さない。
> **本 run は計測段へ到達していないため、attempt registry 側 gate の実値域は本 receipt に無い。**
> 未観測の値を到達不能と読んではならない。

**本 wave は時間予算を新設も改訂もしない** (段 3 レンズ B の B-10 を採用)。1 run の Elapse は
分布の max ではない。過去の完走観測は pilot 系で 2894 / 2981 / 3016 / 3096 秒であり、
本 run は完走していないので所要の一次資料にならない。

**`eligible_for_refreeze` について。** 本 run は result を 1 件も発行していないので、この bit は
立っていない。仮に将来立っても、それは承認でも proof chain の完結でもない
(段 3 レンズ A の A-2)。さらに v5 result は現行の `s8b_holdout_freeze` / `s8b_ratified_freeze` が
exact key で拒否するため、**単位 D2 まで freeze へ到達しない** (同 A-1)。

## 9. 退避 bundle

repo 外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1851-unit-c3b/bundle/` に **848 file** を退避した。
構成 manifest は `bundle-manifest.txt` (本 insight 内に複製、sha256
`c86c03071be83b3facd916aadcbd83738114b1b7e3d7c6f0668ab385055170b4`)。

- `job-staging/` — `job-result.json`、`failure.json`、driver stdout/stderr、toolchain と
  gflags/glog の build receipt、`reservation.json`、`qstat-f` raw、`scheduler-elapse.json`
- `submission/` — submission directory 全体 (pre-submit、submit receipt、qsub raw、
  queue/quota/budget raw、scheduler stdout/stderr)
- `external-checkpoint/` — `checkpoint.jsonl` (stage 遷移の一次資料)
- `admission-snapshots/` — 投入前・投入直前・走行後の 3 点

**run directory と binary store は存在しない** — 計測段へ到達していないため生成されていない。

## 10. 受入全走 (6 attempt、非帰属赤 1 回)

**attempt 6 が `child-green`。22,662 passed / 68 skipped / 0 failed。** receipt 発行済み、
tested main `7f17e1c63b5db01b424c87cf5778635dd653dab2`、tested tip `af5397619`。
`--lease-optional` で走らせ、lease は別 session が保持していたため取得していない (解放対象なし)。

| attempt | 結果 | 帰属 |
|---|---|---|
| 1 | 走行前に停止 (`merge-abort` / `cleanup-failure`、source_rc=128) | **非帰属。** post-claim merge の cleanup が失敗し `MERGE_HEAD` を残した。親が `git merge --abort` で戻し、`DW-O17` の非 ff 手順で改めて取り込んだところ**競合 0 件で auto-merge が通った** — merge 内容ではなく cleanup 側の問題 |
| 2 | 22,650 passed / 68 skipped / **12 error** | **非帰属 (環境)。** 下記参照 |
| 3 | 走行前に停止 (`preclaim-history-provenance` / dispatch `queue-wait-timeout`) | **非帰属 (infra)。** child 未起動 |
| 4 | 走行前に停止 (`preclaim-history-provenance` / `TimeoutExpired`) | **非帰属 (infra)。** D612 上書きを 3600/600 にしたところ外側 watchdog が先に切った |
| 5 | 走行前に停止 (dispatch `queue-wait-timeout`) | **非帰属 (infra)。** 上書き 1000/150 でも queue が飽和 |
| 6 | **22,662 passed / 68 skipped / 0 failed** | — |

### attempt 2 の 12 error はなぜ非帰属か

12 件すべてが `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` の **error** (autouse
fixture 段の失敗) で、1 file に閉じていた。この fixture は `probe._repo_snapshot(REPO_ROOT)` を呼び、
`_run_git()` が git subprocess ごとに **`timeout=30.0`** を掛ける
(`tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:133-144`)。そのうち
`git ls-files --others --exclude-standard` は、この worktree で高負荷時に **16.80 秒**かかることを
git 自身が警告として出しており、load 3.58 の時点では **1.64 秒**だった。3 shard 並列の受入走行中に
30 秒を超えるのは十分ありうる。

- pin される 3 file (`probe.py` / `probe.pbs` / `s8b_floor_campaign.py`) はすべて実在する。
- `_repo_snapshot` は現在正常に走る (`head=af539761918c`、`untracked=0`)。
- 本 wave の変更は docs のみで、この file と編集面が交わらない。
- **attempt 6 で再現しなかった。**

### 併せて実測した既知の締切不一致 ([T-2484])

受入の `preclaim-history-provenance` 段は `check_ai_provenance.py` を subprocess で呼び、待ち手側の
`_STAGE_TIMEOUT_SECONDS = 1200` が掛かる (`tools/dev_wave_wait.py:234`)。一方 dispatch の既定予算は
queue 待ち 900 + grace 300 = **ちょうど 1200** で余裕が無い。**D612 の opt-in 上書きを 3600/600 に
すると必ず外側 watchdog が先に切る** (attempt 4 で実測)。1000/150 まで下げても queue 飽和では
届かない (attempt 5)。上書きは queue 待ちを伸ばせるが、この段では 1200 秒の天井を越えられない。

## 11. 収録物

- `s1-brief.md` — 段 1 brief ((P1) 4 件が段 3 の攻撃対象)
- `s4-adjudication.md` — 段 4 裁定 (所見 25 件の real/refuted と plan v2)
- `ruling-package.md` — ユーザーへ返す裁定 5 件
- `bundle-manifest.txt` — 退避 bundle 848 file の path と sha256
- `admission-snapshot-{pre,presubmit,post}.txt` — 共有 admission root の 3 点 snapshot
- `verbatim/` — 段 2 plan、段 3 敵対 2 本、焦点相談 1 本の逐語
- `verbatim/prompts/` — 全子へ渡した prompt の逐語
