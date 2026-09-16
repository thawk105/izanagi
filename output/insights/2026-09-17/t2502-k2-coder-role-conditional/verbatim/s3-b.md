## 検査位置と副作用の経路

射影の必読9ファイルは読めた。以下の行番号は変更前。`L` は `orchestrator/campaign/p3_s4_loop.py`、`T` は `orchestrator/tests/test_p3_s4_loop.py`、brief／plan／rulings は親 job directory 内の各指定ファイルを指す。編集・pytest・変異実走はしていない。

**B1**

- **所見:** emit 分岐の `return 0` 後、`:2714` の `build_run_context` 前に置く対案を推奨する。plan も正しく拒否できるが、emit 用の条件と追加テスト C を必要とする位置を選んでいる。
- **仮判定:** real
- **根拠 file:line:** plan:5、:12、:95、L:2667、:2689、:2713、:2714、:2728。拒否対象についての到達順は次のとおり。

| 挿入位置 | 拒否前に走る処理 | 拒否前に走らない処理 |
|---|---|---|
| plan：manifest 解決直後 | argparse、prebuild/B4 の既存検査、manifest 解決 | build opt-in 検査、site admission、`default_cfg`、`:2714` の context 作成、tenant/pin 検査、prepare、loader、drive |
| 対案：emit return 後 | 上記に加え build opt-in 検査、site admission、`default_cfg`、environment binding | `:2714` の context 作成、tenant/pin 検査、prepare、loader、drive |
| loader 直前 | context 作成、必要なら tenant 検査、pin 検査、prepare の directory/receipt 作成まで | loader、drive |

`_prepare_knowledge_campaign` は L:1555 で `layout.ensure()`、:1556 で receipt を書く。plan と対案は双方その前で拒否する。loader 直前案は不要な永続副作用を残す。

- **推奨:** 対案を採用する。既存の build/site 拒否が先行する点は明記するが、それらを通る有効な負例で本条件を検証すれば単一理由性を保てる。

**B2**

- **所見:** `build_run_context` を「副作用なし」と一般化できない。また、対案でも `default_cfg()` 内の呼出しは拒否前に走る。
- **仮判定:** real
- **根拠 file:line:** L:1516、:2687、:2714。`orchestrator/campaign/build_admission.py:535`〜`:543` は authority 付きなら `_CLAIMED_AUTHORITY_NONCES` を更新し、常に `secrets.token_hex(32)` を呼ぶ。`default_cfg()` 内は authority を渡さないため token 消費はなく、nonce 生成だけがある。`:2714` は build 実行時の authority 消費を伴いうる。`p2_2.py:300` は競合プロセス検査、`patchharness.py:174` は Git の pin/dirty 検査であり、この箇所で build や receipt 作成はしない。
- **推奨:** 「対案は永続副作用と run 用 authority 消費より前」と記す。「全副作用より前」「build_run_context 自体が純粋」は避ける。

**B3**

- **所見:** plan の emit guard は、その位置では必要。対案では制御フローにより不要になる。
- **仮判定:** refuted — plan が emit 経路を壊すという疑いは棄却。
- **根拠 file:line:** L:2689〜:2713、plan:35〜:43。

| 分岐 | plan／対案での挙動 |
|---|---|
| emit のみ | 既存 prepare・JSON 出力・stdout・rc=0 を保存 |
| emit＋run 併記 | plan は emit guard、対案は先行 return により既存 emit 優先を保存 |
| run＋非空 sources＋role 無し | 新規拒否 |
| run＋空 sources＋role 無し | 既存 legacy 経路を保存 |
| run＋manifest＋K2 role | 既存 K2 consumer 経路を保存 |
| run＋manifest 無し＋role 無し | 既存 legacy 経路を保存 |
| run＋manifest 無し＋role 有り | loader の既存不整合拒否を保存 |
| emit/run とも無し | run guard により既存 fixture 経路を保存 |

- **推奨:** 対案なら C を省く。plan を維持するなら `not a.emit_planner_context` と C は対で残す。空文字の emit path についても、既存分岐と同じ truthiness を使う限り変更しない。

## 所見

**B4**

