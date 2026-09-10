## 総括

**STOP 推奨です. [T-913] は実装せずユーザーへ返すべきです.**

BLOCKER 2 件, MAJOR 2 件, MINOR 1 件です. 4 function は real repository の成長比例テストではなく, `ledger.py` の拒否境界を守る唯一検出者です. `correctness_gate=False` は成立しません.

## BLOCKER B1: 4 function は保留裁定の対象範囲に入っていない

根拠:

- 各 test は `_init_repo(tmp_path)` で固定サイズの一時 Git repository を作ります. real repository の commit 数や file 数を走査しません. `orchestrator/tests/test_t793_publication_ledger.py:31-41,180-185,259-350`.
- D335 の対象は repository growth に比例してコストが増える構造です. `docs/decisions.md:14957-14974`.
- D328 は implementation と measurement の同一性検査だけを保留し, correctness gate と防壁の自己完全性を除外します. `docs/decisions.md:14786-14793`.
- D320 も既存 live check を黙って外す授権ではないと明記しています. `docs/decisions.md:14532-14538`.
- それにもかかわらず plan は `hold_axis="provenance-chain"` と第 4 束を authority にします. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-freeze-hold-residual/s2-plan.md:48-76`.
- brief 自身も wall は動かない見込みと認めています. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-freeze-hold-residual/brief.md:68-71`.

成果物影響: default pytest の受理集合だけが広がり, hold 台帳と統合 report の `ruling` と `hold_axis` は適用外裁定を参照します. 現時点の certified 選択値は non-test caller が無いため不変ですが, wall 改善根拠もありません.

推奨対応: [T-913] を scope から外してユーザーへ返してください. 未使用 publication ledger 全体を退役させるなら, unique test だけを skip するのではなく, module と将来用途を含む別裁定にしてください.

## BLOCKER B2: `correctness_gate=False` は誤分類であり, 唯一検出者を隠す

根拠:

- duplicate identity 拒否は `ledger.py:228-252` を直接検査します. `test_t793_publication_ledger.py:180-185`.
- merge history の正例は同一 bytes を持つ正当な merge を受理できることを検査します. `test_t793_publication_ledger.py:259-302`.
- committed truncate / rewrite 拒否は prefix-only history を検査します. `test_t793_publication_ledger.py:305-328`.
- delete / recreate 拒否は履歴から予約を消せないことを検査します. `test_t793_publication_ledger.py:331-350`.
- 実装側はこれらを明示的な fail-closed gate としています. `orchestrator/publication/ledger.py:247-252,311-361`.
- collection hook は `correctness_gate` の値を見ずに skip します. `orchestrator/tests/conftest.py:359-369`. `False` は検出力を残さず, report から隠すだけです.
- inventory は `True` の key だけを `correctness_gate_keys` に出します. `orchestrator/tests/growth_test_holds.py:215-229`.
- D335 を根拠にする場合でも, correctness test はその事実を一覧へ表示する契約です. `docs/decisions.md:14959-14964`.

性質検索では, 同種の append-only guard は `s8c_acceptance_receipt.py` や `trial_registry.py` にありましたが, それらは publication ledger を実行しません. `entry-duplicate`, publication 固有の prefix error, delete/recreate, merge 正例を検査する別 test は見つかりませんでした.

追加の取り残しとして, working tree が committed tip の strict extension であることを守る `orchestrator/publication/ledger.py:377-382` は現在も直接 test がありません. plan が引用する `ledger.py:311-383` 全体を 4 function が覆うわけではありません.

成果物影響: 通常受入は duplicate reservation, committed rewrite, committed delete/recreate を許す mutationと, 正当な merge を誤拒否する mutationを受理可能になります. 統合 report の `correctness_gate_keys` からも 4 key が欠落します.

推奨対応: 4 function を保留しないでください. 現在の直接指示に反して保留する選択肢はありません. working-tree strict-extension の未被覆は別の裁定候補として返してください.

