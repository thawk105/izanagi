# 段 4 裁定 + plan v2 — [T-675] 住所 (address edge) の構造 lint

親が段 3 の 2 レンズ (A=sol / B=luna、両方 NO-GO) を裁定した結果である。これが実装の正本。

---

## 1. 所見の裁定

### 採用 (real・scope 内)

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| a1 | 単純部分文字列検査は `F260` と `archive/docs/failures.md.bak` で偽 edge を作れる | A-1 | **real・採用** |
| a2 | link definition `[F26]: https://…/docs/failures.md` も偽 edge になる | A-1 | **real・採用** (a1 の修正で同時に死ぬ) |
| a3 | 表セル横断の偽 edge (`\| F260 \| \`archive/docs/failures.md.bak\` \|`) | A-1 | **real・採用** (a1 の修正で同時に死ぬ) |
| a4 | block-level の hidden raw HTML (`<div hidden>…</div>`) で偽 edge を作れる | A-1 | **real・採用** |
| a5 | (P1) は誤り。`_visible_dispatch_inventory_text` なら raw HTML block も除ける | A-2 | **real・採用**。P1 を破棄 |
| a6 | 再 pin しない負例では変異の単一理由性が不成立 (digest finding が併発) | A-4 | **real・採用**。負例は合成 checker の digest だけ再束縛する |
| b1 | 負例で tmp repo の `tools/check_docs.py` の digest だけ再束縛が必要 | B-2 | **real・採用** (a6 と同じ) |
| b2 | 親の R2 文案は R1 の呼称・効能語を満たさない | B-3 | **real・採用**。文案を差し替える |
| b3 | R1 の所有先が (P3) と矛盾し、D と skill で二重化する | B-4 | **real・採用**。(P3) を破棄し 3 分割する |
| b4 | `docs/failures.md` F173 の「機械化は byte 予算に阻まれており」は誤り | B-5 | **real・採用**。訂正する |
| b5 | 「受理集合は変わらない」と無限定に書くのは誤り | B-7 | **real・採用**。限定して書く |
| b6 | 段 2 の推奨案 B は +2 bytes で予算違反 | B-8 | **real・採用**。不採用 |

### 採用 (real・scope 外 → 裁定候補として返す。実装しない)

| # | 所見 | 出所 | 裁定 |
|---|---|---|---|
| s1 | `check_docs` は hooks・CI・pre-commit から呼ばれず、land も fold 経路の generated canonical validation でしか呼ばない。新 lint が効くのは `python3 tools/check_docs.py` を明示的に走らせた層だけ | A-3 | **real・scope 外**。`DW-S03` に従い裁定パッケージ候補として worklog へ返す。**実装しない** |
| s2 | inline の hidden HTML (`<span hidden>…</span>`) では偽 edge が残る | A-1/A-2 | **real・既知限界**。package.md 3.3「(a) は trust root にならない」と整合。**実装しない**。防壁と書かない |

### 親 brief の誤りの訂正 (real)

| # | 誤り | 正 | 出所 |
|---|---|---|---|
| c1 | 「repo の `*.py` 全体で sha256 定数は 2 本だけ」 | 誤り。他に `_EXPECTED_CLEANUP_*`、`SOURCE_FILE_SHA256`、`ROLE_MANIFEST_SHA256` 等がある。**正しい主張は「`docs/skill-self-improvement.md` を pin する sha256 定数は無い」だけ** | A-5 |
| c2 | 「2 literal の同一可視行共起を要求する検査は repo に 0 件」 | 誤り。dispatch inventory は既に同一可視行から typed edge を構成し期待集合と比較する (`tools/check_docs.py:3322` / `:3355` / `:4367`)。**純増は検査パターンではなく「cleanup command の F26 edge という対象」だけ** | A-5 |
| c3 | 「成果物の受理集合は変わらない」 | 限定不足。変わるのは `check_docs` と AI 作業手順の受理集合。certified 選択・レポート・試行台帳の値と参照は変わらない | B-7 |

