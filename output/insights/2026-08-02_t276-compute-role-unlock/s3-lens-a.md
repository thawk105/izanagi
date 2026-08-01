判定は **NO-GO** です。必読資料と関連実装を read-only で確認しました。pytest・接続試験は実施しておらず、緑・赤は主張しません。

### 所見 1 — 「既定 TLS trust root」は証明されず、既知の T-242 を踏み越えている

深刻度: **BLOCKER**

根拠: 親 brief は「2 key 以外を渡さないので trust root は既定」と断定しますが、`PATH` と `HOME` 自体は allowlist に残ります。[brief.md:50](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/brief.md:50)、[s8b_prediction_runner.py:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/s8b_prediction_runner.py:71)。主実行体は親 process の `PATH` から選び、bytes を hash するだけで承認値とは比較しません。[claude_projected_provider.py:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:112)、[claude_projected_provider.py:121](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:121)。この欠陥は既に T-242 として記録済みです。[decisions.md:4799](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:4799)、[decisions.md:4806](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:4806)。

`NODE_OPTIONS` や `NODE_EXTRA_CA_CERTS` のような純粋な env 経路は、再構築された child env に入らない限り遮断されます。ここは P3 の正しい部分です。しかし、`HOME` 配下の認証・設定、`PATH` 選択時の実行体差替え、実行体自身の CA mode、system CA、hash 後から exec までの差替えは別です。指定 probe も実行体の path しか記録しておらず、版・hash・TLS mode を束縛していません。[probe-out.txt:16](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-probe/probe-out.txt:16)。本レビュー時点の実体は native ELF の Claude Code 2.1.220 であり、外部 `node` wrapper ではありません。したがって npm/Node env の列挙だけで trust root を尽くしたとも言えません。

成果物への影響: 差し替えられた実行体は正しい形の envelope を偽造でき、`claude_executable_sha256` が未知値でも拒否されません。T-276 単独では role attempt・report が汚染され、T-277 後はその出力が variant、WAL、certified 候補へ到達します。

推奨対応: **T-242 を T-276 の前提にするか同 wave へ明示的に統合**してください。承認済み executable digest/signature、所有者・mode、起動直前の再照合、固定または credential-only HOME、最小固定 PATH が必要です。現 CLI で利用可能な `--safe-mode` と明示的な global `--tools ""` も防御層にできますが、CLI 版を pin した上で意味を検査すべきです。これをしないなら P3 は「列挙 env override を forward しない」までに狭め、MITM 閉鎖を主張してはいけません。

### 所見 2 — endpoint/policy pin は自己整合検査であり、proxy の真正性を pin していない

深刻度: **BLOCKER**

根拠: plan の policy SHA と endpoint SHA は、同じ policy file と source env から作られます。[plan.md:107](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:107)、[plan.md:131](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:131)。registry は正本上も「所在 inventory」であり、run を支配した設定の認証元ではありません。[decisions.md:5420](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:5420)。テストは tracked/regular/閉集合を確認しますが、runtime の clean checkout や承認 Git blob を強制しません。[test_pegasus_policy_registry.py:370](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_pegasus_policy_registry.py:370)。production CLI が確認する clean tree は CCBench 側だけです。[p3_autonomous_workload_trial.py:1120](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1120)。

脅威モデル別の判定は次のとおりです。

- remote proxy だけが攻撃者なら、exact env 値は「別 proxy への差替え」を防ぎます。しかし固定 IP:port のサービス自体が侵害された場合はそのまま受理します。
- 同一 UID、未監査 checkout、profile/supply-chain が攻撃面なら、policy と env の双方を合わせられるため検査は無意味です。現物 policy directory と CLI binary は同じ利用者の書込み権限下です。
- ネットワーク上の実 peer、CONNECT 結果、証明書 chain、応答 origin は receipt に入りません。plan 自身もこれを認めています。[plan.md:224](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:224)、[plan.md:228](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:228)。

成果物への影響: 自己整合した攻撃者 proxy を正規 transport として記録し、異なる実 route・証明書 chain・応答 origin の行を同じ mode として扱います。endpoint/policy SHA は正確な設定履歴にはなりますが、certified 選択やレポートの真正性を保証しません。

推奨対応: policy の権威を明記し、runtime bytes を独立した承認 Git blob/digest、署名済み manifest、または管理者所有 policy と照合してください。MITM を本当に閉じるなら TLS/SPKI pin、固定 bundled CA、または信頼済み proxy attestation が必要です。固定 proxy 自体を信頼する裁定へ変える場合は、「攻撃者制御 proxy を閉じた」というユーザー裁定を再度取り直す必要があります。

