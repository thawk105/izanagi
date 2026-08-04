# [T-409] 実装 wave — 並行 wave [T-428] の land で裁定前提が覆り、land せず裁定へ返す

2026-08-04、dev-wave `wave-t409-impl-trigger-grammar`、基準 main = 6e22c5b、実装 commit = 48ec948
(**branch 上に留置、land していない**)。設計正本は
`output/insights/2026-08-04_t409-evolve-hole-allowlist/` (文法 v1 と裁定パッケージ)。

## 結論

**実装は完成し全緑になったが、land しない。** 並行 wave [T-428] が本 wave の走行中に main へ着地し
(`dbc0968` 2026-08-04 15:10 ほか)、trigger 軸の受理経路を**固定 5-bit wire + 32 正準述語の閉集合**へ
置き換えた。これは T-409 の裁定 (2026-08-04 /rulings) が前提にしていた「coder が自由文字列
`implementation` を hole へ書く」という攻撃面を構造的に消しており、**裁定 5 件すべての争点が変わる**。
`DW-STOP` / `DW-S04` に従い、親は不採用にせず新事実付きでユーザー再裁定へ返す。

## 覆った前提 (親が main の現物で実測)

| T-409 の前提 (裁定時) | main の現実 ([T-428] land 後) |
|---|---|
| coder は自由文字列 `implementation` を返し、hole へ逐語で入る | `CoderProposalTriggerGating` は固定 5-bit `wire` のみ。述語は凍結 emitter が生成する (`p3_s4_loop_trigger_gating.py:395-396` = `emit_predicate(parse_wire(wire))`) |
| 機械関所は禁止識別子 5 個の substring 検索だけ | 汎用 quarantine に **32 正準述語の完全一致 membership** (`p3_s4_loop.py:203` → `trigger_gate_binding.is_canonical_predicate`、集合は `emit_predicate(TriggerGateIR(mask)) for mask in range(32)`) |
| build 境界は実 source の hole 内容を検査しない | `pipeline.py:679` → `_require_materialized_trigger_predicate` が**実 source の hole 1 行を読み、束縛 mask の正準述語と byte 完全一致を要求** |
| cache / WAL / identity が policy を束縛しない | WAL に `trigger_binding` record + `build_start` commitment、admission receipt の source 束縛あり |

**受理集合の関係:** 32 正準述語の閉集合 ⊊ 文法 v1 適合式 (無限)。したがって main の membership 検査は
T-409 の文法 recognizer より**厳密に強い**。両方を置けば実効 gate は交わり = main 側になり、
T-409 の recognizer は driver 経路で死荷重になる。

## 二重化していない残余 (親が main で不在を確認)

1. **freeze 由来 literal 述語経路**: `s1_direct_comparison.py:515-523` は `system_gate` / `ident_all` の
   `gate_predicate` に**旧 blacklist だけ**を掛ける (membership 不適用)。同型で
   `s1_verify_extime_calibration.py` も literal を流す。→ main の `is_canonical_predicate` を
   consumer へ 1 行足せば閉じる (文法 recognizer は不要)。
2. **材料主張の境界**: main の `layer3_report.py` に `claim_boundaries` / finite-policy-selection は
   **0 件**。凍結 README の must-fix B-6 は未対応のまま。
3. **旧 artifact の再検査**: main に reinspection 相当は無い。ただし正しい述語は「文法適合か」ではなく
   「32 集合の membership か」に変わる。

## 本 wave の成果 (branch 48ec948、未 land)

実装は 49 ファイル (新規 4)、受入 = 関連 20 ファイル **1285 passed / 12 skipped / 0 failed**
(Pegasus gen_S、request 888536)。`check_docs.py` / `check_codex_agents.py` / `check_ai_provenance.py`
(1057 件) はいずれも緑。変異 matrix は**未実走** (land しない判断のため実施せず)。

段 6 の敵対レビュー 2 本で must-fix 15 件 (重複 3 組) を検出し、fix 3 巡で対応した。実測は
27 failed/48 errors → 12 failed → 0 failed。独立の焦点再レビュー (`DW-S06-C`) は
**closed 22 / partial 4 / regressed 0、残 must-fix 3 件**と判定した。

**親の誤判定 1 件 (訂正記録):** 焦点再レビュー子を親が「成果ゼロで異常終了」と判定して再投入したが、
実際は 1 本目がまだ走っていた (完了に約 26 分)。`.done` 不在は「未完了」であって「死亡」ではなく、
死亡判定には当該子の process 生存確認が要る。同一出力 path へ 2 本が走る状態を作ってしまい、
消費した成果物 (`s6-refocus.md`、sha256 `ca63e865…`) が上書きされる危険があった。凍結した逐語は
消費した bytes と一致することを確認済み。1 本目は親が停止した。なお fix 第 3 巡の 1 本目の死亡は
本物で、`.done` 不在に加え process 不在と repo の mtime による編集ゼロを確認している。

### 残 must-fix 3 件 (未修正、裁定材料)

