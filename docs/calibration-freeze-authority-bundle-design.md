# 較正と凍結の権限束 — 世代交代の恒久設計 ([T-657])

**状態: 段 0 実施中 (`incomplete`)。** 本書は「較正 (環境契約の活性化) と
凍結 (ratified freeze の世代) の世代交代を、1 つの権限束として解決する恒久機構」の設計正本である。
第 1 設計段 (v1) が**制約と択一**を確定し、段 0 wave (v2) が確定した裁定を畳み込んで
語彙・schema・fixture を exact 化した。段 2 のプランに対し段 3 の敵対レビュー 2 本が、
v1 に対し段 6 の敵対レビュー 2 本が、v2 に対し段 0 wave の敵対レビュー 2 本が、
それぞれ独立に破れ方を構成した。したがって「決まったこと」と「決まっていないこと」を分けて書く。

**決まったこと (ユーザー裁定 2026-08-10 = worklog エントリ 376、2026-08-11 = 同 403):**
Q1 = (i) 環境の候補 record は権威 directory の外の候補 namespace へ置く /
Q2 = 上位束の承認 A・発効 X とも人間、A は digest + 添付レポートの確認 /
Q3 = lockstep (片側交代を拒否し、承認条件へ「両成分がともに交代」を加える。topology は不変) +
rollback = forward compensating generation + revocation = 下位 authority へ fallback しない +
下位 X_f は上位 X の後 / Q4 = (E-1) literal 保持 / U-A1 = 未発効 activation window /
§8 と §10 の矛盾 = 段 0 の完了判定から段 5 を除く。selection literal と正本節は §12.1。

**決まっていないこと:** §12 が正本である。他者の手番の gate が 2 件
(conformance 期待出力 literal / 下位 A・X commit topology の不適合)、
ユーザー裁定待ちが 3 件 (§12.3 = 失効 record の namespace と schema / 段 0 完了の到達可能性 /
段 6 の完了 predicate)。先送り確定の S (封印と保証境界) と B (副作用境界) は本書では決めない。

**段 0 は `incomplete` である。** 完了か否かは §10.2 の機械算出だけを正本とする。

由来: ユーザー裁定 2026-08-10「[T-657] = R3 (恒久機構へ合流)。封印と境界は先送り、恒久設計は
別 wave 起票。floor 復元はユーザー確認のみ。旧 branch は merge 禁止 (再導出)」。
一次控えは `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md` §58。
択一の材料パッケージは
`output/insights/2026-08-10_t657-restore-redesign/calibration-freeze-joint-generation-design.md`。

**可変状態を本書へ書かない。** 現在の活性化 serial、現在の凍結成果物 hash、record の現存件数は
台帳 (`docs/worklog.md` 末尾) と実成果物が正本である。本書が現行実装の形に言及する箇所には
**「(本 wave 時点の実測。実装 wave 開始時に再確認する)」**を付す。付いていない記述は設計であって
現況報告ではない。

---

## 1. 位置づけ — 何の正本で、何の正本でないか

| 文書 | 正本とする範囲 |
|---|---|
| 本書 | 環境権限と凍結権限を**束ねる上位層**の設計。両者を 1 つの identity のもとで解決し、交代させる機構 (交代の同時性と巻き戻しの扱いは §5・§5.1) |
| `docs/freeze-permanent-design.md` | freeze 族**内部**の恒久設計 (R1..R16 承認済み)。本書はこれを改訂しない |
| `docs/freeze-permanent-design-s2.md` | freeze 族内部の exact 仕様 (bundle digest・commit topology・consumer registry・状態四型) |
| `docs/orchestrator-design.md` | 環境契約そのものの設計 |

**上位と下位を混ぜない。** 下位 (freeze 族) の権限束は、本書の上位束にとって**1 つの成分**である。
下位の pointer を production authority と読む consumer が残ると、環境は上位 resolver、凍結は下位
resolver から取られ、**上位が承認していない直積**が再生成される。段 3 と段 6 のレビューが独立に
この経路を構成した。

### precedence 規則 (状態文でなく、repo から判定できる形で書く)

> **上位 namespace の pointer record が、上位 resolver の検証をちょうど 1 つ通って解決できる HEAD では、
> production authority は上位束である。** 上位 X が**一度も成立していない** HEAD
> (record が無い、複数ある、検証に落ちる) では、`docs/freeze-permanent-design.md` の記述が
> そのまま現行契約である。**上位 X が一度成立した後に解決不能になった HEAD はこれに含まれない** —
> 失効も含めて §7.5 の terminal fail-closed であり、下位 authority へ降格しない (Q3 (ii) 裁定)。

この規則は「起票済み」「裁定待ち」といった可変の状態文に依存しない。判定は
**「上位 resolver が一意に解決するか」**であり、ファイルの存在だけでは足りない (壊れた record が
置かれただけで正本が切り替わってはならない)。上位 namespace の path は §7.5、pointer schema は
同節が定める (段 0 で確定した)。同じ規則は `docs/freeze-permanent-design.md` の冒頭に既にある。

**確定した今も、production authority は下位のままである。** §7.5 の namespace には本 wave で
実体を置かない (置くには §5.3 の凍結側拡張が同じ段で要る)。したがって上位 resolver が解決する
HEAD は存在せず、現行契約は `docs/freeze-permanent-design.md` の記述である。

---

## 2. 解く問題 — なぜ片方だけでは完了しないか

環境を次世代へ進めることと、凍結成果物を次世代へ進めることは、次の 3 つが同時に成立しないため
独立して完了できない。

- **(式 1) live admission の一致要求** — 現在有効な floor protocol が焼き込んでいる契約 hash と、
  現在有効な環境契約の hash が一致すること。protocol builder は呼び出し時点の current 契約から
  hash を焼くため、環境だけを進めると既存 protocol が current と食い違う。
- **(式 2) 凍結の履歴不変条件** — 凍結成果物の各 path について
  「∀C ∈ rev-list(HEAD): entry(C, path) ∈ {absent, HEAD の oid}」。**同一 path への上書き再発行は
  原理的にこれを破る。** 別 path への一度きりの追加は破らない (段 3 で確認済み)。
- **(式 3) 盲検封印の紐付け** — selector の予測を封印した時点の floor protocol と現在の floor
  protocol が一致すること。floor を作り直すと campaign launch が拒否される。これは事前登録性を
  守る正しい挙動である。

環境だけを進めると式 1 が壊れ、固定 path の floor を更新すると式 2 と式 3 が壊れる。
**いま起票されている遷移 (pegasus 第 2 世代) について、較正の世代交代は凍結の世代交代なしには
完了しない。**

**これは一般の lockstep 政策ではない。** 式 1 が発火するのは、有効な floor protocol が環境契約の
hash を焼き込んでいるためであり、契約 hash を焼き込まない成分だけが交代する世代では発火しない。
「環境だけ・凍結だけの後継を一律に拒否するか」は **§12 Q3 の裁定**であって、本節の帰結ではない。

---

## 3. 用語

### 3.1 世代を 4 つに分ける

「generation」と略さない。4 つは独立に動き、番号が揃う必要はない。

| 名前 | 実体 |
|---|---|
| 環境活性化 serial | activation record の `activation_serial` |
| 環境世代 | activation record の `active_contracts[].generation` |
| 凍結世代 | ratified freeze の `generation_number` |
| **権限束世代** | 本書が新設する上位束の世代。上記 3 つの**組**を 1 つの identity にする |

### 3.2 状態型は下位の四型をそのまま継承する

`docs/freeze-permanent-design-s2.md` の状態四型を上位束へも用いる。**`candidate` を落とさない。**

`candidate` (生成済み・未登録) → `registered-inactive` (登録済み・人間承認前) →
`approved-inactive` (人間承認済み・未発効) → `active-official` (現 pointer が指す唯一の束)。

**失効 (revocation) と取消 (cancellation) は lifecycle の型ではなく governance record である。**
型と record を同じ列に混ぜない。

**ユーザー裁定 R3 により、pegasus 第 2 世代は `registered-inactive` のまま維持する。**
本設計のどの段も、この状態を暗黙に進めてはならない。

---

## 4. 骨格 — 上位に束を置き、凍結側の承認済み契約に触らない

