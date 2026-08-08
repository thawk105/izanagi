指定された全ファイルと、未追跡を含む作業差分を読めました。判定は **NO-GO**、must-fix は 7 件です。以下は静的検査結果であり、pytest は実行していません。親の「555 passed / 0 failed」は実測値として受領していますが、後述のとおり land 後検査を代替しません。

## 1. T419 の dirty scope が実 import 閉包を覆っていない

深刻度: **must-fix**

根拠:

- T419 は `campaign.env_contract` を import して `lookup("pegasus")` を実行する: `tools/pegasus/probes/t419_probe_causality.py:3388-3396`
- dirty 対象は activation 関連を足した 8 パスだけ: `tools/pegasus/probes/t419_probe_causality.py:3491-3500`
- 実際の閉包には、少なくとも次が追加で入る。
  - `orchestrator/campaign/__init__.py`
  - `orchestrator/calibrator/__init__.py`
  - `orchestrator/calibrator/effective_clock_policy.py`
  - `orchestrator/calibrator/schema_v2.py`
  - `orchestrator/calibrator/tsc.py`
- `calibration_verify` の直接 import: `orchestrator/campaign/calibration_verify.py:13-14`
- `env_attestation` の直接 import: `orchestrator/campaign/env_attestation.py:22-26`
- 新設テストは activation leaf と directory だけを確認している: `orchestrator/tests/test_t419_probe_causality.py:1567-1595`

これらを dirty 改変しても `not dirty` が真のままなので、`matched=True` になり得る。`__init__.py` は現在空でも、dirty tree では任意の import 副作用を追加できるため除外できない。

**成果物影響:** 実行意味論が dirty な T419 run が `submission_binding.matched=true` として manifest/result に記録・受理される。

修正案: `related` に上記 5 パスを加え、各パスを一つずつ dirty にした閉集合テストを追加する。可能なら identity 閉包と同じ正本から導出し、手書き集合の再乖離を防ぐ。

## 2. issuer が live filename へ直接書き、失敗時に部分ファイルを残す

深刻度: **must-fix**

根拠:

- `O_CREAT|O_EXCL|O_NOFOLLOW`、短い write への loop、file fsync、directory fsync 自体は実装されている: `tools/issue_env_contract_activation.py:42-70`
- しかし例外時は descriptor を閉じるだけで、作成済み filename を除去しない。同時に、書込み中の不完全 bytes が live activation directory に露出する。
- loader は directory の全 entry を直ちに読み、canonical record として検証する: `orchestrator/campaign/env_contract_activation.py:356-398`
- テストは正常作成と二回目の `EEXIST` だけで、途中 write/file fsync/directory fsync 失敗を扱わない: `orchestrator/tests/test_env_contract_activation.py:515-533`

file fsync 前の失敗なら不完全 record が残り、directory fsync 失敗なら tool は失敗を返しても完全 record が既に見えている。いずれも再試行は `O_EXCL` で阻まれる。

**成果物影響:** fresh loader が authority 全体を拒否して certified 選択・レポート発行を停止するか、tool の失敗表示と実際の chain 進行が食い違う。

修正案: activation directory の外、かつ同一 filesystem の staging file を完全書込み・fsyncしてから、no-replace の atomic publishを行う。例えば hard-link create-only または `renameat2(RENAME_NOREPLACE)` を使い、directory fsync と失敗時の残骸回収・再試行判定もテストする。live directory 内の一時名は loader が余分な entry として拒否するため使えない。

## 3. 発行後の head 更新・配備・再起動手順が存在しない

深刻度: **must-fix**

根拠:

- loader は source 内の head 定数を要求する: `orchestrator/campaign/env_contract.py:370-376,458-468`
- validator は terminal serial/hash の exact 一致を要求する: `orchestrator/campaign/env_contract_activation.py:313-321`
- issuer は次 record を live directory に書くだけで head 定数を更新しない: `tools/issue_env_contract_activation.py:113-132`
- 実装報告も create-only 発行までしか記述していない: `s5-a.md:19-22`
- issuer テストにも「発行後は fresh loader が失敗する」「どう回復・配備するか」の検査がない: `orchestrator/tests/test_env_contract_activation.py:515-533`
- authority snapshot は process 内で保持される: `orchestrator/campaign/env_contract.py:501-511`

したがって発行直後は、fresh process は suffix/head 不一致で fail-closed する一方、既存 process は cached old head を使い続ける。

**成果物影響:** 同一配備中に既存 process は旧 certified 選択を継続し、fresh process は全拒否するため、レポート・台帳の発行可否と選択 contract が process ごとに分裂する。

