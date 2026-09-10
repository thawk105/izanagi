# 段 4 裁定 — dev-wave-t657-stage0-fold

段 3 の 2 レンズはともに NO-GO。所見 13 件 (sol 7 / luna 6) を real / refuted と採否で裁定する。
**親 brief の (P2) と段 2 プランの失効 schema を撤回する。** 撤回の根拠は下記 R-01。

---

## 0. 裁定を変えた新事実 (両レンズが独立に指した一次資料)

`docs/freeze-permanent-design-s2.md` §S2-1.10 に、**既に exact 7 fields の失効 schema が存在する**。

```text
path: output/freeze-permanent/revocations/<bundle_digest>.json
exact 7 fields:
  schema_version = "freeze-bundle-revocation/v1"
  bundle_digest / approval_sha256 / revoked_by / revoked_at
  scope = "bundle-only" / reason
- bundle あたり 0 または 1 件
- target は一度 X された N>=1 bundle
- live tip の revocation 後は active bundle なし。fallback 禁止
- descendant generation は自動 revocation しない
- record の変更・削除・rename・再追加を拒否
```

同書は §1 の表で「freeze 族内部の **exact 仕様**」の正本と定められ、§10.1 が「下位の exact 正本は
**凍結済みの design 族**」と明記する。

**したがって R1 (a) の「`revocations/<bundle_digest>.json`・exact 7 key・束当たり 0/1 件・
UTC 秒 int」は、この下位 exact 正本の形をそのまま 1 層上へ写したものである。** 4 点すべてが
§S2-1.10 の逐語と一致する (path 形状・件数 7・0/1 件・時刻)。選択肢 (a) は新 schema の発明ではなく
**下位への conformance** であった。

親 brief (P2) と段 2 プランは §S2-1.10 を読まずに別の 7 key を組み立てた。これは
`FREEZE-AX-TOPOLOGY` (§12.4) と同型の**下位正本への不適合を新規に作る**行為であり、撤回する。

---

## 1. 所見の裁定

| ID | 判定 | 採否 | 根拠 |
|---|---|---|---|
| SOL-A-01 / MF-004 | **real** | 採用 (must-fix) | 束縛が key 名だけでは型・逐語・参照制約の緩和が緑で通る。制約 cell を含む**行全体**を pin する |
| SOL-A-02 | **real** | 採用 (blocker) | `_read_design` は raw text を返し fence を除外しない。canonical 表を fence 内へ移して可視部を緩める decoy が通る。**wave 前の実コードの形そのもの** |
| SOL-A-03 / LB-001 | **real (観察)・refuted (blocker)** | 却下 → 別解で採用 | 7 key が未裁定という観察は正しいが、結論が誤り。§0 のとおり 7 key は下位 exact 正本 §S2-1.10 から**導出可能**であり、親の裁量選択ではない。ユーザー裁定は不要 |
| SOL-A-04 | **real** | 採用 (blocker) | 世代不一致・R 削除後の受理集合再拡大・同 digest 再承認が未規定。**§S2-1.10 の 4 つの意味規則が全部これを閉じる** (削除・再追加の拒否を含む) |
| SOL-A-05 | **real** | 採用 (blocker) | 段 6 構造 predicate の parent が「既存 X」では fork を受理する。§7.2「上位 pointer」の解決義務が **live tip 一意解決・parent 連鎖・世代**を既に要求し、§5.1 が世代単調増加を確定済み。**S/B policy ではなく既決の構造条件**なので構造部分へ入れる |
| SOL-A-06 / LB-002 | **real (観察)・refuted (blocker)** | 採用 (文言のみ) | 「predicate を固定した」と「実 entrypoint で実行した」は別。ただし §10 は fixture と段の対応付けを `CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` (owner = `stage1-and-later`, `pending`) の仕事と明記済み。**段 0 は `incomplete` を主張し続けるので過剰主張は生じない。** docs に「固定 ≠ 実行」を明記し、fixture 追加はしない |
| SOL-A-07 | **real** | 採用 (nit) | brief の「path を持つのは 2 箇所だけ」は不正確。tracked な insight README にも exact path がある (pin ではない)。記録で訂正する。DW-O10 不成立の結論は不変 |
| LB-003 | **real** | 採用 (must-fix) | 冒頭 20 行「ユーザー裁定待ちが 3 件」と 9〜15 行「決まったこと」を段 2 プランが落としている。畳み込み後に自己矛盾する |
| MF-005 | **real** | 採用 (nit) | execution 層は変更不要。**その理由を記録に明記**し、fixture を足さないことと対にする |
| NIT-006 | **real** | 採用 (nit) | 定数名を `_UPPER_REVOCATION_SCHEMA` 系にして下位 `_REVOCATION_KEYS` との混同を断つ |
| LB-002 (fixture 義務) | refuted | 却下 | 上記 SOL-A-06 と同一。既存 gate が `pending` で段 0 を block しており、義務の回避ではない |

