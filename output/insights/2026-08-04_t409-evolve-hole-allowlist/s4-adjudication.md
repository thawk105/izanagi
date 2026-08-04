# [T-409] 段 4 裁定 — 本 wave は実装しない。設計を凍結し、択一 5 件を裁定へ返す

親: dev-wave manager。基準 main = c642263。
入力 = `s1-brief.md` (訂正 3 回)、`stage2-plan.md`、`stage3-lensA2.md`、`stage3-lensB.md`。

## 裁定の結論

**段 5・6 を飛ばし `4→7→8→9` とする。実装差分が無いため、変異 matrix と受入全走は対象外である。**

理由は 3 つで、いずれも親が独立に裏取りした:

1. **producer 側の変更にユーザーの明示承認が要る (機械的な前提条件)。**
   `.claude/agents/` の変更は「明示承認必須」と裁定済み
   (`docs/decisions.md:1367-1370`、`:1967`、axis-onboarding §5)。本 wave はその承認を持たない。
2. **producer を変えずに consumer だけ狭めることは、D127 決定 (1) が反対理由 (i) として
   名指しで退けた形そのものである。** そしてレンズ B が**現行契約を満たすが新文法が拒否する
   実入力**を構成した — `izanagi_gate_pass = 1;` は D48 の「コンパイル時定数のみ」契約、
   1 行制約、副作用なし、禁止識別子 5 個の非参照をすべて満たすが、新文法は数字を字句段で落とす。
   したがって「機械化するだけで契約は狭めない」は**偽**であり、文法の中身そのものが裁定事項である。
3. **発火条件が確定していない条件付き機能は設計メモに留める (DW-G04)。**
   どの層で発火させるか (driver / materializer / build / cache / replay) は択一 1・2 の裁定待ちで、
   brief に発火条件を書けない。

**「実装しない」は scope の縮小ではない。** 択一 1〜3 のいずれが裁定されるかで、書くべきコードの
配置・文法・承認導線がすべて変わる。裁定前に書けば、どの結論でも捨てる実装になる。

## real / refuted 裁定表

親が各所見を裁定した。判定を変えた場合は理由を書く。

### 採用 (real、scope 内、次 wave の must-fix として凍結)

| # | 所見 | 親裁定 | 成果物影響 (DW-G05) |
|---|---|---|---|
| A2-1 | 単独 `!` の優先順位が DSL と C++ でずれる。`!izanagi_abort_reason_ != ...` は DSL で `!(比較)`、C++ で `(!enum) != ...`。`IzanagiAbortReason` は `enum class` (patch:56) で bool へ暗黙変換できずビルド不能 | **real 採用。`!` は削除する** (意味空間の表現に不要 = A2-4 で反証済み)。残す案は採らない | 受理されたのにビルドで落ちる候補が出ると、試行台帳の拒否段階と候補成功率が表記依存で変わる |
| A2-5 | token 内空白と最長一致の境界テスト不足 (`: :`、`= =`、`! =`、`& &`、`&&&`、`===`) | **real 採用** | 空白結合を誤ると C++ で通らない式を受理し、逆順 lex なら正当候補を落とす |
| A2-8 | 資源上限の**数え方と判定順**が未固定 | **real 採用。** 判定順 `type → raw size → character → token count → parse/depth → semantic` を凍結 | 境界定義が揺れると同じ候補の受否と reason_code が変わり再現性が壊れる |
| A2-15 / B-1 | **`s1_verify_extime_calibration.py:329-357` の materializer が配線漏れ。** 加えて汎用 `p3_s4_loop.quarantine()`、`patchharness`、`pipeline.evaluate()`、`buildcache` は trigger 文法を検査しない | **real 採用、最重要。** 2 レンズが独立に到達 (DW-G03 の独立 2 例に相当) | 文法外 implementation が certified 選択へ到達でき、「gate 済み」という認証が偽になる |
| B-2 | cache / replay / WAL / campaign identity が文法 policy を束縛しない。合格側の grammar version が `SourceEvidence`・preimage・`ident` に無い | **real 採用** | gate 導入前の binary が cache hit で再利用され、新 gate 合格相当として材料レポートへ混入する |
| B-4 | 「既存契約を狭めない」は偽 (`izanagi_gate_pass = 1;` 反例) | **real 採用。裁定へ (択一 3)** | 新 D が「単なる機械化」と書くと、契約変更で得た certified 集合を旧契約と同一と誤記する |
| B-6 | 「LLM synthesisability を維持」は過大主張。trigger 軸は高々 `2^5`、D50 実測の有効自由度は 3 bit | **real 採用。**ただし `docs/phase3-main-experiment.md:163-173` が既に trigger を headline から外しており、Phase 3 全体の主張は崩れない | 材料レポートが有限 policy 選択を synthesis の実証として再包装すると、主張が証拠より強くなる |
| B-10 | role 変更は review ledger・adapter・manifest を同一変更単位に要し、かつ**ユーザー明示承認**が要る | **real 採用。本 wave の実装を止める直接原因** | 計画ファイルだけ変えると role parity 検査が通らず、受理可能な変更単位にならない |

