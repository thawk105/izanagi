# [T-094] リテラル placeholder の機械検出 — 子出力の逐語 (2026-07-25)

材料レポート = `2026-07-25_t094-placeholder-gate.md`、変異台帳 = 同 `-mutation-ledger.json`。

## Erratum — 可逆 defang を施している

本ファイルの逐語原文には、本 wave が新設した exact-literal gate の検出対象バイト列が
合計 27 箇所含まれていた。そのまま凍結すると gate が自己発火するため、**該当箇所の半角山括弧を
全角山括弧へ 1:1 で可逆置換**した (`<` → `〈`、`>` → `〉`、内側の文字列は不変)。
置換後に検出対象が 0 hit であることを機械検査済みである。
検出対象の識別は `tools/check_docs.py` の `LITERAL_PLACEHOLDERS` を正本とし、
本ファイル内では宣言順に LP-1 / LP-2 / LP-3 と呼ぶ。

原文の同一性は次の manifest で検証する (SHA-256 は **defang 前の raw bytes** に対する値)。

| 逐語 | 原文 SHA-256 | 原文 bytes | defang 箇所数 |
|---|---|---:|---:|
| `brief.md` | `c0275e0ddf61d12d53370321780b802ca8240d3b3c53e620f76edbde25abc2c6` | 9082 | 9 |
| `s2-plan.md` | `9e62b61d8501adeb48b7b6351c9552383846fa8d8c66e7f81e5511fe33c8dd1c` | 13816 | 0 |
| `s3-lens-a.md` | `bab987c67392b7cd0ce612bc7b346e56cb85cf9f00f838ede609a18b1ff091b3` | 14982 | 11 |
| `s3-lens-b.md` | `42a7f472b453b47b260bec494aebb21d1e3159ef1789204cafd48e2ab56e4bb4` | 14135 | 3 |
| `plan-v2.md` | `eb0d39393ba78aa8db7718f6480860a5f21b121bd54a4fe3566200cee45efced` | 12034 | 0 |
| `s5-impl.md` | `83e89a41d3610a57600fa6c1d0f56bc7113864692df1e70d7fc546f84248486b` | 4617 | 3 |
| `s6-review-a.md` | `99977edd74588383a47d7713b56fed8531dedd660a7441bb850aa2106f51fea9` | 13862 | 1 |
| `s6-review-b.md` | `4aebe0f903a5e3923ec0cbd724cbf2de5414b5a0bc61327f9f2db516185f5b4e` | 12206 | 0 |
| `s6-fix.md` | `a93705ff095841febc6f9182cc15bce768c4dd3b1b28761e861e19818dedead9` | 5375 | 0 |
| `s6-refocus.md` | `8318ab14341280c903132ecb9dfd11c94e8cf5d57e9fd6cd8c3b034f428a2ba3` | 16107 | 0 |
| `s6-fix2.md` | `4de36ffe4b0c6d41f12f2b9fda8460072e675801a1fb4e35d423f8d2cb8401f5` | 4022 | 0 |
| `s6-refocus2.md` | `4b4dec6252746bd3a7ecfcf3abf6cb48ff27af9818b155a63ab41fda0a824028` | 10691 | 0 |
| `s6-fix3.md` | `ec4ca8ce4e32b4fd0ff0aec49336c7650398d04bcad5be643e8ef8c6ff0093c2` | 2948 | 0 |


---

## 段 1 親 brief (`brief.md`)

# 親 brief — [T-094] リテラル placeholder の機械検出 (F36 恒久対応 2)

repo root (worktree) = `/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper`
branch = `worktree-dev-wave-t094-placeholder-gate`、基準 commit = `1d2d298` (main と同一)

## scope

`tools/check_docs.py` にリテラル placeholder の機械検出を新設し、`docs/failures.md` の F36 恒久対応 2
(「リテラル placeholder の機械検出」) を実体化する。テストは `orchestrator/tests/test_check_docs.py`。
docs 記録 (worklog / insights / failures の現行実体更新) は親が段 7 で行う。実装子は docs を触らない。

## 確定済みユーザー裁定 (worklog 2026-07-25 (4) の [T-094] 項)

- 検出対象文字列 = `〈反映〉` / `〈受入結果を反映〉` / `〈受入全走結果を反映〉` の **exact 3 文字列**
  (正規表現 `<[^>]*反映[^>]*>` のような一般化は日本語メタ変数と欠陥説明の引用を誤検出するため却下済み)
- 対象ファイル族 = `docs/worklog.md` と **verbatim でない** `output/insights/*.md`
- 既存 4 件は **行 digest** で例外登録 (allowlist)

## 背景の正本 (必ず開くこと)

- `docs/failures.md` の `### F36.` 節 (恒久対応 1 と 2、retroactive に埋めてはならない理由)
- `docs/failures.md` の `### F37.` 節 (検査 rc をパイプで握り潰した事故 — 本 wave の実装にも関係)
- `docs/worklog.md` の `## 2026-07-25 (4)` エントリの `[T-094]` 項 (裁定文の正本)
- `docs/worklog.md` 冒頭の `## ローテーション` 節 (現行 worklog が archive へ移動する契約)
- `tools/check_docs.py` の冒頭 (LIVING_DOCS のコメント: worklog / insights / archive は
  「追記型の日誌・記録 = 書いた時点で凍結」として既存 living-docs 検査の対象外)

## 親が実測した事実 (2026-07-25、grep による全 repo 走査)

exact 3 文字列の hit = **11 行**。内訳:

### 真の placeholder (埋め戻し失敗の残存。retroactive に埋めることは F36 が禁止) = 4 行

| path | line | 含む文字列 | backtick で囲まれているか |
|---|---|---|---|
| `docs/worklog.md` | 75 | `〈反映〉` | いない |
| `docs/archive/worklog-phase3-0722-0724.md` | 717 | `〈受入全走結果を反映〉` と `〈反映〉` | いない |
| `docs/archive/worklog-phase3-0722-0724.md` | 773 | `〈反映〉` | いない |
| `output/insights/2026-07-24_e2e-real-seal.md` | 37 | `〈受入結果を反映〉` と `〈反映〉` | いない |

### 説明的言及 (検出してはならない = 偽陽性源) = 7 行

