---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1223-snapshot-submodule-gate
seq: 2
title: snapshot oracle の submodule 未初期化 fail-open を無条件 gate で塞いだ — 親の深さ限定案を敵対相談が反証し、期待 node 集合の誤りをレビューが本走前に止めた (コード + テスト + docs、branch worktree-dev-wave-t1223-snapshot-submodule-gate、変異 matrix = 6/6 KILLED)
---

## 本文

`verify_snapshot` は submodule manifest を必ず作りながら、照合するのは caller が spec で
`submodule_manifest_sha256` を渡したときだけだった。既定 spec は 9 key しか pin せず submodule 系を
含まないため、既定経路では照合節が常に不発で、CCBench の作業木を持たない snapshot が reason 0 件で
正規と認定された。記録は正しく判定だけが fail-open で、先行 wave が作った穴ではない。
経緯・実測・残した穴は `output/insights/2026-08-16_t1223-snapshot-submodule-gate/`。

### 親の provisional 裁定を段 3 が反証した

親は brief で「深さ 1 の submodule だけ initialized を要求する」を (P1) として置いた。根拠は
`DW-O20` の起動手順が非再帰 init であることだった。段 3 のレンズ B が high 確信度で反証し、
親が一次資料で裏取りした — 受入 claim 前の `preflight-submodule-ready` は再帰 status の未初期化を
rc=2 で拒否し、runbook も投入前の再帰初期化を要求し、archive の [T-1124] は非再帰 init で
独立 2 wave が受入停止を踏んだ事例を記録している。したがって正当に運用された作業木は全深度が
初期化済みであり、深さ限定は不要だった。親は (P1) を撤回して全行要求へ変え、
副次的に深さ算術ごと消して兄弟 path 誤認の型を排除した。設計判断は
{{D:snapshot-submodule-initialization-gate}}。

レンズ A は逆に「全深度を要求しない裁定を支持する」と書いたが、根拠は `docs/dev-wave/operations.md` の
起動手順だけで、受入 preflight の実装を読んでいなかった。**2 レンズが同じ論点で逆の結論を出したので、
親が実装と runbook と archive を自分で開いて裁定した。**

### 親 brief の実測誤りを 1 件訂正した

brief は「当該 tool の bytes を pin する台帳は無い」と書いたが、検索を `--include=*.py` に限ったため
`output/insights/2026-08-09_t181-certified-rerun/apparatus-pin.json` の `tool_sha256` を落としていた。
レンズ A が反証。実測では pin の値と現行 tool の sha は本 wave 以前に既に乖離しており、
Python の live consumer も 0 件だったので、歴史記録として不変のまま残した。
T-1223 後の tool は T-181 certified rerun の装置 identity とは別物である。

### 恒真でないことを変異で実測した

「新検査が既定の受入走行で一度も発火しないなら恒真な保証」という段 3 の指摘に対し、判定式を反転する
変異と恒真化する変異では、合成テストに加えて実 repo 由来の 3 node が error になることを実測した。
この 3 件は変異ハーネスの `FAILED` 行抽出には現れず ([T-1225] の同型を独立に再現)、親が `-rfE` で
別途採取した。ハーネスの期待 node 集合には含めていない。

### 変異事前登録の誤りをレビューが本走前に止めた

親が裁定文の対応表をそのまま `expected_nodes` へ転記したため、6 件中 3 件の期待集合が誤っていた。
段 6 のレビューが本走前に 3 件とも指摘し、親が各変異を一時注入して実測で再導出してから登録し直した。
F28 の再発として記録した。本走は 6/6 KILLED、MISMATCH 0、SURVIVED 0、baseline PASSED。

### scope 外の real 所見 2 件

いずれも本 wave が作った穴ではなく、実装せず起票した。(a) `initialization == "initialized"` は
内容の実在を保証せず、「正しい HEAD を持つ空の CCBench」は今も通る。(b) 中間成果物層
(`collect_run` / `make_packets` / append・freeze・reveal CLI) は snapshot を再検証しない。

### 受入で踏んだ非帰属の赤

