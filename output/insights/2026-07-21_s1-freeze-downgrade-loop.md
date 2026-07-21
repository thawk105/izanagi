# S-1 freeze `frozen_at_head` 格下げ wave ([T-005]+[T-063]+[T-068]) の逐語 (2026-07-21)

ハイブリッド標準ループ (/dev-wave) の各段の逐語。基準 HEAD `d06a3c3`、branch `worktree-dev-wave-ruling-ac`。
task-run = `20260721-s1-freeze-downgrade-92ee634c`。
**scope 判定・裁定の正本は worklog と D72 であり、本ファイルは素材である。**

本 wave も **実装せず裁定パッケージで終わった** ([T-005] は 2 wave 連続で差し戻し)。canonical 成果物
(`output/s1-freeze/*.json`、`output/s8b-freeze/holdout_freeze.json`) は 1 byte も変更していない。

逐語を残す理由は 2 つある。

1. **親の段 1 実測が「正しく測って誤った結論を出した」実例**であること。ancestry の格下げを
   runtime monkeypatch で模擬したため「現行 bytes の内容は健全」までは正しく測れたが、
   **実差分をモデル化していなかった**。実際には verifier 自身の bytes が成果物に pin されており、
   格下げのためにファイルを編集した瞬間に generator hash が外れる (自己 hash blocker)
2. **敵対相談 2 本が独立に同じ依存閉包へ到達した 2 回目**であること。D71 では
   S-1 → holdout → v1 trust root → v2 transition、本 wave では S-1 → known bytes →
   g1 transition + `FROZEN_MANIFEST`。**親が「触れない」と宣言した面 (P11) が、
   実は transition と両立しない**という同型の誤りだった

## 親が実測した一次資料 (F1..F17 の要点)

- **F1** `s1_known_axes_freeze.verify()` の失敗は ancestry ただ 1 点。generator sha256 一致 /
  63 source sha256 全一致 / s1b pairing ok / ccbench_pin 一致 / 機械再構成 identical
- **F2** `2066ce6b…` は `git cat-file` で bad object (repo に存在しない)
- **F3 (worklog 2026-07-21 (5) の記述を訂正)** measurement freeze は自前の dangling
  `frozen_at_head` を持つ (`s1_measurement_freeze.py:422`)。known_axes だけ格下げしても
  measurement は依然赤。「measurement も連鎖して通る」は**両方格下げした場合に限り**正しい
- **F8** 公式 oracle gate の現在の拒否集合はちょうど 4 件。格下げ後は 3 件になる
- **F9** `test_s8b_oracle_driver.py:506-507` は `any(startswith(...))` しか要求せず、
  この拒否集合の変化を 1 件も検出しない ([T-067] の具体的根拠)
- **F10** holdout の `current_head` を渡すのはテストだけ。production 呼出しは ancestry 枝
- **F13 (前提を反転させた)** 自己 hash blocker。1 行コメント追加で
  `1d4d45a3de4926c6…` → `93174926b84ac9ec…`、`verify()` は `generator sha256 不一致` で失敗
  (ancestry へ到達しない)。**「格下げのみ・bytes 不変」は原理的に不可能**
- **F14** `V1_FREEZE_SHA256` は holdout bytes (`315b1eb8…`) を pin しており **S-1 ではない**。
  機械的に変わる pointer は S-1 JSON 内では**ちょうど 4 つ** (DAG、循環なし)
- **F16** `s8b_oracle_driver.py` はどの freeze 成果物からも pin されていない
  → 消費側格下げ (選択肢 B) は canonical・checker とも byte 不変で可能。ただし判別が
  エラー文字列一致に依存する
- **F17** holdout は `design_source` に加えて `/generator` sha256 も既に不一致 (2 つの独立理由)

## 親が自ら確認した blocker (相談の指摘を鵜呑みにせず実測)

- **`FROZEN_MANIFEST`** (`test_frozen_artifacts.py:33`) が
  `known_axes_freeze.json` = `354f4b87…`、`measurement_freeze.json` = `203de36b…` を pin している。
  4 pointer transition はこの 2 件を必ず赤にする。**親も codex プランも見落としていた**
- **`_TRANSITION_V1_TO_G1`** は 12 pointer の frozenset で、`/known_axes_freeze/sha256` を
  **含まない** (実測 `known_axes pointer allowed: False`)。known bytes を変えると
  将来の g1 が `source-blob-mismatch` で構造的に生成不能になる

## 相談が訂正した親の主張

- **CB-06 (c1)**: 親の F11「格下げ後は別の実在 ancestor へ差し替えても ACCEPTED」は、
  **差分証拠としては refuted**。現行実装も任意の ancestor を既に受理している。
  格下げで新たに失うのは「存在しない SHA」と「実在する非 ancestor」の拒否である。
  ただし calibration provenance へ偽 SHA が流れる事故は具体的に構成できる (real)

---

## 段 1: brief v1 (親、逐語) — (P2)(P3)(P8)(F4)(F7) は後に撤回

# brief — [T-005]+[T-063]+[T-068] S-1 freeze `frozen_at_head` 格下げ wave

repo: /home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac (branch worktree-dev-wave-ruling-ac, 基準 d06a3c3)

## scope

ユーザー裁定 (2026-07-21、worklog 2026-07-21 (5)) で確定済み:
- **[T-068]** `frozen_at_head` を fail-closed 検査から**参考情報へ格下げ**する。内容同一性の検査は fail-closed のまま維持
- **[T-005]** S-1 freeze 再発行は単独実行せず [T-063] [T-068] と束ねる。着手前に「格下げだけで破損が解消するか」を実測すること
- **[T-063]** 再発行するなら許容 JSON Pointer 差分を明示列挙し、列挙外は前世代と厳密一致

## 段 1 実測確認の結果 (裁定の前提は成立。ただし 1 点訂正あり)

- **F1** `s1_known_axes_freeze.verify()` の失敗は **ancestry ただ 1 点**。generator sha256 一致 / 63 source sha256 全一致 / s1b pairing ok / ccbench_pin 一致 / 機械再構成 identical
- **F2** `2066ce6b...` は `git cat-file` で **bad object** (repo に存在しない)。「非 ancestor」ではない
- **F3 (worklog の記述を訂正)** measurement freeze は**自前の dangling frozen_at_head** を持つ (同一 SHA、`orchestrator/campaign/s1_measurement_freeze.py:422`)。known_axes だけ格下げしても measurement は依然赤。worklog (5) の「measurement も連鎖して通る」は**両方格下げした場合に限り**正しい
- **F4** s1 側 2 サイトを格下げすると **現行 bytes のまま** 両者 `verify()` が PASS → **[T-005] 再発行は不要**
- **F5** holdout は `design_source sha256 不一致` で**独立に**落ちる ([T-065])。格下げでは解消せず、公式 oracle gate は `holdout-freeze-verify` で拒否を継続 ([T-064]「oracle 非復旧」と整合)
- **F6** freeze/oracle 4 suite の baseline は **88 passed / 1 skipped で全緑** — 実成果物が検証不能なのに緑
- **F7 (最重要)** `orchestrator/tests/test_s1_known_axes_freeze.py:66` `test_verify_rejects_one_byte_freeze_tamper` は **今日は誤った理由で緑** (改竄でなく ancestry で raise)。格下げ後は機械再構成不一致で raise。**格下げは検出力を上げる**

## 不変条件 (破ったら失敗)

1. **canonical 成果物を 1 byte も変更しない** (`output/s1-freeze/*.json`、`output/s8b-freeze/holdout_freeze.json`)。再発行・再生成をしない
2. 内容同一性の検査 (generator sha256 / source sha256 / 機械再構成一致 / schedule_hash / implementation_hashes) は **fail-closed のまま**
3. `V1_FREEZE_SHA256` (v1 trust root)・`_TRANSITION_V1_TO_G1`・protocol golden・holdout の再生成に**触れない**
4. holdout は [T-064] 裁定どおり**据え置き** (design_source ドリフトは直さない)。公式 oracle gate は復旧しない
5. `s8b_ratified_freeze.py:535 / :2763` の ancestry は `frozen_at_head` ではない (世代グラフ / cert commit、trust root の一部) — **格下げ対象外**
6. 実装子はコードとテストのみ編集。**docs 編集・git commit は禁止**

## 親の provisional 裁定 (すべて攻撃対象。番号ごとに否認/採用を返せ)

