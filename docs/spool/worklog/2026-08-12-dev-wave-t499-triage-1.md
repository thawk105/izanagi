---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t499-triage
seq: 1
title: backlog 仕分け wave — 裁定済みで終端していた 67 項を見送り台帳へ退役させ、凍結・承認手番の「使う機構」を確定した (docs のみ、branch worktree-dev-wave-t499-triage)
---

## 本文

- **[T-499] の仕分け wave。** 2026-08-12 の一括裁定が起票を承認し、粗い provenance 基準
  (同日 rulings の decisions fragment。本 fold で採番される) の適用と、終端した項の退役実務を
  本 wave の担当と定めた。
- **測った backlog の実態。** 現行 worklog 末尾 (463) の「次の一手」を carry 鎖を解いて数えると
  **active 581 件**、うち **50 エントリ以上無変化が 467 件**。[T-499] 起票時の 129 件から 3.6 倍に
  増えている。増加の主因は新規起票ではなく**退役の不在**だった — 先頭行に「終端 / 見送り /
  受容 / 現状追認」と書かれたまま active に残っている項が **63 件**あり、そのうち 52 件は
  残件ゼロで、単に見送り台帳へ落とされていないだけだった。
- **本 wave が退役させた 67 項の内訳。** (i) 2026-08-12 一括裁定で終端した 12 件
  ([T-871]〜[T-874]、[T-868]、[T-864]、[T-751]、[T-837]、[T-687]、[T-689]、[T-691]、[T-679])、
  (ii) それ以前の裁定で終端済みだった 51 件、(iii) [T-786] が「次の docs 機会で行う」と
  委ねていた被覆 3 件 ([T-789]、[T-788]、[T-760]) と、それにより残件が尽きた [T-786] 自身。
- **沈めなかった項 (誤って生きた項を沈めない義務、[T-499] 本文)。** 先頭行に終端語を持ちながら
  退役させなかったのは 11 件。内訳は残件明記が 4 件 ([T-419] 残 blocker (iv)、[T-673] 残余
  §56 (4) E、[T-659] runbook 専用節が未実装、[T-786] は上記のとおり被覆項の退役で解消)、
  実装待ちが 3 件 ([T-369]、[T-386]、[T-412])、語の誤マッチが 2 件 ([T-552]、[T-691] の
  「終端ダイジェスト」)、明文化が残るもの 1 件 ([T-857])、見送り台帳と二重在籍 1 件 ([T-186])。
  **[T-412] は再訪条件が成立していた** — 「剪定は [T-313] 実装後に再開する」の [T-313] は
  land 済みであり、終端の見た目のまま沈めれば生きた作業が消えていた。
- **[T-186] は見送り台帳 (`docs/phase3.md`) と「次の一手」に二重在籍している。** 台帳側が
  残余 3 件の正本であり、active 側は重複である。本 wave では触らず {{T:duplicate-sink-residency}} で返す。
- **fold の順序制約 (実測)。** fold は fragment を `(wave, seq)` 順に適用して active 集合を
  逐次更新するため、同じ項を 2 つの fragment が操作すると後着が
  `transition-target: active でない操作対象` で赤になる (`tools/spool_fold.py` `_render_next_actions`)。
  `dev-wave-t499-triage` は `rulings-20260812-coarse-provenance` より先に当たる。そこで
  cherry-pick した兄弟 fragment から、本 wave が見送りへ落とす 13 項
  (上記 12 件 + [T-499] 自身) の `更新` block だけを外した。裁定内容は失われていない —
  同じ内容が本 wave の見送り台帳エントリと [T-499] の更新本文に入っている。
  **兄弟 branch `worktree-rulings-20260812-coarse-provenance` に残る原形の fragment は、
  本 wave の land 後は再投入できない** (対象項が active でなくなるため)。同 branch は land 済みとして扱う。
