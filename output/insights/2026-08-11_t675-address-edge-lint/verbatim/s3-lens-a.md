静的検査のみを行った。pytest・`check_docs` は実走していない。

## 1. 検出力

**real — 提案された部分文字列検査は、正本 edge を失った状態でも通せる。**

提案条件は単に `"F26" in line and "docs/failures.md" in line` であるため、token 境界・Markdown 構造・リンク先を検証しない。[s2-out.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/s2-out.md:7)

以下の「緑」は whole-file SHA-256 を攻撃編集後に再同期した場合の新 edge lint の判定である。再同期しなければ既存 pin が赤にする。[tools/check_docs.py:4502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4502)

1. 部分文字列による偽 edge — **緑**

```diff
-... 正本は `docs/failures.md` F26。
+... 旧参照 `archive/docs/failures.md.bak` F260 は無効。
```

`F260` は `F26` を、別 path は `docs/failures.md` を部分文字列として含む。exact F26 × exact path は存在しないが通る。

2. hidden raw HTML — **緑**

```diff
-... 正本は `docs/failures.md` F26。
+... 復元する。
+<div hidden>F26 (`docs/failures.md`)</div>
```

通常 helper は fence/comment 以外をそのまま残すため、表示されない HTML でも通る。[tools/check_docs.py:1044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1044) dispatch 用 helper なら `<div>` を除去する。[tools/check_docs.py:1015](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1015)

3. 未使用・外部向け link definition — **緑**

```diff
-... 正本は `docs/failures.md` F26。
+... 復元する。
+[F26]: https://invalid.example/docs/failures.md
```

reference definition は本文に表示されず、リンク先も repo 正本ではないが、scanner は Markdown link grammar を解釈しない。

4. 表セル横断＋部分文字列 — **緑**

```diff
-... 正本は `docs/failures.md` F26。
+| 旧 ID | 旧 path |
+|---|---|
+| F260 | `archive/docs/failures.md.bak` |
```

検査単位は物理行なので、別セルでも共起扱いになる。exact edge は無い。

一方、次は提案 lint が正しく **赤** にする。

| 編集 | 判定 | 根拠 |
|---|---|---|
| `<!-- F26 docs/failures.md -->` のみ残す | 赤 | comment は mask される。[tools/check_docs.py:1077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1077) |
| fenced block 内だけに置く | 赤 | fence 内は空行化される。[tools/check_docs.py:1054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1054) |
| `Ｆ２６` / `docs／failures．md` に全角化 | 赤 | ASCII exact 部分文字列がない。 |
| `F26` と path を別行へ分割 | 赤 | 行境界は保持される。[tools/check_docs.py:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1091) |

したがって「別行迂回」は殺すが、address edge 一般を守る検査にはなっていない。

## 2. 可視行 helper と P1

**real — `_visible_markdown_lines` と `_visible_markdown_text(...).splitlines()` は、この検査について同値。**

後者は前者の visible 部分を元の改行で再結合するだけなので、literal を含む行の集合は変わらない。[tools/check_docs.py:1091](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:1091)

**real — `_visible_dispatch_inventory_text` へ替えると検出力は変わる。P1 は目的に対して誤り。**

dispatch 用 helper は `<script>`、`<div>` 等の raw HTML block も除く。[tools/check_docs.py:922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:922) 段2も差を認識しながら raw HTML を数える方を選んでいる。[s2-out.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/s2-out.md:42) [s2-out.md:54](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/s2-out.md:54)

P1 は「parser 上、comment/fence でない」と「利用者に見える」を混同している。ただし dispatch helper に替えるだけでは link definition、table、inline hidden HTML までは閉じない。

## 3. 全層 scope

**real — 防壁は全層には配線されていない。**

| 層 | `check_docs` 呼出し | 静的判定 |
|---|---|---|
| hooks | なし | settings は guard 4 本だけを呼ぶ。[.claude/settings.json:8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/.claude/settings.json:8) Codex 自体には hooks 未配線。[hooks/README.md:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/hooks/README.md:15) |
| land | 条件付きのみ | spool fold 適用後には直接呼ぶ。[tools/dev_wave_land.py:1795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/dev_wave_land.py:1795) ただし fold が noop なら呼出し前に return する。[tools/dev_wave_land.py:1867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/dev_wave_land.py:1867) 通常 land の noop 経路もそのまま返る。[tools/dev_wave_land.py:2395](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/dev_wave_land.py:2395) |
| CI | なし | repo 自身が「CI は無い」と明記する。[docs/freeze-permanent-design.md:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/freeze-permanent-design.md:384) |
| pre-commit | なし | tracked pre-commit 設定はなく、git hooks 未配線の記録とも一致する。[docs/archive/worklog-phase3-0720.md:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/archive/worklog-phase3-0720.md:105) |

一方、dev-wave supervisor の既定 check は `docs-check` を含み、wrapper は `tools/check_docs.py` へ写像する。[tools/dev_waves/cli.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/dev_waves/cli.py:188) [tools/task_run_check.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/task_run_check.py:14)

**refuted — package が全層を実装済みと装っているわけではない。**

package 自身が land/hooks/provenance 未測定と明記している。[package.md:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/output/insights/2026-08-10_t675-pin-semantic-gap/package.md:163)

裁定パッケージ候補は、`hooks`、通常/no-fold land、CI、pre-commit の4層。これは実装勧告ではなく、現 wave の scope 外として返すべき対象である。

## 4. 変異の帰属

