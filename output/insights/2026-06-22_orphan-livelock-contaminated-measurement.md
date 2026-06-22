# 発見: 前セッションの孤児 livelock (両 no-wait=0) が P2-2 計測を汚染 → 競合検知ガードを追加

- **発見日:** 2026-06-22 (Phase 2 P2-2 計測着手時, env=linux-baremetal)
- **種別:** 計測インテグリティ事故 (絶対規律4) + admission control の fails-open ギャップ
- **重大度:** 高 (汚染数値を採用しかけた near-miss)。durable な汚染 commit は破棄済み・対処実装済み
- **還元判断:** Izanagi 側の運用/ハーネス問題。CCBench 本体への還元は無し
  (孤児の原因 genome 自体は [[2026-06-22_silo-both-no-wait-zero-livelock]] で別途扱い)

## 事象

P2-2 (silo 8 genome × 3 workload の実 fitness 計測) を起動した直後、`ps` で**素性不明の
`ycsb_silo` が 1 つ動いている**のに気づいた。私の read-heavy は `ycsb_rratio=95` だが、その
プロセスは `ycsb_rratio=50 ycsb_rmw=false` で workload が一致しない。調査結果:

| 項目 | 値 |
|---|---|
| PID | 538093 |
| PPID | **1 (孤児 = 親が先に死に init に里子)** |
| ELAPSED | **約 7 時間** (起動 Jun 22 09:20、extime=3 のはず) |
| %CPU | **4793% (≈48 コアを busy-spin で占有)** |
| NLWP | 49 (48 worker + main) |
| flags | `-thread_num=48 -ycsb_tuple_num=1000000 -extime=3 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=false` |

`extime=3` が 7 時間走り続け 48 コアを食う = **両 no-wait=0 の livelock**
([[2026-06-22_silo-both-no-wait-zero-livelock]] の hang 表 "skew0.9 rratio50 48 1m → timeout" と一致)。
**insight を書いた前セッションが調査でこの構成を回し、hang したプロセスを kill し損ねて孤児化**
させたもの。7 時間 48 コアを占有し続けていた。

## 何が汚染されたか

孤児が半分の機械を食う中で P2-2 read-heavy が走り、**3 genome が commit 済み**になっていた
(bench median 3.86M / 3.49M / 3.77M tps、within-run CV 1.3–3.2%)。CV が低いのは「孤児が一定して
半機を奪う」系統誤差ゆえで、**精度は無価値** (クリーン機なら別の値)。これらは durable な WAL commit
= リカバリで terminal skip されてしまう → **campaign ディレクトリごと破棄して再測定**した。
genome 4 は in-flight (commit 無し) だった。

## なぜ admission control が止めなかったか (fails-open ギャップ)

`calibrator.runner.settle()` は 1 分 load average が 4.0 を下回るまで待つが、**20 秒で timeout
すると `settled=False` を返すだけで campaign はそのまま計測に進む**。孤児で load≈48 のとき settle は
必ず timeout し、誰も `settled` を検査しないので**汚染計測がそのまま採用された**。さらに load average は
1 分 EMA なので (a) 汚染が始まった直後は検知が遅れ、(b) 自分の直前 run の残像で誤検知する
— 競合検知の信号として load average は本質的に laggy。

## 対処 (実装済み + 延期)

**実装済み (P2-2 driver の pre-flight ガード):** `p2_2.py._assert_single_tenant()` を各 workload
campaign の冒頭で呼ぶ。`pgrep -af 'build-variants/.*ycsb_.*\.exe'` で**競合ベンチをラグなしに直接
検知**し、居たら **PID を表に出して計測を拒否**する (load average に頼らない確定信号)。
- 孤児/他者プロセスを**自動で kill しない** (規律6: 素性不明な実行物の処遇は人間が判断)。今回は
  孤児と確認した上で手動 kill した。
- pre-flight 時点では自分のベンチはまだ走っていない → 拾えるのは他者/孤児だけ (自己誤検知しない)。

**今回の手動対応:** 孤児 538093 を `kill -9`、汚染した read-heavy campaign dir を削除、機械が
idle (ycsb_silo 0・load 減衰) に戻ったのを確認してから P2-2 を再起動。

**延期 (将来のハーネス硬化):** 「settle が規定時間で quiesce できなければ計測を拒否/中断する」
pipeline 段階の admission を入れるのが本筋 (fails-open を fails-closed に)。ただし load EMA の
自己残像で false-positive する難しさがあるため、競合プロセス直接検知 (今回のガード) を一次対策とし、
段階導入 (規律5) で driver レベルに留める。pipeline への昇格は P2-3 以降で要検討。

## 教訓

- **計測前に機械が単一テナントかを確定信号 (競合プロセス) で確かめる。** load average は EMA で laggy。
- **hang した探索プロセスは必ず後始末する** (orphan 化させない)。長時間 livelock は機械を専有して
  以後の全計測を汚す。timeout 付きで回す調査でも、timeout 後に確実に kill する運用が要る。
- **fails-open な admission control は規律4 を黙って破る。** 「静定できなければ進む」は
  「汚染数値を採用する」と同義。
