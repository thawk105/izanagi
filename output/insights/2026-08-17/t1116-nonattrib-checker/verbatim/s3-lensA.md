pytest は実走していない。以下は HEAD `7c83eeac` に対する静的監査結果である。

[重大度 H] test file の非接触は非帰属の十分条件ではなく、少なくとも 4 経路で差分起因の赤が通る / 再現・影響 (`tools/check_acceptance_reds.py:1354-1396`, `s2-plan.md:60-64`, `tools/dev_wave_wait.py:2803-2821`) / 提案: T-389 相当の依存閉包か tested-main の同形全走証拠が無い限り `flake` を受理しない。

1. production 経路: wave が `orchestrator/campaign/s8b_floor_campaign.py:4293` を変更し、並列全走時だけ共有一時資源を衝突させる。node `orchestrator/tests/test_s8b_floor_campaign.py::test_measure_run_cmd_projection_removes_runtime_root_and_rejects_missing_token` は全走で赤、main/wave の単独走は双方 rc=0。差分は production file だけなので `collection.path` は非接触となり `flake`。

2. conftest 経路: `orchestrator/tests/conftest.py:390-446` の grouping または context hook を変更し、複数 item があるときだけ状態を漏らす。実測 node の形 `orchestrator/tests/test_dev_wave_wait.py::test_public_main_real_signal_after_success_uses_restored_handler` は単独なら双方緑でも、全走だけ赤にできる。

3. fixture 経路: `orchestrator/tests/s8b_floor_evidence_fixture.py` の module cache または共有 path を変更する。同 fixture を読む `orchestrator/tests/test_s8b_floor_campaign.py::test_perf_unavailable_continues_and_records_one_run_receipt` が先行 test 後だけ赤、単独は双方緑となる。

4. plugin 経路: `orchestrator/campaign/patchharness.py:49` を変更する。これは `conftest.py:439-446` の pytest hook から呼ばれるため、複数 node 間だけ context を漏らし、例えば `orchestrator/tests/test_campaign.py::test_buildcache_clears_stale_build_dir` を全走限定で赤にできる。

いずれも main rc=0、wave rc=0 から `flake` となり、変更後 waiter が受理する。checker 自身が未変更なら land の checker blob 一致も通る。  
成果物影響: end-to-end 受理集合へ「差分依存 file が原因だが test file は非接触」の cell が追加され、壊れた main を基礎に certified 選択、レポート、試行台帳が作られる。

[重大度 H] checker 自身の変更は塞がるが、waiter と runner の自己変更は blob 検査で塞がらない / 再現・影響 (`tools/dev_wave_wait.py:1975-2013,3124-3128`, `tools/dev_wave_land.py:659-748`) / 提案: acceptance tooling の更新には tested-main 固定の外側 launcher を使う別 upgrade protocol を設ける。

- checker は wait が main/tip blob 不一致を `tools/dev_wave_wait.py:1982-1985` で実行前に拒否し、land も `tools/dev_wave_land.py:710-744` で再検査する。したがって本 wave は全走が赤なら、正しい flake でも受領証を発行できない。child-green が必須である。

- waiter は「実行中 bytes = tip bytes」しか検査しない (`tools/dev_wave_wait.py:1584-1663`)。wave が waiter を変更し、実 child rc=1 を receipt 上で `child_rc=0, verdict=child-green` とすれば、land は変更後 waiter の tip blob と receipt を照合して受理する。main waiter との一致検査は無い。

- `tools/run_tests.py` はさらに弱く、land は tip に存在することしか確認しない (`tools/dev_wave_land.py:700-705`)。runner は既に全走と target 走を区別できる (`tools/run_tests.py:402-425,1698-1709`)。全走だけ rc=1、checker の単独 selector だけ rc=0 とする変更は、`tools/check_acceptance_reds.py:956-994` を正面から欺ける。

成果物影響: acceptance receipt 自体が wave tip による自己証明になり、実際は赤でも台帳へ child-green と記録され、certified 成果物の land 根拠が失われる。

[重大度 H] exact path 比較は submodule、directory collector、path alias で直接 test source の接触すら見落とす / 再現・影響 (`tools/check_acceptance_reds.py:501-510,896-938,1237-1253`, `s2-plan.md:29-46`) / 提案: lexical canonicalityと path の祖先・子孫 overlap を検査し、symlink・gitlink・virtual collection は fail-closed にする。

