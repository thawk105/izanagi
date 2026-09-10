# 段 1 brief — [T-396] EVOLVE-BLOCK hole の reward hack 経路を機械 gate で塞ぐ

wave = `dev-wave-t396-hole-allowlist`、基準 main = `01af552f`、2026-08-15 07:40 JST。

## 前提実測で覆った事実 (すべて親が現物で裏取り。段 4 で再裁定する)

依頼文が引く台帳 (`docs/archive/worklog-phase3-0804-148.md` の [T-396]) は 2026-08-04 起票で、
**その記述する攻撃面は trigger 軸では既に消滅している。**

1. trigger 軸の coder 出力は固定 5-bit `wire` (32 通り閉集合)。C++ は凍結 emitter
   `emit_predicate(parse_wire(wire))` が生成する (`p3_s4_loop_trigger_gating.py:414`)。
   任意テキストが hole へ入る経路が無い。[T-428] が 2026-08-04 に着地させた。
2. `SYNTAX_CONTRACT_FORBIDDEN` (識別子 5 個) の使用は 2 箇所だけで、どちらも単独関所ではない。
   (a) `check_syntax_contract` = 凍結 emitter 出力の drift assertion (「候補の受理 gate ではない」
   と同関数 docstring に明記)、(b) `s1_direct_comparison.py:639` = `is_canonical_predicate` の
   membership 検査と併用。
3. **AST allowlist は先行 wave [T-409] が完成させ、2026-08-05 にユーザーが「land せず破棄」と
   裁定済み** (worklog entry 166 / 193、控え = rulings-inbox の
   `2026-08-04-t409-implementation-superseded.md`)。理由 = 同じ hole に受理権威が 2 つ並び、
   弱い方が「gate 済み」と名乗る。残余は [T-472] (着地)・[T-473] (未着手)・[T-474] (着地) へ分割。

**したがって台帳の字面どおり「trigger 軸へ AST allowlist を実装する」ことは、既裁定に反する。**

## 生きている攻撃面 (これを本 wave の scope とする)

同じ reward hack が **sort 軸で無防備に成立する。**

- `CoderProposalSort.implementation` = 「hole 全体 (`sort(...)` 文一式) を置換する文字列」。
  識別子 blacklist は sort 軸に**一切かかっていない**。
- `diff_quarantine.DiffQuarantine.validate` は **C++ を解釈しない** (実装コメントに明記)。
  hole 内挿入行への検査は byte 規則のみ = 生前処理指令 / EVOLVE-BLOCK マーカー /
  コメント delimiter / 行末 backslash。**行数上限も文の個数制限も無い。**
- `sort_swo_oracle.check_materialized_sort_swo` は comparator の strict weak ordering だけを見る。
- hole は `external/ccbench/cc/silo/transaction.cc:408` = `TxExecutor` メンバ関数内。
  `pro_set_` は同クラスの member (`cc/silo/include/transaction.hh:37`)。
- 攻撃ベクタ: hole を `pro_set_.pop_back();` + 正当な SWO comparator の 2 文にする。
  検疫も oracle も通り、**関所は LLM auditor だけ**になる。
- 同型の既実測: D127 背景が `std::system` / `execl` / `std::ofstream` / 無限ループの
  hole 内 1 行がいずれも `DiffQuarantine` を通ることを実測済み。
- 検出不能性: verifier の `Txn` に「予定操作数」欄が無く (`orchestrator/verifier/model.py:37`)、
  integrity にも `FLAGS_ycsb_max_ope` 照合が無い (`:132`)。**workload 縮小を検出する経路が
  構造的に存在しない。** = serializable のまま throughput だけ上がる。

## scope (P1〜P3 は親の provisional 裁定であり攻撃対象)

**(P1) 対象軸を sort 軸に限定する。** trigger 軸へは触らない (既裁定 2026-08-05)。
**(P2) 新 gate は「宣言済み producer 契約の機械執行」であり、宣言を狭めない。**
`.claude/agents/coder-v4-autonomous-sort.md:85-89` は既に
「新しいヘッダ取り込み・型/関数/マクロ/グローバル変数の追加は禁止」
「生の前処理指令は禁止」「非決定ビルトインは禁止」
**「既存 silo API を呼ぶ straight-line code のみ (副作用のある呼び出し・ループ・例外送出は不可)」**
と書いている。`pro_set_.pop_back()` は「副作用のある呼び出し」で契約上すでに禁止であり、
機械が検査していないだけである。よって D127 決定 (1) の「producer を変えず consumer だけ狭める」
には当たらず、`.claude/agents/` の改変 (ユーザー明示承認が必須) も不要。
**(P3) 発火層は materializer に置く** (D127 決定 (3) と同型 — driver 単独では sweep /
`pipeline.evaluate()` / 手動 patch が素通しになる)。配線先の実在は段 2 が file:line で確定する。

**scope 外 (実装しない):** trigger 軸の文法 recognizer、[T-473] (layer3 claim_boundaries)、
verifier への予定操作数の導入 (別 task 候補)、sandbox 化。

## 不変条件

