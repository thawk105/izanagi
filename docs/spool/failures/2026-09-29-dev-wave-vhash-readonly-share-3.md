---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-readonly-share
seq: 3
---

## 新規

### {{F:vlife-generation-fixed-at-begin}}. 公開ごとの記録の世代を tx の開始時点で固定し、公開をまたぐ事象の大半を「世代不一致」で除外していた [計測汚染] [テスト代表性]

- 事象: md_15 の Cicada 診断計器 (`patches/instr-cicada-version-lifetime.patch`) の段 5 実装は、GC flag を上げた時刻・ro commit の観測・境界保持用の rts を、tx の `begin()` で決めた公開世代の slot に書いていた。公開の直後に各 worker は走行中の tx の終わりで flag を上げるので、その記録は旧世代に入り、次の公開で leader が読む世代から欠ける。親のコード読みと段 6 レビュー A が指摘し、fix1 で事象時点の世代に改めた後も、原典の `cicadaLeaderWork()` が flag を下ろしてから計器が世代を進める隙間が残った (焦点再レビュー 1 巡目)。fix3 前の patch の smoke の短い走では、公開間隔の 60% (既定 Cicada) と 84% (調整済み) が除外されていた。fix3 (全 flag を見たら公開前に世代を進める)・fix4 (遅れて揃った公開も検出時に進める) の後は 1.0〜1.7%、本計測 258 走で最大 3.5%。本計測は fix 後の patch だけで取ったので、偏った値は結果に入っていない (near miss)。
- 根本原因: 「どの公開間隔の事象か」を事象の時点ではなく tx の開始時点で決めた。原典の公開手順 (flag を下ろす処理が公開の中にある) と計器の世代更新の順序を実行順で追わなかった。純関数 test は計器の C++ の実行時挙動を見ないので、除外の偏りは smoke の実測まで見えなかった。
- 恒久対応: patch の構造 test (`orchestrator/tests/test_vhash_cicada_vlife.py` の `test_mut11_event_generation_and_current_holder`・`test_mut16_epoch_advances_before_cicada_publication`・`test_mut18_late_publication_advances_epoch`、変異 MUT-11・16・18 で kill を確認) と、計器が除外件数 (`dc_generation`・`dc_late_epoch`・`dc_epoch_mismatch`) を出し driver が集計する形 ({{D:vhash-readonly-share-decomposition}})。
- 再発検知: smoke の短い走で D-C の除外率を読む (一次資料 §4・§9)。除外率が数 % を超えたら記録の世代の取り方を疑う。

## 再発

### F26

- **再発: 2026-09-29** — `dev-wave-vhash-readonly-share` の wave 用 worktree の作成で、login の高負荷 (load 50〜170、他 wave の `git worktree add` が 10 本前後並走) の下、`git worktree add` が checkout の途中で EINTR (「システムコール割り込み」) により 2 回 rc=128 で終了した (1 回目 14:42「Could not reset index file to revision 'HEAD'」、2 回目 15:01「cannot create directory ...: システムコール割り込み」、各 20 分弱)。どちらも作りかけの directory と admin dir は消え、branch だけが残った。3 回目は `git worktree add --no-checkout` で登録だけを先に作り、`git worktree lock` の後に `git -C <path> reset -q --hard HEAD` を成功するまで反復する形にして、1 回目の reset で完成した (15:07)。この形なら reset が中断されても登録と作りかけが残り再実行できる見込みだが、今回 reset の中断は起きておらず確かめていない。同じ wave の子木・計測木 7 本もこの形で作り、全件 1 回目で成功した。変異 harness (`tools/mutation_worktree.py`) の login での plan-only は harness 内部の `git worktree add --detach` が同じ EINTR で失敗し (rc=125)、計算ノードでの実行に切り替えた。
