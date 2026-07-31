指定6資料と段3契約はすべて読了しました。read-only の静的検分のみで、編集・pytest・runner・mutation は実行していません。

判定は、現 brief / plan のままでは **NO-GO**。以下の must-fix を段4で事前登録し直した場合に限る **条件付き GO** です。

## 段1「前提実測」1〜8の検分

| # | severity / real-refuted | 実測が支える範囲と過大一般化 | 成果物影響 | 最小是正 |
|---:|---|---|---|---|
| 1 | MEDIUM / prompt 抽出は real、入力再現可能性は refuted | 2本の rollout と各 user message の復元は成立する。ただし復元できるのは user message であり、system/world state、AGENTS、skill、実際に追加で読んだファイル、環境ではない。[brief:13](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:13) | insight が「歴史 run の再現」と誤記される。新しい両 arm 間の prompt 同一性は別途成立しうる。 | 「歴史 prompt 由来の新規 benchmark」と呼び、歴史 session 完全再現とは呼ばない。 |
| 2 | MEDIUM / logged effort は real、backend compute の証明は refuted | `turn_context.payload.effort=max` は実効設定として記録されたことを示すが、backend がその計算量を実行した独立 attestation ではない。ledger が field を読むことも意味論の独立証明ではない。[brief:15](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:15) | T-184 が「実際の reasoning 強度」を断定しうる。 | `recorded effective effort` と表記し、全 turn_context の一致を gate。model/build ID が取得不能ならその限界を明記する。 |
| 3 | MEDIUM / 歴史値は real、費用予測は refuted | 28/320,640、71/498,984、819,624 は当該2 run の記述値。ledger の一致は同じ rollout の再集計であり独立反復ではない。`model_calls` も backend call 数ではなく非null `token_count` event 件数。[ledger:69](/home/SFC/tanab/github/izanagi/output/insights/2026-07-29_t179-worker-ledger-verbatim/README.md:69) | `≈320k×6` や20〜30分という費用見積り、一般的節約率を証拠扱いできない。plan は逐次実行なので brief の並列 wall-clock 予測とも不整合。 | 新runの全値・median・rangeを記述し、歴史値は予算目安に限定する。 |
| 4 | CRITICAL / 2ファイルの逆構成は real、fix1入力全体の再構成は refuted | fix2 patch の逆適用が構成的に pin できるのは後述の2ファイルだけ。「`9b26b3b` から逆適用すればfix1状態」は9入力全体、untracked closure、world stateを証明しない。[brief:19](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:19) | 「同一の歴史入力」という proof chain が成立せず、T-184 が歴史 max の再現性として引用できない。 | 新規 benchmark として再定義し、独立にR-1 ground truthを再裁定する。 |
| 5 | CRITICAL / 長さ一致だけ real、driftなしは refuted | 8,832一致が証明するのは、1パスの2観測で長さが同じことだけ。内容、hash、mode、symlink、改行、他8入力は証明しない。[brief:22](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:22) | snapshot identity の中核主張が偽になる。 | 当時採取のdigestがなければ、歴史byte一致を撤回する。後付けSHAは再構成物のpinにだけ使う。 |
| 6 | LOW / live worktree の現時点driftは real | `tools/check_docs.py +239` は live worktree を使わない理由として十分。ただし完全な歴史 snapshot が回復できることは示さない。[brief:24](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:24) | live tree混用を防ぐ点は正しい。過大なのは回復可能性への飛躍だけ。 | 「live tree不採用」と「歴史再現可能」を分離する。 |
| 7 | MEDIUM / CLI・alias実在は real、将来同一性は refuted | CLI 0.146.0 と model alias の実績、output checker の存在は実走可能性を示すだけ。checker は出力構造を検査し、科学的妥当性や内容正解を保証しない。[brief:27](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:27) | checker rc=0を品質不変の証拠へ昇格させる危険。 | CLI binary hash、config、turn contextをpinし、checkerをformat gateとだけ呼ぶ。 |
| 8 | MEDIUM / 専用回帰不足は plausible、網羅証明と「検出力2点だけ」は refuted | literal `reasoning` のgrepは間接fixture、他directory、config-driven testを排除しない。また新toolはsnapshot/session/scorer等も検査するため「純増2点だけ」とも整合しない。[brief:28](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:28) | unit test緑が推論品質の証拠と誤認される。 | plumbing検出力とlive A/Bの品質証拠を分けて記録する。 |

## Must-fix 所見

### F-1 — 歴史 snapshot の byte identity と入力閉包が成立していない