- **凍結・承認手番の「使う機構」確定リスト (ユーザー手番、[T-782] / [T-750] / [T-607])。**
  一括裁定が「仕分けで使う機構が確定した後にまとめて 1 回」と定めた手番の対象は次の 3 つに確定した。
  いずれも正しさゲート側であり、粗い provenance 基準の引き下げ対象ではない。
  - **(A) s8b oracle の reviewed spec 承認** — `s8b_oracle_spec.py` の `APPROVED_SPEC_SHA256`
    (現在 `None`)。手順は (i) candidate spec の内容確認、(ii) canonical path への設置、
    (iii) 定数への hash 記入 の 3 手 ([T-782]、恒久形は [T-803] で承認済み、[T-750] の残件も同じ手番)。
    未承認のあいだ機構全体が fail-closed で止まる性質は維持されるため、実行しないと止まったままになる。
  - **(B) freeze v2 の approval / active pointer 手番** — 非 merge・逐語 `AI-Agent: none` commit。
    `reverify_published_freeze` の production 到達性がこれに従属する ([T-607])。
  - **(C) 対話 Codex での hook 信頼の承認** と `python3 tools/check_codex_hooks.py` rc=0 の確認
    ([T-815]。一括裁定が「先にやる価値」と明記。これまで codex 側防壁は未発火のまま)。
  - **手番が不要になった (基準により見送り) もの:** 承認 receipt への署名と外部 trust root
    ([T-868])、凍結受領証の恒久機構 ([T-751])、toolchain binding の 4 拡張 ([T-871]〜[T-874])、
    公表 core の原子性・予約 writer と追補 P の blob 凍結 ([T-793] R1/R2)、v1 凍結証拠テスト 4 本と
    未使用 pin ([T-816] Q1/Q2)、blob authority の機械可読 target schema 必須化 ([T-864])。
  - **先に別裁定が要るもの (この手番に含めない):** [T-805] (budget authorization は [T-657] 合流待ち)、
    [T-856] (`VerifiedOracleVerdict` 実装 wave が先)。
- **残りの仕分けは返す。** 退役後も 50 エントリ以上無変化の項が約 400 件残る。全件を 1 度に
  意味判断すると「生きた項を沈める」危険が [T-412] の実例どおり現実になるため、本 wave では
  裁定済み終端項の退役だけを確定し、残余の三値分類の進め方を [T-499] の更新本文で択一にして返した。
- **docs-only 受入免除判定の証拠。** 本 wave の変更は `docs/spool/` 配下の fragment のみ
  (判定手順 = `git diff --name-only main` が `docs/spool/` 配下だけを示す)。実装面ゼロ、
  該当 nodeid 不存在。`tools/check_docs.py` と `tools/spool_fold.py --dry-run` は実走した。

## 次の一手差分

### 更新

- [T-499] **P2・裁定済み (2026-08-12 /rulings) → 退役実務は完了、残余の進め方をユーザー裁定へ**:
  裁定済みで終端していた 67 項を見送り台帳へ退役させた (本エントリ)。凍結・承認手番の
  「使う機構」確定リストも本エントリ本文に確定した。**残余 = 退役後も 50 エントリ以上無変化の
  約 400 件**で、これは起票時の 129 件と別物である。進め方の択一 —
  (a) 複数 wave に分けて 1 件ずつ意味判断を続ける (安全だが高コスト、[T-412] 型の取りこぼしは防げる) /
  (b) 「先頭行に終端語があり active」の機械抽出を定期報告にし ({{T:terminal-item-retirement-check}})、
  残りは自然減に任せる (本 wave の実測で誤検出率は約 17%、報告どまりなら害は小さい) /
  (c) 滞留年齢に上限を設けて自動で見送り台帳へ落とす (低コストだが生きた項を沈める。**推奨しない**)。
  **親推奨 = (b) を主、(a) を裁定待ち項に限って従**。理由 = 本 wave の 67 件のうち 63 件は
  「既に裁定済みで残件ゼロ」であり、残余 400 件の多くは裁定を経ていない生きた項だから、
  同じ一括処理は効かない。
  base: 9ee8836756032443f71ad4d54d5d66e124e66b98c8061a5e8c8cf7828d903fc7
- [T-412] **P2・再訪条件が成立 (2026-08-12 実測) → 剪定を発火実績の観点で再開できる**:
  「剪定は [T-313] 実装後に byte でなく発火実績の観点で再開する」の [T-313] は land 済みで
  (三層構造 land を worklog (390) が記録)、再開条件は満たされている。ただし land 後も
  L1 = 10,625/10,625 で余白は出ていないため、再開しても回収先がない。着手前に L1/L1.5 の
  実測を先に行う。終端の見た目のまま退役させない ([T-499] 仕分けの判定)。
  base: 8223eda4724e0ceca3dab8f9b7c160b69e1ce0797d3bf892391ad21391953589
- [T-782] **P1・実装完了 (2026-08-11) → 承認手番待ち (B 系)、対象と手順は確定済み**:
  reviewed spec の schema・validator・pinned literal 承認 (`APPROVED_SPEC_SHA256`、現在 `None`) を
  `s8b_oracle_spec.py` に置き、`build-approved` CLI を足した。**本手番は [T-499] 仕分けの
  「使う機構」確定リスト (A) として実施対象に確定した** — 正しさゲート側であり粗い provenance
  基準の引き下げ対象ではない。手番は (i) candidate spec の内容確認、(ii) canonical path への
  設置、(iii) 定数への hash 記入 の 3 つ。承認形そのものの恒久裁定は [T-803] で承認済み。
  base: b3eb2c23f1a270ce61717b1321ba1cd2a5dd9739c7aedefa0eccc3b0a0c88673
