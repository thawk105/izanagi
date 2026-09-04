## 観点 1 の所見

- **[real / must-fix 1] `ORACLE_CONTRACT_ID` は oracle の挙動全体を自動では覆わない。**  
  `AXIOM_CHECKER_IMPLEMENTATION_SHA256` は列挙された関数だけを hash し、実装自身も「closure ではない」「列挙外 helper へ判断を移しても identity は変わらない」と明記している (`sort_swo_oracle.py:3020-3061`)。特に PASS/REJECT/UNAVAILABLE を組み立てる最上位 `check_materialized_sort_swo()` (`sort_swo_oracle.py:3216-3479`) は列挙外である。ここで real-TU conformance 呼出しを変更しても、version 定数を手動更新しない限り ID は不変である。`_RUN_TIMEOUT_S`、`_limit_run()`、`_communicate_hard_timeout()` も同様に列挙外 (`sort_swo_oracle.py:61, 2201-2221`)。  
  成果物影響: oracle の受理集合が変わっても同じ campaign identity・束縛 token・cache key が使われ、旧 cache binary と新しい certified 選択を同一契約として台帳・レポートが参照する。

- **[real / nit] 同一の意味的契約でも ID が変わる経路はある。**  
  checker hash は `inspect.getsource()` の逐語 bytes と関数の module/qualname を hash するため、コメント、整形、局所変数名、関数移動でも変わる (`sort_swo_oracle.py:3052-3071`)。TU/broker bundle も source text を同様に hash する (`sort_swo_oracle.py:2140-2184`)。さらに version 定数だけの bump でも最終 ID が変わる (`sort_swo_oracle.py:48-53, 3126-3133`)。  
  成果物影響: campaign ID と cache key が分離して再 build になるが、受理集合や測定値は変わらない。性能上の miss だけなので must-fix ではない。

- **[不確定] 実行 compiler を契約に含めるかは未裁定に見える。**  
  compiler path/version は `OracleReceipt` にだけ入り (`sort_swo_oracle.py:227-234, 3136-3181`)、`_ORACLE_CONTRACT_COMPONENTS` には入らない (`sort_swo_oracle.py:3095-3108`)。静的な oracle コード/data 契約だけを ID とするなら正しい。一方、実現された oracle の受理挙動まで「契約」と呼ぶなら、compiler 更新で受理結果が変わっても campaign/cache identity は同じになりうる。

- **[refuted] sort binder と backoff binder の同一 preimage は構成できない。**  
  backoff は `backoff-src-token/v1\0grammar=...` (`source_digest.py:2189-2194`)、計画の sort は `sort-src-token/v1\0contract=...` で、先頭 byte 列から異なる。値や NUL で後続境界を操作しても先頭 domain は一致しない。SHA-256 自体の未知の衝突を除き、入力構成による cross-domain 衝突ではない。

- **[refuted] 現行 `ORACLE_CONTRACT_ID` は ASCII だけで構成される。**  
  固定 ASCII literal、十進整数、`hexdigest()` だけから作られ (`sort_swo_oracle.py:48-53, 122-124, 989-994, 1208, 2187-2189, 3089-3133`)、guarantee boundary も `.encode("ascii")` が import 時に検証する (`sort_swo_oracle.py:3101-3103`)。計画どおり exact 非空 `str`、NUL なし、ASCII を binder 入口で検査すれば、NUL・非 ASCII は hash 前の `ValueError` になる。

- **[refuted] 両引数非 `None` の検査は既定 bytes を変えない。**  
  `if backoff_grammar_version is not None and sort_oracle_contract_id is not None` は両方 `None` では偽であり、その後の既存分岐へ同じ値で進める。`_resolved_src_token()` でも既存三位置引数を維持し、stock 判定、sort、既存 backoff の順なら既定・backoff bytes は同一である (`source_digest.py:2198-2216`)。

