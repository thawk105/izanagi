### 1. P1 の読み替え

判定: **real**

根拠: 親の支持材料は `docs/decisions.md:5991` の「6 driver」と `:5998` の「namespace は runtime の選択」だが、反証材料は強い。[T-318] は `artifact_role={official,exploration,qualification,dry}` を「正式主張の境界」としている（`docs/archive/worklog-phase3-0802-113-116.md:937`）。[T-337] も `artifact_role=qualification` と明記する（`docs/archive/worklog-phase3-0802-117-121.md:1367`）。これは campaign namespace だけへの同値変換ではない。

成果物影響: RF の qualification 軸を campaign path 軸へ置換したまま land すると、T-337 の裁定対象を未実装のまま実装済みと記録する。

推奨: **裁定へ**。反証が勝つため、本 wave は実装せず裁定パッケージへ返すべき。

### 2. D162 決定 (11) の解除権威

判定: **refuted**（D282 schema pin 単独を解除権威とする主張）

根拠: schema 実体には `declared_use_class` と 4 値が確かにある（`receipt-schema-v1.json:1225`, `:1248`）。record-items も利用意図であり qualification は合格宣言でないと定義する（`record-items-v2.md:77`, `:145`）。しかし D162 は「名前はユーザー再裁定へ返す」「名前が決まるまで新 producer を land しない」と明記する（`docs/decisions.md:8057`, `:8061`）。D282 の supersede 対象は D262/D263 で、D162 (11) ではない（`docs/decisions.md:12884`, `:12888`）。解除根拠になり得るのは、後続のユーザー裁定 T-479 が「新 D で名前を確定」と明記した部分だけ（`docs/archive/worklog-phase3-0805-199.md:3`, `:7`）。

成果物影響: T-479 を引用せず D282 だけで解除すると、D162 の land 禁止を親が自分で解除した記録になる。

推奨: **採用**（新 D に T-479 の委任を明記）。D282 単独の解除根拠は不採用。

### 3. D500 / D264 / D147 / D163 との衝突

判定: **refuted**（campaign-only に厳密限定する限り直接抵触は未成立）

根拠: プランは RF の 9 層を変更しないと明記する（`s2-plan.md:64`, `:80`）。D500 が禁じるのは attempt registry、純粋な組立て、拒否 adapter、fixture leaf を RF producer として land する形である（`docs/decisions.md:20731`, `:20734`; D264 `:12187`; D147 `:7202`; D163 `:8084`）。今回の案は `run_campaign` の実効引数と既存 campaign caller の変更であり、`PreregBinding`、qsub receipt、RF registry は作らない。

成果物影響: RF producer 実装済みと宣伝すれば D500 違反だが、campaign namespace hardening とだけ記録すれば既存 RF 成果物は不変。

推奨: **採用**（ただし RF producer 実装ではないことを新 D と成果物へ明記）。

### 4. D75 の二義化

判定: **real**（「同一軸の 2 producer」とする説明が未完成）

根拠: `artifact_role` は実際に探索 oracle の文書種別であり、`manifest/observations/verdict` の閉表を持つ（`s8b_oracle_artifacts.py:31`, `:33`, `:289`; `s8b_oracle_exploration.py:25`, `:35`, `:61`）。したがって再利用しない T-479 の判断は正しい。一方 `declared_use_class` は schema 上は利用意図だが、plan ではそれから directory namespace を導出する（`s2-plan.md:23`, `:42`）。D123 は namespace を identity でない runtime selector と定義する（`docs/decisions.md:5998`）。利用意図、campaign path、RF classification の関係を正本として一つに束ねる条文がまだない。

成果物影響: 同じ field が admission 入力や namespace identity と誤読されると、D162 が禁じる producer 自己申告の昇格経路が残る。

推奨: **裁定へ**。少なくとも「利用意図を宣言し、namespace は非 identity の派生値」と明記する。

### 5. DW-G03

判定: **real**

