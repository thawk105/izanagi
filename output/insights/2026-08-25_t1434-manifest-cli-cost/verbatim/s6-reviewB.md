結論は「未閉包」です。親実測の 559 passed は尊重しますが、後方互換、`render-prompt`、費用から certified `valid` への逆流、変異網羅に must-fix が残ります。以下は静的検査結果であり、私は pytest を実行していません。

## must-fix

- 対象: `tools/codex_reasoning_ab.py:75-81,2731-2743,7389-7395,10635-10650,11176-11211`; 帰結: artifact schema を v2 のまま digest 欠落を拒否するため、`--task-manifest` 未指定でも旧 v2 schedule、all-null v3、旧 material/packet source が後方互換経路へ入る前に落ちる; 成果物影響: 従来受理された同一 schema の成果物を再生成なしでは supervise、verify、aggregate、make-packets できない。
- 対象: `tools/codex_reasoning_ab.py:3444-3453,7419-7420,9094-9160,11745-11749,11936-11939`; 帰結: `render-prompt` だけ既定 `TASK_MANIFEST` の provenance pin を読み、schedule は prompt hash の長さ、一様性、実 bytes 一致しか検査しないため、外部 manifest の digest を掲げながら既定 task の prompt を実行できる; 成果物影響: task manifest に束縛されたと見える run が別 task の入力を処理し、実験の task identity が偽になる。
- 対象: `tools/codex_reasoning_ab.py:9737-9747,10348-10359,10401,11090-11095`; 帰結: `not-certified` な費用の unavailable 診断を共有 `reasons` へ追加し、唯一の certified field `valid` と全 judgment を落としており、親裁定 §3 の「記述統計、gate 接続は scope 外」に反する; 成果物影響: 費用を算出できないだけの従来有効な bound report が invalid となり、品質判定まで消える。
- 対象: `tools/codex_reasoning_ab.py:9786-9791,10014-10016,10400`; 帰結: 検証済み material manifest tree を捨てて path を再読し、未検証の再読結果で cost 発火と最終 manifest hash を決めるため、同時差し替えで replay 対象、cost 有無、報告 hash が別観測になり得る; 成果物影響: `valid=true` の報告が、実際に replay した manifest と異なる bytes を指し、費用だけ黙って欠落し得る。
- 対象: `orchestrator/tests/test_codex_reasoning_ab.py:12514-12531` と `tools/codex_reasoning_ab.py:7389,10635,10643,11203,11369,11423,11492,11584,11590,11641`; 帰結: M15 は freeze の packet-state mismatch 一箇所しか殺さず、例えば private mapping の検査 `:11641` を外しても生成値確認テストは緑のままである; 成果物影響: 559 件緑でも digest 連鎖の個別リンク全てが実効とは証明できず、manifest 交換済み成果物を受理する退行を見逃す。

## nit / backlog

変更閉包の数え上げは次のとおりです。

- `task_manifest` 引数を持つ関数は 27 個です。
- CLI から直接呼ばれるものは 10 個です: `build_snapshot`、`verify_snapshot`、`collect_run`、`supervise_pair`、`aggregate_manifest`、`verify_manifest`、`make_packets`、`append_verdicts`、`freeze_verdicts`、`reveal_mapping`。
- その配下で到達する内部関数は 16 個です。
- 引数を持つがファイル内の CLI call graph から到達しないものは `_derive_snapshot_from_base` 1 個、`tools/codex_reasoning_ab.py:3123` です。現状はテスト fixture 用の内部 API なので、それ自体は欠陥とは判定しません。
- `--task-manifest` を持つ verb は上記と同じ 10 個です。consumer 8 個は先行 digest を検査し、snapshot producer 2 個は出力 oracle に digest を記録します。option を持つのに完全に無視する verb は静的には 0 個です。
- `render-prompt` は引数側にも option 側にも現れないため、この単純な対応表では検出できない閉包外です。

