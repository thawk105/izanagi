# backlog-guard wave — ハイブリッド標準ループの逐語 (2026-07-20)

worklog 2026-07-20 (17) / D70 の一次資料。**この文書は凍結**する (訂正は erratum 追記のみ)。
承認済み wave C = 「次の一手」への安定 ID 導入と `tools/check_docs.py` の保存則検査。
機構形式のユーザー裁定 (ID + 機械検査) は worklog 2026-07-20 (8)。

**erratum (2026-07-21 追記)**: 本 wave は基準 commit `a23a9a8` で走ったが、その間に別セッションが
main を `ed72579` へ進め、**D69 と worklog エントリ (16) を先に使用した**。本 wave は後発として
**D70 / エントリ (17)** へ繰り下げた。以下の逐語中に現れる「D69」「(16)」は起草当時の番号であり、
**逐語は凍結のため書き換えていない**。現在の正しい番号は D70 / (17) である。

**authority: none** — 本文書は経緯と所見の逐語保存であり、現在状態の正本ではない。
現在状態の正本は worklog 末尾と `docs/phase3.md`、設計判断は D69。

## この wave の要約

| 段 | 実施 | 結果 |
|---|---|---|
| 1 brief | 親 | provisional 裁定 3 件を番号付きで攻撃対象に明示 |
| 2 プラン起草 | codex gpt-5.6-sol / max / read-only | file:line 粒度。親の (P1)(P2) を否認 |
| 3 敵対相談 | codex ×2 並列 / max | **両方 NO-GO。23 所見すべて real (refuted 0)** |
| 4 裁定 | 親 | 致命所見を scope 内で実装。変異 14 件を事前登録 |
| 5 実装 | codex / high / workspace-write | 2 ファイル限定。期待赤 5 件と実測が完全一致 |
| 6 敵対レビュー | codex ×2 並列 / max | **両方 NO-GO。19 所見** (うち 3 件は親 docs の誤り) |
| 6' fix | codex / max | レビュー real 所見の修正 |
| 7 記録 | 親 | 本文書 + worklog + D69 |

## 親 brief 自身の誤り 3 件 (brief を攻撃対象に含める規律が効いた実績)

1. **(P1) 台帳の既存 B-xxx は遡及ラベルしない** → 否認。設計正本 (前身 handoff) が
   「見送り台帳の項目にも同じ ID 体系を使う」と明記しており、読み替えは成立しない。
   B-xxx を残して T-* を併記すれば相互参照 churn も起きない
2. **(P2) 末尾エントリに遡及で ID を振る** → 否認。`docs/worklog.md` 冒頭が
   「過去エントリは凍結し、次の規約は新規エントリに適用する」と明記しており抵触する
3. **台帳の対象を「45 件」と記載** → 誤り。実数 **46 件** (親が実読で確定)。
   プラン初版の「48 行」も誤り (48 は取り消し線を含むトップレベル項目数)

## 親が独立 probe で検出した実バグ (相談 A の BG-01 と二重確定)

プラン初版の見送り台帳抽出 `DEFERRED_LEDGER_RE` は、見出し行の suffix を `(?:[ \t].*)?` と
書いており、`re.DOTALL` の下で `.` が改行を食う。実測で**見出しマッチが 21,847 文字を飲み、
body が 0 文字**になった。台帳が sink として機能せず、見送った項目が常に「落ちた」と誤判定される。
しかも抽出は「成功」扱いのため fail-closed の finding も出ず**静かに壊れる**。
さらにプランの fail-closed 表にあった「台帳 ID 0 件は単独では違反にしない」が、この破損を
ちょうど隠す位置にあった。修正 = 見出し行を `[^\n]*` にする (適用後 body 14,243 字 / 箇条書き 58 行)。

この変異は **BG-M13 として事前登録**し、実測で KILLED (11 テストが赤) を確認した。

---

## 段 1 — 親の brief (逐語)

# brief — backlog-guard wave (C): 次の一手 ID + check_docs 保存則検査

## scope

worklog「次の一手」の項目が黙って落ちる経路を機械検査で塞ぐ。消化・継続・理由付き見送りだけを通す。
成果物は 5 点: (1) ID 書式の規約追記、(2) 現行項目への初回 ID 付与、(3) `tools/check_docs.py` の保存則検査、
(4) `orchestrator/tests/test_check_docs.py` の正例・負例、(5) `docs/decisions.md` に D69 を 1 エントリ。

設計の正本 = `docs/handoff/2026-07-19-backlog-guard-mechanism.md`。

## 確定済みユーザー裁定 (再議しない)

- 機構形式 = **ID + 機械検査**で確定 (worklog 2026-07-20 (8))。対案「書式規律のみ」は不採用
- 本 wave の実施順は承認済み (worklog 2026-07-20 (14) 次の一手 1(b) → (15) で 1(a) へ繰上げ)

## 不変条件 (破ったら NO-GO)

1. **新しい TODO ファイルを作らない** — 可変状態の正本は worklog 末尾と phase doc だけ (CLAUDE.md 6a)。
   既存 2 正本 (次の一手・見送り台帳) を ID で結ぶだけにする
2. **恒真ゲート禁止 (F9/F15)** — 節抽出・エントリ抽出の失敗は「黙って skip」ではなく**違反として可視化**する
   (`_current_pin()` が None を違反にするのと同じ原則)。ID がゼロ件でも検査が蒸発したと分かる形にする
3. **ローテーション偽赤の回避** — 現行 worklog に直前エントリが存在するときだけ保存則を発火させる。
   ただし 2 と衝突させない (「直前が無い」と「抽出に失敗した」を区別すること)
4. `check_docs.py` に警告水準は無い (finding = exit 1)。**新設する検査もこの文化に従う**
5. ID 採番の 正本を新設ファイルにしない。**現存 ID から機械的に導出可能**な規則にする (並行セッション衝突対策)
6. 検査対象は living な現行文書のみ。**アーカイブ済み worklog は対象外** (凍結文書)

## 親の provisional 裁定 (**攻撃対象。誤りならプランで否認せよ**)

- (P1) **T-\* は 次の一手 を通る項目の ID 体系とし、見送り台帳の既存 B-xxx は遡及ラベルしない。**
  B-xxx は監査ローカルキー (前身 handoff 明記) で、既に耐久台帳にあり「次の一手から黙って落ちる」経路を
  持たない。45 件の遡及ラベルは insights 群の相互参照を churn させる。**ただし前身 handoff の
  「台帳保留分にも ID を振る」と字面が食い違う** — この読み替えが正当か判定せよ
- (P2) **現行末尾エントリ (15) の 次の一手 にも遡及で ID を振り、新エントリ (16) で保存則を実際に発火させる。**
  振らないと初回実行が構造的に vacuous になり、実データでの証拠がゼロのまま緑を主張することになる。
  **ただし worklog 冒頭は「過去エントリは凍結し新規エントリに適用」と規定**しており、
  (15) への追記がこの凍結規約に抵触しないか判定せよ (抵触するなら vacuous を受け入れる代替を示せ)
- (P3) 「消化に言及」の判定は **ID トークンが末尾エントリ本文または 次の一手 に出現すること**で足りるとする
  (自然文の意味検査はしない = D30/D45 却下と同根)。sink は末尾エントリか見送り台帳の 2 つだけ

## 成果物の形

- コード: `tools/check_docs.py` (main() の既存 finding 群の隣に追加)、`orchestrator/tests/test_check_docs.py`
  (合成 repo `_build_min_repo()` を土台に、**負例 = ID を黙って落とした worklog が実際に赤くなる**ことを固定)
- docs (**親のみが編集**): `docs/worklog.md` 冒頭の書式節、`docs/phase3.md` 見送り台帳の前書き、
  `docs/decisions.md` D69、`docs/worklog.md` の ID 付与
- 受入: 全走緑 + `python3 tools/check_docs.py` rc=0 + 事前登録変異の全 kill

## 並列分割の方針

**実装は 1 単位 (codex 1 本)。** 検査本体とテストは finding 文字列・抽出関数で密結合しており、
分割すると単位間で契約が腐る。docs は実装子の権限外 (コードとテストのみ編集可) なので**全て親が書く**。
その結果、実装子の所有 = `tools/check_docs.py` + `orchestrator/tests/test_check_docs.py` の 2 ファイルのみで
素集合が自明に成立する。並列化は 段 3 敵対相談 2 本と 段 6 敵対レビュー 2 本で行う。

**実装子への追加要求**: 「テスト緑」の主張には**走らせた範囲を必ず併記**させる (前 wave D68 の実績:
4 ファイル限定の実走で「赤なし」と報告 → 全走で 10 件赤)。テスト fixture へ現行値を差し込んで
破損を隠す変更は禁止 (F27)。

---

## 段 2 — codex プラン起草 v1 (逐語)

# 実装プラン

## 冒頭で否認・保留すべき前提

- **P1 は否認する。** 設計正本は、見送り台帳にも同じ T-* 体系を使い、裁定で生き残った台帳保留分にも初回 ID を付けると明記している（[handoff:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-19-backlog-guard-mechanism.md:23)）。B-* は削除・置換せず、`[T-*]` を行頭へ加える。これなら既存 B-* 参照を churn させず、B→T 対応も同じ行で表現できる。
- **P2 は否認する。** [worklog:14](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:14) の実文は「**過去エントリは凍結し、次の規約は新規エントリに適用する。**」であり、既存 (15) への追記は抵触する。後述の二段 land で、(15) を触らず初回の非 vacuous 検査を成立させる。
- 現在、採番母集団となる worklog・archive worklog・見送り台帳には正式な T-* が **0 件**。`[T-042]` は handoff の例示だけである。したがって初回は `T-001` から始める。
- brief の「45 件」の厳密な対象集合は **不明**。見送り台帳 `phase3.md:394-455` には B-* 付き箇条書きが 48 行あり、B-008/B-009 は terminal、B-056/B-057 はともに「消化」の記述を持つ一方、今回 B-057 は再発火している。45 件とするなら、親が除外する 3 行を D69 で明記してから採番すること。推測で選ばない。
- decisions の最新は [D68:2578](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2578)。`^## D(\d+)\b` の最大値 68 + 1 により D69 で確定する。

## Provisional 裁定

