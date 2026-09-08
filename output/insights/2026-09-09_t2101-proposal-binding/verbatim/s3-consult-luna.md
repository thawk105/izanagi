## 実行前性の実測

- **L1 — real、読解。3 driver とも proposal 照合前に外部 process を spawn する。** 段 2 プランの「その後の境界はすべて比較より後」(`stage2-plan.md:90`) は、build・campaign lock・WAL に限れば正しいが、外部 process まで含めると誤りである。

  | driver | `main` から予定照合位置までの先行処理 |
  |---|---|
  | base | `p3_s4_loop.py:2322` parse → `:2427-2429` `_assert_single_tenant` → `p2_2.py:300-305` → `calibrator/runner.py:403-405` で `pgrep` spawn → `p3_s4_loop.py:2430` `assert_pinned_clean` → `patchharness.py:174-196` → `:73-90` で `git rev-parse` / `git status` spawn → proposal load `p3_s4_loop.py:2473-2481` |
  | sort | `p3_s4_loop_sort.py:671` parse → `:706-707` `pgrep` → `:708` Git pin 検査 → proposal load `:738-742` |
  | trigger | `p3_s4_loop_trigger_gating.py:1221` parse → `:1257-1259` `pgrep` → `:1260` Git pin 検査 → proposal load `:1289-1293` |

  B-4 は `--no-build` を拒否するため、`_assert_single_tenant` は formal B-4 では必ず通る。照合は各 loader の parse/schema 後へ置く計画なので、この spawn より後になる。

  再現手順: schema-valid だが registry hash と不一致の proposal を用意し、`subprocess.run` と binding helper を spy 化して各 `main` を実行する。binding reject より先に `pgrep` と Git の呼出しが記録される。今回は実走していない。

- **L2 — real、読解。launcher は campaign directory と sidecar を照合前に作る。** bootstrap は `p3_b4_launcher.py:540-547` の `prepare_launch` と `write_sidecar` を終えてから `:549-556` で driver を呼ぶ。`write_sidecar` は `:415-425` で `layout.ensure()`、temporary receipt、`os.replace` を実行する。さらに admission 検証は `p3_b4_admission_record.py:726-735` から `:308-327` の固定 Git process を複数 spawn する。

  再現手順: 有効 admission と不一致 proposal/publication を与え、driver は実関数のまま sidecar path を観測する。proposal gate が拒否しても `b4_launch_context.json` と campaign directory は既に存在する。今回は実走していない。

- **L3 — real、読解。continuation の拒否は critic pair の実行、receipt 発行、外部 process spawn より後である。** `launch_continuation_impl` は `p3_b4_launcher.py:569-581` で pair を作り、`:582-589` で両 arm を invoke してから proposal 準備を待つ。pair 作成は `p3_b4_closed_critic.py:1194-1200,1296-1348` で artifact directory と controller directory を作る。invoke は `:891-907` で start/terminal receipt を予約・発行し、`:947-971` で証拠 artifact を書いて provider process を起動する。実 runner は `:1328,1342` の `subprocess.run` である。

  既存の正例はこの順序を明示している。`test_p3_b4_closed_critic.py:2705-2722` の `ReadySignal.readline()` は、terminal receipt path が出力された後に初めて proposal file を作る。driver と予定照合へ進むのは `p3_b4_launcher.py:600-609` である。

  したがって、要求された広い意味ではこれは「実行前」ではない。campaign build 前ではあるが、二つの critic process と多数の durable artifact の後である。

  再現手順: `test_launcher_positive_uses_real_factory_and_real_base_main_for_commit` と同じ ReadySignal を使い、生成 proposal の core を registry と不一致にする。最終的に proposal gate が拒否しても、runner 呼出し 2 回と critic artifact が残る。今回は実走していない。

