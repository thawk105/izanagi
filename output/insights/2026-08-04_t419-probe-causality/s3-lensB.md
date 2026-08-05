結論は「だめ」。この brief は、実験失敗・環境無効・仮説反証を分離できず、U-2 の方式選択に必要な受理集合と数値も定義できていない。以下は指定された [brief](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/output/insights/2026-08-04_t419-probe-causality/brief.md)、[runbook](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/docs/pegasus-runbook.md)、[失敗台帳](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/docs/failures.md)、[現行 probe](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/campaign/env_attestation.py)、[契約](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t419-probe-experiment/orchestrator/campaign/env_contract.py) の静的レビューであり、測定・変更はしていない。

### B-1

**主張:** `CONFIRMED / REFUTED` の二値しかなく、「有効な反証」と「実験自体の失敗」を区別できない。

**攻撃対象:** 「実験設計」の事前登録判定、raw JSON、README。

**具体的な失敗シナリオ:** affinity 設定失敗、CPU 欠落、競合プロセス検出、busy 子の早期終了、途中例外のいずれかで A1 が1件欠けても、brief 上は「1件でも外れたので REFUTED」になる。逆に、実装が観測済み件数だけを分母にすれば部分走が `48/48` に見える。PBS の完走、実験の妥当性、因果判定が同じ「成功」に潰れる。

**成果物影響:** 無効データが F108 の反証または立証として台帳へ入り、U-2 が誤った方式を選ぶか、正当な是正検討を不当に止める。

**強度:** 強い

**最小の是正案:** `execution_validity = VALID / INVALID` と `causal_verdict = CONFIRMED / REFUTED / NOT_EVALUATED` を分離し、全 arm の期待件数・例外・欠測・環境 gate が完全な場合だけ因果判定を生成する。

### B-2

**主張:** 計算ノードで再現可能に走らせる PBS 実行包絡が成果物に存在せず、runbook §3・§7・§8 を満たしたか検証不能である。

**攻撃対象:** 「計算ノード 1 job」と成果物一覧。

**具体的な失敗シナリオ:** bare `python3` が 3.9 未満へ解決する、親だけ `python3.10` でも孫 process が古い `python3` を拾う、ログインノードで誤実行する、対話セッションから無効な request を作る、出力が非永続面へ落ちる、`.o/.e` や会計痕跡が欠ける、といった runbook が実測済みの失敗経路を brief は閉じていない。`--self-test` の出力を本実験結果と誤認する経路もある。

**成果物影響:** raw JSON の出所が計算ノード job だと証明できず、レポートと台帳の参照が非再現な自己申告になる。

**強度:** 強い

**最小の是正案:** exact job script、qsub 呼出し、絶対 `-o/-e`、`python3.10` と PATH shim、計算ノード/PBS/affinity の fail-closed 検査、計算ノード側 marker、qstat 可視性、終了 rc・会計痕跡を証拠包絡へ含める。

### B-3

**主張:** F3 の単独性確認が「記録項目」に落ちており、非専有 allocation を無効化する admission gate になっていない。

**攻撃対象:** 「記録する束縛」の `ps`・`pgrep`・単独性判定。

**具体的な失敗シナリオ:** `Exclusive submit = OFF` のため、開始後に別 job が同居できる。一時点の `pgrep` が空でも実験中の同居を否定しない。さらに hidepid/PID namespace 可視性が不足すれば「見えない」を「いない」と誤認する。A2 の意図的な busy 子を競合から除外する規則もなく、検査を厳密にすると自分で自分を失格にする。

**成果物影響:** 他テナント由来の帯外値が probe の観測者効果へ誤帰属され、α/β/γ の失敗率と F108 の因果記録が汚染される。

**強度:** 強い

**最小の是正案:** 可視性確認、自己 process tree の allowlist、arm 前後と実行中の競合監視を事前登録し、不明または競合検出時は該当 arm を `INVALID` にする。allocation を専有証明として扱わない。

### B-4

**主張:** 因果を測る読み取りと、`ps`・`pgrep`・sysfs・loadavg 等の補助観測が時間的に分離されておらず、補助観測自身を原因と誤認できる。

**攻撃対象:** A0〜A4 と「記録する束縛」、不変条件の観測者効果記述。

**具体的な失敗シナリオ:** arm の critical window 中に `ps` や `pgrep` を spawn すれば、その helper が別 CPU を busy にして追加帯外値を作る。standalone driver が現行 `_parse_cpuinfo()` と異なる read/parser/order を使えば、「現行 probe の因果」ではなく「新 driver の因果」しか測っていない。

