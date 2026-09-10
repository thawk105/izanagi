# 段 4 裁定 — [T-1946] + [T-2107] 試行台帳の配線と proof chain 束縛

親裁定。base `2bf9cf387`(着手時 local main。走査時点の main は `1d2706f9`)。
材料 = 段 2 plan 1 本、段 3 敵対検査 2 本 (レンズ A / レンズ B)、親の独立実測 (`parent-findings.md`)。

## 結論 — 段 1 brief を差し替え、段 2 から再実行する (実装は続行する)

**実装しないという裁定ではない。** 入口の読み込み契約が定める巻き戻しを適用し、
brief を差し替えて段 2・3 をやり直したうえで実装へ進む。理由は次の 3 つ。

1. **brief の実測 3 件が誤りだった** (既存台帳 0 件、編集面 8 file、稼働 wave 重なり 0 件)。
   誤った前提の上に立つ plan と裁定は流用できない。
2. **scope が 2 task ではなく 3 task だった。** 配線 (T-2107) は T-1851 の前半と同一の作業であり、
   T-1851 は裁定済み・実装待ちである。これを brief に書かずに実装子へ渡すことはできない。
3. **plan 自身と両レンズが独立に「現 brief のまま実装を開始してはならない」と判定した。**
   3 者の一致を親の判断で覆さない。

巻き戻し後の brief は本裁定が確定した内容 (下記) を与件として含める。段 2・3 の成果物は
`verbatim/` へ保全し、次の plan の入力にする (同じ調査をやり直させないため)。

---

## 親 brief の訂正 (誤りは親のもの)

| # | brief の記述 | 実測 | 訂正 |
|---|---|---|---|
| C1 | 「既存台帳は repo 内 0 件」(P1-e) | 台帳の実保存先は worktree 内でなく Git common dir 配下の共有 admission root。そこに 193 行の `registry.jsonl` と 96 行の `consumption-catalog.jsonl` が実在する (2026-08-27 19:53、以後不変) | **refuted。** 共有 root を正本として再 inventory する。凍結 hash `db07b575…` は本番の `315b1eb8…` ではなく合成値なので本番消費者は無いが、「移行不要」は根拠を失う |
| C2 | 「編集面は 8 file」 | 一意な production file は 9。実際の必須面は production 11 + test/support 13 | **refuted。** 数え直す |
| C3 | 「稼働 wave と重なり 0 件」 | exact path 集合 + staged + untracked で再走査したところ 3 件。`worktree-dev-wave-t2027-root-class2` が `s8b_floor_campaign.py` (6 行追加)、`worktree-dev-wave-t2074-a1-estimand-realign` と `impl-dev-wave-t2074-fix2` が `test_s8b_floor_campaign.py` | **refuted。** 証跡 = `overlap-scan.txt` (走査時刻・main head・各 worktree の head/base/変更数つき) |
| C4 | DW-G05 「certified 成果物を発行し続ける」 | official mode は core で無条件拒否 (`s8b_floor_campaign.py:453-463`)。稼働可能なのは pilot だけ | **過剰一般化。** 影響範囲を「pilot の材料レポートと、休眠中の official / certification 経路」に限定する |
| C5 | (P1-c) 配線は campaign 側に新しい token 所有を持ち込まず閉じる | 不足入力が 6 件 | **refuted** (B-2、plan の実測表) |
| C6 | (P1-d) 4 sub-feature を 1 wave で land できる規模 | 23-24 path、静的 fanout 164+ test node、既存 span だけで 772 行 | **refuted** (A、B 一致) |
| C7 | (P1-b) 横断 replay は既存 replay を広げるだけ | filesystem 世代集合の権威、directory shape 検査、二回 replay が要る | **半分だけ成立** |
| C8 | (P1-a) 世代識別子は `protocol_sha256` で足りる | raw bytes と canonical bytes が一致し binding field に実在 | **成立** (A、B 一致) |

---

## scope の確定 — 本件は 3 task の閉包である

- **T-1851 (裁定済み・実装待ち) が配線の前提である。** その段 4
  (`output/insights/2026-08-27_t1851-floor-retry-ordinal-axis/s4-adjudication.md`) が
  次 wave へ渡した骨格の**前半**が本件の配線そのものである。逐語:
  「前半 = legacy 統計的測り直しの縦切り 1 本。schema v2 + readable 方針、sealed な理由 authority、
  terminal 理由の再導出、二台帳の crash 整合、launcher / campaign 配線、final inspector / verifier
  までを同時に land する。」後半 (`verified-registry-recovery` 側) は別 wave と明記されている。
- **D1032 (ユーザー裁定)** が測り直しの軸の形を確定済み。「事前登録した別の試行番号軸を同じ耐久台帳の
  中に置き、性能量に到達する前に理由を固定する。受理する理由の集合を広げる場合も外部 scheduler の
  証拠が付いた場合に限る」。
- T-1851 段 4 の (P1) 読み — 「理由が sealed な session record から機械的に導出されるなら
  『受理する理由の集合を広げる』に当たらない (自由選択が存在しないため)」— は
  2026-08-27 /rulings で**推奨どおり承認済み**である。所見 11 の
  「凍結 4 語を再利用せず台帳専用の閉じた語彙を持つ」も同様。
