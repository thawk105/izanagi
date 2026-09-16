---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t1328-certify-perf-optional
seq: 2
---

## {{D:perf-probe-decides-not-candidate-exhaustion}}. 較正認証でも perf 有無は probe が決め、受理集合の変化は到達可能性と最終受理へ分けて記録する

**決定:** 較正認証 (`tools/pegasus/certify_calibration.sh`) は、policy の perf 候補が 1 本も
smoke を通らないことを理由に測定前に停止しない。D494 の順序に従い、候補解決を済ませた
`PATH` の下で canonical probe を 1 度だけ呼び、`use_perf_from_receipt` の結果だけで分岐する。
`probe_error` は `unavailable` へ変換せず停止する。`use_perf` は CLI から `sweep.calibrate` の
closure を経て `runner.measure_point` へ伝播させ、**counter 必須検査だけを perf 有りに限定する**。
throughput 検査・maxrss 検査・rep 失敗処理は変更しない。

**決定 (2):** 本変更のような「停止点を後ろへ動かす」改修では、受理集合の変化を
**到達可能性の変化**と**最終受理の変化**に分けて記録する。「増分はちょうど X」と書けるのは
既存の品質・登録条件も満たす部分集合に限られ、無条件の等式としては書かない。
D494 の順序を守ることで生じる縮小 (旧 smoke は通るが canonical probe だけ失敗する候補) は
限界として記録し、**第二の probe や fallback を足して隠さない**。

**理由:**

- D352 は性能測定に calibration を明示的に含めて「preflight は可用性を検出して記録し、
  実行を止めるためには使わない」と定める。候補全滅での即時 `exit 2` はこれに正面から反する。
  発火頻度が未確定でも是正根拠は独立に成立する — 段 3 の 2 レンズが独立に追認した。
- 候補全滅を直接 degrade の根拠にすると判定入口が 2 本になり、canonical receipt を経由しない
  迂回路ができる (D494 の却下理由と同じ)。`use_perf_from_receipt` 1 本のままにする。
- **perf が本当に要る判定は通さない。** レコード数の飽和選択は LLC miss 率を要し、
  `analyze.py` は全欠損なら判定不能を返す。no-perf 成果物が `accepted` になれないことは
  新しい gate ではなく、`sweep.py` → `report.py` → `cli.py` → `schema_v2.py` の既存多層が保証する。
  この保証を実装で代替・迂回しない。規律 2 は緩めない。
- counter 必須検査を perf 有りに限定するのは「測定の完了条件を取得可能量に対応させる」変更で
  あって、認証の counter 必須条件を削除する変更ではない。認証 predicate は 1 文字も変えない。
- 受理集合を「ちょうど」と書くと、到達可能性の拡大を受理の拡大と読ませる。段 6 の焦点再レビューが
  具体的な反例 (品質理由が残れば rejected のまま) と第三の縮小経路 (policy 候補の重複が
  `perf_preflight` の重複検査で rc=2 になる) を示した。

**却下した選択肢:**

- **acquisition 判定後に測定せず終える** — D352 の「動かない環境では perf なしで測定を進める」を
  満たさない。差分は小さいが、perf 不在が測定停止理由として残る。
- **旧 smoke の成功を新しい gate として再要求して縮小を消す** — D494 が定めた判定順序を壊し、
  「literal `perf` は PATH に無いが policy 候補は動く」入力の受理を付け替える。目的に逆行する。
- **degraded な較正成果物を accepted にする分岐を新設する** — 本 wave の scope 外であり、
  D493 の「degraded は緩い分岐ではなく別の厳しい分岐」に従う新しい認証契約が要る。裁定へ返す。
- **候補全滅を直接 no-perf の根拠にする** — 判定入口が 2 本になる (D494 の却下理由)。
