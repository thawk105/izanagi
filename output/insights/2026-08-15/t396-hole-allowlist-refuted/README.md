# [T-396] EVOLVE-BLOCK hole の reward hack 経路 — 起票の前提が現行 main で失効し、実装候補が消えた

2026-08-15、dev-wave `dev-wave-t396-hole-allowlist`、基準 main = `437be358`
(起動時 = `01af552f` → wave 中に fast-forward)。**本 wave は実装差分を持たない。**
段 4 で「実装しない」と裁定し、択一 3 件をユーザーへ返す。

逐語は `verbatim/`。段 1 brief (訂正節つき)、段 2 プラン、段 3 敵対 2 レンズを凍結した。

## 1. 何を確定したか — 起票の前提は 3 点とも失効している

[T-396] の台帳本文 (`docs/archive/worklog-phase3-0804-148.md`) は 2026-08-04 起票である。
そこに書かれた攻撃面は、現行 main には無い。

| 台帳 (2026-08-04) の前提 | 現行 main (`437be358`) の実測 |
|---|---|
| trigger の hole は `abort()` 内の任意 1 行で、LLM が任意 C++ を書く | 任意テキスト経路は不在。coder 出力は固定 5-bit `wire` (`p3_s4_loop_trigger_gating.py:114`)、`parse_wire` は長さ 5 の `0/1` のみ受理 (`reflux_ir.py:113`)、hole text は凍結 emitter が生成する (`reflux_ir.py:131`) |
| 機械 gate は識別子 5 個の blacklist だけ | `SYNTAX_CONTRACT_FORBIDDEN` が単独の受理関所である箇所はゼロ。production caller は 3 箇所で、いずれも membership 検査か quarantine と併用 (`p3_s4_loop_trigger_gating.py:410`、`s1_direct_comparison.py:635`、`p3_autonomous_workload_trial.py:889`) |
| 関所は auditor (LLM) だけである | trigger 軸は 32 正準述語の完全一致 membership + build 境界の materialized source byte 一致 |

前提を消したのは並行 wave [T-428] (2026-08-04 着地) である。

## 2. 台帳が指す実装は、既にユーザー裁定で破棄されている

先行 wave [T-409] (worklog entry 166、branch `worktree-wave-t409-impl-trigger-grammar`、
commit `48ec948`) が AST allowlist 相当の文法 v1 を**設計・実装し全緑にした**。
その実装は **2026-08-05 の /rulings で「択一 A = (a) land せず破棄」と裁定済み**
(worklog entry 193)。理由は「同じ hole に受理権威が 2 つ並び、弱い方が gate 済みと名乗る」。
残余は [T-472] (entry 207、着地)・[T-473] (未着手)・[T-474] (entry 217、着地) へ分割された。

段 3 レンズ B が裁定文と `s4-adjudication.md` の択一表を選択肢集合で照合し、
**この裁定の射程は trigger 軸に限られる**ことを確認した (親の読みは正しい)。
ただしそれは sort 軸への実装許可を意味しない (下記 §4)。

## 3. 同じ攻撃を sort 軸で試みたが、既存 gate が構造的に拒否する

sort 軸 (`p3_s4_loop_sort.py`) の `CoderProposalSort.implementation` は hole 全体を置換する
自由文字列であり、trigger 軸と違って任意 C++ が入る。親は段 1 で
「`pro_set_.pop_back();` + 正当な SWO comparator の 2 文にすれば関所は auditor だけになる」と
書いたが、**これは誤りである** (段 2 が反証し、親が現物で裏取りして採用した)。

- `sort_swo_oracle._validate_single_sort_statement` (`sort_swo_oracle.py:486-548`) が hole を
  「非修飾 `sort` で始まり、対応する閉じ括弧の後は `;` だけ」の**単一文**に限定する。
  - `pro_set_.pop_back(); sort(...);` → `qualified-or-non-sort-callee`
  - `sort(...); pro_set_.pop_back();` → `not-a-single-sort-statement`
  - 後者は既存境界テスト `orchestrator/tests/test_sort_swo_oracle.py:297-312` が固定済み。
