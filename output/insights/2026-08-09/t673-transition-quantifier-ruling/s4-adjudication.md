# 段 4 裁定 — [T-673] 判断パッケージ wave

親裁定 / 2026-08-09 / HEAD `2c0a418f` (main `f8916b69` 取り込み済み、`7552e322` は段 5 前に取り込む)

段 3 のレンズ A (sol) / B (luna) は、親 brief と段 2 プランの双方を実質的に壊した。
**親 brief の provisional 裁定 4 件のうち 3 件が反証または限定された。** 以下で裁定する。

---

## 0. 親が段 4 で自ら裏取りした事実 (裁定の土台)

| # | 主張 | 裏取り | 結果 |
|---|---|---|---|
| V1 | 現行本番では遷移検査が一度も呼ばれない | `env_contract_activation.py:395` の `if previous_rows is not None`、および `env_contract_activations/` が `00000001.json` 1 件のみ (env 2 個・共に g1) | **確定** |
| V2 | `changed[:1]` の既存検出は 10 node で、うち 5 件が意味的 | T-627 ledger v3 の M4 (同一 blob・2 file scope) の `failed_nodes` を実読 | **確定** |
| V3 | 既存 AST 先例は `[:N]` を全 N 殺すが、意味保存 refactor でも赤になる | 親測定器 `parent_probe_ast_precedent.py` (in-memory、木は不変) | **確定** |

V1 が本 wave の問いの性質を変えた。**この量化縮退は「現在の本番に空いている穴」ではない。**
現行 chain は record 1 件なので遷移検査自体が発火せず、仮に発火しても env は 2 個なので
`[:2]` 以上は恒等変換である。したがって争点は「今ある正しさの穴を塞ぐか」ではなく、
**「将来 record が伸び env が増えたときに効く backstop を、今どれだけの費用で買うか」**である。
裁定パッケージはこの枠組みで書く。

---

## 1. 段 3 所見の裁定

### レンズ A

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| A1 | merge で対象 4 file に差分なし | refuted (差分なしを確認) | — |
| A2 | G 系の `expected_nodes` が全件過少 → MISMATCH になる | **real・採用** | 事前登録を差し替える (§3) |
| A3 | P-N1 は focal で 3 件ちょうど | refuted | — |
| A4 | P-N1 の既存検出は 10 node、318 の「semantic 3 / diagnostic 7」は誤り (正しくは 5 / 5) | **real・採用** (V2 で親が確認) | **erratum を台帳へ記録** |
| A5 | focal scope は A を過小・B/C を過大に見せる | **real・採用** | full-file と focal の両方を測る (§3) |
| A6 | core hash は同一実験を示さない | **real・採用** | manifest に base blob・runner argv・環境 identity を含める |
| A7 | AST 先例は狭義には `[:N]` を殺す | refuted (= 親主張は成立) | V3 で確認済み |
| A8 | その先例の一般化は不可 (cardinality 未検査・decoy loop で回避可) | **real・採用** | C1 は exactly-one を明示 assert する。親は「先例があるから安い」と書かない |
| A9 | 「36/150 が import ast」は採用根拠にならない | **real・採用** | 「AST は stdlib の既知 idiom」までに主張を下げる |
| A10 | 親の「dispatch は tracked 限定コピー」は誤り | **real・採用 (親の誤りを訂正)** | 非変異のコスト測定は repo 外 probe を絶対 path で dispatch 可 |
| A11 | ただし変異台帳を作るには harness が固定 HEAD の tracked target を要求する | **real・採用** | 変異測定だけ使い捨て tracked commit を使う |
| A12 | 「1 変異 27〜37 秒」の転用は不可 (実際 26.9〜42.3 秒に散る) | **real・採用** | option ごとに実測し、桁感以上に使わない |
| A13 | C1/C2 の target 解決が恒真化しうる | unknown → **段 5 の契約で閉じる** | 実装子に cardinality assert を義務付ける |
| A14 | C が閉じるのは直接 literal slice 族だけ (事前 slice・`del changed[N:]`・decoy で回避可) | **real・採用** | C の主張を「直接 literal `[:N]` 族」に限定し、負制御を測る |
| A15 | 測定 commit が本番・land 集合を汚す経路が複数ある | **real・採用** | §4 の隔離条件を必須にする |
| A16 | loader / issuer の 2 consumer 層が候補 scope から落ちている | **real・scope 外** | 追加候補として裁定パッケージへ返す |
| A17 | C3 = slice で失敗する sentinel を渡す runtime 検査があり得る | **real・採用 (限定付き)** | §2 で採用。ただし G 側のみ成立 (後述) |

