---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t452-clock-tolerance-authority
seq: 1
title: [T-452] 実効クロック許容幅の権威設計案を起草し裁定パッケージで返した — 敵対 2 レンズの 12 所見を全採用、較正再登録は凍結 contract 世代まで波及する (docs のみ、受入 5900 passed、branch worktree-dev-wave-t452-clock-tolerance-authority)
---

## 本文

- 段 2 に codex read-only の設計起草 1 本、段 3 に敵対 2 レンズ (恒真ゲート / 整合・consumer) を並列で
  当てた。**両レンズとも NO-GO** を返し、所見 12 件は**すべて real** と裁定して採用した。refuted は 0 件。
  中心方針 (単一 policy 定数 `2.0` / observed 型分離 / 各 trust boundary での再検査 / issuer 独立実装の維持) は
  2 レンズとも支持したため破棄していない。
- **実装しない裁定** (`4→7→8→9`)。依頼が設計案の起草であることに加え、must-fix 2 件が他タスクの
  所有面と順序に触れるため親が独断で確定しない。実装差分が無いので**変異 matrix は射程外**である。
  段 3 が構成した変異 (いずれも「無効化しても現行/提案テストが緑」であることをコード上で確認済み) は、
  実装 wave が `DW-M01` で登録する候補として設計案 §5 に凍結した。
- **親が実測で裏を取った所見 3 件** — (a) receipt の nested observed は任意 key を許すため、
  observed 側 tolerance を注入した forged receipt が現 validator を通る。(b) 凍結された
  floor protocol が contract SHA を内包するため、較正の再登録は凍結 manifest 面まで波及する。
  (c) registry の canonical path 検査は `registered/` も content-addressed 名も要求しない。
  いずれも設計案の移行計画と保証範囲を書き換えた。
- 許容幅 `100` は **literal な恒真ではなく実質恒真**である (帯が `[0, 2*median]` になり、正の標本は
  median の 2 倍を超えない限り通る)。現登録較正は median から +46.641 % の標本を 1 個持ち、
  通すには 46.65 % 以上を要するため、**policy 値の選び方でこの artifact を救済する道は無い**ことを
  実測で確定した。
- 子の工数: 段 2 が約 13 分、段 3 の 2 本が約 9 分と 15 分 (いずれも codex `gpt-5.6-sol`、effort=high)。
  セッション異常なし。並行 wave が同時に 4 本走っていたが干渉は観測していない。
- 実装差分が無いため変異 matrix は射程外。記録 commit 後に `DW-S07` (F34 の恒久対応) に従い
  受入を全走させ **5574 passed / 19 skipped / 0 failed** (計算ノード request 888556、388.65s)。
  AI provenance 監査は merge 後の full 監査で 1134 件、違反なし。
- **land 直前に local main 30 commit を取り込んだ後、受入全走が緑にならず land せずに停止した。**
  赤は `test_reflux_origin_ledger.py::test_v04_global_flock_race_reentry_and_public_signature`
  ただ 1 件で、全走 3 回のうち **2 回赤・1 回緑** (request 888571 赤 / 888597 は別要因 / 888600 赤)、
  **同 file の単独走行は 18 passed / rc=0** だった。失敗点は `:711` の `assert probe_state ==
  "blocked"` で、別プロセス間の flock 競合窓を観測する負荷依存の assert である。当該テストは
  本日 main へ入った `e6349be` ([T-244] origin ledger prototype) 由来で、**本 wave の差分は
  docs のみ**であり当該 file にも `orchestrator/campaign/` にも到達しない。
  `DW-O18` に従い実装差分へ帰属させず、いったん `DW-STOP` で land せず停止して裁定へ返した
  ({{T:reflux-ledger-flock-flake}} を起票)。
- **既知赤 waiver W2 をユーザー裁定で新設した (2026-08-05)。** 発話は
  「既知赤として許可してください」。適用条件を次に釘付けする —
  (1) 対象は `test_reflux_origin_ledger.py::test_v04_global_flock_race_reentry_and_public_signature`
  **ただ 1 node のみ**、(2) 失敗点が `:711` の `assert probe_state == "blocked"` であること、
  (3) 同 file の単独走行が緑であること、(4) **他の赤が 1 件でもあれば適用せず停止する**、
  (5) 原因は並列受入全走の負荷下でのみ発火する競合窓の観測 (単独では再現しない)。
  **失効**: {{T:reflux-ledger-flock-flake}} の land で自動失効する。waiver は本 wave の
  docs のみの差分に対して適用したものであり、実装差分を持つ wave へ引き継がない。
- **land 直前の最終走行は waiver を使わずに緑だった。** 裁定後に local main 33 commit を
  さらに取り込んだうえで走らせた全走 (request 889209) は **5900 passed / 19 skipped /
  0 failed (rc=0)** で、当該 flake は発火しなかった。したがって **W2 は裁定済みだが本 land では
  適用していない** (条件と失効は上記のまま有効)。この node が全走 4 回中 2 回赤・2 回緑という
  非決定性を示した事実は、{{T:reflux-ledger-flock-flake}} の再現条件の一次資料として残す。
