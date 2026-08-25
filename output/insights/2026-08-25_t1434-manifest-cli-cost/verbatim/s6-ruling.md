# 段 6 裁定 (段 4 裁定への追補) — [T-1434]

- レビュー A (正しさ境界): `s6-reviewA.md` (rc=0)、must-fix 5 件、検出力の無いテスト 21 件、総括 NO-GO
- レビュー B (変更閉包・実効性): `s6-reviewB.md` (17399 bytes、rc=0)、must-fix 5 件、総括「未閉包」
- 親の焦点走: 559 passed / 2 skipped / 0 failed (144.15 秒)

**両レンズが独立に NO-GO を出した。559 件緑を正しさの証拠として採らない。**
レビュー A が「実装を壊してもそのテストが緑のまま通る変異」を 21 件挙げたことが決定的である。

## 1. 採用する must-fix (実装必須)

| # | 出所 | 内容 | 成果物影響 |
|---|---|---|---|
| F1 | A-1 | 非ゼロ token を持つ起動前失敗 row が `not-incurred` として valid report に残る。marker が token 値より優先される | 矛盾した ledger が valid のまま残り、当該試行が分母から消えて合計費用を過小化・平均を過大化できる |
| F2 | A-2 | `verify-snapshot` が先行 oracle の digest を受け取らず、snapshot を別 manifest へ再ラベルできる | snapshot 作成時の task 解釈から adjudication の受理集合への交換が最終報告まで検出されない |
| F3 | A-3 | `append-verdicts` が既存 verdict log row の digest を検査せず、A/B 混在 log へ追記できる | 返す `verdict_log_sha256` が別 manifest の行を含む方向へ受理集合が広がる |
| F4 | A-4 / B-4 | material manifest の再読失敗が「descriptor 無し」に化け、valid report から費用が全欠落する | bound v3 report が valid のまま費用証拠を黙って全部落とす |
| F5 | A-5 | price snapshot が schedule 検査と cost loader で 2 回読まれ、裁定 §4 B-2 の一度読み契約に違反する | 同じ schedule がファイル変更時刻により受理・拒否へ分岐し、費用 ledger の生成集合が変わる |
| F6 | B-2 | `render-prompt` だけ既定 manifest の provenance を読み、外部 manifest の digest を掲げた run が既定 task の prompt を実行できる | task manifest に束縛されたと見える run が別 task の入力を処理し、実験の task identity が偽になる |
| F7 | B-3 | 費用の `unavailable` 診断が共有 `reasons` へ入り、certified な `valid` と全 judgment を落とす | 費用を算出できないだけで従来有効な報告が invalid になる。裁定 §3 (費用を gate にしない) に正面から反する |
| F8 | A nit | 軸 row に `unavailable_count` / `not_incurred_count` / `scheduled_attempt_count` が無く、`attempt_count` が観測済みだけを指すことが機械可読でない | F7 で `valid` を戻すと、下流が `attempt_count` を予定数と取り違えて平均を過大化できる |

**F7 と F8 は対で実装する。** レビュー A は「`valid` が false になるから過大平均は通らない」と述べ、
レビュー B は「費用が `valid` を殺すのは誤り」と述べた。両立させる唯一の形は
**費用は `valid` を動かさず、分母の内訳を機械可読にする**ことである。

## 2. real だが不採用 — B-1 (後方互換の破壊)

レビュー B は「digest を無条件に要求するため、旧 v2 schedule・全 null v3・旧 material/packet が
入口で落ちる。破壊範囲は 11 成果物族」と指摘した。**事実だが、これは意図した狭めである。**

- 段 4 裁定 §2 は、digest 無しの成果物を受理すれば manifest 交換の穴が開いたままになると定めた。
  digest 欠落を受理する方向へ戻すことは、絶対規律 2 に反する。
- レビュー B 自身が「legacy shape 自体は受理される。必要なのは digest field の付与だけ」と実測した。
  拒否されるのは形式ではなく、由来を証明できない成果物である。
- 実験は未開始であり、repo 内に該当する実成果物は price snapshot と抜粋だけで、
  これらは digest の対象外である (レビュー B の実測)。

**ただし親の側の誤りを訂正する。** 段 4 で登録した過剰拒否の正例 P02 / P04 は
「v2 legacy と全 null v3 が従来と同じ受理」と書いたが、正確には
**「digest を付けた v2 legacy と全 null v3 が受理され、費用 key を出さない」**である。
下記 §4 で書き換える。

**採用する小さな手当て:** digest 欠落の拒否 message に、
「この成果物は digest 束縛より前に作られたため再生成が要る」と読める文言を入れる (診断性)。

