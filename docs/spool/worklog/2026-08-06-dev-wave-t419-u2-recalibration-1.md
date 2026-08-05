---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-06
wave: dev-wave-t419-u2-recalibration
seq: 1
title: [T-419] U-2 取得サイクルの防壁を入れた — 自己整合検査を benchmark 前へ足し publish 済み bytes を独立に再読する。登録は活性化権限が前提と実測 (コード + docs、受入 6668 passed / 20 skipped、変異 10/10 KILLED、branch worktree-dev-wave-t419-u2-recalibration)
---

## 本文

- **親 brief の前提 2 件が誤っており、段 2 と段 3 が独立に是正した。**
  (a) 親は「取得経路に自己整合検査が無い」と書いたが、canonical 述語を呼ぶ gate が
  benchmark 後に既にあり、現 HEAD は自己不整合な較正を accepted で publish しない。
  純増は新設ではなく**早期化・構造化診断・policy 再束縛経路の閉鎖**である。
  (b) 親は「D176 の fuse により accepted publish receipt も取れない」と書いたが、
  publish 経路は `env_contract` を一切呼ばない。fuse が阻むのは current への活性化と pin 切替だけで、
  **取得と publish は阻まれない**。親は scope を不当に縮小しており、段 4 で戻した。
- **本 wave の到達点と未達を分けて記録する。** 到達 = 取得側の gate 群と、その変異による裏取り。
  未達 = 新較正の取得そのもの (certify job)、登録・pin 更新・例外集合の空化、
  loader self-pass、取得経路の source proof。**`[T-419]` U-2 は完了していない。**
- **登録が機械的に不能であることを実測で確定した。** `env_contract.validate_generations` は
  各 env の世代列長が 1 でなければ拒否し、D176 は活性化権限が実装されるまで 2 世代目を
  fail-closed で拒否すると明記する。旧世代の `calibration_ref` を上書きする迂回は
  D176 の眼目 (正規 publish を通らない較正を活性化させない) を壊すので採らなかった。
- **段 3 の敵対レンズが「別 job の生死 driver」を落とした。** 親は計算ノードで α probe を
  1 回走らせてから certify を投入する案を出したが、allocation・host・boot・時刻が異なるため
  後続 job の許可証にならない。新しい出力先・PBS・guard registry 項目という運用負債だけが残る。
  同一 allocation 内の early gate が同じ役割を果たすので、driver ごと取り下げた。
- **段 6 の 2 レンズが、本 wave の refactor が入れた回帰を検出した。** 帯評価 evaluator の抽出で
  public 述語の短絡が失われ、巨大整数 tolerance や後続 sample で
  **旧版が `False` を返していた入力が `OverflowError` を送出する**ようになっていた。
  これは receipt 再検算を通る campaign / floor / oracle / ratified freeze の fail-closed 性を壊す。
  fix で短絡順を復元し、2 反例を negative vector として固定した。
- **fix は 3 巡 (上限) を使い、うち 2 巡は自分が入れた破壊経路の縮退に費やした** ({{F:cleanup-fix-creates-destructive-path}})。
- **変異は事前登録 10 件で、初回は 5 件が MISMATCH だった。** 原因は親の登録が過少で、
  観測された赤 node 集合が期待集合の真の上位集合だったこと ({{F:mutation-expected-nodes-underregistered}})。
  観測集合で再登録して再走し **10/10 KILLED・期待 node 完全一致・SURVIVED 0** を得た。
  初回 spec と台帳は erratum として insight に残した。
- **親の裁定記録の行き過ぎを 6 件、段 6 レビューが是正した。** とくに
  「1 job の拒否 = α は計算ノードで帯内にならない決定的事実」は一般化のしすぎで、
  証明できるのは *その job・その host・その boot・その cpuset・その時刻の profile が帯外だった*
  ことだけである。「費用は約 1/3」も未立証だったので比率の記述をやめた。
- 受入全走は fix 後の tip (local main `7c2a2cf1` 取り込み済み) で
  **6668 passed / 20 skipped** (計算ノード、request 892166.nqsv)。
  対象 9 file の焦点実走は 669 passed / 2 skipped。
- **certify job (新較正の取得) は本記録の commit 時点で未投入である。** 投入は tree を clean にした
  直後に行う (submitter と job が source commit と clean を照合するため、docs 執筆と同時にできない)。
  結果は別 fragment で記録する。
- 逐語と変異台帳は `output/insights/2026-08-06_t419-u2-recalibration/`。

## 次の一手差分

### 更新

- [T-419] **P1・取得側の防壁は land、取得そのものと登録は未達**: 取得経路に
  benchmark 前の自己整合検査・publish 直前の policy 同一性検査・publish 済み bytes の
  独立再読を入れた ({{D:certify-clock-gate-early-and-published-recheck}})。
  **着手条件 (ii)(iii)(iv) はいずれも未達**である。(ii) accepted publish receipt は
  certify job の結果待ち、(iii) は本 wave で production 化したのが
  「同一 process 内で内部状態を参照しない再読」までで別 process の完全独立検証は未実装、
  (iv) 例外集合の空化は登録が前提で、登録は [T-529] の活性化権限が前提。
  publish 自体は D176 に阻まれないと実測で確定した (publish 経路は `env_contract` を呼ばない)。
  凍結 bytes・pin の更新は 1 件も行っていない。
  一次資料 = `output/insights/2026-08-06_t419-u2-recalibration/README.md`
  base: e6919fc34975fdaada23fe08558043a1044da851ff2f3a43c670dbf8ab3384b0

### 新規

- {{T:publish-transaction-position}} **P2・新規・ユーザー裁定待ち**: benchmark 中および
  benchmark 後の effective clock は依然として検査されない。外側の post probe は publish より
  後に走り、publish を取り消さない。凍結した pre profile と post observed clock の
  canonical 比較を publish 前に課すか、publish transaction 自体を後ろへ移すかの設計択一。
  段 6 レンズ A が file:line で指摘した既存の穴であり、本 wave が作ったものではない
- {{T:independent-verifier-receipt}} **P2・新規・ユーザー裁定待ち**: publish 済み bytes の
  検証を別 process の verifier で行い、判定を最終 receipt へ束縛する完全形。本 wave が入れたのは
  同一 process 内での再読までで、job wrapper も collector も canonical 述語を評価しない
- {{T:certify-reservation-formula}} **P2・新規・ユーザー裁定待ち**: certification job の
  予約式が実際の逐次 timeout 合計と一致しない。header と receipt は build 上限 1080 秒を
  記録するが、実際の cap は gflags 60×3 + glog 120×3 + CCBench 900×2 = 2340 秒である。
  CLI 起動前に「残り時間 >= calibrator の必要 envelope」を検査する改修も含む
- {{T:certify-attempt-path-runbook}} **P3・新規**: attempts 配下は job id の `:` を `_` へ
  正規化するのに対し job-staging は raw のままで、手順文書は両方に raw を使うと書いている。
  逐語実行すると最終 receipt が作れない。rejection のみの attempt を収集する回帰テストも無い
- {{T:certify-midjob-source-drift}} **P2・新規・ユーザー裁定待ち**: certification job は
  冒頭で source commit と clean を照合するが、その後は live worktree の probe / runner /
  calibrate の bytes を読む。immutable snapshot を取るのは CCBench だけであり、
  receipt の `source_commit` と実際に判定・生成した Python bytes が食い違いうる
