## 受理集合と拒否集合の境界

以下、`E`＝`orchestrator/campaign/reflux_result_evidence.py`、`F`＝`orchestrator/campaign/reflux_formal_consumer.py`、裁定ファイルは指定の `verbatim/` 配下を指す。

**受理集合：** plan:17 の述語は、両 layout の exact 型に加え、メタクラスの等価比較でどちらかの型と等しいと判定される別型も通す。

**拒否集合：** 同述語は、両型との同一性・等価比較がともに成立しない型を拒否する。

**[real／must-fix M1] 集合所属検査を exact-type 同一性と扱っている。**
`type(layout) not in (CampaignLayout, ExplorationCampaignLayout)` は `is` だけの検査ではない。独自メタクラスの `__eq__` を持つ subclass／同形 object が通過し得るため、plan:36–38、brief:6・12 の宣言と食い違う。両 gate に同じ式を置くので、後段 gate も防壁にならない。公開 projection も E:534 から内側 gate（E:447）へ直接到達する。

リポジトリを読み書きしない Python の最小再現では、別型について `tuple gate accepts: True`、`identity gate accepts: False` を確認した。producer の発行実走ではない。

修正は両箇所を次に揃えればよい。

```python
if type(layout) is not CampaignLayout and type(layout) is not ExplorationCampaignLayout:
```

既存の subclass／duck 負例に、型の等価比較を上書きするケースを加える。

**放置時の成果物影響：** 証拠発行・公開 projection の型受理集合が裁定された二型を越え、従来型 gate で拒否した object も、残りの入力が有効なら発行処理へ進める。

**[refuted] 明示的な `isinstance`／属性検査への変更はない。** ただし上記の等価比較による緩和は残る（plan:17・23、E:447・1213）。

## 裁定との整合 (D2018/D2044/D1747/D123)

**[refuted] Q1 以外の production 機構への拡張はない。**
D2044-item2:5–6 が解除したのは探索 layout の追加であり、D2017-D2018:45–52 の台帳遷移・専用入口・completion は解除していない。plan:174–182 は schema、path 導出、consumer、Q2〜Q4 を変更対象から外している。M1 の追加受理だけが、この境界を越える。

**[refuted] producer と consumer の root 計算に、本 wave で別の導出実装を加える必要はない。**

- producer：`abspath(layout.root)`（E:1094）。
- loop：`exploration_campaign_layout(cid, output_root)`（loop.py:452・534・542）。
- consumer：`abspath(exploration_campaign_layout(planned_identity, campaign_output_root).root)`（F:916–922）。

したがって、**同じ output base と `cid == planned_campaign_run_identity`** なら、双方は `<base>/exploration/campaigns/<identity>` で一致する（layout.py:589–597）。

本 wave では constructor・root 包含・探索配下の content 参照を保てばよい。33 本の planned identity と実行 identity の結線、lock 内の origin binding、sealed member との対応は後続側であり、plan の探索統合正例だけでは証明しない。consumer は引き続きそれらを検査する（F:926–956・969–981）。

**[real／nit] D123 (4) の引用は不正確。**
D123-item4:5–7 は「型分離は別裁定へ送る」であり、継承禁止を直接決めていない。brief:12 は延期記録と決定を区別すべき。現物では両 class に継承関係がなく、plan も変更しない（layout.py:190・541）。

**[unverified／nit] D528 (9) の逐語との一致は未確認。** 指定射影には本文がなく、brief:12 の引用を裏付ける材料はない。

## 規律 2 への影響

**[real／must-fix] 型拒否の弱化は M1 のとおり。**

**[refuted] それ以外の列挙された検査を迂回・弱化する経路は、この差分では作らない。**

根拠は、変更対象が二つの型述語・import・注釈に限られ、次が維持されること。

- root 束縛：loop.py:303、E:1101–1113・1278。
- capability・contract・receipt：E:1220–1254。
- WAL・trigger・結果導出：E:452–503・1323–1329。
- record 組立・導出 path 照合・参照検査：E:1369–1385・1037–1046。
- create-only：E:1185・1025。

検疫・auditor veto・condition gate を省く新しい起点入口も追加しない（plan:177–180）。loop の評価呼出しも既存のまま（loop.py:782）。これは各上流 gate の全経路を再監査したという意味ではない。

## 親の実測値と一般化の検査

**[real／nit] 探索 root 拒否の維持は、親 probe 自体では確認できていない。**
brief:6・8 の探索入力は型 gate で止まるため、E:1110 の発火を観測していない。維持はコード上では支持され、plan:67 の直呼び負例で実装後に確認する構成になっている。

**[real／nit] 「record bytes 不変」は対象を限定する必要がある。**
探索では発行前後の bytes 比較が成立しない。また root が変われば content ref の path、projection bytes と digest、record bytes が変わる（E:1165–1173・1291–1317）。「既存入力に対する生成規則と schema は不変」とした plan:182 は適切で、brief:6・10 の無限定な表現を訂正すべき。

**[unverified／nit] pin 閉包への hit 無しは、probe が支える結論ではない。**
brief:10 の根拠は別途の文字列検索という申告である。指定資料には閉包・登録簿を網羅した検索結果がなく、文字列 hit の不在だけでは間接参照まで否定できない。pin が実際に存在するとも判定していない。

## file:line と前提の誤り

**[refuted] 主要な関数名・変更前行番号のずれは確認されなかった。**
E:34・444・447・1089・1196・1213、loop.py:285・452、layout.py:540・589、および両 test helper／正例の指定位置は現物と一致する。

**[real／nit] brief:15 の変異説明は不十分。**
外側 E:1213 だけを緩めても、内側 E:447 が同じ subclass を拒否する。「subclass 負例が単独で kill」は照準を限定しなければ成立しない。plan:157・166 は公開 projection への再照準で訂正している。

**[real／nit] root 変異を外す理由も brief:15 より plan:168 が正確。**
別の official 負例が kill することではなく、同じ入力を loop.py:303／E:1173 が重複して拒否することが単一理由性の問題である。

D123 の誤引用と bytes 不変の前提誤りは前節のとおり。

## scope の逸脱と不足

**[refuted] 仮想リスク向けの新しい production gate・台帳・一般化はない。**
plan:5・174–182 は局所変更に限定され、負例は D2044-item2:5–6 が明示要求した拒否境界の確認に対応する（DW-G05:7–9）。

**[real／must-fix M1 に統合] 拒否述語と負例の同時確定は、型同一性について不足する。**
plan:64–70 の通常 subclass／通常 duck 負例では、`is` と等価比較の差を検出できない。M1 の述語訂正と負例追加は、明示された exact-type 要件を満たす局所修正である。

## 総括

**must-fix 1 件：両 gate を等価比較から明示的な型同一性検査へ直し、その差を検出する負例を追加する。** root・schema・consumer・Q2〜Q4 に追加変更は不要。pytest・build・producer 発行は未実行であり、確認した実走は Python の比較意味論の最小再現だけである。

plan は全面的に作り直す必要はないが、M1 を局所改訂してから author 段へ進めるべきである。