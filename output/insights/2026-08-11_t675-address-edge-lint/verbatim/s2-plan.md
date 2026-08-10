結論として、R3 は既存 command interface ループ内の短い分岐 1 個で足ります。以下は `dev-wave` 段 2 / `DW-O05` に従う静的プランで、ファイル編集・pytest 実走はしていません。

## 1. 挿入位置と実装形

[tools/check_docs.py:4075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4075) の直後、`_check_command_docs_guard()` 内の [COMMAND_INTERFACES ループ:4072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4072) に挿入する。

```python
        if (
            rel == ".claude/commands/cleanup-branches.md"
            and not any(
                "F26" in line and "docs/failures.md" in line
                for line in _visible_markdown_text(text).splitlines()
            )
        ):
            findings.append(
                f"{rel}: F26 と docs/failures.md が同一可視行に共起しない"
            )
```

現在の [frontmatter parse:4076](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4076) より前に置く。frontmatter が壊れて `continue` しても、この edge 検査まで消えないためである。既存の到達性 finding は [4103〜4107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4103) にあり、同じ関数・同じループ内である。

その位置で各変数は次を指す。

- `decoded`: [3990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:3990) で作られ、正常に UTF-8 読取できた相対 path と全文文字列を [4023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4023) で格納した辞書。

- `rel`: [4072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4072) で反復中の command path。対象値は registry の [401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:401)。

- `text`: [4073](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4073) で得た、その `rel` の改行を保った全文。

- `findings`: `_check_command_docs_guard(findings: list[str])` の引数 [3887](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:3887)。`main()` が [4556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4556) で生成し、[4559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4559) で渡す違反一覧。

専用関数、定数 registry、台帳、gate、CLI flag は追加しない。

## 2. 可視行の取り方

使用するのは `_visible_markdown_text(text).splitlines()`。意味上の正本は `_visible_markdown_lines` だが、command に対する literal scan の既存経路を優先する。

- `_visible_markdown_lines`: [1044〜1088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1044)。各行を `(visible, offset, newline)` で返す。code fence 内は空文字へ置換し [1054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1054)、HTML comment は [1077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1077) で同長の空白へ mask する。

- `_visible_markdown_text`: [1091〜1097](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1091)。上記 visible 行を元の改行付きで再結合し、offset だけを捨てる。したがって `.splitlines()` すれば同じ可視行集合になり、別々の行にある二 token を誤って結合しない。command literal scan では既に `dev_wave_text` に使用されている [3774〜3777](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:3774)。

- `_visible_dispatch_inventory_text`: [1100〜1106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1100)。別実装 `_dispatch_visible_markdown_lines` を使い、上記に加えて raw HTML block も不可視化する。`<script>` 等は [985〜995](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:985)、`<div>` 等は [1015〜1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1015) で除く。これは dispatch 表抽出 [3322〜3329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:3322) 用で、command への呼出しも dispatch 表専用 [4354〜4355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4354)。

具体的には、次の fence と comment 内の token は数えない。

````markdown
```text
F26 docs/failures.md
```

<!-- F26 docs/failures.md -->
````

一方、次の raw HTML 内の本文は通常の visible parser では数えるが、dispatch inventory parser では全 block が消える。

```html
<div>
F26 (`docs/failures.md`) が正本。
</div>
```

R3 の「可視行」は親 brief の定義どおり code fence / HTML comment 除外であり、raw HTML inventory 規則まで持ち込まない。

## 3. 違反メッセージ

既存の [到達性 finding:4107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4107) と同じ `"{rel}: 条件"` 形式にする。

```text
.claude/commands/cleanup-branches.md: F26 と docs/failures.md が同一可視行に共起しない
```

## 4. 負例テスト

現在の合成 command は実ファイルの逐語コピーである。ただし runtime の `shutil.copy` ではなく、[_SYNTHETIC_CLEANUP_COMMAND:318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:318) から 380 行までの手書き literal である。

その literal を [514](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:514) で無変更代入し、[525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:525) で合成 repo へ書く。`_build_min_repo()` は [764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:764) でこれを呼ぶ。fixture の 355 行目は実ファイルの [38 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/.claude/commands/cleanup-branches.md:38) と一致する。

静的な literal/file 比較では双方 3959 bytes、SHA-256 は `a92d960c…a4722e3`、全文一致だった。テストコード自身が固定するのは fixture の digest [6545〜6547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6545) であり、live file との直接比較ではない点には注意する。

新テストは現在の [6635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6635) の直後へ置く。

1. `_build_min_repo()` [710〜766](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:710) を使う。

