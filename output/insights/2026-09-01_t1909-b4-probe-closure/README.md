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
|`acceptance-child-1.log`|受入全走 attempt 1 の子 log。19033 passed / 5 failed / 21 errors。赤 26 件はすべて本 wave が触っていない `test_codex_reasoning_ab.py`|
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

## 受入が緑にならなかったこと

受入全走 attempt 1 は `19033 passed` の一方で `5 failed, 21 errors` を返した。
赤 26 件はすべて `orchestrator/tests/test_codex_reasoning_ab.py` に集中し、本 wave が
1 度も触っていない file である。本文は 3 種である。21 件 (error) と 1 件 (failed) が
`ValidationError: session 019fac6b-... rollout count is 0, expected 1`、
残る 4 件 (failed) が POS session の固定絶対 path
`/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-....jsonl`
への `FileNotFoundError` である。**後者は fixture を経由しない直接読みなので、
fixture だけを直しても掛からない。** pin された 5 session は全件消えており、
現存 7169 rollout を 5 つの期待 SHA で全件 hash 照合しても 0 件だった。

**決定的な赤である。** 単独再走でも同じ 26 件が同じ本文で再現し、独立 clone 上の local main
単独でも同一の 26 件が同一本文で再現した。原因は repo が pin する過去の codex rollout が
`/home/SFC/tanab/.codex/sessions` に 1 件も無いことで、本 wave の差分からは到達できない。

処置は次のように決まった。**D1144 に従い wave は停止しない。** ただし land には緑の受入
受領証が要るので取り込みもしない — 「止まらないが land もしない」形で、land 以外をすべて
完了させて修正の着地を待つ。修理は編集面の衝突を避けて並行セッションへ一本化した。

hold も復元も採れない。`orchestrator/tests/flaky_test_holds.py` は `green_observation` の
非空 (115 行) と `green_run_count >= 1` (135-139 行) を必須とし、この 26 件は素材消失後に
一度も緑になっていない。rollout の bytes は `~/.codex/sessions`、
`~/.codex/thread_history_1.sqlite` (当該 thread の行は全テーブル 0、最古 thread は 8 月中旬)、
repo、job dir、home のいずれにも残っていない。

**これは事故ではなく運用である。** home の会話ログは容量制限のため定期的に削除される。
剪定窓は実測で約 32-34 日、次の境界では `2026/08/01` の 173 件が落ちる。
したがって復元も、消える場所への pin 張り替えも、同じ窓に繰り返し轢かれる。

**本 wave は local main へ取り込んでいない。** 受入 receipt は発行されていないので、
この tip を land する経路は開いていない。

### 修理側の到達点 (2026-09-01、並行セッション経由。本 wave は同 file に触れていない)

- 26 件の赤は解消した。所有者の焦点走は `602 passed / 27 skipped / rc=0`。
  内訳は **25 skip + 1 pass** で、`test_real_rollout_collector_golden_is_source_bound` は
  file を読む 2 つの assert だけが条件化され、digest 照合・`_validated_usage`・
  `input_tokens` の検査は無条件で走るため緑のまま残った。被覆が 1 件助かっている。
- **ただし `_REAL_ROLLOUT` は固定の絶対 path のままで、`is_file()` による条件化だけである。**
  本 wave が指摘した「POS session を固定の絶対 path で直接読む」構造は解けていない。
  **今回 rc=0 になったのは corpus がどこにも無いからであって、path が正しく解決されたからではない。**
  実走が示したのは guard が効くことであって、path 束縛が解けたことではない。
  この構造は恒久対応の hermetic 化 (`CODEX_HOME` の引数化) へ持ち越された。
- hold の受け皿が無いのは「未採番の新種 flaky 赤」ではなく「入力が消えて恒久に赤いテスト」の方で、
  D1160 を実装しても `green_observation` と `green_run_count >= 1` が `evidence_id` とは
  独立に課されるため今回の型には効かない。ユーザー裁定へ上がっている。