```text
環境活性化 候補 ─┐
                 ├─ 上位束 (承認 record が成分一覧と digest を持つ) ─ pointer
凍結 承認済み束 ─┤
封印束縛 slot  ─┘
```

**凍結側の bundle digest は改訂しない。** 凍結側の digest は成分数固定・配列長強制・domain
separator 固定として既にユーザー承認済みの exact 契約である
(`docs/freeze-permanent-design-s2.md` の bundle digest 節)。ここへ環境成分を追加要素として足す案は、
承認済み契約の改訂を要する。**上位に別 domain separator の束を置けば、凍結側の契約を 1 byte も
変えずに済む。** これが上位層方式を採る理由である。

**上位束は下位と同じ形にする。** すなわち、独立した「束 record」ファイルを別に持たず、
**承認 record が成分一覧と digest を持ち、pointer が digest を指す**。これは下位で承認済みの形状で
あり、次の 2 つの破れ方を同時に消す。

- 束 record の hash を digest の原像に入れると自己参照になり計算できない。入れないと束 record を
  差し替えても identity が変わらない (段 6 レビューが構成)。
- 検査 receipt が束 record を参照し、束 record が receipt の hash を含むと循環する。

---

## 5. commit topology

下位 freeze 族の topology は既に承認済みで、**世代導入 (G_f)・承認 (A_f)・発効 (X_f) はいずれも
別 commit** である。世代導入 commit と承認 commit を 1 本にまとめることはできない — 前者は非 `none`
の AI provenance trailer を要求され、後者は逐語 `AI-Agent: none` を要求されるため、同一 commit は
どちらの検査でも落ちる (本 wave 時点の実測。実装 wave 開始時に再確認する)。

```text
H_base ← E ← G_f ← A_f ← Q ← A ← X
```

| commit | 内容 | 置く条件 |
|---|---|---|
| E | 環境活性化の候補 record 導入 | 環境成分が交代する世代 |
| G_f | 凍結世代の候補導入 (下位契約: 非 none trailer) | 凍結成分が交代する世代 |
| A_f | 凍結側の承認 (下位契約: 承認 record の追加、none trailer) | 同上 |
| Q | 上位の検査 receipt 群の導入 | 常に |
| A | 上位束の承認 (成分一覧 + digest) | 常に |
| X | 上位束の発効 pointer | 常に |

**これは分岐ではなく直列である。** 各 commit の parent は exact に 1 つ前 (置かない commit は列から
詰める)。祖先条件だけにすると順序の入れ替えが通る (§5.1)。

**上の図は「その世代で交代する成分についての commit を、この順で置く」ことを表す。**
**lockstep はユーザー裁定で確定した。** E と G_f / A_f は毎世代必須であり、片方だけの後継は
拒否する。承認の条件に「両成分がともに交代していること」が加わるだけで、topology は変わらない。
なお、無変化の E を形だけ置いて辻褄を合わせる案は採れない — 現行の環境側検査が
全据置の no-op record を拒否する (本 wave 時点の実測)。

**成分一覧の整合は、交代の有無で規則が分かれる。**

- **交代した成分**は、対応する導入 commit と (凍結側なら) 承認が同じ列に実在することを要求する。
- **交代しなかった成分**は、**親束の同名成分と byte 一致すること**を要求する。

**この規則は前進の場合を書いている。** 祖先世代の既承認成分へ戻す操作 (rollback) の扱いは
§5.1 が定める (Q3 (i) 裁定で確定)。

後者を書かないと、世代導入も承認も無い成分値を承認 record に置き、それを Q が検査するだけで
通ってしまう (段 6 再レビューが構成)。**Q と A の集合一致と digest 再計算だけでは、値が親束から
正しく引き継がれたかを検査できない。**

### 5.1 規定しなければならないこと

- **各 commit の parent は exact に 1 つ前とする。** 下位の承認済み topology と同じ形にし、
  「祖先であればよい」にしない。祖先条件だけだと、Q の親を A_f より前に置いて A が後から A_f を
  成分に取る、といった順序の入れ替えが通る (段 6 再レビューが構成)。
- **E / G_f / A_f / Q / A / X それぞれの exact diff、非 merge、provenance を規定する。**
  段 3 は「Q を空 commit にしても上位承認が通る」構成を作った。Q の内容が検査されないなら Q は
  形骸である。Q は **exact schema と再計算規則**を持たねばならない。
- **Q は A より前に置く。** 上位 digest の原像に Q の raw hash が入るためである。順序が逆だと
  循環する。
- **Q が検査した対象の集合と、A の成分一覧は一致していなければならない。** Q の raw hash を
  digest の原像へ入れるだけでは、**別の対象を検査した Q** を持ち込める (段 6 再レビューが構成)。
  よって Q は自分が検査した対象を exact に列挙し、A の成分一覧との**集合一致**を検証器が要求する。
- **X (pointer) は digest だけでなく、承認 record 自身への参照を持つ。** digest 一致だけだと、
  同じ digest を持つ別の承認 record を指せる。下位の pointer が承認 record の hash を持つのと同型
  にする。
- **上位 A の形状は「承認 record 1 ファイルの追加のみ、非 merge、逐語 `AI-Agent: none`」で確定する
  (Q2 = 人間)。上位 X の形状は (E-1) 確定により exact 3 path** — 公式 activation record の追加、
  `env_contract.py` の有効 head literal 2 値の更新、上位 pointer の追加 — **であり、非 merge、
  逐語 `AI-Agent: none`** とする。v1 が「1 ファイル追加のみ」を全分岐へ課したのは誤りであり、
  (E-1) を実行不能にしていた (段 6 レビューが指摘)。
- **lockstep は Q の自己申告で満たしてはならない。** 承認 record の成分一覧に対し、検証器が次を
  **再計算**する。(a) A の環境成分と凍結成分が、親束の同名成分と**双方とも異なる**こと。
  (b) A の環境成分が、同じ列の E が導入した候補 record の nested activation record と一致すること。
  (c) A の凍結成分が、同じ列の A_f を**下位 family 自身の検証器が承認済みと判定した**参照であること。
  検査 receipt Q の `status` を権威にしない — Q に `pass` と書いてあることは、置いた commit が
  実際に参照されたことを証明しない (段 0 wave の敵対レビューが構成した)。
- **rollback は「祖先へ戻す」形では受理しない (Q3 (i) 裁定 = forward compensating generation)。**
  祖先世代の既承認成分を現行 tip として再利用する列を、検証器は rollback として受理してはならない。
  過去の状態へ戻す必要が生じた場合は、環境成分・凍結成分・上位束を**すべて新しい世代番号で前進**
  させ、E / G_f / A_f / Q / A / X の新しい列を置く (補償世代)。**したがって世代番号は単調増加し、
  過去の承認 record と pointer が現行 tip として再び現れることはない。** 補償世代にも lockstep の
  再計算規則がそのまま適用される — 「戻した」ことは片側交代の免除理由にならない。
- **下位 X_f (下位 pointer の発効) の時点は §5.2 が定める (Q3 (iii) 裁定で確定)。** 上位束が
  参照するのは §7.2-1 のとおり**人間承認を経た下位束**であり、参照のために下位 pointer の発効を
  必要としない。

### 5.2 中間 commit の健全性

E / G_f / A_f / Q / A のいずれを追加しても、上位 X を置くまで**上位の** active pointer は変わらない。
ただしこれが「production authority が変わらない」を意味するのは、**§10 段 3 の consumer 移行が
完了した後**に限る。移行前は下位 pointer を直接読む consumer が残っているため、下位 X_f を先に
置けば production 挙動が変わる。**したがって下位 X_f は段 3 の後にしか置けない。**

**下位 X_f の位置は本節を唯一の正本とする (Q3 (iii) 裁定)。** 下位 X_f は
**(a) §10 段 3 の consumer 移行が完了した後、かつ (b) 上位 X の後**に置く。上位 X と同一の commit へ
まとめること、および上位 X より前へ置くことを拒否する。前者は上位 X の exact 3 path (§5.1) を
壊し、後者は移行後も残る下位読み経路で production 挙動を上位承認より先に動かす。

E の健全性は**環境候補 record の置き場 (§6.1 の候補 namespace、Q1 = (i) で確定)** による。
権威 directory の末尾へ置くと、現行の終端と有効 head の一致検査が E の時点で赤になる
(本 wave 時点の実測)。

