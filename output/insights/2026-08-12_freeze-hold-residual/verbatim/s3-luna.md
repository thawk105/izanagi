## 総括

実装と pytest は未実施です。read-only の静的検査と digest 再計算のみ行いました。

判定は BLOCKER 1 件、MAJOR 5 件です。3 pin の予測値自体は、想定 4 key をメモリ上で追加して再計算すると plan の値と一致しました。問題は算術ではなく、独立性と意味の不足です。

### BLOCKER-1: `correctness_gate=False` の分類根拠が弱い

根拠: `brief.md:39,53-56`, `s2-plan.md:9,23-26`, `orchestrator/publication/ledger.py:228-252,311-389`, `orchestrator/tests/test_t793_publication_ledger.py:180-185,259-350`

4 件は現在の非 test caller がないだけで、publication ledger の重複排除と履歴改変拒否という本番実装の不変条件を検査している。brief は self-integrity を保留対象外としているため、caller 数だけで `False` にするのは危険。

影響: 4 key が `correctness_gate_keys` から外れ、通常受入の skip 集合に本番不変条件の検出器が入り、certified の前提と台帳上の分類が変わる。

推奨: 段 4 で裁定する。保持するなら `active_acceptance_gate` と `self_integrity` を別 field にし、将来 caller が増えたら機械的に保留解除または停止する契約を追加する。

### MAJOR-1: digest と束別 assertion が reason と既存 bytes を pin していない

根拠: `s2-plan.md:81-123`, `orchestrator/tests/test_growth_test_holds_contract.py:105-120`, `orchestrator/tests/growth_test_holds.py:28-36,215-228`

row digest は key, axis, ruling, correctness のみで、`reason`, `release_condition`, `measured_seconds`, `collateral_note` を含まない。source を import して digest を算出する command も、実装後に変更済み source から pin を作れる。

例えば新規 4 行の reason を別内容へ変更しても、予定された assertion は緑になり得る。既存 30 行の bytes 再整形も検出しない。

影響: skip reason と inventory report の根拠が変わる一方、台帳の count, key 集合, row pin は緑のままとなり、誤った運用参照が残る。

推奨: 新規 4 行の reason と `collateral_note=None` を独立した期待値で exact pin する。既存 30 行の bytes 保持も別の baseline pin で検査し、実装後 source から期待値を生成する手順を受入条件にしない。

### MAJOR-2: 統合 inventory の完全性が source 同一比較に依存する

根拠: `s2-plan.md:135-184`

想定される壊れ方は次のとおり。

| 壊れ方 | 予定検査 |
|---|---|
| production layer 自体を落とす | exact 2 layer で捕捉 |
| 既存 layer の item を落とす | exact key set で捕捉 |
| 新しい hold provider または producer call site を追加したが inventory が無視する | 捕捉しない |

最後は layer ID を exact 2 件に固定し、現在の 2 source だけを import するため、source 外の hold 層を発見できない。さらに renderer 関数だけを呼び、CLI の `main` と実際の `--format` dispatch を呼ばなければ、CLI wiring の破損も緑になり得る。

影響: inventory の layer 数、item 数、解除参照が実際の hold 集合より少なくなり、運用者が不完全な台帳を完全版として参照する。

推奨: source とは独立した期待 manifest を置き、全 layer の ID, count, release surface を pin する。`main` を実際に呼ぶ契約も追加する。新規 layer の自動発見を保証できないなら、T-914 の完全性を scope 外として段 4 の裁定へ返す。

### MAJOR-3: `measured_seconds` と `0.03 + 0.03 = 0.06` の意味が未定義

根拠: `s2-plan.md:30-34,64-69,146-156`, `orchestrator/tests/growth_test_holds.py:28-36,215-228`, `orchestrator/tests/conftest.py:292-303`

normalized function key は 1 key だが、parametrize により 2 node ある。`0.06` は serial sum としてはあり得るが、field に測定範囲、node 数、runner、commit, machine, parallelism がない。JSON は元の `measured_seconds` 名を保持するため、human renderer の説明だけでは機械 consumer の誤読を防げない。

影響: inventory の 34 entry が実際の 5 node と混同され、秒数が保留理由または受入 wall への寄与と誤解される。

推奨: `observed_seconds`, `measurement_scope`, `parametrized_node_count`, `measurement_source` を分離する。根拠が D320 と caller 数なら、秒数を `None` にして測定値を別の監査記録へ置く選択も検討する。

### MAJOR-4: 親の wall 不変という一般化に測定条件がない

根拠: `brief.md:66-71`, `s2-plan.md:125-129`

「鎖外だから 0.14 秒を足しても wall は動かない」は、同一 HEAD, submodule SHA, machine, worker 数, runner args, env, scheduler, 並行 wave の不在を満たす場合に限る。鎖外は serialization group 外という意味であり、xdist worker の負荷分散や critical path から独立という意味ではない。inventory 契約テストの追加コストも含まれる。

影響: acceptance report に「wall 不変」と記録しても、実際は worker 配置や環境差の結果であり、受入全走の比較値と保留効果の参照が無効になる。

推奨: before/after で HEAD, submodule, machine, nproc, command, env, queue 状態を記録し、複数回の median と分散を比較する。0.14 秒の合計と wall を別値として報告する。

### MAJOR-5: 実効層と bypass surface が inventory scope から抜けている

根拠: `s2-plan.md:141-167`, `orchestrator/tests/conftest.py:346-390`, `docs/worklog.md:184-185`, `tools/run_tests.py:69-70,807-808`, `tools/pegasus/dispatch_compute.py:57-67`

production hold は `s1_measurement_freeze.py:433-434`, `s1_known_axes_freeze.py:871-872`, `s8b_floor_campaign.py:1590-1591`, `s8b_oracle_driver.py:198-199`, `t080_freeze_migration.py:2341-2359` など複数 consumer から marker を発行する。test hold は conftest の collection hook に依存し、plain runner はその hook を通らない。また Pegasus では env の transport allowlist も解除経路の一部になる。

影響: inventory が `held-by-default` と表示しても、実際には plain runner で実行可能であり、producer call site や解除 transport の欠落を報告しない。

推奨: `enforcement_surface`, `bypass_surface`, `producer_refs`, `release_transport` を inventory に含める。そこまで scope に含めないなら、T-914 は source registry の棚卸しだけだと明記し、完全な実効 inventory を名乗らない。

## 所見にならなかった点

- collection: 現在 `test_t793_publication_ledger.py` は 1 file だけで、`conftest.py:267-270` が parametrize suffix を除去するため 2 node は 1 key に正規化される。`tools/run_tests.py:54,379-387` の full acceptance target も complete collection 条件に合う。opt-in は complete collection 検査を無効化しない。file collision は `UsageError` で止まるため、現状に追加起因の false green は見つからない。
- `tools/` placement: 現行 contract 自体が `from tools import run_tests` を使っており、pytest の `testpaths` は `orchestrator/tests` のみ。campaign import invariant も `orchestrator/campaign` の相対 import を対象にするため、現案の置き場所に静的な抵触は見つからない。
- pytest green: 実行していないため、緑とは報告しない。