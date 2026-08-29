---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-29
wave: dev-wave-t2027-t2043-external-input
seq: 4
---

## 新規

### {{F:worktree-submodule-missing-policy-oid}}. policy が pin した submodule oid が主 checkout のローカル branch にしか無く、worktree の受入全走だけが落ちる [テスト代表性] [手順漏れ]

- 事象: T-2027/T-2043 の受入全走 (2026-08-29、tested tip `384e39a68`) が
  `orchestrator/tests/test_mocc_g2_discriminator.py::test_transaction_watermark_surface_is_trace_guarded_and_post_store`
  1 件だけで赤になった (1 failed / 18846 passed / 67 skipped)。破れたのは
  `assert commit_type.returncode == 0` で、`git cat-file -t e9e477ca1b55348ab4530de0b1cf663ce4555290`
  が submodule で rc=128 (`could not get object info`) を返していた。この oid は
  `tools/pegasus/mocc_trace_v1_policy.json` の `mocc_trace.new_oid` である。
- 根本原因: **worktree ごとに submodule の object store が別**である。主 checkout の submodule は
  `.git/modules/external/ccbench` を指し、worktree の submodule は
  `.git/worktrees/<name>/modules/external/ccbench` を指す。当該 oid は主 checkout 側にだけ在り、
  しかも到達経路は upstream ではなく**ローカル branch
  `izanagi-t1943-mocc-g2-readfrom-witness`** 1 本だけだった (push されていない)。
  pin 済み submodule commit `511c9538e...` からは到達しない。
  `tools/dev_wave_submodule_init.py` は docstring どおり "without fetching" で初期化するので、
  新しい wave worktree にはこの object が入らない。**主 checkout でだけ通り、
  どの wave worktree でも落ちるテスト**になっていた。
- 恒久対応: 検出器は当該テスト自身で、object 不在で fail-closed する (恒真ではない)。
  worktree 側の復旧は、主 checkout の submodule から witness branch を ref ごと持ってくる —
  `git -C <worktree>/external/ccbench fetch <主 checkout>/external/ccbench
  izanagi-t1943-mocc-g2-readfrom-witness:refs/heads/izanagi-t1943-mocc-g2-readfrom-witness`。
  tracked file も submodule pin も変えず、object だけが増える。本 wave はこれで復旧し、
  同 file 単独走が 22 passed / rc=0 になったことを確認した。
  **恒久側 (policy の oid を pin 済み commit から到達可能にするか、init tool に provisioning を
  持たせるか、witness を upstream へ出すか) は受理集合と外部 repo の扱いに関わるため
  {{T:witness-oid-provisioning}} で裁定へ返す。テストは緩めない。**
- 再発検知: 受入や焦点走が submodule の `git cat-file` / `rev-parse` の rc で落ちたら、
  同じ oid を主 checkout の submodule で引き、`for-each-ref --contains <oid>` で到達元を見る。
  ローカル branch しか出てこなければ本エントリの型である。新しい wave worktree を作った直後に
  一度確かめると、受入 1 回分を失わずに済む。
