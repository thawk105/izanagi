# [T-2871] 生死確認の形の裁定 (親、2026-09-29 05:40 JST、ユーザー就寝中のためマネージャー指示に従い codex 2 立場で相談して決定)

材料: liveness-decision-context.md。相談: codex/decide-a.md (A 推し)、codex/decide-b.md (A 反対・B 推し)。

## 決定: A (投入済みの本番入口 2 job を待つ。2 本目が予算停止なら記録し、待ち行列が空いた後に新しい系列で 1 回だけ流し直す)

- 理由 1 (A 側): 確かめたいのは本番入口の別 job が同じ系列を引き継ぎ、2 本目が別の計測 claim で候補と stock を完了すること。B は同じ job id・job body を 2 回通らないので、成功しても段 4 §6 の完了にならない。
- 理由 2 (親): B が A に足す情報は小さい。別 process で実 `_authorize_measurement`・実 `acquire_claim`・実 `check_reservation` を通す確認は結合検査 T1 が計算ノード (焦点走 6 回目 33701.nqsv) で緑。B が加えるのは実 build・verify・bench だけで、どれも本 wave で変えていない。B は新しい使い捨て job script (実行手順を変える) を要する。
- B 側の最も強い指摘 (採用): 混雑が続けば A は先送りになる。→ 手当て: (i) 2 本目 33800 に `qsub --after 33730.nqsv` を付け (直列は scheduler が保証)、(ii) 要求 walltime を 1800 s に下げ、(iii) 2 本目の優先度を `qalter -p 10` で上げた (同じ user の job の中での並べ替え、影響は約 15 分の job 1 本)。予算 `MAX_WALLTIME_S` は変えない。
- 判定: 段 4 §1 の完了判定 (各計測 dir の候補・stock WAL、stdout の stock `certified-stock`、系列 state の iteration と履歴行) で行う。1 本目の系列と再試行系列をつないで成功と数えない。
- 2 本目が予算停止した場合: 事実を記録し、再試行は 1 回まで。投入前に計算量を再見積もりし、2 node 時間を超えるなら止める。
- 発見 (scope 外、次の一手に記録): 系列の walltime 予算が待ち行列の時間を含むため、混雑した Pegasus では driver が claim を解いても複数 iteration の loop が予算で止まりうる。予算の数え方の変更は D2256 項 3 に関わる別 task。
