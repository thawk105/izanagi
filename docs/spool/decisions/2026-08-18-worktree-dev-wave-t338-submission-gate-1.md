---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-18
wave: worktree-dev-wave-t338-submission-gate
seq: 1
---

## {{D:t338-gate-sizing}}. 投入 gate は「階級で切る」ことができない — 規模を実測し、B1 の閂を凍結 bytes 不変で外し、費用の判断をユーザーへ返す

**背景:** 2026-08-18 のユーザー裁定は T-338 Q1 = 択 (a)「投入 gate を 1 単位で完成」を定め、
同時に「着手前に規模の見積りを実測で出し、D205 / D220 の水準に触れるなら同 wave 内で
範囲を切り直すこと」を条件に付けた。本 wave はその実測 wave として起動した。

**決定 (1): 本 wave は実装しない。** 実装差分はゼロであり、変異 matrix は `DW-S04` により免除される。
コード・テスト・gate・schema・artifact・凍結 bytes・certified 選択・材料レポート・proof chain・
受理集合はいずれも不変である。一次資料 = `output/insights/2026-08-18_t338-submission-gate-sizing/`
(裁定パッケージ本体は `package.md`)。

**決定 (2): 規模を実測し、切り直し条件が発動することを確定した。** 独立 3 見積り —
親 1,650〜3,450 行 (過小と判定された)、段 2 プラン 2,570〜3,740 行、
段 3 レンズ B 3,550〜6,200 行 (6 層接続込み)。いずれも production のみで tests を含まない。
repo 実測の test/production 行比 2.18 を掛けると総計 8,000〜19,700 行。
D220 が D205 のプロトタイプ基準に照らして過大と判定したのは production 645〜816 行であり、
本件は下限で 3.2 倍、上限で 7.6 倍である。

**決定 (3): 「検査の階級で切る」戦略は成立しないと実測記録する。** 親は D205 の逐語
(「絶対規律と科学的妥当性に直接効くものだけを採り、それ以外の防御的堅牢化は既定で見送る」) に
従い、承認済み要件を A 級 / B 級へ分けて B 級を見送る案を出した。段 2 プランが承認済み要件
63 件を**全件独立に分類**した結果、D320 の見送り対象と判定されたのは受領証 schema digest の
manifest pin と conformance vector index の digest pin の **2 件だけ**であり、しかも
manifest への sha256 1 field と既 land pin の読取 1 行で実現できる。**切っても規模は動かない。**

**決定 (4): 親の切り直し 2 案を撤回する。** 段 2 プランと段 3 敵対レンズ 2 本が独立に、
どちらも承認済み受理述語の緩和であると判定した。起動命令は「規律 2 を緩める方向の変更は
採らない」と定めており、親はこれを採れない。

- **階級による見送り案の撤回:** append-only 全履歴検査、受領証 writer の認可と pointer 検査、
  および対応する schema 外責務は、raw 証拠のすり替えと attempt 脱落を直接防ぐ A 級である。
- **全履歴検査を粗い機構へ置換する案の撤回:** 台帳を truncate / 削除して過去の使用を現在集合から
  外し、同じ `(family_root, ordinal)` を再作成すれば、現 tip の `k = 1` も初出 commit の祖先性も
  成立する。累積有意水準のリセットが通る。**承認済み記録項目 §0.2 が同じ穴を既知として
  逐語で記録していた** — 親はそれを読まずに案を書いた。

**決定 (5): B1 を凍結 bytes 不変で閉じる経路を実測した。これが本 wave の主要な前進である。**
T-139 の裁定パッケージ V1 は「新 exact-byte approval payload を作らずに B1 を閉じる案は
(a) semantic validator を常時拒否 (受理集合が空) か (b) CMakeCache leg を落とす (弱化) の
2 つしかない」と実証したと書いていた。**第 3 の経路が実在する。**

- CCBench の `external/ccbench/cmake/Options.cmake:59-67` の `ccbench_universal_definitions` は
  解析フラグと trace フラグを target_compile_definitions として吐く。よって CMakeCache の 2 値は
  各翻訳単位の compile argv として `compile_commands.json` に必ず現れる。
- 凍結済み受領証 schema は `compile_commands` を `fileRecord` (path/size/sha256) として既に持つ。
  検証側が bytes を再読できる実体である。
- 承認済み記録項目 §6.3 の逐語は第 3 脚を「`cmake_cache` の**申告値**」と定義しており、
  raw `CMakeCache.txt` の再読を要求していない。
- 同 §0 は「producer が申告した派生値は、受理集合を狭める方向にだけ使う。不一致を拒否理由にし、
  一致は受理の正の根拠にしない」を既に定めている。

