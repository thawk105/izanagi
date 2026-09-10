# 段 6 fix 第 1 巡 — 親の裁定

段 6 敵対レビュー 2 本の所見を親が real/refuted・採否へ裁定した結果である。実装子はこの文書を
正本とし、レビュー本文は根拠として読む。

## 親が確認した事実

- 焦点走は緑である。変更した test file 単独走 = 170 passed。consumer 7 file =
  872 passed / 9 skipped。**回帰は出ていない。** 所見はすべて「検出力」と「発火条件」の問題である。
- liveness レビューの H2 判定 (production の oracle 依存検証が成立しない) は、**本 wave が
  作った欠陥ではない。** `SHA256SUMS` を production 側で生成・配置する経路は本 wave の変更前から
  存在せず、oracle 側のコードは本 wave で 1 行も変えていない。したがって「元から dormant な経路に
  禁止を載せた」状態であり、**新たに壊したものは無い。**

## F1 (must-fix) — 発火条件を fail-closed にする

**出所:** liveness 所見 1、regression 所見 3、親仮説 H1。

現状は `build_fn is buildcache.build_v2` が真のときだけ capability を渡す。偽なら拒否ではなく
**禁止が黙って消える**。これは fail-open であり、ユーザー裁定の「fail-closed で実装する」に反する。

**要求する性質:** dependency binding を持つ `sort_best` cell の build は、post-oracle capability を
伴うか、さもなくば **build を実行せずに `FloorCampaignError` で拒否される**。

- capability の構築は builder の同一性で条件付けない。無条件に構築する。
- exact な `buildcache.build_v2` でない builder が dependency-bound `sort_best` に与えられた場合は、
  build 呼び出しの**前に**明示的な例外で拒否する。
- build 呼び出しの直前に、dependency-bound `sort_best` なら capability key が実在することを
  要求する実行時 gate を置く。**Python の `assert` は使わない。**

**受理:** dependency-bound `sort_best` の build が実行されたなら、その呼び出しは post-oracle
capability を伴い、builder は exact な `buildcache.build_v2` であった。
**拒否:** builder が exact でない、または capability が組み立てられないなら、build は 1 度も
呼ばれず `FloorCampaignError` が送出される。
**通る正例:** 既定の official/pilot 経路 (builder が exact `build_v2` に正規化される) は
従来どおり build まで進む。

## F2 (must-fix) — 材料検査は oracle 自身の検証器を使う。自前で書き直さない

**出所:** liveness 所見 2 (`.git` の扱いが oracle 側と build 側で食い違う)、liveness 所見 3
(未宣言 archive の特例受理)。

現在の実装は build 側に独自の inventory 規則を書いており、`.git` を除外し、archive を宣言の
有無にかかわらず受理する。一方 oracle 側の規則は `.git` を含み、宣言集合と実在集合の exact 一致を
要求する。**同じ規則の実装が 2 つあるため食い違い、両方を同時に通る入力が存在しない。**

**要求する形:** build 側の材料検査は、oracle が使っているのと**同一の検証関数**を呼ぶ。
規則を再実装しない。`sort_swo_oracle` の依存検証入口を (必要なら関数内 import で) 使い、
その戻り値と oracle receipt の manifest 権威を照合する。

- 未宣言 file の特例受理を削除する。archive の特例も削除する。
- HEAD と archive sha256 の照合は、manifest 権威とは別系列の追加条件として残してよい。
- **恒真化しないこと:** 期待値を live tree から生成しない。期待値は oracle receipt 由来の値と
  呼び手が渡した束縛だけから来る。

**受理:** 検査が return したなら、oracle が使うのと同一の規則で材料が検証され、その manifest 本体
hash は oracle receipt の値と一致していた。
**拒否:** oracle の規則で材料が検証できない、または manifest 本体 hash が receipt と違うなら、
`cmake` を 1 度も起動せず例外が送出される。
**通る正例:** oracle が PASS した直後の未変更の材料は、build 側検査も通る
(**同一規則なので、この含意が構造的に成立することが F2 の要点である**)。

## F3 (must-fix) — production 配線を守るテストを足す

**出所:** regression 所見 3、liveness 所見 4。

現在、`s8b_floor_campaign.py` の capability 配線を丸ごと削除しても追加テストは全部緑になる。
配線を守るテストがゼロである。

`orchestrator/tests/test_s8b_floor_campaign.py` へ次を足す。

- dependency-bound `sort_best` で **exact でない builder は 1 度も呼ばれず拒否される**
  (呼び出し回数 0 を要求する)。
- 既定経路で **exact builder へ post-oracle capability が渡り、その値が oracle receipt 由来の
  literal と一致する** (テスト側は literal で期待値を書く。production の射影関数を呼ばない)。

## F4 (must-fix) — 変異 M4 と「manifest 本体 hash 照合だけの削除」を殺せるようにする

**出所:** regression 所見 1、regression 所見 2。

- **M4:** identity への policy 配線を削除する変異が、現行テストをすり抜ける。
  同じ base・receipt・archive で capability 無しの build を先に seed し、同じ材料の
  capability 付き build が **必ず cache miss する**統合テストを足すこと。
- **manifest 本体 hash 照合だけの削除:** tracked file とその `SHA256SUMS` の該当行を
  **同時に**書き換えた自己整合的な材料を作り、それが拒否されることを要求する負例を足すこと
  (per-file hash 検査だけでは通ってしまうため)。

## F5 (must-fix) — 正例の自己観測を外す

**出所:** liveness 所見 4。

追加テストの正例 fixture が、live tree を自分で hash してその値を期待値にしている。
これは「観測値と観測値」の比較であり、配線違いを検出できない。**期待値は fixture が書いた
literal から来るようにする** (fixture bytes を先に literal で定義し、それを tree へ書き、
期待値には literal を使う)。

## 実装しないもの (再確認)

X1 (再生成経路)、X2 (mimalloc/googletest)、X3 (cross-base hit の historical argv)、
X4 (process 間排他)、X5 (resume / durable manifest migration) は本 wave の scope 外である。
liveness 所見 5 は X5 そのものなので裁定済み・実装しない。

## H2 の扱い (実装しない・記録する)

production で SWO oracle の依存検証が成立しないこと (指紋一覧の生成器が存在せず、`.git` の
扱いも噛み合わない) は、**本 wave の変更前から存在する別欠陥**である。本 wave では実装せず、
worklog と裁定パッケージへ記録する。

F1 と F2 を実装すれば、この dormant な状態でも次が成立する。

- 禁止が黙って消えることはない (F1 により、capability が無ければ build が止まる)。
- 禁止が発火したときの検査は、oracle と同一規則で行われる (F2 により、両者の受理集合が
  構造的に一致する)。
