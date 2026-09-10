# [T-182] 段 4 裁定 — 実装しない (4→7→8→9)

## 裁定の要旨

**プラン v1 の `tools/codex_model_shadow.py` は実装しない。** 段 5・6 を飛ばし、
本 wave は「段 3 で実走した shadow pilot の証拠 + 限界 + 裁定パッケージ」を成果物とする。
production 既定 (`DW-O01` / `DW-S03` / `DW-S06-A` の model・reasoning) は変更しない。

根拠は独立 3 レンズ (段 2 planner、段 3 レンズ A=実験妥当性、段 3 レンズ B=gate 実効性) が
**すべて NO-GO** を返し、うち 2 本が明示的に「実装せず裁定パッケージへ返す」を推奨したこと。
親はこれを real と裁定する。

さらに親自身の読み直しで、`docs/phase3.md` [T-182] の要求は
「同一凍結入力で比較し、finding coverage・誤検出・token/turn/wall-clock と model identity
receipt を残す」ことであり、**ツールの新設を求めていない**。ツールは親 brief が持ち込んだ
scope であり、3 レンズはそれを正しく攻撃した。要求された証拠は段 3 の実走で既に得ている。

## 所見の裁定

### レンズ B (gate 実効性、authoritative) — 11 件すべて real

| ID | 所見 | 裁定 |
|---|---|---|
| S1 | receipt の model は request echo であり served identity の attest ではない | **real / scope 内 / 採用**。ツールでは閉じられない (attest 経路が存在しない) → 証拠として記録 |
| S2 | 空白正規化 hash と「最初の user message だけ」では同一凍結入力を束縛できない | **real / 採用** → 限界として記録 |
| S3 | process rc・wall-clock・同時実行数は manifest 自己申告で replay 可能 | **real / scope 外** → T-180 の launcher receipt が前提 |
| S4 | arm 集合が未固定で不正 reasoning `ultra` を受理する | **real / 採用** → 証拠として記録 |
| S5 | 空白 500 bytes と見出しだけで成果物 gate を通せる | **real / scope 外** → `check_codex_output.py` 所有の別課題 |
| S6 | ledger parser は集計用の fail-soft parser であり validation parser ではない | **real / scope 外** → T-180 所有 |
| S7 | 閉集合採点は新規 real finding を出した強い arm を run 無効にする | **real / 採用** → 本 wave の採点法の限界として明記 |
| S8 | rc 分類・identifier・receipt schema が一意でない | **real / 実装しないため moot** |
| S9 | テスト案は複数理由の赤と等価変異で欠陥を殺したように見せる | **real / 実装しないため moot** |
| S10 | 新 tool はどの受入経路にも配線されず gate ではない | **real / 採用** → 実装しない裁定の主要根拠 |
| S11 | T-180 と並行する private import は merge 順序が gate になっていない | **real / 採用** → 実装しない裁定の根拠 |

### レンズ A (実験妥当性) — 9 件すべて real

| ID | 所見 | 裁定 |
|---|---|---|
| A1 | 「luna/terra は sol より軽くない」は一般化不能 | **real / 採用**。段 3 の実タスクで親自身が反証した (下記) |
| A2 | 実行順・cache・並行負荷が arm と完全に交絡 | **real / 採用** → 交絡タグつきで記録 |
| A3 | P2 は model 効果を識別せず luna は control ではない | **real / 採用** |
| A4 | sol 由来 oracle は coverage を循環定義し shadow-only 真欠陥を消す | **real / 採用** → 採点の限界として明記。実際に shadow-only 所見が 2 件出た |
| A5 | 段 3・段 6 は低リスクではなく追加 shadow でも親を汚染する | **real / 採用** → 段 6 の shadow は行わない |
| A6 | 本 wave 自己採点の循環が現行配線で未遮断 | **real / 採用** |
| A7 | phase の「turn」を `model_calls` で代用している | **real / 採用** → T-179 の是正語彙どおり `model_calls` と明記して報告 |
| A8 | 後日同値は再現せず凍結契約も不足 | **real / 採用** |
| A9 | 推奨 scope は (c) 実装せず裁定パッケージ | **real / 採用** → 本裁定 |

### 親 brief の provisional 裁定の帰結

- **(P1) 却下**: 段 6 の shadow は行わない。pilot は段 3 レンズ B の 1 箇所だけ (レンズ A5・
  planner・luna L11 が独立に同じ指摘)。
- **(P2) 修正**: mini は model と reasoning の 2 軸同時変更、luna は「軽量」ではなく
  requested-slug comparator。どちらも単独では model 効果の因果証拠にならない。
- **(P3)(P4)(P5)(P6)(P7) 維持**。
- **(P6) は実測で強化された**: 不正値 `reasoning=ultra` が sol/luna/terra で rc=0 のまま通り
  receipt に残る。mini だけが 400 で落ちる。

## 変異事前登録 (DW-M01)

**対象外。** 実装差分がないため変異 matrix と受入全走 (実装面) は本 wave の射程外である。
段 4 で用意していた 10 変異候補は plan v1 の tool に対するものであり、実装しない裁定により破棄する。