- **(P1)** 格下げ対象は `frozen_at_head` の ancestry 表明ちょうど 3 サイト: `s1_known_axes_freeze.py:747-754` / `s1_measurement_freeze.py:417-425` / `s8b_holdout_freeze.py:665-681`
- **(P2)** [T-005] は「**再発行不要**」として閉じる。成果物は byte 不変のまま
- **(P3)** [T-063] は本 wave に実装面を持たない (再発行が起きないため)。ただし将来の再発行に備え「許容 pointer 列挙 + 列挙外は厳密一致」を**規則としてだけ** docs へ記録する (親が書く)
- **(P4)** 「参考情報へ格下げ」の意味 = 値と ancestry 状態を**記録・報告し続けるが raise しない**。field 削除ではない。40 桁 SHA の**形式検査は fail-closed のまま残す**
- **(P5)** [T-066] (`test_s1_measurement_freeze.py` の D68 (7) 型隠蔽) と [T-067] (oracle 拒否理由の exact 検査) を本 wave に**同梱**する。いずれも承認済み実装 wave であり、格下げが oracle の拒否集合を変えるため [T-067] は直接結合する
- **(P6)** **実成果物を verify する統合テストを新設**する (現在 1 本も無い、F6)。無いと格下げの目的そのものが未検証で終わる
- **(P7)** `test_verify_rejects_one_byte_freeze_tamper` に `match=` を入れ、誤った理由での緑へ退行できなくする (F7)
- **(P8)** 規律 2 に抵触しない根拠: ancestry は CC 正しさでなく **provenance** の検査であり、歴代 6 個すべてが不在で**一度も通ったことがない** (D71 (7b))。かつ格下げは遮蔽されていた下流の内容検査を**開放する** (F7)
- **(P9)** holdout の ancestry 枝も同時に格下げする (freeze 族共通の病、[T-068] の射程)。exact 一致枝 (`current_head` 指定時) は**変えない**

## 成果物の形

- コード差分: 3 サイトの格下げ + 参考情報としての報告経路
- テスト: 実成果物 verify の新設 / tamper テストの `match=` 強化 / oracle 拒否理由の exact 検査
- docs (親が書く): worklog・decisions (D72)・insights 凍結

## 並列分割の方針

- 単位 A: `orchestrator/campaign/s1_known_axes_freeze.py` + `s1_measurement_freeze.py` + `orchestrator/tests/test_s1_known_axes_freeze.py` + `test_s1_measurement_freeze.py`
- 単位 B: `orchestrator/campaign/s8b_holdout_freeze.py` + `orchestrator/tests/test_s8b_holdout_freeze.py` + `test_s8b_oracle_driver.py`
- ファイル所有は素集合。単位間に import 依存があれば先行単位を land させてから残りを並列化する

## 既知の罠

- **dual-import**: `campaign.X` と `orchestrator.campaign.X` は別 module object。片方だけ patch すると誤結論 (親が一度踏んだ)
- holdout `_verify_head` は二相 (`current_head` 指定時は exact 一致)

---

## 段 1′: brief v2 (親、逐語) — 自己 hash blocker 判明後の訂正版

# brief v2 — 裁定の前提が変わった (段 1 の実測モデルに欠陥があった)

**brief v1 の (P2)(P3)(P8) と (F4)(F7) は撤回する。** codex プラン v1 が指摘した
**自己 hash blocker** を親が実測で確認した。以下が訂正後の一次資料である。

## 何が間違っていたか

親の段 1 実測確認は **runtime monkeypatch** で ancestry を迂回した。これは
「現行 bytes の内容が健全か」は正しく測ったが、**実際の差分をモデル化していなかった**。

- `known_axes_freeze.json` は `/generator/sha256` に **`s1_known_axes_freeze.py` 全 bytes の
  sha256** を固定している (`1d4d45…`、現行ファイルと一致)
- verifier はその照合を **ancestry より前** (`s1_known_axes_freeze.py:724`) で行う
- ゆえに **ancestry を格下げするために当該ファイルを編集すると、generator hash が外れ、
  ancestry へ到達する前に落ちる**

**親の実測 (2026-07-21):** 当該ファイルに 1 行コメントを足すと hash は
`1d4d45a3de4926c6…` → `93174926b84ac9ec…` へ変わり、`verify()` は
`generator sha256 不一致` で失敗した (ancestry には到達しない)。ファイルは復元済み。

→ **「格下げのみで、成果物を 1 byte も変えずに閉じる」は原理的に不可能。**
SHA-256 の第二原像を作らない限り、「canonical 不変」「generator 全 bytes hash 照合の維持」
「同じファイル内の verifier を変更」の三条件は両立しない。

## ユーザー裁定はこの分岐を既に想定している

[T-005] の裁定文 (worklog 2026-07-21 (5)):
> 着手前に「[T-068] の格下げだけで破損が解消するか」を実測で確認すること — 解消するなら
> 再発行は行わず格下げのみで閉じる。**解消しない場合のみ [T-063] の差分契約に従って再発行する**

実測は「解消しない」を示した。よって **[T-063] の差分契約に従う経路が発火する**。
[T-063] の裁定は「変わってよい箇所を明示列挙し、列挙外は前世代と厳密一致」であり、
その具体列挙は「[T-005] の wave で起草する」と定められている。**それが本 wave の主成果物になる。**

## 依存閉包の実測 (D71 の懸念は [T-064] 裁定で切れている)

- **`V1_FREEZE_SHA256` は `output/s8b-freeze/holdout_freeze.json` の bytes を固定している**
  (実測 `315b1eb8…` = holdout bytes)。**S-1 ではない。**
  → S-1 側の pointer transition は **v1 trust root に触れない**
- `_TRANSITION_V1_TO_G1` と protocol golden も holdout 側の機構であり触れない
- holdout は `known_axes_freeze.json` の bytes (`354f4b…`) を参照する。S-1 を変えると
  この参照は陳腐化するが、**[T-064] 裁定「据え置き・oracle 非復旧」がこれを受容済み**。
  かつ holdout は既に `design_source` と `generator` の **2 つの理由で独立に落ちている**
  (codex 指摘、親未検証 → 相談で裏取りせよ)

## 許容 JSON Pointer の最小集合 (実測に基づく [T-063] の起草案)

verifier 2 ファイルを編集する場合、**機械的に必ず変わる pointer はちょうど 4 つ**:

| # | ファイル | pointer | 変わる理由 |
|---|---|---|---|
| 1 | `output/s1-freeze/known_axes_freeze.json` | `/generator/sha256` | `s1_known_axes_freeze.py` の bytes が変わる |
| 2 | `output/s1-freeze/measurement_freeze.json` | `/generator/sha256` | `s1_measurement_freeze.py` の bytes が変わる |
| 3 | 同上 | `/implementation_hashes/s1_measurement_freeze/sha256` | 同じファイルの二重 pin |
| 4 | 同上 | `/implementation_hashes/known_axes_freeze/sha256` | #1 により known_axes JSON の bytes が変わる |

- 依存は **DAG** (known_axes は .py のみに依存、measurement は .py 群 + known_axes JSON に依存)。
  循環・不動点は無い。適用順序は known_axes → measurement
- `/frozen_at_head` は **変更しない** (dangling 値のまま参考情報として残す)
- 上記 4 点以外は **byte-for-byte 厳密一致**。これを機械検査するテストを置く

## 設計上の発見 (裁定パッケージ候補)

**成果物が「自分を検証する checker」を pin している。** ゆえに checker のバグ修正・仕様変更は
**必ず canonical 成果物の再発行を強制する**。「凍結」と称しながらコード保守に対して凍結できていない。
通常の設計は入力と出力を pin し checker は pin しない。本 wave はこの性質に正面衝突した。
恒久的な設計判断としてユーザーへ返すべき論点 (本 wave では実装しない)。

## 改訂した provisional 裁定 (再度すべて攻撃対象)

- **(P1′)** 格下げ対象は ancestry 表明のみ。holdout は `s8b_holdout_freeze.py:674-680` **だけ**
  (665-673 の形式検査と exact 枝は対象外)。codex の行範囲訂正を採用
- **(P2′) 撤回・反転**: [T-005] は「再発行不要」では閉じない。**4 pointer の外科的
  provenance transition を行う**。再生成 (regenerate) はしない
