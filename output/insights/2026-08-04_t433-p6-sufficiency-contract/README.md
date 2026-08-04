# [T-433] P6 意味的充足契約 — 「実装済み」認定の基準の案 (2026-08-04)

## 0. この文書の地位 (先に読むこと)

- 本文書は **D150 決定 (6)(a) が「本 D では定義しない」と明示した空白** — 「実装のふりをした
  非適用」の判定基準、すなわち P6 を「実装済み」と認定する意味的充足契約 — を埋める**案**である。
- **採否はユーザー裁定の事項であり、本 wave は採用を主張しない** (裁定パッケージは
  `s4-adjudication.md` §4)。採用されるまで規範ではない。採用時に変わるのは cap-lift の
  **規範上の**受理集合だけで、機械受理集合・production 挙動・凍結 bytes は不変である。
- D138 (P6 = 明示的帰納契約) と D150 (非適用の二分・状態と承認の分離) を supersede しない。
  P6 契約設計の正本は `output/insights/2026-08-03_t244-p6-contract/README.md` (以下「P6 設計」)。
- 実装・機械 gate・status field・cap-lift 結線は作らない。`MAX_APPROVED_GENERATIONS = 1`
  (D114) は不変。
- 起草の経緯: 段 2 プラン (`s2-plan.md`) を敵対レンズ 2 本 (`s3-lensA.md` / `s3-lensB.md`、
  ともに NO-GO) が攻撃し、全 18 所見 real を反映した v2 が本文である (裁定は `s4-adjudication.md`)。

## 1. 認定対象と型境界

- 認定対象は「**申請された revision の P6 実装が、D138 の契約の意味を実際に実現しているか**」で
  ある。ファイル・test の存在確認ではなく、申請者の宣言・実装 path 名・test node 名は証拠に
  数えない (D150 決定 (4-b) の継承)。
- P6 実行結果の 4 値型 `P6Derived | P6NotDerived(code) | P6NotApplicable(code) |
  P6ContractError(code)` は不変 (D138 決定 (3))。`NOT_IMPLEMENTED` / `NOT_CLAIMED` は
  **非適用理由の状態語**であり 4 値結果ではない (D150 決定 (3))。両者を混同する検査・calibration を
  書いてはならない。
- 意味的充足を認定しても、それだけでは `NOT_CLAIMED`・P6 充足・cap-lift 承認のいずれも成立しない。
  認定は cap-lift 前提条件の判定の**入力の 1 つ**である。
- 証拠不足時は状態を再分類せず**承認を保留する** (fail-closed、D150 決定 (4-b))。

## 2. 入力の実在台帳 (DW-O13)

認定・calibration が参照するデータの現存性。**この表は判定可能性の前提であり、「存在する」は
「P6 の証拠として使える」を意味しない。**

| データ | 所在 | 今日の状態 |
|---|---|---|
| WAL 外形・stage 修飾 field | `orchestrator/campaign/model.py` (`variant`/`stage`/`env_tag`/`payload`) | 存在する |
| cycle witness schema | terminal `abort` の `payload.verify.anomalies[]` (`orchestrator/verifier/report.py`) | schema は存在する |
| `verify_done.payload.anomalies` | 整数 (witness list ではない) | 存在する — 二義化禁止 (P6 設計 §3.2.1) |
| integrity counters | `lock_coverage/write_intent/permutation_violations` | raw counter は実測値まで存在する |
| canonical 5-bit IR | `orchestrator/campaign/reflux_ir.py` | コードは存在するが P6 へ未束縛 |
| 構造化 IntegrityWitness | — | **存在しない** (U5 起票済み) |
| P6 固有入力/出力 (hypothesis、matrix、`marginal_keys` 等) | — | **将来実装が作る** |
| candidate 帰属が真の cycle witness 実例 | — | **存在しない** (fixture 由来 1 件は帰属が偽) |

