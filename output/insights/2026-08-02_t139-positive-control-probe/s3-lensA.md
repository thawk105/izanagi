静的判定は **NO-GO** です。旧 D120 entry の直接再分類ではありませんが、別 manifest を新しい admission authority にする根拠、実行 binary への終端束縛、checkout witness の独立取得が閉じていません。

## BLOCKER

### B1. qualification manifest が自分自身を admission authority にしている

**自己判定: real。ただし「旧 D120 entry を別名で直接消費する」という狭義の攻撃は refuted。**

`ledger.json` の機械的射程は `scope="registered-entries-only"` で、旧 ID/path/hash に限定されています。[ledger.json:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/patches/ledger.json:2) [ledger.json:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/patches/ledger.json:5) 旧 contract も entry 1 件と `recovery_measurement_eligibility=false` を exact に要求します。[silo_ladder_rung1_contract.py:517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/silo_ladder_rung1_contract.py:517) [silo_ladder_rung1_contract.py:538](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/silo_ladder_rung1_contract.py:538) したがって、新しい patch identity が旧 ID/pathを参照しない限り、旧 entry の byte/identity 上書きではありません。

しかし repository 全体の規範は、ability probe を `ledger.json` 登録必須としています。[patches/README.md:13](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/patches/README.md:13) [patches/README.md:319](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/patches/README.md:319) 現行 gate も、裸 `IZANAGI_*` patch を ledger 登録または固定 allowlist 外なら拒否します。[test_p3_s4_loop.py:943](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_p3_s4_loop.py:943) [test_p3_s4_loop.py:973](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_p3_s4_loop.py:973)

段 2 は manifest 自身に `recovery_measurement_eligibility=true` を書き、その manifest を gate の登録集合へ足します。[s2-plan.md:107](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:107) [s2-plan.md:124](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:124) [s2-plan.md:152](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:152) これは二つの集合を混同しています。

- proposal 字面の拒否集合は新 token 追加で狭まる。
- 裸 macro patch の admission 集合は、ledger/allowlist から新 manifest patch まで広がる。

したがって「拒否集合を強めるだけ」という [s2-plan.md:158](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:158) は不正確です。受理集合変更には新しい D と境界テストが必要ですが、段 5 の所有表に decision 更新がありません。[decisions.md:4269](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/decisions.md:4269) [s2-plan.md:452](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:452)

さらに最新裁定は producer の `artifact_role` を `{official, exploration, qualification, dry}` に閉じています。[worklog.md:1303](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/worklog.md:1303) 段 2 の `"positive-control"` はこの enum 外です。[s2-plan.md:130](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:130) `artifact_role="qualification"`、別 field の `control_kind="positive-control"` とすべきです。

「任意 manifest を一枚置くだけで通る」攻撃は、default path 一件と exact contract に固定する実装なら refuted です。ただし、その一件を誰が承認した authority とするかは依然未定義です。現行 qualification seam は明示的に formal authority を与えません。[pipeline.py:100](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/pipeline.py:100)

**成果物影響:** 旧 ledger の `false` と既存 certified 値は不変だが、裸 patch admission と RF-input qualification の受理集合が新 ID 一件分広がる。consumer がこの自己宣言を信じれば将来の材料レポートへ未承認入力が流れ、信じなければ brief の「RF 計算可能入力が受理された」という主張自体が成立しない。

### B2. `nm` した binary と throughput を出した executable が結ばれていない

**自己判定: real。Genome/OFF-inert 攻撃は build 層では refuted、run 層では未閉鎖。**

専用 driver から `CMAKE_CXX_FLAGS` を注入するので、`Genome.cmake_defines()` が `-DCCBENCH_*` しか出せない制約は回避できます。[model.py:57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/model.py:57) [s2-plan.md:78](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:78) stock を patch 非適用 tree から作り、mode 固有 symbol を `nm` する設計も妥当です。[s2-plan.md:86](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:86) [s2-plan.md:93](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:93) これは `__LINE__` シフト問題への正しい解です。[t139 design:134](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/output/insights/2026-07-29_t139-silo-degradation-ladder-design.md:134)

欠けているのは、その binary と各 performance run の結合です。予定テストは compile argv/nm matrix と fresh build receipt までで、各 run の executable SHA を要求していません。[s2-plan.md:416](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:416) [s2-plan.md:418](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:418)

既存 driver は build record の `binary_sha256` を保存し、各 run の `target_sha256` と `argv0_sha256` を同じ値へ結びます。[silo_ladder_rung1.py:2231](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/silo_ladder_rung1.py:2231) [silo_ladder_rung1.py:3050](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/silo_ladder_rung1.py:3050) evidence test も raw command receipt から再確認します。[test_silo_ladder_rung1_evidence.py:517](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_silo_ladder_rung1_evidence.py:517)

現プランのままでは、正しい mode2 binary を `nm` した後で、macro-OFF、mode1、または上書きされた同名 path を実行しても、結果を `binary_id=mode2` と記録できます。

**成果物影響:** 誤 binary の throughput が `S[mode2,w]` に入り、ordering、between-run floor、分母、`qualification.all_pass` が偽陽性になる。後続材料レポートの RF 入力値が誤る。

