---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2599-stale-carry-states
seq: 1
title: [T-2599] 裁定済みなのに次の一手の本文が裁定前のまま残る 31 項の状態語を現行の裁定へ合わせ、終端が裁定で明示された 2 項を閉じた (docs のみ、branch worktree-dev-wave-t2599-stale-carry-states、実装面の差分 0 なので変異 matrix は DW-S04 により免除)
---

## 本文

- **対象の実体は現行 worklog に 1 件も無かった。** 末尾エントリの「次の一手」641 項はすべて
  carry 印 `- [T-NNN] (1518)` で、実体本文は archive の過去エントリにある。明示参照鎖を遡って
  各項の実体 (項 / エントリ / file / 行) を機械抽出し、それを更新対象にした。
- **起点の索引 (2026-09-14 /rulings 第 18 回、repo 外、AI 起草) は権威ではない。** 30 行を
  1 行ずつ `docs/decisions.md` の現物で裏取りし、**1 行を誤りとして外した** — T-2456 は索引が
  「D1768 で既裁定」とするが、D1768 は本項が前提として引いている決定であり、D1809 の却下欄が
  「class の定義は D1768 のまま…uniqueness の再定義はユーザー裁定へ返す」と明記している。
  **真に裁定待ちなので触っていない。**
- **敵対相談 2 本 (read-only、レンズ = 対応づけの当否 / 取りこぼしと fold 副作用) が
  親の案を 6 行で覆した。** 内訳は、終端が裁定で明示済みの 2 項 (T-2074・T-1728) を
  「状態語の書き換え」で留めようとしていた誤り、裁定保留を裁定済みと書いていた 1 項 (T-2484)、
  裁定の射程を広げすぎた 1 項 (T-2412)、裁定対象外の問いを取り残した 1 項 (T-2445)、
  後続の限定変更と着地を見落とした 1 項 (T-2504) である。
  **親の「実測した事実」も 2 件が過剰だった** — checker 側の pin は現に在る (`next-tasks` は
  `tools/check_docs.py` の frontmatter / arguments 検査に登録済み) ので D1890 (1) を丸ごと
  未実施とは言えず、T-2579 は後続エントリで限定回収まで完了している。
- **終端が裁定で明示された 2 項は閉じた。** D1997 は「持ち越し項目としての『次の attempt を
  投入する』は…完了として閉じる」と決め、却下欄で**「重複項目を閉じずに残し、本文だけ現況へ
  書き替える」を明示的に退けている**。D1704 項 4 は「無条件拒否の残余 — 3 件へ分割済みで、
  本項に独立した手番は残らない」と書いている。よって [T-2074] と [T-1728] は `更新` でなく
  `完了` にした。**終端の宣言は裁定が明示している 2 項に限り、他項は親の判断で閉じていない。**
- **取りこぼしを 5 件足した。** 起点の索引に無いが同型だった項を、相談が現行 active 641 項の
  carry 鎖から見つけた。[T-2101] (D1897)、[T-2481] (D1885)、[T-2498] (D1891)、
  [T-2621] (D1996)、[T-2633] (D1986 項 4) で、いずれも決定の逐語を現物で確かめた。
- **[T-1912] は同型だが触っていない。** D1986 項 3 が「**本項の worklog 側の更新は所有 wave の
  未 fold fragment が持つため、本 wave は触れない**」と明文で書いている。所有 wave の fragment は
  未 land のままである。
- **棄却した所見はない。** 相談の 6 件はいずれも real として採った。
- 更新した 31 項と根拠の対は次の一手の各項に書いた。索引形は下表。

| 項 | 根拠 | 項 | 根拠 |
|---|---|---|---|
| [T-2067] | D1872 | [T-2490] | D1883 |
| [T-2101] | D1343 / D1846 / D1897 | [T-2491] | D1882 |
| [T-2344] | D1884 | [T-2492] | D1881 |
| [T-2355] | D1657 / D1666 | [T-2493] | D1880 |
| [T-2412] | D1873 / D1802 | [T-2494] | D1900 |
| [T-2445] | D1890 | [T-2498] | D1891 |
| [T-2446] | D1889 | [T-2501] | D1879 |
| [T-2453] | D1907 | [T-2502] | D1878 |
| [T-2454] | D1888 | [T-2504] | D1877 / D1936 項 43 |
| [T-2460] | D1902 | [T-2506] | D1876 |
| [T-2463] | D1901 | [T-2621] | D1996 |
| [T-2464] | D1871 | [T-2633] | D1986 項 4 |
| [T-2465] | D1887 / D1936 末尾 | [T-2074] (完了) | D1997 |
| [T-2466] | D1886 | [T-1728] (完了) | D1704 項 4 |
| [T-2479] | D1838 / D1839 / D1885 | | |
| [T-2480] | D782 (D730 の手順) | | |
| [T-2481] | D1885 | | |
| [T-2484] | D1910 項 1 (裁定保留) | | |
| [T-2488] | D1870 | | |

