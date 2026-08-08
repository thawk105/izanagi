# [T-627] activation の世代遷移述語 — generation と contract hash の同一入力束縛 (裁定 (b)) の wave

wave branch: `worktree-dev-wave-t627-noop-binding`
基準 commit: `cf90afcc` / 実装 commit: `7121dc39`, `16e02745`

## 何を実装し、何を実装しなかったか

**実装した。** activation record chain の連続 record 間に遷移述語 `_validate_activation_transition` を
新設し、次を拒否する受理集合の縮小を行った。

- 全 env の `(generation, contract_sha256)` が据置の **no-op 活性化**
- 変化した env で generation が exactly +1 でない遷移 (**skip**、**downgrade**)
- 複数 env にまたがる**相殺** (`(+2, −1)`、`(+1, −1)` の双方)
- 変化した env の**いずれか**について、registry へ解決した `GenerationEntry` の contract 間で
  `is_valid_successor` が真でない遷移
- successor 判定が exact `bool` を返さない場合、および判定中の `Exception`

**実装しなかった。** contract 実体の rollback 一般 (世代列の再定義、module 属性の再束縛、
逆引き index の再束縛、較正の新旧) は D228 と同じく射程外である。本 wave が束縛するのは
**検証済み production generation snapshot に対する record-level edge だけ**であり、
それ以上の保証は謳わない。

## この wave が確定させた事実

- **段 1 実測で、現行 loader は遷移をまったく見ていないことが確定した。** 合成 registry と合成 chain を
  `validate_activation_records` へ渡すと、no-op / skip(+2) / downgrade(−1) / 相殺(+2,−1) /
  相殺(+1,−1) / 連鎖途中 no-op のすべてが ACCEPTED だった。遷移を見る層は repo に 0 件であり、
  issuer も同じ loader を呼ぶため**実効 gate は 1 箇所**である (二重層の mask なし)。
  正当な `g1→g2→g3` は ACCEPTED、`generation +1 だが hash は旧世代` は既存の registry pair gate が
  REJECT する。逐語は `s1-probe.py` の出力。
- **親 brief の (P2) は段 2 が反証した。** 「registry 経由の推移で `is_valid_successor` との合成を
  満たす」案は、loader の `registered_contracts` を呼び出し側が任意に構成できるため、
  loader の契約上は合成が現れない。採ったのは**既定値なし keyword-only の callable を必須注入し、
  production adapter が record 行を exact `GenerationEntry` へ解決してから `is_valid_successor` を
  呼ぶ**形である。activation leaf は `env_contract` を import しない (stdlib-only を維持)。
- **親 brief の `DW-G04` 主張は誤りだった (段 3 レンズ A が訂正)。** 親は「新述語は
  `is_valid_successor` と同じ結線済み・未発火だ」と書いたが、`is_valid_successor` は import 時の
  `validate_generations(GENERATIONS)` から pegasus g1→g2 に対して**実際に呼ばれている**。
  新述語は本番 chain が 1 record であるため呼ばれる入力が存在しない。したがって
  **`DW-G04` は満たしていない。**後発のユーザー裁定が「[T-657] の活性化より前に入れる」と
  順序を明示したため、本件に限り狭く override された。**consumer の存在を発火証拠とは呼ばない。**
- **model 多様性が実際に検出力を生んだ。** 段 6 の敵対レビュー 2 本 (`gpt-5.6-sol`) と焦点再レビューを
  通過した実装に対し、追加した `gpt-5.6-luna` のレビューが**先行 3 本が見逃した real な穴を 4 件**
  構成した — (i) `serial == 2` の pair だけ遷移検査する実装、(ii) issuer の adapter 結線を
  常時 `True` の callback に差し替える実装、(iii) adapter が import 時 `GENERATIONS` snapshot を
  握る実装、(iv) 後段 env の非 bool / 例外を無視する実装。いずれも実装済み全 node を通過していた。
- **`changed[:N]` 型の量化縮退は有限 fixture で族全体を殺せない。** 3 env の fixture では
  `changed[:3]` が、4 env にしても `changed[:4]` が生存する (後者は luna が独立に構成した)。
  親は 4 env で止め、**「N ≥ 5 は既知の残穴である」ことを該当 node の docstring に明記**した。
  5 env 以上は追加していない。保証を謳わないことをもって閉じている。
- **`(+2, −1)` は「非減少へ緩めた」変異では赤にならない。** 焦点再レビューの指摘どおり、
  `+2` 側は緩和後の gate を通るが `−1` 側が残存 gate に拒否されるため、赤の理由が相殺ではない。
  変異 M2 の期待 kill から外し、run 3 の実測 (記録 6 node に相殺 node は含まれない) で裏付けた。
