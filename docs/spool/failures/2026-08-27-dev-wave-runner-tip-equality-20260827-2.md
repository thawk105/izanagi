---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-runner-tip-equality-20260827
seq: 2
---

## supersede 追記

- F385 **supersede: 2026-08-27** — 「dispatch の内側の子は束縛外」という残余は、実際には実行器の main/tip byte 等値要求によって実害を消されているだけだった。受入は shard mode の LOGIN 実行で必ず dispatch し、計算ノード側の子は作業ツリーの実行器を pathname で起動するため、等値を外すと実行器を編集した wave が自分の実行器に自分を判定させる状態になる (2026-08-27 に 7 段の連鎖を実測)。閉じるには計算ノード側の子も tested main の blob へ束縛する必要があるが、その実装は実行器自身を編集するため当の等値要求に塞がれており、順序は {{T:dispatch-child-main-blob-binding}} と [T-1932] のユーザー裁定に係属する。既知の残余として記録済みであることは、その残余が今も無害であることを含意しない。