**成果物影響:** outlier index と self/busy CPU の対応が補助計測で変わり、レポートの因果説明と U-2 の方式評価が成立しない。

**強度:** 強い

**最小の是正案:** critical window を明示し、helper 起動を外へ出し、全 arm で同じ補助観測順にする。現行 `Path.read_text`＋parser と値が一致すること、または raw bytes と両 parser の一致を証拠化する。

### B-5

**主張:** A1 の `48 × R(=5)` を `48/48` へ畳む規則が未定義で、事前登録判定になっていない。

**攻撃対象:** A1 と「因果 CONFIRMED」の判定。

**具体的な失敗シナリオ:** CPU 17 で 5 回中1回だけ pinned CPU が帯外に出た場合、「CPU 17 は一致」と数えるのか、4件の失敗で REFUTED なのか決まっていない。A0 の “self CPU” も read 前、read 後、その和集合のどれか未定義である。実装者が結果を見て有利な集約を選べる。

**成果物影響:** 同一 raw data から CONFIRMED と REFUTED の両方を生成でき、F108 と裁定パッケージが非決定的になる。

**強度:** 強い

**最小の是正案:** 240 個すべてを判定単位にするのか、CPU ごとの閾値を使うのかを固定し、self の定義、欠測処理、集約順、信頼区間を実行前に明記する。

### B-6

**主張:** A2 は「k が1回でも帯外なら busy 仮説採用」という片側だけの判定で、busy 介入が成立した証拠も対照もない。

**攻撃対象:** A2 co-resident arm と P1/P2/P4。

**具体的な失敗シナリオ:** busy 子が barrier 前に死ぬ、affinity が外れる、実際には CPU time を消費しない、または偶然の kernel thread が k を busy にする。前者は偽 REFUTED、後者は偽 CONFIRMED になる。8対の k の選択、反復数、sham process、無効果時の判定も未定義である。

**成果物影響:** β/γ の同居負荷失敗モードが捏造または見逃され、方式選択レポートの実測根拠が変わる。

**強度:** 強い

**最小の是正案:** k 集合・反復・順序・閾値を固定し、開始 barrier、affinity、liveness、`/proc/<pid>/stat` の CPU-time 増分で介入成立を検証する。sham 対照または `INCONCLUSIVE` 分岐を置く。

### B-7

**主張:** A4 の read 前後 processor だけでは「読み中 migration」を立証できない。

**攻撃対象:** A4 migration と P2。

**具体的な失敗シナリオ:** `c0→c1→c0` と移動すれば前後は同じでも2 CPU が busy になりうる。逆に前後が異なっても移動が `/proc/cpuinfo` read の外で起きた可能性がある。kernel thread という対立仮説も消えない。

**成果物影響:** 帯外2個の原因を migration と誤記し、βで除外すべき CPU 集合とその受理集合を誤る。

**強度:** 強い

**最小の是正案:** A4 は「migration と整合的」に格下げし、十分な区間内スケジューリング証拠がない限り原因を `UNRESOLVED` のまま残す。

### B-8

**主張:** A3 は方式 α の実験操作を定義できておらず、現行 gate と異なる「厳密 2101.0」を合否条件に混入している。

**攻撃対象:** A3、P3/P5、規模欄の「3反復×48」。

**具体的な失敗シナリオ:** 現行 probe は1回の `/proc/cpuinfo` read で48値を得る。一方 `3×48` は「全体を K=3 回読む」のか「各 CPU に pin して3回読む」のか不明で、後者は production α と別の介入になる。また現行 comparator は凍結 expected median の ±2% 内を `all()` で検査し、2101.0 との完全一致は要求しない。帯内だが非2101.0の結果を α 不成立と誤判定できる。

**成果物影響:** αの成立可否、必要 K、実行コスト、過剰拒否率が誤り、U-2 が別アルゴリズムの実測を根拠に方式を選ぶ。

**強度:** 強い

**最小の是正案:** K×48 の raw matrix、K 候補、read/pin の正確な順序を固定し、現行 ±2% predicate の結果と「厳密2101.0」診断を別フィールドにする。K別の収束率と read latency を必須値にする。

### B-9

**主張:** 約500回は資源量として多すぎないが、推論精度への配分が無根拠で、重要 arm では明白に少なすぎる。