- [T-750] **P2・実装完了・裁定パッケージ 4 件も裁定済み (2026-08-11 /rulings) → 残りは実凍結手番のみ
  (B 系)、[T-782] と同一手番へ束ねる**: P-1 = [T-803] (a)、P-2 = cell-product 検査を事後承認 +
  [T-804] (B)、P-3 = [T-805] (c)、P-4 = [T-807] (c)。実凍結手番は [T-499] 仕分けの確定リスト (A) と
  同一の 3 手であり、[T-782] とまとめて 1 回で行う。
  base: faf2877ab07b99fc1a5e759b1cf4bda912bcd3ddeea40a5fb09efb20232b5cc7
- [T-607] **P1・裁定済み (2026-08-07 /rulings) → ユーザー手番の対象として確定 (B 系)**:
  `reverify_published_freeze` の production 到達性は「freeze v2 の candidate 発行 (wave 可) +
  人間の approval / active pointer 手番 (非 merge・逐語 `AI-Agent: none` commit)」に従属する。
  [T-529] の活性化では解消しない (2026-08-07 実測)。**本手番は [T-499] 仕分けの「使う機構」
  確定リスト (B) として実施対象に確定した**。
  base: 3f502e4272d273d530ed2d50758cf16d247887b497891a83822a99d80b4e2902

### 新規

- {{T:terminal-item-retirement-check}} **P2・新規**: 「次の一手」の項が裁定で終端したまま
  active に残り続ける構造を検知する。本 wave の実測では 63 件が滞留し、うち 52 件は残件ゼロ
  だった。先頭行の終端語 (終端 / 見送り / 受容 / 現状追認) による抽出は誤検出率が約 17%
  (11/63 は生きた項) なので、**gate ではなく定期報告**にする。受理集合を変えないため
  `DW-G05` の影響は「報告の有無」だけで、実装しなければ backlog の単調増加が続く。
- {{T:duplicate-sink-residency}} **P3・新規**: [T-186] が見送り台帳 (`docs/phase3.md`) と
  worklog の「次の一手」に二重在籍している。台帳側が残余 3 件の正本で、active 側は重複。
  ID 保存則は両方が sink を満たすため機械検査に当たらない。同型が他にないかの棚卸しと、
  どちらを正本にするかの規約化を行う。

### 見送り

#### 正しさ・防壁系

- [T-871] **toolchain binding — attempt 実測値の脚** — 理由: 裁定 2026-08-12 (粗い provenance 基準): 実装しない。再訪条件 = 外部公開で証跡提示が必要になったとき。材料 = `output/insights/2026-08-11_t783-toolchain-binding/package.md`。
  base: bfbad7f7691f0934bb7d6682269f803a8c0b18c40358946cd086608fa22ff417
- [T-872] **成果物への binding report** — 理由: 裁定 2026-08-12 (同基準): manifest / result に binding report は載せない。exact-key consumer の改修も行わない。
  base: 2d637491aad8d3f972b6a3cdbeba691353b6ba2a370d6a1242bab39e587ecb5e
- [T-873] **authority への cxx version / cmake path / module_list / bytes hash 追加** — 理由: 裁定 2026-08-12 (同基準): 追加せず calibration の再発行も行わない。
  base: 2fcb30a43b3982ddd82c80fc457a216e357651f8f0fd74a55214c002f5b59feb
- [T-874] **束縛の producer 拡大** — 理由: 裁定 2026-08-12 (同基準): floor と silo ladder のまま他 producer へ広げない。
  base: 1ac3494639b161bdae76bf65b4c130e0df1505c5520dfb56edff790943a7e833
- [T-868] **承認 receipt の署名と外部 trust root** — 理由: 裁定 2026-08-12 (同基準): 署名方式と trust root は設けない。自己発行可能な性質は `/limitations/approval_receipt_trust_root_absent` の機械可読宣言で明示したまま受容する。
  base: c065034873a3a3fb4b88ac04d12ef47f76d9b2ede3afd1eaea97bcf12e25b022
- [T-864] **blob authority の機械可読 target schema 必須化** — 理由: 裁定 2026-08-12 (同基準): 必須化しない。現行 marker gate が `approved_blobs:` 形式だけを拒否できる状態のままとする。
  base: 95689764fe4547fc3bb9587248b498f5ecbb606ffdbbcf142e562806d0734975
- [T-751] **epoch 以前の pickaxe evidence を持ち回る恒久機構** — 理由: 裁定 2026-08-12 (同基準): 窓限定の現状を受容し checkpoint 連鎖は作らない。再訪条件 = 外部公開で監査地平の提示が必要になったとき。
  base: 35eac470e2a682f0f72cde2e23ca721f94f4f979e3c392904067fd8e1d16dc16