### レンズ B

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| B1 | A′ (固定 fixture の増量) が選択肢に無い | **real・採用** | 独立セル化。B1 の掃引から追加費用ゼロで得られる |
| B2 | D (本番側の走査完全性 guard) が無い | **real・scope 外** (本番編集はユーザーが禁止) | 将来候補として裁定へ返す |
| B3 | E (変異 spec の恒久登録) が無い | **real・scope 外** | 裁定へ返す。harness は恒久 matrix を自動発見しない事実を添える |
| B4 | F (docstring のみ) を「閉鎖」と扱うのは誤り | **real・採用** | 独立セル化し、**「閉じた」という語を禁止**する |
| B5 | frontier は本番侵入確率ではない | **real・採用** | frontier をそのものとして報告し、露出面の事実 (V1) を併記 |
| B6 | 現行 M=2 では `[:64]` も `[:4]` も恒等 | **real・最重要・採用** | §0 のとおり枠組みを変更 |
| B7 | 不正行の位置が末尾に偏っている | **real・一部採用** | 固定 M で先頭/中間/末尾の位置変種を足す (安価) |
| B8 | DW-G05 の「不正な世代前進が受理されうる」は過大 | **real・採用** | §5 で書き換え |
| B9 | 候補を land しない判断に比較が無い | unknown → **維持** | ユーザー scope に従う。ただし可逆 patch + manifest を成果物にする |
| B10 | insights 逐語凍結は再現性を保証しない | **real・採用** | manifest (SHA-256・改行方針・base commit・version) を添える |

### 親 provisional 裁定の最終判定

- **(P1)「PBT も残穴を移すだけ」→ 限定して維持。** 「有限実行で無限族を数学的に閉じられない」は
  成立 (real)。しかし「ゆえに価値がない」は誤りで、有限領域の escape 確率は下がる。
  **本番に M の上限契約が無い**ため「有限領域を閉じた」とも言えない、が正確な形。
- **(P2)「閉じうるのは構造的検査だけ」→ 反証された。** 本番側の cardinality guard (D)、
  slice を拒否する sentinel (C3) も閉鎖手段になる。C は「source の形を pin する案」に限定する。
- **(P3)「M のコストは無視できる、争点は依存だけ」→ 未確定。** `sorted()` が両側にあり
  O(M log M) の面がある。実測して決める。「争点は依存だけ」は撤回する。
- **(P4)「hypothesis は初の第三者テスト依存」→ 反証された。** pytest は既存 import、
  pytest-xdist は既存の自動導入経路。正しくは**「初の追加 test package であり、
  tracked な依存宣言機構の新設を伴う」**。

---

## 2. 測る選択肢の確定 (plan v2)

