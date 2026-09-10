## 段 3 所見の対応表

A1〜A11、B1〜B9 は各相談文書での出現順で付番した。

| ID | 所見 | 判定 | 本体での実際の対応 |
|---|---|---|---|
| A1 | 4 桁量子化が偽の飽和を作る | closed | [§4.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:206) が「整数のまま保存」「丸め値への fallback を認めない」、§7(3)(4) が違反走を失敗とする。 |
| A2 | 正値ゼロ分散で `nu=0/0` | closed | [§4.4(1)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:254) が `v_i+v_prev==0` を `indeterminate` とし、「`se=0` として通してはならない」と固定。 |
| A3 | 探索 CV は throughput の CV | closed | [§2.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:84) が明記し、[§4.7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:302) が両 CV を別 key にする。 |
| A4 | formal cohort にだけ前向き | partial | [§0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:24) は「formal cohort に対する測定規則と判定規則だけ」と限定した。ただし探索値を根拠に選ばれた CV gate 0.02 が非前向き一覧から漏れる。所見 8。 |
| A5 | 上位選言は恒真 | closed | [§3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:127) が「選言は科学的主張ではない」「反証可能な主張は全 workload で位置が存在する」と訂正。 |
| A6 | 個々の規則は恒真ではない | closed | [§4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:254) と [§7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:690) には、それぞれ偽になる観測が存在する。 |
| A7 | correctness・欠測契約が弱い | partial | WAL の `certified` を権威とする点と 24 cell × 5 rep は [§4.6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:288) に入った。しかし field 範囲、rep index、genome・attempt 結合、correctness mode が不足。所見 5。 |
| A8 | binary 相異要求は先例相当 | closed | [§4.6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:298) と §5 `binary_identity` が全 8 genome、完全 SHA、全相異、集合完全性を要求。 |
| A9 | docs-only はまだ走行を拘束しない | closed | [§1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:37) が「consumer はまだ存在しない」「拘束していると書いてはならない」、[§8.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:715) が投入禁止を明記。 |
| A10 | 探索値混入を機械判別できない | partial | [§4.8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:310) は admitted WAL 再構成と出所 field を要求した。ただし値の一致条件、WAL record digest、出所を自己申告でなく導出する規則が無い。所見 7。 |
| A11 | pointwise meaning witness 不在 | closed | 技術的には未解決だが、[§3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:124) と [§9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:736) が主張範囲外として明示した。 |
| B1 | 格子点が raw hole へ落ちる | closed | [§4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:149) が物理値と raw を分離し、`[1000,2999]` を発行禁止域とした。 |
| B2 | 判定入力 field 契約が無い | partial | §5 `analysis_input_contract` は追加されたが、既存 loader 相当の型・範囲・結合条件までは固定していない。所見 5。 |
| B3 | `median_abort_rate` が誤値 | closed | [§2.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:61) と §5 は 5 rep の生配列へ置換し、中央値ラベルを廃止。 |
| B4 | 探索値が 5% を通る懸念 | closed | [§2.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:91) が探索低下を 30.4〜37.7% と開示し、正式 verdict と分離。 |
| B5 | 8944 終端二分は検出力不足 | closed | 8944 を廃止し、[§4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:133) を上限アンカー半オクターブに変更。§4.4 に `U_flat` gate も追加。 |
| B6 | 量子化・正値ゼロ分散 | closed | A1・A2 と同じ対応で、元の穴は閉じた。別のゼロ abort 穴は所見 4。 |
| B7 | 時間枠超過 | closed | [§4.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:202) は 8 genome の実績 11 分と既存 cap を保持。 |
| B8 | 既存系列との衝突 | closed | [§8.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:723) が新 identity/schema/stem と既存 3 系列不変を固定。 |
| B9 | `check_docs.py` は本文を検査しない | not-addressed | [地図追記](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md:29) はあるが、checker 緑が本文検査の証拠でないという限定は両成果物に無い。scope 外 nit のまま。 |

親裁定 R1〜R14 の反映状況は次のとおり。