- `coder_effect_gate.DENY_TABLE` (`coder_effect_gate.py:58-105`) が process-shell / file-stdio /
  network / sleep-block-thread / escape-hatch の識別子群と無条件ループ・malformed token・
  256KiB / 4096 token 超過を拒否する。`pro_set_` / `pop_back` は収載していないが、
  「blacklist が一切かかっていない」という段 1 の記述は誤りだった。
- oracle 不可用は fail-open しない。`p3_s4_loop_sort.py:187-196` が `OracleStatus.UNAVAILABLE` で
  `SortSwoOracleUnavailable` を送出する (D344 決定 4 のとおり)。

## 4. 段 2 が唯一残した実装候補も、レンズ A が caller 閉包で反証した

段 2 プラン §1 末尾は「materialize 済み source を `pipeline.evaluate()` や `buildcache.build()` へ
直接渡す経路は quarantine / auditor / SWO oracle を通らない」と述べた。
段 3 レンズ A が **両 sink の production caller を全列挙し、source 由来を分類**した
(逐語 = `verbatim/s3-lensA2.md` 所見 1)。

- `pipeline.evaluate()` の production caller = `loop.py:256` / `screening_driver.py:189` /
  `s1_direct_comparison.py:970` / `s8b_oracle_driver.py:1490` / `t126_driver.py:537`。
- `buildcache.build()` / `build_v2()` の直接 caller = `s1_verify_extime_calibration.py:358`、
  `backoff_profile.py:148`、`backoff_overthrottle.py:83`、`s2_verify_calibration.py:306-307`、
  `s5_permutation_coverage.py:195`、`pegasus_floor_scoping.py:218`、`between_run_floor.py:167`、
  `s3_lock_coverage.py:199`、`s8b_floor_campaign.py:1949,2115,4118`、`s8b_oracle_driver.py:1091`。
- 各 caller の source は (ii) 列挙・有限構成、または (iii) 凍結 patch / stock であり、
  **(i) LLM 合成断片がこれらへ直接到達する経路は 1 本も無い。**
- LLM sort 断片の唯一の production 列は
  `load_proposal_file` (`p3_s4_loop_sort.py:359`) → `drive_iteration` (`:415`) →
  quarantine + auditor (`:152`) → SWO oracle (`:162`) → `run_campaign` (`:318`) →
  `evaluate` (`loop.py:256`) → build (`pipeline.py:851`)。

**親の裁定:** レンズ A を採用し、レンズ B の所見 7 (「残余は実在する」) を refuted とする。
レンズ B は関数が sort gate を再実行しないことだけを見て caller の到達性を見ていない。
これは親が段 1 で犯したのと同型の誤りである (§6)。

## 5. 決定的な既裁定 — D344 (2026-08-12)

D344 の「却下した選択肢」第 1 項が、本 wave の提案そのものである。

> **sort comparator への typed IR / AST allowlist** — 純粋な field 読取りと比較演算だけに制限すれば
> 同一 process 内の干渉も閉じられるが、「合成」が「事前 allowlist からの選択」に化け、
> raw C++ comparator の独立合成という実証点 (D39) を別実験に変える。既裁定の非対称構成
> (sort は raw 合成維持) と非同値に衝突するため、**親は決めずユーザー裁定へ返す**。

レンズ A・B が独立に「段 2 の提案文法は選択肢集合として D344 の却下対象と一致する」と判定した。
文法が再帰的で受理集合が無限でも、field と operator の有限 production から合成する DSL に変わる
ためである。したがって `DW-STOP` の「ユーザー裁定待ち」に該当し、親は実装できない。

