---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1140-claim-identity
seq: 3
---

## 新規

### {{F:hostname-forgeable-in-userns}}. live hostname を authority に数える設計を、非特権 namespace が恒真化する [恒真ゲート]

- 事象: (2026-08-16、[T-1140] 段 3 レンズ A の実測) reservation の `binding.host` を
  `socket.gethostname()` / `socket.getfqdn()` と照合して「どのノードで測ったか」の
  authority にする設計を検討したところ、Pegasus login ノードでは
  `/proc/sys/kernel/unprivileged_userns_clone` が `1`、`/proc/sys/user/max_user_namespaces` が
  `2147483647` であり、**非特権のまま UTS namespace を作って hostname と FQDN の双方を
  変更できた**。その際 `/proc/sys/kernel/random/boot_id` は親と同一のままだった。
  計算ノードでの可否は未実測。
- 根本原因: 「OS が返す値だから呼び手の支配外」という一段階の推論で authority を認定した。
  実際には呼び手が namespace を作れる環境では、live な OS 状態も呼び手が用意できる。
  2026-07-25 [T-088] の A-03 で「環境変数同士の一致を authorization gate に数えない」を
  設計制約として確定していたが、その制約は「env 対 env」の形でしか書かれておらず、
  「env 対 live OS 状態」が同じ穴を持つことを覆っていなかった。
- 影響: 実装前に発見したため成果物への影響はない。実装していれば、材料レポートと proof chain が
  claim 内の `host` を「scheduler が割り当てたノード」の証明として参照し始めていた。
  実際に証明されるのは「呼び手が名乗ったノード名と、呼び手が観測させた値が一致すること」だけである。
- 恒久対応: {{D:exclusion-lifetime-constraints}} の項目 3 (authority) が
  「呼び手が両側を用意できる照合は drift 検出であって authority ではない」を要求する。
  live OS 状態を authority と数える設計は、その状態が呼び手の namespace 権限の外にあることを
  当該環境で実測してからでなければ採らない。
- 再発検知: 「どのノード / どの process / どの環境で実行したか」を証明すると称する検査が、
  同一 process から読める値 (hostname、FQDN、cgroup 名、環境変数、`/proc/self/*`) だけを
  照合先にしていること。scheduler・kernel の特権面・外部 authority のいずれにも触れていない
  照合は authority に数えない。
