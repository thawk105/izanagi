## (P1) 到達可能性の判定

結論は **到達不能**。親の provisional P1 は途中までは正しいが、現行の正常な artifact pipeline では未検証 final attempt を材料 packet にして `valid: true` まで到達できない。

- `tools/codex_reasoning_ab.py:9900-9965` の prelaunch 分岐は `verify_snapshot` を通らず、`failed_attempt` を `attempts` と `grouped` に追加する。

- `tools/codex_reasoning_ab.py:10156-10165` は最大 attempt を無条件に `final_attempts` へ選ぶため、この未検証 attempt は final になりうる。

- ただし supervisor ledger は未起動 run の `failure_class` を `technical-invalid` または `pair-invalidated` に限定する (`tools/codex_reasoning_ab.py:9630-9667`)。したがって `experiment_complete` は `tools/codex_reasoning_ab.py:9303-9310` で false になる。

- もっとも、`valid` は `experiment_complete` ではなく `not reasons` だけで決まる (`tools/codex_reasoning_ab.py:9557-9562`)。ゆえに `experiment_complete` だけでは P1 を否定できない。実際、`_aggregate_verified` を直接呼べば incomplete かつ `valid: true` は可能である。

- 実際に止める第一の箇所は `make_packets`。prelaunch の `failed_attempt` には `output` がない (`tools/codex_reasoning_ab.py:9917-9962`)。`make_packets` は final の `output` を必須 artifact として開くため (`tools/codex_reasoning_ab.py:10331-10335`)、`_artifact_path` の descriptor 検査 (`tools/codex_reasoning_ab.py:8436-8462`) で失敗する。

- packet 一式を手で組んでこの停止を迂回しても、failed attempt には `output_sha256` がない。`_load_adjudication` は実 packet の SHA と `None` を比較し、read-time mismatch (`tools/codex_reasoning_ab.py:8862-8869`)、freeze mismatch (`:8870-8874`)、revealed mapping mismatch (`:8887-8891`) の少なくとも一つを積む。正常な中間 API は SHA を文字列として生成・検査する (`:10474-10510`, `:10532-10567`, `:10666-10677`) ため、JSON artifact だけで `None == SHA` にはできない。

- その理由が `tools/codex_reasoning_ab.py:9507-9518` と `:9560-9561` に伝播し、最終的に `valid: false` になる。mapping の run_id bijection (`:8782-8792`) だけは通せても、SHA join は通らない。

したがって prelaunch negative manifest を新検査の負例にしてはいけない。それでは既存の `make_packets` または SHA 検査しか試さず、新検査を削除する変異を殺せない。新検査は、正しい adjudication 一式に対して「検証済み run 集合から一つだけ除く」seam injection と、snapshot evidence の生成・伝達を観測する構造検査で非恒真化する。

## (P2) 検査を置く 1 箇所

選択箇所は `_load_adjudication` の mapping loop、現行 `tools/codex_reasoning_ab.py:8811-8813`。

ここでは同時に以下が揃う。

- report の材料となる packet ID
- revealed mapping の run ID
- `final_attempts`
- `_replay_manifest` から渡す snapshot 検証済み run 集合

各 `mapping_row` の `run_id` が集合にない場合、次を `reasons` に一度だけ追加する。

```text
<packet_id>: packet source run is not snapshot-verified: <run_id>
```

落とす候補は次のとおり。

- `_replay_manifest` (`tools/codex_reasoning_ab.py:9781-10199`): snapshot evidence は作れるが、どの run が材料 packet に載ったかをまだ知らない。ここで全 final run を条件化すると、裁定の「材料レポートに載る packet だけ」より広い。

- `_aggregate_verified` (`tools/codex_reasoning_ab.py:9172-9580`): 入力 `verdicts` は slot key に射影済みで、packet ID と revealed run ID の join 情報を失っている。ここへ置くには artifact の再読込か引数の拡大が必要で、join が二重化する。