## MAJOR M1: 統合 inventory の新規 layer 検出は自己参照で成立しない

根拠:

- plan は layer ID を production / test の exact 2 層に固定し, その同じ 2 source と projection を比較します. `s2-plan.md:171-184`.
- 第 3 の保留機構を別 module に追加して inventory を更新しなければ, この 2 source も contract の期待値も変わらず緑です.
- したがって brief が主張する `保留層が増えたのに inventory に出ない` 検出力はありません. `brief.md:60-62`.

成果物影響: 統合 inventory の layer set, count, ID 参照が欠落しても contract は緑のままになり, user-facing report が完全な保留一覧を装います.

推奨対応: 全 hold provider が登録を必須とする canonical provider registry を作り, 未登録機構を独立検査で拒否してください. それを作らない場合は `現行 2 層の snapshot` と保証範囲を下げてください.

## MAJOR M2: `held-by-default` は現在の実効状態を表さず, plain runner も未解決

根拠:

- plan は ambient env に関係なく test layer を `held-by-default` と表示します. `s2-plan.md:145-155`.
- 実際には exact token があれば skip は一切付与されません. `orchestrator/tests/conftest.py:277-289,365-369`.
- dispatch は同 env を計算 node へ伝播します. `tools/pegasus/dispatch_compute.py:59-67,1339-1343`.
- repository は plain runner が hold を迂回する既知限界を記録し, [T-930] を未解決で残しています. `docs/worklog.md:182-185,743-745`. 二重 runner 自体は正式契約です. `orchestrator/tests/README.md:105-120`.
- 対象 file の `_run()` は `pytest.main()` を呼びますが, plan には direct `python3 file.py` で hook が必ず load されることを pin する検査がありません. `test_t793_publication_ledger.py:353-360`.

成果物影響: inventory が 34 entry を held と表示しても, current env または runner 経路では実行中になり得ます. report と実際の受入 run の参照状態が一致しません.

推奨対応: `configured_status` と `effective_status` を分離し, env opt-in と runner 経路を表示してください. plain-runner 問題は [T-930] の裁定パッケージとして返し, 解決前に全層で held と主張しないでください.

## MINOR N1: `measured_seconds` と count の粒度が曖昧

根拠:

- 4 function は 5 pytest node ですが, plan は 4 row として数えます. `brief.md:17-22`.
- parametrized 2 node の丸め値を加算して `0.06` という 1 scalar にします. `s2-plan.md:28-34,62-69`.
- schema は有限かつ非負だけを検査し, run ID, aggregation, node count, precision を持ちません. `orchestrator/tests/growth_test_holds.py:196-203`.
- exact digest も `measured_seconds` を含まず, 別 test が転記値を固定するだけです. `s2-plan.md:115-123`.

成果物影響: report の `count=34` は function entry 数であって実行 node 数ではなく, `observed_seconds=0.06` も 2 node の合算と分かりません. certified acceptance 自体は変わりません.

推奨対応: count を `function_count` と明記し, measurement に `node_count`, `aggregation`, `run_id`, `precision` を持たせるか, 再現可能な raw receipt が無ければ `None` のままにしてください.

## 崩せなかった前提

- non-test caller ゼロは独立検索でも確認しました. public/private reader, module path, ledger path/schema literal, dynamic import, entry point, current docs の運用手順を検索しましたが, production caller はありませんでした. ただし plan はこの前提の将来 drift を機械検査せず comment だけにしています.
- [T-917] の land 済み前提は正しいです. feature `135836be` と fix `54018867` はともに HEAD の ancestor で, 現行 module は `HELD=True`, 21 ID, count/hash runtime check, literal release condition を持ちます. 再実装は不要です.
- P4 の `tools/hold_inventory.py` 配置は current campaign import invariant に抵触する証拠を見つけられませんでした.
- plan 記載の 34 count と 2 digest は read-only 再計算と一致しました.

pytest は実行していません. green は主張しません. file 編集も行っていません.