---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t1391-h1h2-workload
seq: 1
---

## 新規

### {{F:mutated-report-field-whackamole}}. fixtureの1 fieldだけ書き換えて不正状態を模擬したが、並存する複数の整合性checkに阻まれ意図した gate へ届かなかった [恒真ゲート] [テスト代表性]

- 事象: 登録済みbuild reportのacceptance否定側テストで、`report["cells"][0]["workload"]`を
  未知値へ書き換えて意図した gate (producer-supported判定) の拒否を`_accept()`経由でも
  証明しようとしたところ、3回連続で**異なる**手前の整合性check
  (`_check_workload_coverage`→run-envelope`workloads`比較→arm-digest-chainの
  resolver呼び出し) に阻まれ、意図した gate へ到達しなかった。
- 根本原因: 実report構造には同じ論理値 (workload) の複数の独立したコピー
  (`cells[].workload`、`report.workloads_requested`、run-startイベントの`workloads`、
  arm-digest-chain経由の別呼び出し) があり、1 fieldだけを書き換える方式ではこれらの
  相互整合性checkを網羅できない。加えて、直前の段6敵対レビューが検出した本来の問題
  (「receipt非生成assertionがgateまで届かず恒真」) 自体もこの構造への理解不足が一因だった。
- 恒久対応: {{D:t1391-workload-gate-scope}}系のwaveでは採らなかったが、一般則として
  「fixtureが生成した正常reportを不正化する」テストは、個別fieldの手書き書き換えでなく、
  producer-supported判定の正規authority (`resolve_workload_entry`) をmonkeypatchして
  対象の1判定だけを反転させる方式を優先する。ただしresolverが複数gateから呼ばれる場合は
  それも汎用的に効いてしまいうるため、直接gate呼び出し (単体テスト相当) による exact 検証と、
  受入経路 (`_accept()`) 経由の型・receipt非生成検証を**分離**し、受入経路側には
  「どのgateが拒否したか」までは要求しない設計にする。
- 再発検知: 今回はfix4巡目で親が変異matrixのprobeを都度実走して初めて各層の不一致を検出した。
  類似のfixture不正化テストを書く場合、実装前に対象workflow内の該当識別子の参照箇所を
  網羅grepしてから注入方式を選ぶ (段6敵対レビューでの静的検査だけでは発見できず、実走でしか
  見えなかった)。