- severity: **CRITICAL**
- real/refuted: **real**。brief の「歴史focus1と同一入力」は refuted。
- 根拠: focus1 prompt の9入力のうち、fix2 patch と exact post-stateからfix1 bytesを構成的にpinできるのは次の2件だけです。

  - `tools/check_ai_provenance.py`
  - `orchestrator/tests/test_check_ai_provenance.py`

残る7件、すなわち `docs/ai-provenance.md`、`docs/decisions.md`、`tools/check_docs.py`、`orchestrator/tests/test_check_docs.py`、`review-a.md`、`review-b.md`、`fix1.md` には focus1 読取時点のdigestがありません。plan の9 SHAは再構成した候補を固定する値であり、歴史値から独立したoracleではありません。[plan:61](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:61)

さらに厳密には、上記2件も「focus1読取瞬間と同一」という contemporaneous digest はなく、patch前後のchainからの強い再構成です。

加えて、focus1 rollout は実際に `CLAUDE.md`、`AGENTS.md`、dev-wave正本、phase/worklog、`adjudication-plan-v2.md` を読み、artifact directory の `consult-a.md`、`consult-b.md`、`plan.md` 等を検索結果として取り込んでいました。[focus1 rollout](/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl:1) plan の「untrackedはレビュー入力3件だけ」はこの transcript と衝突します。[plan:91](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:91)

- 成果物影響: 新しい max/high 両 arm が同じ再構成 snapshot を見るなら、その新benchmark内の比較は可能です。しかし「歴史focus1の同一入力再走」「歴史maxの再現率」という insight は作れません。欠落artifactや既存focus出力へのアクセス差が arm の応答を汚せば、reasoning差への帰属も崩れます。
- 最小是正: 「歴史再現」を撤回し、`新たに凍結した既知R-1 benchmark` と定義する。その snapshot 上でR-1を独立再裁定する。各runは同じcanonical pathを持つ別mount namespaceで、snapshotと必要なruntime以外、歴史focus出力・他run出力を不可視にする。transcriptの事後監査だけでは漏洩防止になりません。

### F-2 — 正例1点では recall も偽陽性率も測れない

- severity: **CRITICAL**
- real/refuted: **real**。P1の「focus2はrecall未定義だから不要」という理由は refuted。[brief:45](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:45)
- 成果物影響: focus1だけで得られるのは、1個の既知R-1に対する反復確認成功 `k/3` と資源値です。ground truth の総数が1なら0%/100%しかなく、must-fixの種類・難度へのrecall一般化はできません。常にNO-GOを出す攻撃的armでもR-1だけは拾えるため、focus2を捨てると誤警報・GO維持能力を一切測れません。「新規finding件数」だけでは真偽を分離できません。
- 最小是正: focus2を両armへ負の対照として入れ、ground truth 0を独立に再裁定する。`n=3/arm`なら報告できるのは同一負例上のfalse-positive occurrence `k/3` であり、母集団FPRではありません。費用制約で1回/armだけなら sanity sentinel と明記し、FPR・production採用を主張しない。focused review全般へroutingするなら、別の非名指し正例も最低1件必要です。

### F-3 — R-1名指しは「発見」ではなく、答え付き仮説の確認である

- severity: **HIGH**
- real/refuted: **real**。P4のラベル付けは正しいが、それだけで外的妥当性は回復しない。[brief:53](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/brief.md:53)
- 成果物影響: prompt は「pre-policyでもparser実行」「例外ならrc=2」という因果鎖まで提示しています。[focus1:17](/home/SFC/tanab/github/izanagi/output/insights/2026-07-29_t153e-t15423-review-verbatim/focus1.md:17) 測るのは読解・裏取り・severity昇格能力であり、未知のmust-fix発見能力ではありません。T-184がstage全体をhighへ落とす根拠には不足します。
- 最小是正: 次のどちらかを事前選択する。

  - 結論とrouting対象を「明示された因果仮説のfocused confirmation」に限定する。
  - 非名指しのheld-out正例を追加し、named confirmationとblind discoveryを別stratumで報告する。

### F-4 — n=3には非劣性の解像度がなく、判定規則が未登録

- severity: **HIGH**
- real/refuted: **real**
- 成果物影響: iidと仮定してさえ3/3の二側95% exact lower boundは約29%です。3/3対3/3は「この6回で差を観測しなかった」だけで、同等・非劣性を示しません。3/3対2/3も安全gateとしてhighを不採用にすることはできますが、統計的にhighが劣るとは言えません。事後に「1 missを許す／許さない」「maxがmissした場合」を選べる自由度が残っています。
- 最小是正: run前に次を固定する。