- **手順違反 1 件 (自己申告)**: 全走 (request 888597) の最中に本 fragment を編集したため、
  placeholder の参照だけが入り定義がまだ無い中間状態を `test_check_docs.py::test_real_repo_clean` が
  拾って赤くなった。整地後の `check_docs` は緑。`DW-O19` の「本走は統合 commit 後に限る」に反する
  操作であり、走行中は worktree を触らないこと。この赤は本 wave の成果物の欠陥ではない。
- 段 8 自己改善: 候補 1 件を検討したが不採用。「実装しない裁定の wave で受入全走が対象外」という
  `DW-S04` の射程は、`DW-S07` が docs commit 後の repo scan invariant 再走を別途義務づけているため
  穴になっていない (本 wave はその義務どおり全走させた)。契約変更は起票しない。

## 次の一手差分

### 更新

- [T-452] **P2・設計案完成 → ユーザー裁定待ち (U-1〜U-8)**: 権威は独立 leaf module の単一 policy 定数
  `2.0` とし、observed から tolerance field 自体を除いて手入力面 (投入 script → 環境変数 → job script
  → CLI の 4 段) を撤去する案を確定した。恒真化は値域ではなく**権威の一元化 + observed に tolerance を
  持たせない**構造で塞ぐ。裁定を要するのは U-1 配置 / U-2 固定値 / U-3 CLI 互換 / U-4 observed 表現 /
  U-5 schema 結合度 / **U-6 [T-453] との結合** / **U-7 contract 世代移行の所有** / U-8 landing 単位。
  U-6・U-7 は他タスクの所有面に触れるため親は推奨のみを書いた。
  一次資料 = `output/insights/2026-08-04_t452-clock-tolerance-authority/`
  base: 612608422bcc9ae5561e582b7d64dc7dba85eecf42208524ac36f30a411f3431
- [T-453] **P3・方向裁定済み → [T-452] の U-6 で結合を推奨**: `silo_ladder_rung1` の median 比較 2 箇所は
  loader・issuer・canonical consumer の**どの防壁も通らない独立経路**であることを [T-452] の敵対レンズが
  確認した。許容幅の権威を入れても、この 2 箇所だけは artifact 内の値で median どうしを比べ続けるため、
  同じ観測に二つの verdict が残る。別々に進めると同じ 2 箇所を二度変更する二重実装になる。
  推奨は authority 実装と**同一 landing closure** にすること (裁定は U-6)
  base: e45f576a704ba0f417d3a65b0a0795412e01e8927056a7a342030d41e7829536

### 新規

- {{T:calibration-contract-generation}} **P2・新規**: 較正の再登録は `contract_sha256` を動かし、
  それを内包する**凍結 floor protocol**まで波及する (`FROZEN_MANIFEST` に `output/env/` が無いことは
  影響なしを意味しない)。旧 protocol bytes を据え置けば current registry と照合する validator が拒否し、
  書き換えれば凍結 manifest・protocol SHA・selector journal・独立 golden が破れる。旧 contract を厳密に
  解決できるまま保持する**世代 (generation) 付き移行**を設計する。[T-419] U-2 の前提とするか U-2 に含めるかは
  [T-452] U-7 の裁定に従う
- {{T:reflux-ledger-flock-flake}} **P1・新規 (main が赤・land を塞ぐ)**:
  `test_reflux_origin_ledger.py::test_v04_global_flock_race_reentry_and_public_signature` が
  並列受入全走で **4 回中 2 回赤・2 回緑** (赤 = request 888571 / 888600、緑 = 888597 / 889209)、
  同 file の単独走行は 18 件緑。
  失敗点は `:711` の `assert probe_state == "blocked"` で、別プロセス間の flock 競合窓を
  観測する負荷依存の assert である。当該テストは `e6349be` ([T-244]) で 2026-08-04 に main へ入った。
  **これは main 側の非決定性であり、後続の全 wave の land を同じ形で断続的に塞ぐ。**
  timeout を伸ばすのではなく待ち条件を決定的にする方向で直す (競合窓の観測を、
  probe 側の到達を待ってから判定する形へ)。所有は [T-244] 系
- {{T:calibration-producer-provenance}} **P3・新規**: 許容幅の権威を固定しても、policy 一致かつ
  自己整合な JSON を合成すれば git 直接追加・attempt 複製・pin だけの更新・CLI 以外の producer から
  登録できる。registry の canonical path 検査は `output/env/<key>/calibration/` 配下を要求するだけで
  `registered/` も content-addressed 名も要求しない。content-addressed path の強制と publish receipt の
  束縛を**別の防壁**として設計する ([T-452] の保証範囲外と明記済み)