- gitlink 更新では `--ignore-submodules=none` でも superproject の name-only は `external/ccbench` しか返さない。内部変更またはそれに依存する top-level test pathとは一致しない。land の gitlink 検査は同期を要求するだけで、main が tip へ進んだ後に postcondition を返す (`tools/dev_wave_land.py:2831-2858`)。

- custom directory collector が node `orchestrator/tests/cases::case_a` を返し、wave が `orchestrator/tests/cases/a.yaml` を変更する場合、collection path は directory、diff は子 file なので exact 比較は外れる。

- `_outcome_reference()` は `./orchestrator/tests/test_x.py` や重複 separator を canonical 文字列へ固定しない。custom collector がその表記を保持すると、Git の `orchestrator/tests/test_x.py` と一致しない。symlink 経由の test path と実 target pathも同様である。

成果物影響: `wave_touched_path` が偽陰性となり、本来 attributable の node が `flake` として acceptance receipt の `red_nodeids` へ入る。

[重大度 M] two-dot は tip tree の差しか見ず、空 diff でも wave 起因の挙動差が存在する / 再現・影響 (`s2-plan.md:114-118`, `tools/dev_wave_wait.py:3038-3099,3181-3189`) / 提案: commit identity・履歴を読む test が存在する限り、空 path 集合を安全証明にしない。

- `tested_main == wave_tip`、empty commit、または途中で変更して tip で復元した場合、endpoint tree diff は空になる。

- repo には HEAD を session cache key に使う実コードがある (`orchestrator/tests/real_repo_receipt_memo.py:78-96`)。empty commit だけでも cold-cache・並列競合経路は変わり得る。また Git 履歴を読む test も存在する (`orchestrator/tests/test_s8b_oracle_driver.py:3468-3479`)。

- merge commitは実運用では main が tip の ancestor となるため、通常の net tree change に対する two-dot 自体は妥当であり、常に全 path になるわけではない。問題は「tree diff が因果差分の全集合ではない」点である。

成果物影響: path 集合が空という理由だけで履歴起因の赤を受理し、台帳の `tested_main..tested_tip` 参照が実際の依存入力を表さなくなる。

[重大度 M] waiter の受理下限は rc の型だけでなく値を固定しなければならない / 再現・影響 (`tools/dev_wave_wait.py:2803-2815`, `s2-plan.md:131-139`) / 提案: branch ごとに exact type と exact value を同時検査する。

| node 形 | 現行または形だけの検査 | 必須条件 |
|---|---|---|
| `non-attributable` | `rerun_rc` が int なら `0`, `-1`, `2` も通る | `type(rerun_rc) is int and rerun_rc == 1` |
| `flake` | 5 field と int 型だけなら任意の組が通る | 3 値すべて exact int `0` |
| `flake` alias | `(rerun_rc, main_rerun_rc, wave_rerun_rc)=(1,0,0)` | `rerun_rc == main_rerun_rc == 0` |
| 誤分類 | `(0,1,0)` は本来 non-attributable、`(0,0,1)` は attributable | どちらも拒否 |
| 範囲外 | `(2,-1,7)` | 拒否 |
| JSON bool | `False == 0` は真 | `type(value) is int` も必須 |

段 2 プランの「全 rc が 0」は正しいが、brief v2 の「flake 形を受理」だけでは不足する。現行 non-attributable branch の値穴も同時に縮めるべきである。land は rc を受け取らず `red_nodeids` だけを見るため、wait 通過後には回復不能である。  
成果物影響: 意味的に不可能な node 形まで受理集合へ入り、台帳には rc 根拠を失った nodeid だけが残る。

[重大度 H] probe2 は P3 を必ず通す no-op control であり、実運用 flake の証拠ではない / 再現・影響 (`probe2-receipt.json:1`, `run_probe2.sh:9-14`, `tools/check_acceptance_reds.py:1355-1396`) / 提案: probe2 は「同一 snapshot の単独再走が2回緑」の証拠に限定して記述する。

probe2 は `tested_main == wave_tip == 5a19b8ab...` なので、新 P3 の `git diff A..T` は構造的に空である。main probe と wave probe も同じ tree・同じ submodule・同じ runner を別 worktreeで走らせるだけである。