### 所見 3 — valid JSON injection は coder code と auditor 判定へ到達する

深刻度: **BLOCKER**

根拠: `tools=[]` は model の tool surface を縮めますが、model 出力の意味を安全化しません。[claude_projected_provider.py:137](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/claude_projected_provider.py:137)。coder parser は exact key と物理一行を要求するだけで、C++ 式の文法・副作用・call を制限しません。[p3_autonomous_workload_trial.py:261](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:261)。その文字列は preview、proposal、authoritative driver へ渡ります。[p3_autonomous_workload_trial.py:843](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:843)、[p3_autonomous_workload_trial.py:923](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:923)。

DiffQuarantine は自ら「C++ 意味論の完全性を担わない」「auditor + 規律6が担う」と明記しています。[diff_quarantine.py:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/diff_quarantine.py:14)。機械 syntax gate は 5 識別子の grep に限られます。[axis_trigger_gating.py:53](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/axis_trigger_gating.py:53)。一方 auditor は coder と同じ外部 transport を通り、payload に既に入っている `diff_digest` を echo して `verdict="pass"`・空 violations を返せば schema を通ります。[p3_autonomous_workload_trial.py:897](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:897)、[auditor_gate.py:105](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/auditor_gate.py:105)。通過後は build/run されます。[p3_s4_loop_trigger_gating.py:406](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_s4_loop_trigger_gating.py:406)。

成果物への影響: 攻撃者は malformed JSON を使う必要がありません。valid schema の一行 C++ と虚偽 auditor pass を組み合わせられます。verifier は serializability を守りますが、任意副作用・host I/O・verifier blind spot の全てを検査するものではありません。[pipeline.py:697](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/pipeline.py:697)。試行台帳には攻撃文字列が `status=valid` として入り、T-277 後には不正な COMMIT/fitness、または検証前の side effect が生じ得ます。これは規律6の「外部入力はデータ」に反します。[CLAUDE.md:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/CLAUDE.md:86)。

推奨対応: coder 出力を exact な boolean-expression AST/DSL に落とし、許可する識別子・enum・論理演算だけを whitelist してください。call、追加代入、comma expression、文字列、cast、副作用は機械拒否が必要です。さらに build/run は credentialless UID、network 無し、限定 filesystem の sandbox へ置くべきです。同一 transport の auditor を唯一の意味 gate に数えてはいけません。

### 所見 4 — transport receipt が成功応答にしか付かず、失敗行の provenance は依然欠ける

深刻度: **BLOCKER**

根拠: brief は「各 role 行が transport identity を持つ」とします。[brief.md:63](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/brief.md:63)。しかし `_invoke()` は provider/envelope/parser のどこかで例外になると、payload/envelope artifact だけを残し、response provenance を捨てます。[p3_autonomous_workload_trial.py:573](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:573)。provenance が台帳へ入るのは valid branch だけです。[p3_autonomous_workload_trial.py:590](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:590)。provider 初期化失敗も型と文言だけです。[p3_autonomous_workload_trial.py:1043](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1043)。plan もこの残余を明記しています。[plan.md:231](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:231)。

成果物への影響: transport は成功したが model schema が不正だった場合さえ、入手済み receipt が消えます。proxy 遮断、TLS failure、改変応答、純粋な model schema failure が同じ `role-invalid`/`provider-init-error` に寄り、試行台帳と report の原因・transport identity が欠落します。今回直すはずの `planner-invalid` 誤帰属を完全には閉じません。

推奨対応: admission を role provider ごとではなく run 開始時に一度確定し、run header と全 attempt に付けてください。valid、invalid、provider-init-error、timeout、nonzero rc の全てへ同じ immutable receipt を記録し、エラー分類を transport/envelope/role-schema に分離する必要があります。

### 所見 5 — production CLI の opt-in 欠落は T-276 内。T-236 ではない

深刻度: **BLOCKER**

根拠: plan の指摘どおり production caller は opt-in を渡しません。[plan.md:9](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:9)。4 provider の生成箇所には現状その入力がなく、CLI にも transport flag がありません。[p3_autonomous_workload_trial.py:628](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:628)、[p3_autonomous_workload_trial.py:1094](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1094)、[p3_autonomous_workload_trial.py:1136](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_autonomous_workload_trial.py:1136)。

