---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: rulings-selfimprove-20260907c
seq: 3
---

## {{D:acceptance-collection-scoping-stays-forbidden}}. 受入 collection の自 shard 絞り込みは採らず、D711 の禁止を維持する

**決定 (ユーザー裁定、2026-09-07 /rulings 全件 第 13 回、推奨どおり):** 各 shard が同一の全 collection を
行ってから担当外を deselect する D711 の規則を**維持する**。自 shard の file へ絞る変更は採らない。
gate 2 (全 shard の `observed_universe` 一致) は現行のまま置き、代替述語も新設しない。
shard あたり約 55 秒は当面の固定費として受け入れる。

**理由:**

- 起草時の /rulings は「絞り込みを採り、gate 2 の代替として各 shard の collect 集合が割付と exact 一致
  することを新設する」を推奨していた。**別系統モデルの相談 (A) がこれに反対し、親が実装で裏を取った。**
  各 shard は自分のローカルな collection 結果から割付を導くので、その一致は**同じ縮小集合による
  自己証明**になる。独立な全体集合から導いた期待割付を供給しない限り gate 2 と同等ではない。
- gate 2 が断つ経路は「collection plugin が file を 1 件落としても全員が同じ縮小集合に同意して緑になる」
  である。自己証明で置き換えるとこの経路が開く。正しさ防壁を弱める側の変更にあたる (絶対規律 2)。
- D1707 が記録した費用前提の失効 (12.86 秒 → 約 59 秒) は事実として残るが、**費用は正しさ防壁を
  弱める理由にならない。**
- ユーザーが同じ裁定で「過剰実装・過剰ガードレールは無し」と付言した。独立な期待割付の供給機構は
  新設にあたり、この付言と逆向きである。

**却下した選択肢:**

- 絞り込みを採り割付一致検査を代替に置く (起草時の親推奨) — 自己証明であり gate 2 と同等でない。
- gate を保ったまま collection を速くする別案を探す — 探索先が示されていない。本裁定では起票しない。

**再訪条件:** 受入 wall が再び実害として観測され、かつ**独立な全体集合から導いた期待割付を供給する
設計**が具体的に示されたとき。費用の増加だけでは再訪しない。

## {{D:acceptance-observation-fields-deferred}}. 受入 report の観測 field 追加は見送り、内訳の確定は計装なしで済ませる

**決定 (ユーザー裁定、2026-09-07 /rulings 全件 第 13 回、推奨どおり):** D1647 が定めた観測 field の
拡張 (両端の時刻追加、lock の累計待ちへの定義変更) は**行わない**。closed schema は v1 のまま置き、
v2 への移行も追跡下 v1 consumer の張り替えも行わない。

**理由:**

- D1706 が既に残差を「worker 起動・collection・`pytest_runtest_protocol` wrapper の lock 待ち・
  scheduler gap・finalization の混合」と分解しており、collection の寄与は独立 3 者の実測で
  **計装なしに述べられている。**
- 同じ裁定回で受入 collection の絞り込みが採られなかった ({{D:acceptance-collection-scoping-stays-forbidden}})
  ため、内訳を確定しても次の一手は変わらない。
- 相談 (A) は、索引 1 の裁定が実験結果でなく事前に列挙された方針選択である以上、これに条件を
  つけることは**絶対規律 3 の結果先読みには当たらない**と判定した。親もこれを採る。
- schema v1→v2 は追跡下 consumer の張り替えを伴い、得られるのは診断の細分だけである。
  「過剰実装は無し」の付言に照らして採らない。

**却下した選択肢:**

- 両端の時刻を足す / lock の定義を累計待ちへ変える — 上記のとおり次の一手を変えない。
- 索引 1 の裁定を待って再訪する条件付き見送り (起草時の形) — 索引 1 が同じ回で裁定されたため、
  条件が成立と同時に発火する形になり意味を持たない。下記の再訪条件へ置き換えた。

**再訪条件:** 受入 wall が再び実害として観測され、かつ**内訳の確定なしには次の一手が決まらない**
ことを示せたとき。

## {{D:formal-consumer-terminal-outer-shape-closes}}. 8c formal consumer の terminal record の外枠を exact gate で閉じる

