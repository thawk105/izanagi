### 所見 1: 12 path 化は弱化を拒否せず、弱化後の bytes に別 epoch を与えるだけ

- 深刻度: blocker
- 根拠: `orchestrator/campaign/ident.py:465-480` は fresh lock に現在の bytes をそのまま記録し、`orchestrator/campaign/artifact_admission.py:771-793` は記録 map と現在 map が一致する任意の E1 を受理する。`/work/1/SFC/tanab/dev-wave-jobs/t1143-epoch-closure/prompts/s1-brief.md:19-24` はこれを規律 2 の穴の閉鎖と読める形で記す。
- 成果物影響: `model.py:218` を常時真へ弱化してから commit し、その bytes で fresh lock を作れば、新しい E1 のまま `pipeline.py:1083` を通過する。source-binding gate 自体は anomaly 入り variant の COMMIT、certified 受理集合、レポートへの新 E1 記録を拒否しない。
- 提案: worklog は次の 1 文に限定する。  
  「本 wave は、通常の campaign source 検査で verifier 4 source の disk/blob drift が同じ `campaign_verifier_epoch` のまま残る穴だけを閉じ、弱化済み bytes で作る fresh lock、再 export、runtime/import state、推移依存、別 sink は閉じない。」

### 所見 2: D268 の名乗りは「適用された正しさ規則」へ拡張できない

- 深刻度: blocker
- 根拠: `docs/decisions.md:12369-12388` は disk/blob 一致だけを許し、certified 経路、実行時 state、推移閉包を明示的に除外する。一方、brief は `/work/1/SFC/tanab/dev-wave-jobs/t1143-epoch-closure/prompts/s1-brief.md:23-24` で epoch が「適用された正しさ規則」を指すと書く。
- 成果物影響: 受理集合自体は文言だけでは変わらないが、`identity_scope`、`excluded_scope` と layer3/S1/S8b レポートが、実際にロード・実行された規則を証明する値だと誤表示される。
- 提案: D268 の文は次にだけ書き換える。  
  「`require_environment_contract=True` で `ident.ensure_campaign_identity` の source 検査が実際に完了した呼出しについて、各 path を検査が読み取ったそれぞれの時点の enforcement source closure exact 12 path の disk bytes は、その呼出しが authority に採用した `contract_loader_commit` の同 path Git blob と一致した。」  
  D268 の制限箇条書きは削らず継承する。

### 所見 3: プランの既定 exact 13 は確定裁定を越え、exact 12 用の除外文言とも不整合

- 深刻度: blocker
- 根拠: 確定裁定は `docs/archive/worklog-phase3-0816-574.md:565-569` と brief `:5-15` の verifier 4 file、すなわち exact 12 である。プランは `/work/1/SFC/tanab/dev-wave-jobs/t1143-epoch-closure/out/s2-plan.md:3-29,124` で `__init__.py` を加えた exact 13 を実装案にしている。
- 成果物影響: `campaign_lock.py:167-180` の exact wire key 集合と epoch preimage が 12 と 13 で異なり、将来 lock の受理言語と E1 値が変わる。既存 v2 lock は 0 件だが、裁定外変更である点は消えない。
- 提案: 現裁定どおり exact 12 にし、P3 は未束縛 source を `__init__.py, __main__.py, cli.py, report.py` の exact 4 file と記す。追加は scope 外の裁定パッケージ候補とする。P4 の歴史名維持は `docs/decisions.md:12360-12362` と整合し、correctness blocker ではない。

### 所見 4: exact 12 では再 export shim による同一 epoch の bypass が残る

- 深刻度: blocker
- 根拠: `orchestrator/campaign/pipeline.py:30` は package export を固定し、実体は `orchestrator/verifier/__init__.py:16-20` である。プラン自身も `s2-plan.md:43-45` でこの穴を認める。
- 成果物影響: `__init__.py:16` を偽 verifier へ向けても 12-path map と E1 は変わらず、`pipeline.py:1083` が anomaly を通し、WAL の COMMIT、certified 集合、後続レポートが偽緑になる。
- 提案: exact 12 を land するなら「shim 経路は開いたまま」を完了記録へ必須化する。`__init__.py` 追加は scope 外の裁定パッケージ候補とし、黙って exact 13 にしない。

### 所見 5: `report.py` は payload だけでなく import-time に gate 判定を変えられる

