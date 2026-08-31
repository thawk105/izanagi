# 2026-09-01 [T-1909] — D1195 の逆到達閉包の検分と、第一権威点の反射性の修復

authority: none
default_effect: no-state-change

B-4 事前登録 §5.1 (ii) の非標本 probe について、D1195 が要求する形
(3 権威点からの逆到達閉包で生成経路の不在を導き、完全性は主張しない) が
実際に成立しているかを検分し、成立していなかった 2 点を直した wave の素材。

実装は `orchestrator/campaign/p3_b4_wiring_probe.py`、検査は
`orchestrator/tests/test_p3_b4_wiring_probe.py`。機構そのものは T-1769 wave が
2026-08-27 に D1171 として着地させており、本 wave は新設していない。

**本 wave は §5 の欄を 1 つも埋めていない。** 事前登録は発効していない。
発効を止めているのは D1195 の機構の不在ではなく、§5.1 (i) の先行 freeze
(候補集合・exact command・証拠 path と hash・0 件/複数件の決定規則・記入者とレビュー者) の
未充足である。人間の指名を含む。

## 中身

|path|内容|
|---|---|
|`mutation-spec-probe.json`|観測走の登録 (全件 SURVIVED 期待で観測 node を集める)|
|`mutation-ledger-probe.json`|同結果|
|`mutation-spec.json`|本走の変異事前登録|
|`mutation-ledger.json`|本走の結果 (独立 clone を `--source-repo` に渡した取り直し。baseline 緑・KILLED 3/3・期待 node 完全一致・MISMATCH 0)|
|`mutation-ledger-shared-tree-red.json`|本走の 1 回目。変異結果は同じく完全一致だが、走行中に別 wave が local main を進めたため wrapper が rc=125 (共有木の観測 bytes が変化) を返した記録|
|`mutation-spec-prefix.json`|修正前 HEAD への同一変異の登録 (DW-M08 の新旧両走)|
|`mutation-ledger-prefix.json`|同結果 (MWA = SURVIVED。新しい assert だけが検出することの実測)|
|`verbatim/`|段 1 brief、段 2 プラン、段 3 敵対相談 2 本、段 4 裁定、段 5 実装報告、段 6 レビュー 2 本|

## この wave が実測して訂正した事実

- **3 権威点の負例は同型に見えて、第一権威点の 1 本だけ拘束が欠けていた。**
  他の 2 本は権威点自身が遮断目録に在ることを assert するが、第一権威点の 1 本は
  下流の `pipeline.evaluate` しか見ていなかった。実 producer 直接呼出しの負例 9 本にも
  第一権威点は入っておらず、証拠 schema 検査は種の**個数**しか見ない。
  第一権威点を遮断目録から落とす回帰は、どこにも掛からず生存していた。
- **証拠の scope 文言が導出より広かった。** 「解析集合内で権威点に到達する関数はすべて
  閉包に入る」と無条件に書いていたが、閉包は静的に解決できた呼び出し辺からしか導かれない。
  目録構築は閉包へ入った symbol の未解決 binding しか検査しないため、解析集合の内側にいて
  実際には権威点へ到達する未解決 caller は、閉包にも検査にも入らない。
  **ただし生成は逃げない** — 3 権威点自身が遮断目録に入るので、未解決 caller が動的に
  権威点を呼んでも権威点の入口で遮断される。過大なのは文言だけである。
- **D1171 が却下した恒真が検査名に再発していた。**
  `_load_runtime` が preflight の各 name を import して `runtime.modules` を作るため、
  その 2 つの集合の一致は構成上必ず成立する。それを runtime import 閉包の被覆と
  称していた。名前と docstring を実際に検査している内容へ狭めた。assert は変えていない。

## この wave が閉じないこと

- **閉包は閉じていない。** 完全性は主張しない。解析 module 集合の外、3 権威点のいずれにも
  到達しない生成器、および解析集合の内側でも呼び出し束縛を静的に解決できない caller は、
  この層では覆わない。**閉包の外に経路は残りうる。**
- **不在の主張は全件検索の範囲でだけ成立する。** 本 wave が「無い」と書いたものは、
  切っていない検索で件数を数えた範囲のことであり、検索式が捉えない別名・別表現までは覆わない。
- **後発の B-4 producer は解析集合の外にある。** 解析集合は module-level import の推移閉包で
  決まり、関数内 import を追わない。これは明記済みの除外の内側であって、本 wave は
  この境界を動かしていない。
- **未解決 caller を fail-closed で拒否する案は採らなかった。** 受理集合を縮める変更であり、
  D1195 が選べと定めた「範囲を明示した主張」より重い。この判断は本 wave の decisions に残した。
