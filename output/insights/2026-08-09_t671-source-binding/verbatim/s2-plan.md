# 設計択一 — T-671 source binding / t530 F-12

必読 4 文書はすべて読めた。以下は静的設計のみで、本番コード・文書とも無変更、テスト未実行である。

先に結論を示す。

- 争点 A は **R-A1「commit-backed source authority を campaign authority に固定」**を推奨する。
- 争点 B は **R-B2「campaign identity と execution authority を分離し、世代差は書込み前に停止」**を推奨する。
- 親 P2 の「lock の H を `ever_active` で解決すれば旧世代 resume できる」は成立しない。`ever_active` は履歴検証用であり、現行 guard は terminal/current contract だけを認可するからである。
- T-657 活性化そのものを一律に止める必要はない。ただし A は最初の g2 generic certified 書込みより前、B は t530 を活性化より先に land するならその前に必要となる。

## 判断の基礎

A の非対称は実在する。silo は live bytes、qualification は commit blob を独立に束縛する一方、generic loop、WAL、Layer3 report は loader bytes を持たない。[実測 A:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-explore-a.md:7) [実測 A:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-explore-a.md:25)

B では次の区別が重要である。

- [`env_contract.authorize()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/env_contract.py:636) は terminal activation state の current contract だけを発行する。
- [`resolve_by_contract_sha256()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/env_contract.py:671) は ever-active H の履歴検証用である。
- [`execution_guard._contract_from_authorization()`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/execution_guard.py:44) は receipt が terminal state の active row と一致することを要求する。

したがって「旧 H を引ける」と「旧 H で新しい certified measurement を許可できる」は別である。

また、campaign の既存定義は「同じ spec/config は crash/restart 後も同じ id」とし、env を identity から明示的に除いている。[orchestrator-design.md:125](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/orchestrator-design.md:125) [orchestrator-design.md:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/orchestrator-design.md:153) [orchestrator-design.md:155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/orchestrator-design.md:155)

## 争点 A — generic certified producer の source binding

### R-A1 — commit-backed campaign authority に固定する〔推奨〕

`campaign.lock` を新規 campaign に限って v2 envelope にし、logical identity と certified authority を分離する。

```json
{
  "schema": "campaign-lock/v2",
  "identity": {
    "spec_content": "...",
    "ccbench_commit": "...",
    "search_tag": "...",
    "search_config": {},
    "trial": null
  },
  "authority": {
    "environment_contract": {
      "contract_sha256": "...",
      "activation_serial": 2,
      "activation_state_sha256": "..."
    },
    "loader_source": {
      "source_commit": "<full 40-hex>",
      "modules": [
        {"path": "orchestrator/campaign/env_contract.py", "sha256": "..."},
        {"path": "orchestrator/campaign/env_contract_activation.py", "sha256": "..."}
      ],
      "modules_sha256": "..."
    }
  },
  "authority_sha256": "..."
}
```

変更箇所は以下。

- 新規 `orchestrator/campaign/certified_source_binding.py:1` に exact 2-path 集合と二つの API を置く。
  - `capture_loader_binding(repo_root, source_commit)`：live regular-file bytes と `git cat-file blob <commit>:<path>` を一致検査して canonical receipt を返す。
  - `verify_recorded_loader_binding(binding)`：履歴 consumer 用。現在の live bytes ではなく記録 commit の blob と照合する。