- **所見:** Pegasus は既に強い env 契約で閉じている。新 driver guard の検出力を job test で立証することはできないが、driver 直接起動の負例なら二重拒否に遮られない。
- **仮判定:** refuted — 本変更が不可避に単一理由性を損なうという疑いは棄却。
- **根拠 file:line:** `tools/pegasus/p3_s4_loop_pegasus.sh:60`〜`:96` は manifest/role の非空対と proposal path を要求する。`test_p3_s4_loop_job_contract.py:1073`、:1089 は実 job body の早期拒否を検査し、:1339〜:1379 は転送 argv を検査する。一方 L:2774〜:2777 は role 無しなら loader に knowledge を渡さないため、実 flattened proposal は既存相互必須検査を通る。
- **推奨:** job body は変更しない。変異 N は直接 `L.main` を呼び、実 legacy loader を通過可能な入力にする。job test は既存 shell 契約の回帰確認として扱う。

**B5**

- **所見:** CLI の条件付き必須化は runbook に追記が必要。他の2文書に必須の訂正はない。
- **仮判定:** real
- **根拠 file:line:** `docs/phase3-s4b-runbook.md:41`〜`:43` は source 選定だけを説明する。`tools/pegasus/README.md:359`〜`:371` は shell の all-or-none 契約として引き続き正しい。`docs/agent-architecture.md:141`〜`:151` の「明示 role 宣言時だけ consumer 発火」も、role 自動選択を追加しない本変更後に成立する。
- **推奨:** 親が runbook に次の1行を追記する。

> driver の `--run-iteration` 経路では manifest の `sources` が非空なら `--coder-role coder-v4-autonomous-k2` が必須で、空 sources では従来どおり role 省略を許す（D1878）。

## テスト差分と変異 matrix

**B6**

- **所見:** plan の負例は DW-O14 に適合する。成功 helper の流用は避けるべきだが、未到達観測のために loader を拒否する代役へ置き換える必要もない。
- **仮判定:** refuted
- **根拠 file:line:** `docs/dev-wave/operations.md:110`〜`:116` は外側の既存 seam と実物委譲 wrapper を許す。T:1047 は実 resolver、:7169〜:7175 は既存 resolver/layout/pin seam、:7193 は helper 内の drive 代役、:7201 は成功 assert。plan:55〜:70 は実 loader を残し、prepare/receipt に `wraps` を使う。
- **推奨:** N は直書きする。検証の役割を次のように分ける。
  - `ValueError` と drive 未到達：本題の拒否と M1/M4 の検出。
  - prepare 未到達＋campaign root 不在：P1 の早期拒否を最も直接に固定。
  - receipt 未作成だけ：directory 作成後拒否を見逃すため、単独では弱い。
  - loader 未到達：補助として実物委譲 spy なら許容。loader を無条件拒否に替えると、変異時の実 legacy 通過を証明できなくなる。

**B7**

- **所見:** P5 の後半 argv 補正は identity 共有という目的を保つ。非空＋K2 role の実 loader 正例 P も必要である。
- **仮判定:** refuted — P5 が目的を壊すという疑いは棄却。
- **根拠 file:line:** T:6540〜:6548、:6569、:6585〜:6597。L:1531〜:1562 は role を参照せず、identity に manifest level/hash、receipt に resolved manifest と classification/de-novo 宣言を渡す。`knowledge_manifest.py:509`〜`:585` に role field はない。既存 I は loader を代役にしているため、実 consumer の受理証拠にはならない。
- **推奨:** `common` は変更せず後半だけ role を追加する。P は実 loader を通す。`knowledge_use=[]` を非空 sources と組み合わせることを本 wave で新たに禁止しない。

**B8**

- **所見:** 静的棚卸しでは P5 以外に新 guard で赤くなる既存 main test は見つからない。ただし fixture＋非空 manifest＋role 無しの正例も存在しない。
- **仮判定:** real — run guard の検出漏れ。
- **根拠 file:line:** T の `L.main(` は次の15箇所すべてを確認した。

```text
4465, 4504, 5674, 5686, 5688,
6546, 6585, 6636, 6659, 6678,
6691, 7201, 8579, 8828
```

正確には**14箇所**である。`--knowledge-manifest` は :6541、:6639、:7197 の3箇所。:6541 は I、:6639 は空 sources＋role、:7197 の既存 caller 2本も空 sources。残りに manifest はない。

他ファイルの厳密な `L.main(` は0件。間接呼出しは `test_p3_b4_proposal_binding.py:461,494,506,517`、`test_p3_exploration_namespace.py:696,699,713,1160,1222,1476,1534` にあり、base driver の argv に manifest はない。後者の factory は :244、:248、対応表は :416。

