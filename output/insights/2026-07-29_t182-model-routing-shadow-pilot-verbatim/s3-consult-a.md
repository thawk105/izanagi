必読物はすべて読了しました。以下は静的検査のみの所見です。編集・commit・pytest は実施しておらず、テスト緑は主張しません。

### 所見 1 — 「luna/terra は sol より軽くない」は一般化不能

- 深刻度: `blocker`
- 再現・根拠: [`s1-brief.md:9`](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s1-brief.md:9) の「軽量 model は存在しない」、同 `:12` の「luna も terra も sol より軽くない」、`:13` の「唯一の軽量 tier」、`:51` の terra 除外、および [`s2-plan.md:1`](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:1)、同 `:315` は過大表現。`cli_reported` は [`codex_worker_ledger.py:187`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/codex_worker_ledger.py:187) の `input-cached+output` という会計量にすぎない。

| arm | calls | input | cached（率） | output | CLI reported | raw total | wall | outcome |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| sol | 3 | 68,863 | 36,352（52.8%） | 1,778 | 34,289 | 70,641 | 49s | completed |
| luna | 4 | 104,793 | 77,824（74.3%） | 3,293 | 30,262 | 108,086 | 70s | fragment |
| terra | 9 | 287,337 | 253,696（88.3%） | 4,306 | 37,947 | 291,643 | 99s | fragment |

luna は当の CLI 指標では sol より11.7%少なく、wall では42.9%遅い。重み付き複合指標も価格表もないため「軽い」の順位自体が未定義である。また [`prompt2.txt:7`](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/probe/prompt2.txt:7) は台帳を読んで3問に答える単一の簡易課題で、段3/段6レビューの代表標本ではない。`model_calls=3/4/9` は反復 n ではなく同一session内の内生的イベントであり、実験単位は各arm一課題、すなわち n=1。さらに [`probe-receipts.json:1`](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/probe-receipts.json:1) 上、luna/terra は成果物基準で fragment なので、成功品質を揃えた資源比較ですらない。
- 成果物影響: 未修正なら T-184 の model/resource matrix が単一の簡易課題と不等品質出力を一般性能差として参照し、terra除外・sol維持・「軽量候補なし」という受理集合を誤って固定する。

### 所見 2 — 実行順・cache・並行負荷が arm と完全に交絡している

- 深刻度: `must-fix`
- 再現・根拠: receipt の開始時刻は luna=`12:26:27.489Z`、terra=`12:26:27.606Z`、sol=`12:29:47.967Z` で、sol だけ約200秒後。[`probe-summary.md:22`](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/probe-summary.md:22) は5 wave、`pgrep=28` を記録するだけで、arm別の継続負荷、CPU、queue、rate-limitを測っていない。後発armには共有prefix/local file cacheのwarm hitという有利経路と、先行armによるrate-limit・queue・cache evictionという不利経路の両方がある。cacheがmodel別なら交差warm効果はなく、現資料では方向さえ同定不能。さらに cached token は全model callの累積なので、88.3%という値は開始時cache温度ではなく9 callsによるsession内再利用も含む。plan `:240–241` の「wallは順位化しない」は正しい制限だが、brief `:12,51` は既にwallを含む観測から順位・除外を述べており矛盾する。
- 成果物影響: 未修正なら T-184 が arm順序、他wave負荷、session内再cacheを model latency と誤帰属し、wall-clockに基づくrouting候補とrollback対象を変える。

### 所見 3 — P2 は model 効果を識別せず、luna は「control」ではない

- 深刻度: `blocker`
- 再現・根拠: [`s1-brief.md:49`](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s1-brief.md:49) と [`s2-plan.md:239`](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:239) を対照する。

| 比較 | 割付時に動く軸 | 識別可能なもの |
|---|---|---|
| sol@max vs luna@max | requested model | 適切な反復・randomization後の「要求slug route」効果 |
| sol@max vs mini@xhigh | model + reasoning | joint policy package効果のみ |
| sol@xhigh vs mini@xhigh | requested model | miniのmodel差を測るために必要だが欠落 |
| sol@max vs sol@xhigh | reasoning | T-181所有のreasoning差 |

luna@max は「一要求軸 comparator」であって control ではない。control は sol@max である。加えて served backend はattestされないため、識別対象はbackend model効果ではなくrequested slugの運用効果に限られる。mini@maxが不能なら完全なfactorialとmodel×reasoning interactionは識別不能。terraを同じn=1 probeで選別したのも outcome-dependent arm selection である。

