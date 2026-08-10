結論は **NO-GO**。A2・B5・fix は概ね閉じていますが、A1 の grammar 外周と `〜` 展開に、層分類を変えず規範上の読了範囲を変えられる blocker が残っています。

## 段 3 所見の対応

| 所見 | 判定 | 根拠 |
|---|---|---|
| A1 bare path | **partial** | backtick 付き bare path は拒否するが、非 backtick path と他 path への `の全節` は受理 |
| A2 可視 H2 | **closed** | fence/comment/raw HTML は slice に入らず、その bytes は所属節へ算入。malformed H2 は 1:1 が発火 |
| A3 凡例/header | **partial（裁定どおり）** | 凡例・両 header は exact。表外自然言語は依然変更可能 |
| A6 到達不能・負例 | **partial** | coverage は実効だが KILL node がない。L2-only finding は現 repo で到達不能 |
| B5 共有 edge | **closed** | `DW-CTX` / `DW-O04` は正しい3 edge。U/C 変更は不一致になる |

### 1 / blocker / bare path grammar の外側が開いている

対象: [tools/check_docs.py:1795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1795)、[tools/check_docs.py:1803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1803)、[tools/check_docs.py:1843](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1843)、[tools/check_docs.py:3330](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3330)

**実測:** `python3 -B - <<'PY' ...` で現 command を in-memory 変異し、production と同じ structure/U-C/trigger/allowlist/closure/layer 比較を実行。

- 正当な `` `docs/skill-self-improvement.md` の全節 ``: `findings=[]`
- 全角空白 `` `self.md`　の全節 ``: path→pair finding + 段8 U不一致
- self path の backtick 除去: 段8 U不一致
- backtick 付き別 path の bare `全文`: path→pair finding
- 段9の O23 を次へ変更:

  ```markdown
  `docs/dev-wave/operations.md` の全節: `DW-O23`
  ```

  結果は `9453 bytes / max 139 chars / structure=() / U,C maps_equal=True`。parser は O23 の1 pairしか生成しない。規範上は operations 全節を段9 Uで読むため、O23 1,123 bytes以外の **7,206 bytes** を L1 実読へ移せる。

- 既存段行へ非 backtick の `docs/dev-wave/operations.md 全文` を追加: `9479 bytes / max 139 / findings=[]`。

**なぜ壊れるか:** path detector は backtick 付き `.md` だけを認識する。また `の全節` は self の exact fragmentだけを展開するが、別 path への同じ語句を禁止しない。したがって path/pair 集合は不変のまま、人間向け規範だけを全冊読了へ変えられる。

**DW-G05:** 放置すると、最終レポートは L1=10,625 bytes・O23参照だけと記録したまま、実際の段9参照集合を operations 全冊へ拡張した command を受理する。

**提案:** reference cell を厳格 grammar にする。少なくとも `.md` らしい raw文字列をすべて抽出して backtick token集合と一致させ、`の全節` の全出現が self exact fragmentにのみ属することを検査する。上記2変種を独立負例へ追加する。

### 2 / blocker / `〜` は「token 間のどこか」にあるだけで range 扱いされる

対象: [tools/check_docs.py:1864](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1864)

**実測:** 段1の `DW-G01`〜`DW-G05` 列挙を次に置換して同じ in-memory 検査を実行。

```markdown
`DW-G01`（説明〜補足）, `DW-G05`
```

結果:

```text
9434 bytes / max 139 chars / findings=[]
pairs = G01, G02, G03, G04, G05
```

ASCII `~` を URL に置いた `` `DW-G01`（https://x/~u）, `DW-G05` `` も `findings=[]`。一方、全角チルダ `～` は展開されず段1 U不一致になった。

**なぜ壊れるか:** `between` に `[〜~]` が一文字でもあれば range と判定する。人間には G01 と G05 だけの列挙に見える表記でも、checker は G02〜G04を読了済み edge として捏造する。

**DW-G05:** 放置すると、段1 brief が `DW-G02`〜`DW-G04` を実際には読まずに進んでも、レポート・台帳上の必須参照集合は充足扱いになり、正しさ gate を欠いた成果物を受理し得る。

**提案:** token 間を `re.fullmatch(r"[ \t]*〜[ \t]*", between)` のような exact range delimiter に限定する。注記・URL内の `〜/~` と全角 `～` を負例へ追加する。

### 3 / nit / 段表の row multiplicity が set に潰れる

対象: [tools/check_docs.py:1747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1747)、[tools/check_docs.py:3293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3293)、[tools/check_docs.py:3337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3337)

**実測:** 段7 U行をそのまま複製すると:

```text
9491 bytes / max 139 chars / findings=[] / edges=123（baselineと同数）
```

条件22行の複製は `condition-22` で拒否された。条件には row count があるが、段にはない。

**なぜ壊れるか:** 同一4-tuple edgeが `set` で消える。これは event加重読量を増やすが、裁定済みの unique-footprint値は変えない。

**提案:** unique指標の既知限界として明記するか、段についても canonical row-signature の `Counter` を pin する。成果物の値・unique参照集合は変わらないため nit。

### 4 / nit / 到達不能・mutation未被覆の検査が残る

対象: [tools/check_docs.py:3627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3627)、[tools/check_docs.py:3643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3643)、[tools/check_docs.py:3656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3656)、[orchestrator/tests/test_check_docs.py:2613](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:2613)

**実測:**

```text
core       = L1
mutation   = L1 + L1.5
operations = L1 + L1.5 + L2
workers    = L1.5
```

