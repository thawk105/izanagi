## 所見

- `B-1 / brief (bytes) / 基準値は正しいが、P1 の見積もりは小さい /` L1 上限 10,625 bytes は [check_docs.py:357](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:357)、各 slice は brief の [27行目](/home/SFC/tanab/.claude/jobs/562c3b1c/tmp/codex/dev-wave-research-gate/brief.md:27)〜[30行目](/home/SFC/tanab/.claude/jobs/562c3b1c/tmp/codex/dev-wave-research-gate/brief.md:30)と一致し、L1=10,594、残31 bytes だった。一方、必要量「約120〜160」は [brief.md:64](/home/SFC/tanab/.claude/jobs/562c3b1c/tmp/codex/dev-wave-research-gate/brief.md:64)に対し、下記文案の純増は198または212 bytes。`放置時:` P1 単純追記では L1 検査が赤になる。`推奨:` 実測差分と下記195 bytesの縮約を一体で裁定する。

- `B-2 / brief (pin 一覧) / 一覧は不完全 /` C01 は「見出し〜先頭2行」ではなく、末尾の Web 検索行まで節全体が exact pin である（[check_docs.py:635](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:635)、[check_docs.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:663)）。ほかに C00 の同節内 disclaimer 禁止（[check_docs.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:475)、[check_docs.py:5715](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:5715)）、S02/S03 の `reasoning=xhigh` pin（[check_docs.py:506](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:506)）、全 core H2 の一意性・孤児禁止（[check_docs.py:804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:804)、[check_docs.py:6129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:6129)）も一覧外。`放置時:` 親が一覧外を削減原資にすると予期せず検査が赤になる。`推奨:` 一覧を「今回触れない主要 pin」と改称するか、上記を追記する。今回の削減候補はこれらに触れない。

- `B-3 / P1・DW-S01 / P1 の研究前進軸は純増だが、停止動作は G05 の明示的な狭化 /` D205 は投資順位の判断（[decisions-excerpt.md:3](/home/SFC/tanab/.claude/jobs/562c3b1c/tmp/codex/dev-wave-research-gate/projection/decisions-excerpt.md:3)）、next-tasks は候補選定時の上流フィルタ（[next-tasks.md:18](/home/SFC/tanab/.claude/jobs/562c3b1c/tmp/codex/dev-wave-research-gate/projection/next-tasks.md:18)）にすぎない。直接引数が候補より優先される [core.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/core.md:7) 経路へ研究前進を課す正本は現状ない。G05 は成果物の値・受理集合・参照への影響であり（[core.md:79](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/core.md:79)）、論文の何を進めるかではない。ただし書けない場合を1 cycle後へ送る [core.md:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/core.md:81) 動作とは重なる。`放置時:` 「停止」と「後送」が二義化し、P1 が恒真化する。`推奨:` S01 に置き、「後送せず」を明記する。

- `B-4 / P1・収容先 / DW-S01 が唯一適切 /` S01 は brief を作る段1で必ず読まれる（[dev-wave.md:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/.claude/commands/dev-wave.md:66)）うえ、既存の列挙が「だけを書く」と閉じている（[core.md:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/core.md:43)）。G05 は段1・4・6で再読され、STOP は wave 開始と段9で読むため評価時点が早すぎるか遅すぎる（[dev-wave.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/.claude/commands/dev-wave.md:65)、[dev-wave.md:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/.claude/commands/dev-wave.md:74)、[dev-wave.md:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/.claude/commands/dev-wave.md:81)）。`放置時:` G05 収容なら段4・6にも無用な payload が残り、STOP 収容なら brief 作成後の判定にならない。`推奨:` S01 の先頭文を置換する。

- `B-5 / brief 自身の P1 適用 / 現状は新 P1 を満たさない /` 「研究前進」は物理的に5行あり（[brief.md:4](/home/SFC/tanab/.claude/jobs/562c3b1c/tmp/codex/dev-wave-research-gate/brief.md:4)）、土台 wave に必要な「現在止まっている特定の研究」の実測ではなく、wave 比率・行数・台帳件数の総計である。しかも wave 分類は insight 名による粗分類と自己申告されている（[brief.md:71](/home/SFC/tanab/.claude/jobs/562c3b1c/tmp/codex/dev-wave-research-gate/brief.md:71)）。`放置時:` この brief が先例となり、一般的な「研究のため」統計で P1 を通せる。`推奨:` 現在止まっている論文節・実験・図表を1件名指しし、その停止を示す実測1行へ置換する。できなければ新規則どおり停止する。

- `B-6 / 構造 lint / 提案した本文置換は構造を変えない /` checker は可視 H2 を raw byte slice にして（[check_docs.py:5235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:5235)）、H2 と slice の1:1および全文被覆を検査する（[check_docs.py:5323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:5323)、[check_docs.py:5344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:5344)）。dev-wave reference は `TextLimit=None` で、core.md に最長行 cap は掛からない（[check_docs.py:5922](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:5922)）。`放置時:` 新H2や ID 変更なら registry・dispatch が赤になる。`推奨:` S01/S04/S08 の既存 H2 を保持し、本文だけ編集する。提案文には docs 間の行番号参照を入れない。

