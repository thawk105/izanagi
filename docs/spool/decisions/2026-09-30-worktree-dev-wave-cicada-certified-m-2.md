---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: worktree-dev-wave-cicada-certified-m
seq: 2
---

## {{D:cicada-m-implementation}}. Cicada の中間案 M は最良設定 (inline 版) まで範囲に含め、読み束縛は GC を止めない検出型の世代番号で照合し、壊しの帰属は tx 単位にする

**決定:** D2305 項 4 の中間案 M を次の形で実装した (一次資料 `output/insights/2026-09-30/cicada-certified-m/README.md`)。
1. 範囲に `INLINE_VERSION_OPT=1` (promotion 0) を含める。inline slot の返却・再取得を、非 inline 版の回収・再利用と同じ 3 関数 (`gcAfterThisVersion`・`newVersionGeneration`・`writeSetClean`) の分岐で世代の事象として数える。
2. B (読み束縛) は版に TRACE 専用の世代番号を置き、事象を seqlock と同じ 2 段 (開始で奇数・終了で偶数) で進める。読み手は read set 登録の直前に「世代 → wts・status・所属 tuple → fence → 世代」の snapshot を取り、奇数・前後不一致・別 tuple・未確定・読み手より新しい版を `B_WINDOW`、tx の終わり (commit・read-only・abort) の世代の不一致を `B_RETIRED` とする。読み手は GC を止めない。
3. U は設置 (validation の CAS 成功)・公開 (`cpv()` の store の前後の status 確認)・W 行の三者照合と、公開時の wts と C 行の版の照合。主張は `cpv()` を通る公開に限る。
4. read 側 API は `read()` の呼び出し単位で照合する。
5. 正例は壊し 3 本 (B = P5 型、U = 公開後に write set から外す、API = 登録を飛ばす)。B の帰属は (thread, tx 通番) が壊しで下限を実際に上げた tx であることで判定する。
6. 合否は repo 外の起動器が決め、判定器 (`orchestrator/verifier/`)・campaign・既存 patch は変えない。

**理由:**
- 比較相手の観測最良設定と構成 E / E-max の実測がすべて `INLINE_VERSION_OPT=1` の上にあり、範囲外にすると D2305 項 4 (2) の性能値の地位をそれらに付けられない。inline の事象は同じ 3 関数に置けるので追加の費用は小さい。
- 読み手が tuple の GC 権を握る排他は、`gc_versions()` が権利の取得に失敗した回収予定を捨てるので TRACE ビルドの回収挙動を変える。検出型の snapshot は回収を止めずに、登録前の窓で版が別 tuple・別状態・新しい版に化けた場合を検出する。残る場合 (同じ key の別の確定可視版として一貫した snapshot) は、その版の読みとして記録と実行が一致する。
- 壊し B は tx 単位で読み取り下限を動かし、その tx が読んだ全版が回収の対象になるので、帰属の鍵は tx 単位が機序に合う (版単位の鍵は事象行が tx ごとに 1 版しか書かないので 1,925 / 6,988 件しか一致しない)。

**却下した選択肢:**
- inline 版を範囲外と明記する — 主比較の性能値を M の地位に上げられない。
- 版の外の事象台帳 — 並行時の順序付けが重く、登録前の窓も台帳だけでは閉じない。
- 読み手が GC 権を保持する排他 — 回収予定を捨てるので観測対象の挙動を変える。
- B の帰属を (thread, tx 通番, 版) で判定する — 壊しの機序に合わず、発火した正例を不合格にする。
- 判定器に新しい行種別を足して certified にする (案 A) — D2305 項 4 のとおり、Cicada を門に通す campaign の登録時に着手する。
