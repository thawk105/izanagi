---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-a6-read-heavy-cert
seq: 1
---

## {{D:a6-study-shape-map}}. certification policy の形は study ごとの exact map に閉じ、任意 N へ一般化しない

**決定:** A-6 (read-heavy 1 workload) を A-2 と同じ protocol で回すために `load_policy` の
workload 数 / cell 数の固定を外すが、**任意 N への一般化は採らない**。次の 2 層に閉じる。

- `study` から shape を引く exact map を持つ。`paper-story-a2-certification` は workload 2 / cell 4、
  `paper-story-a6-certification` は workload 1 / cell 2。未知 study と shape 不一致は現行と同じ
  `CertificationError` で拒否する。
- policy 選択面 (`--policy`) は repo 内 canonical な 2 path だけを受理する closed set とする。
  任意 path を受理しない。

D1259 の partial v4 境界 (exact 2 workload で成功が exact 1) は、writer 側 `finish_group` と
consumer 最前段 `_validate_completion_receipt` の 2 箇所だけで保つ。前段に支配される
manifest producer / loader / authority へは guard を足さない。

**理由:**
- 任意 N への一般化は、A-6 という名前を持つだけの 3 workload policy や別 rratio の policy まで
  正式 proof chain へ通す。段 3 の独立した 2 レンズが同じ欠陥を挙げた。
- exact map と closed set は「現行の exact 2/4 を、出荷する 2 形状ちょうどへ置き換える」ものであり、
  受理集合は現行より広がらない。
- policy を tracked file に限ると、job body の HEAD 一致・tracked clean 検査を通じて、
  実行された policy bytes が `source_commit` へ git 経由で束縛される。
- partial 境界の guard を 5 箇所へ置くと前段に支配されて発火せず、変異の単独帰属が成立しない。
  恒真な保証を増やすだけである。

**却下した選択肢:**
- `len(workloads) >= 1` の一般化 — 上記のとおり受理集合が承認外へ広がる。
- A-2 policy に read-heavy を足して 3 workload にする — 外側 certification は policy workload 順の
  論理積 (D1169) なので、完了済みの A-2 判定を作り直すことになる。費用も 1 job では済まない。
- 新しい `.sh` を複製する — `tools/pegasus/admission_registry.json` と `test_hooks.py` の
  2 つの登録簿へ追加が要り、並行 wave と衝突する。既存 2 本へ policy 選択を足す方が安い。

## {{D:a6-walltime-twelve-hours}}. A-6 の walltime は read-heavy の検査コスト実測から 12:00:00 とする

**決定:** A-6 policy の `scheduler.walltime` は `12:00:00` とする。A-2 fan-out の `06:00:00` を
転用しない。

**理由:**
- A-2 の 6 時間枠は write-heavy と balanced の実測 (rr5 Elapse 3671s / rr50 3594s) に基づく。
- read-heavy (48 thread / zipf 0.9 / rratio 95 / extime 3) の直列性検査は 1 回 23 分の実測がある。
  同 regime の別走行は 5 時間で 15 点中 3 点しか完了せず CPU/経過 = 1.0 だった。
- A-6 は 2 cell x (legacy 1 + full-scale 5)。full-scale 10 回を max 23 分で見積もると 3.83 時間。
  12:00:00 はその約 3.1 倍で、gen_S の Per-Req Elapse 上限 86400S の内側である。
- D193 により build 後の中断 attempt は自動回復しない。walltime 超過は attempt 全損であり、
  この非対称性が枠を広く取る理由である。
- `scheduler` は `_protocol_preimage` に含まれないため、walltime を変えても protocol の同一性は
  変わらない。D1263 は A-2 fan-out の据え置きを定めた裁定であり A-6 を拘束しない。

**却下した選択肢:**
- A-2 と同じ 06:00:00 を継承する — 実測 regime が違う値の転用であり、超過時の損失が大きい。
- 24:00:00 上限いっぱいにする — 見積りの根拠を超えた枠で、queue の占有だけが増える。