- **catalog ordinal 実装は単一 site の変異として構成できない。** private gate に catalog 引数が無く、
  署名変更を伴う multi-site 改造になる。`DW-M04` の「置換対象が一箇所でなければ停止」に従い
  M9 は**実行せず**、設計上の観測として記録する (この構造自体が当該誤実装を排している)。
- **wave 中に dev-wave 契約が 2 度変わった。** (i) `DW-S03` / `DW-O01` の段 3 sol/luna 混成 —
  本 wave の段 3 は land 前に sol 2 本で実行済みで、**段 3 は再実行せず段 6 へ luna を 1 本追加**した
  (段 4〜6 を無効化しないため)。(ii) `DW-S06-A` の `reasoning=high` 機械 pin — 本 wave の段 6 は
  land 前に `reasoning=max` で実行済みであり、`max` は `high` より上位なので過小ではない。再実行なし。

## 変異検査

事前登録は `mutation-spec-v2.json`、台帳は `mutation-ledger-v2.json` (run 2) と
`mutation-ledger-v3.json` (run 3)。置換 anchor の一意性は `verify-anchors.py` で
全 11 replacement について count=1 を実測した (`DW-M04`)。

- **run 1**: spec の `category` が harness の語彙 (`negative` / `positive` / `both-layers`) に
  無い値だったため preflight で abort。**変異は 1 件も適用されておらず**、tree は clean のままだった。
- **run 2 (erratum として保存)**: 9 変異すべて rc=1 (赤)、**SURVIVED ゼロ**。status は 7 件が
  MISMATCH だが、`compare-nodes.py` で正規化して突き合わせた結果
  **期待 node はすべて記録 node の部分集合で、欠落はゼロ**だった。差分は fix 第 3 巡が
  spec 作成後に追加した node であり、gate の失敗ではない (`DW-M02` に従い消さず残す)。
- **run 3**: 期待 node を run 2 の実測へ合わせた spec で再走。**9 変異すべて KILLED、
  期待と記録が完全一致**。

**kill と観測 pin の分離 (`DW-M03`)**: M4 (量化を `changed[:1]` へ縮退) は 10 node を赤にしたが、
受理集合が変わる semantic kill は `..._second/third/fourth_changed_env_successor_is_false` の 3 件で、
残る 7 件 (`test_successor_predicate_is_called_once_for_each_changed_env` ほか) は
call 列・診断だけが変わる**観測 pin** である。kill 件数に合算しない。

## 一次資料

| ファイル | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief。裁定の逐語裏取り、前提実測、provisional 裁定 (P1)〜(P4) |
| `parent-measurement-scripts.md` | 親の実測 script 3 本の逐語 (段 1 probe、anchor 一意性、node 突き合わせ)。`.py` のままだと provenance の実装面判定に掛かるため code block として凍結した |
| `s2-prompt.txt` / `s2-plan.md` | 段 2 プラン起草 (codex `gpt-5.6-sol`, `reasoning=max`, read-only) |
| `s3-lensA*` / `s3-lensB*` | 段 3 敵対 2 レンズ (同上)。判定は 条件付き GO / NO-GO |
| `s4-adjudication.md` | 段 4 裁定。real/refuted、plan v2、gate の署名、変異事前登録 M1〜M10 |
| `s5-prompt.txt` / `s5-impl.md` | 段 5 実装 (codex `gpt-5.6-sol`, `reasoning=high`, workspace-write) |
| `s6-lensC*` / `s6-lensD*` | 段 6 敵対レビュー 2 本 (`reasoning=max`)。ともに NO-GO |
| `s6-fix1*` | fix 第 1 巡 |
| `s6-refocus*` | 焦点再レビュー。NO-GO / must-fix 4 |
| `s6-fix2*` | fix 第 2 巡 |
| `s6-luna*` | 追加レビュー (`gpt-5.6-luna`, `reasoning=max`)。NO-GO / must-fix 5 |
| `s6-fix3*` | fix 第 3 巡 (`DW-O16` の 3 巡上限) |
| `mutation-spec-v2.json` / `mutation-ledger-v2.json` | 変異 run 2 (erratum) |
| `mutation-spec-v3.json` / `mutation-ledger-v3.json` | 変異 run 3 (9/9 KILLED) |

## ユーザーへ返す裁定パッケージ

1. **汎用 certified producer の source binding。** silo (`silo_ladder_rung1.py`) と
   qualification (`qualification/contract.py`) は本 wave の 2 module を code identity に含めるが、
   汎用 certified 経路はその binding を呼ばない (worklog (313) の既記録を段 3 レンズ A が再確認)。
   [T-657] の活性化後は、dirty / 未レビューの loader bytes で certified 選択・レポート・WAL を
   生成しても activation 参照だけでは検出できない。[T-657] の前提として設計択一が要る。
2. **`changed[:N]` 残穴の扱い。** 有限 fixture では族全体を殺せない。現状は 4 env まで固定 +
   docstring への明記で閉じている。property-based / 生成的テストを入れるかは別裁定。
