# [T-182] model routing の限定 shadow pilot — 実走結果と裁定パッケージ (2026-07-29)

逐語と receipt の凍結は `2026-07-29_t182-model-routing-shadow-pilot-verbatim/`。
親の裁定要約は `docs/worklog.md` 2026-07-29 (65)。**本 wave に実装差分はない。**

## 結論 (先に射程を書く)

第二レンズ 1 箇所・単一 task・n=1・非盲検・後付け採点という射程の中でのみ、次が言える。

- `gpt-5.6-luna` @ `reasoning=max` は、authoritative な `gpt-5.6-sol` @ `max` の所見 11 件のうち
  **10 件 (91%) を誤検出 0 で再現**し、CLI reported token を **31.6% 減**らした。
  さらに authoritative arm が出さなかった real な所見を 1 件出した。
- `gpt-5.4-mini` @ `reasoning=xhigh` は **5 件 (45%) しか再現せず**、
  wall-clock は **39% 増**えた。token は 26.8% 減。

**これは仮説であって policy 採用の根拠ではない** (`eligible_for_t184_policy = false`)。
理由は「採点の限界」節に書く。production 既定は本 wave で一切変更していない。

## 何を測ったか

段 3 の敵対相談レンズ B (gate 実効性レンズ) を、**同一の prompt file**
(`s3-consult-b-prompt.txt`, 5,498 bytes) で 3 arm へ投入した。sol arm は従来どおり
authoritative として走らせ、shadow 2 本は**置換ではなく追加**である。
`tools/codex_worker_ledger.py` が 3 arm すべてに同じ `prompt_hash=02f8f550583d…` を記録した。

| arm | model / reasoning | model_calls | input | cached input | output | CLI reported | wall | 成果物 bytes |
|---|---|---|---|---|---|---|---|---|
| authoritative | `gpt-5.6-sol` / max | 32 | 2,592,607 | 2,390,528 | 43,785 | 245,864 | 1,199s | 23,881 |
| shadow 1 | `gpt-5.6-luna` / max | 14 | 1,022,092 | 895,488 | 41,520 | 168,124 (−31.6%) | 772s (−35.6%) | 15,898 |
| shadow 2 | `gpt-5.4-mini` / xhigh | 17 | 1,112,092 | 984,320 | 52,216 | 179,988 (−26.8%) | 1,667s (+39.0%) | 6,332 |

`CLA reported` の定義は T-179 の正本に従う (`input − cached_input + output`)。
`turn` ではなく `model_calls` と呼ぶ (T-179 の是正語彙)。
全 arm が `tools/check_codex_output.py` rc=0、ラッパの `.done` rc=0。

## finding coverage と誤検出

authoritative arm の 11 所見を基準集合とした対応表。

| 基準 (sol) | luna | mini |
|---|---|---|
| S1 receipt は request echo で served identity の attest ではない | 所見7 | 総括で言及のみ (所見化せず → 非計上) |
| S2 空白正規化 hash と最初の user message だけでは同一入力を束縛できない | 所見3 | — |
| S3 process rc・wall・同時実行数が manifest 自己申告で replay 可能 | 所見4 | — |
| S4 arm 集合未固定 + 不正 reasoning `ultra` の受理 | 所見6 | 2 |
| S5 空白 500 bytes と見出しだけで成果物 gate を通せる | 所見5 | — |
| S6 ledger parser は fail-soft で validation parser ではない | 所見4 に包含 | — |
| S7 閉集合採点が新規 real finding を出した arm を run 無効にする | — | — |
| S8 rc 分類・identifier・receipt schema が一意でない | 所見2・10 | 3 (より具体的) |
| S9 テスト案が複数理由の赤と等価変異で欠陥を殺したように見せる | 所見8 | 5 |
| S10 新 tool がどの受入経路にも配線されず gate でない | 所見1 | 1 |
| S11 T-180 と並行する private import の merge 順序が gate でない | 所見9 | 4 |
| **被覆** | **10 / 11 (91%)** | **5 / 11 (45%)** |
| **親が refuted と裁定した所見 (誤検出)** | **0** | **0** |

### shadow-only の所見 2 件

- **luna 所見11**: 「段 3 B のみへ縮小し、receipt qualification と名乗り、P1/P2 を裁定パッケージへ
  戻すべき」。authoritative arm は出さなかったが、**独立した別の sol run (レンズ A の所見 9) が
  同じ結論に到達**しており real。軽量 arm が authoritative arm の見落としを拾った実例である。
- **mini 3**: schema が `pilot_id` / `arm_id` を「ASCII identifier」と呼びながら例示値に hyphen を
  含む矛盾。authoritative arm の S8 より具体的で real。

### 採点の限界 (この数値を policy に使ってはならない理由)

1. **循環**: 基準集合が authoritative arm 自身の所見である。sol が見落とし shadow だけが
   見つけた真の欠陥は、構造的に「被覆率」へ反映されない (上の 2 件は親が手で拾った)。
2. **非盲検**: 親は各出力の model を知った状態で採点した。
3. **事前登録なし**: label 集合を shadow 実行の**前**に固定していない。これは親の手順上の実欠陥で
   あり、レンズ A が事前に指摘したとおりの循環を実在化させている。