- **(P3′) 撤回・反転**: [T-063] は本 wave の**主成果物**。上表が起草案
- **(P4)** 維持: 値と ancestry 状態を報告し続ける。40 桁形式検査は fail-closed のまま
- **(P5)** 維持: [T-066] [T-067] を同梱
- **(P6′)** 条件付き維持: 実 S-1 成果物の positive integration test は現存しない (核心は正しい)。
  ただし「実成果物 verify が 1 本も無い」は不正確 — oracle gate test が実 holdout を verify している
- **(P7)** 維持: `match=` を機械再構成エラーへ固定
- **(P8′) 撤回**: 「格下げは検出力を上げる」は runtime bypass でのみ成立。実差分では
  自己 hash が新しい短絡点になる。ただし **transition 後**は下流が開放される (要裁定)
- **(P9)** 維持: ancestry 枝のみ格下げ、exact 枝は不変
- **(P10 新)** 許容 pointer は上表の 4 点ちょうど。列挙外の厳密一致を**機械検査**する
- **(P11 新)** v1 trust root・transition table・protocol golden・holdout 成果物は**一切触れない**
- **(P12 新)** holdout の known_axes 参照の陳腐化を受容する ([T-064] 裁定の射程内)
- **(P13 新)** 「checker を pin する設計」の是非は本 wave で実装せず裁定パッケージへ回す

## 相談への追加設問

1. **この transition を行ってよいか。** 実装せず [T-005] を再びユーザーへ差し戻すべき理由があるか。
   D71 で一度差し戻された領域である。**前回と何が変わったのか**を厳密に述べよ
2. 4 pointer の集合は**過不足ないか**。他に機械的に変わる pointer、あるいは
   「変える必要がないのに変えてしまう」pointer はないか
3. transition 後に **新たに到達する下流検査**が現行 bytes で実際に通るか
4. この transition を**誰が検証できるか**。transition 前後で「内容が変わっていないこと」を
   第三者が独立に確認する手段は残るか (provenance の消失)
5. `frozen_at_head` は格下げ後 **40 桁形式以外の完全性保証を完全に失う**
   (親の実測: 別の実在 ancestor commit へ差し替えても ACCEPTED)。これは受容可能か

---

## 段 2: プラン v1 (codex gpt-5.6-sol / reasoning=max / read-only、逐語)

## 結論

この brief は現行制約のままでは **NO-GO** です。格下げロジック自体は設計できますが、S-1 の 2 ファイルが canonical artifact に自己 hash されているため、コードを編集すると ancestry より前で必ず拒否されます。

- known artifact は [known_axes_freeze.json:5](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/known_axes_freeze.json:5>) で `s1_known_axes_freeze.py` 全 bytes の SHA-256 `1d4d45…` を固定し、現行ファイルと一致しています。
- verifier は ancestry より前の [s1_known_axes_freeze.py:724](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:724>) で現行ファイル全体を hash します。
- measurement も [measurement_freeze.json:7](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/measurement_freeze.json:7>) と [同:1292](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/measurement_freeze.json:1292>) で `s1_measurement_freeze.py` を二重に固定し、[s1_measurement_freeze.py:394](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:394>) で ancestry より先に検査します。

したがって、意図した編集後の実際の順序は次です。

```text
S-1 verifier ファイルを編集
  → generator / implementation hash が canonical と不一致
  → ancestry 観測へ到達しない
  → canonical 実成果物 verify は依然 FAIL
```

これは D68 (7) が既に記録している自己 hash 問題そのものです。SHA-256 の第二原像を作らない限り、「canonical を 1 byte も変更しない」「現行 generator 全 bytes の hash 検査を維持」「同じファイル内の verifier を変更」の三条件は両立しません。

必要な先行裁定は次のどちらかです。

1. canonical の最小 provenance transition を許可する。
2. コード変更を中止する。

前者の最小許容 JSON Pointer は、再生成ではなく以下だけです。

- known: `/generator/sha256`
- measurement:
  - `/generator/sha256`
  - `/implementation_hashes/s1_measurement_freeze/sha256`
  - `/implementation_hashes/known_axes_freeze/sha256`

`/frozen_at_head` は参考情報として残すため変更不要です。列挙外は byte-for-byte 同一にできます。ただし、これは依頼の canonical byte 不変制約に反します。

## provisional 裁定への回答

| 裁定 | 判定 | 根拠 |
|---|---|---|
| P1 | 条件付き採用 | ancestry 表明は semantic には 3 サイト。ただし holdout の対象は [s8b_holdout_freeze.py:674](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:674>)–680 だけで、665–673 の形式・exact 枝は対象外。実際の編集面は log/helper/import まで広がる。 |
| P2 | 否認 | 「再発行不要」は runtime monkeypatch なら成立するが、実ファイル編集では自己 hash 不一致になる。 |
| P3 | 否認 | P2 が成立しないため、T-063 は上記の最小 pointer transition として実装面を持つ。 |
| P4 | 採用 | field と 40 桁 lowercase hex 検査を残し、ancestry 失敗だけ非致命化する。 |
| P5 | 採用・ただし blocked | T-066/T-067 は必要。ただし exact oracle テストが自己 hash 問題を即座に赤で検出する。 |
| P6 | 趣旨採用 | positive な S-1 canonical verify テストはない。ただし「実成果物 verify が一本もない」は不正確で、[test_s8b_oracle_driver.py:503](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:503>) が実 holdout を gate 経由で verify している。 |
| P7 | 採用 | `match=` は最終機械再構成エラーへ固定すべき。ただし現制約下でコード編集後は generator hash エラーが先行し、このテストが赤になる。 |
| P8 | 否認 | runtime bypass では下流を開放するが、実差分では自己 hash が新しい短絡点になる。「格下げで検出力が上がる」という説明は実 landing には当てはまらない。 |
| P9 | 採用 | `current_head is None` の ancestry 枝のみ非致命化し、exact 枝は完全維持する。 |

## 制約解消後の正確な実装形

### 1. 3 verifier 共通の形

各ファイル内の `_run_git` 直後に、ローカルな `_observe_frozen_head_ancestry()` と logger を置きます。共有 module 化はしません。共有 helper は generator の新しい未記録依存になり、将来 helper だけ変更しても artifact の generator hash が発火しないためです。

観測 event は同じ schema に揃えます。

```json
{
  "event": "frozen_at_head_observation",
  "site": "s1-known-axes | s1-measurement | s8b-holdout",
  "recorded": "40hex",
  "mode": "ancestry | exact",
  "status": "ancestor | cat-file-failed | merge-base-failed | exact-match",
  "reference_only": true,
  "detail": "optional error"
}
```

- canonical JSON へ field は足さない。
- `verify()` の戻り値は従来どおり document。
- `verify_document()` の signature も変えない。
- JSON 化した event を log message と `LogRecord` の extra field の双方へ載せる。
- ancestry failure は warning、成功は info。
- `try/except FreezeError` は専用 helper 内の Git 2 呼出しだけを囲む。`ccbench_pin`、再構成、検索、binding を同じ `try` に入れない。これが道連れ無効化を構造的に防ぐ境界です。

既存 consumer は [s1_report.py:762](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:762>) で `verify()` の Mapping 戻り値を要求し、[s1_direct_comparison.py:117](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:117>) は `Callable[[Mapping], None]` を注入します。したがって戻り値変更は避けるべきです。

### 2. known axes

[s1_known_axes_freeze.py:747](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:747>)–754 を次の形にします。

- 747–749 の 40 桁形式検査はそのまま。
- 750–754 の `try/except → raise` を `_observe_frozen_head_ancestry(frozen_head)` の一呼出しへ置換。
- [同:755](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:755>)–766 の ccbench pin と再構成比較は無変更かつ helper の外。

### 3. measurement

[s1_measurement_freeze.py:417](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:417>)–425 も同形です。

- 417–419 の形式検査を残す。
- 420–425 の ancestry raise だけ観測呼出しへ置換。
- [同:426](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:426>)–444 の pin・再 build・cells・full document 比較を helper 外に維持。

### 4. holdout の二相

[s8b_holdout_freeze.py:665](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:665>)–680 は次の分離にします。

```python
形式不正:
    raise

if current_head is not None:
    current_head の形式不正または recorded != current_head:
        raise
    exact-match を報告
    return

_observe_frozen_head_ancestry(recorded, root)  # raise しない
```

つまり 668–673 は byte 意味論を維持し、674–680 だけを格下げします。

## `_verify_head` の全呼出し経路

repo 内で `_verify_head` の直接 caller は [verify_document():712](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:712>) だけです。`current_head` 指定はテストにしかありません。