**判定: CLI flag と production caller 配線は T-276 の scope に入れるべきです。** T-236 は login/compute を分割する新 `campaign` dispatch task と domain result 契約です。[decisions.md:4955](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:4955)、[decisions.md:4972](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/decisions.md:4972)。同一計算ノード process 内で既存 provider に明示 flag を渡す作業は、dispatcher・task enum・network 分割のいずれにも触れません。

成果物への影響: plan のままなら direct API の test だけが admission を発火させられ、文書化された `--provider claude-headless` は引き続き proxy を落とします。実 CLI の report は従来どおり partial/`planner-invalid` になり、role receipt も certified 候補も増えません。「計算ノード role 実行を解禁した」という受入判定が非 load-bearing になります。

推奨対応: `--allow-pegasus-compute-transport` のような明示 flagを CLI→`run_trial()`→`_provider_set()`→4 provider へ配線し、未指定・LOGIN・SUSPECT・OTHER・COMPUTE+flag の production 経路境界を固定してください。runbook §3.2/§3.3 も同じ変更単位で更新すべきです。

### 所見 6 — SUSPECT/OTHER は閉じるが、`bnode[0-9]+` の偽陽性は fail-open

深刻度: **MAJOR**

根拠: plan は `current_site() == PEGASUS_COMPUTE` の exact 比較を行うため、実際に SUSPECT/OTHER が返れば拒否方向です。[plan.md:46](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/plan.md:46)。しかし分類器は `bnode[0-9]+` なら NQSV・PBS・FQDN・allocation 証拠なしで COMPUTE を返します。[site_policy.py:29](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/site_policy.py:29)、[site_policy.py:39](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/site_policy.py:39)。この挙動はテストで意図的に固定されています。[test_site_policy.py:59](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/tests/test_site_policy.py:59)。

成果物への影響: container/UTS namespace、別 site、侵害された launcher が hostname を `bnodeNN` にできれば、同じ proxy pair を持つだけで receipt の `site=PEGASUS_COMPUTE` が偽になります。試行台帳・report の site 帰属が変わり、後続 T-277 と結合した場合は別環境の測定・certified 行が Pegasus 行へ混入します。

推奨対応: `site_policy.current_site()` を security attestation と扱わず、scheduler 発行の job receipt、allocation identity、policy-bound host identity の独立 witness を transport admission に追加してください。global site classifier の変更が T-277 と競合するなら、T-276 の transport 専用 predicate として裁定パッケージ化すべきです。

### 所見 7 — probe は必要性を示すが、ノード族・profile・将来 route を証明しない

深刻度: **MAJOR**

根拠: 指定生出力が直接示すのは bnode009・単一時刻・lowercase 2 値・A成功/B失敗だけです。[probe-out.txt:2](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-probe/probe-out.txt:2)、[probe-out.txt:3](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-probe/probe-out.txt:3)、[probe-out.txt:5](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-probe/probe-out.txt:5)、[probe-out.txt:18](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-probe/probe-out.txt:18)、[probe-out.txt:22](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-probe/probe-out.txt:22)。過去記録には bnode002/bnode145 の追加観測がありますが、同一 node の before/after ではなかったことも明記されています。[worklog-phase3-0801-96.md:18](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/archive/worklog-phase3-0801-96.md:18)、[worklog-phase3-0801-96.md:38](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/archive/worklog-phase3-0801-96.md:38)。runbook 自身も command/node/profile ごとの一般化を禁じます。[pegasus-runbook.md:398](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/pegasus-runbook.md:398)。

計画は proxy key/value drift については fail-closed です。別 key、片側欠落、別 endpoint は拒否されます。一方、同じ 2 値のまま CLI binary、HOME、system CA、proxy backend、network route、profile が変わる場合は静かに受理されます。

成果物への影響: endpoint/config SHA が同じでも実 transport の安全性や origin が異なる行を同一 mode として report・attempts に混載します。将来 node での legitimate endpoint 変更は安全側の停止になりますが、同値のままの trust drift は検出されません。

推奨対応: 主張を「観測済み allocation/profile の設定 pair」に限定し、CLI digest、CA mode、profile/revision、node/job receipt、可能なら実 peer/証明書情報を qualification identity に加えてください。これらが変われば再 qualification を要求すべきです。

### 所見 8 — 現 brief は旧虚偽を繰り返してはいないが、能力純増の会計が不足している

深刻度: **MAJOR**

