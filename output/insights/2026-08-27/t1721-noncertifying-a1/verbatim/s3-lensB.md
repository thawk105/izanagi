結論は、段 2 の A/B 分割はそのままでは着地不能です。単位 A は単独 land できず、投入器契約にも未列挙の述語があり、A+B を実装しても A-1 の有効な成果物まで届かない切断が残ります。

## 検査 1 — 分割順序と scope

### 判定

**単位 A は単独 land 不可。A→B の別 land 分割は誤りです。**

第一に D1028 自体が型と consumer の同一変更単位を要求しています。[decisions.md:35933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/docs/decisions.md:35933) 単位 A だけでは新型の production consumer が存在せず、明示的に禁止された休眠 capability になります。

第二に、A の固定 scope から波及更新先が漏れています。`artifact_admission.py` の bytes は図 provenance の validator SHA として再導出されるため、A が同 file を変えると fig4 の provenance が不一致になります。[fig4 provenance:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.provenance.json:58) [test_s1_9pair_figure_provenance.py:667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/tests/test_s1_9pair_figure_provenance.py:667) A の列挙にこの凍結 provenance 更新がありません。

### 根拠

A の 6 production file のうち、閉包 member は現在 5 本です。

- `ident.py`
- `campaign_lock.py`
- `wal.py`
- `artifact_admission.py`
- `pipeline.py`

`model.py` だけが閉包外です。[campaign_lock.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/campaign_lock.py:29)

特に質問対象の `wal.py` と `pipeline.py` は **2 member の bytes 変更から closure digest 1 個を変更**します。現在の 25-path map を静的再計算した digest は `a14a261280e60a25ca28135695fc80c0bfeee2071922d03da4b7225b65190ab3`、台帳の唯一の行は別 digest `db511c3d...` です。[enforcement_source_ratification.py:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/enforcement_source_ratification.py:89) [ratification ledger:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/hooks/enforcement-source-closure-ratifications.v1.jsonl:1)

固定値として見つかった pin の全数は次です。

| 種別 | 全数 | 根拠 |
|---|---:|---|
| 批准 digest 台帳 | 1 file、1 row | 上記 ledger |
| exact path・role 分割 test | 1 tuple、3 role partition | [test_t671_source_binding.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/tests/test_t671_source_binding.py:23)、[同:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/tests/test_t671_source_binding.py:181) |
| 件数 pin | `25` が 1 assert | [test_artifact_admission.py:1127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/tests/test_artifact_admission.py:1127) |
| role 逐語 pin | test 1 箇所 | [test_artifact_admission.py:995](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/tests/test_artifact_admission.py:995) |
| 図 provenance の scope 逐語 | fig2b 3 件、fig4 4 件 | [fig2b:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/docs/paper-story/figures/fig2b_backoff_sweep_3workload.provenance.json:65)、[fig4:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.provenance.json:40) |
| fig4 validator SHA | 4 件 | [fig4:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.provenance.json:58) |
| 2026-08-24 A-1 の v2 lock map | 3 workload map | [result.json:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/output/insights/2026-08-24_paper-story-a1-paired/result.json:349) |
| 同成果物内の `wal.py` hash | 3 件 | 同 3 lock map |
| 同成果物内の旧 `pipeline.py` hash | result/receipt 合計 11 件 | [receipt.json:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/output/insights/2026-08-24_paper-story-a1-paired/receipt.json:71)、[result.json:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/output/insights/2026-08-24_paper-story-a1-paired/result.json:105) |

旧 A-1 の `pipeline.py` hash は現行 bytes と既に違うため、この成果物は現在も historical な旧 source binding です。A のために凍結値を書き換えてはいけません。

### 成果物への影響

- certified の受理集合は現時点ですでに空です。A 単独 land で件数がさらに減るわけではありませんが、新しい closure も批准されるまで certified lock を作れません。
- 既存 certified campaign ID は、既定 `certified` を identity へ serialize しない設計なら維持できます。非認証 A-1 の 3 ID は新しくなります。
- 2026-08-24 A-1 の測定値は変更禁止です。historical raw として残します。
- fig4 の判定値や画像を変える必要はありませんが、validator SHA を持つ provenance は再生成が必要です。従って A の file scope は不足しています。

## 検査 2 — acquisition receipt 契約

### 判定

**field の個数は揃っていますが、述語表は全数ではありません。また「単一正本」という評価は成立しません。**

