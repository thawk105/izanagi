---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-29
wave: dev-wave-cicada-certified-evidence-design
seq: 2
---

## {{D:cicada-certified-evidence-design}}. Cicada を certified まで上げる記録は B (読み束縛)・U (公開の双方向照合)・P (置換保存) の 3 面とし、可視区間・設置順・rts の順序・read-only 境界は帰属の診断とする。実装するかはユーザーの判断に返し、推奨は判定器を変えない中間案 M とする

**決定:** (一次資料 `output/insights/2026-09-29/cicada-certified-evidence-design/README.md`)
1. Silo / MOCC の certified は「観測した実行の依存グラフが非巡回」に「trace が実行を忠実に写す」証拠を足したものと整理する。Cicada で同水準に要る忠実性の証拠は B・U・P の 3 面である。B = 読んだ版 object が read 登録から tx の終わりまで回収・再利用されない。主案は、退役・再利用・返却を版 object ごとの消えない事象として TRACE 専用の台帳 (版の外) に積み、tx の終わりに台帳だけで照合する (版 object を再参照しない)。代替案は版の中の TRACE 専用の世代番号で、項 4 の範囲でだけ成り立つ見込みである (項 4 の条件付き)。どちらを採るかは実装 wave の段 4 で決める。どちらでも版の wts を読み直す現行方式は置き換える。U = 設置・公開した版の集合と W 行の集合の双方向照合 (公開直前の status が pending であること、wts = C 行の版を含む)。P = write set の `partial_sort` の置換保存 (Silo の P を移す)。これに加えて API との双方向照合 (read 側 = 公開 `read()` の成功を read set 登録と独立に捉え、件数でなく呼び出し単位で、返した分岐 (再読 / read-own-write / 外部) ごとに key・返した body・対応する read set / write set 要素を照合し、どの外部 read にも対応しない余分な read set 要素も拒否する。scan は返した要素単位の別設計、write 側 = I) を置き、中間案 M では read 側を入れ、certified 化では両側を必須にする。母集団を `read_internal` を通った呼び出しで決めない (迂回した読みが漏れるため)。
2. 各 read の可視区間・書き込みの設置順・rts の更新と検証の順序・read-only snapshot の境界は、記録した履歴の 1SR には不要で、帰属 (規律 3) の診断とする。主張は観測した読みについての 1SR に限り、終状態と、Cicada が自分の規則どおりの版を選んだこと (版選択規則への適合) は主張しない。規則に反する選び方は巡回を生んだときだけ検出される。
3. 照合回数の自己申告と R 行数の突き合わせは発火の証拠と呼ばない (恒真)。発火の証拠は各分岐の壊し patch だけとする。
4. 対象は YCSB の point read / update、`REUSE_VERSION=1`、`INLINE_VERSION_OPT=0`、`group_commit=0` に限る。この範囲では走行中に版 object を解放する経路が読解と検索で見つからず、B の代替案 (版の中の世代番号を tx の終わりに読む) でも解放済み memory を読まない見込みである。代替案を採るなら、実装 wave で解放経路が無いことを確かめ直すことを採用の条件にする。
5. 3 案 (今のまま / 中間案 M / certified 化) を並べ、中間案 M (B・U・read 側の照合を out-of-tree 計装に足し、repo 外起動器の合否に入れる。判定器の production と campaign は変えない) を推奨する。実装に進むか、M の証拠を満たした variant の性能値を論文で格上げしてよいか、certified 化の着手条件は、ユーザーの判断に返す。

**理由:**
- VHash の U0 (前進を回収境界へ反映) の典型的な失敗 = 既読版の早すぎる回収・再利用は、今の検査器の盲点で、構成 E の仮裁定 P5 で実物が起きた (D2295)。M はこの盲点を直接閉じる。
- 多版の履歴は、ある 1 つの版順で直列化グラフが非巡回なら 1SR である (MVSG 定理)。判定器は wts の数値順を版順に使うので、reads-from が忠実で W 行が公開版をちょうど表せば、記録した履歴の 1SR を言うのに各 read の選び方を個別に再証明しなくてよい (ただし版選択規則への適合は言えない)。
- 論文に書ける文は certified 化と M でほとんど変わらない。どの案でも「実装は一般に serializable を保つ」は書けない (D2292 は小モデル仕様 v1 が対象)。certified 化は判定器の 7 file が campaign lock の 96 path closure に入っているので lock の再批准・fixture・変異・受入を伴い、今それを要する campaign の登録が無い (DW-G04)。
- 段 3 の 2 レンズ (実装する側 / しない側) が独立に中間案を推した。

**却下した選択肢:**
- 親 brief の仮置き「B・U・P + 判定器の protocol 別の門を今実装する (certified 化)」 — 論文の文の増分が小さく、隠れた費用が大きい。
- 照合回数の自己申告を発火の証拠にする — 両方が同じ read set から作られるので恒真。
- U を W 行 → 公開の片方向照合にする — 公開後 emit 前に write set から要素を落とす variant で巡回が消える。
- `.cc` に薄い wrapper の emitter を置いて文面検査を満たす — 検査の実体が header にあるなら証拠は飾りになる。header を含む source snapshot か site ごとの評価を先に設計する。
- 可視区間などの診断の行を必須にする — 1SR に不要で、未知の行種別は判定器が ParseError にするので判定器の変更を先に要する。

**ユーザー不在時の決め方:** 背景 job でユーザーが応答しない間に、設計の整理 (項 1〜4) は段 3 相談 2 本の所見を材料に親が決めた。実装の可否 (項 5) は決めず、推奨として返す。
