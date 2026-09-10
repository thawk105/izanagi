## 所見

1. **主張:** 既存 pin の主要範囲はプラン v2 にあるが、依存 helper と全 `LandResult` 生成点の列挙が不足している。  
   **根拠:** `tools/dev_wave_wait.py:400-406,2493-2643,2720-2822`、`orchestrator/tests/test_dev_wave_wait.py:606-819,1734-1778,3480-3562,8211-8235`、`tools/dev_wave_land.py:142-173,749-765,1877-3343`。  
   **倒れる向き:** helper 未更新なら受入テストが赤になる。逆に `flake_nodeids` を任意扱いにすると、実装は緑でも結果が欠落する。  
   **推奨対応:** `_checker_receipt_bytes`、`_queue_checker`、`_red_check`、land の receipt fixture と、全 `LandResult(...)` 呼出しを明示的な影響一覧に加える。

2. **主張:** producer と consumer の相互 pin は、純粋述語だけを直接呼ぶと偽緑になる。  
   **根拠:** 実 producer の node runner は `tools/check_acceptance_reds.py:956-994`。既存 producer テストは `orchestrator/tests/test_check_acceptance_reds.py:543-568,582-610,624-646` で `node_runner` を注入している。release authority は `tools/dev_wave_land.py:575-589` の exact parser と holder 照合だけで、受入意味論は検査しない。  
   **倒れる向き:** producer と consumer が同じ helper や期待値を共有すると、両方の drift を同時に見逃す。release authority だけ通しても land 本体の flake 検証にはならない。  
   **推奨対応:** producer が実際に書いた receipt bytes を `json.loads` し、独立した literal と実 consumer へ渡す。少なくとも一つは `_verify_red_check_receipt`、v4 outer receipt、release authority、real land を同じ bytes で通す。新テストで production predicate を monkeypatch しない。

3. **主張:** P7 は `tested_main` と `tested_tip` の固定 SHA を使わないと、merge 後に gate が空洞化する。  
   **根拠:** waiter は `tools/dev_wave_wait.py:3181-3215` で `claim_context.main_sha` と postrun head を使う。land は `tools/dev_wave_land.py:3023-3029` で検証するが、現状 runner は `tested_tip` の存在確認だけを `tools/dev_wave_land.py:691-705` で行う。  
   **倒れる向き:** merge 後の `main` または現在の `HEAD` を使うと、main と tip が同一になり、異なる runner を見逃す。  
   **推奨対応:** waiter と land の両方で request の `tested_main` / `tested_tip` を使い、FF 前に比較する。land の P7 失敗は既存 checker blob と同じ retryable 処理へ入れる。docs fragment の commit も final acceptance 前に完了させる。

4. **主張:** `git rev-parse` の 40 桁判定だけでは runner が blob だと証明できない。  
   **根拠:** waiter の `_blob_sha` は `tools/dev_wave_wait.py:1862-1895`、checker 用 `_red_gate_blob_sha` は `tools/dev_wave_wait.py:1951-1972` で SHA 形式だけを検査する。land の現 runner 検査は `tools/dev_wave_land.py:700-705` の `cat-file -e` だけである。submodule と通常 entry の区別は別途 `tools/dev_wave_land.py:1593-1641` にある。  
   **倒れる向き:** `tools/run_tests.py` が将来 gitlink や tree になっても、同じ object ID なら P7 が通る可能性がある。  
   **推奨対応:** runner 専用検査で `git cat-file -t <revision>:tools/run_tests.py` が `blob` であることを確認してから SHA を比較する。現在の tree では runner は通常 blob、`external/ccbench` は gitlink だが、現状は将来不変条件ではない。

5. **主張:** red-only の受理集合を P7 で狭めないことを、既存テストの event 列で固定する必要がある。  
   **根拠:** `orchestrator/tests/test_dev_wave_wait.py:2552-2560` は checker blob が同じなら main/tip が異なる red-only を受理する fixture。P7 の実装対象は flake 非空だけである。  
   **倒れる向き:** gate を無条件化すると、red-only に不要な runner Git query が入り、既存 fake event が赤になる。条件を逆にすると flake-only が runner 不一致でも通る。  
   **推奨対応:** runner 同一性不一致の flake-only reject と、runner が異なっても通る red-only positive を別々に登録する。

