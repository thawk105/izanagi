# [T-1311] arm (on / off / swapped) が実行を変える authority (2026-08-18)

`authority: none` / `default_effect: no-state-change` — 本書は記録であり裁定ではない。
可変状態の正本は `docs/worklog.md` 末尾。一次資料 = 同 dir の `s1-brief.md` /
`s4-adjudication.md` / `mutation-spec.json` / `mutation-out.json` / `verbatim/`。

## 1. 何が問題だったか

8c 正式系列は 2 holdout × 3 arm (`on` / `off` / `swapped`) の 6 cell 比較である。
その arm は**宣言文字列でしかなく、実行を一切変えていなかった。**

- `OriginProducerInputs.enforcement_arm` は呼び手が渡す非空 str で、どの実入力からも導出されない
- 8c supervisor に arm 引数が 1 つも存在せず、descriptor は `WORKLOADS[workload]` だけから作られる
- したがって campaign identity・proposal path・invocation ID も arm 非依存

結果として、同一 holdout の `on` と `off` の label を manifest 内で交換して hash を再生成すると、
trial_id・campaign_id・proposal・invocation・実行 descriptor が不変のまま受入を通った。
acceptance 側の arm 検査は**恒真**であり、規律 3 の「謳うだけで発火しない保証」に該当していた。

さらに `off` の「凍結済み中立入力」は設計文書 (`docs/phase3-8b-descriptor-design.md` §4) に
要求だけがあり、canonical bytes の実体が無かった。

## 2. 何をしたか

arm が選ぶ**実入力 bytes** から二層 digest を導出し、7 つの sink すべてに消費させた。

### 2.1 `off` の中立入力 — canonical bytes を作った

既存 projector `s8b_descriptor.project_from_search_config` を通して生成する。

- 入力: `records=1,000,000`, `threads=48`, `ycsb_rratio="50"`, `ycsb_zipf_skew="0.9"`, `ycsb_rmw="0"`
- canonical bytes = **281 bytes**、sha256 =
  `8ecce69906410c451aa20a242634ba8ce82525636ed912493af6d12487340e89`
- 置き場所 = `output/s8c-preregistration/arm-inputs/off-neutral-descriptor.v1.json` と
  同 dir の freeze sidecar

**値の非恣意性は 2 本の独立根拠が支える** (どちらか一方でも欠けたら生成器は失敗する)。

1. 凍結端点 80 と 20 の算術中点が 50 である (`s8b_holdout_freeze.py` の H1 / H2 定義)
2. 同 module が `_POSITIVE_RATIO = "50"` を `rr50-positive-control` として既に凍結している。
   skew / rmw も同 module の `_FIXED_SKEW` / `_FIXED_RMW` と一致する

手書き literal を使わず projector を通したのは、`source` field が
`campaign_search_config_projection` となり `on` / `swapped` と区別できなくなるためである
(段 3 レンズ A が「`source="human_declared"` は一 field で off を識別でき blind 性が壊れる」と
指摘し、親がこれを採用した)。

### 2.2 二層 digest

- `content_digest = SHA256(canonical_execution_input_bytes(selected_descriptor))`
  — **arm 名を preimage に含めない。** 含めると同一 bytes に別 label を付けただけで別 digest になり、
  「digest が違えば実入力が違う」が崩れる
- `arm_binding_digest = SHA256(domain_separator || holdout || arm || content_digest)`
  — 一層だけでは、resolver 退行で 2 arm が同一 bytes へ潰れた場合を検出できない

加えて **pairwise 非同一検査** — 同一 holdout の 3 arm の `content_digest` が相異なることを
launch 前に要求する。

### 2.3 7 sink

|#|sink|
|---|---|
|1|descriptor (role へ渡す `workload_descriptor` / `descriptor_binding`)|
|2|campaign identity (`search_config` → `cfg_hash8` → campaign_id)|
|3|proposal bytes / path|
|4|invocation namespace (`arm-{arm}.exec-{digest}.{workload}.g{n}.{role}`)|
|5|run-start|
|6|terminal report|
|7|**provider payload / envelope** = 実際に provider へ送った bytes|

第 7 sink は段 6 レビュー A が発見した。当初の 6 sink だけでは
「台帳は off、実 stdin は on」が通る。保存 payload の `workload_descriptor` の canonical bytes から
digest を計算して content digest と照合する。

### 2.4 恒真化の除去

