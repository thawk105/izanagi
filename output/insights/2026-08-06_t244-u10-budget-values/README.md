# [T-244] U-10 — 実験予算 tuple の値案 (ユーザー批准パッケージ)

**種別:** 起草のみ。本番 authority (`orchestrator/campaign/reflux_origin_authority_v2.json`、
71 bytes・entry 0 件) を 1 byte も変えていない (2026-08-06 裁定 (b) / D147 決定 4 / D183)。
発行主体は人間のままである。

## 0. この批准で何が起き、何が起きないか

**起きること:** §6 の候補 budget policy が「合意された値」になる。
worklog が課した「U-10 の値が決まるまで 8c 結線を再起票しない」という**必要条件が 1 つ閉じる**。

**起きないこと:**

- **本 wave (起草) は authority を 1 byte も変えない。**批准後に authority へ entry を書くかどうかは
  **丙群 2 件 (択一 7 と丙-較正) の答えで決まる**。2026-08-06 の裁定文は
  「calibrator 実測から起草し、批准で発行」という一体の条件なので、
  起草側の条件が成り立たない以上、発行の可否は発行時期だけでは決まらない。
  **分岐の表は §7「批准後の順序」にある。**親が推奨するのは発行の延期だが、
  それは裁定文の変更提案であって既定ではない。
- 8c への結線と物理実行は、どちらの答えでも発生しない。
- **D201 が挙げた 3 つの阻害要因は 1 件も解けない** (束縛の供給経路が無い / batch 最低行数と
  1 世代 1 実行の不整合 / evidence の正本が無い)。値の批准は結線の許可ではない。
  次に起票できるのは**結線の実装 wave ではなく設計 wave**である (§7)。
- `Qmax` と `Imax` は探索側の batch 数 (producer topology) に依存する。topology が変われば
  **再計算して再批准が要る** (§5 択一 1・6、§6 の再計算規則)。

**批准の仕方:** §5 の択一は**性質が 3 つに分かれる**。混ぜて読まないでいただきたい。

| 群 | 択一 | 答えると何が起きるか |
|---|---|---|
| **甲. 値が決まる (批准対象)** | 1・2・3・5・6・8 | §6 の候補 budget policy が確定する |
| **乙. 方向だけ決まる (批准対象外)** | 4 (V-2 の evidence 正本) | 発行点の方向が決まるだけで、exact な schema・outcome 対応・consumer は本 wave に無い。設計 wave へ返す |
| **丙. 既裁定の変更を要する (再裁定)** | 7 (発行時期)、および **丙-較正** (値の根拠に calibrator 実測を使わないこと。§5 択一 5 に本文) | 2026-08-06 の裁定文と食い違うため、承認なしに親が決めない。どちらも §6 の値は変えない |

甲だけに「推奨どおり」と答えれば §6 の値は確定する。個別に変える場合は §6 の再計算規則に従うこと
(一部だけ変えると parse を通らない組ができる)。

### 既裁定からの逸脱 2 点 — 再裁定をお願いする

2026-08-06 の /rulings は方式を
**「(b) AI が calibrator 実測から根拠付き値案を起草し、ユーザー批准で authority 発行」**
と定めた。本 wave の起草はこの文言から 2 点ずれている。**親が勝手に不採用にはせず、
新事実を添えて再裁定へ戻す。**

1. **値の根拠に calibrator 実測を使っていない。** 予算値は台帳の受理規則と P6 の証明義務から
   決まり、較正値は式のどこにも入らない (§5 択一 5)。加えて新較正は未活性、旧較正は
   自己 attestation 不合格である。**「calibrator 実測から導く」という前提自体が成り立たない**
   というのが本 wave の実測結果である。
2. **批准と同時の authority 発行を推奨していない。** `Qmax` と `Imax` は未決の producer topology に
   依存するため、いま発行すると topology 確定時に作り直しになる (§5 択一 7)。

いずれも「値を出せなかった」ではなく「出した値の位置づけが裁定文の想定と違う」という報告である。
**2 点は独立に効くのではなく、組み合わせで発行の可否が決まる** — 裁定文は
「較正実測から起草し、批准で発行」という一体の条件だからである。
**1 (較正を根拠に使わない起草) を是としたうえで、2 (発行の延期) を採らないという判断であれば、
§6 の値でそのまま発行手続に進める** (parse と codec の受理は確認済み)。
その場合、作り直しの公算が高い点だけご承知おきいただきたい。
**分岐の全体は §7 の表**にある。

