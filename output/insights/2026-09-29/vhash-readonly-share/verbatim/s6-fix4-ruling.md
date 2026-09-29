# 段 6 fix4 裁定 (2026-09-29 17:3x JST、wave HEAD 038cc63e4 = fix3 統合)

- 対象: 親の所見 P-2 だけ。
- P-2 (real、親のコード読み): fix3 は leader が採取時に全 flag = 1 (`all_ready`) を見たときだけ `cicadaLeaderWork()` の前に `vlife_epoch_` を進める。採取では揃っていなかったが、採取から `cicadaLeaderWork()` 内の flag 走査 (util.cc 283〜289) までの間に最後の flag が上がると、`cicadaLeaderWork()` は公開するのに世代は進まない。すると (i) その公開の D-C は `stale` (dc_generation) として除外され (これは記録される)、(ii) **次の公開間隔では、前の間隔の cf_us (0 でないと上書きされない) が残った同世代の slot が「有効」として読まれ**、最大 cf が過小・Δ_ro が過大に偏り、しかも除外計数に現れない。
- fix: 公開を検出した経路 (`leader_ready && GCFlag[0]==0`) で、事前に世代を進めていない (`!all_ready`) なら、その時点で `vlife_epoch_` を進め、別計数 `dc_late_epoch` に数える (この公開自体は従来どおり stale で除外)。これで毎回の公開ごとに世代が必ず 1 つ進む。計器行 schema 2 に field を足し、driver の検査・集計、test を合わせる。
- 変異の追加登録: MUT-18 = 公開検出経路の遅れた世代更新を外す → patch の leaderWork block で「公開検出経路に `!all_ready` 条件付きの epoch 更新がある」構造 test で殺す。
- 既存テストの期待値を変えない (schema 2 の field 集合を足す test の更新は除く)。`#if` を増やさない (既存 block 内)。
