# 段 4 裁定 — [T-244] D121 P1 の機械部品

両レンズとも **NO-GO**。中心所見は独立に一致した (合議ではない) — 「独立 golden」が実は
旧 emitter の一本の系譜であり、監査が恒真になる。これを受けてプラン v2 を確定する。

## 所見の裁定

| # | 出所 | 判定 | 採否 | scope |
|---|---|---|---|---|
| 1 | A1 | **real** | **採用 (must-fix)** | 内 |
| 2 | A2 | **real** | **採用 (must-fix)** | 内 |
| 3 | A3 / B1 | **real** | **採用 (must-fix)** | 内 |
| 4 | A5 / B3-b | **real** | **採用** | 内 |
| 5 | B4-a | **real** | **採用** | 内 |
| 6 | B5 (dual-import 型 identity) | **real** | **採用** | 内 |
| 7 | B8-a (既存被覆の数え違い) | **real** | **採用 (親の誤りを訂正)** | 内 |
| 8 | A6 (凍結 bytes 抵触) | **refuted** | 不採用 | 内 |
| 9 | B3-a (wire の表記 side channel) | **refuted** | 不採用 | 内 |
| 10 | B7 (受理集合の暗黙変更) | **refuted** | 不採用 (D96 非対象を確認) | 内 |
| 11 | A4 / B4-b (wiring 側の end-to-end 防壁・拒否理由の多面開示) | **real** | **実装しない** | **外 → 裁定パッケージ** |
| 12 | B6 (T-409 との land 順) | **real** | **調整のみ** | 内 (調整) / 外 (相手の設計) |
| 13 | B5 後段 (P3 との origin binding 欠落) | **real** | **最小限のみ** | 内 (schema ID) / 外 (ledger 結合) |

## 採用所見の是正 (プラン v2 の差分)

### 1 — 独立 golden を「規範仕様からの独立起草」に作り替える (最重要)

レンズ A が示した系譜は親が裏取りした。`predicate_for` → campaign provenance
(`_write_provenance` が `candidates()` の出力を格納) → freeze (`_trigger_entries` が
provenance を複写) → `s1_expected_goldens` (freeze から転記) は**一本の系譜**である。
したがって campaign 9 点・freeze 3 点は「歴史的 materialization の記録」であって
**独立な期待値ではない**。段 2 プランの四層は独立 anchor として加算できない。

**是正:**

1. **実装子を所有分離した 2 体にする。**
   - **子 G (golden 起草):** 編集所有は `orchestrator/tests/reflux_ir_expected_goldens.py` **のみ**。
     入力は下記「規範仕様」だけ。`s8a_trigger_sweep.py`、campaign provenance、freeze JSON、
     `s1_expected_goldens.py` を**読むことを禁じる** (prompt に明記し、報告に不読を書かせる)。
   - **親が hash 凍結:** 子 G の成果物 sha256 を、子 E を起動する**前に**記録する。
   - **子 E (leaf + テスト起草):** 編集所有は `orchestrator/campaign/reflux_ir.py` と
     `orchestrator/tests/test_reflux_ir.py`。**golden ファイルを読むことを禁じる**
     (テストは import して使うだけ)。emitter は同じ規範仕様から独立に書く。
2. **規範仕様 (親が段 4 で宣言する。旧 emitter のコードからは取らない):**
   - 要因順 = `axis_trigger_gating.GATEABLE_REASONS` の定義順
     (lock-conflict, update-absent, readvali-tid, readvali-locked, node-vali)。bit i = 位置 i、LSB-first
   - C++ enum 名と変数名 = **骨格 patch** `patches/silo-backoff-trigger-gating-variant.patch`
     が正本 (`izanagi_gate_pass`、`izanagi_abort_reason_`、`IzanagiAbortReason::kUnset` /
     `kLockConflict` / `kUpdateAbsent` / `kReadValiTid` / `kReadValiLocked` / `kNodeVali`)。
     親が実測で実在を確認済み (patch:56-194)
   - 述語の形 = `izanagi_gate_pass = ` + 選言項を ` || ` で連結 + `;`。
     選言項は `izanagi_abort_reason_ == IzanagiAbortReason::<enum>`
   - **kUnset は常に先頭に必在** (骨格の fail-safe sentinel 契約、D48 / 軸 docstring)。
     続けて mask の立った bit を**要因定義順 (0→4)** で並べる
   - 1 物理行、改行なし、末尾空白なし
   - **この順序規則は親が段 4 で宣言したものである** (軸 docstring の定義順に由来)。
     旧 emitter との一致は差分結果であって恒真ではない
