---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-14
wave: dev-wave-t1994-readonly-snapshot
seq: 3
---

## 新規

### {{F:userns-mode-bits-bypass}}. user namespace の中では mode bits による保護が効かない [恒真ゲート]

- 事象: identity map した user namespace の中から、所有者が `chmod 0444` した自分の file へ
  **書けてしまう。** namespace の外では同じ操作が `EACCES` で落ちる (対照を取った)。
- 根本原因: process は自分が作った user namespace の中で全 capability を持つ。
  `CAP_DAC_OVERRIDE` は file の所有 uid がその namespace へ map されている限り
  mode bits による拒否を迂回する。identity map は自分の uid を map するので、
  **自分が所有する file すべてがこの迂回の対象になる。**
- なぜ危険か: D1755 (D984) の「判定後の材料再生成の禁止」は `chmod` に依存している。
  user namespace を素朴に導入すると、**守るべき相手である build 子に対してだけ
  その保護が無効になる。** 受理集合を広げる後退であり絶対規律 2 に触れる。
- **段 3 の敵対レビュー 2 レンズはどちらも予測していなかった。** 一方は
  「同じ inode を bind すれば親の chmod は子に効く」と refuted に分類しており、
  inode と mount についてはそのとおりだが capability の面が抜けていた。**実測でしか出なかった。**
- 恒久対応: {{D:userns-dual-guard}} の二重防護 (全 capability 落とし + `NO_NEW_PRIVS` +
  `CLONE_NEWUSER` の seccomp 禁止)。
- 再発検知: 変異 M14 (capability 落としの除去) と M7 (seccomp installer の無処理化) が
  `orchestrator/mutation/t1994_spec.json` に登録済みで、本走で KILLED を確認した。

### {{F:parent-proposal-reopened-attack}}. 親が提案した設計が、閉じたはずの攻撃を開き直した [設計漏れ]

- 事象: 兄弟 entry の列挙が成立しないと分かったとき、親は「祖先を元の inode へ self-bind して
  非再帰で read-only にする」構成を提案した。実装後、**外側 namespace からの rename で
  source を差し替えられるようになっていた。**
- 根本原因: mount は dentry に付く。namespace の外にいる親が祖先を rename して同じ名前で
  別の tree を置くと、子が絶対 path を解決したときにそちらを辿る。
  **子の側からの rename は止まるが、外側からの rename は止まらない。**
  最初の probe が通っていたのは、祖先の最上段に private tmpfs を被せて
  **子の view を完全に private にしていた**からで、列挙をやめる過程でその性質まで落としていた。
- どう見つかったか: **攻撃テストが実走で捕まえた。** その test は
  「保護の外から同じ reader・同じ絶対 path で読むと B が見える」ことを**対照として先に確かめてから**
  「保護の中では A のはず」を測る形だった。対照が成立したうえで保護側が B を返した。
  login node でも再現したので環境要因ではない。
- 恒久対応: {{D:sealed-private-spine}} の構成 (`/` 直下に private tmpfs、spine だけ再作成、
  共有枝だけ fd から戻す)。
- 再発検知: 変異 M13 (spine を元 inode の self-bind へ戻す) が
  `orchestrator/mutation/t1994_spec.json` に登録済みで、本走で KILLED を確認した。
  捕まえる node には `test_qualification_source_attack_starts_and_is_blocked` と
  `test_sealed_snapshot_outside_ancestor_replacement_with_control` が含まれる。

### {{F:enumerating-churning-directory}}. churn する directory を列挙する設計は成立しない [設計漏れ]

- 事象: sealed の root view が spine の全段で兄弟 entry を列挙し 1 つずつ bind mount していた。
  計算ノードの焦点走で `[Errno 2] No such file or directory` が 92 件出た。
- 根本原因: テストの spine の最上段は `/tmp` で、**この計算機の `/tmp` には 145,596 entry ある。**
  列挙から `os.open` までの間に他 job が消した entry に当たって必ず `ENOENT` になる。
  仮に race しなくても、その回数の bind mount は所要にも mount 数の上限にも収まらない。
  production 側の `/work/1/SFC/tanab` も 212 entry あり、並行 wave が worktree を作り消ししている。
- **失敗本文が path を名指ししていなかったため、親は `/tmp` の entry 数を独立に数えて初めて
  原因を特定できた。**
- 恒久対応: {{D:sealed-private-spine}} で列挙を撤去し、mount 数を spine の深さ + 共有枝の数にした。
  あわせて mount・seal・unmount の失敗本文へ対象 path を入れた。
- 再発検知: 変異 M13 が同じ面を覆う。churn 進行中でも成立することを確かめる
  `test_sealed_snapshot_survives_spine_sibling_churn` を受入に置いた。

### {{F:orphan-codex-after-producer-kill}}. producer を止めても配下の実行体が孤児として編集を続ける [手順漏れ]

- 事象: job artifact の名前衝突に気づいて producer を停止したところ、
  **その配下の `codex exec` が孤児として生き残り、`buildcache.py` へ 223 行書き続けた。**
  次に投入した子はそれを「別 session が編集中」と見て正しく停止した。
- 根本原因: `DW-C00` は「生産者を止めるとき待ち手も落とし、その死も待ち条件に含む」と定めるが、
  **producer の孫にあたる実行体には触れていない。** producer と直子を kill しても孫は残る。
- 二次的な原因: 同一 wave 内で段 2 の plan 子と段 5 の実装子が同じ artifact 名 (`s2.*`) を使い、
  古い `.done` が残っていた。`DW-O02` は「過去 wave と共有しない」としか書いていない。
- 恒久対応: 停止後は **`ps` の全 process の cmdline を走査して、対象 worktree を cwd や argv に
  持つ実行体が 1 つも無いことを実測してから**次を投入する。中断した投入の再投入は
  `--job-id` を変える (attempt artifact が残って rc=2 になる)。
  job artifact の名前は**段ごとに固有**にする。
- 再発検知: 本 wave では次の子自身が「別 session が編集中」として停止し、
  親が実測してから継がせた。この停止は `DW-S05-A` の所有契約が働いた結果である。
- docs 反映 (段 8): **孫の残存確認だけを `DW-C00` へ収容した** (「停止後`ps`全cmdlineで
  対象worktreeの0件実測後に投入。」)。L1 層は追記前 10,619 / 上限 10,625 で残り 6 bytes しか
  なく、独立レンズ 1 本に意味等価な削減余地を探させたところ **6 箇所で 67 bytes** 出たので、
  D730 第 3 段 (上限引き上げ) は使っていない。**artifact 名の段別固有化と `--job-id` の
  差し替えは収容していない** — L1.5 の残りが 4 bytes で、同型の実測が本 wave の 1 例しかなく、
  D730 の原則 (実施しない) に落ちる。手順としては本項が正本である。
- 実測の限界: cmdline の path 一致が 0 件であることは、**その方法で見える実行体が 0 件**という
  意味でしかない。対象 path を argv にも cwd にも持たない子孫の不在は示せない。
