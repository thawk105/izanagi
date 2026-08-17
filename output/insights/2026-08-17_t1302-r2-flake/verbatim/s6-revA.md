## must-fix

1. 合成 repo fixture に新しい runner gate の入力がなく、実測赤 3 件を発生させている。これは実装述語の誤りではなく fixture の更新漏れである。

   - 根拠: `_verify_red_check_receipt` は全 `non-attributable-only` で runner 同一性を検査する (`tools/dev_wave_wait.py:2945-2951`)。ところが `_real_red_checker_repo` は checker しか commit していない (`orchestrator/tests/test_dev_wave_wait.py:2967-2970`)。赤 3 件はいずれもこの fixture を使う (`orchestrator/tests/test_dev_wave_wait.py:3076-3087`, `:3137-3150`, `:3205-3221`)。対照的に別 fixture は runner を正しく追加している (`orchestrator/tests/test_dev_wave_wait.py:3017-3019`)。
   - 成果物影響: 放置すると受入全走は 3 件の差分帰属赤となり、outer receipt が発行されず、本 wave の land 結果は成功にならず main も進まない。
   - 具体的な直し方: `_real_red_checker_repo` の初回 commit に、main/tip で同一 bytes の `tools/run_tests.py` blob を追加する。既存テストの期待値は変えない。

2. land 側で「immutable commit に runner path が存在しない」という恒久拒否まで一律 retryable に分類される。

   - 根拠: runner の `cat-file -t` と `rev-parse` を含む全 Git 結果について、どれかが非 0 なら無条件で `retryable_same_request=True` になる (`tools/dev_wave_land.py:782-796`)。その結果、同じ commit では直らない path 欠落でも `release_safe=False` となり lease が保持される (`tools/dev_wave_land.py:3417-3429`)。
   - 成果物影響: 放置すると land 結果 JSON の `retryable_same_request` が誤って `true` になり、受理集合は閉じたままでも acceptance lease が無駄に保持され、同一 request の再試行が反復する。
   - 具体的な直し方: stderr 文字列ではなく、`ls-tree` または `cat-file --batch-check` の構造化結果で「path 不在」を rc=0 の恒久拒否として識別する。Git process/I/O 失敗だけを retryable に残し、双方のテストを追加する。

## nit

なし。

なお、次は nit ではなく裁定済みの防御範囲外である。

- runner を変更して対象テストを走らせず rc=0 を返せば、待ち手は `child-green` を選び checker と runner gate を呼ばない (`tools/dev_wave_wait.py:3314-3328`)。land も child-green では main/tip runner 等値を要求しない (`tools/dev_wave_land.py:671-683`, `:740-772`)。これは正例 1 として明示的に要求され、テストでも固定されている (`orchestrator/tests/test_dev_wave_land.py:1002-1018`)。
- flake 側も、同一 runner blob であることしか保証しない。変更された `conftest.py` や plugin が対象 node を実行せず rc=0 にする経路は残る。rc=0 に PASSED 証明がない (`tools/check_acceptance_reds.py:956-994`) ことは裁定で明示受容されている (`s4-adjudication.md:15-19`, `:45-46`, `:89-95`)。
- 同一 Unix user が完全な v4 receipt を直接偽造する攻撃も残る。`_receipt_object` は署名ではなく exact JSON parser である (`tools/dev_wave_land.py:573-583`)。これは D387 が意図的偽造を防御範囲外としている (`docs/decisions.md:16451-16468`)。この脅威モデルを変更するなら、新しい authority 機構についてユーザー裁定が必要である。

## 署名との対応表

