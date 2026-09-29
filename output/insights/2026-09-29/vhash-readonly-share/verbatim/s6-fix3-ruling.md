# 段 6 fix3 裁定 (2026-09-29 16:5x JST、wave HEAD a61f193df = fix1 + fix2 統合)

入力: codex/out/s6-focus1.md (焦点再レビュー 1 巡目、fix1 後の木 06071df01 を対象、NO-GO)、codex/out/s6-fix2.md (fix2 = 作図重なり、子が test 本体を直接実行して通過、pytest としては未実走)。
焦点再レビューは DW-O16 の上限 3 巡のうち 1 巡目。fix は 1 単位。

| ID | 所見 | 判定 | fix |
|---|---|---|---|
| F1-r (focus1 対応表 F1 partial) | `cicadaLeaderWork()` は flag を下ろしてから戻り (util.cc 318〜322)、計器の `vlife_epoch_` 更新はその後。隙間に上がった flag・ro の cf 観測が旧世代 slot に書かれ、次回の leader が読めない | real | **leader が全 flag = 1 を採取したとき (`all_ready`)、`cicadaLeaderWork()` を呼ぶ前に `vlife_epoch_` を進める。** flag を下ろすのは leader だけなので、全 flag が 1 と観測した後の `cicadaLeaderWork()` は必ず公開する (util.cc 283〜323)。したがって公開前に世代を進めても、次世代の事象 (flag 上げ・cf 観測は GCFlag==0 が前提) は必ず新世代 slot に入る。公開の検出 (GCFlag[0] の 1→0) と整合しない場合 (all_ready なのに公開が検出されない) は別計数 `dc_epoch_mismatch` にする |
| F13-r (focus1 F13 partial) | 作図器が速度を固定 3 秒で割る。raw の argv に extime が無くても受理 | real | 作図器は各走の argv から `-extime=` を読み、無ければ拒否。速度はその値で割る |
| MUT-15-r (focus1 変異節) | MUT-15 の test が T パネルの一部削除で通る | real | 図 1・図 2 の T 比較パネルが実際に描かれた系列を provenance (または戻り値) に記録し、test は各図の T パネルの系列数・条件 ID を照合する |
| F6 (fix2) | 作図重なり | fix2 で対処 (x 軸 0〜100% 固定、2 パネル図の上余白)。親が pytest で確認する | なし |
| F8・F9・F12 (partial) | 親の作業 (anchor 並記)・変異の実適用・実機所要 | 親が計測・変異本走で確かめる | なし |

## 変異の追加登録 (fix 前)

| ID | 変異 | 殺すべき test (予定) |
|---|---|---|
| MUT-16 | `vlife_epoch_` の更新を `cicadaLeaderWork()` の後へ戻す | patch の leaderWork block で epoch 更新が cicadaLeaderWork 呼出しより前にある構造 test |
| MUT-17 | 作図器の extime 読取りを固定 3 に戻す | extime = 1 の raw fixture で速度が 3 倍違うことを検出する test |

MUT-15 は強化後の test で殺す (再照準)。
