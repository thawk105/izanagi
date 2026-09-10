静的監査のみ。実装変更・pytest・新規実測は行っていない。

## 敵対所見

### 1. Proxy allowlist は「6 key 分」ではなく、無制約な外部制御面を開く

現行は base 5 key だけだが、案は proxy 6 key の**任意文字列値**をそのまま `subprocess.run(env=...)` へ渡す。scheme・host・port・資格情報・site・信頼済み proxy かを一切束縛しない。[plan:28-55](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/s2-plan.md:28) [runner:1089-1150](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1089) [projected:154-205](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:154)

HTTPS では logical API origin が即座に変わるとは限らないが、TCP peer は env 指定 proxy へ変わる。`NO_PROXY=*` 等は逆に監査 proxy を迂回して direct 接続へ戻す。したがって「transport のみ」は隔離契約の一部を変えた事実の言い換えにすぎない。

**扱い・成果物影響:** **real**（brief の「能力は 1 bit も増えない」は **refuted**）。role 呼出しの受理集合が「base env」から「env が指定する任意 proxy/bypass policy」へ広がり、8b の `status/choice_id/rationale`、8c の role validity・proposal・report・台帳参照が変わる。

### 2. 攻撃者 proxy からの MITM／prompt injection 経路が開く

具体的な破断筋は次である。

1. PBS/job profile 等へ攻撃者制御の `https_proxy` を入れる。
2. plan の projection が無検査で role process へ渡す。
3. proxy は常に遮断・遅延・接続先メタデータ観測ができる。さらに CLI が信頼する CA で TLS interception できる proxy なら、送信 prompt/payload または応答を改変できる。
4. 攻撃者は selector の合法な `choice_id`、coder の一行 predicate、auditor の一致する `diff_digest` と `pass` 等、strict schema を満たす内容を返す。
5. 検査は JSON shape、Opus prefix、非空 session、正 token、server-tool count=0 を見るだけで、応答 origin の署名・endpoint pin はない。[projected:221-289](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:221)

これは外部入力を out-of-band の「指示」に昇格させる経路であり、規律 6 の信頼境界に正面衝突する。[CLAUDE.md:86-89](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/CLAUDE.md:86)

**扱い・成果物影響:** **real**。TLS interception が無くても report/台帳の `invalid`、経過時間、artifact SHA が変わる。成立すれば 8b の凍結 selector choice と combined verdict、8c の coder/auditor/critic 出力・proposal・harness 入力が攻撃者選択へ変わる。後段 correctness gate は残るが、候補選択と証拠参照は既に汚染される。

### 3. key-only provenance は 8b resume で異なる proxy 値を一つの run に混載できる

plan は header に key 名だけを記録し、値も hash も捨てる。[plan:57-82](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/s2-plan.md:57) これにより次が成立する。

1. proxy A を設定して seal。header と claim、error envelope までは durable 化される。
2. CLI nonzero で invocation は書かれない。[runner:1145-1172](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:1145)
3. 同じ key 名・別値の proxy B で resume。header/binding は key 集合が同じなので通る。
4. `claimed_missing` は再試行されず、残セルだけ B 経由で実行される。[runner:823-865](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:823)
5. 凍結 row は最初のセルを `missing`、残りを resolved として正規化するが、A/B の差は消える。[runner:905-961](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_prediction_runner.py:905)

raw 値を残さないことは資格情報秘匿には効く。一方 SHA-256 も低 entropy の host:port なら辞書照合でき、安定相関子になるため安全とは言えない。しかし key-only は run identity として明白に不足する。

**扱い・成果物影響:** **real**。単一 journal/freeze が複数 transport 値を同一 provenance として受理する。`missing` による `choice_id=null` は selector 条件を `INDETERMINATE` に変え、残セルの choice は別 proxy 由来になりうる。[s8b_verdict.py:621-659](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_verdict.py:621)

### 4. 凍結 row から transport を落とすことで proof chain が分裂する

plan は transport を `agent_provenance` に入れず、journal header だけへ逃がす。[plan:103-110](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/s2-plan.md:103) しかし凍結側の exact provenance は現在 8 fieldだけで、公式 consumer は invocation receipt と凍結 row を完全一致させている。[selector_freeze:88-91](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_selector_freeze.py:88) [ratified_freeze:2659-2673](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/s8b_ratified_freeze.py:2659)

後日証明できなくなるものは以下である。

- `selector_predictions.json` 単体から、どの transport key/value/route で各 choice が生成されたか。
- 全セルが同じ proxy 値を使ったこと。
- `NO_PROXY` や大小文字競合の結果、実際にどの経路が選ばれたか。
- 同じ凍結 row を再現する運転環境が同値だったこと。

