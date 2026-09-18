---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: worktree-dev-wave-t2777-cleanup-hardlink-fix
seq: 1
title: [T-2777] dev_wave_cleanup.py の hardlink 拒否を registry file と object store で分けた — admin dir 配下の object 名前形 (loose / pack、refs・logs 配下を除く) の regular file に限り nlink>1 を許容し、registry file の拒否は不変。段 9 の自己撤去 (DW-O28) の rc=20 (F1026) の恒久対応 (コード + テスト、branch worktree-dev-wave-t2777-cleanup-hardlink-fix、変異 matrix = baseline PASSED・M1〜M5 KILLED 期待 node 完全一致・等価 M0 SURVIVED・MISMATCH 0)
---

## 本文

- ユーザー依頼は「[T-2777] (P1、F1026、entry 1641) tools/dev_wave_cleanup.py の _read_admin_file が admin dir 配下の submodule object (modules/**/objects/**) の hardlink を st_nlink != 1 で拒否し、DW-O28 の自己撤去が submodule 初期化済み worktree の全数で rc=20 になる欠陥を直す — registry file と object store の検査を分け、正例 (hardlink 入り admin dir で撤去成功) と負例 (registry file の hardlink は拒否) を変異登録する。案は insight §3.2。[T-2778] は含めない。Codex author (D95)。docs/dev-wave/*.md を触るなら稼働 t2290 / t2447 と起動時に照合する。着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の局所修正だけ」。
- **閉じた。** 一次資料は `output/insights/2026-09-18/t2777-cleanup-hardlink-fix/README.md` (verbatim 17 件、変異台帳 3 走)。実装 commit は 94715928d (1 巡目) と fbd8c7038 (fix 1)。decisions fragment 0 (新しい設計判断なし。分類規則の択一 (名前形 vs 構造規則) は wave 内の親裁定として insight §3 と `verbatim/s4-ruling.md`)。failures fragment 1 (F1026 の supersede 追記)。docs/dev-wave/*.md は触っていない。
- 分類規則は object の**名前形** (`modules/…/objects/<2hex>/<38|62hex>`、`modules/…/objects/pack/pack-<40|64hex>.<ext>`、`modules` と末尾 3 component の間に `refs`/`logs` を含まない) だけで決める。構造的規則 (`objects` の親 dir に `HEAD`+`config`) は、撤去が名前順で `HEAD`/`config` を `objects` より先に消すため部分撤去後の再入で生きた snapshot が誤分類して詰まる、として却下 (段 4)。object file では読取中の安定性検査から nlink/ctime を外す (他 worktree の local clone が同一 inode へ link を張る。本 wave の admin dir で nlink 275〜288 → 293 の増加を実測)。
- 段 3 consult A が plan の述語 (中間 component に `objects`) を must-fix (ref 名 `objects/topic` 等の registry file を受理) と指摘 → 段 4 で名前形へ。段 6 レビュー A が親の名前形にも must-fix (合法な ref 名 `objects/ab/<38hex>` の loose ref と reflog が名前形に一致) → fix 1 で `refs`/`logs` を除外、負例 2 case 追加。レビュー B は GO。焦点再レビューは A1 closed、製品コード must-fix なし、**変異登録の must-fix** (fix 後の末尾 return だけを恒真化しても 760/763 行の `if` が残り M1 は生存) → final v1 は erratum として保存し、M1 の anchor を述語本体全体にした v3 で 6/6 一致。親の見落とし: 段 4 で「ref 名が object 形になることは害が無い」と見送った点 (レビュー A が不変条件 (i) との衝突として real 化)、M1 の anchor を fix 後に再検討しなかった点 (焦点再レビューが投入直後に指摘)。
- 受理集合の限界 (裁定済み、追加実装しない): `objects/info/*`・`multi-pack-index`・`pack-*.bitmap` 等の名前形外の補助 file の hardlink、submodule path 自体が `refs`/`logs` を含む真の store は現行どおり rc=20 (fail-closed)。object の ctime だけに残る改変履歴の検出は弱まる (撤去直前の length+sha256 一致は残る)。
- 実測: 焦点走 150 → 152 passed (1 巡目は計算ノード 4.4 秒、fix 後 login 14.1 秒)、consumer `test_pytest_collection_config.py` 76 passed。変異 matrix は container worktree (fbd8c7038) で harness 直接 + dispatch: probe (94715928d) 6 走 5 分で予測と完全一致、final v1 は M1 SURVIVED (erratum)、final v3 は M0 SURVIVED / M1 (負例 6) / M2・M3 (正例 + linked + None-gitdir) / M4 (race[registry]) / M5 (新規負例 2) KILLED、MISMATCH 0。受入全走 attempt 1 = child-green (tested main 1e844bcbc / tip 3d44403f2、25,095 passed / 69 skipped、17 分、他 wave 受入 leader 3 本と同時、受入調停 thread の通知は「中断しない」)。
- 段 9 の自己撤去 (本 wave 自身の worktree、admin dir に hardlink 31 件) は本エントリの凍結後に走るため rc はここに書けない。最終報告に載せ、次 wave の worklog に記録する。unit1 worktree (`.codex/worktrees/t2777-unit1-cleanup`、終端 commit 2 本) と変異 container (`.codex/worktrees/t2777-mutcontainer`) は DW-O28 どおり unlock し、撤去は D703 の例外外なので残す。
- 工数: codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1、全段 `gpt-6-astra` / medium)。計算ノード job: 焦点走 2、consumer 1、変異 19 走、受入 1。

## 次の一手差分

### 完了

- [T-2777] 実装した。分類は object の名前形 (refs・logs 配下を除く) で、registry file の拒否は不変。正例 1・負例 6・race 2・recovery 2 case を変異登録し M1〜M5 KILLED / M0 SURVIVED。段 9 の自己撤去の rc は次 wave の worklog へ。
  remaining: none
  base: 5517eeb3d59bd5ad4761a68af4478d23006425bd563107d6e1028294e59a443f
