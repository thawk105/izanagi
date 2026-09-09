# [T-1851] 単位 C3b — ユーザー裁定へ返す 5 件

本 wave は land しない (D1341)。下の 5 件はどれも成果物の値を今すぐ変えない。
**投入と実測は完了させてある** — 返答を待っている作業は無い。

---

## 裁定 1 — official 床値走行を塞いでいる allowlist の束縛先 (最重要)

**実測:** sanctioned 経路で official campaign を投入したところ、launch certificate が
`launch certificate: freeze allowlist hash 不一致: output/s8b-freeze/floor_protocol.json` で
driver rc=1 を返した。原因は次の 1 行である。

- `allowlist[output/s8b-freeze/floor_protocol.json] = protocol_sha256`
  (`s8b_floor_campaign.py:5313-5315`)
- `protocol_sha256` は**実行時に resolver が選んだ protocol の canonical sha256**
  (`同:8671`)。本 run では versioned protocol の `2c8cf9be…`
- 比較相手は legacy 固定 file の生 bytes hash `261cec1c…`
- 2 file の差は `ccbench_pin` **1 field だけ** (legacy `d706650c…` / versioned `511c9538…`)

**versioned protocol の resolution は D1111 の解決 ([T-1945] 択 (iii)) として正当に land している。
allowlist がその改版に追随していない。** resolver が versioned を選ぶ限り、legacy file の bytes が
resolved protocol の canonical hash と一致することは構造的にありえない。

### 択一

- **(a) allowlist の当該 entry を、resolved protocol の実 path へ束縛し直す。親の推奨はこれ。**
  意味は「preflight が固定した protocol の bytes が、走行が使う protocol と同一であること」であり、
  それは resolved path で表現するのが正しい。受理集合は広がらない (同じ強度の検査が正しい対象へ移る)。
- (b) legacy 固定 file を現行 pin で再封印し、両者を一致させる。**凍結 bytes を変えるので
  ユーザー裁定が要る。** 2026-08-16 の wave が dormant な issuer を用意済み。
- (c) resolver を legacy 固定 path へ戻す。D1111 の解決を巻き戻すことになるので推奨しない。

**放置した場合の成果物影響:** official 床値は永久に採れない。freeze v2 の floor/budget は
埋まらず、oracle gate は 2 件拒否を返し続ける。

## 裁定 2 — 凍結 hold が同一比較の二重化で無効化されている

**実測:** `s8b-floor.protocol-bytes-expected-pin` は `freeze_verification_hold.HELD = True` で
保留中 (解除条件「explicit-user-command-only」、2026-08-12 第 4 束)。しかし保留されるのは
`s8b_floor_campaign.py:5244-5248` の `elif` 側だけで、`_assert_freeze_allowlist()` (`同:5471-5482`) が
**同じ 2 値の同じ比較**を無条件に行う。したがって `HELD=True` でも走行は同じ条件で止まり、
**hold は結果を 1 bit も変えていない。**

### 択一

- **(a) 裁定 1 の (a) を採ると、この二重化は自然に解消する** (allowlist が正しい対象を見るため、
  両検査とも通る)。**親の推奨はこれ。** hold の是非は別途裁定してよい。
- (b) hold の射程を launch certificate 経路まで広げる。**受理集合を広げる向きなので、
  親は独断で採らない。**
- (c) hold を解除する。凍結チェーン検証の再開であり、他 20 件の check にも影響する。

## 裁定 3 — attempt registry の slot 一意性が凍結世代あたり 1 campaign に制限する

**実測:** registry の binding は `(freeze_sha256, protocol_sha256, schedule_sha256)` だけで決まり
(`s8b_floor_attempt_launcher.py:386-392`)、**campaign_run_id を含まない。** protocol の
`master_seed` は凍結値なので schedule も決定的である。同じ凍結世代での 2 本目の official campaign は
同じ planned slot を再予約しに行き、`slot was reserved more than once` に当たる。

D1124 は「落ちたら測り直す」を裁定しているが、それは admission 層の一回性についてである。
**C3a が配線した attempt registry の slot 一意性は別層であり、同型の停止構造がそこにある。**
D1111 の解決 ([T-1945]) は 2 世代の**収容**を解いたが、**同一世代の再走**は解いていない。

### 択一

- **(a) 現状を受容し、再走が要る場合は新しい凍結世代を発行する。親の推奨はこれ** —
  凍結世代は `(contract_sha256, ccbench_pin)` の組で増え、D444 が「組ごとに 1 件・追加のみ」と
  定めている。ただし**任意に組を作れるわけではない**ので、実質的な再走可能性は限定される。
- (b) slot key へ campaign 世代軸を足す。正しさ防壁の意味を変えるので独断では採らない。
- (c) 何もしない。落ちた run が世代を焼く構造が残る。

**本 run は claim / marker / registry を 1 件も作っていない**ので、現時点で焼けた世代は無い。

## 裁定 4 — 本番の共有 admission root に test fixture 行が残っている (既知 F793 の現況報告)

**実測:** `<git-common-dir>/izanagi/s8b-holdout-admission-v1/floor-attempt-registries/
db07b575…/d388477f…/registry.jsonl` に 193 行 (genesis 1 + `start` 96 + `pre-observation-seal` 96) が
2026-08-27 19:53 から存在する。`process_identity` は
`{"execution_uuid": "campaign-fixture-execution", "pid": 101, "starttime": "campaign-fixture-starttime"}`、
`run_start_receipt_sha256` は `4444…44` で、**test fixture の値である。**

**本 run は塞がれなかった** — 本番の freeze は `315b1eb8…` (protocol の `env_tag=pegasus`) で、
fixture 側は `db07b575…` (`env_tag=linux-baremetal`)。両者は別 path になる。

既知の F793 として台帳に記録済みなので新しい F は作らない。**fixture を書いた exact pytest node は
durable bytes からは特定できない。** 別課題として追跡するかを裁定されたい。
規律 6 の観点では、test という別 authority の出力が耐久 production namespace へ入っており、
「共有 root にあるから信頼済み」という扱いを禁じるべき信頼境界の実例である。

## 裁定 5 — 契約 9 節の「実値域」は本単位では供給できていない

attempt registry 側の gate 入力 (封印 pre-probe の 4 key、ordinal 三軸、consumption marker、
result v5 の prefix proof 7 key) の実値域は、**走行が計測段へ到達しなかったため 1 件も観測できていない。**
裁定 1 が解けたあとの再走で初めて供給できる。

- **(a) 裁定 1 を解いてから C3c として再走し、そこで実値域を供給する。親の推奨はこれ。**
- (b) 契約 9 節の「実値域」要求そのものを erratum で弱める。**親の独断では変えない。**
- (c) 単位 D2 (consumers/fixtures) を先に進め、実値域は後回しにする。
  依存順 `C → D2` の正本 (`2026-09-01_t1946-t2107-registry-wiring-design/s4-adjudication-r2.md`) に反する。