| 裁定 | 評価 | 理由 |
|---|---|---|
| P1 | 否認 | handoff `:23-26` と、B→T 対応を要求する既存調査記録に反する。B-* を残したまま T-* を併記すれば相互参照 churn は起きない。 |
| P2 | 否認 | worklog `:14` の凍結規約に字義どおり抵触する。新規 bootstrap エントリと次の実装エントリの二段で代替可能。 |
| P3 | 採用 | 自然言語の「消化」意味判定は行わず、直前 ID が末尾エントリ本文（その中の「次の一手」を含む）または見送り台帳に厳密トークンとして存在すれば受理する。保証は保存則に限定する。 |

## 1. ID 書式と文書変更

### 正規表現・位置

正式 ID の正規表現は次で固定する。

```python
r"\[T-(?P<number>00[1-9]|0[1-9][0-9]|[1-9][0-9]{2,})\]"
```

- `T-001` から始まり、999 を越えたら `T-1000` とする。
- `T-000`、`T-01`、`T-0001`、括弧なしの `T-001` は無効。
- 行末ではなく、Markdown の list marker 直後、すなわち論理的な行頭に書く。

```markdown
1. [T-001] backlog-guard を実装する
- [T-013] **trigger-loop ...** (B-002, ...)
- [T-001] 消化: backlog-guard の検査を導入した
```

「次の一手」に `(a)/(b)` で複数原子を詰めず、1 原子 = 1 list item = 1 先頭 ID に平坦化する。

### 採番規則

親が docs を書く直前と land 直前に、以下の順で機械導出する。

1. 採番母集団を `docs/worklog.md`、`docs/archive/worklog-*.md`、`docs/phase3.md` の「見送り台帳」節だけに限定する。handoff の例示は含めない。
2. `[T-...]` らしいトークンを全抽出し、上記正規表現に full-match しないものがあれば採番を中止する。
3. 有効 ID の数値最大を取り、ゼロ件なら 0 とする。新規 ID は `max + 1`。
4. 初回は bootstrap worklog の原子項目を表示順、その後に生存が確定した見送り台帳項目を文書順で連番にする。
5. 並行セッションは番号を予約したとみなさない。統合直前に再走査し、未 land 側を振り直す。

現在の (15) `docs/worklog.md:654-665` は 12 原子に分解できる。見送り台帳が親確認どおり 45 件なら、推奨順では bootstrap が T-001〜T-012、台帳が T-013〜T-057 になる。ただし45件の対象集合確定前はこの範囲も provisional とする。

### 親が行う docs 編集

- [worklog:12-23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:12) に次の骨子を追記する。

  - 新規「次の一手」の各原子項目は list marker 直後に `[T-NNN]` を必須とする。
  - ID は一度付与したら変更・再利用しない。
  - 直前 ID は、次エントリ本文で消化に言及、次の一手で継続、または見送り台帳で理由付き保留のいずれかに残す。
  - 採番は既存 authority 群の最大値 + 1。並行変更は統合直前に再採番する。
  - ID のない新規 list item は warning ではなく違反。
  - 過去エントリは引き続き凍結し、初回導入も新規エントリから行う。

- [phase3:386-390](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:386) に「生存中の台帳項目は `- [T-NNN] ... (B-xxx, ...)`、B-* は監査ローカル別名として保持、新規見送りは元の T-* を持ち込む」を追記する。
- `phase3.md:394-455` の生存項目に T-* を併記する。terminal 項目へ推測で付与しない。
- `docs/decisions.md:2634` の後へ D69 を追加し、ID 書式、二 sink、fail-closed、ローテーション時の一件状態、B-* 併記、自然言語意味検査をしない限界を記録する。

## 2. `check_docs.py` の file:line 設計

### 定数・正規表現

[tools/check_docs.py:73-78](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:73) の worklog 定数直後へ、`PHASE3` と以下を追加する。

```python
WORKLOG_H2_RE = re.compile(
    r"^##[ \t]+(?P<title>[^\n]+?)[ \t]*$", re.MULTILINE
)
WORKLOG_ENTRY_TITLE_RE = re.compile(
    r"\d{4}-\d{2}-\d{2} \([1-9][0-9]*\) — .+"
)
NEXT_ACTION_RE = re.compile(
    r"^### 次の一手[ \t]*$\n(?P<body>.*?)(?=^###[ \t]|^##[ \t]|\Z)",
    re.MULTILINE | re.DOTALL,
)
DEFERRED_LEDGER_RE = re.compile(
    r"^## 見送り台帳(?:[ \t].*)?[ \t]*$\n"
    r"(?P<body>.*?)(?=^##[ \t]|\Z)",
    re.MULTILINE | re.DOTALL,
)
NEXT_ITEM_RE = re.compile(
    r"^[ \t]*(?:[1-9][0-9]*\.|[-+*])[ \t]+(?P<text>.*)$",
    re.MULTILINE,
)
```

### helper

[_current_pin():90-102](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:90) の直後、`main()` の前へ helper を置く。

1. `_extract_worklog_entries(text)`

   - `WORKLOG_H2_RE` で H2 の開始位置を列挙する。
   - `## ローテーション` を一意に見つける。
   - それ以後の各 H2 title を `WORKLOG_ENTRY_TITLE_RE.fullmatch()` で検証する。不正 H2 を「無視」しない。
   - 各 entry body は、その H2 の末尾から次の H2 の直前、最後は EOF までで切る。
   - 戻り値は title、body、本文開始 offset。構造不成立は `None + 理由` とし、空 list と混同しない。

2. `_extract_unique_section(body, pattern)`

   - `finditer()` がちょうど1件の場合だけ body を返す。
   - 0件と2件以上は別の抽出失敗として返す。

3. `_next_action_ids(section_body, absolute_offset)`

   - `NEXT_ITEM_RE` の各 list item が正式 ID で始まることを検査する。
   - ID なし item、同一節内の ID 重複を finding 化する。
   - 行番号は `text.count("\n", 0, absolute_offset) + 1` で算出する。
   - 保存則の source ID は、単なる本文中の言及ではなく、この item 先頭 ID だけから作る。

### `main()` への挿入

現在の living-doc loop 終了直後、[tools/check_docs.py:173](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:173) に挿入する。これは既存の「次アクションの再掲」finding `:147-151` の直後に当たる。

処理順は以下。

1. worklog と phase3 の存在を検査してから読む。不在は finding、例外や暗黙の空文字にはしない。
2. 見送り台帳を常に一意抽出する。
3. worklog entry を構造抽出する。
4. 末尾 entry の「次の一手」を一意抽出し、item の ID 書式を検査する。
5. entry が2件以上なら `entries[-2]` を直前、`entries[-1]` を末尾とし、直前の「次の一手」も一意抽出する。
6. 直前 source ID がゼロなら finding。
7. `sink_ids = ID(末尾 entry body) ∪ ID(見送り台帳 body)`。
8. `source_ids - sink_ids` を数値順に並べ、ID ごとに finding を出す。

finding は例えば次で固定する。

```text
docs/worklog.md: 直前エントリの「次の一手」に有効な ID が 0 件 — 保存則検査が蒸発する
docs/worklog.md: 直前の「次の一手」ID [T-001] が末尾エントリにも docs/phase3.md「見送り台帳」にもない
docs/phase3.md: 「見送り台帳」節を一意に抽出できない (0 件) — 保存則の sink が蒸発する
```

既存の [findings 出力:227-233](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:227) にそのまま合流させる。warning 経路は作らない。

## 3. fail-closed の核心

| 状態 | 動作 |
|---|---|
| worklog 不在、ローテーション節不在、不正 H2、抽出不能 | 構造 finding。保存則だけ依存停止し、他の lint は継続。 |
| entry 0 件 | finding。「ローテーション直後」と解釈しない。 |
| entry 1 件 | 正常なローテーション直後として保存則比較だけ非適用。末尾の次の一手書式と見送り台帳抽出は実行する。 |
| entry 2 件以上 | 必ず末尾2件で保存則を発火。 |
| 直前 entry の次の一手が0件または複数抽出 | finding。source を空集合へ落とさない。 |
| 直前の source ID が0件 | finding。vacuous pass を禁止。 |
| 末尾の list item に ID がない | finding。少なくとも1件 ID がある場合でも、IDなし item を黙認しない。 |
| 見送り台帳の ID が0件 | 抽出自体が成功していれば単独では違反にしない。全 ID が末尾 entry にある状態は正当。 |
| source ID が両 sink にない | ID ごとに finding。 |
| source ID が両 sink に重複している | P3 の範囲では受理。意味的な二重状態までは判定しない。 |

不変条件2と3は、`None` を「抽出失敗」、`[]` を「正常抽出したが0件」、entry 1件を「正常な no-predecessor」と型として分けることで両立させる。特に entry 1件 branch はテストで固定し、抽出失敗時の fallback と共有しない。

## 4. テスト設計

### `_build_min_repo()` の拡張

[orchestrator/tests/test_check_docs.py:44-67](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:44) を拡張する。

- `_ENUMERATED_DOCS` の placeholder 作成後に `docs/phase3.md` を上書きし、実際の `## 見送り台帳 (...)` と `[T-900]` の合成項目を置く。
- 現状 fixture に存在しない `docs/worklog.md` を作り、既定は2 entryにする。

  - 直前の次の一手: `[T-001]`
  - 末尾本文: `[T-001] 消化`
  - 末尾の次の一手: `[T-002]`

- `_write_backlog_docs(root, worklog_text, phase3_text)` を追加し、各テストが一要因だけ差し替えられるようにする。
- `test_missing_enumerated_doc_only_fires_own_finding` の victim は、構造上必須になった `docs/phase3.md` を候補から除く。これで「削除差分 = 1 finding」の既存意図を維持する。

### 追加テスト