### 5.3 上位層は専用の名前空間を必要とする

上位の Q / A / pointer を凍結側の名前空間へ置くことはできない。凍結側は自分の schema で解釈できない
file を無視せず拒否し、floor の事前検査も既知 file 集合の外を拒否する (本 wave 時点の実測)。
よって上位層は**専用 namespace の新設**と、**凍結側の未知 file 拒否および floor 事前検査の既知集合の
拡張**を、同じ段で行わねばならない。片方だけでは上位 commit を置けない。

---

## 6. 環境権限の解決方式 — (E-1) で確定

現在、有効な活性化 head は Python の literal として固定されており、serial を進めるには source を
編集する commit が必ず伴う (本 wave 時点の実測)。**「だから literal を record 由来へ移さねば
ならない」は成立しない。** 段 3 レンズ A が、literal を残したまま成立する恒久 topology の反例を
構成した。

| 方式 | 内容 | 上位 X の形状 | 得るもの | 失うもの |
|---|---|---|---|---|
| **(E-1) literal 保持** | head literal を残し、候補は束側だけで束縛する | 公式 activation record 追加・literal 更新・上位 pointer 追加の **exact 3 path** | source blob の変化が review signal として残る。loader closure 経由の間接 pin も残る | 上位 X が 1 ファイル追加でなくなる。形状規則を下位と別に定める必要がある |
| **(E-2) record 化** | head を literal から外し、束が指定した record までの prefix を検証する | **pointer 1 ファイル追加** | 発効が純粋に record の追加になる | source-side pin を失う (§13)。「正しい未活性 suffix を拒否する」現行挙動も失う |

**ユーザー裁定により (E-1) を採る。** source-side pin を失わせないためであり、§12 Q4 は発生しない。
上位 X の形状は §5.1 のとおり exact 3 path になる。

### 6.1 候補 namespace と候補 record (Q1 = (i) の確定形)

**候補 record は権威 directory の外へ置く。** 権威 directory は
`orchestrator/campaign/env_contract_activations/` であり、そこへ候補を置く経路は取れない。
理由は 2 つで、いずれも本 wave 時点の実測である。

- 権威 directory の列挙は `[0-9]{8}\.json` 以外の entry を拒否する
  (`orchestrator/campaign/env_contract_activation.py` の record 読取)。名前を変えて逃げられない。
- 連番の終端 serial と state hash を pinned head へ exact 照合する (同 module の chain 検証)。
  正しい形の後続 record を置くだけで、その HEAD 全体が赤になる。

**正確には「候補 record を発行する経路が無い」のではない。** `tools/issue_env_contract_activation.py`
は serial N+1 を検証して権威 directory へ create-only で書き、明示的に非 active と表示する
CLI として実在する。成立しないのは**「候補だけを載せた健全な HEAD を独立に land すること」**であり、
それが Q1 = (i) を必要にしている。同 CLI は §9 の移行対象に含める。

候補 namespace:

```text
output/calibration-freeze-authority/environment-activation-candidates/
```

候補 record は、公式 record の exact key 集合 (5 key、行は 3 key) を**変えずに包む**。
公式 schema へ issuer や束 field を足さない — 足せば §7.4 のとおり公式側の schema 変更になる。

| key | 型・制約 |
|---|---|
| `schema_version` | 逐語 `env-contract-activation-candidate/v1` |
| `lifecycle_state` | 逐語 `registered-inactive` |
| `activation_record` | 公式 activation record と同じ exact 5-key object |
| `activation_record_raw_sha256` | 公式 canonical bytes + 単一 LF の SHA-256 |

file 名は `<activation_serial:08d>-<候補 record 自身の raw SHA-256>.json` とする。
候補の検証は公式側の chain 規則 (serial 連番・predecessor hash・registered successor・
非 no-op) をそのまま再利用し、**別の緩い規則を作らない**。

**候補型は出口まで保つ (§7.2-2)。** 候補 record を読む resolver は公式の権限オブジェクトと
**別の nominal type** を返し、`.activation_record` のように素の値へ降格する accessor を置かない。
発効 X の時点で、nested `activation_record` の bytes をそのまま公式 directory へ導入する。

---

## 7. 束の識別子と resolver 契約

### 7.1 resolver

- 入力は repository root のみ。resolver 内で **HEAD を 1 回だけ**取得する。
- 環境権限と凍結権限を**同じ HEAD から同時に**解決する。family 別の個別 resolve を禁止する。
- 禁止の理由は 2 つ。(a) 同じ HEAD でも、独立した環境 tip と凍結 tip の直積から、承認されていない
  組合せを作れる。(b) HEAD を 2 回取ると、その間に checkout が動き、異なる commit の権限を結合できる。

### 7.2 設計不変条件と、それを機械化する義務

不変条件を散文で書くだけでは、違反実装を落とせない。**各項に「破る実装」と「それを落とす検査を
どの段で作るか」を対にする。** 対を書けない項は不変条件として掲げない。

**各行には安定した row ID を付ける。** row ID は §10 の fixture manifest から参照され、
行の削除・改名・追加が機械的に検出される。行を消すときは fixture 側も同時に消えねばならない。

| row ID | 不変条件 | 破る実装 (段 6 レビューが構成) | 検査を作る段 |
|---|---|---|---|
| `CFAB-7.2-01` | 上位束が参照できる凍結成分は**人間承認を経た束** (`approved-inactive` 以上) に限り、承認前の世代 record を直接参照してはならない。**承認済みであることは、下位 family 自身の検証器 (承認 record と topology の検査) が判定する** — 承認 record に見える形をした record を上位が形だけ照合するのでは足りない。**下位承認の有効期間は未発効 activation window とする (U-A1 裁定)** — 期限は下位 A_f から下位 X_f までの間だけ検査し、X_f 後は期限を理由に失効させない | 承認済み束への参照と並べて世代 record の path も持たせ、consumer に後者を使わせる。あるいは承認 record の形だけ真似た record を置く。あるいは X_f 後も use-time に期限を再検査する (却下された発効後 lease)、逆に A_f→X_f 間の期限を検査しない | 段 4。承認 record の成分 schema が「下位検証器が承認済みと判定した束への参照ちょうど 1 個」を要求し、余分な世代参照 field を拒否する。下位検証器を通らない偽の承認 record を落とす変異を含める。activation window は両向き (window 内の期限切れを受理する変異、X_f 後の期限失効を導入する変異) で確認する |
| `CFAB-7.2-02` | `candidate` / `registered-inactive` の型は**出口まで保たれる**。**候補型から素の権限オブジェクトを取り出す accessor を置かない** | 候補 resolver が通常の環境契約オブジェクトを返し、関数名とログだけ「候補」と名乗る。あるいは候補型を作りつつ `.contract` で素の値を渡す | 段 2。候補の返却型が current と**別の型**であることと、**素の権限オブジェクトへ降格する経路が存在しないこと**を、型と呼び出し面の双方への変異で確認する |
| `CFAB-7.2-03` | 束の identity は最終の出口まで運ばれ、**識別に使われる** | 表示用 field として各 JSON へ足すが、claim key・marker path・budget key・verdict の計算に使わない | 段 3。束 ID だけを変えた 2 走が claim 衝突・budget 共有・verdict 不変にならないことを変異で確認する |

**「持っている」ではなく「識別に使われている」を検査する。** 段 6 レビューが、表示専用 field で
条件を満たしたと主張できる構成を作った。

**schema を満たしたまま意味を空にする実装は、record 種別ごとに存在する。** 段 0 wave の敵対
レビューが、下の 5 つを独立に構成した。したがって各 schema には、schema 検査とは別に
**解決義務**を書き、それを落とす変異を対で登録する。書けない義務は掲げない。