2. `_read()` [4778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:4778) で command を読み、唯一の

   ```text
   正本は `docs/failures.md` F26。
   ```

   を

   ```text
   正本は F26。
   `docs/failures.md`
   ```

   に置換する。両 token は残すが、同一可視行共起だけを壊す。

3. 変更後 command の SHA-256 を既存 import [19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:19) の `hashlib` で計算する。合成 repo の `tools/check_docs.py` 内に旧 `_EXPECTED_CLEANUP_COMMAND_SHA256` が exact 1 件あることを assert し、その一件だけを新 digest へ置換する。実 repo の定数・fixture 定数は触らない。

4. `_assert_violation()` [702〜707](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:702) で新文言を要求し、さらに `_violation_count(res) == 1` を assert する。digest finding がないことも確認する。

`_assert_cleanup_digest_violation` は使わない。同 helper は [6602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6602) で次を要求し、[6603](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6603) では digest finding 自体も要求する。

```python
assert _violation_count(res) == 1, res.stdout
```

負例を再 pin しなければ、既存 digest 検査 [4502〜4510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4502) と新 edge 検査の計 2 件になる。2 件を許す helper を作るより、合成 checker だけ再 pin して新 lint を単独 positive control にする。

## 5. 既存負例群への副作用

既存テストが新たに赤くなることはない、と静的に断定できる。

- baseline fixture は [test fixture:355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:355) に両 token を持つ。

- command の既存 digest 負例はクラス番号の一 byte 変更 [6622〜6633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6622)、別 H2 の表記変更 [6648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6648)、[6660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6660)、[6672](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6672)、末尾 fence 追記 [6684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6684) であり、355 行目を変えない。

- Skill 側の負例 [6606](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6606)、[6638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:6638) は command 自体が baseline のまま。

したがって `_assert_cleanup_digest_violation` の「ちょうど 1 件」は維持される。

## 6. M11 (iv) の偽陽性面

提案条件は文字順を固定しない。

```python
"F26" in line and "docs/failures.md" in line
```

したがって [package.md:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/output/insights/2026-08-10_t675-pin-semantic-gap/package.md:56) の正当な行

```text
F26 (`docs/failures.md`) が正本。
```

は両部分文字列を同一 visible line に持ち、finding は追加されない。助詞・語順・括弧は検査対象にしない。

## 7. R1/R2 の置換文案

現 83〜84 行は [docs/skill-self-improvement.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/skill-self-improvement.md:83) からの 239 bytes（各 LF 込み）で、全体 5997 bytes。上限は [TextLimit(6_000, 100):174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:174)。以下はすべて 2 行を置換し、各行 100 chars 以下である。

案 A（読みやすさ優先、全体 5996 bytes）:

```text
whole-file SHA-256 pin=期待値外 bytes のみ検知、義務の意味=非保証。
他の lint: 予算・dispatch・住所 (address edge) の構造 lint に限定;非協調 drift 検知/意図顕在化;trust root=人間レビュー。
```

- 行別: 85 + 151 bytes
- LF 2 bytes込み: 238 bytes
- 差分: `-1 byte`
- 置換後全体: `5996 bytes`

案 B（「期待値と異なる」を明記、推奨）:

```text
whole-file SHA-256 pin=期待値と異なる bytes のみ検知、義務の意味=非保証。
他 lint:予算・dispatch・住所 (address edge) の構造 lint に限定;非協調drift検知/意図顕在化;trust root=人間レビュー。
```

- 行別: 94 + 145 bytes
- LF 2 bytes込み: 241 bytes
- 差分: `+2 bytes`
- 置換後全体: `5999 bytes`

案 C（byte 中立）:

```text
whole-file SHA-256 pin:期待値外 bytes のみ検知;義務の意味=非保証。
住所 (address edge) の構造 lint 等は予算・dispatch 構造限定。非協調 drift 検知・意図の顕在化、trust root=人間レビュー。
```

- 行別: 83 + 154 bytes
- LF 2 bytes込み: 239 bytes
- 差分: `±0 bytes`
- 置換後全体: `5997 bytes`

## 総括

R3 は current 4075 直後の command loop に、対象限定の `not any(...)` と finding 1 件だけを加える。  
可視性は command literal scan の既存経路 `_visible_markdown_text(...).splitlines()` に揃える。  
負例は token を別行へ分離し、合成 checker の pin だけ再計算して新 finding 1 件を隔離する。  
既存 digest 負例は edge 行を保持するため、期待違反件数は変わらない。  
文案は案 B を推奨する。ファイル編集・pytest・`check_docs` 実走は行っていない。