| 裁定 | 判定 | 本文照合 |
|---|---|---|
| R1 | partial | 上限アンカー式は反映。ただし裁定の `3536/7071` に対し本文は `3535/7070`。本文の方が式の正しい丸め結果。 |
| R2 | closed | 境界 1000 を測定し、6 tail 区間だけを述語対象にした。 |
| R3 | closed | 整数 counter、全精度再計算、fallback 禁止。 |
| R4 | closed | 全ての分散和ゼロを `indeterminate` とした。 |
| R5 | closed | `U_flat > 0.05` を機械 spec に含めた。ただし分類設計に新欠陥。所見 1。 |
| R6 | partial | field 契約と WAL 権威は追加されたが、先例相当の結合・範囲契約は未達。 |
| R7 | closed | throughput/abort CV を分離し、量子化率を精度根拠にしない。 |
| R8 | closed | 探索値は全 rep 生配列。 |
| R9 | partial | 指摘された 3 選択は開示したが、CV gate の選択時点が漏れた。 |
| R10 | closed | 効力限定と consumer 発火前の投入禁止を明記。 |
| R11 | partial | 出所 field と WAL 再構成はあるが、汚染値が自己申告できる。 |
| R12 | closed | raw hole と物理/raw 対応表を明記。 |
| R13 | closed | 上位選言を分類とし、反証可能な主張を分離。 |
| R14 | closed | 冒頭・§3・§9 が「機序ではなく記述」と一貫して限定。 |

## 所見

### [real] [must-fix] `indeterminate` が明白な継続低下まで吸収する

根拠: [§4.4(2)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:259) は `U_flat > 0.05` なら観測傾きに関係なく先に `indeterminate` とする。例えば両端 `cv=0.019`、`qhat=-1` なら CV gate 0.02 は通る一方、平坦時の検出力は不足する。しかし観測値は倍増当たり約 50%の低下で、上側信頼限界を導入すれば 5%超の低下を十分支持し得る。それでも現規則では `indeterminate` になる。

成果物影響: 強い継続低下を示す区間が非飽和の根拠から消え、`not-observed-*` ではなく `indeterminate-in-region` へ変わる。

提案: `qU=qhat+t*se` と低下率の同時下限を追加し、「上限が 5%以下=飽和」「下限が 5%超=継続低下」「どちらでもない=indeterminate」の三分割にする。両側分を含む多重度も本文と §5 で固定する。

### [real] [must-fix] aggregate verdict が排他的でなく、結果後に選べる

根拠: [§4.5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:275) では、`indeterminate` 区間が 1 件あり、別の場所で全 workload に連続 2 飽和区間があれば、`saturated-in-all-workloads` と `indeterminate-in-region` の両条件を満たす。「有効な workload」も定義されていない。§3 の「存在するか、現れなかったかを報告する」とも整合しない。

成果物影響: 同一の 120 observation から異なる aggregate verdict と headline を合法的に発行できる。

提案: workload 単位を `saturated` / `not-observed` / `indeterminate` の完全排他的な状態にし、早い区間の indeterminate が「最初の位置」を不明にする場合も定義する。その直積から aggregate verdict を一意に導出する。

### [real] [must-fix] 連続 2 区間の局所平坦を tail の「飽和位置」と呼んでいる

根拠: [§4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:266) は最初の連続 2 飽和区間だけで位置を発行し、その右側が平坦なままかを要求しない。1250→1768→2500 が平坦でも、2500→3535 以後に大きな低下が再開する観測は §7 の上昇失敗に当たらず、1768 を「飽和位置」と報告する。

成果物影響: 継続的には飽和していない workload の location、bracket、全 workload verdict が飽和へ反転する。

提案: 位置から 9999 までの全 determinate 区間が飽和であることを要求する。局所 2 区間だけを意図するなら、主張名を「局所平坦区間」に狭める。

### [real] [must-fix] 全ゼロから正値への遷移が machine failure になっていない

根拠: [§4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:269) は「全ゼロから正値へ上がる区間: 非単調として扱う (§7)」とする。しかし §7 と §5 `failure_conditions` が無効化するのは `qL>0` だけであり、`log(m_i/0)` では `qL` 自体が定義できない。

成果物影響: 同じゼロ→正値観測が consumer により `invalid`、`indeterminate`、解析エラーのいずれにもなり得る。

