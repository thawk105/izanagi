結論は **NO-GO**。独立再計算では `0.8462 / 0.8080` と `N=13, R=10` の最小性は再現した。一方、修正後も blocker は **6 件**残る。特に、node×round 交互作用の判定が現モデルでは推定不能であり、12-node 脱落解析も状態規則上は実行不能である。

## 対応表

### レビュー A

| ID | 判定 | 現物による根拠 |
|---|---|---|
| A-1 | **closed** | `τ_U²=max(0,(MS_A/F_0.05−MS_E)/R)` の単一式、α、切捨て、代替構成禁止が固定され、assurance も同じ式を使う。[protocol §1.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:47) |
| A-2 | **partial** | 閾値・attempt=2・順序付き対応表は入ったが、validity #8 が未列挙の将来 presence matrix を参照し、開始後不完全／attempt無効／12-node終端の状態が矛盾する。[§5.3–§6.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:285) |
| A-3 | **partial** | `N·R` 目的下の 130 最小は正しい。しかし12-node終端は開始後失敗規則で禁止され、§4.1には未定義の再最適化分岐も残る。[§4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:208) |
| A-4 | **partial** | commit・環境契約・同一preimage retryは固定されたが、compilerは「gcc-11系」に留まり、clean source hash/source token/exact build argvはbuilder前literalでない。[§2–§3.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:103) |
| A-5 | **closed** | §5.3の全結論からfan-outとT-139感度表への写像があり、入力は`τ_U`、pilot点推定、cluster間分散と固定された。[§7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:371) |
| A-6 | **regressed** | drift方向の記述は訂正されたが、新設したnode×round交互作用gateは1観測/cellの二元配置では`MS_E`から分離不能。round同期の実装関門も無い。[§5.2–§5.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:262) |
| A-7 | **regressed** | digest・acceptance manifest・人間承認IDは追加されたが、「全関門成立まで生死確認禁止」と「生死確認receiptが関門」の循環依存が入った。[§9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:398) |
| A-8 | **closed** | runbookの「無条件」は削除され、差=加法offset、比=乗法scale、混合量には双方が残ると分離された。 |
| A-9 | **closed** | 0.6%は厳密な半分でなく、0.6239%から保守側に丸めた人間の価値判断と明記された。[§4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:210) |
| A-10 | **closed** | 1.774%の分母と、UTC日付差19日／実経過18.27日が明記された。[§0](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:16) |

### レビュー B

| ID | 判定 | 現物による根拠 |
|---|---|---|
| B-1 | **closed** | 主区間そのものに対する独立MCで full≈0.8463、drop≈0.8077となり、記載値0.8462/0.8080とMC誤差内で一致した。 |
| B-2 | **regressed** | 現在の目的関数では130が最小だが、生死確認後に`P`だけでN/Rを導き直せる条項は、新しい目的関数・tie-break・再凍結規則がなく最小性を再び可変にする。[§4.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:219) |
| B-3 | **partial** | 12-node終端解析は追記されたが、1 node脱落はrelease後失敗なので「開始後不完全」となり、§6.2が推定結果を禁じる。実効経路は閉じていない。[§5.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:301) |
| B-4 | **closed** | 測定ノードへrepo作業木を置かないことだけを構造的防壁とし、policy/argvは協調的防壁と正しく降格した。[§6.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:328) |
| B-5 | **partial** | ignored fileを含む前後validatorは必須化されたが、成功時exact集合・失敗時matrix・receipt schemaの現物は未列挙で、validityを現在は評価できない。[§6.2–§6.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:348) |
| B-6 | **regressed** | coordinator時計への変更自体は正しい。しかしspread判定はrelease後なのに「測定前無効」とされ、同状態ではrelease記録を禁じる§6.2と矛盾する。[§3.3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:164) |
| B-7 | **closed** | 3秒、2100、NUMA方針、quiet gate、20分timeout、5秒spread、attempt=2がliteral化された。bootstrapは主手続きから削除された。 |
| B-8 | **closed** | runbookは加法offsetと乗法scaleを分け、混合量に作用が残ることも式で明記した。 |
| B-9 | **closed** | `python3.10`、repo外absolute `qsub -o/-e`、repo外working/output root、argv exact検査が必須化された。[§3.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/docs/pegasus-node-variance-protocol.md:199) |
| B-10 | **未対応** | protocolは現在形の運用設計なのに`LIVING_DOCS`へ追加されておらず、実装有無の可変記述も残る。[check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t810-node-variance/tools/check_docs.py:39) |