| 対象 | 意味を空にする実装 | 解決義務と、落とす変異 |
|---|---|---|
| 上位 approval `components` | digest の再計算だけ通し、実際の環境・凍結は現行 resolver から取る | 各成分参照を**実際に解決**し、その結果を権限の値として使う。下位 family 検証器も必ず呼ぶ。成分を 1 つだけ差し替えた変異が受理集合か identity を変えること |
| 上位 pointer | 名前順の先頭を読んで hash だけ検査し、`bundle_digest` / `approval` 参照 / parent は使わない | live tip を一意に解決し、parent 連鎖・世代・承認 raw hash・digest を全て検査する。pointer を差し替えた変異が claim key・budget key・verdict を変えること |
| 検査 receipt Q | `status: "pass"` を入力として受け取り、evidence を読まない | `status` は check の**戻り値**から生成する。check ID の exact 集合一致、1 回ずつの実呼出し、evidence の実在と hash 一致、対象 head との一致を要求する |
| 裁定 profile | 件数と schema だけ検査し、`selection` を policy へ渡さない | ID ごとに許容値 enum と applicability 表を固定し、`selection` を発効・検査の述語へ実際に渡す。selection を変えた変異が挙動を変えること |
| 候補 record | 候補型を作りつつ `.activation_record` で素の値を返す | 候補と公式を別 nominal type にし、active resolver の引数を公式型のみにする。候補を active resolver へ渡す負例を置く |

### 7.3 digest の原像に必ず入れるもの

- 親束の identity
- 権限束世代の番号
- 環境活性化の選択 (`activation_serial` と `activation_state_sha256`)
- 承認済み凍結束の exact な参照
- **封印束縛 slot** (§8)
- **検査 receipt Q の raw hash (全件)**
- **裁定 profile の raw hash**

digest は**承認 record が持つ成分一覧から再計算できる**ものとし、承認 record 自身の bytes を原像に
入れない (自己参照になる)。domain separator は凍結側と別のものを新設する。凍結側の separator と
成分数は変えない。

**exact 符号化。** domain separator は

```text
izanagi.calibration-freeze-authority.bundle-digest/v1\x00
```

の ASCII bytes とする (末尾は NUL 1 byte)。原像は exact 7 要素の JSON array で、順序は固定する。

| 位置 | 内容 |
|---|---|
| 0 | 親束の digest (genesis は `null`) |
| 1 | 権限束世代の番号 (exact int、1 以上) |
| 2 | `[activation_serial, activation_state_sha256]` |
| 3 | `[凍結承認 record の raw sha256, 凍結束の digest]` |
| 4 | `[封印束縛 slot の path, その raw sha256]` |
| 5 | 検査 receipt Q の raw sha256 の配列 (v1 は exact 1 件) |
| 6 | 裁定 profile の raw sha256 |

canonical bytes は `separators=(",",":")`、`ensure_ascii=True`、`allow_nan=False`、
`sort_keys=True` の JSON を ASCII 符号化したものとし、原像 payload には LF を付けない。
digest は `sha256(separator + payload)` の小文字 hex とする。

**record の raw bytes は canonical bytes + 単一 LF** とし、raw sha256 は LF を含めて計算する。
重複 key、`NaN` / `Infinity`、未知 key、`bool` を int と見なす入力は拒否する。
順序の入れ替えと separator の変更は、それぞれ独立した変異点として登録する。

### 7.4 実在しない入力を区別する

設計の入力にしてよいのは、実成果物に実在する field だけである。**次は現行成果物に存在しない。**
上位層で使うなら「新規出力」として新設する対象であり、既存 field と称してはならない。

| 名前 | 現状 |
|---|---|
| 環境契約の **発行者 (issuer)** | 活性化 record にも権限オブジェクトにも無い (本 wave 時点の実測) |
| **どの束に属するか** | 同上 |
| 候補と current を分ける**型** | 環境世代の entry は世代と契約だけを持つ |

活性化 record の schema は**未知 key を拒否する exact key 集合**である (本 wave 時点の実測)。
したがって候補 record にこれらを載せるには公式 schema の変更が要る。**Q1 = (i) はそれを避ける** —
§6.1 のとおり、候補は公式 record を**包む**だけで公式 schema を変えない。

### 7.5 上位層の namespace と record schema

上位層の専用 namespace は次に置く (§5.3 のとおり、実体を置く段では凍結側の未知 file 拒否と
floor 事前検査の既知集合の拡張を同じ段で行う)。

```text
output/calibration-freeze-authority/
  environment-activation-candidates/   # §6.1
  inspection-receipts/                 # 検査 receipt Q
  inspection-evidence/                 # Q が指す evidence
  legacy-runtime-cutoffs/              # §9.1 の legacy catalog
  ruling-profiles/                     # §8-2
  seal-bindings/                       # §8-1 の slot
  approvals/                           # 上位承認 A
  active/                              # 上位 pointer X
```

file 名は原則としてその record 自身の raw sha256 (`<64hex>.json`)。候補 record だけ §6.1 の形。

**上位承認 A** — `approvals/<raw sha256>.json`、top-level exact 7 key。

| key | 型・制約 |
|---|---|
| `schema_version` | 逐語 `calibration-freeze-authority-approval/v1` |
| `authority_bundle_generation` | exact int、1 以上 |
| `bundle_digest` | 64 lower-hex。§7.3 の再計算値と一致 |
| `components` | 下記 exact 7 key の object |
| `approver` | NFC、trim 済み、1〜128 code point |
| `approved_at` | exact int の UTC 秒 |
| `scope` | 逐語 `calibration-freeze-authority-bundle-digest+inspection-receipt/v1` |

`components` の exact 7 key は §7.3 の原像成分と 1 対 1 に対応する —
`parent_authority_bundle_digest` / `authority_bundle_generation` / `environment_activation` /
`approved_freeze_bundle` / `seal_binding` / `inspection_receipt_raw_sha256s` /
`ruling_profile_raw_sha256`。凍結参照は**下位検証器が承認済みと判定した承認 record**に限る。

**検査 receipt Q** — `inspection-receipts/<raw sha256>.json`、top-level exact 6 key
(`schema_version` / `authority_bundle_generation` / `validation_head` / `subjects` / `results` /
`aggregate`)。`validation_head` は exact に `Q^`。`subjects` は A の `components` から
`inspection_receipt_raw_sha256s` **だけ**を除いた object と byte 一致すること (これ以外の除外を
許さない)。`results` は固定順の check ID 列で、各要素は
`{check_id, status, evidence_path, evidence_raw_sha256}`。**`status` は check の戻り値から
生成する。** 固定 check ID は
`parent-authority-bundle/v1` / `environment-activation-candidate/v1` /
`approved-freeze-bundle/v1` / `lockstep-components/v1` / `seal-binding-slot/v1` /
`ruling-profile/v1` / `runtime-cutoff/v1` の 7 件。

**上位 pointer X** — `active/<raw sha256>.json`、top-level exact 5 key
(`schema_version` / `authority_bundle_generation` / `parent_active_pointer_raw_sha256` /
`bundle_digest` / `approval_raw_sha256`)。genesis だけ parent が `null`。
digest は A と一致し、`approval_raw_sha256` は A の raw bytes および file 名と一致する。
**失効の振る舞いは確定した (Q3 (ii) 裁定) が、失効 record の namespace と schema は依然として
本書が定めない。** 裁定が答えたのは fallback の可否だけである (§12.3 R1)。

- **上位 X が一度成立した後に上位権限が解決不能になった場合、下位 authority へ fallback しない。**
  失効を検出した場合も、record の重複・破損で一意に解決できない場合も、resolver は
  **terminal fail-closed** を返す。§1 の precedence 規則が下位を現行契約とするのは
  「上位 X が一度も成立していない HEAD」に限る。
- したがって失効は「解決不能」を**下位が肩代わりできない状態**として設計する。失効後に
  上位が承認していない環境と凍結の直積が再生成される経路 (段 3 レンズ A が構成) はこれで閉じる。
- **固定 schema を land させてはならない。** 置き場・record の粒度・時刻表現・重複数は、
  いずれも複数の形が成立し、選択によって受理集合が変わる。裁定前に選ぶことは
  「決めない」の隠れた解除である。cancellation record も同様に定めない。

---

## 8. 先送り 3 件の構造的隔離

ユーザー裁定により、次は**本設計では決めない**。

- **封印** — S1 (予測を byte 単位で再利用し、世代束縛だけ新設) か S2 (新世代用の封印を作り直す) か。
- **保証境界** — **S1 を採る場合にのみ**、G-a (受理順だけ保証) / G-b (外部非観測まで要求) /
  G-c (信頼境界を人へ移す) のどれか。**S2 を採る場合、この問いは発生しない。**
- **副作用境界** — 稼働 process が保持する古い環境権限を、運用上の停止と再起動に委ねるか、
  束の世代を機械検査するか。

