### B-4 識別子が成果物へ残らず、正式標本の選択層が閉じない

対象: 両方

根拠:

- `materials/D1033.md:3-9` は、専用起動器と識別子による機械的な正式標本の区別を要求している。
- `s2-plan.md:26-29,42,142` は識別子を戻り値、stdout、`search_config`、`CampaignConfig` のすべてから除外する。
- 現行 receipt の exact schema `orchestrator/campaign/p3_b4_closed_critic.py:228-272` と、消費記録 `orchestrator/campaign/p3_s4_loop.py:1262-1269` のどちらにも launcher 識別子またはその commitment は無い。
- `orchestrator/campaign/loop.py:232-254,291-317,492-493` の `run_campaign` は任意の `CampaignConfig` を受け、B-4 launcher 認可を検査せず certified 結果を書ける。`orchestrator/tests/test_p3_s4_loop.py:2497-2500` は `search_config` の marker を `replace` で直接構築できる実例である。
- `orchestrator/campaign/artifact_admission.py:1148-1165` の certified view も B-4 launcher commitment を要求しない。repository code の静的 census では B-4 marker の consumer は 3 driver と closed critic に限られ、report、registry、ledger の consumer は無かった。

成立すると何が変わるか: launcher を通らない exact-marker cfg が `run_campaign` から generic certified artifact になり得て、report・台帳は launcher 正式標本と区別できないため、D1033 の受理集合が成果物層では閉じない。

推奨: 実装済み扱いにせず、D1050 と接する「launcher authorization commitment の永続化先、certified sink、report・台帳 consumer」を裁定パッケージ候補にする。launcher で鋳造した commitment を receipt または campaign artifact に残し、`run_campaign` の certified write と正式標本 consumer の両方で要求する。

### driver kind を持つ識別子が driver 境界で照合されていない

対象: プラン

根拠:

- `s2-plan.md:24-29` は `B4LaunchIdentifier` に driver kind を持たせるが、config/formal verifier の仕様は production/test seal の区別だけである。
- driver kind と admission record の再照合を明記しているのは production factory だけである `s2-plan.md:53`。
- 同じ識別子を `default_cfg`、factory、`main`、`drive_iteration`、`run_one_iteration` へ渡す設計である `s2-plan.md:52-56,64-68`。

成立すると何が変わるか: launcher registry の誤配線または同一 process 内の取り違えで、base 用識別子が sort/trigger の bootstrap や formal driver を認可し、campaign id・receipt の driver 帰属が分裂し得る。

推奨: `require_b4_config_identifier` と `require_b4_formal_identifier` に `expected_driver_kind` を必須化し、3 driver の全境界と factory で exact 一致を検査する。cross-driver identifier の負例も追加する。

### projection 変更の閉包が親 brief より広い

対象: 両方

根拠:

- 親 brief は launcher を閉包へ入れることを主な hash 変更要因としている `materials/brief.md:63-65,90-92`。
- 実際の manifest は全 driver について `p3_b4_closed_critic.py` と base driver を含む `orchestrator/campaign/p3_b4_closed_critic.py:610-663`。今回この両方を編集するため、launcher を閉包へ入れなくても全 3 projection が変わる。sort/trigger 自身も各閉包へ追加される `:643-652`。
- path pin は production manifest に加え、独立算出 helper `orchestrator/tests/test_p3_b4_closed_critic.py:491-554` と exact-set test `:1554-1617` にもある。
- 短縮表現は receipt の `projection_sha256` `orchestrator/campaign/p3_b4_closed_critic.py:246,968`、操作 key は admission の `expected_closed_critic_projection_closure_sha256` `orchestrator/campaign/p3_b4_admission_record.py:201-228,607-624` に残る。
- 静的算出した現行値は base `a2824c5c…03ec`、sort `f81eab6f…71c5`、trigger `9e4cf979…4156`。full/8桁とも repository 内 literal match は無かったので、親の「hex literal pin なし」はこの狭い意味では正しい。
- pair 作成時 `orchestrator/campaign/p3_b4_closed_critic.py:1150-1159`、invocation 中 `:870-874`、receipt 再読 `:1590-1591`、certified pair と admission の照合 `:1883-1888` がすべて live projection を要求する。

成立すると何が変わるか: 既存 receipt bytes 自体は不変でも再検証では拒否され、新規 receipt の `projection_sha256`、terminal receipt SHA、proposal の receipt binding、消費記録の filename/hash、admission sidecar bytes が連鎖して変わる。

推奨: P4 を「launcher 追加」ではなく明示的な受理集合 migration として扱う。独立 helper `test_p3_b4_closed_critic.py:491-554` も更新対象に含め、旧 receipt を失効させるのか versioned verifier で再検証可能にするのかを事前に固定する。現プランのままなら receipt schema は v3 のままだが、launcher commitment を receipt に加える場合は schema bump が必要である。

### 既存 6 拒否の発火維持が証明できない

対象: プラン

根拠:

- 現行の 6 拒否は `orchestrator/campaign/p3_s4_loop.py:1219-1245` に順序付きで存在する。
- プランは `drive_iteration` の先頭で production identifier を要求する `s2-plan.md:99-105`。一方で既存 receipt gate は変更しないとする `:145`。
- 既存 B-4 tests を test-only identifier fixture へ移すとしている `s2-plan.md:74` が、formal driver は test-only identifier を拒否する仕様である `:41,123-129`。
- 現行 integration tests は `drive_iteration` を直接使う。例として bootstrap `orchestrator/tests/test_p3_s4_loop.py:2721-2758`、no-build `:2761-2783`、receipt verification `:2818-2857` がある。

