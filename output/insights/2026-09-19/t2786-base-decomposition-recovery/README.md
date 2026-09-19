# T-2786 — t080 共有 base の実体化・発行・待ちを分ける replica 観測 (回収 wave、3 ブロック完走)

authority: none / default_effect: no-state-change。可変状態の正本は worklog 末尾と現行 phase doc。

## 1. 依頼・不変条件・結論

D2148 項 6 と `output/insights/2026-09-18/t2710-b5-wall-decomposition/README.md` §9 に従い、t080 e2e の共有 base 構築が
48 worker 下で伸びる内訳 (実体化 / 発行 / 待ち) と、構築の並行度 (L) ・順序 (P) の効果を replica で測った。
production の受理集合・保留・成分粒度・test の独立 copy/deepcopy は維持し、D2068 の却下 3 案と圧縮設定変更は扱っていない。
測定 source は着手直前の local main `7975385b55a2e3451f6c80d584a9312f44d5199d` の fresh 専用木 (全走で clean を確認)。
本 wave は前 wave が block1 完走後に中断した測定の回収である。block1 の 3 走却下を原本で判別して計器欠陥 2 件と確定し、
隔離 Codex author で修正したうえで、事前登録の置換 1 ブロック (block1 → block4) と残り 2 ブロックを実施した。

結論 (事前登録の判定式で確定、同 job 内の対比較 3 対):

| 条件 | Wtotal 中央値 (3 走) | 対差 A − 条件 (block2 / block3 / block4) | 判定 |
|---|---|---|---|
| A 通常の要求時構築 | 395.7 秒 (387.9 / 395.7 / 399.4) | — | 基準 |
| L 実 session builder を同時 1 本 | 709.4 秒 (682.7 / 709.4 / 728.0) | −287.0 / −321.6 / −328.6 秒 (3/3 とも A より遅い) | 観測差、改善ではない |
| P gw0〜4 が collection 送信前に各 1 key を先行構築 | 405.4 秒 (388.4 / 405.4 / 422.2) | −9.7 / −0.6 / −22.8 秒 (3/3 とも 10% 未満) | 変化なし (D357) |

- 「改善」の語を許す条件 (有効同 job 3 対・対差 3/3 正・中央値差正・条件起因失敗/未分離外乱なし) を満たす条件は無い。
  L は 3/3 で悪化、P は 3/3 で変化なし。採用改善値・300 秒到達・production 効果は置かない。
- 内訳 (§4): 発行 subprocess は条件・並行度によらず約 65 秒で一定、直下 git も約 11 秒で一定。伸びるのは copy 配置 (実体化) で、
  session 開始直後の他 worker の test と同時に走る build では 89〜112 秒、それ以外 (P の collection 中の先行構築、L の 2 本目以降) では
  28〜35 秒。5 本同時の copy 自体は P で 30〜35 秒に収まるので、伸びの主因は copy 同士の競合ではなく、同時に走る他 unit との干渉と
  読める (観測の記述であり、因果配分は §6 の限界に従う)。

## 2. block1 の却下判別 — 2 件とも計器 (probe) の欠陥

block1 (request 9492.nqsv、ALP) は A rc0 / Wtotal 368.6 秒、L rc0 / 668.8 秒、P rc3 / 159.2 秒で、analyzer は 3 走とも valid=False。

### 2.1 A/L の「group split across workers」= analyzer の思い込み

- analyzer は production report の `group_to_workers` の全群が 1 worker であることを要求していた。
- production report の `group_to_workers` は collection record の xdist_group **marker 単位** (`tools/acceptance_shards.py`)。
  本番 conftest の `_strip_real_repo_loadgroup_suffix` (`5ac638955`、2026-08-26) は process-memo 以外の real-repo item から
  runtime 接尾辞 `@real-repo` を外し、他 worker へ分散させる (docstring「split real-repo runtime work units」)。
- 01-A 原本: real-repo marker 173 件のうち runtime `@real-repo` を持つのは 55 件 (全部 gw0)、118 件は 42 worker へ分散。
  production 側の report 検証 (`report-evidence-group-workers`) は worker 集合の構造だけを見て 1 群 1 worker を要求しない。
- runtime 接尾辞単位では A/L とも 4 群 (real-repo/gw0、campaign-repository-scan/gw1、s8c-preregistration-candidate/gw2、
  s8c-predicate-snapshot/gw3) が各 1 worker で、loadgroup の不変条件は成立していた。