修正案: 少なくとも次を正本化し、統合テストで固定する。

1. quiesce/drain
2. record 生成
3. head 定数と record を同一 commit に収容
4. atomic deployment
5. 全 process 再起動
6. fresh-process lookup と head/hash 確認
7. 中断・fsync 不明時の回復手順

tool も「発行成功＝直ちに有効化成功」ではないことと、更新すべき定数値を明示すべき。

## 4. head pin テストが leaf だけを検査し、production loader の配線誤りを落とさない

深刻度: **must-fix**

根拠:

- rollback/suffix テストは `validate_activation_records()` に期待値をテスト自身で直接渡すだけ: `orchestrator/tests/test_env_contract_activation.py:253-286`
- serial 2 の統合テストは head 定数を record に合わせて monkeypatch した正例だけ: `orchestrator/tests/test_env_contract_activation.py:343-350`
- production seam は head 定数を loader へ渡す箇所: `orchestrator/campaign/env_contract.py:458-468`
- 裁定は tail rollback と valid suffix の独立検査を要求する: `s4-adjudication.md:80-90,123-127`

反例: `env_contract._load_authority_snapshot()` が source 定数ではなく「観測した末尾 record の serial/hash」を expected head として leaf validator に渡す誤実装。leaf の負例はそのまま通り、serial 2 正例も通るが、実運用では rollback/suffix が受理される。

**成果物影響:** source identity に固定されていない activation head が current certified 選択になり、レポート・台帳が未レビューの state hash を参照する。

修正案: source head 定数を変更せず、production の `lookup()` または `current_activation_state()` に対して末尾削除・valid suffix を与える負例を追加する。loader が module 定数を leaf へ渡したことを spy で固定するテストも必要。

## 5. receipt テストが g1 しか通さず、active generation の解決誤りを見逃す

深刻度: **must-fix**

根拠:

- receipt テストの対象は常に `linux-baremetal` g1: `orchestrator/tests/test_execution_guard.py:32-57`
- forged/stale テストも同じ g1: `orchestrator/tests/test_execution_guard.py:60-95`
- campaign の module-level fixture も g1: `orchestrator/tests/test_campaign.py:79`
- g2 テストは `lookup()` までで guard/receipt を通らない: `orchestrator/tests/test_env_contract_activation.py:343-350`
- production は receipt row の generation/hash から解決する: `orchestrator/campaign/execution_guard.py:155-177`

反例: receipt の PID/seal/state/hash は正しく検証するが、最後に常に `GENERATIONS[row.env_tag][0]` を返す誤実装。現在の receipt/campaign テストはすべて g1 のため通過し、Pegasus g2 有効化後だけ誤る。

**成果物影響:** g2 activation 後も certified sink が g1 contract を受理・記録し、report の contract hash、clock、calibration 参照が authority と不一致になる。

修正案: serial 2 authority を production seam に設定し、Pegasus g2 を receipt→guard→certified sink まで通す正例を追加する。同じ state で g1 authorization が拒否されることと、`lookup()` が呼ばれないことも同時に固定する。

## 6. ever-active テストが downgrade 後の歴史保持を検査していない

深刻度: **must-fix**

根拠:

- no-op→skip→downgrade のテストは terminal generation だけを確認し、ever-active 集合を確認しない: `orchestrator/tests/test_env_contract_activation.py:303-340`
- serial 2 テストは terminal g2 の状態で g1 が保持されることだけを確認する: `orchestrator/tests/test_env_contract_activation.py:353-366`
- 初期状態の never-active g2 拒否: `orchestrator/tests/test_env_contract_activation.py:369-375`
- resolver はこの集合を歴史受理の根拠にする: `orchestrator/campaign/env_contract.py:577-590`
- downgrade 受理は確定裁定: `s4-adjudication.md:70-76`

反例: ever-active を「terminal row の hash ∪ 全 g1 hash」と計算する誤実装。初期、serial 2、generic chain の現 assert をすべて通るが、g1→g2→g1 後に g2 を失う。

**成果物影響:** g2 期に作られた歴史レポート・ledger 参照が、許可済み downgrade 後に検証不能になる。

修正案: generic chain の exact ever-active union を assertし、実 catalog でも g1→g2→g1 の後に g2 hashを `resolve_by_contract_sha256()` できることを検査する。downgrade 拒否を追加する提案ではない。

## 7. fork テストが「別 thread 保持」を再現せず、receipt lock も無検査

深刻度: **must-fix**

根拠:

- authority テストは fork を呼ぶ同じ thread が lock を保持している: `orchestrator/tests/test_env_contract_activation.py:436-470`
- receipt の fork テストは lock を保持せず、親の `os.read()` に timeout もない: `orchestrator/tests/test_execution_guard.py:98-125`
- 裁定が要求したのは「別 thread が lock を保持したまま fork」: `s4-adjudication.md:123-127`
- mutation M9 は callback 除去を held-lock test で落とす契約: `s4-adjudication.md:160`
- authority/receipt の callback: `orchestrator/campaign/env_contract.py:489-498`、`orchestrator/campaign/execution_guard.py:63-73`

現行実装自体は、`execution_guard` が先に `env_contract` を importするため、child callback は authority→receipt の順で登録・実行される。両 callback は lock を取得せず相互再入もなく、PID 検査も lock 前なので、静的には deadlock 経路を認めなかった。

ただし現在のテストは裁定された競合形を作らず、callback を削除しても lock 前 PID reset が救済するため M9 を落とせない。receipt lock の継承破壊は完全に無検査。

**成果物影響:** 将来の lock/PID 順序誤実装を gate が通し、fork child が certified 選択前に永久停止して report・ledger を発行しなくなる。

修正案: worker thread が authority lock／receipt lockを保持し、main thread が forkするテストをそれぞれ作る。Event で保持を確定し、child は bounded pipe/select、timeout 時 kill/waitする。callback 除去を区別するには、production callback より後に child PID だけを現 PIDへ揃える test callbackを登録し、lock 再初期化そのものを load-bearing にする。

## 8. import-I/O／cache／root の回帰 gate が閉じていない

深刻度: **should-fix**

根拠:

- production の module 直下に `REGISTRY`/`lookup` の実アクセスはなかった。`REGISTRY` 定義も lazy view の生成だけ: `orchestrator/campaign/env_contract.py:537-550`
- test の module 直下には二件ある:
  - `orchestrator/tests/test_campaign.py:79`
  - `orchestrator/tests/test_screening_driver.py:37`
- fresh subprocess test が禁止する I/O は `os.scandir`、`os.lstat`、`Path.read_bytes` だけ: `orchestrator/tests/test_env_contract_activation.py:395-419`
- `Path.is_file/stat/open/read_text` や `os.open` を import 時に追加する誤実装はこのテストを通る。
- root test は任意 cwd だけ: `orchestrator/tests/test_env_contract_activation.py:473-489`
- resolver は worktree/source-stage を sentinel で判定する: `orchestrator/campaign/env_contract.py:404-422`
- T126 source-stage は full `git archive`: `tools/pegasus/t126_qualification.sh:492-496`

`_use_authority` は patch 復元後に cache clear するため、一時 authority snapshot の teardown 漏れは認めなかった: `orchestrator/tests/test_env_contract_activation.py:129-146`。ただし collection-time lookup は全 fixture より前に cache と filesystem state を固定する。

**成果物影響:** import-I/O 回帰や source-stage sentinel 回帰が偽緑になり、worker が certified 選択前に失敗するか、テスト順により古い authority を受理する。

修正案: module-level lookup を fixture/local setupへ移す。audit hook 等で activation/calibration path への全 open/stat 系 I/O を監視し、実 worktreeと `git archive` source-stageの双方を別 subprocessで検査する。

## 9. committed silo evidence は現行 runtime binding と一致しない

深刻度: **should-fix**

根拠:

- runtime binding は activation leaf と全 JSON を含む: `orchestrator/campaign/silo_ladder_rung1.py:254-277`
- current compatibility verifier は exact listを要求する: `orchestrator/campaign/silo_ladder_rung1.py:3531-3539`
- committed evidence のテストは、歴史 binding が現行と不一致であることを意図的に assertしている: `orchestrator/tests/test_silo_ladder_rung1_evidence.py:1249-1250`
- 静的比較では現行だけに `effective_clock_policy.py`、`calibration_verify.py`、`env_contract_activation.py`、`00000001.json`、`execution_guard.py` があり、共通パスでも `schema_v2.py`、`env_attestation.py`、`env_contract.py`、`run_probe.py` の hash が異なる。
- committed T419 manifest は旧 5 パスを保持する: `output/env/pegasus/t419-probe-causality/0_889400.nqsv/manifest.json:120-126,280-286`

silo evidence はこの wave 前から current-compatible ではなく、歴史成果物そのものを新集合で再検証する設計ではない。T419 の committed manifestにも current集合との offline exact 比較はなく、過去成果物が新たに赤になる経路は見つからなかった。