- [`certified_writer_preflight.py:66-126`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/certified_writer_preflight.py:66) は上記 helper に委譲する。floor/T126 の「import 済み全 module」モードは維持し、generic campaign は exact 2-path モードを使う。
- [`execution_guard.py:107-170`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/execution_guard.py:107) に sealed `CertifiedWriterAuthority` issuer/verifier を追加する。契約 receipt と source binding を一つの値にし、layout 作成より前に発行する。
- [`loop.py:61-89`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/loop.py:61) は `(contract, execution_receipt)` でなく `(writer_authority, execution_receipt)` を返す。[`loop.py:123-164`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/loop.py:123) は authority 発行 → stable id 算出 → v2 lock atomic acquire → repair/replay の順にする。
- [`ident.py:125-178`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/ident.py:125) を `canonical_identity_preimage()` と `canonical_lock_envelope()` に分離する。campaign id は `identity` だけを hash し、source bytes は id に入れない。
- [`pipeline.py:476-601`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/pipeline.py:476) は sealed authority と lock の `authority_sha256` を再照合する。二つの COMMIT mouth、[`pipeline.py:1020`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/pipeline.py:1020) と [`pipeline.py:1069`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/pipeline.py:1069) に `certified_authority_sha256` を追加する。
- [`wal.py:526-590`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/wal.py:526) の repair/recovery 前と replay/read admission に、全 COMMIT と lock authority の exact 一致検査を置く。
- [`artifact_admission.py:600-712`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/artifact_admission.py:600) は v1 historical lock と v2 lock を明示 dispatch し、v2 では commit blob、authority digest、全 COMMIT を検証する。
- [`layer3_report.py:398-507`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/layer3_report.py:398) と `orchestrator/campaign/layer3_schema.json:1` を v4 にする。`meta.certified_authority_sha256` と authority source ref を出す。v2/v3 report reader は残し、既存 report は再生成しない。
- [`test_campaign.py:2513-2557`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/test_campaign.py:2513) が閉集合化している 15 `run_campaign` 呼出しと direct sink 4 箇所（loop、screening、S1 direct、S8b oracle）のすべてに authority 伝播を要求する。

実装量は production 11〜14 ファイル・約 500〜750 行、test 5〜7 ファイル・約 650〜900 行。B-R2 と同時実装すれば lock/WAL/admission/report の重複を約 200〜300 行削減できる。

**成果物影響（未採用時）:** certified 選択は同じ contract/activation ref で異なる loader semantics の COMMIT を受理し、材料レポートは loader ref を持たず、試行台帳ではその差を識別できない。

互換性は維持できる。

- 既存 30 campaign は v1 historical lane のまま bytes 不変。
- 既存 Layer3 v2/v3 report も bytes・受理集合不変。
- 新規 v2 campaign だけが「1 campaign = 1 authority」に狭まる。
- source change 後に同一 campaign を続行する場合は silent resume せず、明示 `trial` が必要になる。

再利用は preflight の commit blob reader、qualification の commit-backed 検証方式、WAL の既存 lock-derived validator である。新規なのは共通 canonical authority、v2 lock dispatch、generic sink 全口への durable ref である。

採用条件は、full repo commit を code identity のアンカーとして認めることと、「悪意ある同一プロセスが verifier 自体を改変する」ことを security boundary の対象外とすること。後者まで防ぐなら out-of-process署名/attestation が必要で、D205 の範囲を超える。

### R-A2 — write-time preflight だけを generic guard に配線する

- `certified_source_binding.py` を切り出す点は R-A1 と同じ。
- [`execution_guard.py:107`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/execution_guard.py:107) の先頭で live loader bytes と source checkout HEAD blob を検査する。
- lock、WAL、report schema は変えない。

production 3 ファイル・約 120〜180 行、test 2 ファイル・約 180〜250 行。

**成果物影響（未採用時）:** dirty loader 実行から COMMIT・材料レポート・試行台帳が生成されるが、採用時は書込み自体が不発になる。ただし二つの clean commit 由来成果物は artifact 上で識別不能のまま。

既存 bytes・30 campaign・reader の受理集合は完全不変。writer の受理集合だけを dirty-tree 分だけ狭める。

既存 preflight を最大限再利用できるが、これは「dirty source 防止」であり「certified artifact の durable code identity」ではない。T-671 を完全に閉じたとは名乗れないため、R-A1 までの暫定策に限る。

### R-A3 — silo 型 live hash を記録し、current live bytes と比較する