- **裁定の内容は 1 件も変えていない。** 変えたのは状態語と、根拠 D の名指しだけである。
  実装の着地は項ごとに監査していない。実測した項にだけ着地を書き、他は「着地は未確認」と明記した。
- **台帳側の食い違いを 1 件見つけた。** D1984 の却下欄が「二読 fallback の択一は未裁定であり」と
  書いているが、同じ択一は D1872 が exact 必須で裁定済みである (D1831 が返した択一への回答)。
  D1984 の決定主文は caller メタテストの不採用であって D1872 の撤回ではないため、現行の効力は
  D1872 にあると読める。decisions は追記でのみ訂正する対象なので、実施せず新規項として起票した。
- **触らなかった 6 項とその理由。** T-2456 = 上記のとおり真に裁定待ち。T-1912 = D1986 項 3 が
  触れるなと明文で書いている。T-2485 / T-2515 = エントリ 1480 で既に更新済み。
  T-2266 = エントリ 1512 で更新済みで現に開いた裁定を持つ。T-1711 = 本文が既に
  「裁定待ちでなく既定方針あり」と書いている。T-2422 = 状態語が「P3・新規」で裁定待ちを
  主張していない。
- 実装面の差分は 0 である。
- 工数: codex 子 2 本 (いずれも consult・read-only・gpt-6-astra / medium、`outcome=accepted` /
  `stop_reason=completed`)。対応づけの当否が wall 262 秒・model call 11・出力 6,776 token、
  取りこぼしと副作用が wall 368 秒・call 16・出力 7,865 token。入力はほぼ cache 済み
  (66 万 / 75 万、112 万 / 123 万)。計算ノード job は使っていない。
