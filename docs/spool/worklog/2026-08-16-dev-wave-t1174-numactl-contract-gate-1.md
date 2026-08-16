---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1174-numactl-contract-gate
seq: 1
title: 裁定が受入条件に挙げた変異検査と敵対検証を [T-1174] へ供給し、契約照合後に launch prefix を書き換えられる経路を塞いだ — 実装本体は同日別 wave が先に land 済み (コード + テスト、branch worktree-dev-wave-t1174-numactl-contract-gate、変異 matrix = 13/13 KILLED)
---

## 本文

- **裁定の実装本体は同日 19:47 に別 wave が land した。** 本 wave は [T-1174] 択 (d) の実装として
  起動したが、段 6 の途中で peer 通知を受け、親が local main を直接読んで裏取りした
  (main = `6d905fc2`、実装 commit は `f689d716`、branch `worktree-dev-wave-t1174-numactl-verify`)。
  **判定式の「どちらが勝つか」は争わず、land 済みの形を土台として本 wave 固有の増分だけを
  載せ直す**方針を親が裁定した。
- **判定式の差は安全差ではなく診断差だった。** 本 wave の HEAD 側は権威に
  `_env_contract.lookup(env_tag)` を使い `None` を gate で拒否していた。land 済みは
  `authorization_contract.contract` と `tuple(numactl or ())` を使う。両者の差で拒否される入力集合は
  変わらない — どちらの形でも、直後の認可検査が同じ入力を拒否する。よって land 済みを採った。
- **裁定が挙げた受入条件は、本 wave が供給している。** 裁定文は「実装は判定式の変更にあたるため
  **変異検査と敵対検証を受入条件とする**」と定めていた。land 済み entry (599) には変異検査・
  敵対検証の記録が無い (本文 300 行を機械検索して 0 件)。本 wave は変異 matrix 13/13 KILLED と
  codex 4 レーン (段 3 相談 2 + 段 6 レビュー 2) の敵対検証を実施し、その両方を land 済み判定式を
  含む最終形に対して回した。
- **敵対レビューが検査の穴を 4 件出し、いずれも production ではなくテスト側だった。**
  (i) 空 list `[]` の正規化が未固定で、truthy だけ tuple 化する誤実装が全テストを通過した。
  (ii) bench の `measure_point` 呼出は `record_rep_returncodes` で 2 分岐するが、検査は既定の
  False 側しか通っていなかった — **qualification はこの値を必須にするため、実運用側が丸ごと
  未被覆だった**。(iii) 動的検査は trace 実行関数自体を差し替えるので、その内側で launch prefix を
  落とす変異が全テストを通過した。(iv) 「正規化は qualification 検査より後」という親が明示裁定した
  受理集合の境界を、どのテストも守っていなかった。2 レーンのうち (ii) は 2 本が独立に指摘した。
- **その 4 件を閉じたことの効果が変異で測れている。** `pipeline.py` を 1 byte でも変えると
  `contract-loader-drift` (disk bytes が記録 commit blob と不一致) で 43 node が意味に関係なく
  落ちるため、この共通核は過剰決定する mask であり単独変異の証拠から外した ({{F:mutation-core-mask}})。
  核を差し引いた delta で帰属すると、bench の True 分岐で prefix を落とす変異と、実 trace 起動の
  argv から prefix を落とす変異は **delta=1 で、段 6 fix が足した検査だけが唯一の killer** である。
  レビュー前はこの 2 つが mask に完全に埋もれていた。
- **親の段 1 での一般化を敵対レビューが正しく限定した。** 親は probe 3 本から「契約不一致側の
  純増検出力は 0」と結論したが、これは「同一 snapshot・有効な current authorization・不変な引数」
  という条件下でのみ成立する限定命題である。無条件の主張としては反証された。
- **古い authorization による過剰拒否は現行 registry では到達不能と実測した。** 敵対レビューが
  「保持された古い receipt と現行 registry がずれると gate だけが拒否しうる」と指摘したので、
  親が全世代の numactl を実測したところ **env_tag ごとに一意** (linux-baremetal g1 のみ、
  pegasus g1/g2 とも空) で、世代差による numactl の食い違いは構造的に発生しない。
  発火条件は「numactl の異なる世代を新規登録したとき」または「authorization 失効を伴わない
  snapshot 更新機構を新設したとき」であり、`DW-G04` に従い実装せず設計メモに留めた。
- **land 済み判定式の診断上の弱みを 1 件観察した (production は変えない)。**
  `tuple(numactl or ())` は str を 1 文字ずつの tuple へ分解するため、list/tuple 以外の型を
  渡すと認可検査の型エラーではなく「launch prefix が契約と一致しない」という的外れな診断で
  拒否される。両方 fail-closed で sink 書込みも無く成果物影響が無いため `DW-G05` に照らし
  must-fix とせず、テスト側の期待を実挙動へ合わせた。
- **環境事象**: Pegasus login node で `tools/run_tests.py` の bounded local が 2 回連続で
  `bounded scope の memory.max / memory.oom.group を走行中に attest できない` により
  `rc=16` (テスト 0 件) になった。赤ではなく基盤側の失敗で、本 wave の全実測は
  `--force-dispatch` 経路で行った。
- **codex 子は `git merge` を起動できないと実測した。** sandbox の Git 管理領域が read-only で
  `ORIG_HEAD.lock: Read-only file system` により merge 開始前に失敗する。実装面の main 取り込みに
  Codex `role=author` の合成監査を要求する規律を満たすには、**親が merge を起こして競合マーカーを
  作り、子は working tree の競合解決だけを行う**分担にする必要がある ({{F:codex-child-cannot-git-merge}})。
- **工数**: codex 子 7 本 (plan 1、consult 2、author 1、review 2、fix 2 のうち merge 失敗 1 を含む
  実質 8 起動)。変異 harness は probe 2 巡 + 本走 2 巡 = 4 巡 (判定式が main の形へ変わったため
  anchor 5 件を再照準し期待 node を再導出した)。

## 次の一手差分

### 完了

- [T-1174] 裁定 (択 (d)) の実装は同日別 wave が `f689d716` で land 済み。本 wave は裁定が
  受入条件に挙げた変異検査 (13/13 KILLED) と敵対検証 (codex 4 レーン) を供給し、
  land 済み実装に無かった launch prefix の immutable snapshot 化と検査 4 層を載せた。
  remaining: none
  base: cca5de486fed1251ebc0962bb29aea473d580336f568d23d877620c7ea86b74b

### 新規

- {{T:numactl-invalid-type-diagnostic}} **P3・新規**: `tuple(numactl or ())` が str を
  1 文字ずつの tuple へ分解するため、`numactl` に list/tuple 以外の型を渡したときの診断が
  「launch prefix が契約と一致しない」になり、真因 (型が不正) を指さない。fail-closed 性と
  sink 無書込みは保たれており成果物影響は無いので、運用診断の質だけの問題である。
  判定式の手前で型を検査するか、認可検査の型エラーを先に走らせるかの選択になる。
- {{T:stale-authorization-numactl-divergence}} **P3・新規**: gate の権威 (保持された
  `authorization_contract.contract`) と現行 registry がずれると、gate だけが承認済み入力を
  拒否しうる。現行 registry では全 env_tag で numactl が世代を跨いで一意なため到達不能と実測した。
  発火条件は「numactl の異なる世代の新規登録」または「authorization 失効を伴わない snapshot
  更新機構の新設」。どちらかが起きた時点で、権威の単一化か更新の原子性固定を検討する。