| 種別 | テスト関数 | 主な assert |
|---|---|---|
| 正 | `test_backlog_guard_carried_id_in_latest_next_action_is_clean` | rc=0、`"違反なし"` |
| 正 | `test_backlog_guard_consumed_id_in_latest_body_is_clean` | rc=0、`"違反なし"` |
| 正 | `test_backlog_guard_deferred_id_in_phase3_ledger_is_clean` | rc=0、`"違反なし"` |
| 正 | `test_backlog_guard_single_entry_after_rotation_is_clean` | rc=0、`"違反なし"` |
| 負 | `test_backlog_guard_dropped_id_is_violation` | rc=1、`"[T-001]"`、`"末尾エントリにも"` |
| 負 | `test_backlog_guard_previous_next_action_section_must_be_unique` | 0件/2件を個別 fixture にし、`"「次の一手」節を一意に抽出できない"` |
| 負 | `test_backlog_guard_zero_source_ids_is_violation` | rc=1、`"有効な ID が 0 件"` |
| 負 | `test_backlog_guard_idless_latest_item_is_violation` | rc=1、`"項目先頭に [T-NNN] がない"` |
| 負 | `test_backlog_guard_deferred_ledger_section_must_be_unique` | 0件/2件、`"「見送り台帳」節を一意に抽出できない"` |
| 負 | `test_backlog_guard_no_worklog_entries_is_violation` | rc=1、`"worklog エントリが 0 件"` |
| 負 | `test_backlog_guard_phase3_id_outside_ledger_does_not_satisfy` | ID を「残存リスク」へだけ置き、dropped finding を assert |
| 負 | `test_backlog_guard_unbracketed_sink_id_does_not_satisfy` | `T-001` だけでは dropped finding |
| 負 | `test_backlog_guard_duplicate_ids_in_next_action_are_violation` | rc=1、`"次の一手 ID [T-001] が重複"` |

既存7テスト `test_synthetic_repo_baseline_clean` から `test_real_repo_clean`（[test file:79-172](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:79)）は、合成 repo の新しい必須文書を baseline 側で満たすため、既存の検査意図を変えず維持できる。`test_real_repo_clean` だけは後述の二段 land 完了後に初めて新検査で clean になる。

## 5. B-057 事前登録変異

判定は pytest の赤ではなく、対象 fixture の rc、すなわち受理集合または fail-closed 挙動が変わったかで行う。

| 変異 ID | 対象 file:line | 変異内容 | 殺すテスト | 実効性・過剰決定 |
|---|---|---|---|---|
| BG-M01 | `tools/check_docs.py:173` 新設保存則 | missing 集合を常に空にする | `test_backlog_guard_dropped_id_is_violation` | 受理集合が拡大。単一理由。 |
| BG-M02 | `tools/check_docs.py:173` latest sink | 末尾 entry 全文ではなく末尾「次の一手」だけを走査 | `test_backlog_guard_consumed_id_in_latest_body_is_clean` | 正当な消化を拒否。単一理由。 |
| BG-M03 | `tools/check_docs.py:173` sink union | 見送り台帳を union から外す | `test_backlog_guard_deferred_id_in_phase3_ledger_is_clean` | 正当な見送りを拒否。単一理由。 |
| BG-M04 | `tools/check_docs.py:79` ledger regex | `(?=^## |\Z)` を外し phase3 EOF まで読む | `test_backlog_guard_phase3_id_outside_ledger_does_not_satisfy` | 受理集合が拡大。ID は台帳外だけに置き、単一理由。 |
| BG-M05 | `tools/check_docs.py:173` entry selection | source を `entries[-2]` から `entries[-1]` に変更 | `test_backlog_guard_dropped_id_is_violation` | dropped ID が検査対象外になる。fixture の他構造は正常。 |
| BG-M06 | `tools/check_docs.py:103` entry cardinality | 1 entry を違反または `[-2]` access にする | `test_backlog_guard_single_entry_after_rotation_is_clean` | 受理集合が縮小。単一理由。 |
| BG-M07 | `tools/check_docs.py:103` next-section helper | 0件抽出を finding なしの `None` として返す | `test_backlog_guard_previous_next_action_section_must_be_unique` | fail-closed が fail-open 化。比較不能時に他 finding を出さない fixture。 |
| BG-M08 | `tools/check_docs.py:173` zero-source branch | ID 0件 finding を削除 | `test_backlog_guard_zero_source_ids_is_violation` | vacuous pass へ拡大。section 本文に list itemを置かず単一理由化。 |
| BG-M09 | `tools/check_docs.py:103` item parser | latest item の先頭 ID 検査を削除 | `test_backlog_guard_idless_latest_item_is_violation` | IDなし新規項目を受理。直前 ID は本文で消化済みにして単一理由化。 |
| BG-M10 | `tools/check_docs.py:103` ledger helper | 台帳抽出失敗を空 body として扱う | `test_backlog_guard_deferred_ledger_section_must_be_unique` | fail-open 化。直前 ID は末尾にも置き、missing-ID finding が重ならない fixture。 |
| BG-M11 | `tools/check_docs.py:103` duplicate check | `set` 化だけ行い同一節内重複 finding を削除 | `test_backlog_guard_duplicate_ids_in_next_action_are_violation` | 異なる2項目の同一 ID を受理。単一理由。 |
| BG-M12 | `tools/check_docs.py:173` finding 文言 | dropped finding の文言だけ変更 | `test_backlog_guard_dropped_id_is_violation` の文字列 assert | **kill に数えない。** rc=1 と受理集合は不変。診断文字列 pin にすぎない。 |

## 6. 赤を land しない実装順序

1. **親 docs bootstrap commit**

   - worklog 書式、phase3 の T-* 併記、D69 を編集。
   - 凍結済み (15) は触らず、新規 (16) に現在の生存原子を ID 付きで記載する。
   - この時点は旧 `check_docs.py` なので、新規検査由来の赤はない。

2. **実装子がコードとテストだけを作る**

   - 編集対象は `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` のみ。
   - この変更を単独で integration branch へ land してはいけない。末尾が (16) のままだと、直前 (15) の source ID が0件として新検査が赤になる。

3. **親が新規 (17) とコードを原子的に land**

   - (17) は (16) の全 ID を本文、次の一手、または既存見送り台帳のいずれかへ残す。
   - backlog-guard 自身の ID は本文で消化、残りは継続または見送りにする。
   - 実装子の2ファイルと親の (17) を同一 integration commit にする。これで新 checker が初めて見る遷移は `(16) → (17)` となり、実データで非 vacuous に発火する。

4. **親が検収・完了文書を扱う**

   - writable 環境で追加テスト、既存全走、`tools/check_docs.py`、Codex/docs/provenance 検査を実施する。
   - handoff の吸収・削除、最終 worklog は親の権限で行う。
   - `codeのみ先行` と `bootstrap (16) + code、(17)なし` はどちらも実 repo を赤にするため禁止する。

本回答では read-only の静的実読のみ行った。pytest、`check_docs.py` とも実行しておらず、green の主張はしない。

---

## 段 3 — 敵対相談 A: 正しさ境界・恒真ゲート レンズ (逐語)

NO-GO。静的再現だけで、見送り台帳の抽出は現行実データに対して `body=""` になり、さらに保存則を通したまま項目を落とせる経路が複数ある。

## 所見

- BG-01 / `plan-v1.md:85-89`; `docs/phase3.md:386-606` / `DEFERRED_LEDGER_RE` は現行台帳を抽出できない / `DOTALL` 下の見出し suffix `(?:[ \t].*)?` が改行を越えて EOF まで貪欲に消費する。実 regex では match は line 386 から 606、`body` 開始は EOF の line 607、`len(body)=0`。したがって台帳 ID は常に0件に見え、`deferred_id...is_clean` は正例にならず、括弧付き台帳を2個置いても1 matchとして飲み込む / 致命的

- BG-02 / `plan-v1.md:43-47,55-66` / 採番の自己汚染を正規表現だけでは防げない / 採番は worklog 全文と archive 全文を走査する一方、「ID-like token」の抽出 regex が未定義。追記予定の `[T-NNN]` は正式 regex に full-match しないため、広く拾えば採番が永久停止し、数字だけ拾えば例示 `[T-999]` を実 ID と区別できず最大値を999へ汚染する。worklog 書式節の有効例示は max に混ざるが、これを文脈で除外する設計がない / 高

- BG-03 / `plan-v1.md:151,160`; `brief.md:22-26` / entry 1件を正常扱いする分岐はローテーション境界の脱落経路になる / `[T-001]` を持つ直前 entry を archive へ移し、現行 worklog に `[T-002]` だけを持つ新 entry 1件を残す。計画どおりなら「正常な no-predecessor」として比較を省略し、`[T-001]` は消化・継続・見送りなしで消える。archive は保存則対象外なので復元不能 / 致命的

- BG-04 / `plan-v1.md:130-133` / 末尾2件しか比較しないため、2 entryを一度に追加すれば古い source を飛び越せる / E0 の次の一手を `[T-001]`、同時追加する E1 を `[T-002]` のみ、E2 を `[T-002]` 継続とする。checker は E1→E2 だけを見て通り、E0→E1 で落ちた `[T-001]` を見ない。各セッションで必ず検査するという運用規律に依存し、機械保存則ではない / 致命的

- BG-05 / `brief.md:5,38-39`; `plan-v1.md:17,132` / brief の「消化・継続・理由付き見送りだけを通す」と P3 の token-presence は両立しない / 末尾本文へ `<!-- [T-001] -->`、コード例、または「今回は `[T-001]` を落とした」と書くだけで sink に入る。消化も継続も理由付き見送りもなく受理される。plan は保証を保存則へ格下げしたが、それは brief の目的未達を明記しただけで、穴を塞いでいない / 致命的

- BG-06 / `plan-v1.md:39,113-118,132`; `docs/worklog.md:652-665` / 「1原子=1 ID」は機械検査されず、IDを1遷移だけ本文へ出して洗浄できる / E0 に `[T-001] A` と `[T-002] B`、E1 の1項目を `[T-001] A+B（旧 [T-002] を統合）`、E2 を `[T-001]` のみにする。E0→E1 は全文 sink 中の `[T-002]` で通り、E1→E2 の source は項目先頭の `[T-001]` だけなので `[T-002]` が消える。実際、現行 (15) は regex 上4項目なのに plan は自然言語解釈で12原子としている / 致命的

- BG-07 / `plan-v1.md:64-66,127,132,156`; `docs/phase3.md:388-390` / 台帳の ID 完備性・項目先頭・理由を検査しない / 現存する生存台帳項目を一件も T-ID 化しなくても、直前 source が末尾本文にあれば green になり得る。台帳へ `- [T-001]` と理由なしで置く、または台帳前書きへ token を置くだけでも sink を満たす。「台帳 ID 0件を単独では違反にしない」は保存則自体を恒真化しないが、台帳 bootstrap と理由付き見送りの保証を完全に外している / 高

- BG-08 / `plan-v1.md:90-93`; `docs/worklog.md:652-665` / `NEXT_ITEM_RE` はインデント深度を無視して過剰・過少マッチする / 実データでは89行を項目、55行を継続行として認識し、インデントされた継続行の誤マッチは0件だった。しかし `   - 補足` は別項目として誤検出し、現行の `   (a)…(f)` のような原子列は完全に無視する。平坦化は prose 規律だけで、同じ隠れ原子形式への回帰を止めない / 中