**ユーザー裁定が要ると判定した所見は 0 件。** 両レンズが「要る」とした LB-001 / SOL-A-03 /
LB-003 / MF-004 は、いずれも下位 exact 正本と本書 §7.2 / §5.1 から導出できる。

---

## 2. プラン v2 — 確定した内容

### 2.1 失効 record R (§7.5、S-B) — **撤回して差し替え**

`revocations/<bundle_digest>.json`、束当たり 0/1 件、top-level exact 7 key。
**下位 exact 正本 `docs/freeze-permanent-design-s2.md` §S2-1.10 と同型で、上位語彙へ写す。**

| key | 型・制約 |
|---|---|
| `schema_version` | 逐語 `calibration-freeze-authority-revocation/v1` |
| `bundle_digest` | 64 lower-hex。file 名の stem と一致し、§7.3 の再計算値と一致 |
| `approval_raw_sha256` | 64 lower-hex。対象束の A の raw bytes の sha256 および `approvals/<raw sha256>.json` の file 名 stem と一致 |
| `revoked_by` | NFC、trim 済み、1〜128 code point |
| `revoked_at` | exact int の UTC 秒。`bool` を int として受理しない |
| `scope` | 逐語 `bundle-only` |
| `reason` | 非空 string |

意味規則 (§S2-1.10 の 4 規則を上位語彙へ写す):

- 対象は**一度上位 X が成立した束**に限る。承認だけで発効していない束への失効 record を受理しない。
- live tip の束が失効した後、active な上位束は存在しない。**下位 authority へ fallback しない**
  (Q3 (ii) = `no-lower-fallback-fail-closed`)。
- **子孫世代を自動的に失効させない。**
- record の**変更・削除・rename・再追加を拒否する** (§11.1 `CFAB-11.1-01` と同型の履歴不変)。

**却下した案:** 段 2 プランの `authority_bundle_generation` + `revoked_active_pointer_raw_sha256` 案。
下位 exact 正本と非適合な新 schema を作り、`FREEZE-AX-TOPOLOGY` と同型の不適合を上位に新設する。
世代の扱いは「子孫世代を自動失効させない」規則が担うため、世代 field は不要。

### 2.2 段 6 構造 predicate (§10 段 6 行、S-C) — SOL-A-05 を反映して強化

- (i) X は `active/<raw sha256>.json` に置く top-level exact 5 key の record で、file 名の stem は
  X の raw bytes の sha256 と一致する。
- (ii) `parent_active_pointer_raw_sha256` は genesis のときだけ `null`、それ以外は**その時点の
  live tip X** の raw sha256 と一致する (祖先の非 tip X を parent にした列を拒否する)。
- (iii) `authority_bundle_generation` は A の同 field と一致し、非 genesis では parent X の値より
  真に大きい (§5.1 の世代単調増加)。
