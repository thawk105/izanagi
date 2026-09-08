---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-09
wave: dev-wave-t2213-probe-condition-gate
seq: 3
---

## 新規

### {{F:enclosing-scope-build-sink-hides-macros-from-closure}}. 入れ子関数の build sink は閉包検査から macro を隠し、繰延べ台帳の entry を無効化する [恒真ゲート] [テスト代表性]

- 事象: `orchestrator/tests/test_ccbench_spawn_sites.py` の繰延べ台帳が
  `tools/pegasus/probes/t2187_adaptive_const_probe.py` の build sink 2 件を先送りしているが、
  親が閉包分類を実走したところ、certify 側の sink
  (`<module>._certify_main._build_trace_binary`) は
  `{'proven-unreachable': 38}` に分類されており、**`deferred` は 1 件も計上されていなかった。**
  もう 1 件の sink (`<module>.main`) は `{'deferred': 14, 'proven-unreachable': 24}` で、
  こちらは繰延べが実際に効いている。
- 根本原因: 到達可能性は sink の source text から判定する。certify 側の sink は
  引数を取らない入れ子関数 `def _build_trace_binary():` の中に在り、build へ渡す
  `genome` を外側 scope の閉包変数から受け取る。macro の字面が sink の範囲に現れないため、
  検査は 38 macro すべてを到達不能と結論する。**build sink は、条件を外側 scope から
  受け取るだけで閉包検査の網から外れる。**
- 影響: この sink について繰延べ台帳の entry は何も抑止していない。entry を削除しても
  閉包検査は緑のままで、関門を 1 行も足さずに「繰延べを解除した」状態を作れる。
  台帳の厳密性検査は entry が生きた sink を一意に指すことしか見ないので、これも通る。
  **「台帳から entry を消して検査が緑」は関門が効いた証拠にならない。**
- 恒久対応: 本 wave では検査本体を変更していない (族全体に効く共有機構の変更であり
  依頼範囲外)。代わりに {{D:t2187-probe-condition-gate-deferral-maintained}} が、
  この sink の繰延べを維持したうえで「解除は緑ではなく、関門除去変異が当該 sink だけを
  赤にすることで示す」ことを配線時の必須条件として固定した。
  検査本体の強化は同 D の次の一手へ送った。
- 再発検知: 繰延べ台帳へ新しい member を足す wave は、その sink の分類を実走して
  `deferred` が実際に計上されることを確かめる。計上されないなら、その entry は
  抑止していないので、繰延べではなく閉包検査の穴として扱う。
