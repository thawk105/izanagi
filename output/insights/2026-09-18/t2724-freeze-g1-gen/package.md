# 裁定パッケージ — [T-2724] 世代導入 G はできたが、chain (X1') を main へ載せると受入全走が赤になり oracle の gate も閉じる

`authority: none` / `default_effect: no-state-change`。**裁定済み (末尾の「裁定」節、2026-09-18、ユーザー委任)。** 本文書は本 wave (`dev-wave-t2724-freeze-g1-gen`) が実測した
新事実と択を並べる。決めるのは人間。G の作成 (D2120 項 2 (b) の AI 手番) は完了し、branch
`freeze-g1-gen-t2724` (G `32ba8cae45001697f050bee377413153e6d798a5`) と wave branch `worktree-dev-wave-t2724-freeze-g1-gen`
(merge `88d02046644acff922937f2c5c10cbf10da2413b`) に保全した。land はしていない。

## 新事実 (D2120 項 2 (a)(d) の裁定時に未見)

前 wave の一次資料 (`output/insights/2026-09-17/t2724-freeze-v2-g1-candidate/README.md` §8、`package.md` (d)) は、chain が main に
載ると赤になる test として growth hold 中の 2 本を記録したが、hold 外で実 root を読む test と production gate への波及を列挙して
いなかった。D2120 項 2 (d) はその材料で「帰結を記録して現行 hold のまま」と裁定した。本 wave が X1' + G を含む wave 木で
実走した結果 (README §4・§7):

1. **非 held の test 45 node が赤になる** (焦点走 `test_s8b_oracle_driver.py` 40 + `test_s8b_floor_campaign.py` 5、
   45 failed / 967 passed / 11 skipped、計算ノード request 5001.nqsv)。node ごとの assertion 本文は
   `evidence/failure-table.txt`。原因は 4 経路で、いずれも X1' の official run_dir 3 file (journal / manifest / result) が三軸
   conjunction に hit すること:
   - (i) T-080 fixture が実 root の git-visible な output を複製し、draft の live scan (`_draft_reconstruct_holdout` →
     `search_repository` → `_assert_search_pass`) が hit — 10 node
   - (ii) 実 committed HEAD を clone して official preflight の clean scan (`clean_scan_digest`) を通す — 5 node
   - (iii) oracle driver の `run_block(root=ROOT)` が T-080 receipt を実 root で解決 (`verify_receipt`、process 内 memo で共有) し、
     `state=invalid` を `_campaign_t080_value` が拒否して `status: refused` で戻るため、後段の WAL / lock / marker / budget 契約
     test が期待する status・例外・呼出しを得られない — 29 node
   - (iv) 公開 driver gate の refusals に v1 `verify` の live scan 拒否が混入し exact 集合と不一致 — 1 node
   G の世代文書は `output/s8b-freeze/` prefix 除外の内側で走査 hit を増やさず、`resolve_active_generation` は `no-active` のまま、
   `clean_scan_digest` の allowlist も世代文書名を chain record として受理する。確認した走査 refusal はすべて X1' の 3 path 由来
   (対照走はしていないので「G が全 test に無影響」までは主張しない)。
2. **production の oracle gate が閉じる。** 実 root の T-080 receipt 解決は `state=invalid`、refusal
   `holdout-freeze-verify: [holdout.unknownness_layer2] FreezeError: rr80: holdout hit 3 件 …; rr20: …` (親の probe、407 秒)。
   runbook §2 P3 `gate-check` は rc=2、`allowed=false`、refusals 4 件 (`evidence/p3-gate-check.log`)。機序 (段 6 レビュー A が
   現物で検証): `s8b_oracle_driver._make_gate_decision` は receipt 解決の refusal を無条件に merge し、`run_block` はさらに
   `_campaign_t080_value` で invalid receipt を拒否する。`gate_check` / `run_block` は v2 処理に先立って receipt を解決し、active v2
   による skip は無い。**したがって現行の receipt・実装・hit を保ったまま A / X を作って g1 を active にしても、X1' を含む
   checkout では driver の gate は refuse される** (コード上の帰結)。v2 の `launch_validate` は closure 関連 artifact の
   occurrence から期待集合を導出して全走査との完全一致を要求する (C2-4) のに対し、T-080 (v1 移行 receipt) の live scan は
   zero-hit を要求し、v2 世代の世界で両者が矛盾する。
3. 帰結: D2120 項 2 (a) 択 1 (chain を main へ) を実行すると、(1) により受入全走が赤で land できず (本 wave と並行 wave (a) の
   両方)、仮に載せても (2) により oracle は動かない。(a)+(b) だけでは 8b oracle 実走に到達しない。

## 択

各択は独立に投げられる。いずれも正しさ gate の受理集合か test の検出力に触れるため、実装は裁定後 (D96: 新 D + 境界 test)。