検証側 (`autonomous_trial_completeness.py`) が producer helper
(`_campaign_for` / `_descriptor_for`) を呼んで期待値を作っていた形を撤去し、
persisted campaign lock / config bytes を独立に読む形へ変えた。producer と verifier が同じ関数を
読む限り、`search_config` から digest を落とす変異は 1 件も検出できない。

## 3. 実測

- 焦点走: **733 passed / 0 failed** (11 test file、自走 harness の meta-test 込み、
  main 取り込み後の tip)
- 変異 matrix: **baseline PASSED、KILLED 10 / 10、SURVIVED 0、MISMATCH 0、TIMEOUT 0**
  (`mutation-out.json`)。dispatch runner、11 走行
- 全史 provenance: 3952 件 新規違反なし (単位 A 時点)
- 期待 node は probe 走行 (全件 SURVIVED 期待) で観測集合を集めてから完全集合として再登録した

変異は 7 sink それぞれについて「producer がその sink へ digest を流さない」形を作った。
`t1311.m4-invocation-id-prewave-form` は **wave 前の実コードの形**
(`{workload}.g{generation}.{role}`) そのものであり、これも殺されている。
`t1311.m10-pairwise-distinct-off` は pairwise 検査を無効化する変異である。

## 4. 段 3 / 段 6 の敵対所見

段 3 は 2 レンズとも plan v1 へ NO-GO / hold、段 6 も 2 レンズとも NO-GO を返した。
親が採用した主な所見:

- **[T-1310] 先行必須は過大** (段 3 両レンズ)。H1/H2 の完全定義と `DERANGEMENT` は
  `s8b_holdout_freeze.py` に凍結済みで、arm が選ぶ 3 入力は本 wave で構成できる。
  [T-1310] が要るのは実 benchmark の production profile だけである
- **`source` 一 field による blind 性の破れ** (段 3 レンズ A) → projector 経由生成へ変更
- **digest の一層は不足** (段 3 レンズ A) → 二層 + pairwise
- **第 7 sink の不在** (段 6 レンズ A) → provider payload / envelope を追加
- **権威ある `run_root` の未使用** (段 6 レンズ B)。verifier が report 内の `campaign_root` から
  run root を再導出しており、campaign_root と proposal / provider path を同時に別 tree へ移す入力を
  受理しえた。あわせて正規 build の proposal path を拒否する実バグでもあった
- **新規 test file の自走 harness 欠落** (段 6 レンズ B)。素の実行で 0 件実行の偽緑になる

親が **refuted** と裁定した所見: 全 artifact を再生成する label 交換攻撃 (段 6 レンズ A)。
これは事前登録 commit 束縛と append-only registry の履歴走査が担当する既存機構の射程であり、
arm authority の欠落ではない。ただし**その 2 機構が機械検査対象外のまま**であることは
条件 3 / 8 の現在地として残る (`docs/phase3-8c-preregistration.md`)。

## 5. 成果物影響

これが無い間、8c 正式受入 receipt は**宣言と違う arm で走った run を受理し続けていた**。
本 wave 後は、7 sink のいずれか 1 つでも digest を消費しない producer は acceptance で拒否される。

**ただし receipt は引き続き `certifying=false` かつ `c02-arm-binding-unproven` を必須理由として
保持する。** 証拠契約 C02 は `machine_checkable: false` であり評価器 table にも無いため、
本 wave では充足しない (充足には receipt v2 と `accept_trial` 実名の整備が要る = [T-822] 問 3 側)。
現時点の certified 選択・certifying receipt の受理集合は 1 件も広がっていない。

## 6. 残る限界 (裁定パッケージ候補)

1. **role payload の `workload` token 漏洩。** `_COMMON_PAYLOAD_KEYS` が `"workload"` を含み、
   `_common_payload` が真の workload 名を role へ渡す。`off` arm では descriptor が中立でも
   role は `workload="rr80"` を見るため、descriptor ablation を迂回しうる。
   本 wave の scope 外 (role payload 契約の変更は別の設計択一)。
   成果物影響: 6 cell の on/off 差と swapped 追従を descriptor 効果として解釈できなくなる。
2. **C02 / C10 の充足と production mode 結線。** 上記のとおり本 wave では充足しない。
3. **[T-1310] への申し送り。** 本 wave の resolver が読む `s8b_holdout_freeze.HOLDOUTS` と、
   [T-1310] が入れる production profile が**同一 bytes を指すことを [T-1310] 側が assert する**必要がある。
   二重管理になると、descriptor と実 benchmark が食い違ったまま両方緑になりうる。