集計は **closed 10 / partial 5 / 未対応 1 / regressed 4**。

## 指定回帰検査

### 自由度

一貫している。

- §1.1: `ν1=N−1`, `ν2=(N−1)(R−1)`
- §4.2: 同じ自由度でassuranceを計算
- §5.2: round固定効果後の同じ`ν2`

したがって `N=13,R=10` は `(ν1,ν2)=(12,108)`、1 node脱落後は `(11,99)`。

### assuranceの独立再計算

SciPy等は使わず、正則化不完全ベータの連分数からlower-tail F分位を逆算し、NumPy、固定seed、10,000,000 drawで直接評価した。

| 解析 | `F_0.05` | 独立MC | MC SE | 文書 |
|---|---:|---:|---:|---:|
| N=13,R=10 | 0.426281343799 | 0.8463304 | 0.0001140 | 0.8462 |
| N=12,R=10 | 0.406988743740 | 0.8076646 | 0.0001246 | 0.8080 |

**一致する。**文書側40万drawのSEは約0.00057／0.00062なので、差は十分その範囲内。ただし文書にMC seedがなく、4桁値の完全再現はできない。

### 「総測定回数130が最小」

現在の制約、

- `R≥10`
- full assurance ≥0.80
- 1 node脱落後 assurance ≥0.80
- 目的関数 `N·R`

では正しい。`N≥3, R≥10, N·R<130` の全112整数設計を列挙し、合格は0件だった。最も近い失敗例でも、

- `N=12,R=10`: drop≈0.7603
- `N=11,R=11`: drop≈0.7589
- `N=9,R=14`: drop≈0.7503

であり、MC誤差で0.80を跨ぐ余地はない。`N·R=130`では`N=13,R=10`だけが両assuranceを満たした。

ただし§4.1の生死確認後再導出を使うと、目的関数自体が曖昧になるため、この最小性はその分岐後まで保証されない。

### validity／対応表／presence matrix

矛盾がある。

- 12 completed nodeで終端解析可能とする。
- 一方、release後の失敗はすべて「開始後不完全」とし、推定結果を禁止する。
- integrity条件の一部は「全job」に要求されるため、失敗した13件目を除いて12件を解析する場合に成立しない。
- validity偽は§5.3では一律「attempt無効」だが、§6.2には「測定前無効」と「開始後不完全」しかなく、release後validator不一致等の状態が閉じていない。
- §5.4がexact一致を要求するpresence matrixは、§6.2ではまだ要求事項だけで、表の現物がない。

### round／反復

用語上は一致している。`R=10`は各nodeの10反復であり、同じ反復番号をroundとして固定効果にする設計である。

ただし実行契約は初回release barrierしか規定しておらず、roundごとの同期barrierがない。開始許容差5秒は1反復3秒より長いため、「同じround」が同じ時間帯を表す保証はない。

### §1.3と§7

用途の集合は一致する。

1. 条件付きfan-out判断
2. 共通乗法モデル下のT-139感度表

感度表の入力も`τ_U`、pilot点推定、pilot cluster間分散に固定され、補正・臨界値・cluster数変更は禁止されている。

## 新規・残存所見

### 1. node×round交互作用gateは推定不能

- **severity:** blocker
- **主張:** §5.3行2は現モデルでは評価できず、モデル破れを未決へ倒す防壁として機能しない。
- **根拠:** `y_ir`はnode×round cellあたり1観測だけで、残差自由度 `(N−1)(R−1)` はそのままnode×round交互作用の自由度である。別の交互作用MSと`MS_E`を同時に推定できず、同一視すれば条件`MS_E > 2MS_E`は発火しない。
- **成果物影響:** ノード固有ドリフトが大きくても材料差反証へ進み、ノード分散レポートとfan-out判断を過小側へ誤らせる。
- **提案:** cell内反復を追加してinteractionとerrorを分離するか、node別傾きなど独立に計算可能な診断量・閾値を定義し、区間とassuranceを再計算する。

### 2. round固定効果を支える同期が実装関門にない

- **severity:** blocker
- **主張:** 初回releaseだけでは共通時間driftをround効果へ吸収できる保証がない。
- **根拠:** §5.2は全node同期roundを要求するが、§3.3と§9の実装項目は初回barrierしか要求しない。§9の凍結対象にも§5.2がない。5秒spreadに対し1反復は3秒である。
- **成果物影響:** nodeごとに異なる実時刻の観測を同じroundとしてfitし、driftをnode差または残差へ混入させる。
- **提案:** 各roundにready/release/timeoutの二相barrierを置いてreceiptへ固定するか、ordinal roundだけで扱えるestimandへ主張を狭める。

