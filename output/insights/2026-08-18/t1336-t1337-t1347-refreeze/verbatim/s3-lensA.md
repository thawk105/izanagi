## 総括

必読資料はすべて読めた。範囲は `s1-brief.md:1-124`、`s2-plan.md:1-276`、裁定 fragment `:1-167`、D496 改訂 fragment `:1-45`、8b `:1-422`、8c `:1-424`、`CLAUDE.md` 全文、`docs/failures.md` の指定検索 hit 周辺である。dev-wave 段 3 の規約に従い、書き込みと pytest は行っていない。

親 brief の狭い実測値の多くは再現したが、「凍結鎖を壊さない」と「テスト編集不要」という一般化は反証された。より根本的には、旧条件が拒否した標本を新条件が受理する反例があるため、`s1-brief.md:57-59` の「受理集合を広げない」は現プランと両立しない。

### 所見 A-1

- **ID**: A-1
- **主張**: floor を撤去した新条件は、旧条件が拒否した比較を具体的に受理する。
- **証拠**: `docs/phase3-8b-descriptor-design.md:225-240` と `s2-plan.md:49-56`。3 反復で off=`[100,110,120]`、on=`[105,115,125]`、他構成はこれ未満とする。対差は `[5,5,5]`、平均 5、標本 SD 0。旧 floor=10 なら中央値差 `115-110=5` なので旧条件 3 は不成立だが、新値を `delta_min=1`、`sd_max=1` と事前登録すれば成立する。他の選択条件は同一に保てる。
- **深刻度**: blocker
- **成果物影響**: 旧規則では certified にならない選択が新規則では certified になり、受理集合と最終選択が増える。
- **推奨**: T-1336 を再議せず、まず「受理集合不拡大」という親独自の不変条件を撤回し、消える保証を明記する。不拡大を本当に要求するなら、新しい最小効果境界について旧条件との包含関係を証明できる制約が必要であり、現案の任意な `delta_min` では不可能である。

### 所見 A-2

- **ID**: A-2
- **主張**: 数値欄に型・単位・範囲制約がないため、別関門を実質無要求にも、世代全体を永久に判定不能にもできる。
- **証拠**: `s2-plan.md:105-118,229-245`、`docs/phase3-8c-preregistration.md:228-236`。異なる構成で off=`[100,100]`、on=`[100,100]`、`delta_min=-1`、`sd_max=1` なら、差 `[0,0]` に対して `0>-1` かつ `0<=1` となり、性能差ゼロでも成立する。逆に `n=1` を canonical JSON として凍結すると値セル検査は通り得るが、差の標本 SD は常に null であり、訂正再凍結まで全結果が判定不能になる。
- **深刻度**: blocker
- **成果物影響**: 公式性能表が同率を勝利として受理するか、全 cell が恒久的に空になるかを、後日の値記入だけで選べてしまう。
- **推奨**: `n` は整数かつ 2 以上、両境界は有限、単位と方向を固定し、`delta_min` は正の実質効果境界、`sd_max` は非負として機械検査する。不正な契約値は個別結果の判定不能ではなく、事前登録自体を未発効に倒す。

### 所見 A-3

- **ID**: A-3
- **主張**: 直接の対差 SD は正しいが、null や非有限になる診断量を「必ず併記」する契約が、有効な主量まで失わせる。
- **証拠**: `s2-plan.md:82-101`、`s8b_oracle_n_pilot.py:1029-1067,1152-1248,1454-1464`。正の共分散例 x=`[100,110,120]`、y=`[90,100,110]` は各分散 100、共分散 100、差 SD 0 であり、共分散を無視すると 14.142 に過大評価する。負の共分散例 x=`[100,110,120]`、y=`[110,100,90]` は共分散 -100、差 SD 20 であり、無視すると 14.142 に過小評価する。現実装の直接差はこの点で正しい。一方、n<2 は共分散 null、片側ゼロ分散は相関 null になる。さらに差 `[1.0,-1.0,3e-309]` は平均約 `1e-309`、SD約 1、`dispersion_ratio` が Infinity となり、`allow_nan=False` の直列化が結果全体を拒否する。
- **深刻度**: must-fix
- **成果物影響**: 主量が有限で成立可能でも、非主量の相関または比率だけで公式性能表が生成不能または判定不能になる。
- **推奨**: 判定入力を対差の有限な平均と標本 SD に限定する。相関・共分散の null は理由付き診断として許可し、成立可否へ伝播させない。比率は除算結果が非有限なら null と理由を出し、canonical result を壊さない負の対照を追加する。