`docs/failures.md` 516 / 519、`docs/worklog.md` 183 / 251 / 252、
`output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md` 380 / 469。
**7 行すべて backtick inline code (`` ` ``) の内側にある。**

→ 実測上、backtick の有無が真の placeholder と説明的言及を完全に分離している。

### その他の実測

- `output/insights/` = 140 ファイル、うちファイル名に `verbatim` を含むもの = 14
- `orchestrator/tests/test_frozen_artifacts.py` の `FROZEN_MANIFEST` = 23 件 (うち
  `output/insights/2026-07-16_*.md` が 5 件)。この 5 件に 3 文字列の hit は **ゼロ**
- submodule = 初期化済み (`external/ccbench` = `d706650`)
- `docs/dev-wave/**` の byte 予算は 23960 / 24000 (残り 40 bytes)。本 wave は dev-wave reference を
  原則触らない

## 実測で覆った裁定前提 (親は段 4 で scope を裁定し直す)

- **N-1**: 確定設計の対象 `docs/worklog.md` の中に説明的言及が 3 行 (183/251/252) ある。
  「既存 4 件の allowlist」だけでは偽陽性 3 件が残る
- **N-2**: 真の placeholder 4 件のうち **2 件は `docs/archive/worklog-phase3-0722-0724.md`** にある。
  確定設計の対象族 (worklog.md + 非 verbatim insights) には archive が含まれないため、対象族内の
  真の hit は 2 件だけになる。裁定文の「既存 4 件」は族横断の計数であり、裁定要約の際に
  対象族から archive が落ちた疑いがある (closure verbatim の提案では archive が対象に入っていた)
- **N-3**: `docs/failures.md` にも言及 2 行。現設計では対象外なので無害だが、族拡張時に影響する
- **N-4**: `docs/worklog.md` の該当行は将来 archive へ**移動**する (ローテーション契約)。
  path 込みの allowlist はローテーションで破れる
- **N-5 (自己言及問題)**: 本 wave が段 7 で書く worklog エントリと材料レポートは、設計を記述するために
  3 文字列を必ず含む。除外機構がなければ**自分の記録で検査が赤になり**、allowlist に自分を足し続ける
  運用破綻に至る

## 不変条件 (侵してはならない)

1. 既存 4 件を retroactive に埋めない (F36: 当時測っていない値を今書くのは捏造)
2. 凍結成果物 (`FROZEN_MANIFEST` の 23 件) の bytes を変えない
3. 検出を弱める方向 (対象族の縮小、検出文字列の削減、恒真になる allowlist、恒真になる除外規則) を
   実装の便宜で選ばない。allowlist は「登録されているから緑」ではなく「登録された行が実在し、
   内容が一致する」ことを能動的に検査する形にする (登録行が消えたら違反にする = F9/F27 の原則)
4. 検査の rc をパイプに通さない (F37)
5. `tools/check_docs.py` 自身の byte / 最長行予算 (`SELF_LIMITS`) を満たす

## 成果物の形

- `tools/check_docs.py`: placeholder 検査 checker + allowlist 台帳 + findings への統合
- `orchestrator/tests/test_check_docs.py`: positive control (allowlist を外すと既存の真 placeholder が
  検出される / 新規 placeholder 行が赤になる) と negative control (説明的言及は緑 / allowlist 登録行が
  消えたら赤) を含むテスト
- 親が段 7 で: worklog エントリ、材料レポート insight、変異台帳、F36 の「現行実体」更新

## 親の provisional 裁定 (P1〜P6) — すべて攻撃対象であり、親の裁定に守る義務はない

- **(P1)** 対象族に `docs/archive/worklog-*.md` を**含める** (真の placeholder 2 件が居るため)
- **(P2)** 偽陽性の除去は **backtick inline code 内の出現を除外**する方式で行い、allowlist への
  追加登録では行わない (説明的言及は今後も増えるため、allowlist 運用は破綻する = N-5)
- **(P3)** allowlist は **path 非依存の行 digest** で固定する (N-4 のローテーション耐性)
- **(P4)** fenced code block (``` ``` ```) 内も除外する
- **(P5)** 実装は 1 子・逐次で行う (編集面が 2 ファイルだけであり、並列化は所有分離のコストに見合わない)
- **(P6)** `docs/decisions.md` への D 起票は不要 (既裁定の lint 追加であり、長期の設計択一ではない)

## あなた (段 2 プラン起草) への依頼

`tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` の**実コードを読み**、
file:line 粒度の実装プランを書け。次を必ず含めること。

1. checker 関数の挿入位置 (既存のどの checker の隣に、どの命名規約で置くか) を file:line で指定する。
   既存の findings 収集・報告経路 (`findings.append` の形式、main の集約) に正しく乗る形を示す
2. 対象ファイル族の列挙方法 (glob か手書き列挙か)。`check_docs.py` 冒頭コメントが述べる
   「列挙対象の不在は黙って skip ではなく違反にする」原則との整合を示す
3. verbatim 除外の判定方法 (ファイル名規約か内容判定か)。実在する 14 ファイルの命名を確認して書く
4. backtick / code fence 除外の実装方法。**既存コードに再利用できる fence 解析があるか**を必ず確認する
   (`FENCE_OPEN_RE` が既にある)。inline code の除去は行内 backtick の対応付けをどう扱うか明記する
5. allowlist の data 構造と、それが恒真化しない検査 (登録行が実在し内容一致することの能動確認)
6. テストの positive / negative control の nodeid 単位の設計。**テストを甘くして緑にしない**
7. P1〜P6 のうち、コードを読んだ結果 **異議のあるもの**を名指しで挙げ、代案を file:line で示す
8. 想定される偽陽性・偽陰性を列挙し、どれを受容しどれを塞ぐかを述べる

## 制約

- あなたは read-only sandbox である。**pytest を走らせる必要はない** (書込可能 tmp がない)。
  静的検査でよい。テストの実測は親が行う。走らせていないテストを緑と主張してはならない。
- 上記の参照ファイルが読めない場合は、推測で進めず**即停止して読めなかった path を報告**せよ。
- 出力は日本語。プランのみを返し、ファイルを書き換えようとしないこと。


---

## 段 2 プラン起草 (codex read-only/max) (`s2-plan.md`)

## 実装プラン

基準は `1d2d298`。編集対象は `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` のみとし、docs・凍結成果物は変更しない。

### 0. 実装前に親が再裁定する事項

- P1 の archive 追加は技術的には必要。現行 checker も archive を `glob("worklog-*.md")` で扱っており、worklog のローテーション契約とも整合する。ただし、確定済みユーザー裁定の対象族を拡張するため、段 4 で明示的に再裁定してから実装する。再裁定されない場合は P1 を黙って実装せず停止する。
- brief の「`check_docs.py` 自身の `SELF_LIMITS`」は現コードと不一致。[check_docs.py:109](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:109) の対象は `docs/skill-self-improvement.md` だけで、checker 自身の上限値は存在しない。さらに `SELF_LIMITS` は [check_docs.py:149](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:149) で dispatch allowlist に混ぜられるため、ここへ `tools/check_docs.py` を足してはならない。実測値は 55,290 bytes・最長 200 chars。checker 自身の予算が本当に必要なら、親が別定数と具体的上限を裁定する。

### 1. `tools/check_docs.py`

1. [check_docs.py:16](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:16) の import 群へ `hashlib` を追加する。

2. [check_docs.py:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:78)〜87 の worklog/archive 定数の隣へ次を置く。

   - `INSIGHTS_DIR = REPO / "output" / "insights"`
   - `LITERAL_PLACEHOLDERS`: exact 3 文字列を順序固定した tuple
   - `VERBATIM_INSIGHT_SUFFIX = "-verbatim.md"`
   - `LITERAL_PLACEHOLDER_ALLOWLIST_COUNTS: dict[str, int]`

   digest は「改行終端だけを除いた論理行の UTF-8 bytes」の SHA-256 とする。strip・Unicode 正規化・path・行番号は含めない。

   既存 4 行は3種類の digestしかないため、set ではなく個数つき multiset にする。

   | digest | 期待行数 | 現在の実体 |
   |---|---:|---|
   | `37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0` | 2 | [worklog.md:75](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/worklog.md:75)、[archive:773](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/archive/worklog-phase3-0722-0724.md:773) |
   | `3beb84d709104086993083d461c6b511b63ffd595f2037c28f5c5ae91e046327` | 1 | [archive:717](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/archive/worklog-phase3-0722-0724.md:717) |
   | `c022f2e9ee8cfaf2237eafa5c30e0c772a368c953e5ccf03a29233028bbe52fd` | 1 | [e2e-real-seal.md:37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/output/insights/2026-07-24_e2e-real-seal.md:37) |

3. 対象ファイル列挙 helper を、後述 checker の直前へ追加する。

   - `docs/worklog.md` は手書き列挙し、不在・symlink・非 regular file を finding にする。
   - `docs/archive/worklog-*.md` と `output/insights/*.md` は、将来追加を自動捕捉するため sorted glob にする。
   - archive/insights の directory 不在、および現在既に実体を持つ族が空になった場合を違反にする。
   - archive の個別消失は既存の [check_docs.py:1258](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1258)〜1273 の README 索引照合も担う。
   - `LIVING_DOCS` へは追加しない。冒頭コメントどおり、living-doc lint と今回の追記型記録 lint は別 checker に保つ。

4. verbatim 判定は内容ではなく `path.name.endswith("-verbatim.md")` の完全 suffix 規約にする。単なる `"verbatim" in name` は使わない。

   実在14件はすべてこの suffix に一致する。

   `2026-07-22_direction-audit-direction-verbatim.md`、`direction-audit-quant-verbatim.md`、`env-strategy-audit-verbatim.md`、`waste-inventory-verbatim.md`、`2026-07-23_ruling-b-verbatim.md`、`t002-stage1-verbatim.md`、`t066-golden-continuation-verbatim.md`、`2026-07-24_t080-postr-audit-verbatim.md`、`t080-prediction-seal-verbatim.md`、`t086-keyset-verbatim.md`、`2026-07-25_t067-exact-residual-verbatim.md`、`t068-t077-t078-closure-verbatim.md`、`t088-floor-wrapper-verbatim.md`、`t088-official-unlock-verbatim.md`。

5. fence/inline code helper を [check_docs.py:413](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:413) の Markdown helper 群へ置く。

   - 既存 `FENCE_OPEN_RE` は [check_docs.py:265](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:265) にある。
   - fence の stateful 処理は `_top_level_items()` の [check_docs.py:447](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:447)〜478 に埋め込まれており、そのまま直接再利用できない。
   - closing 判定を `_is_fence_close(line, marker)` のような helper に抽出し、既存 `_top_level_items()` と新 checker の双方から使う。opener と同じ文字、opener 以上の長さ、indent 3 以下、後続は空白だけ、という現挙動を維持する。
   - EOF まで閉じなかった fence は「残りを黙って除外」せず、それ自体を finding にする。
   - inline code は行内の backtick run を左から調べ、同じ長さの closing run が存在する区間だけ空白へマスクする。未対応 run、escaped run、行をまたぐ span はマスクしない。行全体を backtick の有無だけで除外してはならない。
   - inline span と同じ行に可視 placeholder が残れば、その可視分は検出する。HTML comment は除外対象に追加しない。

6. `_check_literal_placeholder_guard(findings: list[str])` を [check_docs.py:601](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:601) の `_check_backlog_guard` の直前へ追加する。既存の `_check_*_guard` 命名規約に合わせる。

   各対象行について次を行う。

   - well-formed fence 外の行だけを取り出す。
   - inline code span をマスク後、exact 3 文字列を `in`/`count` で調べる。
   - visible hit がある行は、マスク前の論理行から digest を計算する。
   - allowlist 外 digest は `"{rel}:{lineno}: 未許可のリテラル placeholder ..."` を `findings.append()`。
   - allowlist digest でも登録個数を超えれば、その行を違反にする。
   - 全走査後、観測した allowlist digest multiset と登録 multiset を完全一致比較する。登録行が消えた、内容が変わった、対象外ファイルへ移った場合は `expected=N, actual=M` を finding にする。
   - 1行に複数 token があっても finding は行単位で1件とし、検出 token と個数を診断へ載せる。

7. [check_docs.py:1245](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1245) の `_check_backlog_guard(findings)` の直前で新 checker を呼ぶ。直接 print/exit せず、既存の [check_docs.py:1300](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1300)〜1306 の集約報告と rc=1 に乗せる。

### 2. `orchestrator/tests/test_check_docs.py`

1. [test_check_docs.py:35](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:35) の合成 fixture 定数へ、production 定数から導出しない独立な legacy 4 行 fixtureを追加する。重複行も2回書く。

2. [test_check_docs.py:229](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:229) の `_build_min_repo()` で次を用意する。

   - `output/insights/synthetic-legacy.md` に legacy 4 行。
   - 日付が現行 worklog より古く、空遷移として構造的に有効な synthetic archive worklog。
   - archive README にそのファイルを掲載。
   - これにより既存 `test_synthetic_repo_baseline_clean` が、allowlist の実在確認を含めて緑になる。

3. 現在の [test_check_docs.py:736](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:736) の backlog tests 前に、次の no-argument nodeid を追加する。pytest fixture や新たな parametrized test は使わず、[test_check_docs.py:1579](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:1579) の素の runner でも全件実行できる形にする。

   - `test_placeholder_guard_existing_lines_require_allowlist`  
     production allowlist を `try/finally` で一時的に空へ差し替え、新 checker 単体が既存4行を4件検出することを固定する。
   - `test_placeholder_guard_new_literal_is_violation_in_each_family`  
     worklog、valid archive、非-verbatim insight の各族へ新規行を別々に加え、各ケースが赤になることを確認する。
   - `test_placeholder_guard_allowlist_line_removal_is_violation`  
     synthetic legacy 行を1件削除し、登録個数不足が赤になることを確認する。
   - `test_placeholder_guard_allowlist_multiplicity_is_exact`  
     digest が同じ legacy 行を追加し、登録超過が赤になることを確認する。
   - `test_placeholder_guard_allowlist_survives_rotation`  
     legacy 行を insight から archive へ移して総 multiset を維持し、path 非依存性を確認する。
   - `test_placeholder_guard_inline_code_mentions_are_clean`  
     exact 3文字列を対応する1重・2重・3重 backtick 内に置き、非-verbatim insight でも緑になることを確認する。
   - `test_placeholder_guard_inline_code_does_not_mask_visible_literal`  
     同じ行の inline code 外に置いた token は赤になることを確認する。
   - `test_placeholder_guard_unmatched_backtick_does_not_hide_literal`  
     closing のない backtick 後の token が赤になることを確認する。
   - `test_placeholder_guard_fenced_mentions_are_clean`  
     正しく閉じた backtick fence と tilde fence 内の説明例は緑。
   - `test_placeholder_guard_unclosed_fence_is_violation`  
     未閉鎖 fence が tail を隠して緑にならないことを固定する。
   - `test_placeholder_guard_verbatim_suffix_only`  
     `sample-verbatim.md` は緑、`sample-verbatim-copy.md` は赤。
   - `test_placeholder_guard_exact_literals_only`  
     `<結果を反映>`、`<反映済み>` など非 exact 類似表現は緑。
   - `test_placeholder_guard_missing_target_family_is_violation`  
     insights directory または eligible `.md` 全体の消失が黙って skip されないことを確認する。

4. [test_check_docs.py:1569](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:1569) の `test_real_repo_clean` は残し、既存4行・inline説明・verbatim除外を含む実 repo 全体の統合確認に使う。

### 3. P1〜P6 への異議

- **P1:** 技術的には採用。ただし確定済みユーザー裁定からの scope 拡張なので、段4の再裁定前に実装しない。
- **P2:** 採用。ただし「backtick がある行を丸ごと除外」は却下し、対応する inline spanだけをマスクする。
- **P3:** 単純な digest set には異議あり。既存2行が同一 digest なので、`digest -> expected count` が必要。
- **P4:** well-formed fence の除外は採用。ただし現 parser 同様に未閉鎖 fence を EOF まで黙って除外する実装には異議あり。未閉鎖自体を違反にする。
- **P5:** 異議なし。編集面が2ファイルで、逐次実装が妥当。
- **P6:** P1 の再裁定が記録されることを条件に異議なし。再裁定なしに archive を追加する場合、D起票では代替できずユーザー裁定待ち。

### 4. 偽陽性・偽陰性の扱い

| ケース | 扱い |
|---|---|
| inline code・well-formed fence・`*-verbatim.md` 内 | 除外として受容 |
| unmatched backtick・未閉鎖 fence・HTML comment 内 | fail-closed で検出 |
| inline code と実 placeholder が同じ行に混在 | 可視 placeholder を検出 |
| 複数行 inline code span | 行単位では除外せず、偽陽性を受容 |
| `<結果を反映>` 等の類似表現、Unicode lookalike、改行で分断された token | exact 3文字列裁定の外として非検出を受容 |
| 正常な結果欄が token を backtick/fence で囲む | 説明との機械識別不能な偽陰性として受容。運用上、結果欄で引用形式にしない |
| 通常 insight を誤って `-verbatim.md` と命名 | filename 契約上の偽陰性として受容。suffix 完全一致に限定して範囲を狭める |
| legacy 1行削除と同一行の別場所への同時追加 | path 非依存 multisetでは識別不能だが、対象内の残存行数・内容は不変なので受容 |
| legacy 行の空白・周辺文言・token数変更 | digest 不一致と登録不足の双方で遮断 |

検証時は各コマンドを単独実行して rc を直接確認し、パイプへ流さない。今回の起草では pytest を含むテストは実行していない。


---

## 段 3 敵対相談 レンズ A = 恒真ゲート・抜け穴 (`s3-lens-a.md`)

静的判定は **NO-GO（BLOCKER 5 / MUST 4 / nit 0）**。テストは実行していない。以下の「緑になる」は、プランから導ける反例であり実測結果ではない。

### 1. BLOCKER — exact 3 のうち長い 2 文字列を実装し忘れても positive control が通る

**所見**: 提案テストは実質 `〈反映〉` だけの検査に縮退しても緑になり得る。

**場所**: [s2-plan.md:81–104](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s2-plan.md:81)、[worklog archive:717](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/archive/worklog-phase3-0722-0724.md:717)、[e2e-real-seal.md:37](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/output/insights/2026-07-24_e2e-real-seal.md:37)

**なぜ real か**: 既存 4 行はすべて `〈反映〉` を含む。長い token を持つ 2 行にも、同じ行内に別途 `〈反映〉` がある。したがって実装が誤って `LITERAL_PLACEHOLDERS = ("〈反映〉",)` だけでも、allowlist を空にするテストは予定どおり 4 行を検出する。各族テストも代表 token に `〈反映〉` を使えば通る。inline/fence のテストは負制御なので、長い token の欠落を検出しない（F27/F28/F33 型）。

**成果物影響**: `〈受入結果を反映〉` または `〈受入全走結果を反映〉` だけを持つ新規レポート行が受理され、検査結果・材料レポート・worklog 台帳に空証明が残る。

**代案**: [test_check_docs.py:736](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:736) の直前に、test-local に hardcode した 3 行を置き、各行が対象 token を一つだけ含む `test_placeholder_guard_each_literal_independently_fires` を追加する。production tuple から入力を作らず、各 token の削除変異がその node を落とすことを要求する。

### 2. BLOCKER — inline code / fence 除外は検査を記録者任意の opt-out にする

**所見**: P2/P4 は偽陽性除去ではなく、F36 と同じ結果欄を一文字の装飾で非検出にする抜け穴である。

**場所**: [s2-plan.md:45–52](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s2-plan.md:45)、`s2-plan.md:91–100,123–128`、[failures.md:514–534](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/failures.md:514)

**なぜ real か**: 次はいずれも結果欄として読めるが、計画どおりなら緑になる。

```markdown
- **受入**: `〈受入結果を反映〉`
```

````markdown
- **検査**:
  ```text
  repo scan invariant: 〈反映〉
  ```
````

将来の記録者が Markdown の可読性のため token を code 化するだけで検査を回避できる。これは故意の攻撃を要しない。

**成果物影響**: 未実施の受入・検査がレポートと台帳で実施済みに見え、wave の受理判断と検査結果参照が誤って閉じる。

**代案**: [check_docs.py:601](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:601) に追加する checker は対象行の raw text を検査し、generic な inline/fence 除外を設けない。現在の説明的言及だけを安定した記録 ID と行 digest で例外化し、将来の説明は定数名 `LITERAL_PLACEHOLDERS` や F36 節参照で書かせる。予定している inline/fence clean テストは、結果欄では赤になるテストへ反転する。

### 3. BLOCKER — `-verbatim.md` は誰でも作れる全ファイル除外スイッチである

**所見**: ファイル名 suffix だけの verbatim 判定は、通常 insight を検査外へ移す公然の回避 API になる。

**場所**: [s2-plan.md:39–43](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s2-plan.md:39)、`s2-plan.md:101–102,129`

**なぜ real か**: 次の新規ファイルは内容にかかわらず全体が除外される。

```text
output/insights/2026-08-01_acceptance-verbatim.md
- **受入**: 〈反映〉
```

`sample-verbatim.md は緑` というテストは、この抜け穴を仕様として固定する。suffix が「逐語である」という内容・provenance を証明していない（F9/F36 型）。

**成果物影響**: 通常の材料レポートを verbatim 名で保存するだけで placeholder を含むレポートが受理集合へ入る。

**代案**: `check_docs.py:78–87` に既存 14 件だけの `path -> file digest` exemption 台帳を置き、実在・内容一致を検査する。より強くするなら全 verbatim も走査し、実際に literal を含む既知行だけを例外登録する。`sample-verbatim.md` は未登録なら赤、新規 exemption の digest 不一致も赤にする。

### 4. BLOCKER — path 非依存の全域 multiset は legacy 行の移植・身代わりを正当化する

**所見**: P3 の global line-digest multiset は、元の記録を消して同じ行を別記録へ置けば完全一致のまま通る。

**場所**: [s2-plan.md:19–30](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s2-plan.md:19)、`s2-plan.md:63,89–90,130`、[worklog.md:45–50](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/worklog.md:45)

**なぜ real か**: ローテーション時に現在の legacy 行を本来の H2 エントリから落とし、同じ bytes を新しい H2 の結果欄へ置けば、digest と総数は不変で検査は緑になる。計画の「insight から archive へ行だけを移して緑」は正規の worklog ローテーションではなく、まさにこの横流しを positive behavior として固定している（F32/F33 型）。

**成果物影響**: 例外の受理集合が「過去の特定記録」から「repo 内の任意の同一行」へ拡大し、新しいレポートが legacy exemption を盗用できる。元台帳の参照先も失われる。

**代案**: allowlist key を `(record_kind, stable_record_id, line_sha256)` にする。worklog は直前 H2 title/T-ID、insight は安定 basename または文書 ID を使う。ローテーションテストは H2 エントリ全体を current→archive へ移し、別 H2 への同一行 replay は赤にする。

### 5. MUST — allowlist の「内容一致」は提案テストで証明されていない

**所見**: 行削除と個数超過だけでは、実装が digest を無視して総 hit 数だけ数えても全 positive control を満たせる。

**場所**: [s2-plan.md:21](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s2-plan.md:21)、`s2-plan.md:70,85–88,131`

**なぜ real か**: 誤実装が「許可数は合計 4」とだけ検査した場合、baseline=4、削除=3、追加=5、rotation=4 となり、予定されたテスト結果をすべて再現できる。legacy 行の token 外を別の主張へ書き換えても hit 数は 4 のままで緑になる（F27/F32 型）。

**成果物影響**: allowlist 登録行の受入結果・検査名・緑/赤などを改変しても、台帳とレポートが正当な legacy bytes として受理される。

**代案**: `test_check_docs.py:736` 前に、legacy 行の token を維持したまま周辺文言を 1 byte 変更し、「未許可 digest」と「登録 digest 不足」の双方を exact に確認する node を追加する。production の hash 値・期待個数も test-local な固定値と照合する。

### 6. MUST — 対象族の列挙 control が「新規 member の自動捕捉」と自 checker の発火を分離していない

**所見**: 既存ファイルへの追記や単なる rc=1 だけでは、手書き列挙への縮退と別 checker による masking を検出できない。

**場所**: [s2-plan.md:31–36](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s2-plan.md:31)、`s2-plan.md:72–84,105–106`、[check_docs.py:606–613](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:606)、[check_docs.py:1247–1273](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1247)

**なぜ real か**: archive/insight の既存 fixture に行を足すだけなら、既知ファイルしか走査しない誤実装でも通る。worklog 不在は既存 backlog guard、archive 不整合は既存 README checker も赤にするため、「rc が赤」だけでは新 enumerator が発火した証拠にならない（F9/F28 型）。

**成果物影響**: 将来追加された worklog archive または insight が走査対象へ入らず、そのレポート内 placeholder が検査結果 0 件のまま受理される。

**代案**: テスト中に baseline に存在しない `docs/archive/worklog-future.md` と `output/insights/future.md` を新設する。archive README も正しく更新して既存 checker を緑に保ち、新 checker 固有の `path:line` finding が 1 件だけ増えることを確認する。各 directory の不在・空・symlink・非 regular も helper 単体で固有 finding を検査する。

### 7. MUST — helper の positive control と `main()` の rc 配線 control が分離されていない

**所見**: checker 本体が正しくても `main()` の呼出しを忘れた実装を落とす nodeid が明記されていない。

**場所**: [s2-plan.md:54–66](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s2-plan.md:54)、`s2-plan.md:81–108`、[check_docs.py:1245](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1245)、[test_check_docs.py:1569](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:1569)

**なぜ real か**: line 82 は checker 単体呼出しを明記している。一方 `test_real_repo_clean` は負制御なので、`_check_literal_placeholder_guard(findings)` の main 呼出しを削除しても緑である。残りの新規 tests も helper 直呼びで実装されれば、判定核は健全だが live CLI は常に 0 という F21 型になる。

**成果物影響**: `python3 tools/check_docs.py` が不正なレポートに rc=0 を返し、wave の検査結果と受理判断が直接反転する。

**代案**: `test_placeholder_guard_main_propagates_finding_to_rc` を追加し、[test_check_docs.py:258–262](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:258) の pipe なし subprocess 経由で、rc=1・違反件数・新 checker 固有 finding を同時に assert する。main 呼出し削除変異でこの node だけが落ちる形にする（F21/F37）。

### 8. MUST — archive 不在 finding は既存の無条件 read で報告前に潰れる

**所見**: 「archive directory 不在を finding にする」というプランは、後続コードを直さない限り集約報告へ到達しない。

**場所**: [s2-plan.md:33–36](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s2-plan.md:33)、[check_docs.py:1247](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1247)、[check_docs.py:1300–1306](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1300)

**なぜ real か**: 新 checker が `docs/archive` 不在 finding を append しても、その直後の `ARCHIVE_README.read_text()` が例外を投げ、集約表示へ進まない。対象ファイルの読取失敗・不正 UTF-8も同様に、捕捉しなければ traceback だけになる。

**成果物影響**: rc 自体は非 0 でも、検査結果の件数・原因・対象 path が失われ、task-run やレポートから placeholder guard の発火を参照できない。

**代案**: `check_docs.py:1247` を README の存在・regular-file・読取例外を findings に積む分岐へ変更し、`iterdir()` もその成功時だけ行う。新 checker の各 `read_text()` も `OSError` / `UnicodeError` を固有 finding に変換する。subprocess test は traceback ではなく集約 header を要求する。

### 9. BLOCKER — exact 3 検査は F36 の再発クラスを防がず、既知の表記だけを防ぐ

**所見**: この gate を「F36 再発防止」と認証するのは過大主張であり、2026-07-25 の予測値先書きには無力である。

**場所**: [s2-plan.md:16–18](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s2-plan.md:16)、`s2-plan.md:103–104,127`、[failures.md:537–542](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/failures.md:537)、[core.md:84–85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/core.md:84)

**なぜ real か**: プラン自身が次を緑と固定する。

```markdown
- **受入**: <結果を反映>
- **検査**: check_ai_provenance 338 件違反なし。
- **受入**: &lt;反映&gt;
```

1 行目は意味的に同じ placeholder、2 行目は F36 再発と同じ未実測予測値、3 行目は rendered Markdown では `〈反映〉` に見える。exact raw 3 文字列ではいずれも検出できない。

**成果物影響**: 未実測の具体値が検査結果・worklog・材料レポートへ入り、実測値として後続の受理判断や証拠参照に使われる。

**代案**: T-094 は「既知 3 literal の狭い回帰 lint」と明記し、F36 全体を閉じたと主張しない。F36 の機械的閉鎖には、結果欄を構造化し、HEAD・終了時刻・exit status・出力 digest を持つ実走 artifact への参照を必須にする別 checker が必要である。少なくとも `test_placeholder_guard_exact_literals_only` は結果欄の `<結果を反映>` を赤に反転し、一般 prose の誤検出回避は構文位置で行う。

## refuted と考える親の主張

- **N-5**: refuted。将来の記録が exact 3 文字列を「必ず含む」は誤り。定数名・F36 節参照・「三つの禁止 literal」で記述できる。
- **P2**: refuted。generic inline-code 除外は説明用免除ではなく記録者任意の bypass。
- **P3**: refuted（少なくとも s2-plan の global multiset 解釈）。N-4 のローテーション問題は stable record ID で解け、任意移植可能な pathless digest を必要としない。
- **P4**: refuted。generic fence 除外も F36 の結果欄をそのまま隠す。
- **番号外だが、exact 3 gate が F36 の再発を防ぐという解釈**: refuted。防げるのは既知 literal 形だけで、予測値先書きは検出できない。

N-1〜N-4 の観測事実、および P1/P5/P6 は、このレンズの静的資料からは refute しない。


---

## 段 3 敵対相談 レンズ B = 族設計・全層 scope・運用寿命 (`s3-lens-b.md`)

結論は **NO-GO**。archive 追加自体は必要だが、現プランのままでは F36 恒久対応 2 を充足しない。

### 1. 同じ記録 producer が書く成果物の大半が検査 scope 外である

- **所見**: worklog と一部 Markdown だけを検査しても、dev-wave 親が同じ段で書く phase・decision・failure・JSON 台帳には同型欠陥を残せる。
- **場所**: `.claude/commands/dev-wave.md:31-50`、`docs/dev-wave/core.md:78-86`、`CLAUDE.md:153-157`、`brief.md:89`、`s2-plan.md:31-39`
- **なぜ real か**: producer は次のとおり。

  | producer | 書く成果物 | 現プラン |
  |---|---|---|
  | dev-wave 親 | `docs/handoff/*.md`、`docs/worklog.md`→archive、`docs/phase3.md`、`docs/decisions.md`、`docs/failures.md`、insight Markdown、変異台帳 JSON | worklog/archiveと一部MDだけ |
  | `/rulings`・一般クラス2/3 | handoff、worklog、phase、裁定後の decisions/failures | ほぼ対象外 |
  | task-run CLI | `task.json`、`events.jsonl`、集計 report | 対象外。ただし結果値は構造化され、自由文は objective だけ |
  | campaign/selector | lock、WAL、report、freeze JSON、LLM rationale | 対象外 |

  `output/insights/` 140 件の内訳は Markdown 106、JSON 33、patch 1。JSON のうち11件は変異台帳で、例えば `output/insights/2026-07-25_t067-exact-residual-mutation-ledger.json:7` が実際に全走結果を記録する。ここへ `"negative_control": "〈受入結果を反映〉"` を置いても `*.md` glob は無視し、check_docs は他に違反がなければ `tools/check_docs.py:1300-1306` の「違反なし」へ進む。同じことは受入値を持つ `docs/phase3.md:495-507` や `docs/decisions.md:2934-2935` でも起こる。
- **成果物影響**: certified 数値自体は直ちに変わらないが、未実測の変異台帳・phase 完了記録・decision が受理され、次 wave がそれを完了済み証拠として参照する。レポート・台帳の受理集合と次タスク選択が変わる。
- **scope 判定**: `phase3/decisions/failures`、変異台帳 JSON、handoff は、確定済み対象族を超えるため**裁定パッケージ候補**。黙って本 wave に実装してはならない。
- **代案**: `tools/check_docs.py:78-87` 近傍に claim-bearing artifact 族を明示し、少なくとも `*-mutation-ledger.json` と phase/decision/failure を別候補として裁定する。active handoff は未完状態を正当に含み得るため、全 worktree scan ではなく staged-record commit 用検査を別設計する。

### 2. `-verbatim.md` suffix は実在する成果物の役割境界と一致しない

- **所見**: suffix によるファイル丸ごとの verbatim 除外は、非逐語を逃がし、逐語を誤検出する双方向の誤分類である。
- **場所**: `s2-plan.md:39-43,101-102,128-129`、`output/README.md:54-70`、`orchestrator/tests/test_frozen_artifacts.py:33-56`
- **なぜ real か**: 106 Markdown を命名・H1・冒頭役割で照合すると、少なくとも47件が逐語または逐語混合である。内訳は `-verbatim.md` 14件、`-consultations.md` 16件、`-loop.md` 7件、その他の逐語明記10件。したがって plan は33件以上の逐語/混合成果物を通常文書として走査する。

  逆方向も壊れている。`output/insights/2026-07-23_t066-golden-continuation-verbatim.md:3-11` は受入全走と変異台帳を持ち、`output/insights/2026-07-25_t088-floor-wrapper-verbatim.md:1488-1500` には実際の「検査結果」がある。これらは純粋な raw transcript ではない。そこへ真の placeholder が入っても suffix だけで全ファイルが免除される。

  さらに `FROZEN_MANIFEST` の逐語3件は `*-consultations.md` で、suffix を持たない。現在 hit がゼロなだけで、将来 prompt 原文が exact 文字列を非 backtick で含めば、変更不能な凍結逐語が偽陽性になる。
- **成果物影響**: 通常レポートを `-verbatim.md` と名付けるだけで未実測結果が受理される一方、非suffixの凍結逐語が repo 全体を赤にする。レポート受理集合と検査の可用性が双方で変わる。
- **scope 判定**: **本 wave scope 内の must-fix**。非-verbatim境界を実装する以上、分類器の誤りは外へ送れない。
- **代案**: `s2-plan.md:39-43` の suffix 判定を捨てる。新規成果物には検査可能な `artifact_kind: verbatim` を要求し、純逐語 payload と親の要約・受入節を分離する。既存・凍結ファイルは bytes を直せないため、pathと全ファイルSHA-256に束縛した legacy分類台帳を使う。suffixだけ、H1だけ、`authority:none` だけには依存しない。

### 3. backtick/fence 除外は自己言及対策ではなく、誰でも使える gate bypass である

- **所見**: Markdownの見た目を変えるだけで真の placeholder を不可視化できるため、P2/P4は規律2に反する受理集合拡大である。
- **場所**: `s2-plan.md:45-53,91-100,123-128`、`tools/check_docs.py:265,442-478`、`CLAUDE.md:65-69`
- **なぜ real か**: 非verbatim insight に `- **受入**: \`〈反映〉\`` と書けば、意味上は未記入の結果欄だが inline mask が消して緑にする。plan 自身も `s2-plan.md:128` でこの偽陰性を認め、「運用上、結果欄で引用形式にしない」と人間規律へ押し戻している。これは機械検出の充足ではない。fenceも同じで、結果一覧を code block に置くだけで逃げられる。

  加えて既存 `FENCE_OPEN_RE` は backtick opener の後続を無条件に許すため、plan がいう「well-formed fence」より広い行を opener と扱う。除外を残すなら parser 自体にも別の偽陰性がある。
- **成果物影響**: 未実測の受入結果を持つレポート・台帳が check_docs 緑として受理される。受理集合が書式だけで拡大し、記録後検査の参照が空証明になる。
- **scope 判定**: **本 wave scope 内の must-fix**。
- **代案**: 本 wave の記録では exact bytes を書かず、`LP-1〜LP-3` または `LITERAL_PLACEHOLDERS` への記号参照、`&lt;…&gt;` 表記を使う。既存の説明的言及だけは、安定した文書・entry identity付きの有限な historical exception とする。現行 wave 全体の除外は最も事故が起きやすい場所を外すので却下。backtick/fenceの全域除外も却下する。

### 4. path非依存 multiset はローテーション耐性ではなく例外権の譲渡を許す

- **所見**: P3の digest-countだけでは、過去4件の例外を将来の別レコードへ移植できる。
- **場所**: `s2-plan.md:18-29,61-64,89-90,130`、`tools/check_docs.py:324-390`
- **なぜ real か**: 同一digestの旧行を1件削除し、同じ行を新しい worklog entryへ追加すると、総multisetは不変なので緑になる。つまり「旧債務の消失」と「新しい埋め戻し失敗」が相殺される。plan は `test_placeholder_guard_allowlist_survives_rotation` で insight から archive への移動まで緑にし、実際の worklog rotation を超えた異種族間移動を仕様化している。

  N-4の「pathはrotationで変わる」は正しいが、既存コードは既に日付・連番付きentryを抽出している。例外identityを捨てる必要はない。
- **成果物影響**: 新しい未実測受入行が、古い例外の削除と抱き合わせで受理される。台帳の欠損位置とレポートの参照先が変わっても検査結果は緑のままになる。
- **scope 判定**: **本 wave scope 内の must-fix**。
- **代案**: worklog例外は `(日付, entry連番, line digest, occurrence)` に束縛し、現行→archiveだけを許す。既存の `_extract_current_entries()` / `_extract_archive_entries()` (`tools/check_docs.py:324-390`) を再利用できる。insight例外はrotation契約がないのでpath+digest固定。insight→archive移動テストは赤に反転する。

### 5. allowlistの増補権限と凍結後事故の処理が未定義である

- **所見**: 現プランは「既存4件」を普通のdictにしただけで、5件目を誰が何の根拠で許すかを決めていない。
- **場所**: `s2-plan.md:18-29,63`、`brief.md:73-81`、`orchestrator/tests/test_frozen_artifacts.py:38-56`、`docs/archive/README.md:15-19`
- **なぜ real か**: 将来、新しい insight が placeholder を含んだまま `FROZEN_MANIFEST` に追加されると、凍結hashは緑だがplaceholder検査は赤になる。発見後は、

  1. bytesを直すとfreeze違反、
  2. 実測値を埋めるとF36の捏造、
  3. digestをallowlistへ足すとgate弱体化、

  の三択になる。現在5件にhitが無いことは、将来の処理規則ではない。またarchiveのgit-history-only化で旧行が消えた場合も、count不足を直すためallowlist変更が必要になる。
- **成果物影響**: AIが「緑に戻すため」に例外を追加できる運用なら、許可される未実測レコードが単調増加する。逆に追加不能なら、凍結した1件で全記録commitが恒久的に停止する。
- **scope 判定**: allowlistの閉性と事前freeze検査は**本 wave内**。将来の凍結事故waiverと履歴削除は**裁定パッケージ**だが、処理方針なしで実装完了にしてはならない。
- **代案**: 4件を `KNOWN_LEGACY_PLACEHOLDER_DEBTS` のexact key-setとして独立テストで固定し、新規非凍結hitには例外を認めない。追加権限はユーザーの明示裁定のみ。凍結後に発見した場合は別artifactのerratumと、`path + frozen file SHA-256 + decision ref` に束縛した専用waiverに限る。一般line digestへ足さない。check_docsの成功表示も「未許可hitなし、既知債務4行」の意味に限定する。この長期waiver契約は `docs/skill-self-improvement.md:22-33` がいう設計/interface判断なので、P6に反してD記録が必要である。

### 6. campaign JSONには別の生きた free-text placeholder 経路がある

- **所見**: certified側のLLM rationaleは非空文字列しか検証せず、同じliteralを有効な証拠としてsealできる。
- **場所**: `orchestrator/campaign/s8b_selector_output.py:83-121`、`orchestrator/campaign/s8b_selector_output_schema.json:4-12`、`output/s8b-freeze/selector_predictions.json:43-67`
- **なぜ real か**: selectorが `{"schema_version":"8b-selector-output/v1","choice_id":"c03","rationale":"〈反映〉"}` を返すと、choiceはenum内、rationaleは非空かつ2000字以下なので parser は受理する。runnerはそのrationaleをfreeze JSONへsealする。check_docsのMarkdown globは関与しない。
- **成果物影響**: `choice_id` の値自体は変わらなくても、valid prediction rowの受理集合に根拠未記入の行が入り、材料レポート・proof参照が空になる。
- **scope 判定**: **裁定パッケージ候補**。docs lintへcampaign JSONを黙って混ぜてはならない。task-runは結果値が構造化され、自由文がobjectiveだけなので、現時点では同じ欠陥として扱わない。`output/campaigns/*/insights/` は契約上存在するが現物0件なので、発火時候補に留める。
- **代案**: `s8b_selector_output.py:110-116` のproducer validatorでsentinelを拒否し、freeze前テストを置く。campaignのenum/数値/WAL全体への文字列grepには一般化しない。

### 7. 現プランのままF36を「実体化済み」に更新すると恒真な保証になる

- **所見**: backtick・suffix・JSON・別層を通す現設計はF36恒久対応2を充足せず、台帳だけ閉じれば空証明になる。
- **場所**: `docs/failures.md:8-16,530-542`、`brief.md:89`、`s2-plan.md:3,119-131`
- **なぜ real か**: F36は現在、恒久対応2を「未実装」と明記し、現行実体をDW-S07だけにしている。現プランを実装後、単に「check_docsへ追加済み」と追記すると、所見2〜4の入力はなお緑になる。さらにcheck_docsの「違反なし」は既知の真placeholder 4行が存在しない意味ではなく、例外扱いされた意味にすぎない。
- **成果物影響**: failures台帳が恒久対応完了を主張すると、後続レビューはF36を閉鎖済みとして扱い、未実測レポートを許す受理集合と不正な完了参照が固定される。
- **scope 判定**: **本 wave段7のmust-fix**。
- **代案**: `docs/failures.md:15` の追記専用契約に従い、`533-535` の歴史文を上書きせず、F36末尾へ日付付きで追記する。記載は checker関数・main呼出し・positive control node・exact対象族・既知債務4件・除外/waiver契約・「hookではなく実行時detector」であることまで限定する。所見2〜5が閉じるまでは「実体化済み」と書かない。

## refuted と考える親の主張

- **N-5**: 本waveの記録がexact文字列を「必ず」含む、は誤り。rule IDやHTML entityで記録でき、自己言及のためにgateを緩める必要はない。
- **P2**: inline backtick除外は説明判定ではなく、真の結果欄にも使える一般bypass。
- **P3**: path非依存digest multisetはrotation耐性を得る代わりに例外identityを失い、新旧行の置換を許す。
- **P4**: fence丸ごと除外も同じ一般bypassで、既存regexは「well-formed」境界すら十分に固定しない。
- **P6**: verbatim分類と例外増補・凍結waiverは長期の受理集合/interface設計であり、D不要とはいえない。

P1のarchive追加、N-1〜N-4の実測事実はrefuteしない。ただし、それらはP2/P3を正当化しない。P5は本レンズでは反証なし。

テストは実行していない。以上は静的検査による所見である。


---

## 段 4 裁定後の確定設計 (plan v2) (`plan-v2.md`)

# plan v2 (段 4 裁定後の確定設計) — [T-094] リテラル placeholder の機械検出

親が段 3 の両レンズ NO-GO を裁定して確定した設計である。段 2 プラン (`s2-plan.md`) は
**この文書で上書きされる**。相違点は本文書を優先せよ。

## 裁定の要旨

- 段 2 プランの **fence / inline code 除外は全廃**する (両レンズ: 記録者任意の gate bypass)。
  対象行の **raw text** を検査する。Markdown 構文の解釈を一切行わない。
  → `FENCE_OPEN_RE` の再利用、`_is_fence_close` の抽出、`_top_level_items()` の改変は**すべて不要**。
  既存 helper を触るな。
- 段 2 プランの **verbatim suffix 除外は全廃**する (両レンズ: `-verbatim.md` は誰でも作れる
  全ファイル除外スイッチであり、実在 106 Markdown のうち 47 件以上が逐語または逐語混合で
  suffix 分類と一致しない)。`output/insights/*.md` は **全件**対象にする。
- allowlist は **path に束縛**する (段 2 プランの path 非依存 multiset は例外権の譲渡を許す)。
- 対象族に `docs/archive/worklog-*.md` を**追加**する (真の placeholder 2 件が居るため)。

## 実装 1 — `tools/check_docs.py`

### 定数 (worklog / archive 定数の隣、`WORKLOG_ROTATE_BYTES` の近傍)

1. `import hashlib` を既存 import 群へ追加。
2. `INSIGHTS_DIR = REPO / "output" / "insights"`
3. `LITERAL_PLACEHOLDERS`: exact 3 文字列の tuple。順序固定。
   コメントで「F36 恒久対応 2。正規表現への一般化は裁定で却下済み (日本語メタ変数と
   欠陥説明の引用を誤検出する)」と書く。
4. **2 つの独立した台帳**を持つ。意味を混ぜてはならない。

   - `KNOWN_PLACEHOLDER_DEBTS`: **埋め戻し失敗の残存** (F36 が retroactive な埋め戻しを禁じている
     歴史的債務)。実 repo の 4 行:
     | path | 現在の行 | 期待 occurrence |
     |---|---|---|
     | `docs/worklog.md` | 75 | 1 |
     | `docs/archive/worklog-phase3-0722-0724.md` | 717 | 1 |
     | `docs/archive/worklog-phase3-0722-0724.md` | 773 | 1 |
     | `output/insights/2026-07-24_e2e-real-seal.md` | 37 | 1 |

     注意: `docs/worklog.md:75` と `docs/archive/worklog-phase3-0722-0724.md:773` は
     **完全に同一の bytes** である (親が sha256 で実測)。path で分ければ衝突しない。

   - `KNOWN_PLACEHOLDER_MENTIONS`: **説明的言及** (placeholder について語っている行。債務ではない)。
     実 repo の 5 行:
     | path | 現在の行 |
     |---|---|
     | `docs/worklog.md` | 183 |
     | `docs/worklog.md` | 251 |
     | `docs/worklog.md` | 252 |
     | `output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md` | 380 |
     | `output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md` | 469 |

   構造はどちらも `{相対 path 文字列: {行 digest: 期待 occurrence 数}}` とする。
   **行番号は台帳に入れない** (追記でずれる)。上の表の行番号は現状の所在を示す資料であり、
   digest を計算する対象を特定するためだけに使う。

   digest = 「改行終端だけを除いた論理行の UTF-8 bytes」の SHA-256 hex。
   strip・Unicode 正規化・行番号・path を digest の入力に含めない。

5. 台絳の**閉性**をコード側で主張する定数を置く: 期待件数
   (`KNOWN_PLACEHOLDER_DEBTS` の総 occurrence = 4、`KNOWN_PLACEHOLDER_MENTIONS` の総 occurrence = 5)。
   コメントで「新規 hit に例外を認めない。台帳への追加はユーザーの明示裁定のみ」と書く。

### 対象族の列挙 helper

- `docs/worklog.md` = 手書き列挙。不在・非 regular file・symlink は finding にする。
- `docs/archive/worklog-*.md` = sorted glob。
- `output/insights/*.md` = sorted glob (**verbatim を除外しない**)。
- directory 不在、および現在実体を持つ族が空になった場合を finding にする
  (「黙って skip」を禁じる既存原則。`check_docs.py` 冒頭コメント参照)。
- `LIVING_DOCS` へは追加しない。別 checker に保つ。
- 各ファイルの読取失敗 (`OSError` / `UnicodeDecodeError`) は traceback にせず固有 finding へ変換する。

### checker 本体

`_check_literal_placeholder_guard(findings: list[str]) -> None` を `_check_backlog_guard` の直前に置く
(既存の `_check_*_guard` 命名規約に合わせる)。

各対象ファイルの各行について:

1. raw な論理行に対し `LITERAL_PLACEHOLDERS` の各文字列の出現数を数える (`str.count`)。
   1 つも無ければ次の行へ。
2. hit がある行の digest を計算する。
3. その path の 2 台帳のいずれかに digest が登録されていれば、観測 occurrence を計上する。
   登録が無ければ `"{rel}:{lineno}: 未許可のリテラル placeholder ..."` を append する。
   診断には検出された文字列とその個数を載せる (行単位で finding は 1 件)。
4. 全走査後、**台帳の登録と観測を完全一致で比較**する。
   - 登録 digest が観測されなかった (行が消えた・内容が変わった・別 path へ移った) → finding。
     `expected=N, actual=M` の形で path と digest を出す
   - 観測が登録個数を超えた → finding
   - 期待総件数 (debts=4, mentions=5) と実際の登録総数の不一致 → finding
     (台帳を黙って増減させたら赤になる)

`main()` の `_check_backlog_guard(findings)` の**直前**で呼ぶ。print / sys.exit を checker 内で
呼ばず、既存の集約報告と rc=1 に乗せる。

### 既存コードの最小修正 (これだけは触ってよい)

`main()` の `ARCHIVE_README.read_text()` (archive 索引照合の入口) は無条件 read であり、
`docs/archive/` 不在時に例外を投げて**集約報告へ到達しない**。存在・regular file・読取例外を
findings へ積む分岐に変え、`iterdir()` はその成功時だけ行う。
それ以外の既存 checker のロジックを変更してはならない。

## 実装 2 — `orchestrator/tests/test_check_docs.py`

`_build_min_repo()` の synthetic repo に、台帳の登録行に対応する実体を用意して baseline を緑に保つ
(**production 定数から fixture を導出してはならない**。test-local に literal を書く)。
synthetic archive worklog は既存の遷移・README 索引検査を満たす形にする。

次の nodeid を追加する。すべて no-argument 関数で、既存の素の runner でも実行できる形にする。
**必ず `_run_check()` の subprocess 経由 (pipe なし) で rc と finding を確認するものを含める。**

1. `test_placeholder_guard_each_literal_independently_fires`
   **最重要 (レンズ A BLOCKER 1)**。test-local に hardcode した 3 行を用意し、各行が対象 token を
   **1 つだけ**含む形にする。3 文字列のどれを実装が落としても、この node が落ちるようにする。
   production の `LITERAL_PLACEHOLDERS` から入力を組み立ててはならない。
2. `test_placeholder_guard_main_propagates_finding_to_rc`
   **必須 (レンズ A MUST 7)**。`main()` からの呼び出し削除でこの node だけが落ちる形にする。
   subprocess 経由で rc=1・違反件数 header・新 checker 固有 finding を同時に assert する。
3. `test_placeholder_guard_new_literal_is_violation_in_each_family`
   worklog / archive worklog / insights の各族へ別々に新規行を加え、各ケースが赤になる。
4. `test_placeholder_guard_detects_new_family_member`
   **必須 (レンズ A MUST 6)**。baseline に存在しない `docs/archive/worklog-<新>.md` と
   `output/insights/<新>.md` を新設し (archive README も正しく更新して既存 checker を緑に保つ)、
   新 checker 固有の finding が 1 件だけ増えることを確認する。既存ファイルへの追記だけでは
   「既知ファイルしか走査しない誤実装」を落とせない。
5. `test_placeholder_guard_registered_line_removal_is_violation`
   台帳登録行を削除すると `expected/actual` 不一致で赤になる。
6. `test_placeholder_guard_registered_line_content_change_is_violation`
   **必須 (レンズ A MUST 5)**。登録行の **token は維持したまま周辺文言を 1 byte 変更**し、
   「未許可 digest」と「登録 digest の観測不足」の両方が出ることを exact に確認する。
   総 hit 数だけ数える誤実装はこの node で落ちる。
7. `test_placeholder_guard_allowlist_is_path_bound`
   **必須 (レンズ A BLOCKER 4 / レンズ B 所見 4)**。登録行を削除し、同じ bytes を**別 path**へ
   追加する。総数は不変だが赤になることを固定する (例外権の譲渡を遮断)。
8. `test_placeholder_guard_backticked_literal_is_still_detected`
   **必須 (レンズ A BLOCKER 2 / レンズ B 所見 3)**。inline code とコードフェンスの中に置いた
   token が**赤になる**ことを固定する (除外機構がないことの positive control)。
   段 2 プランの「inline/fence は緑」テストは**この node に反転**する。
9. `test_placeholder_guard_verbatim_named_file_is_not_exempt`
   **必須 (レンズ A BLOCKER 3)**。`output/insights/<何か>-verbatim.md` に新規 placeholder を置くと
   赤になることを固定する (suffix 除外がないことの positive control)。
10. `test_placeholder_guard_ledger_size_is_pinned`
    台帳の総件数 (debts=4, mentions=5) を test-local な固定値と照合する。
    台帳を黙って増補できないことを固定する。
11. `test_placeholder_guard_missing_target_family_is_violation`
    insights directory / archive glob の消失が黙って skip されず固有 finding になる。
12. `test_placeholder_guard_non_exact_literals_are_not_detected`
    `<結果を反映>` `<反映済み>` などが緑であることを固定する。
    **docstring に「exact 3 文字列は確定裁定であり、意味的に同じ別表記・HTML entity・
    予測値の先書きは本 gate の射程外である (裁定パッケージ [T-100])」と明記せよ。**
    これは仕様の限界を可視化するための node であり、検出漏れを是とする主張ではない。

既存の `test_real_repo_clean` と `test_synthetic_repo_baseline_clean` は残す。

## 禁止事項 (実装子)

- **docs を一切編集しない。commit しない。** (親が段 7 で行う)
- 台帳へ本 plan v2 に書かれていない entry を足さない。緑にするために台帳を増補しない。
- 既存テストを弱めない。既存 checker のロジックを (上記 archive README の 1 点を除き) 変えない。
- fixture へ production 定数由来の hash を差し込まない (F27)。
- 期待値に working tree の揮発 payload (現在の commit hash、日時、件数) を焼き込まない。
- 指示にない受理集合の拡大・縮小をしない。

## 親が段 6 で打つ変異 (事前登録、DW-M01。実装子は対応不要)

| ID | 変異 | 期待 kill |
|---|---|---|
| M1 | `LITERAL_PLACEHOLDERS` から 3 番目の文字列を削除 | 1 (各 token 独立) |
| M2 | `LITERAL_PLACEHOLDERS` から 2 番目の文字列を削除 | 1 |
| M3 | `main()` の checker 呼び出しを削除 | 2 (main 配線) |
| M4 | 台帳の期待 occurrence を 1 増やす | 5 or 10 |
| M5 | 台帳 entry の digest を 1 文字変える | 6 |
| M6 | 対象族 glob から archive worklog を外す | 3 (族) |
| M7 | 対象族 glob から insights を外す | 3 (族) |
| M8 | 台帳照合から path 束縛を外す | 7 (path 束縛) |
| M9 | digest 計算で行を `strip()` する | 6 (内容変更) |
| M10 | checker の `findings.append` を no-op にする | 全 positive control |


---

## 段 5 実装子の完了報告 (`s5-impl.md`)

実装完了です。変更は指定された 2 ファイルだけで、docs 編集・git add・commit はしていません。

- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:92)
- [test_check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:411)

## 受理・拒否挙動

変更前は placeholder 専用検査がなく、exact 3 文字列は、それ自体を理由には拒否されませんでした。

変更後は以下を新たに拒否します。

- `docs/worklog.md`
- `docs/archive/worklog-*.md`
- 全 `output/insights/*.md`（`-verbatim.md` も対象）
- raw text 中の `〈反映〉`、`〈受入結果を反映〉`、`〈受入全走結果を反映〉`
- backtick、code fence 内も除外しない
- 新規ファイルも glob で自動検出
- 登録行の消失・内容変更・別 path への移動・期待数超過
- 対象 directory／族の消失、読取不能
- archive README 不在時は traceback ではなく集約 finding＋rc=1

引き続き本 gate が受理するものは、台帳 9 entry と、`<結果を反映>`／`<反映済み>`／HTML entity／予測値先書きなどの非 exact 表記です。対象 3 族以外も射程外です。

## 検証結果

実 repo：

```text
python3 tools/check_docs.py
check_docs: 違反なし
rc=0
```

全テスト：

```text
python3 -m pytest orchestrator/tests/test_check_docs.py -q -rf
99 passed in 8.03s
rc=0
```

追加 12 nodeid の明示走は `12 passed / rc=0`：

1. `test_placeholder_guard_each_literal_independently_fires`
2. `test_placeholder_guard_main_propagates_finding_to_rc`
3. `test_placeholder_guard_new_literal_is_violation_in_each_family`
4. `test_placeholder_guard_detects_new_family_member`
5. `test_placeholder_guard_registered_line_removal_is_violation`
6. `test_placeholder_guard_registered_line_content_change_is_violation`
7. `test_placeholder_guard_allowlist_is_path_bound`
8. `test_placeholder_guard_backticked_literal_is_still_detected`
9. `test_placeholder_guard_verbatim_named_file_is_not_exempt`
10. `test_placeholder_guard_ledger_size_is_pinned`
11. `test_placeholder_guard_missing_target_family_is_violation`
12. `test_placeholder_guard_non_exact_literals_are_not_detected`

素の runner も `99 passed / 0 failed / rc=0`、`check_codex_agents.py` も rc=0、`git diff --check` も問題なしです。

期待していた赤は 0 件でした。初回全走では shared fixture の置換により既存 backlog 3 nodeid が赤になりましたが、回帰として fixture を修正し、最終全走で解消済みです。

## 台帳 9 entry

| 種別 | path | SHA-256 digest |
|---|---|---|
| debt | `docs/worklog.md` | `37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0` |
| debt | `docs/archive/worklog-phase3-0722-0724.md` | `3beb84d709104086993083d461c6b511b63ffd595f2037c28f5c5ae91e046327` |
| debt | `docs/archive/worklog-phase3-0722-0724.md` | `37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0` |
| debt | `output/insights/2026-07-24_e2e-real-seal.md` | `c022f2e9ee8cfaf2237eafa5c30e0c772a368c953e5ccf03a29233028bbe52fd` |
| mention | `docs/worklog.md` | `abdbb38938a76268b5cf63c13309339f58f0cc996deaa13db39c3786e2f3b866` |
| mention | `docs/worklog.md` | `80101b39632c395324f424bc9929db7a5c5b76c66b21d61e30afd52434f097ce` |
| mention | `docs/worklog.md` | `9162d9fc17d08b52b54c4f4b1adb96a3b614ed4d944ac955de27bb0ea5b539e5` |
| mention | `output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md` | `90d8e1f6a7f7229085d78f91ddc7bc91155bbe1ec39b44aaae2b2809daaaf5d9` |
| mention | `output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md` | `c66c4f6e14de10c369167108971c74fd0d1462b6a4489792efae907c5d02875c` |

## 静的な波及可能性

直接 import／起動・制御する所有外箇所：

- `tools/task_run_check.py`：`docs-check` launcher
- `tools/dev_waves/cli.py`：docs check spec の生成
- `tools/dev_waves/checker.py`：check_docs の識別・実行順制御
- `tools/dev_waves/daemon.py`：exactly-once 検証
- `tools/task_runs/cli.py`、`tools/task_runs/schema.py`：`docs-check` 結果の記録 schema

consumer tests：

- `test_dev_waves_cli.py`
- `test_dev_waves_checker.py`
- `test_dev_waves_git_state.py`
- `test_dev_waves_integration.py`
- `test_run_tests_task_run.py`

これらは今後、対象 3 族に未許可 placeholder がある場合に従来より rc=1 を受け取ります。CLI・引数・出力 header の既存インターフェースは変更していません。


---

## 段 6 敵対レビュー A (`s6-review-a.md`)

結論は **NO-GO（must-fix 7 / backlog 1 / nit 0）**。pytest・素の runner・変異実走は行っていない。以下の kill / survive はコードと assertion からの静的判定である。

確認済みの適合点:

- `git status` は `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` の 2 ファイルだけ。docs 編集なし。
- fence / inline-code の解釈、verbatim suffix 除外はない。
- 台帳は plan v2 どおり debts=4、mentions=5。9 digest すべて現行行と一致し、追加 entry はない。
- `main()` は `_check_backlog_guard()` の直前で新 checker を呼ぶ。
- archive README 対応以外の既存 checker ロジック変更は見当たらない。
- 現行 9 行は LF。BOM なし。末尾空白を持つ mention 1 行も digest に含まれている。

指定された主要テストの静的評価:

| node | 判定 |
|---|---|
| `each_literal_independently_fires` | 有効。test-local の 3 literal を別々に書き、各行は exact token 1 個だけ |
| `main_propagates_finding_to_rc` | 有効。helper 直呼びではなく shell pipeline なしの subprocess で rc/header/finding を検査 |
| `detects_new_family_member` | 有効。baseline にない archive/insight を作り、既存 checker の clean も分離確認 |
| `allowlist_is_path_bound` | cross-path 移植には有効。ただし所見 1 の same-path replay は残る |
| `registered_line_content_change` | 総 hit 数だけの誤実装には有効。ただし digest の空白・正規化契約は所見 4 |

### 1

- **所見**: path-bound 台帳でも、同じファイル内の別 record へ legacy 行を移植できる。
- **場所**: [tools/check_docs.py:713](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:713)、[test_check_docs.py:545](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:545)
- **なぜ real か**: `docs/worklog.md:75` の行を旧 H2 から削除し、同じ bytes のまま新しい H2 の結果欄へ置く。key は `(rel, digest)` だけなので、観測数は引き続き 1 となり finding が出ない。cross-path テストではこの移植を再現しない。
- **成果物影響**: 新 wave の未実測結果行が過去債務の例外権を継承し、worklog の受理集合と証拠参照先が変わる。
- **自己判定**: **must-fix**
- **代案**: `tools/check_docs.py:713` で worklog 台帳を `(path, H2 entry identity, digest)` に束縛し、`test_check_docs.py:545` の後へ同一 path・別 H2 移植の拒否テストを追加する。

### 2

- **所見**: 登録行の過剰複製を拒否する `actual > expected` 側に positive control がない。
- **場所**: [tools/check_docs.py:745](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:745)、[test_check_docs.py:505](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:505)
- **なぜ real か**: `if actual != expected` を `if actual < expected` に壊しても、削除・内容変更・cross-path の各テストはすべて `actual=0` を作るため assertion 条件は変わらない。登録行を同じ path 内へもう 1 本コピーすると `actual=2` だが、その誤実装では受理される。
- **成果物影響**: legacy 行を残したまま新しい結果欄へ複製でき、未実測行が worklog / report の受理集合へ増える。
- **自己判定**: **must-fix**
- **代案**: `test_check_docs.py:523` の前に、登録行を同一 path へ複製し `expected=1, actual=2` を要求する node を追加する。

### 3

- **所見**: 新 checker が読取失敗を finding 化しても、後続 backlog checker の再読が例外を投げ、集約報告へ届かない。
- **場所**: [tools/check_docs.py:693](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:693)、[tools/check_docs.py:760](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:760)、[tools/check_docs.py:861](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:861)
- **なぜ real か**: worklog または archive worklog を invalid UTF-8、directory、読取不能状態にすると、新 checker は finding を append する。その直後に `_check_backlog_guard()` が同じ path を無条件 `read_text()` し、`UnicodeDecodeError` / `IsADirectoryError` / `OSError` を再送出する。header・件数・先の finding は表示されない。
- **成果物影響**: rc は非 0 でも、検査結果の件数・対象 path・原因参照が traceback に置き換わり、task-run や材料レポートが placeholder finding を証拠として参照できない。
- **自己判定**: **must-fix**
- **代案**: plan v2 の既存変更許可を広げ、`tools/check_docs.py:760` と `:861` も例外を findings に変換する。`test_check_docs.py:619` に invalid UTF-8 と directory member の subprocess ケースを追加する。

### 4

- **所見**: digest の「改行終端だけ除去・非正規化」契約が実装とテストの双方で閉じていない。
- **場所**: [tools/check_docs.py:702](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:702)、[test_check_docs.py:523](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:523)
- **なぜ real か**: `str.splitlines()` は CR/LF だけでなく VT、FF、NEL、U+2028 等も分割する。登録行の直後、LF の前へ `U+000B + 追記` を入れると、最初の segment は元 digest のまま観測される。また `normalize("NFC", line)` を digest 前へ追加する誤実装は、現行 fixture が NFC なので既存 assertion を変えない。例えば `docs/worklog.md:183` の token 外にある `プ` を分解表現へ変えても同じ digest になる。
- **成果物影響**: 台帳が固定したはずの行 bytes を変更しても受理され、digest 参照と後続 finding の行番号が実ファイルからずれる。
- **自己判定**: **must-fix**
- **代案**: `tools/check_docs.py:694` で `newline=""` の text streamを使い、末尾の CRLF / LF / CR だけを明示除去する pure digest helper を置く。`test_check_docs.py:523` に CRLF 同値、末尾空白・BOM・NFC/NFD・VT 非同値を test-local bytes で固定する。

補足すると、現実装の通常経路では CRLF は LF と同じ digestになり、空白・BOM・valid UTF-8 非 ASCII は含まれ、Unicode 正規化もしていない。この点自体は正しい。問題は上記の追加 line-boundary と回帰 oracle の不足である。

### 5

- **所見**: 事前登録 M1/M6/M7/M9 は DW-M01 の単一理由性を満たさず、kill を検出力として数えられない。
- **場所**: [plan-v2.md:167](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/plan-v2.md:167)、[test_check_docs.py:296](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:296)、[mutation.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/mutation.md:5)
- **なぜ real か**: M1 は third-token-only の登録 mention を未観測にし、M6/M7 は既知台帳行を丸ごと未観測にし、M9 は先頭・末尾空白を持つ登録行の baseline hash を外す。いずれも悪い新規入力を受理する前に baseline 自体が fail-closed になるため、期待 node の固有検出力を示さない。
- **成果物影響**: 変異台帳が「新テストが unsound な受理を kill した」と誤記し、検査レポートの検出力参照が空証明になる。
- **自己判定**: **must-fix**
- **代案**: M6/M7 は「glob 削除」ではなく「既知 path の手書き列挙へ縮退」に再照準する。M1 は pure literal-count helper で台帳を切り離す。M9 は ledger hash 再計算との累積二地点変異、または baseline 不変の Unicode 正規化変異へ変更し、F33 どおり注入 diff を確認する。

### 6

- **所見**: `ledger_size_is_pinned` は総数しか固定せず、debts と mentions の意味的な入替えを検出しない。
- **場所**: [tools/check_docs.py:99](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:99)、[test_check_docs.py:599](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:599)
- **なぜ real か**: archive debt の `3beb…` と insight mention の `c66c…` を両 dict 間で交換すれば、総数は 4/5 のまま。走査・観測比較は両 ledger で対称なので baseline と各 positive control の判定条件も変わらない。
- **成果物影響**: 真の未充足結果が説明的言及として、説明行が歴史的債務として台帳・欠損診断へ記録され、レポートの debt 参照が逆転する。
- **自己判定**: **must-fix**
- **代案**: `test_check_docs.py:599` で、test-local の各 literal 行から独立計算した `(ledger, path, digest, count)` exact map と両 production 台帳を照合する。

### 7

- **所見**: archive / insights の directory と member は symlink・非 regular file を拒否せず、検査対象 identity を外部へ譲渡できる。
- **場所**: [tools/check_docs.py:661](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:661)、[tools/check_docs.py:670](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:670)
- **なぜ real か**: `.is_dir()` と `read_text()` は symlink を追う。登録済み insight path を、同じ登録行を持つ workspace 外ファイルへの symlink に置き換えると、rel と digest は一致し finding が出ない。FIFO の `*.md` は read で停止する可能性もある。worklog だけが明示的に symlink を拒否しており、族間で非対称である。
- **成果物影響**: report path が commit 内 bytes ではなくホスト依存 target を参照し、台帳の受理集合と proof 参照が実行機ごとに変わる。
- **自己判定**: **must-fix**
- **代案**: `tools/check_docs.py:661` で directory symlink、`:670` で各 member の symlink / 非 regular を finding にし、走査対象へ加えない。対応する helper-direct テストを `test_check_docs.py:619` に追加する。

### 8

- **所見**: exact literal 自体でも、claim-bearing Markdown が 3 対象族外なら検出されない。
- **場所**: [tools/check_docs.py:657](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:657)
- **なぜ real か**: 次を `docs/phase3.md` に置いても placeholder checker は走査しない。

  ```markdown
  - **受入**: 〈受入結果を反映〉
  ```

  同じ経路は decisions / failures / mutation-ledger JSON / selector rationale にも残る。これは plan v2 が明記した「非 exact 表記」ではなく、exact token の scope 抜けである。
- **成果物影響**: 未実測の phase 完了記録・decision・変異台帳が受理され、次 wave の task 選択と証拠参照が変わる。
- **自己判定**: **backlog** — 現 plan の対象族を超えるため、黙って本 wave に追加できない。
- **代案**: `tools/check_docs.py:657` の族拡張ではなく、T-100 の裁定で claim-bearing docs / JSON producer ごとの validator を決める。active handoff は別扱いにする。

`<結果を反映>`、HTML entity、予測値先書き等の非 exact 表記は、plan v2 が明示した既知限界なので新規 must-fix には数えていない。

## 段 3 所見の閉鎖状況

| 段 3 所見 | 状態 | 根拠 |
|---|---|---|
| A-1: 3 literal 独立検出 | **closed** | test-local・1 token/行で固定 |
| A-2: inline/fence bypass | **closed** | raw text 走査、2 context の positive control |
| A-3: verbatim suffix bypass | **closed** | 全 `*.md` 対象 |
| A-4: pathless 例外移植 | **partial** | cross-path は閉じたが same-path record replay が残る |
| A-5: 総 hit 数だけの照合 | **closed** | case 1-byte 変更で未許可＋不足を要求。ただし digest edge は新所見 4 |
| A-6: 既知ファイルだけ走査 | **closed** | baseline にない 2 family member を作る |
| A-7: main 配線 | **closed** | subprocess rc/header/finding |
| A-8: 例外で集約不能 | **partial** | archive README 不在は閉じたが worklog/archive 再読で traceback |
| A-9: exact 3 は F36 全体でない | **partial** | 限界は明記されたが scope / 予測値経路は未閉鎖 |
| B-1: 他の claim-bearing 成果物 | **partial** | 対象族は拡張されていない |
| B-2: verbatim 分類 | **closed** | suffix 除外を全廃 |
| B-3: Markdown 装飾 bypass | **closed** | Markdown 構文を解釈しない |
| B-4: pathless multiset | **partial** | path 束縛済みだが record identity 未束縛 |
| B-5: allowlist 閉性・増補権限 | **partial** | 4/5 とユーザー裁定は固定。exact ledger 意味と将来 waiver は未固定 |
| B-6: campaign JSON rationale | **partial** | 本 wave の scope 外で未変更 |
| B-7: F36 の過大な完了主張 | **partial** | docs 未編集なので未発生だが、現実装だけで F36 全体の閉鎖は主張できない |

**regressed はなし**。ただし must-fix 1〜7 を塞ぐまでは段 6 の受理と変異台帳の確定は不可と判定する。


---

## 段 6 敵対レビュー B (`s6-review-b.md`)

判定は **NO-GO（must-fix 4 / backlog 1）**。以下では対象3文字列を、`LITERAL_PLACEHOLDERS` の順に LP-1〜LP-3 と呼び、段7逐語へ安全に転記できるよう bytes は再掲しない。

pytest と `check_docs.py` 本体は実行していない。実施したのは静的検査、`git diff`、`rg`、行 SHA-256 照合のみ。

## 実 repo・既存 checker の照合結果

- 差分は想定どおり `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` の2ファイルだけ。
- 全 repo grep は **45 matches / 37 lines / 7 files**。
- 対象3族に限ると **14 literal matches / 9 logical lines / 4 files**。台帳の occurrence は literal 個数ではなく logical-line occurrence なので、債務4 + 言及5と一致する。

| file | 債務行 | 言及行 | literal matches | digest |
|---|---:|---:|---:|---|
| `docs/worklog.md` | 1 | 3 | 5 | 全一致 |
| archive worklog | 2 | 0 | 3 | 全一致 |
| E2E insight | 1 | 0 | 2 | 全一致 |
| closure verbatim | 0 | 2 | 4 | 全一致 |
| **計** | **4** | **5** | **14** | **9/9 一致** |

残り28行は `tools/check_docs.py`、テスト、対象外の `docs/failures.md` にあり、対象族の登録漏れではない。

archive 索引の健康系では、`sorted(ARCHIVE_DIR.iterdir())`、未掲載検査、墓標行除外、索引から実体への逆向き検査は変更前と同じである。synthetic archive も 1900年→現行2026年の順で、README掲載済み、次アクションは legacy ID なしなので、静的には既存 backlog 遷移を汚染しない。通常の placeholder 行と既存 checker の意図しない二重 finding も見つからなかった。

## 1. 対象ファイルの読取失敗は、後続 backlog checker でなお traceback になる

- **所見**: 新 checker が読取失敗を finding 化しても、同じ worklog/archive を既存 backlog checker が無防備に再読する。
- **場所**: [tools/check_docs.py:693](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:693)、[tools/check_docs.py:755](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:755)、[tools/check_docs.py:859](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:859)、[test_check_docs.py:619](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:619)
- **なぜ real か**: `docs/worklog.md` を directory にすると新 helper は非 regular finding を積むが、後続の `WORKLOG.read_text()` が `IsADirectoryError` を送出する。archive worklog を invalid UTF-8にすると新 helper は捕捉するが、後続の `archive_path.read_text()` が未捕捉で停止する。集約表示へ到達しない。
- **成果物影響**: task-runには違反件数・原因が残らず、plan v2の「読取失敗を固有 finding 化」が未充足になる。
- **判定**: **must-fix**
- **代案**: `tools/check_docs.py:755-764,859-863` の既存読取も共通 safe-reader 経由にする。これは plan v2 の「既存ロジックはarchive README以外変更禁止」と衝突するため、親が先に plan を改訂する。`test_check_docs.py:619` へ worklog非regular・archive invalid UTF-8の subprocess controlを追加し、集約headerと `Traceback` 不在を確認する。

## 2. path束縛台帳のローテーション手順が、正本にもコードコメントにもない

- **所見**: 例外移植は閉じたが、正規のworklogローテーションも無手順のまま必ず赤になる。
- **場所**: [tools/check_docs.py:98](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:98)、[tools/check_docs.py:713](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:713)、[docs/worklog.md:45](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/worklog.md:45)、[test_check_docs.py:545](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:545)
- **なぜ real か**: 現行worklogの登録4行を新archiveへ移すと、各行について「新pathの未許可」と「旧pathの actual=0」が1件ずつ出る。全4行なら8 findings。新pathを台帳へ単純追加すると固定総数も不一致になる。
- **成果物影響**: 将来の通常ローテーションcommitが停止し、運用者が新規waiver追加で直そうとする誘因になる。
- **判定**: **must-fix**
- **代案**: `docs/worklog.md:45-50` と `tools/check_docs.py:98-127` に、「同じ分類・digest・countを旧pathから新archive pathへ移す key migrationであり、追加・増数ではない」「READMEとtest-local fixtureも同時更新」と追記する。

## 3. 本waveの段7逐語は、そのまま凍結すると即座に自己発火する

- **所見**: worklogと材料レポートは安全に書けるが、標準の逐語凍結は現入力をそのまま複写できない。
- **場所**: [core.md:78](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/core.md:78)、[brief.md:14](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/brief.md:14)、[s3-lens-a.md:5](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s3-lens-a.md:5)、[s3-lens-b.md:16](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s3-lens-b.md:16)、[s5-impl.md:15](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/s5-impl.md:15)
- **なぜ real か**: 指定5資料をgrepすると、4ファイルの16行に26 matchesある。従来形式でこれらを `*-verbatim.md` へ複写すると、少なくとも16行が未許可 finding になる。一方、`DW-S07` の事前defangは三軸語 conjunction専用で、placeholder引用には適用されない。一般のdocs検査は記録commit後なので、凍結後に初めて発見する順序になる。
- **成果物影響**: 段7記録commitが直後に赤になるか、逐語省略・台帳増補という別の規約違反を誘発する。
- **判定**: **must-fix**
- **代案**: `core.md:81-85` をbyte-neutralに置換し、全 `output/insights/*.md` を凍結前にLP-1〜LP-3走査、hitは可逆defang＋erratum＋原文SHAで保存、凍結hashはdefang後に採取、とする。現 `docs/dev-wave/**` は23964/24000 bytesなので単純追記は不可。

worklog・材料レポートは、次の表現なら3文字列を含まないことを `rg` で確認済み。

```markdown
- **[T-094]**: `LITERAL_PLACEHOLDERS` の3要素を対象3族の raw text で拒否する gate を実装。既知債務4行・説明的言及5行は path + 行digestで固定した。
- **検証**: 段6の実測値と変異結果は同waveの変異台帳を正本とし、ここでは再掲しない。
- **材料レポート注記**: 禁止bytesは再掲せず `tools/check_docs.py` の `LITERAL_PLACEHOLDERS` を参照する。
```

## 4. 凍結後に見つかった正当な逐語hitの専用waiverが未設計

- **所見**: pre-freezeをすり抜けた凍結逐語について、bytes不変とchecker復旧を両立する経路がない。
- **場所**: [tools/check_docs.py:112](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:112)、[test_frozen_artifacts.py:34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_frozen_artifacts.py:34)、[core.md:80](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/core.md:80)
- **なぜ real か**: `*-consultations.md`には全bytes SHA固定済みの実例が3本ある。将来そこに正当な引用hitが入ると、bytes修正はfreeze違反、一般line台帳追加は例外単調増加、放置は全commit停止になる。現コメントは「ユーザー明示裁定のみ」で、waiverのidentity・erratum・失効条件を定めない。
- **成果物影響**: 凍結成果物1本がcheckerを恒久停止させるか、歴史的債務台帳を汎用免除表へ腐らせる。
- **判定**: **backlog**
- **代案**: T-100の裁定対象として、`path + frozen-file SHA-256 + decision ref + erratum ref` に束縛した専用waiverを、債務・言及台帳とは別に設計する。一般line digestへの追加で処理しない。

## 5. F36全体を「実体化済み」と書くと過大保証になる

- **所見**: 実体化済みと言えるのは対象3族のexact-literal gateだけで、F36再発クラス全体ではない。
- **場所**: [tools/check_docs.py:90](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:90)、[test_check_docs.py:654](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:654)、[docs/failures.md:530](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/failures.md:530)
- **なぜ real か**: 非exact同義表記、HTML entity、予測値先書きは明示的に受理され、phase・decision・failure・handoff・JSONも対象外である。既知債務4行自体も消えていない。
- **成果物影響**: 後続レビューがF36を閉鎖済みと誤認し、予測値先書きや対象外台帳を完了証拠として使う。
- **判定**: **must-fix**
- **代案**: `docs/failures.md:542` の後へ、既存歴史文を直さず次の3行を追記する。

```markdown
- **恒久対応 2 の現行実体 (2026-07-25)**: `tools/check_docs.py` の `_check_literal_placeholder_guard` を `main()` に結線し、`LITERAL_PLACEHOLDERS` の各要素を独立 positive control で固定した。
- 射程は `docs/worklog.md`、`docs/archive/worklog-*.md`、`output/insights/*.md` の raw text と、既知債務 4 行・説明的言及 5 行の path + 行 digest 台帳に限る。
- この exact-literal gate だけを「実体化済み」とする。既存債務の解消、同義表記・HTML entity・予測値先書き、対象外文書/JSONまで含む F36 全体の防止は保証しない（[T-100]）。
```

## Scope判定

scope逸脱はない。変更は指定2ファイルだけで、docs・campaign・selector・JSON producer・T-100層には触れていない。逆にplan v2の未実装層は所見1の「CLI全体での読取失敗集約」。段3 B-1/B-6のphase/JSON/campaign拡張は正しく裁定パッケージ側に残っている。

## 段3 BLOCKER・MUST closure

| 段3所見 | 状態 | 判定根拠 |
|---|---|---|
| A-1 各literal独立control | closed | test-local固定3入力あり |
| A-2 inline/fence bypass | closed | raw line走査、positive controlあり |
| A-3 verbatim suffix bypass | closed | 全insight Markdown走査 |
| A-4 path非依存例外 | closed | path+digest束縛、移動負例あり |
| A-5 内容一致未証明 | closed | 1-byte変更で未許可＋不足を固定 |
| A-6 新規member捕捉 | closed | 新archive/insightと他checker分離controlあり |
| A-7 main配線 | closed | subprocessでrc・header・固有finding固定 |
| A-8 読取失敗集約 | **partial** | archive README不在は閉じたが、worklog/archive member再読でtraceback |
| A-9 exact gateのF36過大主張 | **partial** | T-100射程外はテスト明記、F36追記は段7未了 |
| B-2 verbatim分類 | **partial** | suffix bypassは閉じたが、正当逐語のpre/post-freeze運用が未定義 |
| B-3 backtick/fence bypass | closed | Markdown構文を解釈しない |
| B-4 pathless multiset | closed | 例外権移植は遮断。ローテーション手順は別途must-fix |
| B-5 allowlist権限・凍結事故 | **partial** | 4/5固定とユーザー権限は閉じたが、凍結waiver未設計 |
| B-7 F36実体化の恒真化 | **partial** | コード射程は限定されたが、段7文言が未確定 |

**regressed は0件**。ただしA-8のpartialはコード修正を要するため、現状のまま段7へ進む判定にはできない。


---

## 段 6 fix round 1 の報告 (`s6-fix.md`)

実装完了です。編集は指定された 2 ファイルだけで、docs 編集・git add・commit はしていません。

- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:103)
- [test_check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:552)

## FIX 対応表

| FIX | 状態 | 対応 |
|---|---|---|
| FIX-1 | closed | key を `(scope, digest)` 化。同一/別ファイルの別 H2 replay を拒否し、H2 全体のローテーションは緑 |
| FIX-2 | closed | 同 scope 複製で `expected=1, actual=2` を exact 検査 |
| FIX-3 | closed | 共通 safe-reader を導入。worklog directory・archive invalid UTF-8 を集約報告し Traceback なし |
| FIX-4 | closed | CRLF/LF/CR のみ論理改行化。空白・BOM・NFC/NFD・VT の差を固定 |
| FIX-5 | closed | 9 entry の `(種別, scope, digest, count)` exact map を test-local literal で固定 |
| FIX-6 | closed | archive/insights の directory symlink、member symlink・非 regular を拒否して走査対象外化 |
| FIX-7 | closed | worklog ローテーション、insights key migration、新規 waiver 禁止をコードコメント化 |
| FIX-8 | closed | docs checker 全 107 node、dev-wave consumer 全 25 node が緑 |
| regressed | なし | 最終検証で回帰なし |

## 検証結果

- `python3 tools/check_docs.py` → `rc=0`
- `orchestrator/tests/test_check_docs.py` 全 nodeid → `107 passed / rc=0`
- `test_dev_waves_cli.py` + `test_dev_waves_checker.py` 全 nodeid → `25 passed / rc=0`
- 素の runner → `107 passed, 0 failed / rc=0`
- `tools/check_codex_agents.py` → `rc=0`
- `git diff --check` → `rc=0`

追加した fix nodeid は次の 8 件で、すべて上記全走および素の runner で緑です。

- `test_placeholder_guard_registered_line_duplication_is_violation`
- `test_placeholder_guard_same_file_record_replay_is_violation`
- `test_placeholder_guard_entry_rotation_keeps_ledger_green`
- `test_placeholder_guard_ledger_entries_are_pinned_exactly`
- `test_placeholder_guard_digest_line_boundary_contract`
- `test_placeholder_guard_read_failures_are_aggregated_without_traceback`
- `test_placeholder_guard_rejects_symlinked_target_directories`
- `test_placeholder_guard_rejects_symlinked_and_non_regular_members`

## 新台帳 9 entry

| 種別 | scope | digest |
|---|---|---|
| debt | `worklog-entry:4926160d0e41c9e972953e535dcce8cc1744eff78b13277cc91d722dc06129f2` | `37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0` |
| debt | `worklog-entry:0885598e3ddffd2a6a5c0424c3e6a65ba24f67048374cf3eefc064247e746eb7` | `3beb84d709104086993083d461c6b511b63ffd595f2037c28f5c5ae91e046327` |
| debt | `worklog-entry:be893df535111cf91c64c141d38afa482dbca6f0a8a829a55b36ac72d8dc79bc` | `37c4a1747e10844c9c4deb2281e644bd655cc80409b80c09c0a840297d6e8ef0` |
| debt | `insights-path:output/insights/2026-07-24_e2e-real-seal.md` | `c022f2e9ee8cfaf2237eafa5c30e0c772a368c953e5ccf03a29233028bbe52fd` |
| mention | `worklog-entry:1241aea6de50f3519f1cb497ff8b0fc07d4b4c2b76f35047d091bfb893aa685a` | `abdbb38938a76268b5cf63c13309339f58f0cc996deaa13db39c3786e2f3b866` |
| mention | `worklog-entry:825788c80a8f458dd12f5682450f134950c37fb0ea6ebbdaddfb26d9f9e95511` | `80101b39632c395324f424bc9929db7a5c5b76c66b21d61e30afd52434f097ce` |
| mention | `worklog-entry:825788c80a8f458dd12f5682450f134950c37fb0ea6ebbdaddfb26d9f9e95511` | `9162d9fc17d08b52b54c4f4b1adb96a3b614ed4d944ac955de27bb0ea5b539e5` |
| mention | `insights-path:output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md` | `90d8e1f6a7f7229085d78f91ddc7bc91155bbe1ec39b44aaae2b2809daaaf5d9` |
| mention | `insights-path:output/insights/2026-07-25_t068-t077-t078-closure-verbatim.md` | `c66c4f6e14de10c369167108971c74fd0d1462b6a4489792efae907c5d02875c` |

全 entry の count は `1` です。

## 受理・拒否挙動の差

変更前は、同じ bytes を別 H2 に移植すると受理され、H2 ごとの正常ローテーションは拒否されました。変更後は逆になり、行だけの replay は拒否、H2 全体の移動は受理します。

追加で、以下が拒否されます。

- 登録行の同 scope 内複製
- VT 等による擬似行分割
- 行末空白、BOM、Unicode 正規化差
- archive/insights の symlink・非 regular member
- 対象 directory 自体の symlink

読取失敗は Traceback ではなく、既存 header・件数を含む集約 finding と `rc=1` になります。

## 波及可能性

CLI・引数・成功時出力は変更していません。所有外 caller は `task_run_check.py`、dev-wave CLI/checker/daemon、task-run schema/CLI です。失敗時は従来の例外停止ではなく構造化された `rc=1` を受け取ります。

共有 synthetic fixture は登録 H2 を archive に配置し、日付を後続側へ移しました。production 定数由来の hash は fixture に使用していません。consumer 25 node の全走で回帰がないことを確認済みです。

事前指定された期待赤は 0 件です。作業中には fixture 順序に起因する既存 backlog node 1 件と、初版 rotation control 1 件が赤になりましたが、いずれも fixture 設計の回帰として修正し、最終全走では赤 0 件です。


---

## 段 6 焦点再レビュー round 1 (`s6-refocus.md`)

# 総合判定

**NO-GO**。fix 子の「FIX-1〜8 すべて closed」は支持できません。pytest、素の runner、`check_docs.py` 本体は実行しておらず、以下は `git diff`、`rg`、`find`、実ファイルの SHA-256 再計算による静的判定です。

確認事実:

- 差分は指定された 2 ファイルのみ。`+1076/-71`。
- 現行 worklog 族の H2 は 234 件、同一 bytes の H2 は 0 件。
- 対象族の既知 9 logical lines は、scope・digest とも台帳に 9/9 一致。
- `.git` を除く 2,895 regular files に CR byte は 0 件。CRLF / CR-only ファイルも 0 件。
- 指定された `find . -type l -not -path './.git/*' -not -path './external/*'` の結果は 0 件。現行 repo の実 symlink に対する誤 finding はない。
- 既存 test 関数は 48 件すべて残り、現在は 68 件。既存 `assert` の削除はない。
- fix 子が申告した実行結果は独立検証していない。

## 独立所見

### 1. H2 scope は同一 bytes の別エントリを識別できず、旧 path 束縛より受理集合が後退した

- **場所**: [tools/check_docs.py:745](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:745)、[test_check_docs.py:579](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:579)
- **失敗シナリオ**: 登録行を元エントリから消し、同一 bytes の H2 を同じ archive 内または別 worklog に複製して、その下へ登録行を移す。scope と行 digest は同じで `actual=1` のままになる。backlog checker も同一ファイル内の H2 重複を拒否しない。
- **ローテーション途中**: H2 エントリ全体が現行・archive の両方にあると登録行も二重になり `actual=2` で赤。一方、H2 だけが重複し、登録行が片側だけなら緑になり得る。
- **H2 前の hit**: ファイル先頭・ローテーション marker 前は `<none>` scope、marker 後かつ最初の dated H2 前は marker の hash scopeとなり、いずれも未登録なので拒否される。現行 repo に該当 hit はない。
- **成果物影響**: 過去債務の例外権を、同名 H2 の新しい結果欄へ移植できる。
- **自己判定**: **must-fix**

最終 tree で worklog 族全体の H2 raw bytes を一意にする検査、または明示的で一意な stable entry ID が必要です。

### 2. safe-reader が「読めない」を「空集合」として後続判定し、偽 finding を派生させる

- **場所**: [tools/check_docs.py:354](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:354)、[tools/check_docs.py:846](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:846)、[tools/check_docs.py:955](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:955)、[tools/check_docs.py:1435](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1435)
- **失敗シナリオ**:
  - `docs/decisions.md` が読めないと `known_d=set()` となり、living docs 内の正当な D 参照が大量に「実在しない D」と誤判定される。
  - `docs/phase3.md` が読めないと見送り台帳を空集合として worklog 遷移を続け、正当に見送り済みの ID を消失扱いする。
  - 複数 archive の一つが読めないと、そのファイルだけを除外して非隣接 archive 間の遷移を比較し得る。
- **成果物影響**: 材料レポートや task-run に、読取失敗とは別の偽の構造欠陥と誤った件数が記録される。
- **自己判定**: **must-fix**

読取不能は tri-state の「不明」として扱い、その入力に依存する後続判定を停止すべきです。

### 3. symlink を拒否した後も、後続 checker が同じ外部 target を読む

- **場所**: [tools/check_docs.py:684](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:684)、[tools/check_docs.py:838](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:838)、[tools/check_docs.py:1511](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1511)
- **失敗シナリオ**:
  - `docs/worklog.md` を外部 FIFO への symlink にすると placeholder 列挙は拒否するが、backlog checker の `_safe_read_text()` が追跡して `open()` で停止し得る。
  - `docs/archive` が symlink でも、後段の `ARCHIVE_README` 読取と `ARCHIVE_DIR.iterdir()` は親 symlink を追跡する。
- **成果物影響**: checker が host 依存 bytes を読む、または集約 header を出さず停止する。
- **自己判定**: **must-fix**

### 4. rotation node は負の oracle だけで、placeholder guard が消えても単独では常に通り得る

- **場所**: [test_check_docs.py:614](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:614)
- **失敗シナリオ**: `main()` から `_check_literal_placeholder_guard()` を削除しても、移動前後とも他 checker が clean なら 2 個の `returncode == 0` は成立する。別の main 配線テストはこれを補完するが、この node 自身は rotation の検出力を証明しない。
- **追加の弱さ**: 既に索引済みの archive path を使い、移動 H2 の「次の一手」は空なので、README 更新と遷移保存則は実質的に発火しない。
- **成果物影響**: 変異台帳がこの node を rotation 保証として引用すると空証明になる。
- **自己判定**: **must-fix**

新 archive member の作成・README 更新・非空の遷移を含め、H2 を外した行だけの移動は赤、H2 全体の移動は緑、という対を同一 node に置くべきです。

### 5. safe-reader / symlink の追加 control は「拒否後に読まない」を固定していない

- **場所**: [test_check_docs.py:874](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:874)、[test_check_docs.py:902](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:902)、[test_check_docs.py:936](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:936)
- **失敗シナリオ**:
  - backlog checker が読取不能ファイルを無言で skip しても、placeholder finding と任意件数 header があるため read-failure node は成立する。
  - symlink finding の後の `continue` を削除し、外部 target を実際に走査しても symlink 文字列が残るため両 node は成立する。
  - FIFO member は扱っていない。
- **成果物影響**: 外部読取・hang・偽の派生 finding がテストで固定されない。
- **自己判定**: **must-fix**

### 6. lone CR の positive oracle がない

- **場所**: [tools/check_docs.py:733](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:733)、[test_check_docs.py:777](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:777)
- **失敗シナリオ**: split regex から standalone `\r` だけを削除しても、追加 node は LF / CRLF / VT しか使わないため成立し得る。
- **成果物影響**: 将来の CR-only 文書で digest と logical line 番号の契約が回帰しても検出できない。
- **自己判定**: **nit**。現実装自体は CRLF / LF / CR のみを正しく分割している。

### 7. レビュー A 所見 5 の変異単一理由性は未解決

- **場所**: [plan-v2.md:167](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/plan-v2.md:167)、[mutation.md:5](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/mutation.md:5)
- **失敗シナリオ**: M1/M6/M7/M9 は悪い入力の受理より先に、既知台帳の未観測で baseline を fail-closed にする。現 diff に再照準はない。
- **成果物影響**: kill を新テスト固有の検出力として記録すると、変異台帳が空証明になる。
- **自己判定**: **must-fix**

## レビュー A/B 対応表

| 項目 | 判定 | 根拠または残る失敗シナリオ | 残分類 |
|---|---|---|---|
| A-1 同一 path・別 record replay | **regressed** | 異なる H2 は閉じたが、同一 bytes の H2 なら同一/別 path へ移植可能。旧 path key が拒否した cross-path も受理し得る | must-fix |
| A-2 `actual > expected` | **closed** | 同 scope の複製を `expected=1, actual=2` で比較 | — |
| A-3 読取失敗集約 | **partial** | traceback は閉じたが、読取不能を空集合扱いして偽 finding を派生 | must-fix |
| A-4 digest 行境界 | **closed** | 実装は CRLF/LF/CR のみ。9 entry の digest 不変 | lone CR test は nit |
| A-5 変異単一理由性 | **partial** | M1/M6/M7/M9 が未再照準 | must-fix |
| A-6 ledger 意味的入替え | **closed** | 9 entry の種別・scope・digest・count を exact 固定 | — |
| A-7 symlink / non-regular | **partial** | placeholder guard は拒否するが後続 reader が外部を追跡 | must-fix |
| A-8 対象3族外 | **partial** | phase、decisions、failures、JSON 等は現在も対象外 | backlog / T-100 |
| B-1 読取失敗 | **partial** | A-3 と同じ | must-fix |
| B-2 rotation 手順 | **closed** | 最終状態で H2 全体を移動すれば台帳無変更。insights key migration コメントも存在 | — |
| B-3 段7逐語の自己発火 | **partial** | raw 複写は未許可 hit。下記 defang を段7で適用する必要 | must-fix |
| B-4 frozen artifact waiver | **partial** | freeze 後に発見した正当 hit の専用 waiver は未設計 | backlog / T-100 |
| B-5 F36 過大保証 | **partial** | 段7文言が未確定。exact 3要素・3族だけと明記が必要 | must-fix（記録） |

## FIX-1〜FIX-8 対応表

| FIX | 判定 | 根拠または残る失敗シナリオ |
|---|---|---|
| FIX-1 scope 化 | **regressed** | 別 H2 replay は閉じたが、同一 H2 bytes collision で cross-path replay を新たに許す |
| FIX-2 過剰観測 control | **closed** | `actual=2` の branch と exact finding がある |
| FIX-3 safe-reader | **partial** | 集約到達は改善したが、依存検査の偽 finding・不完全 archive 比較が残る |
| FIX-4 行分割 | **closed** | 実装と既知9 digestは正しい。CR-only oracleのみ不足 |
| FIX-5 exact ledger | **closed** | 9 entry の exact map が test-local literal で固定 |
| FIX-6 symlink拒否 | **partial** | 列挙 helper は拒否するが、CLI全体では後続 reader が追跡 |
| FIX-7 コメント | **closed** | worklog rotation、insights key migration、waiver権限を記載 |
| FIX-8 既存回帰防止 | **closed**（静的） | 既存48 test・assertの削除なし。日付は相対順序を維持して移動。実行結果は未確認 |

## 追加された fix 8 nodeid の恒真化監査

| nodeid | 実装を壊しても当該 node が成立する経路 |
|---|---|
| `test_placeholder_guard_registered_line_duplication_is_violation` | scope を観測 key から落としても、同じ digest が2本なので `actual=2` は維持される。別 replay node に依存 |
| `test_placeholder_guard_same_file_record_replay_is_violation` | target H2 を source と同一 bytes にすれば現実装のまま受理される |
| `test_placeholder_guard_entry_rotation_keeps_ledger_green` | main 配線削除・guard no-op でも両状態が clean。単独では常時緑経路あり |
| `test_placeholder_guard_ledger_entries_are_pinned_exactly` | checker が台帳定数を使用しなくても、定数自体が不変なら成立。削除/content node に依存 |
| `test_placeholder_guard_digest_line_boundary_contract` | standalone CR の分割を削除しても成立 |
| `test_placeholder_guard_read_failures_are_aggregated_without_traceback` | 後続 checker を無言 skip、または偽 finding を多数派生させても header/substring 条件は成立 |
| `test_placeholder_guard_rejects_symlinked_target_directories` | symlink finding 後に外部 directory を走査しても成立 |
| `test_placeholder_guard_rejects_symlinked_and_non_regular_members` | member finding 後に target を読む実装でも成立。FIFO hang も未検査 |

## fixture・通常経路の判定

legacy fixture を単純化して既存検査を弱めた証拠はありません。

- 既存 test / assert の削除なし。
- Jan/Feb の synthetic 日付は、登録 H2 を含む Jul archive より後になるよう Aug/Sep へ平行移動され、既存の相対順序 oracle は維持。
- archive README は登録 archive を常時掲載し、専用 archive tests の追加 member も引き続き掲載。
- 読取成功する regular UTF-8 / LF 経路では `_safe_read_text()` は従来と同じ text を返し、legacy finding 文言・順序の静的変更は見当たりません。新 guard が backlog より前に入ることだけが意図された追加です。

弱いのは legacy fixture ではなく、新規 rotation / read-failure / symlink node の oracle です。

## 段7の可逆 defang

原文全 bytes を **RFC 4648 Base64** に変換する規則を推奨します。token 単位ではなく全文を変換します。

- 原文を改行正規化せず raw bytes のまま SHA-256 と byte 数を計算。
- raw bytes 全体を Base64 化し、76文字など固定幅で折り返す。
- 同じファイルへ実測した `source-sha256`、`source-bytes`、`encoding: base64-rfc4648` を記録。
- 凍結 SHA は defang 後の成果物に対して取得。
- 復元時は payload を Base64 decode し、原文 SHA-256 と byte 数を照合。

Base64 alphabet は ASCII の英数字、`+`、`/`、`=` だけなので、LP-1〜LP-3 の raw bytes が payload に現れることはありません。完全可逆であり、次の erratum 文が使えます。

> **Erratum**: 逐語原文は exact-literal gate の自己発火を避けるため、raw bytes 全体を RFC 4648 Base64 に可逆変換した。原文同一性は同ファイルの `source-sha256` と `source-bytes` で検証する。対象の識別は `tools/check_docs.py` の LP-1〜LP-3 を正本とする。

worklog / 材料レポートには次の文面を使用できます。

```markdown
- **[T-094]**: `LITERAL_PLACEHOLDERS` の3要素を対象3族の raw text で検査する exact-literal gate を実装。既知台帳は debts 4 / mentions 5 を H2-entry scope または insights path と行 digest に束縛した。
- **射程**: 保証対象は上記3要素と、現行 worklog・archive worklog・insights Markdown に限る。F36全体、同義表記、予測値の先書き、対象外 docs / JSON は保証しない。
- **逐語保存**: 子出力の raw bytes は RFC 4648 Base64 で可逆 defang し、原文 SHA-256 と byte 数を併記した。対象 byte 列は本文へ再掲しない。
```

## 残 must-fix

1. worklog 族の同一 H2 bytes を最終 tree で拒否し、同一ファイル・現行/archive 間の collision replay control を追加する。
2. prerequisite の読取失敗時は依存検査を停止し、「空集合」として判定しない。
3. symlink / non-regular の拒否状態を後続 checker まで共有し、外部 target を一切開かない。
4. rotation、safe-reader、symlink node を非恒真化し、README・遷移・no-follow を実際に発火させる。
5. M1/M6/M7/M9 を単一理由の変異へ再照準してから変異台帳を書く。
6. 段7逐語へ Base64 defang を適用し、F36全体を閉じたと読める文言を避ける。

**最終判定: NO-GO**。


---

## 段 6 fix round 2 の報告 (`s6-fix2.md`)

実装・検証完了です。編集は指定された 2 ファイルのみで、docs 編集・git add・commit は行っていません。

- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:355)
- [test_check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:615)

## FIX2 対応表

| FIX | 状態 | 対応 |
|---|---|---|
| FIX2-1 | closed | worklog 族全体で H2 raw bytes の重複を検出し、全所在を finding に出力。同一ファイル内・別 archive 間の collision replay control を追加 |
| FIX2-2 | closed | 読取不能を未知状態として扱い、D 参照、見送り台帳依存遷移、archive 間遷移、placeholder 台帳照合などの依存検査を停止。停止理由も読取 finding に明記 |
| FIX2-3 | closed | `_safe_read_text()` が final path・親 component の symlink と非 regular file を読取前に拒否。worklog symlink/FIFO、archive 親 symlink で外部内容を読まないことを固定 |
| FIX2-4 | closed | rotation node 内に「行だけ移動→赤」「H2 全体を新規 archive member へ移動→緑」の対を実装。README 更新と非空 archive 境界遷移を含む |
| FIX2-5 | closed | 外部 symlink target の未許可 placeholder/sentinel が finding に現れないこと、派生偽 finding がないこと、FIFO が timeout 内に終了することを assert |
| partial / regressed | なし | 最終全走で回帰なし |

## 検証結果

指定されたコマンドは最終状態でそれぞれ単独実行しました。

- `python3 tools/check_docs.py` → `check_docs: 違反なし / rc=0`
- `orchestrator/tests/test_check_docs.py` 全 nodeid → `111 passed / rc=0`
- `test_dev_waves_cli.py`・`test_dev_waves_checker.py` 全 nodeid → `25 passed / rc=0`
- `python3 tools/check_codex_agents.py` → `rc=0`
- `git diff --check` → `rc=0`

焦点 8 nodeid も限定実行し、`8 passed` を確認しています。

- `test_placeholder_guard_duplicate_worklog_h2_is_violation`
- `test_placeholder_guard_h2_collision_replay_is_violation`
- `test_placeholder_guard_entry_rotation_keeps_ledger_green`
- `test_placeholder_guard_read_failures_are_aggregated_without_traceback`
- `test_safe_reader_dependency_failures_do_not_emit_derived_findings`
- `test_safe_reader_rejects_worklog_symlink_and_fifo_without_hang`
- `test_placeholder_guard_rejects_symlinked_target_directories`
- `test_placeholder_guard_rejects_symlinked_and_non_regular_members`

## 受理・拒否挙動の差

変更前は、同一 H2 bytes を別 worklog ファイルへ複製すれば登録行を replay できました。変更後は、同じ raw H2 が worklog 族内に2箇所以上ある時点で拒否されます。

読取失敗時は空集合として判定せず、関連検査を停止します。したがって正当な D 参照、見送り済み ID、非隣接 archive 遷移から偽 finding は派生しません。

symlink・FIFO・directory は開かず、外部 target の placeholder、H2 sentinel、archive README sentinel は報告に現れません。通常の regular UTF-8 読取成功経路の finding 文言・順序は変更していません。

## 維持確認

- round 1 時点の既存 68 test 関数を維持
- 新規 4 関数を追加し、現在 72 test 関数
- 既存 positive-control assert を残したまま no-follow・非派生 assert を追加
- 台帳は debts 4 / mentions 5、合計 9 entry のまま
- fixture に production 定数由来の hash は追加していない
- 最終 `git status` は指定 2 ファイルの未コミット変更のみ

事前指定の期待赤は 0 件です。作業中には rotation fixture の追従不足による焦点 node の赤と、worklog 不在時の既存 finding 抑止による全走 `110 passed / 1 failed` が発生しました。いずれも回帰として修正済みで、最終全走の赤は 0 件です。


---

## 段 6 焦点再レビュー round 2 (`s6-refocus2.md`)

## 総合判定

**NO-GO** です。親提示の実測結果は前提として受け取り、こちらではテストを実行していません。判定は指定文書、現行差分、round 1 スナップショット、`rg` / `find` による静的照合です。

表の6行はいずれも残 must-fix です。最右列が `DW-G05` の成果物影響です。

| # | 判定 | 独立判定 | 放置時の成果物影響 |
|---|---|---|---|
| 1. H2 collision replay | **partial** | 空白形式の同一 H2 は閉じたが、直後がタブの H2 を既存 parser は認識する一方、新 guard は認識しない | 登録 placeholder を別 entry へ移しても台帳が受理し、レポートの債務・言及の帰属先が変わる |
| 2. tri-state | **partial** | 指定3ケースは改善したが、停止範囲が粗く、構造 parse 失敗はなお空集合扱いを残す | レポートの finding 件数が欠落または過大になり、検査結果が真の欠陥集合を表さなくなる |
| 3. symlink / non-regular | **partial** | worklog/archive 経路は改善したが、全読取経路への集約にはなっていない | 外部 bytes に依存した検査結果を出す、または外部内容を正規文書として受理する |
| 4. node 非恒真化 | **partial** | rotation は closed。H2、dependency、safe-reader node には恒真・mask 経路が残る | 変異台帳やレビューが、実装退行を検出しない node を保証根拠として参照する |
| 5. 変異単一理由性 | **regressed** | M6/M7/M9 は適切だが、現 harness は M3 で anchor abortし、M8/M11 は semantic kill でない | 変異台帳が生成不能になるか、診断差だけを「12/12 KILLED」と誤記する |
| 6. 段7 defang / 射程記録 | **partial** | 設計済みだが未適用。working tree はコード・テスト2ファイルだけ | 逐語成果物が gate を自己発火させるか、F36 全体を閉じたと読める過大な材料レポートになる |

## 決定的な所見

### 1. H2 構文が checker 間で不一致

既存 entry parser は `##` 後の空白またはタブを認識しますが、H2 一意性と scope 更新は `line.startswith("## ")` だけです。[正規表現](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:316)、[新 guard](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:853)

具体的には、登録行を H2 A から削除し、その後に literal tab を使った有効な `##\t2026-...` entry B を置いて登録行を移すと、

- backlog parser は B を別 entry と認識
- placeholder scanner は B を H2 と認識せず、scope は A のまま
- H2 一意性にも B は登録されない

ため、元の scope・digest・`actual=1` を維持できます。

H2 全体の raw bytes が比較対象なので、同じ日付・同じ連番でも後続タイトルが違えば新検査は拒否しません。正規 rotation は「コピー」ではなく「移動」であり、最終 tree に完全同一 H2 が2本残る正当運用も規約上ありません。したがって一意性そのものは妥当で、問題は parser の不一致です。

### 2. tri-state は停止しすぎる一方、停止不足もある

任意の対象1件が読めないと単一の `complete=False` になり、全 scope・両台帳の照合を一括停止します。[全体停止](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:911)

例として、無関係な `output/insights/unrelated.md` を invalid UTF-8 にし、同時に readable な worklog 内で登録行を二重化すると、`actual=2` は観測されても台帳比較が全停止するためレポートに出ません。少なくとも worklog 族と path-bound insights は別 completeness にする必要があります。

逆に、構造抽出失敗は未知状態になっていません。

- phase3 の ledger 抽出失敗後も `ledger_ids=set()` のまま遷移検査を続けます。[ledger 処理](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:958)
- archive entry 抽出失敗時に `archive_input_complete=False` を設定せず、読めた非隣接 archive を比較できます。[archive 処理](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1076)

また worklog symlink/FIFO は placeholder finding に「台帳・H2検査停止」とだけ出し、共有状態を受け取った backlog guard は黙って停止します。`次の一手` 保存則も停止したことがレポートから明確には分かりません。

一方、`docs/worklog.md` 不在時の修正方向は正しいです。不在 path は blocked set に入れず、既存 backlog finding を[現在も出します](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:938)。既存テストの assert も緩められていません。

### 3. `_safe_read_text` は worktree 配置では誤発火しないが、全読取経路を閉じていない

`REPO` は resolved path で、親検査は `REPO` より上へ進みません。このため `.claude/worktrees/` 配下という配置自体は将来も誤発火要因になりません。repo 内部の symlink component を拒否するのは意図どおりです。[親検査](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:364)

ただし `_check_command_docs_guard()` は `_safe_read_text` を使わず、final component だけを調べて直接 `read_bytes()` します。[直接読取](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1366)

`.claude/commands` 自体を外部 directory への symlink にし、外部に契約を満たす command 群を置くと、子ファイルは final-component symlink ではないため外部 bytes を読み、後段の `_safe_read_text` にも到達しません。FIX2-3 の「全読取経路」「外部 target を一切開かない」は未達です。

## 新規4 nodeid の恒真化監査

| node | 実装を壊しても緑になる経路 |
|---|---|
| [`duplicate_worklog_h2`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:615) | 空白形式しか使わないため、タブ H2 を無視する現実装でも成立 |
| [`h2_collision_replay`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:636) | 同じくタブ H2 による cross-entry replay を検出しない |
| [`dependency_failures`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:1041) | 通常経路の D 参照検査を恒久的に無効化しても「読取失敗時に派生 finding がない」は成立。`rg` 上、存在しない D 参照の positive control もない |
| [`worklog_symlink_and_fifo`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:1117) | worklog symlink/FIFO は `_literal_placeholder_targets` が先に拒否するため、`_safe_read_text` の symlink/non-regular 拒否を削除しても node は成立 |

FIFO の timeout は有効で、実際に hang すれば `TimeoutExpired` により失敗します。ただし「safe-reader が拒否した」証明ではなく、前段拒否によって終了しても緑です。

外部 sentinel は worklog、directory、member の各 symlink ケースで実際に `_write()` され、同じ path を `os.symlink()` に渡しています。「そもそも target が作られていない」現行経路はありません。ただし member target は backlog が読んでも必ず露呈する構造 sentinel ではなく、未許可 placeholder だけなので no-follow の全 consumer 証明には不足します。

## 既存テスト弱体化

弱体化は認めませんでした。`snapshot-pre-fix2.patch` から round 1 状態を復元して比較した結果、

- test 関数は 68 → 72、既存関数の削除 0
- AST 上の assert は 86 → 143
- round 1 の全 assert 式が現在も残存
- `_build_min_repo()` は fix2 で変更なし
- 既存 fixture の単純化なし

です。変更された既存 node は assert を追加しており、`_run_check()` の timeout オプション追加と no-op guard の戻り値を `set()` に合わせた修正も弱体化ではありません。

## DW-M01 / DW-M03 判定

[M01/M03 契約](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/docs/dev-wave/mutation.md:5)に対し、方針の一部だけが適合します。

- M6/M7 の既知命名 glob 縮退と M9 の VT 分割復活は、baseline を壊さず不正入力の受理を変えるため適合します。
- M1/M2 の `overdetermined=True` 明記は透明性には寄与しますが、harness はそれらも通常の `KILLED` として summary・成功条件へ算入しています。[集計](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/mutate.py:164) 単独理由の証拠から除外した集計になっていません。
- M3 の anchor は旧 standalone call のままですが、現在は代入式です。[旧 anchor](/home/SFC/tanab/.claude/jobs/9963fb67/tmp/wave-t094-placeholder/mutate.py:43)、[現行 call](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:1635) 現状態では事前 anchor 検査が count=0 で abortします。
- M8 は lookup の scope 束縛だけを外しても、最終 observed reconciliation が元 scope を要求するため入力は依然拒否されます。診断差だけです。
- M11 は列挙 helper の拒否を外しても `_safe_read_text` が同じ symlink/FIFOを拒否します。これも受理集合を変えない diagnostic sensitivity です。

したがって「12変異・expected node 登録・anchor 事前検査」という形式だけでは `DW-M01` / `DW-M03` を満たしません。

## 残 backlog / nit

- standalone CR の positive oracle 不在は引き続き **nit**。現実装は正しく、repo に CR byte がないという親実測とも整合します。
- exact 3文字列・3族外、意味的同義表記、frozen artifact waiver は **T-100 系 backlog**。
- 段7では raw 子出力全体の Base64 defang、原文 SHA-256・byte数の併記、exact 3文字列・3族だけという射程記録が必要です。


---

## 段 6 fix round 3 の報告 (`s6-fix3.md`)

実装・検証完了です。編集は指定された 2 ファイルのみで、docs 編集・git add・commit は行っていません。

- [tools/check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:355)
- [test_check_docs.py](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/orchestrator/tests/test_check_docs.py:615)

## FIX3 対応表

| FIX | 状態 | 対応 |
|---|---|---|
| FIX3-1 | closed | H2 判定を `WORKLOG_H2_RE.match()` に統一。タブ H2 の重複検出と scope replay 拒否を追加 |
| FIX3-2 | closed | completeness を worklog / insights 族に分離。phase3 ledger・archive entry の構造抽出失敗を未知状態とし、依存検査と停止理由を明示 |
| FIX3-3 | closed | command/reference 読取を `_safe_read_text()` 経由に変更。`.claude/commands` 親 directory symlink は外部 member の列挙前に拒否 |
| FIX3-4 | closed | D 参照・見送り台帳・archive 遷移の通常経路 positive control、および decisions.md symlink/FIFO による safe-reader 単独 control を追加 |
| partial / regressed | なし | 最終全走で回帰なし |

H2 構文は [既存の `WORKLOG_H2_RE`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t088-floor-wrapper/tools/check_docs.py:316) だけを正本としています。走査中に一度 `match()` し、その結果を重複登録と `preceding_h2` 更新の両方で共有しており、`[ \t]+` の二重定義はありません。

## 検証結果

指定コマンドを最終状態で個別実行しました。

- `python3 tools/check_docs.py` → `違反なし / rc=0`
- `orchestrator/tests/test_check_docs.py` 全 nodeid → `113 passed / rc=0`
- `test_dev_waves_cli.py`・`test_dev_waves_checker.py` 全 nodeid → `25 passed / rc=0`
- `python3 tools/check_codex_agents.py` → OK
- `git diff --check` → 問題なし

限定実行した焦点 6 nodeid は `6 passed` です。

- `test_placeholder_guard_duplicate_worklog_h2_is_violation`
- `test_placeholder_guard_h2_collision_replay_is_violation`
- `test_placeholder_guard_unreadable_insight_does_not_mask_worklog_mismatch`
- `test_safe_reader_dependency_failures_do_not_emit_derived_findings`
- `test_safe_reader_rejects_worklog_symlink_and_fifo_without_hang`
- `test_command_docs_guard_rejects_symlinked_commands_directory`

事前指定の期待赤は 0 件です。作業中、新規タブ control の `repr()` 表示期待に誤りがあり限定実行で 1 件赤になりましたが、テスト期待値を修正し、最終全走では赤 0 件です。

## 境界・維持確認

- 既存 72 test 関数・143 assert は削除・緩和なし
- 最終状態は 74 test 関数・189 assert
- 台帳は debts 4 entry / mentions 5 entryのまま
- `git status` は指定 2 ファイルの未コミット変更のみ
- docs 編集、git add、commit は未実施です。