### B3. measurement checkout は「独立観測」でなく同じ object の複写でも通る

**自己判定: real。**

段 2 は root receipt と全 session receipt の exact equality のみを要求します。[s2-plan.md:202](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:202) [s2-plan.md:225](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:225) M4 も一 job の field を変えるだけなので、全 job が親の receipt をコピーする実装を殺せません。[s2-plan.md:442](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:442)

恒久要件は source HEAD、clean witness、依存 repo HEAD、binary SHA、compile argv を **in-job capture** することです。[t139 design:196](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/output/insights/2026-07-29_t139-silo-degradation-ladder-design.md:196) また実際の build 入力は fresh `/scr` CCBench worktree ですが、提示された checkout schema は共有 repo checkout の field だけで、`/scr` tree の独立 git観測・patch適用後 source hash・取得 command receipt が明記されていません。[s2-plan.md:210](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:210) [s2-plan.md:227](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:227)

各 PBS job が自分で git observation を取得し、その command receipt と実 build sourceを結ばなければ、必須の「測定 checkout」を証明していません。

**成果物影響:** 8 session が別 checkoutまたは別 `/scr` sourceを使っても同一 receiptを複写して受理でき、session median・floor・qualification の由来が誤る。台帳参照は同一に見えるが実測 source は一致しない。

## MAJOR

### M1. pin 閉包は「旧 bytes 不変」だけでは閉じない

**自己判定: real。path と key の両側を確認済み。**

| 面 | 静的結果 |
|---|---|
| 旧 ledger・patch・evidence・shared policy | 予定どおり無変更なら既存整合鎖は維持。evidence は ledger/patch/driver/job/policyを現物 SHA へ束縛する。[test_silo_ladder_rung1_evidence.py:1188](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1188) |
| `FROZEN_MANIFEST` | 予定 path は23件の exact key集合外で、直接は壊れない。[test_frozen_artifacts.py:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_frozen_artifacts.py:38) [test_frozen_artifacts.py:87](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_frozen_artifacts.py:87) |
| role 名 key の SHA pin | `SOURCE_FILE_SHA256` / `ROLE_MANIFEST_SHA256` の13 roleを key 側から確認した。role変更予定がないので不変。[review_ledger.py:13](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/codex_roles/review_ledger.py:13) [review_ledger.py:34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/codex_roles/review_ledger.py:34) |
| Pegasus policy registry | 新 policy は registry 追記必須で、段 2も認識している。[s2-plan.md:307](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:307) しかし別テストが registry 全体を literal exact 固定しており、編集面から漏れている。[test_claude_transport.py:156](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_claude_transport.py:156) |
| repository file-set digest | 新 patch/driver/tests/scripts/artifact追加で必ず変わる。列挙は全 tracked/untracked regular fileを含み、`repository_files` が digest preimageに入る。[s8b_holdout_freeze.py:197](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/s8b_holdout_freeze.py:197) [s8b_floor_campaign.py:1623](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/s8b_floor_campaign.py:1623) |

最後の面は既知の F39 再発型で、T-310 として未解決です。[failures.md:735](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/failures.md:735) [worklog archive:631](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/archive/worklog-phase3-0802-106-110.md:631)

**成果物影響:** 旧 T139 artifact値と ledger SHA は不変だが、次回 floor launch certificate の `clean_scan_digest` と proof-chain replay参照は変わる。policy registry exact testも現計画のままでは landを拒否する。

### M2. stock逐語の答え露出を再生産し、入力射影は証明していない

**自己判定: real。ただし「新 patch が自動的に tool-less planner/coderへ渡る」という強い主張は refuted。**

新 patch は mode branch の隣に stock CAS を逐語で置きます。[s2-plan.md:20](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:20) [s2-plan.md:47](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:47) これは設計台帳が明記した「コピーで RF=1」を許す構造です。[t139 design:190](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/output/insights/2026-07-29_t139-silo-degradation-ladder-design.md:190)

現行 guard 自身が、proposal出力の字面 tripwireにすぎず、semantic copyや入力 originを保証しないと明記しています。[projection_guard.py:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/projection_guard.py:1) [projection_guard.py:339](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/campaign/projection_guard.py:339) 既存恒久レポートも prompt bytes の因果束縛を未実装としています。[silo_ladder_rung1-permanent.md:94](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/output/insights/2026-07-29_t139-silo-ladder-rung1-permanent.md:94)

planner/coder は tool-less なので filesystemから直接読む経路はありません。[planner-v4.md:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/.claude/agents/planner-v4.md:20) [coder-v4-autonomous.md:20](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/.claude/agents/coder-v4-autonomous.md:20) ただし、実 prompt構築時に新 patch/manifestを含めなかったことを証明する receipt は依然ありません。M9 は禁止 token が proposal出力へ現れる回帰を殺すだけです。[s2-plan.md:447](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:447)

**成果物影響:** 現 artifact は `pipeline_eligible=false` なので即時の certified 選択は変わらない。しかし後続 coder が意味的にコピーした候補を独立合成と誤認し、材料レポートの新規性・合成可能性の参照を汚す経路が残る。

