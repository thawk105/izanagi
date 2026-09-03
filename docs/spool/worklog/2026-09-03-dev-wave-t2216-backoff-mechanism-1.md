---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-t2216-backoff-mechanism
seq: 1
title: [T-2216] 刻み応答の非単調性は確定しない — 上限の自然実験が滞在説を支持し、逐語 model がそれを再現できなかった (code + docs + insight、branch worktree-dev-wave-t2216-backoff-mechanism、変異 9/9 KILLED)
---

## 本文

- **ユーザー依頼:** 刻みへの応答の非単調性 (0.5 µs 最良 / 5〜25 µs 谷 / 100 µs やや回復) の
  機序を切り分ける。**「機序が確定しないなら『確定しない』と書いて終える — 説明を作文して
  埋めない」が明示条件。** 本題の切り分けだけを行い、仮想リスク向けの gate・検査・台帳・
  一般化は scope 外。
- **結論は「確定しない」。ただし空手ではない。**
  実測とソースだけから 3 件を確定させ、既存記録の誤り 4 件を訂正し、
  **素直な滞在説を model で反証した。** 材料は
  `output/insights/2026-09-02_t2216-adaptive-backoff-nonmonotonicity-mechanism.md`、
  設計判断は {{D:backoff-residence-model-refuted}}、
  {{D:backoff-update-window-is-not-constant}}、{{D:backoff-static-t0-is-zero-loop}}。
- **既存データの中に自然実験があった。** D1475 の材料に上限だけを変えた対が
  同一 job (`0:966801.nqsv`) 内にあり、上限 1000 → 50 µs で刻み 2 µs は
  1,647,478 → 3,397,531 tps (2.062 倍)、刻み 0.5 µs は 3,547,516 → 3,599,288 tps (1.015 倍)。
  **新規測定なしに「滞在が効いている」ことを実測で支持できた。**
  親が段 3 の走行中に材料を洗い直して見つけたもので、依頼時点では誰も参照していなかった。
- **しかし model はその滞在を再現しない。** 刻み 25 µs で実測 1,241,671 に対し予測 2,859,726
  (相対誤差 130%)、`P(Backoff_ > 100 µs)` は 0.038 止まり。上限の自然実験も
  2.062 倍に対し 1.030 倍しか出ない。**判定は `status: null`。**
  通ったのは最も鑑別力の低い「更新間隔 2560 µs での平坦化」だけ。
  balanced と read-heavy でも同じ形で外れた。
- **敵対検査が本 wave の成果を 2 度作り替えた。**
  (1) 段 3a が「滞在も切り捨ても勾配ノイズも持たない事後当てはめ model が判定 (A)(B)(C) を
  全部通る」という反例を実際に構成した。**形の一致は機序の同定ではない**という指摘で、
  親は到達しうる status を下げた。
  (2) 段 6 の 2 本が {{F:mutation-binds-only-the-readable-twin}} と
  「中間量 gate がキーの存在しか見ていない」を挙げ、**恒真な gate 2 件と
  目標格子から乱数の種への漏れ**を暴いた。修正後に変異 9/9 KILLED。
  **手を抜いた検査のままなら偽の一致を報告していた可能性がある。**
- **親の裁定の誤りを 2 件、レビューが突き返した。**
  (a) (P1) の閾値を「b が 0〜100 の最小は T(100)」と書いたが正しくは T(0)。
  (b) 未分類の新規 tool を login で走らせてよいという運用裁定
  ({{F:ai-self-authorized-login-run-of-unclassified-tool}})。
  後者は撤回し、`generic` task (D895) で計算ノードへ送り直した。
  **login 本走 (12 分、rc=0) は正規成果から外した。**
- **セッション異常 3 件。**
  (1) **Codex の利用枠が尽きて段 6 の fix 子が 14 秒で死んだ** (`f45_missing_output`、
  events に `You've hit your usage limit ... Sep 7th`)。従量課金へは切り替えず中断し、
  ユーザーから枠回復の連絡を受けて再開した。中断中に材料文書と未修正実装を branch へ保全した。
  (2) **待ち手 3 本が「exit code 0 で完了」と通知したのに `.done` が存在しなかった。**
  うち 1 本の通知本文には注入された欄と壊れたタグが入っていた。**必ず現物で検算する。**
  (3) 前セッション終了時に dispatch の収集役だけが落ち、**計算ノード側は完走して結果ファイルを
  残していた**のに孤児ロックが残った。job の終端と source の clean を確認して 2 file を削除した。
- **本走が制限時間を超えた** ({{F:model-run-slower-after-hollow-gate-fix}})。
  恒真な検査を実物の比較へ直した結果、12 分だった本走が 50 分を超えた。
  制限時間を 4 時間へ広げて完走。
- **受入全走はキュー混雑で 1 度 rc=70 になった** (前段の履歴監査が `queue-wait-timeout`)。
  この前段は D612 の上書きが効かない経路なので、放棄した投入が自分の順番を塞がないよう
  逐次再試行する形にした。
- 成果物はすべて**認証されていない**。trace-disabled の性能測定に基づく解析で、
  直列性の検査を通していない。variant 採用の根拠には使えない (規律 2)。

## 次の一手差分

### 新規

- {{T:backoff-diagnostic-build}} **P1・新規**: 走行中の `Backoff_`、実効 `time_diff`、
  leader 試行間隔、窓ごとの commit 数、勾配・parity 分岐率を直接記録する診断ビルドを作る。
  **絶対規律 1 により性能計測用ビルドとは別ビルドにし、計装は性能ビルドから
  コンパイル時に完全除去する。** 新規 Pegasus 実行体なので機構の着地と実測を別 wave に分ける
  (F660)。**機序を確定させ D1515 の再訪条件を満たす唯一の道。**
- {{T:backoff-static-tail-measurement}} **P1・新規**: b = 150, 200, 300, 500, 750, 1000 µs の
  静的 `T(b)` と abort 率を、同一ビルド・同一 job 割付けで測る。
  **未測定の tail が説明を供給している状態を、仮定でなく実測で閉じられる。費用が小さく効果が大きい。**
- {{T:t2216-model-execution-class}} **P2・ユーザー手番**: `tools/t2216_backoff_walk_model.py` の
  login 実行場所分類をユーザー端末で測定する (commit / argv / 入力の総 bytes と件数 /
  `memory.max` / 観測ピーク / 繰り返し数 / 測定日)。
  参考値として `generic` で計算ノードへ送った job のメモリは 101 MB、経過 733 秒。
  **これは runbook が要求する login cgroup の観測ピークではない。**
- {{T:submodule-init-file-transport-flag}} **P3・新規**: `tools/dev_wave_submodule_init.py` へ
  `-c protocol.file.allow=always` を足す ({{F:submodule-init-tool-blocked-by-file-transport}})。
  **全 wave の新規 worktree が毎回踏む。** 段 8 の自己改善候補として記録したが、
  tool のコード変更なので実装子が要り、本 wave の scope 外とした。
- {{T:backoff-window-count-distribution}} **P3・新規**: 窓あたり commit 数の実分布を測り、
  Poisson 仮定の妥当性を確かめる。{{D:backoff-residence-model-refuted}} が挙げた
  疑うべき前提の 3 番目。