- **(A) chain + G の main 取り込みを保留し、T-080 receipt 解決の live scan と v2 closure の整合を production 側で先に設計・裁定・
  実装してから載せる。親の推奨。** 理由: 主経路 (oracle 実走) に到達する択であり、G と chain は branch に保全済みで可逆、保留の間
  main は official 床値を起動できる。設計案の候補 (AI が起草できるのは設計案まで。実装は人間が候補を採った後):
  - (A-1) T-080 live scan の期待集合を、**承認済み (active) v2 世代**の artifact (protocol / result / journal / manifest /
    measurement closure) から `launch_validate` と同じ occurrence 検証で導出し、全走査との完全一致を要求する。未批准の候補 data
    が期待集合を定める形は採らない (規律 6: data は authority ではない)。除外集合の拡大はしない。
  - (A-2) v2 世代が active なら driver の gate は T-080 receipt を要求しない。receipt の何を置換し何を残すか (静的検証、epoch
    束縛、`_campaign_t080_value` の campaign epoch) を設計で定義しないと広すぎる。
  - (A-3) receipt の静的検証と epoch 束縛は維持し、重複する未知性層 2 (`_verify_holdout_live_scan`) だけを承認済み v2 の full
    launch validation による検証へ委譲する。実現可能性・同等性の検証が要る (段 6 レビュー A の提案)。
  いずれも受理集合が変わるので新 D + 境界 test + 変異 matrix、規律 2 を緩めない。着地後に test 側 (経路 (i)(ii)) を追随させ、
  chain + G の land を再開する (後発 wave は先発の fold 後 main を固定 SHA で merge して再受入)。
- (B) test 側だけを直して受入を通す (T-080 fixture と実 HEAD clone test を official namespace のない合成 tree にし、
  oracle_driver の実 root receipt memo を fixture 化)。45 本は緑になる見込みだが (2) は残り、oracle は動かない。受入だけを通す形。
- (C) 当該 45 node を growth hold に足す。検出力の削除であり D2120 項 2 (d) の趣旨 (除外集合を広げない) と規律 2 に反する。
- (D) D2120 項 2 (a) を撤回して chain を保存 branch に留め、A / X と oracle も別 branch で行う。(2) は X1' を含む checkout なら
  branch を問わず起きるので解決にならない。

## 依存と手番

- 人間が (A) 系を採ったら、設計 wave (AI 手番、設計案の起草まで) → 人間が候補 (A-1 / A-2 / A-3) を裁定 → 実装 wave
  (Codex author、新 D + 境界 test + 変異 matrix) → 着地後に本 wave の branch と並行 wave (a) の branch を main へ取り込む。
- A / X の人間手番 (README §5) は上の着地後、G と X1' を含む branch 上で行う。T-750 P-1 / P-3 は別管理のまま。
- 本 wave は受入全走を投入していない (赤が確定しているため。赤の受領証は取らない)。land していない。前 wave の資料は直接
  編集せず、本資料と worklog で訂正する。

## 裁定 (2026-09-18、ユーザー委任「codex に相談して決めて」)

read-only codex 2 レンズ (正しさ境界 `artifacts/…/s10-a.md`、実効性・順序 `s10-b.md`、job dir) が一致し、親が次のとおり決めた。
記録は本 wave の decisions fragment (slug `t080-receipt-defers-unknownness-to-active-v2`、番号は fold が付ける)。

- **択 A、設計候補 A-3。** receipt の履歴・静的検証・epoch 束縛・`_make_gate_decision` の集約・`_campaign_t080_value` の拒否は
  維持し、承認済み active v2 の `launch_validate` が同一 root・HEAD・世代で成功した場合に限り、未知性層 2 (zero-hit 判定) をその
  完全一致検証へ委譲する。未発効の木と official clean scan は従来どおり拒否。走査除外・hold・chain と G の bytes・A / X の境界は不変。
- **4 経路 45 node の test の実 root 切り離し (負例維持) を同じ実装 wave に含める** (A-3 だけでは A / X 前の受入が成立しない)。
- **設計 wave と再裁定を分けず**、新 D + 境界 test + 変異 matrix + 段階別 preflight 文書を Codex author の 1 wave に収める (D96)。
  A-3 の同等性を境界 test で示せなければ停止する (検査を省略して通さない)。
- **順序:** 整合 wave を chain の無い main へ land → 本 wave が保存 branch の X2 と fold 後の main を固定 SHA で merge し X1' + X2 + G
  を 1 wave で受入・land → 人間 A / X (README §5) → W-4 spec (T-750 P-1) → W-5。
- 却下: A-1 (C2-4 の二重実装)、A-2 (置換範囲が広い)、E (走査免除の拡大)、B 単独、C、D。

相談で確認した事実: main は `a0ccb8ad9` へ前進、並行 wave (a) は entry 1640 で「land せず再裁定へ戻した」記録だけを着地 (X1' / X2 は
main に無い)。よって chain を運ぶ wave は本 wave 1 本になり、merge-base 2 つの問題は本 wave が fold 後の main を固定 SHA で取り込む
ことで回避する。