**裁定パッケージへ回す:** `SCHEMA_VERSION` を 2 のまま受理形を変えた点。
世代を schema で区別する移行契約は、本 wave の scope を超える。

## 3. 検出力の無いテスト (レビュー A の 21 件) の扱い

**登録変異に対応するテストだけを本 wave で強化する。** 登録した変異が生存するなら、
それは harness の失敗であって backlog ではない。

強化必須 (登録変異に対応):
`test_m01_*`、`test_m02_*`、`test_m03_*`、`test_m04_*`、`test_m07_*`、`test_m10_*`、
`test_m15_*`、`test_m16_*`、`test_p01_*`、`test_m08_p02_p04_*`、
`test_task_manifest_digest_is_recorded_through_packet_freeze_and_reveal`、
`test_material_replay_rejects_task_manifest_exchange_at_digest_consumers`、
`test_default_and_explicit_default_task_manifest_cli_results_are_equal`、
`test_task_manifest_cli_option_surface_is_closed`。

backlog (登録変異に対応しない):
`test_task_manifest_loader_accepts_only_strict_canonical_json_object` の正例のみ性、
`test_cost_constant_false_rejections_are_owned_by_snapshot_validator` の
「cost 実装を消しても緑」性、`test_replay_failure_*` / `test_cost_token_field_unavailable_matrix` の
generic reason 化。理由: これらは実効 gate が上流にあり、
本 wave の受理集合を変える変異と対応しない。

## 4. 変異登録の改訂 (段 4 §5 の erratum)

**取り下げ (単一理由性なし、または production 経路で恒偽):**
M06、M09、M14。加えてレビュー A の指摘により **M10 を再照準**する
(helper 単体でなく、**全経路の read 回数が exact 1** であることを照準する。F5 の修正が前提)。

**分割:** M15 を consumer ごとに分ける。
`supervise-pair` / `collect-run` / `aggregate` / `verify` / `make-packets` /
`append-verdicts` (既存 log 含む) / `freeze-verdicts` / `reveal-mapping` (private mapping 含む) の
各 digest 検査を 1 箇所ずつ外す変異とする。

**追加:**
- M17: 費用の `unavailable` 診断が top-level `valid` を false にする (F7 の逆変異) → KILLED
- M18: 起動前 marker があれば非ゼロ token でも `not-incurred` とする (F1 の逆変異) → KILLED
- M19: `verify-snapshot` が先行 oracle の digest を検査しない (F2 の逆変異) → KILLED
- M20: `render-prompt` が snapshot の digest を検査しない (F6 の逆変異) → KILLED
- M21: 軸 row から分母内訳を落とす (F8 の逆変異) → KILLED

**過剰拒否の正例の書き換え:**

| ID | 入力 | 期待 |
|---|---|---|
| P01 | 凍結 price snapshot + 全 slot が凍結 version + digest 付き schedule | 費用が生成され受理される |
| P02 | **digest 付き**の全 slot `price_version=null` の v3 schedule | 費用 key を出さずに受理される |
| P03 | `--task-manifest` 未指定 (既定 `TASK_MANIFEST`) で、既定 digest を持つ成果物 | 現行と同じ結果で受理される |
| P04 | **digest 付き**の v2 legacy schedule | 従来と同じ受理・同じ出力 (費用 key 無し) |
| P05 | 費用が `unavailable` の試行を含む bound report | **`valid=true` のまま**、費用 key だけが欠け、分母内訳が出る |

## 5. 段 4 裁定への反論の処遇

- レビュー A「裁定の fallback を `verify-snapshot` へ適用できていない」→ **正しい。F2 で是正。**
- レビュー A「`append-verdicts` が §2 の即時拒否要求を満たさない」→ **正しい。F3 で是正。**
- レビュー A「§3 費用を certified と呼ばない判断に反論なし」→ 維持。
- レビュー B「事前登録の到達度は『部分実装』としか書けない」→ **採用。**
  差し替え文面案はレビュー B のものを裁定パッケージの基礎とする。
  「実装済み」と無条件に書けない理由は 5 つある: `render-prompt` の task identity、
  旧 schema の移行契約不在、費用 field の読み手ゼロ、cache-write 数量の不在、
  独立 oracle acceptance の不在。

## 6. fix の分割

編集面は `tools/codex_reasoning_ab.py` と `orchestrator/tests/test_codex_reasoning_ab.py` の
2 ファイルだけで一枚岩であり、所有を素集合に分けられない。**fix 子は 1 本とする**
(`DW-S06-B` の「一枚岩なら理由 1 行を handoff へ残す」に従う)。
