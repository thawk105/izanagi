結論は land 前 **NO-GO**。親の byte 実測は再現しましたが、新 gate を緑のまま L1 実読範囲を増やせる反例が複数あります。

### 1 / blocker / allowlist 済み bare path

対象: [.claude/commands/dev-wave.md:63](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/.claude/commands/dev-wave.md:63)、[tools/check_docs.py:1767](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:1767)、[tools/check_docs.py:4066](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:4066)、[s2-plan.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s2-plan.md:66)

**実測:** plan の U/C 変換を in-memory で再現すると command は `9,442 bytes / 最長139 chars`。wave 開始 U 行へ次を足した。

```markdown
; `docs/dev-wave/operations.md` 全文
```

結果は `9,480/9,500 bytes`、当該行 `94/140 chars`。実 parser では:

```text
pair_delta []
disallowed []
```

`operations.md` は実測 8,329 bytes。そのうち従来 L1 は preamble 205 + `DW-O23` 1,123 だけなので、少なくとも **7,001 bytes** が新たに常時読了側へ移る。

**なぜ壊れるか:** `_dispatch_pairs_from_line()` は path と pair を別々に集め、allowlist は path が許可済みかしか見ない。節 ID のない whole-file 参照は typed pair、registry 閉包、層予算のすべてを変えず通る。`SELF_LIMITS` の path でも同じで、`docs/skill-self-improvement.md 全文` は `9,483 bytes / 97 chars` で通る。

**提案:** 各参照行について `line_paths == {path for path, _ in pairs}` を必須にし、pair を一つも所有しない bare path を拒否する。whole-doc 読了は exact grammar で全節 pair へ展開する。負例 `stage-bare-allowlisted-path` を追加する。

### 2 / blocker / 可視 H2 と raw byte 境界の二重 parser

対象: [s1-brief.md:61](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s1-brief.md:61)、[s2-plan.md:92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s2-plan.md:92)、[tools/check_docs.py:890](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:890)、[tools/check_docs.py:3788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:3788)

**実測:** `core.md:10-11` 間へ、in-memory で fence 内偽 H2 と可視本文を追加した。

```markdown
```text
## DW-X99
```
常時読む追加。…
```

既存 scanner と plan の raw `^## ` 分割規則を適用した結果:

```text
visible_X99_count 0
visible_orphans []
raw_X99_slices [2829]
partition_sum 10779 file_bytes 10779
classified_sum 7950 unclassified_bytes 2829
DW-C00_raw_before 1059 DW-C00_raw_after 354
```

HTML comment、raw HTML block でもそれぞれ `raw=1 / visible=0` を再現した。

**なぜ壊れるか:** 必須 H2・孤児検査は偽 H2 を不可視化する一方、予算 splitter は境界として扱う。偽 H2 以降の本物の L1 本文が未登録 slice に入り、L1 から消える。plan の「全 slice + preamble = file bytes」はこの反例でも成立しており、分類完全性を証明しない恒真条件である。

節表記にも同じ不一致がある。`## DW-C00 —` を `## DW-C00—` にすると、実測で H2 inventory は `DW-C00=1`、`_reference_id_sections()` は `0`、probe 型 raw ID は `DW-C00—` になった。

**提案:** 既存の可視 H2 offset を raw text の slice 境界として使う。さらに `classified bytes + assigned preambles == 全4冊 bytes` と、可視登録 H2 と byte slice ID の一対一対応を検査する。fence/comment/raw-HTML/malformed-heading を境界テストと変異へ追加する。

### 3 / blocker / U/C の意味自体は pin されない

対象: [.claude/commands/dev-wave.md:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/.claude/commands/dev-wave.md:19)、[.claude/commands/dev-wave.md:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/.claude/commands/dev-wave.md:59)、[s2-plan.md:30](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s2-plan.md:30)

**実測:** plan どおりの target `9,442 bytes / 139 chars` で、marker 説明だけを次へ置換すると `9,429 bytes / 139 chars`。

```text
種別は U=無条件、C=毎回読む。
```

mode cell、pair 集合、条件表第2列は一切変わらない。

また現行 `_dispatch_tables()` は raw 行を読む。段表全体を HTML comment に入れた in-memory probe でも:

```text
stage_maps_equal True
visible_wave_row False
```

だった。

**新案への静的帰結:** typed map と `CONDITION_TRIGGER_CONTRACT` は直接の `C→U`、trigger cell の「常に」化を止める。しかし marker 凡例、表 header、読み込み契約本文、参照 cell 内の自然言語は pin しないため、そこで C を常時読了へ再定義できる。前回 A1 の直接経路は閉じるが、意味の権威面は閉じない。

**提案:** marker 凡例、table header、条件性を決める規範文を exact contract にする。dispatch 表も可視 Markdown scanner から解析し、規範的な読了指示を表外へ置けない構造テストを追加する。

直接試した他経路の判定は次のとおり。

