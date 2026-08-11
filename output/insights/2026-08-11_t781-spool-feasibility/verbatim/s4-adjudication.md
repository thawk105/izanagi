# 段 4 裁定 — [T-781] 案 A 実現可能性調査

親が各所見を real / refuted、採用 / 不採用、scope 内 / 外へ裁定する。
**本 wave は実装差分ゼロで終端する** (段 5・6 を飛ばし `4→7→8→9`)。
scope 外の real 所見は実装せず、裁定パッケージでユーザーへ返す。

## 決定 1 — 実装しない

案 A を実装しない。理由は下の D1〜D3 で、いずれも本 wave の実測と 2 レンズの独立所見に基づく。
D86 の裁定は 1 項も覆さない。official の受理集合は空集合のまま。

## 決定 2 — 親の provisional 裁定の確定形

| 記号 | 段 1 の形 | 段 4 の確定形 | 根拠 |
|---|---|---|---|
| P1 | 案 A は「D86 §4 の独立取得要求を満たす証拠経路」として実現可能 | **訂正**: 「spool された bytes を取得する primitive」は実現可能 (計算ノードを含む)。**「D86 §4 を満たす証拠経路」としては未成立** | レンズ A 2 / レンズ B 2。取得できるのは caller が指定した live request の input であって、現プロセスを同定しない |
| P2 | 案 A は A-1 を部分的にしか閉じない | **強化**: 閉じないだけでなく攻撃面はより広い。`qattach command = Enable` (実測) により、真正 request の**外**にいる同一 uid の攻撃者が任意 command を request 内へ注入できる | レンズ A 1、`probe/out2/qstat_f.out:40` |
| P3 | User Attributes は A-2 への新しい候補であり D86(3) に直接は当たらない | **撤回**: 属性は外部 authority を**運ぶ器**にはなれるが、authority の**発生源**にはなれない。「Git receipt ではない」から「D86(3) に当たらない」への推論は、ユーザーが下すべき判断の先取りだった | レンズ A 3 / レンズ B 3。D86(8)、D87(5) |

## 決定 3 — real / refuted の裁定

### real・採用 (記録と択の再提示に反映する)

- **A-1' (`qattach`)**: real、BLOCKER。scope 外 (実装しない)。**本 wave の最大の新事実**。
  実際に attach を実行して検証はしていない (属性の実測にとどまる) と明記する。
- **A-2' (primitive と証拠経路の混同)**: real。P1 を狭める。
- **A-3' (User Attributes は authority でない)**: real。P3 を撤回する。
- **A-4' (下流 proof chain から消える)**: real。既登録 A-5 と同一。択 Q3 へ。
- **A-5' (`+\n` 規則の一般化範囲)**: real。主張を「小さい text script 3 例・非 TTY・同一 site・
  同一 client version」に限定して記録する。長大 script・巨大 1 行・locale 差は未測定。
- **A-6' (状態一般化)**: real。**親の記述を訂正** — 「run 中しか取れない」は誤りで、正しくは
  「request が保持され取得可能な状態にある間」。QUE / PRR でも全 bytes を観測している。
  未観測状態 (ARI/HOL/MIG/POR/SUS/TRS/WAT/STG/EXT) は明示拒否すべき、も採用。
- **A-7' (M4 の射程)**: real。「少なくとも 1 request で消滅後取得不能。永続性の保証なし」へ狭める。
- **A-8' (JSV 差替え推論の条件)**: real。I1 に「immutable flag・NFSv4 ACL・LSM・mount option が
  反例になりうる」「root 所有 `user_script` 自体の unlink は未実測」を明記する。
- **A-9' (I2 が過大)**: real。**親の I2 を訂正** — server record を `qalter` で変えられないことと、
  admission process が正しく観測できることは別問題。`PBS_JOBID`・PATH・`$0`・`LD_PRELOAD`・
  同一 Python 内 monkeypatch はすべて攻撃者側にある。
- **A-12' (M1 の射程)**: real。「Pegasus で観測した NQSV CUI/API は R1.16」へ狭める
  (batch server 実装の version は未実測)。
- **A-13' / B-10 / B-12 (本 wave 自身の手続き)**: real。決定 5 で個別に処理する。
- **B-1 (択が択一でない)**: real。決定 4 の軸別再構成を採用する。
- **B-5 (受理集合の記述が甘い)**: real。レンズ B の表を採用して裁定パッケージへ載せる。
- **B-6 (P2 の実測と脅威モデルの分離)**: real。兄弟プロセス実験は**実施していない**。
  「静的に real、実測はしていない」と記録する。