1. **marker 外側の条件分岐が未検査** (`source_digest.py:245`)。`#if BACKOFF_TRIGGER_GATING && 0` 型の
   内側すり替えは拒否するが、marker の外を囲む分岐は見ない。receipt が安全な hole を指しながら
   binary が別枝を実行しうる。**この露出は main の `_require_materialized_trigger_predicate` にも同型で
   存在する** (どちらも hole 1 行しか読まない) ため、T-428 側の所見としても有効。
2. **S8A sweep の非 stock materialization が grammar を束縛しない** (`s8a_trigger_sweep.py:262,336`)。
3. **S8A sweep の quarantine 2 経路が opt-in 引数を渡さない** (`s8a_trigger_sweep.py:421,443`)。

**2 と 3 は本 wave の scope では閉じられない。** `s8a_trigger_sweep.py` は
`output/s1-freeze/known_axes_freeze.json` が live sha を pin する producer (同 freeze 内に 18 箇所出現)
であり、編集すれば凍結検証が落ちる。つまり **T-409 の設計は、凍結 pin された producer に触れないと
自身の scope (trigger 軸の全 materializer) を閉じきれない**。これも裁定の材料である。**この過程で見つかった知見は [T-428] の設計にも効く**:

- 旧 WAL terminal を標準 attempt として再発行するのは実測の捏造になる (A-10)。
- `render_hole` は hole 行の indent を前置するので、proposal 文字列と実 source bytes は一致しない (A-1)。
- `parse_template_file` は text-mode 読みで CR を落とす。source 検査は binary で行う必要がある (A-2)。
- protocol violation の診断 (無効行・truncated tail) を落とすと、確定的な correctness-red を隠す (H-1)。
- 歴史的 campaign ID は identity 束縛の追加で動く。束縛は実際に materialize する経路に限定する (G-3)。
- 汎用 diff 検疫の既定 scope に質の検査を足すと D48 決定 2 / F5 の分担 pin が壊れる (G-4)。

## 裁定パッケージ (ユーザー択一)

### 択一 A — 本 wave の実装をどう扱うか

(a) **破棄し、残余 3 点だけを小さい別 T で実装する** (親の推奨)。残余は「membership を s1 consumer へ
1 行」「layer3 の主張境界」「reinspection の要否再検討」で、いずれも T-428 の閉集合を権威にすれば安い。
(b) 実装を T-428 の上へ再統合する (14 conflict の解消 + 二重権威の一本化設計が必要)。
(c) 保留し branch を残す。

**推奨 (a) の理由:** land すると同じ hole に受理権威が 2 つ並び、弱い方 (文法) が「gate 済み」と
名乗る経路が増える。SourceEvidence v2 / admission v2 / campaign identity / layer3 schema v4 の
導入は repo 外の qualification evidence と S8B oracle manifest の再発行を要求するが、その代価を
払う相手が既に main にある機構と重複している。

### 択一 B — 受理権威をどちらに寄せるか (択一 A で (b) を選ぶ場合)

(a) 32 正準述語の閉集合 (T-428) を唯一の権威とし、文法 recognizer は削除する。
(b) 文法 recognizer を上位互換として残し、閉集合はその部分集合と位置づける。
**親の推奨 = (a)。** 閉集合は列挙可能で検証が易しく、`emit_predicate` の source が唯一の真理源になる。

### 択一 C — 旧 artifact の再検査を続けるか

(a) 32 集合 membership で再検査する新 T を起票する / (b) 旧 trigger artifact は
`legacy-unclassified` のまま扱い再検査しない。**親の推奨 = (a) の縮小版** — 実施は
「admitted view を名乗らせない」ことが本質で、reinspection ledger まで作るかは費用次第。

## 逐語 (凍結)

| ファイル | 中身 |
|---|---|
| `s1-brief.md` | 段 1 brief (pin 閉包の誤りを段 3 で訂正) |
| `s2-plan.md` | 段 2 codex プラン (`gpt-5.6-sol`、reasoning=max、read-only) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対 2 レンズ |
| `s4-adjudication.md` | 段 4 裁定 + 変異事前登録 M1-M18 / 正例 P1-P9 |
| `s6-reviewR1.md` / `s6-reviewR2.md` | 段 6 敵対レビュー 2 本 (must-fix 15) |
| `s6-fix.md` / `s6-fix2.md` / `s6-fix3.md` | fix 3 巡の対応表 |
| `s6-refocus.md` | 段 6 焦点再レビュー (closed 22 / partial 4 / regressed 0、残 must-fix 3) |

## 環境

計測 (性能) は行っていない。テスト実測 = Pegasus login node から `tools/run_tests.py` が gen_S へ
同期 dispatch した走行 (request 885111 / 887753 / 887759 / 887767 / 888336 / 888402 / 888420 / 888536)。
初回 2 回 (885111 / 887753) は queue が `INA` (229 QUE / 0 RUN) で `queue-wait-timeout` となり、
ユーザーの指示で wave を中断・回復後に再開した。