### M3. 「旧 bytes 不変」テストは独立 golden がなければ自己整合にしかならない

**自己判定: real。M4/M9 自体が恒真という攻撃は refuted。**

段 2 は「旧 ledger false値と旧 evidence bytes不変」を一つの予定 node にしていますが、pre-wave SHAや固定 base commitを指定していません。[s2-plan.md:424](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:424) 現行 evidence test は現在の evidence内 hashと現在の ledger/patchを比較する整合鎖なので、両方を協調更新すれば通ります。[test_silo_ladder_rung1_evidence.py:1172](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1172) D120もこれを「独立 byte sealではない」と訂正済みです。[decisions.md:5776](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/docs/decisions.md:5776)

M4 は field mismatch、M9 は literal-output漏洩には実際に発火し得るため、恒真ではありません。しかしそれぞれ「独立 checkout取得」「prompt入力非露出」という上位主張は検査しません。独立 literal SHA、in-job command receipt、prompt payload SHAが必要です。

**成果物影響:** 協調更新・receipt複写・semantic copyを検出できず、旧台帳参照または新 artifact の `all_pass` が見かけ上整合したまま誤る。

## nit

### N1. 親 brief の要求数は誤りだが、不足数4は正しい

**自己判定: real。**

承認 scope は `env_tag`、checkout、pin、attestation、between-run floor、schedule、3 armの **7要求**です。[brief.md:5](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/brief.md:5) 表は floorを落として6行にし、「6要求のうち3」と数えています。[brief.md:11](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/brief.md:11) 既存 artifact は pin/attestation/scheduleの3つを満たし、4つ不足なので、[brief.md:27](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/brief.md:27) の「実質差分4点」は requirement gapとして正しいです。

段 2 は実装面が4 editでは済まない点では正しいものの、親は「実装差分4ファイル/4作業」とは書いておらず、そこはやや藁人形です。[s2-plan.md:3](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:3)

**成果物影響:** 段 2 は floorを実装対象に含めているため現時点の値・受理集合への影響なし。6項目表をschema正本にするとfloor欠落を受理する危険だけがある。

### N2. mode2 の概念コードはそのままでは compile不能

**自己判定: real、ただし概念コードなので nit。**

予定コードは `key.empty()/key.back()` を使います。[s2-plan.md:62](/home/SFC/tanab/.claude/jobs/f722c14b/tmp/t139-wave/s2-plan.md:62) 実際の `lockWriteSet()` に `key` 変数はなく、iterator の `(*itr).key_` を使う必要があります。[transaction.cc:145](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/external/ccbench/cc/silo/transaction.cc:145) keyは `WriteElement` の基底に保持されています。[op_element.hh:17](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/external/ccbench/include/op_element.hh:17) YCSB keyは8-byte big-endianなので末尾 parity自体は有効です。[ycsb.hh:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t139-positive-control/external/ccbench/include/ycsb.hh:44)

**成果物影響:** 修正しなければ buildで停止しartifactは生成されない。受理済み値やledgerへの影響はない。

## 総括

### (a) 判定

**NO-GO。** 次を設計へ戻す必要があります。

1. qualification authorityをmanifest自己宣言から分離し、新D・境界テスト・T318準拠の `artifact_role=qualification` を置く。
2. `nm` 対象 binary SHAと各runの`argv0_sha256/target_sha256`を終端結合する。
3. 各PBS jobがcheckoutと実 `/scr` build sourceを独立取得したcommand receiptを持つ。

### (b) BLOCKER 一覧

- B1: 並列 manifestによる未裁定の admission拡張。
- B2: activation witnessと実行 executableのSHA結合欠落。
- B3: measurement checkoutが独立取得でなく複写でも通る。

### (c) provisional案への賛否

- **P1: 条件付き賛成。** 二stripeは実ソース上実装可能で、部分回復候補として妥当。ただし性能順序は未実測。
- **P2: 一部賛成・現案には反対。** 旧 entryを触らない点は正しい。ledger新entryはexact-one contractを壊す。外部宣言は新しい権威境界を裁定・固定してからでなければならない。
- **P3: 賛成。** 既存6 repはbetween-run floorではなく、独立allocationで取り直す必要がある。
- **段2推奨案: 反対。** 旧D120 entryの直接上書きではない点は支持するが、上記3 BLOCKERのため実装へ進めない。
- **親briefの実測:** 「7要求中3充足・4不足」が正しい。「6要求中3」は誤り。

### (d) 確認できなかった前提

- 二stripeが両workloadで `degraded < X < stock` になること。
- 新patchのcompile、nm、verifier、t48 liveness。
- manifest loaderが将来もexact一件固定で、directory discoveryへ広がらないこと。
- checkout/runtime command receiptの実装形。
- T-088側に現在有効な事前承認済み `clean_scan_digest` 期待値が残っているか。
- PBS queue、実割当、他利用者負荷、5 rep×8 sessionの統計的十分性。

read-only静的監査のみです。ホストは `pegasus02` で、pytest・build・benchmark・Pegasus投入は実行しておらず、緑とは報告しません。