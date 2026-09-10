## タスク 1 — 所見対応表

全 32 件（lens1 14 件、lens2 18 件）を列挙した。

### lens1

| ID | 判定 | 修正後の対応節 | 残る破れ方 |
|---|---|---|---|
| R-1 | `partial` | §4 で独立 B を廃止、§5.1 で Q→A、§7.3 で Q hash を A digest に束縛 | Q が検査した `subjects` / tree と A の成分列を一致させる規則がない。Q(T1) の hash を A(T2) に入れても digest は再計算できる。 |
| R-2 | `partial` | §5.1 で E-1/E-2 別形状に変更、§5.3 で専用 namespace を要求 | E/G_f/A_f/Q/A/X の exact parent は依然未定義。たとえば Q の親を A_f 前に置き、後から A が A_f を成分にしても、本文上の検査 snapshot が成立しない。 |
| R-3 | `partial` | §10 で段0の陽性・陰性 fixture 固定を前提化 | fixture の immutable identity、checker との全単射、実行・合格義務がない。段5/6/8はなお `未定義` で reject-all を排除しない。 |
| R-4 | `partial` | §7.2 各行に破る実装と検査段を追加 | 1 は「承認済み参照」という schema 名だけで lower approval の provenance/topology を証明しない。2 は名目上の別型を live consumer が unwrap する構成を落とさない。 |
| R-5 | `closed` | §7.4 で issuer・bundle membership・candidate/current 型を非実在と明記し、新設対象へ分類 | — |
| R-6 | `partial` | §11.2 で bundle-ID 拒否を新設と訂正、§9.1 で発効時必須化 | 「既存成果物」の機械的 cutoff がない。移行中に新規生成した bundle-less 成果物を legacy と称して受理できる。 |
| R-7 | `partial` | §5.1/§6/§12 Q2 で上位 A/X の主体・形状の先取りを削除 | Q3 は未裁定なのに §1・§5・§10段4が毎世代 E と G_f/A_f の双方を要求する。freeze-only successor は新 E を作れず、dummy E は現行 no-op 拒否に落ちる。 |
| F-1 | `not-applicable` | §5 は下位 G/A 分離、§6 は literal 保持/record 化を択一化 | 元の「M1/M2 が誤り」という疑いは引き続き反証済み。 |
| F-2 | `not-applicable` | §3/§7.3 は実在 core field、§7.4 は非実在 field を分離 | 元の「core field 全部が架空」は引き続き反証済み。 |
| F-3 | `not-applicable` | §2 式2で一度きりの新 path は許容と明記 | 元の疑いは反証済み。 |
| F-4 | `not-applicable` | §2 式1、§11.1 で current contract/protocol hash 不一致を保存 | 現行 live admission に拒否が実在する。 |
| F-5 | `not-applicable` | §1 と freeze 文書冒頭に precedence 追記済み | 「追記がない」は反証済み。pointer 実在判定の欠陥は別件 M7。 |
| F-6 | `not-applicable` | §8/§12 で S1/S2、G、B を未裁定のまま保持 | 元の全面先取り疑いは反証済み。 |
| F-7 | `not-applicable` | §3、§14、§15 | 現 checkout は activation record が serial 1 のみで lower active record も見つからない。旧 branch の全履歴について cherry-pick が一切ないことは今回未確認。 |

### lens2

