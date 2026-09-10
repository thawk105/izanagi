## 親の実測の再測結果

1. **支持 — active ratified freeze / v2 generation / approval / official floor run は 0 件。**  
   working tree と `HEAD=2bf9cf387643bf7ac087c31f5c38cfcc5539de68` の双方で、`output/s8b-freeze/holdout_freeze.v2.g*.json`、`approvals/*.json`、`active/*.json`、official `result.json` / `launch_certificate.json` は 0 件だった。path 文法は `s8b_ratified_freeze.py:67-92`、official run 作成位置は `s8b_floor_campaign.py:7794-7816`。`BUDGET_APPROVAL_SHA256` は `s8b_holdout_freeze.py:52` で `None`。

2. **支持（限定付き）— `s8c_budget.py` に floor artifact の直接参照は 0 件。**  
   `floor` literal、ratified loader、floor protocol/source loader は無い。ただし ledger identity として `freeze_sha256` と `ratified_generation_sha256` は保持する (`s8c_budget.py:153-159`)。これらを導出する実 site は `p3_autonomous_workload_trial.py:4640-4657` であり、親の訂正を支持する。

3. **支持 — 選択経路は非 strict validator を呼ぶ。**  
   `_validate_selected_floor_launch_certificate` は `validate_launch_certificate` を import し、`:1674-1681` で呼ぶ (`s8b_holdout_freeze.py:1654-1686`)。`clean_scan_digest` を照合する strict 版は `s8b_launch_cert.py:129-144`。

4. **訂正 — strict 版は「凍結側で再利用できる既存の締め代」とは一般化できない。**  
   strict 検査に独立 expected が存在するのは、発行直前の二重 scan 間だけ (`s8b_floor_campaign.py:5368-5393,7330-7336`)。D80 も certificate 自身の値を expected にする恒真を明示的に禁止する (`docs/decisions.md:3417-3421`)。凍結時には同等の独立 expected が保存されていない。

5. **訂正 — 「C06 経路全体が到達不能」は過大。**  
   freeze load は `p3_autonomous_workload_trial.py:4640`、C05 常時例外はその後の `_prepare_s8c_budget_inputs:1837`。したがって selection gate 自体は先に評価できる。ただし `reserve_all_cells:4647` 以降は到達不能である。

6. **支持（因果関係は訂正）— `s8c_result_judge` の production importer/caller は 0 件。**  
   tests/docs/output を除く全 repo で import 0、公開3関数の外部 call 0。`p3_autonomous_workload_trial.py:41-54` にも import は無い。aggregate acceptance は別経路 `trial_registry.assert_trial_registry_acceptance:5675-6267` と CLI `:6348-6354` に存在するため、「final claim は C05 の直下」という説明は誤りである。

## 所見

### 1. 残件2は「再計算不能」ではなく「独立した launch 時 expected を認証不能」

- **対象:** brief (P1-2)、plan `:93-109`
- **何が誤りか:** `clean_scan_digest()` 自体は現在の repository と allowlist に対して再実行できる (`s8b_floor_campaign.py:5272-5314`)。しかしそれは現在値であり、launch 時の値ではない。scan は run directory 作成前に行われ (`:7278-7306`)、後に certificate/result の tracked 集合が増える。Git からは launch 時の untracked 名集合を復元できず、certificate・journal・manifest は preimage を保存しない。certificate 自身の digest を expected にすれば恒真、現在 scan を使えば正当な drift を過剰拒否する。
- **放置時の成果物影響:** current-state equality を実時間証明と誤認するか、正当な official result を drift だけで拒否する。
- **親が採るべき対応:** 実装しない結論は維持し、理由を「launch 時点に独立した外部 commitment が無い」へ修正する。repo 書込主体は claimed time・Git 履歴・cert・journal・manifest を整合的に後成できる。署名主体、外部発行 nonce、一回性台帳のいずれかが無ければ実時間順は証明不能で、D1241 が今回はそれらを禁じている。

### 2. `s8c_result_judge` の選択強制は production に届かない dead-layer 実装

- **対象:** plan 残件1 Unit A、`s8c_result_judge.py` の helper 追加
- **何が誤りか:** production importer/caller が 0 なので、`verify_floor_bytes` / `publish_result_table` を強化しても現行 production artifact は変わらない。C07 は source AST の静的 readiness 検査にすぎず、動的 dispatch・実 bytes 対応は証明しない (`s8c_preregistration_evidence.py:3021-3025`)。token-only stub でも terminal `EVIDENCE_UNDEFINED` になることがテストで固定されている (`test_s8c_preregistration_predicates.py:963-1039,1347-1353`)。
- **放置時の成果物影響:** certified 選択・report・台帳の値、受理集合、参照は不変のまま、「final consumer を配線した」という誤った説明だけが残る。
- **親が採るべき対応:** production final claimant と発火 artifact が実在するまで設計メモに留める。直接 unit test の緑を production 配線の証拠にしない。