- **[refuted / scope correction] `run_campaign` の三者 gate は仮想リスク向けの新設であり scope 外。**  
  旧 lock を通常 resume すると、改版後の `default_cfg()` は新 ID を `search_config` に置くため別 campaign ID になる (`p3_s4_loop_sort.py:285-328`, `ident.py:196-229`)。旧 ID の cfg を明示的に持ち込んでも、計画の `_require_sort_oracle_contract(cfg)` を `layout.ensure()` と `ensure_resumable_attempts()` より前に置けばそこで停止する (`p3_s4_loop_sort.py:343-387`)。したがって単一 producer を守る限り、入口 gate が無いことで変わる in-scope 成果物はない。producer を迂回した直接 `run_campaign` だけなら、旧引数で旧 token/cache/WALへ新 module の判断を混ぜられるが、それは plan 自身が禁止する経路である。親 brief `s1-brief.md:13` と P3 `:39-40` はこの点で矛盾している。

## 観点 2 の所見

- **[refuted] 引数を渡さない caller の identity/cache bytes は、計画どおりなら不変。**

  - `loop.run_campaign()` は非 `None` のときだけ resolver/evaluate kwargs を増やす (`loop.py:477-485, 531-591`)。
  - pipeline も resolver、legacy build、v2 build の dict へ非 `None` 時だけ追加する設計である (`pipeline.py:1090-1101, 1219-1278`)。
  - 両方 `None` の非 stock token は従来どおり raw digest、stock は先に `"stock"` となる (`source_digest.py:2198-2216, 2294-2338`)。
  - legacy key は同じ token を `|src=` に使い (`buildcache.py:624-642`)、v2 preimage も既存 `src_token` fieldだけを使う (`buildcache.py:1295-1324`)。
  - `s1_direct_comparison.py` は ID を config に持つが resolver/evaluate へ引数を渡さない (`s1_direct_comparison.py:471-482, 923-927, 1219-1224`)。`s6_sort_sweep.py`、trigger loop、backoff/P2-4 sweep も新引数を渡さない (`s6_sort_sweep.py:383-418`, `p3_s4_loop_trigger_gating.py:811-820`)。

- **[refuted] backoff 経路を緩める編集は計画にない。**  
  入口の三者 exact gate は現状維持 (`loop.py:336-350`)。sort が `None` なら既存 `_bind_backoff_grammar_version()` が同じ int・同じ ASCII preimageで呼ばれる (`source_digest.py:2177-2203`)。四つの build 出口も既存 version を再照合へ渡す (`buildcache.py:2594-2598, 2836-2840, 3176-3180, 3241-3245`)、再 resolver も非 `None` のときだけ既存 keyを加える (`buildcache.py:3308-3328`)。

- **[refuted] sort campaign の `search_config` と campaign ID は、この wave の記載どおりなら不変。**  
  `default_cfg()` の値を変更せず、追加値は runtime-only keyword である (`p3_s4_loop_sort.py:298-305`)。ただし must-fix 1をこの wave で直して `ORACLE_CONTRACT_ID` 自体を変える場合は、実効 `search_config` と campaign IDも変わるため、段4の裁定が必要になる。

- **[real / nit] テスト計画は binder の exact contract を pin し切っていない。**  
  `s2-plan.md:91-95` は分離と既定 identityを検査するが、固定入力に対する exact preimage hash、backoff tokenとの不一致、空文字・NUL・非 ASCII の拒否を明記していない。また既定不変テストの列挙に `verification_variant` がない。実装記述が正しければ成果物は変わらないため nit だが、回帰検出面として追加すべきである。

- **[real / nit] `loop.py` への top-level `sort_swo_oracle` import は既定経路の失敗面を広げる。**  
  同 module は import 時に `inspect.getsource()` を実行し、取得不能を fail closed にする (`sort_swo_oracle.py:3052-3061, 3089-3094`)。したがって unrelated campaign も source を取得できない配布形では loop import 自体に失敗する。bytes の誤生成はないが、レポート・台帳が生成されない運用退行になる。入口 gateを外すなら import自体が不要である。

## 親 brief への指摘