- **L4 — refuted、読解。campaign lock、campaign WAL、build、計測開始、実 worktree 操作は driver 内の予定照合より前には見つからない。** lock/WAL は base `p3_s4_loop.py:2209-2212,1628-1634`、sort `p3_s4_loop_sort.py:573-576,399-403`、trigger `p3_s4_loop_trigger_gating.py:1092-1095,776-779` 以後である。実 build/bench は各 `run_campaign`、base `:1699-1708`、sort `:413-418`、trigger `:811-820` 以後である。sort/trigger の `patchharness.checkout` は context manager の作成だけが loader 前で、`git worktree add` を行う enter は proposal load 後の `with wt_cm` である。

  修正位置は二段必要である。

  - driver 内では、B-4 引数の構文・mode 整合を検査した直後、`_assert_single_tenant`、`assert_pinned_clean`、knowledge receipt 作成より前に proposal を一度だけ読み、registry 照合まで完了させる。
  - launcher bootstrap は `prepare_launch` より前に同じ単一 buffer の照合を行う必要がある。
  - continuation は現在の一回呼出し構造では満たせない。proposal が critic receipt 後に生成されるため、critic pair 発行段と finalized proposal を消費する実行段を分離し、後段では proposal の単一読取りと registry 照合を最初に行ってから admission、sidecar、driver へ進む必要がある。照合を単に `p3_b4_launcher.py:596` 付近へ移すだけでは、先行した二つの critic process を取り消せない。

## 単一読取りと ABA

- **L5 — real、読解。launcher へ前倒しするだけでは二重 open の ABA が生じる。** 段 2 の loader 内単一読取り案自体はよいが、L2/L3 を直すため launcher が `Path.read_bytes()` し、driver が既存 loader `p3_s4_loop.py:2025`、sort `:457`、trigger `:936` で再度開けば二重読取りになる。

  攻撃列:

  1. path `P` を proposal A にし、registry に `H(A)` を登録する。
  2. launcher の一回目の open が A を読み、照合を通す。
  3. close 後に `os.replace(B, P)` で schema-valid な Bへ差し替える。
  4. driver loader の二回目の open が Bを parseする。
  5. gate は Aを承認したのに Bを実行する。

  launcher 前倒しを採るなら、launcher が所有する immutable bytes またはそこから作った document/typed proposal を同一 process 内で driver へ渡し、driver は path を再度開いてはならない。

- **L6 — refuted、読解。parse object の再 dump は二度読みではなく、D1343 に必要な canonical content hash である。** `attempt_registry_core.canonical_json_bytes` は `attempt_registry_core.py:197-206` の固定 serializer である。D1343 は raw file SHA ではなく canonical hash、D302 は内容の再導出を要求している。したがって採るべき意味論は「一度読んだ bytes を一度 parseし、その exact parse result を canonical JSON bytes へ再符号化して hash」である。

  raw bytes の hash を採ると、空白、key 順、Unicode escape の違いだけで同一内容が別 proposal になる。一方、producer が raw bytes を hash し consumer が parse result を hash する組合せは危険である。両側が同じ public canonical 関数と同じ parser 契約を使う必要がある。

  再現手順: key 順や空白だけが違う二つの JSON を `json.loads` 後に `canonical_json_bytes` へ渡すと同じ bytes になる。これは設計上の正例であり、今回は実走していない。

- **L7 — real、読解。段 2 が duplicate key を許す決定は「正しい file bytes」を束縛しない。** 段 2 プラン `:42` は通常 loader の last-key-wins を維持する。base も K2 条件時だけ `object_pairs_hook` を使い、formal launcher が作る通常 base argv では `p3_s4_loop.py:2034-2035` の通常 `json.load` になる。sort `p3_s4_loop_sort.py:457-458` と trigger `p3_s4_loop_trigger_gating.py:936-937` も last-key-wins である。

  攻撃列:

  1. registry に通常 document A の canonical hash `H(A)` を登録する。
  2. file B に同じ top-level keyを二度置き、最後の値だけが Aになるようにする。例えば異なる `planner` を先に置き、Aの `planner` を後に置く。
  3. Python loader は後者だけを残し、canonical hash は `H(A)` になって通る。
  4. raw bytes は Aと異なり、first-key-wins の reader では別 document になる。

  同じ Python objectを実行する限り Bを実行して Aを hash する事故ではないが、「proposal file の bytes が固定された」という主張は成立しない。B-4 の3 loaderすべてで duplicate keyを fail-closed に拒否するのが安全である。

## 信頼境界