実装上の exact field 数は top-level 11、`submit_observation` 6、`qstat_visibility` 5、PBS observation 3 です。[paper_story_a1_paired.py:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:916)

### 根拠

表から落ちている実効述語は次です。

- receipt 自体が canonical absolute path、既存 regular file、非 symlink であること。[paper_story_a1_paired.sh:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/tools/pegasus/paper_story_a1_paired.sh:116)
- open 後の file size を固定し、短縮や size 変更を拒否すること。[paper_story_a1_paired.sh:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/tools/pegasus/paper_story_a1_paired.sh:119)
- duplicate JSON key の拒否と top-level exact key closure。[paper_story_a1_paired.sh:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/tools/pegasus/paper_story_a1_paired.sh:136)
- job 側で receipt 検証時には attempt root がまだ存在しないこと。[paper_story_a1_paired.sh:190](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/tools/pegasus/paper_story_a1_paired.sh:190)
- driver 側では同じ root が real directory、非 symlink、同じ inode であること。[paper_story_a1_paired.py:787](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:787)

`qsub` contract は二重定義です。

- driver validator の `_canonical_qsub_contract()`。[paper_story_a1_paired.py:846](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:846)
- job の embedded Python が同じ variables/options/argv を再実装。[paper_story_a1_paired.sh:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/tools/pegasus/paper_story_a1_paired.sh:214)

段 2 の producer が Python helper を共有しても、job validator を含めれば二重定義のままです。request ID 正規化も同様ですが、現行の意味は一致しています。双方とも whitespace と末尾の全 `.` を落とし、先頭 `0:` を 1 回だけ除去します。[paper_story_a1_paired.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:316) [paper_story_a1_paired.sh:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/tools/pegasus/paper_story_a1_paired.sh:147)

実機面では次の評価です。

- `cd "$REPO_ROOT"` 後の qsub は必須で、段 2 は正しく要求しています。job は `PBS_O_WORKDIR == repo` を exact 比較します。[paper_story_a1_paired.sh:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/tools/pegasus/paper_story_a1_paired.sh:49)
- direct `qsub -v` は既存 sanctioned interface です。[pegasus-runbook.md:1554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/docs/pegasus-runbook.md:1554) `dispatch_compute` の env allowlist 問題はこの直接投入には当たりません。
- ただし `_canonical_qsub_contract()` は `-v` 値の comma/newline delimiter を拒否しません。現行 policy の durable path は安全ですが、contract としては不足しています。[policy:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.v2.json:37)
- `submit_host` を `hostname` と `hostname -f` のどちらから作るかが plan にありません。job は receipt と `PBS_O_HOST` を exact 比較するため、選択を誤ると必ず refuse します。[paper_story_a1_paired.sh:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/tools/pegasus/paper_story_a1_paired.sh:245)

### 成果物への影響

carrier/path/host/cwd のどれかがずれると attempt directory 作成前に job が拒否し、WAL、result、receipt の値は 1 件も増えません。現行固定 path について `qsub -v` の静的な伝播切断は見つかりませんでしたが、実 qsub を行わない scope なので実機動作済みとは判定できません。

## 検査 3 — 休眠 capability の再生産

### 判定

**段 2 の設計どおり実装しても、A-1 の有効な非認証結果まで経路は通りません。少なくとも 3 箇所で切れます。**

### 根拠

1. **非認証 class を A-1 に設定する作業が plan に無い。**

   現在の `campaign_config()` は新しい authority class を設定しません。[paper_story_a1_paired.py:692](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:692) 段 2 の B 実装項目は receipt parser/builder/CLI だけで、campaign config への配線を列挙していません。[s2-plan.md:282](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1721-noncertifying-a1/s2-plan.md:282)

   このままでは A-1 は既定 certified のまま `_capture_current_loader_binding()` に入り、批准 gate で止まります。[ident.py:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/ident.py:234)

2. **新しい terminal stage の最初の reader が未対応。**

   段 2 は非認証 terminal を `STAGE_COMMIT` と別にするとしています。[s2-plan.md:12](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1721-noncertifying-a1/s2-plan.md:12) しかし A-1 の集計器は stage 列を `... bench_done, commit` に固定し、最後が `STAGE_COMMIT` でなければ無効化します。[paper_story_a1_paired.py:1706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:1706) snapshot の評価 stage・terminal 集合も `COMMIT/ABORT` だけです。[同:2120](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:2120)

   B の plan にこの consumer 更新がありません。