- U/C cell の直接変更、condition trigger 第2列変更: 新 typed/trigger 照合で赤。
- 可視 H2 の追加・削除・統合、直接の ID 改名: required/orphan/closure で赤。
- 通常の preamble 移動: plan どおりなら L1/L1.5 に算入され、単独の逃げにならない。
- fence/comment 偽 H2、bare allowlisted path、marker/header/表外文による意味変更: 緑の迂回が残る。
- `REQUIRED_REFERENCE_SECTIONS` の単独変更: 双方向 closure で赤。ただし bare path は pair が発生せず closure の外。

### 4 / major / 「実読量」ではなく unique footprint

対象: [s1-brief.md:29](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s1-brief.md:29)、[s1-brief.md:67](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s1-brief.md:67)、[s2-plan.md:70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s2-plan.md:70)

**実測:** worktree `b9c7a534` の raw UTF-8 を、見出し・原改行込み、次の raw H2 直前まで、preamble は最優先層へ一度だけ、で独立計算した。

| 層 | bytes / 節 |
|---|---:|
| L1 | **10,625 / 15** |
| L1.5 | **9,566 / 20** |
| L2 | **5,008 / 13** |
| 合計 | **25,199** |

file bytes も `8,655 + 4,526 + 3,689 + 8,329 = 25,199`。親の数値は再現した。

一方、P3/P4 後の常時段について、同じ節を読む各 dispatch event を重複込みで足すと、L1 節は **12,248 bytes**。preamble を一度だけ足しても **12,670 bytes** で、gate の 10,625 とは異なる。

**なぜ壊れるか:** plan は pair の集合和と優先順位で一度だけ数える。G01〜G05、STOP 等の複数段読了を数えないため、「実読量増加を検出する」という主張は過大である。段表への重複行や表外の再読指示も unique layer bytes を変えない。

また brief の「縮める変更は L1 のみ」は、L1.5 `9,566→9,567` を新 gate が拒否する plan 自身と矛盾する。純増検出力にも L1.5 cap、L2単節 cap、trigger pin が脱落している。

**提案:** 指標名を「dev-wave leaf の unique byte footprint」と明記するか、event-weighted envelope を別途設計する。brief の不変条件は「L1/L1.5」と正し、純増検出力を全軸列挙する。

### 5 / major / 受理集合の差と command cap

対象: [tools/check_docs.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:168)、[s2-plan.md:166](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s2-plan.md:166)

**実測:**

```text
core headroom 945
workers headroom 474
mutation headroom 61
operations headroom 71
file-cap family headroom 1551
aggregate headroom 1
```

現行13個のL2節を各1,000 bytesまで許す固定節集合の最大は:

```text
10,625 + 9,566 + 13,000 = 33,191 bytes
旧25,200との差 = 7,991 bytes
現行L2 headroom = 7,992 bytes
```

**広がる方向:**

- 現行 L2 の成長、file 間の同層 byte 移動、旧 file cap を超える集中。
- registry/dispatch/checker を整合更新できれば、L2節数・L2合計には直接上限がない。
- `operations.md` の既存 L2 配置を変えない前提では、P1 の残余 **71 bytes** は実測どおり。

**狭まる方向:**

- L1 +1、L1.5 +1。
- 他本文を同量縮めて総量/fileを維持しても、L2単節が1,001 bytesなら赤。
- mode 欠落・未知値、typed retype、trigger逐語変更、未到達登録 pair。
- 意味等価な trigger の表記変更も exact contract により旧緑→新赤になる。

**取りこぼし:** 「L2節を追加すれば緑」は `.claude/commands/dev-wave.md` の独立した `9,500 bytes / 140 chars` gate を満たす場合だけである。target の余白は **58 bytes / 1 char** なので、新条件行や長い参照の追加は L2 gate より先に command cap で拒否され得る。

**提案:** 受理集合表へ固定13節の上限33,191、L2追加時の command cap 条件、L1.5縮小、exact-trigger の過剰拒否を追加する。P1 は「既存配置・本文無削除なら71 bytes」に限定して記述する。

### 6 / blocker / 恒真保証と未検出 production 欠陥

対象: [s2-plan.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s2-plan.md:94)、[s2-plan.md:144](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s2-plan.md:144)、[docs/dev-wave/core.md:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/docs/dev-wave/core.md:60)

**実測:** 現行 `python3 -B tools/check_docs.py` は `rc=0 / check_docs: 違反なし`。新実装は未存在で、read-only のため pytest・実編集変異は未実測。

- `全slice+preamble == file bytes` は、反例2でも `10,779 == 10,779`。分類漏れ2,829 bytesを検出しない。
- 「L2節しかない将来 file の preamble をL1へ」は現在絶対に通らない分岐。4冊すべてにL1/L1.5節があり、第五fileは未登録実体検査で拒否される。brief に既存 artifact path がなく `DW-G04` 不成立。
- expected/actual の typed map が双方一致すれば、両者から導出した flattened map の一致は論理的に従う。独立検出力ではない。