- **B-7 (qstat 要約の訂正)**: real。「計算ノードから qstat は使えない」ではなく
  「ID 正規化が要る。script/hash/環境変数は返さないが User Attributes は返す」。
- **B-8 (費用見積りの欠落)**: real。lineage・authority・proof chain の費用は見積り外。
  裁定に必要な数字を Q へ添える。
- **B-9 (返却粒度)**: real。Q1〜Q4 に分割し、W-2 優先を明記する。

### refuted

- **A-10' (「qcat は何も閉じない」)**: refuted。`qcat` は元プランの `9<"$0"` にあった
  「caller が選んだ path を自分で読むだけ」という恒真化を、request → spooled bytes の辺に限れば
  実際に閉じる。primitive 自体は有用である。
- **A-11' (「A-1 を閉じる設計は一般に無い」)**: 親の一般化は未証明として refuted。
  正しくは「現 scope・現 queue 設定では閉じない」。queue-level の `qattach` 無効化、
  scheduler が保護する PID→request 対応、privilege-separated launcher 等の設計余地は残る。
- **A-14' (「AI が qsub した時点で全 probe 無効」)**: refuted。F49 (ii) が背景 job セッションからの
  診断投入を 3 点検査付きで許可している。ただし「AI が置いた属性を人間が選んだ revision の
  証明へ昇格する」ことは D86(8) / D87(5) が禁じる (この部分は real)。

## 決定 4 — 択の再構成 (裁定パッケージ本体は insights の package へ)

元の (A)〜(D) は判断軸が異なり択一ではない。実測後の軸別 4 問 Q1〜Q4 へ再構成する。
**親の推奨を付ける** — 起票時は実測が無く「推奨なし」だったが、実測が揃ったため推奨できる。

## 決定 5 — 本 wave 自身の手続きに対する自己裁定

1. **並走ガード (i)**: **形式的に未充足**。実測上ノード同居は無い (他 wave = bnode034、
   probe 1 = bnode042、probe 2 = bnode046) が、**計算ノード上での単独性確認と静穏 preflight は
   実施していない**。probe 1 の `ps -u $USER` は自 uid しか見えず代替にならない。
   `Exclusive = (none)` も実測した。**性能値を一切採っていないため計測汚染は生じていない**が、
   ガード文言は無条件であり、「非性能 probe だから」は充足の論拠にならない。記録に明記する。
2. **F49 (ii) の 3 点検査**: (a) 計算ノードが書いた marker = 実在、(b) `qstat` 可視性 = 901499 /
   901501 は投入直後に親側で確認、**901512 は投入直後の親側 qstat を実施していない**、
   (c) 会計痕跡 = `.e` / `.o` 3 組が実在。ポイント消費差分は `racctjob` が sudo を要求するため未取得。
   → **(b) の一部が欠けた**。real な手続き不備として記録する。
3. **投入 request 数の訂正**: 「probe 2 本」ではなく **3 本** (901499 / 901501 / 901512)。
   901501 は hold 解除後、`qdel` の前に実際に実行された (`izt781held.o901501` に出力あり)。
4. **`-U` は sanctioned submit script に無い qsub surface**: real。ただし `-U` は script へ
   パラメータを渡す用途ではなく **測定対象そのもの**だった (属性が保持され `qalter` で変えられるかの検査)。
   runbook の「投入インタフェースを発明しない」の趣旨には反しないと裁定するが、逸脱として記録する。
5. **probe 2 は read-only ではない**: real。JSV jobfile dir (`/var/opt/nec/nqsv/jsv/jobfile/0.901512.10/`)
   へ `touch` → `rm` を実行した。自分の job の dir だが scheduler 管理領域への書き込みである。
   「非破壊」と「read-only」は同義ではないという指摘は正しい。記録に明記する。
6. **破壊的検査の不実施**: `user_script` の unlink / 差し替え検査は権限層に拒否されたため
   **実施しておらず、迂回もしていない**。POSIX 意味論からの推論 (I1) として実測と区別して記録する。

## 決定 6 — 変異事前登録

実装差分ゼロの「実装しない」裁定であるため、`DW-S04` により変異 matrix を免除する。
**受入全走は免除しない** — `docs/worklog`・`docs/spool`・`output/insights` を読む実 repo テストが
実在する (`test_check_docs.py` / `test_spool_fold.py` / `test_frozen_artifacts.py` /
`real_repo_ratified_memo.py` 等) ため、記録 commit 込みの最終 tip で実走する。
