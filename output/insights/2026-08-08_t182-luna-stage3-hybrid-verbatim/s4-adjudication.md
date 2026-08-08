# 段 4 裁定 — dev-wave-t182-luna-stage3

## ユーザー再裁定 (2026-08-08、段 3 の所見を受けて)

段 3 敵対相談は **混成** とする。レンズ 1 本を `gpt-5.6-sol`、1 本を `gpt-5.6-luna`。
全 luna 化は採らない。段 2 / 段 5 / 段 6 は `gpt-5.6-sol` のまま。

これにより sol の検出集合は 1 件も失われないため、レンズ B の規律 2 論点 (B1) と
D207 先例論点 (B2) は**発火しない構成**になった。

## 親の erratum (段 1 brief の訂正)

brief と段 3 レンズ B への入力で「luna は sol が出さなかった所見を 2 件出した」と書いたのは**誤り**。
一次資料 `output/insights/2026-07-29_t182-model-routing-shadow-pilot.md` の
「shadow-only の所見 2 件」は **luna 1 件 + mini 1 件**であり、さらに luna のその 1 件は
**別の sol run (レンズ A の所見 9) が独立に到達**している。
したがって sol 2 本構成に対する luna の純増所見は **0 件**である。この訂正は worklog に残す。

## 所見の裁定

### レンズ B (正しさ境界)

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| B1 | 段 3 は正しさゲート、全 luna 化は規律 2 違反 | **real** | 混成採用により発火せず。論証は decisions に記録 |
| B2 | D207 の対象外を抜け道にしている | **real** | 混成で検出力低下なし。decisions に D207 との関係と「T-184/T-189 を supersede しない」を明記 |
| B3 | 91% は見落とし確率でなく P2 は導けない | **real** | ユーザー再裁定で混成へ。erratum を上記のとおり記録 |
| B4 | pin が文書だけを守り実起動を縛らない | **real** | 設計変更。`DW-O01` 雛形から slug を除去し `<model>` にする。slug の**不在**を pin する |
| B5 | F56 により served model を attest できない | **real** | worklog に `requested_model` / `served_model=unknown` を明記。runtime attest は [T-189] 所有のまま |
| B6 | 記録が条件付き裁定を洗浄する | **real** | 列挙項目を worklog / decisions に書く |
| B7 | rollback が不完全 | **real** | 射程を policy-only と明示し、発火条件と supersede 方式を decisions に書く |
| B8 | DW-G05 の影響否定が無効 | **real** | brief の成果物影響を書き直す (下記) |

### レンズ A (整合・実効性)

| # | 所見 | 裁定 | 処置 |
|---|---|---|---|
| A1 | 案 A は実行時 model の precedence を一意にしない | **real** | **案 A を破棄**。単一権威方式へ (下記) |
| A2 | decoy 1 つで drift が通る | **real** | 期待値照合をやめ、**slug の不在**を照合する設計にした。decoy を置く場所自体が違反になる |
| A3 | M3〜M5 が単一理由変異として不成立 | **real** | 変異を公開経路 (`_build_min_repo()`) 経由で登録し直した (下記) |
| A4 | `DW-O01` 見出し変更で意味索引を失う | **real** | 見出しは**変更しない** (案 A 破棄により自動解消) |
| A5 | checker は visible でなく raw bytes を数える | **real** | 親の計測方法の訂正。数値自体は一致 (LF・末尾改行ありのため raw=visible) |
| A6 | 棚卸しが SKILL.md と本 wave の実 model を落としている | **real** | `.agents/skills/dev-wave/SKILL.md` を consumer に追加 (model 無記載を確認済み、変更不要)。本 wave の段 2/3 が sol で走った事実を worklog に明記 |

refuted は 0 件。

## プラン v2 — 単一権威方式

model の権威を **1 か所だけ**にする。`.claude/commands/dev-wave.md` は Claude 経路が第一に読み、
Codex 経路も `SKILL.md` 手順 3 で全文読むため、両経路が到達する。