| ID | 案 | 本 wave で | 理由 |
|---|---|---|---|
| A | 現状維持 (4 env fixture + docstring) | **実測** | 基準線 |
| A′ | 固定 fixture を 5 / 8 / 64 env へ増量 | **実測 (B1 掃引から導出)** | 追加費用ゼロで frontier を動かせる対抗案 |
| B1 | stdlib の決定的生成テスト (M を掃引) | **実測** | 依存を増やさない生成的案 |
| B2 | hypothesis による property-based テスト | **実測** | ユーザーの問いそのもの。導入不能なら「未測定」と書く |
| C1 | AST 構造検査 (exactly-one assert 付き) | **実測** | 族全体を殺す唯一の実装可能案 |
| C3 | slice で失敗する sentinel を private gate へ渡す runtime 検査 | **実測 (G 側のみ)** | レンズ A の追加案。`successor_rows` は引数なので注入可 |
| C2 | bytecode 検査 | **不採用** | C1 と検出力が同等で、Python/compiler 依存が増えるだけ。却下理由を記録 |
| D | 本番側の走査完全性 guard | **scope 外・裁定へ** | 本番編集はユーザーが禁止 |
| E | 変異 spec の恒久登録 | **scope 外・裁定へ** | 実装でなく運用の択一 |
| F | docstring の記述強化のみ | **静的評価・裁定へ** | 検出力は増えない。リスク受容の明示として別セル |

**C3 の重要な非対称性 (親の裁定):** sentinel を注入できるのは `successor_rows` (関数引数) だけである。
`changed` は関数内で `list` として構築されるローカルであり、外から型を差し替える経路が無い。
したがって **C3 は量化点 G を閉じるが P は閉じない。** これは実測で確認し、
「runtime 検査で全部閉じられる」と書かない。

---

## 3. 変異事前登録 (DW-M01 / DW-M08)

anchor (HEAD `2c0a418f` で各 1 箇所であることを確認済み):

- 量化点 G: `    for successor in successor_rows:\n` → `    for successor in successor_rows[:N]:\n`
- 量化点 P: `    for predecessor, successor in changed:\n` → `    for predecessor, successor in changed[:N]:\n`

### 単一理由性 (DW-M01)

同じ入力を拒否する層は前後に無い。実効 gate は `_validate_activation_transition` の 1 箇所で
(D245「発行 tool は独自の遷移判定を持たない」)、loader と issuer は同じ gate を呼ぶ。
G を切ると `changed` の母集合が縮むため **G の変異は P の witness も消す** — これは
単一理由性の破れではなく因果の順序であり、期待 node 集合に反映する (A2 の裁定)。

### matrix 1 — focal scope (4 node)、frontier と帰属

runner: `test_transition_rejects_fourth_env_downgrade` (D4),
`test_transition_rejects_when_{second,third,fourth}_changed_env_successor_is_false` (P2/P3/P4)

| mutant | expected_status | expected_nodes |
|---|---|---|
| G-N1 | KILLED | D4, P2, P3, P4 |
| G-N2 | KILLED | D4, P3, P4 |
| G-N3 | KILLED | D4, P4 |
| G-N4 / G-N8 / G-N63 / G-N64 | SURVIVED | (空) |
| P-N1 | KILLED | P2, P3, P4 |
| P-N2 | KILLED | P3, P4 |
| P-N3 | KILLED | P4 |
| P-N4 / P-N8 / P-N63 / P-N64 | SURVIVED | (空) |

### matrix 2 — full-file scope、生存側だけ (A の真の検出天井)

`test_env_contract_activation.py` 全体を回し、**N ∈ {4, 8, 63, 64} × {G, P} の 8 件をすべて
`SURVIVED` / `expected_nodes` 空で登録する。** ここが本 wave の中心的な主張点であり、
1 件でも KILLED になれば A の検出力は事前想定より高く、裁定の前提が変わる。

生存側だけを full-file で登録するのは、KILLED 側の期待 node 集合を full-file で正確に
書き下すことが実質不能で (T-627 は同じ理由で 7 件 MISMATCH を出した)、
frontier の確定には生存側の判定で足りるためである。KILLED 側の内訳は matrix 1 が担う。

### matrix 3 — 各候補 (DW-M08 の「新旧両走」)