費用フィールドの製品コード内の読み手は、`normalized_cost` が 0、`normalized_cost_axis_ledger` も 0 です。書き込みは `tools/codex_reasoning_ab.py:10317-10320,10422-10423` だけで、テスト内に出力値の assertion が 13 箇所あります。配置自体は `partial`、`not-certified`、未計上 category を明示しており妥当ですが、共有 `reasons` 経由で `valid` を変えるため、実際には「読み手ゼロの説明値」より強い作用を持っています。

価格 snapshot は cost loader 単体では一回読みですが、bound schedule の通常経路では schedule 検査と `tools/codex_reasoning_ab.py:9493-9505` の cost loader がそれぞれ読みます。固定 SHA があるため別内容の採用には至りませんが、親裁定 B-2 と M10 の「経路全体で一回」という説明は過大です。

性能面では、新設テストから pytest の再帰起動、`os.walk`、`rglob`、subprocess による実 suite 起動は見つかりませんでした。

- `test_material_replay_rejects_task_manifest_exchange_at_digest_consumers` は `_full_manifest` により固定 5 block、10 run の synthetic pipeline を一式再生します。新設中では最も重いですが、任意入力サイズには比例しません。
- `test_cost_constant_false_rejections_are_owned_by_snapshot_validator` は実 repo の固定 price snapshot 1 ファイルを parameter 3 件で読みます。repo 走査ではありません。
- `_walk_json_values` は cost subtree サイズに比例しますが、生成された小さい JSON tree に閉じています。
- 141.94 秒から 144.15 秒への増加は 2.21 秒、約 1.56% で、静的には性能 must-fix はありません。

## 過剰拒否の実測

read-only での静的実測です。

| 入力 | 最初に落ちる箇所 | 判定 |
|---|---|---|
| option 未指定、digest 無しの旧 material manifest | `_replay_manifest` `:10635` | `material manifest task_manifest_sha256 mismatch` |
| digest 無しの v2 legacy schedule | `supervise_pair` `:7389`、または replay `:10643` | `_legacy_schedule_view` に到達する前に拒否 |
| digest 無しの all-null v3 schedule | 同上 | price が null でも拒否 |
| schedule descriptor 無し、digest 無しの旧 packet source | `make_packets` `:11176` | descriptor 分岐前に拒否 |
| digest 無しの旧 launch receipt | `collect_run` `:7990-7991` | RC_RECEIPT |
| digest 無しの旧 packet state | append、freeze、reveal の各入口 | 全て拒否 |
| digest を新たに付けた v2、all-null v3、descriptorless 入力 | legacy shape 自体は受理 | cost key は出ないが、これは旧 bytes の互換ではない |

破壊範囲は少なくとも 11 artifact family です。

1. schedule
2. material / packet-source manifest
3. attempt ledger row
4. snapshot oracle
5. launch receipt
6. collect receipt
7. packet state
8. private mapping
9. verdict log row
10. verdict freeze
11. revealed mapping

しかも `SCHEMA_VERSION` は引き続き 2 です。新旧を schema generation で区別できません。

repo fixture への実害は既に差分に現れています。`_schedule`、`_manual_run`、`_full_manifest`、`_packet_fixture`、legacy schedule、packet swap fixture など、従来 digest 無しだった正例を一斉に現行 helper で自己整合させています。現行 test file には `TOOL._task_manifest_sha256(...)` が 37 箇所あります。

射影資料内で確認できる実 `output/` artifact は price snapshot と excerpt だけで、これらは今回の digest 対象ではありません。一方、schedule/material/packet の repo 全体 inventory は射影外なので、「該当 output が存在しない」とは立証できません。仮に checked-in output がゼロでも、同じ v2 schema の外部保存成果物と fixture 契約を破っているため「実害なし」とは言えません。

## 偽緑のおそれがあるテスト