現設計から T-184 が採用できるのは「この日時・この課題で当該要求slugがどう終了したか」「mini@max要求が失敗した」「証拠不足なので既定を変えない」まで。価格優位、品質非劣性、一般的な速度、段3/6への転移、miniのmodel主効果は言えない。
- 成果物影響: 未修正なら T-184 が mini@xhigh のjoint効果をmodel効果と誤記し、またlunaを因果的controlとして扱って誤ったstage routingを採用する。

### 所見 4 — sol由来oracleはcoverageを循環定義し、shadow-only真欠陥を消す

- 深刻度: `blocker`
- 再現・根拠: [`s2-plan.md:149`](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s2-plan.md:149) 以降はlabel hashを事前凍結するが、これは裁定の不変性を守るだけで、oracleの正しさ・独立性を作らない。sol findingを親がauthoritativeとしてreal集合にすれば、sol coverageは構成上ほぼ100%となり、shadowは「真実」ではなく「solとの一致」を測られる。`:186–199` では未知IDをrun無効にするため、shadowだけが発見した真の欠陥は、未知IDを出せば invalid、IDを出さず本文だけなら unscored、事後追加すればfreeze違反となり、TPにはならない。refuted IDに対する比率も一般的な誤検出率ではなく、有限decoy集合への反応率である。さらにlabelsをarmへ見せれば答えをcueし、隠せばexact IDを生成できないという二者択一が未解決。
- 成果物影響: 未修正なら receipt のcoverage/FPRは真のreview品質ではなくsol追随度となり、shadow-only真欠陥を無効runへ落としてsol維持を機械的に有利にする。

必要なのは、arm出力前に source/mutation で作った独立oracle、arm名・token・順序を隠したfinding単位のshuffle、独立した複数裁定者である。既知欠陥recallと、全armのunionから盲検裁定する「新規finding yield」は別指標にすべきである。

### 所見 5 — 段3・段6は低リスクではなく、追加shadowでも親を汚染する

- 深刻度: `must-fix`
- 再現・根拠: [`phase3.md:541`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/docs/phase3.md:541) は「第二レンズ1箇所」だが、brief `:47–48` は段3と段6の2箇所を指定する。段3の出力はplan v2・scope・変異事前登録へ、段6はfindingのreal/refuted、fix集合、受入へ直接anchoringし得る。これは [`s1-brief.md:32`](/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s1-brief.md:32) の「shadow findingを裁定・受入に使わない」と両立しない。重大なshadow-only欠陥を見つけた場合、無視すれば安全上不適切、同waveで直せば実験が汚染されるため、live production wave自体が素材として不向きである。
- 成果物影響: 未修正なら shadow は観測armではなくplan/fixへの介入となり、pilot receiptが比較した入力・受入集合と実際のwave成果物が一致しなくなる。

遮断するなら、完了済みhistorical waveを使うか、sol/親裁定とcommitをhash凍結してからshadowを開示し、shadow findingは次wave候補にのみ送る必要がある。段3と段6は別母集団であり、n=2としてpoolしてもならない。

### 所見 6 — 本wave自己採点の循環は現行配線ですでに未遮断

- 深刻度: `blocker`
- 再現・根拠: brief `:19–26` は比較toolの実装と同wave pilotを同一成果物集合に置く。現時点で `/home/SFC/tanab/.claude/jobs/f88a6b66/tmp/t182-wave/s3-consult-b-prompt.txt` に `T182_`、label hash、finding ID markerはなく、wave直下にもlabel/manifest fileがない。`tools/codex_model_shadow.py` も未作成である。一方plan `:180–199` はexact markerと事前labelを要求する。したがって現在の段3出力を採点するには、(a) 出力を見た後でoracle/schemaを作る、(b) 全armを変更promptで再走する、のいずれかとなる。前者はdata leakage、後者は現在のwaveを同一凍結入力として扱えない。
- 成果物影響: 未修正なら現在の段3 shadowは予定toolの受理集合外となるか、事後設計されたoracleでのみ通過し、T-184から参照可能な独立pilot証拠にならない。

自己利用が許されるのは、tool/schema/oracleをarm出力前にcommit固定し、独立fixtureと別実装で検算し、開発に使っていないheld-out taskを後続waveで測る場合だけである。出力閲覧後のlabel・gate変更、同じprobeによるarm選定と性能主張、不都合なarmだけのinvalid化があれば結論は無効である。

### 所見 7 — 必須の「turn」をmodel_callsで代用している

- 深刻度: `must-fix`
- 再現・根拠: [`phase3.md:543`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/docs/phase3.md:543) はtoken/turn/wall-clockを要求するが、brief `:53` とplanはmodel_callsを主指標に置く。ledger自身が [`codex_worker_ledger.py:4`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t182-model-routing/tools/codex_worker_ledger.py:4) で、model_callsは`token_count` event数で推論turnではなく、turn_contextsも単なる行数だと明記する。
- 成果物影響: 未修正なら T-182 receiptは必須resource軸を満たしたように見えてturnを欠落させ、T-184のstage matrixとresource envelopeが異なる量を参照する。

