## 止まらない抜け道

**所見: refuted / scope 内。** 計画の2行追加後、対象 except まで到達した `CampaignAbort` を外側で飲んで campaign を継続する経路は見つからない。

以下を実際に辿った。以下の `C` は `orchestrator/campaign/s8b_floor_campaign.py`。

- planned: `C:6232 _run_session → C:6524 _Runner.run`
- retry: `_run_session → C:6406 _retry_round → _Runner.run`
- resume replay: `_run_session → C:6426 _replay_cut6_start → _Runner.run`
- 共通外側: `C:7251 _run_campaign_core → C:7193 run_campaign → C:8573 main → sys.exit(main())`

retry・round・replay に捕捉はない。`C:7955` は aborted terminal を追記して再送出する。CLI の `C:8668` は `FloorCampaignError` として捕捉するが、**終了コード1を返す停止処理**である。この呼出し列に bare except／`contextlib.suppress` による継続はない。

**所見: real / scope 外。** 「どこで発生した `CampaignAbort` でも停止する」まで一般化すると成立しない。測定内部から投げた場合、`orchestrator/calibrator/runner.py:1184` は `RuntimeError` 系として捕捉し、rep 失敗へ変換できる。certified launcher の `:1400`、`:1443` にも同様の捕捉がある。ただし、今回の admission wrapper の3つの abort はこれらの**外側**で発生する。別箇所の修正は提案しない。

## 親の実測の検算

| アンカー | 判定 | 現物との照合 |
|---|---|---|
| A1 | refuted / scope 内：誤記なし | `C:360`、`FloorCampaignError(RuntimeError)`。 |
| A2 | refuted / scope 内：誤記なし | `C:408`、`CampaignAbort(FloorCampaignError)`。 |
| A3 | real / scope 内：限定不足 | `C:6283–6284` は正しい。「wrapper から送出された abort を launch failure に変換する箇所」として唯一。非 certified 測定経路全体の唯一の except ではない。runner 内にも捕捉がある。 |
| A4 | refuted / scope 内：誤記なし | `C:6334–6341` は該当分岐。ただし post-probe 競合なら先行分岐で `competing_process` になる。 |
| A5 | refuted / scope 内：誤記なし | raise は `C:5983`、`:5988`、`:6002`。wrapper 作成時には別途 `C:5969` の coverage abort もあるが、`measure_attempt` 内の3箇所という記述は正しい。 |
| A6 | refuted / scope 内：誤記なし | `C:7926` で wrapper 作成、`:7938` で `_Runner` に渡す。 |
| A7 | refuted / scope 内：経路の主張は正しい | 決定的な根拠は `C:6259` の早期 return。launcher `:1400` は capture 例外の捕捉箇所であり、それ単独では分岐の証明にならない。 |
| A8 | real / scope 内：関数の混同 | runner `:963` は deferred capture の `open_measurement_point`、`:1184` が通常の `measure_point`。両方とも捕捉節で、plain `RuntimeError` の送出例は `:967`、`:1188`、`:1281`。 |

段2 plan の `_run_certified_floor_session` 定義位置も **`C:8874` ではなく `C:8889`**。呼出し `C:8998` は正しい。

## 親の一般化への反証

**所見: real / scope 内。** 「manifest に hit がない」から「凍結 bytes の pin は無い」への推論は強すぎる。

確認した範囲では、次は支持できる。

- `FROZEN_MANIFEST` の全エントリに driver source はない。
- `C:4380` の `resolve_evidence` は `prepared.genome` と CCBench source を対象にする。
- W-d と production consumer 19件は path の登録である。
- source 内容を検査する別形式は実在する。例：
  - `test_s8b_floor_campaign.py:9713`：`_Runner` の AST による precedence 検査。
  - 同 `:15274`：source 全体の禁止属性検査。
  - `test_pegasus_floor_tools.py:1379`：文字列位置と正規表現による処理順検査。
  - `test_official_perf_closure.py:181` 以降：関数名・呼出し名による固定。

これらを読む限り、今回の2行はその検査対象条件を変えない。

