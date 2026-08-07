# 段 4 裁定 — [T-595] reasoning A/B

段 3 は 2 レンズとも NO-GO。レンズ A must-fix 11 件、レンズ B must-fix 8 件 / should-fix 1 件。
親が real/refuted と採否を裁定し、plan v2 を確定する。

## 親 brief の訂正 (自分の実測値を差し替える)

- **A-2 は real (実測で確認)。** 親の fix 巡回分布は `s6-fix*.md` の glob で数えており、
  `s6-fix-ruling.md` (3 件) と `s6-fix-adjudication.md` を巡回に混入させていた。
  除外して数え直すと非ゼロ側は `1×2, 2×7, 3×4, 4×4, 6×1` (18 wave) に変わる。
  さらに分母 (実装を伴う wave) の同定も `s5-impl*.md` の命名揺れに依存しており信頼できない。
  **この分布を power の根拠にしてはならない。**
- **A-3 は real。** 親は「必要 pair 数 9〜15」と書いたが、正規近似だけでも
  `((1.645+0.842)×1.6)^2 = 15.83` で最低 16 pair であり、有限標本 t・co-primary の joint power・
  欠測を入れればさらに増える。親の見積もりは**過小**だった。
- **結論の向きは変わらない** — 単一 wave での実走は不能。ただし**根拠を差し替える**。
  根拠は「pair 数の見積もり」ではなく、**endpoint・盲検・実 treatment・解析凍結が未閉鎖**
  (A-1/A-4〜A-11、B-1〜B-6) であることとする。
- **B-1 は real (実測で確認)。** `build_snapshot()` は `CASE_HASHES` の POS/NEG 以外を拒否する
  (`tools/codex_reasoning_ab.py:1277`)。親の (P6) 生死確認は**現装置では実行不能**である。
  本 wave は家族一般化を実装しないため moot に落とすが、「生死確認済み」とは書かない。

## 裁定

### 採用 = 実装する (1 件)

**B-8 — D207 adoption latch。** `tools/check_docs.py` に、`docs/dev-wave/workers.md` の
`DW-S02` / `DW-S03` が `reasoning=max` を規定していることを exact pin する検査と、
その負例テストを追加する。

- 実測根拠: `check_docs.py` に `reasoning` の出現は **0 件**。D207 の
  「引き下げの可否は A/B だけが決める」は現在 **prose だけ**で機械防壁が無い。
- 成果物影響 (DW-G05): 実装しなければ、将来の wave が `workers.md` の prose を書き換えて
  段 2/3 を `high` にしても全検査が緑のまま通る。A/B 未完了のまま production の敵対レビュー
  検出力が下がり、reward hack・oracle 穴の must-fix が段 4 へ届かず、
  **certified 選択と材料レポートの受理集合が黙って広がる**。
- 規律 2 との整合: 検出力を**上げる**方向であり、緩める変異ではない。
- DW-O13 (gate 入力の実在): `docs/dev-wave/workers.md:7` と `:12` に `reasoning=max` が実在する。
- DW-G04 (発火 gate): 発火条件を満たす既存 artifact path = `docs/dev-wave/workers.md`。
- docs bytes を 1 byte も増やさない (コードとテストのみ)。予算残 13 bytes を消費しない。

### 不採用 = real だが scope 外 → 裁定パッケージでユーザーへ返す

**(1) 段 2 プランの本体 (case family 一般化 + full-wave endpoint ledger + protocol freeze)。**

- A-7 / B-2 が real: endpoint を偽装不能にするには、wave の全 worker を実際に spawn する
  trusted supervisor が要る。現行 dev-wave の正本は `DW-O01` の直接 `codex exec` + `.done` で、
  `codex_worker_launch.py` の production caller は repo 内に存在しない (実測)。
  この結線は**装置ファイルの外**にあり、`docs/dev-wave/*.md` への producer 契約追記を伴う。
- B-2 が real: その追記先の aggregate 予算は **25,187 / 25,200 = 残り 13 bytes** (実測)。
  安全義務を削らずに空きを作る裁定が先に要る ([T-597] と束ねる)。
- A-9 / B-5 が real: 外部 custodian は repo 外の credential 分離と承認済み公開鍵 fingerprint を
  要求する。ユーザーが用意しない限り `blind=true` を名乗れない。
- A-1 / A-3 が real: 母集団・層化・margin・power が未確定。
- **これらを閉じずに (b) を実装すると、「schema 試作」を「判断可能な装置」として台帳に記録する
  ことになる。** それは本 wave が防ごうとしている fail-open そのものである (規律 3)。

**(2) 完全 campaign の実走 (joint 30 本 / 段別帰属 45〜60 本)。**
資源決定であり、ユーザー裁定事項。親は決めない。

**(3) 段別帰属か joint かの択一。** 段 2 プランは joint (`MM` 対 `HH`) を推奨、
codex 自身の反対意見 2 が「段 2 と段 3 の個別寄与を識別しない」と指摘。
T-595 の文面は「段 2/3 の max を high へ落とせるか」であり、joint でも文面は満たすが、
片方だけ落とす選択肢は答えられない。**ユーザー裁定へ返す。**

### moot (本 wave が家族一般化を実装しないため発火しない)

A-4, A-5, A-6, A-10, A-11, B-3, B-4, B-6, B-7, B-9。
いずれも real の指摘だが、対象となる新 family / 新 ledger / 新 protocol を本 wave が作らない。
**裁定パッケージへ全文を持ち越し、campaign 設計 wave の入力にする。**
本 wave の worklog には「refuted」ではなく「未実装ゆえ未発火」と書く。

## plan v2 (実装単位)

単一単位。所有パスは `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` のみ。

1. `check_docs.py` に `DW-S02` / `DW-S03` の `reasoning=max` を exact pin する検査を追加する。
   - 節ごとに独立に検査する (片方だけ落ちる負例を作れること)。
   - 「`reasoning` という文字列がある」だけの恒真検査にしない。
     **`max` 以外の値を書いたら赤になる**ことを負例で示す。
   - finding 文言に「引き下げは D207 の A/B が未充足のため不可」を含める。
2. `orchestrator/tests/test_check_docs.py` に正例 1 件と負例 3 件を追加する。

## 変異事前登録 (DW-M01)

前後に同じ入力を拒否する層が無いことを実測で確認済み — `check_docs.py` の `reasoning` 出現は
0 件であり、effort 値を見る検査は他に存在しない。赤理由は単一に絞れる。

| # | 変異点 | 殺す test | 単一理由性 |
|---|---|---|---|
| M1 | pin 検査そのものを削除 | 負例 (DW-S02 を `high` に改変) が赤にならない | 他層に effort 検査なし |
| M2 | pin を「`reasoning` を含む」の恒真検査へ弱化 | 負例 (値だけ `high`) が通ってしまう | 節名検査は値を見ない |
| M3 | `DW-S03` 側の pin を落とす | 負例 (DW-S03 だけ `high`) が通ってしまう | 節ごとに独立検査 |
| M4 | 正例側 — 現行 `workers.md` を拒否するよう過剰拒否化 | 正例 test が赤 | 承認外の過剰拒否検出 (DW-M01) |

`DW-M08` (テスト強化だけの wave の新旧両走) は、本 wave が**検査を新設する**ため該当する。
新テストが旧コード (pin 追加前) で赤、新コードで緑になることを両走で示す。
