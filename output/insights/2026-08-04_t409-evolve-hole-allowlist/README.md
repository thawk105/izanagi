# [T-409] EVOLVE-BLOCK hole の受理文法 (allowlist) 化 — 設計凍結と裁定パッケージ

2026-08-04、dev-wave `wave-t409-evolve-hole-allowlist`、基準 main = c642263。
**本 wave は実装差分を持たない。** 設計を凍結し、ユーザー択一 5 件を返して終わる。
裁定の全文と real/refuted 表は `s4-adjudication.md` が正本。

## 何を確定したか

### 1. 攻撃経路は real である (親が現物で裏取り)

trigger-gating 軸の EVOLVE-BLOCK hole は `TxExecutor::abort()` 内の 1 物理行で、置換文字列は
`izanagi_gate_pass = true;` 行の全体である。機械関所は識別子 5 個の substring 検索だけ
(`axis_trigger_gating.py:58` の `SYNTAX_CONTRACT_FORBIDDEN`、執行は
`p3_s4_loop_trigger_gating.py:114-124`)。`pro_set_` はその 5 個に無く、`TxExecutor` の member
(`external/ccbench/cc/silo/include/transaction.hh:37`) なので `abort()` から届く。

`makeProcedure(tx.pro_set_, ...)` は `RETRY:` の**前**で 1 回だけ呼ばれ
(`external/ccbench/include/ycsb.hh:102` / `:108`)、retry ループは同じ vector を舐め直す (`:117`)。
したがって hole に `pro_set_.pop_back()` を書くと、**同一論理トランザクションが retry のたびに
短くなる**。`makeProcedure` は冒頭で `pro.clear()` する (`:57`) ため、縮小は次の論理
トランザクションへは持ち越さない。

**なぜ検査を素通りするか (段 3 レンズ A が構造面から裏取り):** trace は commit した実際の
read/write 集合しか出さず、verifier の `Txn` に「予定していた操作数」の欄が無い
(`orchestrator/verifier/model.py:37`)。integrity 検査にも `FLAGS_ycsb_max_ope` との照合が無い
(`:132`)。**workload が縮んだこと自体を検出する経路が構造的に存在しない。**
なお「当該変異を入れた実 run が実際に certified されるか」は**未実測**である。

### 2. 受理文法 v1 (親裁定込みで凍結)

段 2 が起草し、段 3 レンズ A の must-fix (単独 `!` の優先順位不一致) を親が採用して `!` を削除した版。

```bnf
<implementation> ::= H* "izanagi_gate_pass" H* "=" H* <or-expr> H* ";" H*
<or-expr>        ::= <and-expr> (H* "||" H* <and-expr>)*
<and-expr>       ::= <primary> (H* "&&" H* <primary>)*
<primary>        ::= "true" | "false" | <comparison> | "(" H* <or-expr> H* ")"
<comparison>     ::= "izanagi_abort_reason_" H* ("==" | "!=") H*
                     "IzanagiAbortReason" H* "::" H* <member>
<member>         ::= kUnset | kLockConflict | kUpdateAbsent | kReadValiTid
                   | kReadValiLocked | kNodeVali | kInsertNode | kScanNode
```

- `H` = space または tab のみ。
- 許可文字 = `A-Z a-z _ : = ! & | ( ) ; space tab`。**数字を含まない** — これが択一 3 の争点。
- 判定順を固定する: `type → raw size → character → token count → parse/depth → semantic`。
- semantic 段で `reason=kUnset` 評価が `True` でなければ拒否 (D48 の fail-safe sentinel 契約)。
- 資源上限 4096 byte / 512 token / 括弧深度 64。数え方は「空白と EOF を除く lexical token 数」
  「同時に開いている `(` の最大数」「正規化前 ASCII の byte 数」と定義する。

**なぜ `!` を消したか:** C++ では `!` が `==`/`!=` より強く結合するため、
`!izanagi_abort_reason_ != IzanagiAbortReason::kUnset` を DSL は `!(比較)`、C++ は `(!enum) != ...`
と読む。`IzanagiAbortReason` は `enum class` (骨格 patch:56) で bool へ暗黙変換できないので
**受理したのにビルドが落ちる**。意味空間は `!` 無しでも失われない — `kUnset=True` 固定のまま
残り 7 値の真部分集合を `||` で列挙すれば `2^7` 写像を全て構成できる (段 3 レンズ A が反証済み)。

**通る正例:**
`izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset || izanagi_abort_reason_ == IzanagiAbortReason::kLockConflict;`

**通らない例 (本 task の起点):**
`izanagi_gate_pass = true; pro_set_.pop_back();`

### 3. 正例コーパス (回帰の基準)

`positive-controls.txt` = campaign 成果物から回収した `implementation` 26 件。
**内訳は trigger 代入式 9 件 + trigger stock の説明文字列 1 件 + sort 軸 16 件。**
新 gate に通すべきは**9 件だけ**で、26 件全部を通すことを要求してはならない
(sort の comparator と散文をコードとして認めてしまう)。9 件はすべて `kUnset` 項を含む
等値比較の `||` 連結で、上記文法で受理される。

### 4. なぜ本 wave で実装しなかったか

3 つとも親が独立に裏取りした機械的・手続的な前提である。