| ID | 判定 | 修正後の対応節 | 残る破れ方 |
|---|---|---|---|
| REAL-1 | `closed` | §5 で G_f/A_f/X_f を分離し、A_f を approval のみに訂正。§5.2 で X_f を別扱い | 現行実装との差は新規 M9。本文上の再結合は解消。 |
| REAL-2 | `closed` | §5.1、§6、§12 Q2 | 上位 A/X の人間主体・trailer・単一 path 断定を削除。 |
| REAL-3 | `closed` | §6 の E-1/E-2 表 | E-1 は exact 3 path、E-2 は pointer 1 path と分離。 |
| REAL-4 | `closed` | §8-2、§12 S | G-a/b/c の解決要求を S1 選択時だけに限定。S2 は保証境界不要。 |
| REAL-5 | `partial` | §5.1、§7.2-1 で `approved-inactive` 以上を許容 | lower `ApprovedInactiveArtifact` を生成する semantic verifier が指定されず、raw approval-looking record の受理か正当な approved-inactive 全拒否の二択が残る。 |
| REAL-6 | `partial` | §9.1、§11.2 | 遡及拒否との形式矛盾は解消したが、legacy cutoff がなく受理集合を一意に実装できない。 |
| REAL-7 | `closed` | §3.2 | `candidate → registered-inactive → approved-inactive → active-official` に訂正し、revocation/cancellation を governance record へ分離。 |
| REAL-8 | `closed` | §10.1、§12 | U-A1 を段0の前提へ追加。別の lower conformance gate 落ちは新規 M9。 |
| REAL-9 | `closed` | §4、§7.3 | B 自体を廃止し、A の components から digest を再計算する形へ変更。pointer→A の欠落は新規 M1。 |
| REAL-10 | `partial` | §1 と freeze 文書「適用範囲」 | 可変状態文は除去したが、pointer の path/schema/validity、同一 HEAD での存在判定がない。 |
| REAL-11 | `closed` | 冒頭、§6、§7.4、§9 | 実装現況を「本 wave 時点の実測」と明示し、値の正本を台帳・成果物へ戻した。 |
| REAL-12 | `closed` | freeze 文書冒頭、由来記載、docs/README | `§7-X` を §7 に訂正、§58 の path を明示、README を「2件」と明記。 |
| REFUTED-1 | `not-applicable` | §8-1/§8-2 | slot 自体は S1/S2 の双方を表現できる。 |
| REFUTED-2 | `not-applicable` | §3、§14、§15 | pegasus G2、旧 branch、floor 復元の確定裁定に直接違反する記述はない。 |
| REFUTED-3 | `not-applicable` | freeze 文書の差分は冒頭追記のみ | R1..R16 本文は物理的に未変更。 |
| REFUTED-4 | `not-applicable` | 冒頭の可変状態規則 | 現 serial/hash/commit literal や docs 間行番号参照はない。 |
| REFUTED-5 | `not-applicable` | §1、§7.3、§9、§14、§15 | 指定 path・主要節は実在する。 |
| REFUTED-6 | `not-applicable` | §12 Q2/Q3 | 下位 R13/R14/R15 だけから上位主体・lockstep は導出できない。 |

## タスク 2 — 修正で新たに入った欠陥

### 8変更の判定

| # | 判定 |
|---|---|
| 1 | 循環は必然ではなくなった。しかし pointer→A と Q→A成分の二つの束縛が欠落（M1/M2）。 |
| 2 | E-1/E-2 の形状矛盾は解消。exact ancestry の先送りは M2 に残る。 |
| 3 | `approved-inactive` 許容自体は正しい。承認済みであることの semantic proof が欠落（M3）。 |
| 4 | 四型訂正による新しい破れ方は確認できない。 |
| 5 | fixture を置くだけで checker を走らせない構成を排除できない（M5）。 |
| 6 | 遡及不拒否自体は既存ゲートの緩和ではない。ただし legacy 判定不能が新しい迂回路になる（M6）。 |
| 7 | pointer の「実在」を決める機械規則がなく、precedence が不定（M7）。 |
| 8 | S1 限定は正しい。S2 を不要な G 裁定で閉じる欠陥は解消。 |

### 残る must-fix

#### M1 — 上位 X が exact な承認 record を指さない

[本体 §4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:94) は「pointer が digest を指す」とだけ規定する。一方、下位同型の実物は digest に加えて [`approval_sha256`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design-s2.md:377) を持つ。本体は A 自身の bytes を digest から除外するため、同じ components/digest を持ち、approver・approved_at・将来の U-A1 field が異なる複数 A を X が区別できない。

成果物影響: 同じ bundle digest に異なる承認・期限・provenance が結び付き、active authority、certified 選択、report、台帳がどの A を根拠にしたか一意でなくなる。

#### M2 — Q の検査対象と A の成分列が未束縛

本体には Q の `subjects`、`validation_head`、Qの唯一 parent、A components との全一致がない。下位正本はこれらを [§S2-2b.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design-s2.md:916) で明示している。Q(T1) を正常に作り、その raw hash を異なる A(T2) に入れる構成は循環せず、現本文の digest 条件を満たす。

循環を避けるには、Q は prospective digest ではなく exact subject vector と Q^ tree を検査し、A がその vector と自分の components を照合すればよい。

成果物影響: Q が検査していない環境×freeze×seal 組を、検査済み bundle として certified 材料・report・試行台帳へ入れられる。