**決定 (ユーザー裁定、2026-09-07 /rulings 全件 第 13 回、推奨どおり):** D1715 がユーザー裁定へ返した
terminal record の外枠 (key 集合・値の型・重複・root shadow) を、**D1665 が trigger 側 (FC05C) へ入れたのと
同じ形の exact gate で閉じる。** FC07 の受理集合はこの 1 点だけ狭まる。他の gate・reason code・
判定式は変えない。

**理由:**

- 変異 B-057-M5 (`terminal.get("stage")` を `_wal_field(terminal, "stage")` へ緩める) が焦点走 11 file で
  **生存した。**外枠が pin されていないことは実測済みの実在欠陥である。
- 同一 consumer の姉妹検査 (FC05C) に既に同型の gate がある。**新機構ではなく既存機構の対称な適用**で、
  過剰ガードレールには当たらない。相談 (A) も、canonical-list 経路では `wal.parse_line()` の外枠検査を
  通らず root shadow が実際に FC07 を通ることを確かめて同意した。
- 塞ぐのは「fixture 由来の形が本番へ紛れ込む」経路であり、絶対規律 2 の面に直接効く。

**却下した選択肢:**

- 閉じない (現状維持) — 生存変異が示した穴を開けたまま残す。
- 外枠検査を独立の新しい検査層として足す — 姉妹検査と同型に収めるので新層は要らない。

**限界:** consumer は全検査通過後も `P6Unavailable` を返すため、**certified 選択集合は本決定では
変わらない。**変わるのは report の reason と receipt / evidence-root 参照だけである。
rejected 側の projection が FC07 で止まる件 (D1715 の限界節) も本決定は解消しない。

## {{D:d906-effective-layer-is-separate-os-principal}}. D906 の実効層は別 OS principal とし、実施はユーザー手番とする

**決定 (ユーザー裁定、2026-09-07 /rulings 全件 第 13 回、推奨どおり):** 署名鍵と発行権限を AI から
分離する実効層として、**別 OS principal を採る。**別 host と hardware signer は採らない。
配置と権限設定は D1436 に従い**ユーザーの手番**であり、AI は代行せず代行案も作らない。
閉じるまでの間、着地受領証を根拠にした正しさ主張は D1197 のとおり**未閉鎖と明記**する。

**理由:**

- 起草時の /rulings は「いずれも作らず、現行の書込み面縮小を上限として保証限界に明記する」を
  推奨していた。**別系統モデルの相談 (A) が、D1197 の却下欄が「限界の明記だけで足りるとする」を
  逐語で退けていることを指摘し、親が現物で裏を取った。**起草時の推奨は既裁定の実効を奪うもので
  あり採れない。
- D1197 の決定節は「署名鍵と発行権限を候補および AI が書ける領域の外に置く外部署名主体を実装する」
  である。**別 OS principal は 3 択のうち最小**で、既存の鍵配置 (2026-09-05、worklog 1278) と
  発行主体 subtree の防護 (D1718) の続きに置ける。新しい運用基盤を建てない。
- 別 host と hardware signer は計算環境の管理権限を要し、主目的 (CC 自動合成) の主経路から遠い。
  「過剰実装は無し」の付言に照らして採らない。
- D1674 (evidence writer の権限分離は作らない) は**別対象**であり、本対象固有の後発裁定 (D1197) を
  上書きしない。相談 (A) の指摘どおりである。

**却下した選択肢:**

- いずれも作らず限界の明記だけで足りるとする (起草時の親推奨) — D1197 が逐語で却下済み。
- 別 host / hardware signer — 最小でなく、主経路から遠い。

**限界:** 別 OS principal でも、同一 UID で動く主体を前提としない攻撃者像には届かない。
D387 / D1128 の「検証器と被検証対象を同じ主体が変更できる限り完全な防壁にならない」は残る。

## {{D:a1-group-receipt-publishes-via-os-link}}. A-1 の group submission receipt の公開は `os.link()` で行う

**決定 (ユーザー裁定、2026-09-07 /rulings 全件 第 13 回、推奨どおり):** A-1 driver の group submission
receipt の公開を **`os.link()` による hard link** へ改める。素の rename への退避と `O_EXCL` の直接
書込みは採らない。`complete` の completion receipt 公開と materialize 側も同族として同じ形へ棚卸しする。
実装は Codex `role=author` が持ち、正例・負例を同じ commit へ入れる。