提案: log 計算より先に適用する直接の failure item として `all-zero-to-positive` を列挙し、cohort 全体を `invalid` にする。

### [real] [must-fix] correctness・欠測契約が先例の実 loader よりまだ弱い

根拠: 本体 §5 は配列型を置くが、非負整数 counter、`aborts+commits>0`、正 throughput、rep index=`0..4`、canonical genome・raw・label・attempt の一致、verify record 内部の exact field を固定していない。対して現行実装は [期待 genome 集合、重複、attempt-bound record、rep index](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1023)、[正 throughput と abort 範囲](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1063)、[WAL verify の `certified`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1080) を明示的に検査する。また本体は先例 §5 の `correctness_mode="legacy+performance"` も落としている。

成果物影響: 負 counter、ゼロ分母、誤った rep/genome 結合、弱い correctness mode の observation が formal 値と verdict に入り得る。

提案: §5 に exact 型・範囲・集合・結合述語と correctness mode を追加し、どれか不一致なら cohort 全体を `invalid` とする。

### [real] [must-fix] 3 job 間の環境・source・toolchain 同一性が固定されていない

根拠: [§9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:743) は Pegasus 計算ノード条件へ主張を限定するが、§5 に environment contract、calibration、site、single-tenancy の受理条件が無い。§7(10) の source/toolchain 同一性は resume 内だけで、3 workload 間には掛からない。現行実装は投入前に [single tenant と calibration 一致](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/orchestrator/campaign/backoff_extended_sweep.py:1339) を要求し、各 campaign identity に environment contract を結ぶ。

成果物影響: 異なる環境・source・toolchain の workload を混ぜた 24 cell が正式 cohort として受理され、全測定値と aggregate verdict が変わり得る。

提案: 3 campaign lock 間で一致させる source digest、toolchain manifest、environment contract、calibration identity、prereg/spec identity を §5 に列挙する。

### [real] [must-fix] provenance field が自己申告値のままで汚染を止めない

根拠: [§4.8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:310) は field の存在だけを要求する。`source_run_kind=="t2500-tail-formal"`、campaign lock との digest 一致、attempt/rep の WAL envelope からの導出、record digest が規定されていない。汚染入力が自分を formal と名乗る経路が残る。

成果物影響: 探索 rep や別 campaign の rep が formal CV、`qL`、`U`、location、verdict を変更し得る。

提案: provenance は observation payload から信用せず admitted WAL envelope から導出し、trusted campaign lock と exact equality を取る。WAL record digest と canonical genome も必須化する。

### [real] [must-fix] `spec_sha256` の対象 bytes が未定義

根拠: [§0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:17) と [§8.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:725) は spec SHA を要求するが、JSON 本文だけ、code fence 込み、marker 間全体、canonical JSON のどれを SHA-256 に掛けるかを定めていない。

成果物影響: 同じ文書を使った走行が consumer の hash 解釈だけで valid/invalid に分かれる。

提案: UTF-8、改行、開始・終了 offset、fence 除外の有無を逐語で固定する。document blob SHA も raw file bytes か Git blob payload かを明記する。

### [real] [must-fix] 非前向き一覧から CV gate 0.02 の選択が漏れた

根拠: 本体 [§0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:31) と §5 `not_prospective` は 3 項だけを列挙する。一方、段 2 plan は [0.02 を探索最大 CV の約 3 倍として選んだ](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/plan.md:153)。その最大値が throughput CV だったという指摘を受け、根拠だけが本文から消えた形である。

成果物影響: §5 `preregistration.not_prospective` と将来 report の登録区分が、探索非依存から探索後選択へ変わる。

提案: `two-percent-cv-quality-gate-choice` を非前向き一覧と §2.3 に加え、誤った throughput CV 根拠で選ばれたことも開示する。値を維持するかは別判断とする。

### [real] [nit] §6 の `U_flat` 約 3%は許容した abort 精度根拠から導けない

根拠: [§6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:681) は探索 CV を使って約 3%とするが、開示した最大 CV は throughput の値である。abort CV は量子化率からしか作れず、[§4.7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:307) 自身が精度根拠への使用を禁じる。

