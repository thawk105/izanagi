1. refuted — 差分は `dispatch_compute.py` と `test_pegasus_dispatch_compute.py` の2ファイルのみ。報告にもコミット・docs変更なしとあり、権限逸脱の矛盾はない。

2. refuted — scope外の4ファイルへの言及・変更は差分にない。追加変更は `dispatch_compute.py:144,939` と指定テストだけ。

3. refuted — 4ケースはいずれも拒否方向で正しい。

- `OTHER` → `["OTHER"] != ["SFC"]`
- 欠落 → `[] != ["SFC"]`
- `SFC`重複 → `["SFC", "SFC"] != ["SFC"]`
- `SFC`/`OTHER`混在 → `["SFC", "OTHER"] != ["SFC"]`

正例は `SFC` 1件で、既存の `assert DC._accounting_present(...)` と整合する。既存のID不一致・必須field欠落ケースにも正しいSFCを補っており、理由の混同はない。

4. refuted — lens B が挙げた4経路は既知のscope外残存であり、実装子の「変更なし」という申告と矛盾しない。新たな波及先は差分から確認できない。

5. real（軽微、DW-M01記録の説明不整合） — M1〜M4はいずれも実際の `dispatch_compute.py:939` の条件式へ適用可能。ただし M2 の「混在行だけが新たに通る」という説明は不正確で、`DEFAULT_PROJECT not in findall(...)` 変異なら重複SFCケースも誤受理する。変異自体は重複・混在ケースで検出可能。

## 総括

blocker級の実装問題はない。差分は2ファイル内に閉じ、正例・拒否例とも意図どおり。唯一、M2変異の「混在だけ」という記録が重複ケースを見落としており、DW-M01記録の補正が必要。