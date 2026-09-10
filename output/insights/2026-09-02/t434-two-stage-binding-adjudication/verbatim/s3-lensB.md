## must-fix

**M1 — 段 2 の NO-GO は支持されるが、親 brief の実装前提は成立しない。NO-GO を崩す実装単位も見つからない。**

(a) 主張: 性質で全件探索した結果、cap-lift 固有の認定記録、receipt、P6 実認定、呼出し済み production 経路はない。`subject_revision_sha` など認定記録の必須 field は設計文書にしかなく、`output/s8c-trial-registry/` 自体が存在しない。`CAP_LIFT_RECEIPT_*` は未使用の reason 語彙だけで、C11 の実評価は定数、3 入口、critic 射影を見て最後は `EVIDENCE_UNDEFINED` になる。`run_origin_trial` は public API だが repo 内 caller はなく、CLI `main` も origin 入力を渡さない。したがって DW-G04 を満たす artifact path または計測 ID は 1 件も挙げられない。

(b) 現物: `orchestrator/campaign/reflux_formal_consumer.py:1-8,959-1035`、`orchestrator/campaign/p3_autonomous_workload_trial.py:5016-5040,5201-5224`、`orchestrator/campaign/s8c_preregistration_evidence.py:80-87,2525-2568`、`orchestrator/campaign/s8c_acceptance_receipt.py:420-423`、`orchestrator/campaign/trial_registry.py:55-63,771-772`、親 brief `:7-12,45-48`、段 2 `:3-7,124,147`。

(c) 影響: 親 brief のまま land すると certified 選択、材料レポート、試行台帳の値と受理集合は変わらず、「topology を強制済み」という参照だけが偽に増える。

NO-GO を崩す側では、次の近似候補も除外した。

- `assert_effective_commit_exact_parent` は preregistration の production 経路で発火するが、cap-lift の G 要素ではなく、cap-lift artifact を読まない。
- `_validate_generation_budget` は `main`、`run_trial`、`_run_workload` から発火するが、現行 literal 2 を守る機構であり、D1407 の新 manifest、P6、receipt、consumer 結線のどれも実装しない。
- P6 formal 経路は `run_origin_trial` より外に caller がなく、「呼び手のいない public API」の反例にならない。

よって、(i) receipt 入口でない、(ii) 今日の production から発火する、(iii) 受理集合を広げない、を満たす D1407 G の新規実装単位はない。

**M2 — exact 2 create-only の既存実装はあるが、段 2 の wrapper 案は「exact 2」を完全には証明しない。**

(a) 主張: 性質検索では `diff-tree`、`ls-tree`、raw status、tree 比較の production 実装を全件確認し、exact 2 は `_added_paths` と `_verify_pairing` に実在した。これは `resolve_active_generation` から呼ばれ、さらに production loader に結線済みである。一方、段 2 の `{accreditation_path, receipt_path}` との set 比較には、2 引数が同一なら 1 path に縮退する穴がある。また `_added_paths` は status `A` しか見ないため、expected path が symlink または gitlink でも受理する。literal regular blob の確認はない。

(b) 現物: `orchestrator/campaign/s8b_ratified_freeze.py:607-618,1273-1295,1314-1335,1399-1412`、段 2 `:60-78`。既存の tree type 検査先例は `orchestrator/campaign/s8c_acceptance_receipt.py:658-683`。性質検索で見つかった別実装 `orchestrator/campaign/t080_freeze_migration.py:1253-1268` は `-M -C` 付き exact 1 path であり exact 2 ではない。

(c) 影響: wrapper を単独の発効 gate として信頼すると、1 path だけ、または記録でない symlink/gitlink 2 件の A が発効参照として受理され、certified 選択と台帳が不正な A を指し得る。

**M3 — exact-parent の述語ロジックは再利用可能だが、3 module の実行契約を「そのまま再利用可能」と一般化できない。**

