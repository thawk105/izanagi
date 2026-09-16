---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t1907-backoff-v1-patch-freeze
seq: 1
title: [T-1907] 式 v1 の silo-backoff-fixed.patch を別名で凍結し、旧 backoff consumer の裁定を閉じた (patch 1 本 + docs、branch worktree-dev-wave-t1907-backoff-v1-patch-freeze、変異 matrix = baseline PASSED・1/1 KILLED・SURVIVED 2 (登録どおり)・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「旧 backoff consumer について、v1 patch を別名で凍結する。裁定は D1281、8 件の WAL SHA pin を
  張り替える移行案は採らない。対象は既存 v1 の保存に限定する。[T-2647] と backoff 消費側が重なる可能性が
  あるので段 1 で編集面の重複を実測すること。本題の凍結だけ。仮想リスク向けの gate・検査・台帳・一般化の
  追加は scope 外」。一次資料は `output/insights/2026-09-16/t1907-backoff-v1-patch-freeze/README.md`。
- **実装は新規 file 1 本。** `patches/silo-backoff-fixed-v1.patch` に、合成枝の式が v2 へ変わる直前の
  patch (git blob `f7a5444…`、sha256 `35237d31…f911`) を bytes のまま Codex author が書き出し、
  親が `sha256sum` / `git hash-object` / `cmp` の 3 通りで一致を実測した。現行 patch・consumer の参照先・
  凍結 3 file・旧 sweep の 3 WAL の sha256 は plan 時点の値と全件一致 (不変)。設計判断は {{D:v1-patch-alias-freeze}}。
- **段 1 の前提実測で、起票時の懸念経路が現行コードでは成立しないことが分かった。** 現行 `backoff_sweep`
  が admission policy を束縛して導く campaign id は旧 3 campaign (`484c663e` / `493813a7` / `610004b9`) と
  3 件とも不一致で、旧 lock は admission policy を持たないため identity 照合が resume を拒否する
  (コードの読解、実走なし)。**ただし親はこれを「pin 破壊経路は閉じた」「止めている研究は無い」へ
  一般化して brief に書き、段 3 レンズ A が射程超過として退けた。** probe は site 設定を通していない
  3 構成だけを見ている。記録は限定表現に直した。
- **親 brief の事実誤りを子が 2 件直した。** 旧 3 WAL の生成日を「2026-06-22」と一括断定していたが、
  read-heavy の先頭時刻は 06-28 である。ホスト帰属も WAL の `env_tag` からは確定しない。
- **編集面の重複は 0 件だった。** `git worktree list` の 128 件を committed / dirty (HEAD blob と bytes 比較) /
  untracked の 3 方法で見て、`patches/` と凍結 3 file に触れる worktree は無い。backoff 消費側の他 file に
  触れる 20 件は本 wave の編集面と素集合。[T-2647] の残作業も本 wave の編集面に触れない。
  独立 clone・index だけの変更・将来の編集は観測外 (段 3 レンズ B)。
- **段 3 レンズ B が変異計画を 3 点直した。** (1) 作業ツリーの非 output 変更を一律拒否する
  `test_p3_b4_wiring_probe.py` の node を棚卸しから落としていた → 冗長 gate として runner 集合から除外。
  (2) runner の node 集合を固定しないと M1 の期待 node が完全集合にならない → 8 node に固定し、検出力の
  主張をこの集合に限定。(3) harness の spec は file 削除を表現できない → M4 を空 file 化へ変更。
- **変異 M1 (未登録 `IZANAGI_` token の追記) は KILLED、失敗 node は登録と完全一致。** これは新 file が
  既存の token 在庫 gate の走査対象に入ることの確認であり、凍結 bytes の正しさの検出力ではない。
  **M2 (式の改変) と M4 (空 file 化) は登録どおり SURVIVED** — 依頼が bytes pin の追加を scope 外としたので、
  runner 集合内の既存テストは式の改変も内容の喪失も検出しない。equivalent とは呼ばない。
- **段 6 の敵対レビュー子は省いた (DW-C00 の軽量版)。** 設計択一は段 4 で閉じ、実装は blob の bytes 複製で
  親の `cmp` / `git hash-object` が完全に検収でき、正しさ防壁と受理集合に触れないため。
- **README は既存の警告文を書き換えず、凍結小節だけを足した。** D1098 の「旧消費者はそのまま動き」を
  本 wave が実現したとは書いていない — consumer の配線は変えていない。
- 検査: 実装 commit の provenance は `--message-file` rc=0、full-history 監査 rc=0 (10,512 件、新規違反なし)。
  焦点走 10 passed (request `1591.nqsv`)。受入全走は本 fragment を含む docs commit の後に投入し、結果は
  land 前に本エントリへ amend しない (受入 receipt が一次資料)。
- 工数: codex 子 4 本 (plan 889 秒 / 15 call、consult 2 = 238 秒 / 9 call と 312 秒 / 15 call、
  author 126 秒 / 10 call)。全段 `gpt-6-astra` / `medium`。実装子 worktree `.codex/worktrees/t1907-u1`
  (branch `impl-dev-wave-t1907-u1`) は残置。

## 次の一手差分

### 完了

- [T-1907] D1281 のとおり v1 patch を `patches/silo-backoff-fixed-v1.patch` として別名凍結し、8 件の WAL SHA pin と
  凍結成果物には触れなかった。consumer の再配線と bytes pin は依頼の scope 外で、行わない。
  remaining: none
  base: baebbdf6990a1b13d90b1a0feb5894c9488030124b3b0923832adf3947840957