3. **scheduler completion receipt の producer と materialize 呼出しが無い。**

   submitter plan は acquisition receipt の発行で終わります。[s2-plan.md:270](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1721-noncertifying-a1/s2-plan.md:270) 一方、materializer は completion receipt の exact 10-field document、配送 stdout/stderr、job-terminal、terminal qstat を必須にします。[paper_story_a1_paired.py:1095](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:1095) `run_materialize()` もその file が無ければ停止します。[同:3312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:3312)

   tracked tree の全数検索では completion schema の producer は 0 件でした。

さらに、campaign 例外は driver が workload error に変換して処理を続け、最終的に raw receipt を書いて rc=0 を返します。[paper_story_a1_paired.py:2551](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:2551) [同:2610](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:2610) そのため「job が終了した」だけでは A-1 が走った証拠にならず、`complete=false` の raw bundle を成功と誤認できます。

最後の tracked reader は materializerで、目的は `formal=false`、`promotion_prohibited=true` の記述的 3-workload report を `output/insights/2026-08-26_paper-story-a1-sized` に公開することです。[paper_story_a1_paired.py:2389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/orchestrator/campaign/paper_story_a1_paired.py:2389) しかしその呼出し手がなく、公開先を読む report consumer もありません。paper-story は現行 study が headline estimand と不一致で、完走しても正式 A-1 を動かさないと明記しています。[2026-08-26.md:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/docs/paper-story/2026-08-26.md:764)

### 成果物への影響

現設計では次のどれかになります。

- 批准 gate で全 workload が止まり、値 0 件。
- 非認証 WAL はできても A-1 collector が新 stage を認識せず `complete=false`。
- raw result はできても completion receipt 不在で materialize 不能。
- materialize できても、既存 paper の certified 選択と headline claim は不変。

有効な実装には、同じ変更単位で「A-1 config への型設定」「新 terminal の collector 対応」「completion receipt producer」「materialize の起動」「非認証結果を限定付き観測として読む report/pointer」が必要です。

## 検査 4 — 正しい終端

### 判定

**(ii) が正しいです。ただし「t1629 が問題を解くまで待つ」のではなく、所有解除後に T-1721 を一体の変更として再設計するための順序待ちです。**

### 根拠

t1629 後は closure が 25 から 27 path へ広がり、新しい署名 receipt verifier 2 本が closure に入ります。[t1629 campaign_lock.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/campaign/campaign_lock.py:27) post-A の `wal.py`、`pipeline.py` 等を含む map は、signed receipt の exact digest/path と一致しなければ certified 側で拒否されます。[ratification receipt:1016](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/orchestrator/campaign/enforcement_source_ratification_receipt.py:1016)

これは A の schema/consumer 編集を不可能にはしません。ただし certified lane の正例を動かすには、A land 後の 27-path closure について broker receipt が別途必要です。非認証 lane は D1070 によりこの gate の対象外に保つ必要があります。[decisions.md:36725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1721-noncertifying-a1/docs/decisions.md:36725)

また t1629 は現在、信頼根と receipt ledger が未 bootstrap で受理集合が空です。[t1629 README:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/output/insights/2026-08-27_t1629-ratification-broker/README.md:22) land 自体も非帰属赤 1 件で停止中です。[同:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1629-ratification-broker/output/insights/2026-08-27_t1629-ratification-broker/README.md:85)

D1028 が却下したのは「D905 の着地を解決策として待つだけ」です。今回は t1629 の所有 file を同時編集できないための順序制約であり、land 後に非認証型を省略する判断ではありません。従って射程外です。

- (i) はまだ早いです。所有解除後にも 4 層固定が不可能だという証拠はありません。
- (iii) は成立しません。投入器だけは D1028 違反、型の一部だけは D1038 の 4 層条件未達、provenance は最終 hash 未確定のため先行更新できません。

正しい再開形は、t1629 後の実 tree を再列挙し、旧 A/B を別 land にせず、型、A-1 配線、submit lifecycle、materializer、最終 reader、波及 provenance を 1 land 単位にまとめることです。

静的読取だけを行いました。Web 検索、pytest、書き込みは行っておらず、検査結果を緑とは報告していません。

## 総括

**(ii) t1629 の land と所有解除を待ち、旧分割を捨てて型から最終 reader までを同一 scope でやり直す。**