**本 wave が実測したもの / していないもの:** parser と codec の受理検算は実走した (§4)。
**8c の live 実行はしていない** — 現行の許可経路では投入できない (§7・§9)。

---

## 1. 依頼された 14 項目の対応

依頼は定義正本 (`2026-08-05_t244-p3-design/s2-plan.md` §1.3) の入力 12 項目 +
8c V-3 (#13) + 8c V-2 (#14) の計 14 項目。全項目を扱うが、**性質が 3 つに分かれる**。

| 分類 | 項目 | 意味 |
|---|---|---|
| **A. authority の欄で、本 wave で値が決まる** | #2 `Imax` / #3 `Qmax` / #4 `Kmax` / #5 `Bmin` と `candidate_min` / #9 floor tuple | 値を入れれば parser と seal 判定が実際に読む |
| **B. 既存の実装値で、authority は読まない** | #6 1 round の物理反復数 / #7 自動再測定 round 上限 / #12 codec・storage 上限 | 現行値の追認。批准値としての consumer は無いが、measurement config / feasibility 制約として現に効いている |
| **C. 規則だが、批准可能な形まで閉じていない** | #1 の source closure 部分 / #8 の early-stop と失敗→event 対応 / #10 課金範囲の caller 側 / #11 完全性規則の consumer / #13 R の消費点 / #14 V-2 の schema と outcome 対応 | **本 wave では閉じない。**方向だけ推奨し、exact 化は設計 wave へ返す |

**分類 C は「批准対象外」である** (§0 の乙群に対応する)。推奨を書いてあるが、
これに答えても実装契約は一意にならない。
特に #1 の source closure、#8 の失敗→event 対応、#14 の exact schema は
**内容自体が未提示**であり、本 wave の欠落として明記する。

---

## 2. 既裁定からの導出 — ここは動かさない

2026-08-04 の /rulings でユーザーが確定させた事項がある
(`docs/archive/worklog-phase3-0804-161.md`、P6 契約 `2026-08-03_t244-p6-contract/README.md` §3.10.1)。

> **[T-244] 択一 1 (予算値) = (a) 下限式から再導出する。**
> `Q >= 1 + 32R + E_min` の下限式から導き直す。R は最小の 1 でも Q は 33 以上となり
> 候補値 2 とは 1 桁以上違う。
> — これは U3 (帰納段を踏む) の代償であることを明示的に受け入れた裁定である。

この式は台帳の floor tuple にそのまま対応する。

| 下限式の記号 | authority の欄 | 値 | 由来 |
|---|---|---|---|
| `1` (source の元 run) | `base_queries` | **1** | 既裁定 |
| `32` (5-bit universe の全 mask 数) | `queries_per_round` | **32** | 既裁定 |
| `R` (独立 validation replicate 数) | `rounds` | §5 択一 5 | 既裁定は「R=1 が既に下限」 |
| `E_min` | `evidence_min` | §5 択一 3 | 未確定 |

**D205 (プロトタイプ基準) はこの下限を下げる根拠にならない。** D205 が見送るのは防御的堅牢化で
あって科学的妥当性ではない。`Q >= 1 + 32R + E_min` は座標 cut の証明義務そのものである。
(ただし §5 択一 6 の異常終了余裕は別問題で、これは科学的下限ではなく費用対効果の判断である。)

### erratum — 既裁定文の用語

既裁定文の「半空間 32 点すべてで同じ anomaly class を実測」は用語が不正確である。
5-bit universe は 32 点、**各座標半空間は 16 点**。座標 cut の証明が 32 run を要するのは、
bad-side 16 点で同じ class が再現し、paired good-side 16 点でその class が消えることを
両方確かめるためで、**合計 32 mask の全被覆**が要る (P6 契約 §2、証明義務 9)。
**数値 32 は変わらない。**用語だけの訂正である。

なお**現行の 8c は 32 mask を掃く producer を持たない** — 1 世代につき 1 回 `drive()` を呼ぶだけである。
32 mask の掃引は分類 C (未実装) に属する。

### 「R」の同定 (親の初期解釈の訂正)

floor の `rounds` と 8c V-3 の `R` は**同じ量** (P6 の独立 validation replicate 数) である。
実装の欄名が `rounds` なので紛らわしいが、別軸なのは次の 2 つの方で、
どちらも authority は読まない: 1 round の物理反復数 `reps` (現行 2)、
自動再測定 round の上限 (現行 3)。

---

## 3. parser が課す制約 (閉形式)

`orchestrator/campaign/reflux_origin_ledger.py` の `_budget_from_object` /
`_floor_from_object` / `_check_budget_codec_feasibility` から列挙した。
`I=Imax`, `Q=Qmax`, `K=Kmax`, `B=Bmin`, `D=candidate_min`, `F = base + q_round·R + E_min`。

1. `I >= 1`, `Q >= 1`, `K >= 0`, **`B >= 2`**, `D >= 1`, `D <= B`
2. `B <= 2248`
3. `q_round >= 1`, `rounds >= 1`, `base >= 0`, `E_min >= 0`
4. **`max(2, B) <= F <= Q`**
5. `Q <= I × 2248`
6. `ceil(F / 2248) <= min(I, Q // max(B, D))`
7. `K <= 15638` (**実効上限。literal 定数 15650 ではない** — §4)
8. floor 群は canonical 昇順・重複禁止、`formula_id` は
   `q-lower-bound/base+perRound*R+Emin/v1` のみ
9. 直列化後の origin stream / 共有 head / authority bytes が各上限以下 (実走検査)

**`B >= 2` の帰結:** 1 行だけの batch は作れない。したがって
**「validation 実行 1 回 = iteration 1」という 1:1 対応は現 schema で表現できない。**
これが §5 択一 1 の原因である。

---

## 4. 制約検算 (本 wave の実測)

**逐語と全表は `verification.md`。**確かめたのは
**parse と codec 直列化が受理するかだけ**であり、値の科学的妥当性・32 mask の物理被覆・
query と evidence row の対応・8c からの到達可能性は検証していない。

要点だけ:

| 実測 | 結果 |
|---|---|
| topology 格子 576 組 (`R`,`E`,`K`,`B`,`D`,`I` の組合せ) | **全て parse・codec 受理**。D189 / D198 で狭まった codec 包絡線は U-10 の値域ではまったく効かない。効くのは §3 の閉形式制約だけ |
| `Kmax` の実効上限 | **15,638** (literal 15,650 との差 12 は、literal が SHA 配列単体の概算で、実際は `OriginSealed` frame 全体を 1 MiB gate に通すため) |
| `Qmax` の 64 MiB 境界 | 73,717 受理 / 73,718 拒否。既裁定の値域 (数十) から 3 桁離れており実質効かない |
| 単一 batch に `32R` 行を入れる形の最大 `R` | **70** |
| 3 origin を載せた authority | 受理。ただし**budget 以外はダミー manifest**なので、示せたのは schema と容量の smoke test まで |
| §6 の推奨 tuple | **受理を個別に確認済み** (`verification.md` §1)。なお 576 組の格子に `I=4` は含まれない |

---

## 5. 択一 8 件 (推奨付き)

### 択一 1 — `Imax` の意味と batch topology 【最重要】

**問題:** 既裁定は「追加 I = 32R」と書き、validation 実行 1 回ごとに iteration を 1 数える
会計を意図していた。しかし現行台帳の `Imax` は**予約 batch 数の上限**であり、
`B >= 2` のため 1 行 batch も作れない。**実行と iteration の 1:1 対応は表現できない。**
さらに `Imax` は上限にすぎず、「32R 回予約せよ」と強制する力を持たない。

**推奨: (a) 全 validation 行を 1 batch にまとめる形を採り、P6 の iteration 会計を
「実行回数」から「予約 batch 数」へ**変更する**ことを批准する。**

これは既契約からの導出ではなく、**契約の改訂**である。根拠は 2 つ。

- P6 の独立再導出の条件 4 は「validation mask、replicate ID、実行順、予算予約は
  **最初の validation result より前に一括 commit** される」と要求する。現行 FSM では
  次の予約は `IDLE` 相からしか受理されず、commit 後は seal して結果を開示するまで
  `IDLE` へ戻らない。したがって**複数 batch に分けると条件 4 を満たせない**。
- 会計の型が変わっても、実行回数の証明は `member_row_count` (= 32R) が担う。
  失われるのは「予約単位での no-refund の粒度」だけである。

代案 (b) 2 行ずつの batch に割る (`I = 16R`) — 条件 4 に反する。
代案 (c) parser の `B >= 2` を 1 へ緩める — 正しさゲートの緩和にあたるので推奨しない。

### 択一 2 — `candidate_min` を 1 にするか 32 にするか

**問題:** `candidate_min` は「seal 対象 batch に含まれる**候補平文の相異数**」の下限である。
32 にすれば「相異候補 32 件を含まない batch は seal できない」となるが、
policy は origin 単位なので**探索側の batch にも 32 件を要求してしまう**。

**推奨: (a) `candidate_min = 1`。**

**注意 (誇張の訂正):** `candidate_min = 32` にしても、保証されるのは
**候補平文が 32 通り相異なること**だけで、それが **5-bit universe の 32 mask に一致すること**も
**物理実行されたこと**も保証しない。したがって (b) を採っても mask 被覆は台帳では閉じない。
どちらを選んでも、mask 被覆と物理実行の保証は V-2 の formal consumer 側の仕事である (§7 残余 1)。

代案 (b) `candidate_min = 32` は「相異候補が 32 未満の batch を弾く」弱い篩にはなるが、
探索 batch を 32 幅に膨らませる代償がある。検算では (b) も受理される。

### 択一 3 — `E_min` の値

**問題:** `E_min` は「P6 後に探索を成立させる最小余白」であり、P6 の結果を使って
**次の候補を作る**ことを要求する量である。D114 の承認済み generation 上限 1 の下では実行できない。

**推奨: (a) `E_min = 0`。**

代償を明記する — この選択では、**最初の authority は構造だけを固定する道具**であり、
**還流が実際に起きたことは主張しない**。`E_min > 0` を選ぶと、承認上限 1 の下で
floor に到達できない authority ができる。
**D114 の上限を 2 以上へ上げる裁定を行うときは、同じ裁定の中で `E_min` を必ず再訪すること。**

### 択一 4 — V-2: seal の result evidence の正本 【乙群・批准対象外】

**問題:** 台帳は `accepted` / `rejected` に evidence digest を要求するが、現行 `drive()` の
戻り値に per-query の evidence も constraint 正本も無い。`records` は段ごとの last-wins 射影で
複数 verify pass の先行結果を落とし、詳細な anomaly は reject の abort payload に偏る。
`outcome` からの後付け合成は verifier の構造化 anomaly を捨てることになる (規律 3 違反)。

**推奨: (a) 物理実行点で trusted harness が create-only の result-evidence record を発行し、
`drive()` は digest / 参照だけを運ぶ。record の schema と outcome 対応は
`verifier_policy_sha256` に束縛する。**

**この択一は「発行点」だけを決めるものであり、exact な schema・outcome 対応・issuer・
formal consumer は本 wave では提示していない (分類 C)。**したがって推奨を採っても
V-2 は一意に閉じない。exact 化は設計 wave の仕事である。
代案 (b)「現行戻り値から事後合成」は現物に無いので成立しない。

### 択一 5 — `R` (validation replicate 数) 【甲群。ただし末尾の較正の扱いは丙-較正】

**推奨: (a) `R = 1`。**

既裁定が「R を下げる案は R=1 が既に下限なので不可」と書いており、1 が形式上の下限である。
**上げる根拠となる実測が取れない** — 現行の許可経路では 8c を live 投入できず (§7 残余 3)、
費用も代理ログからの外挿しかない (§9)。`R = 1` は**実測に基づく最適値ではなく形式下限**であり、
科学的十分性を主張するものではない。`R` を上げるなら、まず `R=1` を許可された経路で
実走して再現性を測ってから決めるのが順序である。

較正値は本値案の根拠に**使っていない**。予算値は台帳の受理規則と証明義務から導かれ、
較正には依存しない (新較正は未活性、旧較正は自己 attestation 不合格)。

### 択一 6 — 異常終了への余裕をどれだけ持たせるか 【費用対効果の判断】

**問題:** D189 により予約は返却されない。必要最小 (`I=2, Q=34`) に置くと、
**予約直後に 1 回落ちただけで、その origin は二度と certifiable terminal へ到達できない。**

**推奨: (a) 探索 batch と P6 batch のそれぞれについて 1 回だけ予約し直せる余裕を持たせる —
`Imax = 4`、`Qmax = 68`。**

内訳 (訂正済み): 予約 4 回 = 探索 1 + 探索放棄 1 + P6 1 + P6 放棄 1。
query 68 = 探索 2 + 探索放棄 2 + P6 32 + P6 放棄 32。

**保証の限界を明記する:** `Imax` / `Qmax` は上限であって、この余裕の使い方を強制しない。
保証されるのは「上の内訳どおりに進めば予算が尽きない」ことだけである。
また**これは科学的下限ではなく liveness のための追加予算**であり、D205 の「防御的堅牢化」に
当たるかどうかは自動判定できない。**費用 (query 34 分) と保護対象 (異常終了 1 回) を見て
別途判断していただきたい。**

代案 (b) 余裕なし (`I=2, Q=34`) も検算では受理される。1 回の異常終了で origin を捨てて
作り直す運用になる。

### 択一 7 — いま authority record を発行するか 【丙群・既裁定の変更を要する】

2026-08-06 の裁定文は「ユーザー批准で authority 発行」と書いている。以下は**その変更提案**であり、
承認が無ければ裁定文どおり (批准と同時に発行) が有効である (§0 の逸脱 2 を参照)。

**推奨: (a) 値と択一は今確定させ、authority record の実発行は
「V-2 の evidence 正本 + producer topology + 許可された実行経路」の 3 件が揃ってから行う。**

理由: `Qmax` と `Imax` の実値は探索側の batch 数に依存し、それは producer topology が
決まるまで確定しない。先に record を発行すると topology 確定時に作り直しになる。
代案 (b) 今すぐ発行は、上記の理由で作り直しの公算が高い。

### 択一 8 — `Kmax` の値

**問題:** `Kmax` は `OriginSealed` が公開する **exact rejected class 集合の上限**であり、
「ちょうど K 件」を強制しない (0 件でも通る)。座標 cut の主張は「全 bad-side context で
**同じ** class が再現する」ことなので、主張に必要な class は 1 件である。しかし
**good-side で別の class により reject された場合、その hash も exact set に入るため
`Kmax = 1` では seal できなくなる。**

**推奨: (a) `Kmax = 1`。**「主張した 1 class 以外が観測されたら seal しない」という
**狭い policy として批准する**という意味である。曖昧な結果を通さない側に倒す。

- `Kmax = 0` は座標 cut の証拠そのものを載せられなくする。
- `Kmax = 2` は付随的な 2 つ目の class を許容するが、主張より多くを公開する。

**caveat:** 公開される class 識別子は生の SHA-256 である。既裁定が受け入れた
「origin あたり 33 bit 超の accept/reject 漏洩」とは別に、class の指紋面が開く。
閉じた辞書への射影は値の問題ではないので、V-2 の設計時に扱うこと。

---

## 6. 推奨どおり批准した場合の候補値

**甲群 (択一 1・2・3・5・6・8) を推奨どおり**とした場合、budget policy は次の 1 組になる。
乙群 (択一 4) と丙群 (択一 7・丙-較正) の答えはこの値を変えない — 乙は設計の方向、
丙は発行時期と根拠の位置づけの話である。

**本 wave の時点ではこれは未発行の候補である。**この値を authority へ書くかどうかは
**丙群 2 件の組合せ**で決まる (分岐の表は §7)。
**いずれの場合も 8c への結線と物理実行は発生しない。**
producer topology または V-2 契約が変われば `Imax` / `Qmax` / `Kmax` を再計算して再批准する。

```json
{
  "imax": 4,
  "qmax": 68,
  "kmax": 1,
  "batch_member_row_count_min": 2,
  "batch_distinct_candidate_count_min": 1,
  "query_floor_constraints": [
    {
      "formula_id": "q-lower-bound/base+perRound*R+Emin/v1",
      "base_queries": 1,
      "queries_per_round": 32,
      "rounds": 1,
      "evidence_min": 0
    }
  ]
}
```

- `F = 1 + 32×1 + 0 = 33`、`Qmax − F = 35`
- parse と codec の受理は個別に確認済み (`verification.md` §1、origin stream 75,206 bytes /
  transaction 寄与 30,753 bytes。上限は各 64 MiB)

### 個別に変える場合の再計算規則

一部だけ変えると parse を通らない組ができる。次の順で再計算すること。

1. `R` を変えたら `F = 1 + 32R + E_min` を再計算する。
2. `Qmax = 2 + 2 + 32R + 32R = 4 + 64R` (択一 6 の余裕あり) または `2 + 32R` (余裕なし)。
   **`Qmax >= F` を必ず確認する** (満たさないと `query floor is outside authority budget` で拒否)。
3. `E_min` を上げたら `F` が上がるので 2 を再確認する。
4. `candidate_min` を上げたら `ceil(F/2248) <= min(Imax, Qmax // max(Bmin, candidate_min))` を再確認する。
5. `Kmax <= 15638`。
6. 変更後の組を `verification.md` と同じ手順で実コードに通し直す。

参考値 (`verification.md` §1 で実測): `R=2` → `F=65`, `Qmax=132`。`R=3` → `F=97`, `Qmax=196`。

---

## 7. 批准が達成しないこと (残余) と、次に来るもの

**これらは値では閉じない。**

1. **台帳だけでは物理実行を保証しない。** 台帳は evidence digest の中身を参照しない。
   同一 wire・連番 replicate・同一 outcome・形式だけ正しい任意 digest の 33 行を並べれば、
   commitment・replicate・floor・`candidate_min`・exact class の各 gate を通せる。
   **物理実行 0 件でも certifiable terminal に到達しうる。**
   閉じるのは択一 4 の formal consumer であって、予算値ではない。
2. **予約より前は無課金のまま。** candidate 生成失敗・provider 失敗は `BatchReserved` の前に
   起きるので課金されず、成功するまで引き直せる。P6 の validation sweep は 32 mask が
   決定的で生成段を持たないため**この経路は P6 の主張には効かない**が、探索側には残る。
   D205 の下では残余として受容するのが妥当と考える。
3. **現行の許可経路では 8c を live 投入できない。** したがって `R` も費用も実測で決められない。
4. **`Kmax` の class 指紋面** (§5 択一 8 の caveat)。
5. **D201 の 3 阻害要因は 0/3 件しか解けない。**

### 批准後の順序

**発行するかどうかは丙群 2 件の答えで決まる。** 2026-08-06 の裁定文は
「calibrator 実測から起草し、批准で発行」という**一体の条件**なので、
起草側の条件 (丙-較正) が成り立たない以上、発行の可否は択一 7 だけでは決まらない。

| 丙-較正 (較正を根拠に使わない起草を是とするか) | 択一 7 (発行時期) | 帰結 |
|---|---|---|
| 是とする | 推奨 (延期) を承認 | **発行しない。**下記 1 → 4 の順に進む |
| 是とする | 承認しない (裁定文どおり) | **甲群の批准が発行の引き金**になる。人間承認の provisioning 手続で §6 の値を書き、その後 1 → 4 を進める |
| 是としない | — | **発行しない。**裁定文の起草条件を満たさないため、値案の位置づけ自体を再裁定していただく |

**発行しても発行しなくても、下記 1 → 4 の順序は変わらない。** 発行は「値を台帳に置く」ことであり、
結線でも実行でもない。

1. 批准 (と、上表で発行する場合はその発行) の時点では、**runtime と計算資源の投入に変化は無い**。
   8c は結線されていないので、authority に値があっても発火しない。
2. 次に起票できるのは**設計 wave**であり、結線の実装 wave ではない。設計 wave が閉じるのは:
   source closure の referent 集合と実在検査 / V-2 の exact schema・outcome 対応・issuer・
   formal consumer / 32 mask を掃く producer / launch admission が発行する束縛 capability /
   失敗と crash からの event 対応。
3. 設計が確定した event topology から `Imax` / `Qmax` / `Kmax` / `Bmin` / `E_min` を**数え直す**。
   本パッケージの候補値と違えば**再批准**する (既に発行済みなら世代を上げ直す)。
4. その後にはじめて、結線実装を検討する。

---

## 8. 分類 B・C の推奨 (批准対象外)

| # | 項目 | 推奨 | 状態 |
|---:|---|---|---|
| 1 | 科学的 cell の同一性 | 現行 4 要素 `cell_key` (workload / axis / verifier / environment) を維持し、同一 series 内での `cell_key`・`origin_id` の再利用を禁止する | **source closure は未提示** (分類 C)。series 横断の検査器も無い |
| 6 | 1 round の物理反復数 | **2** (現行実装値の追認) | 分類 B。authority は読まない |
| 7 | 自動再測定 round の上限 | **3** (現行実装値の追認) | 分類 B。floor の `rounds` とは無関係 |
| 8 | early stop / 失敗 / tombstone / no-refund | D189 の既裁定をそのまま参照する (本 wave は差分を提案しない) | **early stop 規則と、8c の失敗を event へ写す対応は未提示** (分類 C) |
| 10 | 失敗の課金範囲 | 予約受理以降のすべて。予約前は無課金 (§7 残余 2 として受容) | caller 側は未実装 (分類 C) |
| 11 | 物理 query と evidence row の完全性 | **1 validation drive = 1 non-tombstone row**。内部の `reps` と再測定 round はその 1 行の evidence 内訳に畳む (行ごとに作ると floor を最大 6 倍に水増しし、停止 topology も漏れる) | consumer は未実装 (分類 C) |
| 12 | codec 上限・storage 上限 | **authority へ複写せず実装定数のまま**。批准値ではなく検算項である | 分類 B |
| 13 | V-3 の `R` | 択一 5 に同じ (`R = 1`) | 消費点は未実装 (分類 C) |
| 14 | V-2 の evidence 正本 | 択一 4 に同じ (発行点のみ) | **exact schema・outcome 対応は未提示** (分類 C) |

---

## 9. 費用の見積り — **外挿であり実測ではない**

8c の 1 世代の実 wall-clock を示す成果物は repo 内に**無い**。
最も近い代理は同じ trigger-loop harness の WAL
(`output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl`) で、
`records=100000 / threads=4 / extime=1 / reps=2 / rounds=1` が一致する 2 本の drive:
**131.0 秒**と**170.4 秒**。role 呼出し時間・ycsb-b/c・自動再測定・結線分は含まない。

| `R` | 1 cell の外挿 | 3 cell 合計の外挿 | 現行の許可経路で投入可能か |
|---:|---|---|---|
| 1 | 約 1.16〜1.51 時間 | 約 3.49〜4.54 時間 | **不可** |
| 2 | 約 2.33〜3.03 時間 | 約 6.99〜9.09 時間 | **不可** |
| 3 | 約 3.49〜4.54 時間 | 約 10.5〜13.6 時間 | **不可** |

上表は「mask ごとに build/verify から丸ごと繰り返す」前提である。
対照として、**build/verify を完全に再利用できるという未確定の仮定**の下では、
`R` を 1 増やす分の 32 query の測定末尾だけなら約 4 分 (237.6〜238.8 秒) まで縮む。
**これは 1 cell の総時間ではなく、増分の測定部分だけの外挿である。**
再利用 policy 自体が未定義なので、この 1 桁以上の幅は `R` ではなく実行 topology が支配している。

→ **費用を根拠に `R` を決めることは、現時点ではできない。**

---

## 10. 逐語と根拠

| 文書 | 場所 |
|---|---|
| 制約検算の逐語 (親の実走) | `verification.md` |
| 段 1 brief / 段 1 前提実測 | `brief.md` / `parent-measured.md` |
| 段 4 裁定 (親の誤りの撤回を含む) | `s4-adjudication.md` |
| 段 2 プラン / 段 3 敵対 2 レンズ / 段 5 probe と出力 / 段 6 レビュー 2 本 | `/work/1/SFC/tanab/dev-wave-jobs/t244-u10-draft/` (repo 外、land しない) |

段 3 の敵対 2 レンズも段 6 のレビュー 2 本もすべて **NO-GO** を返した。
本版はそれらの must-fix と、焦点再レビュー 2 巡の指摘を反映した**第 4 版**である。段 6 で訂正した主なものは
**`Qmax` の会計誤り (66 → 68)**、**`Kmax = 1` を「導出」から「狭い policy の選択」へ格下げ**、
**択一 1 を「導出」から「契約の改訂」へ格下げ**、**`candidate_min = 32` の保証範囲の誇張の訂正**、
**検算の追跡可能性の補完**である。
親自身の暫定裁定 4 件の撤回は `s4-adjudication.md` §1 にある。
