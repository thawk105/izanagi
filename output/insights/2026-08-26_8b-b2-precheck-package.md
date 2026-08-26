# 8b B-2 (descriptor 条件付き合成の因果証拠) の投入可否 — precheck 裁定パッケージ

**測定点:** local main `9463bcbcb1541625db59abb97cf6a76934b4c80c` (2026-08-26)。
本書の判定はこの commit 限定の snapshot であり、長期の裁定ではない。再訪条件は §7。

**結論:** **投入できない。** B-2 の証拠として受理されうる実験 (段 8c 正式系列) は、現時点で
起動経路がコード上で閉じている。最小 canary セル 1 本も取れない。実装差分ゼロで返す。

---

## 1. B-2 の実験が何であるかの同定

`docs/phase3-8b-descriptor-design.md` §1 は 2 種の実験を区別する。

- **selector 実験** — 固定 variant 集合から descriptor 条件付きで選ぶ。同節が
  「descriptor-conditioned synthesis の証拠には数えない」と自己申告する。
- **generation/search 実験** — proposal/search の開始前に descriptor を与え、on/off または
  swapped 対照を置く。「ワークロード特化合成」の主張にはこちらが必須。

`docs/phase3-8c-preregistration.md` §2 が「8b 設計 §7 の段階 2 generation/search 実験に対応」
「段階 1 の selector 実験とは独立であり、selector の成否を本系列の根拠にしない」と明記する。
したがって **B-2 の器は段 8c 正式系列であり、selector 側の状態を B-2 の証拠に代替できない。**

## 2. descriptor を渡す口は実在する (これは塞がっていない)

`orchestrator/campaign/p3_autonomous_workload_trial.py` の role payload は
`workload_descriptor` と `descriptor_binding` を持ち、proposal 生成の前に planner/coder へ渡る。
descriptor は `s8b_descriptor.project_from_search_config()` で射影され、
`s8c_arm_inputs` が on/off/swapped の入力 bytes を分離して content digest と
arm binding digest を作る。**「proposal/search 開始前に descriptor を与える口が無い」わけではない。**

## 3. 実測した閉塞 — 独立な 3 本ではなく、層である

親の初期仮説は「独立した 3 本の閉塞」だったが、段 3 の敵対相談 2 本と親の再実測により
**因果モデルを差し替えた**。閉塞は次の層で、上流ほど下流を規定する。

### (a) 発効判定 — 最上流。充足を返す終端が設計上存在しない

- 発効は `validation ∧ decider_version_matches ∧ all_filled ∧ all_satisfied` の連言
  (`orchestrator/campaign/s8c_preregistration.py`)。
- `orchestrator/campaign/s8c_preregistration_evidence.py` は
  `SATISFIABLE_CONDITION_IDS = frozenset()` を持ち、条件評価器が仮に SATISFIED を返しても
  id がこの集合に無ければ `ERROR / evaluator-internal-error` へ倒す。`_STAGED_EVALUATORS` も空。
- 実際に SATISFIED を返す site は同 module に 1 つも無い (唯一の一致は status を検査する補助関数)。
- 検出側は空ではない。`_MACHINE_EVALUATORS` は C01・C02・C04・C05・C06・C07・C09・C10・C11・C12 の
  10 件を持ち、違反 (negative control) は検出できる。**欠けているのは「完了を証明する層」だけである。**
- テストがこの終端を固定している。`orchestrator/tests/test_s8c_preregistration_predicates.py` の
  `_terminal_result` は、理想的な合成入力に対しても
  `EVIDENCE_UNDEFINED / completion-proof-not-machine-checkable` を期待値として pin する。
  すなわちこれは実装漏れではなく、8c §6 条件 2 が述べる意図された fail-closed である。

**帰結:** 実装がどれだけ進んでも、完了証明層の新設と `SATISFIABLE_CONDITION_IDS` への
条件 id の追加を行う別 wave (およびユーザー承認) が入るまで、`effective` は真にならない。

### (b) §5 の数値欄 — 8 欄中 7 欄が未記入

実測 (`s8c_preregistration.py check`) の `section5_findings`: 記入済みは「検定 4 点」だけ
(`no_hypothesis_test` の canonical JSON)。未記入は累積ベンチ実時間の上限、env_tag、
反復単位対比の判定パラメータ、master_seed、未既知性再確認の証跡、swapped 対応表、
6 cell manifest、実行責任者・開始時刻の 7 欄。
これらの記入条件自体が (a) と (d) に従属する (8c §4 の記入規約、8b §10.2)。

### (c) 正式 profile の hard stop