- `test_default_and_explicit_default_task_manifest_cli_results_are_equal`、`:9450-9486`: `build_snapshot` を fake に置換し、変更後の暗黙値と明示値だけを比較します。旧 artifact の受理や変更前 bytes との互換は一切通りません。
- `test_m08_p02_p04_null_v3_and_legacy_emit_no_cost_keys`、`:13949-13991`: `_aggregate_verified` を直接呼び、digest を要求する `_replay_manifest` と `make_packets` を迂回します。P02/P04 の「受理」を証明せず、cost key 不在だけを証明します。
- `test_schedule_descriptor_absence_emits_no_cost_keys`、`:13994-14014`: 同じく direct helper test で、digest 無し packet source が入口で拒否される事実を見ません。
- `test_task_manifest_cli_option_surface_is_closed`、`:9369-9404`: parser option の存在集合だけです。main dispatch が値を渡すか、各 consumer が検査するかは証明しません。
- M16、`:9407-9447`: fake `build_snapshot` 一 verb だけを通します。他の 9 verb の CLI forwarding を壊してもこのテストは緑です。
- M15、`:12514-12531`: mismatch を入れるのは packet state から freeze への一リンクだけです。schedule、attempt ledger、verdict row、freeze、revealed mapping、private mapping の個別交換は未試験です。
- `test_task_manifest_digest_is_recorded_through_packet_freeze_and_reveal`、`:12534-12596`: producer が出した同じ digest の存在を確認する正例です。consumer の exact mismatch 検査を外しても producer が値を残せば緑です。
- fixture 群は production の `_task_manifest_sha256` を期待値生成にも使います。独立した固定 digest や外部 canonical oracle がなく、fixture と実装が同じ誤った digest 規則へ動く自己整合リスクがあります。
- M10、`:13708-13734`: wrapper 経由の read 回数と validator 呼出回数は見ますが、validator の返却 tree と cost に渡った tree の同一性、通常 aggregate 経路全体の read 回数は assertion しません。
- `test_cost_constant_false_rejections_are_owned_by_snapshot_validator`、`:14035-14049`: 新 cost interpreter を通らず、既存 `PRICE_SNAPSHOT.validate_price_snapshot` だけを試します。この新設テスト単体は cost 実装を削除しても緑です。
- M01、`:13785-13805`: 揮発しやすい完全な診断文面を期待値にし、さらに uncertified cost 診断が material failure reason へ入る現在の誤った結合を正解として固定しています。

## 事前登録の到達度 — 差し替え文面案

`prereg-s5.md`:

- `:42` の差し替え案: 「**部分実装**。外部 task manifest は 10 verb の CLI から読み込まれ、canonical digest が snapshot、schedule、run、material、packet、verdict 系へ伝播する。ただし `render-prompt` は既定 manifest の provenance のみを読み、task 入力処理の CLI 閉包は未完成である。」
- `:47` の差し替え案: 「**実装済み**。`supervise-pair` は `--task-manifest` を受け、schedule の digest を exact 検査し、ledger、launch、completion へ同じ digest を記録する。」
- `:50` の差し替え案: 「**部分実装**。snapshot、schedule、run、aggregate、packet/adjudication の現行 task manifest consumer は CLI 接続されたが、prompt producer は未接続で、task 固有 acceptance と独立 oracle は未束縛である。」
- `:53` の差し替え案: 「**部分実装**。凍結 price version を軸に、観測可能な input、cached input、output の部分正規化 cost を per-run と軸別に生成する。cache write 数量は未計上で、値は `partial` かつ `not-certified` であり、resource gate と overall の読み手は未実装である。」
- `:54` 末尾への追記案: 「ただし新 consumer は packet-source manifest に task manifest digest を要求するため、digest 無しの既存 legacy artifact との byte-level 後方互換はない。」
- `:96-100` の差し替え案: 「**task-specific oracle manifest: 部分着地**。現行 task manifest の `oracle_kind` と `known_finding_ids` は schedule、verdict、aggregate へ伝播し、digest で同一 manifest に束縛される。一方、独立 oracle ledger、task 固有 acceptance、oracle manifest 自身の独立 hash 契約は未登録であり、機構全体は実装済みと呼ばない。」
- `:102` の差し替え案: 「task ごとの snapshot と provenance pin は外部 manifest から一部利用可能。prompt は `render-prompt` 未接続、独立 oracle manifest hash は未実装。」
- `:105` の差し替え案: 「price snapshot の保存と parser 接続は完了。登録世代 lock と完全費用に必要な cache-write 数量 receipt は未完了。」

