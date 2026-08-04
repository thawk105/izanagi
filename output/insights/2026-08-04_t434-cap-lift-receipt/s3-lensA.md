静的敵対監査の結果、レンズ A の全領域に所見がある。実走・編集は行っていない。

### 1. Q1 は receipt を機械 gate から誤って切り離している

**対象:** brief provisional 前提 Q1、設計案「producer + completeness gate」

**主張:** receipt 自体が人間作成物でも、`generations > 1` の受理条件として三入口・completeness が読む時点で、機械 gate の権威入力である。「receipt は機械 gate ではない」と分類すると、意味評価器より先に schema・reader・consumer を land できる余地が生じる。

**根拠:** `brief.md:23-24`、`s2-draft.md:173-178`。D150 決定 (6)(c) は、receipt と判定 field が無いため再検証不能だとする。

**反例・破り方の要約:** hash・親 commit・10 個の status の形式検査だけを実装し、未定義の「証拠再評価」を成功扱いすれば、見た目の整った receipt が cap を開く。

**提案修正:** receipt を「人間が署名する、機械 admission gate の policy input」と明記する。意味評価器・独立 oracle・境界変異が先に land しない限り、reader や consumer が存在しても `generations > 1` は常時拒否する依存順を裁定に入れる。

**確度:** high

### 2. receipt と witness の status 突き合わせは自己一致であり、恒真化を防がない

**対象:** 設計案「field 契約」「witness manifest」

**主張:** `prerequisite_statuses` と witness 内の同じ status を byte-equivalent に比較しても、同じ申請側が作った二つの写しの一致しか示さない。評価結果・評価器 source hash も、評価器が非空・正しいことを示さない。

**根拠:** `s2-draft.md:47-57,76-86,88-99`。D150 決定 (6)(a) は空 handler・恒真 assert でも形式要件が埋まると明記する。D121 決定 (7) も P1・P2・P3・P5・P7 は検査対象の閉集合なしに恒真化すると警告する。

**反例・破り方の要約:** 常に `SATISFIED` を返す評価器、その source hash、その出力 hash を witness に収めれば、全 hash と二つの status 列は矛盾なく一致する。

**提案修正:** status は receipt/witness から読むのでなく、型付きの P 別 evidence から独立評価器が再導出する。各 P に policy hash、正負 calibration、限界効果を殺す変異、独立検査者の結果を必須化し、source hash 単独を証拠に数えない。

**確度:** high

### 3. `AI-Agent: none` は人間承認の self-attestation である

**対象:** 設計案「誰が書くか」「人間承認の実証」

**主張:** 非 merge・親一意・receipt 一ファイル追加という topology は承認分離を示すが、commit message の `AI-Agent: none` は作成者が自由に書ける文字列であり、人間性を証明しない。`decision=APPROVED` も同じ commit に含まれる自己申告である。

**根拠:** `s2-draft.md:51,61,113-122,188-193`。D150 決定 (4-b) は申請者の宣言を証拠に数えず、状態語を申請側に選ばせない。

**反例・破り方の要約:** 申請側が要求 topology と trailer を満たす commit を作れば、機械からは正規の人間承認と区別できない。

**提案修正:** 許可鍵 registry による署名、保護された外部承認 ledger、または同等の repo 外 trust root を必須にする。現行の「push は人間」という運用を trust root とするなら、その仮定と検証不能範囲を明記し、機械的本人確認とは名乗らない。

**確度:** high

### 4. `ruling_ref` と P10 は裁定の意味を検証できず、D150 (2-b) も表現不足である

**対象:** `ruling_ref`、P10、凍結・改訂契約

**主張:** D 番号・ledger blob hash・見出しの存在は bytes の同一性しか示さず、その D が対象 revision、witness、cap を承認したかを示さない。P10 を通常の `SATISFIED` に畳むことも、人間 gate という型を消している。また P4 は `SATISFIED/FAILED` しか持たないため、D150 (2-b) が要求する将来の「代替状態」は新 receipt だけでは表現できない。

**根拠:** `s2-draft.md:54,56,93,99,132`。D121 決定 (7) は P10 を人間 gate とする。D150 決定 (2-b) は明示 supersede・代替状態・D96 記録・境界テストを同一変更単位に要求する。

**反例・破り方の要約:** 無関係または内容不足の D を一意な見出しとして参照し、P10 を `SATISFIED` と書いても、現在の field 検査案では意味不足を機械判定できない。