親の前提実測「P6 実装 0 件」の根拠は、識別子 4 種 (`derive_p6_cut` /
`PrecommittedHypothesis` / `P6Derived` / `witness_class`) の Python 内文字列不在 +
D150 決定 (4-b) の記録 + `docs/phase3.md` の記載の**合成**である。文字列不在単独を意味的不在の
証明としない (レンズ A #8)。

## 3. 意味的充足の必須条項

凡例 — 分類は**判定可能性**であり、checker の実装・結線の有無は §2 が持つ (レンズ B #10)。
**[コア]** = 規律 2 由来の削除不可条項: §6 の排除規則を適用できず、反転変異を書けない場合は
条項を落とすのではなく**認定不可** (fail-closed)。

| ID | 必須条項 | 分類 |
|---|---|---|
| SC-01 | stage 修飾 field だけを読み、ordered WAL 上で `variant`・`env_tag`・workload・attempt を束縛する。曖昧なら `P6NotDerived(ambiguous-wal-binding)` | 定義後ならできる |
| SC-02 | evidence を CycleWitness + 3 種 IntegrityWitness の閉じた和とし、**4 adapter 各々に最低 1 個の `P6Derived` 正例到達**を要求する。未知 kind は `P6ContractError(unknown-witness-kind)` | 定義後ならできる |
| SC-03a | witness の内部整合検査 (長さ・辺の隣接・reason 型) | 定義後ならできる |
| SC-03b | rotation 正規化 (辞書式最小、辺方向は同一視しない) | 定義後ならできる |
| SC-03c | key 分割・version 等値関係の保存 (捨てる情報と残す情報が P6 設計 §3.3 のとおり) | 定義後ならできる |
| SC-03d | 複数 anomaly の class-set 規則と切詰め witness の拒否 | 定義後ならできる |
| SC-04 | `hypothesis` は source failure 前に hash 固定、`extrapolation_set` 非空、反証 test・evidence plan を持つ | 定義後ならできる |
| SC-05 | `P6Derived` は `B \ C_exact ≠ ∅` の場合だけ。`marginal_keys` は差集合と完全一致。空なら `P6NotDerived(no-marginal-effect)` | 定義後ならできる (入力 artifact が将来所有のため。演算自体は純粋な集合演算) |
| SC-06 | 事前登録した反証 test の失敗で `P6NotDerived(hypothesis-falsified)` + origin seal。仮説差替え禁止 | 定義後ならできる |
| SC-07 | handler は全入力で 4 値のいずれかを返し、固定 corpus と検査者生成 hidden case の双方で exact verdict。case ID は handler 入力に渡さない | 定義後ならできる |
| SC-08a **[コア]** | qualifying red の exact cut は P6 と独立・先行して append され、P6 の失敗で外れない | 定義後ならできる |
| SC-08b **[コア]** | P6 禁止集合に無い候補も、**候補 admission の全入口**で通常 verifier を必ず通す。入口の閉集合 inventory (D114 の三入口先例に整合) を認定 package が含み、各入口で verifier call を検査する | 定義後ならできる |
| SC-09 | 4 値結果と状態語を混同しない。意味的認定済みかつ明示的非主張の構成だけが `NOT_CLAIMED` 候補。欠落・曖昧を既定の `NOT_CLAIMED` にしない | 人間 gate |
| SC-10 | 独立検査者による再計算・再実走 (§7)。申請者の宣言・path 名・test node 名は証拠 0 | 人間 gate |
| SC-11 | 全必須条項 (合接条項は conjunct 単位) に最低 1 個の判定反転変異を対応させ、生存変異ゼロ (§6) | 定義後ならできる |
| SC-12 **[コア]** | **admission 結線**: `P6Derived` の install 後、`forbidden_candidate_keys` 内の候補が次 admission で generalized cut を唯一の理由に build 前 reject され (query は消費)、P6 無効の対照アームでは同じ候補が admission を通る。`P6_PENDING` 中は admission が閉じる (P6 設計 §3.9) | 定義後ならできる |

SC-12 が本契約の中心である (レンズ A #1 ≡ B #1): 「正しい集合を返すこと」(SC-05) と
「受理集合が実際に変わること」(SC-12) は**別の条項**であり、後者なしの認定はあり得ない。

## 4. 正負 calibration の具体ケース

候補キーは将来 fixture 上で `k0=("izanagi-trigger-gate-ir/v1","00000")`、
`k1=("izanagi-trigger-gate-ir/v1","10000")` とする。C-01〜C-10 の入力・期待 verdict・現存性は
`s2-plan.md` §5 の表を契約の一部として継承する (C-01 Derived-cycle / C-02 rotation /
C-03 no-marginal / C-04 late-precommit / C-05 falsified / C-06 truncated / C-07 invalid-witness /
C-08 unknown-kind / C-09 environment / C-10L/W/P adapter 正例)。v2 での変更・追加:

| case | 内容と期待 | 出所 |
|---|---|---|
| C-02b〜C-02e (class-separation) | C-01 の witness を、正規化が**保存すべき次元 1 つだけ** (key 分割 / version 等値関係 / 辺方向 / reason 重複度) 変えた変種。期待 = **C-01 と異なる** `witness_class_id`。射影表駆動の暗記実装はどれかで落ちる | レンズ A #2 |
| C-11 (再定義) | handler calibration から**外す**。claim 有無の状態分類は §8 の認定手続で、cap-lift 申請の構成照合例として検査する (4 値型と状態語の混同を calibration に持ち込まない) | レンズ A #7 |
| C-12 | P6 禁止集合外の候補に通常 verifier が走り reject + exact cut append。**全入口** inventory の各入口で検査 | レンズ A #4 |
| **C-13 (admission A/B 対)** | 同一 origin・同一候補列で、(アーム 1) `P6Derived` install 済み → `k1` が generalized cut を唯一の理由に build 前 reject、(アーム 2) P6 無効 (enforcement off) → 同じ `k1` が admission を通過し build に進む。両アームの差分が generalized cut 以外に無いことまで検査 | レンズ A #1 ≡ B #1 |

### 偽物の最低棄却集合

`s2-plan.md` §5 の 7 行 (空 handler / 恒一 verdict / blanket error / 未知 kind 無視 /
常時 `NOT_CLAIMED` / 一律エラー adapter / case ID 暗記) を継承し、v2 で 2 行を足す:

| 偽物 | 落ちる case |
|---|---|
| **集合を返すだけで admission に結線しない実装** (enforcer no-op) | C-13 アーム 1 で `k1` が reject されず落ちる |
| **形状射影の表駆動実装** (rotation だけ処理し key 分割・version 関係を捨てる) | C-02b〜C-02e で class が分離せず落ちる。検査者の hidden case が射影の粒度を跨ぐ |

## 5. 認定 package (申請者の提出物) と発火イベント

認定手続の**発火**は次で定義する (レンズ B #2 を閉じる): P6 実装 wave の land 後、cap-lift
申請の前に、申請者が**認定 request** を起票した時点。request は以下を含む。

1. 対象 revision の commit SHA と、P6 実装・全入口 inventory・calibration corpus・
   変異対応表 (提案) の path。
2. corpus と変異対応表の **hash 固定の証拠** (認定 request より前の commit に含まれること)。
3. 検査の実行環境の指定 (実装時点の環境 runbook に従う)、工数上限、timeout、
   infrastructure failure の扱い (mutant survival と区別し、認定判定に数えず retry する)。

request が無い間、認定手続は発火せず、P6 の状態判定は D150 決定 (4-b) の既定
(基準はあるが認定記録が無い → 承認保留) に従う。

## 6. 非空の限界効果を示す変異 (排除規則 v2)

対応表の正式列は `条項ID / 変異対象 / 破壊変異 / 対応case / 無変異期待 / 変異後観測 /
KILLED判定 / 検査者` とする。`s2-plan.md` §6 の代表変異を継承し、次で運用を固定する
(レンズ A #3、B #6 を閉じる):

1. **kill 判定は calibration verdict の反転のみ**で行う。実装が calibration 検査用に置く
   副作用 (compliance bit 等) は判定に数えない。
2. **合接条項は conjunct 単位**で変異を対応させる (SC-03 は a〜d に分割済み。SC-08 も a/b の
   2 義務に分割済みで、`または` による片側充足を認めない)。
3. **変異の最終選択権は独立検査者にある。** 申請者の変異対応表は提案であり、検査者は
   hidden 変異・hidden case を自分で追加する権利と義務を持つ。corpus・対応表は認定 request 前に
   hash 固定されているため、実装を変異に合わせて後から調整できない。
4. **排除規則**: 一般条項は、当該 conjunct だけを破壊した変異が最低 1 件の calibration 判定を
   PASS→FAIL へ反転させなければ、意味的効果を示せないため認定根拠に使わず契約から削除する。
   条項を残すために期待値を変異実装へ合わせてはならない。**[コア] 条項 (SC-08a/b、SC-12) には
   この削除を適用しない** — 反転変異を書けない場合は認定不可とする (fail-closed)。
   規則を通る正例: SC-05 は「`B \ C_exact` 空検査の恒真化」変異が C-03 を反転させるので残る。
5. SC-10 (検査者独立性) 自体の検証は変異でなく §7 の attestation で行う (手続の仮想変異という
   自己参照を置かない)。SC-11 の表完全性は、検査者が契約本文と対応表を突合する人間 gate とする。
6. 冗長二重実装で片方除去の変異が生存した場合、それは条項の恒真性ではなく**実装の冗長性**であり、
   検査者は両実装同時変異で再判定する (DW-M02 の既存規律と同型)。

## 7. 独立検査者

独立性 = 申請者の期待値・会話履歴・mutable workspace を引き継がない fresh context。ただし
**fresh context の名乗りだけでは独立性を認めない** (レンズ A #6 ≡ B #7)。読むもの・再計算する
もの・自分で走らせるもの・証拠に数えないものは `s2-plan.md` §7 を契約の一部として継承する。
v2 での追加:

- 検査者は**監査可能な attestation** を認定記録に添付する: 検査者 context の素性 (session 記録)、
  申請者から受け取った入力の閉集合とその digest、workspace 非継承の宣言、hidden case・
  hidden 変異を検査者自身が選択した旨とその一覧。
- attestation の真正性は最終的に人間 gate が確認する。本契約は偽装を機械的に不可能にすると
  主張せず、**偽装が事後監査で反証可能な証拠を残すこと**を要求する。
- 検査者が結論を出せない入力欠損・環境障害時は fail-closed (認定不可ではなく**判定保留**とし、
  infrastructure failure は mutant survival と区別する)。

## 8. 認定記録と失効 (T-434 との境界)

認定の出力は**認定記録 (accreditation record)** — 機械 status field ではなく docs artifact — と
する (レンズ B #3/#5 を閉じる)。最小 field:

```text
subject_revision_sha, contract_version_hash, corpus_sha256, mutation_table_sha256,
toolchain_note, verdict (accredited | not-accredited | withheld),
examiner_attestation_ref, calibration_results_ref, mutation_results_ref, date
```

- 本契約が定義するのは**この最小 interface と意味だけ**である。receipt schema・置き場所・
  runbook / journal / report / 層 3 / producer / completeness gate への結線は **T-434 が所有**する。
  T-434 の receipt は認定記録への参照 (path + hash) を収容し、人間の PASS 宣言を無検証で
  信じない。
- **失効**: 認定記録は `subject_revision_sha` に束縛される。cap-lift 承認者は申請時に、申請対象
  revision と認定記録の一致を照合する義務を負う。不一致 (実装・corpus・契約版のいずれかが
  変わった) なら認定は無効で、承認は保留する。自動失効検知の機械 gate は本契約では作らない。
- 状態分類 (旧 C-11) の照合例: 同一 revision・同一 origin で、claim を宣言した申請は
  `NOT_CLAIMED` に分類できず、P6 の 4 値実行結果と認定記録で判定する。明示的非主張の申請だけが
  `NOT_CLAIMED` 候補になり、その場合も認定記録 (意味的充足) が無ければ D150 決定 (4-b) の
  保留に落ちる。

## 9. V1 裁定案 — `NOT_CLAIMED` の射程

u2-na-bifurcation の 3 択 (a) per-run gate / (b) `NOT_CLAIMED` では cap を開けない /
(c) global 免責は、**いずれも「run」の量化が未定義でそのままでは判定可能でない**
(レンズ A #5 ≡ B #4: (a) は tuple 内 standing 免責にも U2 の実質無効化にも読め、(c) は
calibration facade + 常時非主張で限界効果ゼロのまま cap が開き、(b) は「構成」の細分化で
claim 用構成と実運転構成を分離できる)。よって量化を明示した **(a′)** を推奨する:

> P6 状態 (`NOT_CLAIMED` を含む) の**判定単位は cap-lift 申請**とする。申請は revision・origin・
> 運転構成・claim 有無を固定し、承認者が申請時に判定して receipt (T-434) に束縛する。
> **run 単位の義務は receipt との conformance** とする — 承認の下で走る各 run は receipt の
> 構成と一致しなければならず、一致しない run (claim の切替・revision 変更・origin 変更を含む)
> は承認の外であり、承認上限 1 (D114) に落ちる。`NOT_CLAIMED` は申請をまたいで持ち越さず、
> standing な global 免責にしない。

- U2 (ユーザー裁定: `NOT_CLAIMED` だけを免責) は申請評価の中で保存される — `NOT_CLAIMED` は
  失敗に数えない。
- D150 決定 (6)(b) の残余「`NOT_CLAIMED` 構成に多世代を許してよいか」はこの定式化でも残る。
  **(a′) は許す側の答え**である (他の 9 前提条件と意味的充足の認定を要した上で)。許さないなら
  択 (b) だが、免責の唯一の用途が消え U2 を実質空にするため推奨しない。(c) は却下を推奨する。
- conformance 照合の実装 (receipt field・検査) は T-434 と将来の機械束縛 wave の所有である。

## 10. 択一 (裁定パッケージ)

判断点は 4 件 — U1 契約案の採否 / U2 V1 = (a′) / U3 adapter 正例要件 = (b) /
U4 calibration 新鮮性 = (b)。詳細と推奨は `s4-adjudication.md` §4。

## 11. 書かないもの・決めないもの

- **将来の P6 実装 wave が所有**: handler、4 adapter、構造化 IntegrityWitness と discriminator、
  normalizer、hypothesis/validation artifact、calibration fixture、mutation harness、
  全入口 inventory、exact-cut/P6/verifier/admission 統合。
- **T-434 が所有**: cap-lift receipt の schema・置き場所、認定記録への参照形式、P1〜P10 status・
  裁定参照・witness hash の束縛、全 consumer 結線。
- **T-435 が所有**: 段 8c 事前登録文書の改訂。本契約は同文書を編集しない。
- **本契約が決めない**: crash 回復状態機械、replicate 数、schedule/seed policy、generator への
  0 bit 証明、sort witness の同値関係、`Bmax`・build 計数 (D138「確定していないこと」の継承)。
- **本 wave で行わない**: コード・テスト・設定変更、機械 gate / status field 新設、cap-lift 結線、
  `MAX_APPROVED_GENERATIONS` 変更、pytest 実測 (docs 検査を除く)。

## 12. ファイル

| ファイル | 内容 |
|---|---|
| `README.md` | 本文 (契約案 v2 = 段 4 裁定反映済み) |
| `brief.md` | 段 1 brief (提示時点の親 provisional (P1)〜(P3) を含む。(P2)(P3) は段 4 で訂正) |
| `s2-plan.md` | 段 2 プラン (codex、契約案 v1。§5 のケース表・§6 の変異表・§7 の検査者手続は本文が継承) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対レンズ (ともに NO-GO、計 18 所見) |
| `s4-adjudication.md` | 段 4 裁定 (全所見 real・採用、実装しない裁定、裁定パッケージ U1〜U4) |
