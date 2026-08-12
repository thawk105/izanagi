# 段 4 裁定追補 1 — 子 A の fail-closed 停止 (schema 不足 5 点 + 封印統合) への裁定

子 A は実装せず停止し、schema への要求 5 点と統合問題 2 点を返した。全点 real と裁定し、
以下を確定する。**本追補は s4-adjudication.md に対して優先する。**

## 裁定 A-i: effect 入口の gate は launch authorization witness (s4 裁定 3 の実装形を訂正)

- slice 1 の `validate_t810()` は `run_authorized=True` を拒否する (dormant seal が閉じていることの
  検査、`orchestrator/campaign/t810_validator.py:1365-1366`)。これは不変条件 2 で保護される。
- したがって effect 入口 (scheduler adapter・qdel・benchmark 実行) の封印検査に prereg の
  `run_authorized` を使わない。代わりに **`t810-launch-authorization/v1` witness** を新設する:
  `schema_version`, `approval_id`, `preregistration_sha256`, `policy_sha256`, `run_kinds`
  (⊆ {builder, liveness, main}), `issued_on`, `nonce`。
- effect 入口は「witness が引数として与えられ、schema valid、digest 一致、対象 run_kind を含む」
  ときだけ進む。**witness を発行する経路は本 wave に作らない** (人間の第 1 段承認 ID [§9.1 item 6]
  が実体で、trust root 不在の限界は [T-868] と同じ limitations 宣言)。CLI・設定・環境変数から
  witness を合成する経路を作らない。テストだけが dict literal で witness を構成してよい。
- coordinator は validator へ**別途 dormant load した prereg** を渡す (pre/post とも)。
  `request_t810_launch()` は使わない。

## 裁定 A-ii: schema 改訂 5 点 (単位 S の改訂として実装)

1. node-event `preflight` payload の `submission_argv_match` (自己申告 boolean) を廃し、
   `observed_submission_argv` (非空 str 配列、wrapper が観測した投入 argv の生値) に置き換える。
   照合は coordinator が exact 再計算する。
2. reason code 語彙へ追加 (すべて境界 post_release → `post_release_pre_measurement_invalid`):
   `release-marker-mismatch`, `ack-missing`, `ack-unknown-slot`, `ack-duplicate`。
3. coordinator-event `start_ack_received` の details へ `accepted` (bool) と `reason_codes`
   (str 配列、空可) を追加する。
4. terminal-state の `post_validator_receipt_sha256` は**全状態で必須 (非 null)** とする。
   §6.3 の pre/post 同一 validator は attempt の終端状態によらず走る (validator は dormant prereg
   で動くので封印と両立する)。
5. `t810-launch-authorization/v1` schema を追加する (裁定 A-i の field)。

## 子 B / 子 C への指示訂正

- prompt 中の「`run_authorized` を再検査」はすべて「launch authorization witness の検証」と読み替える
  (witness 引数なし・不正・run_kind 不一致は deny)。prereg loader の API はこの目的では使わない。
