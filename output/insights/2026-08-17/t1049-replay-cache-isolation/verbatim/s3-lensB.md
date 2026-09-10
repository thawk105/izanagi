## 「実装しない」への攻撃

- **real:** (519) と (535) は同じ producer/consumer の同一事象であり、独立 2 例ではない。`docs/archive/worklog-phase3-0813-519.md:64-72`、`docs/archive/worklog-phase3-0813-535-536.md:34-40`。542 も同じ再発記録である。
- **real:** 独立例として F306 がある。`test_signal_after_receipt_publish_does_not_reverse_success` が worker の signal mask を汚染し、後続の別 test が赤になった。赤 node が族内で移動した事実もある (`docs/failures.md:7790-7802`)。後に真因が worker state 汚染へ訂正されている (`docs/failures.md:7833-7835`, `docs/archive/worklog-phase3-0816-607.md:3-15`)。
- **refuted:** F306 は `_OPERATION_REPLAY_CACHE` や `operation_id` 衝突の直接反証ではない。現 HEAD の formal cache の lookup/write は `orchestrator/campaign/reflux_formal_consumer.py:1045-1067`、production の間接呼出しは `orchestrator/campaign/reflux_origin_client.py:252-257` に限られる。従って P0 の「現行 formal cache の衝突は静的には見つからない」は未反証である。

結論として、DW-G03 は「process-local test state 汚染」という広い族には適用できるが、formal replay cache 専用の共通 fixture を正当化する根拠には足りない。

## 「実装する」への攻撃

- **real:** 共通 autouse fixture は全 test node に乗る。静的な test function 定義は 8,430 件、test file は 212 件で、plan の 8,421 件は 9 件少ない。既存の autouse は `orchestrator/tests/conftest.py:148-165`、`:279-292`、`:295-305` にある。追加 fixture は import lookup、setup、yield、teardown、dict clear を各 node に課す。
- **未確定:** これは O(1) per test で履歴比例ではないため、D311 (`docs/decisions.md:14266-14278`) の直接違反とはまだ言えない。しかし +10% 閾値の実測なしに「最小」とは言えない。
- **real:** cache clear は旧不具合を隠す。旧定数へ戻しても、test A の書込み後に test B の開始前 clear が入れば、順序依存の REPLAY red は発火しない。
- **real:** `_ISSUED_RECEIPTS` まで消す必要はない。現在の seal key は新規 object identity であり、`orchestrator/campaign/reflux_formal_consumer.py:219,237,393,922` にある。将来の module/session fixture が発行した receipt を function fixture が壊す危険もある。
- **refuted:** `pin` は suite 全体のコストを増やさないため、autouse fixture よりは小さい。ただし helper の実装形を固定するだけで、現行成果物を変えない防御的 nit に留まる。closed-set AST guard は今回の静的監査を suite へ複製する過剰案である。

## 成果物影響の検算

- brief 第 1 行は「pytest の受入判定が変わる」という意味では real である。ただし、衝突が起きると `_complete_origin_runtime` が report 構築前に走る (`orchestrator/campaign/p3_autonomous_workload_trial.py:2286-2296`)。例外時は lifecycle が indeterminate になり (`:3210-3221`)、`run_origin_trial` は report 無しの partial を返し得る (`:3272-3287`)。
- それでも現 scope では一時 test root の report/lifecycle が壊れるのであり、certified 選択や実運用の report、台帳の値が変わることまでは示していない。brief は DW-G05 の成果物影響としては不十分である。
- 第 2 行も将来の CI red 復活という保守リスクであり、production 成果物影響ではない。

正しい 1 行は次である。

> 現行 scope で変わるのは主に pytest の受入判定であり、certified 選択・実運用の report・台帳は不変。実際に衝突した test では一時 run root の report 欠落と lifecycle の indeterminate 化が起き得る。

## 記録の整合

docs-only で閉じる場合も、`docs/spool/README.md:3-5,84-86` に従い canonical 台帳を直接編集せず、`docs/spool/worklog/` に fragment を置く。

`worklog` fragment は次を満たす必要がある。

- frontmatter、`## 本文`、`## 次の一手差分` の順 (`docs/spool/worklog/README.md:5-33`)。
- 本文に、静的所見と「pytest はこの子が実走していない」ことを明記する。
- 親が実測した最終受入については、tested tip、実行 command、request、passed/failed/skipped、実行時間を実値で書く。hand-off の件数だけでは最終受入証明として不足する。
- 完了項目には `remaining: none` と、carry stub ではなく実体 item に対する `base:` を付ける (`docs/spool/worklog/README.md:64-86`)。
- 親の受入が未実施なら `完了` ではなく `更新` にする。

書いてはいけない文言は、「このレビューで 403 passed」「受入は緑」「汚染は存在しない」「P0 を実測で証明した」である。子は pytest を実走しておらず、これらは未実測または過剰断定になる。

## 未確定として残すもの

- `tmp_path` の一意性が、全 xdist・basetemp・再入実行条件で保証されるか。
- F306 を formal replay cache と同じ族に数えるか。広い state 汚染族では real、formal cache 族では未確定。
- autouse fixture の実時間増分が D311 の +10% 閾値を超えるか。
- pin を nit/backlog とするか、ユーザーが deterministic regression guard として採用するか。
- 動的 alias や将来の新 producer が静的 call-site 検索の外に出ないか。

## 総括

P0 の formal cache 衝突は現 HEAD では静的に反証されない。一方、共通 autouse fixture は全 suite へ費用を広げ、今回の再発そのものを隠すため不採用が妥当である。F306 は広い process-local state 汚染の独立例として記録し、必要なら pin だけを nit として裁定へ返すべきである。