# 段 4 裁定 + プラン v2 — [T-1219] carry 検査の同一 ID 化 (D837 択 c)

親が段 3 の 2 レンズ (sol 8 件 / luna 8 件) を real / refuted に裁定し、プラン v2 を確定する。
裁定は親自身の実測で裏を取ったものだけを real とする。

## 0. 裁定前の再走査

- **裁定 inbox 再走査 (DW-S04):** `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/` を
  `T-1219` / `D837` / `carry` で全走査。該当は
  `2026-08-16-rulings-full3-28rulings.md` の項 9 のみで、内容は D837 と同一
  (択 (c) 採用、択 (b) は「同型違反が素通りするため不採用」)。**覆す新事実なし。**
- **main の前進:** wave 開始時の `d8f777a4` から `33cb6321` へ 11 commit 前進。
  `git diff --name-only d8f777a4..main -- tools/check_docs.py orchestrator/tests/test_check_docs.py`
  は**空**。編集面の衝突は依然として無い。取り込みは `DW-O20` に従い受入の post-claim merge で行う。

## 1. 親が実測で確定させた事実

裁定の土台。すべて本 wave の親が worktree (base d8f777a4) で走らせた。

| # | 実測 | 値 |
|---|---|---|
| A | carry 参照の母数 (probe 条件) | 404,326 |
| B | carry 参照の母数 (production の収集条件と同一) | 404,326 (**差 0**) |
| C | 内訳 | 現行 worklog 2,749 / 採番 archive 401,577 |
| D | 非採番 archive の carry (両条件とも対象外) | **1** |
| E | 同一 ID が参照先に在る carry | 404,322 |
| F | ID 不一致 (= 既存違反) | **4** |
| G | 参照先 key 不在 / 索引 None / 空集合 | **0 / 0 / 0** |
| H | 次の一手を索引できた entry | 957 (うち索引 None は 0) |
| I | 既存違反 4 件の source entry 番号 | **すべて 77** (77 は当該 archive の唯一の entry) |
| J | baseline `python3 tools/check_docs.py` | rc=0 / wall 10.52 秒 / maxrss 157MB |
| K | 全 traversal 1 回 | 1.69 秒 / 23MB |
| L | 既存 carry テスト | 11 passed (計算ノード request 947647.nqsv) |

B は sol の S-7 (probe と実装の母集合が一致する保証がない) への直接の回答である。
G と H は S-8 (索引不能 category が実コーパスで 0 件である根拠がない) への回答である。

## 2. プランの誤りを 1 件、親が実測で訂正した

プラン「既知違反台帳の設計」の表は source entry を **74 / 76 / 77 / 78** と書いているが、
これは親の probe 出力の**行番号**であって entry 番号ではない。
`docs/archive/worklog-phase3-0731-77.md` が持つ entry は **77 の 1 件だけ**である (実測 I)。
この誤りのままなら 4 件とも `expected=1, actual=0` となり、同時に 4 件の新規違反が出て
実 repo が赤になる。プラン v2 で訂正する。

## 3. 所見の裁定

### 採用 (real、scope 内)

| 所見 | 判定 | 親の裏取り | 対応 |
|---|---|---|---|
| S-1 carry 風の不正文法が母数も違反数も動かさず素通りする | **real / blocker** | `[T-999] (073)` `[T-999] 変わらず ((073) 参照)` `[T-999] (73 )` `[T-999] 変わらず ( (73) 参照)` はいずれも 2 つの regex 双方に不一致、かつ `TASK_ID_AT_HEAD_RE` には一致するので正規項目として受理されることを実測 | v2-3 で candidate 検出を新設 |
| S-3 / S-5 / L-2 固定下限は完全性を保証せず、最初の fold から縮退を見逃す | **real / blocker** | 論理として正しい。`>= 404326` は「C 件増えた後に C 件失われる」を通す | v2-4 で **candidate == parsed の同数検査**と **universe == index の集合一致**を主柱にし、固定下限は粗い補助へ降格 |
| S-4 索引 key 不在が空集合へ潰れると台帳に吸収される | **real / must-fix** | 実コーパスは 3 種とも 0 件 (実測 G) なので緑を壊さない | v2-5 で三分割 (key 不在 / 値 None / 空集合) |
| S-6 / L-1 台帳 key の三つ組は座標の再利用と内容差替えを既知違反として認証する | **real / must-fix** | `(source_entry, task_id, target)` は F58 型の ID 再利用をそのまま受理する | v2-2 で key を `KNOWN_PLACEHOLDER_DEBTS` と同型の digest 対にする |
| L-4 最悪の赤経路で 404,326 件の finding が常駐する | **real / must-fix** | `findings` は list であり上限が無い。必須 lint が壊れた時だけ運用不能になる | v2-6 で分類別に上限つき sample + 抑止件数 |
| L-5 不一致診断に参照先の所在が無い | **real / must-fix** | 診断だけで復旧操作へ到達できない | v2-7 で診断項目を契約化 |
| L-8 1.69 秒は提案実装の費用上限にならない | **real / must-fix (実測義務)** | 親の K は probe の値であって実装の値ではない | v2-9 で緑経路と最悪赤経路を実装後に実測する義務にする |