M1〜M8 の comparator、U/C retype、marker欠落、trigger変更は、記載 fixture が実装されれば対応 test が赤になる構造である。一方、次の production 欠陥には KILL node がない。

- unclassified raw slice を黙って捨てる。
- allowlist 済み bare path を pair 無しで受理する。
- table/heading を fence・comment 内から解析する。
- marker凡例・headerの意味を変える。
- L2-only future preamble branchを無効化する。
- 未知mode、同一 stage row 重複を受理する。

**提案:** 上記6系統を独立負例にし、`classified coverage` と `path→pair binding` を変異事前登録する。L2-only branchは削除して fail-closed にするか、別裁定へ返す。

### 7 / nit / `DW-CTX`・`DW-O04` 位置修正

対象: [.claude/commands/dev-wave.md:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/.claude/commands/dev-wave.md:16)、[.claude/commands/dev-wave.md:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/.claude/commands/dev-wave.md:90)、[.claude/commands/dev-wave.md:106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/.claude/commands/dev-wave.md:106)、[docs/dev-wave/core.md:102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/docs/dev-wave/core.md:102)、[docs/dev-wave/operations.md:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/docs/dev-wave/operations.md:27)

**実測:**

- `DW-CTX` は段9、条件21/22、外部 supervisor の入口16-17に残る。
- `DW-O04` は条件04と段5/6のC行に残る。
- `REQUIRED_REFERENCE_SECTIONS` からも消えない。
- 節 bytes は `DW-CTX=878`、`DW-O04=200`。

**判定:** 到達不能節も義務消失も生まれない。`DW-S08` の専用commitは条件04/17を操作直前に再評価でき、`DW-S09` は段9でCTXを読む。

ただし actual event では、CTX の開始時再読が878 bytes、O04 の段8先読みが該当commit pathで200 bytes減る。unique layer値が不変なのは「実読量不変」を意味しない。

**提案:** P3/P4は採用可。ただし成果物説明を unique footprint と event 読量で分ける。

### 8 / major / consumer 閉包と scope 全層

対象: [tools/check_docs.py:33](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/tools/check_docs.py:33)、[orchestrator/tests/test_check_docs.py:1645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t313-read-budget-gate/orchestrator/tests/test_check_docs.py:1645)、[s1-brief.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t313-read-budget-gate/s1-brief.md:5)

**実測:** 指定定数群を `grep -rn --include='*.py' --exclude-dir=output` した live consumer は正確に2本。

```text
./tools/check_docs.py
./orchestrator/tests/test_check_docs.py
```

plan は named consumer の `REFERENCE_LIMITS`、aggregate、cap-sum、matrix、living-doc victim 除外をすべて列挙しており、第三の実行 consumer は見つからなかった。`SELF_LIMITS` は残り、self doc も allowlist に残る。この点は前回 A4 を閉じている。

一方、実際に常時読む別 surface は scope 外である。

| surface | 実測 / cap |
|---|---:|
| target L0 command | 9,442 / 9,500 |
| self doc | 5,997 / 6,000 |
| Codex dev-wave Skill | 3,747 / 5,500 |
| reference L1 unique | 10,625 |

self doc は段8 Uで全節を読む。したがって成果物を「dev-wave 全層の常時読量 gate」と呼ぶことはできない。

**提案する裁定パッケージ:** 今回は名称を「`docs/dev-wave/**` leaf unique-footprint gate」に限定する。L0/self/Codex surfaceを含む複合 envelopeは、読了 surface と event/unique の定義をユーザー裁定して別waveへ送る。既知の leaf→scope外 living doc 間接委譲も同パッケージへ残す。

### P1〜P6 の最終判定

| provisional | 判定 |
|---|---|
| P1 | 71 bytes は実測どおり。ただし file cap 全撤廃の必然性までは導かず、family余白は1,551 bytes。 |
| P2 | **不成立**。bare path と marker意味変更で分類を動かさず実読範囲を増やせる。 |
| P3 | 成立。O04の義務・到達性は残る。 |
| P4 | unique分類として成立。actual event は878 bytes減る。 |
| P5 | **不成立**。可視 inventory と raw budget splitter の二重化が新しい迂回になる。 |
| P6 | self allowlist維持は成立。ただし path→pair 非束縛が blocker。 |

前回所見では、再裁定要求は択1で解決、L2受理拡大は意図的裁定、self allowlist脱落と旧M5は解消済み。残ったのは前回A1の意味面を別経路で再現した所見1・3と、P5が新しく作る二重parser所見2である。

NO-GO

## 総括

- allowlist 済み bare path を U 行へ足すだけで、pair・層予算不変のまま operations 全文を常時読了へ移せる。
- 可視 H2 inventory と raw byte splitter の不一致で、偽 H2 以降の L1 bytes を未分類にできる。
- U/C cell と trigger は pin されても、marker凡例・header・表外規範による条件性変更は通る。
- `全slice=file` は恒真、L2-only preamble は到達不能で、現テスト計画にこれらの KILL node がない。