`prereg-s10.md`:

- `:49-50` の差し替え案: 「**数量が不明な token category はキャッシュ書込である。** 単価は snapshot に存在するが、正規 receipt が `cache_write_input_tokens` を保存しないため、その金額を計算できない。」
- `:76-83` の差し替え案: 「**price binding に加え、部分正規化 cost の計算器を接続した。** bound v3、schedule descriptor 有り、token 観測可能な試行について、凍結 snapshot の mapping と Decimal を使い per-run と軸別の値を生成する。cache write は未計上で、`coverage_status=partial`、`certification_status=not-certified` とする。resource gate と overall への接続は未実装である。」
- `:94` の差し替え案: 「比較可能性のため、token が観測可能な run の部分正規化 cost は開始時に凍結した price version で計算する。`unavailable` と `not-incurred` は金額と費用分母へ入れない。」

「実装済み」と無条件に書けない理由は、`render-prompt` の task identity が閉じていないこと、旧 schema artifact の移行契約がないこと、費用診断が誤って certified `valid` を変えること、費用 field の製品 reader と gate がゼロであること、cache-write 数量と独立 oracle acceptance が未登録であることです。「部分費用計算器が実装された」とは書けます。

## 親裁定への反論

§2 の scope 拡大動機自体は正しいです。外部 manifest を invocation ごとに交換できる状態は、従来より正しさを弱めます。しかし裁定は次の二点で閉じていません。

1. 「digest 欠落は拒否」と「option 未指定は現行と同じ」を、schema generation や migration なしで同時に要求しています。`SCHEMA_VERSION=2` のままでは両立しません。既定 manifest に限り旧 v2 artifact を legacy として受理するか、新 schema と明示 migration を用意する裁定が必要でした。
2. `render-prompt` を「receipt digest consumer がない」という理由だけで除外したのは誤りです。これは task-dependent producer であり、出力 prompt hash は外部 manifest の provenance 由来であることを検証されません。digest artifact の有無ではなく、実験 task の全入力 producer/consumer 閉包で scope を決めるべきでした。

§3 の「記述統計」という裁定も、実装条件が不足しています。`normalized_cost` field を certification scope から外すだけでなく、費用の unavailable 診断が material `valid`、experiment completeness、decision を変更してはならない、と明示すべきでした。

変異登録については次の判定です。

- M06 取り下げ: 妥当です。production end-to-end では `tools/codex_reasoning_ab.py:8171-8173` が先に cached > input を拒否します。
- M09 取り下げ: 妥当です。`:8971-8975` が unknown model を cost 層より先に拒否します。
- M14 取り下げ: 妥当です。loader の top-level 検査を外しても `_validate_task_manifest` が同じ入力を拒否します。
- M15 継続: 不適切です。「consumer 一箇所」では mutation target が一意でなく、実装には多数の独立 check site があります。リンク別の mutation family に分解すべきです。
- M16 継続: 不十分です。現行テストは build-snapshot 一 verb だけです。10 verb の dispatch 別 mutation、または main の dispatch table を独立に検証する必要があります。
- P03: 変更後の default と explicit-default の比較であり、変更前との後方互換正例ではありません。
- M10: loader 単体の一回読取は見ますが、schedule validation から cost 出力までの一 byte observation 契約を証明していません。

## 総括

この wave を「事前登録が要求する二つの機構を閉じた」と記録するのは早いです。費用計算器そのものは値、Decimal、partial 表示まで着地していますが、task manifest 経路は `render-prompt` と旧 artifact migration が未閉包で、費用は説明値でありながら certified `valid` を落とします。

受理には少なくとも、旧 schema の互換方針または generation bump、`render-prompt` の manifest 束縛、cost 診断と material failure の分離、M15/M16 のリンク別テストが必要です。親実測の 559 passed / 2 skipped は既存実装の実走結果であり、本レビューはそれを再実行または緑認定していません。