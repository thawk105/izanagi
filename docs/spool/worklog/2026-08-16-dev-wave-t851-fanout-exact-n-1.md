---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t851-fanout-exact-n
seq: 1
title: fan-out の admission gate は恒偽だった — 本走は実装の巧拙と無関係にこの機体で実行不能 (docs のみ、実装差分ゼロ、branch worktree-dev-wave-t851-fanout-exact-n)
---

## 本文

[T-851] は「fan-out の採用可否を決める exact-N の本走を 1 回行う」だった。**本走は 1 度も
投入していない。投入できないことが先に確定したからである。**

- **`memory.peak` がこの kernel に無い。** `uname -r` = 5.15.0-186-generic。
  `/sys/fs/cgroup/user.slice/user-31609.slice/` にも同 slice 配下の session scope にも
  `memory.peak` は存在しない (`memory.current` / `memory.max` / `memory.oom.group` / `memory.stat`
  はある)。`tools/mutation_fanout.py` の `_attest_measurement_cgroup` は try block の先頭で
  `memory.peak` を読むため、OSError で必ず `False` を返す。
- **生きた cgroup に対して実測した。** 親が同 tool を import し、`populated 1` の実 cgroup へ
  `_attest_measurement_cgroup` を直接呼んだ結果は `False`。静的推論ではなく実測である。
- **逃がし道が無い。** `validate_admission_receipt` は全 measurement log について attestation の
  真を要求し、`run_fanout` は既定引数で当該関数を固定する。CLI に override は無い。
  したがって**どの admission receipt も必ず拒否され、shard は 1 本も起動しない。**
- **代替実行面も無い。** 計算ノードは PBS ジョブに user systemd session が無く
  `systemd-run --user --scope` が成立しない (D180 が記録する 2026-08-05 実測)。

この矛盾は正本 docs の中で閉じている。`docs/pegasus-runbook.md` は **2026-08-01 実測**として
「`memory.peak` はこの kernel (5.15) に存在しない」と明記し、代わりに専用 scope の
`memory.current` を 3 反復以上 sampling して最大値を採る手順を正本にしている。
fan-out の `MIN_CERTIFICATION_REPETITIONS = 3` はこの手順に由来するのに、attestation だけが
runbook に無い `memory.peak` の kernel 再読を足した。既存テストは attestation を stub で
置換するため、この矛盾を 1 件も検出できない。詳細は {{F:fanout-attestation-impossible}}。

裁定は {{D:fanout-unrunnable-here}}。**正しさゲートを緩めて本走を成立させる道は採らない。**

段 3 の敵対 2 本 (`reasoning=max`) は独立に同じ結論へ到達し、加えて次を real と構成した。
いずれも本 wave では実装しない (実装差分ゼロ)。

- receipt を作る前の certification 3 走そのものが admission を通らない bootstrap になる。
- attestation は測定 cgroup と wrapper 実行を束縛しないため、無関係な sleeper 1 本と
  `..` を挟んだ同一 scope の別表記 3 通りで receipt を成立させられる (重複検査が raw string 比較)。
- identity は HEAD ではなく caller 指定 commit の 2 blob にしか束縛されず、
  `mutation_fanout_contract.py` は identity 外なのに split と merge 判定を実行する。
- registry 差分は path 集合の Counter 比較だけで、他 wave の同時変更・同一 path の再束縛を検出しない。
- 段 2 プランが提案した 2 案は、仮に gate が通っても単独で却下する。
  (a) kernel `memory.peak` を `memory_current_bytes` sample として書き足す案は、
  時刻に存在しない観測を記録に足す捏造である。(b) group root の再帰削除は、
  他 wave がその下を scratch に使っていれば相手の evidence を消す。

**親 brief の誤りを 2 件訂正する。** (i) harness lock の位置は `mutation_harness.py:430-434` ではなく
2090-2111 (`_lock_path_for` / `_lock_for`)。鍵が repo 絶対 path の sha256 である事実は変わらない。
(ii)「真の競合は計算資源だけ」は過剰一般化で、共有 Git worktree registry・inode・quota も競合面である。

エージェント工数: codex 子 3 本 (plan `reasoning=max` 1、consult `reasoning=max` 2)、いずれも rc=0。
本走・変異走行を投入しなかったため計算ノードの資源は消費していない。

**非帰属フレーク 1 件。** 段 3 レンズ A の待ち手 (背景 job) が、成果物・`.done` の双方が不在で
producer が生存中 (11 分経過) のまま完了として通知された。出力 file は完全に空で
`[exited with code 0]` 行すら無く、同時に張った他の待ち手には有った。`dev_wave_wait.py` の
欠陥か harness 側の背景 task 終了かを切り分けられないため、帰属させずここに記録する。
DW-O01 の「完了は `.done` と exit code だけで判定し、通知を判定にしない」に従って
偽完了と判定し、待ち手を張り直して正しく回収した。段 8 の自己改善は、この件も
`memory.peak` の件も既存正本と本エントリの D/F で覆われるため、docs 編集を行わなかった。

## 次の一手差分

### 完了

- [T-851] fan-out の exact-N 本走は**実行不能**と実測確定した。採用可否の答えは
  「現状のままでは採用不可」であり、gate を緩めない限り本走は成立しない。
  残余の判断 (attestation をどう直すか) は {{T:fanout-attestation-schema-v2}} へ移した。
  remaining: none
  base: 41385aba777d9747eba58907c1788a580b00392ec99c1043ac1adc866d8cb2dc

### 新規

- {{T:fanout-attestation-schema-v2}} **P2・ユーザー裁定待ち**: 実行不能と判明した fan-out を
  どうするか決める。(1) attestation を runbook の正規手順 (専用 scope の `memory.current` を
  3 反復 sampling し最大値 + margin、live 証明は `cgroup.events` の `populated 1` と
  `memory.max` 一致で残す) へ揃える schema v2 を別 wave で起票する。**gate の受理集合を
  変えるためユーザー裁定が要る。** (2) 「実行不能」と docs へ明記して凍結する
  (安いが、次に本走を試みる者が同じ 1.5 時間を使う)。(3) fan-out を撤去する
  ([T-849] [T-850] も moot になるが 3,400 行超を捨てる)。
  **親の推奨は (1)。** gate が恒偽なのは設計の誤りではなく実装が正本 runbook と食い違っただけで、
  修正は局所である。変異本走の wall-clock は dispatch queue 待ちが支配項であり、
  N shard の並行投入で queue 待ちを重ねられる利得は実在する。
  なお段 3 が構成した receipt 偽造経路は [T-849] と同族 (同一 Unix user による偽造) であり、
  プロトタイプ基準で見送り済みの族である。(1) を選ぶ場合もこの族を同時に閉じる必要はない。