根拠: (96) では「能力は 1 bit も増やさない」が明示的に撤回されています。[worklog-phase3-0801-96.md:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/archive/worklog-phase3-0801-96.md:35)。今回の brief はその文言を再掲せず、role 行と report が変わることは認めています。[brief.md:59](/home/SFC/tanab/.claude/jobs/acef4d0f/tmp/t276-wave/brief.md:59)。したがって同じ虚偽の再発ではありません。ただし、増える能力を transport receipt の追加としてしか数えていません。

純増は次です。

- OS 上の手動 proxy 到達能力は既に存在したが、izanagi の sanctioned provider がそれを使用し、外部応答を受理する能力が新設される。
- workload descriptor、metrics、working diff、harness digest が compute node から外部へ出る。
- proxy は接続先・時刻・量を観測し、遮断・遅延できる。TLS root が破れれば内容も改変できる。
- shared `HOME` の認証情報を compute node 上の CLI が使用する。
- 外部 coder/auditor の出力がローカル code/harness の制御入力になる。
- API 課金、availability、telemetry、credential misuse の損失面が増える。
- 反対に、s8b provider、generation budget、T-277 の measurement admission、T-236 dispatcher、tool allowlist はこの wave だけでは増えない。

成果物への影響: T-276 単独では主に role attempt・report・費用が変わります。certified 選択の変化は T-277 の measurement gate 解禁後に初めて発火します。[p3_s4_loop_trigger_gating.py:277](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/orchestrator/campaign/p3_s4_loop_trigger_gating.py:277)。

推奨対応: 新 D に「host capability ではなく sanctioned application capability の純増」であること、外部へ出る field、credential 境界、proxy の観測・妨害能力、T-277 後に code execution/certification まで伸びることを明記してください。

### 所見 9 — 新 gate の全層閉包が不足している

深刻度: **MAJOR**

根拠:

| 層 | plan の状態 | 判定 |
|---|---|---|
| policy file / registry | 新設 | registry は inventory であり認証 root ではない |
| site classification | leaf が確認 | hostname 偽陽性が残る |
| provider API | opt-in を追加 | ここだけは発火可能 |
| production CLI/caller | 配線なし | **T-276 内の欠落** |
| child subprocess env | 5+2 key exact | env-only override は閉じるが HOME/PATH/binary trust は未閉鎖 |
| envelope/schema | 既存検査 | shape は閉じるが valid-schema semantic injection は通る |
| success provenance | receipt 追加 | generic copyで attempts/report へ届く |
| invalid/init provenance | 追加なし | **transport identity が消える** |
| compute build/certification | T-277 で拒否中 | T-276 だけで live pilot 完遂とは言えない |
| s8b `ClaudeHeadlessProvider` | 明示 scope 外 | compute transport は解禁されない。凍結非波及の説明は正直 |
| `s6_proposal_rounds.py` / daemon | T-278 | transport 契約は非対称のまま。[worklog-phase3-0801-96.md:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t276-compute-role/docs/archive/worklog-phase3-0801-96.md:71) |
| `dispatch_compute.py campaign` | T-236 | 凍結済みのまま触らないのが正しい |
| direct trigger-gating driver | role provider を呼ばない | T-276 の保証対象ではない |

成果物への影響: 現 scope のまま「計算ノードの Claude/role transport を解禁」と広く記録すると、実際には direct provider API の success 行だけが新保証を持ち、CLI、失敗行、別 provider、live measurement は未解禁・未帰属のままです。

推奨対応:

- T-276 に production CLI flag、4 role caller、全 outcome receipt、run-level admission を入れる。
- T-242 の executable/TLS trust root を前提化する。
- valid-schema code injection の grammar/sandbox は新裁定パッケージにし、悪意 proxy を脅威に含める限り解禁前 blocker とする。
- T-277 は measurement/site/build identity として別のまま維持する。
- T-278 は他 caller の transport 非対称を引き続き別 task とする。
- T-236 の dispatch task は本変更へ混ぜない。

## 総括

**NO-GO**

最重要 3 件:

1. CLI binary・HOME・system CA・proxy peer の独立 trust root がなく、既知の T-242 未解決のまま「MITM 閉鎖」を主張している。
2. `tools=[]` と JSON schema は valid-schema injection を止めず、同じ transport の coder code と auditor pass が build/certification 境界へ到達する。
3. production CLI が opt-in を渡さず、invalid/init attempt に receipt も残らないため、「role 実行解禁」と「試行台帳の transport 帰属」の双方が未達である。