[`silo_ladder_rung1.py:254-294`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/silo_ladder_rung1.py:254) を汎用化し、lock/COMMIT/report に live hash を記録する。historical validation も [`validate_current_bindings():3517`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/silo_ladder_rung1.py:3517) と同様に current live bytes と比較する。

production 6〜8 ファイル・約 250〜400 行、test 3〜4 ファイル・約 300〜450 行。

**成果物影響（未採用時）:** loader 差は台帳・レポートに出ない。採用時は差が出るが、source update 後に過去の certified 選択・材料レポート・台帳が current-live 不一致で拒否される。

既存 30 本を legacy exempt にはできるが、採用後の成果物が次の loader edit で歴史検証不能になる。qualification の commit-backed 検証より弱く、凍結成果物の原則にも合わないため却下する。

### R-A4 — 記録のみ、または docs pin / 見送り

production/test とも 0 ファイル・0 行。

**成果物影響（未採用時＝現状維持）:** certified 選択・材料レポート・試行台帳の値も参照も変わらず、受理集合だけが loader 改変込みのまま残る。

発火 gate が存在しない。D205 は防御的 hardening を見送る裁定だが、certified proof chain の欠落は測定・台帳の正しさに直接関係するため、見送り根拠にはならない。[D205:9840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/decisions.md:9840)

## 争点 B — contract generation を跨ぐ campaign resume

### R-B1 — lock-pinned H で historical certified resume を許可する

これは親 P2 を実現する完全形であり、単なる `ever_active` 呼出し追加ではない。

- [`env_contract_activation.py:74-97`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/env_contract_activation.py:74) の `ActivationState` に、各 serial の state hash と active rows の履歴 index を保持させる。
- [`env_contract.py:636-703`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/env_contract.py:636) に `authorize_historical_resume(contract_sha256, activation_serial, state_sha256)` を新設する。ever-active 集合だけでの発行は禁止する。
- [`execution_guard.py:44-104`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/execution_guard.py:44) に current authorization と historical-resume authorization の別型・別用途を追加する。Pegasus の calibration/attestation が旧 H の実行値をなお満たすことを再検査する。
- t530 `loop.py:123-136` は ambient authorize より先に logical lineage の既存 lock を探し、そこから H・serial・state hash を取得して旧 id を再構成する。
- [実測 B:39-43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-explore-b.md:39) の ambient `lookup/authorize` 呼出し群も、clocks/numactl を current から早取りせず resume authority から受け取る形へ変える。

production 14〜19 ファイル・約 700〜1,100 行、test 7〜10 ファイル・約 900〜1,300 行。

**成果物影響（未採用かつ他の B gate なし）:** g1 の certified set は旧 root に残り、g2 COMMIT は新 root に入り、材料レポートと試行台帳参照が二分される。採用時は同じ root/H_g1 に継続する。

既存 30 campaign は H 欠落の historical laneとして不変。t530 の H 入り id も維持できる。

ただし受理集合は「terminal/current H」から「厳密に記録された historical H の resume」へ広がる。これは正しさ gate の単純緩和としては採れない。次の二条件をユーザーが明示裁定した場合だけ viable である。

1. retired contract で新しい certified measurement を取ることを許す。
2. 旧 calibration/attestation を現時点のマシンに再適用できる。

### R-B2 — identity と authority を分離し、世代差は書込み前に停止する〔推奨〕

R-A1 の v2 lock envelope を共通基盤にする。

- t530 `ident.py:52-74` の `bind_environment_contract()` は `search_config` へ H を入れない。H は `lock.authority.environment_contract` に置く。
- t530 `ident.py:155-203` の campaign id は `lock.identity` のみから導出する。これは現行 [`ident.py:125-156`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/ident.py:125) と D13 の env 非 identity 規則を回復する。
- [`loop.py:123-164`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/loop.py:123) は stable id から既存 lock を読む。
  - 初回なら current authorization を authority に atomic pin。
  - resume なら current authorization と pinned H を比較。
  - H が異なれば `CampaignAuthorityBoundary` を発生させ、`layout.ensure()`、repair、recovery、WAL 書込みより前に停止する。