1. **`.claude/agents/` の変更にはユーザーの明示承認が必須** (`docs/decisions.md:1367-1370`、`:1967`)。
2. **producer を変えずに consumer だけ狭めるのは D127 決定 (1) が名指しで退けた形。**
   そして「機械化するだけで契約は狭めない」は**偽**である —
   `izanagi_gate_pass = 1;` は D48 の「コンパイル時定数のみ」契約・1 行制約・副作用なし・
   禁止識別子非参照をすべて満たすが、新文法は数字を字句段で落とす。
3. **発火条件が未確定の条件付き機能は設計メモに留める** (DW-G04)。
   どの層で発火させるかは択一 1・2 の裁定待ちである。

### 5. 実装 wave の must-fix (段 3 で確定済み、再導出不要)

| 出所 | must-fix |
|---|---|
| A2-1 | 単独 `!` を文法から削除する (上記) |
| A2-5 | token 内空白と最長一致の境界テスト (`: :`、`= =`、`! =`、`& &`、`&&&`、`===`、`\|\| \|`) |
| A2-8 | 資源上限の数え方と判定順を凍結する |
| A2-15 / B-1 | **`s1_verify_extime_calibration.py:329-357` の materializer が配線漏れ。** 汎用 `p3_s4_loop.quarantine()`・`patchharness`・`pipeline.evaluate()`・`buildcache` も trigger 文法を検査しない。**2 レンズが独立に到達** |
| B-2 | cache / replay / WAL / campaign identity が文法 policy を束縛しない。合格側の grammar version が `SourceEvidence`・preimage・`ident` に無い |
| B-4 | 「既存契約を狭めない」は偽 (択一 3) |
| B-6 | 「LLM synthesisability を維持」は過大主張。trigger 軸は高々 `2^5`、D50 実測の有効自由度は 3 bit。材料レポートに「有限 policy 選択であり headline synthesis evidence ではない」と境界を書く |
| B-10 | role 変更は review ledger・adapter・manifest を同一変更単位に要する (`.codex/role-adapters/coder-v4-autonomous-trigger-gating.json` の `.source.sha256` と `.review_ledger.source_file_sha256` が現物と一致することを親が確認済み) |

### 6. scope 外の real 所見

- **checked-in freeze と live source を結ぶ回帰テストが無い** (2 レンズが独立に到達)。
  親の実測: `axis_trigger_gating.py` へ 1 行足して全スイートを走らせても `5430 passed` で
  発火しない。ただし**本番の検証経路では発火する** —
  `s1_direct_comparison.load_verified_freeze` (`:119-131`) →
  `s1_measurement_freeze.verify_document` (`:387-408`) → `_verify_known_axes` が live source の
  sha を照合する。したがって「pin が不発」ではなく「**通常スイートが checked-in freeze 対
  live source を検査していない**」が正しい。no-touch 制約は維持。→ 択一 5
- **trigger 軸だけでは EVOLVE-BLOCK hole は閉じない。** backoff 軸
  (`p3_s4_loop.py:554-582` は数値 literal を regex で拾うだけ) に owner が無い。
  sort 軸は [T-410] が所有済み。→ 択一 4
- **verifier が workload 縮小を検出しない** (上記 1)。verifier 側の不変条件追加は別 task 候補。

## 逐語 (凍結)

| ファイル | 中身 |
|---|---|
| `s1-brief.md` | 段 1 brief (段 2・段 3 の指摘で 3 回訂正済み。訂正は本文中に明記) |
| `stage2-plan.md` | 段 2 codex プラン起草 (read-only、`gpt-5.6-sol`、reasoning=max) |
| `stage3-lensA2.md` | 段 3 レンズ A = 文法の穴と親実測の一般化 (条件付き可、must-fix 3) |
| `stage3-lensB.md` | 段 3 レンズ B = consumer 閉包・既裁定整合・全層 scope (採用不可、must-fix 5) |
| `s4-adjudication.md` | 段 4 親裁定 (real/refuted 表、択一 5 件、射程) |
| `positive-controls.txt` | 受理済み `implementation` 26 件 (回帰の基準) |

段 3 レンズ A は初回投入が上流の安全分類器に拒否されたため、防御目的 (境界テストの negative
ベクタ設計) を明示した prompt で再投入した。凍結してあるのは再投入版の出力である。

## 環境

計測は行っていない (実装差分なし)。テスト実測 = Pegasus login node から `tools/run_tests.py` が
gen_S へ同期 dispatch した走行 (request 882282 / 882288 / 883957 / 883999)。

**受入 (docs のみ):** 全スイート = `2 failed, 5437 passed, 19 skipped`。
`tools/check_docs.py` / `tools/spool_fold.py --dry-run` / `tools/check_ai_provenance.py` (992 件) は
いずれも緑。赤 2 件はどちらも本 wave の差分 (docs のみ) に帰属しない。

1. `orchestrator/tests/test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight`
   — main c642263 以前から赤。[T-407] が所有する非 UTF-8 blob
   (`output/insights/2026-08-03_t361-t362-cluster-probes/evidence/.../home-read-write.probe.raw`) を
   `ruleops.py inventory` が strict UTF-8 decode して停止する。clean tree で単独再現を実測して切り分けた。
2. `orchestrator/tests/test_codex_worker_launch.py::test_check_receipt_rejects_impossible_truth_table`
   — **単独再走で 64 passed、再現しない。**`_run_case` の子プロセスが stdout / stderr 空のまま
   rc=1 で終わる形で、`--termination-grace-s 0.05` / `--poll-interval-s 0.01` の極小時間窓を使う。
   DW-O18 に従いフレークとして起票した (worklog 新規項)。
