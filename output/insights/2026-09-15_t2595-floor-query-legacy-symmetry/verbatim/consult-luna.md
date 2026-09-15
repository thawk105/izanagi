## production 到達性

以下、`A`＝`orchestrator/campaign/s8b_holdout_admission.py`、`C`＝`orchestrator/campaign/s8b_floor_campaign.py`、`T`＝`orchestrator/tests/test_s8b_holdout_admission.py`、`TC`＝`orchestrator/tests/test_s8b_floor_campaign.py`。行番号は現行コード。

**real — plan の resume 経路では、混在履歴は新しい拒否に到達する前に拒否される。**

query への通常の呼出し関係は次のとおり。

```text
C:7954 Runner.run()
→ C:6595 _retry_round()
→ C:6407 _round_failed_cells()
→ C:6170 _retry_authorization()
→ C:6179 retry_trigger_query_fn()
→ C:6073 A.floor_retry_trigger_for_round
```

しかし、問題の入力「planned P の failed 完了＋P を trigger とする retry1 start＋P の recovery 候補」では、`C:6595` より前に次が実行される。

```text
C:6593–6594 既存 retry1 start の replay 判定
→ C:6432 floor_attempt_requires_cut6_replay
→ A:5341 _assert_attempt_authorized_by_journal
→ A:4342 _assert_retry_start_authorized_locked
→ A:5765 完了候補数＋recovery 候補数 != 1
→ 拒否
```

`A:5341` は completed 判定・marker 判定より前である。retry1 の consume 済み／未完了にかかわらず、この入力は先に拒否される。`C:6435` が `CampaignAbort` に変換し、`C:7955` が `aborted` を記録する。

したがって、**この履歴を置いて通常の resume を実行しても、追加予定の `A:5881` の検査には届かない。** plan 冒頭の経路説明は `C:6594` を飛ばしている。

**real — 現行 production に recovery 行を生成する呼出し元がない。**

書込み API は `orchestrator/campaign/s8b_attempt_registry.py:3508` の `record_attempt_recovery`。同 `:3537` が core を呼び、`:3549` が永続化する。しかし、現行コード検索でこの API の呼出し元はテストのみだった。

混在履歴を実際に書くのは、例えば `T:1979`・`:1995` の fixture と `T:3520` の journal 追記である。既存 production resume テストも `TC:12847` で registry を fixture 注入している。

**refuted — query 関数そのものが production 未接続、という指摘。** `C:6073`・`:6179` に実接続がある。到達しないのは今回の混在履歴に対する新しい拒否分岐である。

## resume 経路の検算

**real — brief 事実4の「同一 process では1回」「resume＝新 process」は誤り。**

cache は `C:6103` で作る **Runner インスタンス単位**。`C:7934` は campaign 呼出しごとに新しい Runner を生成する。同じ process 内で crash を捕捉して resume を再呼出しすれば、空の cache で再問い合わせする。`TC:12830`・`:12874`・`:12898` にその実例がある。

**refuted — 同じ Runner の通常処理が cache を迂回して同じ key を再問い合わせする、という指摘。**

- `C:6176` は保存済みの `None` も含めて返す。
- `_round_failed_cells` と `_retry_round` の連続呼出しもこの cache を使う。
- cut-6 replay は別の query を呼び、cache を消去しない。
- 例外は cache に保存されないが、通常の `run()` はそこで中断する。

また、「resume で本件が発火する」という結論は、前節の先行拒否により成立しない。

## テスト 3 の費用対効果

**refuted — 提案された helper が存在しない、という指摘。**

すべて実在する。

| helper | 行 |
|---|---|
| `_freeze_document` / `_freeze_sha` / `_verified_freeze` | `TC:344` / `:360` / `:367` |
| `_protocol` | `TC:371` |
| `_run_campaign` / `_make_measure_fn` | `TC:815` / `:948` |
| `_only_run_dir` / `_read_journal_lines` | `TC:990` / `:1747` |

**refuted — テスト3が明確に scope 外、という指摘。** 正当な legacy resume を保持する I2 に直接対応する。ただし、テスト2と同じ「使用済み legacy を除外してはいけない」という退行について、campaign 全体の完了まで確認する分の重複はある。所要時間は未実測。

**より安い正例：** plan のテスト2で十分に同じ局所退行を捉えられる。registry なしで P の failed 完了と retry1 consume を作り、再queryが P を返し、retry2 consume も通ることを確認する。使用済み legacy の一律除外・空候補拒否の両方で失敗する。

**real — テスト3を残しても、今回の新しい拒否の production 到達性は証明できない。** 入力に registry がなく、追加条件は偽になる。さらに `_run_campaign` は `TC:819` の内部 core と注入測定を使うため、official の全経路を証明するテストでもない。

削除すると、この特定の legacy resume の結合確認は失う。ただし、**残すだけで F591 型を防げるという説明は過大**である。今回の混在履歴が先行拒否される事実は、この正例では検出できない。

## テスト 1 は修正前に落ちるか

**refuted — 3 parameter のいずれかが修正前にも通る、という指摘。** 提案どおり構築すれば、すべて query の `pytest.raises` が失敗する。

共通経路：

1. `A:5834`–`:5841` が P の failed 完了を legacy に追加。
2. `A:5842` が retry1 start から P を使用済みと認識。
3. `A:5851`–`:5852` が P の recovery 収集をスキップ。
4. `A:5860` の多重性検査を通過。
5. **`A:5882`–`:5885` が legacy 認可を返す。**

