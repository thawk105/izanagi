---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t419-generation-migration
seq: 3
---

## 新規

### {{F:effective-clock-method-vacuous-comparison}}. attestation の `effective_clock.method` 比較が非空検査でしかなく、計測方式の実体不一致を pass と記録していた [恒真ゲート] [誤前提]

- 事象: 実行時 attestation の receipt は `effective_clock.method` を expected/observed の
  比較 field として持つが、判定は「両方が非空 str であること」だけである。
  登録済み Pegasus 較正 (第 1 世代) の method は素朴な `proc-cpuinfo` で、
  実行時 probe が返す method は走行 CPU を巡回させる方式 α である。
  **両者は実体として別の計測方式であるにもかかわらず、receipt には pass と記録されていた。**
- 根本原因: method は自由文字列であり、環境ごと・方式改訂ごとに値が変わりうる。
  比較を導入した時点で「値の一致を要求すると方式改訂で全 attestation が落ちる」ため
  非空検査へ退避したまま固定された。結果として、**この field は定義上どんな入力でも
  fail しない**。恒真ゲートである。
- 影響: 計測条件の同一性を receipt で主張できない。
  期待側の較正がどの方式で取得されたかと、実測がどの方式で観測されたかが食い違っていても、
  proof chain の上では区別が付かない。
- 恒久対応: 未実施。是正は受理集合を縮小する変更であり、
  第 1 世代が active な状態で入れると Pegasus の全 attestation が即座に落ちる。
  環境契約世代の活性化と対で行う必要があるため、
  {{D:env-generation-activation-is-human-lockstep}} の裁定パッケージへ従属項目として返した。
- 再発検知: 比較 field を足す改修では、その field を**必ず fail させる負例**を同じ変更単位で
  置く。負例を書けない field は比較ではなく形式検査であり、receipt の比較表に
  verdict として並べない。

## 再発

### F10

- **再発: 2026-08-16** — 同型 (pin 前進で参照が腐る構造) が **runbook ではなく凍結証拠の
  完全検証入口**で実現していた。`silo_ladder_rung1` の公開 `verify-result` は今日すでに
  `correctness provenance values mismatch` で赤であり、原因は module 定数側の ccbench pin が
  前進した一方で、凍結証拠側の pin が取得時のまま据え置かれていることである。
  短絡するため後段の current binding 検査には到達しない。
  F10 の恒久対応 (check_docs の runbook glob 検査) は docs の参照を守るが、
  **コード内の pin 定数と凍結成果物の間の同型ドリフトは射程外**である。
  さらに環境契約世代の前進でも同型の破綻が起きることを本 wave が実測しており、
  producer も consumer も異なる独立 2 例が揃った。
  したがって「凍結成果物は記録時の値で検証し、live 適格性は別 API で検査する」の
  族一般化は `DW-G03` の閾値を満たす。設計は
  {{D:env-generation-activation-is-human-lockstep}} の裁定パッケージへ返した。
