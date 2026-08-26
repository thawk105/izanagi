## must-fix

### MF-01 — `requested_model` は schedule の必須 authority になっていない

- **ID:** MF-01
- **対象の文:** §5.2 `MODEL` 行の「`requested_model` を schedule slot から受ける」、`_supervise_one` 行、validator 行、および §14・総括の「model 軸の配線は完了・着地済み」
- **主張:** schedule で `requested_model` を省略すると `MODEL` へ既定化される。さらに旧 `_codex_exec_argv` 呼出しも `MODEL` 固定へ戻る。したがって単一 hard-code を routing authority から除いた、という到達度は強すぎる。
- **一次資料:** `docs/phase3-t189-model-routing-preregistration.md:186,191,196,1011,1059`、`tools/codex_reasoning_ab.py:3893-3903,7130,9034-9041`
- **重大度:** must-fix
- **代案の文:** 「**部分実装**。`requested_model` が schedule に明示された経路では allowlist 検査、argv、receipt への伝播が成立する。**閉じていない面**: schedule で同 field を省略すると `MODEL` へ既定化され、旧 `_codex_exec_argv` 互換呼出しも `MODEL` を使用するため、schedule はまだ唯一の routing authority ではない。」

### MF-02 — `supervise_pair` は sol/luna pair を要求していない

- **ID:** MF-02
- **対象の文:** §5.2 `supervise_pair` 行の「同一 task の sol/luna block を検証」、validator 行の「model の paired schema」
- **主張:** block 検査が要求するのは二行と、異なる `(arm, requested_model)` tuple が二つあることだけである。同じ model でも arm が異なれば通るため、sol と luna が一回ずつ存在する保証はない。
- **一次資料:** `docs/phase3-t189-model-routing-preregistration.md:192,196`、`tools/codex_reasoning_ab.py:9193-9213`。特に `len(arm_model_pairs) == 2` だけで、model 集合を `MODEL_ALLOWLIST` と一致させる検査がない。
- **重大度:** must-fix
- **代案の文:** 「**部分実装**。同一 task・stage・cache・price の二行を連続 block として検査し、二つの `(arm, requested_model)` tuple が異なることは要求する。**閉じていない面**: model 集合を sol/luna 各一回へ固定しておらず、同一 model の二行も arm が異なれば受理する。」

### MF-03 — 「schedule の canonical digest を全 artifact へ束縛」は別の二 digest を混同している

- **ID:** MF-03
- **対象の文:** §5.2 `supervise_pair` 行の「schedule の canonical digest を exact 検査し、attempt ledger・launch/completion・返却値を同じ digest へ束縛する」
- **主張:** schedule 自身は raw bytes を比較して SHA-256 を算出する。その schedule SHA は launch receipt に入るが、reserved/completion ledger と返却値に入るのは `task_manifest_sha256` である。「同じ schedule digest」が全箇所へ伝播する実装ではない。
- **一次資料:** `tools/codex_reasoning_ab.py:7411-7426`、schedule SHA の launch 伝播は `:7521,7297`、task-manifest digest の ledger/completion/返却値は `:7500-7509,7339-7342,7668-7675`
- **重大度:** must-fix
- **代案の文:** 「`supervise-pair` は schedule bytes を run root へ exact 固定し、その SHA-256 を launch receipt へ残す。別に、schedule 内の `task_manifest_sha256` を canonical task-manifest digest と exact 比較し、この digest を attempt ledger・launch/completion・返却値へ伝播する。」

### MF-04 — `collect-run` CLI には `MODEL` 既定値が残る

- **ID:** MF-04
- **対象の文:** §5.2 `collect_run` 行の「`expected_model=MODEL` 既定値を廃し slot 由来を検査」、総括の「`collect_run` も着地済み」
- **主張:** Python API の引数は必須になったが、standalone `collect-run` CLI の `--expected-model` は依然 `default=MODEL` である。表自身の「実装済みは内部 API と CLI の双方」という定義に反する。
- **一次資料:** `docs/phase3-t189-model-routing-preregistration.md:171,194,1059`、必須 API は `tools/codex_reasoning_ab.py:8004-8017`、CLI 既定値は `:11895-11908`、その値の伝播は `:12098-12111`
- **重大度:** must-fix
- **代案の文:** 「**部分実装**。内部 API と material replay は期待 model を明示的に受けて検査する。**閉じていない面**: standalone `collect-run` CLI の `--expected-model` は未指定時に `MODEL` を使い、schedule 由来ではない。」

### MF-05 — v3 の task/arm cardinality は manifest 由来ではない

- **ID:** MF-05
- **対象の文:** §5.2 `TASK_MANIFEST` 行の「v3 schedule 経路では task/arm の cardinality を manifest 由来で検査する」、§14・総括の残余一覧
- **主張:** v2 と version 欠落が `LEGACY_EXPECTED_SCHEDULE` 固定なのは正しい。しかし v3 の期待件数は、検査対象 schedule 自身の slot を数えて作られる。`_validate_schedule` の実測件数も同じ schedule から数えるため、manifest に独立登録された cardinality との比較ではない。
- **一次資料:** v2 固定は `tools/codex_reasoning_ab.py:2990-2996,9106-9117`。v3 の自己導出は `:2997-3011`、同じ schedule からの実測値との比較は `:9124-9152,9181-9191`
- **重大度:** must-fix
- **代案の文:** 「**部分実装**。外部 task manifest は 10 verb から読み込まれ、v3 schedule の task identity と task 別 known finding 集合を manifest 由来で検査する。paired block の形も検査する。**閉じていない面**: v3 の task/arm 期待件数は manifest に独立登録されず schedule 自身から導出されるほか、v2 と `schema_version` 欠落経路は `LEGACY_EXPECTED_SCHEDULE` 固定である。」

  §14・総括の「残余は3つ」も、v3 cardinality の未束縛を加えて訂正する必要がある。