- (iv) `bundle_digest` は A の `bundle_digest` と一致し、§7.3 の再計算値と一致する。
- (v) `approval_raw_sha256` は A の raw bytes の sha256 と `approvals/<raw sha256>.json` の
  file 名 stem の双方に一致し、参照先 A は下位 family 検証器と §5.1 の topology 検査を通った
  承認済み A に限る。

陽性 control 1 件以上を受理し、各条件を 1 つだけ破る 5 個の陰性変異をそれぞれ対応する理由で拒否する。
**本節が固定するのは predicate であって実行ではない** — 実 entrypoint と fixture の対応付けは
`CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` (`pending`) の手番であり、段 0 は `incomplete` のまま。

policy 依存部分は `CFAB-STAGE6-POLICY-PREDICATE` (owner = `user`, status = `unresolved`) として残す。

### 2.3 検証器の drift 束縛 (S-B / S-C 共通)

1. **`_read_design` から fenced code block を除去する** (SOL-A-02)。除去後の text を全 extractor が
   使う。現行 5 経路 (§7.2/§11 row、§11.2 宣言 row、§8.1 裁定 ID、§8.1 selection 列、§10 段集合宣言)
   の anchor はいずれも fence 外にあることを実測済みなので、受理集合は縮小のみ。
2. **失効 schema は key 名でなく「key + 制約 cell」の順序付き tuple 全体を pin する** (SOL-A-01)。
3. **段 6 構造 predicate は (i)〜(v) の全文 + 陽性/陰性 control 文 + policy gate tuple を pin する。**
4. `required_gates` は 8 → 12 件。追加は `CFAB-R1-REVOCATION-RECORD` /
   `CFAB-R2-STAGE0-COMPLETION` / `CFAB-R3-STAGE6-PREDICATE` (いずれも owner = `user`, `resolved`) と
   `CFAB-STAGE6-POLICY-PREDICATE` (owner = `user`, `unresolved`)。
   `entries_sha256` = `26aa463b024e9f64e87401ca3dcebd508efe146ed28c166557a6a4447811b948`
   (**親が独立に再計算して子の申告と一致を確認済み**)。
5. 定数名は `_UPPER_REVOCATION_*` 系にする (NIT-006)。

### 2.4 docs 畳み込み (S-A) — LB-003 を反映

親が編集する箇所を exact に列挙する。

- 冒頭 9〜15 行「決まったこと」— R1 / R2 / R3 を追加。
- 冒頭 18〜20 行「決まっていないこと」— 「ユーザー裁定待ちが 3 件」を削り、他者手番 gate 2 件と
  先送り S / B と `CFAB-STAGE6-POLICY-PREDICATE` だけが残ると書く。
- §7.5 (行 449〜464) — 失効 record R の表と 4 意味規則へ置換。「固定 schema を land させては
  ならない」の逐語を削除し、下位 §S2-1.10 への conformance であることを明記。
- §7.5 namespace 列挙に `revocations/` を追加。file 名規則に失効の例外を追記。
- §10 段 6 行 (683) — 2.2 の構造部分 + policy 部分へ置換。
- §10.2 blockquote (721〜725) — R2 = (b) の帰結へ置換。
- §12.1 表 — R1 / R2 / R3 の 3 行を追加。
- §12.3 — 「残るユーザー裁定なし」へ置換し、S / B と policy gate が引き続き段 0 を block すると書く。

### 2.5 no-touch (不変条件、brief §3 のまま)

`ruling-profile.v1.json` / `cases/*.json` 10 件 / `_PROFILE_IDS` / `_SELECTION_ENUMS` /
`_EXPECTED_RULING_STATES` / `_EXPECTED_RAW_SHA256_BY_FIXTURE` / `_EXPECTED_FIXTURE_ENTRIES_SHA256` /
`_EXPECTED_ROW_IDS_SHA256` / manifest の `fixtures` と `row_coverage` /
`_applicable_unresolved_count` / execution 層 2 file / 他者手番 gate 2 件 /
`CFAB-STAGES1-4-AND6-8-FIXTURE-ASSIGNMENT` の `pending`。