実 acceptance は lease 取得時の main SHA を保持し、必要なら main を wave へ mergeし、最終 tip を別 SHA として checker に渡す (`tools/dev_wave_wait.py:3028-3099,3181-3189`)。したがって通常は A と T が異なり、probe2 と挙動的に非同値である。

成果物影響: probe2 を P3 または R2 の実効性証拠としてレポート・台帳へ載せると、常に空になる比較を安全根拠として参照することになる。

[重大度 H] 4/89 は R2 の救済率を測っておらず、「95.5% が残る」は支持されない / 再現・影響 (`touch_stats.py:11-49`, `brief.md:115-116`) / 提案: この数字を裁定根拠から外し、分類候補と path 集計を分離する。

読取時点の 45 receipt / 89 node は、88 `attributable`、1 `non-attributable`、0 `flake` だった。集計 script は `nodes` を分類・schema・重複なしに全件分母へ入れ (`touch_stats.py:21-31`)、wave 単独 rc を一度も測っていない。したがって 85 件が R2 で救済されるとは言えない。

さらに `nodeid.split("::")[0]` と非 NUL の既定 `git diff --name-only` (`touch_stats.py:33-41`) は rename 旧名、quoted path、submodule 内 path、非 canonical collection pathを過小計上する。一方、同じ test file のコメントや別 nodeだけを触った場合も「接触」と数えるので、因果率を過大計上する。

成果物影響: レポートの 4.5% と 95.5%、それを参照する段 4 裁定・worklog・変異台帳の費用便益評価が無根拠になる。

[重大度 M] 変異を end-to-end で走らせると別層が先取りし、kill 帰属が崩れる / 再現・影響 (`tools/dev_wave_wait.py:1982-1985,2754-2756`, `orchestrator/tests/test_check_acceptance_reds.py:571-611`, `orchestrator/tests/test_dev_wave_land.py:943-960`) / 提案: checker と waiter の変異を別登録し、期待 node を層ごとに一意化する。

- P3 の過剰受理変異を checker commit として実 acceptance に入れると、main/tip checker blob 不一致が実装より先に落とす。これは P3 の kill ではない。`test_check_acceptance_reds.py` の直接単体 nodeだけを killer にする必要がある。

- 「何か差分があれば attributable」という checker 過剰拒否変異は、既存 `test_main_green_wave_green_is_recorded_as_flake` が既に `tracked.txt` だけを変更して殺す (`test_check_acceptance_reds.py:571-611`, helper `:106-109`)。新規検出力として数えてはいけない。

- waiter の flake branch 削除を殺す正例は、新しい valid 5-field receipt の waiter 単体 testでなければならない。touched-file fixtureでは checker rc=1 が `dev_wave_wait.py:2754-2756` で先に止める。

成果物影響: 分離しないと mutation ledger が「P3 または consumer を実証した」と記録しながら、実際には blob gate や既存 test が殺しただけになる。

[重大度 L] 指定された特殊形の一部は計画どおりなら抜け道ではない / 再現・影響 (`tools/check_acceptance_reds.py:501-556,896-938,1237-1253`, `orchestrator/tests/test_check_acceptance_reds.py:2180-2209`) / 提案: 新しい nodeid 再解析を足さず、静的前提を回帰 testで固定する。nit。

`@group`、parameter ID 内の追加 `::`、` - detail` は最初の path と collection exact selector を分離しており、P3 が `main_probe.collection.path` を使えば影響しない。同名 basename も完全な repo-relative path 比較なので衝突しない。.py 以外も拡張子制限が無い。計画の `-z --no-renames` は quoting と rename の旧新 pathを安全側に扱い、mode-only の test file変更も name-only に現れる。

成果物影響: これら自体は現在の受理集合を広げない。ただし専用 pin が無ければ将来の nodeid 再解析で同じ受理境界が崩れ得る。

## 総括

NO-GO。直接 test-file 非接触は非帰属証明ではなく、production、conftest、fixture、plugin、submodule、履歴、waiter/runner 自己変更から差分起因赤を通せる。  
段 4 の推奨択一は、(A) waiter の flake 受理を見送り fail-closed を維持し、P3 は防御補助に限定する、である。  
(B) を選ぶなら、tested-main 固定の trusted launcher、runner/waiter upgrade protocol、main 同形全走または実効依存閉包まで scope を広げる明示的な人間裁定が必要である。  
probe2 と 4/89 は受理拡大の根拠にせず、rc 値 pin と層別 mutation を事前登録し直すべきである。