根拠: DW-G03 は異なる producer/consumer で同型欠陥が独立 2 件再現した場合だけ族一般化を許す（`docs/dev-wave/core.md:69`, `:71`）。しかし現行の 5 p3 driver はすべて既に `campaign_namespace="exploration"` を明示している（`p3_kickoff.py:111`, `p3_s4_loop.py:958`, `p3_s4_red.py:168`, `p3_s4_loop_sort.py:328`, `p3_s4_loop_trigger_gating.py:640`）。「宣言なしで official に書いた」独立実例は共有 sink の既定値 `loop.py:132` 1 件しかない。さらに D123 の族は 5 ではなく 8c を含む 6 driver である（`docs/decisions.md:5991`）。

成果物影響: 5 module の meta-test を足しても、8c と未再現の誤配線を防いだ証拠にはならず、acceptance を広域変更するだけになる。

推奨: **裁定へ**。T-318/T-479 は DW-G03 waiver ではない。明示的な例外裁定がなければ違反。

### 6. DW-G04

判定: **real**

根拠: D162 の発火条件は 3 arm の事前登録、環境タグ・checkout・pin・attestation、実 consumer hook の三条件である（`docs/decisions.md:8049`）。既存 `892042.nqsv` は計測 ID として存在し条件 (i) だけ成立、`env_tag` と attestation が欠け、consumer hook も 0 件である（`output/insights/2026-08-16_t338-rf-validator-trigger-audit/trigger-audit.md:11`, `:30`, `:47`, `:59`）。親 brief はこの実体を gate として書いていない（`s1-brief.md:10`, `:52`）。

成果物影響: 発火しない機能を production gate として land しても、RF の受理集合や certified 選択は変わらず、保証だけが増える。

推奨: **裁定へ**。campaign-only と RF 条件付き機能を分離して brief を再起草する。

### 7. 実効性

判定: **real**

根拠: 具体的に防げるのは、新 caller が必須 `declared_use_class` を省略した場合に signature binding で止め、`campaign_id` と output directory 作成前に失敗させることだけである（plan `s2-plan.md:9`, `:38`; 現行 `loop.py:123`, `:179`）。一方、caller が誤って `official` を明示する事故は検出しない。D162 も caller の自己申告は意味 gate でないとする（`docs/decisions.md:8014`）。従って brief の「探索由来 campaign が official 受理集合へ入る経路を閉じる」という強い記述（`s1-brief.md:84`）は過大である。

成果物影響: 省略事故は防げるが、誤分類・悪意の `official` 宣言、既存 marker の blocklist 穴は防げず、受理集合の狭まりを保証しない。

推奨: **不採用**（現在の「防げる」主張）。producer identity 束縛か、主張の縮小が必要。

### 8. 親 brief / plan の数値

判定: **real**

根拠: HEAD は `38f173cb` で一致するが、再測定値は次のとおり。

- `output/campaigns`: 16 file、194 matching line、195 occurrence。brief の 194 は line 数なら一致する。
- `run_campaign(`: 禁止 fixture を除く raw scan は 199 line / 200 occurrenceで、brief・plan の 195 と不一致。意味的な loop target の AST inventory は production 15、test 30。
- `artifact_role`: production Python は 2 file、10 hit (`s8b_oracle_exploration.py` と `s8b_oracle_artifacts.py`)。brief の「production 3 file」は誤り。
- `output/exploration`: source file は 6 で一致。`declared_use_class` の production Python hit は 0 だが、schema/record-items の pin は存在する。
- D123 の driver 外延は 5 でなく 6。plan の実装対象 5 は 8c を黙って落としている。

成果物影響: 数値を直さないまま段 4 裁定を行うと、scope、網羅性、DW-G03 判定を誤る。

推奨: **不採用**。数値を訂正し、8c の扱いを明示する。

## 総括

- P1 は T-337 の qualification 軸を campaign namespace 軸へ置き換える非同値の読み替えで、real。
- D282 は field の存在を証明するが、解除権威は T-479 の委任であり、schema 単独ではない。
- campaign-only に限定すれば D500 の直接違反はないが、RF producer 実装とは記録できない。
- `artifact_role` の再利用は D75 違反で、`declared_use_class` の軸対応は条文化不足。
- 独立 2 例はなく、8c も未処理なので DW-G03 は real。
- `892042` は D162 の発火条件 (ii)(iii) を満たさず、DW-G04 も real。
- pytest は未実行。静的検査と成果物読取のみで、緑は主張していない。