各候補 (A′-8 / B1 / B2 / C1 / C3) について N ∈ {1, 4, 8, 63, 64} を回し、
**変更前 HEAD 版 (= A) と同じ変異に対する差分**を示す。候補が殺した件は
matrix 2 の SURVIVED と対にして「新テストだけが検出する差分」として記録する。

### 受理集合を変えない変異の別枠 (DW-M03 / DW-M08)

`changed[:1]` の 10 node のうち、call 列だけを見る 5 件は
**diagnostic sensitivity pin として別枠**に記録し、kill 件数へ合算しない。
意味的検出は P2/P3/P4 に非 bool・例外の 2 件を加えた 5 件である (V2)。

### 負制御 (C の限界、親測定器で in-memory 実施・dispatch 不要)

C1 が **殺せない**ことを確認する変異: 事前 slice (`changed = changed[:N]` を loop 前に置く)、
`del changed[N:]`、decoy loop の挿入。
C1 が **誤って殺す**ことを確認する変異 (偽陽性): `tuple(changed)` 化、変数 rename。
いずれも期待を事前登録し、結果を裁定パッケージの表に載せる。

---

## 4. 測定の隔離条件 (A15 の裁定、必須)

1. 候補テストを載せる commit は **side branch 上に作り、wave branch の祖先にしない。**
   land する tip の ancestry に probe を 1 件も入れない。
2. 変異走行は `tools/mutation_worktree.py --commit <probe-commit>` の使い捨て worktree で行い、
   **共有 wave worktree を `--repo` にしない。**
3. option ごとに一意な scratch root と `--out` を使う。
4. 走行中は wave worktree へ書き込まない (memory: 変異走行中は tree へ書かない)。
5. 終了時に `orchestrator/campaign/**` と `orchestrator/tests/test_env_contract_activation.py` が
   base HEAD と byte 一致することを確認して記録する。

---

## 5. 成果物影響 (DW-G05) の書き換え

旧: 「不正な世代前進が受理されうる残穴が現状のまま残る」→ **過大 (B8)。撤回する。**

新:
> 本 wave は certified 選択・レポート・台帳の値・受理集合・参照を変えない (production 不変、
> 候補テスト未 land)。実装しない場合も**現行の成果物は 1 bit も変わらない** — 現行 activation
> chain は record 1 件で遷移検査が発火せず (V1)、env は 2 個なので `[:2]` 以上の truncation は
> 恒等である。残るのは将来リスクであり、(i) record が 2 件以上に伸び、(ii) 変更 env 数または
> 不正行の位置が truncation bound より後ろに来たときに、退行が検出されずに通る。
> 発行 tool は serial 2 を publish する時点で 1 edge を実際に検査する。

---

## 6. 段 5 の分割と実装子への契約

Codex `role=author` 1 単位。所有は
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t673-transition-pbt-package/probes/` 配下のみ。

- 生成する候補: `b1_sweep.py` / `b2_hypothesis.py` / `c1_ast.py` / `c3_sentinel.py`
  (測定時に `orchestrator/tests/test_t673_probe_<id>.py` として side branch へ載せる)
- **C1 は対象 FunctionDef と対象 loop の cardinality を明示 assert する** (A13/A8)。
  `next(gen)` の裸使用でなく、`matches = [...]; assert len(matches) == 1` の形にする。
- **恒真禁止**: 観測値から期待値を作らない。空集合を通す `all([])` 形を書かない。
- 既存テスト・本番コードを 1 byte も編集しない。docs 編集と commit をしない。
- 実走できないので「実装済み・未実走」と書く。緑を主張しない。
- 完了報告に、所有外への波及可能性と、各候補が**閉じない**族を明記する。

---

## 7. 裁定パッケージへ返す項目 (scope 外の real 所見)

D (本番側 guard)、E (変異 spec の恒久登録)、A16 (loader / issuer の integration pin)、
F のリスク受容条件 (env 数・record 数・期限・再評価 trigger)、
B2 を採る場合の依存宣言機構の新設。