**理由:**

- attempt-0002 は 3 job とも body preflight を通ったが、group receipt の公開だけが Lustre 上で
  `Invalid argument` で決定的に失敗し (F870)、bench・build・verify が 1 つも走らなかった。
  **pilot の測定値は 1 点も無い。**
- `os.link()` は既存先に `EEXIST` を返すので、**create-only の排他性を落とさない。**素の rename は
  既存先を黙って上書きし、`O_EXCL` の直接書込みは部分公開の窓を作る。相談 (A) も同一 Lustre
  directory の実測で同じ結論に達した。
- 完成済み staging file への hard link は、公開の原子性を保つ既存の作法であり新機構ではない。

**却下した選択肢:**

- 素の rename — 既存先を黙って上書きし排他性を落とす。
- `O_EXCL` で直接書く — 部分公開の窓が開く。

## {{D:driver-gate-supply-limited-to-screening}}. 条件関門への FetchContent base 供給は screening 関門 1 箇所だけに入れる

**決定 (ユーザー裁定、2026-09-07 /rulings 全件 第 13 回、推奨どおり):** `backoff_sweep` の screening 段の
関門 (`screening_driver._run_condition_gate_for_genome`) にだけ、D1666 が driver 段へ入れたのと同じ
FetchContent base の供給を入れる。**`backoff_repro` と `s1_direct_comparison` には入れない。**
pin の整合と freeze の再生成も本裁定では行わない。

**理由:**

- 起草時の /rulings は赤 3 箇所すべてを D1666 の「実測経路になった時点」に当たると扱っていた。
  **別系統モデルの相談 (A) が反対し、一次資料
  (`output/insights/2026-09-07_t2228-driver-gate-liveness/README.md` 1.3 節) 自身が
  「現状のまま `backoff_repro` を起動すると、関門に触れる前に止まる」と書いていることを親が確かめた。**
  測られた赤は歴史 pin `dff0f1e` の木で得たものである。同 insight の限界節も
  「`backoff_repro` と s1 については CLI 入口から関門までの到達性は測っていない」と明記している。
- `s1_direct_comparison` は `load_verified_freeze` で停止し、凍結入力に inert cell が 1 件も無いため
  **inert 経路は production では構築されない。**
- したがって D1666 の条件 (「実測経路になった時点」) を満たしたのは screening 関門だけである。
  残り 2 箇所へ同時に入れるのは、発火経路の無い条件付き機能を main へ入れることになる (`DW-G04`)。
- screening への供給は D1666 と同型の水平展開であり、関門を緩めない。関門を通すために preprocess を
  skip する案は D1666 が既に却下している。

**却下した選択肢:**

- 3 箇所すべてへ入れる (起草時の親推奨) — 2 箇所は正規入口から関門へ到達しない。
- pin の整合 / freeze の再生成 — 名指し外で、到達性が未測のまま前提を動かす。
- 直さず未充足として明記する — screening は実測で到達しており、直せる赤を残す理由がない。

**再訪条件:** `backoff_repro` または `s1_direct_comparison` が**現行の正規入口から関門へ到達した**
ことを実測で示せたとき。到達性の実測なしに供給を足さない。

## {{D:prebuilt-receipt-nonconsumption-stays}}. terminal variant で事前構築 receipt が消費されない挙動は現状維持とする

**決定 (ユーザー裁定、2026-09-07 /rulings 全件 第 13 回、推奨どおり):** 既に terminal な variant を
`run_campaign` が `evaluate` より前に skip し、事前構築 receipt が 1 度も消費されない現行挙動を
**維持する。** campaign identity へ receipt transport を足す案と duplicate の意味論を変える案は
いずれも採らない。現行挙動の test pin と `tools/pegasus/README.md` 7 節の運用注記で閉じる。

**理由:**

- どちらの案も受理集合か campaign identity を動かす。既裁定が「再測定は fresh campaign identity で
  行い、同一 identity の復旧専用機構は新設しない」としている向きに正面から反する。