1. `.claude/commands/dev-wave.md` の「凍結境界」へ段別 model 表を 1 行追加する (**+169 bytes**)
2. `docs/dev-wave/workers.md` の `DW-S02` / `DW-S03` から model slug を除去する (**−32 bytes**)
3. `docs/dev-wave/operations.md` の `DW-O01` 雛形の `-m gpt-5.6-sol` を `-m <model>` にする
   (**−4 bytes**)。**見出しは変更しない**
4. `tools/check_docs.py` に pin を追加する
   - dispatcher の段別 model 行を exact literal で pin する
   - `DW-S02` / `DW-S03` / `DW-O01` の可視本文に `gpt-5.6-*` slug が **1 つも現れない**ことを pin する
5. test を追加する (公開経路 `_build_min_repo()` 経由の negative を含む)

### byte 会計 (親の実測、raw bytes)

| file | 現行 | 変更後 | cap |
|---|---:|---:|---|
| `docs/dev-wave/` 4 file 合計 | 25,196 | **25,160** | 25,200 |
| `.claude/commands/dev-wave.md` | 9,035 | **9,204** | 9,500 |

reference 予算は逼迫を**解消する側**へ動く (残り 4 → 40)。安全義務の prose は 1 字も削らない。

## 成果物影響 (DW-G05、B8 を受けて書き直し)

段 3 の検出力が落ちると、gate 欠陥 (未存在 proof を accepted とする fallback 等) を
plan v2 が scope 外に落とし、その実装が land する。結果として campaign で
anomaly を持つ variant が `reject`/`tie` から `selected` へ移り、材料レポートが存在しない proof を
参照し、試行台帳が誤って accepted を記録しうる。
**本 wave の混成構成は sol レンズを 1 本残すため、この経路の検出力は現行から減らない。**
pin を入れない場合の影響は、model slug が黙って drift し、worklog の model 帰属が実起動と乖離すること。

## 変異事前登録 (DW-M01)

すべて公開経路 (`_build_min_repo()` + `_assert_findings`) で単一理由に帰属させる。

| ID | 変異位置 | 入力 | 唯一の期待赤 |
|---|---|---|---|
| M1 | `_check_dev_wave_model_pins` の呼び出しを削除 | `DW-S03` に `gpt-5.6-sol` を混ぜた min repo | workers slug 不在違反 1 件 |
| M2 | pin table から workers 側の規則を削除 | 同上 | 同上 |
| M3 | pin table から `DW-O01` 側の規則を削除 | `DW-O01` 雛形に slug を戻した min repo | operations slug 不在違反 1 件 |
| M4 | dispatcher literal の pin を削除 | 段別 model 行を改変した min repo | literal 不一致 1 件 |
| M5 | slug 検出正規表現を backtick 付きだけに限定 | `DW-S03` に bare `-m gpt-5.6-sol` を置いた min repo | workers slug 不在違反 1 件 (A2 の decoy) |

正例 (過剰拒否の検出): 現行の実 docs 一式が `check_docs` で緑のままであること。

## scope 外 — 裁定パッケージへ返す

1. **実起動の runtime binding。** `-m` の実引数を段別 model 表と機械照合する層 (hook / launcher)。
   Claude 経路の hook は Codex 経路に未配線であり、両経路を覆う設計が要る
2. **served model の attest (F56)。** receipt は要求 slug の echo にすぎない。所有は [T-189]
3. **EOL 正規化の欠如。** 4 reference を CRLF 化すると byte gate が別環境で壊れる (A5)
4. **`orchestrator/codex_roles/` の model allowlist に luna が無い。** named role で luna を
   使うなら別 wave (spec.py の `{gpt-5.6-sol, gpt-5.6-terra}`)

## 実装単位

1 単位。docs 3 file = 親 (docs-only 本文編集)。`tools/check_docs.py` + test = Codex `role=author` 実装子。
