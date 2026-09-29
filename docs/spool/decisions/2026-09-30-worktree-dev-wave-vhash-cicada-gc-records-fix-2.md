---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: worktree-dev-wave-vhash-cicada-gc-records-fix
seq: 2
---

## {{D:cicada-gc-records-fix}}. stock Cicada の削除経路の欠陥は、回収側 (gc_records) が aborted の版を読み飛ばす形と、scan の key を Tuple の複写から取る形で直す。受理集合を変える直し方は採らず、CCBench の local branch 2 commit と同じ差分の out-of-tree patch に置く

**決定:**
1. 原因 (診断で 10/10 実測): 後発の Delivery の削除版が read set 再検査で abort し、`writeSetClean()` が aborted にしたまま版鎖の最上段に残るため、先発の削除を commit した thread の `gc_records()` が ERR する。
2. 修理 1: `gc_records()` が最上段から続く aborted の版を何段でも読み飛ばし、到達した版が deleted なら回収、それ以外 (null・pending・committed) は ERR を残す。最上段の wts による待機判定、validation・commit・abort・版の install は変えない。
3. 修理 2: 修理 1 で表に出た既存欠陥 (scan が最新版の body から key を取り、body の無い削除版が最上段の行で key が空になる) を、作成時に複写される `Tuple::body_` の key を使い、空なら従来どおり最新版から取る形で直す。上流の「1 課題 1 文脈」に合わせ別 commit・別 patch。
4. 置き場: CCBench local branch `izanagi-cicada-gc-records-fix` (F `25898d00` の子 2 commit) と、同じ差分の `patches/fix-cicada-gc-records.patch`・`patches/fix-cicada-gc-records-scan-key.patch` (pin C → (計装) → 修理 1 → 修理 2 の順で厳密適用、`patches/ledger.json` には登録しない)。push と pin の前進は人間の手番 (D16・D18・D20)。
5. 確認は事前登録した観測 (修理自身が出さない量) で判定した: 修理版の完走と同じ job の無修理版の ERR、修理版 trace の判定器の数値 (巡回・integrity・存在履歴・C 行)、削除を含まない cell の判定不変、TRACE=0 の命令列一致、ASan、変異 (1 段だけ読み飛ばす変異は KILLED、read 再検査の壊しは判定器が巡回として検出)。

**理由:**
- 修理 1 は回収の判定だけを変え、どの tx が commit / abort するかを変えない。安全性は (i) 削除版の上に install された版は read set 再検査か write set 検査で必ず abort する、(ii) 回収可の時点 (最上段の wts < MinRts) で版鎖に実行中の tx の版は無い (thread ごとの wts の単調性と公開 rts の関係、group_commit=0)、(iii) 読み飛ばす aborted 版と削除版はどこからも解放されない、に依る (一次資料 §2)。
- ERR を残すので、本当に不整合な状態 (committed の版が最上段に来るなど) は従来どおり止まる。
- 修理 2 がないと修理版の trace が判定器に掛からず、依頼の完了判定 (並行下の削除を含む trace の判定) が取れない。CC 自体でも空 key は read-own-reads の key 照合を誤らせうる。

**却下した選択肢:**
- abort 時に install 済みの版を版鎖から外す — 並行する CAS・読み手の走査・版の回収と再利用の全部に触れ、小さな修理にならない。
- install 時に最新版が deleted / pending なら abort する — pending の削除と競合する経路を塞げず単独では足りず、受理集合を縮める。
- ERR を外す — 本当の不整合を隠す。
- 1 段だけ読み飛ばす — 診断で 2 段重なる例があり、変異走行で落ちた (KILLED)。
- 修理 2 を別 wave に回す — 依頼の完了判定に必要。
- ASan が見つけた `abort()` の use-after-free を同じ wave で直す — 削除経路と無関係の別の欠陥で、依頼の完了判定に要らない。次の一手に置いた。