### refuted

- 既存負例テスト群の巻き添え (B-1) — 起きない。fixture 355 行目が edge 行を保持する。
- 実 command の pin 3 箇所の同期 (B-2 前半) — 不要。実 command の bytes を変えない。
- R2 置換が F173 の再演 (B-3 前半) — 違う。削る語 (`byte・最長行`、`lint に固定せず`) は
  他文書の義務への唯一の到達手段ではない (`docs/decisions.md` と同文書 46 / 49 / 50 行に残る)。
- M11 (iv) の偽陽性 (A-6) — 起きない。
- `DW-G03` 逸脱 (A-7 前半、B-8 前半) — していない。1 分岐・1 対象のまま。
- 段 2 §7 の所有逸脱 (A-7 後半) — 手続き上は指摘のとおり。文案は**親が決める**。

---

## 2. plan v2 — R3 の実装 (codex author が書く)

### 2.1 `tools/check_docs.py`

`_check_command_docs_guard()` の `for rel, contract in COMMAND_INTERFACES.items():` ループ内、
`text = decoded.get(rel)` / `if text is None: continue` の**直後**、`_parse_frontmatter(text)` の
**手前**に置く (frontmatter が壊れて `continue` しても edge 検査が消えないため)。

```python
        if rel == ".claude/commands/cleanup-branches.md" and not any(
            re.search(r"(?<![0-9A-Za-z])F26(?![0-9A-Za-z])", line)
            and "`docs/failures.md`" in line
            for line in _visible_dispatch_inventory_text(text).splitlines()
        ):
            findings.append(
                f"{rel}: F26 と `docs/failures.md` が同一可視行に共起しない — "
                "他文書にしか無い義務への到達 edge を失っている"
            )
```

要件は次の 3 点であり、**これ以外を検査しない**。

1. **可視行**は `_visible_dispatch_inventory_text` で取る (code fence・HTML comment に加え
   raw HTML block も不可視化する)。`_visible_markdown_text` は使わない (a5)。
2. **`F26` は ASCII 英数字に隣接しない出現だけを数える。**`\b` は使わない —
   Python の `\b` は日本語文字も word 文字とみなすため、「正本はF26。」のような
   空白なしの正当表記が偽陽性になる。lookaround で ASCII 英数字だけを排除する (a1)。
3. **path は backtick 込みの exact code span `` `docs/failures.md` `` で照合する。**
   これにより `archive/docs/failures.md.bak` と link definition と表セルの偽 edge が死ぬ
   (a1/a2/a3)。

**やらないこと** — 専用関数・定数 registry・新台帳・新 gate・新 CLI flag を作らない。
他 command・Skill 側・F51・helper path・path 実在性・全 F 番号到達性へ広げない。
`re` は既に import 済みなので import を足さない。

### 2.2 `orchestrator/tests/test_check_docs.py`

新テストは既存の cleanup 系テスト群の直後に置く。`_build_min_repo()` で合成 repo を作り、
`_read` / `_write` で合成 `.claude/commands/cleanup-branches.md` を編集し、
**合成 repo 側の `tools/check_docs.py` の `CLEANUP_COMMAND_SHA256` 定数だけを新 digest へ
置換**してから `_assert_violation` + `_violation_count(res) == 1` を assert する。
実 repo の定数・`_EXPECTED_CLEANUP_COMMAND_SHA256`・`_SYNTHETIC_CLEANUP_COMMAND` は**触らない**。
`_assert_cleanup_digest_violation` は使わない (digest finding 不在を確認するため)。

負例 4 本 (いずれも「違反ちょうど 1 件・digest finding なし」を assert する):