3. **記録の文言:** campaign 9 点 / freeze 3 点は「**歴史的 artifact との一致**」と書き、
   「独立 anchor」「12 個の anchor」とは書かない。独立性を担うのは
   **子 G の literal 表 (32 点)** と **旧実装との差分 (32 点)** の 2 層だけである

### 2 — forged exact IR と dual-import への対処を 1 つの是正で閉じる

A2 (`object.__new__` / `object.__setattr__` で exact 型のまま範囲外 mask を作れる) と
B5 (`campaign.reflux_ir` と `orchestrator.campaign.reflux_ir` の二重 import で
`type(x) is T` が同値 IR を拒否する) は、**sink 側の判定法を変えれば同時に閉じる**。

- `encode_wire` / `emit_predicate` は `type(ir) is TriggerGateIR` の一致だけに依存しない。
  `isinstance` で受け、**毎回 mask の不変条件 (exact int・`bool` 不可・0..31) を再検証する**
- 負例に「正規 constructor を通らない exact 型の `mask=-1` / `mask=32`」を必ず入れる
- 二重 import 経路のテストを 1 本入れる (repo が両形を支える現物があるため)

### 3 — 「P1 を満たした」と名乗らない。記録文言を固定する

brief の表題「P1 のみ」と自己限定「P1 を満たしたと名乗らない」の矛盾を、**後者に寄せて**解消する。

- 本 wave の成果物名 = **「D121 P1 の機械部品 (candidate IR と正準 emitter) と、その静的一致監査」**
- 台帳には **P1 は未充足 (production 到達性ゼロ)** と明記する
- レンズ B の指摘「実装しても cap-lift は FAIL のまま」は真であり、そのまま記録する。
  本 wave の限界効果は「将来の wiring wave が使える監査済み部品ができる」ことに限る

### 4 — 「JSON 全拒否」を実現可能な範囲へ縮める

JSON decode 後の `"10010"` は通常の `str` と区別できない。記録・テストの主張は
**「非 `str`、container、引用符/封筒付き text、非正準文字列を拒否する」**までとする。
transport 由来の判定は本 leaf の外 (裁定パッケージ 11 に含める)。

### 5 — 拒否を「開示なし」にする

D121 決定 (3) は強制を 0 bit と定める。`TypeError` / `ValueError` の二分類と可変メッセージは
それ自体が理由チャネルである。

- 公開 API の拒否は **単一の例外型**とし、**固定文字列**を送出する。
  **入力本文・長さ・位置・失敗種別をメッセージへ入れない**
- 「全ての非正準入力に対しメッセージが byte 一致する」テストを 1 本入れる
- 内部診断を持たせない (持つと将来の journal 配線で漏れる)

### 6 — schema identity は最小限だけ置く (P3 面には触らない)

B5 後段の「IR schema/emitter の束縛点が無い」は real だが、origin ledger 側は P3 wave の所有である。
本 wave は **module 定数 `SCHEMA_ID` (版を含む文字列) を公開するだけ**とし、
digest の台帳 pin・origin preimage への組み込みは行わない
(digest 値を golden に literal 固定すると自己参照になるため**やらない**)。

### 7 — 親の誤りの訂正 (2 件)

- 既存被覆は **8 点でなく 9 predicate** (`candidates(EFF3)` = 8 subset + `ident_all`)。親が実測で確認した
- brief の「`s8a_trigger_sweep.py` も pin 済み no-touch」は不正確。現物 `8911dd24…` は
  freeze 記録 `3e94735a…` と**不一致**であり、closure の「changed 12」側である。
  `axis_trigger_gating.py` (`47507d9b…`、一致) だけが「unchanged 51」側の変更不可ファイルである。
  どちらも本 wave では触らない

## scope 外 (裁定パッケージへ返す)

1. **wiring wave の要件 (A4 / B4-b).** 自由 `implementation` の拒否、wire→mask→predicate の唯一経路化、
   raw mask と source digest / variant ID の束縛、WAL/provenance/report での同束縛の要求、
   binding 欠落 artifact の proof chain からの拒否、旧経路が残っていない負例。
   **受理集合の縮小なので D96 手続が要る**