### 採用 (real だが対応を変更)

| 所見 | 判定 | 理由 |
|---|---|---|
| L-6 fold との互換を固定するテストが無い | **real / 部分採用** | 親が `tools/spool_fold.py:1839-1840` を確認し、fold は `- {task_id} ({prior_ordinal})` を**同じ ID で**生成し、`active` は直前 entry の次の一手から導かれるので新検査を必ず通ることを確定した。さらに fold 自身が carry 解決時に `参照先 entry ({ordinal}) に item がない` で fail-closed する (`:1606`) ため、**現行 fold は既に同型の規律を持っている**。今日の land を止める危険は無い。v2-8 で fold 形の carry 鎖が緑になる焦点テストを 1 本だけ足し、spool_fold を実走する統合テストは scope 外とする |

### scope 外 (real だが実装しない — 裁定パッケージへ)

| 所見 | 判定 | 理由 |
|---|---|---|
| S-2 / L-7 非採番 archive の carry が構造的に検査対象外 | **real / scope 外** | 既存テスト `test_backlog_guard_unnumbered_archive_carry_is_out_of_scope` が**その名前で**対象外を意図的に固定し rc=0 を要求している。これを赤へ反転するのは不変条件 2 (既存テストの期待値を反転しない) と F80 に正面から反する。加えて非採番 archive の entry は全域 universe に入らないため参照先の実在すら判定できず、除外は整合している。実コーパスの該当 carry は **1 件** (実測 D、母数の 0.00025%)。D837 は archive 全体への拡張を命じていない |
| L-3 台帳・固定総数・exact テストを同一 patch で書き換えれば無裁定で緑にできる | **real / scope 外** | 既存の `KNOWN_PLACEHOLDER_DEBTS` 族が**現に持っている同じ性質**であり、本 wave が新設する欠陥ではない。塞ぐには承認 receipt か保護レビュー境界という新機構が要り、編集面 2 file の外へ出る。本 wave では「機械強制ではない」と正直に書き、裁定へ返す |
| S-2 補足: `/rulings`・fold・land の carry 文法が checker と同一である保証 | **real / scope 外** | 共通 parser 化は別 wave の所有 |
| F58 型「同じ ID で内容を差し替える」検査 | **real / scope 外** | 本 gate は参照先に同じ ID が在るかを見るだけで、内容同一性は見ない。sol も luna も独立に指摘した。substantive digest を carry 鎖へ持たせる案は別裁定 |

### refuted (親の実測が反証)

| 所見 | 反証 |
|---|---|
| S-7 probe と production の母集合が一致する保証がない | **実測で一致を確定した (実測 B、差 0)。** 内訳も現行 2,749 / 採番 archive 401,577 で一致 |
| S-8 索引不能 category が実コーパスで 0 件である根拠がない | **実測で 0 件を確定した (実測 G / H)。** 索引 957 件のうち None は 0、key 不在・空集合も 0 |
| L-1 の「三つ組は通常の rotation に耐えない」部分 | rotation は entry bytes をそのまま移すので三つ組は保たれる。耐えないのは**内容差替え**であり、そこは採用した |

### 親 brief の provisional 裁定の取り下げ

- **(P1) 取り下げ。** 台帳 key を三つ組から digest 対へ変更する (S-6 / L-1)。
- **(P2) 精緻化して採用。** collapse をやめる方向は維持し、404,326 件を materialize せず
  streaming にする。検査粒度は `(target, task_id)` より細かい occurrence 単位。