6. **主張:** runbook の2箇所は現行の `check_docs.py` の §7.0 exact table 契約や byte budget には直接触れないが、fragment は別の spool 契約で落ちうる。  
   **根拠:** 対象は `docs/pegasus-runbook.md:833-843,878-882` の §7.3。§7.0 構造検査は `tools/check_docs.py:2462-2528,3389-3435`、runbook は `LIVING_DOCS` の通常列挙外である `tools/check_docs.py:47-87`。fragment は `tools/check_docs.py:894-950` の spool guard で検査される。  
   **倒れる向き:** runbook prose だけなら check_docs は赤にならないが、D fragment が無い状態で worklog の `{{D:r2-flake-observation}}` を入れると unresolved placeholder で dry-run が赤になる。  
   **推奨対応:** decision seq 1 と worklog seq 2 を同じ wave commit に入れ、`check_docs.py` と `spool_fold.py --dry-run --show-diff` を両方実行する。§7.0 の見出し、table、fence は変更しない。

7. **主張:** worklog fragment の形式は概ね適合するが、提案本文は実測前に「変更後の受入で判定した」と記録しており、段 7 規律に反する。  
   **根拠:** 提案 fragment はプラン v2:185-212。段 7 は `docs/dev-wave/core.md:87-100`、実行手順と記録の分離は `docs/dev-wave/operations.md:77-82`。`完了` の構造は `docs/spool/worklog/README.md:64-86`。  
   **倒れる向き:** fragment の形式は通っても、未実施の受入結果を記録した偽の完了になる。  
   **推奨対応:** final acceptance、land、fold、provenance の実測後に内容を確定する。未実施段階では `完了` を作らない。

8. **主張:** `base:` は現在の T-1302 実体には合っているが、land 時点で再計算が必要である。  
   **根拠:** 現在の実体は `docs/worklog.md:2962-2966`。その本文 digest は `d22493a12155e80c0b1989e409764ecfc36853018b84b008383bb1b8a7281fe4`。carry 解決は `tools/spool_fold.py:1536-1597`、照合と赤化は `tools/spool_fold.py:1743-1777`。  
   **倒れる向き:** 先行 wave が T-1302 を更新すると、`check_docs.py` は通っても `spool_fold.py --dry-run` が `base-mismatch` で赤になる。  
   **推奨対応:** fragment の本文や `base:` 自身を hash せず、carry 解決後の現 canonical item を hash する。fold は wave 側で実行しない。

9. **主張:** 追加テストの履歴比例コストは現案なら発生しないが、固定 fixture のまま保つ必要がある。  
   **根拠:** spool は active T を列挙せず carry できる `docs/spool/README.md:90-118`。ただし実 fold は archive も読む `tools/spool_fold.py:2327-2351`。  
   **倒れる向き:** node 数、過去 ledger、archive file 数ごとに fixture やテストを増やすと、受入コストが履歴比例になる。  
   **推奨対応:** producer、waiter、land、authority は各1〜数個の固定 node fixtureにする。64 KiB テストも固定 filler 1個だけを再計算する。

10. **主張:** 段 6〜9では、P7 と2集合伝搬に特化した追加手順が必要である。  
    **根拠:** 段 6 の再レビューと親による mutation/受入再走は `docs/dev-wave/workers.md:45-67`。段 7 の fragmentと非foldは `docs/dev-wave/core.md:87-100`。受入 cwd・単独走は `docs/dev-wave/operations.md:111-120`。landとfoldの lock 内順序は `docs/dev-wave/operations.md:146-157`。  
    **倒れる向き:** 変更 test file の単独走、final tip 固定、fragment fold、post-land authority のいずれかを省くと、実装は通っても最終成果物へ発効しない。  
    **推奨対応:** 変更した3 test fileを別 processで焦点走、docs commit後に final acceptance、receiptの tested SHA と同じ bytes を landへ渡す。land成功後に lock 内 fold、`landed`/`already-landed`、main HEAD、fold receipt、provenance、release authority を確認する。

## 落ちる既存テストの一覧

プラン v2:21-24 の列挙は主要範囲を押さえているが、以下の差分がある。