したがって現4冊では `L2 節しかない reference` finding は絶対に発火しない。さらに `_dev_wave_visible_inventory_is_exact()` が true のとき、登録IDの slice cardinalityは必ず1なので、`len(section_slices) != 1` 側と直後の `continue` も到達不能。1:1 finding自体は `exact_count=0` で発火するため全体が死んでいるわけではない。

一方、可視 `## — anonymous` の挿入では coverage finding が実際に発火した:

```text
classified=23592, preamble=587, actual=25225
```

ただしこの入力のテスト・mutation nodeは見つからなかった。coverage比較を `if False` にする1行変異は、現在の新規fixture群では殺せない。F42 meta-testはテスト名の存在だけを見るため production検出力にはならない。

**提案:** anonymous可視H2を coverage専用負例にする。L2-only findingは将来のregistry admissionと同時に実効化するか、現 waveでは dead branchとして明記する。

### 5 / nit / A3 の裁定済み残余は具体的に再現する

対象: [.claude/commands/dev-wave.md:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/.claude/commands/dev-wave.md:22)、[tools/check_docs.py:3299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3299)

**実測:** exact凡例を残したまま直後へ `C は常時成立。` を追加すると:

```text
9464 bytes / max 139 chars / findings=[]
```

凡例自体、段header、条件header、trigger cellの変更は拒否される。

**なぜ壊れるか:** checker は表外自然言語を条件性の権威として解析しない。これは段4で明示的に[T-316]へ残した限界であり、本waveの新たな回帰ではない。

**提案:** land報告で「条件性の意味全体を固定した」と主張せず、T-316残余を維持する。

## A2・B5 の実測

A2:

```text
fence       X99 sliceなし、注入33 bytesはC00へ算入、L1=10658で拒否
comment     X99 sliceなし、注入30 bytesはC00へ算入、L1=10655で拒否
raw HTML    X99 sliceなし、注入35 bytesはC00へ算入、L1=10660で拒否
DW-C00—     coverage合計は実bytesと一致するが、
            visible_exact=0/slices=1 の1:1 findingで拒否
```

合計一致だけ通って1:1が必要になる malformed 反例は実在し、1:1検査が発火した。A2は closed。

B5:

```text
DW-CTX = (段9,U), (条件21,C), (条件22,C)
DW-O04 = (段5,C), (段6,C), (条件04,C)
```

`DW-CTX` の U→C、`DW-O04` の段5 C→Uはいずれも U/C 両map不一致。共有を使った層下げは再現しなかった。O20へ154 bytesを in-memory追加すると `643 bytes / findings=[]` で、裁定したL2正例も成立した。

## その他の迂回 probe

| 編集 | 結果 |
|---|---|
| core preamble +1 byte | L1 10,626で拒否 |
| workers preamble +1 byte | L1.5 9,567で拒否 |
| `DW-C00`を既存`DW-STOP`へ再利用 | C00=0、STOP=2、inventory不一致 |
| `DW-C00`を未知`DW-X99`へ変更 | orphan + inventory不一致 |
| 条件key 25追加 | `condition-25`で拒否 |
| 条件行重複 | row countで拒否 |
| 段key改名・valid pair追加 | typed mapのmissing/extraで拒否 |
| `REQUIRED_REFERENCE_SECTIONS`だけ変更 | 静的に registry/typed-edge closure が不一致 |
| 正規 `G01〜G05` | 展開して受理 |
| `G01～G05` | 中間pair欠落で拒否 |
| `G01（注記〜補足）, G05` | **受理。所見2** |

## fix の受理集合

fix報告の「productionはheaderについてのみ狭まった」は妥当です。

- fix前の s5 実装は stripped cells が `["#", "発火条件", "読む節"]` の場合だけheaderとしてskipしていた。
- 現在は exact literal 1件・先頭table rowを要求し、空白差・改名・重複をstructure findingにする。
- exact headerは受理、空白差・改名・重複は拒否することをin-memoryで確認。
- `_grow_test_section()` の変更はtest helperだけ。
- productionに新しい `try/except`、例外握り潰し、恒真化はない。

pytestはこのread-onlyレビューでは **未実走**。`python3 -B tools/check_docs.py` は実走し、`rc=0 / check_docs: 違反なし`。これはpytest全体の緑を意味しない。

## 段4要件 1〜7

| 要件 | 状態 |
|---|---|
| 1. typed edgeを正本化 | 実装済み。共有edgeも正しい。ただし同一段row重複はsetに消える |
| 2. path→pair束縛 | **部分実装**。backtick付きは閉じたが所見1のgrammar外周が残る |
| 3. 可視H2 slice + coverage + 1:1 | 実装済み。coverage専用KILL nodeは欠落 |
| 4. 凡例・header exact pin | 実装済み |
| 5. L2-onlyをfail-closed | 機能は存在するが現repoで到達不能。裁定の「到達不能分岐を書かない」とは部分不整合 |
| 6. 10,625 / 9,566 / 1,000 pin | 実装済み |
| 7. 予算置換・CTX/O04移動・registry再編 | 実装済み。`DW-C00`変更は旧83 bytes→新83 bytesでbyte-neutral |

**NO-GO**

## 総括

- 非backtick pathと別pathへの`の全節`で、最大7,206 bytesを未計上のL1読了へ移せる。
- `〜/~`がtoken間の注記やURLにあるだけで、中間必須節を読了済みと偽装できる。
- A2の可視slice/1:1とB5の共有edgeは現物・in-memory probe上 closed。
- fixはheader契約だけを狭めており、新たなproduction緩和は確認しなかった。