| 観測 | 許される裁定 |
|---|---|
| max 3/3、high 3/3 | bounded sentinelで劣化未観測。非劣性・採用証明ではない |
| max 3/3、high 2/3以下 | 事前登録したzero-miss安全条件をhighが不充足。統計的劣性とは言わない |
| max 2/3以下、high 3/3 | benchmarkまたはmax基準が不安定。high優越とは言わない |
| 両方2/3以下 | 品質判断不能 |
| false positiveをいずれかで観測 | 事前登録したnegative-control gateに従う |
| technical invalid発生 | 固定したpair/batch規則で処理し、全attemptを保存する |

順序は固定high先行でなく、事前seedによるpair内randomizationにする。pilotは意味出力を封印したtechnical preflightとして本数外にするか、max側も対称に行う。非劣性を本当に主張したいならmarginとpowerからnを再設計する必要があります。n=3を維持するなら、用途を記述的sentinelへ落とすしかありません。

### F-5 — R-1採点器が歴史maxの文体へ過適合している

- severity: **CRITICAL**
- real/refuted: **real**
- 成果物影響: plan の規則は `### R-1` block、`regressed`、`HIGH`、`must-fix`、複数の関数名、`rc=2`、二範囲のcitationまで要求します。[plan:198](/home/SFC/tanab/.claude/jobs/c94644e8/tmp/t181-wave/plan.md:198) これは歴史max出力の構造を見た後に作られており、正しい因果を自然言語で説明したhighをfalse negativeにできます。厳しすぎる規則は詳細・定型を出しやすいmaxに有利です。逆に元briefの3語共起は、refuted/closed文脈やprompt echoを真陽性化し、一般には冗長なarmを有利にします。
- 最小是正: primary endpointをarm情報を隠した意味裁定にする。必要条件は「pre-policyでCAB parserが不要実行される」「その失敗が従来rc=0をrc=2へ変える」「NO-GO/must-fix相当」の3命題とし、同義表現を許す。関数名・R番号・citation完全性は二次的なevidence-quality指標へ分離する。run IDをランダム化し、可能なら独立2名、最低でも凍結codebook＋不一致時の保守裁定を用いる。

### F-6 — 「無効run」除外がarm依存の品質劣化を消す

- severity: **CRITICAL**
- real/refuted: **real**
- 成果物影響: effort/cwd/snapshot mismatchはtreatment未成立なので技術的invalidでよい一方、部分出力、`## 総括`欠落、形式不遵守、post-inference abortはproduction reliabilityそのものです。これを分母から外すと、highが部分出力を増やしても「有効runでは3/3」と見せられます。逆にmaxの長大化がtruncationを増やす場合はmax側が同様に救済されます。方向は事前に決まらず、いずれもselection biasです。これは [T-181] 自身が「品質劣化または部分出力」をescalation対象にしていることとも衝突します。[phase3:537](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t181-reasoning-ab/docs/phase3.md:537)
- 最小是正:

  - snapshot/effort/model/cwd mismatchなどpre-treatment失敗: technical-invalid。固定規則でpairまたはbatchを無効化。
  - 部分出力、validator reject、曖昧GO、処理後abort: assigned armの失敗としてscheduled_n分母へ含める。
  - conditional-on-valid分析は二次指標として併記。
  - batch再実行上限を事前固定し、失敗batchを削除しない。token・wall-clockはinvalidでも全件計上する。

### F-7 — benchmark上のsilent missからruntime escalation条件は作れない

- severity: **HIGH**
- real/refuted: **real**
- 成果物影響: benchmark scorerはR-1を知っていますが、productionではhighが整形式GOを出してmust-fixを黙って見逃したかを観測できません。したがってT-181から直接作れるruntime escalationは、部分出力・receipt mismatch等の可観測失敗だけです。「品質劣化ならmaxへescalate」はoracleなしには発火しません。
- 最小是正: offline採用条件とonline escalationを分離する。silent missが1件でも出た場合はunshadowed high routingを不採用にする。highを使うならmax shadow、周期監査、または人間oracleを残す。T-184は「silent degradation検知gateができた」と引用してはいけません。

## 交絡因子の棚卸し

全体severityは **HIGH / real**。制御不能な残差は結論の適用範囲へ書く必要があります。