- **[refuted] 「identity と WAL には届くが cache には届かない」という中核測定は正しい。**  
  ID は `default_cfg()` の `search_config` に入り (`p3_s4_loop_sort.py:298-305`)、全 search config が campaign preimageと lockへ入る (`ident.py:196-223, 583-602`)。oracle attempt/reject recordにも ID が入る (`sort_swo_oracle.py:3482-3532`)。一方、段5の現行 `run_campaign()` 呼出しには sort ID がなく (`p3_s4_loop_sort.py:397-401`)、source tokenは raw digestのまま cache keyへ届く。

- **[real / nit] 「WAL に届く」は build attempt への束縛まで一般化してはならない。**  
  oracle attempt の WAL recordと campaign.lockには ID があるが、accepted candidate の `BUILD_START` は現状 `src_token` と admission receiptだけで、平文 contract IDはない (`pipeline.py:1184-1197`)。しかも oracle attempt の variant は `diffq_variant_id`、build attempt は source-bound `variant_id` で別系列である (`p3_s4_loop_sort.py:230-257, 397-407`)。親のP4はこの限定を認識しているため、scope節側にも同じ限定が必要である。

- **[refuted] `test_campaign.py:5355` は実際に一回呼出しを pin している。**  
  単なる文字列検査ではなく、repo-wide resolved-call inventory の Counter と実 inventoryを比較する (`test_campaign.py:5308-5323, 5346-5400`)。sort loopの登録数は exact 1である。

- **[real / nit] 「D1411 テスト群が署名を固定」は過度な一般化。**  
  現行 introspection testが固定するのは `run_campaign`、`evaluate`、`resolve_evidence`、`resolve`、`src_token` の5 seamだけ (`test_p3_s4_loop.py:3439-3454`)。`_prepare_evaluation_core`、`build_v2`、`build`、`_recheck_source_evidence` の署名は固定していない。後続の伝播/cacheテストは動作を覆うが、全 seam の signature pinではない。

- **[real / must-fix 1と同一] P1の「oracle全体を覆う」という説明は実コードより強い。**  
  親 brief `:36` と plan `:122-124` は corpus/checker/TU等を列挙して十分とするが、checker hash自身が列挙 closureでないことを明記している。ここは「手動 version bumpを含む運用契約」なのか「コードから自動導出される完全な契約 ID」なのかを分離して書く必要がある。

## 裁定パッケージ候補

- **C-ID-CLOSURE — `ORACLE_CONTRACT_ID` の権威境界**
  - 推奨: sort-localに top-level orchestration、判定に効く helper、timeout/resource semantic constantsまで component manifestへ含め、schema/contractを更新する。その場合、現行 ID・campaign IDが変わることを明示的に受け入れる。
  - 代案: 現行の列挙 hashを維持し、列挙外変更では `CONTRACT_VERSION` を必ず手動 bumpする運用を正本化する。この場合、P1を「自動的に oracle全体を覆う」とは主張しない。

- **P3-ENTRY-GATE — defense-in-depth を scopeへ追加するか**
  - 推奨: `run_campaign` gateと global importは外し、`p3_s4_loop_sort.py` の早期単一 producerだけを残す。
  - gateを残すなら、仮想リスク向け機構をscope外とした親 brief `:13` を明示的に覆す裁定が必要。

- **ORACLE-RUNTIME — compiler identityの位置付け**
  - compiler/versionを realized contractと見るなら campaign/cache bindingへ含める別裁定が必要。
  - execution receiptの環境証跡と見るなら、現行の receipt-onlyを意図した境界として明記する。

## 総括

must-fix は **1件**。最重要は、`ORACLE_CONTRACT_ID` が top-level oracle判断を含む behavioral closureではなく、契約変更時にも同じ IDを返しうる点である。  
既定 `None` と backoff の bytes不変、cache identity、sort `search_config` 不変は、記載どおり実装すれば静的には成立する。  
`run_campaign` の三者 gateは単一 producerが早期照合する限り成果物を守らず、親のscope規定どおり外すべきである。  
段4では ID closureを今回直してcampaign identity移行を受け入れるか、手動version bump境界を明文化して現行IDを束縛するかを裁定すべきである。  
pytestは実走しておらず、以上は静的検査結果である。