- 規律 2: 正しさゲートを緩める方向の変更をしない。gate の禁止は署名で書き、通る正例を添える。
- D96: 受理集合が縮むので、**新しい D の記録**と**境界テストの同時更新**を同じ変更単位で行う。
- 凍結: `s1_known_axes_freeze.py` が live source の sha256 を pin する。編集面が
  `s1_direct_comparison.py` / `s8a_trigger_sweep.py` に及ぶと凍結検証が落ちる (F301 と同型)。
  **段 2 は編集面ごとに pin 閉包を識別子 key と path の両方で再検索すること。**
- 既存テストの期待値を変更しない。赤なら実装側が誤りとする。

## 成果物の形

1. sort 軸 hole の受理判定器 (Python、self-contained。libclang 等の外部依存を gate 経路へ入れない)。
2. materializer 側の配線 (P3)。
3. 境界テスト = 拒否ベクタ + 正例。**正例の正本は
   `output/insights/2026-08-04_t409-evolve-hole-allowlist/positive-controls.txt` の sort 軸 16 件**
   (同 dir README が内訳を凍結済み)。16 件が全て通ることを要求する。
4. 新 D (D96 手続)。
5. 変異事前登録 (段 4、`DW-M01`)。受理集合を縮小するので**承認外の過剰拒否を検出する正例**を必ず登録する。

## 成果物影響 (DW-G05)

実装しない場合: sort 軸の coder 自律ループで、workload を縮める variant が
**certified 選択の候補として build・計測・fitness 評価まで到達しうる**。verifier が構造的に
検出しないため、certified な選択結果と材料レポートの throughput 値が偽になる。関所は LLM auditor 1 枚。

## 並列分割方針

判定器 (新規ファイル) と materializer 配線 + テストで編集ファイル所有が素集合になる。
段 5 は 2 単位まで。段 3 敵対相談は 2 レンズ (正しさ境界 / 整合・実効性)。

---

## 段 2 による brief の訂正 (2026-08-15 08:23 JST、親が現物で裏取り済み)

**本節が上の scope 節に優先する。上の (P1)〜(P3) は段 4 で再裁定する。**

段 2 プラン (`s2-plan.md` §1) が親の中核主張を反証した。親は 3 点とも独立に裏取りし、採用した。

1. **「攻撃ベクタは検疫と oracle を通過する」は誤り。**
   `sort_swo_oracle._validate_single_sort_statement` (`orchestrator/campaign/sort_swo_oracle.py:486-548`)
   が hole を「非修飾 `sort` で始まり、対応する閉じ括弧の後は `;` だけ」の**単一文**に限定する。
   - `pro_set_.pop_back(); sort(...);` → `qualified-or-non-sort-callee`
   - `sort(...); pro_set_.pop_back();` → `not-a-single-sort-statement`
   既存境界テスト `orchestrator/tests/test_sort_swo_oracle.py:297-312` が後者を固定済み。
2. **「sort 軸に識別子 blacklist が一切かかっていない」は誤り。**
   `orchestrator/campaign/coder_effect_gate.py:58-105` の `DENY_TABLE` が
   process-shell / file-stdio / network / sleep-block-thread / escape-hatch の識別子群と
   無条件ループ・malformed token・256KiB / 4096 token 超過を拒否する。
   正しくは「汎用 host-effect blacklist はかかるが、`pro_set_` / `pop_back` を収載していない」。
3. **oracle 不可用は fail-open ではない。** `p3_s4_loop_sort.py:191-196` が
   `OracleStatus.UNAVAILABLE` で `SortSwoOracleUnavailable` を送出する (D344 決定 4 のとおり)。

### 決定的な既裁定 — D344 (2026-08-12)

`docs/decisions.md` D344 の「却下した選択肢」第 1 項が本 wave の提案そのものである。

> **sort comparator への typed IR / AST allowlist** — 純粋な field 読取りと比較演算だけに制限すれば
> 同一 process 内の干渉も閉じられるが、「合成」が「事前 allowlist からの選択」に化け、
> raw C++ comparator の独立合成という実証点 (D39) を別実験に変える。既裁定の非対称構成
> (sort は raw 合成維持) と非同値に衝突するため、**親は決めずユーザー裁定へ返す**。

**したがって sort 軸の AST allowlist も、trigger 軸と同じくユーザー裁定待ちである** (`DW-STOP`)。
親 brief の (P2)「宣言済み契約の機械執行にすぎないので宣言を狭めない」は、段 2 §2 の
契約項目別 機械検査可能性 表により**無条件には成立しない**と判定された
(「任意の既存 API call が副作用なしであることは C++ 意味解析なしには判定不能」)。

### 残る scope 候補 (D344 と衝突しない唯一の残余)

段 2 §1 末尾: 「既に materialize された source を `pipeline.evaluate()` や `buildcache.build()` へ
直接渡す経路は quarantine / auditor / SWO oracle を通らない」。
これは AST allowlist ではなく **既存 gate の配線漏れ**であり、D127 決定 (3)
「gate は driver ではなく materializer に置く」と同型の是正になる。
**段 3 の 2 レンズは、この残余が実在の到達可能経路かを最優先で判定すること。**
実在しなければ本 wave は実装差分ゼロで裁定パッケージへ返す。
