---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1879-cir-cvn
seq: 1
title: [T-1879] arXiv 2604.09318 (CIR+CVN) の一次資料で軸 1 への接地を確定した — 対象はトランザクションの並行性制御ではない (docs のみ、branch worktree-dev-wave-t1879-cir-cvn、実装面の差分ゼロのため変異 matrix は DW-S04 で免除)
---

## 本文

- **依頼は「一次資料を読んで軸 1 への接地を確定せよ」。** `docs/related-work/claim-survey/2026-08-26-inventory.md`
  の軸 1 分類 pilot が、監査前の 1 行要約からは包含条件 A を決められず `要裁定` に残した 4 件のうち、
  最も軸 1 の核に近いとされた 1 件である。
- **判定は `部分接地` / 極性 `方法論的祖先`。軸 1 の主題ではない。** 対象はスレッドの同期構造
  (mutex / rwlock / condvar / semaphore / channel / atomic) のデッドロックとシグナル消失であって、
  トランザクションの並行性制御ではない。包含条件は A=✗、B=✓、C=✗、D=✓。
  全根拠は `docs/related-work/claim-survey/2026-08-26-cir-cvn-adjudication.md` (新規・凍結物)、
  精読は `docs/related-work/notes/note_cir_cvn_bridging_llm_semantic_understand.md` (新規)。
- **`要裁定` の原因は日本語要約の 1 語だった。** `docs/related-work/literature-map/` の要約は
  「並行制御構造を合成」と書いており、これは concurrency control とも concurrency structure とも
  読める。原文は後者である。**litmap は監査前データなので書き換えず**、同 README の
  「既知の危険」へ 2 例目として足した (1 例目は Polyjuice / CCaaLF の「合成」の語)。
  同じ producer の同型欠陥なので DW-G03 の族一般化は行わない。
- **段 6 の敵対レビュー (read-only codex) は主判定を支持し、must-fix 6 件と nit 2 件を返した。
  全件を一次資料へ照合して real と裁定し反映した。** 最も価値があったのは 4 件目である。
  親は「修理の回帰 4 件はすべて第 1 層の静的検査が捕まえた」と書いていたが、一次資料はそれとは
  別に **61 本の静的規則もバグ検出器も素通りする意味的な回帰 2 件**を報告しており、
  「目標到達検査だけがこれを捕まえる。無ければ、本質的な振る舞いを黙って落とした修理が
  検証済みとして受理される」と明記している。**これは絶対規律 2 の外部証拠として本件で最も強い
  部分であり、親はそれを取りこぼしたまま弱い形で書いていた。** 逐語を引いて直した。
- **他の must-fix。** (a) 表を文章へ組み直したものを逐語と称していた → 転記と明記し、
  閉じた集合であることの根拠を §4.1 の形式定義の逐語へ移した。(b) arXiv の site 告知文を
  `profit! Learn more` と切り出して「広告文」としていた。原文は
  `arXiv is now an independent nonprofit! Learn more` である。(c) `atomicity` 2 件の文脈のうち
  1 件は参考文献の題名だった。(d) 判定記録が「世界の不在は一切主張しない」と自称しながら
  7.6 の空白域を肯定していた。軸 1 は `RW1` なのでその資格が無い → 自分で測る不在はこの 1 論文の
  中だけとし、既存の世界側の不在は `RW1` が許す逐語引用に限って出典節・掃引日・監査前である旨を
  併記する形へ直した。(e) 「性能は評価されない」が無限定だった → この論文は状態空間探索と検査の
  時間を測っているので「アプリケーションのスループット・遅延を評価しない」へ限定した。
- **7.6 の空白域 1 から「対象は Rust/C の逐次コード・形式仕様」という母集団の特徴づけを
  取り下げた。** CIR+CVN は同じ検証付き合成の群で対象が並行プログラムであり、
  母集団全体がどちらへ寄っているかは一次資料 1 件では測れない。**空白域の主張そのものは
  変えていない。**
- **`docs/paper-story/2026-08-26.md` §3 の 1 は書き換えない。** CIR+CVN は現行の文を覆さない。
  ただし覆さない理由は 2 つの限定にあり、**どちらを落としても本件が反例になる** —
  (1) 対象がトランザクションの並行性制御であること、(2) 空間の「拡張」であって固定した
  原始操作語彙の中の「生成」ではないこと。CIR+CVN は Cir とソースコードの両方を生成するので、
  「LLM に並行処理のコードを書かせた例は無い」とは書けない。版は凍結物なので
  `docs/paper-story/README.md` の「最新スナップショット以後に確定したこと」から指した。