**「決めない」を成立させるには、決める場所を先に作っておく必要がある。**

1. **封印束縛 slot を digest 原像の必須成分にする。** slot が指す**中身**が S1 と S2 で異なる
   (S1 = 旧予測 bytes への束縛 record、S2 = 新世代用の封印)。**slot 自体はどちらでも必須**である。
2. **裁定 profile を実体にする。** raw hash だけでは中身を検査できない。profile は **bytes・path・
   namespace・canonical schema** を持つ record とし、各裁定項目を `unresolved` と書ける型にする。
   **発効 X が要求するのは「その分岐で適用される裁定項目がすべて解決していること」**であって、
   全項目の解決ではない。S2 を選んだ束に保証境界の値を求めない (求めると S2 が実行不能になる)。
3. **保証境界の裁定前に、計算ノードへの投入 receipt schema を凍結してはならない。** 現在の投入
   receipt は束の識別子を持たない (本 wave 時点の実測)。この形のまま固めると、外部で先に実走して
   結果を見てから束縛を作る経路が排除できず、**受理集合が黙って G-a 相当に固定される**。
4. **副作用境界は、権限オブジェクトが束の識別子を持つかどうかで分岐する。** 現行の権限オブジェクトは
   束の識別子を持たないため、書き込み時点で「まだ有効か」を検査できない (本 wave 時点の実測)。
   機械検査を選ぶなら識別子の追加が前提になる。運用停止に委ねるなら不要。**どちらでも設計が
   成立するよう、識別子の追加は独立した段に置く。**

### 8.1 裁定 profile の exact schema

`ruling-profiles/<raw sha256>.json`、top-level exact 2 key (`schema_version` / `rulings`)。
`schema_version` は逐語 `calibration-freeze-authority-ruling-profile/v1`。
`rulings` は**固定順・固定件数**の配列で、各要素は exact 3 key
(`ruling_id` / `status` / `selection`)。`status` は `resolved` / `unresolved` /
`not-applicable` の enum。`selection` は `resolved` のときだけ非空 string、それ以外は `null`。

| `ruling_id` | 現状 | 許容 `selection` |
|---|---|---|
| `CFAB-Q1-PLACEMENT` | resolved | `outside-authority-directory` |
| `CFAB-Q2-ACTOR` | resolved | `human-approval-and-activation` |
| `CFAB-Q2-MEANING` | resolved | `digest-plus-inspection-receipt` |
| `CFAB-Q3-LOCKSTEP` | resolved | `both-components-change` |
| `CFAB-Q3-ROLLBACK` | resolved | `forward-compensating-generation` |
| `CFAB-Q3-REVOCATION` | resolved | `no-lower-fallback-fail-closed` |
| `CFAB-Q3-XF-POSITION` | resolved | `after-upper-activation` |
| `CFAB-Q4-HEAD-MODE` | resolved | `literal-pinned` |
| `CFAB-S-SEAL` | unresolved (先送り確定) | `S1` / `S2` |
| `CFAB-S-GUARANTEE` | `CFAB-S-SEAL` = `S1` のときだけ applicable | `G-a` / `G-b` / `G-c` |
| `CFAB-B-SIDE-EFFECT` | unresolved (先送り確定) | 裁定後に確定 |
| `FREEZE-U-A1` | resolved | `activation-window` |

**この表の「許容 `selection`」列は検証器の enum と機械的に束縛する。** 各セルの backtick 付き
literal の集合が、検証器が持つ許容集合と exact に一致しなければならない。literal を 1 つも持たない
セルは「enum を登録しない」を意味し、その ID の `resolved` は受理されない。片側だけを書き換える
drift (docs の列だけ広げる / 検証器側だけ広げる) は本束縛が落とす。

**applicability の規則。** `CFAB-S-SEAL` が `S2` のとき `CFAB-S-GUARANTEE` は
`not-applicable` でなければならない。`not-applicable` を applicability 表の外の ID へ書くことは
拒否する (書けると「決めなくてよい」抜け道になる)。

承認 A は applicable な `unresolved` を含む profile を持つ束を作ってよい (`approved-inactive` まで
進める)。**発効 X は、applicable な項目に `unresolved` が 1 件でもあれば拒否する。**

**未裁定 ID の `selection` enum は、その裁定が land する commit で追加する。** それまで検証器は
当該 ID の `resolved` を受理しない。裁定前に `resolved` と書ける実装は、裁定を経ずに発効へ
進める抜け道になる。したがって「裁定が済むまで status が `incomplete` のままである」ことは
欠陥ではなく、意図した fail-closed である。

---

## 9. 移行が触らねばならない層

**producer 側だけ束対応にして consumer を旧経路に残すのは「実装したふり」である。**
新しい検証器を足しても、launch と verdict が旧経路なら、束縛 record を消しても差し替えても結果が
変わらない。

移行対象は次の閉包とする。**実装 wave の開始時に再列挙して本表と突き合わせること。**
以下は本 wave 時点の実測であり、完全性を主張しない。

- **凍結側 consumer** — `docs/freeze-permanent-design-s2.md` の W-d consumer registry が固定済み。
  本書はその列挙を再掲せず、同節を正本として参照する。
- **環境側** — 環境契約、活性化、identity、campaign lock、contract loader binding。
  campaign lock は環境権限だけを記録しており、束の識別子と凍結の exact 参照を持たない。
- **活性化 record の発行 CLI** — `tools/issue_env_contract_activation.py`。権威 directory へ
  create-only で次 serial を書く既存経路であり、候補 namespace (§6.1) を新設したまま放置すると
  **発行経路が二重化する**。移行対象から落としてはならない。
- **計算ノード境界** — floor campaign の投入 script と job script、およびその receipt schema。
  いずれも固定 path を直接実行し、束の識別子を持たない。
- **floor 事前検査の既知 file 集合** — allowlist は固定 path 定数から組まれる。versioned path の
  成果物は「未知の file」として拒否される。
- **凍結 manifest と key-set pin** — 成果物 path の bytes を pin する台帳。versioned path 化は
  manifest と key-set の両方の追随を要する。
- **上位層の専用 namespace** — §5.3。凍結側の未知 file 拒否と floor 事前検査の既知集合を、
  上位 commit を置く段と同じ段で拡張する。

### 9.1 移行境界での受理集合 (遡及拒否をしない)

§7.2-3 の「束 ID が識別に使われる」は、**発効 (§10 段 6) の後に効く**。段 1 と段 3 の挙動保存は
「束 ID を持たない既存成果物を遡及的に拒否しない」ことを含む。両者を同時に課すと矛盾する
(段 6 レビューが指摘)。したがって:

> **移行段 (1〜5) では、束 ID を持たない既存成果物を拒否しない。束 ID の必須化は発効と同時に
> 効かせ、それ以前に作られた成果物は歴史として読む。**

**「それ以前」は機械的に判定する。** 「移行中だから」という自己申告で新規成果物を legacy と
称して通せてはならない (段 6 再レビューが構成)。cutoff は次で定める。

> **発効 commit X を cutoff とする。Git に追跡された成果物について、その導入 commit の集合
> (複数ありうる) を取り、**
>
> - **全要素が X の ancestor** — 束 ID なしで受理する (歴史として読む)。
> - **全要素が X の子孫** — 束 ID を持たなければ拒否する。
> - **X をまたぐ (ancestor と子孫が混在する)** — 拒否する。

判定は導入 commit の ancestry で行い、成果物内の日付・宣言・世代番号では行わない。
**導入 commit が複数あること自体は拒否理由にしない** — 現行の履歴検査は同一 bytes の削除・再作成を
許すため、X より前に完結した削除・再作成を持つ既存成果物まで拒否してしまい、遡及不拒否と矛盾する
(段 6 再レビューが構成)。拒否するのは**分類が定まらない場合、すなわち X をまたぐ場合**だけである。

**Git に導入 commit を持たない成果物 (実行時に生成される receipt・marker・budget 台帳・WAL 等) は、
この cutoff で分類できない。** v1 ではこの規則は未定義だった。段 0 が次のとおり定める。