- 深刻度: blocker
- 根拠: `orchestrator/verifier/__init__.py:20` は `report.py` を無条件 import し、同 file は `orchestrator/verifier/report.py:12,42-76` で `VerifyResult` を保持する。例えば import 時に `VerifyResult.certified` を差し替えれば `orchestrator/campaign/pipeline.py:1083` より前に判定が変わる。プラン `s2-plan.md:47-52` は通常フローの `result_to_dict` だけを見て受理可否に無関係としている。
- 成果物影響: exact 13 でも report source は epoch 外なので、同じ E1 で anomaly が COMMIT されうる。通常の `result_to_dict` 本体だけの変異でも、`pipeline.py:1090-1093` の anomaly・依存辺を含む rejection payload と次手生成信号が失われる。
- 提案: selected-source drift モデルなら `report.py` までの exact 14 が最小。ただし任意の import-time 攻撃まで「閉じた」とは名乗れず、同一 process の自己検査を越える対策は scope 外の裁定パッケージ候補とする。

### 所見 6: CLI は別 gate のまま開き、プランの exact 16 でも wrapper が漏れる

- 深刻度: major
- 根拠: `orchestrator/verifier/cli.py:23-25,58-104` と `orchestrator/verifier/__main__.py:5-8` は campaign と別の exit-code gate である。さらに正式 wrapper `orchestrator/verify.py:14-19` も closure 外だが、プラン `s2-plan.md:50-52,119` の「CLI 全体」はこれを列挙していない。
- 成果物影響: CLI の rc・JSON は anomaly を成功扱いに変更できる。repo 内 campaign の certified 集合へ直結する consumer は確認できず、その影響は書けない。
- 提案: 本 wave では「CLI は対象外」と明記する。CLI 全体を名乗る案は wrapper を含む別の scope 外裁定パッケージ候補とする。

### 所見 7: `__pycache__`、monkeypatch、`sys.modules`、`PYTHONPATH` はすべて開いたまま

- 深刻度: major
- 根拠: `docs/decisions.md:12385-12388` が `__pycache__`、in-process 改変、既ロード state を未検出と明記する。`pipeline.py:30` の module global は monkeypatch 可能であり、disk 検査は `contract_loader_binding.py:150-229` の `.py` bytes しか読まない。
- 成果物影響: forged bytecode、`pipeline.verify_trace_dir` の差し替え、偽 module の事前登録、`sitecustomize` や別 import root により、12 path の disk bytesと E1を保ったまま偽緑の WAL・COMMIT・レポートを作りうる。
- 提案: 4 経路はいずれも「本 wave 後も開く」と D268 supersede に残す。隔離 interpreter、loader/module provenance、実行 code attestation は scope 外の裁定パッケージ候補とする。

### 所見 8: 未束縛 bootstrap を変えれば閉包検査そのものを無効化できる

- 深刻度: major
- 根拠: `docs/decisions.md:12386-12388` は `campaign_lock.py`、`contract_loader_binding.py`、Git executable を root of trust とする。実装も `contract_loader_binding.py:243-275` で ambient `PATH` から Git を解決する。
- 成果物影響: `capture_contract_loader_binding` を記録 map の返却だけにする、検証関数を no-op にする、または偽 Git を解決させれば、verifier source drift が同じ E1 で certified admission を通る。
- 提案: accidental drift モデルの root of trust と明記し続ける。敵対モデルで閉じるなら外部 launcher から検査器 bytes と Git executable を固定する別設計が必要で、scope 外である。

### 所見 9: pipeline の推移依存は列挙された全 module が未束縛のまま

- 深刻度: major
- 根拠: `pipeline.py:26-45` は calibrator、buildcache、build_admission、source_digest へ委譲し、`execution_guard.py:22-27,137-159` は env_attestation と site_policy へ委譲する。D268 も `docs/decisions.md:12376-12378` で全て閉包外と明記する。
- 成果物影響: buildcache は検証用 trace binary と fitness 用 binary の対応を変え、source_digest/build_admission は variant・source・receipt 参照を変え、calibrator は fitness と winner 順位を変え、env_attestation/site_policy は環境受理集合を変えられる。いずれも epoch は不変である。
- 提案: brief `:23-24` の「適用された正しさ規則」を削除する。各 module の閉包化は scope 外の裁定パッケージ候補として分離し、本 wave を推移的 source closure と記録しない。

### 所見 10: 4 path 追加が効く層と、効かない層の区別がプランにない

