# 段 1 brief — [T-2145] sort SWO oracle の受理言語を検証済み IR へ縮める

親 = dev-wave manager。基準 = local main `82a259c0a`。branch `worktree-dev-wave-t2145-sort-oracle-ir`。

## scope

sort SWO oracle が候補 comparator について「報告された関係行列がその comparator の真の関係である」
ことを保証できない現状 (D1355 が閉じよと定めた非保証) を、**受理言語を型付きの検証済み IR へ縮め、
関係行列を trusted evaluator が自分で計算する**ことで閉じる。これは**受理集合を狭める変更**である。

scope 外: 仮想リスク向けの gate・検査・台帳・一般化の追加。sort 以外の軸。性能計測。
`sort_best` の 15 組 exact binding (D1357) の受理範囲変更。

## 確定済みユーザー裁定 (逐語は refs/)

- **D1451** — 後発決定 (D1355) は先行決定 (D344) が却下理由に挙げた実験同一性の論点を
  supersede しない。技術的な設計着手は妨げない。**別実験になる点を明示したうえで起票してよい。**
  → 本 wave の成果物は「この変更は D39 の raw C++ 独立合成の実証点を別実験へ移す」と明記する。
  D344 を supersede したとは書かない。
- **D1355** — IR 方向を採る。生死確認を先に置く (済、[T-2113] 4 点すべて真)。
- **D1357** — `sort_best` の権威集合は name↔comparator の exact binding 一本。
- **D345** — 受理集合を変える gate の契約 ID は campaign identity へ焼く。導入前 campaign は再開不可。
- **D344** — 実型 harness を使う / 模擬型を置かない / 候補の stdout を判定に使わない / 判定不能を
  合格にしない。これらは本 wave でも不変。

## 不変条件

1. **規律 2 を緩めない。** 受理集合は狭くなる方向のみ。現行 accepted 集合の真部分集合であることを
   実測で示す。広がる経路が 1 本でも見つかれば実装しない。
2. **受理権威を二重化しない。** 同じ hole に受理権威が 2 つ並ぶ設計は、先例
   (`output/insights/2026-08-15_t396-hole-allowlist-refuted/`) で破棄されている。
   どれが権威で、どれが恒真化するかを名指しで決め、恒真化するものは gate として数えない。
3. **判定不能を合格にしない** (D344 決定 4)。`UNAVAILABLE` の分離は現行のまま。
4. **契約 ID は必ず変える。** 受理集合が変わるので `ORACLE_CONTRACT_ID` が変わらない実装は誤り
   (D345)。exact golden 2 件 (`test_critic.py:100`、`test_sort_swo_oracle.py:2056`) の更新は必須。
5. **F568 の identity churn を変異評価から引く。** oracle module を触ると contract identity が
   変わり identity pin node がどの変異でも落ちる。機構固有 node 数 0 の変異は KILLED と数えない
   (`DW-M02`)。
6. 親は実装面を直接編集しない。実装は Codex `role=author` (D95)。

## 親の provisional 裁定 (割れうる前提 — 段 3 の攻撃対象)

- **(P1-a) 受理権威は IR admission 一本にする。** `_validate_single_sort_statement` は候補への
  gate ではなくなり、trusted renderer の出力に対する事後条件へ降格する (= 恒真化する側)。
  `coder_effect_gate` の DENY_TABLE は hole 全般の host effect 拒否として残る (別の関心事であり
  二重化ではない) — ここが割れうる。
- **(P1-b) 候補の提出形は「小さい文法に適合する C++ テキスト」とし、JSON wire にしない。**
  根拠は既存策の存在: backoff 軸は `orchestrator/campaign/backoff_hole_grammar.py` (760 行) が
  同型の Tier 1 文法 admission を既に持ち、決定順序・固定 rule/reason bytes・候補文字列を
  射影しない規約まで確立している。sort 軸だけ JSON wire を新設すると軸間で非対称になる。
  D344 が禁じたのは**任意 C++ からの字句抽出**であって、小さい明示文法の parse ではない
  — ここが最も割れうる。生死確認 driver は JSON wire で測っているので、対立仮説には実測がある。
- **(P1-c) pointer 意味論は「現行 C++ の `<` を corpus 上で再現する」を採り、明示 rank へ
  意味を変えない。** trusted 側が corpus の allocation 順を確定しているので再現可能で、
  実測 (2 corpus x 3 order x 79 値 = 153,576 セル、不一致 0) がある。ただし `CORPUS_SHA256` は
  allocation 順の変更を捕捉しないので、**pointer mapping を contract components へ入れる**。
- **(P1-d) 79 値 admission と `sort_best` の 15 組 exact binding は別権威のまま分離する。**
  79 値で置き換えると certified 側の受理集合が広がる。

## 親が段 1 で実測した事実 (probe_narrowing.py、repo 外・job dir)

生死確認 ([T-2113]) が測っていなかった `coder_effect_gate` まで含めて親が測り直した。

| # | 測ったこと | 結果 |
|---|---|---|
| 1 | 79 値の render が `_validate_single_sort_statement` を通るか | **全件通過** (失敗 0) |
| 2 | 79 値の render が `coder_effect_gate.scan_host_effects` を通るか | **全件通過** (finding 0) |
| 3 | 権威集合 15 件が render 値集合に **byte exact** で含まれるか | **全件含まれる** (欠落 0) |
| 4 | レンズ A の「広がる経路」候補 `while (true) { break; }` 入り comparator | effect gate が `host-effect.unconditional-loop.v1` で拒否。文形 validator は通す |