**攻撃対象:** 「規模（規律4）」。

**具体的な失敗シナリオ:** 独立 Bernoulli と仮定してさえ、CPUごと5回全成功では真の失敗率の片側95%上限は約45%、A3の3回全成功では約63%である。A0の30/30も成功率の片側95%下限は約90.5%にしかならない。一方、A1全240回は定性的な反例探索には過剰かもしれない。依存・時系列相関があれば保証はさらに弱い。

**成果物影響:** 「αは収束する」「self は必ず帯外」というレポート数値に支持できない確度が付き、裁定が見せかけの実測になる。

**強度:** 強い

**最小の是正案:** 先に必要精度・反証目的・停止則を決め、同じ約500回上限内で A1/A2/A3 へ再配分する。無造作な増量ではなく段階的停止を使う。

### B-10

**主張:** `raw/*.json + README` だけでは、第三者が同じ実行を同定・再解析・反証できない。

**攻撃対象:** 成果物定義。

**具体的な失敗シナリオ:** raw に次が無ければ、後から別 script、別閾値、別 job の出力と区別できない。

- repo commit と dirty 状態、driver SHA-256、exact argv、N/R/K、k 一覧、順序・乱数 seed
- `sys.executable` と Python version、kernel/boot ID、raw/正規化 PBS job ID、queue/project、job script
- qstat allocation、開始・終了時刻、rc、`.o/.e`・会計痕跡・計算ノード marker
- calibration path/SHA-256、expected median、tolerance、算出した上下限
- read ごとの48値、affinity、read 前後 CPU、開始/終了 monotonic time、read duration
- arm の期待件数・実件数・欠測・例外、busy 子の PID/affinity/CPU time/liveness

再実行で同名 JSON を上書きできる場合も、最初の反証材料が消える。

**成果物影響:** certified 選択結果の proof chain が mutable README に依存し、raw 参照を台帳から監査できない。

**強度:** 強い

**最小の是正案:** versioned schema と no-clobber の request-ID ディレクトリを定め、manifest に全ファイル hash・完全性・上記 provenance を保存し、完了時だけ原子的に publish する。

### B-11

**主張:** cpufreq の「可読性」と開始・終了 snapshot だけでは P5 を評価できず、構成 drift と観測値を結び付けられない。

**攻撃対象:** 「記録する束縛」と P5。

**具体的な失敗シナリオ:** policy と CPU の対応、値の単位、欠落と permission error、`scaling_min_freq` / `scaling_max_freq`、boost、governor が arm 間で変わっても、単なる readable=true では判別できない。P5 の「2101.0 は走行 CPU だけを符号化する」という結論も、同期した値がなければ支持されない。

**成果物影響:** レポートが cpufreq 状態を固定したと偽って方式 α/β/γ の根拠を変え、別 job で再現不能になる。

**強度:** 中

**最小の是正案:** policy→CPU mapping、exact path/value/unit/errno、driver/governor/boost/min/max/current を時刻付きで arm 前後に記録し、「不在」「不可読」「値あり」を区別する。

### B-12

**主張:** `48/48・47/48・47/48` は受理集合ではなく単なる要素数であり、裁定パッケージの中核が壊れている。

**攻撃対象:** 「成果物影響」と裁定パッケージ。

**具体的な失敗シナリオ:** βは「特定した self CPU の1要素」を除外するが、γは「任意の1帯外」を許すため、同じ47要素でも受理集合は全く違う。αも comparator の文字列を変えなくても、K回の履歴から最小値だけを残すため、raw K×48 履歴に対する意味的受理集合を拡張する。「述語を緩めない」は構文面だけの主張である。現行 comparator は method も厳密比較するため、取得意味の変更面も無視できない。

**成果物影響:** ユーザーが異なる受理集合を同値だと誤認し、gate の過剰受理・過剰拒否と凍結 bytes 再発行範囲を誤裁定する。

**強度:** 強い

**最小の是正案:** 各方式について、入力領域、量化条件、受理式、最小反例、実測 pass/fail、残余不確実性、変更対象となる method/schema/predicate/frozen artifact/pin、撤回・再発行コストを表にする。

### B-13

**主張:** 新規 evidence JSON が非規範・非 certification 成果物だと機械可読に区別されず、将来 consumer が calibration/receipt と誤用できる。

**攻撃対象:** `output/insights/.../evidence/raw/*.json` と README、fragment の参照。