(a) 主張: `assert_effective_commit_exact_parent` 自体は署名、root/merge/別親、shallow/graft/replace 拒否まで含み、述語 (i)(ii) にはそのまま使える。ただし新 wrapper 全体では差が残る。`trial_registry` は exact top-level と環境 allowlist を使う一方、`s8b` は cwd と `core.useReplaceRefs=false` だけで、private helper は `RatifiedFreezeError`、UTF-8 decode は `UnicodeDecodeError` を直接出し得る。`trial_registry._git` も process 起動失敗の `OSError` を包まないため、段 2 の「例外を一種類だけ露出」は未達である。`s8c` の封印型は `AcceptanceReceipt` と private seal に固定され、parser が `certifying=False` を強制するため、cap-lift に再利用できるのは pattern と primitive だけで型そのものではない。

(b) 現物: `orchestrator/campaign/trial_registry.py:942-985,1152-1269`、`orchestrator/campaign/s8b_ratified_freeze.py:290-325,518-555,607-618`、`orchestrator/campaign/s8c_acceptance_receipt.py:95-105,152-169,357-423,580-619,1219-1243`、段 2 `:28-56,80-94`。

(c) 影響: 非 UTF-8 message/path や Git 起動障害で構造化拒否ではなく処理全体が落ち、材料レポートと試行台帳に拒否理由や参照が残らない。現行封印型を流用すれば正例は構造的に永久不成立になる。

**M4 — trailer 末尾空白の負例は、段 2 が指定した helper だけでは本物にならない。**

(a) 主張: 段 2 は `test_trial_registry.py` の `_commit` を使うとしているが、これは通常の `git commit -m` で、Git の既定 cleanup が末尾空白を除去する。`AI-Agent: none ` を実 commit に保存するには `--cleanup=verbatim` が必要である。既存 s8b test はこの点を明示している。

(b) 現物: 段 2 `:98-120`、`orchestrator/tests/test_trial_registry.py:99-162`、`orchestrator/tests/test_s8b_ratified_freeze.py:100-115,1909-1929`。

(c) 影響: 通常 helper のままでは負例が正しい trailer に正規化され、raw 逐語 gate の変異を殺せないため、将来 regression 時に不正 trailer の A が発効参照へ入る余地を残す。

**M5 — 段 2 の裁定パッケージは consumer 列挙を改善したが、実効性に必要な層がまだ不足している。**

(a) 主張: 段 2 `:159-168` は主要 consumer を列挙したが、次は別の裁定パッケージ候補として明記が必要である。

- receipt SHA を含む campaign identity と、campaign identity を含む origin binding の循環を解く domain-separated preimage。
- `_RunScopeBinding` への generation と receipt SHA の封印。
- Layer 3 generator SHA 変更時の既存材料レポート互換規則。
- A の 2 path の distinctness、literal blob type、A blob と measurement HEAD blob の一致。
- 実在しない certified-selection consumer の新設範囲。
- 認定 request、独立検査者 attestation、失効照合から A 発見までの所有境界。

(b) 現物: `prior-design-v3.md:100-115`、`orchestrator/campaign/p3_autonomous_workload_trial.py:477-482,4896-4908`、`orchestrator/campaign/layer3_report.py:643-653,682-703`、`orchestrator/campaign/autonomous_trial_completeness.py:4687-4721`、段 2 `:153-168`。

(c) 影響: 放置すると同じ receipt が別 generation/configuration を承認し、試行台帳が誤った receipt を参照し得る一方、Layer 3 更新で既存材料レポートが fresh rebuild 不一致となり、certified 選択は依然発火しない。

## nit

**N1 — rename 負例の `R` は現行 `_added_paths` では発火せず、削除負例と冗長である。mode-only も内容変更と同じ gate である。**

(a) 主張: 実 rename commit `69e8d443d63d36deda1f64d1250d9e788a80bc72` で検算した。現行と同じ `diff-tree --no-commit-id --name-status -r` は `A + D`、`-M` 付きだけが `R100`、`diff.renames=true` だけでは `A + D` だった。したがって rename 負例は `other=D` で落ち、削除負例と同じ理由である。mode-only と内容変更も双方 `other=M` である。root、merge、別親、extra、M、D、trailer の各群は、wrapper を exact-parent、diff、trailer の順に呼ぶ限り狙った層まで到達する。