成立すると何が変わるか: marker 不在での receipt 供給は直接 unit gate なら維持できるが、no-build、非権威 layout、bootstrap receipt、continuation receipt 欠落、検証中改変は新 launcher error に前置され、旧拒否理由と既存 15 変異の参照が検査不能になる。

推奨: 6 条件を `require_b4_iteration_authorization` の直接 unit test として全件残す。そのうえで、実際に verified admission から作った非公開 production identifier を使う integration fixture を用意し、launcher 認可通過後にも同じ 6 拒否が発火することを別に固定する。新旧 gate の順序もプランへ明記する。

### exact message は変異の過剰決定を解消しない

対象: プラン

根拠:

- プランは境界ごとの message 差で過剰決定を避けるとしている `s2-plan.md:68`。
- `drive_iteration` は既存 gate の後に `run_one_iteration` を呼ぶ `orchestrator/campaign/p3_s4_loop.py:1451-1476,1504-1506`。main は `default_cfg` の後に drive を呼ぶ `:1622-1628,1673-1682`。
- trigger の公開 `run_one_iteration` は `_run_one_iteration_resolved` へ進む `orchestrator/campaign/p3_s4_loop_trigger_gating.py:793-829`。drive も同 resolved 関数を直接呼ぶ `:1010-1018`。
- production factory は識別子 gate の後にも admission、executable、projection の拒否層を持つ `orchestrator/campaign/p3_b4_closed_critic.py:1186-1216`。

成立すると何が変わるか: main、drive、trigger 公開 API、factory、test-only 流用の変異を外しても同じ入力は下層で拒否され、テストが落ちても「受理集合が変わった」のではなく error message が変わっただけになる。

推奨: 変異 matrix を二分する。境界 ownership test は下層 stub を使い「routing の証拠」と明記し、E2E acceptance test は冗長な全 gate を一括で外す変異または認可済み positive control と対にする。負例 1 の default_cfg と base/sort の直接 run-one は単独帰属可能だが、負例 3〜6 と trigger の二重 run-one gate は現状のままでは単独帰属不可である。

### golden 一覧は完全ではない

対象: 両方

根拠:

- campaign hash は `spec_content`、commit、`search_tag`、`search_config`、trial のみから算出される `orchestrator/campaign/ident.py:150-189`。識別子を config に保存しない限り、ordinary identity は静的には不変である。
- 親が挙げた ordinary pin は base `orchestrator/tests/test_p3_s4_loop.py:2475-2494`、sort `orchestrator/tests/test_p3_s4_loop_sort.py:854-870`、trigger 8 件 `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:112-134` に実在する。
- 直接 scope の同種 pin として、B-4 marked on/off の 6 件が別 test にある: base `ad0444da/8700ee8e`、sort `2c241821/df423528`、trigger `2adb6cf7/6328b84a` `orchestrator/tests/test_p3_b4_closed_critic.py:2564-2588`。
- 他 test file の historical/negative pin は base `0b53a387`、sort `3be89e0d`、trigger `3f72ecd5` `orchestrator/tests/test_artifact_admission.py:83-104`、pre-T428 trigger `0e79a5f1/63bc09ae` `orchestrator/tests/test_campaign.py:3095-3112`。同じ historical paths は `test_critic.py:580-588`、`test_s6_sort_sweep.py:812-816`、`test_s8a_trigger_sweep.py:1026-1030` にもある。

成立すると何が変わるか: 旧 closed-critic CLI test の置換時に B-4 marked 6 IDs の exact pin が消え、launcher 経路の campaign path、receipt campaign_id、比較参照が無検知で変わり得る。

推奨: ordinary golden に加え、marked 6 IDs を新 launcher の on/off config test へ移植する。historical/negative IDs は更新対象にせず、影響在庫として明記して保持する。

### D1042 の一回 token を後付けしにくい認可形である

対象: プラン

根拠:

- D1042 の署名・一回性は実装しない `s2-plan.md:33`。
- 同じ sealed identifier を config 作成、factory、main、drive、run-one の全境界で繰り返し検査する `s2-plan.md:37-56,64-68,187-189`。

成立すると何が変わるか: 将来 token を最初の gate で消費すると後続 gate が失敗し、消費を最後まで遅らせると入口の一回性が成立しないため、D1042 着地時に call graph と API を作り直す必要が出る。

推奨: 今回は署名を実装せず、将来の外側 `SignedLaunchToken` と、launcher が消費後に鋳造する内側の multi-hop `B4LaunchContext` を別概念にする。現 identifier は後者として命名・仕様化する。

### 既存受理集合の拡張、D1043/D1050 の先取り

対象: 両方

根拠:

- ordinary branch を変えず新しい拒否だけを足す設計である `s2-plan.md:39-44,139-146`。
- proposal bytes の固定は明示的に行わない `s2-plan.md:55-58`。WAL schema と受理記録 path も変更面外である `:14,145-146`。

成立すると何が変わるか: 無し。静的に確認した範囲では、既存の拒否入力を新たに受理する分岐、D1043 の送信前固定、D1050 の path 一本化の先取りは無い。

推奨: 代案なし。D1050 と接する永続 identifier 問題だけは、最初の所見の裁定パッケージとして分離する。

## 総括

最大の問題は、識別子が in-process object に留まり、certified sink・report・台帳へ証拠が残らないため、D1033 が成果物層で成立しない点である。  
projection は launcher 追加前から今回の編集面を閉包しており、既存 receipt の受理失効は明示的な migration として扱う必要がある。  
既存 6 拒否は新 gate 通過後の到達検査が不足し、test-only fixture だけでは formal 境界へ到達できない。  
exact error message は層の routing を示すが、変異による受理集合の単独帰属にはならない。  
pytest は実走しておらず、上記は指定資料と repository code の静的検査、および read-only の projection hash 算出に基づく。