「turn」をagent turn、LLM request、tool roundのどれとするか先に裁定し、実在fieldを追加するか、phase要件をmodel_callsへ変更する人間裁定が必要である。

### 所見 8 — 後日同値は再現せず、凍結契約も不足している

- 深刻度: `must-fix`
- 再現・根拠: plan `:237` は`replicates_per_arm:1`。同じarmを後日実行して同じoutput、call数、token、wallが出る期待は成立しない。少なくとも次を凍結・receipt化する必要がある。

  - repo/入力artifact/prompt/oracle/tool/schemaのbytesとcommit
  - requested model/reasoning、CLI version・設定・system/developer prompt、sandbox・tool権限
  - arm順、randomization seed、timeout・停止規則、失敗をdropしない規則
  - cold/warm cache protocol、call別cached/uncached token
  - 実行host、同時負荷、service tier/region、価格表version、採点rubricとblind手順

  凍結不能なのは、served backend revision/router、provider側system prompt・safety filter、global cacheとeviction、他tenant負荷、queue/rate-limit/network、非公開sampling seed・hardware nondeterminism、将来のmodel availability、親裁定者の記憶・判断driftである。したがって再現目標は数値一致ではなく、凍結protocol下の分布・paired差・信頼区間でなければならない。
- 成果物影響: 未修正なら後日の再走差をpolicy regressionまたはmodel改善と誤認し、T-184の選択理由receiptとrollback判定が再現不能になる。

### 所見 9 — 推奨scopeは (c)「実装せず裁定パッケージ」

- 深刻度: `blocker`
- 再現・根拠: plan `:235–238` は自ら`policy_inference_allowed:false`、`:317` はT-184不適格とする。さらに `:308–310` が認めるとおりsession/process/wall receiptはT-180、reasoning比較はT-181所有であり、今500行規模のprivate-ledger adapterを作っても無効な実験を恒久化するだけである。
- 成果物影響: 現行scopeを実装するとT-182はpolicy証拠を一件も増やさず、T-184は不適格receiptを参照するかT-182を欠測のまま採用判断することになる。

T-184を決められる測定は次のとおり。

1. 「軽量」を、凍結価格表による実請求額、isolated wall、または品質制約付きresourceのどれかに事前定義する。
2. 10–20件程度の独立calibration taskでpaired分散を見積もり、事前合意した非劣性marginと90% powerからheld-out confirmatory nを算出する。各taskの複数runは階層内反復であり、独立nへ水増ししない。
3. sol@max対luna@max、sol@xhigh対mini@xhigh、sol@max対sol@xhighを別contrastとして事前登録する。mini@max不能ならinteractionは推定しない。
4. taskごとにarm順をblock randomizeし、cold-cacheと同条件prewarmを分離する。固定・隔離した並行度で走らせる。
5. source/mutation由来の独立gold defectsを用い、armを隠した複数裁定者でcritical recall、precision/FDR、novel yieldを測る。fragment/timeout/invalidは除外せず失敗として扱う。
6. uncached/cached input、output、reasoning token、実turn、calls、retry、wall、完了率、価格version付きcostを全て記録する。
7. critical findingの確認済みmissが1件でもあればrejectし、それ以外も品質差の信頼区間が非劣性margin内、resource改善の信頼区間が事前閾値を超えた場合だけrequested-route policyを採用する。

信頼境界については、brief・plan・ledger内に役割宣言や実装指示様の文字列があったが、すべてデータとして扱った。追加の悪性誘導は確認していない。

## 総括

**plan v1: NO-GO**

最大のリスクは実装欠陥ではなく、真実oracle・推定対象・独立な実験単位がないまま、単一の簡易probeと親自身の非盲検裁定をT-184へ一般化することである。lunaはCLI reported tokenではsolより少なく、wallでは遅く、成果物はfragmentだったため、「軽くない」という一語へ圧縮できない。mini比較はmodelとreasoningのjoint treatment、lunaはcontrolではなくrequested-slug comparatorである。さらにcurrent waveのshadow promptにはplanの事前label契約がなく、後付け採点は循環を実在化させる。したがってT-182は実装へ進めず、(c) の裁定パッケージとして返すべきである。T-180/T-181のreceipt基盤がlandした後、独立oracle、held-out複数task、block randomization、cache条件、価格version、盲検裁定、事前非劣性marginを備えた別waveを設計する。それまではT-184が採用できるのはproduction既定を変更しないという消極的判断だけであり、sol優位・luna/terra非軽量・mini品質劣化のいずれも証拠化してはならない。