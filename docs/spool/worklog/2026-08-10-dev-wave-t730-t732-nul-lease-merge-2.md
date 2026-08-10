---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t730-t732-nul-lease-merge
seq: 2
title: 証拠 path の NUL を両防壁で拒否し、受入 lease の待ち手内 merge を正本化した — [T-732] は裁定前に実体が landed 済みで残余は精密化だけだった (コード + docs、受入 7982 passed / 20 skipped / 490.59 秒 / rc=0、変異 7/7 KILLED・事前登録と完全一致、branch worktree-dev-wave-t730-t732-nul-lease-merge)
---

## 本文

- **裁定の一次資料。** rulings-inbox §58 (2026-08-10、発話「推奨通りで」) の
  **[T-730] = (a) NUL 拒否** と **[T-732] = (a) 待ち手内 merge の正本化**。
  [T-730] の (b) C0 一般拡張、[T-732] の (b) lease 粒度拡大はいずれも不採用。
- **[T-732] の裁定前提は stale だった。** 裁定文の実体は commit `69379268`
  ([T-721] wave の段 8 自己改善、2026-08-10 15:02) が既に runbook §7.3 へ入れていた。
  裁定は同日の /rulings で後から確定したもので、**裁定時点で未見の新事実ではない**。
  親は裁定を不採用にせず、残余 (正本としての精密化) を本 wave の scope とした。
  repo 内に旧契約の残存記述は 0 件だった。
- **[T-730] の裁定前提は成立したが、brief の根拠は誤っていた。** 親は brief に
  「git の tree entry 名は形式上 NUL を含めないので凍結台帳に NUL path は存在しえない」と
  書いたが、**`evidence_contract_sha256()` は `load_contract_bytes()` を通らない**ため、
  凍結発行・検証は NUL path を含む契約 JSON を束縛できる (段 3 レンズ A が指摘、親が確認)。
  正しい根拠は内容検査であり、現行契約 JSON に `u0000` は 0 件なので再発行は不要という
  結論だけが残る。凍結層への gate 追加は承認外のため実装せず裁定へ返す。
- **段 3 レンズ A の指摘で probe を作り直した。** 初版は `cat-file --batch-check` の応答が
  blob record であることを確かめず、両方 missing でも一致しうる比較だった。v2 は blob 型・
  完全 OID・blob 本体の full sha256 を assert し、wave 前 source (`6a159e0d` の archive) に対して
  全通過した。以後の主張はすべて v2 を根拠にしている。
- **段 6 の敵対レビューが層 1 の迂回路を見つけた。** `"\x00" in value` は `str` サブクラスの
  `__contains__` を呼ぶため、membership を偽装した値が層 1 を素通りできた。直前 wave の
  `__format__` 迂回 (D267) と同型である。層 1 も exact `str` を作ってから検査し、
  その値を返す形へ直した ({{D:guard-input-exact-str}})。
- **同レビューが「検査は exact、返却は元 value」の退行を検出できないことも指摘した。**
  拒否テストだけでは `return` に到達しないためである。受理される `str` サブクラスを渡して
  `type(result) is str` を固定する正例を fix 子が追加し、対応する変異 M06 を事前登録へ足した。
- **変異 matrix は 7/7 KILLED で事前登録と完全一致** (SURVIVED 0 / MISMATCH 0 / TIMEOUT 0、
  baseline rc=0)。wave 前の実コードの逐語へ戻す変異 (M01 = 層 1 全体、M02 = 層 2) と、
  承認外の C0 一般拒否を入れる過剰拒否変異 (M03 / M04) の両方を含む。
  走行は `tools/mutation_worktree.py` の使い捨て worktree で行い、主 tree を変異させていない。
- **F196 の記述が stale なまま残る (未閉鎖)。** 同エントリは「runbook §7.3 の待ち手契約自体の
  改訂は本 wave の scope 外であり、裁定へ返す」と書いており、F197 と本 wave の正本化で
  supersede されている。**spool の failures fragment は `新規` と `再発` しか表現できず、
  既存エントリの状態が supersede されたことを書く節が無い**ため、fragment では直せなかった。
  ここに記録し、文法追加の可否は裁定へ返す。
