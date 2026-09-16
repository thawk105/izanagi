---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-worklog-state-fix-20260917
seq: 1
title: 既裁定なのに「裁定待ち」のまま残っていた次の一手 23 項の状態語を根拠 D で照合して訂正した (docs のみ、branch worktree-dev-wave-worklog-state-fix-20260917、実装差分 0)
---

## 本文

- **出発点は /rulings 全件 第 20 回の B-1 節 (既裁定の主題照合) と依頼の一覧である。** 各 ID の描画行は
  carry stub だったので、carry 鎖を遡った実体本文 (entry 1178〜1546) を対象にし、根拠 D の逐語と
  現物 (コード・事前登録・insight) で残作業を確かめてから、`完了` / `更新` に分けた。
  一律に実装手番へ変換していない — 完了 10 件、裁定済み → 実装手番 6 件、→ AI の実測・記録・収容手番 6 件、
  → 保留 (整合待ち) 1 件。
- **稼働 wave が所有する ID は無かった。** 全 worktree (`.claude/worktrees/` 35 本・`.codex/worktrees/` 2 本) の
  spool fragment を対象 ID で走査して 0 件。同時刻に走る peer (rulings 自己改善 wave) へ編集面を照会し、
  「既存 T の `完了` / `更新` は 1 件も書かない」と回答を得た。T-2402 / T-2665 は entry 1596 が更新済みなので
  触っていない。真に裁定待ちの項 (T-2724 (a)〜(d)、T-2632 の 3 件、T-2288 の A-5、T-1505、
  T-2732 / 2735 / 2737 / 2742、T-2035 / 2037) にも触っていない。
- **`完了` にした重複項は、残作業を持つ同一面の ID を本文で名指しした。** T-2442 は T-2458 (D1826 の
  条件付き相乗り待ち)、T-2701 は T-2463 (D1901 の実装手番)、T-2180 は T-2102 の実装 (entry 1219、
  D1431 / D1521)、T-2140 の floor 欄は T-2288 の凍結後工程が持つ。
- **T-2693 は branch `worktree-dev-wave-t2639-branch-rescue-path-first` が撤去済みで patch-id 比較の相手が
  無い。** 実装 `99125e783` と段 7 記録 `aa0a34a55` が main の祖先、entry 1542 (同 wave の記録) が fold 済み、
  `impl-dev-wave-t2639` は main に対し ahead 0 であることから land 完了と判定した。
- **「裁定済み → 実装手番」と書いた項は着地の有無を現物で 1 回見た。** T-2459 は `report == expected` のまま、
  T-2451 の issuer は `loaded_head` を形式検査だけで転記、T-2478 の `DW-O26` に `--repo` checker の義務なし、
  T-2447 の P2 / P6 は `docs/dev-wave/` に無い、T-2393 は D1701 の実装 wave が worklog に無い。
  T-1912 の事前登録 §7.2「pair の完全性と receipt shopping」は D1986 項 3 が着地済みとした束縛を
  「強制しない」と書いたままで、追補は未実施である。
- **T-2487 の保証限界の明記 (D1892) は `output/insights/2026-09-09/t2457-a6-fanout-live/README.md` の
  「保証しないこと」4 (hard bound は 12 時間の walltime だけ) が既に担っている**と読み、`完了` にした。
- docs-only で子ゼロ (段 2・3・5・6 を省略)。実装面の差分は 0、変異 matrix は免除 (D95 決定 2)。
  受入全走の結果は本エントリの末尾に書く。工数: codex 子 0 本、計算ノード job 0 件。

## 次の一手差分

### 完了

- [T-2671] D2044 項 31 で「受入と着地で checker の実行環境を揃えない、受領証が跨がらない状態のまま置く」と
  裁定した。残作業はない。
  remaining: none
  base: 24fcc31c136b737770f7f9e12ba0a1bbe3d5061c90b080a80084dfe5db7a14ed

- [T-2645] D2022 で発見経路は既存の参照方式 3 本だけと裁定し、`DW-S01` への追加は却下した。
  `docs/cc-diagnostics.md` と `docs/README.md` / `docs/glossary.md` / `patches/README.md` からの誘導は着地済み。
  remaining: none
  base: c2a1c65fa49655706e8256aa4f7ea3ae659e97fc23d6145045c4f37f03aff4a3

- [T-2487] D1892 で遠隔検査へ追加の timeout を入れないと裁定した。hard bound が 12 時間の walltime だけである
  限界は `output/insights/2026-09-09/t2457-a6-fanout-live/README.md` の「保証しないこと」に明記済み。
  再訪条件 = 遠隔検査が実際に停止して資源を占有した例の観測。
  remaining: none
  base: d4930f98f913257f3a825a6becbc6995a39d8dc22c9398d7dd18a1862d36d657