**所見: 不明 / scope 内。** 対象差分を禁止する bytes／派生 digest／絶対行番号 pin は発見していないが、完全な不在証明には至らない。path・basename・対象行番号・except 本文・`getsource`・`__file__`・source hash 系・glob 系を検索した。任意の別名や外部保管 digest まで閉じた探索ではないため、結論は**「確認範囲で該当 pin 未発見」**に留めるべきである。

追加探索先の `.github`、`pyproject.toml`、推測した identity/config path は不存在だった。必読5ファイルは読取可能であり、検査は継続した。

## 受理集合への影響

**所見: real / scope 内。** campaign 実行全体の受理集合は不変ではない。

変わるのは、非 certified 測定 callback／admission wrapper が `CampaignAbort` を送出する実行である。従来は session 除外と retry へ進み得たが、修正後はその場で停止する。例えば、正常な admission 消費後に callback が初回だけ abort する入力は、従来の継続処理と異なる。

**所見: refuted / scope 内。** 以下の受理条件を変更する差分は見つからない。

- certified：`C:6259` で対象 try より前に別経路へ分岐。
- 最終 inspection：`C:7964` 以降の別処理。abort 実行が到達しなくなるが、検証述語は不変。
- 既存 artifact の再検証：既存 bytes と verifier の条件は変更しない。
- 従来拒否した入力を新たに受理する方向：例外を継続から停止へ変える2行には認められない。

したがって「**certified と inspection の受理条件は不変、非 certified の実行継続条件は厳しくなる**」が正確である。

## (P1) 射程の裁定

**所見: refuted / scope 内。** 今回 `FloorCampaignError` 全体へ広げる必要性は確認できない。`CampaignAbort` 限定を支持する。

親型の docstring は入力・identity・実行契約の fail-closed 拒否を意味するため、親型を launch failure にする扱いにも意味上の懸念はある。しかし、今回の wrapper の送出型は `CampaignAbort`。予約段の `C:7924 FloorCampaignError` は対象 try の外である。

**所見: real / scope 外。** 注入 callback が非 abort の `FloorCampaignError` を投げれば現在も捕捉される。親型全体の扱いを変えることは、今回確認した停止命令の局所修復を超える。

## (P2) β-7 との整合

**所見: real / scope 内。** 「停止後の診断に post-probe 情報は不要」とは断言できない。

省略すると、測定後の競合プロセスの有無や probe 自体の失敗情報が得られない。今回の3つの admission abort は実測 callback より前だが、計画の再送出は**callback が測定後に投げる abort にも適用される**。「常に測定前だから不要」という根拠では足りない。

ただし、失われる情報は abort 実行を有効な測定へ戻す材料ではない。後続 probe の失敗が元の admission 拒否理由を置換する可能性もあるため、**元の停止理由を保って即時送出する provisional は支持する**。

`C:32–33` の「必ず」はこの裁定と文字どおりには一致しない。既存の非 RuntimeError 例外も post-probe を飛ばす事実は実装の射程を示すが、全称文言の例外規定そのものではない。

## 変異の帰属

**所見: refuted / scope 内。** 採用候補3件に、先行 admission／binary gate が必ず捕まえて対象差分へ届かない変異はない。

| 候補 | 帰属の評価 |
|---|---|
| 再送出節を削除 | 負例は admission 消費後に到達する。例外オブジェクト同一性と session 不在で、この差分を直接検査できる。 |
| `except RuntimeError: raise` に拡大 | 新正例で検出可能。ただし既存 `test_post_probe_runs_on_launch_error_and_competing_takes_precedence` も検出するため、受入全体の赤だけでは新正例への帰属を示せない。 |
| 再送出前に post-probe | 負例の callback 後 probe 回数で直接検出可能。 |

**所見: real / scope 内。** plan が候補から外した **freeze・binary・admission を事前に壊す変異**は、先行 gate による代替検出となるため除外が妥当。`FloorCampaignError` への拡大も今回の2本では生存し、殺傷証拠にはならない。

## 総括

**所見: refuted / scope 内。** 局所修正を覆す停止伝播上の欠陥は見つからず、`CampaignAbort` の先行再送出2行を支持する。

**所見: real / scope 内。** brief／plan には、A3の「唯一」の限定、A8の関数区別、certified helper の行番号、pin 不在の断言、β-7と診断情報の説明に修正余地がある。

コード編集・commit・pytest 実走は行っていない。以上は静的検査の結果である。