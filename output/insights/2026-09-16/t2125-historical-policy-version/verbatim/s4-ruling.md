# [T-2125] 段 4 裁定とプラン v2

親が段 3 の 2 レンズを裁定し、実装範囲を確定する。`s2-plan.md` はこの文書で上書きされる。
裁定 inbox 再走査: wave 開始 (d97c423bd) 以降 local main は 0 commit。新しい裁定は無い。

## R1. DW-G04 は満たしていない。それを明記したうえで実装する。

**レンズ B 所見 1 は real。** 提示できる証拠は次の 2 つまでである。

- **発火事象の計測 ID**: `fb5e74a17` (2026-08-12)。`CURRENT_PIN` が `d706650` → `511c953` へ前進し、
  policy の版が実際に上がった。policy 照合の導入 (`a21bf413e`、2026-08-03) より後である。
- **不一致条件を満たす既存 artifact**: 2026-08-04 の evidence lock 2 件 (記録 `d706650`)。
  ただしこの 2 件は WAL 不在で、**より手前の別理由で落ちる**。

**現に停止している材料レポートは 0 件である。** 外部 official の v2 lock 20 件は
5 field すべてが現行 policy と一致する (`parent-corrections.md` C1 の再実測)。

**裁定:** `DW-G04` は親が自発的に足す条件付き機構を止める gate であり、本件は台帳 [T-2125] として
ユーザーが名指しで依頼した本題である。**gate を「満たした」とは書かない。満たしていない事実を
worklog と insight に明記したうえで実装する。** そのうえで `DW-G04` の趣旨 (仮想の機構を建てない) は
**R2 の scope 切り詰めで守る。**

## R2. 照合先の差し替えは 2 つだけにする (plan の 5 つから削る)

`s2-plan.md:69` の表は policy SHA / stock pin / generator registry / review registry /
coder authority の 5 つを記録側へ向けていた。**採用するのは前の 2 つだけ。**

| 比較 | 現行入口 | 歴史入口 (裁定) | 理由 |
|---|---|---|---|
| receipt の `policy_sha256` (`build_admission.py:687`) | 現行 policy の sha256 | **記録 policy の sha256** | 版上げのどの事象でも必ず差が出る。ここを直さないと何も解けない |
| stock class の source commit (`build_admission.py:709`) | `CURRENT_PIN` | **記録 `repo_stock_pin`** | 実測された唯一の版上げ事象 (pin 前進) で必ず落ちる |
| generator 登録 (`build_admission.py:548`) | 現行 `GeneratorId` | **現行のまま** | member 追加では通る。削除・改名は**未実測**の事象 |
| review 登録 (`build_admission.py:718`) | 現行 `ReviewId` | **現行のまま** | 同上 |
| coder authority (`build_admission.py:734`) | `_AUTHORITY_KIND` | **現行のまま** | literal 変更は**未実測**の事象 |

**この切り詰めはレンズ A 所見 1 への最良の応答でもある。** 記録側の registry と authority を
信じないので、偽造 policy が架空 generator / authority を名乗っても**現行の登録簿が拒否する**。
自己申告へ落ちるのは policy SHA と stock pin の 2 点に限定される。

**切り詰めが本題を解けることの確認 (実測 2 事象に対して):**

- pin 前進: 記録 preimage は `repo_stock_pin` だけが違う → policy sha が違う (1 番目で解消) +
  stock receipt の source commit が旧 pin (2 番目で解消)。generator / review / authority は
  変わらないので現行照合をそのまま通る。**通る。**
- registry への member 追加: 記録 preimage は registry 列が違う → policy sha が違う (1 番目で解消)。
  receipt が指す ID は現行 enum に残っているので現行照合を通る。**通る。**

**残余 (scope 外・R9 へ):** registry から member を削除・改名する、`_AUTHORITY_KIND` または
`POLICY_SCHEMA` の literal を変える、のいずれかが起きると歴史閲覧はまた塞がる。

## R3. 共有 helper 抽出の退行を負例で塞ぐ (レンズ A 所見 2 は real、採用)

現行入口と歴史入口が検査本体を共有する以上、**現行入口の比較対象が恒真化しても、
旧 policy の入口拒否テストと現行 policy の正例テストは両方緑のままになる。**

段 5 の必須要件とする。

- **現行 policy SHA を維持し、outer / 伝播 digest を整合させた不正 receipt** を現行入口へ渡し、
  (a) 旧 stock pin、(b) 未登録 generator ID、(c) 異なる authority kind が
  **それぞれの比較まで到達して**拒否されることを固定する。
- 「旧 policy だから入口で落ちた」拒否を検出成功に数えない (レンズ B 所見 8 と同じ理由)。

## R4. 識別子は classification に置く (plan どおり採用)

- `classification = "historical-policy-version"` を新設する。
- `admission_status` は既存の `historical-not-reclassified` を再利用する。**新 status literal を作らない。**
- `policy_sha256` には記録 policy の sha256 を入れる。
- **epoch は 1 byte も触らない** — `CampaignVerifierEpoch.__post_init__` の reason 値域、
  `HistoricalCampaignVerifierEpoch` の scope、nested object、`current-closure-unavailable` は不変 (D1365)。
- `layer3_schema.json:293` の classification enum に新値を足し、
  同 `:12` の `certifying_input=true` 側では従来 2 値に制限して**増やした受理形だけを相殺する**。
- **critic digest へは届かない** (レンズ B 所見 7)。追加配線はしない。射程を insight に書く。

## R5. 成果の説明を縮める (レンズ B 所見 2・3 は real)

**本 wave の完了範囲はこう書く。**