**具体的な失敗シナリオ:** 将来の glob consumer や U-2 が raw JSON を calibration 候補として読み、counterfactual γ の「pass」を正規 gate の pass と扱う。現時点では brief 自身の検索どおり当該新規 path の consumer/pin は見つかっていないため、これは仮想的懸念である。

**成果物影響:** 実験データが凍結 expected bytes や receipt の根拠へ昇格し、意図せず受理集合を動かす可能性がある。

**強度:** 弱い

**最小の是正案:** 専用 schema 名と `non_certifying=true`、`counterfactual_only=true` を持たせ、calibration/receipt と異なる形にし、現行 consumer・manifest・pin がゼロである検査結果を README に固定する。

### B-14

**主張:** valid な `REFUTED` の終了経路がなく、成果物一覧の F108 fragment は成功時文言「因果立証済み」と矛盾している。

**攻撃対象:** 成果物欄の worklog/failures fragment。

**具体的な失敗シナリオ:** A1で妥当な反例が1件出た場合、raw/README を残す一般記述はあるが、台帳には「因果立証済み」を追記する指示しかない。実装者は反証を捨てる、成功に丸める、fragment を作らず wave を宙づりにする、のいずれかになる。

**成果物影響:** F108 が反証と逆の事実を正本化するか、失敗実験が台帳から消え、U-2 が因果不明のまま進む。

**強度:** 強い

**最小の是正案:** `VALID+CONFIRMED`、`VALID+REFUTED`、`INVALID/INCONCLUSIVE` の3終端を明記し、全分岐で raw・README・hash 参照を残す。F108 には実際の結論と最小反例だけを追記する。

### B-15

**主張:** 生の `ps` command line は外部入力であり、README 作成者への指示または秘密情報として混入しうる。

**攻撃対象:** 同居プロセス一覧、規律6。

**具体的な失敗シナリオ:** 他テナントの argv に prompt 風文字列や token が含まれ、後続 AI が指示として解釈するか、そのまま repository に保存する。実際にそのような argv が存在する証拠はないため仮想的懸念である。

**成果物影響:** レポート内容が外部 process に誘導されるか、proof artifact が不要な秘密情報を含む。

**強度:** 弱い

**最小の是正案:** PID、UID、comm、cgroup、affinity 等の allowlist 済み構造だけを記録し、argv/env は保存せず、全 process 情報を untrusted data と明記する。

### B-16

**主張:** 1 job・1 node の結果を Pegasus 全計算ノードへ一般化する根拠がない。

**攻撃対象:** scope の「計算ノード上」と最終裁定パッケージ。

**具体的な失敗シナリオ:** 別 bnode で driver、policy、kernel、負荷挙動が異なれば、単一 node の α 成立率を fleet の性質として使えない。現時点で node 間差の実測はないため、この一般化懸念は弱い。

**成果物影響:** 単一 job の局所結果を根拠に frozen calibration を再発行し、別 allocation で attestation が再び certified run を塞ぐ可能性がある。

**強度:** 弱い

**最小の是正案:** 今回の結論を exact node/job/config に限定し、fleet 外的妥当性は未立証と裁定パッケージへ明記する。追加 job は自動で増やさず、必要性を次の段階裁定へ返す。

## 総括

(a) 判定: **だめ**。少なくとも brief を修正するまで job を投入してはいけない。  
(b) 最重大3件: **B-1** 無効実験と反証の混同、**B-3** 非専有/F3 を admission にしていない、**B-12** 受理集合と裁定材料の定義崩壊。  
次点は B-2 の PBS/Python/永続性包絡欠落と、B-8 の α 実験操作・現行 predicate 不一致である。  
走行前に、実行妥当性と因果 verdict を分離する。  
全 arm の件数、欠測、例外、競合、可視性を fail-closed にする。  
job script、Python shim、qstat、marker、会計、rc を再現可能な成果物へ含める。  
A1/A2/A3 の反復集約・閾値・K・介入成立条件を事前登録する。  
A4 は現状のまま migration の立証に使わない。  
現行 ±2% gate と「厳密2101.0」診断を分離する。  
α/β/γ の受理集合を要素数でなく式と反例で示す。  
raw schema、hash manifest、no-clobber、非 certification 印を定める。  
`REFUTED` と `INVALID` の双方で raw・README・正しい F108 fragment を残す。  
500回は資源面で過大とは言えないが、A2/A3には統計的に不足し、配分根拠を直す必要がある。