- [T-837] **`c9c1a9c` の乗せ直し** — 理由: 裁定 2026-08-12: [T-816] Q1/Q2 の裁定により乗せ直しを省略し `511c9538` へ直接前進する。Q1 (a) の旧裁定は上書きされた。残るユーザー手番なし。
  base: b2898a746276a7ca47f1f495614f56a116695208fd2851bac05d2f3b7dd08a8d
- [T-449] **repo 外 cache の同一 UID 敵対者 TOCTOU** — 理由: 裁定 2026-08-11 (境界外宣言): 防御境界に含めない。RP-2 (a) の既裁定と整合。再訪条件 = 信頼モデル自体の見直し (D86 系の再裁定)。
  base: 6219133dcdef7065850b454fedb7936924eee4b91beb6478374e439530d05a2f
- [T-546] **`git rm --cached` の deletion gate すり抜けと preflight 後 TOCTOU** — 理由: 裁定 2026-08-06: 残余として記録し対策実装はしない。正本 = `output/insights/2026-08-05_t450-t412-preface/README.md` §3 R2。
  base: 611da3836e177403e93274cf05f19cde5064c6fa98f011910e34259b821faea6
- [T-560] **publish 済み bytes の別 process verifier + 最終 receipt 束縛** — 理由: 裁定 2026-08-06: 完全形は作らない。同一 process 内再読で足りる (プロトタイプ基準)。
  base: 7dd52a0204761c781a690ed0931b05ad50355dea092501612ce219ef4012e67b
- [T-563] **certification job の immutable snapshot 拡大** — 理由: 裁定 2026-08-06: live worktree bytes 参照を容認する (自 checkout を信頼する。プロトタイプ基準)。
  base: 1d8353549a4ad5349253a4294413ccb80c2d2d6bd2de0d3c3dadbbd11ed0856f
- [T-605] **receipt expectation の top-level structured issue 新設** — 理由: 裁定 2026-08-07 (委任 (a)): 現状の観測経路を受容する (受理集合を変えないため)。根拠 = `output/insights/2026-08-06_t574-world-expansion/README.md` R9。
  base: 202e8ef0c941f1ebc6bf39719d765cf548aed9a3375d99ba0d193b11c4a261c7
- [T-608] **`generator_versions` pin の rollover 手順明文化** — 理由: 裁定 2026-08-07 (委任 (a)): 生成器 source bytes の変更が pin を動かすのは設計どおりとし明文化しない (発行済み manifest 0 件、既存受理不変)。同 README R12。
  base: e67b57e0a48b439b2d3d6c984c1dcc87ab383835b79e042a4012c99d47761f69
- [T-628] **activation transition の env 集合変化用の別機構** — 理由: 裁定 2026-08-07 (a): 同一 env 集合の世代進行だけを受理し集合変化は永久拒否。別機構は設計しない。再訪条件 = 新 env を実際に追加する実需。
  base: cd6edec36f78fc54be54ca7bd750a4cca2de69eddb8ca57de3952a5e6d13940e
- [T-644] **書込みなし hardware attestation の pre-built probe** — 理由: 裁定 2026-08-08: PBS wrapper の preflight は静的 admission までと明示し別設計は行わない。再訪条件 = 較正運用で最初の書込み前 attestation の実需。
  base: f31312cfbaeeb9c0cc80d19e8697799adf0cb1684fe3b3ee735a480ea00884c7
- [T-649] **lease の fencing token / epoch と release 権限証明の nonce 化** — 理由: 裁定 2026-08-08 (D205 委任): 入れない。無くても「本機構が無い場合と同じ競合」までで悪化はしない。再訪条件 = 二重 winner の実害観測、または dev-wave 投入の自動化。
  base: a030a97723ed83ba1318c8c0aca2678eadc86f34f79dc99f72bded519029603b
- [T-654] **`dev_wave_land.py` no-touch の byte 不変検査 gate** — 理由: 裁定 2026-08-08 (D205 委任): 所有宣言のままとする。「main land を妨げる検査を作らない」と衝突するため作らない。再訪条件 = no-touch 違反の実害。
  base: c03089409924211ef4645feadc31c7c2c782a4ff08c69a2d5a7ff63ba1157f9e
- [T-658] **activation receipt の書込み境界への配線** — 理由: 裁定 2026-08-08: 行わない。認可の本丸は sink 必須化 ([T-609]) と contract hash 束縛 ([T-530]) が担い、全書込み口配線は防御的堅牢化 (D205)。再訪条件 = durable receipt の実需。
  base: d61bfc69ac012d1405de9e77b42bd1473942a83b07e4378bb033a37d44e7fc3b