- `orchestrator/tests/test_dev_wave_wait.py:1734-1778`  
  `set(receipt)` の exact field 集合、schema v3、child-green の `red_nodeids` 空を pin している。v4 と `flake_nodeids` 追加で赤になる。

- `orchestrator/tests/test_dev_wave_wait.py:8211-8235`  
  実 process receipt の schema v3 literal を pin している。v4 へ更新が必要。

- `orchestrator/tests/test_dev_wave_wait.py:3480-3562`  
  `red_nodeid_count` だけの detail JSON を exact 比較している。flake count追加後に期待値が赤になる。

- `orchestrator/tests/test_dev_wave_wait.py:606-819`  
  `_checker_receipt_bytes`、`_queue_checker`、`_checker_execution_events`、`_red_check` が node形、event列、`_RedCheckResult` の現 field数を固定している。特に `_red_check` は新 field に default が無ければ直接赤になる。

- `orchestrator/tests/test_dev_wave_wait.py:3215-3240`  
  red-only receipt の検査が `red_nodeids` だけで、flake空の pin がない。実装後も通る可能性はあるが、伝搬欠落を検出できないため更新必須。

- `orchestrator/tests/test_dev_wave_wait.py:2841-2865,3029-3071`  
  real checker 結果の red 集合だけを検査している。プラン v2:21 の wait test 範囲から漏れており、`flake_nodeids == ()` の独立 pinを追加すべき。

- `orchestrator/tests/test_dev_wave_land.py:216-273`  
  child-green fixture が exact outer field集合を作る。`flake_nodeids` を追加しないと、`_receipt_object` の `tools/dev_wave_land.py:562-572` で全 fixture が拒否される。

- `orchestrator/tests/test_dev_wave_land.py:424-446`  
  red-only fixture が `flake_nodeids` を持たない。`orchestrator/tests/test_dev_wave_land.py:751-985` の tamper/verdict/red-only 群へ波及する。

- `orchestrator/tests/test_dev_wave_land.py:726-811`  
  schema v2、unknown field、receipt exact parserを検査する。v4 missing field と v3 fallback拒否を追加する必要がある。

- `orchestrator/tests/test_dev_wave_land.py:819-897`  
  child-green と red-only の field整合性だけを検査する。flake非空、空集合、非整列、重複、red/flake重複のケースが不足している。

- `orchestrator/tests/test_dev_wave_land.py:919-941`  
  現在は `wave.txt` だけを変えて checker blob の同一性を検査している。P7の red-only 正例には runner blob divergence を入れ、別途 flake-only divergence reject を追加する必要がある。

- `orchestrator/tests/test_dev_wave_land.py:1119-1227`  
  real waiterからreal landへのred-only経路で、outer receiptと結果 JSONにflakeがない。real flake receipt、release authority、landの同一 bytes 経路は現テストに存在しない。

- `orchestrator/tests/test_dev_wave_land.py:3739-3778`  
  `LandResult` exact equality の期待値が `acceptance_flake_nodeids` を持たない。実結果は verified child-green なら空 tupleになるため赤になる。

- `orchestrator/tests/test_dev_wave_land.py:6071-6084`  
  既定 JSON の field存在をまだ検査していない。赤化しないが、未検証結果が `None` であることを追加 pin すべき。

- `orchestrator/tests/test_dev_wave_land.py:6558-6611`  
  JSON byte長 `65491/65547/65526` を exact pin している。新 field 追加で確実に赤になり、filler再計算が必要。

- `tools/dev_wave_land.py:1877-3343`  
  production の `LandResult(...)` 呼出しが多数ある。新 field を必須 positional field にすると実装側が赤になる。v2:14,23 は代表テストを示すだけで全 call site を列挙していない。

- `orchestrator/tests/test_check_acceptance_reds.py:533-646`  
  producerの3分類 node literal。プラン v2の相互 pin対象であり、独立 literalのまま実 consumerへ渡す必要がある。

- `orchestrator/tests/test_check_acceptance_reds.py:1149-1184`  
  producer receipt の canonical JSONと非帰属 node literalを別途 pin している。producer 変更なしでも、プラン v2:88-94 の相互 pin一覧から漏れているため、維持対象か追加対象かを明記すべき。

## 変異事前登録の提案