> 現行 grammar で decode でき、既存の構造検査を満たす v2 campaign について、
> **build admission policy の値差による拒否だけ**を歴史閲覧で解く。

- **`tools/plotting/plot_s1_9pair.py` の回復を成果に数えない。** 同 `:589` は epoch `E0` /
  `v1-authority-absent` を要求し、有効な v2 authority は `E1` になるので到達しない。
- **「図・材料レポートが全部通る」と書かない。** `layer3_report.py:112` の `_read_campaign_lock` は
  通常 decoder を使うため、旧 grammar の lock は report 投影で落ちる (主題は [T-2483])。
- 変わる consumer: `critic/digest.py` (p2_2 経路)、`critic/online_digest.py`、`p2_2_report.py`、
  `layer3_report.py` の admission 段、`b10_backoff_static_tail_formal.py` の exploration 読取、
  `replay.discover_*` の歴史 purpose 経路。
- 変わらない consumer: `s1_report.py` (policy admission を呼ばない)、
  `replay.load_landscape` (certified 固定)、`plot_s1_9pair.py` (上記)。

## R6. `wal.py:2767` の第 2 照合は変更しない

両レンズと親の独立実測が一致した。production の呼び手はすべて policy を明示的に渡す。
`loop.py:800` が plan の表から抜けていた (nit、記録のみ)。

## R7. 親の実測の訂正を確定する

`parent-corrections.md` の C1〜C3 をそのまま採る。要点だけ再掲する。

- M4 は全 preimage で測り直した。外部 20 件は 5 field すべて現行と一致 (`repo_stock_pin` だけの
  観測から一般化していた誤りを直した)。
- M2「版上げは 2 事象」→「preimage の 5 field のどれが変わっても版は上がる」。
- M10「実経路がある」→ status 条件は満たすが最終受理までは立証していない。
  **`layer3_report.py:966` と `autonomous_trial_completeness.py:4965` の再 admission は残す。**
- M9 は「本 wave の歴史 admission は `_replay` を通らない」までに縮める。
- M5 は「予定編集面どうしの比較」に限る。未 commit 編集面は測れていない。
- M1 の行番号は `:1368` / `:1370`。brief の「編集面は 1 module」は**撤回**する。
- **不変条件 4 の文言を C3 のとおり訂正する。** 形検査を真正性の保護と呼ばない。

## R8. 変異 #3 の欠落 key ケースを登録から外す (レンズ B 所見 8 は real)

exact key 検査を消しても、欠落 key は後続の field 参照・型検査で拒否されうる。
**単一理由性 (`DW-M01`、F820) を満たさない。** 余分 key と schema 違いを主判別例にする。

## R9. real だが scope 外 (裁定パッケージ候補)

1. registry からの member 削除・改名、`_AUTHORITY_KIND` / `POLICY_SCHEMA` literal の変更で
   歴史閲覧がまた塞がる残余 (R2 の切り詰めの代償)。
2. `layer3_report.py:112` の通常 decoder による旧 grammar 拒否 ([T-2483] と主題が重なる)。
3. critic digest の出力に admission classification が届かない。
4. **記録 policy の真正性を検証する手段が無い** — 歴史閲覧で成立するのは
   「記録 policy と記録 receipt の内的整合」までである (レンズ A 所見 1 の恒久的な限界)。
5. plan が挙げた「記録 policy に存在しなかった ID を通す逆方向の誤り」。
   これは受理を**狭める**追加検査であり、`DW-G05` により本 wave では足さない。

## R10. 確定した編集面

`orchestrator/campaign/artifact_admission.py`、`orchestrator/campaign/build_admission.py`、
`orchestrator/campaign/wal.py`、`orchestrator/campaign/layer3_schema.json`、
`orchestrator/tests/` の既存テスト。**新 module を作らない。新 test file を作らない。**

## 変異事前登録 (DW-M01 — 実装前に確定)

| # | 変異 | 赤になるべき検査 | 単一理由性 |
|---|---|---|---|
| M1 | `artifact_admission.py` の purpose dispatch を常に現行一致入口へ向ける | 歴史正例 (旧 pin の v2 が読める) | 前後に同じ入力を拒否する層は無い |
| M2 | 同 dispatch の certified 側も記録 policy 入口へ向ける | certified 拒否 (旧 policy を CERTIFIED_ACCEPTANCE で拒否) | 同上 |
| M3 | 歴史 policy decoder の exact key 集合検査を削除 | **余分 key** の形検査 (欠落 key は使わない、R8) | 余分 key は後続検査に掛からない |
| M4 | 同 decoder の schema literal 一致を削除 | schema 違いの形検査 | 他が有効な入力を使う |
| M5 | 歴史 receipt 照合で記録 policy SHA でなく現行 SHA を使う | 歴史正例 | 単一 |
| M6 | 歴史 stock 比較先を `CURRENT_PIN` に戻す | 旧 pin の stock 正例 | 単一 |
| M7 | **現行入口**の stock 比較値を receipt 自身の source commit にする (恒真化) | R3 の現行入口負例 (a) | 現行 policy SHA は維持するので入口では落ちない |
| M8 | decision の classification を従来値に戻す | 歴史正例の診断期待値 | 単一 |
| M9 | `layer3_schema.json` の certifying 側 classification 制限を削除 | schema 単体負例 (新 classification の certifying report) | 他の historical marker を持たせない |

baseline 緑を先に確認する。SURVIVED は注入実在を diff で確認するまで equivalent と数えない。

## 段 5 の分割

実装子 1 本 (Codex `role=author`、`sandbox=workspace-write`)。編集面が相互に依存するため分けない。