- **§8 の C-4 (体系的な先行研究調査) はこの 1 件では閉じない。** pilot の `要裁定` は
  3 件残り、そもそも pilot の母集合は `literature-map/` の閉じた 29 件で、7.7.4 が求める
  索引・検索式・cutoff の事前登録は未着手である。**軸 1 の成熟度は `RW1` のまま動かない。**
- **規律 6 の走査は陰性。** 本文全体に対し誘導記述の定型 16 語を走査し、唯一の hit
  (`report that`) は道具の診断の説明文だった。anomaly なし。
- **検査。** `tools/check_docs.py` rc=0、焦点走 (`orchestrator/tests/test_check_docs.py`)
  560 passed / 3 skipped、`tools/check_ai_provenance.py` 6,277 件 新規違反なし。
- **受入全走は 2 走とも同じ 1 件の非帰属赤で戻った。** どちらも
  1 failed / 17390 passed / 64 skipped、rc=70 (source_rc=1)。唯一の赤は
  `test_codex_worker_launch.py::test_sigterm_ignoring_child_is_killed` で、assertion 本文は
  `child.pid was not registered before deadline; stderr=''` — launcher の子が **2 秒の deadline 内に
  child.pid を登録しなかった**という時間依存の主張である。同一 tree の単独走は
  1 passed / 7.18 秒 / rc=0 で再現しない。当 wave の差分は docs だけで `tools/` にも
  `orchestrator/` にも触れていないため帰属しない。
- **DW-O18 に従い hold へ登録した。証拠は F57。** 実装面なので Codex `role=author` が
  `orchestrator/tests/flaky_test_holds.py` へ 1 行足した (`evidence_id="F57"`、
  `failure_signature="child.pid was not registered before deadline; stderr=''"`、
  `reintroduction_task_id` は slug `flaky-child-pid-registration-deadline` の placeholder 形式で、
  既存 3 行と同じく未解決のまま置く)。
  登録件数は 3 から 4 になった。焦点走
  (`test_flaky_test_holds_contract.py` + `test_check_docs.py`) は 597 passed / 3 skipped。
- **[T-1675] wave が「登録は構造的に不可能」と書いた閂は、この時点では解けていた。**
  同 wave は F57 への再発記録が canonical へ fold されるまで登録できないと述べ裁定へ送っていたが、
  その再発はすでに fold 済みで、検証器が要求する 3 述語 (F 節の実在、test 関数名の逐語一致、
  `failure_signature` の逐語一致) を実データで検算するとすべて通った。**閂の前提は必要条件であって、
  解除後も塞がったままとは限らない。**
- **工数。** 段 2・3 は軽量版として省略 (docs-only)。段 6 のレビュー子 1 本のみ、
  一次資料の全文を job dir へ渡して逐語と語の件数を子が独立に数え直せる形にした。
  Web を使えない子でも外部文献のレビューが成立する。
- **段 8 の候補 2 件はどちらも不採用にした。理由は予算の実測である。**
  (a) 「外部一次資料の走では全文も job dir へ置く」を `DW-O02` へ足そうとしたが、
  L1.5 の unique footprint は **9,566 / 9,566 bytes でちょうど満杯**であり、124 bytes 超過で
  `check_docs` が赤になった。他節を削って捻出することはしない (安全義務の弱化を招く)。
  (b) 「worktree 隔離 session では複合 shell が harness に拒否されるので job dir への出力は
  絶対 path で書く」は `DW-O20` が対応節だが、同節は **998 / 1,000 bytes** で余地が無い。
  どちらも事故ではなく手順の明確化なので、予算値を上げる審査へは送らず記録に留める。

## 次の一手差分

### 完了

- [T-1879] 一次資料を読み、判定 `部分接地` / `方法論的祖先` を確定して採録・記録した。
  remaining: none
  base: aa36c6cd3b09ba86d53b601d18868ab71dbe4b37c792ec2d6004a6420f991621

### 新規

- {{T:pilot-remaining-adjudications}} **P3・新規**: 軸 1 分類 pilot に残る `要裁定` 2 件
  (`2512.18746` MemEvolve / `2605.22721` DecentMem) の包含条件 B を一次資料で確定する。
  どちらも「メモリ構造の進化」が設計空間の生成に当たるかを 1 行要約では決められずに残った。
  残る 1 件 `2404.13359` は [T-1880] が持つ。
