---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-forwarding-proof
seq: 1
title: VHash の選択的 forwarding の中核規則 (reader は rts を上げてから観測し直す、writer は PENDING を越えて最初の確定版まで検査する) が直列化可能性を守ることを、md_4 仕様 v1 について一般の形で論証した。範囲・仮定 A1〜A11・補題と証明・反例との対応表・未主張の一覧を一次資料にした (insight のみ、branch worktree-dev-wave-vhash-forwarding-proof)
---

## 本文

- 依頼: 並行 VHash wave の md_13 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_13.txt`、投げ直し分。md_8・md_10 の結果を前提として参照する指示つき)。新規の計測・探索・実装はしていない。対象 item は wave 開始時点と land 直前の local main の「次の一手」に無かったので、完了した作業は本エントリで記録し、後続を新規登録した。
- 正本: `output/insights/2026-09-29/vhash-forwarding-proof/README.md` (定理の一文、範囲、仮定 A1〜A11 とモデルでの根拠行、補題 1〜3・定理 4、系と備考、Cicada 型の待つ検査の補題 2′ と条件 W*、反例との対応表、後で確かめる項目、未主張の一覧、Mermaid の構成図と 2 場合の順序図)。設計判断は {{D:vhash-forwarding-proof-scope}}。
- 段 1 の親の仮置き (書き込み側を 1 つの性質 WP で R9' と Cicada の待ちの両方に通す、md_10 を「発火の契機を問わない」根拠にする) は、段 2 の起草と段 3 の相談 2 本がそろって退けた。段 4 で定理を R9' に固定し、Cicada 型は条件付きの別補題に、発火契機からの独立は証明が R4 を使わないことから示す形に改めた。
- 段 3 相談 A (反例を作る側) と段 6 レビュー A (論理・反例) は、主張の範囲の中で定理を破る列を作れなかった。相談の must-fix だった「複数 writer のとき W の検査が v に届くこと」は、違反状態で確定している版のうち wts が最小のものを取り、確定・abort が吸収状態であることを使って帰納法なしに閉じた。
- 段 6 レビュー B (過剰・削除と事実照合) は、一次資料の数値・場面・反例の step 数・J1⇒J2 の列挙を原表と照らして食い違いなしとした。must-fix 2 件 (仮定 A9 を「既読版が W の検査時に版列に残り走査対象になる」に強めること、段 4 で採用した 2 場合の順序図の未反映) は親が直した。焦点再レビューは 2 巡使った。1 巡目は、親が直すときに補題 2 の主張を確認の前の状態まで広げたことが未証明だと指摘し (範囲を「確認の成功より後」に戻した。補題 3 にはそれで足りる)、2 巡目は強めた A9 の文面が場合 2 と両立しないと指摘した (条件付きに直し、指摘の示した文面どおりの局所修正なので 3 巡目は起動せず親が照合して閉じた)。
- セッション異常 (実害なし): `EnterWorktree` が名前形では filter driver の読取エラー、path 形では worktree 一覧の 10 秒 timeout で失敗し、手動の `git worktree add` は 1 回目が checkout 中の EINTR で失敗した (2 回目 rc=0)。`tools/dev_wave_submodule_init.py` は git の timeout と update-no-fetch の失敗で 2 回 rc=1 になり、手動の再帰初期化 (file transport 許可つき) を 2 回で googletest まで揃えた。いずれも同時刻に別 session の worktree 作成・撤去が多数走っていた局面。待ち手を同じ条件に 2 本張り、気づいて 1 本を止めた。
- エージェント工数: Codex plan 1・consult 2・review 2・focus 2 (いずれも gpt-6-sol、read-only)。実装子なし (実装面の差分ゼロのため変異 matrix は免除)。

## 次の一手差分

### 新規

- {{T:vhash-proof-assumptions-in-impl}} **P2・新規**: VHash の forwarding の一般論証が置いた仮定を、Cicada 実装と md_6 試作で照らす。書き込み検査が条件 W* (待機解除後に status を観測し直し、ABORTED なら下へ進み、止まった確定版の rts を設置後に読む) を満たすか、読み検査が「rts 更新 → 観測し直し」の順か、stock の時刻生成が abort 後に同じ値を返しうるか (時刻の一意性)、前進が PENDING 設置の前だけか、読み手と書き手の相互見落とし (記憶順序)。静的な読みで足りない項目は正しさ検査器で確かめる。根拠: `output/insights/2026-09-29/vhash-forwarding-proof/README.md` §5・§7。
- {{T:vhash-proof-late-entry-gc}} **P3・新規**: 途中で入場する txn を許すとき、GC が既読版を回収した後に小さい時刻の writer が入場して書き込み検査が既読版に届かなくなる (論証の仮定 A9 の破れ) のを防ぐ規則 (入場する txn の時刻を回収の境界より大きく取る等) を決め、小モデルに途中入場を足して確かめるかを判断する。根拠: 同 README §8 の注。