**提案修正:** 裁定 record に decision kind、target revision、witness hash、cap、policy version、supersedes、境界テスト manifest hashを構造化して束縛する。P10 は `HUMAN_RATIFIED` 等の別型にし、P4 緩和は schema/policy の版上げを必須にする。

**確度:** high

### 5. revision drift の検出閉包が申請側定義で、validator も自己検証している

**対象:** witness closure、runtime descendant 契約

**主張:** 列挙した path の hash は既知ファイルの変更を検出するが、新しい bypass、別入口、import 差替え、環境依存を検出しない。さらに validator 自身が自身の source hash を検査する構造では、改変された validator が検査を省略できる。現行 completeness 二 gate も producer module を再 import し、同じ可変定数を権威にしているため独立 oracle ではない。

**根拠:** `s2-draft.md:80-82,118,126-131`、`autonomous_trial_completeness.py:162-167,438-442,1030-1031`。D121 決定 (7) の閉集合要求。

**反例・破り方の要約:** receipt closure に無い新入口を descendant revision に追加し、列挙済み bytes を不変に保つと、手書き closure は drift を見落とす。

**提案修正:** 安全な v1 は runtime tree を承認対象へ exact 固定する。descendant 再利用が必要なら、repo 外の不変 admission wrapper、機械生成した入口・import・consumer inventory、未知 callsite 拒否を設ける。validator source の pin は同 validator の自己検査だけに依存させない。

**確度:** high

### 6. 親の「三入口 + 二 consumer」実測は正しいが、完全境界への一般化は成立しない

**対象:** brief の seam 棚卸し、設計案 `scope` と producer 結線

**主張:** 現 tree では `_validate_generation_budget()` の三呼出しと completeness 二比較は実在し、件数自体は反証できない。しかし D114 の保証外である直接 `drive_iteration()` 反復や、programmatic API の `providers`・`drive`・`preview` 注入まで閉じたことにはならない。定数文字列の `scope` もこれらを区別しない。

**根拠:** `p3_autonomous_workload_trial.py:1245,1554,1740`、`autonomous_trial_completeness.py:438,1030`。注入面は `p3_autonomous_workload_trial.py:1541-1544` と `:1461-1471`。D121 決定 (7) 後の明示 (`docs/decisions.md:5864-5866`) は直接反復・注入・race を保証対象外とする。

**反例・破り方の要約:** 同じ receipt を、既定 production dependency と注入された drive の双方へ適用すると、承認者が評価した実行面と異なる多世代処理が receipt-backed と表示される。

**提案修正:** receipt-backed な `generations>1` では注入を拒否するか、callable/module・provider・build mode を admission record に束縛する。下位 driver の直接反復は明示的に scope 外とし、receipt による全プロジェクトの多世代承認とは名乗らない。

**確度:** high

### 7. Q2 は設計案自身と矛盾し、受理集合拡大を隠す

**対象:** brief provisional 前提 Q2

**主張:** Q2 は「受理集合を広げる結線を含まない」とするが、設計案は receipt 有効時に現在拒否される 2 世代以上を受理し、受理集合を広げると明記している。docs-only の本 wave が不変であることと、将来結線の効果が不変であることが混同されている。

**根拠:** `brief.md:25-26` と `s2-draft.md:173-178`。D150 決定 (7) は本 wave の機械受理集合不変だけを保証する。

**反例・破り方の要約:** Q2 を根拠に将来実装を「狭めるだけ」と分類すると、D96 の新 D・正負境界・受理集合拡大変異が省略され得る。

**提案修正:** 「本 docs-only wave は不変。将来実装は valid receipt を持つ 2..N を意図的に追加し、constant-only 経路を削除する」と書き分け、D96 と mutation preregistration を必須化する。

**確度:** high

### 8. `MAX_APPROVED_GENERATIONS` との三者一致は循環し、承認前の G に“approved”値を置く

**対象:** `approved_max_generations`、G→A 導入順

**主張:** receipt cap を target revision の `MAX_APPROVED_GENERATIONS` と一致させるなら、candidate `G` は人間 receipt `A` より先に同定数を 2 以上へ上げる必要がある。現在、その定数は三入口と completeness 二 gate の共通承認根拠であり、G 側の値との一致は申請側同士の自己一致になる。

**根拠:** `s2-draft.md:53,115-118`、現行 `p3_autonomous_workload_trial.py:134,249-258`、`autonomous_trial_completeness.py:438-442,1030-1031`。

**反例・破り方の要約:** G で定数・witness・receipt 予定 cap を同時に大きくし、receipt 必須化を一箯所取り残すと、その consumer は A 不在でも多世代を受理する。