- t530 `wal.py:947-986` の COMMIT validator は期待 H を `search_config` でなく `lock.authority.environment_contract.contract_sha256` から読む。
- t530 `pipeline.py:1027-1028,1086-1088` の COMMIT `contract_sha256` は維持する。
- [`artifact_admission.py:637-712`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/artifact_admission.py:637) は id を `identity` から再導出し、authority と COMMIT を交差検査する。
- g2 で新しい campaign を開始する場合は既存仕様どおり明示 `trial` を変える。[orchestrator-design.md:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/docs/orchestrator-design.md:153)
- [`replay.py:89-107`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/replay.py:89) に exact campaign id / trial selector を追加し、意図した複数 trial を ambient current H で選ばない。

単独なら production 7〜9 ファイル・約 350〜550 行、test 4〜6 ファイル・約 450〜700 行。R-A1 と束ねた場合、共通 lock schema、WAL validator、artifact admission、report projection を一度だけ実装できる。

**成果物影響（未採用かつ t530 をそのまま land）:** g1/g2 で certified 選択・材料レポート・試行台帳が別 id/root に分裂する。採用時は世代差で成果物を一切増やさず、明示 trial の新 root だけを許す。

互換性は次のとおり。

- 既存 30 campaign と凍結 bytes は v1 historical として不変。
- t530 は未 land なので、t530 branch の golden id は変更してよい。既存 H-bound production artifact の移行は不要。
- 新規受理集合は「authority 一致、または明示 trial」に狭まる。旧 H で新規計測する受理拡大はない。

既存の current authorization、t530 WAL H validator、atomic lock acquire、`trial` を再利用できる。新規なのは identity/authority の分離と boundary error だけであり、研究プロトタイプとして最も正しさ/実装量の釣合いがよい。

採用条件は「activation で retired になった H は、新しい certified measurement の authority ではない」という現行 `authorize()` の意味を維持すること。連続 resume が必須なら R-B1 の別裁定が要る。

### R-B3 — t530 の H 入り id を維持し、事前 lineage scan で停止する

t530 の設計・golden id をほぼ保つ最小案。

- t530 `ident.py:155-203` に、`environment_contract_sha256` だけを除いた `logical_lineage_preimage()` を追加する。
- t530 `loop.py:123-136` は current H で新 layout を作る前に、同じ slug/tag の lock を strict parse し、同じ lineage・異なる H があれば停止する。
- 0 hit なら current H で開始、同じ H が 1 hit なら resume、複数 hit は fail-closed。
- 明示 `trial` は lineage が異なるため新 g2 campaign を許す。

production 3〜4 ファイル・約 150〜240 行、test 2〜3 ファイル・約 200〜320 行。

**成果物影響（未採用時）:** 新 H の certified set・report・ledger が別 root に静かに生成される。採用時は異世代 root を作らず boundary error だけを返す。

既存 30 本と t530 golden id は不変。実装量は最小だが、env が campaign id を変える D13 違反と、consumer が世代別 id を扱う複雑さは残る。R-B2 の再構成が許されない場合の暫定案である。

### R-B4 — 分裂を仕様化し、discover を H-aware にする

- [`replay.py:89-107`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/campaign/replay.py:89) を `discover_campaign_dir(..., contract_sha256=...)` にする。
- Layer3 report、backoff report、raw readers の全 caller に explicit H selector を渡す。
- H selector 欠落時に複数 root があれば従来どおり拒否する。ambient current H への defaultは禁止する。

production 4〜7 ファイル・約 180〜320 行、test 3〜4 ファイル・約 250〜400 行。

**成果物影響（未採用時）:** 分裂後の certified 選択・材料レポートが 2-hit error で読めない。採用時は H ごとの選択・report・ledger を読めるが、未完了 g1 が自動的に g2 の別 campaign へ変わった事実は残る。

