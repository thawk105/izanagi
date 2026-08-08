---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: dev-wave-t529-activation
seq: 1
title: [T-529] 契約世代の活性化権限を実装した — 第 2 世代は登録のみで活性化していない (コード + docs、受入 7345 passed / 20 skipped、変異 2 走で未登録 SURVIVED 0、branch worktree-dev-wave-t529-activation)
---

## 本文

- **裁定どおり「活性化権限の機構」を入れ、「pegasus 第 2 世代の活性化」はしていない。**
  第 2 世代は registry へ登録したが、初期 activation record (serial 1) は両 env とも
  第 1 世代を選ぶ。`lookup("pegasus")` の返り値は land 前後で不変である。活性化そのものは
  certified 計測の基盤較正を差し替える行為なので、裁定パッケージへ返した。
- **段 1 の生死実験がこの wave の形を決めた。** 第 2 世代を実編集で登録して fuse を外すと、
  committed な floor protocol は historical lane では受理され live admission では拒否される。
  [T-615] の 2 lane 分離は効いており、壊れるのは live 入口だけだと特定できた。同時に
  「登録すると `sequence[-1]` が黙って current になる」ことが判明し、active pointer を
  activation record 由来へ束縛する改修が必須になった。
- **段 3 が親の暫定裁定 (P2) を反証した。** 実在する第 2 世代の素材から作った serial 2 でも、
  一時 record である以上「レビュー済み経路に残る永久 fuse」とは区別できない。本 wave は
  「活性化を実証した」とは名乗らず、正例を `DW-G04` の発火証拠に数えていない。
- **[T-627] の見送り裁定を守って遷移述語を入れなかった。** 段 2 プランは「本 wave で schema が
  確定するから停止条件は解消する」と主張したが、段 3 レンズ A が反例を構成した — 各 env の
  delta だけを見る実装は、プランのテスト表を全部通ったうえで `(+2, −1)` の相殺ケースを受理する。
  親が独立に裏取りし、[T-624] wave と同型の「検出力ゼロの gate」を land する寸前で止めた。
- **親の段 4 の理由づけに誤りがあり、段 6 が訂正した。** 親は「head 定数を Python 側に置けば
  既存の source binding が効くのでレビュー済み commit への束縛が閉じる」と書いたが、その
  source binding は汎用の certified 経路からは呼ばれていない。head pin 自体の効果は残るが
  **「レビュー済み commit に束縛した」とは名乗れない**。既存の穴と同じもので本 wave が
  開けたものではないため scope 外に裁定した。
- **receipt を 1 度作り直した。** 最初の実装は認可関数が自分で receipt を発行して自分で照合する
  恒真な gate だった。呼び出し側が保持して渡す「認可済み型」へ設計し直し、素の契約・複製・
  改竄・古い receipt・別 PID・fork 継承値を拒否する形にした。fork 経路 (T126) は子側で取り直す。
- **fix 子が 1 巡空振りした。原因は親の scope 記述。** 「入口の最初の書込み境界に receipt の
  検査を新設しない」と書いたつもりが、「必須引数を満たすために呼び出し側が receipt を渡すこと」
  まで禁じたように読める文になっていた。子は矛盾を検出して 1 行も書かずに停止し、必要な配線の
  一覧を返した。親が境界を再裁定して再投入した。fix は計 6 巡 (うち 1 巡は上記の空振り、
  1 巡は焦点再レビューが見つけた regression の修理)。
- **焦点再レビューが、受入全走では見えない regression を 1 件見つけた。**
  `test_campaign.py` は pytest 不在でも素の Python で走る二重 runner 契約を持つが、
  fix 第 5 巡が pytest を import 必須にし、認可の初期化を autouse fixture 内だけに置いていた。
  pytest 経由の全走は緑なので検出できない類である。最終巡で回復した。
- **変異は 2 走。未登録の SURVIVED は両走ともゼロ。** run 1 の MISMATCH 3 件は gate の失敗では
  なく親の node 帰属の誤りで、node を訂正した run 2 で 3 件とも KILLED になった。
  head pin の serial 検査と state hash 検査は互いを mask していたため、`DW-M02` に従って
  両層同時変異を追加登録した。production 層の末尾削除 node だけは、chain が 1 record しか
  ないため「末尾削除 = 空 chain」となる過剰決定で、`DW-M03` に従い単独変異の証拠から外した。
