---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-vhash-eval-pstar
seq: 1
title: [T-2914] VHash の評価計画の草稿 v1 §5.5 を md_21・md_23 の結果に規則を変えずに当て、確認段へ持ち込む前進先の方策を p* = c (既読の可視区間に収まる最大)、hot の段数を K* = 1 とした — md_21 は E-hb・E-now・C が md_21 の門を通っていないので主要な比較の判定語が門未完了で止まり、どの組にも予備的な支持は出ない (docs のみ、計測なし、branch dev-wave-vhash-eval-pstar)
---

## 本文

- VHash 並行 wave md_34 (依頼 `/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_34.txt`)。結果は草稿 `docs/vhash-evaluation-preregistration-draft.md` §15、選択の要点は {{D:vhash-eval-pstar-kstar}}。
  §5.5 の本文は変えていない。結果を見た後の規則の変更は無い。
- 数値は一次資料の集計から repo 外の単発コマンドで再計算し、生の出力を job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-vhash-eval-pstar/` (`judge-md2*.stdout.txt`・`md21-raw-*.txt`) に残した。
  md_23 §5.1 自身の当てはめ (48 組・12 組・K* = 1) とは全組一致。md_21 の性能用 240 走行は raw と compact で throughput が一致。
- 段構成は軽量版 (段 2・3 なし、実装面なし)。段 6 の read-only review 1 本 (gpt-6-sol、21 call、536 秒) が must-fix 3・should 2 を出した。
  must-fix 1 は、親の初稿が md_14 §5 の門 (target patch を重ねる前の build) を md_21 の門として完了扱いし、E-hb・E-now・C を含む比較に語を付けていた点。
  親は「md_21 §7 の一致は全 macro 未定義の前処理と既定 flag の出力行までで、門用 build での意味の同一性を示さない」という反論を否定できず、門未完了を主の当てはめにし、md_14 の門で完了とみる読みは「参考の語」に下げた。
  p* はどちらの読みでも c。must-fix 2 (c21 の c+d は欠測より門未完了が先)・3 (P21-5 の登録 cell Y50・L-ops の GC 100 µs に語を付ける。c・e 対 A は欠測、C を含む列は門未完了) と should 2 件も採った。
- 焦点再レビューは 3 巡 (上限): 1 巡目 NO-GO (10 call、255 秒。「主 cell は欠測とした」の一括記述が門未完了を先に当てる語と食い違う)、2 巡目 NO-GO (5 call、167 秒。
  「c・e 対 A だけが判定語を持つ」が門未完了も判定語であることと食い違う、worklog の要約が広い)、3 巡目 GO (3 call、83 秒)。3 巡とも数値の再計算で p* = c・K* = 1 を覆す誤りは無く、残った所見は言い回しの量化だった。
- セッション異常: `EnterWorktree(name)` が filter driver の文言で失敗し、`git worktree add --no-checkout` + lock + `reset --hard` で作った (1 回目で成功)。開始 gate は local main が 1 commit 進んでいて NG、`merge --ff-only main` 後に rc 0。
  隔離 session の guard が、変数を sed の file 引数に置く形と、glob を含む python heredoc を拒否した (Edit ツールと repo 外の .py に切り替えた)。
  撤去を促す終了時 hook が、commit 0 本の未 land の木に「land 済み、撤去せよ」を 3 回出した。撤去せず未 land と 1 行書いて続けた ({{F:cleanup-stop-hook-ff-before-first-commit}}、段 8 の routing)。
  wave 中に local main が 213d411c6 → 5b7134c5c へ進んだ (別 wave の記録と worklog のローテーションだけ)。最初の commit の前に ff-only で取り込み、T-2914 の base digest が変わらないことを確かめた。

## 次の一手差分

### 完了

- [T-2914] 草稿 v1 §5.5 を md_21・md_23 に規則を変えずに当て、方策・K・cell ごとの予備的な語と p* = c・K* = 1 を草稿 §15 に書いた ({{D:vhash-eval-pstar-kstar}})。
  remaining: none
  base: 01b186bf414729d332ea813b4e2b950df9c268e5753302eb457c65ad85b64b87

### 新規

- {{T:vhash-c-now-target}} **P3・新規**: 評価計画の H3 (C 対 C_now) の処置 C_now (アクセス駆動の前進 C の前進先を「今」の時刻にする方策 a) が実装されていない。md_21 の `--cicada_fwd_target` は
  min|max|partial だけである (草稿 §15.7、§11 の P3)。target patch の既存の `#if` の内側の実行時 flag の値として足すか、H3 を確認段から外して追補に回すかを決める。docs と patch、計測なし。
- {{T:cleanup-stop-hook-ff-false-positive}} **P2・新規**: `tools/dev_wave_cleanup_stop_hook.py` が、最初の commit の前に `DW-O20` の ff-only で main へ揃えただけの未 land の wave 木に
  「land 済み、撤去せよ」を出す ({{F:cleanup-stop-hook-ff-before-first-commit}})。判定を直し、`orchestrator/tests/test_hooks.py` の `test_cleanup_stop_*` に負例を足す。コード + test。