- **(P3) 降格。** 固定下限は主柱でなく補助にする (S-3 / S-5 / L-2)。
- **(P4) 強化して採用。** 二分でなく三分にする (S-4)。
- **(P5) 拡充。** 最低 3 本を最低 11 本へ (下記 v2-10)。

## 4. プラン v2 (確定)

編集面は `tools/check_docs.py` と `orchestrator/tests/test_check_docs.py` の 2 file のみ。

**v2-1 occurrence streaming.** `_validate_next_action_items` から carry 収集を外し、
項目構造検査だけに戻す。`_CarrySource` (path / whole_text / source_entry / H2 raw line /
section body / section offset) を約 957 件だけ保持し、`_iter_carry_references` が
occurrence を逐次 yield する。404,326 record を常駐させない。追加 traversal は 1 回。

**v2-2 既知違反台帳 (digest 対).** `KNOWN_PLACEHOLDER_DEBTS` と同型にする。

- 外側 key = carry を書いている entry の **H2 raw 行の sha256**
- 内側 key = carry 項目の **論理行 raw bytes の sha256**、値 = 期待観測数
- `EXPECTED_KNOWN_CARRY_ID_MISMATCHES = 4`
- 登録は 4 件。すべて外側 key は entry **77** の H2 行 digest (実測 I による訂正)。
  内側は `- [T-208] 変わらず ((73) 参照)` `- [T-209] ...` `- [T-210] ...` `- [T-211] ...`
  の 4 digest、各 1。
- path と行番号は key に入れない (診断表示にだけ使う)。
- 「追加はユーザーの明示裁定のみ」をコメントで明記し、**機械強制ではないことも明記する** (L-3)。

**v2-3 carry 風 candidate の fail-closed 化 (S-1).**
トップレベル項目のうち「carry を名乗っている」ものを広い述語で数える。述語は
「`変わらず` と `参照` を両方含む」または「行末が `)` で終わり `(` と数字を含む」程度の
包含条件とし、**厳密 2 regex のどちらにも一致しないものは専用 finding にする**。
正例 (通る形) を 1 つ添える: `- [T-1219] (953)`。
負例は向きで 2 分する — 発火自体が目的なので `(073)` `(73 )` `( (73)` の 3 形を positive control にする。

**v2-4 母集合の完全性 (S-3 / S-5 / L-2).** 次の 3 本を対で持つ。

1. **candidate == parsed** — carry 風 candidate 数と厳密 parse 成功数が一致すること。
   parser 退行はここで必ず赤になる。コーパスの成長で腐らない。
2. **universe == index** — `_validate_entry_universe` の `locations` の key 集合と
   次の一手索引の key 集合が一致すること。索引構築の取りこぼしはここで赤になる。腐らない。
3. **`MIN_EXPECTED_CARRY_REFERENCE_COUNT = 404_326`** — 粗い下限。
   母集合が丸ごと消える型だけを捉える補助であり、**完全性の保証ではない**とコメントに明記する。
   1 と 3 を対で持つことで「母集合が空でも緑」も「parser 退行でも緑」も塞がる。

**v2-5 参照先索引の三分割 (S-4).** `index[target]` を sentinel で三分する。
key 不在 / 値 None (section 抽出対象外) / 空集合 (次の一手が空) をそれぞれ別 finding にする。
実コーパスは 3 種とも 0 件 (実測 G) なので `test_real_repo_clean` は緑のまま。

**v2-6 finding の氾濫防止 (L-4).** 分類ごとに最大 20 件まで表示し、
`他 N 件を抑止` を必ず併記する。**数え上げは全件継続する** (台帳照合と母数検査は打ち切らない)。

**v2-7 診断の契約 (L-5).** 新規不一致の finding は次を必ず含む。
carry の path:line / task ID / 参照先 entry 番号 / 参照先 entry の H2 の path:line /
「参照先の次の一手に同じ ID を置くか、carry を正しい参照先へ直す」旨。
既知 key の `actual=0` は「凍結 archive を編集せず、復元するか裁定へ返す」旨を含める。

**v2-8 fold 形の焦点テスト (L-6 部分採用).** fold が生成する形
(`- [T-NNN] (直前 entry 番号)` かつ直前 entry の次の一手に同じ ID) が緑になることを
1 本の焦点テストで固定する。`spool_fold` を実走する統合テストは scope 外。