### 3. C06 selection gate は成果物でなく例外の優先順しか変えない

- **対象:** plan `:76-91`、変異3・4
- **何が誤りか:** bare loader へ戻しても C05 が `:1837` で必ず拒否するため、実装前後とも budget ledger を生成できる集合は空である。変わるのは selection error と C05 error のどちらが先かだけ。これは `DW-G05` の成果物影響を満たさず、診断文字列だけの赤を kill と数えない `DW-M03` (`docs/dev-wave/mutation.md:16-20`) にも抵触する。
- **放置時の成果物影響:** production 成果物は変わらず、死んだ gate と無効な変異証拠が増える。
- **親が採るべき対応:** C06 helper、対応2 test、変異3・4を今回の実装から外す。D586 は C01契約が明示要求した cross-check に対する個別の先行実装裁定 (`docs/decisions.md:23676-23706`) であり、別の非到達 gate 一般への許可ではない。

### 4. 残件3を止める理由は C05 単独ではない

- **対象:** brief (P1-3)、plan `:111-132`
- **何が誤りか:** C06 budget は C05 に遮断されるが、aggregate acceptance CLI は別経路である。また `registered-formal-non-certifying` は C06 を通らない (`p3_autonomous_workload_trial.py:4496-4508`)。一方、現時点では schedule、trial registry、attempt registry、lifecycle、6 report がすべて 0 件で、8c attempt genesis の production callerも 0 件。さらに judge は最終的に exact 6 cell、`n>=2`、`6×n` observationを要求する (`s8c_result_judge.py:281-303,330-431,1867-1880`)。producer/acceptance は replicate 0 に固定される (`p3_autonomous_workload_trial.py:1330-1338`; `trial_registry.py:3496-3509`)。
- **放置時の成果物影響:** C05が実装された時点で他のauthorityも揃ったと誤認し、generation 2件を統計反復へ流用するなどの意味違反を招く。
- **親が採るべき対応:** 「C05が唯一の blocker」ではなく、反復 schedule・throughput attestation・params authority・attempt producer・publication binding の連言として記録する。現在は実装しない。

### 5. `trial_registry.py:6104-6256` は「正しい配線位置」ではなく候補境界

- **対象:** plan `:113-126`
- **何が誤りか:** `publish_result_table` は repository 外の絶対 pathだけを許す (`s8c_result_judge.py:2255-2284`)。一方 acceptance receipt schema は3表の path/hashを持たない (`s8c_acceptance_receipt.py:45-67`)。したがって receipt 前に表を書くと receipt 失敗時に孤児表が残り、receipt 後に書くと表失敗時に不完全 receipt が残る。
- **放置時の成果物影響:** repo内 receipt とrepo外3表の片側だけが存在し、相互参照のない final claim が生成される。
- **親が採るべき対応:** 「aggregate後の候補 coordination boundary」と書き換え、schema・authority・failure-atomicity が裁定されるまで callsite を確定しない。

### 6. テスト登録は妥当だが、production 実効性は検査しない

- **対象:** plan `:134-165`
- **何が誤りか:** s8c tests は loader と `launch_validate` を双方 patch するため、consumer wiring は検査できても実 validator との production E2E にはならない。C06 tests は前述のとおりエラー優先順だけである。
- **放置時の成果物影響:** dead layer の直接 unit test を production hardening の証拠に数える偽緑。
- **親が採るべき対応:** 実装を延期する。将来実装時は、実在 artifactを使う production importer testを要求する。新規 oracle test file の `PYTEST_ONLY_ALLOWLIST` 登録案と、動的列挙メタテストへの依存 (`test_plain_runner_coverage.py:44-86`) は正しい。現行 repo hash を fixtureへ差し込む案は見つからなかった。

## 到達可能性の判定

- **残件1: 書けない。**  
  oracle manifest CLI は実在する (`s8b_oracle_manifest.py:1198-1260,1278`) が active ratified freeze が0件。s8c judge は production caller 0件。C06 は active freeze・schedule・registry artifactが無い。合成 fixture以外の発火 artifact path / 計測IDは書けない。

- **残件2: 書けない。**  
  official certificate/result が0件で、観測済み `clean_scan_digest` も0件。現在 scan の pathは書けても、launch 時点の独立 expected を保持した artifact path / 計測IDは書けない。

- **残件3: 書けない。**  
  `output/s8c-preregistration/schedule.v1.json`、trial/attempt registry、lifecycle、autonomous trial reports、acceptance receiptsはいずれも0件。A-1 non-certifying経路は exact 3 workload専用 (`trial_registry.py:3887-3896`) で、H1/H2×3 arm の s8c result judge経路ではない。

## 実装すべきか

- **残件1: 裁定へ返す。**  
  設計上の consumer位置は理解できるが、3群すべてについて `DW-G04` の既存 artifact pathを書けない。特に s8c judge と C06 は `DW-G05` の成果物影響が0である。