## 本 wave が実際に生産した pilot 証拠

段 3 のレンズ B を **同一 prompt file** (`s3-consult-b-prompt.txt`, 5,498 bytes) で 3 arm に投入した。
`codex_worker_ledger.py` が 3 arm すべてに `prompt_hash=02f8f55058…` を記録しており、
同一凍結入力であることの機械証拠になっている (レンズ A の 1 箇所への縮小要求とも整合)。

| arm | model / reasoning | model_calls | output tok | CLI reported | wall | 成果物 bytes |
|---|---|---|---|---|---|---|
| authoritative | `gpt-5.6-sol` / max | 32 | 43,785 | 245,864 | 1,199s | 23,881 |
| shadow 1 | `gpt-5.6-luna` / max | 14 | 41,520 | 168,124 (**−31.6%**) | 772s (**−35.6%**) | 15,898 |
| shadow 2 | `gpt-5.4-mini` / xhigh | 17 | 52,216 | 179,988 (**−26.8%**) | 1,667s (**+39.0%**) | 6,332 |

全 arm が `check_codex_output.py` rc=0、`.done` rc=0。session_id は insight へ凍結する。

### finding coverage と誤検出 (限界つき)

authoritative arm の 11 所見を基準集合とした被覆:

- **luna: 10/11 (91%)**。落としたのは S7 (閉集合採点の選択バイアス) のみ。
- **mini: 5/11 (45%)**。落としたのは S1・S2・S3・S5・S6・S7。うち S1 は `## 総括` の散文で
  言及したが所見として構造化しなかったため被覆に数えない。
- **誤検出 (親が refuted と裁定した所見): luna 0 件 / mini 0 件。**
- **shadow-only の所見が 2 件**: luna L11 (scope を段 3 B のみ + receipt qualification へ縮小せよ)
  は authoritative arm が出さなかったが、**独立した別 sol run (レンズ A9) が同じ結論に到達**しており
  real。mini M3 (schema が識別子を「ASCII identifier」と呼びながら例に hyphen を含む矛盾) も
  authoritative arm の S8 より具体的で real。

**この被覆率の限界 (A4/A6 の採用結果として明記する)**:
基準集合が authoritative arm 自身であるため循環しており、盲検でもない。label は shadow 実行の
**前**に事前登録していない (親の手順上の実欠陥)。したがってこの数値は
「sol の所見集合に対する再現率」であって品質の絶対尺度ではなく、
**T-184 の policy 採用根拠にしてはならない** (`eligible_for_t184_policy = false`)。

### 交絡 (A2 の採用結果)

3 arm は同時刻に起動し、起動時の同時 codex 実行数は 22、終了時は 10〜15。
並行 wave (T-126 / T-180 / T-181 / ai-provenance-forward-fix / dev-wave-skill) が同一 account で
稼働していた。**wall-clock は model 差の証拠として使えない。** token は cache 比率が
arm 間で大きく異なるため (cached: sol 2,390,528 / luna 895,488 / mini 984,320)、
`cli_reported = input − cached_input + output` の差も単一 task の観測に留まる。

### 段 1 実測の自己反証 (A1 の採用結果)

段 1 の trivial probe (820 行のファイルを読んで 3 問に答える) では
sol 34,289 / luna 30,262 / terra 37,947 CLI reported token であり、親は
「luna も terra も sol より軽くない」と brief に書いた。段 3 の実レンズ課題では
luna が sol より **31.6% 少ない** token で完了しており、**この一般化は成立しない**。
親の brief の当該記述は本裁定で撤回する。

## ユーザーへ返す裁定パッケージ

1. **T-182 は「限定 shadow pilot の実走 + 証拠 + 限界」で完了とし、専用ツールは作らない。**
   異論があれば、どの受入経路に配線するかを先に決める必要がある (S10)。
2. **model identity の attest 経路が存在しない。** rollout に残るのは要求 slug であり、
   400 応答だけが実体名 (`gpt-5.4-mini-codex-1p-codexswic-ev3`) を露出する。
   これを閉じるには codex CLI 側の変更か、別の attest 源が要る。裁定を仰ぐ。
3. **不正 reasoning 値が silent に通る** (`ultra` が sol/luna/terra で rc=0)。
   `DW-O01` の「効いた値」は現状どこでも機械検査されていない。T-181 / T-184 と
   どちらが所有するかの裁定を仰ぐ。
4. **有効な model routing 実験の設計** (レンズ A が提示): 独立 oracle、held-out 複数 task、
   block randomization、cache 条件の分離、価格 version、盲検裁定、事前非劣性 margin。
   これは T-180 / T-181 の receipt 基盤 land 後の別 wave とすべきである。
5. **暫定的に言えること**: 第二レンズ 1 箇所・n=1・非盲検という射程の中でなら、
   `gpt-5.6-luna` @ max は sol の所見の 91% を誤検出 0 で再現し token を 31.6% 減らした。
   `gpt-5.4-mini` @ xhigh は 45% しか再現せず wall-clock は 39% 増えた。
   **これは仮説であって policy 根拠ではない。**