さらに plan は journal validator の受理 schema を v1 から `{v1,v2}` へ拡張する一方、prediction freeze は v1 のままにする。[plan:84-110](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/s2-plan.md:84) 現行 frozen journal は bytes pin 済みである。[test_frozen_artifacts.py:57-68](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/tests/test_frozen_artifacts.py:57)

**扱い・成果物影響:** **real**。現行 certified bytes は直ちには変わらないが、公式 journal のコード上の受理集合は v1→v1/v2 に拡張される。将来の certified row/body SHA は transport を含まず、journal 参照を失った consumer は key 名すら証明不能になる。brief に `DW-O09` の live/frozen/history 分類がなく、段 1 の不変条件も未成立である。

### 5. 8c は同じ v1 schema のまま「transport 有／無」の両方を受理する

8c の `AttemptJournal` は exact schema を持たず、plan は report/payload schema version を bump しない。[trial:370-397](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/p3_autonomous_workload_trial.py:370) [plan:125-141](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/s2-plan.md:125)

さらに `getattr(provider, "transport_env_keys", ())` は、未計装 custom provider を「transport key なし」に偽装する。`run_trial()` は programmatic に任意 provider mapping を受け、報告上の `provider_kind` と実 provider を照合しない。[trial:841-901](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/p3_autonomous_workload_trial.py:841)

**扱い・成果物影響:** **real**。同じ `p3-autonomous-workload-trial-report/v1` が field 欠落・空 list・実 proxy list をすべて表せる。レポート/台帳の受理集合が曖昧化し、`transport_env_keys=[]` から「proxy 未使用」と「未計装 provider」を区別できない。8c は正式 certified 選択ではないが、report と build-mode campaign 記録の provenance が偽になりうる。

### 6. 「transport だけ」は実挙動について実測で反証されている

| 面 | コード上の実態 |
|---|---|
| timeout | outer timeout 定数は 1200 秒のままだが、親実測は proxy 有 3 秒、無 172 秒。挙動は既に変わっている。[reach3.txt:8-17](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/t241_reach_out/0_876529.nqsv/reach3.txt:8) |
| retry | supervisor の `attempt=1/retry=false` は不変。一方、単一 CLI 内の HTTP retry/backoff を無効化・記録するコードはない。172 秒の内訳も証明不能。 |
| token | 成功時は正 token を要求するが値を provenance へ保存しない。[projected:239-289](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/claude_projected_provider.py:239) transport 断では zero、開通後は課金 token が発生する。 |
| session id | endpoint 由来の非空値を受理し、重複拒否は provider instance 内だけ。4 role 横断では拒否しない。 |
| server tool | `tools=[]` は argv 構成。server tool は実行後 envelope の自己申告 counterを検査するだけで、非実行の事前証明ではない。MITM は zero を偽装できる。 |
| provenance | invalid attempt は session/model/token/CLI provenance を落とし、追加予定の key 名だけが残る。[trial:523-571](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/orchestrator/campaign/p3_autonomous_workload_trial.py:523) |

**扱い・成果物影響:** **real**。supervisor-level retry不変という狭い主張だけは **refuted attack**。それ以外は role status、経過時間、session/model、token/cost、report completeness、attempt journal SHA を変えるため、「transport 以外の成果物値は不変」は成立しない。

### 7. bnode002・lowercase 2 key から 6 key/global への一般化に根拠がない

親実測が示したのは bnode002、Claude CLI 2.1.220、非空の lowercase `http_proxy/https_proxy` だけである。[reach.txt:1-14](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/t241_reach_out/0_876527.nqsv/reach.txt:1) [reach3.txt:1-17](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/t241_reach_out/0_876529.nqsv/reach3.txt:1)

- TEST C は uppercase を**空文字で人工的に追加**しただけで、非空 uppercase や競合優先順位を測っていない。[t241_reach3.sh:25-30](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/t241_reach3.sh:25)
- `no_proxy/NO_PROXY` は未測定。値次第で必須 proxy を迂回し、Pegasus では direct DNS failureへ戻る。
- bnode145 の対照は proxy 名 2 件を数えただけで、proxy 経由の成功を測っていない。[context.txt:1-8](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/before/0_876813.nqsv/context.txt:1)
- 現 frozen selector は CLI 2.1.218 を記録しており、測定版とも違う。[journal.jsonl:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/s8b-freeze/selector-runs/journal.jsonl:1)
- plan が除外する `ALL_PROXY` を実 CLI が認識しない根拠もない。
- P1 が引用する worklog (93) は、site 固有値を trusted `env_contract` へ寄せ、production override を開かなかった記録である。任意 `os.environ` を全 site で通す根拠とは逆向きである。[worklog:934-952](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/worklog.md:934)

fake runner の exact env テストは Python が渡した mapping は証明するが、HTTP stack の大小文字優先順位・`no_proxy` 解釈・実効 route は一切通らない。S2 live も source env に存在する lowercase 2 key しか実証せず、8b provider/freeze 経路は live 対象外である。[plan:178-199](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/s2-plan.md:178)