### 採用 (real、scope 外 → 裁定パッケージへ)

| # | 所見 | 親裁定 |
|---|---|---|
| A2-11 / B-12 | **checked-in freeze と live source を結ぶ回帰テストが無い。** 2 レンズが独立に到達 | **real。**親の前提 D 実測 (全スイートで発火せず) と整合する。**択一 5 へ** |
| B-13 | trigger 軸だけでは EVOLVE-BLOCK hole は閉じない。backoff 軸 (`p3_s4_loop.py:554-582` は数値 literal を regex で拾うだけ) に owner が無い | **real。択一 4 へ。**sort 軸は [T-410] が所有済み |
| A2-9 | trace / verifier は workload 縮小を**構造的に検出しない** (`orchestrator/verifier/model.py:37` の `Txn` に予定操作数が無く、`:132` の integrity に `FLAGS_ycsb_max_ope` 照合が無い) | **real。**前提 A を構造面から補強する重要所見。**verifier 側の不変条件追加は別 task 候補** |
| A2-10 | 当該変異を入れた実 run が実際に certified されるかは**未実測** | **未確認のまま残す。**親も実測していない。「必ず検査を通る」と書かない |

### 不採用 (refuted)

| # | 所見 | 親裁定 |
|---|---|---|
| A2-2 | 式内部の代入は EBNF を忠実実装すれば受理されない | **refuted 追認。**ただし境界テストには残す (lexer の許可 token をそのまま式文法へ流用する実装ミスを pin する) |
| A2-4 | `kUnset=True` 固定でも `2^7` 写像を全表現できる | **refuted 追認** (= 意味空間は狭まらない)。128 部分集合の truth-table 照合を境界テストへ |
| A2-6 / A2-7 | 字句迂回の漏れ、`!` 修正後の評価器不一致 | **refuted 追認** |
| A2-12 / B-11 | 親の前提 D「pin は発火しない」 | **親の誤りとして受け入れ、brief を訂正済み。**正しくは「本番検証経路では発火するが、通常スイートが checked-in freeze 対 live source を検査していない」。**no-touch 制約は維持** |
| A2-13 / B-14 | 既存 `test_ruleops.py` 赤の切り分け | **refuted 追認 (切り分けは妥当)。**ただし A2 の警告を採用し、waiver は nodeid だけでなく `non-utf8` + 対象 path で固定する |
| B-3 | D96 との手続き衝突 | **refuted 追認。**D96 の「機械検査は新設しない」は consumer 閉集合の一般 AST 固定についての判断であり、個別 domain recognizer の恒久禁止ではない |
| B-5 | D48 が機械執行を auditor 目視へ永久限定したか | **refuted 追認。**D51 が既に 5 識別子 blacklist を machine hard gate としている (`decisions.md:1947-1955`)。新 D で足り、段階 B 差し戻しは不要 |
| B-7 | 受理集合が広がる入力 | **refuted 追認。**新 gate を通る入力は全て旧 blacklist も通る |
| B-8 | 正例 9 件の分類 | **refuted 追認。**親も独立に検算済み |
| B-9 | 許可文法を role に書くと勝ち筋が漏れる | **refuted 追認。**現行 role が既に全 enum 名を提示 (`decisions.md:1957-1962` が naked member 提示を許可)。member ごとの説明・順位・推奨 subset は引き続き禁止 |

## 凍結する設計 (次 wave はここから始める)