- 段 3 レンズ B は「runbook 794 行の release 記述が [T-732] (b) 不採用と矛盾する」と
  must-fix で指摘したが、**親が D239 本文を読んで refuted した** — D239 は
  「受入と land の終端で必ず解放する」と既に定義しており、矛盾ではない。
- 親の brief が「docs は check_docs の byte 予算内」と書いたのは不正確だった。
  `docs/pegasus-runbook.md` は予算表に登録が無く、機械検査は §7.0 の dispatch 表の構造だけである。
- 受入 lease は本 wave が正本化した手順そのもので取得した (JSON の `state` を exact 比較、
  `acquired` 直後に main を取り直し、6 commit 遅れを待ち手内で `--no-ff` merge、
  再検査 0 を確認してから投入)。**1 回の claim で取得でき、空振りゼロ**だった。
- 逐語・変異台帳・probe 出力は `output/insights/2026-08-10_t730-t732-nul-lease/`。

## 次の一手差分

### 完了

- [T-730] 証拠 path の NUL を `_safe_path` と `read_blob_at` の 2 層で fail-closed 拒否した。
  受理集合の縮小は NUL を含む path と、偽装 dunder に依存して通っていた `str` サブクラスだけで、
  NUL-free の exact `str` と JSON 契約入力の受理・拒否・reason は不変。層ごとに TAB の正例を置いた。
  remaining: none
  base: 0115f16d590f1abed6792ac8d87d0f9d8f05c65fb89dd151760591e706e96c33
- [T-732] 受入 lease の待ち手契約 (runbook §7.3) を正本化した。裁定文の実体は `69379268` で
  既に landed 済みだったため、本 wave が入れたのは取り直しの明示、非 0 のときだけ merge、
  provenance 参照、rc 個別判定、`state` の exact 比較、2 走時の TTL 取り直し、残余 race の明記である。
  remaining: none
  base: fb17d81b408089ff5d76b972febdc14c6c8753a09e4e66b685f2538d2988607f

### 新規

- {{T:freeze-layer-nul-gate}} **P2・新規・ユーザー裁定待ち**: 凍結発行・検証層は
  `evidence_contract_sha256()` 経由で `load_contract_bytes()` を通らないため、NUL path を含む
  契約を凍結記録へ束縛できる (発効は後段で `evidence-contract-invalid` に倒れる)。
  選択肢 = (a) 凍結発行・検証にも NUL-only 検査を広げる / (b) 「invalid contract も凍結可能だが
  発効不能」という現行境界を維持し保証文をそこへ狭める / (c) `load_contract_bytes` 全体を流用する
  (NUL 以外も拒否するので受理集合が変わる)。推奨 = (a)。成果物影響 = (b) のままなら
  凍結台帳・proof chain の受理集合に NUL path 契約が残りうる。現行契約 JSON には 0 件。
- {{T:canonical-acceptance-waiter}} **P2・新規・ユーザー裁定待ち**: 受入 lease の待ち手は
  runbook の散文手順しか正本が無く、各 wave が書き直している。実際に旧 wave の script は
  `state` を glob 判定していた。選択肢 = (a) `tools/` に正本 script を新設し runbook から参照する /
  (b) 散文手順のままにする。成果物影響 = (b) のままなら consumer が取り込みを省いて受入を投入し、
  受入結果が land 不能になる。実装面の新機構なので裁定前に着手しない。
- {{T:spool-failures-supersede}} **P3・新規・ユーザー裁定待ち**: failures fragment は
  `新規` と `再発` しか表現できず、既存エントリの記述が supersede されたことを書けない。
  本 wave は F196 の stale な記述を直せなかった。選択肢 = (a) `supersede 追記` 節を
  fragment 文法へ足す (`見送り追記` と同型の 1 行挿入) / (b) worklog 記録で足りるとして直さない。
  成果物影響 = (b) のままなら後続 reviewer が裁定済みの項を未裁定と読む。
- {{T:guard-non-str-input}} **P3・新規・ユーザー裁定待ち**: 証拠 path 防壁の保証を
  「単一文字列化した後の値」に限定したままにするか、`bytes` / `os.PathLike` 自体も検査対象に
  するか。後者は既存の受理集合を変えるため無裁定では足さない。推奨 = 現行維持。