親が段 1 で置いた (P2)「宣言済み producer 契約の機械執行にすぎないので宣言を狭めない」も
成立しない — 段 2 §2 と段 3 レンズ A 所見 2 が、
「任意の既存 API call が副作用なしであることは C++ 意味解析なしには判定不能」
「提案文法は既存正例の generic lambda (`const auto&`) を落とす」ことを示した。

## 6. 親の誤りの型 (記録として残す)

親は段 1 で「gate が無い」と 3 度書き、3 度とも実在した。レンズ B が F73 型
「防壁の射程誤認」と診断した — 軸限定の gate 不在を全関所の不在へ一般化している。

恒久対応として、段 1 で **gate inventory 表**を作ることを段 8 の改善候補へ回す。
入口から下流への順方向表と、各 gate symbol から caller への逆方向表に、
file:line・拒否条件・UNAVAILABLE 挙動・直接 caller・既存 test を記録し、
その表なしに「gate は無い」と書かない。今回レンズ A の caller 閉包が実際にこの表であり、
それが唯一の実装候補を反証したことが有効性の証拠である。

## 7. 実装しなかったが real と裁定した所見 (裁定材料)

段 3 レンズ A 所見 2 が、`.claude/agents/coder-v4-autonomous-sort.md:84-89` の closed-region 契約に対し、
**機械執行されていない項目を 5 つ**特定した。いずれも「契約は禁じているが機械は見ていない」型である。

| 契約項目 | 未実装の内容 | 放置した場合に起きること |
|---|---|---|
| 型/関数の追加禁止 | lambda 本体は raw C++ のまま compiler へ渡る (`sort_swo_oracle.py:1529`) | 宣言した三 field 能力より広い source が受理される |
| 非決定ビルトイン禁止 | `DENY_TABLE` に time / random の閉じた禁止集合が無い | 有限観測で変動しなかった非決定性が通り、実 workload で relation が変わる |
| 副作用のある呼び出し禁止 | blacklist 外で corpus を変えない call は受理されうる (実装自身が残余を明記、`coder_effect_gate.py:12`) | TxExecutor / process / host 状態を介して workload や fitness を変える余地が残る |
| ループ禁止 | 明示的な無条件 `while`/`for` だけを拒否 (`coder_effect_gate.py:527`) | bounded / data-dependent loop が通り、実 workload だけで長時間化しうる |
| 例外送出禁止 | `throw` 自体の構文禁止は無く、有限 corpus で発火した分だけ捕捉 | corpus で発火しない条件付き送出が通り、実入力で sort を中断しうる |

**最も重い所見:** bounded / data-dependent loop は「通ること」が
`orchestrator/tests/test_coder_effect_gate.py:151` で**明示的に固定されている**。
契約と実装の不一致がテストで恒久化されている状態である。

段 3 レンズ B 所見 8 は、これらより **verifier の予定操作数欠落**が本丸だと指摘した。
`orchestrator/verifier/model.py:37-48` の `Txn` は実際の reads/writes しか持たず、
`:132-148` の integrity も予定操作数との照合を持たない。
入口の文法 gate はこの不変条件を代替しない。

## 8. 訂正した親の記述

- 正例コーパスの内訳は「sort 軸 16 件」ではなく **実 C++ implementation 15 件 + `SORT_VARIANT=0` の
  stock メタデータ 1 件**である (`positive-controls.txt:9`、`s6_sort_sweep.py:154` の `STOCK_IMPL_NOTE`)。
  説明文を文法の正例にすると非 C++ を受理させることになる。
- `check_syntax_contract` の production caller は 2 箇所ではなく 3 箇所である
  (`p3_autonomous_workload_trial.py:889` を数え落とした)。結論には影響しない。

## 9. 裁定パッケージ (ユーザー択一)

### 択一 A — closed-region 契約の 5 つの未実装項目 (§7) をどうするか

