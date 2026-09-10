# 親 (manager) の実測値 — 2026-08-17 09:10 JST

worktree = /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t987-floor-rebind, base = 699c9cae。
以下はすべて上記 worktree 上で実行した生の観測である。解釈ではない。

## M1. 承認定数と現 gitlink

```
orchestrator/campaign/s8b_approved.py:67
  CCBENCH_FULL_SHA = "511c9538e4e8efa54b45cda62e72389ed3b706ec"

$ git ls-tree HEAD external/ccbench
160000 commit 511c9538e4e8efa54b45cda62e72389ed3b706ec	external/ccbench
```

→ 承認定数と現 gitlink は**一致**している。

## M2. legacy anchor protocol の中身

```
$ python3 -c "import json; d=json.load(open('output/s8b-freeze/floor_protocol.json')); ..."
ccbench_pin     = d706650cdb31e442bef45b9b4216951d4fb40969
env_tag         = pegasus
contract_sha256 = e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
```

→ protocol 側の pin は **d706650c** で、現 gitlink **511c9538** と異なる。

## M3. 現行 env 契約の解決 (live library 呼び出し)

```
$ python3 -c "from orchestrator.campaign import s8b_floor_campaign as fc; r = fc.resolve_current_floor_protocol(); ..."
OK path          = output/s8b-freeze/floor_protocol.json
   contract_sha256 = e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01
   doc ccbench_pin = d706650cdb31e442bef45b9b4216951d4fb40969
```

→ 現時点では例外を上げず、legacy anchor が唯一の候補として解決される。

## M4. 凍結保留の登録状況

`orchestrator/campaign/freeze_verification_hold.py`

- `HELD = True` (:14)
- `HELD_CHECK_IDS` に `s8b-floor.protocol-bytes-expected-pin` (:20) と
  `s8b-floor.sealed-protocol-ccbench-pin-current-head` (:21) が登録済み。
- `HELD_CHECK_IDS` / `HELD_CHECK_ID_COUNT=21` / `HELD_CHECK_IDS_SHA256` は
  import 時に自己整合を検査する 3 つ組 pin (:39-48)。

呼び出し側:

- `s8b-floor.protocol-bytes-expected-pin` → production の
  `orchestrator/campaign/s8b_floor_campaign.py:3628-3634` が `HELD` 分岐で marker を出し、
  `elif` 側の bytes 比較を**実行しない**。
- `s8b-floor.sealed-protocol-ccbench-pin-current-head` → production 呼び出し site は
  検索で見つからず、`orchestrator/tests/test_s8b_floor_campaign.py:1210-1236` の
  test 側 helper `_assert_sealed_protocol_ccbench_pin` だけが使う。

## M5. AI 再封印 issuer

`orchestrator/campaign/s8b_floor_campaign.py`

- `_reseal_protocol_at_root` (:936-1064), `reseal_protocol` (:1066-1068)。
- commit `230fc757` (2026-08-16 14:27:55 +0900) で着地。
- ~~production caller は検索で 0 件~~ **← 誤り。段 3 レンズ B に refuted され、親が再確認して確定。**
  訂正: `main()` に `reseal-protocol` サブコマンドが実在する
  (`orchestrator/campaign/s8b_floor_campaign.py:6691-6701`、parser は同 :6566-6570)。
  `python3 orchestrator/campaign/s8b_floor_campaign.py reseal-protocol` で発行できる。
  誤りの原因: 親の grep が `grep -v "^orchestrator/campaign/s8b_floor_campaign.py"` で
  **同一 file 内の呼び手を自分で除外**していた。
  正しい記述: 「CLI から実行可能な発行経路が存在する。ただし Pegasus job script
  (`tools/pegasus/floor_campaign.sh`) からの自動呼出しは無い」。

## M6. index と解決の構造 (コード読解、要裏取り)

- `_scan_floor_protocol_index_at_commit` (:782-871) は
  (a) legacy anchor を **commit blob** から必ず index へ入れ (:810-817)、
  (b) `output/s8b-freeze/floor-protocols/` 配下を **working tree** から列挙して足す (:819-)。
  index の key は `(contract_sha256, ccbench_pin)` の組。
- `resolve_current_floor_protocol` (:882-901) は index 全件のうち
  `record.contract_sha256 == current.contract_sha256` を候補とし、
  **候補が exact 1 件でなければ `FloorCampaignError`** を上げる (:896-900)。
- `_reseal_protocol_at_root` は successor の `contract_sha256` を
  target_contract のものへ代入する (:1002)。M2 より legacy anchor の contract_sha256 も
  同じ `e576e9cd...` である。

これらから導かれる帰結 (**要検証。裏取りせよ**):
`reseal_protocol()` を実行すると、key は
`(e576e9cd, d706650c)` と `(e576e9cd, 511c9538)` の 2 件になり、
どちらも `contract_sha256` が現行 env 契約と一致するため、
`resolve_current_floor_protocol()` は `count=2` で例外を上げるようになる。

`resolve_current_floor_protocol` の消費者には
`orchestrator/campaign/certified_writer_admission.py:201` がある。

## M7. M6 の帰結は既存テストが明示的に pin している (読解でなく実在の検査)

`orchestrator/tests/test_s8b_protocol_builder.py:1053-1084`

