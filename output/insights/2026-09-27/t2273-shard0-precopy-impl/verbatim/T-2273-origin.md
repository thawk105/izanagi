# 依頼の逐語 (2026-09-27 14:27 JST、/dev-wave の引数)

[T-2273] (= [T-2560] の次の一手) 受入 shard-0 の候補 (a) を実装する。正本: D2242・D2253、insight
  output/insights/2026-09-26/t2273-shard0-precopy-ab/README.md、worklog entry 1873 の carry。形: 既存の早期 memo prewarm と同じ controller の
  pytest_configure_node で背景 thread を起こす。実関数 _copy_git_visible_output を session で 1 回だけ実 repo に呼んで session
  所有の写しを作り、共有 base の builder は写しの完成を待ってから写しから局所複製する (D2242 の「最初の builder が作る」形は流用しない)。land
  条件は段 4 で実受入の隣接対 (D357) として事前登録し、5 分上限は同じ実受入で別に判定する。届かなければ次は (b) = 発行 subprocess
  と記録して止める。計算は job Elapse の実測単価で見積もり、検査込みで 2 node 時間以上ならユーザー確認。test_s8b_oracle_driver.py の fixture
  を絞る件 ([T-2604]、別系列の所有) は触らない。規律 2 を緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope
  外。着手直前の local main から fresh worktree を作る。