既存 30 campaign には legacy selector が必要。これは可用性だけを直し、restart identity の破断を仕様化するため却下する。activation が必ず新 campaign を意味するという別のユーザー裁定がある場合に限り採用候補になる。

## 推奨組合せと採用条件

推奨は **R-A1 + R-B2** である。両者を一つの `campaign-lock/v2` authority envelope として実装する。

採用条件は三つ。

1. campaign は spec/config/trial で決まり、loader commit と environment generation は campaign の logical identity ではなく、最初の certified write に固定される authority である。
2. source commit または contract generation が変わった同一 campaign は自動継続せず、明示 `trial` を要求する。
3. source binding の脅威モデルは accidental/dirty checkout・履歴の取り違えまでとし、悪意ある in-process code に対する暗号学的隔離までは要求しない。

条件 2 が許容できず旧 generation の連続 resume が研究上必須なら、B だけ R-B1 へ切り替える。その場合は「ever-active を current authorization と同格にする」のではなく、historical-resume 専用 authority と再 attestation を設計する必要がある。

## 2 争点の結合

両者は同型である。共通原則は次の一文にできる。

> Ambient current は最初の durable write の authority 解決にだけ使い、その exact identity を atomic lock に固定する。resume は記録 authority を先に読み、current と一致しなければ書込み前に停止する。historical consumer は current live state でなく記録された commit/activation chainを検証する。

この原則により、

- source edit 後に古い artifact が current-live mismatch で壊れること、
- activation 後に current H が別 id を作ること、
- lock 作成後に ambient 値が変わって同一 WALへ混ざること、

を同じ構造で防げる。

## 恒真性・実発火監査

| 案 | 現存する発火 artifact / measurement | 自己検査 |
|---|---|---|
| R-A1 | source drift 自体は [`test_campaign.py::test_m8_preflight_rejects_fail_open_domain_module_drift`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/test_campaign.py:2696) で実発火する。generic sink の実 artifact は [wal.jsonl](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:1) と [layer3_report.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/reports/layer3_report.json:1)。 | 両者を結ぶ generic integration measurement は現存しない。実装時に「loader drift が layout/WAL より前に拒否」と「recorded commit blob mismatch を admission が拒否」の二つを必須追加しない限り、閉じたと主張しない。 |
| R-A2 | 上記 `test_m8_preflight...` は gate 本体を発火させる。direct sink 閉集合は [`test_certified_writer_authorization_caller_inventory_is_closed`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/orchestrator/tests/test_campaign.py:2513)。 | generic guard 配線の実発火はまだない。配線後の direct-sink mutation test が必要。 |
| R-A3 | 実 artifact [campaign-root-receipt.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/campaign-root-receipt.json:1) に `runtime_modules_sha256` が存在し、silo の gate は実在する。 | generic path には未配線。さらに current-live 比較が歴史 artifact を拒否する反例 test が必要。 |
| R-A4 | なし。 | gate がないため強度を主張できない。 |
| R-B1 | t530 measurement `test_campaign_identity_is_unchanged_for_other_and_split_for_compute` (`t530@9f60471b:orchestrator/tests/test_p3_s4_loop_trigger_gating.py:590`) は H による id split を実測する。 | g1 lock→g2 activation→historical resume の measurement はない。既存 production 30本にも H がないため、実装前に cross-generation test が必須。 |
| R-B2 | 同じ t530 id-split measurement が失敗入力を構成できる。g1/g2 fixture は t530 test 群に存在する。 | boundary gate を実際に発火させる artifact はまだない。`g1 lock + partial WAL → g2 current → no dir/WAL mutation` の決定的 test が必要。 |
| R-B3 | 同上。 | lineage scan の positive rejection measurement は未存在。追加できないなら恒真性を否定できず採用不可。 |
| R-B4 | t530 id-split measurement が 2 id を作ることは示す。 | WAL を持つ 2 root を `discover_campaign_dir` が H selector で一意化する measurement は未存在。追加が必要。 |