- 生出力と資料は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2599-stale-carry-states/`。

## 次の一手差分

### 完了

- [T-2599] 裁定済みなのに次の一手の本文が裁定前のまま残る 31 項の状態語を、根拠 D と対にして
  現行の裁定へ合わせた。起点の索引 30 行を decisions.md の現物で裏取りして 1 行 (T-2456) を
  誤りとして外し、索引外の同型 5 件を足し、終端が裁定で明示された 2 件を閉じた。
  裁定の内容は変えていない。
  remaining: none
  base: 67fbc0109fc049e84953a2f7339073c873bf8f65fc4449074c2efe5ec698d3db

- [T-2074] A-1 balanced5 pilot の追加 attempt は D1997 が「投入しない。持ち越し項目としての
  『次の attempt を投入する』は、同じ作業が 2026-09-11 に attempt-0004 として実施済みである
  ことを理由に完了として閉じる」と裁定済みである。依存先 [T-2349] の fix もエントリ 1304 で
  着地しており、pilot の sizing 入力は D1973 の証明書と本走 policy 凍結で消費済みである。
  本項が持っていた投入手番は消滅しているので閉じる。本走の認可 (人間手番) と実行面の整備は
  D1997 が名指しする既存の 2 項目が持つ。
  remaining: none
  base: 7e824dd9bfd129f96af35c39841ca22093bfea53b9dcc050d8936ef404ddb0ad

- [T-1728] 無条件拒否は二段束縛の条件付き検査へ置き換え、token は `p3_s4_loop_trigger_gating` から
  `run_campaign` を経て `pipeline.evaluate` まで結線した。「関門が production で発火することを
  実データで示す」は達成できないと確定している (activation 評価器の allowlist と C05 schedule
  正本が独立に塞ぐ)。残余は D1704 項 4 が「3 件へ分割済みで、本項に独立した手番は残らない」と
  裁定しており、分割先の [T-2158] [T-2159] [T-2160] が各々の手番を持つ ([T-2159] は D1567 が
  whiteboard・予約値・台帳 path・schedule 行 hash の 4 件を材料確定後に再提示するとしている)。
  remaining: none
  base: ccda187745259d11ded718a992b72e81743ec5a5a09f2b0c40f1d5364153e9cc

### 更新

- [T-2067] **P1・(a)(b)(c)(d) 完了、(e)(f)(g) は塞ぎを再実測して不実装を維持。残る 1 件は裁定済み**:
  2026-09-14 の main で母集合を 3 者独立に数え直し、9 callsite / 9 関数 / 7 module・配線済み 7
  (狭い選択 API 5 + full launch validation 2) / 未配線 2 で D1831 の値と一致した。件数の出所は
  今も AST 走査であり、loader の caller を exact 固定するメタテストは実在しない。**(e)(f)(g) を
  塞ぐ 3 前提はいずれも現物で成立する** — (e) と (g) は `_load_s8c_schedule_authority` が無条件に
  raise するため予算台帳を作れる入力集合が空で、C05 は上流待ちのまま。(f) は clean scan の
  preimage が成果物へ保存されず、閉じるには D1241 / D1243 が禁じる署名・外部 nonce・一回性台帳の
  いずれかが要る。配線済み 7 の意味も狭い — 直接 API は非 g1 で空検査に、full launch は非 g1 を
  拒否し、`reverify` 経路は選択検査を通らない。現行 HEAD では loader 自体が `no-active` である。
  caller 閉包テストの新設は D1984 で不採用とした。**裁定済み (D1872、2026-09-09)**:
  `_gate_check_core` の二読 fallback (`s8b_oracle_driver.py:496`) は択 (ii) で決着している —
  v2 fallback を廃し exact な `LaunchValidatedFreeze` を必須にし、D65 決定 (5) の不変条件を
  全分岐で成立させる。D1872 は「現状維持で台帳へ記録する」を「穴を記述するだけで穴は残る」として
  却下している。実装面なので D95 の Codex role=author と変異事前登録が要る。着地は未確認。
  **いずれも D1241 / D1313 の advisory / non-certifying 上限を解除しない。**
  base: 3d267d07a88d6a5b9bea138c848c76336cf6b71beb71bf9a327da86c548f5824

- [T-2101] **P2・裁定済み (D1343 → bootstrap は D1846 で着地、continuation は D1897) → 明記手番**:
  実行ループ側の束縛は bootstrap で閉じた (D1846)。残っていた continuation の提案束縛は、
  D1897 が「**継続 (continuation) 側の提案は束縛対象外である**ことを事前登録と成果物へ限界として
  明記する。耐久 carrier の新設もリーク遮断の設計変更も行わない」と裁定した。登録値が指すのは
  block 共有の初期 proposal で、continuation の提案はアームごとに異なる次の合成であるという
  一次資料の事実 (事前登録 §5.1 と `precursor_hash_mismatch`) は変わらない。耐久 carrier は
  whiteboard の永続化契約を変え、リーク遮断は D39 / D45 の構造遮断に触るため採らない。
  一次資料 = `output/insights/2026-09-09_t2101-proposal-binding/README.md` §1〜§2。
  base: ea8ecf50e3b7e44de2189887d3c89afa382d911297c60ad0ceab2c8d0733a350

- [T-2344] **P2・裁定済み (D1884) → 段階実装の手番**: enforcement source closure の収載範囲は
  現行 63 で終端せず、D1075 が定めた推移閉包 (発行器起点を含む候補 165) を目標として段階実装を
  続ける。同時に、閉包が閉じるまで「certified 経路が source-bound である」を推移閉包の意味では
  名乗らない。段階のどこまでを次の変更単位に含めるかは実装 wave が決めてよいが、名乗りを先に
  広げてはならない。D1513 が求めた実測は完了している
  (`output/insights/2026-09-09_t2344-closure-reachability/`)。未収載は 69 でなく 77、発見集合は
  131 でなく 140、収載は 62 でなく 63 である。反実仮想 10 か所で受理判定が変わった例は 0 件
  だったが、手元の 50 campaign はすべて拒否され受理へ抜ける経路が実行されないため、D1884 は
  これを据え置きの根拠として採らなかった。
  base: bf0d2ad67eb81e93ccfa698bcd66e39fb4f2f5f548bf402db3ae3bd929876ff3

- [T-2355] **P2・裁定済み (D1657 / D1666) → 明記手番 + 再訪条件つき保留**: 条件関門が見た
  第三者生成 header (masstree `config.h` 等) と計測 build が使う同 header の bytes 同一性は
  **束縛しない** (D1657)。A-2 経路 (`paper_story_a2_certification.py`) にも同じ限界があり、
  insight と A-2 の設計に限界として明記する。第 2 の問い — 条件関門の他 4 呼び手
  (`backoff_overthrottle` / `backoff_profile` / `backoff_requested_us` / `backoff_repro`) に
  同じ prebuild を入れるか — は D1666 が「既定値のままとし、実測経路になった時点で同じ形を
  入れるかを裁定する」と定めている。現状は第 2 層が未修正で実測経路ではないため、再訪条件は
  未成立である。D1704 項 1 も同じ整理で索引から外している。
  base: 090f2dd0fe8a9db55d06886e6fe9db4c5df301edad4a1b1396da9689ec29ad56

- [T-2412] **P1・裁定済み (D1873) → 残件なし**: 凍結 spec の不動点に「唯一の親 + spec 1 path
  差分」という狭い形は**採らない**。D1774 が定めた祖先関係と tracked blob 一致の形を維持する。
  理由は狭い形が freeze commit の後続 commit で load 不能になることで、正常な前進で既存の
  凍結成果物が読めなくなるのは規律 7 に反する。**実装は既にこの形である** — エントリ 1357 で
  「D1774 に合わせて祖先関係へ直した (D1802)」と記録されており、D1873 が却下したのは狭い形への
  再変更である。branch `worktree-dev-wave-t2412-frozen-spec-fixpoint` の成果を不採用にする
  ものではない。
  base: 324286fb6b0125ac5f5ed37fa288d22f9dcdcdd61433accd76d2c6f1de3e5776

- [T-2445] **P2・編集境界は裁定済み (D1890) → 反映手番。Codex 側移設 (d) は本裁定の対象外**:
  `.claude/commands/next-tasks.md` について D1890 が (1) 共通自己改善契約
  (`docs/skill-self-improvement.md`) と checker の終端 pin に next-tasks を**加える**、
  (2) 本文の「本ファイル (repo 外)」という文言を消し `/work/1/SFC/tanab/scripts/` の絶対 path
  依存は runbook へ移す、(3) byte 予算は既存 3 command と同じ tight のままにする、と決めた。
  (4) Codex 側 `~/.agents/skills/next-tasks/` の repo への移設は**本裁定に含めない**ので、
  その採否は未決のまま残る。**(1) のうち checker 側は着地済みである** —
  `tools/check_docs.py` の command 終端検査に `.claude/commands/next-tasks.md` の
  `frontmatter_keys` / `arguments_count` が登録されている (実測)。一方
  `docs/skill-self-improvement.md` に `next-tasks` の出現は 0 件で、契約側は未反映である (実測)。
  base: d181239a48808ab92c3390c5d39692c404e61e889888997dac0bc58827934ecd

- [T-2446] **P2・裁定済み (D1889) → 残件なし**: `.gitignore` へ `.codex/worktrees/` は
  **足さない**。主 checkout で `git add -A` を打たず、対象 path を明示して stage する規律で
  再発 (F100) を防ぐ。D1797 のとおり除外設定で隠すと変異 harness が走行前後で bytes 一致を
  要求する共有 checkout の `?? .codex/worktrees/` 行が消え、F599 の既裁定と衝突する。
  D1936 項 26 も全面 ignore の却下を維持している。
  base: 05dd756f1efd49145bb6758d674d8866415dcc9f36549b0c46780ff229bdb953

- [T-2453] **P3・裁定済み (D1907) → 実装手番**: `Genome.canonical()` で flag 名に
  `|` `,` `=` を含む値を**拒否する**。protocol の許可リストや CCBench source 束縛へは寄せない
  (D1696 の再訪条件が未成立)。issuer は共有 helper の解釈に従うので issuer 側だけでは締められない。
  実装面なので D95 の Codex role=author と変異事前登録が要る。着地は未確認。
  base: d79c638685231f3b5b48f14fb71b1259001a95d27fbda01c2d2623d61808b7de

- [T-2454] **P2・裁定済み (D1888) → 残件なし**: `/cleanup-branches` 実行中の mutation allowlist を
  機械で強制する経路は**作らない**。信頼できる非モデル起動器・OS 水準の閉じ込め・attestation の
  いずれも新設せず、規律と敵対監査のまま運用する。成立には主目的 (CC 自動合成) の主経路から
  最も遠い基盤が要り、作っても D387 / D1128 の限界 (検証器と被検証対象を同じ主体が変更できる) は
  残る。モデル自己申告の marker は恒真になるため代替にしない。**機械防壁が完成したという意味では
  ない。**
  base: 4ef7606bbd54ac87f51902fd7ca4bd8073818c37eb52c197330c50d612eb9cdc

- [T-2460] **P3・裁定済み (D1902) → 記載手番**: `/cleanup-branches` の既存 2 欠陥 (裸 ref の
  曖昧性、`git branch -d` の判定基準) は**文面で塞がない**。どちらも現 repo では到達しないという
  実測を限界として 1 行記す。実測は、tag が `t1806-pre-rebuild-history` の 1 本だけで branch 名と
  衝突せず、upstream を持つ local branch は §2 が削除対象から除外している `main` の 1 本だけ、
  という内容である。裸 ref の修正は +22 bytes 要り現在の余りは 2 bytes で、予算のために既存の
  安全義務を削るのは自己改善契約が禁じている。
  base: aa51f783a88783577e2fa224c52e9a479bb63d62fdff1e8dba93824e7ee8a892

- [T-2463] **P3・裁定済み (D1901) → 実装手番**: 受入時間の測定面は、**受領証 schema へ
  shard 別 wall の field を足して**満たす。D1620 の文言 (receipt が記録する最遅 shard の wall、
  collection 開始から teardown 終了まで) は変えない。junit の `time` が D1620 の区間と右端で
  2.8〜7.1 秒ずれることは [T-2462] が実測済みで、junit 側は代替にならない。D1901 は
  「D1620 の文言を junit 側の面へ訂正する」を、固定した測定面を後から動かし過去の実測との
  連続性を失うとして却下している。D1620 自身が「receipt のどの field が区間と K を示すかの
  文書化は AI 手番として残す」と書いており、field を足す方向は同決定の枠内である。着地は未確認。
  base: e74b98ef722ac809c3023604c4a8c5623362d94afd678427cca505e8f7940122

- [T-2464] **P1・裁定済み (D1871) → 実装 + 追補手番**: B-4 事前登録の「実行責任者・開始時刻」欄は
  **開始時刻を発効条件から外す**。`p3_b4_admission_record.py` の行 label 集合は変えず、本欄に限り
  `未記入` を受理する。§0 の原子性・sentinel 規則は他の欄についてはそのまま維持する。
  事前登録本文の改訂は同文書の改訂契約 (追補) に従って別 wave が行う。受理側がまだ `未記入` を
  拒否しているのは D1649 決定 2 の未実施であり、本欄に非 sentinel の値を定義する案は同決定と
  食い違うため却下された。着地は未確認。
  base: ba647aebf3082a57feb1ca31f16ec27642c13ba85de7a66542bf064dad0d7af6

- [T-2465] **P2・裁定済み (D1887 / D1936 末尾) → 追補手番 (AI)**: 事前登録 §11.3 が担当者の指名・
  対象集合・統計関数・採用証拠の受理をユーザー手番として列挙したまま残っている件は、
  **追加の授権を要しない**。D1887 が担当者の指名と採用証拠の受理について「D1641 決定 1・2 の
  反映として AI が追記訂正してよい。追加の授権は要らない」と決め、残していた対象集合と統計関数の
  2 点は D1936 末尾が「D1641 決定 3 に記載されているため、追加授権ではなく追記反映とする」と
  閉じた。よって 4 点すべてが AI の追記訂正で反映できる。n へ言及する反映は後続 D1695 の 62 を
  採り、失効した 59 を復活させない。決定の効力は変えず追記でのみ訂正する。
  base: 883f71528f189eaa9daa8a972b17f77a0ba6a7768f693e30c0a14e30115b90f5

- [T-2466] **P2・裁定済み (D1886) → 残件なし**: 8c 予算 consumer の極小正値 regime は
  **閉じない**。最低予約量の導入も、正式 workload の事前コスト計画との結合も行わない。どちらも
  事前登録の規範に無く、実装が決めると D1832 が避けた「権威のない仕様」になる。総上限 1e-9・
  arm 上限 各 1e-9・holdout 上限 各 5e-10・予約 各 5e-324 が `held` になること自体は事前登録の
  述語を満たしており、実害の観測も無い。
  base: be5d08bab587850dbc7fb8483e4e1d03adc9394c8205d6066fef3fc8876d9317

- [T-2479] **P2・裁定済み (D1838 / D1839 / D1885) → 決着 (再訪条件つき)**: 3 field を正常値で
  自己申告した偽 WAL が述語を通ることは**閉じない**。D1839 が主張してよい範囲を
  「WAL に記録された 3 値が正常であること」だけに限定し、WAL の真正性・値の生成主体・verifier が
  実際に走ったこと・block record との attempt 対応は主張しないと定め、母集合を「reader が例外なく
  返した終端済みで parse 可能な `verify_done` record」と定義した。D1885 が WAL の欠落・読取例外・
  未終端 tail の fail-closed 化を採らず開示のまま扱うと決め、D1838 が実施形を 3 field の
  exact 値述語に固定した (系列別 WAL digest literal は新設しない)。閉じるには暗号学的束縛 =
  新しい gate 機構が要り、D1772 が却下している。再訪条件 = 偽 WAL による誤った report 発行が
  実際に起きたと示せたとき、または論文の主張が WAL の真正性まで要求するようになったとき。
  base: 0affebb3f4fe986b25d75b4fb56c1f7a8b71d33edcf645157c9963a24160d708

- [T-2480] **P2・裁定済み (D782) → AI 手番**: 段 1 の pin 閉包で「行番号を焼いた test も閉包に
  入れる」を `DW-O09` へ明文化する件は、**ユーザー裁定へ返さない**。D782 が「手順書の節予算に
  入りきらない収容案件は、案件ごとに裁定へ返さず、D730 が定める手順 — 既存記述の削減を試す →
  独立 3 例以上なら例外として収容する → それでも収容先を作れないと確かめられた場合にだけ
  上限を引き上げる — を AI が適用して閉じてよい」と定めている。上限引き上げに至った場合だけ
  報告する。`DW-O09` は 992 bytes で単節予算 1000 bytes に対し残り 8 bytes、1 文で約 220 bytes
  という実測は、D730 手順の入力として使う。
  base: a702f2ab7d3b1d30cc4c29767b3ac2cfde5868d8f858c6e02ad00553caa12d52

- [T-2481] **P2・裁定済み (D1885) → 残件なし**: WAL 欠落・読取例外・未終端 tail は述語へ到達
  しない。これらの経路では `incomplete_slots > 0` か `wal_read_error` が立った見て分かる別物の
  report になるので、[T-2409] が名指しした「同じ判定の report が出る」穴には当たらない
  (`_verification_completeness` は一度も raise せず開示するだけであることを実測)。
  D1885 が**fail-closed 化しない**と決め、現行の開示のまま扱う形を維持した。理由は、
  fail-closed 化が受理集合をさらに狭め、欠測を含む正常な部分結果まで捨てることである。
  base: e81db61477208f6e253a747ad6a331c3bceece68bfd0bb677e53a0751ca4153a

- [T-2484] **P2・裁定保留 (D1910 項 1) → 実測手番**: 変異 harness の外側 watchdog
  (`spec.timeout_seconds` / `hang_timeout_seconds`) が dispatcher の締切構造のどの区間を覆う
  契約かは、D1910 項 1 が「必要な実測が揃うまで**裁定しない**。実測後に改めて索引へ載せる」と
  決めている。**これは択一への回答ではなく、実測先行の保留である。** 測るのは区間別の所要と、
  既存 artifact を混雑下で走らせたときの実際の発火である。発火する実在 artifact は
  `output/insights/2026-09-07_t2195-policy-binding/mutation-spec-final.json` (timeout 3600 /
  hang 900、hang_risk 変異 5 件)。実測は 2026-09-16 時点で未取得。裁定すべき 3 択 ((a) 契約の
  定義、(b) 既存 collection gate の式を合わせるか、(c) 理由付きの早期診断に留めるか) は
  そのまま残る。根拠は
  `output/insights/2026-09-09_t2279-mutation-dispatch-override/README.md` 第 3・4 節。
  base: 37b5f9381530e67d36db2d9c32a4ffeb5ccd03918d00e674ef13ea92715eb96e

- [T-2488] **P1・裁定済み (D1870) → 残件なし**: 実行基盤の測定に付随して得た A-6 の性能値
  (効果 −4.876%、前回 −5.784%) は、A-6 の 2 本目の attempt として**扱わない**。実行基盤の
  副産物のまま残し、A-6 の主張には使わない。attempt として数えるには attempt 数と停止基準の
  事前登録および `tracked_destination` の新 leaf が要り、値を見た後の昇格は規律 3 を崩す。
  D1841 が同型の「結果を見た後の虚偽分類をコードで検出できない」設計を既に退けている。
  base: 31d359e0496f404781b77f72edcbea14b698d1d90e09c6092767649a384b8c0b

- [T-2490] **P2・裁定済み (D1883) → 明記手番**: 条件 evidence を実行 binary の同一性へ束縛する
  新しい関門は**作らない**。「条件 evidence は要求した測定条件が供給され実効化したことだけを言い、
  その条件で建った binary であることは言わない」を保証限界として成果物へ明記する。
  注入 seam を持つ driver 全体に共通する性質で配線前から存在し、実害の観測が無い。
  D1674 (evidence writer の権限分離は作らず運用前提を保証限界として明記する) と同型である。
  **限界が閉じたという意味ではない。**
  base: b562e5f6c1e20e714c4ffad82a78c477ea8c8806037a9e9145f1f4e7ab9feadd

- [T-2491] **P2・裁定済み (D1882) → 実装手番**: 閉包検査の `injected-*` 特殊経路について、
  「sink の直後に名前の suffix が一致し第 1 引数が sink の代入名である call が 1 つある」だけでは
  **被覆済みに数えない**。この形を fail-closed 側へ寄せる。族全体に効く共有機構の変更なので
  D1869 に従い名指しした判定だけを変える。D1882 は「文言だけ弱める」案を、F918 が実測した
  「拒否を握り潰す変異が閉包検査を通る」穴が残るとして却下している。**裁定済みは閉包検査の穴が
  修正済みという意味ではない。** 着地は未確認。
  base: 19d7c100eeab5efd0e0f559e00330e7ce4a42fc9a1a40a49174670f8b486ed7b

- [T-2492] **P2・裁定済み (D1881) → 実装手番、実装は [T-2545] が持つ**: B-4 の prerun
  publication は、**事前登録が publication root を 1 つ名指しし、発行器はその root 以外での
  発行を拒否する**。呼び手が実行時に root を選ぶ現状は改める。呼び手が選べるままだと、任意の
  提案に対しその hash を持つ registry を別 root へ発行すれば bootstrap 束縛も通り、束縛が
  恒真になる (規律 6)。事前登録に 1 行足すだけで閉じる。エントリ 1411 の時点で未実装であり、
  実装は [T-2545] が持つ (2026-09-16 時点で active)。一次資料 =
  `output/insights/2026-09-09_t2101-proposal-binding/verbatim/s3-consult-sol.md` の S3 / S5。
  base: 716e656d7162e63760cbd5b044a52e1e169ebbba46b4bc1a82dc72a7678ecde0

- [T-2493] **P2・裁定済み (D1880) → 実装着地済み (エントリ 1411)**: formal B-4 の母集合は
  **analysis manifest の 201 行**に固定する。scheduled attempt registry の全行は母集合にせず、
  manifest 外の registry 行は hash が一致しても実行しない。エントリ 1411 の [T-2051] wave が
  formal bootstrap の manifest membership を閉じた。後続 D2016 も 201 行を上書きしていない。
  B-4 全体の完成を主張するものではない。一次資料 = 同 s3-consult-sol.md の S13。
  base: 536dfb56cfbbc3ca56368180714765dc7d378577f743747d93a0ca99127eb553

- [T-2494] **P3・裁定済み (D1900) → 明記手番**: 提案束縛の保証境界は **formal launcher 限定**と
  明記する。B-4 marked config を受けるすべての sink へ広げる型変更は行わない。束縛は
  proposal loader 内に閉じており `drive_iteration` / `run_one_iteration` の型には載らない。
  D1343 の文言は「実行ループ側」だが実装の射程は loader である。全 sink へ広げるには束縛を
  型に載せる設計変更が要り、実害の観測が無い。一次資料 =
  `output/insights/2026-09-09_t2101-proposal-binding/verbatim/s3-consult-luna.md` の L16 / L23。
  base: 3238bb75928d561210776a3abc324ef6bc782ae11f08d350d4d15982eb9acea1

- [T-2498] **P2・裁定済み (D1891) → 実装手番**: `hooks/guard_bash.py` の重量 interpreter 検出が
  直接の pytest 起動を拒否する一方で profiler module を挟んだ形を素通しする件は、D1891 が
  「**既存の script-executor parser が抽出した内側の実行対象へ、同じ重量判定を再帰的に適用する**。
  wrapper module の列挙追加はしない」と裁定した。`cProfile` / `profile` / `coverage` は既に
  `_SCRIPT_EXECUTOR_MODULE_OPTIONS` と `_script_executor_targets` に列挙されており、素通りは
  列挙の不足ではない。2026-09-09 に login node で 172 秒の走行が 1 回素通りした実測がある
  (load 17/96 コアで実害なし)。正本は `hooks/README.md`。実装面なので D95 の Codex role=author と
  変異事前登録が要る。着地は未確認。
  base: e5f1d087dd54f6a6189c6d852a673632fcce939203446b8e7ee2cc2d6940e5f7

- [T-2501] **P2・裁定済み (D1879) → 実装手番 (語の整理だけ)**: [T-2418] が scope 外として
  返した 4 件のうち、**runbook の `IZANAGI_EXPLORATION_OUTPUT_ROOT` が指す「exploration campaign」と
  D1813 の「探索」が別語である件の整理だけ**を実施する。B-10 job 本体への working bytes 拘束の
  追加 (D1658 が同じ面を裁定済み) と、既存の正式 consumer への `run_kind == "extended"` 必須化
  (正式 consumer の受理集合を動かす) は**採らない**。正値 `BACKOFF_FIXED` の pointwise meaning
  witness については、D1879 の提示後に D1859 が production 経路で確立したため、同項の
  「見送り」は適用しない。D1859 を全経路の保証へ広げてはならない。
  base: 025334aba94ce2ba712e0d3ed744f891a76df9852b16cb3e3c8f7ff9f51cb54a

- [T-2502] **P2・裁定済み (D1878) → 実装手番**: driver の `--run-iteration` について、
  `--knowledge-manifest` の `sources` が**非空のときだけ** `--coder-role` を必須にする。
  空取得 (`completed_empty` / `sources: []`) の経路は現状のまま通す。無条件の相互必須化は
  既存正例 `test_main_manifest_only_accepts_legacy_flattened_proposal` を壊すため却下された。
  Pegasus の production 経路は [T-2182] の job body 側で既に閉じており、残るのは driver 直接
  起動の経路だけである。**空取得経路の維持は、非空経路の修正が済んだという意味ではない。**
  着地は未確認。
  base: ba24eb4eb09f1887044b437ab9cba1709d21b6b2576c9f34ac2788fb7474730c

- [T-2504] **P2・裁定済み (D1877 → D1936 項 43 で限定変更) → 実装着地済み ([T-2579])**:
  `orchestrator/tests/test_t1259_qsub_env_delivery_probe.py` の setup が使う
  `git ls-files --others --exclude-standard -z` の 30 秒 timeout が並行 wave 2 本以上で落ちる件は、
  D1877 が「混雑時の実所要に見合う値へ上げる。fixture の共有範囲は変えない」と裁定したのち、
  **D1936 項 43 が当該 fixture の共有範囲と解消方法を限定変更した** — 実 repo 走査を module ごと
  1 回へ減らして各 test へ独立 copy を渡し、**production timeout と走査範囲は維持する**。
  この形の実装は [T-2579] が現行 main へ限定回収し、正負検査・独立レビュー・変異検査まで
  完了している。よって現行の手番は「timeout を上げる」ではない。
  base: 5ce68f33775b2b969f14942209f86a27b3226e629213c59b79e34fef6a69064f

- [T-2506] **P2・裁定済み (D1876) → 明記手番**: published group receipt の再受理検査を
  **exact 化しない**。現状 (`certified_requests` だけを見て件数・claim limitations・未認証
  marker・各 row の状態・`trace_dir` を確認せずに削除へ渡す) を維持し、保証しない範囲として
  明記する。実害の観測が無く、同型の D1656 が「直さず非保証として明記」で決着している。
  「仮想リスク向けの gate 追加は scope 外」というユーザー指示に当たる。**保証が完成したという
  意味ではない。**
  base: c176aa5422278c735591fab1835286268c333757d2b45fdbec33bdfd726d5301

- [T-2621] **P1・裁定済み (D1996) → 実装手番**: land の共通 lock 待ち窓を lock 外の provenance
  監査が食い潰す構造 (F975) は、D1996 が `tools/dev_wave_land.py` の `_LAND_LOCK_WAIT_SECONDS` の
  意味を「窓開始からの絶対期限」から**累積の競合待機予算**へ変えると裁定した。
  `_run_outside_land_lock` は guard (全史 provenance 監査 / fold gate) の完了後に残予算から
  自前の deadline を作って再取得し、監査後と fold gate 後の両方の再取得に適用する。
  **値 180 秒は据え置き、取得ごとに 180 秒を補充する禁止も維持する。** D432 の「取得点ごとに
  同じ絶対 deadline を渡す」条項は本決定が supersede する。監査の範囲・内容・`--range`・
  `authoritative` 述語は変えない。reason 文の書き分けも同じ変更単位で直す。着地は未確認。
  base: 09f9e72c91612b8a875c7b91d0be793c687e90906d05525fb95ae51ce9d0056a

- [T-2633] **P1・裁定済み (D1986 項 4) → 残件なし**: D1936 項 8 の「適格な少数の赤 precursor を
  使う」と §5.1.1 の選択関数 (適格行が n 未満なら `design_not_feasible` として実走しない)・
  D1880 の 201 行契約の関係は、D1986 項 4 が決めた — **適格な行が必要数に満たない間は実施不可の
  まま走らせない。選択関数と母集合の契約は変えない。少数の赤 precursor に対して許されるのは
  記述としての報告までで、実験の実施と有意差の主張は起こさない。** 必要数を下げる案は D1936
  項 8 の「固定 201 だけの無言の削減」に、供給を増やす基盤を作る案は同項の「母集合を作るための
  追加基盤」に当たり、どちらも不採用済みである。
  base: d449c14b0017a6381a307ae2bac70a724dc1a0e3bd5e27507f4a0f99bd7a95ac

### 新規

- {{T:d1984-reason-contradicts-d1872}} **P2・新規・ユーザー裁定待ち**: `docs/decisions.md` の
  D1984 却下欄が「**未配線 2 群のどちらかを期待値として固定する** — 二読 fallback の択一は
  未裁定であり、片方を機械的な期待値にすると変更コストの非対称が生まれる」と書いているが、
  同じ択一は D1872 (2026-09-09) が exact 必須で裁定済みである (D1831 が「実装せず裁定へ返す」と
  した択一への回答)。D1984 の決定主文は caller メタテストの不採用と「未配線 2 群の扱いも
  変えない」であって D1872 の撤回ではないため、現行の効力は D1872 にあると読める。
  台帳側の状態記述の誤りであり、過去の判定は追記でのみ訂正する対象なので AI が既成事実に
  しない。裁定すべき点は (a) D1984 の却下理由を追記で訂正するか、(b) 誤記として記録だけ残すか。
  **[T-2599] が worklog 側で見つけたのと同型の欠陥が decisions 側にもある**という一般的な
  含意は、独立 2 例が揃うまで主張しない (DW-G03)。