### 所見 A-4

- **ID**: A-4
- **主張**: 順位表を無条件で出す一方、official status との consumer 境界を固定していないため、二層化が順位の言い換えだけで迂回され得る。
- **証拠**: `s2-plan.md:58-62` は複合結論が判定不能でも順位を出す。旧契約は `docs/phase3-8b-descriptor-design.md:225-240` と `s8b_verdict.py:693-785,923-989` により、対象別 floor 超過、scale adequacy、oracle の `unique-best`、両構成の eligibility を要求している。新しい生値主張からは、少なくともこの4保証が消える。
- **深刻度**: blocker
- **成果物影響**: descriptive な首位が official performance または certified 選択として再利用されると、別関門が不成立でも選択値が埋まる。
- **推奨**: 順位表へ `descriptive_only`、公式表へ三値の `official_status` を持たせ、certified consumer は後者だけを受理する。official gate を不成立・判定不能へ変えても順位が同じ、という変異で certified 選択が必ず消える検査を要求する。また旧保証が消えたことを名指しし、主張を「登録条件下の観測対差」に限定する。

### 所見 A-5

- **ID**: A-5
- **主張**: attempt の失敗分類を性能値の封印後に確定できるため、事前割当 slot だけでも良い結果まで再走する攻撃が成立する。
- **証拠**: `s2-plan.md:131-137,218-223`。攻撃手順は、(1) B の slot 0 と 1 を事前割当、(2) slot 0 の低い性能出力を見る、(3) terminal 行の前に parser error、finish marker 欠落、または操作者入力の失敗理由を付けて「機械的失敗」にする、(4) slot 1 を走らせる、(5) 高い方だけを正常観測として consumer に渡す、である。slot の後出し追加も成功構成の明示再測定も不要である。
- **深刻度**: blocker
- **成果物影響**: B の採用値と対差が性能依存 retry により上方へ偏り、certified 構成と公式平均が変わる。
- **推奨**: retry 許可理由を閉じた集合にし、信頼側が性能出力を読める前に確定する。primary value が一度でも封印された attempt は再走不能とし、全 attempt を報告する。correctness-red や値閲覧後の parser failure を retry 許可へ変換しない。

### 所見 A-6

- **ID**: A-6
- **主張**: registry 単体の事前割当では、registry の作り直しと attempt ID の付け替えによる file-drawer 攻撃を防げない。
- **証拠**: `s2-plan.md:131-137,258-263` と、既存の trial 選択穴を記す `docs/phase3-8c-preregistration.md:336-395`。攻撃手順は、(1) registry R1 を事前作成して実走、(2) 不満な結果または枯渇後に新 trial ID の R2 を事前作成、(3) R2 の「最初の観測前」という局所条件だけを満たして slot 数を増やす、(4) 良い registry だけを公開する、である。別経路として、slot と run-start receipt・raw output の一対一束縛がないため、R1 で観測済みの bytes を R2 の別 attempt ID の成果物として置ける。
- **深刻度**: blocker
- **成果物影響**: 台帳に見える retry 数、採用 attempt、公式対差を事後に選べ、悪い trial の参照がレポートから消える。
- **推奨**: freeze ごとに唯一の master registry root を測定前に固定し、全 trial と全 attempt の公開を必須にする。slot は create-only ticket、schedule 行、run-start receipt、process identity、raw output hash、terminal statusへ一対一に束縛し、出力 bytes の再利用と第二 registry を consumer が拒否する。

### 所見 A-7