`_preflight_workload_profile()` は正式 profile に対し、入力検査を通したあと**無条件に**
`formal launch is not admissible: effective preregistration unavailable` を送出する。
条件分岐ではない。呼び手は `run_trial()` と CLI の 2 か所で、どちらも通る。

### (d) committed artifact の不在

`registered-effective` の起動は、measurement HEAD に commit された
6 cell manifest・発効束縛 record・trial registry を要求する (`trial_registry.py`)。
現物には `output/s8c-preregistration/` に条件契約 freeze と arm-inputs しか無く、
manifest・binding record・registry はいずれも存在しない。

### (e) schedule authority

8c supervisor の schedule 権威は現在も無条件 raise であり、C05 の評価器も
`schedule-schema-absent` を返す (親の実測で確認)。

### (f) 共有 8b ratified freeze が active でない

`registered-effective` かつ build を伴う起動だけが C06 予算を有効化し、観測開始前に
`load_ratified_freeze(ROOT)` を必ず呼ぶ。親が実測したところ、この loader は
`RatifiedFreezeError [no-active] live active pointer が無い (v2 未発効)` を返す
(v1 legacy freeze は正常に読める)。この freeze の verifier は selector predictions や
selector journal も検証対象に含む。

## 4. canary — 「構造的に不可能」は誤りだったが、今は取れない

親の初期裁定は「arm 実行は正式発効系列にしか存在しない」だったが、これは**反証された**。

- `trial_registry.admit_registered_formal_noncertifying()` という登録モードが実在する。
  明示 opt-in (`--allow-formal-noncertifying`) が要り、条件契約 freeze の妥当性だけを検査して
  **発効判定を呼ばない**。戻り値は `mode=registered-formal-non-certifying`, `certifying=False`。
  この mode のときだけ `run_trial` は正式 workload (H1/H2) を受理する。
- したがって「(a)〜(c) が正式 arm 実行を全経路で塞ぐ」という説明は誤りである。

**それでも今は canary を取れない。理由は arm の構造ではなく artifact の不在である。**

- この経路も manifest を必須とし、`load_trial_manifest()` は**ちょうど 6 試行**を要求し、
  各試行の `generations` は**整数 2 固定**、`(holdout × arm)` の全 6 組を過不足なく要求する。
  「1 セル・G=1 の軽い canary」は loader が受け付けない。
- launch binding は manifest と registry を measurement HEAD の commit 済み file として要求し、
  二段束縛 (内容 commit `P` と発効 commit `C`) も検証する。現物にいずれも無い。
- 仮に artifact を用意して走らせても `certifying=False` かつ role payload の
  `scientific_claim=False` であり、**B-2 の因果証拠には 1 行も算入できない**
  (8b §10.6 の epoch 境界: 追随実装の発効前に走った run は legacy・exploratory であり、
  後から formal へ昇格・再解釈・混合しない)。
- 正規の未登録 exploratory 経路は holdout を明示拒否し、arm execution も拒否するため
  (`exploratory run cannot carry arm execution`)、そちらでも対照は作れない。

**この wave の canary 判定:** 取らない。配線 canary は価値があるが、それは
「6 cell manifest・二段束縛 record・registry を authoring する実装 wave」の成果物であり、
precheck の scope 外である。

## 5. B-2 と selector の従属関係 (引数が問うた点)

- **結果の従属は無い。** 8c §6 の 12 前提条件に selector の実走は含まれず、8b §10 は床値を
  判定の基礎から外した。「selector 実験は B-2 の証拠に数えない」は維持される。
- **実走 infrastructure の従属はある。** §3(f) のとおり、認証経路の build は共有の
  8b ratified freeze が active であることを要求し、その freeze の検証対象に selector 成果物が
  含まれる。「selector の再凍結・active 化から独立」という言い方は誤りである。
- 引数が挙げた「selector 予測の実実行は freeze 再凍結が前提」という記述は selector 側の
  条件であって B-2 の前提条件ではない。ただし共有 freeze の active 化という一点で交差する。

## 6. 判定器の欠陥 2 件 (この wave で発見、修正はしない)

1. **`s8c_preregistration.py` を CLI として起動すると 12 条件すべてが
   `ERROR / evaluator-exception` になる。** package として import して同じ引数で
   `main()` を呼ぶと本当の内訳が出る。原因は `__main__` 実行時に core module が二重に
   実体化し、`_normalize_predicate_results` の `isinstance` 判定が落ちて例外が握り潰されること。
   `python3 <path>` と `python3 -m` の両形式で再現する。
   **正しさゲートは緩んでいない** — `effective=false` は両形式で一致し、ERROR を無害として
   受理を広げる consumer は見つからなかった (発効は exact enum SATISFIED の連言、
   両 CLI とも非発効で rc=1)。壊れているのは「何が塞いでいるか」を問う診断経路だけである。