| 契約 | 待ち手 | land | 検査 |
|---|---|---|---|
| 禁止 1: runner blob 不一致 | `tools/dev_wave_wait.py:2041-2065`, 呼出 `:2945-2951` | `tools/dev_wave_land.py:763-772`, 比較 `:813-817` | `orchestrator/tests/test_dev_wave_wait.py:2760-2773`; `test_dev_wave_land.py:1021-1059` |
| 禁止 2: object type が blob でない | `tools/dev_wave_wait.py:1962-1977` | `tools/dev_wave_land.py:751-762`, `:809-816` | `test_dev_wave_wait.py:2776-2795`; `test_dev_wave_land.py:1062-1086` |
| 禁止 3: node shape と rc pin | `tools/dev_wave_wait.py:2851-2887` | land は checker node を再読せず、分離済み outer 集合を検証 | `test_dev_wave_wait.py:2496-2591`; 実 producer 相互 pin は `test_check_acceptance_reds.py:541-702` |
| 禁止 4: sorted・unique・disjoint | checker receipt は `tools/dev_wave_wait.py:2888-2894`、outer producer は `:2644-2663` | `tools/dev_wave_land.py:696-706` | `test_dev_wave_wait.py:2602-2609`; `test_dev_wave_land.py:865-922` |
| 禁止 5: 2 集合の和が空 | `tools/dev_wave_wait.py:2644-2649` | `tools/dev_wave_land.py:696-708` | flake-only 正例 `test_dev_wave_wait.py:3479-3503`; `test_dev_wave_land.py:952-976` |
| 禁止 6: child-green で集合非空 | `red_check is None` を要求 `tools/dev_wave_wait.py:2630-2643`、両集合を空で出力 `:2712-2721` | `tools/dev_wave_land.py:671-680` | `test_dev_wave_wait.py:1791-1834`; `test_dev_wave_land.py:835-922` |
| 禁止 7: v4 と exact field | schema `tools/dev_wave_wait.py:231`、出力 `:2695-2722` | schema・field 集合 `tools/dev_wave_land.py:70-97`, parser `:573-583`, schema値 `:643-670` | `test_dev_wave_land.py:736-827` |
| 正例 1: child-green は runner 差異を許す | `test_dev_wave_wait.py:3863-3884` | `test_dev_wave_land.py:1002-1018` | 署名どおり受理 |
| 正例 2: red 1 件と flake 1 件を分離受理 | `test_dev_wave_wait.py:3505-3531` | `test_dev_wave_land.py:979-999` | 両集合を別々に結果へ伝搬 |

署名より広い実装上の受理集合は見つからない。上記 child-green と PASSED 証明欠落は、署名自体が残している受理集合である。

D389 の `child_rc==1`、checker rc/status、`log_sha256`、checker blob 等値は維持されている (`tools/dev_wave_wait.py:2820-2829`, `:2909-2958`; `tools/dev_wave_land.py:684-708`, `:740-821`)。v3、field 欠落、型違いは land 本検証を抜けない。release-authority は共有 exact parser を通る (`tools/dev_wave_land.py:586-600`) が schema 値や型までは見ず、最終 land は必ず完全検証を行う (`:3097-3104`)。

`cat-file -t` は tree fixture で実際に拒否可能なので恒真ではない。一方、rc pin は現 producer が rc を `{0,1}` に限定し (`tools/check_acceptance_reds.py:1264-1269`)、分類もその rc から生成する (`:1379-1396`, `:1563-1582`) ため、現 producer に対しては発火せず、crafted receipt・競合差替え・将来 drift への防御深度である。

本 wave は runner と checker を変更していない。待ち手の `tested_main` は lease claim 時の main、`tested_tip` は走行後 fingerprint の HEAD から取る (`tools/dev_wave_wait.py:3318-3342`)。land は request の両 SHA を固定して検証する (`tools/dev_wave_land.py:2982-2983`, `:3097-3104`)。したがって gate 自体は本 wave の child-green または非帰属 receipt を過剰拒否しないが、must-fix 1 の赤を残したままでは receipt に到達できない。

## 総括

must-fix は fixture 更新漏れと、runner path 欠落の retryable 誤分類の 2 件。  
署名 1〜7 は待ち手と land の双方で実装され、署名より広い追加受理は見つからない。  
ただし child-green の runner 改変、rc=0 の PASSED 証明欠落、同一 user の receipt 偽造は裁定済み残余として実在する。  
実測赤 3 件は fixture の誤りであり、期待値を緩めず fixture に同一 runner blob を追加すべきである。  
pytest は実走しておらず、緑は主張しない。