段 0 の算出は `status=incomplete` / `pending=5` / `applicable_unresolved=2` /
`blocking_gates=3→4` のまま。

---

## 3. 成果物影響 (DW-G05、must-fix ごとに 1 行)

- **SOL-A-02 未修正:** 設計正本の可視部を緩めたまま drift gate が緑になり、S-B / S-C の
  「機械束縛済み」という proof が成立しない → 段 1 以降が偽の固定を前提に resolver を書く。
- **SOL-A-01 未修正:** `revoked_at` を int から string へ、`scope` を逐語から任意値へ緩めても
  検査が通り、失効 record の受理集合が独立 pin なしに動く。
- **SOL-A-04 未修正 (§S2-1.10 の意味規則を写さない):** 失効 record を削除すれば旧 X が再受理され、
  失効の不可逆性と `no-lower-fallback-fail-closed` が証明できない。
- **SOL-A-05 未修正:** 段 6 の構造 proof が fork (祖先 X を parent にした列) と世代偽装を受理し、
  発効 X の受理集合が §5.1 の単調増加を破る。
- **LB-003 未修正:** 同じ正本に「裁定待ち 3 件」と「残る裁定なし」が同居し、後続 wave の起票条件が
  再現不能になる。
- **R 差し替え (§0) 未実施:** 上位が下位 exact 正本と非適合な失効 schema を持ち、
  `FREEZE-AX-TOPOLOGY` と同型の不適合を新規に作る。

---

## 4. 変異の事前登録 (DW-M01)

段 6 の fix 後に走らせる。各変異は単一理由性を確認済み。

| ID | 変異 | 期待 | 単一理由性 |
|---|---|---|---|
| M1 | `_read_design` の fence 除去を外し raw text へ戻す (**wave 前の実コードの形**) | KILLED | fence decoy 負例だけが落とす。他層に fence を見る検査は無い |
| M2 | 失効 schema の束縛を「key 名の集合」へ退化させる (制約 cell を捨てる) | KILLED | 制約 cell 負例だけが落とす。key 集合は不変なので key 検査は発火しない |
| M3 | §7.5 の `scope` を逐語 `bundle-only` から「非空 string」へ **docs 側だけ**緩和 | KILLED | 行全体 pin だけが落とす。key 数 7 は不変 |
| M4 | §10 段 6 (ii) の「その時点の live tip X」を「既存 X」へ **docs 側だけ**緩和 | KILLED | 構造 predicate 全文 pin だけが落とす |
| M5 | manifest の `CFAB-STAGE6-POLICY-PREDICATE` を `unresolved`→`resolved` (count/hash 追随) | KILLED | `_EXPECTED_REQUIRED_GATES` の独立 pin だけが落とす。count/hash は追随済みで発火しない |
| M6 | `required_gates` から `CFAB-R1-REVOCATION-RECORD` を削除 (count/hash 追随) | KILLED | 同上 |
| M7 | 失効 schema extractor を常に空 tuple を返す形へ (**reject-all 正例検査**) | KILLED | 陽性テストだけが落とす。受理集合を縮小する wave の過剰拒否検出 (DW-M01) |

**先取り注意 (memory: 新設 gate は先取りされる後段検査を数える):** M1 は `_read_design` の共有
経路を変えるため、既存 5 extractor の node も同時に落ちうる。期待 node 集合は fix 後に
完全集合として再導出する (memory: 期待 node は fix 後に完全集合を再導出)。

---

## 5. 段 5 の分割 (確定)

1. 親が §2.4 の docs を編集し commit する (実装子は docs を触らない)。
2. **U1** = `orchestrator/tests/calibration_freeze_authority_contract.py` +
   `orchestrator/tests/fixtures/calibration_freeze_authority/manifest.v1.json`。
3. **U2** = `orchestrator/tests/test_calibration_freeze_authority_contract.py`。U1 完了後に逐次。

manifest を第 3 単位へ分けない (module pin と manifest literal が別所有になると中間状態で
必ず三者照合が破れる)。