| 呼出し元 | 到達する枝 |
|---|---|
| [test_s8b_holdout_freeze.py:202](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:202>) | source が通り exact-match 枝 |
| [同:209](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:209>) | design hash で先に拒否。exact 枝へ未到達 |
| [同:218](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:218>) | exact-match 後、binding で拒否 |
| [同:236](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:236>) | exact-match、下流も通過 |
| [同:244](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:244>) | exact-match 後、snapshot hash で拒否 |
| [同:250](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:250>) | exact-match 後、live holdout hit で拒否 |
| [同:403](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:403>) | exact-match、下流も通過 |
| [同:412](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:412>) | `_reject_unratified_generation()` が先行し exact 枝へ未到達 |

一方、公式 oracle の [s8b_oracle_driver.py:222](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:222>) と CLI の [s8b_holdout_freeze.py:871](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:871>) は `current_head=None`、すなわち ancestry 参考枝です。

## 新たに到達する下流検査

静的照合結果は次のとおりです。

### known axes

現行 bytes については以下を確認しました。

- source record 63 件、欠落 0、hash 不一致 0。
- generator hash は現行ファイルと一致。
- ccbench HEAD `d706650c…` は artifact の pin と一致。
- pairing の基本 shape は一致。

ancestry 後に開くのは [s1_known_axes_freeze.py:755](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:755>)–766 の pin と機械再構成です。ただし実コード編集後は [同:724](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:724>) の自己 hash で先に落ちます。

### measurement

現行 bytes では以下が一致しています。

- generator / `s1_measurement_freeze` hash。
- `s1_stats` hash。
- known artifact bytes hash。
- `ccbench_pin=d706650` と [pin.py:28](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/pin.py:28>)。

新規到達点は [s1_measurement_freeze.py:426](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:426>)–444 です。特に `build_document()` が [同:249](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:249>) で known verifier をもう一度呼ぶため、known の generator/source/pairing/pin/reconstruction 一式が二度目に走ります。brief が列挙していない追加到達経路です。

実コード編集後は [同:395](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:395>) の自己 hash で先に落ちます。

### holdout

canonical は ancestry へ到達しません。

- design source: recorded `1829af…`、actual `5fbdd7…`。
- generator: recorded `1910ff…`、actual `41c0b6…`。
- known artifact hash は一致。

したがって [s8b_holdout_freeze.py:709](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:709>) の design mismatch が最初、仮に直しても 711 の generator mismatch が次です。brief F5 は最初の理由としては正しいものの、generator mismatch を落としています。

source が一致する synthetic artifact では、dangling ancestry 後に 714–823 の live repository search、陽性対照、snapshot hash、holdout hit、binding、top-level positive control がすべて新たな攻撃面になります。

## テスト計画

### 実成果物 integration

- [test_s1_known_axes_freeze.py:66](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:66>) の前に `test_verify_real_canonical_freeze()` を追加し、`M.verify(M.FREEZE_PATH)` が返す document を元 JSON と比較。
- [test_s1_measurement_freeze.py:166](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:166>) 付近に同形の canonical verify を追加。
- submodule skip は既存 [test_s1_known_axes_freeze.py:26](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:26>) と同じく `external/ccbench/.git` 不在時だけ。init 済みで source 欠落なら skip せず赤。
- holdout は pass テストでなく、canonical が exact な `design_source sha256 不一致` で拒否される integration test にする。

この S-1 integration test は現制約下の実装差分では generator hash mismatch で赤になり、まさに blocker を機械検出します。

### tamper の `match=`

[test_s1_known_axes_freeze.py:73](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:73>) を次へ強化します。

```python
with pytest.raises(
    M.FreezeError,
    match="^freeze JSON の内容が現行 generator による機械再構成と不一致$",
):
    M.verify(path)
```

`sp_dd → xp_dd` は schema/source/pairing/pin を通り、最後の再構成だけで落ちる入力です。generator mismatch や ancestry で誤って緑になる退行を排除できます。

measurement の `what` 改竄 [test_s1_measurement_freeze.py:192](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:192>) も同じ再構成 message へ固定するのが妥当です。

### T-067 oracle exact

[test_s8b_oracle_driver.py:503](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_driver.py:503>) を、prefix/`any()` ではなく順序込み完全一致へ変更します。

期待値は格下げと S-1 canonical verify が成立した場合、次の 3 件だけです。

```python
assert decision == driver.GateDecision(
    allowed=False,
    refusals=[
        "holdout-freeze-verify: FreezeError: "
        "design_source sha256 不一致: "
        "recorded=1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d "
        "actual=5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae",
        "floor-null: freeze.floor が null",
        "budget-null: freeze.budget が null",
    ],
)
```

submodule 未 init 時はこの exact test だけ skip。init 済みで欠落なら赤にします。

現制約のまま S-1 を編集すると、2 番目に以下が増えて赤になります。

```text
known-axes-freeze-verify: FreezeError:
generator sha256 不一致: recorded=1d4d45… actual=<post-edit hash>
```

### dangling head の積極テスト

3 サイトすべてで追加します。

- known/measurement: canonical artifact 自身の `2066ce…` が bad object なので、実成果物 integration が「dangling でも raise しない」positive controlを兼ねる。さらに log record の `status == "cat-file-failed"` を確認。
- holdout: `_synthetic_freeze_root()` を Git repo 化し、存在しない `"f" * 40` を `frozen_at_head` にして `current_head` を省略。source/search/binding が全部通り、warning observation が 1 件出ることを検査。
- 各サイトで `"z" * 40` は引き続き形式検査で拒否する negative control を置く。
- holdout では dangling head と binding tamper を同居させ、「ancestry 失敗を捕捉しても下流 binding error は捕捉しない」ことも検査する。

### T-066 fixture 隠蔽

[test_s1_measurement_freeze.py:91](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_measurement_freeze.py:91>)–117 を変更します。

- production K の現行 HEAD/hash 注入を削除。
- `K.build_document` の echo monkeypatch を削除。
- measurement 単体 fixture では `M._verify_known_axes` を明示的 synthetic seam として差し替え、固定 known document を返す。
- production K の integrity は canonical integration test だけに担わせる。

## 変異候補 5 件

前提として [test_s8b_holdout_freeze.py:75](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_holdout_freeze.py:75>)–77 の `M.__file__` copy を固定 fixture generator bytes に置き換えます。現状のままだと mutant ごとに input artifact の generator hash まで変わり、「同じ入力」条件を満たしません。

| ID | 変異 | 同じ入力を先行拒否する検査 | 単一理由で赤になる根拠 |
|---|---|---|---|
| M1 | [s8b_holdout_freeze.py:666](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:666>)–667 の recorded 形式検査を無効化 | schema/source は head の値を見ない | `"z"*40`, `current_head=None` は baseline だけ形式エラー。mutant は ancestry failure を参考化して下流を通す |
| M2 | [同:669](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:669>) の `recorded != current_head` を削除 | recorded/current とも 40hex なら先行拒否なし | recorded=`a*40`, current=`b*40`。baseline は exact mismatch、mutant だけ受理 |
| M3 | ancestry observer の failure pathを旧 `raise` に戻す | source は固定 fixture で一致、head 形式も正しい | dangling `f*40`, `current_head=None`。baseline だけ受理、mutant だけ ancestry 拒否 |
| M4 | [同:711](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:711>) の generator `_verify_source` 呼出しを削除 | design/known source は一致。nested generator record を見る先行検査なし | document の generator hash だけ `0*64` にする。baseline だけ source mismatch、mutant は下流通過 |
| M5 | [同:812](</home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:812>)–813 の binding equality を削除 | source/head/search/snapshot は binding 内部値を見ない | dangling head + binding identity だけ改竄。baseline は binding mismatch、mutant だけ受理 |

S-1 ファイル内への通常の file mutation は generator self-hash が先行するため、現制約では全件「登録不可」です。ancestry guard を変異しても canonical input は generator mismatch で先に落ち、kill の帰属が成立しません。

## ファイル所有分割

brief の A/B はファイル集合としては素ですが、実行依存は素ではありません。

- A: known/measurement 実装 + 両テスト。
- B: holdout 実装 + holdout テスト。
- `test_s8b_oracle_driver.py` は driver が known と holdout の双方を import し、期待 refusal 集合が A の格下げ結果に依存します。

したがって推奨分割は次です。

1. A — S-1 コード・T-066・S-1 integration。
2. B — holdout コード・二相テスト・変異用 fixture。
3. C — A/B landing 後に `test_s8b_oracle_driver.py` の exact refusal。

