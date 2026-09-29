---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-gc-connection
seq: 1
title: VHash の前進を GC の回収境界へつなぐ手順 (読み取りの後に待つ tx への圧力による前進・確定→公開・fallback の段階) を小モデルに足し、6 場面を全探索した。健全版は反例なし、危ない版 5 種のうち 4 種で違反を検出し、回収境界の前進と回収できる版の数をモデル内で数えた (コード + test + insight、branch worktree-dev-wave-vhash-gc-connection)
---

## 本文

- 依頼: 並行 VHash wave の md_10 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_10.txt`、出典メモ §15〜§18 と文献調査の U0)。ユーザー就寝中のため、判断は codex の相談・レビューを踏まえて親が決めた。対象 item は wave 開始時点と land 直前の local main の「次の一手」に無かったので、完了した作業は本エントリで記録し、後続を新規登録した。
- 正本: `output/insights/2026-09-29/vhash-gc-connection-model/README.md` (仕様 G1〜G7、SP と HP の比較、場面、60 構成の結果、反例の読み、規則と反例の対応表、効果の数、範囲と確かめていないこと)。設計判断は {{D:vhash-gc-connection-sp}}。
- 段 2 plan は SP と HP の両方をモデル化する案だった。段 3 の相談 2 本 (正しさ境界 / 実効性・過剰) は、待機を操作列の末尾に限ると危険結果に届かないこと、「確定時に refs を外す」危ない版は反例にならない見込みであること (親の予想と一致)、効果は同じ trace の前後差ではなく対照との差で数えるべきことを指摘し、レンズ B は HP を削ることを推奨した。段 4 で SP だけを採り、WAIT を操作列の任意位置に置く形に改めた。
- 段 6 レビュー 2 本の must-fix 3 件 (効果の増分に他 tx の進行が混ざる、公開した floor の最大値がアクセス駆動の公開を記録しない、効果の対象が指定の待機 tx に限られない) は real として fix した。焦点再レビューは上限 3 巡を使った。1 巡目は fix の子が依頼外に入れた探索順の並べ替え (同じ長さの反例の選び方を変えていた) と floor 単調性の検査範囲を、2 巡目は数え上げの正例が探索器の統計経路を通らないことを指摘し、それぞれ fix した。3 巡目は一次資料の書き方だけを指摘し、親が直した。
- 棄却・据置き: `explore()` を直接呼んだときの G1・G2 の danger が空の結果になる点は、既存 API の形を変えないために fix しない (CLI は null を出す)。
- セッション異常 (実害なし、3 件): (1) 親が別の script を作る command の中に fix1 の detach script を誤って書き、fix1 の launcher が再実行された。起動器の「出力 file 不在」検査で rc=2 停止し codex は起動しなかったが、`.done`・log・pid を上書きした (採否は上書き前に確定済み)。(2) 40 桁 sha を手で書く誤りを 2 回した (git が拒否、または起動前に気づいた)。(3) 全史 provenance 監査 (計算ノードへ自動 dispatch する) と所要計測の dispatch を同じ worktree で同時に起動し、監査の qsub 中の一時 hold に当たって所要計測が rc=16 (子は未起動) になった。
- エージェント工数: Codex plan 1・consult 2・author 1・review 2・fix 3・focus 3 (いずれも gpt-6-sol / medium)。子の worktree `.claude/worktrees/vhash-gcc-author` (branch vhash-gcc-author, vhash-gcc-fix1〜3)。計算ノード: 焦点走 2 本 (680 passed・681 passed)、vhash の 2 test file の所要計測 4 本 (うち 1 本は監査の hold で rc=16・子未起動)、変異の本走 1 job (束ね経路 D842、request 34779.nqsv、Elapse 775 秒、8 変異すべて事前登録どおり KILLED、MISMATCH 0)。変異 MG7 は事前登録の初案 (pressure と WAIT の両条件を外す) が既存場面で状態爆発し自走が終わらなかったため、pressure の条件だけを外す形に再照準した。受入全走 1 回目 (記録 commit に local main を post-claim merge した木 b2fe29e39): child-green、28004 passed・74 skipped。この結果を書き足した docs だけの commit の後に、land の前提として受入をもう一度通す。

## 次の一手差分

### 新規

- {{T:vhash-gc-rules-into-prototype}} **P2・新規**: VHash の C++ 試作 (md_6 系) の GC 接続を、小モデルで必要と分かった規則に合わせて確かめる。前進は待機の安全点で tx 自身が行う、確定してから floor を公開する、floor を下げない (公開した floor より古い時刻へ fallback しない)、回収は後続の確定版で行う (md_4 の R10)。試作の正しさ検査 (md_3 の検査器) で確かめ、回収境界の前進と回収できた版の数を実測する。根拠: `output/insights/2026-09-29/vhash-gc-connection-model/README.md` §2・§8。
- {{T:vhash-gc-helper-and-stopped-thread}} **P3・新規**: 止まった thread の論理境界まで進める代行型の前進 (HP) と、その場合の物理参照の解除 (段階 C) を、論文の対象に入れるかを決める。入れるなら descriptor の世代つき CAS が確定から公開までを覆う形を小モデルで検査する。根拠: 同 README §3・§7。