- **pin 閉包の検索で tool の取りこぼしを実測した。** 同じ hash を repo root から `grep -rl` すると
  tracked file を 1 件落とすが、`git grep -l` と部分木指定の `grep -rl` は拾う (再現性あり)。
  親 brief の「4 件」は誤りで正しくは 5 件。段 3 レンズ A が独立に検出した。
- **環境ゴミによる偽赤を同定した。** `/tmp/.git` という空 directory が 7/28 から残っており、
  一時 directory の祖先に `.git` があるかで「repository 外か」を判定するテスト 5 件が
  ローカル実行で必ず落ちる。計算ノードでは出ない。**自分が作ったものではないため削除していない。**
- **計測基盤の順番待ちで実測を 4 回取り直した。** 内訳は既知の cgroup attest race が 1 回、
  並行セッションの job でキューが埋まり待ち上限を超えたのが 2 回、`git log` / `git cat-file` の
  15 秒 timeout による偽赤 3 件が 1 回。いずれもテスト内容と無関係で、キューを空けた単独実行で消えた。
- 一次資料 = `output/insights/2026-08-08_t529-activation/` (段 1 brief、段 2 プラン、段 3 の
  2 レンズ、段 4 裁定、段 5 実装報告 2 本、段 6 の 2 レンズと fix 6 巡、焦点再レビュー、変異 2 走の台帳)。

## 次の一手差分

### 完了

- [T-529] 活性化権限の機構を実装した。bootstrap fuse を撤去し、pegasus 第 2 世代を登録し、
  activation record の chain を active 世代の正本にした。第 2 世代の活性化そのものは
  {{T:pegasus-g2-activation}} が引き取る。
  remaining: none
  base: 3c473f41b2e607bf629cb540762b2229d3caaa4bb5a107284521a0933774412a

### 更新

- [T-627] **P2・裁定済み (2026-08-07 /rulings、(c)) → 停止条件は解消、実装形の再裁定待ち**:
  no-op 拒否の述語実装。[T-529] 実装で activation record の実 schema が確定したため
  「実 schema 確定まで置かない」の停止条件は満たされた。ただし本 wave の段 3 が番号 delta
  述語の反例を再構成した (`(+2, −1)` の相殺ケースが提案テスト表を全部通る)。次点 (b) の
  「generation と contract hash の同一入力束縛」で実装形の再裁定が要る。
  base: 5fbe2b9fd40f84d42eec669d1afbae049719341ada41797609e3321aaf01b8e1

### 新規

- {{T:pegasus-g2-activation}} **P1・ユーザー裁定待ち**: pegasus 第 2 世代をいつ活性化するか。
  活性化すると committed floor protocol が live admission から外れる (親が実測)。前提条件は
  (a) silo の歴史 evidence を historical 解決へ変えること、(b) floor protocol の再発行。
  [T-139] 本走の基盤較正に触れるため単独では進めない。
- {{T:activation-receipt-entry-wiring}} **P2・ユーザー裁定待ち**: activation receipt を
  floor / oracle driver / selector / T126 の fork child / PBS wrapper の最初の書込み境界へ
  配線するか。PBS wrapper と writer は別 process のため「receipt と writer が同一 process」の
  解釈では現構造で実現不能で、durable receipt (別 wave) と併せた設計択一が要る。
- {{T:activation-issue-deploy-window}} **P2・新規**: 発行から配備までの分裂窓を閉じる。
  発行 tool は record を live directory へ公開するが head 定数を更新しないため、head 更新と
  再起動までは fresh process が fail-closed し、既存 process は旧 head で走り続ける。
  失敗方向は安全側だが quiesce/drain と atomic deployment が無い。
- {{T:activation-tail-rollback-observability}} **P3・新規**: production 層の末尾巻き戻し検査は
  chain が 1 record の間は空 chain 拒否に mask されて観測できない。第 2 世代の活性化後に
  head=2 の状態で検出力を確認する。
