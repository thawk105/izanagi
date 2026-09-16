# 既裁定の逐語 (docs/decisions.md、base 1042a1bc9 から機械抽出、省略なし)

## D65. 探索/公式の namespace・型隔離 (Stage 0) と report 証拠検査の閉表化 — 裁定パッケージ 5 件の実装 (2026-07-20)

**背景:** ユーザー裁定 (worklog 2026-07-20 (2)(3)): P-A1 は (b) 探索成果物の別 namespace/書式隔離を
先行し (a) 検査必須化は段階導入、P-A2 は「reps=5 = 成功した測定値 5 個」、P-A5/B5/B6 は推奨案承認。
プラン起草を codex に委譲するハイブリッド標準ループの初回試行で実装 (敵対相談 25 所見 → プラン v2、
レビュー 9 所見 → fix。逐語 = `output/insights/2026-07-20_wave2-adjudicated-package-loop.md`)。

**決定:**
(1) **artifact 型は JSON 互換 runtime marker であり provenance 証明ではない。** `s8b_oracle_artifacts.py`
に Official*/LegacyManifest/ExplorationArtifact を非継承で置き、official consumer (report/judge/combined
verdict) は exact type gate + strict parse (duplicate key・非有限・1e999 拒否) + 有限 float 射影で受ける。
schema 定数は本 leaf が単一 authority。
(2) **official namespace は不変、探索は `output/exploration/campaigns/`。** exploration root には
namespace.json role marker を書き、official report は resolved root の marker 検査 + campaign root の
containment/symlink component 検査で拒否 (blocklist 型。allowlist 必須化 = marker 無し root の拒否は
P-A1(a) の段階導入に残す)。
(3) **段階 truth-table は abort reason 閉表と別 leaf** (`s8b_outcome_stage_contract.py`)。段階の
存在・順序 (verify_sequence) ・abort workload frontier (4 状態: absent/invalid/legacy/s2) は形の契約、
reason 閉表は語彙の契約で、変更理由が異なる。report は StageEvidence を一度だけ射影し matches() を
module-qualified で呼ぶ。
(4) **P-A2 は report 側の証拠検査** (expected_reps = APPROVED_REPS 恒常参照、宣言 reps の一致も検査、
legacy でも免除しない)。runner の require_all_reps 既定は探索/汎用経路の契約として不変。
(5) **P-A5 は第二の部分 validator を作らず launch_validate を再利用。** public gate_check は v2 で
必ず自己検証 (launch_validated 注入口を public から除去、run-block 専用 private は caller を静的固定)。
(6) **P-A1(a) の段階導入 (未実装):** Stage 1 = report official API を VerifiedManifest のみ受理 +
verify_manifest 必須化、Stage 2 = verified upstream identity の連鎖 (observations→judge→combined の
hash 再束縛)、Stage 3 = legacy (schema/run_contract 欠落) 受理の廃止 — manifest v2 bump とは区別する。
各段階は個別にユーザー承認を得る。

**残存リスク (Stage 0 の限定保証):** 本 wave が閉じるのは「正規探索 producer 成果物の誤投入・交差
受理」まで。official schema を名乗る手書き JSON や schema-less legacy は依然 report を通る (= (a) の
責務)。意味論 leaf (outcome_stage_contract / artifacts) は oracle manifest の generator pin の外
(裁定パッケージ P-C3)。rep の「成功」は暫定的に「有限 tps が parse された rep」であり rc=0 を含意
しない (P-C1)。正当な prepare retry の report 偽陽性は既存挙動として残置 (P-C2)。

**scope 訂正:** E1 の sys.path bootstrap で s8b_verdict.py の直接実行 (既存 ModuleNotFoundError) が
修復された。V13 (CLI 実 subprocess テスト) の enabler として維持し記録で訂正。

**検収:** 対象テスト群 + 全走 7 連続緑 (2111 passed / 19 skipped)。変異 matrix 22/22 KILLED
(machine-readable 台帳 = `output/insights/2026-07-20_wave2-mutation-ledger.json`、B-057)。coverage
観測 (B-056、gate 化なし): report 76→83% / judge 77→84% / 他は同水準。研究結果・実測値への影響なし
(公式計測・freeze 再発行・artifact 発効なし)。


## D1831. 床値選択の未強制母集合は到達条件を併記した 2 群とし、二読 fallback は実装せず裁定へ返す (2026-09-08)

**決定:** 床値選択規則を強制していない入口の母集合について、次を確定する。

1. **母集合の単位は「批准床値 (`RatifiedFreeze`) を静的 loader で得る production callsite」**とする。
   2026-09-08 の main での値は 9 callsite / 9 関数 / 7 module で、内訳は強制済み 7
   (狭い選択 API 5 + full launch validation 2) と未強制 2 である。