### MF-06 — §10 の無条件 fail-closed 文は `{null}` 受理と矛盾する

- **ID:** MF-06
- **対象の文:** §10「上記項目が欠落する場合、schedule を無効化する」
- **主張:** 同節は全 slot `{null}` を許すと明記しており、実装も all-null の場合は price snapshot を検査せず受理する。現在の文は全 schedule に price binding が必須であるように読める。
- **一次資料:** `docs/phase3-t189-model-routing-preregistration.md:670-673,710-711`、null の受理は `tools/codex_reasoning_ab.py:2783-2801,8943-8955,8982-8989`
- **重大度:** must-fix
- **代案の文:** 「schedule が非 null の price binding を選ぶ場合、全 slot は同じ凍結 `price_version` を参照し、上記 binding 項目の欠落は schedule を無効化する。全 slot `{null}` の schedule は price 未束縛として別に受理する。」

## should-fix / nit

### SF-01 — 「外部 manifest なら snapshot oracle 必須」には同一 digest の例外がある

- **ID:** SF-01
- **対象の文:** §5.3「外部 manifest を使う prompt は同じ digest を持つ snapshot oracle を要求する」
- **主張:** 発火条件は外部 file を指定したかではなく、その canonical digest が組込み `TASK_MANIFEST` と異なるかである。同一内容の外部 manifest なら snapshot oracle 無しで通る。
- **一次資料:** `docs/phase3-t189-model-routing-preregistration.md:263-265`、`tools/codex_reasoning_ab.py:3465-3482,3552-3555`
- **重大度:** should-fix
- **代案の文:** 「組込み `TASK_MANIFEST` と異なる canonical digest の manifest を使う prompt は、同じ task-manifest digest を持つ snapshot oracle を要求する。prompt receipt は task-manifest digest を常に、snapshot oracle が指定された場合はその digest も記録する。」

## 親の裁定への反論

「部分実装」の追加自体には反対しない。今回まさに、二値では正確に書けない model authority と cardinality の状態が残っている。ただし親はその語を追加しながら、MF-01、MF-02、MF-04 の model 系行を「実装済み」に残し、MF-05 の閉じていない面を列挙し切れていない。適用が裁定自身の義務を満たしていない。

`_aggregate_verified` / `_replay_manifest` の status を「実装済み」に維持した裁定には賛成する。`_AXIS_FIELDS` と集計は閉じており、費用の partial は別軸の限定である (`tools/codex_reasoning_ab.py:9581-9587,10090-10107,10381-10425`)。

§13・§14・総括への scope 拡大にも賛成する。費用の古い到達度を残さないために必要だった。ただし拡大先へ「model 軸の配線は完了」「残余は3つ」という別の過大主張を複製したため、MF-01、MF-04、MF-05 の修正閉包に含める必要がある。

## 総括

結論は **must-fix 6件、should-fix 1件**。特に model routing authority、sol/luna pair gate、v3 cardinality の三点は、実装より高い到達度になっている。

名指しされた残りの検査結果は次のとおり。

- task-specific 入力処理層の文は正しい。task 選択、session・rollout・prompt-source pin、artifact 集合照合は `tools/codex_reasoning_ab.py:3461-3504,3518-3555` にある。`new_root` と snapshot oracle が CLI 入力で、standalone `verify-snapshot` に `--task-manifest` が無いことも `:11864-11874` と一致する。
- blind verdict の manifest 全体 union は `:11506-11516`、reveal 後の集計での task 別集合は `:10175-10184` にあり、対象文は正しい。
- §10 の指定文は、費用層が無効化理由を追加するかという因果的な読みでは D932 と一致する。通常の観測不能は `unavailable` / `not-incurred` を返し (`:9613-9656,9723-9730`)、malformed は共通 reasons へ入り (`:9732-9749,9819-9835`)、最終 `valid` を落とす (`:10502-10510`)。D932 の逐語 `d932.md:3-7` の範囲内で、新しい gate の密輸はない。
- 逆向きの誤りとして、`_aggregate_verified` を未到達へ落とすべき根拠はない。`_load_adjudication` の task-specific oracle 対応を未実装とする記述も実態と一致する。

補助行番号22件は全件一致した。

```text
MODEL 95; MODEL_ALLOWLIST 3643
TASK_MANIFEST 265; EXPECTED_SCHEDULE 331; KNOWN_FINDINGS 337
_normalized_exec_argv 3678; _launch_identity_value 3731; _codex_exec_argv 3886
_supervise_one 7110; supervise_pair 7373; _verify_launch_receipt 7696; collect_run 8004
validate_nullable_dimensions 2819; _slot_dimensions 8998; _validate_schedule 9097
_load_adjudication 9238; _aggregate_verified 10078; _replay_manifest 10738
make_packets 11285; append_verdicts 11528; freeze_verdicts 11608; reveal_mapping 11697
```

文書全体を打切りなしで検索した。古い「費用の正規化計算は未実装」「正規化 cost の値は生成しない」「task manifest の CLI 入力が無い」に相当する表現は 0 件だった。一方、model 到達度の全件検索では §5.2、§14、総括に同じ過大主張が残ることを確認した。pytest は実走しておらず、結論は指定どおり静的検査による。