```
def test_current_floor_protocol_resolver_rejects_two_current_contract_matches():
    current = ec.GENERATIONS["pegasus"][0].contract
    records = [ ... for path, pin, raw in (
        (fc._FLOOR_PROTOCOL_REL, "1" * 40, b"first"),
        (fc._derived_reseal_protocol_relpath(current.contract_sha256, "2" * 40),
         "2" * 40, b"second"),
    )]
    ...
        with pytest.raises(fc.FloorCampaignError, match="exact 1 件でない: count=2"):
            fc.resolve_current_floor_protocol(root=ROOT)
```

この test が組み立てる 2 件は、**legacy anchor** と
**`_derived_reseal_protocol_relpath` が返す reseal 出力先**であり、
`contract_sha256` が同一で `ccbench_pin` だけが異なる。これは
`reseal_protocol()` 実行後に実際に生じる状態そのものである。

→ M6 は real。**「発行経路は存在するが、呼ぶと解決が fail-closed で壊れる」**。
legacy anchor を退役させる手段 (= 世代移行) が無い限り、reseal 済み protocol は解決できない。
これが「再測定は世代移行 wave と同一 chain でのみ」という束縛の**コード上の実体**である。

同ファイル :1046-1051 に count=0 側の対照
`test_...rejects_...` も存在し、resolver の exact-1 規則は両側で pin されている。

## M8. env 契約は 2 世代あり、g2 は宣言済みだが未活性

```
$ python3 -c "from orchestrator.campaign import env_contract as ec; ..."
linux-baremetal n_generations= 1
  gen 0 contract_sha256= 1b2ee85346a4c867...
pegasus n_generations= 2
  gen 0 contract_sha256= e576e9cd1369bba3...   <- 現在 active (M3 の解決結果と一致)
  gen 1 contract_sha256= 1346c20b5519be4b...   <- 宣言のみ、未活性
```

`env_contract.REGISTRY` は `_ActivationRegistryView` (env_contract.py:729-742) で、
`_authority_snapshot().current` が返す **活性世代**だけを見せる。

帰結: g2 を活性化すると `lookup("pegasus")` は `1346c20b` を返す。すると

- legacy anchor (contract `e576e9cd`) は候補から外れる
- **g2 活性化後に** `reseal_protocol()` を呼べば successor の contract は `1346c20b`、
  pin は `511c9538` となり、候補はこの 1 件 → `count=1` で解決できる

つまり「世代移行 → reseal」の順で 1 chain に並べたときだけ resolver が通る。
これが「同一 chain でのみ」という条件の設計上の理由である。

## M9. その世代移行は**現在稼働中の別 wave が今日実施しつつある**

`/work/1/SFC/tanab/dev-wave-jobs/t657-activation-rebuild/handoff.md` (2026-08-17 08:2x JST 開始)
より逐語:

```
- `GENERATIONS`: linux-baremetal [1], pegasus [1, 2]。active = pegasus g1 (`e576e9cd…`)
- `_is_valid_activation_successor(g1, g2)` = True
- anchor floor protocol: env_tag=pegasus, contract=`e576e9cd…`, pin=`d706650c…` (index 1 件)
- 現行 ccbench gitlink = `511c9538…`
- g2 活性化後の reseal target pair = (`1346c20b…`, `511c9538…`)、**未発行**
```

同 wave の依頼はユーザー指示 (2026-08-17 08:16 以降) で
「現行 main の `reseal_protocol()` (D444) を使って立て直す」であり、
編集点として `env_contract.py:381 _ACTIVATION_HEAD_SERIAL: int = 1` → 2 を挙げている。

## M10. gate 2 (holdout 受入) は t657 着地後も残る — 親の独立読解

`orchestrator/campaign/s8b_holdout_admission.py`

- `_PROTOCOL_REL = "output/s8b-freeze/floor_protocol.json"` (:64) — 固定 legacy path。
- `_authority()` (:463-490) は `_head_blob(root, _PROTOCOL_REL)` で**固定 path の HEAD blob**
  を読み、`if protocol_document != dict(protocol): raise HoldoutAdmissionError(
  "fixed protocol bytes do not match the supplied protocol")` (:472-474)。

t657 着地後の状態を当てはめる:

- resolver が返すのは versioned protocol (contract `1346c20b`, pin `511c9538`、
  path = `output/s8b-freeze/floor-protocols/1346c20b...--511c9538....json`)
- `_authority()` が読むのは legacy fixed path の document (contract `e576e9cd`, pin `d706650c`)
- → 必ず不一致 → `HoldoutAdmissionError`

**よって gate 2 は t657 では解消しない。** 段 2 プランの「第二の主 gate」判定と一致する。

### 副次的な好材料 — one-shot claim key は pin を含む

`_key_fields()` (:492-) の引数に `ccbench_pin` が入っており、
`# protocol_sha256 is deliberately evidence only and must never enter here.` と明記されている。
→ pin が変われば claim key も変わるため、旧 pin の測定と新 pin の測定が
同じ one-shot claim を共有する事故は構造的に起きない。
束縛を緩めるうえでの障害にならない。

**帰結 (裁定の前提を覆す新事実):**
[T-987] の再裁定は「待つ相手 ([T-478] (d)) が保留確定の機構であり事実上の無期限凍結になる」
ことを、択 (a) を採らない理由として明示していた。しかし待つ相手である世代移行は
**保留どころか本日ユーザー指示で稼働中**であり、床値 v2 を解ける target pair
(`1346c20b`, `511c9538`) まで確定している。t657 が着地すれば、
床値 v2 の再測定は**束縛を一切緩めずに**着手可能になる。