- `_load_adjudication` は packet と run の既存 join 点そのものであり、検査を追加しても中間層の再検証にはならない。検査ロジックも一箩所に限定できる。

## (P3) 宣言 field の設計

top-level field は `certification_scope`、値は固定 shape の object とする。

```json
{
  "certification_scope": {
    "certified": [
      "aggregate.valid"
    ],
    "uncertified": [
      "packet",
      "packet_state",
      "verdict_log",
      "revealed_map"
    ],
    "material_packet_requirement": "source_run_snapshot_verified"
  }
}
```

自由文ではなく、certified/uncertified の集合と発火条件を別々の machine identifier にする。`material_packet_requirement` を含めることで、宣言と `_load_adjudication` の検査をテストで直接対応させられる。

この field は valid report だけでなく、`sessions_root` 欠落や replay 例外で返る invalid report (`tools/codex_reasoning_ab.py:10208-10213`, `:10228-10233`) にも載せる。「verify/aggregate が返した report object なら常に認証水準を自己記述する」が契約となる。

`SCHEMA_VERSION` は 2 のままとする。理由は report-only の追加 metadata で、既存 field の意味や型を変更せず、同じ定数を使う凍結 artifact まで一斉変更すると不変条件 2 に違反するため。report 専用 schema を新設する判断は本 scope を超える。

## (P4) 検証済み run 集合の導出

`_replay_manifest` の現行 `snapshot_cache` (`tools/codex_reasoning_ab.py:9876`) とは別に、`snapshot_verified_run_ids: set[str]` を作る。

現行の path だけの cache key と、検査途中でも cache へ追加する `tools/codex_reasoning_ab.py:10023-10029` は、そのまま run 集合の根拠にしてはいけない。次の構造へ改める。

1. 成功済み cache key を `(oracle_path.resolve().as_posix(), snapshot_oracle descriptor の sha256, case)` とする。

2. `_artifact_path` が descriptor SHA と現在 bytes の一致を検査する (`tools/codex_reasoning_ab.py:8451-8461`)。同じ path が別内容へ再入した場合、descriptor SHA が同じならそこで拒否され、SHA が異なるなら別 cache key となって `verify_snapshot` を再走する。

3. cache へ入れるのは `verify_snapshot` が正常 return し、canonical replay bytes が oracle bytes と一致した identity だけ。現行のように mismatch reason を積んだ後でも cache へ入れてはならない。

4. `oracle_after == oracle` と両者の bytes 一致は run ごとの証拠なので、cache miss 分岐の外へ出して全 run で検査する。成功済み oracle を共有していても、各 run の pre/post binding は省略しない。

5. schedule snapshot SHA、submodule state、canonical replay、pre/post equality の snapshot 関連理由は局所的な `snapshot_reasons` または boolean で追跡する。その run についてこれらが全て成功した場合だけ `snapshot_verified_run_ids.add(run_id)` する。別 run の既存 `reasons` は集合への追加を妨げない。

6. `verify_snapshot` が例外を投げた run は `tools/codex_reasoning_ab.py:10111-10145` の technical failure へ入り、集合には追加されない。

これにより、同一 oracle identity の成功証拠は安全に共有しつつ、「途中で reason が出た最初の run を cache 済みとして後続 run まで検証済みにする」取りこぼしを防ぐ。

## 変更計画

- `tools/codex_reasoning_ab.py:9169-9172` 付近  
  `_certification_scope()` のような fresh object を返す小 helper を追加する。入力は読まない。`certified`、`uncertified`、`material_packet_requirement` を上記 JSON に固定する。これは理由を生成する検査ではないため、失敗時に積む `failure_reasons` はない。

- `tools/codex_reasoning_ab.py:9557-9562`  
  `_aggregate_verified` の report に `certification_scope` を追加する。既存の `schema_version`、`valid`、`failure_reasons`、`turn_accounting` その他は変更しない。