- [T-703] **receipt publication 後の受理再評価を塞ぐ commit protocol 再設計** — 理由: 裁定 2026-08-09: 行わない (実害未観測の liveness 系、D205)。「最後の可逆点まで」の防御を維持。再訪条件 = 停滞由来の再評価の実観測。
  base: 31d9ae894f6cb3c1b8ee3e8523e480be2e02b82405e84a8c3459c7ebd4a16b80
- [T-718] **production 側 cache の設計変更** — 理由: 裁定 2026-08-11 (見送り): 受理集合・proof chain に触れる変更は今は認めない。positive control の実プロセス検査は不変。再訪条件 = R-c 実装後も receipt 解決 2 回が受入 wall の支配項であるとき。
  base: b1597301dd3572decc1a12c381f6c638d2a2088336e2e6d214e5745cb013fde0
- [T-742] **path 防壁の検査対象拡大** — 理由: 裁定 2026-08-10: 文字列化後の値に限定したままとする (実害経路なし、D205)。再訪条件 = bytes / PathLike を直接渡す新経路の出現。
  base: 5cc46a23751ab7551d767cb0b67dd60129cb60e960a2e9009a10b75b286cf306
- [T-744] **二重 namespace への実行時機構** — 理由: 裁定 2026-08-10 (c): 静的検査 ([T-720]) で足りるとする。alias / ImportError はテスト 2 本の supersede と受理集合変更を伴うため見送り (D205)。再訪条件 = 静的検査をすり抜ける再発の実害 1 件。
  base: 04e7f1fc6c97e581d3e988c1660e8c9c20cf5ffc3d8873938ad58693d7fce796
- [T-767] **可視文字列の confusable 正規化** — 理由: 裁定 2026-08-11 (c): 現状維持。攻撃は信頼済み経路の内側からしか実行できず最悪ケースは構造側で封じ済み。再訪条件 = 誤用の実測 1 件。
  base: 874a26d131b126f800f5bf653c586f8bf00f340c7a83928864522b2b1a85849d
- [T-781] **official 受理集合と proof chain 拡張 (Q1〜Q4)** — 理由: 裁定 2026-08-11 (全問 (a)): 実装なしで保留終端。official は空集合維持、User Attributes は認可に使わない、proof chain 拡張は先送り維持 (D86(5))、[T-139]・A 系列の後まで保留。D86 は 1 項も覆さない。再訪条件 = queue の `qattach` 無効化、または lineage を閉じる設計の登場。材料 = `output/insights/2026-08-11_t781-spool-feasibility/package.md`。
  base: bfbcffada66a15af8a0a3f9cb9b4b583bb09f4411122e0bed6cd9f2e0bbb2227
- [T-802] **dry-run の no-write 検査を Git 管理 bytes へ拡大** — 理由: 裁定 2026-08-11 (b): 広げない (index stat cache 等は正当な操作でも変わり誤検知検査になる)。守るべき実体は現検査が覆う。再訪条件 = dry-run 起因の汚染の実害 1 件。
  base: aedb377b441c56da4a755f10974529ffa67b876435914666ce11b07c042d7c1a
- [T-807] **旧 writer の任意 path 受理を狭める** — 理由: 裁定 2026-08-11 (c): 狭めない。失敗様態は `namespace-dirty` の fail-closed 拒否で、原因ファイルの除去で復旧でき外部入力からは到達しない。再訪条件 = `namespace-dirty` の実発生 1 件。
  base: 265e001ddd3d29d1394e25b860ac0270b52bfeb4a1f72a3656a55e50e993215e
- [T-858] **consumer pin の全称保証** — 理由: 裁定 2026-08-12 (b): 限定 AST inventory + 敵対レビューの併用を続け全称保証は主張しない。再訪条件 = loader-only sink の実増加。
  base: 9f62e069fe685a81fa5d2f7c93f7402131a27e01538f2e7bc5b11c9b975f13c8

#### 研究・計測系

- [T-539] **α 取得の事後証拠の versioned schema 凍結** — 理由: 裁定 2026-08-06: 行わない (プロトタイプ基準)。再訪条件 = 論文化・外部公開で attestation 証跡の提示が必要になったとき。
  base: 9e1e4915c9a2f5a31f602b23182e4b4bb59e4f991d26155bb3994b86e03d2ecb
- [T-542] **α 巡回の暖機持ち越し ablation** — 理由: 裁定 2026-08-06: 行わない。再訪条件 = 変異比較で説明不能な系統差が観測されたとき。
  base: 1211a38de6c382c4c2958c58ab2f48aa7a3a84c64f02aae05379bb6f4b84a29e
- [T-595] **reasoning=max→high の非劣性 A/B campaign** — 理由: 裁定 2026-08-07: 着手しない (D205、運転コスト最適化であり研究成果に寄与しない)。D223 の機械 pin を恒久 latch とする。再訪条件 = ユーザーが token 予算の逼迫を理由に明示的に再開を指示したとき。
  base: aac34bdec7b3e57bdb4e422021398ac319e8acb242094007e32204f1defafe63