(b) 現物: `orchestrator/campaign/s8b_ratified_freeze.py:607-618`、段 2 `:68-74,108-120`、`orchestrator/campaign/t080_freeze_migration.py:1262-1266`。

(c) 影響: 現行の値、受理集合、参照は変わらないが、負例件数が独立 gate 数を過大表示する。

**N2 — 段 2 の 3 件の行番号は stale で、親 brief 側が現物と一致する。**

(a) 主張: `MAX_APPROVED_GENERATIONS` は 144 行、比較は 506 行、`generations must be the integer 2` は 771 行である。段 2 の 139、501、743 は不一致。他の主要引用、`1243`、`607-618`、`1273-1295`、`172-184`、`421-423`、`6073-6249`、`2289`、`4829`、`1499` は一致した。

(b) 現物: `orchestrator/campaign/p3_autonomous_workload_trial.py:144,501-509`、`orchestrator/campaign/trial_registry.py:743-773`、親 brief `:42-43`、段 2 `:134-137`。

(c) 影響: 受理集合や成果物値は変わらないが、実装者が誤った locus を参照する。

**N3 — 親 brief の 7 アンカーは行番号、関数名、定数、診断文字列とも一致する。ただし P6 の一般化だけ修辞が強すぎる。**

(a) 主張: 7 行すべて現物一致した。唯一の留保は「P6Unavailable で無条件停止」で、実際には C1-C7、C9-C10 等の前段が失敗すれば `FormalContractRejected`、全前段を通ったときだけ `P6Unavailable` になる。正確な一般化は「非 aborted 成功はなく、前段通過後は必ず P6Unavailable」である。

(b) 現物: `orchestrator/campaign/reflux_formal_consumer.py:959-1035`、親 brief `:33-43`。残るアンカーは `trial_registry.py:1211-1269`、`s8b_ratified_freeze.py:518-573`、`s8c_acceptance_receipt.py:152-172,259-266,421-423`、`p3_autonomous_workload_trial.py:144,506`、`trial_registry.py:771`。

(c) 影響: 現在の値は変わらないが、「P6 だけを壊した負例」のつもりで前段 contract も壊すと、材料レポートの reason と試行台帳の拒否参照が別理由になる。

**N4 — topology 正例の設計は real Git commit だが、まだ存在せず cap-lift end-to-end 正例でもない。既存 certifying 正例は stub である。**

(a) 主張: 段 2 の将来正例は実 repo、実 G、実 A を作り、Git/trailer parser を差し替えないため topology 単体としては本物である。既存 exact-parent 正例も実 commit で通る。一方、cap-lift schema、認定記録、receipt、consumer がないため end-to-end 正例はない。既存 Layer 3 certifying 正例は `SimpleNamespace(certifying=True)` と `require_current_verified_receipt` の monkeypatch に依存する。

(b) 現物: 段 2 `:96-105,124`、`orchestrator/tests/test_trial_registry.py:6135-6181`、`orchestrator/tests/test_layer3_report.py:264-270,1824-1842,1911-1931`、`orchestrator/campaign/layer3_report.py:689-702`。

(c) 影響: 現状の値と受理集合は変わらないが、topology fixture を cap-lift positive control と記録すると材料レポートと台帳が存在しない end-to-end 証拠を参照する。

## 総括

最も重い所見は M1 である。段 2 の NO-GO は、識別子だけでなく artifact field、output tree、caller graph、manifest/receipt/P6 の意味的性質を全件確認して支持された。NO-GO を崩す 3 条件同時成立の実装単位もない。

崩れた親 brief の前提は「既存 helper を組み合わせれば、今この wave で実効性のある D1407 topology 機構と実正例を成果物にできる」である。helper の部品は実在するが、cap-lift の発火 artifact、production caller、P6 実認定がなく、exact 2 と例外契約にも未解決差分がある。したがって現段階はコード無変更、設計メモと裁定パッケージへ戻すのが妥当である。

pytest は実行していない。Git の rename 挙動だけ、既存履歴の実 commitを使って read-only 実測した。