> **実行時成果物の proof chain の根に、`authority_admission` record をちょうど 1 件置く。**
> exact 6 key = `schema_version` / `authority_head` / `mode` / `authority_bundle_digest` /
> `authority_pointer_raw_sha256` / `legacy_run_root_raw_sha256`。
>
> - `mode == "legacy"`: `authority_head` は **X の strict ancestor**。digest と pointer は `null`。
>   `legacy_run_root_raw_sha256` は、**X の strict ancestor で導入された** legacy catalog に
>   列挙済みであること。
> - `mode == "bundle"`: `authority_head` が X と等しいか X の子孫。digest と pointer は、その
>   `authority_head` で上位 resolver が一意に解決した値と exact 一致。legacy root は `null`。
> - `authority_head` が X と比較不能、field 欠落、mode 混在、chain 内に admission が複数 —
>   いずれも拒否する。

**legacy catalog は X より前に凍結する。** catalog は
`legacy-runtime-cutoffs/<raw sha256>.json` に置き、top-level exact 3 key
(`schema_version` / `validation_head` / `roots`)、各 root は exact 4 key
(`kind` / `root_id` / `anchor_path` / `anchor_raw_sha256`)、固定順・重複なし。
WAL のように追記される成果物は全 file hash ではなく、**不変な最初の root record** を anchor にする。
catalog の raw hash と導入 commit は Q と A へ束縛する。

**X 以後に catalog へ root を足して legacy を名乗る経路を閉じる。** catalog 自身が X の
strict ancestor で導入されていなければ、そこに列挙された root を legacy 分類の根拠にしない。
これを書かないと、発効後に作った成果物を「移行中だから」と自己申告で通せる (段 0 wave の
敵対レビューが構成した)。

**逆向きの穴も閉じる。** legacy 判定は **strict** ancestor と定義し、X commit で導入された
成果物は bundle 側に分類する。X 自身を ancestor に含める実装は、X が導入した成果物まで legacy に
落としてしまう。また、X 以前に生成済みで catalog に載っていない実行時成果物を拒否すると、
本節冒頭の遡及不拒否と衝突する — **したがって catalog の作成は発効の前提条件**であり、
その完全性 (X 以前の全 legacy root を列挙したこと) は Q の `runtime-cutoff/v1` check が判定する。

cutoff は受理集合を発効の瞬間に変える。**変える対象と時点を明示することが、規律 2 の要求である。**

---

## 10. 段階分割と完了判定

**完了判定は、満たさない実装を実際に落とせるものだけを書く。** 加えて次の規則を課す。

> **各段の完了判定は、陽性条件 (正常な入力がちょうど受理されること) と陰性条件 (不正な入力が
> 落ちること) の両方を持つ。** 陰性だけを判定にすると、**何も受理しない実装 (reject-all) が
> 全段で緑になる。** 段 3 と段 6 のレビューがこの穴を独立に構成した。

**そして、陽性条件は fixture を名指ししなければ判定にならない。** 「正常な入力」「正常な campaign」
と書くだけでは、任意の 1 ケースを通して完了と主張できる。**したがって本書は各段の完了判定を
exact に書かない。書けないからである。** 段 0 で次を確定してから、実装 wave が判定式を書く。

- 各段の**陽性 fixture の実体** (path・内容・期待値)。
- 各段の**陰性 fixture の実体** (固定の負例一覧と、期待する拒否理由)。
- 拒否理由の oracle (診断文字列ではなく、受理集合または fail-closed 挙動の変化で判定する)。

**この fixture 閉包が対象とする段は、段 1〜4 と段 6〜8 である (§8/§10 矛盾の裁定 = 段 5 を除外)。**
段 5 の判定式は封印 S と副作用境界 B に依存し、両者は先送り確定 (§8) だから段 0 では書けない。
§8-2 の「適用される裁定項目だけを要求する」と同型に、**先送り確定項目に依存する段を段 0 の
完了判定から外す**。除外は段 5 に限り、他の段へ広げない。

> **この段集合は宣言であって、段と fixture の実体対応からの導出ではない。** 現行の fixture は
> §7.2 / §11 の row に対応しており、段を表す field を持たない。導出可能にすること自体が
> fixture assignment gate (§10.2 の `required_gates`、owner = 段の fixture を作る後続 wave) の
> 仕事である。**「段 5 を除外した」と gate ID が名乗ることは、除外の証拠ではない。**
> 段 0 wave の敵対レビューがこの自己申告性を指摘した。宣言と gate ID の drift だけは機械束縛する。

**fixture を置くだけでは完了判定にならない。** 段 6 再レビューが「fixture ファイルだけ置き、
検査を一度も呼ばずに完了と主張する」構成を作った。よって段 0 は次まで固定する。

- fixture の**閉じた manifest** (件数と hash を pin し、未登録の実体を拒否する)。
  **hash pin は manifest 自身の入力から再計算してはならない** — 実 file 集合・manifest の literal・
  検査側が持つ独立した期待値の 3 者を比べる。同じ入力から期待値を生成する実装は pin ではない。
- 各 fixture と、§7.2 の不変条件の各行・§11 の各行との**全単射**。対応の無い fixture と、
  fixture の無い行を、どちらも違反にする。
- fixture を実際に走らせる**検査 node の名前**と、その実行が受入に含まれること。
  **node 名を書くだけでは足りない** — 検査は、manifest の全 fixture が実際に読まれ、
  その `input` が実 entrypoint へ渡されたことを実行記録として突き合わせる。
- **実行できていない行は `pending` と明示する。** 対象 entrypoint がまだ存在しない行だけでなく、
  **entrypoint は存在するが実行可能な入力をまだ構築していない行**も `pending` である。
  fixture 内で理由と entrypoint 名を伴って `pending` とし、manifest がその件数を数える。
  `pending` を実装済みの体裁で隠さない。**どちらの `pending` も段 0 未完了の理由になる**ため、
  この区別が保証を緩めることはない。
- **`unresolved` は不変条件 fixture の代用にできない。** 裁定待ちを表す `unresolved` は
  §8.1 の裁定 profile の側にだけ書き、§7.2 / §11 の行に対する fixture の代わりにしない。
  代用を許すと、最重要の不変条件を fixture 無しのまま完了と算出できる (段 0 wave の
  敵対レビューが構成した)。

> **「未定義」と書かれた段は、完了と宣言できない。** 未定義のまま次段へ進むことも、
> 未定義の段を「該当なし」として飛ばすこともしない。定義は段 0 の裁定が与える。
> **唯一の例外は段 5 であり、それはユーザー裁定による段 0 完了判定からの除外である** —
> 段 5 自身が完了と宣言できるようになるわけではない。例外を他の段へ拡張しない。

| 段 | 内容 | 完了判定の状態 |
|---|---|---|
| 0 | 択一の裁定、語彙・schema・fixture の確定 | **§12 の全問 + 既存の未裁定 (下記) に裁定がつき、本節冒頭が定めた段集合 (段 1〜4・6〜8) の陽性・陰性 fixture が実体として固定される。** これが後続全段の前提である。判定は §10.2 の機械算出だけを正本とする |
| 1 | 現状を指す休眠束と resolver の導入 | 段 0 で固定した fixture に対し、導入前後で受理集合と拒否集合が一致する |
| 2 | 環境候補の表現と (E-1)/(E-2) の実装 | 正しい未参照候補を足しても active 束は不変。参照済み record の破損は拒否。**かつ候補が current と別の型として解決される** (§7.2-2) |
| 3 | consumer の束経由への移行 (挙動保存) | §9 の閉包に対し、束外の固定 path 参照・下位 family resolver の直接呼び出し・独立した HEAD 取得が残っていれば落ちる。**かつ §7.2-3 の識別変異が落ちる**。挙動保存は §9.1 の遡及不拒否を含む |
| 4 | その世代で交代する成分の commit 列 (E / G_f / A_f のうち該当分) と Q / A の構成 | これらを追加しても active 束は不変。A の余分な file・merge・trailer 不正・digest 不一致・**Q の対象集合と成分一覧の不一致**・承認前世代の直接参照・非承認組合せ・**parent が exact でない列**が落ちる。**かつ正当な A が X の候補としてちょうど受理される** |
| 5 | 裁定に応じた policy 実装 | **未定義。** 封印・保証境界・副作用境界の裁定がないと、期待する受理・拒否の集合を一意に書けない。裁定に依らず言えるのは「適用される裁定項目が未解決の束は発効を拒否」「全観測に束の識別子が残る」まで |
| 6 | 発効 X | **段 5 の後にしか置けない。** policy 未実装のまま X を置くと、X 自身が拒否されるか policy なしで production へ入るかの二択になる。判定式は段 0 と段 5 の裁定後に書く。**段 5 の除外は段 6 へ及ばない** — 段 6 は fixture 閉包の対象のままであり、その帰結は §12.3 のユーザー裁定待ちである |
| 7 | 発効後の受入と再検査 | 旧固定 path の履歴不変条件が引き続き成立し、新 path にも別 bytes の歴史が無い。**かつ段 0 で固定した陽性 campaign fixture が通る** |
| 8 | 次世代への継承の先行検証 | 段 0 が定義した (§10.2)。現行は世代 2 以上を先に拒否するため、その拒否が先に発火して全変異が「緑」に見える (本 wave 時点の実測)。判定は**先行拒否を外した隔離環境で、実 entrypoint を呼んで**行う |