- 深刻度: blocker
- 根拠: source 発行・resume は `ident.py:449-477`、中央 admission は `artifact_admission.py:771-793,1068-1093`、S1 は `s1_report.py:385-407`、certifying Layer3 は `layer3_report.py:594-610`、S6/S8a は `s6_sort_sweep.py:471-477` と `s8a_trigger_sweep.py:573-579` で gate を読む。一方、通常 Layer3 は `layer3_report.py:424-427`、P2-2 の winner は `p2_2_report.py:126-157` で `HISTORICAL_RAW` を使う。selector payload は `s8b_selector_input.py:102-130` に epoch field を持たない。S8b oracle writer は `s8b_oracle_driver.py:1106-1139,1523-1565` で独自 lock と `pipeline.evaluate` を直接使う。
- 成果物影響: 4 file drift は中央 admission、S1、certifying Layer3、S6/S8a では拒否になる。通常 Layer3/P2-2 は記録 epoch を表示し続け、P2-2 は historical 値から winner を選ぶ。selector は一切変わらない。S8b direct writer の書込 gateにも変化はない。
- 提案: plan v2 に層別表を追加する。通常 Layer3/P2-2 は「表示のみ」、selector は「非 consumer」、S8b direct writer は「scope 外の裁定パッケージ候補」と明記する。

### 所見 11: oracle judge は epoch の意味を認証せず、P2 の namespace 曖昧性が実害化する

- 深刻度: blocker
- 根拠: `s8b_oracle_artifacts.py:141-183` は E1 prefix と非空 scope しか検査せず、`s8b_oracle_artifacts.py:255-259` は任意の official-schema JSON を型で包む。実際、`test_s8b_oracle_judge.py:35-45,123-129` は任意の epoch と fixture scope から `unique-best` を得る。プランは `s2-plan.md:56-69` で `/v1` 据え置きと scope 診断で足りるとする。
- 成果物影響: 旧 8-path E1 または捏造 E1 を `certified_eligible=true` とした observations が、現在の 12-path lockを再検査せず `OfficialVerdict` の determinate winner を作れる。
- 提案: 中央 lock gateでは path が preimage に入るため、生の SHA 衝突問題ではないと明記する。ただし oracle には versioned closure schema、campaign lock への検証可能な参照、または current producer との再照合が必要である。domain 文字列だけの変更では直らず、scope 外の裁定パッケージ候補とする。

### 所見 12: 変異計画は「identity が変わる」を直接証明せず、fixture も production tuple に従属する

- 深刻度: major
- 根拠: プランの変異は `s2-plan.md:83-111` の事後 drift と path removal に限られる。使用予定の `_committed_closure_repo` と期待 epoch は `test_artifact_admission.py:312-346` で production の `CONTRACT_LOADER_RELATIVE_PATHS` から生成される。
- 成果物影響: path-removal mutant が fixture 構築失敗や別の exact-set assert で落ちても、中央 certified gate の検出力を証明したことにならない。また、弱化後に fresh lock を作る mutant は新 E1 として生存するため、「規律 2 の穴を閉じた」という主張だけが偽緑になる。
- 提案: 事前登録を分ける。各 4 file について、事後 drift は中央 admission node が落ちる、production tuple の path 除去は独立 exact-12 node が落ちる、commit 済み変更から作る fresh lock は受理されつつ旧 epoch と異なる、`__init__.py` bypass は exact 12 で生存、report import-side-effect は exact 13 で生存、と期待結果を固定する。S1・certifying Layer3・oracle report の gate-call 除去変異も各 consumer node で落とす。

### 所見 13: 親の「pin 0 件」は検索方法からは確定していない

- 深刻度: minor
- 根拠: brief `:32-34` は文字列 `campaign_lock.py` の path 検索だけで pin 0 と一般化するが、`docs/dev-wave/operations.md:54-64` は role/key、directory closure、review ledger を別に検索し、path hit 0 を pin なしと結論しないよう要求する。32 lock・v2 0 件という件数自体は静的に再確認できた。
- 成果物影響: 書けない。未列挙 pin がある場合は frozen manifest、独立 golden、受入参照のどれが変わるか未確定である。
- 提案: `campaign_lock.py` という path 以外に、authority key、closure role、generator/runtime-module 集合を検索し、live copy・independent golden・frozen snapshot・歴史記録へ分類してから「pin 0」を確定する。

## 総括

**NO-GO（現行 brief／plan のまま）。**  
exact 12 の実装自体は有益だが、閉じるのは選択した 4 source の同一 epoch 事後 driftだけである。  
exact 13 への無裁定拡張、「適用された正しさ規則」「規律 2 の穴を塞いだ」という記録は不可。  
段 4 で名乗りを狭め、shim・runtime・推移依存・oracle consumerを裁定パッケージへ戻す必要がある。  
pytest は実走せず、結論は指定どおり静的検査による。