- BG-09 / `plan-v1.md:147-160,178-195`; `orchestrator/tests/test_check_docs.py:79-172` / fail-closed 表の主要分岐に positive control も変異もない / worklog 不在、ローテーション0件・複数件、不正H2、末尾「次の一手」0件・複数件、phase3 不在が追加テストにない。現行の generic missing-doc テストの実 victim は `docs/glossary.md` と `.codex/agents/README.md` で、phase3 不在経路を通らない。これらの分岐を `skip` 化しても表の変異群は殺せない / 高

- BG-10 / `plan-v1.md:168,184,190,206-213` / 変異表には等価・未注入・元 fixture 不成立がある / BG-M03 の正例は BG-01 により元実装から赤。BG-M04 は lookahead を単に外すと lazy `.*?` が空 body を返し、主張する「EOFまで読む」変異にならない。実際、括弧付き2台帳の合成文字列では元 regex と lookahead 削除版がともに1 match・空 bodyだった。BG-M10 の2件 fixture も元 regex が2件を識別しない。さらに exact patch、注入確認、HALT 検出、復元確認が計画されていない / 高

- BG-11 / `brief.md:47`; `plan-v1.md:215` / 受入条件「事前登録変異の全 kill」と BG-M12 が矛盾する / BG-M12 は診断文言だけを変え、受理集合も fail-closed 挙動も変えず、plan 自身が「kill に数えない」とする。ならば M12 は事前登録変異から外して診断 pin と分類しなければ、brief の受入条件は定義上達成不能 / 中

- BG-12 / `brief.md:25-26`; `plan-v1.md:45-46` / brief の「現存 ID から max+1」と「archive は対象外」はローテーション後に両立しない / 最大 ID が消化済みで archive にしか残らない場合、archive を除外すれば再利用が起きる。plan は archive を採番母集団へ入れて片方を破ったが、今度は凍結 archive 内の例示・不正 token が新規採番を阻止する / 高

- BG-13 / `brief.md:32`; `plan-v1.md:8`; `docs/phase3.md:394-455` / 「45件」の対象集合は確定しておらず、plan の状態分類も不十分 / 指定範囲には B-ID 付きトップレベル項目が正確に48行ある。B-008/B-009 は取消線付きだが B-008 には line 400 の再試験 tail がある。B-056 は「safety gate changed」、B-057 は「validator or rejection gate changed」が発火条件であり、本 wave は双方の再評価対象になる。B-057 だけを再発火扱いして3件を除外する根拠はない / 高

- BG-14 / `brief.md:30-33`; `docs/handoff/2026-07-19-backlog-guard-mechanism.md:23-26` / brief の P1 は設計正本と guard 自身の sink 契約に反する / handoff は見送り台帳にも同じ ID 体系を使い、生存台帳分へ初回 ID を振ると明記する。B-IDだけでは T-ID保存則の sink になれない。Bを残してTを併記すれば既存B参照は変更されず、「相互参照 churn」も根拠にならない / 高

## 保存則を通す具体的回避手順

1. 本文 token 洗浄: E0 の `[T-001]` を E1 の HTML commentや「落とした」という文章へ一度だけ書き、E1 の次の一手から除く。E0→E1は通り、E2で完全に消せる。
2. ID統合: `[T-001] A` と `[T-002] B` を、E1で `[T-001] A+B（旧 [T-002]）` の1項目へ統合する。次遷移の source は `[T-001]` だけになる。
3. ID再利用: E0 の `[T-001] A` に対し、E1で同じ `[T-001]` を無関係な C に付ける。token保存は成立するが A は消える。
4. 理由なし台帳: 台帳内へ `- [T-001]` または単なる prose mention を置く。理由検査がないため受理される。
5. ローテーション: source entryをarchiveへ移し、現行worklogを新entry 1件だけにする。比較自体が非適用になる。
6. 二段飛ばし: 一度の検査前に2 entry追加し、脱落を最初の遷移へ置く。末尾2件の比較から外れる。

したがって、この設計が保証するのは「現スナップショットで、末尾から2番目の認識可能な list-head ID 集合が、末尾全文または regex 抽出台帳に token として含まれること」だけである。項目の意味、原子性、消化、理由、IDの不変性・非再利用、全遷移、ローテーション境界、台帳の完備性は保証しない。

## 攻撃が失敗した点

- worklog 実構造: ローテーション後H2は24/24が `WORKLOG_ENTRY_TITLE_RE` に full-matchし、`## ローテーション` は1件、各entryの `### 次の一手` も各1件だった。
- 現行継続行: 55本の非空継続行に `NEXT_ITEM_RE` の誤マッチはなく、現リポジトリをこれだけで赤にはしない。
- ID regex境界: `[T-001]`〜`[T-1000]` は意図どおり有効で、`[T-000]`、`[T-01]`、`[T-0001]`、裸の `T-001` は無効だった。
- 初回採番: 現 worklog、4 archive、実台帳の正式 T-ID は合計0件であり、現時点だけなら `T-001` 開始は正しい。
- D番号: 最大見出しは D68で、次をD69とする導出は正しい。
- D69の例示: decisions.md は計画上の採番母集団・source・sinkの外なので、D69内の例示だけでは自己汚染しない。
- P1否認: handoffの明文により plan 側の否認が正しい。
- P2否認: `docs/worklog.md:14` は過去entry凍結を明記しており、(15)を触らない判断が正しい。
- 台帳ID 0件単独: 非空 source が末尾にも台帳にもなければ差集合は残るため、これだけで保存則全体は恒真化しない。
- BG-M05: dropped fixtureで source を latestへ変えると latest自身の `[T-002]` が全文 sink に必ず存在し、missing findingだけが消えるため単一理由になる。
- BG-M07: 0節 fixtureを list itemなし・他構造正常に限定し、callerも `None` を黙って skipする実装なら単一理由になる。ただし2節 fail-open変異は別途必要。
- BG-M10: 台帳0節 fixtureだけなら、直前IDを末尾本文に置くことで構造findingだけにできる。2節 fixtureはBG-01のため成立しない。

pytest および `check_docs.py` 本体は実行していない。以上は全て読み取り専用の実ファイル走査と、記載された正規表現そのものの静的再現による。

---

## 段 3 — 敵対相談 B: 既存規律との整合・実行可能性 レンズ (逐語)

判定は **NO-GO**。静的検査のみであり、pytest / `check_docs.py` は実行していない。

## 所見

- **R-01** / [plan-v1.md:217](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:217>)、[CLAUDE.md:154](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/CLAUDE.md:154)、[handoff/README.md:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/README.md:12)、[backlog-guard handoff:33](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/2026-07-19-backlog-guard-mechanism.md:33) / **(16) と (17) を書く二段 land は既存運用と両立しない** / 同一セッションなら (16) は作業中の worklog 追記となり、「作業中は追記せず、正常終了時に1回だけ吸収」に違反する。セッションを分けても、bootstrap 時点では handoff の作業が未完なので正常終了・吸収・削除できない。設計 handoff 自身も「完了検査後、worklog 1 エントリに吸収」と明記している / **Critical**

- **R-02** / [plan-v1.md:219](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:219>)、[docs/worklog.md:652](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:652) / **「初回の非 vacuous 発火」という主張が検査対象を取り違えている** / 新 checker が初めて見るのは `(16)→(17)` であり、既存 `(15)→(16)` の移行ではない。(15) は Markdown 上4項目、plan の意味分解では12原子だが、(16) への転記漏れを機械検査する対応表がない。bootstrap 時に1原子を落としても、その欠落済み (16) を source にした検査は通る / **High**

- **R-03** / [plan-v1.md:85](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:85>)、[docs/phase3.md:386](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:386)、[docs/phase3.md:457](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:457)、[docs/phase3.md:498](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:498) / **`DEFERRED_LEDGER_RE` が terminal 記録まで sink に含める** / 正規表現は次の H2 まで読むため、H3 `### 裁定・完了記録` も capture する。将来 T-ID が完了記録に残ると、その古いトークンが同 ID の脱落を永久に満たす。終端を `### 裁定・完了記録` にするか、live ledger を別 H2 に分離しなければ保存則は fail-open / **Critical**

- **R-04** / [brief.md:30](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/brief.md:30>)、[plan-v1.md:8](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:8>)、[docs/phase3.md:394](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:394) / **brief の「45件」に根拠がなく、plan の「生存項目だけ採番」も実行不能** / 394–455行には B-ID 付き箇条書きが48行ある。B-008/B-009 は取り消し線付きだが再発条件を残す。B-056/B-057 は「消化」履歴付きでも現在形の再発述語を持つ。B-015 も「終了」と再評価条件が同居する。現行台帳に machine-readable な `live|terminal` 状態はなく、凍結 insight は `authority: none` で現在状態の正本ではない。したがって対象集合は **不明**。親が D69 で3件を推測除外してはならない / **High**

- **R-05** / [brief.md:51](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/brief.md:51>)、[plan-v1.md:225](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:225>)、[CLAUDE.md:22](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/CLAUDE.md:22)、[AGENTS.md:23](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/AGENTS.md:23) / **実装子の「2ファイルだけ」所有は通常 Codex 子の規律と衝突する** / コードを変更する子はクラス2/3であり、専用 handoff・セッション末の worklog・関連検査が必要。一方 brief は docs 全面を禁止している。read-only projected role なら例外だがコード編集はできない。親を唯一の実装セッションとし、子は read-only のパッチ提案者にするか、所有契約の再設計が必要 / **High**

- **R-06** / [plan-v1.md:113](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:113>)、[plan-v1.md:225](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:225>)、[test_check_docs.py:165](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:165) / **「意図的赤」の期待結果と検収契約がない** / 計画どおり同じ `_next_action_ids()` を直前 (15) に使うと、IDなし top-level 項目は 654・657・663・664行の4件。これに source ID=0 finding が加わり、少なくとも5 finding になる。plan はゼロ件 finding だけを説明しており、実装子の赤が期待差分か別回帰かを親が判別できない / **High**

- **R-07** / [plan-v1.md:49](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:49>)、[plan-v1.md:58](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:58>) / **「IDは変更しない」と「未 land 側を振り直す」の境界が未定義** / worklog 本文や phase 台帳へ書いた時点、feature branch commit 時点、integration branch への merge 時点のどれを「付与」「land」とするかがない。両分岐が既に commit 済みなら、一方の frozen worklog を書き換えない限り衝突解消できない。integration の直列化もない / **High**