**4 の読み方 — レンズ A の懸念は受理集合の拡大を示していない。** その comparator と外延同値な IR
`("single","key","asc")` は**今日すでに受理されている** (権威集合の `k_asc`)。IR は `while` 形を
新たに受理するのではなく、正準形だけを受理する。したがって受理される**文字列の集合は真に縮み**、
受理される**挙動の集合は不変または縮む**。1 と 2 は「新受理集合 ⊆ 現受理集合」を 2 つの現行 gate で
実測したものである。

**残る唯一の拡大経路は evaluator 側にある。** trusted evaluator が実行由来の行列と食い違えば、
今日 `REJECT` される候補が `PASS` になりうる。[T-2113] は 2 corpus x 3 order x 79 値 = 153,576 セルで
不一致 0 を実測しているが、これは**本 wave の実装に対しては再測が要る** (`DW-M02` の
「記録済み成果物は producer が変われば別命題」)。段 3 レンズ A の主攻撃面はここに置く。

## 成果物の形

- 実装: sort 軸の hole 文法 / IR admission + trusted evaluator + renderer。既存 oracle の
  compile/run 経路は残すが、**関係行列の出所は trusted evaluator にする**。
- 契約: `ORACLE_CONTRACT_ID` の更新と、IR 文法版・pointer mapping の components 追加。
- 検査: (1) 79 値の全件が現行 accepted 集合に含まれることの実測、(2) admission の負例、
  (3) trusted evaluator と実 oracle の行列一致 (生死確認の再現)。
- 記録: worklog、insight (別実験である旨の明記を含む)、decisions。

## 実アンカー表 (変更面)

| path:anchor | 現在の役割 | 本 wave での想定 |
|---|---|---|
| `orchestrator/campaign/sort_swo_oracle.py:523` `_validate_single_sort_statement` | 候補の外形 gate | 恒真化 → renderer 事後条件へ降格 (P1-a) |
| 同 `:2486` `_AXIOM_CHECKER_SOURCE_FUNCTIONS` | contract に焼く関数 13 個の列挙 | IR admission / evaluator を追加 |
| 同 `:2547` `_ORACLE_CONTRACT_COMPONENTS` | 契約 components | pointer mapping・文法版を追加 |
| 同 `:2574` `ORACLE_CONTRACT_ID` | 契約 ID | 必ず変わる |
| 同 `:629` `_CORPUS_TOPOLOGY` / `:2122` `_run_matrix` | corpus と実行経路 | evaluator の入力・照合先 |
| `orchestrator/campaign/p3_s4_loop_sort.py:154` `CoderProposalSort.implementation` | hole 全体の C++ 文字列 | 受理言語が縮む当事者 |
| 同 `:204`-`:246` | oracle 呼び出し | admission の位置 |
| `orchestrator/campaign/s1_direct_comparison.py:871`-`:890` | 第 2 の oracle 呼び出し | 同上 |
| `orchestrator/campaign/backoff_hole_grammar.py` (760 行) | backoff 軸の Tier 1 文法 | **再利用すべき既存策** |
| `orchestrator/campaign/coder_effect_gate.py:58` `DENY_TABLE` | host effect 拒否 | 不変 (P1-a) |
| `orchestrator/campaign/s6_sort_sweep.py:143` `CANDIDATES` (15 件) | 権威集合の候補空間 | IR 表現の全件対応先 |
| `orchestrator/campaign/s1_known_axes_freeze.py:94` | `sort_best` exact binding | **触らない** (P1-d) |
| `orchestrator/tests/test_critic.py:100` | 契約 ID の exact golden | 更新必須 |
| `orchestrator/tests/test_sort_swo_oracle.py:2056` | 契約 ID の exact golden | 更新必須 |
| `.claude/agents/coder-v4-autonomous-sort.md` | 合成子の出力規約 | 受理言語の変更に追随 |

## 既存被覆の検索 (性質で引いた結果)

- 「hole へ入る候補テキストを小さい明示文法で admission する」機構は **既に存在する**
  (`backoff_hole_grammar.py`、backoff 軸)。trigger 軸は固定 5-bit wire。**sort 軸だけが raw C++。**
  → 純増は「sort 軸の文法 + trusted evaluator (関係行列の出所を候補実行から外す)」。
    admission 機構そのものは新規発明ではない。
- 契約 ID を campaign identity へ焼く機構も既存 (D345、`ORACLE_CONTRACT_ID` 消費側 3 file)。純増なし。

## 受入・実測環境

受入全走は login node で `python3 tools/run_tests.py`。`test_sort_swo_oracle.py` は D669 で
受入全走から恒久除外されているため、**親が focus 走で別途実走する**。性能計測は行わない
(本 wave に計測項目なし)。

## 並列分割方針

段 2 プラン 1 本 → 段 3 敵対 2 レンズ (レンズ A = 受理集合が広がる経路の探索、
レンズ B = 受理権威の二重化と恒真化の検出) → 段 4 裁定 → 段 5 実装子 1 本
(admission・evaluator・contract は producer/consumer 契約が 1 単位なので分割しない) →
段 6 レビュー 2 本 + fix 1 本。
