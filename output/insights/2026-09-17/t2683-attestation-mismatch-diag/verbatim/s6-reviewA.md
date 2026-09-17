## 総括

- **must-fix 0／nit 3。GO（静的レビューとして）。**
- 比較述語・通常例外時の拒否・成功 attestation bytes を変える不具合は見つからない。
- snapshot の追加・文脈計384行は変更後実体と一致。変異 anchor 表も一致。
- 実走根拠は [focus1-driver.log:20](/home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/focus1-driver.log:20) の **65 passed**。受入全走・変異走行の成功は主張しない。
- 留保：射影には比較関数の実装がなく、全入力について比較行の JSON 化可能性までは証明できない。
- nit は AST 配線 pin の射程、広い `Path.exists` patch、M1/M5 の赤理由の記録方法。

以下、`D`＝[t126_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/t126_driver.py)、`T`＝[test_t126_qualification_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/tests/test_t126_qualification_driver.py)、`A`＝[artifacts.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/artifacts.py)。

## 1. 受理集合の不変性

**所見：通常経路で受理集合が変わるという懸念は refuted。**

- `D:478` の `not comparisons or any(... != "pass")` は変更なし。
- typed raise は従来どおり `_attest` 内の `except Exception` より後。比較不一致が汎用 probe 失敗へ包み直されない。
- `D:499–525` の外側 `except BaseException` が、比較・診断構築・書込み・成功 payload 公開を覆い、失敗時は31。
- 親は `D:1311` で従来どおり非ゼロ終了を `AttestationError` に変換する。
- timeout 文言 `aggregate attestation cap exhausted`／`aggregate attestation cap exceeded` は不変（`D:1267–1269,1307–1308`）。

`os._exit` 自体は helper の外へ移ったが、実際の呼出しは固定整数0/31であり、通常動作の差はない。

**成果物への影響：** certified 選択・拒否状態は不変。失敗 message とその台帳上のハッシュは意図どおり変わる。実時間・stall の不変性は段4の保証対象外。
**是正案：** なし。

## 2. 成功経路の bytes 不変

**所見：helper 出力を期待値に戻す自己参照という懸念は refuted。**

`D:485–491` の payload は不変。`D:521–523` は旧 closure と同じく `stage`、`round_index` の順に追加し、同じ `relative` に同じ `create_json` を呼ぶ。成功時には mismatch 分岐へ入らない。

`T:427–440` は期待値を `_attest`／子 helper の戻り値から作らず、fixture・独立した hash 計算・実比較関数から構築する。比較関数の共有はあるが、今回の変更対象である payload 包装・公開処理からは独立している。canonical JSON と末尾改行も直接比較する。

**成果物への影響：** 同じ入力で成功 attestation の bytes・相対参照は不変。ただし driver 自体の source identity は変わるため、run 全体の identity 不変を意味しない。
**是正案：** なし。

## 3. sidecar の内容

**所見：P2 の構造違反は refuted。JSON 化可能性の全称命題は未証明。**

`D:503–515` は exact 9 keys。`comparisons` は `exc.comparisons` をそのまま保存し、`failed_fields` は同じ行列から `verdict != "pass"` の `field` を順序維持で抽出する。空比較は双方 `[]`。

`T:402–418` は辞書全体の一致に加え、21行・20 pass・1 governor 不一致・expected/observed を検査する。

ただし、`D:466` の JSON round-trip は**比較前の観測**に対するもの。これだけでは `compare_profiles` が生成する全行の型を証明できない。指定射影に比較関数本体がないため、「非 JSON 値が来る経路は絶対にない」とは断定しない。実例は発見していない。

**成果物への影響：** 仮に非 JSON 値が生成されれば sidecar は欠落するが、`D:524–525` により拒否31は維持される。通常 fixture の全行保存は焦点走で裏付けられる。
**是正案：** 全入力保証を報告するなら比較関数の型導出を追加確認する。新 validator は不要。

## 4. D474 との整合

**所見：診断失敗による通常 rc 変更・判定 authority 化は refuted。**

書込み失敗と create-only 衝突は外側 catch に入り31を返す（`D:516–525`、`A:449–451`）。親 helper は表示文字列だけを返し、比較述語や成功判定に使われない。

sidecar が collector の manifest に列挙されること（`T:620–628`）は、診断内容を受理判定に使うこととは別である。失敗時は `run_series` から例外が伝播し、成功 result 作成へ進まない（`D:1353–1364`）。

`create_json` が fsync を行う点は事実（`A:470,480,492`）。段4 A2/B2 の明示裁定に従い、stall・強制終了後 staging の限界を今回の新規 must-fix にはしない。

**成果物への影響：** 診断欠落時も通常の拒否結果は不変。診断がある場合は失敗台帳の message/hash と収集対象参照が増える。
**是正案：** 段4で指定された限界の記録を維持する。

## 5. 親 message helper

**所見：通常の filesystem／strict loader 例外の吸収漏れは refuted。**

- `D:532–538` は path 構築、`exists()`、`relative_to()` を覆う。
- `D:540–545` は読取り、キー欠落、型処理、表示用 JSON 化を覆う。
- 不正 JSON、非 regular file、非 canonical JSON は `A:557–570` の例外となり吸収される。
- `KeyboardInterrupt`／`SystemExit` など `BaseException` 全般は吸収しない。「全例外を吸収する」との表現は不可だが、通常の診断 I/O 失敗の漏れではない。

成功側と診断側は同じ `capability.root / relative` を基準に、末尾 suffix だけを変える。production の `prefix = attempts/{attempt_id}`（`D:1177`）と layout の組合せでは一致する。