既存 30 campaign は 30/30 が `build_admission` も contract H も持たないため、B の新 gate を現在の production artifact で正に発火させることはできない。[実測 B:53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-explore-b.md:53) これは隠さず、DW-G04 上、本件をいま設計 wave に留める根拠とする。

## 順序制約

安全な順序は二通りある。

1. **推奨する短期順序**
   - T-657 の既裁定 prerequisites を完了
   - t530 を未 land のまま g2 を活性化
   - R-A1 + R-B2 を t530 に統合/rebase
   - t530 を land
   - 最初の g2 generic certified campaign を開始

2. **t530 を先に land する場合**
   - R-B2、少なくとも R-B3 を t530 に先に統合
   - t530 land
   - T-657 g2 活性化
   - 最初の g2 generic write より前に R-A1

理由は、分裂条件が `t530 land ∧ g1 H-bound unfinished campaign ∧ g2 resume` の conjunction だからである。[brief:27](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t671-source-binding/s1-brief.md:27) 現在は t530 未 land、g2 未活性化、H-bound production campaign 0 本なので、T-657 を先行させれば B の発火条件は成立しない。

したがって「活性化の前に本件を閉じる必要があるか」への答えは、**一括では No、境界別には次のとおり**である。

- B：t530 を未 land のまま活性化するなら不要。t530 を先に land するなら必要。
- A：activation record を追加するだけなら不要。ただし、最初の g2 generic COMMIT・材料レポート・WAL より前には必要。
- certified producer の無稼働を機械的に保証できない場合は、A も活性化前提へ昇格させる。

T-657 の既裁定 prerequisites は silo 歴史解決と floor protocol 再発行であり、さらに T-627 は活性化前と裁定済みである。[ruling §44–45](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md:387) 本設計はその裁定を黙って増補せず、「activation」と「最初の generic certified output」を分けて扱う。

## 却下すべき案

- **契約文・docs pin・運用宣言だけで「source-bound」「resume-pinned」と名乗る案。** 実 producer の bytes/H を拘束しない。[T-665 段4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t671-source-binding/output/insights/2026-08-08_t665-t662-launch-binding/verbatim/s4-adjudication.md:54) が否定した問題の再演である。
- **loader hash を自己申告するだけの案。** COMMIT field は増えるが、live bytes↔commit blob の write gate と独立 consumer がなければ受理集合は変わらない。
- **source binding を `search_config` に入れる案。** loader edit ごとに campaign id が分裂し、争点 B を source code 側でも再現する。
- **`ever_active` をそのまま historical write authorization とみなす案。** 履歴検証と新規計測許可を混同し、現行 guard の current-only gate を実質的に弱める。
- **H を id から外すだけで、resume 時は ambient current を書く案。** 同一 WAL に g1/g2 COMMITを混在させ、t530 が閉じようとした provenance 欠落へ戻る。
- **discover だけ直して分裂を受容する案。** read availability は戻るが、同じ campaign の unfinished ledger が別 root へ静かに移った問題は残る。
- **既存 30 campaign や v2/v3 report を新 schema へ再生成する案。** frozen bytes と歴史受理集合を不必要に変えるため採らない。

## 総括

争点 A は R-A1、commit-backed loader binding を v2 campaign authority に固定し、COMMIT・artifact admission・Layer3 report まで同じ digest を通す案を推奨する。R-A2 は dirty-tree 防止の暫定策に限る。

争点 B は R-B2、campaign identity と execution authority を分離し、generation 不一致を最初の書込み前に停止する案を推奨する。旧世代での連続計測が必要な場合だけ、別の historical authorization を備えた R-B1 を再裁定する。

順序は、t530 未 land のまま T-657 を先行させるなら本件全体を activation 前提にする必要はない。ただし A は最初の g2 generic certified 出力より前、B は t530 を T-657 より先に land するならその前に閉じる。