受入全走は複数回投入した。1 走目は
`test_dev_wave_wait.py::test_public_main_real_signal_after_success_uses_restored_handler` が 1 件赤で、
これは [T-1227] が既に記録している同一 node のフレークである。2 走目は
`test_codex_worker_launch.py` の `test_check_receipt_rejects_impossible_truth_table` /
`test_check_receipt_rejects_unknown_and_duplicate_fields` /
`test_setsid_escape_is_not_claimed_as_contained` の 3 件が赤で、捕獲 log の一次資料では
launcher subprocess が **rc=1・stdout/stderr ともに空**で落ちており、48 並列下の資源圧の形である
(3 failed / 11878 passed / 92 skipped / 95.28 秒)。

4 件はいずれも本 wave の差分が到達しえない file にあり、**親が単独再走で緑を実測した**
(1 走目の 1 件 = 1 passed / 2.63 秒、2 走目の 3 件 = 3 passed / 3.38 秒、いずれも計算ノード)。
`check_acceptance_reds.py` は 4 件とも `attributable-red` と判定したが、これは
[T-1227] が起票している「1 標本ではフレークと帰属を区別できない」限界そのものである。
本 wave はこの判定を実装差分へ帰属させず、受入を再投入した。緑になった走行の receipt が land の権威である。

### 段 8 の候補と結末

候補 1 は「変異の期待 node を裁定の対応表から転記せず、注入・走行・復元で実測してから登録する」。
発火点は `DW-M01` なので同節へ 1 行統合を試みたが、`docs/dev-wave/**` の L1 unique footprint が
予算 10625 bytes に対し 10739 bytes になり `check_docs` が赤になったため撤回した。予算引き上げは
自己改善に含めないので、恒久対応は F28 の再発本文に残した (意味は保存されている)。
候補 2 は `tools/dev_wave_wait.py producer` が、生産者が生存し `--artifact-file` も `--done-file` も
不在の状態で rc=0・無出力で戻った観測。原因を特定できていないので docs は変更していない。

### 工数

codex 子 6 本 (plan 1、敵対相談 2、実装 1、レビュー 2)。実装子は dispatch preflight rc=1 で
pytest を走らせられず「実装済み・未実走」と正しく申告したため、焦点走・ベースライン・
期待 node 再導出・変異 matrix はすべて親が回した。

## 次の一手差分

### 完了

- [T-1223] `verify_snapshot` の submodule 未初期化 fail-open を無条件 gate で塞ぎ、
  負例 4 + 正例 2 を合成 repo で追加した。変異 matrix 6/6 KILLED。
  remaining: none
  base: f5d5aa873039ddddf1b25809412e37ad7e06680c184581cd862c9fad98f843a6

### 新規

- {{T:submodule-content-identity-gate}} **P1・新規**: `initialization == "initialized"` は
  内容の実在を保証しない。`_submodule_worktree_state`
  (`tools/codex_reasoning_ab.py`) は「submodule path が Git top-level」かつ
  「HEAD == gitlink」で initialized を返し、`.git` marker と期待 admin dir の束縛、
  index と `HEAD^{tree}` の一致、worktree bytes と index の一致を検査しない。
  親 repo 側で `submodule.<name>.ignore=all` を設定すれば root の status / numstat も汚れないので、
  **正しい HEAD を持つ空の CCBench** が snapshot oracle を通る。空または改変済みの CCBench を
  読んだ試行が「pin 済み」として trial ledger・材料レポート・proof chain に載りうる。
  三者照合を入れると manifest 層の受理集合と実行コストが変わるため [T-1223] では scope 外とした。
- {{T:snapshot-verification-in-intermediate-layers}} **P2・新規**: 中間成果物層が snapshot を
  再検証しない。`collect_run` は launch receipt の oracle SHA を転記するだけ、`make_packets` は
  manifest を直接読み `verify_manifest` を要求せず、append / freeze / reveal の CLI は
  snapshot gate を通らない。正規 supervisor 経路の certified decision は閉じるが、
  receipt・材料 packet・verdict freeze は未認証 snapshot 由来でも生成できる。
  「aggregate の valid だけが certified で中間 packet は未認証」と明記するか、
  `collect_run` と `make_packets` に frozen oracle の再検証を要求するかを裁定する。
