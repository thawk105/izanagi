静的検査のみで判定した。pytest と変異ハーネスは実走していない。

### [A-1] membership 検査は局所的には発火するが、現行の受理集合に対しては恒真である

**確信度**: high

**根拠**:

事実:

- plan は snapshot 関連検査がすべて成功した run だけを `snapshot_verified_run_ids` に加える設計である。`s2-plan-out.md:79-89`
- 開始済み run について、集合へ加えられない原因はすでにすべて既存理由になる。
  - schedule snapshot SHA 不一致: `tools/codex_reasoning_ab.py:10011-10015`
  - submodule 不一致: `tools/codex_reasoning_ab.py:10016-10022`
  - canonical replay 不一致、pre/post 不一致: `tools/codex_reasoning_ab.py:10023-10029`
  - `verify_snapshot` その他の例外: `tools/codex_reasoning_ab.py:10111-10145`
- plan はこれらの既存理由を消さない。`s2-plan-out.md:113-114`
- 未起動 run は `output_sha256` を持たない。`tools/codex_reasoning_ab.py:9917-9965`
- その run を mapping に載せると、read-time、freeze、revealed mapping、packet body の output SHA 結線が既存理由になる。`tools/codex_reasoning_ab.py:8862-8905`
- 最終的な `valid` は `not reasons` だけで決まる。`tools/codex_reasoning_ab.py:9557-9562`

推論:

- 公開入口から得た manifest と通常の安定した artifact 状態では、`mapping run_id not in snapshot_verified_run_ids` なら、membership 理由を追加する前から、または同じ replay 中に、必ず既存理由が存在する。
- したがって predicate 自体は空集合を直接渡せば false になるが、`valid:true` だった manifest を新検査だけで `valid:false` にする入力は plan からは構成できない。「受理済み report に限れば membership は恒真」である。
- `s1-brief.md:87-91` の「実装すると `valid` の受理集合が狭まる」は、この membership 検査については成立しない。

**成り立たなくなる条件**: 既存 snapshot 理由を `valid` から外す、独立した外部 evidence 集合を受け入れる、または既存理由が空のまま membership だけ失敗する公開 manifest を提示できた場合。

**成果物影響**: membership 検査単独では受理集合を狭めず、材料レポートには新 field と既存失敗への重複理由だけが増えるため、「受理集合を狭めた」という材料値は誤りになる。

### [A-2] prelaunch 負例は新検査の発火証明にならず、plan の seam 負例も manifest 負例ではない

**確信度**: high

**根拠**:

事実:

- prelaunch attempt は snapshot replay を通らず `grouped` に入り、その場で `continue` する。`tools/codex_reasoning_ab.py:9899-9965`
- `final_attempts` は最大 attempt を無条件で選ぶ。`tools/codex_reasoning_ab.py:10156-10160`
- しかし正常な `make_packets` は final attempt の `output` descriptor を必須とし、未起動 attempt はここで `ValidationError` になる。`tools/codex_reasoning_ab.py:10330-10335`
- packet 一式を手で作っても、`output_sha256=None` に対して `_load_adjudication` の既存 SHA 検査が理由を積む。`tools/codex_reasoning_ab.py:8862-8905`
- `_load_adjudication` の早期 return は、artifact 読み込み失敗、配列欠落、`judgments` 非配列である。`tools/codex_reasoning_ab.py:8696-8713`, `8733-8736`, `8793-8796`
- それ以外では bijection や digest の理由が積まれても loop と join は続き、最後にまとめて返す。`tools/codex_reasoning_ab.py:8741-8749`, `8761-8792`, `8811-8907`
- started attempt 内の `ValidationError` は `replay failed` 理由と technical-invalid attempt に変換される。`tools/codex_reasoning_ab.py:10111-10145`
- plan 自身も P1 を到達不能と訂正している。`s2-plan-out.md:1-19`
- 代替負例は、正常な `_full_manifest` から wrapper が検証済み集合の要素を人為的に除く方式である。`s2-plan-out.md:130-131`

推論:

- prelaunch manifest は membership 検査へ到達できても、既存 SHA 理由が必ず併発するため、新検査の純増検出力を証明しない。
- wrapper 負例は membership append の局所効果を証明できるが、manifest から evidence が導出される本番経路の負例ではない。新検査を発火可能にするため、本番 invariant をテスト側だけで破っている。

**成り立たなくなる条件**: wrapper を使わず、同じ公開 API と evidence 導出を通り、既存 `reasons` が空のまま membership 理由だけが出る manifest を用意できた場合。

