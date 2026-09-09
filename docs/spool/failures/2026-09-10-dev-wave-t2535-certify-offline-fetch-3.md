---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-10
wave: dev-wave-t2535-certify-offline-fetch
seq: 3
---

## 新規

### {{F:dirty-tree-during-pending-source-bound-job}}. 投入した job の走行中に親が repo を書き、job 自身の source 再照合で止めた [手順漏れ]

- 事象: 認定較正 job (request 989232.nqsv) を投入した直後、親が待ち時間を使って
  `docs/spool/` へ台帳 fragment を 2 本書いた。job は冒頭で source 面の clean を再照合するため、
  `source_identity` / `working tree became dirty before job start` で rc=2 終了した。
  計算ノードの割当てを 1 回無駄にした。
- 根本原因: 親が「投入したら待つだけ」と考え、job が **投入時点ではなく起動時点**の作業ツリーを
  見ることを勘定に入れなかった。job の clean 検査は `output/` を除外するので、
  走行中に書いてよいのは `output/` 配下だけである。
- 恒久対応: 防壁は既に在って正しく発火した — `tools/pegasus/certify_calibration.sh` の
  `source_identity` 検査は `git status --porcelain --untracked-files=all -- . ':(exclude)output'` で
  fail-closed に止める。足りなかったのは親の作法なので、**source identity を再照合する job の
  投入中は `output/` 以外を書かない**を運用の既定にする。同型は変異走行にもあり、
  そちらは「変異中は親の編集と worktree へ書きうる子の起動を止める」として既に成文化されている。
- 再発検知: job が `failure.json` に `stage=source_identity` を書く。
  無駄になった割当ては scheduler の Elapse (今回 7 秒) と `failure.json` の対で識別できる。

## 再発

### F333

- **再発: 2026-09-10** — 親が `tools/check_ai_provenance.py` の全史監査へ 300 秒の timeout を掛けた。
  同監査は計算ノードへ dispatch するため 300 秒では足りず、打ち切りで request 988752.nqsv が
  孤児化して orphan hold が武装した。次の監査は `rc=16` / `orphan-hold` で起動を拒否された。
  hold は `output/pegasus-dispatch/orphan-hold.json` と `orphan-holds/<request>.json` の
  **2 箇所**にあり、`qstat` の行頭照合で対象が一覧から消えたことを確認したうえで両方を消して復旧した。
  以後この監査には打ち切らない長さの timeout を掛ける。

### F500

- **再発: 2026-09-10** — 同じ job script へ新しい python3 呼出しを足す実装が、再び裸の
  `python3` を使った。今回の呼び先は pristine source verifier で、その import 経路には
  `orchestrator/holdout_observation.py` の `@dataclass(..., slots=True)` と
  `orchestrator/campaign/attempt_registry_core.py` の `typing.TypeAlias` があり、いずれも 3.10 以降
  でしか動かない。計算ノードの既定 `python3` は 3.9 に解決されるため、この呼出しは configure へ
  到達する前に必ず失敗する構成だった。**計算ノードへ投入する前に段 6 の敵対レビューが静的に検出し、
  同 file が既に持っていた版数 smoke check と同型の解決を verifier 用に置いて閉じた。**
  実害は出ていないが、同じ file の同じ型が 2 度目である。恒久対応は
  `orchestrator/tests/test_pegasus_calibration_workload.py` の
  `test_certify_third_party_verifier_uses_version_checked_interpreter` と
  `test_certify_third_party_verifier_interpreter_resolution_fails_closed` で、
  前者は裸 `python3` への差し戻しを変異走行で KILLED として実測している。
