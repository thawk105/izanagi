# 段 4 裁定 — [T-313] 常時読量 gate

**裁定: 実装する (通常遷移 1→…→9)。** 一次裁定 (worklog (140) = 前 wave パッケージの択 1) は
実装方向まで裁定済みであり、段 3 の所見はいずれも「別案へ戻す新事実」ではなく
**実装の必須要件**である (`DW-S04`)。ただし成果の**主張は縮める** (下記 B2)。

## real / refuted

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 | 段 dispatch 行に**節 ID を持たない bare path** (`… 全文`) を書くと、pair も層予算も registry 閉包も動かないまま operations 全文 (≥7,001 bytes) を常時読了へ移せる。allowlist は path しか見ない | **real (blocker)** | **採用** — 参照行の `line_paths == {path for path, _ in pairs}` を必須にし、pair を 1 つも持たない path を拒否 |
| A2 | 予算 splitter を raw `^## ` で切ると、fence / HTML comment 内の偽 H2 が境界になり、以降の**本物の L1 本文が未分類**になる (実測 2,829 bytes が L1 から消える)。プラン案の不変条件「全 slice + preamble == file bytes」は**恒真**でこれを検出しない | **real (blocker)** | **採用** — 既存の可視 H2 offset を slice 境界に使い、`可視登録 H2 ↔ slice` の 1:1 と `分類済み + preamble == 全 bytes` を両方検査 |
| A3 | `U`/`C` cell と trigger を pin しても、**marker 凡例・表 header・表外の規範文**で条件性の意味を書き換えられる | **real (blocker)** | **部分採用** — 凡例行と表 header を exact contract で pin する。表外の規範文までは閉じない (下記「本 wave の限界」) |
| A4 | 「常時読量」は unique footprint であって event 加重読量ではない。同じ節を複数段で読む重複を数えないため、親 brief の主張は過大 (event 加重なら L1 は 12,670 bytes) | **real (major)** | **採用** — 名称を「`docs/dev-wave/**` leaf の unique byte footprint」に限定し、brief の不変条件「縮める方向は L1 のみ」を「L1 と L1.5」に訂正 |
| A5 | 受理集合表の取りこぼし: 固定 13 節での理論上限 33,191 (旧比 +7,991)、L2 追加は `.claude/commands/dev-wave.md` の 9,500/140 gate に先に当たる (余白 58 bytes / 1 char)、exact trigger は意味等価な言い換えも拒否する | **real (major)** | **採用** — 受理集合表へ全部書く |
| A6 | 「L2 節しかない将来 file の preamble を L1 へ」は**現 repo で到達不能** (`DW-G04` 不成立)。未分類 slice の黙殺・bare path・fence 解析・凡例改変・未知 mode に KILL node が無い | **real (blocker)** | **採用** — 到達不能分岐は書かず fail-closed にする。6 系統に負例と変異を登録 |
| A7 | `DW-CTX` / `DW-O04` の位置修正は到達不能節も義務消失も生まない | **real (nit)** | 採用 (P3/P4 成立) |
| A8 | live consumer は `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` の 2 本ちょうど (前 wave 所見 A4 は解消)。一方 L0 command 9,442 / self doc 5,997 / Codex skill 3,747 は scope 外なので「dev-wave 全層の常時読量 gate」とは呼べない | **real (major)** | **採用** — 名称を leaf に限定。複合 envelope は**パッケージ Q2** へ |
| B1 | 新規 L2 節の admission が無い。受理上限は `20,191 + 1,000N` で N に上限が無く、[T-577] の見送り候補も L2 として再登録すれば復活できる | **real (blocker)** | **scope 外 → パッケージ Q1**。機械側の現状 (L2 ID は `REQUIRED_REFERENCE_SECTIONS` / `CONDITION_DISPATCH_CONTRACT` の literal pin なので追加には checker 編集が要る) は事実として記録する |
| B2 | 実装後も **[T-328] 従属 4 件の大半は書けない**。L1/L1.5 固定に当たるため。通るのは [T-279] A3 (`DW-O20`、489+154=643) と、[T-317] A9 を `DW-O19` へ置く場合 (602+147=749) だけ。[T-665]/[T-662]/[T-648]/[T-550] は全部 L1/L1.5 側で止まる | **real (major)** | **採用 — 親 brief の `DW-G05` 主張を訂正する。**本 wave の効果は「T-328 系の L2 部分だけ解放」であって「予算で止まっている項目の解放」ではない |
| B3 | file cap を「L1/L1.5 の hot slice にだけ適用し L2 は単節 cap のみ」にする第三の道がある。P1 の「file cap を残すと解放されない」は O04/O20 には当たるが全面撤去の必然性は導かない | **real (major)** | **不採用 (理由付き)** — 層 cap が既に同じ形状 (層内での交換のみ) を守る。file 別 hot cap は根拠となる現在値を持たず、pin が 4 本増えて drift 面が広がる。**P1 の記述は「既存配置・本文無削除なら 71 bytes」に限定して書く** |
| B4 | 入口は外部 supervisor に `DW-CTX` 読了を課すが、`tools/dev_waves/daemon.py` / `worker.py` に読取処理は無い。P4 は dispatch の重複整理であって「読み動線を直す」起票目的を解消しない | **real (major)** | **採用 (scope 限定)** — 本 wave の成果を「`DW-CTX` の分類重複除去」と書き、実結線は**別タスク起票候補**として返す |
| B5 | 同一 `(path, ID)` が複数 stage/condition edge を持つ正当例 (`DW-CTX` = 段 9 + 条件 21/22、`DW-O04` = 段 5/6 + 条件 04) の合法性がプランに無い。集合へ潰すと重複を検出できず、owner exactly-one にすると正当な共有参照を誤拒否する | **real (major)** | **採用** — `(stage/condition, mode, path, ID)` の **edge 表**を正本にし、typed map・flatten view・層導出をそこから導く。`DW-CTX` / `DW-O04` の共有参照は正例テストにする |
| B6 | routing 3 の L2 削除条件は docs に在るが checker は見出ししか見ない。将来の L2 追加・削除への機械的歯止めは無い | **real (nit)** | B1 と同じ面。**パッケージ Q1** へ集約。self doc は本 wave で変更しない |
| B7 | brief の実測基準 `@34957a24` は現 HEAD `b9c7a534` と不一致 (値は一致) | **real (nit)** | **採用** — 実装直前の HEAD で再計測し、層 pin の基準 commit をその値にする |

