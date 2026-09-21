高 3 件、中 3 件です。最大の欠陥は、**P3 が約束する各 item の開始時刻を、指定された通常受入の成果物からは正確に復元できないこと**です。以下は静的検査の結果で、pytest は実行していません。

## 所見

1. **主張:** P3 の観測可能性が過大で、ΔL を対の判定へ反映する規則も不足している。
   **根拠:** 入力 session の `shard-0/report.json` にある `session_timeline.workers.<worker>` は `first_test_started_epoch_s`、`last_test_finished_epoch_s`、`real_repo_lock_intervals` のみ。`worker_occupancy` は所要和と件数で、item 別開始時刻ではない。JUnit の property は `scope/rank/partner/worker`、testcase は `time` を持つ。例えば delegation は gw33、rank 456、189.183 秒まで確認できるが、その開始 epoch はない。T-2817 §3.2 の詳細 timeline は計装した Job B の成果である。
   **親の記述との差:** P3 の「開始 t を観測」は成立しない。worker の初回開始に先行 item の所要を累積しても、item 間の空白を観測できず推定になる。また、単に ΔL を記録するだけでは依頼の「対の判定に含める」が未定義。
   **重大度:** **高**。このまま全走しても、約束した計時情報は得られない。
   **修正案:** 開始 t は「未観測」、累積所要による値を出すなら「推定」と明示する。各対に L とその nodeid、ΔL、ΔO_max、Δ(O_max−L) を必須化し、「差が縮んでも L 増大なら、それだけで短縮とは判定しない」と事前登録する。copy 競合・builder/waiter の因果断定はしない。

2. **主張:** 「collection が main と一致する最新緑走」の確認方法が不足している。
   **根拠:** `tools/update_acceptance_duration_ledger.py:294` は collection を集合化し、`:332` は台帳との被覆率を表示するだけ。`:559` 付近の coverage 処理にも collection 同一性の判定はない。T-2236「残存限界」は hold marker 行の誤読も記録している。入力 request の `runner_binding.tested_main` は `5efd69367…` で、投入 tree 全体の同一性を表す field ではない。
   **親の記述との差:** brief「前提の実測」の限定 path の diff と `--coverage-against` では、入力 JUnit と現 main の collection 一致を証明できない。「最新」の選択時点・候補比較も示されていない。
   **重大度:** **高**。D2107 の入力条件を確定しないまま測ると、測った B 自体が再生成対象になる。
   **修正案:** 測定前に、固定した main の正規化 collection と入力 3 shard の canonical nodeid 多重集合を照合し、重複・欠落・余分をゼロ確認する。hold marker は分離し、group/hold 情報も照合する。選択締切と最新適格走の根拠を残して入力 JUnit を hash 固定し、性能値による選び直しを禁止する。

   入力候補自身については、3 shard の `pytest_rc=0`、failures/errors=0、`observed_universe` 一致、`selected` の重複なし・和集合 26,808 件を確認した。**候補が不適格と判明したのではなく、main との一致と最新性が未証明**である。

3. **主張:** 有効走・無効対・系列停止の契約を「T-2766 形」の参照だけに任せている。
   **根拠:** `verbatim/T2766-prereg.md`「有効走／有効対／赤」と T-2802 README §5.1 は、無効対全体の取り直し、有効 3 対固定終了、12 走上限、赤の分類を明記する。T-2802 は成果物 hash、投入時門番、skipped 集合の一致、`impl/unclassified` による系列無効も定義している。
   **親の記述との差:** P2 は判定式、P4 は投入経路を記すが、それらの実施条件がない。旧 T-2766 の「B のみ witness」や「効果にかかわらず land しない」は今回へそのまま移せない。
   **重大度:** **高**。無効走の扱いを結果後に決めると、対の選別と停止条件が結論を左右する。
   **修正案:** 今回用の有効性規則を列挙し、launcher・系列・集計器の責任を固定する。赤は本文で infra/impl/unclassified に分類し、後二者は系列を停止・無効化する。有効 3 対で終了、12 走未満でも不足なら判定不能とし、測定完了と性能改善の判定を分ける。

4. **主張:** shard 構成の変化を認識しているが、不変条件と帰属の書き方が追いついていない。
   **根拠:** `tools/acceptance_shards.py:381` の `allocate` は台帳値を成分重みに使い、`:404` では未登録を 1.0 秒にする。一方、`orchestrator/tests/conftest.py:1859` の未登録 cost は既知 unit の最大 96 番目。refresh は割付・順序・未知 cost の基準を同時に変える。
   **親の記述との差:** 「受理集合（selected …）は不変」は shard 別 `selected` まで不変と読める。P2 の W_max 併記だけでは、shard-0 の構成差を説明できない。
   **重大度:** **中**。
   **修正案:** 不変なのは全 shard の受理多重集合と group/unit 境界、と限定する。条件別に shard ごとの selected hash・件数・移出入 node を保存し、W_0 と全 W_j/W_max を対表に載せる。結果は「refresh 全体の効果」とし、順序だけへの寄与分解はしない。

   W_0 を依頼に沿う主指標として残すことは妥当。ただし、W_0 の改善だけで「受入全体が短縮」とは書かない。W_max へ主指標を置換する必然性はない。

5. **主張:** warm の成果物名はあるが、両 tree の bytecode 条件を揃える手順が未登録。
   **根拠:** D2177、T-2802 §5.1 は両 tree の計算ノード collect-only と証跡を要求する。T-2766 §4、T-2802 §5.1 とも page cache・fixture の warm は保証していない。
   **親の記述との差:** brief「成果物」の `warm` だけでは、片側だけ既存 pyc がある状態や env 差を排除できない。
   **重大度:** **中**。
   **修正案:** 系列開始前に両 tree の collect-only を同じ bytecode 設定で実行し、job ID・env・HEAD/clean・pyc 状態を記録する。page cache の対称性は未保証とする。門番は依頼どおり leaders ≤1・load1 ≤60 を維持し、先例の <30 との差と投入直前値を残す。