- **L8 — refuted、読解。P1-3 の receipt key 追加・削除だけでは proposal 側は hash を制御できない。** 現行順序を維持する限り、除外 key は提案が選ぶのではなく固定 constant が選ぶ。

  - bootstrap で key を追加すると base `p3_s4_loop.py:2043-2047`、sort `:466-470`、trigger `:945-949` が hash 前に拒否する。
  - continuation で key を削除、または誤値にすると base `:2049-2053`、sort `:472-479`、trigger `:951-958` が拒否する。
  - trusted terminal receipt bytes と一致する値だけが受理され、その後 top-level key 一つだけが base `:2054-2055`、sort `:480-481`、trigger `:959-960` で除かれる。
  - nested 同名 key は closed schema が拒否する。

  攻撃再現は「bootstrap に追加」「continuation から削除」「誤値へ変更」の3変異であり、すべて hash 比較へ到達しない。予定 helper をこの receipt gate より前に呼ばないことが条件である。

- **L9 — real、読解。ただし操作主体は proposal ではなく launcher caller である。** 段 2 は registry 行を supplied `attempt_id` だけで選び、row の `driver`、`workload`、`bootstrap_member` 等を current execution と照合しない (`stage2-plan.md:67-78,289`)。registry 型にはこれらが実在する (`p3_b4_analysis_ledgers.py:124-143`)。

  攻撃列:

  1. publication に `attempt_id=t_base`, `driver=base`, `initial_proposal_sha256=H(A)` の行を封印する。
  2. sort launcher を選び、`--b4-attempt-id t_base` と同じ proposal Aを渡す。
  3. 計画された検査は row の `H(A)` しか比較しないため通る。
  4. 実行 driver は sort だが、成果物は base 用 registry attempt を参照できる。

  proposal document が expected hash や除外 key を選ぶ経路は見つからないが、argv identity が誤った registry 行を選べる。これは「内容 hash の一致」より上の scheduled-attempt identity 層の穴である。

## 3 driver の非対称

- **L10 — refuted、読解。formal `main` から proposal loader を素通しする driver は見つからない。** launcher registry は `p3_b4_launcher.py:140-144` で3つの real `main` を保持し、共通 `_driver_argv` `:177-193` が全 driver に同じ B-4 marker と proposal path を渡す。各 main は base `p3_s4_loop.py:2473`、sort `p3_s4_loop_sort.py:738`、trigger `p3_s4_loop_trigger_gating.py:1289` で自 module の loader を必ず呼ぶ。予定 helper を3 loaderに追加すれば formal main の片肺はない。

  再現手順: `DRIVER_REGISTRY` の各値を実 main のまま、各 loader/binding helperだけを spy化して三回 bootstrap を行い、各一回呼出しを確認する。今回は実走していない。

- **L11 — real、読解。terminal receipt の検証順序は非対称である。** base は proposal load前に `require_b4_iteration_authorization` を呼び、terminal receipt 全体を検証する (`p3_s4_loop.py:2455-2468`)。sort と trigger は load前には raw receipt SHAだけを計算する (`p3_s4_loop_sort.py:729-742`、`p3_s4_loop_trigger_gating.py:1280-1293`)。完全検証は後の `drive_iteration`、sort `:543-563`、trigger `:1062-1082` まで遅れる。

  これは registry gate の素通しではないが、「3 driver で同じ順序」という説明は誤りである。統一するなら、registry binding は receipt keyを除いた core に対して全 driverで最初に行い、terminal receipt の完全検証はその後の同じ段に揃えるべきである。

  再現手順: hash は取れるが schema-invalid な terminal receipt と registry-mismatch proposal を渡す。base は receipt error、sort/trigger は先に proposal registry mismatchへ到達する構造になる。今回は実走していない。

- **L12 — refuted、読解。trigger の proposal 再読取りは formal B-4 では発火しない。** `_write_source_preimage_artifact` は `p3_s4_loop_trigger_gating.py:299-382` で proposal path を再読するが、呼出しは `:798-801` の `require_source_preimage_artifact=True` 時だけである。formal main から `drive_iteration` へは private optionを渡しておらず既定 `False` (`:994`) のため、この経路は B-4 の二度読みにならない。

  再現手順: formal main の `drive_iteration` kwargs を記録し、`_require_source_preimage_artifact` が未指定であることを確認する。今回は読解のみ。

## 親の provisional 裁定の個別評価

- **L13 — P1-1 は条件付き賛成、読解。** publication root と attempt id を明示 argv で渡す選択は正しい。campaign layout から探索すると identity が二義化する。ただし、argv forwarding だけでは launcher 先行副作用を塞げない。proposal の単一 bufferを誰が所有するかも同時に決め、bootstrap の `p3_b4_launcher.py:540` より前、continuation の独立した実行段の最初で照合する必要がある。

  再現手順:同じ campaign layout から複数 publication root が見つかる状態を想定しても、明示 argv なら一意に選べる。一方、launcher照合とdriver再読取りを併用するとL5のABAが再現する。