- **R-08** / [plan-v1.md:115](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:115>)、[plan-v1.md:132](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:132>)、[plan-v1.md:164](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:164>) / **phase3 の初回 ID 付与を検証する歯がない** / 先頭ID・重複検査は worklog の「次の一手」だけ。台帳48行の一部に ID を付け忘れる、同じ ID を複数行へ貼る、無効形式を置く、といった初回移行ミスは source にならない限り finding にならない / **Medium**

- **R-09** / [plan-v1.md:147](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:147>)、[plan-v1.md:180](</home/SFC/tanab/.claude/jobs/9b2bec65/tmp/wave-backlog-guard/plan-v1.md:180>) / **宣言した fail-closed 構造分岐に positive control がない** / 追加テストに worklog 不在、ローテーション節不在、不正 H2、末尾「次の一手」0/2件、列挙した無効 ID 形式の検査がない。`no_worklog_entries` は「ファイル不在」「ローテーション不在」と別経路であり、brief の恒真ゲート禁止を固定できない / **High**

## 1 worklog エントリでの代替

単一 integration commit にコード・テスト・D69・phase3・新規 (16) をまとめる。その (16) に一度だけ使える `### ID 導入元` を置く。

1. 導入元には、(15) の4つの top-level list block を ID 付きで完全複写する。
2. checker は ID を除いた block が (15) と一対一・完全一致することを検査する。
3. 導入元 ID を初回 source とするが、導入元節そのものは latest sink の走査対象から除外する。
4. (16) 本文・次の一手・live ledger のいずれかに全 source ID を要求する。
5. 4つの複合項目を12原子へ分けるなら、本文で親 ID を消化し、新しい子 ID との split 対応を記録する。
6. bootstrap 節は「過去 worklog に正式 ID が0件」の一度だけ許し、再出現を finding にする。

これなら `(15)→(16)` が非空 source で検査され、worklog 更新・handoff 吸収も1回で済む。

この特例を入れない最後の手段は、(15) の source=0 を一度だけ許容する migration marker 方式。その場合、失うものは「既存 (15) からの脱落を実データで検査した証拠」と「導入 commit で保存則が実発火した証拠」であり、保証開始は次回 `(16)→(17)` まで遅れる。

## 既存7テストの静的照合

`_enumerated_rels()` の現行 sorted 順は次の19件。

```text
 0 .codex/agents/README.md
 1 AGENTS.md
 2 CLAUDE.md
 3 README.md
 4 docs/README.md
 5 docs/agent-architecture.md
 6 docs/ai-provenance.md
 7 docs/axis-onboarding.md
 8 docs/ccbench-anatomy.md
 9 docs/glossary.md
10 docs/isolation-phenomena.md
11 docs/orchestrator-design.md
12 docs/phase3-8b-descriptor-design.md
13 docs/phase3-main-experiment.md
14 docs/phase3.md
15 docs/related-work/README.md
16 docs/roadmap.md
17 output/README.md
18 output/task-runs/README.md
```

したがって、

- `rels[0]` = `.codex/agents/README.md`
- `rels[len(rels)//2]` = `docs/glossary.md`

どちらも `docs/phase3.md` ではない。「phase3 を victim 候補から除く」は現状の victim 選択には何も効いていない。ただし合成 repo に有効な worklog と phase3 ledger を追加すれば、`.codex/agents/README.md` 削除時の「ちょうど1 finding」は静的には維持可能。phase3 除外は将来 phase3 が victim になった際の二重 finding 回避策にすぎない。

## 意図的赤を残す場合の最低限の検収手順

現行案を維持するなら、次を明文化しない限り受け入れ不能。

1. 実装子は「green」と言わず、synthetic tests と `test_real_repo_clean` を分けて報告する。
2. 中間状態では、失敗 test が `test_real_repo_clean` だけであることを報告する。
3. 内側の `check_docs.py` finding は、上記4件の IDなし項目＋source ID=0 の期待集合と完全一致させる。追加 finding は回帰扱い。
4. 親は子の2ファイル diff を検査後、(17) を未コミット状態で加え、同じ test と `check_docs.py` を再検収する。
5. その後に全走・Codex/docs/provenance 検査を実行する。ここで初めて受入判定を行う。

ただしこれは R-01/R-05 の規律衝突を解消しない。

## 採番競合時の実手順

実行可能にするには「landed = integration target に入った時」と定義し、それ以前は provisional と明記する必要がある。

1. integration を直列化し、最新 target へ rebase。
2. authority 群を再走査し、最大 ID と不正形式を確認。
3. 未 land diff が導入した ID だけを文書順に列挙し、旧→新の一対一写像を作る。
4. worklog 本文・次の一手・phase3・B→T 対応・handoff 内の参照を exact token で一括更新する。合成テストの固定 ID は対象外。
5. 旧 provisional ID の残存、target ID との衝突、live ledger 内重複を再走査。
6. 関連検査後、同じ integration 操作で land。

既に integration target に入った ID、または frozen entry 内の ID は振り直せない。その競合は手順で修復するのでなく、integration の直列化で予防するしかない。

## 攻撃不成立だった点

- **P1 否認:** handoff 23–26行は「台帳にも同体系」「生存した台帳保留分にも最初の ID」と明記しているため、brief の読み替えは成立しない。plan の否認が正しい。
- **P2 否認:** worklog 14行は既存エントリ凍結と新規エントリ適用を明記しており、(15) の遡及編集は不可。plan の否認が正しい。
- **正式 T-ID 0件:** worklog・archive worklog・phase3 の静的検索で該当なし。`T-001` 開始の前提は正しい。
- **D69 採番:** D 見出し最大は D68。D69 は正しい。
- **既存 lint:** `[T-NNN]` 自体は D参照・パス参照・pin literal・行番号参照のいずれにも一致しない。D69 は LIVING_DOCS 外で、phase3 から D69 を参照しても同一 commit に見出しがあれば既存 lint 経路は発火しない。
- **worklog rotation:** 現在55,607 bytesで閾値100,000 bytes未満。今回の追記だけを理由とする rotation 発火は見込めない。

---

## 段 4 — 親の裁定 + プラン v2 (逐語)

# 親の裁定 + プラン v2 (段 4)

相談 A 14 所見 / 相談 B 9 所見 = 23 所見。**real 23 / refuted 0。** うち **3 件は親 brief 自身の誤り**
(P1・P2・「45 件」)。BG-01 は親の独立 probe と一致し二重に確定。

## 裁定表

| 所見 | 判定 | 処置 |
|---|---|---|
| BG-01 / 親 probe | real 致命 | **実装で修正。** 台帳 regex の見出し部を `[^\n]*` にする (DOTALL で改行を食う) |
| R-03 | real 致命 | **実装で修正。** 台帳 sink を `### 裁定・完了記録` の手前までに限定 (完了記録の古い ID が永久 sink 化するのを防ぐ) |
| BG-03 | real 致命 | **実装で修正。** archive の最新 worklog 末尾エントリ → 現行先頭エントリ の遷移も検査する |
| BG-04 | real 致命 | **実装で修正。** 末尾 2 件でなく**現行 worklog の全隣接遷移**を検査する |
| BG-05 / BG-06 | real 致命 | **実装で修正。** sink を「トップレベル list item の**先頭** ID」に限定 (本文散在 token・HTML コメント・prose 言及では満たせない) |
| R-01 | real 致命 | **プランの二段 land を否認。** worklog は 1 エントリ。親が docs を先に書き patch 展開してから実装子を起動する |
| R-02 | real 高 | **限界として受け入れ、D69 に明記。** (15)→(16) の転記は人手であり機械検査しない。保存則は (16) 以降を守る |
| R-06 | real 高 | **消滅。** 親が docs を先に land する順序変更により実装子は緑を目指せる。「意図的赤」を作らない |
| BG-09 / R-09 | real 高 | **実装で修正。** fail-closed 全分岐に positive control を置く |
| BG-02 | real 高 | **実装で修正。** 採番母集団から worklog 冒頭 (`## ローテーション` より前) を除外。例示は `[T-NNN]` 形式で書き有効 ID を書かない |
| BG-12 | real 高 | **実装で修正。** archive も採番母集団に含める (再利用防止)。archive 内の不正形式 token は無視する (現状 0 件) |
| BG-07 / R-08 | real 高 | **実装で修正。** 台帳の ID も形式検査・重複検査の対象にする |
| BG-11 | real 中 | **採用。** BG-M12 を事前登録変異から外し「診断 pin」に分類する |
| BG-08 | real 中 | **部分修正 + 限界明記。** source/sink はトップレベル list item のみ。インデント項目は原子として扱わない |
| BG-13 / R-04 | real 高 | **親が実読して確定する。** 推測除外はしない (下記「対象集合」) |
| BG-10 | real 高 | **採用。** 変異は exact patch + 注入確認 + HALT + 復元確認を必須にする。BG-M03/M04/M10 は再設計 |
| R-05 | real 高 | **scope 外 → 裁定パッケージ。** 実装子の権限境界と AGENTS.md クラス 2/3 規律の衝突は /dev-wave 全体の設計問題 |
| R-07 | real 高 | **簡素化して採用。** 採番は親が統合直前に 1 回だけ行う。実装子は発番しない。`landed` = main 統合時点と D69 で定義 |

## 確定設計 (プラン v2)

**ID**: `\[T-(?:0*[1-9][0-9]*)\]` を 3 桁 0 埋め以上に限定 → `[T-001]` 〜。トップレベル list item
(インデント無し `1. ` / `- `) の**先頭**に置く。

**source**: 各 worklog エントリの `### 次の一手` 節の**トップレベル list item 先頭 ID**。
**sink**: 後続エントリ全体の**トップレベル list item 先頭 ID** ∪ 見送り台帳
(`## 見送り台帳` 〜 `### 裁定・完了記録` の手前) の**トップレベル list item 先頭 ID**。

**保存則**: 全隣接遷移 E(i)→E(i+1) で `source(E(i)) ⊆ sink(E(i+1)) ∪ sink(台帳)`。
archive 最新ファイルの末尾エントリ → 現行先頭エントリ も 1 遷移として検査。
`source` が空の遷移は非適用 (ID 導入前の遷移が自然に抜ける)。