- `tools/codex_reasoning_ab.py:10208-10213` と `:10228-10233`  
  `sessions_root` 欠落と `ValidationError` fallback report にも同じ field を追加する。既存理由 `"sessions-root is required"` と `exc.reasons` はそのまま保持する。

- `tools/codex_reasoning_ab.py:8687-8694`  
  `_load_adjudication` に必須 keyword-only 引数 `snapshot_verified_run_ids: set[str]` を追加する。default は設けない。呼び忘れを fail-open にしないためである。

- `tools/codex_reasoning_ab.py:8777-8792`, `:8811-8813`  
  revealed `mapping` の各 `packet_id -> run_id` を読み、run ID が `snapshot_verified_run_ids` にないときだけ `"<packet_id>: packet source run is not snapshot-verified: <run_id>"` を `reasons` に積む。既存 bijection、SHA、judgment 検査は削除も短絡もせず、joined verdict の構築も継続する。

- `tools/codex_reasoning_ab.py:9870-9877`  
  成功済み snapshot identity cache と `snapshot_verified_run_ids` を初期化する。cache は path 単独ではなく path、descriptor SHA、case の tuple にする。

- `tools/codex_reasoning_ab.py:10011-10029`  
  schedule SHA、submodule、canonical replay、pre/post の既存検査を、理由文字列を変えずに局所的な成功判定へ結線する。成功 identity だけ cache に入れ、run ごとの pre/post が成功した場合だけ run ID を検証済み集合へ追加する。既存 mismatch reason は一つも消さない。

- `tools/codex_reasoning_ab.py:10161-10167`  
  `_load_adjudication` へ実際に導出した `snapshot_verified_run_ids` を渡す。`_replay_manifest` の返却 tuple は変えず、既存 caller を維持する。

- `tools/codex_reasoning_ab.py:10250-10384`  
  `make_packets` と `_write_frozen_json` 呼出しには触れない。したがって packet-state と custodian mapping の bytes は変わらない。

## テスト計画

- `test_material_report_certification_scope_is_exact_on_all_return_paths`  
  `_aggregate_rows` から作る valid `_aggregate_verified` report、`sessions_root=None` の invalid verify report、`_replay_manifest` が `ValidationError` を投げる fallback report を固定する。全てについて `certification_scope` が上記 JSON と完全一致することを assert する。期待値は production helper を参照せずテスト側へ literal に書き、宣言の自己参照テストを避ける。

- `test_verify_replays_complete_fake_codex_experiment` (`orchestrator/tests/test_codex_reasoning_ab.py:7488-7521`)  
  既存 end-to-end 正例へ exact `certification_scope` assertion を追加する。従来どおり `valid is True`、`experiment_complete is True`、既存 ledger 値も維持されることを同じ node で確認する。

- `test_material_report_rejects_packet_run_missing_snapshot_verification`  
  `_full_manifest` (`orchestrator/tests/test_codex_reasoning_ab.py:1420-1602`) で正常な packet、verdict、freeze、revealed map、judgments を作る。`_load_adjudication` wrapper で受け取った検証済み集合から、revealed mapping 上の一 run だけを除いて本体へ渡す。`aggregate_manifest` の report について、`valid is False`、rc が `RC_AGGREGATE`、上記 exact reason が `failure_reasons` に存在し、`certification_scope` はなお exact であることを assert する。新しい membership check を削除すれば赤くなる、宣言 node と対になる性質検査 node である。

- `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication`  
  `orchestrator/tests/test_codex_reasoning_ab.py:7566-7701` の軽量 replay fixture を再利用・抽出する。`verify_snapshot` の call と `_load_adjudication` に渡る集合を spy し、以下を parameterize する。

  - canonical replay 一致: `verify_snapshot` が呼ばれ、集合が `{"r01"}`。
  - canonical replay 不一致: 呼出し自体はあるが集合は空で、既存 `"snapshot oracle replay mismatch"` が残る。
  - 同一 resolved path の descriptor SHA が途中で A から B に変わる再入: 2 identity として二度検証される。path-only cache への退行なら call 数 assertion が赤くなる。

  `verify_snapshot` 呼出しを削除して run ID だけ追加する変異、mismatch 後に追加する変異、path-only dedup への退行をこの node が検出する。