- [T-645] **NQSV / PBS 証拠による計算ノード判定の分類条件化** — 理由: 裁定 2026-08-08: 行わない。権威は bnode hostname と affinity のまま。再訪条件 = 誤検出の実測 (CI・別施設ホスト名での実害)。
  base: c34ee09970e00c21671a0e1a06d8512c59b5064c6df8654151abfe81cc379ff0
- [T-647] **bench なし correctness-only COMMIT の計測契約束縛** — 理由: 裁定 2026-08-08: 束縛の対象と数えない。numactl 等は宣言値に留まると正直に記録する現状を正とする。
  base: b027a2b1326bbde1fe416e1622177b2f6658f0847afb8e69e510f2ace3369a3d
- [T-676] **launcher テストの時間予算の据え置き** — 理由: 裁定 2026-08-09: 実負荷 artifact 1 件が取れるまで変更しない。[T-663] の計装が次回再発時に失敗署名を自己申告するので、それを根拠にパッケージで再提示する。根拠なき受理緩和はしない。
  base: ccaa402da18bbdd1fe3d5fdf4fce4496a4323965e86cbf369d1947a2de3fcbcd

#### プロセス文書系

- [T-687] **xdist internal error / pre-item crash の診断項目化** — 理由: 裁定 2026-08-12 (プロトタイプ基準): 診断項目は増やさず既存 xdist summary を正本と定める。
  base: 1c660b7356efd005d449ca77a87e0d82b214c0e6055e299b0fa34c0d9a7d7800
- [T-689] **dispatch 中継の耐久経路** — 理由: 裁定 2026-08-12 (同基準): best-effort の中継を正とする。耐久経路も手順追記もしない。
  base: 4ad28a9e1d3776f2a7e7fc45d23cfabdc103febdc834333ae04668fd49df751c
- [T-691] **終端ダイジェスト failure stash の session 束縛化** — 理由: 裁定 2026-08-12 (同基準): module global のまま現状維持 (経路実在未確認、回帰 pin 維持)。
  base: d400efb23d24d22fab3aaed240d0781ab9432d0e601b6b09cf00cd1e239f75f4
- [T-679] **preflight / publication 失敗時の早期 receipt** — 理由: 裁定 2026-08-12 (同基準): 置かない。
  base: b8b4adc48ef32477e35daa2b6755b65357fcb5fa49c2cc6c68bcb699cb395513
- [T-317] **親が子に書かせる規律の射程** — 理由: 裁定 2026-08-10 (b): 射程は repo へ入る artifact に限る。wave 運転用の使い捨て script は repo 外に置く限り射程外で親が直接書いてよい。worktree session の Bash 複雑度制限との衝突は解消。
  base: 2fe93980c646bc0fdfad37db3eb2aa767b32e355917a0ccaf1cc20f034a8de13
- [T-454] **子起動の単一経路化 (R1)** — 理由: 裁定 2026-08-08: 現状維持。再訪条件 = 子起動由来の実害、または R8 安全前提を満たす実需。R5 は [T-577] 裁定が、R4 は [T-625]/[T-632] が解消済み。
  base: a92adf8414f89dcaf1ecc16bfd1381198af55bda79c00df17bf095922e4f3909
- [T-537] **docs-only wave の変異・受入射程と軽量版の境界** — 理由: 裁定 2026-08-06: (a) は [T-577] の優先列で扱う (所有移管)。(b) は現行慣行の追認とし規約化しない。
  base: e581fbc3c58dd3e64c04eb5d614471bec58940f5a12bc1acae8b0a9bc466fb74
- [T-545] **`DW-O11` 第 2 文の機械化 (acceptance mode + receipt + land 消費)** — 理由: 裁定 2026-08-06: 起票者推奨どおり見送り。正本 = `output/insights/2026-08-05_t450-t412-preface/README.md` §3 R1。
  base: ad76d4e1a5bb0d698e7c7d093bd62ec96fd04305fd19be2a5ec19cb2bc1eb1fe
- [T-555] **admission registry の `reason` / `primary_gate` の docs 投影** — 理由: 裁定 2026-08-06: 行わない (プロトタイプ基準)。`submit_silo_ladder_rung1.sh` の説明齟齬は実測時に手で直す運用のまま。
  base: bf14ee8710d1a40c5e5e7b150040480e45c55b747f64267aaf748ee5a0933471
- [T-556] **分類 claim を書ける living doc の閉集合化** — 理由: 裁定 2026-08-06: 行わない。検査対象を runbook と Pegasus README に限る現状を正とする。
  base: 56d2fde35089a388c1351822e5cebda4b0c1175c8fa45d20eb46600c4711e902