#### M3 — `approved-inactive` が semantic state ではなく schema 名になっている

§7.2-1 は「承認済み束参照ちょうど1個」を要求するだけで、lower approval の人間 trailer、A topology、reports、digest、登録済み世代を検証した typed result を要求しない。下位正本の [`approve(...) -> ApprovedInactiveArtifact`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design-s2.md:1359) 相当を上位入力契約にすべきである。現行実装には active-pointer を要求する resolver しかなく、approved-inactive resolver は未実装である。

成果物影響: 未承認世代が freeze 成分として受理されるか、正当な approved-inactive が全拒否され、certified authority の受理集合が変わる。

#### M4 — candidate の「別型」は live admission 拒否を証明しない

§7.2-2 の oracle は返却型が別であることだけである。`CandidateContract` を返した後、protocol builder や consumer が `.contract` を unwrap して現行の exact `ExecutionEnvironmentContract` gateへ渡す実装でも型テストは通る。candidate を current-only 各入口へ投入して拒否される陰性 fixture が必要である。

成果物影響: X 前の環境契約で protocol・campaign・report が作られ、certified 選択が未発効権限を使用する。

#### M5 — 段0 fixture は完了 oracle として機械化されていない

[§10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/calibration-freeze-authority-bundle-design.md:300) は path・内容・期待値を要求するが、closed manifest、hash pin、各表行との全単射、checker node、実行コマンド、合格記録を要求しない。さらに段5/6/8は `未定義` のままである。fixture ファイルだけ置き、checker を一度も呼ばず、段5/6を reject-all、段8を既存 generation-1 先行拒否のまま完了扱いできる。

成果物影響: 正常 bundle/campaign が全拒否されて成果物が生成不能になるか、未検査 bundle が certified 選択・report・台帳へ受理される。

#### M6 — 「既存 bundle-less 成果物」の cutoff がない

§9.1 は移行段で既存成果物を許すが、「既存」を commit ancestry、導入 commit、X^ tree、namespace のどれで判定するか定義しない。mtime や自己申告に依存すれば、段3〜5で新規作成した bundle-less receipt/report を legacy と偽装できる。

成果物影響: 異なる bundle の新規 run が旧 marker・claim・budget・report へ合流し、certified 選択と試行台帳の authority 参照が失われる。

#### M7 — precedence の pointer「実在」が未定義

§1 は存在だけで authority を切り替えるが、上位 pointer の exact path/schema、承認・revocation・cancellation 検証、同じ一回捕捉 HEAD 内での判定を規定しない。存在確認と resolver が別々に HEAD を取れば checkout race も再発する。単なる malformed file の存在で上位へ切り替えるのか、無効 pointer は lower へ fallback するのかも不明である。

成果物影響: 同一 HEAD を lower authority と読む consumer と upper authority と読む consumer が分岐し、report に未承認の環境×凍結直積が再出現するか、全公式成果物が拒否される。

#### M8 — Q3 を開いたまま保持する topology がない

§12 Q3 は一成分 successor を許す可能性を残すが、§5/§10段4は毎回 E・G_f・A_f を列挙する。freeze-only successor では E がなく、dummy no-op E は現行 activation validator の [no-op 拒否](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/env_contract_activation.py:293) に落ちる。逆方向も同様である。

成果物影響: environment-only/freeze-only successor、rollback の受理集合と、active pointer・report・台帳が参照する世代がユーザー裁定前に固定される。

#### M9 — 下位 exact 正本の開始 gate と現行実装差が段0から落ちている

下位正本冒頭は未了を U-A1 と [conformance期待出力 literal](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/docs/freeze-permanent-design-s2.md:3) の2件とするが、本体 §10.1 は U-A1 だけを段0前提にした。また現行 [`_verify_pairing`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-permanent-bundle-design/orchestrator/campaign/s8b_ratified_freeze.py:1189) は approval と pointer の同一 commit を要求し、下位 exact 正本の分離 A/X をまだ実装していない。段4の A_f を作る前提 wave が工程にない。

成果物影響: 正当な approved-inactive freeze を構成できず certified 経路が空になるか、未確定 conformance oracle の lower bundle が上位 A・report・台帳へ入る。

### 親裁定への反証