- **D880** は retry trigger の排他二択を定め、回復権限 pin を意図的に空にし、
  「registry の空 `retryable_failure_reasons` との不整合は既知で、別裁定へ回す。
  本 wave はその不整合を増やさない」と書いている。本 wave は D880 の回復側 pin を**変更しない**。

したがって本件の land 単位は **T-1851 前半 + T-2107 + T-1946** であり、D1341 と
T-1851 段 4 の「書き手と検査を別々に land する分割は不可」の両方がこれを 1 commit に束ねる。

---

## 所見の real / refuted と採否

### レンズ A

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A-1 | classification claim path が世代化されておらず第 2 世代が衝突する | **real / blocker** | 採用。claim の address と payload を binding 全体で世代化する |
| A-2 | pre-probe 競合経路が launcher と台帳を完全に迂回する | **real / blocker** | 採用。B-1 と同一。下記「親裁定 2」 |
| A-3 | 正の `row_count` は genesis-only や別 campaign の台帳を正例にできる | **real / blocker** | 採用。B-1 と同一。下記「親裁定 1」 |
| A-4 | registry terminal と journal の間に未設計の crash cut がある | **real / blocker** | 採用。二相 write と再開時 reconciliation を plan v2 の必須項目にする。T-1851 段 4 の「二台帳の crash 整合」と同一項目 |
| A-5 | 「既存台帳 0 件」は live shared root で反証され、列挙案が既存 freeze を閉塞する | **real / blocker** | 採用。C1 のとおり親の誤り。列挙は 64 hex directory だけを世代とみなし、既存 bytes を削除・書換えせず sibling file を明示的に無視する |
| A-6 | 横断 replay は単一 profile では旧世代を replay できない | **real / blocker** | 採用。各世代の genesis から profile を解決して replay し、budget accumulator だけを合成する |
| A-7 | M8 の変異帰属が後段 proof 比較と重複する | **real** | 採用。proof validator の直接 unit test へ再照準する (DW-M01) |
| A-8 | v4 受理テストとした既存 node は実際には v3 拒否テスト | **real / nit** | 採用。v3 拒否 node は維持し、v4 正例は別に追加する |
| A-9 | 「稼働 wave 0 件」は独立検証できない | **real** | 採用。C3 のとおり再走査し証跡を固定した |

### レンズ B

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| B-1 | S3 が全 session を台帳へ到達させず、S4 に被覆検査もない | **real / blocker** | 採用。A-2 + A-3 と同一。親裁定 1・2 |
| B-2 | 発火対象は実在するが S3 の必須入力は構築不能 | **real / blocker** | 採用。下記「不足入力の裁定」で 6 件すべてに解を与える |
| B-3 | prefix inspector が N 行以後の壊れた tail を恒真化する | **real / blocker** | 採用。下記「親裁定 3」 |
| B-4 | 旧 path 不在の根拠が production 保存先を見ていない | **real / blocker** | 採用。A-5 と同一 |
| B-5 | candidate の earlier-result 選択層が v5 proof を発火させない | **real / blocker** | 採用・**scope 内**。D1342 の射程外は最終 8c 発行層であり、`_official_earlier_floor_results` / `_derive_floor_selection_eligibility` は g1 candidate 選択層である。親が現物で確認した (`s8b_holdout_freeze.py:1813-1840` が earlier `result.json` を読む) |
| B-6 | file 所有は素集合だが依存順と規模の主張が成立しない | **real / blocker** | 採用。C6。単位 C と D は相互依存なので、独立緑を前提にした並行分割を採らない |
| B-7 | file:line と既存 test 説明に具体的な誤りがある | **real / nit** | 採用。`append_production_emitter_g2()`、v3/v4 の理由、public/private caller 数、production file 数を訂正する |
| B-8 | 親 brief の provisional 判定と DW-G05 が一部 refuted | **real** | 採用。C4〜C8 |
| B-9 | 45 worktree の重なり 0 件は再現不能 | **real / blocker** | 採用。C3 |

**refuted と裁定した所見はない。** 両レンズの所見はすべて real である。

---

## 親裁定 (plan v2 の与件。ユーザーが覆せる)

### 親裁定 1 — v5 proof に「試行の被覆」を加える

D1337 が確定した `{row_count=N, chain_head_at_N}` の prefix 証明は**維持する**。
そのうえで、**その result 自身の全 attempt が台帳の lifecycle 行に対応することの検査を加える。**

- 根拠: D1194 の目的は「台帳の欠落を許したまま追跡を謳う状態を作らない」である。
  A-3 と B-1 が独立に、`{N, head}` だけなら genesis 1 行の台帳でも別 campaign の台帳でも
  通ることを示した。これは D1194 が却下した恒真な保証そのものである。
- D1337 は identity の**形**を定めた裁定であり、「proof はこれだけでよい」とは述べていない。
  したがって被覆の追加は D1337 の変更ではなく D1194 の実装である。