4. **n=1**: task 1 本、arm あたり run 1 本。分散推定がない。
5. **交絡**: 3 arm は同時起動で、起動時の同時 codex 実行数は 22、終了時 10〜15。
   並行 wave (T-126 / T-180 / T-181 / ai-provenance-forward-fix / T-186) が同一 account で
   稼働していた。**wall-clock を model 差の証拠に使ってはならない。**
   cached input 比率も arm 間で大きく異なる (sol 2,390,528 / luna 895,488 / mini 984,320)。

## 段 1 実測の自己反証

段 1 の生死確認 (`DW-G01`) では、820 行のファイルを読んで 3 問に答える trivial task を
`reasoning=max` で 3 model へ投げ、CLI reported token が sol 34,289 / luna 30,262 /
terra 37,947、wall 49s / 70s / 99s だった。親はこれを根拠に brief へ
「luna も terra も sol より軽くない」と書いた。

**段 3 の実レンズ課題ではこの一般化が成立しなかった** — luna は sol より 31.6% 少ない token で
完了した。trivial task での n=1 測定は実タスクへ一般化しない。brief の当該記述は撤回する。

## 実測で判明した fail-open (一次資料つき)

1. **未サポート model は「消費 0 の session」として rollout に残る。**
   `gpt-5.4-nano` と `gpt-5.1-codex-mini` は「ChatGPT account では未サポート」で 400 拒否
   (rc=1) されるが、rollout には session が生成され、receipt の `model` は要求 slug のまま、
   `model_calls=0` / `cli_reported=0` になる。素朴な pilot はこれを
   「軽量 model は finding を 0 件しか出さなかった」と記録できる。
   session = `019fadd3-c15a-79e1-8783-f083061d4e3d` / `019fadd3-c19c-7a12-bbf0-ded998aed815`。
2. **不正な reasoning 値が silent に通る。** `-c model_reasoning_effort="ultra"` は
   `gpt-5.6-sol` / `gpt-5.6-luna` / `gpt-5.6-terra` で **rc=0 のまま成功**し、receipt には
   `reasoning=ultra` と記録される。`gpt-5.4-mini` だけが 400 で落ちる。
   `DW-O01` は「効いた値」を使えと書いているが、効いたかどうかを機械検査する経路は現状ない。
3. **receipt の model は要求 slug であって served model の attest ではない。**
   `gpt-5.4-mini` に `reasoning=max` を要求したときの 400 応答だけが実体名
   `gpt-5.4-mini-codex-1p-codexswic-ev3` を露出する。成功した rollout に served model は残らない。
4. **model により reasoning の受理集合が異なる。** `gpt-5.4-mini` は `max` を拒否し
   (`none` / `low` / `medium` / `high` / `xhigh` のみ)、sol / luna / terra は `max` を受ける。
   model と reasoning を独立な軸として扱えない組合せが存在する。

## なぜ専用ツールを作らなかったか

親 brief は `tools/codex_model_shadow.py` (arm manifest から receipt を作り fail-closed にする
read-only tool) を成果物 1 に置いていた。独立 3 レンズがすべて NO-GO を返し、うち 2 本が
「実装せず裁定パッケージへ返す」を推奨した。親はこれを real と裁定し、実装しないことにした。

決め手は次の 3 点である。

- **どの受入経路にも配線されない** (レンズ B S10、luna 所見1、mini 1 が独立に指摘)。
  現行の trust root は `tools/check_*.py` と `run_tests.py` であり、親が手で 1 回叩く解析は
  gate ではない。「gate を新設した」と記録すること自体が偽になる。
- **閉じたい穴の多くがツールの外にある**。served identity の attest 経路は存在せず (上記 3)、
  process rc・wall-clock・同時実行数の真正性は T-180 の launcher receipt が前提 (レンズ B S3)。
  ツールは「未検証値に限定条件の文を添える receipt formatter」にしかならない。
- **`docs/phase3.md` [T-182] はツールを要求していない**。要求は
  「同一凍結入力で比較し、finding coverage・誤検出・token/turn/wall-clock と
  model identity receipt を残し、production 既定は変更しない」であり、段 3 の実走で充足済みである。

## ユーザーへ返す裁定パッケージ

1. **T-182 を本レポートで完了とする**か、ツールを別 ID で作るか。作るなら、どの受入経路へ
   配線するかを先に決める必要がある (未配線のまま作れば「gate を名乗る非 gate」になる)。
2. **model identity の attest 経路が存在しない**。現状の receipt は要求値の記録である。
   これを閉じるには codex CLI 側の変更か別の attest 源が要る。放置する場合、
   T-184 の policy は「要求した slug」に対する policy であって「実際に応答した backend」に
   対する policy ではない、と明記する必要がある。
3. **不正 reasoning 値の silent 通過をどの ID が閉じるか** (T-181 / T-183 / T-184)。
   `DW-O01` の「効いた値」は現状どこでも機械検査されていない。
4. **有効な model routing 実験の設計** (レンズ A の提案): 独立 oracle、held-out 複数 task、
   block randomization、cache 条件の分離、価格 version、盲検裁定、事前非劣性 margin。
   T-180 / T-181 の receipt 基盤が land した後の別 wave とすべきである。
5. **暫定仮説として記録してよい範囲**: 第二レンズのような冗長レンズに限れば `gpt-5.6-luna` @ max は
   有望 (91% 被覆・誤検出 0・token −31.6%)、`gpt-5.4-mini` @ xhigh は第二レンズには不足
   (45% 被覆・wall +39%)。**採用判断には上記 4 の実験が要る。**