2. **未強制 2 群は C06 予算群と、standalone gate の二読 fallback
   (`orchestrator/campaign/s8b_oracle_driver.py` の `_gate_check_core` 内 self-load) とする。**
   後者を母集合へ載せるにあたり、**到達条件を併記する** — 発火には「初回 read が失敗し、
   直後の再 read が成功する」外部要因の状態変化が要り、`sha256` 完全一致の要求により受理されうる
   freeze は active 世代そのものに限られる。先行 wave の「private core の self-load だから
   public wrapper はこの形で到達させない」という除外は採らない。
3. **件数の出所は AST 走査であると明記し、権威ある閉包に由来するとは書かない。** loader の caller を
   exact 一致で固定するメタテストは repo に実在しない。隣接する `build_observations` /
   `_gate_check_validated` / `verify_manifest` には caller 閉包テストが実在するため、
   対象を取り違えると在るものを無いと書くことになる。
4. **二読 fallback を閉じる実装は本課題では行わない。** 択一 (現状維持で記録する / exact
   `LaunchValidatedFreeze` 必須へ縮める) をユーザー裁定へ返す。
5. **library 経路 (`verify_manifest` が選択 token を要求しない、`build_observations` の
   optional 引数、`_write_approved_manifest`) にも選択強制を課さない。** production の到達経路が
   0 件であり、閉じていない範囲として記録に留める。

D1241 / D1313 の advisory / non-certifying 上限は解除しない。

**理由:**

- 除外の根拠だった「public wrapper はこの形で到達させない」は、公開 CLI からの具体経路で破れる。
  最初の freeze load が失敗すると core へ入り、core は同じ path を自分でもう一度読む。
  二読目が v2 として成功すると、launch validation を通さないまま gate 判定へ進む。
- 一方で DW-G04 は「発火条件を満たす既存 artifact path か計測 ID を書けない条件付き機能は
  設計メモに留める」と定め、DW-G05 は「成果物への影響を示せない must-fix は nit / backlog」と定める。
  この fallback は安定した同一 filesystem 状態では発火せず、どちらの基準も満たさない。
- 放置時の被害は限定される。受理されうるのは active 世代そのものであり、別の freeze が
  混入する経路ではない。欠けるのは active 世代自身の選択 identity 検査である。
- ただし D65 決定 (5) が「public gate_check は v2 で必ず自己検証」と定めており、この分岐では
  その不変条件が成立していない。**承認済み裁定に対する新事実**なので、親が不採用で閉じず
  裁定へ返す。
- 件数の出所を偽らないことは、後続が「権威ある閉包で数えた」と誤読して再検算を省くのを防ぐ。

**却下した選択肢:**

- 先行 wave の除外を維持する — 公開 CLI からの到達経路が示された以上、事実に反する母集合の上で
  残余を数えることになる。
- 二読 fallback を今すぐ token 必須へ縮める — DW-G04 / DW-G05 に反し、依頼の scope 制約
  (仮想リスク向けの gate・検査の追加は scope 外) にも反する。regression の固定には
  「初回失敗→二回目成功」を mock で作る node が要り、既存入力の回帰ではなく仮想遷移の新設になる。
- library 経路へ選択 token を課す — production 到達経路が 0 件であり、同じ理由で仮想リスク対応になる。
- 母集合の件数を「権威ある閉包に由来する」と書く — そのメタテストは実在しない。
- 到達条件を書かずに未強制 2 群とだけ記録する — 2 群の到達可能性が同じだと誤読され、
  C06 (裁定済みで機構的に到達しない) と fallback (race でのみ到達) の差が消える。


## D1872. 起動検証済み凍結の gate は exact 必須へ縮める (2026-09-09)

**決定:** `_gate_check_core` の v2 fallback を廃し、exact な `LaunchValidatedFreeze` を必須にする。
D65 決定 (5) の不変条件を全分岐で成立させる。実装面なので Codex `role=author` と変異事前登録を要する。

**理由:**

- 到達に「初回 read 失敗 → 直後の再 read 成功」という外部要因が要ることと、受理されうる freeze が
  active 世代に限られることは偶然の性質であって、gate の意味ではない。gate が 2 通りの意味を持つ
  状態は正しさゲートの穴である (規律 2)。
- 受理集合を狭める局所修正であり、新しい機構を作らない。

**却下した選択肢:**

- 現状維持で台帳へ記録する — 穴を記述するだけで穴は残る。


## D1984. 静的 loader の caller 閉包テストは現時点で新設しない (2026-09-14)

**決定:** 批准床値の静的 loader (`orchestrator/campaign/s8b_ratified_freeze.py` の
`load_ratified_freeze`) について、production caller を exact 一致で固定するメタテストを新設しない。
D1831 決定 3 が記録した「そのメタテストは実在しない」という状態を、状態のまま維持する。
母集合の件数は引き続き AST 走査由来として記録し、**権威ある閉包に由来すると書かない。**