- `orchestrator/tests/test_codex_reasoning_ab.py:11246-11313`, `:11416-11418`  
  既存 `_load_adjudication` 直呼出しへ、`final_attempts` の全 run ID を持つ集合を明示的に渡す。これらの node が試す SHA redundancy や conservative disagreement の入力は全て検証済み正例として扱い、既存 assertion の意味を変えない。

既存 `_aggregate_verified` node は report 全体の exact key set を固定しておらず、field の追加で壊れない。`_replay_manifest` の返却 shape は維持する。必須引数化で影響する `_load_adjudication` 直呼出しは上記全箇所を更新する。

## 変異候補

- C1: `certified` を `["aggregate.valid", "packet"]` に変更する。  
  赤くなる node: `test_material_report_certification_scope_is_exact_on_all_return_paths`、既存正例への追加 assertion。

- C2: `uncertified` から `"packet"` を削除する。  
  赤くなる node: `test_material_report_certification_scope_is_exact_on_all_return_paths`。

- C3: `material_packet_requirement` を `"packet_self_certified"` または `"none"` に変更する。  
  赤くなる node: `test_material_report_certification_scope_is_exact_on_all_return_paths`。

- C4: `tools/codex_reasoning_ab.py:8811-8813` へ追加する membership condition または reason append を削除する。  
  赤くなる node: `test_material_report_rejects_packet_run_missing_snapshot_verification`。

- C5: `tools/codex_reasoning_ab.py:10161-10167` で実測集合の代わりに `final_attempts` の全 run ID を渡す。  
  赤くなる node: `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication` の mismatch case。

- C6: `tools/codex_reasoning_ab.py:10023` 相当の cache key を再び `oracle_path.as_posix()` だけにする。  
  赤くなる node: `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication` の同一 path・別 descriptor SHA case。

これらは宣言だけの変異を exact declaration node が、発火配線を外す変異を性質・evidence node が殺す構成であり、恒真な検査ではない。

## 残るリスク

- replay 時点の filesystem をロックしないため、descriptor 検査と後続 read の間の TOCTOU は残る。cache key 強化は再入を狭めるが、同時書換え全般を暗号学的に排除しない。

- 過去の各 run 時点の snapshot を再構成するのではなく、凍結 pre/post oracle と replay 時の現物から同一性を推論する。実験後に同じ bytes へ戻す攻撃はこの scope では扱わない。

- 中間 packet、packet-state、verdict log、revealed map 自体は引き続き未認証であり、verify/aggregate を通さず直接消費する外部利用者は保護されない。これは今回の裁定どおりである。

- `SCHEMA_VERSION=2` の additive field は、未知 field を拒む外部 consumer が存在すれば互換性問題になりうる。repo 内でその consumer は確認できないが、report 専用 schema の要否は将来課題として残る。

- 今回の plan は read-only 静的検査だけで、pytest や変異ハーネスは実走していない。

## 総括

P1 は覆り、prelaunch 未検証 attempt から正常な材料 packet を経て `valid: true` へ至る経路は現行では到達不能である。  
それでも `_load_adjudication` の必須集合検査と、evidence 生成・伝達 node を入れることで、将来の SHA 防壁や snapshot replay の退行を検出できる。  
宣言は `certification_scope` 一 field に certified、uncertified、材料 packet 条件を固定する。  
親が段 4 で裁定すべき主点は、P1 の到達不能への更新、上記 field identifier の確定、cache key を path・SHA・case にする設計の採否である。  
`SCHEMA_VERSION` は 2 のまま、凍結 packet bytes と事前登録 protocol は変更しない。