- 規律 2 の面: producer から registry 書き込みを落とした変異が、この検査なしでは緑になる。
- **仮想リスク向けの追加ではない。** 追加しなければ機構が発火しないことを、独立 2 検査が示している。
- **ユーザーが覆せる項目として裁定パッケージに載せる。**

### 親裁定 2 — 計測前に除外された試行も台帳へ残す

campaign の pre-probe 競合による早期終了経路も、計測を開始せずに reserve → terminalize する
launcher 所有の経路を通す。campaign が probe 結果を launcher へ渡して分類させる形は
**採らない** (候補が自分の信頼の根を名乗る形になる。D880 が同じ理由で却下した形と同型)。

### 親裁定 3 — live 台帳は全体を replay し、比較は先頭 N 行だけ

D1337 の「現 tail との完全一致を要求しない」を守りつつ、B-3 の恒真化を塞ぐ。
shared lock 下で live registry を**全行 replay** し、`len(rows) >= N` と
`rows[N-1].event_sha256 == 記録 head` だけを proof と比較する。
N 行以後が壊れていれば replay が落ちるので受理しない。正当な append は受理する。

### 親裁定 4 — 不足入力 6 件の解 (B-2)

| 不足 | 裁定 |
|---|---|
| classification authority | launcher 自身の出力前分類方針を名指しする production 定数を新設し、policy digest は `s8b_scheduler_accounting.py` の `AUTHORITY_POLICY_BYTES` → `AUTHORITY_POLICY_SHA256` と**同じ形**で方針 bytes から導出する。test literal を昇格させない。**新しい信頼の根にあたるのでユーザーが覆せる項目として裁定パッケージに載せる** |
| recovery authority (profile 構築用) | `s8b_scheduler_accounting.AUTHORITY_ID` / `AUTHORITY_POLICY_SHA256` を渡す。**admission の pin 集合 (`_FLOOR_RECOVERY_AUTHORITIES`) は空のまま変更しない** (D880)。回復経路は fail-closed のまま。不整合を増やさない |
| run-start receipt digest | campaign が既に fsync している session-start bytes の digest を返す形にする。新しい成果物を作らない |
| admission claim digest | private `_CellState.measurement_generation_claim_digest` を公開 `CellHoldoutAdmission` へ射影する。値の導出は変えない |
| retry ordinal 軸 | D1032 + T-1851 段 4 の承認済み (P1) 読みに従う。台帳専用の閉じた理由語彙を持ち、各値を sealed な session record から**機械的に導出**する。呼び手が理由を選べる形にしない。`S8B_RETRYABLE_FAILURE_REASONS` はこの導出経路の下でのみ非空になる |
| consumption marker の path 不一致 | admission 所有の exact validator を通し、adapter は検証済み marker だけを受ける。legacy marker の既存 test 面は維持する |

### 親裁定 5 — 実装単位

plan の A/B/C/D を採るが、**C と D の独立緑を前提にしない** (B-6)。
4 単位を unlanded workstream として順に統合し、統合後に一度だけ commit・land する。
checkpoint = (1) authority/ordinal の実体化、(2) 全 suite 更新、(3) 変異確認。

### 親裁定 6 — 共有 root の既存 bytes に触れない

`.git/izanagi/s8b-holdout-admission-v1/` 配下の既存 193 行台帳と consumption catalog は
**削除も書換えもしない**。世代列挙は 64 hex の directory だけを世代とみなし、
freeze 直下の sibling file は明示的に無視する。既存 bytes を読める必要はない
(凍結 hash が本番値でないため本番消費者が無い)。

---

## 変異事前登録 (DW-M01) — 段 5 実装前に plan v2 で確定する

本裁定時点では登録しない。理由: plan v2 で実装位置が変わるため、いま登録すると anchor が
確実に外れる。plan v2 の確定と同時に、次の 3 点を満たす形で登録する。

- 各変異について、同じ入力を拒否する層が前後に無いことをコードで確認する (A-7 の型を避ける)。
- 親裁定 1 (被覆) と親裁定 2 (pre-probe) に対応する変異を必ず含める。
  これらは「機構が発火するか」を直接測る位置である。
- 束縛の負例と、台帳部品検査の負例を別枠にする (前 wave 継承 must-fix 8)。

---

## ユーザーへ返す裁定パッケージ (実装を止めるものではない)

次の 2 件は親が裁定して実装へ進むが、ユーザーが覆せる。

1. **親裁定 1 (proof に試行の被覆を加える)。** D1337 が定めた proof の形に、
   「その result の全 attempt が台帳に対応する」検査を足す。足さないと機構が恒真になることを
   独立 2 検査が示した。足すことは D1337 の変更ではなく D1194 の実装だと親は読んでいる。
2. **親裁定 4 の classification authority (新しい信頼の根)。** launcher の出力前分類方針を
   名指しする production 定数を新設する。既存の scheduler accounting authority と同じ形で
   方針 bytes から digest を導出する。

覆す場合は、1 なら「恒真な束縛のまま land してよいか」、2 なら「別の権限の置き場所」を示す必要がある。