**提案修正:** no-receipt fallback の literal `1` は維持し、別の絶対実装上限を設ける。実効 cap は `1` または「外部 trust root で認証済み receipt cap」からだけ導出し、target revision の“approved”定数を証拠に数えない。

**確度:** med

### 9. Q3 は成立せず、P6 の単一 status は抽象度が誤っている

**対象:** brief Q3、P6 status/受理写像

**主張:** D138 の 4 値は、origin・source failure・hypothesis・validation・enforcement・WAL を入力とする一回の導出結果であり、revision 全体の静的な実装充足 status ではない。複数 campaign 用の global receipt に単一の `P6Derived` 等を凍結する設計は、[T-433] が決める意味的充足・claim scope・configuration 単位に依存する。

**根拠:** `brief.md:27-28`、`s2-draft.md:55,65-72,95,111`。D138 決定 (3)(4) は origin/environment 有界の入力・結果契約を定める。D150 決定 (4) は `NOT_CLAIMED` を「その運転構成」の状態とし、決定 (6)(b) は cap-lift 可否を未裁定とする。

**反例・破り方の要約:** T-433 が `NOT_CLAIMED` を per-run/per-origin と裁定した場合、既存の global receipt は必要な configuration identity を格納できず、同じ語彙でも意味が変わる。

**提案修正:** T-433 裁定前に v1 schema を凍結しない。少なくとも `semantic_contract_hash`、claim scope、origin/environment/config identity を束縛し、「実装 readiness」と「個別実行の 4 値結果」を別 field・別成果物に分ける。なお現案が `NOT_CLAIMED` を当面拒否する点自体は fail-closed である。

**確度:** high

### 10. decision ledger の staleness 規則が二択とも不完全である

**対象:** `ledger_blob_sha256`、witness 規範 bytes、descendant reuse

**主張:** `docs/decisions.md` 全 blob を runtime closure と比較すれば、無関係な D の追記だけで全 receipt が stale になり、「無関係 commit なら再利用」と矛盾する。target revision の blob だけを確認するなら、後続の関連 supersede や transition 不成立を検出できない。

**根拠:** `s2-draft.md:56,79,126-132`、D150 決定 (2-b)。

**反例・破り方の要約:** 無関係 D の追加は過剰失効を起こし、逆に関連裁定の追加を runtime 比較対象外にすれば旧 policy が静かに残る。

**提案修正:** 全 ledger blob ではなく関連 D の canonical entry hash と、単調な supersession/revocation index を分離する。関連 policy が変わった場合だけ新 schema/policy version と新 receipt を要求する。

**確度:** high

### 11. 「起草のみ」の表示は入口に偏り、将来の承認済み誤読を防げない

**対象:** brief 成果物、設計案の総括

**主張:** brief と設計案冒頭は docs-only・未実装を明記している一方、総括は「6 consumer は…拒否する」と現在形で断定する。抜粋・検索・worklog 要約では冒頭の disclaimer が脱落し、「設計済み」が「裁定済み／結線済み」に変換され得る。

**根拠:** `brief.md:3-17`、`s2-draft.md:1,226-230`。D150 決定 (7) は cap=1・receipt 非結線・status field 不在を維持する。

**反例・破り方の要約:** 後続 wave が総括だけを入口にして、receipt gate は既裁定と判断し、裁定待ちの T-433・意味評価器・D96 を前提済みにする。

**提案修正:** design、rulings-inbox、worklog fragment の各々に機械検索可能な `status: PROPOSED_UNRATIFIED`、`machine_effect: NONE`、`MAX_APPROVED_GENERATIONS: 1`、依存する未裁定 T を置く。裁定・実装・検証を別 checkbox にする。

**確度:** med

所見ゼロの領域はない。限定的には、誠実かつ改変されていない verifier を仮定すれば、`target_revision` と A の唯一親契約は単純な別親 revision へのコピペを、raw SHA は単純な bytes 改変を検出できる。ただし上記の trust・closure・意味評価の不足は残る。

## 総括

現案の最大の穴は、hash で「どの bytes か」は束縛しても、「その bytes が前提を満たすか」を独立に束縛していない点である。  
Q1・Q2・Q3 はいずれも修正が必要で、特に Q2 は受理集合拡大を明示し、Q3 は T-433 後まで凍結を待つべきである。  
人間承認の trust root、P 別意味評価器、完全な runtime closure が揃うまでは `MAX_APPROVED_GENERATIONS = 1` を維持すべきである。  
本所見は read-only の静的監査であり、テスト・build・実測は行っていない。