### 3. dropout・validity・presence状態機械が閉じていない

- **severity:** blocker
- **主張:** 12-node terminal analysisは現在の規則では到達不能で、開始spread失敗も矛盾した状態になる。
- **根拠:** §5.4は12-node解析を許す一方、release後失敗を開始後不完全として主推定を禁止する。§6.2も開始後不完全の推定結果を禁じる。またspread判定はrelease後なのに「測定前無効」とされ、その状態ではrelease記録を禁じる。
- **成果物影響:** 同じ失敗から「12-nodeで結論」「attempt無効」「開始後不完全」のいずれも選べ、attempt台帳と主報告が分岐する。
- **提案:** 状態を順序付き有限表にし、release前無効／release後・測定前無効／12-node終端／開始後不完全／validを分離する。各状態のexact artifact presenceと解析可否を列挙する。

### 4. §9の承認関門が循環している

- **severity:** blocker
- **主張:** 文面どおりなら生死確認を合法的に実行できない。
- **根拠:** §9冒頭は全条件成立まで「生死確認も投入禁止」とするが、条件4は「生死確認の成功receipt」である。冒頭§0にも同じ全関門先行規則がある。
- **成果物影響:** 正式経路は停止し、進めるには関門を無視するしかなくなるため、承認IDと実験台帳の信頼性を失う。
- **提案:** builder／生死確認用のpre-authorization関門と、本走関門を二段に分ける。生死確認後のreceiptだけを本走関門へ要求する。

### 5. 生死確認後のN/R再導出に事後自由度がある

- **severity:** blocker
- **主張:** `P`観測後にどの目的関数でN/Rを変えるか、tie-break、探索範囲、再凍結が定義されていない。
- **根拠:** §4.1は目的関数を`N·R`と固定しながら、`P`だけで「同じ基準でN・Rを導き直してよい」とする。`N·R`は`P`に依存しないため、意味のある再導出には暗黙の目的関数変更が必要になる。
- **成果物影響:** liveness後に都合のよい設計へ変更でき、§2 literal、assurance表、digest、予算receiptの参照が食い違う。
- **提案:** 現在の`N=13,R=10`を固定するか、`P`を含む完全な目的関数・候補範囲・tie-break・再凍結と再承認を事前登録する。

### 6. build preimageがbinary選択を完全には固定しない

- **severity:** blocker
- **主張:** binary hashはbuild後に固定されるが、build前の候補集合がまだ広い。
- **根拠:** compilerは「gcc-11系」で、clean source/tree hash、source token、compiler executable hash、exact build argv/flagsが本文literalにない。commitだけではdirty sourceを排除しない。
- **成果物影響:** builder失敗等を見た後に別toolchain/source状態を選び、異なるbinaryのノード分散を同じprotocol名で報告できる。
- **提案:** clean-tree検査、source-tree hash/token、compiler path・SHA-256・version、完全argv/flagsをbuilder投入前artifactへ固定する。

### 7. Monte Carlo seedが未固定

- **severity:** must-fix
- **主張:** assurance表の4桁値を第三者が完全再現できない。
- **根拠:** 40万drawは固定されるがseedとRNG algorithmがない。独立10M再計算とはMC誤差内で合うものの、同じ0.8462/0.8080にはならない。
- **成果物影響:** 設計根拠台帳の数値監査で差が出る。
- **提案:** NumPy version、bit generator、seed、draw順、比較演算を固定するか、決定的数値積分で表を生成する。

## 総括

**NO-GO。残 blocker 6件。**

数値面では、自由度、`0.8462 / 0.8080`、`N=13,R=10`の130回最小性は確認できた。NO-GOの理由は数値ではなく、解析gate・round同期・失敗状態・承認順序・再設計自由度・binary preimageがまだ閉じていないことにある。

未検査の攻撃面:

- 実PBS投入、N-job barrier、round単位barrier、cancel markerの動作
- schedulerの現在状態とlive `qstat`
- 測定ノードにrepoが存在しないこと、filesystem/ACLの実効性
- 未実装validator、receipt schema、exact presence matrix
- binaryのclean-source再現性とruntime dependency照合
- 将来データに対する正規性・等分散・独立性
- pytest/build/docs全検査はread-only焦点レビューのため未実施

`git diff --check`上の空白エラーはなかった。