`relative_to` が失敗するのは、異なる attempt/root を渡した場合や絶対・相対 path の不整合など。この場合も旧文言へ戻る。

**成果物への影響：** 読取り障害は診断表示を縮退させるだけで、通常の拒否型・rc は変わらない。
**是正案：** なし。

## 6. test の弱さ

**所見：実物を通していないとの包括的懸念は refuted。限定的な弱さは real、nit。**

通常の正負例は較正 loader と probe だけを置換し、parser・比較・hash・writer・strict loader を通す（`T:279–285,387–442`）。書込み失敗の置換は `.mismatch.json` だけで、他の path は実 writer へ委譲する（`T:466–470`）。

空比較 test の比較関数置換（`T:447`）と reader 障害注入（`T:533,535`）は追加の stub 境界である。空比較分岐・読取り失敗の検査としては妥当だが、それらを実比較／実 reader の証明には数えない。既存 assertion の変更・弱体化はない。

**N1 — AST 配線 pin の射程不足：real、nit。**
`T:590–599` は closure 全体の呼出し数だけを数え、子分岐・非ゼロ分岐への所属や引数を確認しない。現実装の配置は正しいが、死んだ分岐への移動などは検出できない。

**成果物への影響：** 現差分による誤値・誤参照は示せない。将来の誤配線で診断が欠落する回帰を見逃す余地がある。
**是正案：** 対象 `If` の条件・body と keyword 引数を追加検査する。既存期待値は変更しない。

**N2 — `Path.exists` の全体 patch：real、nit。**
`T:535` は sidecar 以外の Path にも作用し、test 本体終了後の teardown まで有効。ただし fixture 作成は patch 前であり、今回の焦点走にも破壊の証拠はない。

**成果物への影響：** production の値・受理集合・参照への影響は示せない。test 障害時の誤帰属リスクに限る。
**是正案：** sidecar だけを失敗させ、他は元関数へ委譲し、`monkeypatch.context()` で範囲を限定する。

## 7. 変異事前登録との対応

author の M1〜M11・E1 anchor はすべて実体と一致する。

**N3 — M1/M5 の赤は明示 assertion より前：real、nit。**
M1 は `T:401`、M5 は `T:452` の strict loader が、欠落ファイルに対して `QualificationArtifactError` を上げる。期待 test は赤になるが、「その内容 assertion が赤」と報告してはいけない。

**成果物への影響：** production の値・受理集合・参照への影響はない。変異報告の失敗地点・検出理由を誤記する問題。
**是正案：** 実際の赤理由を記録する。明示 assertion を求めるなら、読取り前に sidecar 実在 assertion を追加する。

M4 の辞書一致と行数、M2 の不在確認と directory 集合確認は、それぞれ同一欠陥の複数観測であり、それだけで単一理由性違反ではない。M6 は他 test の probe 失敗・衝突でも赤になり得るため、全 suite の赤数を「書込み失敗境界」の独立証拠として数えない。

## 変異の帰属判定

以下は**静的予測**。KILLED／生存の実測報告ではない。分類は段4の報告枠に従う。

| ID／D行 | 枠 | 期待 test の赤地点・帰属 |
|---|---|---|
| M1／516 | 診断 pin | `mismatch_preserves_all_comparison_rows` の **T:401 読取り例外**。sidecar 欠落が単一理由。内容 assertion 前。 |
| M2／521–523 | 境界 | `match_preserves_accepted_bytes_without_sidecar` の **T:441**。成功 sidecar の余分な公開。変異が未定義変数等で T:438 を赤にするなら帰属不適格。 |
| M3／513 | 診断 pin | `mismatch_preserves_all_comparison_rows` の **T:402**。期待 governor と空 `failed_fields` の不一致。 |
| M4／512 | 診断 pin | 同 **T:402**。全21行に対して失敗1行のみ。T:412–413 も同じ情報欠落を検査する。 |
| M5／502–520 | 診断 pin | `empty_comparisons_writes_rejected_sidecar` の **T:452 読取り例外**。空比較時の sidecar 欠落。 |
| M6／524–525 | 境界 | `sidecar_write_failure_preserves_rc` の **T:473**、34≠31。両 parameter とも書込み失敗時 rc が理由。他の汎用失敗も赤になり得る。なお production 親は非ゼロを31へ変換するため、証明対象は直接の子 rc。 |
| M7／501,524 | 診断 pin | `probe_failure_has_no_sidecar` の **T:489**。probe 失敗で不要 sidecar が存在する。 |
| M8／528–546 | 診断 pin | `parent_message_names_sidecar_and_failed_fields` の **T:511**。固定文言では診断 path／field が欠落する。 |
| M9／541–545 | 境界 | `parent_message_unreadable_sidecar_is_best_effort` の **T:539 評価中に例外伝播**。`json`／`read` は赤。`shape` は例外を起こさず生存、`exists` は別 catch のため生存。恒真ではなく対象外 case。 |
| M10／1312 | 診断 pin | AST test の **T:599**、helper を伴う raise が0件。message 委譲削除が理由。 |
| M11／1277 | 診断 pin | AST test の **T:598**、helper を伴う exit が0件。子 helper 委譲削除が理由。 |
| E1／498 | 等価対照 | comment/docstring だけなら helper の処理結果は等価。ただし docstring 自体と driver source bytes／identity は変わる。全 test 生存は未実測。 |

登録どおりの変異に、期待 test 全体が恒真となる候補は見つからない。M2 は構文上有効で実際に余分な sidecar を公開する変異であること、M9 は reader 側 catch だけを変更することを、変異実体で確認する必要がある。