**v2-9 費用の実測義務 (L-8).** 実装後に親が測る。
(a) 実 repo 緑経路の wall / maxrss、(b) 全件不一致の worst-case fixture の wall / maxrss。
baseline は J (10.52 秒 / 157MB)。倍化しないことを緑経路で確認し、赤経路の値も記録する。

**v2-10 テスト (最低 11 本).**
新規: 同一 ID 不一致が赤 (**主 positive control**) / 既知 4 件は緑 / 台帳の exact pin /
台帳総数の逸脱が赤 / 登録済み occurrence の消失が赤 / 同一 (target, ID) の別 source が赤 /
candidate == parsed の破れが赤 (**S-1 の positive control**) / 母数下限割れが赤 /
universe == index の破れが赤 / 三分割の 3 種がそれぞれ別 finding / fold 形が緑。
既存: `..._existing_in_current_is_clean` と採番 archive 正例は、**assertion を一切変えず**
fixture の参照先に同じ ID を置く補正だけを行う。
`..._dangling_carry_reference_is_violation` `..._new_carry_syntax_in_prose_is_not_a_reference`
`..._unnumbered_archive_carry_is_out_of_scope` は**一切変更しない**。

## 5. 変異事前登録 (B-057、DW-M01)

実装前に登録する。各変異は単一理由性 — 前後に同じ入力を拒否する層が無く、無効化時の赤理由が
1 つに絞れることを段 6 の harness 実走で確認する。確認できない変異は登録から外し理由を台帳へ書く。

| ID | 変異 | 期待して殺すテスト | 単一理由性の根拠 |
|---|---|---|---|
| M1 | 同一 ID 比較を撤去し、索引に ID があれば常に受理 | 同一 ID 不一致が赤 | 他に ID 一致を見る層は無い (実在検査は ID を見ない) |
| M2 | 台帳照合を「未登録も既知として受理」へ反転 | 同一 ID 不一致が赤 | 新規違反を止める層は台帳照合だけ |
| M3 | 登録 key ごとの `actual == expected` 検査を撤去 | 登録済み occurrence の消失が赤 | 消失を捉える層は他に無い |
| M4 | 台帳総数の固定値照合を撤去 | 台帳総数の逸脱が赤 | 総数を見る層は他に無い |
| M5 | candidate == parsed の同数検査を撤去 | candidate 破れが赤 (`(073)`) | 下限検査は母数を動かさないので発火しない |
| M6 | `MIN_EXPECTED_CARRY_REFERENCE_COUNT` の下限検査を撤去 | 母数下限割れが赤 | candidate == parsed は同数なので発火しない |
| M7 | 索引 key 不在を空集合へ潰す | 三分割の key 不在が赤 | 空集合との区別を見る層は他に無い |
| M8 | occurrence を `(target)` で collapse する形へ戻す | 同一 (target, ID) の別 source が赤 | collapse を捉える層は他に無い |
| M9 | universe == index の集合一致検査を撤去 | universe == index の破れが赤 | 他に索引の完全性を見る層は無い |
| M10 | `numbered_archive_input_complete` が偽でも継続する | 入力不完全で停止が赤 | fail-closed の早期 return はここだけ |

`DW-M08` の新旧両走は「テスト強化だけの wave」向けであり、本 wave は production 側の
受理集合を変えるため該当しない。段 6 で `DW-M02`〜`DW-M06`, `DW-M08` を読み直して再判定する。

## 6. 成果物影響 (DW-G05)

実装しない場合、carry 鎖が別 ID を指したまま増え続け、`/rulings` の裁定収集が参照解決に失敗して
**裁定項目を取りこぼす** (F58 / F79 では実際にユーザー裁定 6 件が正本から消えた)。
実装すると `python3 tools/check_docs.py` の受理集合が変わり、新規の carry ID 不一致・
carry 風不正文法・索引取りこぼし・母数縮退で rc=1 になる。既存 4 件は受理のまま。
凍結 archive の bytes は 1 byte も変わらない。

## 7. 段 5 へ渡す境界

- 編集面は 2 file のみ。docs は触らない。commit しない。
- 既存テストの期待値を反転・緩和・skip・削除しない。fixture 補正は上記 2 本に限る。
- 台帳へ 5 件目を足さない。実 repo が赤なら実装側が誤っている。
- `tools/check_docs.py` の総所要が baseline 10.52 秒から倍化しない。
