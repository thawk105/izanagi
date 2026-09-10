# 段 4 裁定 — [T-2148] 排他権の世代の意味論

基準 commit 6ff06800de0e2a0a8ac261d2e20320e68db8ebb3。裁定時点の local main は c7b2f8e85。
main の新規 D は D1488 / D1489 (A-6 の certification policy と walltime) だけで、本件の面と重ならない。

## 0. 実装の可否

**実装しない。** repo へ入る実装面の差分は 0 とする。schema、受理集合、lease payload、
`lease_generation` の slot はいずれも変えない (D1449 が維持を命じている)。
probe は repo 外 (job dir) に置き、production 入口を叩く形にする ([T-317] 裁定)。
したがって段 5・6 を飛ばし `4 -> 7 -> 8 -> 9` とする。実装面の差分ゼロなので変異 matrix は
免除 (DW-S04)。受入全走は免除しない。

## 1. real / refuted と採否

### レンズ A (正しさ境界)

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| A1 | 非保持走行の世代が候補集合で未定義 | **real** | **採用・scope 内。本 wave の主成果へ昇格する** |
| A2 | 「再取得で別値になり得る」は再送防止の基準として弱い。current writer 候補は replay 可能または恒真 | **real** | 採用・scope 内。候補の分類軸に「値を選べる主体」を足し、C13 を current / external へ分割する |
| A3 | 署名 probe が同じ値を両辺へ渡す循環 | **real** | 採用。Command 4 は「署名機構の機能確認」として実施し、**世代の出所の確認としては使わない**。重い monkeypatch を伴う部分は F29 により裁定根拠にしない |
| A4 | shortlist を強制する production consumer が無く、積極採用の正の end-to-end 証拠が無い | **real** | 採用。ただし実装は scope 外。**裁定パッケージの前提へ昇格**する |
| A5 | D1400 の訂正は helper の fresh 経路には成立するが system 全体へ一般化できない | **real** | 採用。訂正の射程を「基準 commit の current helper の fresh 経路」に限定する。**「規律 2 に触れない」とは書かない** |
| A6 | 使い捨て directory は production directory と同値でない | **real** | 採用。C13 / C14 / C15 は使い捨て dir の結果を採用根拠にしない。「この環境で取れるか」だけを測る |
| A7 | 親観測は controlled injection であり writer の provenance ではない。raw transcript が無い | **real** | 採用。probe の stdout を artifact として insight へ保存する |
| A8 | consumer 閉包は 6 file。`test_resume_gate_acceptance_boundary.py` が漏れている | **real** | 採用。閉包を 6 file に確定する |

### レンズ B (網羅性・実効性)

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| B1 | 計画が「取得ごと」という粒度を先に決め打ちし、その前提で C4 / C5 を不可としている (循環) | **real** | **採用・最重要。裁定の第一階層を「粒度」にする** |
| B2 | 候補 4 件 (A1 repo 内台帳 / A2 wave 単位 / A3 main 単位 / A4 lease dir 単位) が欠け、C7 / C8 / C13 / C15 が分割されていない | **real** | 採用。候補を 17 -> 21 とし、writer 別に分割する |
| B3 | 候補別の影響 wave 数と回復時間が無い | **real (欄の欠落)** | 部分採用。回復挙動は測る。**影響 wave 数の絶対値は rollout 時の旧版稼働数に依存するため測れない**とそう書く |
| B4 | 定常費用 (残留・掃除主体・不完全更新窓) が候補別に無い | **real** | 採用。残留と掃除主体は測る。crash 窓は設計上の推論として記し、**実測しない** (DW-G05: 仮想リスク向けの機構を足さない) |
| B5 | 64 桁 SHA-256 形式への変換規約が候補別に無い | **real** | 採用。候補表に変換規約の欄を足す |
| B6 | 「119 セル」は測定でなく等価類の予測 | **real** | 採用。**測定と予測を表で分けて書く** |
| B7 | probe の観測穴 (外部台帳が記録されない、xattr を読み戻さない、sidecar 残留後の再取得が無い) | **real** | 採用。probe を修正する |
| B8 | 1 つ目の P1 (helper から acceptance 全体への一般化) は未成立 | **real** | 採用。**production 入口の acceptance を実走して閉じる** |
| B9 | 「2400 秒間固まる」は不正確 | **real** | 採用。新 writer が renew すれば停止は無期限になりうる。owner release は stale 後も回復しない。この 3 分岐を測る |
| B10 | 2 つ目の P1 (候補集合の網羅) も未成立 | **real** | 採用。B2 の追加で埋める |

