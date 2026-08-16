# 裁定パッケージ — [T-1140] / [T-330] (c) / 予約照合

2026-08-16 / wave dev-wave-t1140-claim-identity / 実装差分ゼロで返す

## 何が起きたか (3 行)

2026-08-16 のご裁定 (#12・#14) どおり 3 つを 1 wave で実装しようとしたところ、
**裁定文が前提にしていた 2 つの事実が偽**だと実測で分かりました。
指示された修正をそのまま入れると、床値 campaign が 1 回で永久に使えなくなります。

## 偽と分かった前提 1 — 「claim identity を protocol 単位にすれば直る」

直りません。**床値 campaign が 1 回しか動かせなくなります。**

claim を取る仕組みは、意図的に「解放も期限切れも回収も持たない」設計です
(`campaign_claim.py:167-174` にそう書いてあります)。今は識別子が run ごとに違うので、
失敗しても crash しても次の投入ができます。識別子を protocol 単位にすると、この性質が反転します。

実測した運用の形:

| 測ったもの | 値 |
|---|---|
| 床値 campaign が使う protocol | **固定 1 本** (`floor_campaign.sh:947`) |
| 実行 mode | **pilot 固定** (`floor_campaign.sh:962-964`) |
| official mode | **無条件で拒否される** (`s8b_floor_campaign.py:342-352`) |
| これまでの投入回数 | **3 件** (うち 1 件は実ジョブ 873200.nqsv) |

床値 campaign は「同じ protocol を pilot で繰り返し投入する」運用です。
protocol 単位の永久 claim を入れると、**最初の 1 回**が — 成功でも失敗でも crash でも —
その protocol を永久に占有し、以後の投入がすべて拒否されます。
戻す手段は claim ファイルの手動削除だけで、それはこの仕組みが「持たない」と明言した経路です。

## 偽と分かった前提 2 — 「予約照合には scheduler 所有の create-only receipt が要る」

そういう receipt は**存在しません**。存在するのは submitter (投入する側) が作る create-only の
receipt です (`submit_floor.sh:466-495`)。ただし、それは無意味ではありません:

- receipt には qsub が返した job ID が入っており、計算ノード側で **`PBS_JOBID` と照合**
  されています (`floor_campaign.sh:452`)。`PBS_JOBID` はスケジューラが付けるので、
  ここが唯一の「偽装しにくい錨」です。
- さらに、**照合そのものは既に実装済み**でした — ただし Python ではなく shell wrapper の中に
  (`floor_campaign.sh:406-555`)。Python 側にも receipt を検査するコードが既にあります
  (`certified_writer_admission.py:177-204,297-381`)。

つまり「照合できない」のではなく、**「Python の leaf は wrapper の照合を信じてよいのか」**
が本当の問いでした。wrapper を通らない呼び手 (oracle driver、将来の計測 sink) には照合がありません。

## もう 1 つの新事実 — hostname 照合は authority にならない

敵対レビューが Pegasus の login ノードで実測しました。非特権のまま UTS namespace を作れば
(`unprivileged_userns_clone=1`、`max_user_namespaces=2147483647`)、
**hostname も FQDN も呼び手が自由に変更でき、boot_id は変わりません。**
したがって hostname 照合は「ずれの検出」であって「どのノードで測ったかの証明」にはなりません。
計算ノードで同じことができるかは未実測です。

## ご裁定いただきたいこと

### 問 1 — 排他の寿命 (これが決まらないと実装できません)

- **(a) 生存プロセス単位の排他**: claim に protocol の digest を持たせ、
  「同じ protocol の claim があり、その持ち主がまだ生きている」ときだけ拒否する。
  claim record には既に pid・プロセス開始時刻・boot_id・job ID が入っているので判定材料はある。
  *長所*: 二重投入を止めつつ、繰り返し投入も crash からの再投入も壊さない。
  *短所*: 別ノードの持ち主の生死は `/proc` からは判定できない。
  判定できない場合を「通す」にすると、クラスタで一番効いてほしい場面で発火しない。
  「止める」にすると (b) と同じく永久停止する。
- **(b) protocol 生涯 1 回**: 指示どおり protocol 単位の永久 claim にする。
  *長所*: 指示そのまま。実装は最小。
  *短所*: **床値 campaign が 1 回で永久に止まります。** 上の実測のとおり運用と両立しません。
- **(c) 生存判定をスケジューラに聞く**: (a) に加えて、別ノードの claim は
  `qstat` でそのジョブがまだ queue に居るかを見て生死を決める。
  wrapper には既に qstat の解析があります (`floor_campaign.sh:593-643`)。
  *長所*: クラスタ全体で正しく効く唯一の案。
  *短所*: wave が 1 本では収まらない。Python から scheduler を叩く経路の新設が要る。
- **(d) 現状維持**: F321 を開いたまま残す。

**親の推奨は (a) → (c) の順で 2 wave に分ける。** 理由は 3 つです。
(a) だけでも今日より確実に強くなる (同一ノードの二重投入は止まる) こと、
(a) は運用を 1 度も壊さないこと、
(c) は scheduler 連携という別の設計判断を含むので、混ぜると (a) の検証が薄まることです。
ただし (a) 単独で land する場合、**「protocol 単位の排他ができた」とは書けません** —
書けるのは「同一ノード・共有 out_root の範囲で二重投入を止める」までです。
別の out_root を使われると識別子を変えても排他は成立しません
(`campaign_claim.py:170-173` にそう明記されています)。

### 問 2 — 予約照合をどこまでやるか

- **(a) submitter 所有の receipt を authority として明示的に認める**:
  `PBS_JOBID` との束縛があるので恒真ではない、という理由付きで採用する。
  script SHA と nonce の照合を Python 側にも入れる。
  *短所*: 床値経路では wrapper が先に落とすので二重の検査になる。
  効くのは wrapper を通らない呼び手だけ。
- **(b) hostname だけ入れて残りは別タスクへ**: 段 2 プランの推奨。
  *短所*: ご裁定 #14 (3 つを 1 wave) の縮小になる。かつ hostname は上記のとおり authority でない。
- **(c) 予約照合そのものを保留し、問 1 だけ先に進める**。

**親の推奨は (a)。** hostname 単独 (b) は、authority でないものを authority として台帳に載せる
ことになり、今回直そうとしている恒真ゲートを 1 つ増やします。
(a) なら「wrapper を通らない呼び手」という発火面が実在するので DW-G04 を満たします。

### 問 3 — 併せて裁定が要る繰り越し

- `loop.py` の計測 sink は単独性を一度も検査しません (F322)。本 wave の scope 外としましたが、
  [T-1097] の transport 欠陥が直った瞬間に未検査の値を受理し始めます。
- `env_contract.py` は `single_process=True` と `allow_resume=True` の組合せを型として禁じて
  いません。現在の登録には無いので今日の値は変わりませんが、将来登録すると
  claim が残っている限り正当な再開が拒否されます。

## 本 wave が確定させた設計制約 (どの択を採っても効く)

1. 変異検査は「leaf 単体 / wrapper を通らない呼び手 / 実運用 end-to-end」の 3 つに分ける。
   wrapper が先に落とす入力で Python 側の新 gate を撃ったことにしない。
2. 「protocol 単位の global な排他」と表現しない。共有 out_root の範囲に限ることを明記する。
3. `s8b_oracle_driver.py` の generic な claim 取得を取り残さない。
4. hostname 照合を authority と呼ばない。ずれの検出として計上する。
5. 過剰拒否 (承認外の拒否) を検出する正例を必ず事前登録する。