- **推奨:** 対案の run guard 除去は、既存テストで KILLED と登録しない。非等価だが未検出であり、実走前の予測は SURVIVED。

**B9**

- **所見:** plan の6 node に限定すれば M1〜M5-route の期待集合は整合する。しかし M5-route は run guard 単独除去の検出漏れを閉じない。
- **仮判定:** real
- **根拠 file:line:** plan:117〜:139、T:7209、:7245、`docs/dev-wave/mutation.md:55`〜`:61`。

| 変異 | plan の6 node 内の期待失敗集合 |
|---|---|
| M1：if/raise 削除 | N |
| M2：sources 反転 | N、E |
| M3：role 条件反転 | N、P、I |
| M4：raise を return 0 に変更 | N |
| M5-route：run/emit の両限定を除去 | I、C |
| run guard 単独除去 | 空集合、SURVIVED 予測 |

K は空 sources なので M3 を殺さない。brief:26 の期待は訂正が必要。

- **推奨:** 対案では M1〜M4 の期待集合を維持し、C と M5-route を外す。run guard 単独除去について、全 KILLED を完了条件に残すなら **fixture＋非空 manifest＋role 無しの正例 F を1本追加**し、期待集合を F とする。追加しないなら SURVIVED を記録し、等価と扱わない。

4観点での比較は以下になる。

| 観点 | 判定 |
|---|---|
| 副作用順序 | 双方 receipt 前。plan は nonce 生成も早く避けるが、対案も run authority 消費前 |
| テスト本数 | 対案は C 不要。ただし F を追加して全 KILLED を満たすなら、新規本数は plan と同じ3本 |
| 変異帰属 | 対案＋F は run guard 単独の意味を直接検証できる |
| scope | 対案は emit 専用条件を追加せず、本題の run 条件だけで表現できる |

**B10**

- **所見:** plan の複数行 anchor は一意になる構成で、削除変異でも前後の既存文を保持している。ただし対案採用後にその anchor は使えない。
- **仮判定:** refuted — plan anchor の曖昧性は現時点では認めない。
- **根拠 file:line:** L:2667 と :2670 の連続する resolver／代入は検索上各1箇所。plan:141〜:156 は間の追加 block を含む全体を old にする。`tools/mutation_harness.py:623` は `{file, old, new}` の exact keys、:882〜:920 は runner target の実在・固定 HEAD 所属を検査するが、関数 node の実在までは保証しない。
- **推奨:** 対案なら emit の `return 0` と次の `build_context` を含む新 anchor を事前登録する。最終 commit で一意性・構文・node 実在を再検証し、`-x` 等で失敗集合を途中打切りにしない。ここでは変更後 file への実注入は検証していない。

**B11**

- **所見:** plan の29 test file 集合から全体 collection を呼ぶ2ファイルを外す判断は妥当。文字列一致だけで本題の検出力を主張してはならない。
- **仮判定:** refuted
- **根拠 file:line:** 再検索で以下の31 test file と補助3ファイルが一致した。接頭辞は `orchestrator/tests/`。

```text
test_p3_s4_loop.py
test_p3_s4_loop_sort.py
test_p3_s4_loop_trigger_gating.py
test_p3_build_authority_cli.py
test_p3_exploration_namespace.py
test_p3_s4_loop_job_contract.py
test_p3_b4_raw_record_producer.py
test_p3_b4_launcher.py
test_p3_b4_wiring_probe.py
test_p3_b4_closed_critic.py
test_p3_b4_proposal_binding.py
test_p3_b4_material_report.py
test_campaign.py
test_s1_direct_comparison.py
test_s8b_floor_campaign.py
test_s8a_trigger_sweep.py
test_s6_sort_sweep.py
test_sort_swo_oracle.py
test_layer3_report.py
test_trigger_gate_binding.py
test_codex_agents.py
test_campaign_import_invariant.py
test_hooks.py
test_pegasus_tools.py
test_s8b_oracle_driver.py
test_s1_known_axes_freeze.py
test_update_acceptance_duration_ledger.py
test_auditor_gate.py
test_floor_pair_driver.py
test_pytest_collection_config.py
test_real_repo_serialization.py
conftest.py
s1_expected_goldens.py
acceptance_duration_ledger.json
```