- [T-558] **`DW-M08` への kill 判定明記** — 理由: 裁定 2026-08-06 ([T-577] 傘下): 回収 207 bytes の優先列に入らないため見送り。予算の独立審査は行わない。教訓は worklog (258) と `output/insights/2026-08-06_t454-testification/ruling-package-drafts.md` が保持する。
  base: b06413f272cd492458f10bce3f96689897b0685aa6374078a9dbe1243f0742d1
- [T-576] **dev-wave 子起動の単一経路化 (二経路の統合)** — 理由: 裁定 2026-08-06 (c): 行わず現状の二経路を受容する (プロトタイプ基準)。摩擦の最悪部は guard 解析強化が対処する。
  base: d527038fd87d19597b5b4f4e014e3869df0db74e1c8c40ed2c21589f123e1a73
- [T-616] **見送り裁定と依存タスクの突き合わせの機械化** — 理由: 裁定 2026-08-07 (b): 起動読了の prompt 規律に留める。fold 時の相互参照機械化は D205 基準で不採用。都度訂正は規律の下位互換として併存。
  base: e75d31f9699c6355179a80d4c69fa0e851a91bc15ce283bbee7e607a3034d206
- [T-640] **fragment と fold の「同じ変更単位」要求** — 理由: 裁定 2026-08-08 (α): fragment が wave commit 時点の署名済み決定であり fold は採番と転記だけ、という解釈で充足と認める。不可分性は wave commit が担保する。
  base: 6578c3e96cc6bfe05353ec4ba7bd05f0d80c751088f501cc249884742c494520
- [T-641] **予算超過で撤回した恒久対応の扱い** — 理由: 裁定 2026-08-08 (c): failures 台帳と memory の記録で担う。予算の独立審査は行わず、縮約余地も尽きていると実測済み。「制度化条件を満たした改善が予算で止まる」構造は受容する。
  base: 398e641d9cf1299f0ecde51afb81147e44a00a47f2c2d01584c7b7a23f5490be
- [T-661] **段 8 改善 2 行の dev-wave 参照文書への本文編集** — 理由: 裁定 2026-08-08: 行わない。台帳の記録 (F169 と F112 独立 2 例目) で担う。節の削除もしない。再訪条件 = 同型失敗の再発で本文契約化の実需。
  base: 3c25e596d74bdff0a9dba6cc424614fed9acc47456baa15db5a3ace9919a4a11
- [T-664] **docs 予算の 2 経路審査** — 理由: 裁定 2026-08-09 (R1〜R5 全問推奨どおり): 2 経路とも予算は空かないと確定して閉じる。R4(a) の需要は [T-313] の実装へ集約済み。正本 = `output/insights/2026-08-08_t664-docs-budget/package.md`。
  base: 3292e3cbe049cfa4282f34a5e40ffdb84875f21654213d758bd107f6ec2d5977
- [T-666] **規範文 pin の強度** — 理由: 裁定 2026-08-08: 意図した設計として受容する。再訪条件 = 正当な文面改善の需要が実測で頻発したとき。
  base: e5ad16677171e0cd3b4e01701b0ac70751172bf1df14673d584b8c7d7e2a9540
- [T-667] **`DW-S05-A` の `high` と `DW-S06-B` への pin 拡大** — 理由: 裁定 2026-08-08: 行わない (防御的堅牢化、D205 既定。`DW-S05-A` は D207 の pin が別途ある)。再訪条件 = 当該節の drift の実測。
  base: 7da99a0fe503cc62f03b347db8a43bb898abe2f16a29f904353eb3b325b20f8d
- [T-668] **CR-only 改行の文書への対応** — 理由: 裁定 2026-08-08: UTF-8 / LF 契約の想定外入力として非対応とする。checker は変更せず、非対応の明示は本台帳の記録が担う。
  base: af2db31f37bf423f8906db0469218889f16460d42ea3ad0ab4040031f0119759
- [T-686] **insights `verbatim/` 配下の guard 対象外明記** — 理由: 裁定 2026-08-09: 逐語凍結の場として placeholder guard・三軸語検査の対象外とし、明記は本台帳の記録が担う。再帰 guard は作らない (D205、過去逐語への偽陽性を避ける)。再訪条件 = 実害。
  base: 56f045d80fc601812e527e084f0a5ac7628ff1df15368eb8cff2ad574c8e7545
- [T-690] **`DW-S05-C` / `DW-S01` への追記 2 行の採録** — 理由: 裁定 2026-08-09: [T-313] の構造変更後に採録する方針だが land 後も余白は出ておらず、それまで本台帳の記録が担う。上限引き上げ審査と節削除は行わない。
  base: 20a0c21c941e0ed0cea707b30d84d3772631bc03040eb64990e3ff1a6baca4cb