**refuted は 0 件。** 前 wave の未解決 4 点のうち、self allowlist 脱落 (A4) と旧 M5 は解消済み、
受理拡大は一次裁定が意図的に承認済み、残る「L0/self を含めるか」は **Q2** として再度返す。

## プラン v2 — 段 2 案からの差分

段 2 案 (`s2-plan.md`) を土台にし、次を必須要件として上書きする。

1. **edge 表を正本にする (B5)。** `(stage_or_condition, mode, path, section)` の 4-tuple 集合を
   parser の出力とし、`STAGE_UNCONDITIONAL_DISPATCH_CONTRACT` / `STAGE_CONDITIONAL_DISPATCH_CONTRACT` /
   flatten view / 層分類をすべてそこから導出する。共有参照は許可し、`DW-CTX` (段 9 U + 条件 21/22) と
   `DW-O04` (段 5 C + 段 6 C + 条件 04) を正例で固定する。
2. **path→pair 束縛 (A1)。** 参照行が挙げる path 集合と、その行の pair が持つ path 集合の一致を必須にする。
   節 ID を持たない path は理由付きで拒否する。負例 `stage-bare-allowlisted-path` を置く。
3. **可視 H2 を slice 境界にする (A2)。** 既存 `_visible_markdown_lines()` 系の可視判定で得た H2 offset で
   raw text を切る。検査は 2 本 — (i) `分類 bytes + 算入 preamble == 4 冊の実 bytes`、
   (ii) **可視登録 H2 と slice の 1:1 対応**。(i) だけでは恒真なので (ii) を必ず併置する。
   fence / HTML comment / raw HTML / `## DW-C00—` 形式崩れを境界テストに入れる。
4. **凡例と header の exact pin (A3)。** marker 凡例行と段表 header 行を literal contract にする。
5. **到達不能分岐を書かない (A6)。** 「L2 節しかない file の preamble」分岐は実装せず、
   そのような file を見つけたら fail-closed で拒否する。
6. **層予算値は実装直前の HEAD で再測した値を pin する (B7)。** 現時点の見込みは
   L1 10,625 / L1.5 9,566 / L2 単節 1,000。
7. 段 2 案の B (予算置換)、C (`DW-CTX`/`DW-O04` 位置修正)、`DW-C00` の byte-neutral 文言修正、
   registry/allowlist の作り替えはそのまま採用する。

## 変異事前登録 (`DW-M01`)

段 2 の M1〜M8 を採り、A1/A2/A6/B5 の穴に 4 件を足す。各行は「同じ入力を先に拒否する層が
前後に無い」ことを実装時にコードで確認してから登録を確定する。