- [T-2442] D1826 で「派生値は台帳から外して consumer が数える、専用 wave は立てず相乗り、衝突 hunk が実際に減る
  ことを確かめてから」と裁定済み。同一裁定は [T-2458] が条件付き相乗り待ちとして持ち越し中で、本項は重複。
  remaining: none
  base: 8e23c5f20d1a491997b6f60b703bd3192bcd25084d6a36fa48a31a23ae21f22e

- [T-2450] D1905 で `--no-replace-objects` を付けないと裁定した。`refs/replace` が本 repo に存在せず作る運用も
  無いことは同決定の本文が前提として明記している。
  remaining: none
  base: 0f0e9acc5e81aa5f9ba55e3d7f992b8923ad685d8cbf044329d97e4b605b2844

- [T-2140] D1812 の 4 項は反映済み。残余 2 件のうち [T-2464] は D2079 で着地 (entry 1571)、[T-2465] は
  entry 1581 で §11.3 の追記訂正が着地した。§5 floor 欄の記入は [T-2288] が凍結後の工程として持つ。
  remaining: none
  base: 3e40c9ea22dd0a78afe010f31153f19d3f81c848d91879d2e79ef22cbe537265

- [T-2693] 実装 `99125e783` と段 7 記録 `aa0a34a55` は main の祖先、同 wave の記録 entry 1542 は fold 済み、
  `impl-dev-wave-t2639` は main に対し ahead 0。branch `worktree-dev-wave-t2639-branch-rescue-path-first` は
  撤去済みで patch-id 比較の相手は無いが、land は完了している。
  remaining: none
  base: e89d7975fab5ee86c47ddc7b9153653f070384387a9a1e617576e256161f6007

- [T-2180] [T-2102] の α 裁定は D1431 (周辺実測を根拠に狭める) で下り、配置は D1521 (registry admission 限定)。
  実装は entry 1219 で land 済み (述語は `_validate_attempt` のみ、M12 は producer 側の直接検査へ再定義済み)。
  remaining: none
  base: c87d0cbe7bf642e51a283209344fcdf2a7c03bf04a532589c02a6f1b2440fbd6

- [T-2701] D1901 で「受領証 schema へ shard 別 wall の field を足す」と裁定済み。同一裁定は [T-2463] が
  実装手番として持ち越し中で、本項は重複。
  remaining: none
  base: 92d9951edf8c5f6d32a5ecfc11c6b08998a5366a111a5e3f3112427a12ab3fa1

- [T-2690] D2054 の却下欄で「削除 fragment にも fallback を足す」を却下した。required の不在も old blob の
  過去存在も削除という required state の到達を証明しないため、削除 fragment は fallback の対象外。
  remaining: none
  base: 20b016bd39095216423de61200622174a00d7af6fad0a919d5f0e48d86f66747

### 更新

- [T-2670] **P1・裁定済み (D2044 項 5) → 実装手番**: `merge-history-provenance` の監査位置を、取り込んだ
  変更を選択集合に含める側へ動かす。中止・後始末の契約も同じ変更単位で直す。説明文を実装へ合わせる案は
  採らない。着地は未確認。
  base: 92ecb682a061cfaee8f441defe3af016d689c6edba17644c34a3c32b1e80509f

- [T-1912] **P1・裁定済み (D1986 項 3) → 記録手番 (AI)**: block id・precursor・proposal・on/off receipt の
  4 者を封印 registry と凍結 manifest へ束縛する部分は着地済み (`227ec6892`) として扱う。残る publication 間の
  選別は閉じない — 閉じていないことを成果物の文面へ出す (D1884 / D1896 と同じ形)。事前登録 §7.2 / §10 の
  「強制しない」記述のうち事実と違ってしまった部分 (§7.2「pair の完全性と receipt shopping」は 4 者の束縛を
  強制しないと書いたまま) を追補で訂正する。詳細と逐語は `output/insights/2026-09-14/t1912-pair-completeness/`。
  base: 8b49cd206e960a605122495eaacc48cc46388445efa1bc61819b82881a98fbe8

- [T-2489] **P2・裁定保留 (D1910 項 2) → AI 実測手番**: A-2 (rr5 / rr50) の `scheduler.nodes` を 5 にするかは
  必要な実測が揃うまで裁定しない。A-6 の実走資料は nodes=5 の結果を A-2 へ一般化しないと明記している。
  A-2 固有の 5-node 実走か同等の probe で出力同値性・所要短縮・queue 費用を確かめ、実測後に改めて索引へ載せる。
  base: 766c0206f78752ad3e0cd689851ba0ca0fe3b50215ccba664e5a0e9548f428aa