- J3 の「下位 active pointer だけ」は誤りである。下位正本には人間承認済みの `ApprovedInactiveArtifact` がある。修正文書が J3 を緩和した点は正しい。
- J6 の「Q を digest に入れる」だけでは不足する。Q hash の存在は Q subject と A components の一致を証明しない。
- J4 の「陽性条件を必須にする」だけでは不足する。fixture と checker の実行・identity・行単位対応がなければ自己申告になる。
- J2 は lower X を落としていた。修正文書は X_f を復活させたが、現行実装から下位 exact topology へ移る依存工程をまだ落としている。

## タスク 3 — 恒真の再検査

凡例: `○` は該当する破れが残る、`△` は段0で exact 化されれば消せるが現時点では判定不能、`—` は具体的な破れを構成できなかった。

### §7.2

| 行 | 書けば自動的に真 | 測定手段なし | 判定者の主観 | 行単位判定 |
|---|---:|---:|---:|---|
| 1 承認済み freeze のみ | ○ | ○ | ○ | field を `approved_bundle_ref` と命名するだけで真を装える。lower typed approval の検証がない。 |
| 2 candidate 型保持 | ○ | △ | ○ | 別名 wrapper 型だけ作り、live consumer で unwrap できる。active入口での拒否観測がない。 |
| 3 bundle ID を識別に使用 | △ | △ | △ | claim/budget key の差を exact に観測すれば成立するが、現状は verdict bytes の表示 field 変化だけでも「不変でない」と主張できる。 |

### §10

| 段 | 書けば自動的に真 | 測定手段なし | 判定者の主観 | 行単位判定 |
|---|---:|---:|---:|---|
| 0 | ○ | ○ | ○ | fixture file の存在だけで完了を名乗れる。checker/manifest/hash pin がない。 |
| 1 | — | △ | △ | 段0 fixture が正しく固定・実行されれば判定可能。現時点では母集合がない。 |
| 2 | ○ | △ | ○ | nominal candidate 型で通る。live入口への負例がない。 |
| 3 | △ | △ | ○ | §9 自身が閉包の完全性を主張せず、legacy cutoff もない。 |
| 4 | ○ | △ | ○ | 「正当なA」「偽Q」「非承認組合せ」が未定義で、Q/A cross-binding もない。 |
| 5 | ○ | ○ | ○ | 本文自身が `未定義`。reject-all が残る。 |
| 6 | ○ | ○ | ○ | 段5後という順序だけで、正常 X の受理 oracle がない。 |
| 7 | — | △ | △ | 陽性 campaign fixture が固定・実行されれば判定可能。現時点では未実体化。 |
| 8 | ○ | ○ | ○ | `未定義`。generation-1 先行拒否で全変異を同じ理由へ落とせる。 |

### §11.1 / §11.2

| 行 | 書けば自動的に真 | 測定手段なし | 判定者の主観 | 行単位判定 |
|---|---:|---:|---:|---|
| §11.1-1 同一path別bytes | — | — | — | 現行 immutable-history 検査で観測可能。 |
| §11.1-2 floor新・seal旧 | — | — | — | protocol/prediction/journal hash と pre-oracle tree の比較手段がある。 |
| §11.1-3 activation新・floor旧 | — | — | — | current contract と protocol hash の比較手段がある。 |
| §11.1-4 record末尾/head不一致 | — | — | — | activation terminal serial/hash の literal 比較で観測可能。Q1(ii) 採用時は明示的な政策変更になる。 |
| §11.1-5 generationのみ | — | — | — | active resolution の pointer/approval 不在として観測可能。 |
| §11.1-6 未承認generation | ○ | ○ | ○ | lower active 経路では測れるが、新しい approved-inactive 上位入力の semantic verifier がない。 |
| §11.2 bundle IDなし | — | ○ | ○ | 新設であることは正しいが、発効前後・legacy の機械的 cutoff がない。 |

## 総括

残る must-fix は **9件**。

主因は、Q→A、X→A、approved-inactive→lower approval の三つの権限辺が exact に束縛されていないこと、fixture が実行可能な完了 oracle になっていないこと、precedence と legacy cutoff が判定不能なことである。

**GO / NO-GO: NO-GO。** 実装 wave へ渡すと、正当な bundle を構成不能にする経路と、未検査・未承認・bundle-less の成果物を公式受理する経路の双方が残る。静的検査のみ実施し、ファイル変更・pytest 実行はしていない。