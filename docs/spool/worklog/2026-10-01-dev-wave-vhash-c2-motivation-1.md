---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: dev-wave-vhash-c2-motivation
seq: 1
title: [T-2916] VHash の動機 C2 を測った — 完走する長い read-write tx は修正済みの最良 Cicada の回収境界を 1 ms 未満しか止めず (長い tx なしの 3.4〜21 倍)、1 ms を超えるほど長い tx はほぼ commit しない。事前登録の成立点 0 で本計測なし (driver + test + insight、branch dev-wave-vhash-c2-motivation)
---

## 本文

- 一次資料 `output/insights/2026-10-01/vhash-c2-motivation/README.md`。§1〜§3 (腕・負荷・smoke grid・成立条件・点の選び方) は計測の投入前に commit した (`7bdc3adbf`)。
- 経緯: 00:4x に land 調整役の指示 (5 時間枠の残り 4%) で停止し、09:43 にユーザーの「続けて」で再開した。再開時に md_42 の着地 (今の VHash を主論文の候補から外す推奨、C1) を見て、C2 は md_42 が測っていない型なので中止せず進めた (段 1 brief の (P0))。
- 腕は md_42 と同じ定義 (S = md_11 の観測最良 genome、R = 同 + `IZANAGI_CICADA_RO_GCFLAG`)。負荷の knob は計器なし build でも同じに作れるものに限り、通常 tx の read-only 指定 (計器側の `izanagi_ronly_pct`) を使わなかった。
- smoke 3 job (skew 0・0.3・0.6、request 40672〜40674、各 Elapse 約 210 s) の 78 走はすべて有効。成立判定は driver の aggregate で機械的に当て、27 点すべて不成立。依頼と事前登録どおり本計測を投入せず止めた。計算は合計約 0.2 node 時間。
- CCBench は pin C で測った。記録の前に pin F の main を取り込んだ (C → F は Cicada の source を変えない)。計測の取り直しはしていない。
- 段の構成は軽量版 (段 2・3・段 6 review 子なし)。Codex author 1・fix 2 (test の取り出しの欠陥 1、main 取り込みで main 側を採った登録 2 行の足し直し 1)。変異 M0〜M9 は登録どおり (M0 生存、M1〜M9 KILLED、赤の集合も一致)。wrapper は走行中の main の land で事後検査 rc 125 (変異の判定には影響しない)。
- 計測用 checkout 3 本の submodule 初期化を並列に打つと 3 本とも `update-no-fetch` の I/O 失敗で rc 1 になり、順次の再実行で通った (DW-O08 の 1 回再実行の範囲)。

## 次の一手差分

### 完了

- [T-2916] 長い read-write tx (C2) が修正済みの最良 Cicada の回収境界をどれだけ止めるかを smoke grid で測った。完走する長い tx では境界年齢の平均 217〜864 µs (長い tx なしの 3.4〜20.6 倍)、生存版数は record の 1.00〜1.10 倍。境界が 1 ms を超える長さではほぼ commit しない。事前登録の成立点 0 で、論文 §1 の動機に「C2 が回収を止める」は使えないと記録した。
  remaining: none
  base: 49af96e1abcdce93874ff0bb0166c2c1c34c0007386ccbf40a7cc30fef66fae0

### 新規

- {{T:c2-low-write-pressure}} **P3・新規 (VHash を続ける場合だけ)**: 通常 tx の read-only 割合が高い (書き込み圧が低い) 負荷で、修正入りの R に「完走し、かつ回収境界を 1 ms 以上止める」長い read-write tx があるかを測る。md_29 の WO1-09 (read-only 指定 95%・24 thread) では 1,000 操作の長い update tx が完了率 0.68〜0.72 で完走したが、修正なしの build で read-only commit の欠陥による停止が混ざる。計器なし build に read-only 指定を作る最小の workload patch が要る。md_42 の推奨 (今の VHash を主論文の候補から外す) が採られたら見送る。詳細は `output/insights/2026-10-01/vhash-c2-motivation/README.md` §7。