### 10.1 段 0 が閉じねばならない既存の未裁定

上位束は下位の承認済み束を参照する。したがって**下位承認の有効性が確定しないまま、上位の承認と
発効を設計することはできない。** 次の 3 件を段 0 の前提に含める。

1. **U-A1 — 承認の有効期間 (activation-window / lease)。** `docs/freeze-permanent-design-s2.md` の
   冒頭がユーザー裁定として未解決と記録している。
2. **conformance 期待出力 literal の確定。** 同冒頭がもう 1 件の未了として記録している
   (下位実装 wave の開始前 gate)。**決定権者はユーザーではない** — 同書 §S2-11.2 が
   「W-a 開始時の親。外部参照実装で導出後レビュー」と明記している。したがってこれは
   ユーザー裁定パッケージに入れず、他者の手番の gate として §12 に記録する。
3. **下位の実装と下位 exact 正本の差。** 現行実装は承認と pointer を**同一 commit**に要求するが、
   下位の exact 正本は両者を**別 commit**と規定する (本 wave 時点の実測)。上位束は下位の承認済み束を
   参照するため、この差が解消される前に上位の参照規則を確定できない。**差そのものは下位の実装
   wave の課題であり、本書はそれを解く場所ではない。** ここで要求するのは「上位の実装を始める前に
   差が解消済みであること」という gate だけである。
   **これは「どちらへ寄せるか」の二択ではない。** 下位の exact 正本は凍結済みの design 族であり、
   実装がそれに適合していないという不適合 (expected = 別 commit、observed = 同一 commit 要求、
   status = nonconforming) である。同一 commit を正本へ昇格したい場合にだけ、凍結 design を
   再開する別のユーザー裁定が要る。

### 10.2 段 0 の完了 status と、段 8 の完了判定

**段 0 の status は機械的に算出する。** 次のいずれかが残る間、status は `incomplete` である。

- §8.1 の裁定 profile に applicable な `unresolved` が残っている。
- fixture manifest に `pending` が残っている。
- manifest の `required_gates` に `unresolved` / `pending` / `nonconforming` の entry が残っている
  (§10.1 の他者手番 gate と、段の fixture assignment gate を含む)。

**`incomplete` を成功結果として返さない。** 完了を要求する検査 node は、`pending` と
applicable な `unresolved` の件数がともに 0 で、blocking な gate が 0 件で、status が
`complete` であることを要求する。

> **本節の第 1 条件は、先送り確定の `CFAB-S-SEAL` と `CFAB-B-SIDE-EFFECT` も数える。**
> 両者は applicable であり `unresolved` だから、**先送りを維持する限り段 0 は `complete` に
> 到達しない。** §8/§10 矛盾の裁定 (段 5 の除外) は fixture 側の要求を外すだけで、この条件には
> 触れていない。これは裁定時点で見えていなかった事実であり、扱いは §12.3 のユーザー裁定待ちである。
> **親判断で applicability を広げて回避しない。**
manifest の整合検査が通ることと、段 0 が完了したことは別である — 全行を未解決印に結んだ
manifest でも整合検査だけは通せる (段 0 wave の敵対レビューが構成した)。

**段 8 の完了判定。** 現行は世代 2 以上を先に拒否するため、その拒否が先に発火して全変異が
「緑」に見える。判定は次で行う。

- 隔離した使い捨て worktree で、**その先行拒否だけ**を外す。fixture の世代番号は 2 のまま変えない。
- 実 entrypoint (`resolve_active_generation` から launch 検証まで) を実際に呼ぶ。
  **検証関数を差し替えて `Accepted` を返させる構成は判定にしない。**
- 陽性: 正当な次世代束が全 downstream 述語を通り、世代 2 の束として受理される。
- 陰性: parent pointer・supersedes・lockstep・Q と A の対象集合・digest・束 ID cutoff の
  各単一変異が、**世代 scope 以外の**対応する理由で拒否される。拒否理由が対象の述語まで
  到達したことを機械的に確認する (先行拒否で止まっていないこと)。
- 変異 lane は既存の「世代 2 を成果物 I/O より前に拒否する」テストと**分離する**。
  分離しないと、先行拒否を外す変異をそのテストが先に殺し、帰属が成立しない。

---

## 11. 拒否 — 保存すべきものと、新設するもの

### 11.1 保存しなければならない既存の拒否

次はいずれも production の正しい fail-closed であり、**恒久機構はこれらを緩めて通してはならない**
(規律 2)。設計案がこのどれかを消すなら、それは設計の欠陥であって最適化ではない。

| row ID | 状況 | 拒否の理由 |
|---|---|---|
| `CFAB-11.1-01` | 同一の凍結成果物 path に別 bytes が歴史へ入る | 削除 → 別 bytes 再作成の遮断 (式 2) |
| `CFAB-11.1-02` | floor だけ新世代、予測と journal は旧のまま | 封印時 floor と現行 floor の不一致 (式 3) |
| `CFAB-11.1-03` | 環境活性化だけ進み、floor は旧世代のまま | current 契約と protocol の契約 hash 不一致 (式 1)。**これは契約 hash を焼き込んだ protocol が有効な場合の拒否であり、環境単独後継を一般に禁じる政策ではない (§2)** |
| `CFAB-11.1-04` | 活性化 record は増えたが有効 head は旧のまま | 活性化連鎖の終端と有効 head の不一致 |
| `CFAB-11.1-05` | 凍結世代 record はあるが承認・pointer が無い | 世代の存在は権限ではない |
| `CFAB-11.1-06` | 承認を経ていない世代が production 権限になる | `CFAB-7.2-01` |

**Q1 の (ii) はこの表の `CFAB-11.1-04` を消す選択肢だった。ユーザー裁定は (i) であり、
この行は保存される。** 候補 record を権威 directory の外へ置くのは、この拒否を残したまま
候補を表現するためである。

**この 6 行は、今日すでに production で発火する。** したがって §10 の fixture は、これらを
**実 entrypoint へ実際に流す**陽性・陰性の対として持つ。宣言だけの期待値は判定にしない。

**fixture の射程は、名指しした entrypoint が担う層に限る。** §11.1 の fixture が固定するのは
その entrypoint の fail-closed 挙動であって、上位の semantic 層まで検証したとは主張しない
(例えば活性化 chain の検証器は chain と head の整合を担い、凍結成果物の内容妥当性は担わない)。
射程を書かずに「実 entrypoint で確認した」とだけ書くと、合成入力が実物より甘い場合に
過剰主張になる (段 0 wave の敵対レビューが指摘した)。上位層の検証は、それを担う entrypoint の
行として別に持つ。

### 11.2 新設する拒否 (現行には存在しない)

row ID = `CFAB-11.2-01`。

**「束の識別子を持たない成果物を公式に受理しない」は保存ではなく新設である。**
現行の実行 receipt・run marker・budget 台帳・campaign lock は束の識別子を持たず、それが正常な形で
ある (本 wave 時点の実測)。v1 でこれを「保存すべき拒否」と書いたのは虚偽であり、段 6 レビューが
訂正した。新設の時点と対象は §9.1 に従う。

---

## 12. 裁定の状態

### 12.1 確定済み (ユーザー裁定 2026-08-10 = worklog 376、2026-08-11 = 同 403)

規則の本文は正本節にだけ置く。本表は索引と `selection` literal だけを持つ。