- **L14 — P1-2 は賛成、既存テストへの波及は修復可能、読解。** B-4 実行時の束縛引数なしは拒否すべきである。

  実際に壊れる中心は `test_p3_b4_closed_critic.py:109-160` の `_production_launch_context` である。この helper は real bootstrap launcher に存在しない `unused-proposal.json` を渡して contextだけを回収している。15件の利用者がこの helperに依存する。段2が述べるように、実 proposalとpublication fixtureをhelper内で用意すれば従来の検査目的を維持できる。

  `create_b4_closed_critic_pair` 自体は `p3_b4_closed_critic.py:1226-1357` で proposalを消費せず、pair生成経路へbinding引数を追加する必要はない。影響するのはproduction contextをbootstrap helper経由で得る部分である。continuation正例は `test_p3_b4_closed_critic.py:2705-2722` でproposalをreceipt後に作るため、fixture更新だけでなくL3の順序設計にも従う必要がある。

  また、base `test_p3_s4_loop.py:5216-5237`、sort `test_p3_s4_loop_sort.py:1210-1238`、trigger `test_p3_s4_loop_trigger_gating.py:3153-3184` はfixture/no-build拒否がpin検査より前であることを固定している。binding不在検査をこれら既存拒否より前へ出すと例外理由が変わるため、非実行routeの既存拒否順は保持する必要がある。

- **L15 — P1-3 は修正付き賛成、読解。** canonical対象はparse後のproposal documentからtop-level receipt keyだけを除いた値でよい。receiptはcontinuation中に生成されるため含められない。ただし条件は次の二つである。

  - B-4の3 parserすべてでduplicate keyを拒否する。
  - issuer側の将来producerも同じparser、同じreceipt除外、同じ`attempt_registry_core.canonical_json_bytes`を使う。

  receipt keyの有無によるhash制御攻撃はL8のとおりrefutedである。

- **L16 — P1-4 はformal mainについて賛成、最終sinkについて不足、読解。** 3 mainを全部覆う必要がある。ただしbindingがloader内だけに存在すると、各 `drive_iteration` / `run_one_iteration` public APIはbound proposalであることを型や引数で要求しない。base `p3_s4_loop.py:2106-2126`、sort `p3_s4_loop_sort.py:503-511`、trigger `p3_s4_loop_trigger_gating.py:984-1002` はpublication rootもattempt idも受け取らない。

  formal production contextの発行はlauncherに閉じているため、通常CLIの直接bypassではない。しかし「loop側の最終sink自身が束縛を閉じる」というD1343の局所不変にはなっていない。保証をformal launcher経路だけに限定するか、loaderからsinkまでspecificなbinding成功値を携帯するかは裁定が必要である。

## 凍結・pin への波及

- **L17 — 親の「現時点で凍結literal pinなし」は実測で支持された。** 読取り専用で現在値を計算した。

  - `p3_b4_launcher.py` SHA-256: `5553ad8d6ba88281ce9ad1c6a42c77a51242c7e5b211e94f74e95ce245d04741`
  - `p3_s4_loop.py` SHA-256: `73ffcd1715bdc189de7306f5d39df1a8a6a8d53f704475fbba584fca474a3759`
  - live projection: base `48881297...e34e8fd`、sort `20582007...87d348`、trigger `1a74e41b...0aa5a9e`

  `rg --fixed-strings` でrepository/outputを検索し、5値ともhit 0だった。`docs/phase3-b4-reflux-ablation-preregistration.md:166` はprojection欄が未記入で、要求される3 admission record fileも現worktreeには存在しない。`output` の32個の `campaign.lock` にも `p3_b4_launcher.py` memberはhit 0だった。これは実走したread-only検算である。