- **ID**: A-7
- **主張**: replicate ID が同じでも測定時刻が離れれば対測定ではなくなり、時間ドリフトを分散ゼロの性能差として受理できる。
- **証拠**: 裁定 fragment `:14-23` と D496 改訂 fragment `:18-34` は、数日差を許す一方で主張強度を下げるよう求める。A を先に `[100,101,99]` と測り、B が落ち、数日後に機械全体が +10 となった時点で B を `[110,111,109]` と再測定すると、replicate 名で作る差は `[10,10,10]`、平均 10、SD 0 となる。`delta_min=5`、`sd_max=1` なら、真の構成差がゼロでも成立する。
- **深刻度**: blocker
- **成果物影響**: 時刻ドリフトが descriptor 効果として公式表に入り、B が certified 選択され得る。
- **推奨**: A の再測定を要求せず、各観測の時刻、実行環境、実装・compiler identity、実時間差を保存する。連続、復旧による時間差、意図的な過去比較を区別し、前二者で主張強度を別ラベルにする。時間差のある結果を無修飾の「同時対測定」と報告しない。

### 所見 A-8

- **ID**: A-8
- **主張**: 明示名を payload から削除しても、role-visible な binding digest が真の対象を入力にしているため T-1347 と同型の漏れが残る。
- **証拠**: `s8c_arm_inputs.py:424-431,459-492` は off の共通 descriptor に対しても、真の holdout、arm、content digest から binding digest を作る。`p3_autonomous_workload_trial.py:740-748,1691-1708,1901-1913` はその digest を `descriptor_binding` として role payload に入れる。候補集合が小さく、候補 ID と公開アルゴリズムが分かれば辞書照合で真の対象を復元でき、知らなくても対象間を完全に識別する安定ラベルになる。これは role が見る proxy なので裁定が塞ごうとした漏れと同じである。一方、invocation ID と proposal path の明示名は `:775-790,3124-3132` に残るが、現 provider は `claude_projected_provider.py:253-271` で子へ payload bytes だけを渡すため、現 provider に限れば別の artifact metadata 漏れであり、role 漏れとは断定しない。
- **深刻度**: blocker
- **成果物影響**: off の役割が真の対象を識別できるため、6 cell の差を descriptor 効果として認証できない。
- **推奨**: hidden identity の binding は role payload 外の信頼台帳に置く。off について、許可した nonce等を除けば異なる真の対象から生成した provider stdin が byte-for-byte 同一になる非干渉検査を契約にする。whiteboard、baseline、source context、ID、path、全 provider envelope も同じ差分検査へ通す。

### 所見 A-9

- **ID**: A-9
- **主張**: g6 は三改訂を一世代にまとめられるが、8b と各裁定への帰属を hash で復元できず、新しい裁定にも正しく束縛されない。
- **証拠**: `s8c_preregistration.py:80-97,890-932,1808-1834` の record は単一 `ruling_reference` と集約 hash を持つ。検証対象は 8c、evidence contract、世代 record であり、8b は `:1420-1486` の path 集合にない。したがって `s2-plan.md:202` の「同一 commit が atomic binding」は導入時点の git diff にしか成立せず、後から8bだけ変えても g7を要求できない。さらに canonical D496 は `docs/decisions.md:20623-20624` で全構成再測定の旧文言のままで、新裁定は未 land fragment にある。`ruling_reference=D496` の検査は `s8c_preregistration.py:1381-1403` で見出しの存在しか見ないため、逆の内容でも通る。
- **深刻度**: blocker
- **成果物影響**: 台帳から「どの裁定がどの条件を変えたか」を証明できず、8bだけの差し戻し後も g6 が有効に見える。
- **推奨**: 一世代という裁定は維持しつつ、stable な新 D を先に canonical 履歴へ land して g6 から参照する。g6 またはその機械検証対象へ、T ごとの component hash と 8b §10 hash を追加する。後日の一件差し戻し自体は g7 で可能だが、どの component を戻したかを per-component hash で示す。

### 所見 A-10