| # | 変異 (production を無効化する位置) | KILL する node |
|---|---|---|
| M1 | L1 比較を恒偽化 | `test_dev_wave_layer_budget_rejects_plus_one[l1]` |
| M2 | L1.5 比較を恒偽化 | `…[l1_5]` |
| M3 | L2 単節比較を恒偽化 | `…[l2_section]` |
| M4 | typed U/C 照合を外し flatten 集合だけ比較 | `test_dev_wave_dispatch_conditionality_retyping_is_rejected[stage-u-to-c]` |
| M5 | mode 欠落を U へ fallback | `…[stage-marker-missing]` |
| M6 | 条件表第 2 列の exact trigger 照合を除去 | `…[condition-always]` |
| M7 | preamble を層合計から除外 | `test_dev_wave_layer_budget_rejects_plus_one[l1]` |
| M8 | UTF-8 byte 数を Python 文字数へ弱化 | `…[l2_section]` (fixture は 1,001 bytes かつ 1,000 文字以下) |
| **M9** | path→pair 束縛を外す (bare path を受理) | `test_dev_wave_dispatch_rejects_bare_path[…]` |
| **M10** | slice 境界を可視 H2 から raw `^## ` へ戻す | `test_dev_wave_layer_slicing_ignores_fenced_heading[…]` |
| **M11** | 可視登録 H2 と slice の 1:1 検査を外す (合計一致だけ残す) | 同上 (恒真化の検出) |
| **M12** | edge 表を集合へ潰し mode を落とす | `test_dev_wave_shared_reference_edges_are_typed[…]` |

**過剰拒否の正例 (`DW-M01` の受理集合縮小 wave 要件):** 現行 repo が緑であること、
`DW-CTX` / `DW-O04` の共有参照が緑であること、`DW-O20` へ 154 bytes 足した状態が緑であること
(裁定どおり L2 が解放されることの正例)。

## `DW-G05` — 成果物影響 (訂正版)

certified 選択・レポート・台帳の**値は変わらない** (docs 契約のみ)。実装しない場合の差は
「予算で止まっている項目のうち **L2 に置けるものだけ**が書けないままになる」であり、
具体的には [T-279] A3 (`DW-O20` +154 bytes) と [T-317] A9 (`DW-O19` へ置く場合 +147 bytes) の 2 件。
**[T-328] の他の従属項目、[T-665]/[T-662]、[T-648]、[T-550] は実装後も L1/L1.5 固定に当たって
書けない** (B2 実測)。親 brief の「予算で止まっている項目の解放がここに集中」という記述は
過大であり、本裁定で訂正する。

## 本 wave の限界 (報告に必ず書く)

- 表外の規範文・凡例外の自然言語で条件性の意味を書き換える経路は閉じない (A3 残余)。
  意味面の gate は [T-316] の所有である。
- 指標は unique footprint であって event 加重読量ではない (A4)。
- 外部 supervisor が実際に `DW-CTX` を読む結線は無いままである (B4)。
- 新規 L2 節の admission control は無い (B1)。機械的には L2 ID が literal pin なので
  checker 編集とレビューは要るが、byte 上限は無い。

## ユーザーへ返す設計択一 (小さく 4 件)

- **Q1. 新規 L2 節の admission (B1/B6)。** (a) 現状どおり literal pin + code review だけで足りるとする、
  (b) routing 3 の 3 条件 (発火実績・機械代替・ユーザー裁定) を**新規登録側にも**課す規範を
  `docs/decisions.md` (byte 上限なし) へ D として記録する、(c) L2 節数上限を置く。
  **親推奨 = (b)。** 一次裁定の「無制限には増えない」を成立させるのは削除条件ではなく登録条件であり、
  予算を使わずに書ける ([T-664] R6(a) と同型の先例)。
- **Q2. L0 command / self doc / Codex skill を常時読量に含めるか (A8、前 wave の未決)。**
  (a) 含めず、現行の個別 cap のみ (親推奨)、(b) 複合 envelope を設計する。
  (b) を採るなら「self doc のどの節を常時と数えるか」の追加裁定が要る。
- **Q3. event 加重 envelope (A4)。** (a) 作らない (親推奨)、(b) 別 wave で設計する。
  unique 10,625 に対し event 加重 12,670 で、差は同一節の複数段読了に由来する。
- **Q4. `DW-CTX` の実読取結線 (B4)。** (a) 別タスクとして起票する (親推奨)、(b) 現状追認で閉じる。
  入口は外部 supervisor へ読了を課すが `tools/dev_waves/daemon.py` / `worker.py` に読取処理が無い。

**Q1〜Q4 はいずれも本 wave の実装を止めない。** 実装は一次裁定の範囲で完結し、
Q1〜Q4 はその上に載る追加判断である。