**受理文法 v1 (親裁定込み)。** `!` を削除し、判定順を固定した版:

```bnf
<implementation> ::= H* "izanagi_gate_pass" H* "=" H* <or-expr> H* ";" H*
<or-expr>        ::= <and-expr> (H* "||" H* <and-expr>)*
<and-expr>       ::= <primary> (H* "&&" H* <primary>)*
<primary>        ::= "true" | "false" | <comparison> | "(" H* <or-expr> H* ")"
<comparison>     ::= "izanagi_abort_reason_" H* ("==" | "!=") H*
                     "IzanagiAbortReason" H* "::" H* <member>
<member>         ::= kUnset | kLockConflict | kUpdateAbsent | kReadValiTid
                   | kReadValiLocked | kNodeVali | kInsertNode | kScanNode
```

`H` = space または tab のみ。許可文字 = `A-Z a-z _ : = ! & | ( ) ; space tab` (数字を含まない
— これが択一 3 の争点)。判定順 = `type → raw size → character → token count → parse/depth → semantic`。
semantic 段で `reason=kUnset` 評価が `True` でなければ拒否。

**gate の禁止 (署名で書く、DW-S04):**
`check_trigger_gate_implementation(implementation: str) -> GateLanguageResult` が
`passed=False` を返す入力は materialize されない。`reason_code` は閉じた enum で、
入力本文・未知 token・文字位置を返さない (リーク規律)。

**通る正例 1 つ:**
`izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict;`

**通らない例 1 つ (本 task の起点):**
`izanagi_gate_pass = true; pro_set_.pop_back();`

## 裁定パッケージ (ユーザー択一 5 件)

### 択一 1 — 権威境界: 中央再検査 か 封印済み receipt か
文法検査をどこに置くか。(a) trigger marker を書く**全 materializer で中央再検査**する /
(b) 合格時に**封印済み receipt** を発行し、build 境界が receipt を要求する。
**親の推奨 = (b)。** D127 決定 (3) が同型問題で materializer 側へ寄せた先例があり、
receipt なら cache preimage・WAL へ束縛でき択一 2 と同時に閉じる。(a) は新 materializer が
増えるたびに漏れる。

### 択一 2 — 既存 artifact の移行: cold invalidate か 再検査か overlay か
gate 導入前の cache・WAL・S8B resume 実体をどう扱うか。
**親の推奨 = 再検査。** cold invalidate は既存の計測資産を捨てる。overlay は
「合格したことにする」に近く規律 2 に反する。再検査は source bytes が残っている限り可能。

### 択一 3 — 数値 literal を文法に入れるか、契約を狭めるか (**最重要**)
`izanagi_gate_pass = 1;` は現行契約を満たすが新文法は拒否する。
(a) 数字を文法へ入れて現行 producer 契約を維持する / (b) 契約を狭め、role 定義変更の
**明示承認**を取る。
**親の推奨 = (b)。** 数字を入れると `1` 由来の算術・比較が復活し、字句 prefilter の
単純さ (= 検証しやすさ) が失われる。ただし (b) は承認が要るため、**ユーザーが承認しない限り
本件は前へ進まない**。

### 択一 4 — scope: trigger のみで閉じるか、全軸へ広げるか
backoff 軸に owner が無い。(a) trigger 完了とし backoff へ別 T を起票 /
(b) 本件を全軸へ拡張。
**親の推奨 = (a)。** sort は [T-410] が所有済みで、backoff は独立に起票するのが
D127 の「軸ごとに分離」と整合する。

### 択一 5 — 凍結 pin の回帰テストを本件に含めるか
checked-in freeze 対 live source の回帰テストが無い (2 レンズ独立検出)。
(a) 本件に含める / (b) 別 T を起票。
**親の推奨 = (b)。** 本件は実装待ちで止まるため、含めると防壁の追加まで止まる。
独立に安く入れられる。

## 射程の明記

- **実装差分が無いため、変異 matrix と受入全走は対象外である** (DW-S04)。
- 本 wave は受理集合を**変えていない**。したがって D96 手続 (新 D + 境界テスト) は
  実装 wave が負う。本 wave は新 D を起こさない。
- 凍結 bytes・proof chain・certified 選択・既存 gate はいずれも不変。