**fail-closed (全て finding、警告水準は作らない)**:
- worklog / phase3 不在、`## ローテーション` が 0 件または複数、H2 が entry title に full-match しない
- `### 次の一手` が 0 件または複数、見送り台帳節が 0 件または複数、`### 裁定・完了記録` が 0 件または複数
- **現行 worklog に有効 ID を持つエントリが 1 件も無い** (検査の蒸発)
- 末尾エントリの `### 次の一手` のトップレベル項目に ID が無い / 同一節内で ID 重複
- 台帳のトップレベル項目の ID が不正形式 / 台帳内で ID 重複

**採番**: 母集団 = 現行 worklog (`## ローテーション` 以降) + archive worklog + 台帳。max+1。

## D69 に明記する限界 (保証しないこと)

1. **ID 再利用**: 同じ ID を無関係な項目へ付け替えると token は保存されるが内容は消える
2. **意味的な「消化」判定**: 項目先頭に ID があれば受理する。理由の妥当性は検査しない
3. **原子性**: 1 項目に複数原子を詰める回帰は規約でのみ防ぐ (BG-08)
4. **台帳の理由記載**: 検査しない
5. **(15)→(16) の転記**: 導入時点の人手作業であり機械検査しない (R-02)

## 対象集合 (親が実読して確定)

親 probe 実測: 台帳の `- ` 箇条書き **58 行** / `(B-\d+,` キー **50** / 取り消し線 **2** (B-008・B-009) /
「(完了」始まり **6**。**brief の「45 件」もプランの「48 行」も誤り。** 生存 = 5 節
(正しさ・防壁系 / 研究・計測系 / プロセス文書系 / 外部環境系 / テスト衛生) の取り消し線なし項目。
`### 裁定・完了記録` 節は sink 範囲外なので ID を振らない。

## 実装順序 (R-01/R-06 解消版)

1. **親** が docs を書く: worklog 冒頭 書式節 / 台帳 ID 付与 / D69 / 新規エントリ (16) の次の一手 ID
2. **親** が docs 限定 patch を作り、実装子 worktree へ展開
3. **実装子** が `tools/check_docs.py` + `orchestrator/tests/test_check_docs.py` のみ編集。**緑を目指せる**
4. **親** が統合 → 全走 → 変異 matrix → commit (worklog エントリは 1 本)

---

## 段 4 — 事前登録変異 (B-057、実装前に凍結)

# 事前登録変異 (B-057) — backlog-guard wave

**凍結時刻: 実装子の起動後・成果物の受領前。** 実装コードを見ずに、裁定 (ruling-v2.md「確定設計」) の
機能単位で登録する。file:line は実装受領後に確定する (登録内容は変更しない)。

## 判定基準 (/dev-wave 段 6)

**kill = 「受理集合または fail-closed 挙動が期待方向へ変わった」。** 「テストが赤くなった」ではない。
診断文字列だけが変わって赤くなる変異は帰属不成立として数えない。
kill を数える前に、対象 fixture が**単一理由**で赤くなるか (他の独立条件でも赤くならないか) を確認し、
過剰決定なら fixture を単一理由へ差し替えるか、当該条件を冗長ゲートと明記して単独変異の証拠から外す。

## ハーネス要件 (敵対相談 BG-10)

1. **exact patch**: 置換対象文字列が **1 箇所でなければ HALT** (0 箇所 = 未注入、2 箇所以上 = 曖昧)
2. **注入確認**: patch 適用後にファイル内容が実際に変わったことを検査してから実行する
3. **HALT を緑と誤報しない**: 未注入を「変異が殺された」と数えない
4. **復元確認**: 各変異後に原状復帰し、baseline が再び緑になることを確認する

## 登録した変異 (14 件、診断 pin = 0 件)

| ID | 対象機能 | 変異内容 | 期待 kill テスト | 挙動の変化 |
|---|---|---|---|---|
| BG-M01 | 保存則の差集合 | missing 集合を常に空にする | 保存則の負例群 | 受理集合が拡大 |
| BG-M02 | sink (後続エントリ) | sink を後続エントリ全体でなく `### 次の一手` 節だけにする | 消化の正例 | 受理集合が縮小 |
| BG-M03 | sink (台帳) | sink から見送り台帳を外す | 見送りの正例 | 受理集合が縮小 |
| BG-M04 | 台帳 sink の終端 | `### 裁定・完了記録` の手前で切るのをやめ台帳末尾まで含める | 「完了記録にしか ID が無い」負例 | 受理集合が拡大 (fail-open) |
| BG-M05 | 全隣接遷移 | 全遷移でなく末尾 2 件だけの比較に戻す | 「2 エントリを一度に足して飛ばす」負例 | 受理集合が拡大 |
| BG-M06 | archive 境界 | archive 最新末尾 → 現行先頭 の遷移検査を外す | ローテーション境界の負例 | 受理集合が拡大 |
| BG-M07 | 項目先頭 ID | sink 判定を「項目先頭」から「行内どこでも」に緩める | prose / HTML コメント洗浄の負例 | 受理集合が拡大 |
| BG-M08 | 有効 ID 0 件検査 | 「現行 worklog に有効 ID を持つエントリが 0 件」finding を削除 | 恒真化の positive control | 受理集合が拡大 |
| BG-M09 | 節抽出 fail-closed (0 件) | 節 0 件を finding でなく空 body 扱いにする | 節 0 件の positive control | fail-closed → fail-open |
| BG-M10 | 節抽出 fail-closed (複数) | 節 2 件以上を「先頭を採用」にする | 節複数件の positive control | fail-closed → fail-open |
| BG-M11 | 末尾項目の ID 必須 | 末尾エントリの「ID 無し項目」finding を削除 | ID 無し項目の positive control | 受理集合が拡大 |
| BG-M12 | 節内 ID 重複検査 | 重複 finding を削除 | ID 重複の positive control | 受理集合が拡大 |
| BG-M13 | 台帳 regex 見出し | 見出し行を `[^\n]*` から `(?:[ \t].*)?` へ戻す (**実際に見つかった DOTALL バグの再導入**) | 見送りの正例 | 受理集合が縮小 (body 空で sink 消失) |
| BG-M14 | source の範囲 | source を `### 次の一手` 節でなくエントリ全体にする | 消化・本文 ID を含む正例 | 受理集合が縮小 (誤検出増) |

## 事前の過剰決定リスク宣言

- **BG-M02 と BG-M14 は対称**であり、同じ fixture が両方で赤くなる可能性がある。
  実測時に「消化の正例」fixture が単一理由か確認し、必要なら fixture を分離する
- **BG-M09 と BG-M10** は同じ helper を触るため、fixture が相互に赤くなりうる。
  0 件用と複数件用の fixture を**別々に**用意し、それぞれ他方の条件を満たさない構成にする
- **BG-M04 と BG-M13** はどちらも台帳 sink を壊すが、方向が逆 (拡大 / 縮小) なので分離できるはず。
  実測で確認する

---

## 段 5 — 実装子の完了報告 (逐語)

実装完了です。編集は指定された次の2ファイルだけで、docs 編集・git 操作は行っていません。

- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/impl-backlog-guard/tools/check_docs.py)
- [orchestrator/tests/test_check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/impl-backlog-guard/orchestrator/tests/test_check_docs.py)

現行全隣接遷移、最新 archive→現行先頭、台帳 sink、トップレベル項目先頭 ID、全 fail-closed 分岐を実装しました。

## 実行結果

- `python3 -m py_compile tools/check_docs.py orchestrator/tests/test_check_docs.py`
  - 対象: 変更した2ファイルの構文検査
  - rc=0

- `python3 -m pytest orchestrator/tests/test_check_docs.py -q -k 'not test_real_repo_clean'`
  - 対象: 指定テストファイルのうち実 repo clean 検査を除く合成テスト
  - `31 passed, 1 deselected`

- `python3 -m pytest orchestrator/tests/test_check_docs.py -q`
  - 対象: `orchestrator/tests/test_check_docs.py` 全体
  - `31 passed, 1 failed`
  - 失敗は意図された `test_real_repo_clean` のみ。内訳は期待どおり5 findingsです。

- `python3 tools/check_docs.py`
  - 対象: 実 repo 全体の docs lint
  - rc=1、5 findings

出力全文:

```text
check_docs: 5 件の違反
  - docs/worklog.md: 現行 worklog に有効 ID を持つエントリが 1 件もない — 保存則検査が蒸発している
  - docs/worklog.md:654: 末尾エントリの `### 次の一手` の トップレベル項目先頭に有効な [T-NNN] ID がない
  - docs/worklog.md:657: 末尾エントリの `### 次の一手` の トップレベル項目先頭に有効な [T-NNN] ID がない
  - docs/worklog.md:663: 末尾エントリの `### 次の一手` の トップレベル項目先頭に有効な [T-NNN] ID がない
  - docs/worklog.md:664: 末尾エントリの `### 次の一手` の トップレベル項目先頭に有効な [T-NNN] ID がない