`subprocess|run_tests` を照合した。全体 collection の経路は `test_pytest_collection_config.py:368`〜`:403`、`test_real_repo_serialization.py:1035` にある。保持対象の `pytest.main([__file__, ...])` 等は自身の直接起動用で、通常 collection 時に全 suite を起動する証拠ではない。T の subprocess は :1015 の Git fixture。

- **推奨:** plan の除外を維持する。29ファイルの回帰確認と、失敗完全集合を固定する変異 node 集合は分ける。

## 親の前提実測への反証

**B12**

- **所見:** 「空 sources の manifest は completed_empty と同義」は過度の一般化。
- **仮判定:** real
- **根拠 file:line:** rulings:24。`knowledge_manifest.py:320`〜`:332` が保証するのは「sources 空 ⇒ scope/result 必須かつ completed_empty」。`:287` は status と result_count=0 の同値を検査するが、`:335`〜`:360` は result_count と sources 長を照合しない。したがって非空 sources＋completed_empty/result_count=0 を逆向きに拒否する条件はない。
- **推奨:** 親の説明を片方向の含意へ訂正する。P2 の sources 判定は維持する。parser の追加整合検査は scope 外であり、本 wave に混ぜない。

**B13**

- **所見:** 「受理される起動の identity・receipt・WAL bytes 不変」は、同条件での通常経路の保存としては支持できるが、全成果物・全再実行への無条件保証にはできない。
- **仮判定:** real
- **根拠 file:line:** brief:18、plan:31。knowledge receipt は `knowledge_manifest.py:575` の決定的 bytes。WAL は `wal.py:1592` の時刻等を含み、T:4410 付近の既存比較も `ts` と `build_attempt_id` を除外している。

さらに rulings:32 が挙げた B4 closure は、`p3_b4_closed_critic.py:635`、:669、:681 で **変更対象ソースの生 bytes を hash** する。`:687` は宣言済み closure と live 値を比較し、`p3_b4_launcher.py:386` が呼ぶ。raw producer も `p3_b4_raw_record_producer.py:1192` で terminal の projection hash と比較する。数行追加だけでも、この closure hash は変わる。

- **推奨:** 「追加 guard を通過する通常経路の identity/knowledge receipt 構築と WAL 生成ロジックを変更しない。同一外部結果を前提とする」と限定する。B4 のソース束縛済み成果物の互換性は別問題として記録し、古い closure を受理するために gate を緩めない。

**B14**

- **所見:** 親の残る前提は概ね現物と一致するが、履歴上の測定結果と検索による閉包保証は区別が必要。
- **仮判定:** refuted — 中核の「直接起動だけが抜ける」という前提への反証はない。
- **根拠 file:line:** rulings:17〜:32 を再照合した。
  - Git log の T-2502/D1878 検索は0件。worklog の持ち越しは現物では `docs/worklog.md:2819` の **(1579)** まで進んでおり、親記載の (1578) は最新ではない。未着地という結論は変わらない。
  - `docs/decisions.md:56844,56847` が coder-role/D1878 の一致箇所。D1999 は :60607 の source 選定規律。
  - loader の相互必須検査、main の knowledge 抑制、prepare の identity/receipt 作成、argparse choices、空/非空 fixture は親記載どおり。
  - `26 passed in 21.52s` は rulings:31 にある親の報告。本 consult では再実走しておらず、独立検証済みではない。
  - consumer path は role adapter と manifest に存在する。指定 SHA の今回の `rg` 逆引きは一致0件だったが、これは検索対象の内容についての結果であり、全履歴・全外部成果物の pin 不在の証明ではない。
- **推奨:** 持ち越し番号を更新する。測定結果の出典を親のログに固定し、「live hash だから変更影響なし」と一般化しない。

## 総括

- **所見:** 対案を採用し、N・P・P5 を維持、C を省く。全 KILLED を要求するなら fixture 正例 F によって run guard 単独除去を検出する。
- **仮判定:** real
- **根拠 file:line:** L:2713〜:2728、plan:95〜:139、brief:18、:26、:30、rulings:24、:32。
- **推奨:** 実装前に位置・変異登録・不変条件の説明を補正する。追加すべき production gate は本題の条件1つだけ。parser、loader、job body の契約は変更しない。

補助の静的 AST／anchor 確認コマンド1件は、PreToolUse の `guard_bash` に「Pegasus login 上の pytest 実行」と判定され拒否された。実際の pytest 起動は含めていなかったが、その確認は未実施として扱い、上記は読取りと検索による判定である。