1. **位置:** `tools/dev_wave_wait.py:2802-2822` の flake node述語。  
   **変異:** `classification == "flake"`、5 field exact、または3つの rc == 0 のいずれかを削除する。  
   **期待される赤:** 正常な root、checker blob、runner blobを使った malformed-node test が `acceptance-red-check` で赤。root gateより前に拒否されない入力にする。

2. **位置:** `tools/dev_wave_wait.py:2802-2822` と landの `tools/dev_wave_land.py:671-688`。  
   **変異:** red/flake の和集合ではなく red だけを見て受理、または相互排他検査を削除する。  
   **期待される赤:** flake-only と red/flake overlap の固定 payload が拒否されない。checker root と Git blobは全て正常にする。

3. **位置:** waiterのP7分岐。  
   **変異:** `flake_nodeids` 非空時の `tested_main:tools/run_tests.py` と `tested_tip:tools/run_tests.py` 比較を削除、または tip同士を比較する。  
   **期待される赤:** checkerが正常で、flake nodeも正常だが runner blobだけ異なる実Git fixtureから、outer receiptを発行してしまう。

4. **位置:** `tools/dev_wave_land.py:691-748` のP7検査。  
   **変異:** main runnerを検査しない、`tested_main` の代わりに現在の `main` を使う、または比較結果を `receipt_git_results` へ入れない。  
   **期待される赤:** crafted v4 flake receiptを実Git fixtureへ渡し、main HEADが不変のまま `acceptance-receipt-rejected` にならない場合を kill とする。

5. **位置:** waiterとlandのP7条件。  
   **変異:** flake限定条件を削除し、red-onlyにも runner等値を要求する。  
   **期待される赤:** runner blobが異なる正しい red-only receipt が受理されない。checker blob、schema、red node、child rcは正常にして、P7だけが理由になるようにする。

6. **位置:** `tools/dev_wave_land.py:562-572,632-690`。  
   **変異:** v3 fallbackを追加、または v4 の `flake_nodeids` 欠落を許す。  
   **期待される赤:** v3 receiptとv4 missing-field receiptが mainを変更せず拒否されない場合を kill とする。ほかの fieldは完全に正常にする。

7. **位置:** `tools/dev_wave_land.py:749-765` と `tools/dev_wave_land.py:156-173`。  
   **変異:** verificationから `flake_nodeids` を落とす、または `LandResult.as_json()` から落とす。  
   **期待される赤:** runner同一の flake receiptを受理した後、tupleとJSON listの両方に nodeが残らない場合を kill とする。

8. **位置:** runner blob取得部。  
   **変異:** object typeを見ず、40桁 SHAまたは `cat-file -e` だけで通す。  
   **期待される赤:** `tools/run_tests.py` を treeまたはgitlinkとして持つ固定Git fixtureで、同一 object IDでも拒否されない場合を kill とする。通常の blob fixtureでは前後 gateが赤にならないようにする。

9. **位置:** `docs/spool/worklog/2026-08-17-dev-wave-t1302-r2-nonattrib-2.md` の `base:`。  
   **変異:** digestを1桁変更する。  
   **期待される赤:** `check_docs.py` が通っても `spool_fold.py --dry-run` が `base-mismatch` で赤になることを確認する。これは check_docs と dry-run の役割分担を pin する diagnostic ではなく、fold fail-closed の KILLED 登録である。

10. **位置:** `orchestrator/tests/test_check_acceptance_reds.py:571-610` の producer-consumer相互 pin。  
    **変異:** producerの flake classification を attributable にする、または consumerの attributable拒否を緩める。  
    **期待される赤:** producerが実際に書いた bytes を独立 literalの consumerへ渡したとき、双方を同時に変えない限り不整合が赤になる。期待値を producer helperから生成しない。

## 総括

主要な受入閉包は成立するが、P7の revision と blob type を固定しないと gate が空洞化する。  
既存テストでは wait helper、land fixture、`LandResult` equality、64 KiB境界が必須更新箇所である。  
fragment の形式は妥当だが、実測前の `完了` 記録と stale `base:` は dry-run を壊す。  
段6の変異、段7の未fold記録、段9の同一 receipt bytesによる land までを一つの受入手順として扱う必要がある。