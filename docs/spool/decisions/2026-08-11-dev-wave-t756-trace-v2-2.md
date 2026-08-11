---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-11
wave: dev-wave-t756-trace-v2
seq: 2
---

## {{D:trace-completeness-external-counter}}. trace 完全性は trace 外 counter で裏取りし、witness は API では省略可・pipeline 境界では必須にする

**決定:** trace の committed txn 数を、trace 自身ではなく **CCBench が stdout へ出す
`commit_counts_`** と突き合わせる。verifier は `verify_trace_dir(..., *, expected_commits=None)` で
witness を受け、`Integrity` の一致条件を `clean()` の**純粋な連言**として持つ。witness を渡さない
呼び出しでは判定・出力・text が現行と完全に同一で、**受理集合は 1 mm も緩まない**。
production 経路 (`pipeline.evaluate`、S2 calibration、ladder 証拠) では witness を必須にする。

**理由:**
- 欠番検査は `expected = max(txid)+1` で数えるため、txid 最大側の trx が丸ごと消えると欠番 0 と
  数えられ、cycle の相手が消えて certified になる。trace の内部情報だけでは原理的に閉じない。
- witness を trace の外から取るので、**欠落位置に依らず** thread の trace file 丸ごとの欠落も捕える。
  当初案の「txn 終端マーカー」は末尾切りしか捕えない。
- silo/YCSB では `include/ycsb.hh` が commit 成功後に counter を 1 回だけ増やし、silo の `commit()` は
  validation 成功時に必ず `writePhase()` を呼んでその冒頭で C 行を 1 回だけ出す。早期 return が無い。
- **witness は failure-independent ではない。** trace と counter は同じ実行体から出るので、両方が
  同時に落ちる common-mode failure と個数を保存する破損は検出しない。文書は「独立 witness」ではなく
  「trace 外 counter による個数の裏取り」と書き、非検出限界を明記する。

**前提の機械 pin:** 「commit 後に無条件で counter を増やす」のは YCSB workload だけである。
TPCC / BoMB 系は counter 増分の**前**に `quit` を見て return するため、C 行数と counter が乖離し
正しい trace が赤になる。したがって witness 検査を通す run は trace binary が YCSB であることを
**allowlist 形**で確認し、非対応 workload は fail-closed で拒否する (denylist にしない)。
`batch_commit_counts_` は加算せず、非 0 は帰属不能として拒否する。

**却下した選択肢:**
- **共有の bench stdout parser を witness の権威にする** — 同一 label の重複行を last-wins で潰すため、
  壊れた stdout が静かに別の値になる。正しさ witness には「該当行がちょうど 1 行」を要求する専用の
  厳格 parser を置く。計測層の parser は他 consumer がいるので変更しない。
- **witness を必須引数にして API 全体で強制する** — 凍結証拠が `result_to_dict` の witness なし出力を
  bytes で pin しているため不可能。optional にしたうえで production 側の有限個の呼び出し元で必須化し、
  「直接 API と CLI の省略呼び出しには旧挙動が残る」と正直に書く。
- **verifier の出力 schema に構造化 witness を足す** — 凍結 ladder evidence が
  `orchestrator/verifier/report.py` の現行 bytes 一致を要求する (`driver` と `policy` だけが歴史 drift
  許容という非対称契約) ため、同 file は編集できない。構造化した witness 値は pipeline の WAL payload に
  載せ、verifier 側は既存 key (`integrity.clean` と `integrity.notes`) で表現する。
- **trace 形式そのものを v2 化する (C 行に R/W 件数 + 終端マーカー)** — trx 尾部欠落の偽陰性を閉じる
  唯一の道だが submodule の gitlink 前進を伴い、承認定数の追認禁止と push の人間手番に当たる。
  裁定パッケージで返し、本決定の射程外とする。

**位置づけ:** 実装済みの設計判断の記録。絶対規律の変更ではない — 規律 2 に対しては拒否側だけを
増やし、規律 3 に対しては不一致の期待値・観測値・差を構造化して次手へ渡す。