**扱い・成果物影響:** **real** `[誤前提][テスト代表性][防壁の射程誤認]`。node/profile/CLI版によって12件 valid と3件 planner-invalidが入れ替わり、同じ `transport_env_keys` を持つ report の `status/outcome/attempt_journal_sha256` が変わる。6 key の受理集合を通したという証拠にはならない。

### 8. S2 は現行の sanctioned location 契約に反する

現 runbook は計算ノードで `claude -p` を起動しないと明記し、D108 も LLM 4役を login 側に置くと決定している。[Pegasus runbook:390-393](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/pegasus-runbook.md:390) [同:415-418](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/pegasus-runbook.md:415) [D108:4944-4959](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/docs/decisions.md:4944)

brief はその決定前提を覆す新事実を認識しつつ、S2 で直ちに compute-side role 実走を命じる。S3 は §7.1 の訂正しか scope に書かず、§8 checklist と D108 の location 境界を残す。plan も Pegasus 修正を自分の計画外へ置いた。[brief:38-49](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:38) [plan:143-149](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/s2-plan.md:143)

**扱い・成果物影響:** **real**。このままの S2 report は現行運用契約が拒否する経路で生成され、sanctioned acceptance evidence としての参照資格がない。runbook と decision の参照先が分裂し、後続台帳は同じ compute role 実走を合法・禁止の両方として読める。

## brief 行別攻撃

| 対象 | 判定 | real/refuted と成果物影響 |
|---|---|---|
| 不変条件 [53-54](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:53) | 自己反証 | **real／対象主張 refuted**。tools/MCP/argv の静的構成不変だけは真だが、外部到達能力と env 制御入力は増える。role validity、choice、report が変わる。 |
| 不変条件 [55-56](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:55) | 射程誤認 | **real**。exact test が証明するのは Python env の key 集合だけ。「proxy 分だけ」の実効受理集合ではない。同じ key list で良性・悪性・空値・bypass が受理される。 |
| 不変条件 [57](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:57) | 規範文 | **refuted／nit**。login で重処理しない規律自体への攻撃は成立しない。成果物値への直接影響なし。 |
| 不変条件 [58](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:58) | 所有規律 | **refuted／nit**。author 所有は正しいが、transport の安全性証拠ではない。成果物値への直接影響なし。 |
| P1 [71-73](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:71) | 一般化不能 | **real**。測った2 lowercaseから6 key/globalへ飛躍。role受理集合、report status、proxy迂回可否が全siteで変わる。 |
| P2 [74-75](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:74) | provenance 不足 | **real**。raw値は秘匿上危険、SHAも相関・辞書照合器、key-onlyは値差を消す。freeze/report が異なる route を同一 provenance として扱う。 |
| P3 [76-79](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:76) | 検出力過大表現 | **real**。4 vector は projection 形状を検査するだけ。大小文字競合、`no_proxy`、値変更 resume、CLI 消費を殺さない。誤った transport provenance を受理する。 |
| P4 [80-81](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:80) | 手続宣言 | **refuted／nit**。軽量版にしない判断は事実だが、防壁そのものではない。成果物値への直接影響なし。 |
| DW-G05 S1 [62-65](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:62) | 実測反証 | **real／対象主張 refuted**。実対照は12件でなく planner 3件だけが invalid。8b は nonzero で invocation 前に落ち `role-invalid` でなく `claimed_missing` になる。report の role件数/statusと凍結 row が記述と違う。[attempts.jsonl:2-4](/home/SFC/tanab/.claude/jobs/dcb1a3a9/tmp/wave-t241/before/0_876813.nqsv/run/attempts.jsonl:2) |
| DW-G05 S3 [66-67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:66) | 真だが不足 | **real**。D108 の誤前提が残るという影響は真。しかし §7.1 だけ直しても checklist/D108 参照は残り、S2 report の受理資格が矛盾する。 |
| DW-G05 欠落 [38-43](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t241-abc-pilot/output/insights/2026-08-01_t241-compute-llm-transport/s1-brief.md:38) | S2/S4 の影響行なし | **real**。S2を放置すると6-key一般化・8b経路が未証明のまま、S4を放置するとT-241残余の台帳参照が消える。brief は DW-G05 を S1/S3 にしか適用していない。 |

## 総括

- 最重は、攻撃者制御 proxy 値を無検査で role process の外部制御面に昇格させ、条件付きで MITM／prompt injection を成立させる点。
- 次点は、key-only provenance により 8b resume が異なる proxy 値を同一 journal/freeze に混載でき、凍結 row からその事実が消える点。
- 3件目は、bnode002・lowercase 2 key の実測を6 key・全siteへ一般化し、8c no-build の自己整合検査だけで8b/official proof chainまで安全と扱う点。