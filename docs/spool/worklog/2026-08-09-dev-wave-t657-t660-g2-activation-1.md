---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t657-t660-g2-activation
seq: 1
title: pegasus 第 2 世代を活性化し head=2 で末尾巻き戻し検査を開いた ([T-657] + [T-660]) — floor 再発行はユーザー手番のため land していない (コード + docs、編集面 subset 333 passed、受入全走と変異は未実施、branch worktree-dev-wave-t657-t660-g2-activation)
---

## 本文

- **ユーザー裁定 (2026-08-08、`rulings-inbox/2026-08-04-rulings-session-5rulings.md` §44) に基づく wave。**
  「[T-657] = T-139 裁定後、前提 2 件 (silo 歴史解決・floor protocol 再発行) を揃えてから活性化」。
  前提 [T-627] (世代遷移述語) は land 済みを確認して着手した。
  一次資料は `output/insights/2026-08-09_t657-t660-g2-activation/`。
- **親の実測が brief の前提を 1 件撤回させ、scope を縮小した。** 活性化**前**の状態で committed silo
  evidence の `verify-result` を実走すると既に rc=1 で、失敗は
  `current binding mismatch: driver` と `raw attestation binding/ordinal set mismatch` の 2 件だった。
  driver の歴史 sha256 検査が先に発火するため **contract 検査に到達しない**。したがって contract 軸を
  historical 化しても受理集合は 1 bit も変わらず、`DW-G05` の成果物影響を書けない。
  production の `validate_current_bindings` 変更を **scope 外へ落とし**、前提 (a) の実体を
  「g2 活性化で新たに赤くなる面の除去」= テスト 1 箇所の current 依存の解消と定義し直した。
  T-529 の所見 B5 が実際に指していたのは production CLI ではなくテストだったことになる。
- **段 3 の敵対 2 レンズはいずれも NO-GO** (A = sol / must-fix 3、B = luna / must-fix 8)。
  両者が独立に一致した中核が上記の「committed 保全という主張と実受理集合の食い違い」であり、
  親の実走がそれを決着させた。A-2 (受理行列の追加) は production を変えない裁定により
  新受理集合が存在しなくなったため **一部 refuted** とした。
- **段 6 の敵対 2 レンズも NO-GO** (C = sol / must-fix 1、D = luna / must-fix 5)。
  C-1 は変異事前登録の誤りを突いた。空 chain guard を丸ごと無効化すると `rows` が未束縛のまま
  `ActivationState(...)` へ進み `UnboundLocalError` が漏れるため、変更前 HEAD 版でも production node が
  赤くなり「新テストだけが検出する」は成立しない。**理由文字列だけを変える変異**へ再設計し、
  受理集合の kill ではなく diagnostic sensitivity pin として集計を分ける裁定にした
  (親がコードで裏取り)。
- **D-4 は取り込みで前提ごと解消した。** レンズ D は「[T-530] の contract hash 束縛が未 land のまま
  activation-only を land すると、g1 の WAL COMMIT / campaign identity を g2 実行が再利用できる」を
  must-fix にした。campaign identity が env も date も含めない設計 (D13) と、WAL COMMIT が世代を
  区別しない `env_tag` しか持たないことは実コードで確認したが、**段 6 の直後に取り込んだ local main に
  [T-530] 本体が land 済み**だったため、land 前に経路が閉じた。
- **前提 (b) floor protocol の再発行は AI が実行できないと確定した。** 発行 CLI は
  isatty gate + T-080 receipt (active-valid) + create-only writer を要求し、`output/s8b-freeze/` への
  書込みは hook が拒否し、初回発行 commit も `AI-Agent: none` の人間 commit である。
  さらに `build_protocol_document` は呼び出し時点の current 契約から `contract_sha256` を焼くため、
  **活性化を適用した tree でしか再発行できない**という順序制約がある。
  したがって本 wave は **実装完了 + ユーザー手番の逐語 script を用意した時点で終端し、land しない。**
  活性化だけを land すると floor live admission と prediction seal が壊れた窓を main に作る。