- [T-695] **`DW-O25` の trigger の preflight 契約化** — 理由: 裁定 2026-08-11 (a 受容): 現行のまま維持する。(b) L1 再分類は §60 既裁定の不採用を維持。再訪条件 = 条件 25 の読み違いによる実害 1 件。
  base: 7e9497cb451443d25f232575486365e5abaa92447f5729bdde59c6ff1418d79b
- [T-701] **全層 + event 加重の複合 envelope** — 理由: 裁定 2026-08-09: 作らない。unique footprint との乖離 (10,625 vs 12,670) は台帳記録が担い、読み過ぎは JIT 読みの規律で抑える。再訪条件 = 実害。
  base: 8d9e2519c200e34d7217ff0554d7d6cfc4e82604ffe2a6fd293a711ccce50694
- [T-716] **s8c candidate 3 node の canonical group 移動** — 理由: 裁定 2026-08-11 (見送り): 単独では行わない (+58.35 秒の受入増、t553 の git 時間予算定数の前提破壊)。排他閉包の体系化は [T-826] (M0) の設計で一括判断する。
  base: 8e66b8aa4d7acc1d5f51b4963d02208f96a16d8387a307cecb3e4f3e1792e76b
- [T-738] **待ち手の pid 死判定禁止の明文化** — 理由: 裁定 2026-08-10 (c): memory (`waiter-death-check-by-pid`) と F32 の記録運用を正とする。L1 の圧縮審査と予算の独立審査は行わない。再訪条件 = pid 判定由来の実害の再発。
  base: bc9bdec5689789bfda236fafbe2a4166449946b2ade6460e5e9eef50db4e37eb
- [T-743] **レビュー子の欠陥判定基準の `DW-S06-A` 統合** — 理由: 裁定 2026-08-10 (c): wave ごとに prompt へ手書きする現運用を正とする。統合は L1.5 予算 191 bytes 超過のため行わない。再訪条件 = 手書き漏れの実害 1 件、またはテスト化で 191 bytes の見込みが立ったとき。
  base: ba65d290e132826565ea955e93e78cbc16e0ef0e3d82d549ea3308c967259129
- [T-774] **待ち手 rc を受入証拠と誤読させない機械化** — 理由: 裁定 2026-08-11 (b 現状維持): 誤読の実例はゼロで、受入完了の証拠規律 (成果物実在 + done marker + producer 死の 3 点照合) が別途確立しているため機械化しない。再訪条件 = 誤読の実例 1 件。
  base: 63fa0de10f8506c85e3df327413a189117df69a42ca6a1c20abdca49147e788d
- [T-813] **受入全走のノード横断分割** — 理由: 裁定 2026-08-11 (package どおり 4 点): いま入れない (2 通りの分割の両方で別々のテストが静かに消えた実測 = 「全走が緑」の意味が分割の取り方に依存する、規律 2 の面)。M0 = [T-826]、M5 = [T-827] として起票済み。再評価条件 3 つを確定。正本 = `output/insights/2026-08-11_t813-acceptance-sharding/`。
  base: cae2576bf58e1dd0f7323036c7e95b48cc87b3c8bdb7e7649b84ed7c5e91ec66
- [T-786] **docs 予算の未入庫 6 件の棚卸し** — 理由: 裁定 2026-08-11 (審査受諾): 予算引き上げは行わない ([T-127] 既裁定と整合)。被覆項の終端化は本 wave で実施した ([T-789]、[T-788]、[T-760]、[T-738])。正本 = `output/insights/2026-08-11_t786-docs-budget/verbatim/package.md`。
  base: c9bb1c61ef45e172a83b0cb9b0961ee1a64b93fcd3a175998c6aeb83e76d304f
- [T-789] **`DW-O02` への必読 path 実在確認と正本不変の入庫** — 理由: 裁定 2026-08-11 ([T-786] 審査): (3) は `DW-O18` へ入庫済み。(1)(2) は 105 bytes 必要で入らず、既存義務が実質的に (2) を覆う。再訪条件 = 同型の空費が 2 例目に達したとき。
  base: b528126d16c8f701907a6e153e96a3eaa11d0544cf1443d446413513af7e523a
- [T-788] **`DW-O02` への制御 byte 走査の入庫** — 理由: 裁定 2026-08-11 ([T-786] 審査): docs でなく機械検査で閉じるため [T-825] へ移管した。
  base: 8d4c93a613a7e6cc57281c4663941ee0ece7f6ef000f22d043914cf9f641068b
- [T-760] **`DW-O01` への `--sandbox` caller 必須の規範化** — 理由: 裁定 2026-08-11 ([T-786] 審査): L1.5 の残余は 2 bytes で再訪条件「余白が出たとき」は成立しない。
  base: 866876032230984860a361ddee6faa066aff4d2b90844e81f0f4927465ba4bbe