- group 検査だけ外した analyzer 写し (job tmp、probe 不変) で A/L は他の全検査 (5 key の実 build 各 1 回、M node の
  call/helper/get/base_copy 観測、L の builder 同時数 1 と slot 待ち 5、JUnit/selected 一致) を通った。
- probe test は合成 `group_to_workers={'g': ['gw0']}` だけで緑にしており、本番の形を一度も通していなかった。

### 2.2 P の rc3 = plugin の remote hookimpl 同定が実 worker で必ず失敗

- `check_prepare_order` は `from xdist.remote import WorkerInteractor` の class に対する `isinstance` で remote の
  `pytest_collection_finish` 実装を探していた。
- xdist の worker は `xdist/workermanage.py` の `gateway.remote_exec(remote_module)` で `xdist/remote.py` の source を
  execnet が `exec(compile(source, file_name, 'exec'), {'__name__': '__channelexec__', ...})` で実行して作る。
  登録される interactor はその名前空間の class の instance で、import した class object とは別物 → `isinstance` は常に False。
- 03-P 原本: 48 worker 全部が collection イベントの 0.01 秒後に sessionfinish exitstatus 4 (UsageError)、`prepare-wiring`
  イベント 0 件、controller は「Unexpectedly no active workers available」で rc 3。source 文字列 2 条件
  (`"collectionfinish"`、`assert self.collection_is_completed`) は同じ xdist 3.8.0 で成立していた。test は 0 本だった。

### 2.3 判別の帰結

いずれも外乱・条件依存の失敗ではない。ユーザー指示 (欠陥なら隔離 Codex author D95 で修正して block1 を再走) に従い、
事前登録の「置換は wave 全体で 1 ブロック」を block1 → block4 (ALP) に使った。block1 の A/L は個別観測として保持し、
完全有効ブロックの比較母集団へ混ぜていない (pilot 除外もしていない)。

## 3. 計器の修正と検証

- fix2 (隔離 Codex author、fix1 木 `b36ee2731` → `2277c8236`、差分は `t2786_probe/` 4 file、親ハンク 0):
  - F-1: marker 単位の拒否を撤去。controller reports から runtime 接尾辞作業単位ごとの実行 worker 集合を作り、
    集合一致 (`runtime loadgroup unit set mismatch`) と各 1 worker (`runtime loadgroup unit split across workers`) を独立理由で
    検査。production `group_to_workers` は群別 worker 数を row (`production_group_worker_counts`) に記録するだけで、
    signature・中央値・成分集計へ入れない (11 走で real-repo は 42 または 43 worker、他 3 群は 1)。
  - F-2: 登録 hook の関数 code object を imported `WorkerInteractor.pytest_collection_finish.__code__` と比較して同定。
    ちょうど 1 件・tryfirst/hookwrapper/wrapper でない・schedule/`"collectionfinish"` の source 検査は維持。
  - 新 test 8 本 (合計 20): 多 worker marker + 1 worker runtime 単位の受理、runtime 単位分割の拒否、集合の欠落/追加の拒否、
    worker 割当て変更で signature 不変、xdist.remote の source を別 `__name__` で compile/exec した別 class を
    `PytestPluginManager` へ登録して受理 (`isinstance` は False であることも assert)、未登録/重複/tryfirst の拒否。
  - 変異 M5 (runtime 分割検査を落とす)、M6 (`isinstance` へ戻す)、M7 (marker 拒否を再導入) を追加。M1〜M4 は維持。
- 段 6 レビュー (逐語は job dir `artifacts/dev-wave-t2786-base-decomposition/review2-a.md` / `review2-b.md`):
  A (過剰・削除レンズ) は fix2 実装に must 0、親裁定の P smoke 案に must 1 (事前登録外の 13 走目、`_one` 直呼びは
  1200 秒制限と process group 回収を通らない) → real・採用し smoke を撤回、置換 block4 を配線確認兼用にした。
  B (実機配線レンズ) GO、must 0。
- 実データ照合 (job tmp、probe 不変): fix2 の `selection_signature` は block1 01-A/02-L 原本を受理し、`@real-repo` の 1 report
  を gw5 へ動かした負例は `runtime loadgroup unit split across workers` で拒否。
- probe test 20 本: 計算ノード (10725.nqsv、Elapse 18 秒) で 20 passed (12.19 秒)。
- 変異 (10748.nqsv、Elapse 130 秒、`mutation-results3.json`): baseline PASSED、M1〜M6 は期待 node と完全一致で KILLED。
  M7 は KILLED だが失敗 node が期待 1 に対し 4 (再導入した marker 拒否が同じ多 worker fixture 族の負例 3 本より先に発火) で
  DW-M08 の完全一致則では MISMATCH。初回結果は erratum として保持し、期待集合を 4 node の完全形に再登録して再走した
  (`mutations-final3.json`、11218.nqsv、Elapse 128 秒、`mutation-results4.json`): baseline PASSED、M1〜M7 の 7 件すべてが
  期待 node 集合と完全一致で KILLED。M2/M4 は計器の診断感度であり production gate kill ではない。