A と B は共有 helper を作らない限り並列可能ですが、C は必ず後です。現状は A が自己 hash blocker で開始不能です。

## brief の具体的な誤り

1. **F4/P2 が実差分をモデル化していない。** ancestry を runtime で迂回すれば通りますが、実ファイルを編集すると generator hash が先に外れます。
2. **F7 の「格下げ後は機械再構成不一致」は実 landing では誤り。** canonical 不変なら先に generator hash mismatch です。
3. **F5 は不完全。** holdout は design source だけでなく generator hash も既に不一致です。
4. **P1 の holdout 行範囲が広すぎる。** 665–681 全体ではなく、格下げ対象は 674–680。668–673 は exact fail-closed 枝です。
5. **P6 の「実成果物 verify が現在 1 本もない」は文字どおりには誤り。** real holdout は oracle gate test が verify しています。ただし unmodified S-1 artifact の positive integration がない、という核心は正しいです。
6. **P8 の下流開放説明は runtime bypass にしか成立しない。** 実差分では自己 hash が新しい短絡点になります。
7. **P3 は P2 依存なので成立しない。** requested behavior を landing するには、少なくとも上記 4 pointer の provenance transition が必要です。

pytest は実行していません。基準 `d06a3c3` の関連ファイルが clean な状態で、Git object、SHA-256、source 63 件、submodule pin、呼出し経路だけを静的に確認しました。
---

## 段 3a: 敵対相談 — 正しさ境界レンズ (codex、逐語)

# 結論

**NO-GO**。S-1 成果物内で機械的に変わる値が 4 pointer だけ、という局所分析は正しい。しかし D71 の依存閉包は解消していない。

特に、known-axes の bytes を変えると、承認済み holdout v2 の transition 契約では将来の g1 が構造的に生成不能になる。さらに `FROZEN_MANIFEST`、oracle manifest、ratified-freeze fixture、実 repo 並列化台帳がプランの所有範囲から落ちている。

## 所見

### CB-01 — blocker / real

- **file:line:** [s8b_ratified_freeze.py:115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:115)、[同:934](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:934)、[test_s8b_ratified_freeze.py:428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:428)、[同:572](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:572)
- **壊れ方:** S-1 transition 後の known JSON hash を `K_new` とする。legacy holdout は旧 `K_old` を保持し、v1→g1 allowlist は `/known_axes_freeze/sha256` を許さないため、g1 は `K_old` を継承する。一方、g1 の `frozen_at_head` の blob には現行 known JSON、すなわち `K_new` が存在する。`_verify_generation_semantics()` は `K_new != K_old` を検出して `source-blob-mismatch` で拒否する。次回の正規 floor 再凍結が永久に通らない。
- 現存 happy-path fixture も、現行 known bytes を base にコピーしてから `g1 = dict(v1)` するため、transition 後は [test_happy_path_resolves_and_loads:852](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:852) が同じ理由で赤になる。
- **推奨対処:** 人間裁定を取り直し、v1→g1 に限って `/known_axes_freeze/sha256` を許可し、g1 emitter が parent blob の新 hash を記録するようにする。path は引き続き protected にする。許可しないなら S-1 transition 自体を中止する。
- **scope:** 影響は scope 内変更から発生するが、修正対象は P11 が明示的に scope 外としている trust/transition 面。

### CB-02 — blocker / real

- **file:line:** [test_frozen_artifacts.py:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33)、[同:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:61)、[decisions.md:2747](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2747)
- **壊れ方:** 4 pointer transition は S-1 JSON 2 本の全 bytes SHA を変える。現在の manifest は旧 hash を固定しているため、更新しなければ `test_frozen_artifacts` が必ず誤拒否する。反対に、新 hash へ単純に追随させるだけなら、「S-1 本文も変更した成果物 + それに合わせた manifest」を同じ producer が同時更新しても通り、T-063 の前世代同一性を検査できない。
- D71 自身が「一回限りの receipt とし、新 hash と receipt hash を `FROZEN_MANIFEST` に再 pin」と要求しているが、brief v2 と所有分割には receipt も `test_frozen_artifacts.py` もない。
- **推奨対処:** old/new artifact SHA、old/new generator SHA、許可 4 pointer、基準 commit、raw-byte 差分証明を持つ immutable receipt を作り、その receipt と新 S-1 2 hash を manifest に pin する。artifact と manifest の更新者・レビュー者も明示する。
- **scope:** T-063 の本体なので論理上 scope 内。ただし現在の A/B/C 所有集合から漏れており、明示的な scope 拡張が必要。

### CB-03 — major / real

- **file:line:** [s8b_ratified_freeze.py:614](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:614)、[同:645](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:645)、[s1_known_axes_freeze.py:118](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:118)、[同:765](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:765)
- **壊れ方:** T-063 のテストを既存 `_assert_transition()` と同じ leaf-value 比較で作ると、4 hash を更新したうえで JSON のインデント変更、key 並べ替え、末尾空白追加を行っても、列挙外の leaf 値は同じなので通る。S-1 loader と最終比較も parsed dict しか見ない。manifest を新 hash へ repin すれば、宣言上禁止された列挙外 byte 変更が受理される。
- 通常の `json.loads` は duplicate key も最後の値へ潰すため、object 比較だけでは raw-byte 契約にならない。
- **推奨対処:** transition 後 bytes から許可された 4 値だけを旧値へ戻し、再構成した raw bytes の SHA が receipt の旧 artifact SHA と一致することを検査する。空白変更・key reorder・duplicate key を入れる負例を置く。
- **scope:** scope 内。

### CB-04 — major / real

- **file:line:** [s8b_oracle_manifest.py:625](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:625)、[同:296](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:296)、[test_s8b_oracle_manifest.py:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_manifest.py:112)、[同:133](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_oracle_manifest.py:133)
- **壊れ方:** known JSON を更新して legacy holdout の参照を旧 hash のままにすると、`build_manifest()` は floor/budget 検査より先に現行 known bytes を旧 record と照合し、`参照 source sha256 不一致` で拒否する。現在「floor/budget null の理由で拒否」を検査しているテストは異なる先行理由で赤になる。floor/budget を充填する synthetic fixture も旧 record を引き継ぐので、manifest の schedule/binding 検査へ到達しなくなる。
- `test_s8b_oracle_driver.py` の refusal 1 本だけ直しても、この consumer 群は残る。
- **推奨対処:** production の stale-reference 負例は保持しつつ、manifest 単体 fixture は固定 synthetic known bytes と対応する固定 record を使う。`test_s8b_oracle_manifest.py`、ratified freeze 群、driver manifest fixture を依存閉包へ追加する。
- **scope:** 影響は scope 内。必要なテスト修正ファイルは現在の所有分割では scope 外。

### CB-05 — major / real

- **file:line:** [s8b_holdout_freeze.py:709](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:709)、[同:712](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:712)、[s1_report.py:759](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:759)、[同:767](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:767)
- **壊れ方:** canonical holdout は `design_source` 不一致で `_verify_head()` より前に停止するため、提案された observer は一度も状態を報告しない。measurement 側では dangling head を warning log に出しても、`verify()` は従来どおり document だけを返すため、`s1_report` は warning を取り込まず `freeze.status=pass` と記録する。結果として「参考情報として報告し続ける」という説明に反し、成果物上は無条件 pass に見える。
- exact-match/ancestor 成功を `logger.info` にする案も、logger 設定や handler のない現コードでは通常出力へ現れない。
- **推奨対処:** `document + observations` の型付き結果、または optional collector を設け、report、calibration、oracle driver が構造化状態を保存する。ログだけを契約にするなら、全状態を確実に出力する handler/level と consumer 検査が必要。
- **scope:** observer 自体は scope 内。report/calibration/oracle への状態伝播は現在の分割外。

### CB-06 — major / real