### refuted / 不採用

- **refuted:** 計画の「現行制約の下で比較すべき候補は 17 件ある」。B2 が 4 件の追加と 4 件の分割を
  示した。母集合は確定していない。
- **不採用:** 外部署名主体の実在を本 wave で実測すること。鍵と発行権限の配置は人間の手番であり
  (D906、D1400 決定本文)、AI は代行しない。
- **不採用:** Command 4 の重い monkeypatch を採用根拠にすること (F29)。機能確認としてだけ記録する。
- **不採用:** production の land を probe として実走すること。main を進める操作を測定目的で
  起動しない。lander 側は code 読解として記し、未実測と明記する。

## 2. 裁定の第一階層 — 世代とは何の単位か (B1 の採用結果)

候補を並べる前に、次の 4 つの粒度のどれを「世代」と呼ぶかが決まらなければ比較にならない。
D906 は署名対象に世代を含めることを求めるだけで、粒度は決めていない。

| 粒度 | 意味 | 非保持走行での定義可否 |
|---|---|---|
| G-acq | 排他権の取得ごと | **定義できない**。非保持走行には取得が無い |
| G-wave | wave ごと | 定義できる。ただし現行の非保持経路が既に `sha256(wave)[:12]` を合成しており、自己申告と同値 |
| G-main | main の進みごと | 定義できる。ただし受領証の `tested_main` の再符号化であり新しい情報を持たない |
| G-dir | lease directory ごと | 定義できる。同じ directory 内の再取得を区別しない |

**取得単位 (G-acq) を選ぶと、非保持走行の世代が定義できない。** D1449 は非保持走行を着地不可に
する方向を明示的に不採用としているので、G-acq を採るなら「非保持走行の世代」を別に定める必要がある。
これが本 wave で新たに特定した、裁定に足りていなかった中身である。

## 3. 実測計画 v2 (親が実走する)

probe は repo 外の script file として書き、production 入口を叩く。stdout は artifact として保存する。

| probe | 何を測るか | 閉じる所見 |
|---|---|---|
| P1 | 配置 matrix。18 シナリオ x claim / release / status / renew。外部台帳と xattr を読み戻し、entry 残置を全列挙する | B7、B4 の残留、A6 の環境可否 |
| P2 | 導出値の安定性。payload hash、holder+main hash、dev/ino/mtime/ctime/birthtime を renew 前後と再取得前後で比較する | C4 / C5 / C14 の恒真性、B1 の粒度 |
| P3 | **production 入口の acceptance を実走**し、payload に世代を足した lease で停止点・rc・受領証の有無・lease bytes 不変を観測する | B8 (P1 の 1 つ目) |
| P4 | **非保持走行**。受領証が lease 取得へ束縛されるかを確かめる | A1 (本 wave の主成果) |
| P5 | TTL 前後の 3 分岐 (claim 回収 / status stale / owner release 不能) と、新 writer の renew による停止の延伸 | B9 |

lander (`tools/dev_wave_land.py`) は実走しない。renew / release の結果が land 本体を止めないことは
code 読解として記し、未実測と明記する。

**P4 も実走しない (実測の途中で裁定を変更した)。** `tools/dev_wave_wait.py:3671-3690` は
main に遅れているとき post-claim merge を実行し、**wave branch に merge commit を作る**。
本 branch は main に遅れているため、非保持走行を probe として起動すると測定の副作用で
branch が動く。一方この所見は、書く側 (`:2903-2911`, `:3907`) と読む側
(`tools/dev_wave_land.py:792-800`) の 2 箇所の単純・無条件な code で確定しており、
実走が足す証拠は限界的である。**code 読解として記し「未実走」と明記する** (DW-O05 の
「子の非実走を緑と記録しない」と同じ規律を親自身に適用する)。

## 4. 成果物影響 (DW-G05)

粒度を決めずに候補を選ぶと、非保持走行の世代が定義されないまま署名 schema へ値が入る。
その値は lease の取得に束縛されないため、着地受領証の真正性の主張が実際より強く読める。
D906 が却下欄で名指しした「署名だけを足して恒真になる」形にそのまま当たる。