| 因子 | 制御・記録 | 制御不能時の結論 |
|---|---|---|
| model version drift | aliasだけでなくservice/build IDが取れれば一致gate。取れなければ短時間のrandomized block | 「当該時刻の`gpt-5.6-sol` alias」に限定 |
| sandbox | `turn_context.sandbox_policy`、permission profile、world_stateを一致gate。root readをやめsnapshot-only mount | requested read-onlyだけでは漏洩なしを証明しない |
| cwd / filesystem | 各runを別namespaceの同一canonical pathへmountし、manifest前後検査 | 歴史cwdとの意味等価やhost全体同一は主張しない |
| 時刻・service負荷 | pair内順序をrandomizeし、隣接逐次実行、timestamp保存 | wall-clock差はserving window依存 |
| 並列実行・rate limit | 本比較は逐次。並列予測を撤回。rate-limit eventとretryを保存 | 並列時の速度・品質へ一般化しない |
| context圧縮 | compaction eventと`comp_hash`を記録。同一設定をgate | reasoningにより圧縮時点が変わるなら媒介効果として含め、調整で消さない |
| `summary=auto` | 全runで値をpin・記録 | autoのarm依存発火は総効果の一部。アルゴリズムdriftは残差 |
| personality | 歴史値は`pragmatic`。turn_context/world_stateで一致gate | planが未記録のままなら歴史比較不可 |
| CLI version | 0.146.0だけでなく実行binary hash、config、起動引数をpin | backend model同一性までは証明しない |
| cache | raw/cached tokenを別報告し、pair順をrandomize | 同一prompt反復は相関し、replicate独立性を仮定しない。high固定先行はcold-cacheをhighへ偏らせる |
| prior output/result leakage | 歴史focus1/2と先行run成果をmountから除外 | transcript事後監査だけなら強い能力主張を禁止 |
| system/AGENTS/skill context | visible world_state、AGENTS、skill、`comp_hash`をhash・一致gate | hidden system promptは制御不能なので現在のCodex surface限定 |
| sampling/backend routing | seed・backend/request IDが取れれば保存 | 取得不能ならiidや再現確率の母集団推定をしない |
| locale・timezone・PATH・Git/tool version・host load | env manifestを固定・保存 | tool利用差をreasoningだけへ完全帰属しない |

## 許される結論と禁止表現

現設計のまま出せる最強形は次です。

> 固定した、R-1の因果仮説を明示した単一正例に対する各3回の記述的確認で、recorded effort=`high` はR-1を X/3 回、`max` は Y/3 回must-fix相当と裁定し、scheduled runの構造・部分出力失敗はそれぞれ A/3、B/3、観測token・wall-clockは提示値だった。この結果は当該prompt、snapshot、serving期間に限定され、focused review全般のrecall・非劣性・production安全性を推定しない。

3/3対2/3なら、許されるのは次です。

> highは事前登録したzero-miss safety sentinelを満たさなかったため、当該routingの採用候補から外した。ただしn=3からhighの母集団性能がmaxより統計的に低いとは結論しない。

T-184で禁止すべき引用は以下です。

- 「highのmust-fix再現率は100%」
- 「highはmaxと同等／非劣性」
- 「focused review全体をhighへ落として安全」
- 「偽陽性率は0」— negative controlなし、または同一負例3回だけでは不可
- 「歴史focus1とbyte-identicalな入力を再走した」
- 「実際のbackend reasoningがmax/highだった」
- 「部分出力を除けば品質不変」
- 「3/3対2/3なので統計的にhighが劣る」
- 「T-181がruntimeの品質劣化escalationを実装可能にした」
- 「このpilot単独でproduction stage matrixを決められる」

## 総括

致命的欠陥は三つあります。第一に、8,832 bytes一致は1ファイルの長さしか証明せず、focus1が指定された9入力のうちfix2逆適用で構成的にpinできるのは2ファイルだけです。しかも歴史transcriptは指定9件以外の正本・裁定文書・artifact検索結果を実際にモデルへ入れており、planの「untracked 3件だけ」というsnapshotは歴史入力と一致しません。第二に、答えを名指しした正例1点を3回繰り返しても得られるのはR-1確認頻度だけで、must-fix recall、blind discovery、false-positive rate、focused review全般の非劣性は得られません。focus2を負の対照から落とすのはpolicy判断用実験として致命的です。第三に、歴史maxの文体へ過適合した採点規則と、部分出力を無効runとして分母から除く規則が、arm依存の品質差を隠せます。

したがって判定は **条件付き GO（現状は実走停止）** です。段4で、歴史再現ではなく新規凍結benchmarkへscopeを訂正し、結果漏洩をmountで遮断し、focus2負対照を加え、意味ベースの盲検採点、scheduled-run基準の失敗分類、randomized block順、全attemptを残す停止規則、3/3・3/2・baseline missの両側裁定を事前登録した場合にだけ実行してよいです。それでも成果物は「名指しR-1正例と限定負例における記述的sentinel」であり、T-184がproduction focused review全体をhighへ落とす単独根拠にはできません。テスト・runner・mutationは実走しておらず、緑は主張しません。