| 問 | 裁定 | `selection` literal | 正本節 |
|---|---|---|---|
| Q1 | **(i)** 権威 directory の外の候補 namespace | `outside-authority-directory` | §6.1。(ii) は `CFAB-11.1-04` を消すため不採用 |
| Q2 | 上位 A・X とも**人間**。A は digest + 添付レポートの確認 | `human-approval-and-activation` / `digest-plus-inspection-receipt` | §5.1 |
| Q3 (lockstep) | 片側交代は拒否し、承認条件へ「両成分がともに交代」を加える。topology は不変 | `both-components-change` | §5、§5.1 |
| Q3 (i) rollback | **祖先へ戻さず、両成分を新しい世代番号で前進させる補償世代** | `forward-compensating-generation` | §5.1 |
| Q3 (ii) revocation | **失効後に下位 authority へ fallback しない (解決不能は terminal fail-closed)** | `no-lower-fallback-fail-closed` | §7.5、§1 の precedence |
| Q3 (iii) 下位 X_f | **consumer 移行の後、かつ上位 X の後** | `after-upper-activation` | §5.2 |
| Q4 | **(E-1)** literal 保持 | `literal-pinned` | §6。source-side pin を失わない |
| U-A1 | **未発効 activation window** (A_f→X_f の間だけ期限を検査し、X_f 後は失効させない) | `activation-window` | §7.2 `CFAB-7.2-01` |
| §8/§10 矛盾 | **(a) 段 0 の完了判定から段 5 を除外する** | — (gate `CFAB-S8-S10-CONTRADICTION`) | §10 冒頭の fixture 閉包 |

### 12.2 先送り (ユーザー確定済み。本設計では決めない)

- **S**: 封印は S1 / S2 のどちらか。**S1 を採る場合にのみ**、保証境界を G-a / G-b / G-c のどこに置くか。
- **B**: 副作用の境界を、運用上の停止と再起動に委ねるか、束の世代を機械検査するか。

決める場所は §8 と §8.1 に用意済みであり、決めないまま固定 schema を land させない。

### 12.3 残るユーザー裁定 (親が決めない)

2026-08-11 の裁定 (worklog 403) で U-A1・Q3 の残部・§8/§10 矛盾は閉じた (§12.1)。
その実施 wave が、裁定文からは導けない次の 3 件を新たに残した。

- **R1. 失効 record の namespace と schema。** 裁定が答えたのは fallback の可否だけである
  (§7.5 に反映済み)。置き場・record の粒度・時刻表現・重複数は複数の形が成立し、選択で受理集合が
  変わる。段 3 の 2 レンズが独立に「親が選ぶのは越権」と構成した。候補は
  (a) `revocations/<bundle_digest>.json`・exact 7 key・束当たり 0/1 件・UTC 秒 int /
  (b) `revocations/<record raw sha256>.json`・承認 record 単位・RFC 3339。**どちらでも
  「fallback しない」は成立する。** 親の推奨は (a) — 束を単位にすると「同じ束に対する 2 通りの
  失効」が構造的に置けず、resolver の解決不能条件が単純になるため。
- **R2. 段 0 完了の到達可能性。** §10.2 の第 1 条件は先送り確定の `CFAB-S-SEAL` と
  `CFAB-B-SIDE-EFFECT` を数えるため、**先送りを維持する限り段 0 は `complete` に到達しない。**
  §8/§10 矛盾の裁定 (段 5 除外) は fixture 側だけを外し、この条件に触れていない。
  (a) §8-2 の applicability を段 0 status にも及ぼす (先送り確定項目を算入から外す) /
  (b) 段 0 の完了を S と B の裁定後まで待つ / (c) 現状維持で、後続段は段 0 完了を前提にしない。
  親の推奨は (b) — (a) は「決めなくても完了できる」経路を作り、§8-2 が発効 X に課した
  「適用される項目は解決していること」を段 0 側で空洞化する。
- **R3. 段 6 の完了 predicate。** 段 6 の判定式も段 5 の裁定に依存する (§10 の段 6 行)。
  段 5 の除外を段 6 へ広げるか、段 6 を構造部分 (X の形状・ancestry) と policy 依存部分へ
  分割して前者だけ段 0 で固定するか。親の推奨は分割 — 段 6 の構造部分は S / B に依存しない。
  **本 wave では gate を新設していない** (裁定の無い択一を台帳へ既成事実化しないため)。

### 12.4 他者の手番の gate (ユーザー裁定ではない)

- **conformance 期待出力 literal。** 決定権者は `docs/freeze-permanent-design-s2.md` §S2-11.2 が
  「W-a 開始時の親。外部参照実装で導出後レビュー」と明記。
- **下位 A・X の commit topology 不適合。** expected = 別 commit (同書 §S2-1.14)、
  observed = 同一 commit 要求 (`orchestrator/campaign/s8b_ratified_freeze.py` の pairing 検証)、
  status = nonconforming。下位 family の実装 wave が正本へ合わせる。

---

## 13. 損失と限界の明示

- **人間承認は暗号署名ではない。** 確認者の真正性は repo のレビュー過程に依存する。
- **(E-2) を採ると source-side pin を失う。** 代替として得るのは、発効 commit・ancestry・
  content digest・束 ID を campaign lock へ記録する data-side pin であり、**同一の保証ではない**。
  ユーザー裁定は (E-1) なので、この損失は発生しない。
- **採った (E-1) の側にも代償がある。** 発効 X は環境契約 source の blob を変えるため、
  campaign lock が記録した contract loader の blob 束縛と食い違う。X より前に作られた lock を
  持つ実行の resume は、loader の drift として拒否されうる。また同 source は新規 T-126 series の
  code identity にも入るため、X は identity 値も変える。**これは §9.1 の「既存成果物を遡及的に
  拒否しない」と衝突しうる面であり、旧 process・旧 lock の扱いは先送り B の裁定対象である。**
  本書は事実を明示するに留め、政策を決めない。
- **束の identity は、実走時に実際に使用した binary と submodule の identity を完全には機械束縛
  しない。** static provenance と live safety の分担は凍結側設計の限界と同じであり、残余は
  レビューと実行環境規律で回収する。
- **保証境界を G-a に置く場合、外部での先行実走と目視は排除されない。** 束縛より前に別ノードで
  実走して結果を見てから束縛を作る経路が残る。これは「予測を改変していない」ことは証明するが
  「結果を見る前に選んだ」ことは証明しない。
- **束 ID の必須化は、発効の瞬間に受理集合を変える** (§9.1)。移行中の遡及拒否はしない。
- **本書は完全性を主張しない。** §9 の層と §10 の fixture は、段 0 と実装 wave 開始時に再列挙が
  必須である。

---

## 14. 旧 branch の扱い — 再導出するもの / しないもの

ユーザー裁定により、旧 activation branch は **main へ merge しない**。cherry-pick も行わない。
取扱いの規範は `output/insights/2026-08-10_t657-restore-redesign/restore-floor-protocol.md` の
「旧 branch の取扱い規範」節が正本。

**再導出してよい考え方** (内容を読んで作り直す。commit は運ばない):

- 活性化 record の生成と後継遷移の検査 vector。
- 「正しい未参照 suffix は非活性」「参照済み prefix の破損は拒否」という負例群 (新しい意味論へ
  合わせて作り直す)。
- 公式 E2E を「歴史の再現」と「現行 HEAD での拒否の固定」の 2 lane に分ける構成。
- 較正証拠の検証 CLI を**新規生成専用**と明示し、既存証拠への遡及的な再検証主張を撤回した裁定。

**再導出しないもの:** 固定 path の上書き、有効 head literal の更新、それに追随する pin、
旧 topology を前提にした E2E。

---

## 15. floor protocol 復元 — ユーザーの手番として残す

ユーザー裁定により、floor protocol の復元は**ユーザー確認のみ**であり、repo への書き戻しは不要である。
手順の正本は `output/insights/2026-08-10_t657-restore-redesign/restore-floor-protocol.md` の
「ユーザーの対話 shell が必要な確認」節。確認対象は repo ではなく、**scheduler に投入済みの job・
稼働中の process・未登録の checkout** である (AI から観測できない範囲)。

**本設計のどの段も、この確認を前提条件として消費しない。** 確認が済んでいなくても段 0 の裁定は
進められる。確認が必要になるのは、新世代の floor を実走する段である。