- **file:line:** [s1_known_axes_freeze.py:759](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759)、[s1_measurement_freeze.py:430](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:430)、[s1_verify_extime_calibration.py:193](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:193)、[同:403](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:403)
- **壊れ方:** canonical と同じ document の `frozen_at_head` だけを `"0"*40`、または実在する非 ancestor branch commit にする。格下げ後は形式検査を通り、再構成側にはその値がそのまま注入されるため document 比較も通る。calibrator はこれを検証済み freeze として受理し、`configuration_provenance.freeze_frozen_at_head` に偽 SHA を出力する。
- 親の「別の実在 ancestor へ変えても受理」は差分証拠としては **refuted**。現行実装も「任意の ancestor」を既に受理する。格下げによって新たに失うのは、存在しない SHA と実在 non-ancestor の拒否である。
- **規律 2:** 現 consumer と内容 hash/reconstruction を前提に、これを CC variant の誤選択へ結び付ける反例は構成できなかった。ただし provenance/evidence の誤受理は具体的に構成できる。したがって「CC 内容検査ではない」は成立するが、「正しさへの影響がない」は成立しない。
- **推奨対処:** field と consumer 出力を `unverified_recorded_head` 相当に明示し、`status=cat-file-failed/non-ancestor/ancestor` を同じ成果物へ残す。calibration の `configuration_provenance` に未検証 SHA だけを置かない。
- **scope:** 格下げ自体は scope 内。calibration/report の意味修正は scope 外。

### CB-07 — major / real

- **file:line:** [conftest.py:70](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:70)、[同:91](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:91)、[test_real_repo_serialization.py:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_real_repo_serialization.py:28)、[test_s1_known_axes_freeze.py:66](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:66)
- **壊れ方:** 新設する known/measurement canonical integration は実 repo と実 submodule を読む。現在は known の既存 node だけが xdist の real-repo group にあり、measurement 全件は synthetic という前提で除外されている。並列 writer が `Options.cmake` 等を一時変更している窓で新テストが走ると、正しい artifact を source mismatch と誤拒否する。
- known tamper テストへ最終再構成の `match=` を追加するだけでは、fresh clone の未 init submodule で先行 `source が存在しない` となり、意図した skip ではなく誤失敗する。
- known テストの素 runner は [test_s1_known_axes_freeze.py:156](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:156) で `tmp_path` しか注入しないため、ログ検査に `caplog` fixture を直接追加すると素 runner が `TypeError` になる。
- **推奨対処:** 新 node を `conftest.py` と独立 golden の両方へ追加し、tamper テストにも `_require_submodule_sources()` を置く。ログ検査はローカル handler を使うか素 runner を明示対応させる。
- **scope:** テスト目的は scope 内。`conftest.py` と serialization golden は現在の所有分割外。

### CB-08 — major / refuted

- **file:line:** [s1_known_axes_freeze.py:755](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:755)、[s1_measurement_freeze.py:426](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:426)、[s8b_holdout_freeze.py:714](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:714)
- **壊れ方:** プラン記載どおり observer helper の `try/except` を Git 2 呼出しだけに閉じれば、dangling head と binding tamper を同居させた入力は observer 後に binding mismatch で拒否される。ccbench pin、再構成、search、binding の道連れ無効化は生じない。
- **推奨対処:** helper 外境界をコードレビューで固定し、dangling + downstream tamper の複合負例を維持する。
- **scope:** scope 内。

### CB-09 — major / refuted

- **file:line:** [s8b_holdout_freeze.py:665](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:665)、[同:668](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:668)、[s8b_oracle_driver.py:222](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:222)
- **壊れ方:** `recorded="a"*40, current_head="b"*40` は現 exact 枝で拒否される。提案どおり 674–680 だけを変える限り、exact mismatch は observer へ入らない。repo 内の `current_head=` caller はテストだけで、production oracle/CLI は ancestry 枝である。
- **推奨対処:** 形式、exact mismatch、exact match の 3 テストを独立に固定する。
- **scope:** scope 内。

### CB-10 — major / refuted（S-1 局所に限る）

- **file:line:** [s1_known_axes_freeze.py:634](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:634)、[s1_measurement_freeze.py:252](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:252)、[同:263](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:263)
- **壊れ方:** observer 以外の生成意味論を変えない限り、S-1 JSON 内で必要な変更は brief の 4 pointer で過不足ない。known は self hash 1 点、measurement は self hash 2 点と known JSON bytes hash 1 点である。
- read-only 照合では known の source record 63 件は欠落 0・hash 不一致 0、ccbench HEAD は `d706650…` で pin と一致した。したがって 4 値を最終コード hash へ更新した後、S-1 verifier 内の下流検査が新たに落ちる静的根拠は見つからない。
- **推奨対処:** この局所結論を repository 全体の GO 根拠へ拡張しない。
- **scope:** scope 内。

## consumer 全列挙

| consumer | 読み方 | transition 後 |
|---|---|---|
| [s1_measurement_freeze.py:156](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:156) | known verifier を直接呼ぶ | 4 pointer が正しければ通る。再構成中に known を再度検証する |
| [s1_verify_extime_calibration.py:193](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:193) | known を検証後、head を provenance に転記 | bogus 40hex を検証済み provenance として出力し得る |
| [s8b_oracle_driver.py:249](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:249) | holdout 内の path から known を直接 verify | known refusal は消える。holdout 自身の旧 known hash はここでは照合しない |
| [s1_report.py:750](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:750) | measurement `verify()` | observer 状態を保存せず freeze pass とする |
| [s1_direct_comparison.py:115](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_direct_comparison.py:115) | measurement `verify_document()` | 内容は使えるが observation は捨てる |
| [s8b_oracle_driver.py:216](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:216) / holdout CLI | legacy holdout verifier | real artifact は design mismatch で observer 未到達 |
| [s8b_oracle_manifest.py:616](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_manifest.py:616) | holdout の known record と現物を照合 | 新 known bytes を旧 holdout record が拒否 |
| [s8b_ratified_freeze.py:901](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:901) | v2 source blob + transition | P11 のままでは次の g1 を拒否 |
| [s8b_ratified_freeze.py:1329](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:1329)、[s8b_selector_freeze.py:735](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_selector_freeze.py:735) | legacy holdout bytes を `V1_FREEZE_SHA256` で exact pin | holdout bytes 不変なら無傷 |
| [test_frozen_artifacts.py:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:61) | S-1 JSON 全 bytes pin | manifest 更新なしでは必ず赤 |
| check 系 tools | `frozen_at_head` の直接 consumer なし | `check_docs` 等への直接影響なし |

## 追加設問への回答

1. **この transition を行ってよいか:** 現状は不可。D71 以後に変わったのは、自己 hash blocker が確定したこと、T-064 が legacy holdout の stale reference と当面の oracle 非復旧を受容したこと、S-1 が `V1_FREEZE_SHA256` 自体ではないと確認できたこと。しかし、承認済み F5 allowlist と source-blob 検査は一切変わっていない。T-064 は legacy 据え置きの裁定であって、将来 g1 を永久に生成不能にする裁定ではない。

2. **4 pointer は過不足ないか:** S-1 JSON 2 本の内容差分としては過不足ない。repository transition としては不足しており、`FROZEN_MANIFEST` の S-1 2 hash、transition receipt、oracle/ratified fixture が追加で必要。将来 g1 には別途 `/known_axes_freeze/sha256` の許可が必要になる。legacy holdout の同 pointer は今 wave では変えない。

3. **新たに到達する下流検査は通るか:** S-1 verifier 内部は、observer 以外を変えない条件で静的には通る。63 source、pin、現行 generator hash は整合している。一方、repository 全体では `test_frozen_artifacts`、oracle manifest、ratified g1 が新たに落ちる。したがって「S-1 2 本が通る」から wave 全体の PASS は導けない。

4. **第三者が独立検証できるか:** 現時点なら `d06a3c3` と post-transition tree を持つレビュー者が raw diff を検証できる。しかし artifact・checker・manifest を同時更新するだけでは、後から独立に内容不変を証明できない。old/new SHA と許可差分を持つ receipt を別 reviewer が確認し、その receipt hash を manifest に pin する必要がある。

5. **40 桁形式以外の保証喪失は受容可能か:** 現計画のままでは不可。CC 選択内容を変える攻撃は構成できなかったが、存在しない/non-ancestor SHA を calibration provenance として受理する事故は構成できる。`unverified` 状態を report/calibration/oracle へ構造化伝播することを条件に、参考 metadata としてなら受容可能。

## provisional 裁定

