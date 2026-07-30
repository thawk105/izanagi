# T-145 段 1 brief

- scope: `test_socket_roundtrip_works_beyond_108_byte_repository_path` の serve thread 停止検査から固定
  `join(120)` の liveness 二律背反を除き、確定停止退行は赤、正常 shutdown は無期限 starvation だけを
  理由に偽赤にしない形へ置き換える
- 確定済み裁定: ユーザーの `$dev-wave T-145` を着手指示とする。起票元 B-2 は P2 nit で、
  T-136 の一般化後も固定 join が 30 秒から 120 秒へ拡大されただけで未解消
- 不変条件: `daemon=True` を維持し、serve thread の例外回収・停止退行の赤・長 path AF_UNIX
  roundtrip・capability 不足時だけの skip・xdist 隔離契約を弱めない
- 不変条件: T-136 の通常 run timeout 拡大、state/reason/side-effect の期待集合、製品 daemon の受理集合を
  変更しない。性能計測値は作らない
- 既存被覆: 現テストは real server の roundtrip 後に `shutdown()`、`join(120)`、`is_alive()` を検査し、
  停止しない daemon thread を赤にするが、確定退行と scheduler starvation を wall clock だけで分類する
- 純増検出力: shutdown の停止根拠と serve loop の再反復を観測可能な同期へ束縛し、固定待ち時間を
  伸縮しても得られない「正常 exit と停止条件無視の決定的分類」を mutation で実証する
- 成果物影響: 放置すると正常 commit を偽赤で受理集合から除外するか、確定退行で受入結果・試行記録の
  生成を最大 120 秒遅らせ、外部 ceiling 下では結果自体を失う
- 成果物: test-only の最小 patch、対象 vector の回帰テスト、事前登録 mutation matrix、受入記録、
  T-145 完了を同期した phase/worklog
- `(P1)` 親の provisional 裁定・攻撃対象: production へ wakeup API を足さず、既存 test seam または
  test-owned 同期だけで固定 join を除去できる
- `(P2)` 親の provisional 裁定・攻撃対象: real roundtrip node と決定的 shutdown-contract node を
  分離しても、前者の後始末が偽緑・hang に戻らない
- 受入と実測は本 worktree のログインノードで行い、対象テスト、mutation、repository 全走を使う。
  共有計算ノードや性能測定は使わない
- 分割: read-only plan 1、正しさ/検出力と並行性/cleanup の敵対相談 2、隔離 author 1、
  実装後 review 2 と必要な fix を別 Codex subprocess にする
