---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-15
wave: dev-wave-t1076-waiter-bytes-contract
seq: 1
title: 稼働中の待ち手が実行している bytes を新 tip の blob へ束縛し、受入投入前に止める (コード + テスト + docs、変異 7/7 KILLED、branch worktree-dev-wave-t1076-waiter-bytes-contract)
---

## 本文

- ユーザー裁定 第 12 回 #3 ((a) 契約化、2026-08-13 23:44 JST) の実装。同裁定が「独立 1 wave」と
  束ね方まで指定していたため、他の実装 wave と束ねていない。設計は {{D:waiter-executed-bytes-gate}}、
  rollout の扱いは {{D:waiter-gate-rollout-not-by-schema-cutoff}}。
- **裁定文の「実害 1 件実測済み」は一次資料と食い違う。** 敵対レンズ A が指摘し、親が確認した。
  entry 546 は lease 取得前・dispatch 前に旧待ち手を停止したと明記しており、旧 schema の receipt の
  実発行も land 拒否の実観測も記録に無い。正しくは「静的に確定した未然事故 1 件」である。
  実装判断は変わらないが、証拠の分類を訂正して記録する。
- **段 2 プランは親の provisional 前提 (P1) を棄却した。** 「gate を持たない起動済みの旧 process は
  新 tip を merge しても旧 control flow のまま受領証を発行でき、land はそれを区別できない」。
  敵対 2 レンズが独立に real と判定した。親は所見を real と認めたうえで、対策として提案された
  receipt schema の互換なし世代交代は **scope 外**と裁定した (理由は上記 D)。
  代案 3 つを裁定パッケージでユーザーへ返す。親の推奨は activation tip による grandfather。
- **敵対 2 レンズが割れた 1 点を親が裁定した。** 同内容 inode 置換を拒否すべきか。
  待ち手は自分を再実行しないため pathname の現在の中身は「何を実行しているか」に無関係であり、
  land が inode を見るのは束縛後に実行するからである、という順序差を根拠にレンズ B を採った。
- **段 5 実装は既存テスト 1 件を壊した。** 起動形を `__spec__ is None` に限定したため、待ち手を
  file loader で in-process にロードして `main()` を呼ぶ既存テストが停止側に落ちた。
  敵対 2 レンズが独立に「述語が誤っており、テストの期待値は正しい」と判定し、親も採用して
  実装側を直した (段 6 fix)。
- **子はテストを 1 件も実走できなかった** (段 5・段 6 とも `qstat -Q preflight rc=1` / rc=16)。
  親の bounded local も cgroup の memory.max を attest できず rc=16 で、いずれもテスト結果ではない。
  実測はすべて親が `--force-dispatch` で計算ノードへ投入して得た。
- **変異走行は 3 回起動に失敗した。** いずれも harness の引数契約で、`--wrapper-attempt` が path
  でなく試行番号であること、期待 node に param 名が要ること、`--attempt-out` は毎回新規 path で
  なければならないこと。走行そのものは 1 回で完走した。
- **親が期待 node の完全集合を導出するのに repo 外の script を書いた。** DW-M08 は完全集合での
  完全一致を親の義務とする一方、凍結境界は script を実装面としており、両者が衝突する。
  今回は repo に入れず job dir へ置いたが、導出は tools 側の command として提供されるべきである
  (段 8 の改善候補へ回した)。
- 段 6 レビュー所見のうち 1 件を backlog へ回した。停止後に lease 解放が失敗すると
  `restart-required` の detail が cleanup 側の結果に上書きされて診断が消える。受理集合に影響せず、
  かつ並行 wave が同じ印字経路を編集中のため本 wave では触らない。
- **親の記述に過大主張が 1 件あり、焦点再レビューが検出した。** 実装 commit の本文と runbook 追記が
  「detail に期待 sha・実 sha・tested tip・理由を載せる」と無条件に書いていたが、上の backlog 事象の
  ときは表示されない。commit は変異走行の anchor なので amend せず、runbook 側に例外を明記して
  訂正した。commit 本文の当該 1 文だけは、この例外を書いていない状態で残っている。

## 次の一手差分

### 完了

- [T-1076] 受入投入前に稼働中待ち手の束縛 source bytes と新 tip blob を照合する契約を入れた。
  実測は焦点走 221 passed / 0 failed、変異 7/7 KILLED (SURVIVED 0・MISMATCH 0・baseline 緑)。
  rollout 被覆の窓は {{T:waiter-gate-rollout-coverage}} へ分離した。
  base: 8ccc38ec5150f55e095f30affa664001830230ae60d145bdeec143ee5a6bbde8
  remaining: none

### 新規

- {{T:waiter-gate-rollout-coverage}} **P2・ユーザー裁定待ち**: gate 導入より前に起動した待ち手が
  契約の被覆外である窓を閉じるか決める。案は (a) 排水、(b) activation tip による grandfather、
  (c) 現状維持 (窓を明記したまま自然に枯らす) の 3 つで、親の推奨は (b)。
  却下理由と (b) の 2 段活性化の要点は {{D:waiter-gate-rollout-not-by-schema-cutoff}} に整理した。