| 裁定 | 判定 | 根拠 |
|---|---|---|
| P1′ | 条件付き採用 | semantic 対象は ancestry 3 サイトで正しい。helper/import/reporting 面は追加で必要 |
| P2′ | 否認 | 4 pointer だけでは v2 g1、manifest、receipt が閉じない |
| P3′ | 条件付き採用 | T-063 を主成果物にするのは正しいが、raw-byte receipt と consumer closure が必要 |
| P4 | 否認 | logging-only では値・状態が report/calibration/oracle に残らない |
| P5 | 条件付き採用 | T-066/T-067 は必要。oracle manifest/ratified fixture まで閉包を広げること |
| P6′ | 条件付き採用 | real S-1 positive integration は必要。xdist group、submodule skip、負例を同時に直すこと |
| P7 | 条件付き採用 | 最終再構成 message 固定は正しい。未 init submodule guard が必要 |
| P8′ | 条件付き採用 | S-1 内では transition 後に下流が開く。全体の検出力は head anomaly 喪失と consumer failure のため上がらない |
| P9 | 採用 | 674–680 だけなら exact 枝は不変 |
| P10 | 否認 | S-1 JSON 内は 4 点だが repository transition としては不足 |
| P11 | 否認 | V1 trust root・protocol golden・legacy holdout は不変でよいが、transition table 不変は成立しない |
| P12 | 否認 | T-064 は legacy 据え置きと「当面」非復旧の裁定。将来 g1 の構造的不能までは承認していない |
| P13 | 条件付き採用 | checker pin の恒久再設計は後送可。ただし今回の immutable receipt は後送不可 |

# 最終裁定: NO-GO

ユーザー裁定へ次の 3 点を差し戻す必要がある。

1. v1→g1 allowlist に **`/known_axes_freeze/sha256` だけ**を追加することを承認するか。
2. 一回限りの transition receipt、新 S-1 hash、receipt hash の `FROZEN_MANIFEST` 再 pin を承認し、所有者を割り当てるか。
3. `frozen_at_head` を未検証 metadata と明記し、その observation を report/calibration/oracle へ構造化伝播するか。それとも consumer 単位では fail-closed を残すか。

pytest は制約どおり実行していない。SHA、63 source record、呼出し経路、transition/consumer 閉包のみ read-only で照合した。
---

## 段 3b: 敵対相談 — 整合・実効性レンズ (codex、逐語)

結論は **NO-GO** です。

S-1 の canonical JSON に限れば許容差分は4 pointerで過不足ありません。しかし repo 全体の transition としては、少なくとも次の2点が未裁定です。

1. `FROZEN_MANIFEST` と旧世代対応 receipt がなく、[T-063] の差分契約を第三者が再検証できない。
2. known-axes の hash 更新が、現行の v1→g1 transition と ratified freeze 検査を破壊する。

## 所見

### R-01 — blocker / real

- **file:line:** [test_frozen_artifacts.py:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:33)、[test_frozen_artifacts.py:61](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_frozen_artifacts.py:61)、[decisions.md:2747](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2747)
- **壊れ方:** 4 pointer を変更すると、known/measurement の bytes hash が変わり、`test_frozen_artifacts_match_manifest` が必ず赤になる。単に manifest の2 hashを置換すると、旧成果物との対応を示す不変資料が消え、「4 pointer 以外は同一」を後から確認できない。JSONを parse して pointer 外を比較するだけでは、空白・key順・改行の変化も見逃す。
- **推奨対処:** 旧/new artifact hash、基準 commitまたはblob、許容4 pointer、raw bytesをpointer値だけmaskした同一性検査結果を持つ一回限りの transition receipt を作る。新しいS-1 hash 2件と receipt hash を `FROZEN_MANIFEST` に pinし、shape testも更新する。
- **scope:** **内**。[T-063] が本waveの主成果物なら不可欠。

### R-02 — blocker / real

- **file:line:** [s8b_ratified_freeze.py:110](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:110)、[s8b_ratified_freeze.py:934](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_ratified_freeze.py:934)、[test_s8b_ratified_freeze.py:428](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:428)、[test_s8b_ratified_freeze.py:572](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s8b_ratified_freeze.py:572)
- **壊れ方:** v1 holdout は known hash `354f4b…` を保持したまま、`_TRANSITION_V1_TO_G1` は `/known_axes_freeze/sha256` の変更を許可しない。一方、ratified verifier は `frozen_at_head` の実blobと記録hashを比較する。S-1 transition後の通常のsource headには新known bytesがあるため、v1値を継承したg1は `source-blob-mismatch` になる。既存happy-path fixtureも「現行known bytesをcommitへコピーし、v1文書を継承」しているので同じ理由で破損する。
- **推奨対処:** 次のいずれかをユーザー裁定する。
  1. 推奨: v1→g1だけ `/known_axes_freeze/sha256` を許容し、transition/golden/testsを更新する。
  2. tableを維持するなら、旧known bytesを持つ歴史的source headからg1を導入する手順を仕様化し、production相当テストを置く。
  3. 将来のv2/oracle復旧が引き続きblockedであると明示的に受容する。
- **scope:** 裁定は**内**。恒久実装を別waveへ送る選択は可能だが、現行テスト破損と将来blockは本waveで記録・処理が必要。

### R-03 — major / real

- **file:line:** [s8b_holdout_freeze.py:709](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:709)、[s8b_oracle_driver.py:216](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:216)、[s8b_oracle_driver.py:249](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:249)、[s8b_oracle_driver.py:263](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_oracle_driver.py:263)
- **壊れ方:** transition後に「S-1 freezeが直った」とだけ記録すると、oracleも使用可能になったと誤読される。実際にはknown refusalが消えるだけで、holdoutはdesign mismatchでhead検査にすら到達せず、floor/budgetもnullのまま。
- **推奨対処:** D72、worklog、phase doc、テストで「現行known/measurement verifierのみ復旧」「公式oracle非復旧」「canonical holdoutのancestry observerは未到達」を明記する。
- **scope:** **内**。

格下げ・4 pointer transition完了後の公式oracle拒否集合は、順序込みで次の3件だけです。

```text
holdout-freeze-verify: FreezeError: design_source sha256 不一致: recorded=1829af7fec4140fedaceae7c35ed5349e6d478e9d688de77a70f3be845a4a27d actual=5fbdd7ef2028ebbdd1187fb601c427d6b3b1250b4f86611f3ddfbd7f9be23cae
floor-null: freeze.floor が null
budget-null: freeze.budget が null
```

holdoutのknown/generator hashも陳腐化しますが、design検査が先にraiseするため、公式拒否集合へ別項目としては現れません。measurement verifierはoracleから呼ばれません。

### R-04 — major / real

- **file:line:** [s8b_holdout_freeze.py:665](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:665)、[s8b_holdout_freeze.py:709](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s8b_holdout_freeze.py:709)、[s1_verify_extime_calibration.py:193](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_verify_extime_calibration.py:193)
- **壊れ方:** P4の「値とancestry状態を記録・報告」は、verify内部のloggerだけでは満たせない。canonical holdoutはsource検査で先に落ち、observerが実行されない。また、プランの共通eventでexact枝にも `reference_only: true` を付けると、実際にはfail-closedであるexact一致まで参考情報と誤診させる。
- **推奨対処:** advisory観測を構造化した診断APIまたは明示的CLI出力にする。ancestryは `trusted=false`、exactは `reference_only=false` と分ける。canonical holdoutの状態も報告対象なら、通常verifyとは独立した診断経路を用意する。
- **scope:** **内**。単なるlogger追加だけではP4未達。

### R-05 — major / real

- **file:line:** [conftest.py:44](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:44)、[conftest.py:71](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:71)、[conftest.py:91](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/conftest.py:91)、[test_real_repo_serialization.py:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_real_repo_serialization.py:28)
- **壊れ方:** 新しいmeasurement canonical testは実repoとccbenchを読むが、現在measurement testsはreal-repo serial groupから明示的に除外されている。xdist下でrepo/submoduleを操作する別テストと競合し、source hashやgit結果が非決定的に赤くなる。
- **推奨対処:** 新設するknown/measurement canonical test nodeを `REAL_REPO_SERIAL_NODES` と独立goldenの双方へ追加する。
- **scope:** **内**。

### R-06 — major / real

- **file:line:** [s1_known_axes_freeze.py:724](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:724)、[s1_measurement_freeze.py:394](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:394)、[test_s1_known_axes_freeze.py:66](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:66)
- **壊れ方:** observerを旧raiseへ戻すようなS-1コード変異は、artifact pinも同時更新しない限りself-hashで先に死ぬ。したがってcanonical integration testだけでは「ancestry failureが本当に非致命か」を単一理由でkillできない。またcanonicalのbad objectを固定期待すると、将来そのobjectがfetchされた際にテスト意味が変わる。
- **推奨対処:** `_run_git`結果を決定的に注入するobserver単体テストを置き、`missing object`、`non-ancestor`、`ancestor`を別々に検査する。canonical positive testではPASSだけを検査し、現在のobject欠落種別へ固定しない。
- **scope:** **内**。