## 削減候補

| file:line | 削る逐語 | 節約 bytes | D227 の重複先 | pin 抵触なしの確認方法 |
|---|---|---:|---|---|
| [core.md:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/core.md:91) | `実装前の変異事前登録は \`DW-M01\` に従う。` と行末 LF | 56（実測） | `DW-M01` の「変異は実装前に登録する」（[mutation.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/mutation.md:7)）。S04 と M01 は同じ段4で必読（[check_docs.py:878](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:878)）。 | S04 は exact literal map の対象外。`DW-S04` H2 は保持し、[REQUIRED_REFERENCE_SECTIONS](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:804)を変えない。 |
| [core.md:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/core.md:119) | `段 7 後に一度だけ \`docs/skill-self-improvement.md\` の発火 gate・routing・command 別終端を適用する` + 次行の `（同文書と入口が正本。手順を本節へ再掲しない）。` を、`\`docs/skill-self-improvement.md\` を適用する。` に縮約 | 139（旧191−新52、実測） | 自己改善契約の dev-wave 終端が「段7後の段8で一度適用」を上位互換で持つ（[skill-self-improvement.md:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/skill-self-improvement.md:57)）。S08 と同文書全節は段8で同時必読（[check_docs.py:899](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:899)）。 | S08 本文に exact pin はない。`DW-S08` H2 を保持し、exact pin される自己改善文書自体は編集しない（[check_docs.py:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/tools/check_docs.py:650)）。 |

合計195 bytes。ほかの L1 は、preamble、C00/STOP、G01〜G05、S07、CTX、M01、O23 が各読点固有で、S09 は pin 対象であるため、D227 適合候補に数えない。

## P1 の文案

1. `DW-S01` 先頭文への統合案:

   > brief は 10〜30 行で研究前進 1 行（論文の主張・図表・実験節の何を進めるか、土台なら今止まっている研究の実測）、scope、確定済みユーザー裁定、不変条件、成果物の形、並列分割方針だけを書く。研究前進を書けなければ後送せず段 2 へ進まず停止する。

   UTF-8 本文347 bytes。現行先頭文135 bytesを置換するため純増212 bytes。削減後の L1 は10,611 bytes、残14 bytes。

2. `DW-S01` 先頭文への二文統合案（推奨）:

   > brief は 10〜30 行で scope、確定済みユーザー裁定、不変条件、成果物の形、並列分割方針、研究前進 1 行だけを書く。研究前進は論文の主張・図表・実験節の何を進めるか、土台なら今止まっている研究の実測とし、書けなければ後送せず停止する。

   UTF-8 本文333 bytes。純増198 bytes。削減後の L1 は10,597 bytes、残28 bytes。改行を追加する場合は LF 1本につき1 byte増える。

## P3 と P5 の判断

- `P3: 採らない。` `DW-S07` に `wave の純増（製品行 / テスト行 / 新規 tool / 新規 gate）を 1 行で worklog に記録する。` を足すと、本文111 bytes、行末LF込み112 bytes、S07 は1,244→1,356 bytesになる。既存 S07 は記録先と実測前の欄作成禁止を定めるだけで（[core.md:104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/core.md:104)、[core.md:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/core.md:112)）、4指標は重複していない。したがって削減原資にもできず、推奨P1一式後の L1 は10,709 bytes、84 bytes超過する。さらに製品行・gate の分類基準がなく、P1 の研究前進そのものも測れないため、増枠に値しない。

- `P5: 採らない。` 現行は「実装面差分ゼロだけ」を免除する（[core.md:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/core.md:94)）ため、削除だけを追記すれば直接矛盾し、置換すれば免除集合を広げる。M01 も実装前登録を無条件に置く（[mutation.md:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/mutation.md:7)）。削除だけでも reject 分岐・テスト・checker を消せば受理集合は広がり、D95 の実装面にはそれらが含まれる（[decisions-excerpt.md:271](/home/SFC/tanab/.claude/jobs/562c3b1c/tmp/codex/dev-wave-research-gate/projection/decisions-excerpt.md:271)）。また「影響を書けない」を削除許可へ反転するのは、影響不明を安全の証拠にする誤りで、G05 の安全規律・受入要件を弱めない義務（[core.md:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-research-gate/docs/dev-wave/core.md:85)）と衝突する。

## 総括

P1 は `DW-S01` の先頭文を置換して収容する。  
D227 適合原資は S04 の重複 pointer 56 bytesと S08 の pointer 縮約139 bytes、合計195 bytes。  
推奨文案なら L1 は10,597/10,625 bytesとなり、増枠は不要。  
P3 は84 bytes超過かつ効果測定にならないため不採用、P5 は受理集合を広げうるため不採用。  
brief の bytes は正しいが、pin 一覧と自己 P1 適用は是正が必要。