```

指定された期待5件と完全一致し、追加 finding はありません。

## 追加テスト

`_build_min_repo()` は、保存則を満たす2エントリの worklog と、見送り台帳・完了記録を持つ phase3 を生成する clean baseline に変更しました。

- `test_backlog_guard_missing_worklog_is_violation` — worklog 不在を finding 化。
- `test_backlog_guard_missing_phase3_is_violation` — phase3 不在を finding 化。
- `test_backlog_guard_rotation_heading_must_be_unique` — ローテーション0件・複数件を拒否。
- `test_backlog_guard_entry_title_must_fullmatch` — 不正なH2 entry titleを拒否。
- `test_backlog_guard_zero_entries_is_violation` — entry 0件による検査蒸発を拒否。
- `test_backlog_guard_next_action_section_must_be_unique` — 次の一手0件・複数件を拒否。
- `test_backlog_guard_deferred_ledger_section_must_be_unique` — 見送り台帳0件・複数件を拒否。
- `test_backlog_guard_completion_record_section_must_be_unique` — 完了記録0件・複数件を拒否。
- `test_backlog_guard_completion_record_must_follow_ledger` — 台帳と完了記録の逆転を拒否。
- `test_backlog_guard_zero_entries_with_valid_ids_is_violation` — 有効IDを持つ現行entry 0件を拒否。
- `test_backlog_guard_latest_item_requires_id` — 末尾トップレベル項目のID欠落を拒否。
- `test_backlog_guard_latest_next_action_rejects_duplicate_ids` — 末尾節内ID重複を拒否。
- `test_backlog_guard_ledger_rejects_invalid_id_format` — 台帳先頭の不正ID形式を拒否。
- `test_backlog_guard_ledger_rejects_duplicate_ids` — 台帳内ID重複を拒否。
- `test_backlog_guard_carried_id_in_next_action_is_clean` — 後続の次の一手への継続を受理。
- `test_backlog_guard_consumed_id_in_body_is_clean` — 後続本文での消化を受理。
- `test_backlog_guard_deferred_id_in_ledger_is_clean` — 見送り台帳への移動を受理。
- `test_backlog_guard_pre_id_transition_is_not_applicable` — source空の導入前遷移を非適用化。
- `test_backlog_guard_dropped_id_is_violation` — ID消失を実際に赤くする。
- `test_backlog_guard_prose_and_html_comment_do_not_satisfy_sink` — prose・HTMLコメント中だけのIDをsinkにしない。
- `test_backlog_guard_completion_record_does_not_satisfy_sink` — 完了記録中だけのIDをsinkにしない。
- `test_backlog_guard_checks_all_adjacent_transitions` — 3 entryで古い脱落を飛ばせないことを固定。
- `test_backlog_guard_checks_latest_archive_rotation_boundary` — archive末尾→現行先頭の脱落を検出。
- `test_backlog_guard_latest_archive_is_selected_by_entry_date` — archive最新判定がファイル名でなくentry日付であることを固定。
- `test_backlog_guard_latest_archive_structure_is_fail_closed` — 最新archiveのentry/次の一手抽出失敗を拒否。

既存テストは削除・弱化・skip化していません。

## 解釈上の留意点

- IDは裁定記載の正規表現に「数字部3桁以上」を重ねています。このため `[T-001]`、`[T-1000]` に加え、正規表現上は `[T-0001]` も有効です。「canonical表記だけ」を意図していた場合は追加裁定が必要です。
- 最新archiveは、各archive内のH2 entry日付の最大値で決定し、同日だけファイル名で決定的にtie-breakします。mtimeや単純なファイル名辞書順は使っていません。
- `max+1` の実採番は親が行うdocs統合作業と解釈し、read-only lint自身には発番機能を設けていません。

意図的な赤は `test_real_repo_clean` 1件だけで、その原因は上記5 findingsちょうどです。

---

## 段 6 — 敵対レビュー A: 正しさ境界・恒真化 レンズ (逐語)

判定は **NO-GO**。保存則を通して項目を消す経路が複数残り、実データ上は保存則の適用遷移がまだ 0 件である。

## 所見

- BG-R01 / [tools/check_docs.py:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:86), [test_check_docs.py:465](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:465) / Markdown の fenced code・複数行 HTML comment 内の list 行が sink になるため、本文 token 洗浄は塞がっていない / E0 の次の一手を `[T-001] A`、E1 本文を ```` ```md\n- [T-001] A を落とした\n``` ````、E1 の次の一手を `[T-002] B` とする。raw regex は fence を認識せず `- [T-001]` をトップレベル sink と数えるため E0→E1 は通り、E2 で完全消去できる。`<!--\n- [T-001]\n-->` も同じ。追加テストは単一行 comment と通常 prose しか置いていない / 致命

- BG-R02 / [tools/check_docs.py:318](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:318), [tools/check_docs.py:326](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:326), [tools/check_docs.py:353](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:353), [test_check_docs.py:440](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:440) / 導入後の過去 source から ID を消すと「導入前」と区別できず、遷移全体を skip できる / ID 必須・重複検査は末尾エントリだけ。E16→E17 導入後に E16 の `[T-001] A` を `A` へ変更し、E17 から A を落とすと E16 の `source_ids` は空になり 353–354 行で非適用になる。E17 に別の有効 ID があれば `any(sources)` も通る。`test_backlog_guard_pre_id_transition_is_not_applicable` はこの状態を正例として固定している / 致命

- BG-R03 / [tools/check_docs.py:368](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:368), [tools/check_docs.py:390](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:390), [test_check_docs.py:522](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:522) / ローテーション検査は archive の末尾エントリだけで、archive 内部の遷移を検査しない / E0=`次 [T-001] A`、E1=`本文 [T-001]、次 [T-002]` を同時に最新 archive へ移し、移動時に E1 本文から T-001 を削除する。現行先頭で T-002 を受ければ archive末尾 E1→現行だけは通るが、E0→E1 は検査対象外になる。既知のローテーション経路は一エントリ移動の場合だけ塞がった / 致命

- BG-R04 / [tools/check_docs.py:286](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:286), [tools/check_docs.py:298](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:298), [docs/phase3.md:391](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:391), [test_check_docs.py:381](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:381) / live 台帳項目の ID 完備性を検査していない / `docs/phase3.md:401` の `[T-014]` だけ、または項目行全体を削除しても、T-014 を source にする現行 worklog はなく、ID のない項目は 300–301 行で黙って無視される。逆に取り消し線項目へ ID を付けても受理される。テストは閉じ括弧付きの `[T-01]` だけを負例にしており、ID 欠落を固定していない / 高

- BG-R05 / [tools/check_docs.py:355](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:355), [docs/decisions.md:2671](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2671) / ID 再利用は保存則をそのまま通す / E0=`[T-001] A`、E1=`[T-001] 無関係な C` とすれば raw token 集合の包含は成立し、A は消える。D69 に限界として明記されているが、既知経路自体は未封鎖 / 高

- BG-R06 / [tools/check_docs.py:84](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:84), [tools/check_docs.py:288](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:288), [docs/decisions.md:2677](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2677) / 理由なし台帳が有効 sink になる / 台帳へ `- [T-001]` だけ置くと、ID は行末境界で有効になり `ledger_ids` へ入る。理由・元項目本文がなくても E0 の T-001 は消せる。これも D69 が明記した未保証経路 / 中

- BG-R07 / [tools/check_docs.py:174](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:174), [tools/check_docs.py:189](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:189), [tools/check_docs.py:373](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:373), [test_check_docs.py:597](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:597) / archive の「H2 が 0 件」finding は production 経路で到達不能 / `_extract_archive_entries()` が呼ばれるには先に `ARCHIVE_ENTRY_DATE_RE` が1件以上必要だが、その match は必ず `WORKLOG_H2_RE` にも match するため `if not h2s` は成立しない。テストの `"zero entries"` は 377–381 行の「日付付き entry 0 件」を発火させており、189–191 行は検査していない / 中

- BG-R08 / [test_check_docs.py:554](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:554), [docs/decisions.md:2655](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2655) / archive 最大日付が同日の場合の filename tie-break がテストされていない / fixture は 2025-12-31 と 2026-02-01 で日付だけで決着する。tie 時に先頭ファイルを選ぶ、逆順にする等の変異でも追加25テストは緑のまま / 低

- BG-R09 / [tools/check_docs.py:83](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:83), [test_check_docs.py:381](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:381) / ID 形式テストは 4 桁以上の正例を固定していない / 正例は T-001/T-002/T-900、負例は T-01 だけ。実装を「ちょうど3桁」に狭めても全追加テストが通り、仕様上有効な `[T-1000]` を拒否する回帰を殺せない / 低

- DOC-R01 / [docs/worklog.md:40](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:40), [docs/decisions.md:2668](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2668) / 親の D69 は「決定記録には有効 ID を書かない」という同時追加規約に違反する / D69 本文に有効 token `[T-014]` と `[T-059]` がある。現コードは decisions.md を採番・source・sink に含めないため現時点の自己汚染はないが、文書契約そのものは自己矛盾している / 低

## 既知6経路の判定

| 経路 | 判定 | 根拠 |
|---|---|---|
| 本文 token 洗浄 | 未封鎖 | 通常 prose は拒否するが、fenced code／複数行 comment 内の list 行で通る |
| ID 統合 | 元の一項目手順は封鎖 | `[T-001] A+B（旧 [T-002]）` では T-002 が行頭でなく欠落 finding になる |
| ID 再利用 | 未封鎖 | raw ID 集合しか比較しない |
| 理由なし台帳 | 未封鎖 | `- [T-001]` だけで sink |
| ローテーション | 未封鎖 | archive末尾境界だけ。archive内部遷移を隠せる |
| 二段飛ばし | 現行内では封鎖 | 全隣接遷移を走査する。ただし二エントリを archive 内へ移すと BG-R03 で再び通る |

追加25テストの負例は、すべて `_assert_violation()` に対象診断の部分文字列を渡しており、「return code が赤だけ」のテストはなかった。問題は BG-R01/R02/R04 の fixture 欠落と、BG-R07 の到達不能分岐である。

## 親 docs の実数検算

- `phase3` の live 5節は順に `9 / 19 / 11 / 6 / 3 = 48` 項目。
- うち取り消し線は B-008/B-009 の2件。残る46件すべてに `T-014..T-059` が文書順で付与され、重複・欠番なし。
- `### 裁定・完了記録` は10項目で T-ID は0件。
- B-ID は live 範囲48/48で残り、46行の変更は T-ID prefix の追加だけ。重複・破損なし。
- B-015/B-056/B-057 は過去の終了・消化記録を含むが、将来の再評価述語が残るため live 採番は妥当。B-008 の再試験は worklog の T-010 へ生存している。
- `worklog` は `T-001..T-013` の13件で重複・欠番なし。(15) から生存する11原子を保持し、R-05 と初回発火確認の2件を新規追加。今回消化した backlog-guard 自体だけが次の一手から除外されている。
- 採番母集団の実データは worklog 13件 + 台帳46件 = `T-001..T-059`。archive に有効 T-ID は0件。worklog 冒頭はローテーション前なので source/sink 外、D69 は decisions.md なので同じく外。現時点の自己汚染はない。

現実の conservation 適用数は、過去 worklog と最新 archive に T-ID source がなく、唯一の T-ID 群が後続を持たない末尾 (16) にあるため **0 遷移**。pytest と `check_docs.py` 本体は実行していない。上記は `git diff`、raw regex、実文書の独立集計による静的判定。

---

## 段 6 — 敵対レビュー B: 既存資産への退行・運用整合 レンズ (逐語)

NO-GO。静的に再現できる欠陥がある。

## 所見

- AC-01 / [tools/check_docs.py:86](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:86) / fenced code・複数行 HTML comment 内の行を sink の「トップレベル list item」と誤認し、既知の token 洗浄攻撃が残る / `TOP_LEVEL_ITEM_RE` は Markdown 槊造を見ず、行頭だけを見る。後続エントリに ```` ```text\n- [T-001] dummy\n``` ```` または `<!--\n- [T-001] dummy\n-->` を置くと `_top_level_ids()` が `[T-001]` を返し、[check_transition:355](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:355) の sink を満たす。負例テストは list marker のない単行 comment しか試していない / 致命