- **L18 — real、読解。「pinなし」は変更が波及しないという意味ではない。** `p3_b4_closed_critic.projection_closure_manifest` はbaseを含む全driverで `p3_s4_loop.py` と `p3_b4_launcher.py` をmemberにする (`p3_b4_closed_critic.py:632-657`)。sort/triggerはさらに各driver fileを追加する (`:658-667`)。このwaveでbase loopとlauncherを変えると3 projection digestすべてが変わる。

  記録済み値が存在する場合、launcherの `issue_context` は `p3_b4_launcher.py:352-359` で全3 live digestを再計算し、prereg/admission値との不一致をsidecar前に拒否する。現在は値が未記入なので既存artifactとの衝突はないが、記入済みcheckoutへ後からこの変更を適用することはできない。

  再現手順: current projection値を記録したfixture admissionを作り、`p3_s4_loop.py` の任意byteを変えたcheckoutでbootstrap admissionを検証すると3driver共にprojection mismatchになる。今回は変更・実走していない。

- **L19 — realな停止伝播だが、現在のrepo/outputには対象lockなし。** `p3_b4_launcher.py` は `campaign_lock.py:49-113` の63-path closure memberである。新規lockは `contract_loader_binding.py:518-532` がcurrent HEAD blobを捕捉する。既存v2 lockの再開では `ident.py:350-396` → `verify_live_contract_loader_binding` `contract_loader_binding.py:535-555` が記録commit blobとlive bytesを比較するため、旧launcherをpinしたlockは変更後に`contract-loader-drift`で止まる。

  未commit中に焦点テストが赤になるのもこの経路であり、commit後の新規campaignは新hashを捕捉する。親briefの「repo/outputに既存pin 0件」は支持されるが、外部artifact rootにあるv2 lockまでは今回の検索範囲から証明できない。

## scope 外の層と裁定パッケージ候補

- **L20 — issuer producer層。** `initial_proposal_sha256` は現在64 hexだけを検査する (`p3_b4_analysis_ledgers.py:305-340`)。実proposalからcanonical hashを作るproducerは存在せず、`p3_b4_raw_record_producer.py:62-70` も非保証として明記する。

  裁定候補: formal publication発行前の別scopeで、L15のsemantic canonical規約をproducerに実装する。それまではruntime gateを実装済みと呼べても、正しいregistryを生成できるend-to-end束縛とは呼ばない。

- **L21 — scheduled-attempt identity層。** L9のとおり、driver/workload/bootstrap membershipとの照合は段2が明示的にscope外としている。

  裁定候補: 「D1343の保証はproposal content hashだけ」と限定するか、current driver等とregistry rowの既存fieldを同時照合するかを決める。事前固定した201試行という主張を守るなら後者を推奨する。

- **L22 — raw/material report層。** raw producerはregistry hashを`precursor_hash`として転記するだけ (`p3_b4_raw_record_producer.py:2027-2037`)。material reportもbindingを`transcribed`として表示する (`p3_b4_material_report.py:396-411,470-477`)。runtime照合成功を既存raw artifactから独立に再確認するfieldはない。

  裁定候補: 今回はruntime拒否だけを完成させ、report文言を「runtimeで強制されるが、このreport単体では独立再証明しない」と整合させるか、既存raw schemaへobserved canonical hashと選択publication/attempt identityを後続scopeで載せるかを決める。新しい台帳の新設は不要である。

- **L23 — direct loop API層。** 段2は`run_one_iteration`一般APIをscope外にしているが、D1343の文言は「実行ループ側」である。formal launcherだけの保証か、B-4 marked configを受ける全sinkの保証かが未裁定である。

  裁定候補: formal launcher限定ならその境界を明記する。全B-4 sinkが対象なら、binding成功値を`drive_iteration`の必須入力にして最終sinkでも確認する。

## 総括

段2プランは、campaign build、campaign lock、WAL、benchより前に不一致を拒否する狭い条件は満たせる。しかし、要求された広い「実行前性」は満たさない。3 driverは照合前に`pgrep`とGitをspawnし、launcherはsidecarを作り、continuationはproposalが存在する前に二つのcritic processとreceipt群を生成する。

実装前の必須修正は、proposalの単一buffer所有を保ったままdriver内照合をpreflightの先頭へ移すこと、およびcontinuationのcritic発行段とfinalized proposal実行段を分離することである。canonical意味論とP1-3のreceipt除外は妥当だが、duplicate key許容は除くべきである。receipt key追加・削除によるhash制御攻撃は、既存receipt gate順序を守る限りrefutedである。

ファイル編集、commit、pytest実走は行っていない。hash計算とrepository/output内のpin検索だけをread-onlyで実走した。