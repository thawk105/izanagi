---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-03
wave: dev-wave-t293-perf-site
seq: 1
---

## 新規

### {{F:compute-node-default-python-is-oneapi}}. 計算ノードの既定 `python3` が oneAPI 版で orchestrator を import できない [環境前提] [手順漏れ]

- 事象: 新規 probe を計算ノードへ投入したところ (request `881946`)、`qualification.submission` の
  import が `TypeError: dataclass() got an unexpected keyword argument 'slots'` で失敗し、probe が
  rc=3 / `ok:false` で fail-closed した。`dataclass(slots=True)` は Python 3.10 以降の機能である。
- 根本原因: `.pbs` が bare `python3` を呼んでいた。計算ノードの `python3` は
  `/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin/python3` (3.10 未満) に
  解決される。ログインノードの `python3` は 3.10 なので、ログイン側の静的検査では発覚しない。
- 恒久対応: 計算ノードで python を起動する新規スクリプトは、`t126_qualification.sh:13-25` の
  既存の正規手順 (候補列を `command -v` で解決し `sys.version_info[:2] >= (3,10)` を実際に走らせて
  検査し `realpath -e` で確定、選べなければ exit 2) を使う。新方式を発明しない。
  `dispatch_compute._INTERPRETER_CANDIDATES` も同じ 3.10 要件を持つ。
- 再発検知: 選んだ interpreter の絶対 path を成果物へ create-only で記録し、
  「どの python で測ったか」を証拠に残す (本 probe は `interpreter` ファイルに記録する)。
- 補足: **probe 側の欠陥ではない。** 測定器の故障と正当な否定結果を分離する設計
  ({{D:two-sided-control-for-gateless-measurement}}) が効いたため、誤った測定結果が成果物へ入らなかった。

### {{F:python-and-shell-executable-acceptance-diverge}}. 同じ候補列に対し Python 経路と shell 経路の受理集合が食い違う [受理集合] [説明と実装の食い違い]

- 事象: 共有 policy の `perf_candidates` が指す perf は、計算ノードに実在し
  `perf --version` も production と同じ smoke argv も rc=0 で成功するのに、
  実物の `qualification.submission._executable` は `required executable unavailable: perf` で
  解決に失敗する (2026-08-03 に bnode005 / bnode009 で実測)。
- 根本原因: 当該 path は計算ノードでは **symlink** である。`_executable` は
  `not Path(found).is_symlink()` を要求して symlink 候補を捨てるが、同じ候補列を読む
  `t126_qualification.sh` は `[[ -x "$candidate" ]]` なので symlink を受理する。
  **同じ設定に対して 2 つの受理集合が存在する。**
- 恒久対応: 未定。受理集合の変更にあたるため D96 手続としてユーザー裁定へ返した
  (`output/insights/2026-08-03_t293-perf-site/adjudication-package.md` の択一 (b))。
  symlink 拒否が「path を pin したつもりが差し替えられる」ことへの防御である可能性があるため、
  意図を確認せずに緩めない (規律 2)。
- 再発検知: 同じ設定を Python と shell の双方から読む箇所は、受理・拒否の条件が一致することを
  実測で確かめる。片側だけの成功を「その設定は使える」と読まない。
