---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-md26-vhash-gc-connection-proof
seq: 1
title: VHash md_26: 前進を GC の回収境界へつなぐ構成 E が、まだ要る版を回収せず直列化も壊さないことを、floor だけで既読版を守る抽象仕様について一般の形で論証した。開始 floor の 3 条件・公開の規則・確認を始めた後は読まない条件 RA を前提にし、P5 を反例表に置いた (insight のみ、branch worktree-dev-wave-md26-vhash-gc-connection-proof)
---

## 本文

- 依頼: 並行 VHash wave の md_26 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_26.txt`)。新規の計測・探索・実装はしていない。対象 item は wave 開始時点の local main の「次の一手」に無かった (「GC 接続の一般の論証」で該当なし) ので、完了した作業は本エントリで記録し、関連する [T-2906]・[T-2907] を更新・完了にし、後続を新規登録した。
- 正本: `output/insights/2026-09-30/vhash-gc-connection-proof/README.md` (定理、範囲、抽象仕様 E、条件 FS-a/b/c・PUB・CAND・RA・REFS・RC とモデル・Cicada の対応行、補題 R・P・A・I、定理 G・S、公開の順序の図、各段が要る理由、反例との対応表、安全性と効き目の区別、Cicada で後で確かめる項目、未主張の一覧)。設計判断は {{D:vhash-gc-connection-proof}}。
- 段 1 の親の仮置き (floor だけで既読版を守れる) は、段 2 の起動後に親自身が「公開の後に新しく読んだ版は守れない」列 X1 に気づき、段 2 の起草も独立に同じ穴を指摘し、段 3 相談 A が列を完成させた。段 4 で条件 RA を置いた。段 6 レビュー A は初稿の RA (「公開の後に読まない」) が確認の成功と公開の間の読みを除かない列 X2 を作り、RA を「floor を上げる前進の確認を始めた後は読まない」に強めた。どちらの列も md_10 のモデルでは refs が守るので探索に現れない。
- 段 3 相談 A は、P5 型の列 (開始 floor の条件だけでは途中の引き上げを防げない)、Cicada の leader の非原子的な集計で開始 floor の条件 FS-b の導出が崩れる列 (害の完成列ではない)、read-modify-write で (I2) を「他 tx の後続版」に限る必要を作った。段 4 で親が、Cicada 型の待つ検査 W* の非原子的な走査で止まる予定の版が回収されうる紙の上の列と、md_10 の UG3 が GC 違反を出さなかったのは refs が覆ったため (D2300 の盲点と同型) である点を足した。
- 段 6 レビュー B は、定理 G が md_13 の A9 をそのまま置き換えるとした記述の隙間 (md_13 の補題 2 の場合 1 は、確認より前に設置された版 w 自身の保持を使う) を指摘し、回収された版を除いた列でも補題 1・2 の結論が保たれる補題 A を足した。数値・節番号・行番号の照合で食い違いは無かった。焦点再レビューは 3 巡 (上限) 使った。1 巡目 (NO-GO) は補題 A の選択で commit の検証が自分の PENDING 版を除く規則の欠落、外部 read の場合で既に回収された後続版を扱う段の欠落、公開値と floor の同一視 (max で公開するので一般には一致しない)、W* の列が経路 F の開始 floor の条件と両立することの書き漏れを、2 巡目 (NO-GO) は上端の走査の補題で回収の後に読んだ既読版に (I2) を当てはめる段の欠落を指摘し、親が直した。3 巡目は GO。残った partial 2 件 (工程記録が残る、未主張の説明が複数節に分散) は編集上の所見で論証に影響しないので直さなかった。
- 棄却した所見: なし (段 3・段 6 の所見はすべて real)。
- 実 repo を読む検査: 記録 commit の前に `python3 tools/check_docs.py` 違反なし、`python3 tools/spool_fold.py --dry-run` rc=0。受入は縮小受入 (D2316) を land の前に取る。
- セッション異常 (実害なし): 段 6 の待ちの間に、base digest を取るため共有の作業木へ `cd` し、隔離 guard が以後の Bash を拒否した。`EnterWorktree` の path 形で即座に戻れた (F100 と同型、md_22 の wave のような長い復帰は要らなかった)。
- エージェント工数: Codex plan 1・consult 2・review 2・focus 3 (いずれも gpt-6-sol、read-only)。実装子なし (実装面の差分ゼロのため変異 matrix は免除)。

## 次の一手差分

### 完了

- [T-2907] 途中入場の規則は md_26 の一次資料 §3 の開始 floor の条件で決めた: 登録時の floor f0 は開始時刻以下 (FS-a) で、それまでに GC が読んだどの境界以上 (FS-b)、登録後に他 tx が設置する版の wts は f0 より大きい (FS-c)。これで回収の後に入場する tx の時刻は境界以上になり、その書き込み検査は回収された版で止まらない (補題 P の 3)。小モデルに途中入場を足して確かめるかは、floor だけの経路の小モデルの新規 item {{T:vhash-floor-only-model}} に統合する。
  remaining: none
  base: 9027700dd43eaebca1bae1e77dd4190bc3d18b90465a69db27c3efb6807ce00b

### 更新

- [T-2906] **P2**: VHash の forwarding と GC 接続の一般論証が置いた仮定を、Cicada 実装と md_6 / md_14 / md_21 の試作で照らす。書き込み検査が条件 W* (待機解除後に status を観測し直し、ABORTED なら下へ進み、止まった確定版の rts を設置後に読む) を満たすか、W* の非原子的な走査で、通り過ぎた位置へ後から確定した版を根拠に止まる予定の版が回収されないか、読み検査が「rts 更新 → 観測し直し」の順か、stock の時刻生成が abort 後に同じ値を返しうるか (時刻の一意性と、開始 floor の条件 FS-a・FS-c が要る thread ごとの時刻の単調性)、leader が ThreadWtsArray と ThreadRtsArray を別々に読むことで新しい tx の開始 floor が既に公開された境界を下回らないか (FS-b)、構成 E で floor を上げる前進の確認を始めた後に read が無いか (RA、待機型以外の workload に安全点を置く場合)、MinRts = 0 付近の uint64 の減算、前進が PENDING 設置の前だけか、読み手と書き手の相互見落とし (記憶順序)。静的な読みで足りない項目は正しさ検査器で確かめる。根拠: `output/insights/2026-09-29/vhash-forwarding-proof/README.md` §5・§7、`output/insights/2026-09-30/vhash-gc-connection-proof/README.md` §6・§10。
  base: 3dde353c7c9a6cef225794a06259fd588cd690e8c7e5643301c220e3209594e8

### 新規

- {{T:vhash-floor-only-model}} **P3・新規**: VHash の GC 接続の小モデル (`tools/vhash_forwarding_model/`) に、refs を使わず floor だけで既読版を守る経路 (開始 floor を「以後に設置される版の wts より小さい」値にする) と途中入場を既定 off の option で足し、md_26 の一般論証の条件ごとの witness を取るかを判断する。対象: P5 型 (確認なしに floor を上げる)、列 X1・X2 (floor を上げる前進の確認を始めた後の読み)、既読不一致を無視する前進、FS-b を崩す入場。論証の証明ではなく、条件を 1 つ崩したときに J3 が出ることの固定場面の確認になる。根拠: `output/insights/2026-09-30/vhash-gc-connection-proof/README.md` §8・§11。