2. **拒否理由の多面開示 (B4-b).** 現行 gate / preview / journal / whiteboard / critic digest が
   subtype・reason・禁止識別子・件数を公開している。閉じるなら report と投影契約の別 wave
3. **P3 との origin binding (B5 後段).** origin preimage が IR schema と emitter SHA を束縛する契約
4. **T-409 との land 順 (B6).** T-409 は `s8a_trigger_sweep.py` を編集予定であり、本 wave の
   differential oracle の基準そのものである。**本 wave は先に land を狙わず、赤が出たら
   drift 検出として扱う。**相手の設計は裁定しない

## 却下した案

- (a) 本 wave で production へ wiring する — 受理集合の縮小になり D96 手続と consumer 閉包が要る。
  ユーザー引数の「新規 leaf に閉じる」に反する
- (b) 段 2 プランどおり単一実装子で golden と emitter を同時に書く — A1 が real なので恒真監査になる
- (c) campaign / freeze を「独立 anchor」として点数に加算する — 系譜が旧 emitter に収束する
- (d) leaf が `predicate_for` を呼ぶ — 差分照合が自己比較になる (段 2 プランの判断を維持)

## 変異事前登録 (DW-M01)

実装前に登録する。各変異は「手前に同じ入力を拒否する検査が無いこと」と「無効化時の赤理由が
一つに絞れること」を実装後にコードで確認してから本走する。受理集合を縮小する wave ではないが、
**拒否面を新設する**ため過剰拒否を検出する**正例**も登録する。

| ID | 種別 | 変異位置 | 期待 |
|---|---|---|---|
| V1 | negative | emitter: kUnset 先頭項を削る | KILLED (32 literal / differential) |
| V2 | negative | emitter: 選言の区切りを ` \|\| ` から ` or ` へ | KILLED |
| V3 | negative | emitter: 末尾 `;` を削る | KILLED |
| V4 | negative | emitter: 要因の並びを逆順にする | KILLED |
| V5 | negative | emitter: enum 名 1 個を別名へ (`kReadValiTid`→`kReadValiTID`) | KILLED |
| V6 | negative | wire: bit 順を MSB-first にする | KILLED (round-trip / literal) |
| V7 | negative | parser: 長さ検査を `>= 5` へ緩める | KILLED (拒否面) |
| V8 | negative | parser: `strip()` を足す | KILLED (拒否面) |
| V9 | negative | parser: `bool` を int として受理する | KILLED |
| V10 | negative | sink: mask 再検証を消す (forged exact IR) | KILLED (A2 の負例) |
| V11 | negative | sink: `isinstance` を `type() is` へ戻す | KILLED (dual-import テスト) |
| V12 | negative | 拒否メッセージへ入力本文を足す | KILLED (固定メッセージ検査) |
| V13 | negative | golden 表の 1 行を書き換える | KILLED (差分 32 点が食い違う) |
| V14 | negative | golden の AST 独立性検査を無効化し、golden が production を import する | KILLED |
| V15 | **正例** | 正準入力 32 点すべてを通す (`"00000"`〜`"11111"`) | 全通過 = 過剰拒否なし |
| V16 | negative | 軸順 drift guard を消し `GATEABLE_REASONS` を並べ替える | KILLED |

## 成果物影響 (DW-G05)

- **実装しない場合:** 現在の certified 選択・材料レポート・proof chain・台帳値は**すべて不変**。
  変わるのは decisions の D121 決定 (7) P1 行が「機械部品すら無い」状態のまま残ることだけ
- **誤って実装した場合:** 将来 wiring した wave が誤った emitter を唯一経路にすると、
  提案 mask と build される variant が食い違い fitness の帰属が汚染される (D39 決定 7 と同型)
- **恒真な監査を書いた場合:** 「32 mask 監査済み」が台帳に載り、将来の cap-lift 裁定が
  偽の前提充足を参照する。**本 wave で最も避けるべき失敗はこれである**

## 段 5 の投入方針

所有が素集合なので **2 体を直列**で投入する (子 G → 親が hash 凍結 → 子 E)。
並列にすると「emitter 実装前に golden を凍結する」順序が保証できない。