**成果物影響:** committed silo evidence を現行 compatibility verifierへ入力すると拒否されるが、歴史 evidence の保存値自体は変わらない。

修正案: s5/land handoff に「既存 silo evidence は current-compatible ではない」と明記する。歴史成果物を新集合へ書き換えたり、validator を緩めたりしない。

## 10. 未追跡 leaf のため、555件は post-land identity 検査の証拠ではない

深刻度: **should-fix**

根拠:

- 現在 `env_contract_activation.py` と初期 JSON は untracked。
- identity test は全 required pathに `git ls-files --error-unmatch` を要求する: `orchestrator/tests/test_t126_pegasus_tools.py:1468-1489`
- 実装報告も commit 前は赤、commit 後に再検査が必要と明記する: `s5-b.md:47-61`

したがって親の 555 passed は、その実測自体を疑うものではないが、現在の indexを前提とする post-commit tracked-path gate の証明にはならない。

**成果物影響:** leaf/recordを commitし忘れると、T126 source identityが生成不能になり、source-stageでは activation authorityそのものが欠落する。

修正案: leaf、初期 record、issuer、テストを同一 land commitへ確実に含め、commit 後に tracked-path testと provenance監査を再実行する。

## Identity pin と JSON 除外の静的照合

追加された activation/receipt import 閉包を、相対 import、lazy import、package initializerまで辿った結果は次のとおり。

- 不足: **0**
- 過剰: **0**

対象は `campaign/{__init__,calibration_verify,env_contract,env_contract_activation,env_attestation,execution_guard,site_policy}` と `calibrator/{__init__,effective_clock_policy,schema_v2,tsc}` で、`REQUIRED_CODE_IDENTITY_PATHS` と一致する: `orchestrator/qualification/contract.py:38-76`。対応テストの列挙も一致する: `orchestrator/tests/test_t126_pegasus_tools.py:1428-1447`。

preimage validator は key setを exact 比較する: `orchestrator/qualification/contract.py:528-536`。歴史 verifier も現在の定数を要求し、recorded commitの各 blobを再 hashする: `orchestrator/qualification/identity.py:130-144`。このため旧 key setの preimageは一度拒否集合へ移るが、repo内に影響を受ける committed T126 series evidenceは見つからなかった。

activation JSON を identity path集合へ加えない判断は整合している。head hashが predecessor chainを通じて全 record bytesを束縛し、head定数を持つ `env_contract.py` 自体が identity pin対象であり、T126 source-stageも commit全体の `git archive` だからである。将来 recordを追加しても path集合を変えず、head定数と commit/treeで歴史を再現できる。

## 受理集合の変化

新たに受理するもの:

- Pegasus g2を含む構造的に正しい複数世代 catalog。
- source headとexact一致する activation chain。
- exact env集合・登録済み generation/hashの no-op、skip、downgrade。これは裁定どおりで、拒否追加を提案しない。
- activation済み generationの current lookupと、ever-active generationの歴史解決。
- 同一 process/PID/seal/stateへ束縛された receiptを通る certified sink。
- 新しい exact T126 identity set、新しい silo runtime binding、新規 runでのactivation関連T419 dirty scope。

新たに拒否するもの:

- symlink、非regular、余分なentry、schema/hash/連番/predecessor/env集合/catalog不一致のauthority。
- source headに対するtail rollback、valid suffix、同serial hash不一致。
- 登録済みだがnever-activeのhash。
- stale、forged、cross-PID、cross-seal、fork継承receipt。
- 旧T126 identity key set、旧silo bindingをcurrent bindingとして扱う入力。
- activation leaf/record directoryがdirtyな新規T419 run。
- sentinelを欠くinstalled copy。これは裁定で明示的に対象外: `s4-adjudication.md:95-105`

裁定を超えた変化は、意図せず残っている次の二点である。

- T419で、閉包外5パスのdirty変更をなお受理する。
- issuer発行後からhead更新・再起動まで、fresh processだけを拒否しcached processを受理し続ける。

これらの修正にユーザー再裁定は不要で、現裁定の閉包を満たすための修正である。

## 総括

1. **NO-GO**
2. **must-fix: 7件**
   - T419 dirty scopeに実 import閉包5パスが不足。
   - issuerが部分／曖昧なlive recordを残す。
   - 発行からhead更新・配備・再起動までの運用契約がない。
   - head pinのproduction配線誤りをテストが検出しない。
   - receiptのg2解決誤りをテストが検出しない。
   - downgrade後のever-active保持誤りをテストが検出しない。
   - 別thread-held-lock forkとreceipt lockをテストしていない。