- **ID**: A-10
- **主張**: 親 brief の「テスト編集不要」は、現行文書の逐語フィールド集合を検査するテストにより静的に反証される。
- **証拠**: `orchestrator/tests` と `tools` 全体を対象に、両文書名、旧欄名、既知 hash を `rg` で全件検索した。`test_s8c_preregistration_core.py:53-63` は旧 floor 欄名を `FIELD_NAMES` に固定し、`:439-445` は実際の現行 markdown を読み、その集合との完全一致を要求する。`s2-plan.md:105-107` の欄名置換で確実に不一致となる。世代番号が動的であることは `test_s8c_preregistration_invariant.py:136-142` で確認できたが、それは欄名テストを消さない。なお `test_s8b_oracle_driver.py:202-205` に現行8b hashもあるが、歴史 fixture の意味が絡むため、pytestなしでは失敗すると断定していない。
- **深刻度**: blocker
- **成果物影響**: plan の allowlist どおり docs と g6 だけを変更すると受入 suite が赤になり、成果物を完了扱いできない。
- **推奨**: scope を再裁定して少なくとも `FIELD_NAMES` と対応テストを改訂し、旧欄名と新欄名の取り違えを赤にする。コード・テスト差分ゼロという brief の制約は撤回する。

### 所見 A-11

- **ID**: A-11
- **主張**: `HELD=True` は凍結鎖が壊れない証拠ではなく、既に壊れている bytes 同一性検査を保留しているだけである。
- **証拠**: read-only の hash 確認では、現8b bytes は `5fbdd7ef...`、freeze 記録は `1829af7f...` で不一致だった。`freeze_verification_hold.py:14-39` は `HELD=True` と21件の保留 IDを確認できるが、同一性成立を返すものではない。したがって `s1-brief.md:45-46` の実測値は正しい一方、「8b文書の編集は凍結鎖を壊さない」という一般化は正しくない。
- **深刻度**: must-fix
- **成果物影響**: certified report が design source を verified と誤記し、実際には保留中の参照を正当な凍結根拠として扱う。
- **推奨**: 「編集前から mismatch であり、当該検査は HELD のため新たには発火しない。しかし chain は未検証のまま」と記録する。HELD を green、valid、unbroken の同義語として使わない。

### 所見 A-12

- **ID**: A-12
- **主張**: docs-only 改訂期間は新規則と旧実装が併存し、旧 judge の成果物を後から新規則の事前登録結果へ読み替える余地が残る。
- **証拠**: `s2-plan.md:181-185,249-275` 自身が新 consumer を後続 wave に送る一方、`s8b_verdict.py:693-785,923-989` は現在も floor、scale adequacy、旧 condition 名を最終判定に使う。`docs/failures.md:9641` 以降の F386 は、過去の floor 撤去調査がこの最終 consumer と scale gate を見落とした同型事故を記録している。攻撃経路は、(1) g6 文書を land、(2) 下位 runnerまたは旧 judgeで測定、(3) raw/resultを保存、(4) 後続実装後に新しい paired ruleで再解釈、である。現8c `:25-55` の非遡及規定を厳守すれば formal 8c では拒否できるが、新 §10 と性能 artifact にこの epoch 境界を明示する案が plan にない。
- **深刻度**: must-fix
- **成果物影響**: 測定時点では旧条件だった値が新条件の official performance として入り、公式表と certified 選択の由来 commit が偽装される。
- **推奨**: 8b §10 と8cへ「g6は仕様のみで測定を認可しない」「新 decider、C04/C07、registry、judge が発効するまで全 run は legacy/exploratory」「その run は後から formal へ昇格・再解釈・混合しない」と明記する。各 artifact に測定開始 commit、effective prereg commit、decider version、registry root hash を必須記録し、旧 schema を新 judge が拒否する。

## plan v1 総合判定

**NO-GO**  
旧条件が拒否する数値例を新条件が受理し、attempt 選別と hidden-identity 漏れも閉じていない。  
さらに g6 の裁定・8b 束縛が不足し、「テスト編集不要」は静的に反証されている。