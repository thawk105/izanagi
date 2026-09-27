## 所見

1. **nit — `orchestrator/tests/test_campaign.py:3178`**
   保持区間を出た後の直接再取得と、直後の引数なし `run()` は、どちらも解放後に取得できることを測る。引数なし経路が自分で取得する契約は、同じ test の `run()` が `CampaignBusy` になる箇所でも確認できる。
   **成果物影響:** 直接再取得を削っても、B-4 の記録や契約の検証結果は変わらない。
   **推奨:** 直接再取得の 2 行を**削除**。

2. **nit — `orchestrator/tests/test_p3_s4_loop.py:7235`**
   `Path(path).is_file()` は、直後の `Path(path).read_bytes()` と重なる存在確認。
   **成果物影響:** 削っても checkpoint の保存内容と保持区間の検証は変わらない。
   **推奨:** `is_file()` の assert を**削除**。

## 総括

**GO（静的レビュー）。** D1346 に必要な認可・preflight・実行・checkpoint の保持区間と、`main()` からの handle 受け渡しが差分に含まれる。producer と driver の path 一致も test で直接確認している。これにより、実行中の arm を終了済みとして不可逆な `missing` に記録し、block score と verdict を変える経路を塞ぐ意図に沿う。`main()` の字下げ変更は候補 driver の復帰まで保持するために必要な範囲。変更は指定の 5 ファイルで、空白差分を除く production は約 55 行、test は 266 行と上限内。

**削除推奨:** 上記 2 件の重複 assert・取得のみ。テストと build は指示どおり実行していないため、緑の判定は親の実測に委ねる。