| # | 変形 | 期待 |
|---|---|---|
| n1 | 「正本は `` `docs/failures.md` `` F26。」を「正本は F26。」+ 次行「`` `docs/failures.md` ``」へ**分割** | 赤 |
| n2 | 同文を「旧参照 `` `archive/docs/failures.md.bak` `` F260 は無効。」へ**部分文字列化** | 赤 |
| n3 | 同文を消し、`<div hidden>F26 (`` `docs/failures.md` ``)</div>` を**block raw HTML** で足す | 赤 |
| n4 | 同文を消し、`[F26]: https://invalid.example/docs/failures.md` の**link definition** を足す | 赤 |

正例 2 本 (`_run_check` が緑 = 違反 0 であることを assert する):

| # | 変形 | 期待 |
|---|---|---|
| p1 | 同文を「F26 (`` `docs/failures.md` ``) が正本。」へ**言い換え** (package.md M11 (iv)) | 緑 |
| p2 | 変形なし (baseline `_build_min_repo()`) | 緑 |

p1 も合成 checker の digest を再束縛する必要がある (bytes が変わるため)。

---

## 3. R1 / R2 / R4 の docs (親が書く。実装子は触らない)

**3 分割し、二重化しない (b3)。**

- **R1 → `docs/decisions.md` の新 D (spool fragment)。**呼称「住所 (address edge) の構造 lint」、
  効能「非協調 drift の検出と意図の diff への顕在化」、trust root は人間レビュー、
  そして「協調改変を防ぐ防壁ではない」ことを書く。**採用理由だけを書く。**
- **R2 → `docs/skill-self-improvement.md` 83〜84 行の置換。**pin と lint の責務契約だけを書く。
  確定文案 (実測 **238 bytes / 現行 239 bytes / 差 -1 / 置換後 5996 bytes / 上限 6000**、
  最長 73 chars / 上限 100):

  ```
  `check_docs.py` の担保は予算と dispatch・節・孤児・逃がし・住所 (address edge) の構造 lint に限る。
  whole-file SHA-256 pin も bytes 差だけを検知し、意味は敵対監査と人間レビューが担う。
  ```

- **F173 → `docs/failures.md` の恒久対応の訂正 (spool fragment)。**事故と訂正だけを書く。
  「機械化は `docs/dev-wave/**` の byte 予算に阻まれており」は誤りなので撤回し、
  実装した 1 件と、その効力範囲を書く。**「(b) を実施したので F173 対策を打った」と書かない。**
- **R4 → worklog。**`DW-G05` 上 backlog であること、s1 / s2 を裁定候補として返すこと、
  c1 / c2 / c3 の親の誤りの訂正を書く。

---

## 4. 変異事前登録 (`DW-M01`、B-057 発火)

いずれも「同じ入力を拒否する層が前後に無い」ことを確認済み —
whole-file pin は負例側で再束縛するため digest finding は出ず、
`CODEX_FIRST_REFERENCE_LITERALS` は core/workers だけが対象で cleanup command を見ず、
既存 command 到達性は `docs/skill-self-improvement.md` の有無しか見ない (A-4)。

| ID | 変異 | 期待 | 第一失敗 |
|---|---|---|---|
| M1 | 新 lint の分岐ごと削除 | KILLED | n1 |
| M2 | lookaround を単純 `"F26" in line` へ緩める | KILLED | n2 |
| M3 | `` "`docs/failures.md`" `` を backtick 無しの `"docs/failures.md"` へ緩める | KILLED | n2 |
| M4 | `_visible_dispatch_inventory_text(text)` を `text` へ | KILLED | n3 |
| M5 | `not any(...)` を `any(...)` へ (条件反転) | KILLED | p2 (baseline が赤) |
| M6 | 対象 `rel` を `.claude/commands/dev-wave.md` へ差し替え | KILLED | n1 |
| M7 | `_visible_dispatch_inventory_text` を `_visible_markdown_text` へ | KILLED | n3 |

M7 は (P1) の破棄が本当に検出力を生んだかを測る (a5 の帰属)。
