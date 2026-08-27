### 公開 producer が検査層の下に残る

対象: 両方

根拠:

- 静的根拠: プランは `CampaignConfig`、`loop.py`、`pipeline.py` を変更しない (`s2-plan.md:1-14`) 一方、手作り marker も最下層で拒否できるとする (`s2-plan.md:44`)。
- 静的根拠: `CampaignConfig` は frozen だが、`search_config` は可変の `Dict` である (`orchestrator/campaign/model.py:66-81`)。通常の `default_cfg()` が返した dict へ marker を後付けでき、その現在値が identity に入る (`orchestrator/campaign/ident.py:150-177`)。
- 静的根拠: 公開 `loop.run_campaign()` は B-4 marker を検査せず (`orchestrator/campaign/loop.py:232-317`)、WAL を復元して (`:325-360`)、`pipeline.evaluate()` を呼ぶ (`:456-465`)。
- 静的根拠: 公開 `pipeline.evaluate()` も B-4 を検査せず (`orchestrator/campaign/pipeline.py:705-731`)、検証通過後に `certified=True` とし (`:1453`)、COMMIT を書く (`:1466-1502,1532-1563`)。
- 評価: 親 brief の「実走の入口は今 3 本の driver main」という一般化 (`materials/brief.md:21-22`) は、Python 公開 API を含めると誤りである。

到達経路:

- `orchestrator.campaign.loop.run_campaign` (`loop.py:232`) → `pipeline.evaluate` (`loop.py:456`) → COMMIT。driver 3 本には同じ関数の公開 module binding もある: base `p3_s4_loop.py:78`、sort `p3_s4_loop_sort.py:86`、trigger `p3_s4_loop_trigger_gating.py:72`。
- `orchestrator.campaign.pipeline.evaluate` (`pipeline.py:705`) へ、公開 `exploration_campaign_layout` と `ensure_campaign_identity` (`layout.py:589`, `ident.py:410`) で用意した B-4 layout を明示指定する経路。
- 既存の marked WAL は `loop.run_campaign` の replay (`loop.py:325-360`) から再開できる。loop checkpoint も公開 `load_loop_state` / `save_loop_state` (`p3_s4_loop.py:802-822`) で補える。

成立すると何が変わるか: launcher admission を一度も通らない marker 付き campaign が `STAGE_COMMIT` と `CampaignSummary.committed` に入り、certified B-4 受理集合が狭まらない。

推奨: marker 付き campaign の COMMIT 支配点で launcher capability を要求する。候補は `wal.append()` の COMMIT 分岐 (`wal.py:411-472`) で、campaign lock の marker と launcher 由来 capability を照合する形である。少なくとも `loop.run_campaign` と直接 `pipeline.evaluate` の両入口を閉じない限り、「全経路を閉じた」としない。

### P1 の置き場所は支配点になっていない

対象: 両方

根拠:

- 静的根拠: P1 は鋳造時点を支配点とする (`materials/brief.md:82-84`)。
- 静的根拠: 識別子は `search_config` にも `CampaignConfig` にも保存せず (`s2-plan.md:42,142`)、WAL schema も変更しない (`s2-plan.md:14`)。したがって process 終了後の campaign lock、WAL、レポートから識別子の通過を再検証できない。
- 静的根拠: 採用する sentinel idiom は module global の object identity だけである。現行先例も `_PAIR_SEAL` を module 属性に持ち (`p3_b4_closed_critic.py:132-133`)、同一 process の global 差替えを非保証と明記する (`:160-163`)。
- 評価: D1033 は専用起動器と識別子を要求する (`materials/D1033.md:1-9`) が、「鋳造場所だけを一つにする」とは裁定していない。鋳造を launcher に置くことは正しいが、それだけでは標本生成を支配しない。

到達経路:

- `p3_b4_launcher.require_b4_formal_identifier` または driver registry の module 属性差替え後、公開 `main` / `drive_iteration` / `run_one_iteration` から入る経路。プラン自身もこの非保証を認める (`s2-plan.md:31-33`)。
- private seal や private mint 関数を同一 process から直接参照する経路。Python の先頭 underscore は呼出制限ではない。