6. **主張:** land 時再生成と、測定した B の同一性確認が欠けている。
   **根拠:** D2107 と `tools/update_acceptance_duration_ledger.py:459` の `_refresh_result`。出力は「base の凍結部分＋固定 JUnit の非凍結部分」で決まる。
   **親の記述との差:** brief「確定済み裁定」は main 現物で再走・落ちた node 記録までで、測定 B と land bytes の照合を要求していない。
   **重大度:** **中**。
   **修正案:** 再生成後に測定 B と全 bytes/hash を照合する。通常の非凍結 add-only だけなら同じ出力になり、追加分が必ず測定差になるわけではない。異なる場合は差分を記録し、旧 B の測定を land 現物の性能証拠として転用しない。

## (P1)〜(P5) の判定

- **P1 — 維持。ただし理由を限定。** conftest `:1005/:1707` と割付器の path は固定で、通常の env 切替はない。固定 2 tree は clean 条件下で依頼の意図に最も近い。ただし、`run_tests.py:784` は未 stage **削除**検査であり、台帳の一時変更を一律拒否する clean 検査ではない。`:2201` の指紋も OOM fallback 前後の照合である。「runner が拒否するから同一 SHA は不可能」とは書かない。
- **P2 — 修正。** W_0 主指標と保守的 10% 判定は維持。全体短縮の主張には W_max を併記し、構成差と ΔL を含む読み方を固定する。
- **P3 — 修正。** worker・rank・所要・L は取得可能。各 item の正確な開始 t は取得不可で、推定との区別が必要。
- **P4 — 維持。** 直接投入と land 用最終受入の分離は D2177 と整合する。所見 3・5 の系列制御を明記する。
- **P5 — 維持。** 台帳データの再生成だけなら変異 matrix 適用外は妥当。検索上、列挙した consumer と既存 test の閉包に追加の漏れは見つからない。測定 probe の自己検算まで省略する理由にはならない。

## 事前登録の修正版 (差分だけ)

- **追加:** 入力選択締切、最新適格走の根拠、3 JUnit の hash、main collection との完全照合。被覆率検査は別検査とする。
- **追加:** 入力 8 node の生 time と量子化値を固定する。今回の 189〜192 秒群と 38〜48 秒群が順位を規定する点を限界として記録し、builder/waiter の役割は所要だけで断定しない。
- **置換:** 「selected 不変」→「全 shard の受理多重集合不変。shard 別 selected は変化しうる」。
- **追加:** A/B の selected 差、全 W_j、W_max/argmax、shard-0 の O_max・L・O_max−L、最大占有 worker の item 列を必須出力にする。
- **置換:** 「各 node の開始 t を観測」→「開始 t は原則未観測。累積所要からの再構成は推定」。L の最大 nodeid 交代を記録し、固定した旧 L 候補の所要も併記する。
- **追加:** ΔL>0 と O_max−L 減少が同時に起きた場合は「L 増大を伴う差の縮小」と記述する。改善の判断を O_max−L 単独で行わず、W_0/W_max の正味差から行う。
- **追加:** 両 tree の collect-only warm、bytecode env、前後 HEAD/clean、投入直前の門番証跡。page cache の同等性は主張しない。
- **具体化:** rc、全 shard 完走、成果物整合、全体 collection と skipped 集合、HEAD/clean、門番を有効性条件にする。無効対は同順序で全体を取り直し、有効 3 対固定終了・12 走上限。赤と未投入 abort の記録・上限への数え方を明記する。
- **削除・置換:** T-2766 の旧 env 切替・B 限定 witness・一律非 land 方針は継承しない。現行 pairing は両条件で同じ検算を行う。
- **追加:** land 再生成 bytes と測定 B の照合。不一致時の測定結果は旧 B に限定する。

## 見つからなかったこと

- **凍結破壊:** prefix を抽出して実台帳と dryrun を照合した。426 entry は値だけでなく該当行 bytes も一致し、`@real-repo=0.19` は保持されている。
- **件数の取り違え:** 24,379→26,605、added 2,366、removed 140 は再計算と一致。2,366 は全 shard の新規台帳 key、334 は T-2817 の特定 shard・再現条件の未収載 unit で、同じ母数ではない。
- **consumer/test の漏れ:** `tools/` と `orchestrator/` の Python を `acceptance_duration_ledger` で検索した。実行時 consumer は conftest と割付器の 2 つ。test は brief の 3 本と整合し、paper-story test は固定 commit 区間の非接触検査だった。
- **依頼成果物の脱落:** 最大占有 worker の item 列、参考値の別欄は brief に存在する。ただし O_max・O_max−L は出力仕様として明記した方がよい。
- **scope 外の実装追加:** gate・台帳・一般化の新設は見つからない。門番 ≤60 は依頼指定なので、先例の <30 へ戻すべき欠陥ではない。

## 総括

高は **3 件**。判定は **修正後 GO**。段 4 で事前登録を直してから測定へ進める。
最重要は、通常成果物にない item 開始時刻を「観測できる」とした P3 の訂正である。
入力候補の緑・内部集合整合・凍結保持は確認できたが、main collection 一致と最新性は未確定。
固定 2 tree、W_0 主指標、軽量版そのものを却下する根拠は見つからない。