| parameter | 未除外で数えた recovery 候補 | 修正前 |
|---|---:|---|
| `valid-one` | 1 | `A:5882` で認可 |
| `corrupt-one` | 1 | 同上 |
| `valid-plus-corrupt` | 2 | 同上 |

`corrupt-one` で壊すのは recovery 行の `configuration_id`。start 行は残るため `A:5471` の対象 start hash 集合は維持される。`A:5485` または `:5486` の hash 一致で候補に残り、`A:5494` が計数する。

canonical JSONL への書戻しであれば、hash chain が古くても候補読取りは `A:5392`–`:5395` を通る。この段階は replay による chain 検証ではない。consume は全ケースで `A:5765` の件数条件により拒否する。

以上は静的追跡であり、テスト実測ではない。

## 焦点走の過不足

**refuted — 表の12 file に存在しない import 根拠がある、という指摘。** 掲載された参照関係は確認できる。

ただし、**module の import と変更関数への到達は別**である。

- 変更関数を直接検証する中心は `T`。
- production consumer を検証する中心は `TC`。
- 残り10 file は周辺回帰の集合。例えば `test_s8b_floor_contract.py:263`・`:269` は campaign の schedule／protocol API、`s8b_oracle_n_pilot.py:1325` は別の consume API を扱う。これらの import だけでは今回の query への到達根拠にならない。

**real — import 基準だけでは12 file の選択境界を説明できない。** 例えば、表外の `orchestrator/tests/test_s8b_dependency_prefix_bridge.py:17`・`:18` も campaign と campaign fixture を import する。同じ基準ならこちらも該当する。ただし plan は網羅集合ではないと明記しているため、これを必須の追加対象とは判定しない。

**必須なのに欠落した file は確認できなかった。** private helper は `A:5759` の consume、`:5853` の query、`:6645` の履歴検査へつながる。この関係は公開 API の consumer 表だけでは見えないが、今回は helper を変更せず、`T` と `TC` が焦点走に含まれる。

結論：12 file は周辺回帰集合として許容できる。ただし「全12 file が今回の変更を踏む」という説明には使えない。

## scope の膨張と不足

**refuted — 提案の局所チェックや変異 matrix 自体が scope 外、という指摘。** 既存 helper による候補計数であり、新設 framework・台帳・一般化はない。変異 matrix も brief の成果物に明記されている。

**real — 不足は production 到達性の立証。** plan は query が呼ばれる経路を示したが、混在履歴がそこまで生き残ることを確認していない。実際には `C:6594` → `A:5765` で停止する。

**real — 効果説明と完了条件の限定が不足。** 本件で示せるのは「低層 query の実在する認可非対称を閉じる」こと。現行 resume の測定浪費を防ぐ、という効果は示せない。

テスト3は保持可能だが、局所保存性に対する重複と、証明できる範囲を明記するのが妥当である。

## 親 brief の誤り

- **事実1・2：refuted。** 提案された最小履歴では正しい。query の認可と consume の拒否は現物で追える。
- **事実3：refuted。** `A:5866` に逆方向チェックが存在し、legacy 返却側にはない。
- **事実4：real。** cache の単位が誤り。さらに混在履歴は resume の先行検査で拒否される。
- **事実5：refuted。** `C:6414` の while と `:6423` の recovery 限定 break が legacy 複数 retry を裏付ける。
- **事実6：条件付きで正しい。** registry 不在は `A:5376`、slot identity 不明は `A:5460` で空候補。ただし registry 読取りは identity 判定より先で、壊れた framing 等は `A:5386` で例外になる。「identity 不明なら常に空」と一般化してはいけない。
- **事実7：live bytes pin 不在の完全な再監査は未確認。** 確認した `test_check_docs.py:6086` 以降の R33 契約は今回のブロックとは無関係。反証となる pin は確認していない。
- **I1〜I6：refuted。** 今回の局所修正に課す制約として、緩和すべき矛盾は確認できない。

**real — brief:10 の「測定を1本空費」は誤り。** 仮に誤認可後に新しい retry を実行しても、`C:5998` の consume が `C:6008`・`:6012` の実測 callback より先に拒否する。

legacy 経路では `CampaignAbort` が `RuntimeError` の派生型（`C:360`・`:408`）なので、`C:6283` がこれを測定失敗として捕捉しうる。しかし、これは実測 callback を1回実行したことを意味しない。また「1本」に限定する条件もなく、`C:6414` は残り retry 枠まで進む。

今回の通常 resume については、そもそも先行拒否による `aborted` であり、brief:17 の `artifact-invalid` まで進まない。

## 裁定パッケージ候補 (scope 外の real 所見)

**現行 production の recovery writer 未接続。**

- 永続化 API：`s8b_attempt_registry.py:3508`・`:3549`
- 呼出し元：現行検索ではテストのみ
- production resume 正例も registry を fixture 注入：`TC:12847`

親が裁定すべきなのは、**本 wave を「低層 API の実在非対称の解消」として閉じるかという効果・優先順位の位置付け**である。writer 接続、新しい recovery 機構、authority の緩和は本 wave に含めない。

## 総括

**局所的な非対称は real。提案された負例3ケースは、静的には修正前にすべて落ちる。**

一方、**production resume の混在履歴は既存 cut-6 検査で先に拒否され、新しい query 検査には届かない。** registry writer の production 呼出し元もない。brief と plan は、この到達性と実測浪費の説明を訂正する必要がある。

ファイル変更・commit・pytest・変異実走は行っていない。