- **再発行後の bytes を親が独立検算し、レンズ A の値と一致した。** 旧 774 bytes /
  旧 sha256 `261cec1c…` / 旧 bytes 中の g1 hash の出現はちょうど 1 回。期待される新 bytes は
  その単一置換であり、期待 sha256 は `c0eeed87ab1f449b97c0b7d88654a8c3a5c07fae3565dc90c5724e29f1cb660d`
  (長さ 774 不変)。この 4 条件を script の停止条件に事前登録した。
- **ユーザー手番の script は 3 度の must-fix を経て安全化した。** 原案は `mv` で tracked file を
  外へ出したまま復旧経路が無く、検査が表示のみで停止条件になっておらず、provenance preflight も
  欠けていた。最終形は `set -Eeuo pipefail` + trap で、失敗・中断のどの経路でも HEAD へ復元して
  HEAD/index/worktree の blob 一致まで確認し、冪等分岐と exact staged path 検査を持つ。
  実行ファイルであるため Codex `role=author` が書き、親は仕様と裁定だけを与えた。
- **受入全走と変異本走は実施していない。** floor 未再発行の tree では
  certified writer admission 系・floor 系・prediction seal 系が構造的に赤くなるためで、これらは
  `blocked/pre-floor` の期待赤であって回帰ではない。実施したのは編集面 4 file の実測
  (計算ノード、request 896505、22.21 秒、**333 passed**、非受入形) だけである。
  変異 spec の実 JSON も、`DW-M07` の anchor が再開時の tree と一致する保証がないため
  本走直前に作る裁定とし、設計 (5 件、うち 2 件は SURVIVED 期待) だけを凍結した。
- **worktree と branch を残す。** ユーザーが再発行 script をこの worktree で実行する必要があるため、
  背景 job の常例に反して畳まない。

## 次の一手差分

### 更新

- [T-657] **P1・ユーザー手番待ち**: pegasus 第 2 世代の活性化。実装・commit は完了
  (branch `worktree-dev-wave-t657-t660-g2-activation`)。残るのは前提 (b) floor protocol の再発行で、
  対話 shell 限定・T-080 receipt 必須・create-only・hook 拒否・`AI-Agent: none` commit のため
  **AI が実行できない**。同 branch の
  `output/insights/2026-08-09_t657-t660-g2-activation/reissue_floor_protocol.sh` を worktree 内で
  実行したのち、pin 3 件の更新 → 受入全走 → 変異本走 → land を fresh context で行う。
  前提 (a) は実測により「テストの current 依存解消」へ縮小して完了。
  base: 5bbbf44762f76230e5a720d8fb7ce639f1519aa7ed82f7c4e14eff2033c39f7a
- [T-660] **P3・実装済み・実測待ち**: production 層の末尾巻き戻し検査の検出力。head=2 になったため
  空 chain 拒否の mask が外れ、期待例外を head serial / state hash 不一致へ絞り、空 chain 拒否の
  理由を独立 node で固定した。**変異による検出力の実測は floor 再発行後の本走で行う**
  (設計は 5 件を凍結済み。うち serial 単独・state hash 単独は SURVIVED が正解で、
  対変異のみが実効 head pin の kill 証拠)。
  base: 6cde23c9936be6325596675ddadb7959e49c5e3002e69d5afb8f0c8dae0ec70b

### 新規

- {{T:silo-full-historical-lane}} **P2・新規**: committed silo evidence の完全な historical 再検証
  lane。現在 `verify-result` は contract 以前に driver / policy / verifier_module / runtime_modules /
  raw bundle を current bytes と比較するため、committed evidence に対して恒常的に赤であり
  誰も再検証に使えない (本 wave で実測)。記録 hash から歴史 blob を検証する独立経路を作るか、
  この CLI は新規生成 evidence 専用と明示して committed 再検証の主張を撤回するかの設計択一。
- {{T:t126-series-rotation-evidence}} **P3・新規**: g2 活性化で T126 の
  `qualification_series_id` が回転することを受入成果物で固定する。protocol admission は
  contract hash 非依存で不変だが、`env_contract.py` が code identity に入るため series は回る。
  旧 series の継続・再利用を拒否する named acceptance node が無い (段 6 D-6)。