D1241 / D1313 の advisory / non-certifying 上限は解除しない。未配線 2 群 (C06 予算群と
二読 fallback) の扱いも変えない。

**理由:**

- **反実仮想が成立しない。** 母集合の記録で実際に起きた誤りは 2 件あり、一方は carry が訂正前の
  文面を写した転記誤り、他方は private core の self-load を到達不能と判断した到達可能性の判断誤り
  である。**caller の静的件数を固定するテストは、どちらも検出しない。** 機構の必要性は、過去の
  事故を実際に止められたかで測る。
- **防ぐ対象に発生実績が無い。** このテストが検出するのは「選択規則へ配線されていない callsite が
  新たに増える」ことだけで、その発生は記録に無い。D1831 は同じ理由で二読 fallback の縮小と
  library 経路への token 追加を却下しており、本件はその却下線の同じ側にある。
- **証拠力が既存テストと重複する。** 起案された事前登録候補 10 件のうち 8 件は、同じ source 変更で
  既存テストが先に赤になる。新しい node が単独で殺せる変異は 2 件に満たず、変異 matrix は
  追加保護でなく既存保護の再計上になる。
- **受入の所要を押し上げる。** 同型の既存 inventory テストは所要時間台帳で 6.9 秒と 7.8 秒を要する。
  起案は全 production Python を対象にし、負例側で走査を反復するため、台帳値からの粗い試算で
  数十秒の追加になる。
- **上限解除に寄与しない。** D1313 は削除済み earlier run、後続世代、起動証明書の実時間性も残余と
  して挙げる。inventory の固定は未配線 2 件も公開物の受理集合も変えない。

**併せて記録する事実:**

- `assert_g1_floor_selection_identity` は g1 以外で何もせず返る。full launch core は逆に非 g1 を
  拒否する。`reverify_published_freeze` は `ReverifiedFreeze` を指定するため選択検査の分岐に入らない。
  **「launch という名の呼び出し = 配線済み」は一般には偽**であり、公開 `launch_validate` の
  exact wrapper に限って成立する。
- 静的な隣接は「公開成果物までに必ずその検査を通る」ことを証明しない。再代入・到達しない分岐・
  例外の握り潰しは静的には区別できない。配線の分類名をこれ以上強く書かない。

**却下した選択肢:**

- **隣接関数と同型の caller inventory テストを足す** — 上記のとおり過去の事故を止められず、
  既存テストと証拠が重なり、受入を重くする。
- **件数を「権威ある閉包で数えた」と書く** — そのメタテストは実在しない。D1831 決定 3 を維持する。
- **未配線 2 群のどちらかを期待値として固定する** — 二読 fallback の択一は未裁定であり、
  片方を機械的な期待値にすると変更コストの非対称が生まれる。
- **既存の同型 inventory テスト群を一般化して共通化する** — 依頼が一般化の追加を scope 外と
  定めており、本件の判断材料でもない。


# [T-2067] 持ち越し本文の逐語 (docs/archive/worklog-phase3-0916-1527.md 382〜399 行)

- [T-2067] **P1・(a)(b)(c)(d) 完了、(e)(f)(g) は塞ぎを再実測して不実装を維持。残る 1 件は裁定済み**:
  2026-09-14 の main で母集合を 3 者独立に数え直し、9 callsite / 9 関数 / 7 module・配線済み 7
  (狭い選択 API 5 + full launch validation 2) / 未配線 2 で D1831 の値と一致した。件数の出所は
  今も AST 走査であり、loader の caller を exact 固定するメタテストは実在しない。**(e)(f)(g) を
  塞ぐ 3 前提はいずれも現物で成立する** — (e) と (g) は `_load_s8c_schedule_authority` が無条件に
  raise するため予算台帳を作れる入力集合が空で、C05 は上流待ちのまま。(f) は clean scan の
  preimage が成果物へ保存されず、閉じるには D1241 / D1243 が禁じる署名・外部 nonce・一回性台帳の
  いずれかが要る。配線済み 7 の意味も狭い — 直接 API は非 g1 で空検査に、full launch は非 g1 を
  拒否し、`reverify` 経路は選択検査を通らない。現行 HEAD では loader 自体が `no-active` である。
  caller 閉包テストの新設は D1984 で不採用とした。**裁定済み (D1872、2026-09-09)**:
  `_gate_check_core` の二読 fallback (`s8b_oracle_driver.py:496`) は択 (ii) で決着している —
  v2 fallback を廃し exact な `LaunchValidatedFreeze` を必須にし、D65 決定 (5) の不変条件を
  全分岐で成立させる。D1872 は「現状維持で台帳へ記録する」を「穴を記述するだけで穴は残る」として
  却下している。実装面なので D95 の Codex role=author と変異事前登録が要る。着地は未確認。
  **いずれも D1241 / D1313 の advisory / non-certifying 上限を解除しない。**
- [T-2077] (1526)
- [T-2078] (1526)
- [T-2081] (1526)