- [T-2447] **P2・裁定済み (D1893) → 実装手番**: P2 (段 3・6 のレンズ 1 本を過剰・削除レンズに固定) と
  P6 (研究前進か実測欠陥の根拠が無い scope 外所見は起票せず記録のみ) を採る。P4 (変異 matrix の義務を
  防壁・台帳・受入判定の実装面に限定) はそのままでは採らず、「正しさ・受理・記録の証拠を変えうる実装」を
  すべて義務の対象に残す形へ定義し直してから採る。`docs/dev-wave/` への収容は未着地。
  根拠は `output/insights/2026-09-08_dev-wave-research-gate/RESULT.md`。
  base: 34749f5b60de0f17d54f987a95af8ac62edb71fbd13495dae10bc43a1eba557a

- [T-2393] **P3・裁定済み (D1701) → 実装手番**: `not-consumed` の試行を outer receipt へ運ぶ。`not-consumed`
  では report hash を要求しない条件分岐を report-count / status / hash 契約へ明記し、status・個数・slot identity を
  outer receipt と受入側で照合する。運ばずに限界として明記する案は採らない。着地は未確認。
  base: 4e7d84ac9a81e883d53dee6255ca8279a679c7327e20679a7641a4b4356d2d2c

- [T-2394] **P3・裁定済み (D1704 項 6) → 記録手番 (AI)**: 独立 clone / repository を跨ぐ best-of-N は閉じない
  (閉じるのに要る一元的一般化は D1269 が却下済み)。単一 repository という運用前提を事前登録と成果物へ限界として
  明記し、機械的に閉じたと主張しない。明記は未着地。
  base: 261bca6cc007ec68f9f516f40bcbbe1f0269dff89cdbc1c7527f8e7bb4892fd6

- [T-2451] **P3・裁定済み (D1906) → 実装手番**: issuer が `summary["loaded_head"]` を検証せず転記している件を、
  load 済み spec の `loaded_head` との 1 比較で塞ぐ。現物は形式検査 (40 桁 hex) だけで、着地は未確認。
  base: 321bbdf4c3240fab9bd836b3909b80ad4eb6ca00143b261ef61be3bcb57c5a8e

- [T-2459] **P3・裁定済み (D1904) → 実装手番**: A-2 certification の materializer の再導出一致検査を partial (v2) と
  full (v4) の両側で `_canonical_json(report) == _canonical_json(expected)` へ変える。現物は `report == expected` の
  ままで、着地は未確認。
  base: 1d3621b3ac0fe0eb321f58fb911c6b1874c7a4ada5c488701f7e39ccbe207965

- [T-2478] **P3・裁定済み (D1908) → 実装手番**: 受入前に `--repo` を取る checker を叩く義務を `DW-O26` へ足す。
  byte 予算に収まらない場合は D782 が委任した D730 の手順で閉じ、上限引き上げに至った場合だけ報告する。
  `DW-O26` に義務は未着地。
  base: 0dbb47e1f6ef3015b1a2b75a1add990980f3b6d2107044e696e9d1aa0c3ed534

- [T-2696] **P3・裁定済み (D782) → AI 手番**: 隔離 session からの実装子成果の取出し手順 (`diff -u`→`git apply`) の
  収容は、D730 の手順 (既存記述の削減 → 独立 3 例なら例外収容 → それでも無理なときだけ上限引き上げ) を AI が
  適用して閉じる。上限引き上げに至った場合だけ報告する。`DW-S05-A` には所有 path 限定 patch の手順
  (`git diff --cached --output=<f>`→`git apply`、`d9f4a63bd`) が既に在り、差分はそれとの統合で測る。
  base: 06beb40ef14de809eb947ba12f94d6ab6c3033093e3a8eba1e71b7718b6c107c

- [T-2290] **P2・裁定済み (D782) → AI 手番**: `tools/dev_wave_land.py` の cwd 要件 (rc=22) の `DW-O23` への収容は、
  D730 の手順を AI が適用して閉じる。上限引き上げに至った場合だけ報告する。
  base: 3b8868b0295c2461182f75d866d7cdc1729c35b71fa257b2e27389d9f77aac2f

- [T-2291] **P2・裁定済み (D782) → AI 手番**: 再投入時に log/receipt を新 path にする義務の `DW-O27` への収容は、
  D730 の手順を AI が適用して閉じる。上限引き上げに至った場合だけ報告する。
  base: bb2e1b5600e88a547b55ff918dc35dce3a0ec88580b4b929b7b2bed336f5ab25

- [T-2507] **P2・裁定済み (D1875) → 保留 (整合待ち)**: `run_origin_trial` の production 呼び手は置かない。
  fixture provider の real build 拒否の解除、`--no-build` 経路の変更、世代制約との整合は、承認済み世代予算
  (D410 で 2) と還流設計 (D106 残余 1) の整合が決まるまで着手しない ([T-2293] Q2〜Q4 と同一面)。
  到達しない呼び手を production へ置く案は採らない。
  base: 7d6db047bed540d9cc56d94a19b2d9048a5972ddf6cd3669de1836b9bd2f0cd1
