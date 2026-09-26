## 所見

**RA-01（should）** — V28 の `reached` と `changed` は同じ分岐で連続加算されるため、構造上つねに等しくなります。[V28 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/patches/broken-si-read-uncommitted-version.patch:53)。影響: 検出表の二つの値を独立した発火証拠として読めません。推奨: 結果の説明に等値の理由を明記してください。

**RA-02（nit）** — V28 は status と cstamp を別々に読むため、並行 commit 中の `reached` は「元コードなら必ず飛ばした」という厳密な反実仮想にはなりません。[V28 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/patches/broken-si-read-uncommitted-version.patch:54)、[元コード](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2847-si-v2/external/ccbench/cc/si/transaction.cc:154)。影響: 境界付近の発火件数の解釈に限界があります。推奨: 診断値を版選択時の観測値として記述してください。

そのほかに静的検査で示せる must-fix はありません。V28 は「status が適格なら snapshot を満たす版で停止、不適格なら次へ」という元ループから status 除外だけを取り、snapshot 不適格時の `prev_` 移動と null 終了を保持しています。V29 は committed 後の abort だけを外し、inflight 分岐、CAS 再試行、元 abort 側の版再利用を残しています。両 patch の無効枝は v2 後の元コードを保持し、site 数は 7・5 で登録値と一致します。

v2 の C 行は指定の 7 field、R/W 件数は出力元コンテナのサイズ、E 行は R/W の後です。`thid_` は数値へ変換され、abort 経路は emitter に入りません。診断の印は `begin()` で戻り、`committed` は `commit()` の成功側だけで加算されます。通常終了では worker を join して main から戻るため、static destructor の出力経路とも整合します。

gate 差分は si の登録、witness、件数、既定値と固定表の更新で、既存の受理述語・供給経路を変えていません。起動器の V2 patch 列は v2 のみで、J1・J2 の cell、gate 呼出し、診断行の正規表現も事前登録に合致します。S1・S2 は各取引が一つの key だけを扱い、S1 の RMW は同じ key の R を消すため、対照の巡回 0 という期待は source から支持されます。S2 の integrity 0 は実測で確認すべき期待値であり、裁定どおり対照が外れた場合は変異の帰属を止める扱いが適切です。

## GO / NO-GO

**レビュー判定は GO。** 静的検査で J1・J2 を止める実装誤りは見つかりませんでした。検出表の確定と受入は、本走・焦点 test・変異 matrix の結果待ちです。

## 総括

指定された資料と commit 差分を読み取り専用で照合しました。テストと build は実行していません。