- **(a) 契約側を実態へ合わせる (親の推奨)。** `.claude/agents/coder-v4-autonomous-sort.md` の
  closed-region 節を「機械執行される項目」と「auditor 目視に委ねる残余」に二分して明記する。
  D344 の設計 (raw C++ 合成を維持し、有限 corpus 上の反例探索 gate で守る) と整合し、
  受理集合を変えないため D96 の境界テスト更新も不要。`.claude/agents/` 改変の明示承認は要る。
- (b) 実装側を契約へ合わせる = typed IR / AST allowlist を導入する。**D344 を明示的に覆す裁定が要る。**
  合成が事前 allowlist からの選択に化け、D39 の実証点 (LLM が raw C++ comparator を独立合成できるか) が
  別実験に変わる。先行実装 (T-409 の文法 v1) は破棄済みで再作成が要る。
- (c) 現状維持。契約文言と機械執行の乖離をそのまま残す。

**推奨 (a) の理由:** 乖離の実害は「契約に書いてあるのに守られない」という記述の誤りであって、
到達可能な reward hack ではない (§3・§4 で実測)。記述を正すのが最も安く、
研究上の実証点を壊さない。

### 択一 B — テストで恒久化された契約違反 (bounded loop) をどうするか

- **(a) テストの意図を明示する (親の推奨)。** `test_coder_effect_gate.py:151` に
  「契約は禁じるが本 gate は検査しない (auditor 残余)」を書き、択一 A の (a) と対にする。
- (b) bounded loop を機械拒否する。**受理集合の縮小なので D96 手続 (新 D + 境界テスト) が要る。**
  data-dependent loop の判定は停止性判定に近く、過剰拒否の危険が高い。
- (c) 現状維持。

### 択一 C — verifier の予定操作数検査 (§7 末尾) を起票するか

- **(a) 独立 T として起票する (親の推奨)。** workload 縮小を検出する不変条件の欠落は、
  入口 gate では代替できない。今回の 3 レンズすべてが独立に言及した。
- (b) 起票しない。

### 択一 D — 段 8 の改善候補 (§6 の gate inventory) を dev-wave docs へ入れるか

段 8 で `DW-S01` へ次の 1 文を追記しようとしたが、**L1 予算に収まらず取りやめた。**

> 「gate が無い」は sink の caller 閉包と由来分類なしに書かない（F73）。

実測: 追記後の L1 unique footprint は 10,710 bytes で、予算 10,625 bytes を **85 bytes 超過**する
(短縮前の初版は 169 bytes 超過)。`docs/skill-self-improvement.md` の
「予算に収まらなければ reference へ統合し、それでも意味等価にできなければ変更を止めてユーザー裁定へ
返す」に従い、本文編集は行わず復元した (`check_docs.py` は緑)。

- **(a) 入れない (親の推奨)。** 本 wave の insight と worklog に記録済みで、実害は
  「親の段 1 実測が 1 回遠回りした」ことに留まる。予算は上げない。
- (b) L2 の空き枠へ新節として入れる。D271 の新規 L2 登録条件
  (発火実績あり × 義務が現に機械代替されていない × 同じ意味検索で反証も既存正本もなし) の
  判定が要る。発火実績は本 wave の 1 件 (レンズ B も同型の誤りを犯したので実質 2 件)。
- (c) L1 の既存文を削って空きを作る。**過去 2 wave が「削除可能な節ゼロ件」を実証済み**のため、
  安全義務の弱化になる危険が高い。

## 10. 環境と実測

計測 (性能) は行っていない。テスト実測は段 7 の記録 commit 後に受入全走で行い、
結果は worklog エントリへ書く。段 3 レンズ A の初回投入は上流の安全分類器に拒否され
(`This content was flagged for possible cybersecurity risk`)、model call 16 回・出力 0 bytes を
空費した。F256 の再発である (§記録は `docs/failures.md`)。防御目的は prompt 冒頭に書いていたが、
後から追記した節が「回避する C++ 文字列を構成せよ」と攻撃成果物の作成を求めていた。
被覆監査の枠組みへ書き直した再投入版が成功し、凍結してあるのはその再投入版である。