- **残件2: 裁定へ返す。**  
  D1241 の禁止範囲を守る限り、実時間性は既存材料だけでは証明不能。strict validatorへの単純置換は恒真または過剰拒否になる。

- **残件3: 設計メモに留める。**  
  aggregate boundary候補は記録できるが、production入力authorityとpublication transactionが無い。`DW-G04`・`DW-G05` とも実装を許さない。

## 変異の帰属

1. **変異1 — 殺せる（direct API限定）。**  
   selection mismatch以外をすべて正当化したfloor refs/bytesを用意すれば、bare loader化で `verify_floor_bytes` が受理へ進む。他のselection gateは無い。ただし production caller 0なのでproduction killではない。

2. **変異2 — 殺せる（direct API限定）。**  
   verify後にnamespaceだけを変え、出力条件をすべて満たせば、publish側のbare loader化により3表が作られる。別gateによるmaskは無い。

3. **変異3 — 殺せない。**  
   baselineはselection error、mutantはC05 unavailableで、どちらも `reserve_all_cells` 前に拒否する。失敗理由だけの差で、`DW-M03`上のkillにならない。

4. **変異4 — 殺せない。**  
   正常入力では `launch_validate(...).ratified` は入力 `ratified` そのもの (`LaunchValidatedFreeze.ratified`, `s8b_ratified_freeze.py:816-828`)。不正selection入力でも、call削除後はC05で拒否される。spy/call-count assertionを赤にできても受理集合のkillではない。

5. **変異5 — 殺せる（条件付き）。**  
   static load・spec・manifest構築をすべて満たすselection mismatch fixtureなら、call削除によりcandidate writeへ到達する。ただし現状はactive artifact不在かつ既存test所有競合があり、実走可能な事前登録にはまだなっていない。

いずれも静的反実仮想であり、mutation harness・pytestは実走していない。

## 既裁定との抵触

- D80 は strict digest equality を発行時の独立二重scanに限定し、certificate自身をexpectedにする恒真を禁止する (`docs/decisions.md:3412-3421`)。残件2の凍結時strict流用はこの前提を満たさない。
- D1241 / D1313 は署名・nonce・一回性台帳なしでは実時間順を閉じず、non-certifying上限を維持する (`docs/decisions.md:42158-42170`)。
- D549 は C05 runtime authority・schedule artifactを権威実体配線まで保留する (`:22399-22430`)。残件3で暫定scheduleを作るのは順序飛越し。
- D586 は既存C01契約が要求したcross-checkだけの個別先行実装。新しいC06 selection helperの一般根拠にはならない。
- D510 は exact反復、`n>=2`、attempt registry、judge追随前の正式起動禁止を順序として固定する (`:21229-21260`)。generation番号をreplicateへ転用できない。
- D618 は formal non-certifyingでもD510 attempt registryを省略できない (`:24792-24820`)。
- D1032 は再走理由を性能値到達前に同じ耐久台帳へ固定する (`:35995-36009`)。final wiringだけを先行して入力を合成できない。
- D1161 / D1334 は予算承認と数値をユーザー手番・正式実行後へ留保する (`:38805-38819`, `:42650-42664`)。
- D1193 / D1279 は予算の集約を凍結単位に保ち、置き場所は設計案提示時の裁定へ留保する (`:39805-39825`, `:41380-41393`)。final claim配線がこれを暗黙決定してはならない。
- D1284 はfloor protocol世代移行を段0権限束に残す (`:41454-41467`)。D1325もg2実在前の設計を禁止する。
- D1294 は共有批准凍結の発効を新機構で検知せず、rulings照合で拾う (`:41616-41628`)。
- D1336 はまだ「親裁定＝ユーザー裁定待ち」だが、production writer 0のgateを先行landしないという同型問題を明示している (`:42688-42727`)。

## 残る不確実性

- read-only静的検査のみ。pytest、acceptance、checker、mutation harnessは未実走で、緑とは記録しない。
- 件数は当worktreeと当HEADの再測値であり、他branch・repo外成果物の存在までは否定しない。
- 任意Pythonによる動的importは一般には完全否定できないが、repo内の明示import、call、CLI、既知dynamic import site、tools配下を検索し、該当経路は無かった。
- official artifactが0件なので、残件2の結論は実値比較ではなく保存形式・threat model・call graphによる構造的判定である。
- 将来C05・active freeze・attempt genesisが実在した場合は、reachabilityをそのartifact pathで再測する必要がある。

## 総括

残件2は既存strict validatorでは締まらず、独立した外部commitmentなしに実時間順を証明できない。  
最も重い実装所見は、Unit Aのs8c judge/C06強化がproduction成果物へ届かないdead-layer変更である。  
残件3を止める結論は正しいが、理由はC05単独でなく、反復・attestation・params・attempt producer・publication束縛の欠落である。  
変異3・4は別gateが拒否するため有効なkillにならない。  
親は段4で、残件1・2を裁定へ返し、残件3を設計メモへ降格し、今回の実装範囲を再確定すべきである。