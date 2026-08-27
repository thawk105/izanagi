# 親の独立実測 (段 3 と並行して取得。段 4 裁定と段 5 実装の入力)

## M1. trigger driver は公開関数を通らない内部経路を持つ (プランの主張は正しい)

`orchestrator/campaign/p3_s4_loop_trigger_gating.py:1011` の `drive_iteration` は
公開の `run_one_iteration` (:793) ではなく `_run_one_iteration_resolved` (:692) を直接呼ぶ。
公開関数だけに関門を置くと trigger の実走経路には効かない。

## M2. 識別子を cfg へ入れなければ golden identity は動かない (プランの主張は正しい)

`orchestrator/campaign/ident.py:150-177` の `canonical_preimage` が覆うのは
`spec_content` / `ccbench_commit` / `search_tag` / `search_config` / `trial` だけである。
封印済み識別子を `search_config` へ入れない限り、campaign identity は 1 bit も動かない。

## M3. 生きた受理記録は存在しない。projection 閉包の変更は何も失効させない

- 事前登録 §5 の 10 欄はすべて `未記入` である
  (`docs/phase3-b4-reflux-ablation-preregistration.md:150-165`)。
- `p3_b4_admission_record.py:81-88` の `_RESERVED_SENTINEL_RE` は `未記入` を予約 sentinel として
  拒否するため、現行の文書を指す受理記録は原理的に検証を通らない。
- repository 内に `p3-b4-prerun-admission/v1` の実成果物は無い (insight 台帳の写しだけ)。

したがって **(P4) 新 module を `projection_closure_manifest` へ入れる費用は今なら 0 である。**
既存 receipt も既存受理記録も存在しないため、失効させるものが無い。後から入れるほど高くつく。

## M4. **今日ただちに生きている穴は bootstrap である** (これが本 wave の正例)

`p3_s4_loop.py:1197-1233` の `b4_bootstrap` 経路は、iteration 0 かつ whiteboard が空のとき
**receipt を要求しない** (`B4IterationAuthorization(receipt=None, ...)` を返す)。
受理記録は production factory 側にしか無いため、bootstrap は受理記録も閉じた critic も通らない。

つまり現状、`main --b4-reflux-ablation --run-iteration` を bootstrap 状態で叩くだけで、
**受理記録を一度も検証せずに B-4 識別子付きの certified campaign を作れる。**
`run_one_iteration` の直呼びに至っては marker すら要らない。

**負例はこの経路を必ず含めること。** 起動器の bootstrap は、loop 側の bootstrap が receipt を
要求しないにもかかわらず、**受理記録の検証を必須にしなければならない。**

## M5. 内容走査型の在庫検査

`materials/inventory-tests.md` を参照。17 file・22 箇所。
