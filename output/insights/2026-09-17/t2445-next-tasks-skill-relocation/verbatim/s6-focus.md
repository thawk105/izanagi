## 所見ごとの closed / partial / regressed 対応表

`adapter` は `.agents/skills/next-tasks/SKILL.md` を指します。判定は静的な焦点再レビューの範囲です。

| 所見・確認項目 | 判定 | root cause と修正の対応・照合結果 |
|---|---|---|
| B 所見1：編集禁止条件 | **closed** | adapter L61–64 が、発火・クラス2起動手順完了後に「同終端が許す command の該当節の是正と道具追加」を明示的に許可。禁止は非発火時と許可範囲外に掛かり、許可した操作まで禁じる読みは解消された。契約 `### next-tasks` L76–77 の是正・追加・docs変更の裁定パッケージ化と一致する。 |
| B 所見2：handoff 記録義務 | **closed** | 旧版 L59 の「wave 側で回収できる情報は handoff に記録する」が、overlay 第4項の adapter L56 に復元された。既存 artifact を束ねる義務とは別に、記録義務が明記された。 |
| B 所見6：新Dの「委譲だけ」 | **closed** | fragment 決定(1) が「委譲を基本とし、Codex 固有の対応（決定2）と義務（決定3）だけを重ねる」に変更され、overlay を持つ実装と一致する。 |
| A 所見1：M5 anchor | **closed** | 生成器 L76–80 の3行の `old` を現物全文で数え、**1件**（checker L739–741）。第3行が next-tasks command を指定するため、rulings 側への誤置換原因が除去された。 |
| M3 の数値追従 | **closed** | 生成器 L52 は既に `TextLimit(5_732, 400)`。現物への一致は **1件**（checker L734）。懸念された旧値 `5_460` の残存はない。 |
| fix 子の予算・負例・needle | **closed** | 現物 **5,730 bytes** に対し上限 **5,732**、負例 **5,733**、needle `5733 bytes > 予算 5732 bytes`、独立pin **5,732** が一致。実装patchは指定2ファイルの4行変更だけで、統合commitの差分と完全一致した。 |
| A 所見4：needle の対象明記（nit） | **partial** | byte needle の数値追従は完了。ただし tests L7605–7606 の YAML／adapter needle は依然として汎用文言で、対象path・欠落literalの明記はない。元のnitは残る。 |
| 親の bytes・比率・commit の照合 | **partial** | 下記の数値とcommitは再現した。ただし `docs-fix.diff` は docs fix commit 単体の差分ではない。修正後内容は一致するが、差分の説明には訂正が必要。 |
| A 所見7・B 所見7/9の未確認事項 | **partial** | テスト・変異の実走、実際の入口選択、退避時原本との一致等は今回も証明していない。修正完了から実走成功や切替完了は導けない。 |

派生値は原データから次のとおり再計算しました。bytes は末尾LF込みです。

| 対象 | 再計数 |
|---|---:|
| adapter | 5,730 bytes |
| `agents/openai.yaml` | 208 bytes |
| 自己改善契約 | 5,997 bytes |
| next-tasks command | 26,950 bytes |
| rulings adapter | 2,999 bytes |
| 旧版複製 | 13,255 bytes |
| next-tasks 必須literal | 23件、全件存在 |

`3000 / 2999 = 1.00033344448…`、`5730 × 3000 / 2999 = 5731.910636…` なので、切上げ後の上限は **5,732**、余白は **2 bytes** です。切上げ後の実際の比率は `5732 / 5730 = 1.00034904014…` になります。

commit の解決結果：

- docs fix：`3183ec132c14cee4b89ed3e6c2dbc79a8e2c677a`
- 実装fix統合：`9889058817998a705d47d9efac64d5e710723dce`
- 先行docs：`835a2dc33bea60f6169d008dd6cc00550b1b3145`
- 先行実装：`e9a4efeaed3858acd28839f3dacc115a85f91b97`

## 新たな所見 (あれば)

**記録上のnit：`docs-fix.diff` の比較基点が説明と異なります。**

同ファイルは adapter と fragment を `/dev/null` からの新規追加として示しています。一方、`3183ec132^ → 3183ec132` は既存2ファイルの **11行追加・8行削除**です。そのため「commit 3183ec132 の差分」としては一致しません。

ただし、diff の追加内容から復元した両ファイルは、同commitのblobおよび現物と完全一致しました。修正内容の欠落ではなく、差分の比較基点・説明の問題です。

## 総括

**GO — fix後の静的な焦点再レビューとして。**

B の must-fix 2件と A の M5 anchor は閉じています。M3 と予算関連の数値も追従済みで、回帰は確認しませんでした。

残件は needle の対象明記と `docs-fix.diff` の説明訂正というnitです。テスト・変異の実走成功を認定するGOではありません。ファイル編集、Git状態変更、pytest実行は行っていません。
