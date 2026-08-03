---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-04
wave: wave-a-transport-smoke
seq: 1
---

## 新規

### {{F:pegasus-attestation-self-rejecting}}. 登録済み Pegasus 較正が自分自身の attestation 述語を通らず、計算ノードでの campaign 実行を全面的に塞いでいた [誤前提] [恒真ゲート]

- 事象: 使い捨て smoke (request 882490, bnode002) の 2 脚とも、build へ到達する前に
  `execution_guard.ExecutionGuardError: attestation comparisons failed` で停止した。
  失敗した比較は `effective_clock.samples_mhz` のちょうど 1 件。
  期待中央値 2101.0、`tolerance_pct` 2.0 なので許容帯は [2058.98, 2143.02] であり、
  観測列の index 34 が 3076.13 でこれを外れた。
- 根本原因: 述語は「期待列の**中央値**を中心に、**観測列の全要素**が ±`tolerance_pct` に入ること」で
  ある (添字対応の比較ではない)。一方、登録済み較正
  `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` の
  `attestation_profile.effective_clock.samples_mhz` は index 40 に 3080.935 を持つ。
  **この参照データを観測値として同じ述語にかけると不合格になる** — 参照が自分自身の受理条件を
  満たしていない。物理的には「48 コアのうちサンプリング時にたまたま 1 コアがブーストしていた」
  状態が焼き込まれており、実行時も「1 コアでもブーストしていれば不合格」になる。
  どのコアがいつブーストするかはスケジューラと熱の都合で決まり、再現性のある機器特性ではない。
- 恒久対応: 未実施。**述語と凍結較正のどちらを正とするかは受理集合に触れるためユーザー裁定へ返す**
  ({{D:pegasus-attestation-blocks-wall1}} に択一と推奨を置いた)。本 wave では緩和も迂回もしていない。
- 再発検知: 裁定後に、登録済み較正自身を観測値として与えると受理される (自己整合性) ことを
  確かめる positive control を `orchestrator/tests/` へ置く。これは「参照が自分の判定を通る」
  という恒真でない性質の検査であり、今回の型を直接撃つ。

### {{F:qsub-positional-args-invented}}. 使い捨て job script が sanctioned な `qsub -v` を写さず位置引数を発明し、投入前レビューで止めた [誤前提]

- 事象: 段 5 実装子が書いた job script は progress directory を位置引数 `$1` で受けていた。
  NQSV の `qsub` usage は `[script-file ...]` としか示さず、スクリプトへ位置引数を渡す syntax が
  無い。そのまま投入すれば計算ノード到達直後に rc=2 で死に、混雑した queue を 1 往復むだにした。
- 根本原因: F84 と同型。sanctioned な投入器 (`tools/pegasus/submit_floor.sh` は
  `qsub -v "$export_spec" "$JOB_SCRIPT"`) を写さず、自前の受け渡し方を発明した。
  逐語再利用の対象を「環境正規化」だけと解釈し、**投入インタフェース**を含めなかった。
- 恒久対応: 親の投入前レビューが検出し、段 6 fix で環境変数経由へ差し替えた (実走前に閉じた)。
  規律面では F84 の「sanctioned job script の正規化を逐語で再利用する」の射程に
  **qsub 引数の受け渡し形も含む**ことを {{D:pegasus-attestation-blocks-wall1}} の理由欄で明示した。
- 再発検知: 投入前チェックリスト (runbook §8) に沿って親が qsub 行を実際に組み立てる段で、
  sanctioned な submit script の qsub 呼出し形と突き合わせる。今回はこれで捕捉した。