- 実害は「同じ REPO_ROOT へ同じ fixture 値で 2 度目を投入したとき、事前構築が無駄になる」という
  運用上の非効率に留まる。**正しさ側の性質には触れない。**
- 現行挙動は既に test で pin され、運用注記もある。相談 (A) も同意した。
- 「過剰実装は無し」の付言に照らし、identity を動かす費用は実害に見合わない。

**却下した選択肢:**

- campaign identity へ receipt transport を足す — identity を動かす。
- duplicate の意味論を変える — 受理集合を動かす。

## {{D:unit-c-two-rulings-decided-ahead-of-land}}. 単位 C1b を塞いでいる 2 件を land 前に裁定する

**決定 (ユーザー裁定、2026-09-07 /rulings 全件 第 13 回、推奨どおり):** D1703 が定めた
「単位 C が揃って land するまで個別に裁定しない」を**この 2 件については見直し、先に裁定する。**

1. **core の等値検査と台帳専用 4 語の衝突** — 「観測前に分類された理由」と「観測後に導出された理由」を
   **別軸として契約へ追記する。** v2 の transition policy 自体は変えない。
2. **`exec_failures` の出所** — **契約側を campaign の現行算出に合わせる。** campaign 側の算出を
   私有 sink 由来へ変える案は採らない。

D1703 が挙げた残り 2 件 (封印の信頼境界、C1b を縦 1 単位で実装するか) と、項 4・項 5 の持ち越し群は
**D1703 のまま単位 C が揃って land するまで待つ。**

**理由:**

- D1703 の理由の柱は「現時点で C1b の brief はこれらのいずれも前提にしていない (実測で確認)。
  したがって待っても進行中の作業は塞がらない」だった。**その後 C1b が実装 0 行で終わり、
  未 land fragment は「裁定が決まるまで実装子を起動しない」と明記している。前提が実測で反証された。**
  /rulings の作法 6 (未成立で後続が塞がるなら条件見直しを立てる) に従う。
- 項 1 で 2 軸へ分ける形は、v2 の transition policy を変えるより**射程が狭い。**契約への追記で閉じる。
- 項 2 で契約側を合わせる形を採るのは、campaign 側の算出を変えると**計測の意味論が変わり**、
  既測値との比較可能性を落とすためである (絶対規律 7 の面)。
- 相談 (A) は「AI が裁定を上書きするのでなく、変化した前提を示してユーザーへ再裁定を求めるもの」と
  判定して同意した。本決定はそのユーザー再裁定である。

**却下した選択肢:**

- D1703 のまま 4 件すべてを待つ — C1b が塞がったままになる。
- 4 件すべてを今裁定する — 残り 2 件は稼働中の実装で前提が動く。D1703 の理由がなお成立する。
- v2 の transition policy 自体を変える / campaign 側の算出を私有 sink 由来へ変える — 射程が広く、
  後者は計測の意味論を変える。

**注:** 本項は稼働 wave (`dev-wave t-1851 unit-c inheritance`) が所有している。第 11 回・第 12 回の
先例に従い、/rulings 側は worklog の項本文を書き換えない。所有 wave が着地時に整理する。

## {{D:rulings-13-implementation-scope-rider}}. 第 13 回の裁定の実装は最小形に限り、名指し外の gate・検査・台帳を足さない

**決定 (ユーザー裁定、2026-09-07 /rulings 全件 第 13 回):** 本回の裁定を実装する wave は、
各決定が名指しした変更だけを行う。**名指し外の gate・validator・検査・台帳・一般化は scope 外**で
あり、必要と判明した場合も同じ wave では実装せず裁定パッケージへ送る。

**理由:**

- ユーザーが裁定と同じ発話で「過剰実装・過剰ガードレールは無しで」と付言した。
- 本回は起草時の推奨 3 件が相談で覆っており (索引 1・4・6)、いずれも**射程を広げる側の案が
  退けられた**。実装段で射程が戻る経路を塞ぐ。
- 2026-08-12 のユーザー方針 (研究最優先・プロトタイプ基準、防御的堅牢化と bytes 級 provenance は
  既定で見送り) と同じ向きである。

**却下した選択肢:**

- 付言を各決定の本文にだけ書く — 実装 wave が決定を 1 つずつ読む運用では横断の制約が落ちる。