2. **`s8c_gate_report.py` はファイルパス直接起動では動かない** (相対 import で ImportError)。
   `python3 -m orchestrator.campaign.s8c_gate_report` なら正しく動き、12 条件の本当の内訳を返す。
   すなわち**診断の正しい入口は現存する** — 1 の欠陥は `s8c_preregistration.py` 自身の CLI に閉じる。

## 7. 段 3 の所見のうち、親が採らなかったもの

- **test registry 注入と live module 差し替えで発効を偽造できる (sol 所見 1・2)。** real だが
  採らない。`_activation_report_at_for_test` / `allow_test_registry` は production entrypoint
  (`activation_report_at`) からは到達せず、in-process の module 差し替えは「repo のコードを
  書き換えられる」のと同じ権限を前提とする。commit blob 再計算という信頼境界の外側にある
  攻撃であり、ここに機械 gate を新設しても防壁は増えない。記録のみとする。
- **C04 の「旧 whole-trial no-restart policy が残っている」(sol 所見 6 の C04 項)。**
  **refuted。** C04 の評価器自身が `mark_experiment_indeterminate` と
  `forbid_trial_restart` の到達可能性を要求しており、これらは残骸ではなく契約である。
  終端が `completion-proof-not-machine-checkable` なのは §3(a) の理由による。
- **1 セル・G=1 の canary (luna 所見 4)。** refuted。§4 のとおり loader が拒否する。

## 8. 文書と現物の食い違い (別 wave へ)

8c §6 の「現状」記述には、現物より遅れているものが複数ある。段 3 の 2 レンズが挙げ、
親が代表例を確認した。

- **条件 1** — 文書は「現行の `WORKLOADS` は 100k/4 に hard-code」とするが、現物は
  `FORMAL_WORKLOADS` を `s8b_holdout_freeze.HOLDOUTS` から構成し、正式 entry に
  1,000,000 records / 48 threads を要求する (満たさなければ raise)。
- **条件 5 / 6** — 文書の「現在地」は machine-checkable の件数を古いまま述べるが、現物の
  `_MACHINE_EVALUATORS` は 10 件を持つ。条件契約の世代 10 record も C06 の昇格と
  decider v6 を記録している。
- ほかに条件 3・8・9・12 についても、段 3 が本文と現物のずれを指摘した。

**この wave では直さない。** 8c 文書の §1〜§4・§6・§7 の本文全体は条件契約の保護 hash 対象で
あり、記述を直すには条件契約の新世代 record を伴う改訂手続きが要る。**docs の 1 行修正が
発効判定の入力を動かす**ため、precheck の scope で触ってはならない。

## 9. 次に何をするか (順序)

依存グラフ上、最上流は §3(a) である。次の 1 手を 1 つだけ選ぶなら:

**「完了証明層の設計をユーザー裁定にかける」** — 具体的には、
(i) 10 件ある machine-checkable 条件のどれから充足証明を実装するか、
(ii) `SATISFIABLE_CONDITION_IDS` へ条件 id を追加する手続き (誰が承認し、どの record に残すか)、
(iii) 各条件の充足証明に対する negative control の要求水準。

これはコードの問題である前に**「どうなったら充足と認めるか」を人間が決める問題**であり、
AI が勝手に決めてよい範囲を越える。8c §6 条件 2 が「充足を返す経路は無い」と書いたのは
意図的な fail-closed であって、実装漏れではないからである。

これが決まらないうちに (b) の §5 欄記入、(d) の artifact authoring、(c) の hard stop 解除へ
着手すると、検証されない値で発効を通す順序違反になる (8b §10.2、8c §4 の記入規約が
明示的に禁じる)。

なお §3(f) の共有 ratified freeze の v2 active 化は (a) と独立に進められる別線である。

## 10. 再訪条件

本書は `9463bcbc` 限定の snapshot である。次のいずれかが変われば再実測する。

- `SATISFIABLE_CONDITION_IDS` が空でなくなる。
- `output/s8c-preregistration/` に 6 cell manifest または発効束縛 record が現れる。
- `output/s8b-freeze/active/` が現れる (v2 active 化)。
- `_preflight_workload_profile` の正式 profile 分岐が条件付きになる。
- 8c 事前登録の条件契約 freeze が世代 10 から進む。

再実測の最短手順は
`python3 -m orchestrator.campaign.s8c_gate_report --commit HEAD --repo-root .` である
(`s8c_preregistration.py` の CLI は §6 の欠陥により内訳を返さない)。

**還元判断: 不要** (CCBench 上流への還元対象ではない。本書は izanagi 内部の順序裁定である)。