## 4. 11 走の内訳 (block1 の A/L は個別観測、block2/3/4 が比較母集団)

Wtotal は各走の準備前から run_tests.py 終了まで、Wpytest は JUnit testsuite time。成分は排他化した区間の時間 (worker 秒、
wall ではない)。key は (trailer, history_mutated, issued, extra) の 4 要素で、発行 key 4 つと非発行 key 1 つ。
「最終 base 完成」は最初の build 開始からの経過秒。

| 走 | 条件 | Wtotal | Wpytest | 発行 key の copy (4 key) | 非発行 key の copy | git 中央値 | issue 中央値 | 最終 base 完成 | slot 待ち合計 |
|---|---|---|---|---|---|---|---|---|---|
| block1-01 | A | 368.6 | 362.5 | 89.0 ×4 | 89.0 | 11.4 | 65.4 | 165.9 | 0 |
| block1-02 | L | 668.8 | 662.6 | 80.1 / 30.9 / 28.6 / 28.3 | 28.0 | 10.8 | 65.2 | 512.3 | 1129.3 |
| block4-01 | A | 399.4 | 392.1 | 92.9 ×4 | 92.9 | 11.3 | 65.3 | 170.1 | 0 |
| block4-02 | L | 728.0 | 721.9 | 94.7 / 32.2 / 32.1 / 29.6 | 29.3 | 10.9 | 65.1 | 533.5 | 1259.8 |
| block4-03 | P | 422.2 | 416.1 | 34.5 / 34.1 / 33.1 / 31.9 | 34.6 | 11.0 | 65.2 | 112.1 | 0 |
| block2-01 | L | 682.7 | 675.9 | 90.1 / 31.2 / 30.9 / 28.5 | 30.3 | 10.8 | 65.0 | 525.4 | 1174.5 |
| block2-02 | P | 405.4 | 399.2 | 33.9 / 31.2 / 30.6 / 30.4 | 31.1 | 11.0 | 65.2 | 112.9 | 0 |
| block2-03 | A | 395.7 | 386.4 | 111.9 ×4 | 111.9 | 11.4 | 65.4 | 189.1 | 0 |
| block3-01 | P | 388.4 | 382.0 | 34.4 / 33.5 / 33.3 / 33.1 | 34.1 | 10.9 | 65.1 | 113.6 | 0 |
| block3-02 | A | 387.9 | 378.2 | 103.5 ×4 | 103.5 | 11.6 | 65.4 | 180.7 | 0 |
| block3-03 | L | 709.4 | 703.1 | 95.9 / 29.8 / 29.7 / 28.6 | 51.4 | 10.9 | 65.1 | 550.9 | 1321.6 |

- 発行 subprocess (issue: 発行子の起動/import/発行/検証/終了) は 11 走・44 key で 65.0〜65.9 秒。並行度・順序に依存しない。
- 直下 git は 10.8〜12.0 秒で一定。history 確認・runtime 配置は 0.1 秒未満。
- copy 配置は二峰: session 開始直後の他 test と同時に走る build (A の 5 本、L の先頭 1 本) は 80〜112 秒、
  それ以外 (P の collection 中の先行構築 5 本、L の 2 本目以降) は 28〜35 秒。P の 5 本同時 copy が 30〜35 秒で収まるので、
  copy 同士の同時実行そのものは主因でない。L の先頭 1 本が単独 builder でも 80〜96 秒なのは同じ時間帯の他 test との干渉と読める。
- L は最終 base 完成が 512〜551 秒 (A の約 3 倍) で、M node の slot 待ち合計が 1129〜1322 worker 秒。Wtotal が A より 287〜329 秒
  遅いのはこの直列化で説明できる。
- P は最終 base 完成が 112〜114 秒 (collection 中) で A より約 60〜75 秒早いが、gw0〜4 の先行構築 (prepare 合計 473〜484 worker 秒、
  wall 約 112 秒) が終わるまで 48 worker 全部の collection が完了せず test 開始が遅れるため、Wtotal は A と 0.6〜23 秒差に留まる。
  P の key 集計は prepare phase (5 key) と通常 test phase を分けて保存している (`key_totals_by_phase`)。
