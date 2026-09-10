# 段 4 裁定 — dev-wave token-economy (2026-08-04)

段 3 の 2 レンズ (A: 正しさ境界 / B: 整合・実効性) の所見を real/refuted、採用/不採用、
scope 内/外で裁定し、プラン v2 と変異事前登録を確定する。

## 1. 所見の裁定

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A-1 | P1 の「直前エントリ」は履歴から一意に導出できない。実 corpus で exact carry 23,635 行中 **1,316 行が `参照先 != ordinal-1`**。archive max と current 末尾は別々に取得される (`spool_fold.py:1110,1128,1792`) | **real** | 採用 | 内 |
| A-2 | P1′ も `spool_fold` の**意味的**受理集合を変える。`- [T-001] (1)` は現行では実体 item として digest されるが、変更後は carry へ再分類される | **real** | 採用 | 内 |
| A-3 / B-04 | `.claude/commands/rulings.md:13` が旧語句「変わらず (前エントリ参照)」を literal で名指しする生存 consumer。追随しないと裁定待ち項目が索引から落ちる | **real** | 採用 | 内 |
| A-4 | D70 保存則本体は ID 単独 source の脱落を現に赤にする (実効性低下は **refuted**)。ただし `(?=$|[ \t])` → `(?=[ \t])` 変異を kill する負例がない | **real** (後半のみ) | 採用 | 内 |
| A-5 | rotation / ordinal-gap / 同一 fold 連続 entry の fixture が弱く、`ordinal-1` 変異や compact parser 削除が生存しうる | **real** | 採用 | 内 |
| A-6 / B-03 | 親 brief の計数が過大。exact carry は 1,671 行 / 63,498 bytes (親の 1,673 / 63,764 は書式説明 2 行の部分一致)。archive exact carry は 830,541 bytes (親の 1,061,487 は部分一致)。**「rotation 約 2.5 倍」は導出不能**で実比は 1.52 倍 | **real** | 採用 | 内 |
| B-03b | active T は **245 件**であり 237 件ではない (237 は旧 carry 行数、残り 8 件は実体本文)。削減は固定 5,214 でなく `22 × そのエントリの carry 件数` | **real** | 採用 | 内 |
| B-01 | `.agents/skills/dev-wave/SKILL.md:12` が単独段 worker と manager を分けず無条件にクラス 3 起動させる。単独 reviewer あたり最低 **25,663 bytes** の管理者用文脈が余分 (carry 案の約 5 倍) | **real** | **不採用 (実装しない)** | **外** |
| B-02 | campaign の session 再利用除外は支持。ただし「cache 化も品質を落とす」は広すぎる。byte-identical な固定 prefix は 4 役計 36,713 bytes、既定 3 workload で初回以外 **73,426 bytes** が同一。ただし repo 内に cache 提供能力・hit・token 会計の証拠がない | **partial real** | **不採用 (実装しない)** | **外** |
| B-02b | brief の役割列挙 planner/coder/critic/selector は現行 `ROLE_FILES` の planner/coder/**auditor**/critic と不一致 | **real** | 採用 (記録の訂正のみ) | 内 |
| B-07 | 変異のうち `fullmatch`→`match`、3 桁固定、reader 契約落としの 3 件がプラン漏れ | **real** | 採用 | 内 |
| A-6 nit | 末尾エントリ 15,167 vs 15,168 の 1 byte 差 | real (nit) | 不採用 | — |

## 2. 確定した設計 (プラン v2)

- **(P1) は却下、(P1′) `- [T-NNN] (N)` を採用する。** A-1 が親 brief の
  「`((N) 参照)` の N は構成上 100% 導出可能」を実データで反証した。**親の主張が誤りだった。**
  1,316 行が `ordinal-1` 以外を指す以上、ordinal は情報を持つ。行内に残す。
- **削減は 1 エントリあたり `22 bytes × carry 件数`。** 現末尾 (237 carry) で 5,214 bytes、
  無操作なら次エントリ (245 carry) で 5,390 bytes。**「59%」は削除率でなく占有率**であり、
  末尾エントリ全体では 15,167 → 9,953 bytes (**34.38% 減**) と書く。
  **「rotation 約 2.5 倍」は撤回する** (実比 1.52 倍、carry ブロック限定なら 2.375 倍が上限)。