成立すると何が変わるか: レポートや台帳は formal identifier を通った標本と後付け marker の標本を永続 bytes から区別できず、formal 参照集合が自己申告のまま残る。

推奨: launcher だけが発行する campaign-id 束縛済み capability を、COMMIT receipt または create-only sidecar に永続化し、certified consumer とレポートでも要求する。P1 は「launcher で発行し、certified sink で消費する」へ修正する。

### 負例 1〜7 の実体拘束

対象: プラン

根拠:

| 負例 | プランが名指しする本物の実体 | launcher と factory の両 stub に対する判定 | 候補集合による恒真性 |
|---|---|---|---|
| 1 | 3 driver の実 `default_cfg` (`s2-plan.md:83-89`) | 影響されず、guard 除去で落ちる | 無し |
| 2 | 実 `run_one_iteration`、trigger の実 `_run_one_iteration_resolved` (`:91-97`) | 影響されず、guard 除去で落ちる | 無し |
| 3 | 3 driver の実 `drive_iteration` (`:99-105`) | 影響されず、exact 下層 message では合格しない | 無し |
| 4 | 3 driver の実 `main` (`:107-113`) | 影響されず、実 main を直接呼ぶ | 無し |
| 5 | 実 `create_b4_closed_critic_pair`。stub 禁止を明記 (`:115-121`) | factory を stub にした時点でこの負例の契約違反 | 無し |
| 6 | 実 test-only helper、実 factory、実 driver main (`:123-129`) | 個別負例は実体を通る | test-only helper 自体が `test-only` 候補だけを作るため、field 判定と seal identity 判定を区別しない |
| 7 | 実 `p3_b4_closed_critic.main` (`:131-137`) | launcher stub と無関係 | 無し |

評価:

- 1〜5、7 は、記載どおり実体を直接呼び exact error を照合すれば空回りしない。
- 6 の driver main は過剰決定される。main の formal check を外しても、test-only identifier は `default_cfg` を通り、下層 `drive_iteration` の同じ `require_b4_formal_identifier` が同じ generic error (`s2-plan.md:126-127`) を出せる。main 境界だけの変異が生存しうる。
- 6 は test-only 候補の性質から拒否理由がほぼ決まるため、production seal 検査を落として `evidence_class` だけを見る弱い実装も通りうる。

成立すると何が変わるか: test-only 流用テストは緑でも main 境界や production seal identity が未検査となり、検査報告が実装より強い保証を主張する。

推奨: 各境界で test-only error も別 message にするか、main テストで `default_cfg` / `drive_iteration` 未到達 spy を置く。さらに誤 seal の exact class 候補を formal verifier に渡す負例を追加する。

### launcher と本物の factory・driver の合成は未証明

対象: 両方

根拠:

- 静的根拠: brief は launcher が実 `create_b4_closed_critic_pair` と実 driver `main` を呼ぶことの固定を要求する (`materials/brief.md:42-46`)。
- 静的根拠: プランの ordering test は factory と driver を stub にする場合があると明記する (`s2-plan.md:77-78`)。
- 静的根拠: 予定された census は production factory caller だけであり (`s2-plan.md:77,183`)、3 driver の `main` binding census は明記されていない。
- 評価: stub factory と stub driver の順序テスト、実 factory の単体負例、実 driver の単体負例は、launcher が本物同士を合成していることを合わせても含意しない。

到達経路: launcher registry が local fake driver または別 callable を指す `p3_b4_launcher.main` からの経路。factory 単体負例と driver 単体負例はどちらも通りうる。

成立すると何が変わるか: テストは全て緑でも launcher が本物の driver を一度も呼ばず、formal 標本の生成経路が検査対象外の callable に差し替わる。

推奨: registry の各値が `p3_s4_loop.main`、sort `main`、trigger `main` と object identity で一致する検査を置く。factory caller census は全 production module を母集合に qualified AST call を収集し、factory 名を含む file だけを候補にしない。

