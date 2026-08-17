---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1255-floor-freeze
seq: 1
title: 床値 v2 protocol を AI が実発行し、live consumer を resolver へ配線した — 裁定が名指しした tty の閂は実凍結の経路ではなかった (コード + テスト + 凍結記録、branch worktree-dev-wave-t1255-floor-freeze)
---

## 本文

[T-1255] の実凍結を AI が実行し、[T-419] (3) の配線を同一 wave で完了した。
一次資料 = `output/insights/2026-08-17_t1255-floor-freeze/`。

**発行物**: `output/s8b-freeze/floor-protocols/e576e9cd…--511c9538….json`、774 bytes、
sha256 `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a`。
組は現行 pegasus 契約 `e576e9cd…e242c01` と HEAD の gitlink `511c9538…3b706ec`。
`reseal-protocol` を親が実行した。tty も PTY 偽装も使っていない。

**「`ccbench_pin` 以外 1 byte も動いていない」を機械検証した** — field 集合は legacy と 18 件で一致、
値が違うのは `ccbench_pin` ただ 1 欄、byte 差は 40 bytes の pin 置換ちょうど 1 箇所 (残り 734 bytes 同一)、
legacy bytes は不変 (`261cec1c…`)、repository の差分は新規 1 file のみ。

**「旧 protocol を退けた」は削除ではなく解決優先度の後退として実装した。** legacy は
`FROZEN_MANIFEST` 23 key と系譜 anchor が bytes を縛るため削除できない。発行前は
`resolve-current-protocol` が legacy を返し、発行後は versioned artifact を返す (両方とも実測)。

**裁定の前提のうち失効していたもの。** 裁定文が閂として名指しした `freeze_protocol` の
`sys.stdin.isatty()` は、v2 実凍結の経路ではなかった。実経路は零引数 public issuer
`reseal_protocol()` (`230fc757`、2026-08-16 14:27 着地) で tty gate を持たない。
`freeze_protocol` の destination は legacy anchor 自身で、既存のため create-only で必ず失敗する。
**裁定 inbox の逐語ではユーザーの言葉は「床値の操作？あなたでできるものを私にやらせないで。」の
1 文だけ**で、`freeze_protocol`・tty・「旧 protocol を退ける」は rulings 側の親 AI が付けた分析である。
したがって手段の訂正はユーザー裁定の上書きではなく、別 AI の分析の誤りの訂正にあたる。

**実際の閂は 2 つあった。** (i) 発行すると現行契約に一致する候補が 2 件になり resolver が
fail-closed する。(ii) 解決先を versioned へ移すと、凍結成果物の権威が Git の commit から
作業ツリーへ後退する (段 3 レンズ A が発見)。(ii) を塞がずに (i) だけ直すのは規律 2 違反になるため、
committed-only 権威を同 wave の scope に入れた。詳細は {{D:floor-protocol-committed-authority}}。

**敵対検証 4 本すべてが NO-GO を返した。** 段 3 の 2 本は「ユーザー再裁定が要る」を根拠にしていたが、
裁定 inbox の逐語で崩れた。段 6 の 2 本が挙げた must-fix 3 件 (作業ツリー権威、固定 commit の伝播、
副作用前の拒否) は採用して実装した。

**段 6 レビュー D の断定が実測で覆った。** 同レビューは「発行後に赤くなる既存 node は 0 件」と
根拠つきで断定したが、実測では 1 件あった (`test_real_seal_protocol_to_floor_official_core_e2e`)。
レビューは index / resolver を直接読む node を探しており、「供給した protocol が admission で
拒否される」形の破断は検索から漏れた。**発行という不可逆操作の前に「赤ゼロ」の断定を
信用してはならない**という実例である。

**親の訂正**: 段 4 で「official preflight と v2 candidate producer は official mode の CLI 拒否の
背後で休眠」と書いたが理由付けが不正確だった。v2 candidate producer は独立した公開 CLI から入れる。
休眠の実際の理由は予算承認が未設定で official floor result が 0 件であること。

**変異は生存 2 件を等価変異と構造で示して再照準した。** probe 走で
`len(head_exact) == 1` の件数判定と record の `commit_oid` 整合検査が生存した。前者は index の key が
`(contract_sha256, ccbench_pin)` で一意なので `head_exact` が常に 1 件以下、後者は同じ走査で
同じ値を入れているので恒真であり、どちらも構造上等価だった。実効 gate へ再照準した結果
SURVIVED は 0 件になった。

## 次の一手差分

### 完了

- [T-1255] 床値 v2 protocol の実凍結を AI が実行した。`ccbench_pin` 以外が 1 byte も動いていないことと、
  旧 protocol が解決先から退いたことを実測で確認した。
  remaining: none
  base: 1f57e37e36e32be62f0ccd0b80a29c7415d3a499382d6ad5de9ac47445c34fbe

### 更新

- [T-419] **P2・(3) 実施済み、残りは見送り裁定済み**: (3) 床値 protocol path の shell 層・driver 層の
  配線を実施した。shell wrapper と `s8b_holdout_admission._authority` を resolver 経由へ移し、
  証明鎖の歴史錨定 3 件 (`s8b_prediction_runner`、`s8b_ratified_freeze`、`s8b_holdout_freeze`) は
  移すと過去の受理集合と生成 bytes が変わるため据え置いた。(1)(2) は 2026-08-17 /rulings 全件 第 4 回で
  見送り裁定済み。本項に残るのは下記 3 件の未接続面であり、いずれも official mode の解禁が発火条件。
  base: a0995343a3c4cba10827189a56d34a1efb73efcc4976400e899544653f8cad49

### 新規

- {{T:floor-driver-cli-caller-selection}} **P3・新規**: 床値 driver CLI の `--protocol` が
  caller 選択面のまま残っている。段 6 レビュー C / D が real と判定した。ただし本 wave の
  「供給 protocol の権威不一致を最初の副作用の前に拒否する」実装により、不一致は build・
  run directory・binary store・manifest のいずれよりも前で止まる。公開 CLI 契約の変更を伴うため別 wave。
- {{T:official-preflight-versioned-protocol}} **P3・新規**: official launch preflight
  (`_PREFLIGHT_FIXED_FILES` と legacy bytes 比較) が versioned protocol を受け付けない。
  official mode は CLI で拒否中のため今日は休眠。解禁時に配線する。
- {{T:v2-candidate-producer-versioned-protocol}} **P3・新規**: v2 candidate producer
  (`s8b_holdout_freeze.generate-v2-candidate`) が legacy path を固定で読む。独立した公開 CLI から
  入れるが、予算承認が未設定で official floor result が 0 件のため今日は到達不能。
- {{T:floor-protocol-worktree-mode-drift}} **P3・新規**: committed-only 権威は bytes 一致を要求するが、
  commit 後の `chmod` による作業ツリー側の mode drift は拒否しない。段 6 レビュー C の C-3。
  祖先 directory の symlink 差し替え競合 (C-4) も同じ枠で扱う。どちらも攻撃者を仮定した
  防御的堅牢化であり、既定方針に従って見送った。