- **`tools/check_docs.py` は無改変。** D70 の regex 受理集合は変えない (A-4 前半で実効性も確認済み)。
- **`carry_re` は旧形と compact 形の完全一致二択**とし、旧形の受理形を一字も狭めない。
  `legacy_ordinal` / `compact_ordinal` のちょうど一方だけを採り、両方・両方なしは例外にする。
- **fail-open を作らない。** 参照先 entry 不在・task 不在・循環・自己/未来参照はすべて例外のまま
  伝播させ、`_task_item_digest(item.block)` の stub へ退避する経路を新設しない。
- **land 前に corpus sentinel を通す。** 現行 worklog + 全 archive に `- [T-NNN] (正整数)` の
  exact 形が 0 件であることを親が再確認してから統合する (A-2、B-04 とも 0 件と報告)。

### 追随する docs / consumer (must-fix)

| 面 | 変更 |
|---|---|
| `docs/worklog.md` 冒頭 D35 節 | 現行書式を compact に、旧書式を凍結済み互換形として定義。有効 ID literal を書かない |
| `docs/spool/README.md` | fold の生成形を compact へ |
| `docs/spool/worklog/README.md` | stub 例と substantive digest 契約を新旧混在へ |
| `.claude/commands/rulings.md:13` | 旧語句 literal を**書式非依存**の文言へ **net-neutral 以下**で置換 (予算 4,988/5,000、余裕 12 bytes) |
| `CLAUDE.md` | **変更しない** (親裁定)。CLAUDE.md は carry 書式を一切名指ししておらず、書式正本は同一ファイル冒頭にある。段 6 で再攻撃させる |

## 3. scope 外 real 所見 → 裁定パッケージ (実装しない)

- **B-01 (最大)。** 単独段 worker/reviewer のクラス 3 起動を分岐させれば **reviewer 1 本あたり
  25,663 bytes**、本 wave の carry 案の約 5 倍が減る。**段構成・裁定境界の変更**であり
  `docs/skill-self-improvement.md` の「実装せず裁定パッケージへ送る」に該当するため実装しない。
- **B-02。** campaign の固定 prompt prefix は初回以外 73,426 bytes が同一。ただし
  prefix cache の提供能力・hit・token 会計の証拠が repo 内に無く、実現済み削減として数えられない。
  出力 cache・session 再利用・payload 欠落 cache key は引き続き禁止のまま。
- **長期滞留 245 件のうち 129 件が 50 エントリ以上連続で無変化** (最長 109 連続、今回更新は 8 件)。
  見送り台帳は D70 の正当な sink であり、整理すれば carry 件数そのものが減るが、
  1 件ずつの意味判断が要るため自動削減の対象にしない。
- archive の遡及圧縮は凍結規約に抵触するため行わない。D70 機構自体は変更しない。

## 4. 変異事前登録 (DW-M01)

対象 node は `orchestrator/tests/test_spool_fold.py` と `orchestrator/tests/test_check_docs.py`。
harness は `tools/mutation_harness.py`。各変異は単一理由性をコードで確認してから登録する。

| ID | 変異 | 期待 |
|---|---|---|
| M01 | producer を旧書式 `変わらず ((N) 参照)` へ戻す | KILLED (byte-exact golden) |
| M02 | producer を P1 (ID 単独行) にする | KILLED (byte-exact golden) |
| M03 | `carry_re` から compact 分岐を削る | KILLED (compact chain / stub digest) |
| M04 | `carry_re` から legacy 分岐を削る | KILLED (既存 legacy 後方互換テスト) |
| M05 | `prior_ordinal` を `ordinal - 1` にする | KILLED (ordinal-gap fixture) |
| M06 | `spool_fold.py:1811` の `prior_ordinal = ordinal` 更新を削る | KILLED (2 entry 即時 prior fixture) |
| M07 | `substantive_digest` の再帰例外を捕捉し stub digest を返す | KILLED (missing entry / missing task) |
| M08 | `carry_re.fullmatch` を `match` にする | KILLED (複数行実体 `- [T-001] (1)\n  詳細`) |
| M09 (正例) | compact carry を常に拒否する | 複数 node が赤 = 過剰拒否の検出力確認 |

## 5. gate の禁止 (署名 + 通る正例)

`carry_re` は次を**拒否**する: `- [T-001] (0)`、`- [T-001] (01)`、`- [T-001] (1) 実体本文`、
`- [T-001] ()`、複数行にわたる item 全体。
**通る正例**: `- [T-001] (1)` (単一行、正整数、末尾 LF) は carry として解決され、
参照先 entry (1) の実体 item の digest を返す。