したがって V1 の新 approval payload は不要であり、**D320 との衝突は消える。**
これは D500 が「producer を止めている閂」と同定した箇所の直接の解除である。
採否は Q-C としてユーザー裁定へ返す (親の推奨は採用)。

**決定 (6): 再利用先を確定する** (D500 決定 (6) が次 wave の段 1 要件と定めたもの)。

- **採る:** `orchestrator/qualification/attempt_ledger.py` の hash 連鎖 replay と連番 create-only
  event を T-139 用 module へ移植する。同 file の series 台帳クラス自体は T-126 固定
  (64 桁 series ID、一初回 + 最大一 retry、write capability 束縛) なので直接使わない。
- **採る:** 同 package の private-token 型 opaque write capability を `PreregBinding` の
  構造的先例とする。
- **採る:** `orchestrator/campaign/trial_registry.py` の祖先検査 (D234 が「同型」と名指しした
  当の関数) と commit tree からの blob 取得。ただし S8c import graph を避けるため、
  `orchestrator/preregistration/blobref.py` の衛生化 Git 実行面を公開 helper へ抽出して使う。
- **採る (書き直しつき):** 原子公開と、排他生成 + 全量 write + fsync のパターン。
- **採らない:** T-126 の SPRT / subject-reference 二者 FSM に固定された series module。
  holdout admission の台帳本体 (同 file 自身が「排他生成は file が存在する間だけ効く。
  この耐性は保証範囲外」と明記)。T-126 の script path / protocol に固定された identity module。
- **新規実装が要る (親の「無料再利用」判定の訂正):** path の**各 component** を `O_NOFOLLOW` で
  辿る読取 (既存は最終 component のみ)。canonical bytes を強制しない duplicate-key 拒否 JSON
  reader (既存は承認外の canonicality を一緒に強制するため、流用すると受理集合を承認なしに狭める)。

**決定 (7): 実装単位を 6 つに確定する。** 編集 path が素集合になる分割で、依存順は
`1 || 2` → `3`, `4` → `5` → `6`。1 = manifest / binding / Git 基盤、2 = 受領証 IO / schema、
3 = semantic validator と申告値の拒否専用化、4 = 全履歴検査と attempt authority、
5 = writer と conformance vectors、6 = 統合と 4 名前 export。
**4 名前の export は単位 6 の最終 commit だけで行い、同じ commit で非 export 検査を
all-or-none 検査へ置換する。** 半 export しない。

**決定 (8): ユーザー裁定へ返す 3 問を確定する。**
Q-A = 投入 gate に production 2,570〜6,200 行を投じるか
((a) 投じる / (b) RF study 系列を畳む / (c) 承認済み受理条件を明示的に縮小する新 decision を起こす)。
**親は Q-A に推奨を付けない** — 費用の判断であり親が決める性質ではない。
Q-B = D229 決定 (8) の必須 kill 3 件の帰属段 (親の推奨は validator / consumer 段)。
Q-C = B1 の閉じ方 (親の推奨は決定 (5) の第 3 経路)。

**却下した選択肢:**

- 受領証 IO と schema だけの shape-only 単位を land する — consumer が 0 件の未結線 leaf であり、
  D147 決定 (3) / D163 決定 (1) / D500 が却下した型である。
- 全履歴検査を現 tip 検査へ置換して gate を完成扱いする — 決定 (4) のとおり累積有意水準の
  リセットが通る。承認済み文書が同じ穴を既知として記録している。
- 恒真 deny の投入入口を置いて 4 名前を export する — D264 が名指しで却下している。
- 段 3 レンズ A の「申告値の拒否専用化は 3 者一致を 2 者一致へ弱める」を採る — refuted。
  §6.3 の逐語自身が第 3 脚を申告値と定義しており、レンズが挙げた反例
  (実 cache が 1 で configure・compile command・申告値が 0) は凍結 schema に raw pointer が
  0 件である以上どの実装でも検出できない。拒否専用化に固有の弱化ではなく schema 自身の限界であり、
  保証境界へ書く事項である。
- 規模を理由に承認済み裁定 (Q1 = 択 (a)) を親が不採用にする — `DW-S04` は親が不採用にせず
  新事実を添えてユーザー再裁定待ちへ戻すことを定める。

**研究状態への影響:** `pilot_submission = forbidden` / `main_submission = forbidden` は
1 bit も動いていない。D264 の 4 名前非 export も維持されている。実装差分はゼロであり、
certified 選択の値・材料レポート・proof chain・凍結 bytes・既存 gate・受理集合はいずれも不変である。
変わるのは、gate の実装規模が実測で確定したこと、「階級で切る」戦略が死んだこと、
B1 の閂が凍結 bytes 不変で外れる見通しが立ったことの 3 点である。
