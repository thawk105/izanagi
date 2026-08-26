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
- **DW-O18 に従い hold へ登録したが、並行セッションの指摘で撤回した。**
  受入 2 走目までは、F57 を証拠に Codex `role=author` が
  `orchestrator/tests/flaky_test_holds.py` へ 1 行足す形で進めた。
  **撤回した理由は 2 つあり、どちらも独立に成立する。**
  (a) 別 wave (`worktree-dev-wave-t1848-env-coincidence`) が同じ node を hold ではなく
  **是正**していた — 2 秒の絶対期限を除去して launcher 終了後の判定へ移す形で、外側の
  10 秒 watchdog は温存されている。一方 `orchestrator/tests/conftest.py` は hold 対象へ
  `pytest.mark.skip(..., append=False)` を**無条件**に付ける (現物で確認した)。
  両方が着地すると、**決定的に緑になったテストが受入でも焦点走でもどこでも走らなくなる。**
  (b) `worktree-dev-wave-flaky-holds-20260826` は同台帳を**全撤去**する内容で、追加行は
  そちらとも競合する。
  **教訓は「hold は落ちても許すではなく、走らせないである」。** 是正が進行中の node を hold すると、
  検出力が静かに消える。DW-O18 の本文には「同じ node を触っている稼働 branch があるか」を
  確かめる手順が無い。撤回後、本 wave の実装面の差分はゼロに戻った。
- **受入は当初 5 走を要し、非帰属赤は 2 種類・のべ 3 件だった。** 1・2 走目は上記の `sigterm`。
  3 走目は hold が効いて `sigterm` が collection から外れ (skipped が 64 から 65 へ)、
  代わりに**別の node** `test_campaign_claim.py::test_two_real_processes_racing_acquire_have_exactly_one_winner`
  が落ちた (`assert None == 2255171`、単独走は 1 passed / 3.64 秒)。
  この node は失敗台帳に F 証拠が無いので DW-O18 に従い登録しなかった。4・5 走目は緑。
  **落ちる node が毎走変わるのは F57 が記録している型そのものである。**
  この機体の負荷下では受入 1 走あたり 1 件程度の負荷依存フレークを見込む必要がある。
- **land は 1 回目に `status=fold-failed` で戻り、main は 1 bit も動かなかった。**
  worklog の rotation で entry 1001 を archive へ送る計画だったが、`tools/check_docs.py` の
  `_archive_filename_entry_range` が `1001` を MMDD (10 月 01 日) と読み、
  `docs/archive/worklog-phase3-0826-1001.md` を「番号なし archive」に分類した。
  `(1001)` を指す carry stub 821 本が全域番号 universe から外れて宙吊りになる。
  **`spool_fold.py --dry-run` はこの赤を出さない** — 計画 JSON だけで生成後の canonical 検査を
  走らせないためで、land 結果 JSON 自身が `fold_gate_uncovered_families: ["rotation"]` と報告する。
  診断は `output/insights/2026-08-26_worklog-rotation-entry-1001-mmdd-collision.md`。
- **この欠陥は少なくとも 6 セッションが独立に診断し、修正は 1 本が所有した。**
  親は稼働中の全 branch tip を走査して `tools/check_docs.py` に差分を持つのが
  `worktree-dev-wave-t1732-condition18-two-points` 1 本だけであることを確認し、**重複実装しなかった。**
  同 branch の修正は `dcf7c615` (`D1054` = D445 の改訂) として main へ着地し、
  その land 自身が entry 1001 の rotation を通した。本 wave はその後 main を取り込んで再受入した。
- **診断で 2 点、他セッションの指摘を受けて訂正した。** (a) 衝突域は 1101〜1130 ではなく
  **1101〜1131** — `ARCHIVE_MMDD_TOKEN_RE` は月ごとの日数を検証しないので 11 月 31 日も通る。
  900〜1299 の全件実測は `[(1001,1031), (1101,1131), (1201,1231)]` の 93 件。
  (b) **この欠陥は 2 token 形の単一 entry rotation でしか出ない** — 複数 entry をまとめた名前は
  3 token になり修正前でも正しく numbered になる (`worklog-phase3-0826-1000-1001.md` で実測)。
  **したがって回帰検知の負例は単一 entry 名でなければ、欠陥が残ったまま緑になる。**
- **[T-1675] wave が「hold 登録は構造的に不可能」と書いた閂は、この時点では解けていた。**
  同 wave は F57 への再発記録が canonical へ fold されるまで登録できないと述べ裁定へ送っていたが、
  その再発はすでに fold 済みで、検証器が要求する 3 述語 (F 節の実在、test 関数名の逐語一致、
  `failure_signature` の逐語一致) を実データで検算するとすべて通った。**閂の前提は必要条件であって、
  解除後も塞がったままとは限らない。** ただし本件は上記のとおり、通ったうえで撤回が正解だった。
- **取り込み commit の message にずれがある (訂正)。** `受入のため local main 4c88c3d0 を
  取り込む` と書いた merge commit の第 2 親は実際には `869712c8` である。
  main の位置を確認してから `git merge` を打つまでの間に、並行 wave の land で main が進んだ。
  merge commit は amend しない (reflog を壊すと段 9 の自己撤去が拒否される) ので、ここで訂正する。
  **並行 land が多い時間帯は、確認した SHA を message へ焼くと必ずずれる。**
  message には確認時刻の SHA でなく「取り込み時点の main」と書くほうが安全である。
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