### 発火順序は正しいが bootstrap の実効テストが不足する

対象: プラン

根拠:

- 静的根拠: 現行 bootstrap は iteration 0・空 whiteboard なら receipt なしで認可する (`p3_s4_loop.py:1197-1233`)。親 M4 の観測は正しい (`materials/parent-measurements.md:26-37`)。
- 静的根拠: 予定 continuation は admission 検証 → identifier → cfg → factory → pair invoke → driver の順 (`s2-plan.md:48-57`)。
- 静的根拠: 予定 bootstrap も admission 検証 → identifier →実 driver main の順 (`s2-plan.md:60`)。
- 静的根拠: 負例一覧には launcher bootstrap で実 `verify_b4_admission_record` が driver より先に発火する専用負例がない (`s2-plan.md:81-137`)。
- 評価: 記載順どおりなら canonical bootstrap では標本より前に admission が発火する。ただし公開 producer の迂回があるため、M4 を wave 全体で閉じたとはいえない。

到達経路: 予定 driver main の直接 bootstrap は main の先頭関門で閉じる。一方、`loop.run_campaign` / `pipeline.evaluate` の bootstrap 相当生成は admission 前のまま残る。

成立すると何が変わるか: canonical launcher の順序が崩れた場合、受理記録未検証の最初の `certified` COMMIT が一件増える。

推奨: 不正な admission record で実 verifier を通し、driver main spy が未到達であることを検査する bootstrap 専用負例を追加する。

### 実装量は多いが中心の producer を閉じていない

対象: プラン

根拠:

- 静的根拠: 新 module 約300行、4 production file、4 test fileへ変更する計画である (`s2-plan.md:1-12,70-79`)。
- 静的根拠: 7種の負例と main・drive・iteration の多層 guard を追加する (`s2-plan.md:81-137`) が、共通 producer `loop.run_campaign` は変更しない。
- 静的根拠: 在庫資料は17 file・22走査箇所を列挙する (`materials/inventory-tests.md:1-26`)。特に新 CLI module が相対 import と main guard を持つ場合、規定 bootstrap が相対 import より前に必要である (`test_campaign_import_invariant.py:849-947`)。
- 評価: 大半の在庫検査は特定 symbol の出現だけを見るため、launcher が subprocess、build API、WAL writerを直接使わない限り allowlist 編集は不要という見込み (`s2-plan.md:170-183`) は妥当。ただし走査確認と CLI bootstrap 追随の費用はゼロではない。

成立すると何が変わるか: 多層 guard の保守費用が増える一方、certified 受理集合は公開 producer の迂回分だけ広いまま残る。

推奨: launcher + production factory gate + COMMIT 支配点の capability 検査を中心にし、driver の重複 guard は早期エラーに必要な最小数へ減らす。新 enforcement module は projection 閉包にも含める。

### stdin 固定 JSON handshake は性質に対して過剰

対象: プラン

根拠:

- 静的根拠: receipt 後に stdin の固定 JSON で proposal path を受け取る (`s2-plan.md:55-58`)。
- 静的根拠: この wave は proposal bytes の固定も critic 決定との因果束縛も行わない (`s2-plan.md:58`; `materials/brief.md:51-53`)。
- 評価: identifier を process 外へ出さない性質は、proposal path の表現を JSON にすることからは得られない。必要なのは「receipt 後に proposal を読む」という時系列だけである。

成立すると何が変わるか: certified 選択集合は変わらず、launcher parser、schema、ordering testだけが増える。

推奨: proposal path は起動時の通常引数で固定し、receipt 出力後の stdin EOF または固定一行を ready signal としてから読む。path 自体を後から選ぶ必要があるなら、JSON object ではなく厳格な単一 UTF-8 行で十分である。

### provisional 裁定と projection

対象: 両方

根拠:

- P1: 上記のとおり不十分。
- P2: 無し。same-process 非保証を明示する限り、既存 sentinel idiom の再利用判断自体は整合する (`materials/brief.md:85-87`; `p3_b4_closed_critic.py:160-163`)。
- P3: 親案は誤り。現 `p3_b4_closed_critic.main` は自ら marked cfg を作り production factory を呼ぶ (`p3_b4_closed_critic.py:1941-1968`)。プランの hard-fail 化 (`s2-plan.md:150-154`) が正しい。
- P4: 判断は正しい。projection は file bytes の manifest (`p3_b4_closed_critic.py:610-669`) を invocation 時 (`:870-874`) と receipt 再読時 (`:1590-1591`) に検査するため、launcher bytes も含めるべきである。
- P4/M3: 「失効対象が無い」は正しい (`materials/parent-measurements.md:15-24`) が、「費用0」は既存成果物の失効費用に限る。exact manifest test と将来の admission expectation 更新費用は残る (`s2-plan.md:160-168`)。
- P5: 不十分。負例6の下層同一 errorと、launcher・driver合成の stub 空回りが mutation matrix に残る (`materials/brief.md:93-94`; `s2-plan.md:68,123-129`)。

成立すると何が変わるか: P3/P4修正により旧 receipt-only 入口は消え、将来 receipt の projection 参照は launcher bytes を含むが、P1/P5のままではformal受理集合の支配は成立しない。

推奨: P3とP4は採用する。P1は sink消費まで拡張し、P5には合成binding、bootstrap順序、test-only境界固有の変異を追加する。

### 事前登録 §7.2 は二項を丸ごと閉じられない

対象: 両方

根拠:

- 静的根拠: プランは「直接 API」と「marker 自己申告」の2項を閉じた側へ移す (`s2-plan.md:79`)。
- 静的根拠: §7.2 の marker 項目には、任意 configへの marker付与と、marker不在 campaignを報告時だけB-4と名乗る経路の両方がある (`materials/prereg-section7.md:40-43`)。
- 評価: wave が閉じるのは、3 driverの `default_cfg`、`main`、`drive_iteration`、iteration関数を通る「marked cfgだがformal identifierなし」の呼出しと、旧 receipt-only mainだけである。後付け報告はreport/ledger変更が無いため閉じない。

§7.2の各項目:

- file-drawer: 閉じない (`prereg-section7.md:21-22`)。
- proposalとcritic決定の因果束縛: 閉じない (`:33-35`)。
- `run_one_iteration`直呼び: 3 driverの列挙済み関数についてのみ閉じる。ただし同じcertified成果物を作るgeneric producerは開いたまま。
- `policy_hint`: 閉じない (`:37`)。
- legacy `Agent(...critic...)`: 閉じない (`:38-39`)。
- marker自己申告: driver経路だけ部分的に閉じる。generic producerと報告時の後付け名乗りは閉じない。
- PATH上の実行主体: 閉じない (`:44-46`)。
- pair完全性・receipt shopping: 閉じない (`:47-49`)。
- same-process属性差替え等の非保証: 閉じない (`:51-54`)。

成立すると何が変わるか: §7.2から二項を削除すると、実際より狭い残存迂回集合を報告し、formal B-4参照の事前登録上の証拠クラスを過大表示する。

推奨: `run_one_iteration`項は「列挙した3 driver境界では閉じたが、generic producerは開いている」と分割する。marker項は削除せず、「sanctioned driver内の自作だけ閉じた」「報告時 relabel と generic producerは残る」と更新する。

## 総括

プランどおりの launcher 内順序は admission を標本生成より前に置き、旧 receipt-only main の閉鎖と projection 追加も妥当である。  
しかし `loop.run_campaign` と `pipeline.evaluate` が検査層の下に残るため、「B-4実走の入口はlauncherだけ」にはならない。  
負例1〜5、7は実体を名指ししているが、launcherと実factory・実driverの合成、およびtest-onlyの各境界は空回り余地がある。  
P1は鋳造だけでなく、campaign-idに束縛したcapabilityをcertified COMMITで消費する設計へ修正すべきである。  
§7.2で正直に閉じられるのは列挙済みdriver境界だけで、marker自己申告全体や報告時relabelは閉じない。  
pytestは実行していない。本所見は指定資料とrepositoryの静的検査だけに基づく。