- block1 の 03-P は §2.2 の計器欠陥で test 0 件のまま終了 (Wtotal 159.2 秒は collection と失敗までの時間で、条件の観測ではない)。

## 5. 実行条件と外乱

- 計算ノード gen_S、48 core affinity、各 block は 1 job で 3 走を逐次 (ALP / LPA / PAL)。block1 = bnode109、
  block4 = bnode111、block2 = bnode117、block3 = bnode080。各走とも fresh session・fresh base、
  `PYTHONDONTWRITEBYTECODE=1`、production の 3 shard 配分の shard0 (selected = finished = 4011、48 worker digest 一致)。
- 各 block の開始時 node loadavg (1 分平均) は 0.2〜1.1、他 user の活動 process (CPU 5% 超) は 0。同 node の単独性は成立。
  job の Elapse は block1 1218 秒、block4 1594 秒、block2 1541 秒、block3 1553 秒。
- 同 uid の別 wave job (fp-rr*、izdw-*、b10_back、paper-b7 等) が同時に走っていた (`activity-before/after.json` の qstat)。別 node の
  共有 FS 負荷は分離していない。§1 の判定は改善を主張しない方向なのでこの未分離は結論を変えない。
- 置換は block1 → block4 の 1 回だけ (合計 4 job / 12 走、上限内)。失敗側だけを別 job で補っていない。

## 6. 限界

- replica のみ。全受入や CC 性能ではない。P は順序・builder 割当て・collection 重複が変わる複合条件で、純粋な順序効果ではない。
- bytecode 初期条件だけ統一。OS/Lustre cache の同一性は未保証。別 wave の同時 job による共有 FS 外乱は未分離。
- issue は発行子の起動/import/発行/検証/終了込み。build − issue を丸ごと実体化と呼ばない。
- copy 配置の伸びを「他 test との干渉」と読むのは観測からの解釈で、旧 tip の単独 98 秒に対する因果配分はしない (事前登録どおり)。
- main は 7975385b5 から 41 commit 先へ進み、T-2724 で `test_s8b_oracle_driver.py` の shared-base key が 5 要素になった。
  本資料の値は 7975385b5 の命題であり、現行 main へ probe をそのまま当てることはできない (規律 7: 事実と現行適合は別)。
- 計器の validity 述語を本番契約と照合せず合成 fixture だけで緑にしたため、実機 1 走で 2 欠陥が出た。前 wave の
  レビュー 2 本 + 焦点再レビューも見逃した (F649 型の再発)。

## 7. 次の諮り直し用パッケージ (提案。採用済み判断ではない)

- 採用候補なし: L は悪化、P は変化なし。builder の並行度制限と先行構築は t080 共有準備の短縮手段にならない。
- 残る短縮余地は copy 配置の 80〜112 秒 → 28〜35 秒の差 (5 key で最大 5 × 約 70 worker 秒) と、その先の M node の
  base 依存 chain (A で最終 base 完成後さらに約 200〜230 秒)。前者は同時に走る他 unit との干渉を避ける配置 (受入順序で
  重い I/O unit を base build と重ねない等) の話で、D2068 の却下 3 案には触れない。後者は base 構築でなく test 本体の問題。
  いずれも本資料は観測までで、設計・実装の起票は別裁定。
- 現行 main (key 5 要素) で再測定するなら probe の KEYS と成分名を作り直す必要がある。

## 8. 再計算方法・成果物対応

- job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2786-base-decomposition/`: `runs/block1` (原本、P 却下)、
  `runs/block4|block2|block3` (各 3 走の run.json / controller.json / spans-*.jsonl / acceptance-session / activity / env)、
  `analysis-block3.json` (12 走の最終解析、`analysis-block4.json` / `analysis-block2.json` は途中版)、
  `probe/` (fix2 版、`probe-block1-b36ee2731/` は block1 時点の版)、`probe-author.bundle`、
  `recovery-brief.md` / `recovery-adjudication.md` / `fix2-findings.md` / `adjudication.md` (事前登録)、
  レビュー・author 逐語 `artifacts/dev-wave-t2786-base-decomposition/`、変異 `mutation-results3.json` / `mutation-results4.json`。
- 再解析: `python3.10 probe/t2786_probe_analyze.py --out-root runs --output <out>` (rc 1 は block1-03-P の無効を含むため)。
- 本 README の表は `analysis-block3.json` の `runs[*].key_totals` / `builder_timeline` / `Wtotal` / `Wpytest` と
  `condition_medians` / `within_job_pairs` から転記した。