### R-07 — major / real

- **file:line:** [report.json:2](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/reports/s1_direct_comparison/report.json:2)、[s1_report.py:750](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_report.py:750)、[s_prime_final_report.md:68](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/reports/s_prime_final_report.md:68)
- **壊れ方:** 公開済みdirect-comparison reportはmeasurement artifact hash `5c719c…` に束縛されており、現行artifactは既に `203de36…`、本transition後はさらに別hashになる。新canonicalがverify可能になっても、過去reportを新checkerで再検証したことにはならない。
- **推奨対処:** 文書上の閉鎖範囲を「現行S-1 canonicalのロード可能化」に限定する。過去report・measurement provenanceは修復済みと書かない。再束縛・再計測は別裁定とする。
- **scope:** 境界記録は**内**。report再発行は**外**。

### R-08 — major / real

- **file:line:** [decisions.md:2757](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2757)、[s1_known_axes_freeze.py:632](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:632)、[s1_measurement_freeze.py:261](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:261)、[worklog.md:1012](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:1012)、[2026-07-21-s1-freeze-downgrade.md:1](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-21-s1-freeze-downgrade.md:1)
- **壊れ方:** generatorは今後も生成時HEADを書き込むため、wave branchで生成後rebaseすれば再びdanglingになる。格下げで拒否は消えるが、fieldは継続して無意味なprovenanceを表示する。T-005/T-063/T-068を閉じ、P13をinsightだけに送ると恒久対応の追跡主体が消える。加えてactive handoff冒頭とworklogには「再発行なし／bytes不変」の旧前提が残る。
- **推奨対処:** 少なくとも次の2件へ安定task IDを付ける。
  - freeze生成後rebaseと`frozen_at_head`意味論の解消またはfield廃止。
  - generatorとcheckerの同居・self-pin設計の分離判断。
  
  worklogには過去記録を改変せずerratumを追記し、phase doc、handoff、`output/README`、failuresも更新する。
- **scope:** 台帳化と訂正は**内**。恒久実装は**外**。

### R-09 — minor / refuted

- **file:line:** [known_axes_freeze.json:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/known_axes_freeze.json:5)、[measurement_freeze.json:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/measurement_freeze.json:5)、[measurement_freeze.json:1292](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/output/s1-freeze/measurement_freeze.json:1292)
- **壊れ方:** 「S-1 JSON内に4 pointer以外も機械的に変わるのでは」という疑いは、編集面を2 verifierとancestry処理に限定する限り成立しない。knownは自身のgenerator hashのみ、measurementは自身の二重pinとknown JSON hashのみが変わる。
- **推奨対処:** 「artifact semantic差分は4 pointer」「repo transitionの変更面はそれ以上」と明確に分けて記録する。
- **scope:** **内**。

### R-10 — minor / refuted

- **file:line:** [test_s1_known_axes_freeze.py:66](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_s1_known_axes_freeze.py:66)、[s1_known_axes_freeze.py:759](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_known_axes_freeze.py:759)、[s1_measurement_freeze.py:430](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/campaign/s1_measurement_freeze.py:430)
- **壊れ方:** P7のtamper testが依然過剰決定になる懸念は、transition完了後にはrefutedできる。`sp_dd → xp_dd` はschema/source/pairing/pinを通り、最後の機械再構成だけで落ちる。measurementの`what`改竄も最終document比較へ到達する。
- **推奨対処:** 予定どおり完全一致の`match=`を入れる。ただしR-06のobserver単体テストとは別物として扱う。
- **scope:** **内**。

## 改訂 provisional 裁定

| 項目 | 裁定 | 根拠 |
|---|---|---|
| P1′ | **採用** | semanticな格下げ対象は3 ancestry枝だけ。holdoutの形式・exact枝は維持。 |
| P2′ | **条件付き採用** | 4 pointer transitionは必要。ただしmanifest/receiptとratified依存を加えない限り実行不可。 |
| P3′ | **条件付き採用** | [T-063]を主成果物とするのは正しいが、JSON値比較だけでなくraw-byte連続性と不変receiptが必要。 |
| P4 | **条件付き採用** | 40桁形式維持は妥当。現行のlogger案ではcanonical holdoutの状態を報告できず、exact/advisoryも混同する。 |
| P5 | **条件付き採用** | T-066/T-067は直接関係する。ただしreal-repo serializationとexact refusal 3件を含めること。 |
| P6′ | **採用** | positiveな実S-1 canonical testは必要。「実成果物verifyが皆無」ではない、という訂正も正しい。 |
| P7 | **採用** | 最終再構成エラーへの完全一致は単一理由を保証できる。 |
| P8′ | **条件付き採用** | transition後にS-1下流は開く。ただしholdout、oracle、ratified g1、過去reportには波及しない。 |
| P9 | **採用** | ancestry枝だけ参考化し、exact枝をfail-closedで維持する。 |
| P10 | **条件付き採用** | S-1 JSONのsemantic差分として4点はexact。repo全体のtransition変更面はmanifest/receipt/tests等を含む。 |
| P11 | **否認** | trust root・holdout本体は維持可能だが、transition tableを絶対不変とすると通常のv1→g1経路と既存テストが破損する。 |
| P12 | **条件付き採用** | legacy oracleが拒否継続する範囲では受容可能。将来ratified g1まで受容済みとは読めない。 |
| P13 | **条件付き採用** | checker/self-pin再設計の実装はscope外でよいが、安定task IDによる台帳化は本wave内。rebase原因も別件として残す。 |

## 追加設問への回答

1. **このtransitionを行ってよいか**

   現案のままは不可。前回D71以降に変わったのは、T-068でancestryを非致命化する裁定が得られ、self-hashによりT-063経路が実際に発火した点です。変わっていないのは、凍結成果物の独立pinとv1→g1 transitionの制約です。R-01/R-02を裁定後なら実行可能です。

2. **4 pointerは過不足ないか**

   S-1 JSON内では過不足ありません。他のJSON pointerを変える必要はありません。ただしrepo変更面にはmanifestの2 hash、receipt、manifest shape、real-repo serial groupとgolden、ratified testまたはtransition tableが加わります。holdout JSONのknown hashを黙って変えてはなりません。

3. **新たに到達する下流検査は通るか**

   静的照合上、transition後のknownは63 source hash、pairing、ccbench pin、機械再構成を通る。measurementもimplementation hashes、known検証、schedule hash、cells/full-document再構成を通る。measurementの再構成中にknown verifierがもう一度実行される点も含みます。canonical holdoutはdesign mismatchでhead以前に止まり、ratified g1はR-02のままでは通りません。

4. **第三者が内容不変を検証できるか**

   現案では、基準commitのGit objectを保持する第三者だけが独自diffできます。新artifactと更新後manifestだけでは旧世代との連続性は証明できません。固定したpredecessor blob/hashとraw-byte比較を含むreceiptをmanifestへpinすれば、完全historyを持つ第三者が再検証できます。ただし外部署名がない以上、最終的な真正性はレビュー済みcommitへの信頼に依存します。

5. **`frozen_at_head` の完全性喪失を受容できるか**

   ancestry modeでは、40桁形式以外の意味保証を完全に失います。artifact全体のbyte pinは値の改変を検出しても、そのcommitが正しい生成地点であることは保証しません。したがって `untrusted/reference-only historical note` と明示し、gate・provenance判断に一切使わない条件なら受容可能です。exact modeは従来どおり信頼検査なので、同じ診断ラベルを使ってはいけません。

## ユーザーへ差し戻すべき設問

1. v1→g1について、`/known_axes_freeze/sha256` をtransition許容集合へ加えるか、旧known bytesを持つ歴史的source head導入手順を採るか、それとも将来のv2/oracle復旧blockedを受容するか。
2. 旧/new hash・基準blob・4 pointer・raw-byte外部同一性を持つ一回限りのreceiptを作り、新S-1 2件とreceiptを`FROZEN_MANIFEST`へ再pinしてよいか。
3. 本waveの閉鎖範囲を「現行S-1 canonical verifierの利用可能化」に限定し、過去report、holdout、公式oracle、ratified g1は未復旧と明記してよいか。

以上が決まるまでは **NO-GO** です。pytestは制約どおり実行していません。