**成果物影響**: seam 負例を実 manifest の負例として記録すると、材料レポートの受理集合を実際より狭く説明し、発火実測の参照先も誤る。

### [A-3] C1からC6は静的には殺せるが、C4からC6は受理集合の純増を証明しない

**確信度**: high

**根拠**:

| 変異 | 静的判定 | 理由 |
|---|---|---|
| C1 | 赤にできる | literal の exact comparison が `certified` の追加要素を検出する。`s2-plan-out.md:124-128`, `149-150` |
| C2 | 赤にできる | 同じ exact comparison が `"packet"` 欠落を検出する。`s2-plan-out.md:151-153` |
| C3 | 赤にできる | 同じ exact comparison が requirement 値の変更を検出する。`s2-plan-out.md:155-156` |
| C4 | seam node だけが赤になる | 検証成功済み集合を wrapper が人為的に欠損させるため、membership append を削除すると report が再び valid になる。`s2-plan-out.md:130-131`, `158-159`。現行の manifest 導出からこの状態へ至る根拠はない。 |
| C5 | spy assertion なら赤になる | mismatch case の既存 `"snapshot oracle replay mismatch"` は変異前後とも残る。`tools/codex_reasoning_ab.py:10023-10029`。report の赤では区別できず、渡された集合が空かを直接見る新 spy だけが変異を殺す。`s2-plan-out.md:133-140`, `161-162` |
| C6 | call-count assertion なら赤にできる | 現行の path-only cache は同一 path の二回目を呼ばない。`tools/codex_reasoning_ab.py:10023-10029`。二回目の descriptor 検査が通るよう、artifact を一行目終了後から二行目開始前に A から B へ変える fixture が必要である。`s2-plan-out.md:164-165` |

事実として、C1からC3は宣言文字列だけを固定する変異であり、実装との対応を検査しない。C5 の mismatch は membership の有無にかかわらず既存理由ですでに `valid:false` である。C6 は現在の実装そのものが path-only なので、既存 node はこの変異を殺していない。

推論として、変異一覧は「各コード片にテストが接続されている」ことは示せるが、「公開 manifest の受理集合に純増検出力がある」ことは示さない。特に C4 の killer は本番では生成不能な引数状態である。

**成り立たなくなる条件**: C4 node が wrapper 注入ではなく公開 manifest だけで membership 単独失敗を作る場合、または C5 node が集合 spy 以外に既存理由のない report 反転を示す場合。

**成果物影響**: 変異台帳をそのまま発火証拠として引用すると、局所配線の被覆率を材料レポート受理集合の検出力として誤記する。

### [A-4] cache 強化が実際の受理集合変更を担い、membership 検査へ誤帰属される

**確信度**: high

**根拠**:

事実:

- 現行コードは path-only cache の内側に `verify_snapshot`、canonical replay、pre/post equality のすべてを置く。`tools/codex_reasoning_ab.py:10023-10029`
- plan は key を path、descriptor SHA、case に変更し、pre/post equality を cache miss 分岐の外へ移す。`s2-plan-out.md:79-87`
- これにより、同じ oracle path を再利用した後続 run の pre/post mismatch は、現行では skip されるが変更後は既存理由 `"pre/post snapshot oracle mismatch"` になる。
- C6 node は membership check ではなく、この cache/evidence refactor を固定する node である。`s2-plan-out.md:133-140`, `164-165`

推論:

- この wave 後に受理集合が狭まる入力が存在するとしても、その反転を起こすのは `_load_adjudication` の membership 理由ではなく、`_replay_manifest` で新たに実行される既存 snapshot 検査である。
- 「検査は材料 packet の join 一箇所」という説明と、実際の受理集合変更箇所が一致しない。cache 修正が sound evidence 導出に必要なら、別の正しさ変更として明記すべきである。

**成り立たなくなる条件**: cache と pre/post の変更を wave から外す、またはそれらが拒否する全入力が現行の別理由でも必ず拒否済みだと証明できた場合。

**成果物影響**: 新たに拒否される manifest の failure reason と受理集合差分が membership 検査ではなく replay cache 修正由来になり、材料レポートの検査箇所と変異参照が変わる。

### [A-5] `source_run_snapshot_verified` は既知限界を表さず、文字どおりには実装より強い

**確信度**: medium

**根拠**:

事実:

- 宣言値は `material_packet_requirement: "source_run_snapshot_verified"` である。`s2-plan-out.md:48-67`
- replay が実際に再検証するのは、report 作成時に `oracle["snapshot"]` が指す現在の filesystem である。`tools/codex_reasoning_ab.py:10023-10029`
- supervisor は実行前後に `verify_snapshot` を行い、その時点の canonical equality を記録する。`tools/codex_reasoning_ab.py:6854-6856`, `7012-7029`
- plan 自身が「過去の各 run 時点の snapshot は再構成しない」「実験後に同じ bytes へ戻す攻撃は扱わない」と認めている。`s2-plan-out.md:171-173`
- この限定は提案された machine-readable field には含まれず、docs 追加も変更計画にはない。`s2-plan-out.md:93-120`

推論:

- `"source_run_snapshot_verified"` を「source run が実際に見た歴史的 snapshot が認証された」と読むと、実装は replay 時の現物と凍結 pre/post evidence の一致までしか保証しないため、宣言が強すぎる。
- identifier を `"source_run_snapshot_evidence_replayed"` のように証拠検査へ限定するか、脅威モデルと時点を機械可読または正本文書で定義する必要がある。

**成り立たなくなる条件**: `"source_run_snapshot_verified"` を「凍結 pre/post evidence と replay 時現物の検査成功」と正式に定義し、その定義を report 消費者が必ず参照できる場合。

**成果物影響**: 現状の field を論文から引用すると、歴史的 snapshot 同一性まで certified だと読め、保証範囲と proof-chain の意味が実装より強くなる。

### [A-6] 親 brief の実測表には三つの過一般化があり、P1 の根拠にはならない

**確信度**: high

**根拠**:

| brief 行 | 判定 | 実装上の根拠 |
|---|---|---|
| `s1-brief.md:26` | verifier 文脈なら概ね正しいが、「`_replay_manifest` だけ」は全体では誤り | supervisor も実行前後に `verify_snapshot` を呼ぶ。`tools/codex_reasoning_ab.py:6854`, `7014`。cache key が path-only なのは正しい。`10023-10029` |
| `s1-brief.md:27` | replay 中に検証しないことと `grouped` へ入ることは正しい。「一度も snapshot 検証を通らない」は過一般化 | `verify_snapshot` 成功後の version probe、Popen などで prelaunch 失敗する場合がある。`tools/codex_reasoning_ab.py:6854-6928`, `7206-7253` |
| `s1-brief.md:28` | 正しい | 最大 attempt を選ぶ。`tools/codex_reasoning_ab.py:10156-10160` |
| `s1-brief.md:29` | report verifier の join 点という限定なら正しい。全コードで唯一は過一般化 | packet/run mapping は `make_packets` で作られ、`reveal_mapping` でも出力される。`tools/codex_reasoning_ab.py:10348-10355`, `10696-10710`。`_load_adjudication` の bijection が snapshot evidence を見ない点は正しい。`8782-8792` |
| `s1-brief.md:30` | 正しい | return dict と `valid:not reasons`。`tools/codex_reasoning_ab.py:9557-9580` |
| `s1-brief.md:31` | snapshot/oracle を参照しない点は正しい。「output bytes を写すだけ」は過一般化 | schedule の正規化、cardinality、slot 集合も検査する。`tools/codex_reasoning_ab.py:10265-10302` |
| `s1-brief.md:32` | 正しい | aggregate/verify は結果を受け、最後に stdout へ canonical bytes を書く。`tools/codex_reasoning_ab.py:11018-11025`, `11082-11083` |

P1 は `continue`、final 選択、run ID bijection だけをつないでいるが、packet 生成時の必須 output descriptor と report join 時の SHA equality を含めていない。`s1-brief.md:63-70` の到達可能性根拠は成立せず、plan の P1 訂正が正しい。ただし、その訂正は同時に `s1-brief.md:87-91` の受理集合縮小も否定する。

**成り立たなくなる条件**: P1 が想定する未起動 final attempt に、既存 API を通して正しい output descriptor と SHA-bound packet 一式を生成できる経路が別に存在する場合。

**成果物影響**: brief の P1 と受理集合差分を根拠にした材料レポート記述は撤回が必要で、参照すべき実測は「prelaunch は到達不能」「cache 強化だけは別差分」に変わる。

## 総括

- 段 4 では、membership 検査が公開 manifest の受理集合に対して冗長であり、seam 負例を発火証拠として認めるかを必ず裁定する。
- P1 と「membership により受理集合が狭まる」という親 brief の記述は同時に撤回する必要がある。
- cache key 強化と run ごとの pre/post 再検査を、この wave の別の正しさ変更として採るか、scope から外すかを決める。
- 変異結果は局所配線の証拠と manifest-level の純増検出力を分けて記録する。
- `source_run_snapshot_verified` を歴史的事実ではなく replay evidence の検査として定義するか、より弱い identifier へ変更する。