**real — 再 pin しない負例では単一理由性が不成立。**

command を編集すると whole-file pin も必ず finding を追加する。[tools/check_docs.py:4502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4502) 新 lint を無効化しても digest finding が残るため、その入力では変異を殺せない。

**refuted — 段2が計画した「再 pin 済み合成 checker」の入力なら、既存層による競合はない。**

- 段2は合成 checker の digest だけを更新し、違反数1と digest finding 不在を確認する計画である。[s2-out.md:99](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/s2-out.md:99)
- `CODEX_FIRST_REFERENCE_LITERALS` は core/workers だけが対象で、cleanup command は対象外。[tools/check_docs.py:615](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:615)
- 既存 command 到達性は `docs/skill-self-improvement.md` の有無だけを見るため、今回の分割入力は通る。[tools/check_docs.py:4103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4103)
- archive 到達性は `docs/archive/` の実体と索引だけが対象。[tools/check_docs.py:4697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4697)

したがって、計画どおり再 pin と違反数1を保持すれば変異帰属は静的には成立する。

## 5. 親の実測値・一般化

- **M-a: real。** F26 は29、31、38行目、path は38行目だけで、現行 edge は38行目にある。[cleanup-branches.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/.claude/commands/cleanup-branches.md:29) [cleanup-branches.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/.claude/commands/cleanup-branches.md:38)

- **M-b前半: real。** `docs/skill-self-improvement.md` は `TextLimit` と構造検査の対象だが、whole-file digest pin ではない。[tools/check_docs.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:174)

- **M-b後半: refuted。** 「repo の `*.py` に SHA-256 定数が2本だけ」は事実でない。対象テスト内だけでも `_EXPECTED_CLEANUP_SKILL_SHA256` と `_EXPECTED_CLEANUP_COMMAND_SHA256` がある。[test_check_docs.py:261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/tests/test_check_docs.py:261) 他にも `SOURCE_FILE_SHA256`、`ROLE_MANIFEST_SHA256` 等が存在する。[review_ledger.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/orchestrator/codex_roles/review_ledger.py:15)

- **M-c: real。** 対象は84行で終わり、上限は6000 bytes/100 chars。静的 byte count は5997で、headroom 3。[skill-self-improvement.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/skill-self-improvement.md:83) [tools/check_docs.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:173)

- **「既存被覆0件」: refuted。** production checker は既に raw-HTML-aware な可視 Markdown を行へ分け、同一表行・同一参照セルから path × section の typed edge を構成する。[tools/check_docs.py:3322](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:3322) [tools/check_docs.py:3355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:3355) その edge を期待集合と比較して拒否する。[tools/check_docs.py:4367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/tools/check_docs.py:4367) これはまさに「同一可視行内の2要素から edge を構成する検査」の先例である。

したがって新規なのは検査パターンではなく、cleanup F26 edge という対象だけである。

## 6. M11 (iv)

**refuted — 偽陽性にはならない。**

`F26 (`docs/failures.md`) が正本。` は両 ASCII 部分文字列を同一の通常行に持つため、提案条件は finding を追加しない。[s2-out.md:123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/s2-out.md:123) package の要求どおり緑である。[package.md:51](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/output/insights/2026-08-10_t675-pin-semantic-gap/package.md:51)

## 7. `DW-G03` と scope

**refuted — 機械 lint 本体は F51・Skill・全 path 等へ一般化していない。**

提案コードは cleanup command の1分岐だけであり、`DW-G03` が禁じる族一般化はしていない。[s2-out.md:7](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/s2-out.md:7) `DW-G03` の条件は異なる producer/consumer の独立2例である。[core.md:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t675-address-edge-lint/docs/dev-wave/core.md:55)

**real — 段2成果物の §7 は R3 実装プランの所有範囲を越えている。**

R1/R2 docs は親所有、R3だけが Codex実装面と brief に分離されている。[brief.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/brief.md:16) [brief.md:20](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/brief.md:20) それにもかかわらず段2は親所有文書の文案を選定し、案Bを推奨している。[s2-out.md:139](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/s2-out.md:139) これは第二の lint 一般化ではないが、R3プランとしては scope/ownership 逸脱である。

さらに案Bは `+2 bytes` であり、brief の「byte 中立」に直接違反する。[brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/brief.md:8) [s2-out.md:155](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t675-address-edge-lint/s2-out.md:155)

## 判定

NO-GO

最小修正は次のとおり。

- 同じ1分岐のまま、`_visible_dispatch_inventory_text` を使う。
- `F26` は token boundary、path は exact code span `` `docs/failures.md` `` として照合し、部分 path、`F260`、table row、link definition、raw HTML を positive edge に数えない。
- 分割負例に加え、上記の部分文字列・hidden HTML・外部 link definition の3負例と、M11(iv) の正例を追加する。
- 合成 checker の再 pin と違反数1を維持し、変異の単一理由性を固定する。
- R1/R2 文案は実装プランから外し、親が byte-neutral 案だけを扱う。全層配線は実装せず、scope外裁定候補として明記する。

## 総括

NO-GO。提案 lint は別行迂回を殺すが、部分文字列・hidden HTML・link/table 構造で偽 edge を作れる。  
P1 は rendered visibility と一致せず、hooks・通常 land・CI・pre-commit に防壁はない。  
変異帰属は合成 checker を再 pin する計画どおりなら成立する。  
exact token/code-span と adversarial 負例への最小強化後に再審査すべきである。