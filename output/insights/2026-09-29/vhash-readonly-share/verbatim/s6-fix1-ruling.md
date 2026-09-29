# 段 6 fix1 裁定 (2026-09-29 16:1x JST、wave 統合 commit 315c1d125 = base 035fc11fa + author 4a0e630d0 と同内容)

入力: codex/out/s6-review-a.md (レンズ A、NO-GO)、codex/out/s6-review-b.md (レンズ B、NO-GO)、焦点走 35493.nqsv (316 passed / 1 failed: `test_readonly_figure_full_campaign_layout`、ValueError figure text overlaps)。
fix は 1 単位 (patch・driver・test・作図が計器行 schema で結合するため一枚岩)。

## real と判定し fix する所見

| ID | 所見 | fix の内容 | 放置時の成果物への影響 |
|---|---|---|---|
| F1 (A-M1・親 P-1) | slot 世代を begin 時に固定 → 公開をまたぐ tx の flag 上げ・ro 観測・rts が leader の読む世代に載らない | flag 上げ (mainte) と ro commit の cf 観測は**事象の時点**で `vlife_epoch_` を読み、その世代の slot に書く (世代が違えば cf/raise を 0 に初期化してから)。境界保持用の (rts, 種別) は世代で分けない thread ごとの現在値 slot (seqlock) にし、leader は `cicadaLeaderWork()` の前に採取して公開値と照合する。各条件の除外件数 (dc_first・dc_generation・dc_missing・dc_negative・holder_unresolved) は既存のまま出す | D-C と保持種別が gc 間隔・tx 長に応じて系統的に欠測し図の条件比較が偏る |
| F2 (A-M2・B-M2) | 計測レコード数が 1M に固定されていない | measure は N = 1,000,000 固定。smoke の較正 (maxrss と L3) は参考記録とし、1M が D15 第二基準 (maxrss ≥ 4 × L3) を満たさなければ smoke を失敗にする | md_2 と条件が変わり比較不能 |
| F3 (A-M3・B-M3) | `readonly_deep` (deleted 判定前) と `readonly_reads` (判定後) の母集団がずれる | 両方を deleted 判定後の同じ位置 (選択版を read set に積む直前) で数える。`readonly_candidate` も同じ母集団 | ro 深部割合が過大・100% 超、または計器行の拒否 |
| F4 (B-M1) | 既定 genome の照合値が CMake 既定と違う (`INLINE_VERSION_PROMOTION` の既定は Options.cmake で 1) | 既定 build の期待 -D を Options.cmake の実既定値 (PROMOTION=1 を含む) にする。既定・調整済み双方の compile_commands fixture test を置く | smoke が止まり 86 条件を測れない |
| F5 (B-M4) | T 条件が図に出ない | 図 1 と図 2 に「T (調整済み) と対応する R (既定、同じ r・長い tx・gc)」の比較パネルを足す (図は 4 枚のまま、パネル追加) | 補遺の問い (調整済み Cicada でも ro の深い探索が残るか) を図で判断できない |
| F6 (焦点走の赤) | 全 86 条件の fixture で図の文字が重なる | 作図の配置を直す (layout 検査は緩めない) | 図が生成できない |
| F7 (A-S1・nit) | D-C 第 3 項に公開後の計器処理時間が入る | `cicadaLeaderWork()` 復帰直後に時刻を採り、以後の計器処理をその後に置く。第 3 項の名称を「最後の flag 上げから公開検出まで」(英語 caption も同義) にする | 第 3 項の値と意味が計器の遅延を含む |
| F8 (A-S2) | leader が毎回 256 要素の配列群を zero 初期化 | 全 flag が立っているときだけ採取用配列を使う (毎回の初期化をしない)。一次資料で anchor と md_2 を並べて計器増分を示す (親) | 観測者効果が条件依存で公開間隔を押し上げる |
| F9 (A-S3) | MUT-7・MUT-8 の静的検査に穴、MUT-2 の fixture が単一理由でない | MUT-8: ro commit block 内の GCFlag への全書込み API (`storeRelease`・`__atomic_store_n`・`.store`・代入) と `gcstart_` への代入を検出。MUT-7: guard の外に抽選 (`draw.next()`) や書換えが無いことを block 構造で検査。MUT-2: 三項不一致だけを起こす fixture に替える | 変異を登録しても殺せない |
| F10 (B-S1) | 見積り (a) の呼称 | 題名か凡例に「観測鎖・先頭 K 版・既読区間に限定した楽観的適格率」(英語 caption も同義) | 一般の適格率として読まれる |
| F11 (B-S2) | D-F の誤差棒が対応の無い rep 同士を対にしている | 非対応の条件平均差として不確実性を計算 (条件ごとの反復の平均と分散から) | 図 3 の誤差棒が無意味 |
| F12 (B-S3) | smoke の所要見積りが準備・stock/default build を含まない | smoke で 3 秒の代表走を既定・調整済み双方で測り、全 build・依存準備の実測を足した job 合計を出す | 2 node 時間判定が過小 |
| F13 (B-S4) | 作図器の集計で update commit/s・install/s が落ちる | 作図器側でも raw の extime から速度を再計算し provenance に載せる | 裁定の 5 指標を図の provenance で照合できない |

## fix しない (親が扱う)

- B-nit: `patches/README.md` の entry 更新 → 親が段 7 で書く (docs)。
- B-nit・A: 実機の build・計測・4 図生成 → 親が smoke・計測で確かめる。

## 変異の追加登録 (fix 前、DW-M01)

| ID | 変異 | 殺すべき test (予定) |
|---|---|---|
| MUT-11 | mainte の flag 上げ記録を begin 時の世代 (`vlife_slot_generation_`) に戻す | patch の mainte block が事象時点の `vlife_epoch_` を読む構造 test |
| MUT-12 | measure のレコード数を smoke の較正 N にする (1M 固定を外す) | measure の N = 1,000,000 test |
| MUT-13 | `readonly_reads` を deleted 判定前へ戻す (深部数と別位置) | patch の read block で両計数が同じ位置にある構造 test |
| MUT-14 | 既定 genome の期待 PROMOTION を 0 に戻す | 既定 build の compile_commands fixture test |
| MUT-15 | 作図から T 比較パネルを外す | 作図 fixture で T パネルの存在 test |

MUT-7・MUT-8 は F9 の強化後の test で殺す (再照準)。既存の MUT-1〜MUT-10・EQ-1 の登録は維持。