成果物影響: formal の受理集合は変わらず、格子選択理由の参考数値だけが削除または「量子化値による非規範的試算」へ変わる。

提案: 約 3%・9%を非規範的な量子化値試算と明記するか削除する。

### [real] [nit] 半オクターブ区間の記載範囲が数値と一致しない

根拠: [§4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:161) は対数比を `0.3465〜0.3467` とするが、登録値からの実値は `0.346422567...〜0.346724613...` である。

成果物影響: 格子・判定値・受理集合は変わらず、説明値だけを `0.3464〜0.3468` などへ訂正する。

提案: 実 min/max を記載する。

### [real] [nit] 2000・4000 の除外で独立な再現性アンカーを失った

根拠: [§2.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:101) は再測定する探索 abscissa を 9999 だけにした。正式推定へ探索標本を混ぜない点は健全だが、2000・4000 の独立 cohort 間差を同一座標で評価できなくなった。

成果物影響: formal report から探索→formal の 2000・4000 における再現性比較値と参照が消える。主 saturation verdict は直接変わらない。

提案: 点を戻す必要まではないが、「探索結果の再現性を検証する設計ではなく、exact anchor は上限 9999 のみ」と §3/§9 に明記する。

### [real] [nit] 境界区間の除外により最初の位置は左打切りになる

根拠: 1000→1250 を述語から外し、連続 2 区間を要求するため、[§4.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:266) が発行できる最初の位置は 1768、bracket は `[1250,2500]` である。1000 直後に始まった plateau の onset を bracket できない。

成果物影響: 最初の saturation location/bracket は 1768/[1250,2500] より左へ解像できない。

提案: 境界区間を戻さないなら、この左打切りを主張制限として明記する。

### [real] [裁定パッケージ候補] 親裁定 R1 の literal が生成式と矛盾する

根拠: [adjudication R1](/home/SFC/tanab/.claude/jobs/8a4f2a40/tmp/t2500/adjudication.md:25) は式 `round(9999/2^(k/2))` と同時に `3536/7071` を載せる。しかし四捨五入結果は本文どおり `3535/7070` であり、測定順も本文の値で正しく再生成できる。

成果物影響: 次 wave が裁定 literal を優先すると、formal point set、raw 値、測定順、spec SHA が本文と異なる。

提案: 本体の `3535/7070` は変えず、親裁定側へ算術 erratum を返す。

### [refuted] [nit] `indeterminate` は結果後に任意選択できる分類ではない

根拠: 区間単位では `v_i+v_prev==0` または `U_flat>0.05` という機械的条件であり、分散和が正かつ `U_flat<=0.05` なら偽になる。問題は条件自体の任意性ではなく、強い低下まで吸収する設計と aggregate precedence の欠落である。

成果物影響: 条件を裁量フラグへ置換する必要はない。

提案: 数式条件は維持し、所見 1・2 の三分割と排他的集約だけを直す。

### [refuted] [nit] 機序・9999 超・性能認証への主張拡張

根拠: 冒頭の「記述であって機序ではない」、[§3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:116)、[§9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/b10-backoff-static-tail-preregistration.md:736) は一貫して機序、9999 超、性能認証、他環境転移を除外している。地図の [追記](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2500-backoff-tail-prereg/docs/README.md:29) も 7 点+境界 1 点と整合する。

成果物影響: 主張範囲を追加で狭める変更は不要。

提案: 局所平坦を「飽和位置」と呼ぶ所見 3 だけを別途修正する。

## 総括

元の量子化、正値ゼロ分散、raw hole、binary 完全性、docs-only の効力限定は概ね閉じている。  
ただし現状は `indeterminate` が明白な継続低下まで吸収し、aggregate verdict も排他的でないため、事前登録の主要判定が一意でない。  
連続 2 局所区間を永続的な tail saturation と呼ぶ点、ゼロ→正値の未定義経路も must-fix である。  
correctness・欠測・provenance・環境束縛は既存実装の実 gate より弱く、汚染入力が受理集合を緩められる。  
親裁定の `3536/7071` は算術誤りで、本文の `3535/7070` が正しい。2000・4000 の除外は主 verdict より独立再現性を失う変更である。  
read-only の静的照合のみを行い、pytest・本走・性能測定は実施していない。