- AC-02 / [tools/check_docs.py:326](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:326) / 「各項目に ID」の規約は末尾エントリにしか強制されず、2 エントリ同時追加で ID なしタスクを黙って落とせる / E17 で E16 の ID を本文項目として全消化しつつ、`### 次の一手` に ID なし新規タスクを置き、E18 を有効 ID 付きで追加する。E16→E17 は通り、E17 の source は空なので [check_transition:353](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:353) で非適用、ID 必須検査は E18 だけを見る。このタスクを E18 から落としても finding は出ない / 高

- AC-03 / [tools/check_docs.py:383](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:383) / 同日 archive が複数あると「最新」を決められず、ファイル名順で誤った境界を検査する / candidate は `(最大日付, filename, ...)` で、[max():387](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:387) が同日なら辞書順最大名を選ぶ。`worklog-z-early.md` の `(1)` と `worklog-a-late.md` の `(2)` が同日なら前者が選ばれ、後者末尾から落ちた ID は未検査になる。現 worklog 自体に同日 16 エントリがあり、日付だけでは順序を表せない / 高

- AC-04 / [docs/worklog.md:685](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:685) / 作業中に完了用 worklog エントリを追記しており既存運用規律に違反する / 現在の handoff は「状態: 作業中」で「レビュー 2 本が実行中」と明記している一方、エントリ (16) は既にレビュー 2 本を工数へ計上している。これは [CLAUDE.md:154](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/CLAUDE.md:154) と [handoff/README.md:12](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/handoff/README.md:12) の「セッション末に 1 回」「作業中は追記しない」に反する / 高

- AC-05 / [docs/worklog.md:703](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:703) / 「docs を先に展開して実装子の意図的赤を消した」という工程記録が一次資料と逆 / 実装子 prompt の 49–50 行は「親はまだ docs に ID を振っていない」「期待赤 5 件」と明記し、`impl.md` 20–25 行も 1 failed・5 findings を記録する。さらに `impl.md` は 23:47、`docs.patch` は 23:54。したがって [worklog:704](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:704) の順序変更も「意図的赤が消えた」も事実でない / 高

- AC-06 / [docs/phase3.md:392](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/phase3.md:392) / 「生存項目の行頭には ID」と書く一方、実装は ID のない生存項目を正常扱いする / [tools/check_docs.py:286](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:286) で valid でも ID-like でもない項目は `continue`。例えば line 401 から `[T-014] `だけを除いても、その項目について finding は生じない。実装 prompt 58 行もこの非検査を明示しており、phase3 の規約と意図的に食い違う / 中

- AC-07 / [docs/worklog.md:28](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:28) / 「ゼロ埋め連番」という正規形と実装の受理集合が一致しない / [TASK_ID_PATTERN:83](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:83) は `[T-001]` と `[T-0001]` の両方を別文字列 ID として受理する。重複・保存比較も文字列比較なので両者は別 ID になるが、docs の `max+1` 連番規約は同じ数値 1 の二表記を説明していない。実装子自身も未裁定事項として報告している / 中

- AC-08 / [orchestrator/tests/test_check_docs.py:489](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:489) / source を「次の一手」から「エントリ全体」へ広げる退行をテストが検出できない / 同テストは既に `[T-001]` 脱落で赤い。誤実装が中間本文の `[T-900]` まで source にして追加 finding を出しても、テストは `[T-001]` の存在と `[T-002]` の不在しか検査せず通る。他の正例は2エントリ止まりで末尾本文が source にならない / 中

- AC-09 / [docs/worklog.md:698](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:698) / エントリ (16) の監査記録に複数の事実誤りと一次資料欠落がある / 「5 箇所すべて致命」は誤りで、冒頭除外を扱う BG-02 は ruling-v2 で「高」。[worklog:706](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:706) の `プラン1 + 相談2 + 実装1 + レビュー2` は合計6であり「codex 5 本」ではない。また「逐語は insights」としながら、この wave の insight ファイル名・repo 内ポインタが存在しない / 中

- AC-10 / [docs/decisions.md:2668](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2668) / 「本決定には有効 ID を書かない」という規約を D69 自身が破っている / [decisions:2664](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/decisions.md:2664) と [worklog:40](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/docs/worklog.md:40) が禁止しているのに、直後に有効な `[T-014]` と `[T-059]` を記載している / 低

## 指定された静的追跡

- 既存 7 テストの victim は19件中 `rels[0] = .codex/agents/README.md`、`rels[9] = docs/glossary.md`。`_build_min_repo()` が上書きするのは `docs/phase3.md` と新設する `docs/worklog.md` だけなので、どちらを削除しても backlog guard は clean fixture のまま。`test_missing_enumerated_doc_only_fires_own_finding` は静的には従来どおりちょうど1 finding になる。

- 現 repo の遷移候補は  
  `archive 2026-07-18 (13) → 2026-07-19 (14) → 2026-07-19 (1)…(8) → 2026-07-20 (1)…(16)`  
  の25本。archive 末尾から現行 (15) までの source はすべて空で非適用。(16) だけが `[T-001]`〜`[T-013]` を持つが後続がない。したがって保存差集合まで評価される遷移は0本である。実際に働くのは「末尾13項目の形式・重複」と「台帳46 IDの形式・重複」だけ。

- 数値は、相談 A 14 + 相談 B 9 = 23、台帳は48トップレベル B 項目 − 取り消し線2 = 46、実装子の中間 finding は「ID保有エントリ0件」1 + 末尾ID欠落4 = 5。これら3数値自体は一次資料と一致する。

- 既存 lint 本体は変更されていない。新 finding はパス参照検査の後、archive索引・worklog肥大・handoff鮮度検査の前へ挿入されるため、複合違反時の全体順序だけは変わる。archive worklog 約455KBを毎回全走査する新しい線形コストも加わる。

pytest および `check_docs.py` は実行していない。

---

## 段 6' — fix 単位の完了報告 (逐語)

実装完了しました。[check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/tools/check_docs.py:84) と [test_check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-ruling-ac/orchestrator/tests/test_check_docs.py:381) のみ編集しています。docs 編集・git 操作・commit は行っていません。

### 検証結果

- 変更前対象テスト:
  `python3 -m pytest orchestrator/tests/test_check_docs.py -q`
  → 32 passed / rc=0

- 回帰テスト先行追加時:
  同コマンド → 34 passed / 11 failed / rc=1  
  新しい負例が旧実装を実際に破ることを確認。

- 最終対象テスト:
  `PYTHONDONTWRITEBYTECODE=1 python3 -m pytest orchestrator/tests/test_check_docs.py -q`
  → 47 passed / rc=0  
  範囲は `orchestrator/tests/test_check_docs.py` 全体。全走は未実施です。

- 実 repo:
  `python3 tools/check_docs.py`
  → 出力 `check_docs: 違反なし` / rc=0

### 所見 1〜9

1. fenced code・HTML comment  
   Markdown-aware なトップレベル項目走査を追加。``` / ~~~ fence と複数行 HTML comment 内を `_top_level_ids()`、台帳収集、ID 完備性検査の全てから除外しました。

2. archive 全遷移・同日順序  
   全 archive の内部隣接遷移、archive 間境界、最終 archive→現行先頭を検査。ファイル間順序は日付＋明示 `(n)` で決め、同日で証明不能・範囲重複なら finding にします。filename は意味的 tie-break に使いません。

3. 全 ID 保有エントリの完全性  
   現行・archive とも、本文を含むエントリ全体に有効 ID があれば、その `### 次の一手` の全トップレベル項目へ ID 必須・節内重複禁止を適用しました。

4. 台帳 ID 完備性  
   生存項目は正規 ID 必須。`~~` 始まりの項目に T-ID があれば finding にしました。

5. 到達不能分岐  
   全 archive を直接 `_extract_archive_entries()` に渡す構造へ変更。H2=0 分岐は production 経路で到達可能になり、既存 fail-closed テストが実際に同分岐を通ります。

6. ID 正規形  
   `T-001`〜`T-999` と、先頭ゼロなしの `T-1000` 以上のみ受理。`T-0001` は不正形式 finding です。

7. source 範囲の退行  
   3 エントリ fixture を追加。中間本文の消化 ID と次の一手 IDを分離し、source をエントリ全体へ広げる変異では正例が赤になります。

8. 同日 archive  
   `(1)`→`(2)` を filename と逆順に配置する正例と、同じ ordinal で順序不能になる負例を追加しました。

9. 4桁 ID  
   `[T-1000]` の正例と `[T-0001]` の診断固定負例を追加しました。

### 追加テスト関数

既存テストの削除・弱化・skip 化・内容変更はありません。追加は次の15本です。

- `test_backlog_guard_id_bearing_middle_entry_requires_ids_on_all_items`
- `test_backlog_guard_id_bearing_middle_entry_rejects_duplicate_ids`
- `test_backlog_guard_ledger_live_item_requires_id`
- `test_backlog_guard_ledger_struck_item_rejects_id`
- `test_backlog_guard_source_is_only_next_action_in_three_entry_chain`
- `test_backlog_guard_four_digit_id_is_clean`
- `test_backlog_guard_fences_and_multiline_comment_do_not_satisfy_sink`
- `test_backlog_guard_hidden_ledger_items_do_not_satisfy_sink`
- `test_backlog_guard_hidden_ledger_items_are_not_live_items`
- `test_backlog_guard_rejects_redundant_zero_padding`
- `test_backlog_guard_checks_archive_internal_transitions`
- `test_backlog_guard_id_bearing_archive_entry_requires_ids_on_all_items`
- `test_backlog_guard_checks_boundaries_between_all_archives`
- `test_backlog_guard_same_day_archives_use_entry_ordinal_not_filename`
- `test_backlog_guard_ambiguous_same_day_archive_order_is_violation`

### 仕様解釈上の注意

古い archive の ID 非導入・非末尾エントリには `### 次の一手` がない実データがあります。有効 T-ID がない場合は自然な非適用遷移とし、各 archive の末尾と ID 保有エントリだけは構造を必須にしました。

また、存在する台帳項目の ID 完備性は検査しますが、項目行そのものが過去から削除された事実は単一スナップショットだけでは直接判別できません。今回指定された per-item 規則の範囲で実装しています。

---
