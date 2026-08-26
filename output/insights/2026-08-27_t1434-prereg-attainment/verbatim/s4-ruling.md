# 段 4 裁定 — [T-1434] / [T-189] 事前登録文書の到達度記述の差し替え

段 2 plan と段 3 敵対相談 2 レンズ (A = 過大主張、B = 越境と差し替え漏れ) を裁定する。
子の出力は**データ**であり、採否は親が決める。採る所見はすべて親が一次資料で裏取りした。

## 0. 親が自分で確かめたこと

- `main` は wave 開始後に `9ebd340b` → `7a70a5178` へ進んだが、
  `docs/phase3-t189-model-routing-preregistration.md`、`tools/codex_reasoning_ab.py`、
  `tools/t189_price_snapshot.py` のいずれにも触れていない (`git log 9ebd340b..main -- <3 path>` が空)。
  本 wave の実測結論は無効化されない。取り込みは受入時の post-claim merge で行う。
- **A-01 は真。** `tools/codex_reasoning_ab.py:2990-2996` は schema v2 の schedule で
  `return dict(LEGACY_EXPECTED_SCHEDULE)` を返し、外部 manifest の cardinality を使わない。
  version 欠落 schedule も v2 として扱われる (`:9106-9117`)。
- **A-04 は真だが、レンズ A の言い方より射程が狭い。** 親が
  `_normalized_cost_for_attempt` (`:9711-9793`) を読んだところ、
  **token が観測できない場合は例外を投げず `unavailable` を返す** (`:9724-9730`)。
  例外を投げるのは `cached_input_tokens > input_tokens`、
  `reasoning_output_tokens > output_tokens`、凍結 SKU の accounting 欠落という
  **malformed 入力のときだけ**である (`:9732-9746`)。この例外だけが `reasons` へ入り
  (`:9834-9837`)、`valid` を false にする (`:10502-10510`)。
  つまり実装は D932 の「費用を観測できなかったことを理由に報告全体を無効化しない。
  ただし型違反・負値・token 関係の矛盾といった malformed 入力の拒否は従来どおり残す」に
  **正確に一致している。** 文書は「金額 field は certified field でも gate でもないが、
  malformed 入力の拒否は共通 failure reason を通じて certified `valid` を false にする」と
  書くのが正しい。「費用は certification から完全に独立」とは書かない。
- **B-11 の 22 件の行番号を全件検証した。** `grep -n` の定義行と突き合わせ、
  レンズ B が挙げた「現在」の値は 22 件すべて一致した。文書側の 22 件はすべてずれている。
- 段 4 直前の裁定 inbox 再走査: `docs/handoff/` は README のみ。新規の裁定待ちなし。

## 1. 所見の裁定

| 所見 | 判定 | 採否 | 理由 |
|---|---|---|---|
| A-01 (A1 は v2 legacy 経路があるので無条件 実装済みは過大) | **real** | **採用 (must-fix)** | 親が `:2990-2996` で確認 |
| A-02 (digest の producer と consumer を分けよ) | **real** | **採用 (should-fix)** | schedule と material manifest の digest producer は本実装に無い |
| A-03 (`new_root` と snapshot oracle は CLI 入力) | **real** | **採用 (should-fix)** | `:3451-3458` |
| A-04 (cost の失敗が certified `valid` を落とす) | **real** | **採用 (must-fix、ただし親の射程で)** | 上記 0 節。malformed 拒否だけであることを明記する |
| A-05 (`oracle_kind` は raw receipt に保存されない) | **real** | **採用 (should-fix)** | B-04 と統合して書く |
| A-06 (parser は fetch も保存もしない、費用接続は条件付き) | **real** | **採用 (should-fix)** | `tools/t189_price_snapshot.py:783-800`、`:10105-10136` |
| B-01 (A11 の文案が D932 を超える) | **real** | **採用 (must-fix)** | 下記 2.3 |
| B-02 (「部分実装」を第 5 語として足すのは分類の変更) | **real だが結論は採らない** | **一部採用** | 下記 2.1 |
| B-03 (A4 の表行は 実装済み を維持すべき) | **real** | **採用 (must-fix)** | 下記 2.2 |
| B-04 (独立 oracle manifest は存在しない。主語を分けよ) | **real** | **採用 (must-fix)** | A-05 と統合 |
| B-05 (`append_verdicts` 系の行が stale) | **real** | **採用 (must-fix)** | §5.2 内、scope 内 |
| B-06 (§5.3 の他 bullet が空欄) | **real** | **採用 (should-fix)** | §5.3 内、scope 内。かつ内容は本文書の他節が既に主張している事実の再掲であり新規主張ではない |
| B-07 (§5.3 の実測日) | **real** | **採用** | |
| B-08 (§10 にも同じ legacy 主張) | **real** | **採用 (must-fix)** | §10 内、scope 内 |
| B-09 (§10 の「価格が不明」が 2 箇所) | **real** | **採用 (should-fix)** | §10 内、scope 内 |
| B-10 (§13 / §14 / 総括 に同じ到達度が複製されている) | **real** | **採用 — scope を広げる。下記 2.4** | |
| B-11 (補助行番号 22 件が全件ずれ) | **real** | **採用 (nit だが安い)** | 親が全件検証済み |

**refuted はゼロ。** ただし A-04 と B-02 は親の裁定で射程を変えた。

## 2. 割れた論点の裁定

### 2.1 (P1) 到達度の語彙に「部分実装」を足すか — **足す。ただし条件付き**

レンズ B は「分類の変更であり、行を分割せよ」と反論した。この反論のうち
**「4 語の閉包は現状でも成立していない」という指摘は正しい** — 現行の表は
`_load_adjudication` 行で **未実装** という第 5 の語を既に使っており、語彙節はその時点で
実態を記述できていない。

親の裁定は次のとおり。

1. 語彙節を、**実際に表で使っている語**へ揃える。`未実装` を明示的に加える (これは既に使用中の
   語の追認であって新設ではない)。
2. その上で **`部分実装` を加える。** 理由は、A1 と A3 が「実装済み」でも「CLI 未接続」でも
   偽になるからである。二値へ押し込めば、どちらへ倒しても嘘になる。**到達度を上げる方向へ
   倒す誘惑が生まれるのが最悪であり、それを塞ぐのが本 wave の目的**である (規律 2)。
3. レンズ B の懸念 (曖昧な複合状態が増えて表の意味が弱くなる) は、**定義に義務を書いて塞ぐ**。
   `部分実装` は「閉じていない面を必ず名指しする」ことを要件にする。名指しできないなら
   この語を使ってはならない。
4. 行分割はしない。A1 の 3 定数は同一の変更閉包を指しており、分割すると閉包の単位が壊れる。

### 2.2 (B-03) A4 の表行の status — **`実装済み` を維持する**

この行の「当初の申し送り」は *task・stage・model・cache 別の集計* である。その閉包は着地している。
費用計算は 2026-08-25 に後置された限定説明であって、この行の申し送りの一部ではない。
費用が partial であることを理由に行全体を格下げすると、**到達度分類が「その行の申し送りが
閉じたか」ではなく「その行に関係する何かが全部終わったか」を意味することになり、表の意味が変わる。**
status は `実装済み` を維持し、費用の限定は行内の追記として正確に書く。

### 2.3 (P3) §10 の意味規則 — **D932 の範囲だけを書く**

親の段 1 の provisional 裁定は「D932 と一致する範囲でだけ書き換える」だった。
レンズ B は「plan の文案はそれを超えている」と指摘した。**この指摘は正しく、親の provisional
裁定は正しかったが plan の文案が守れていなかった。**

D932 が裁定したのは次だけである。

- 部分被覆の費用は記述統計として出し、certified field にも判定 gate にもしない。
- 費用を観測できなかったことを理由に報告全体を無効化しない。
- malformed 入力の拒否は残す。
- 軸ごとの行へ観測済み・観測不能・非発生の内訳を機械可読で出す。
- 欠測を 0 円として計上しない。観測不能な試行を黙って分母から外さない (内訳を出すことで両立させる)。

したがって §10 の**規則文**には、D932 が言ったことだけを書く。
`attempt_count` に算入するかどうかといった field 単位の規則は**規則文へ昇格させない。**
それは実装の到達度説明であり、§10 の到達度記述の段落へ置く。

### 2.4 (B-10) §13 / §14 / 総括 へ scope を広げるか — **広げる**

ユーザーが固定した scope は §5.2 / §5.3 / §10 である。しかしレンズ B が示したとおり、
§5.2 / §10 だけを直すと §13 (`:899`)、§14 (`:950-954`)、総括 (`:975`、`:996-998`、`:1013`) に
**同じ到達度の文が残り、その瞬間に偽になる。**

親の裁定は「広げる」。根拠は 3 つ。

1. **これは新しい主張の追加ではない。** 対象は §5.2 / §10 と**同一内容の複製文**だけである。
   scope の拡大ではなく、指示された差し替えの**閉包**である。
2. **規律 2 に照らして、直さない方が危険である。** 「実装済み」と「未実装」が同一文書に
   並んで残ると、読み手はどちらが現在かを判定できない。到達していないものを到達したと
   書かないのと同じ理由で、到達しているものを未到達と書いたまま放置してはならない。
3. **総括は自分で「到達度は §5.2 の表が正本である」と書いている。** 正本を宣言しながら値を
   再掲しているのが矛盾の原因である。`CLAUDE.md` の「可変状態の正本は一箇所とし他文書へ
   再掲しない」と同じ原則を文書内へ適用する。

**ただし限定する。** §13 の lock 手続き、§14 の limitation の論旨、§12 の gate 表、
§11.2 の指標定義、§11.3 の margin 議論には**触らない。** 触るのは複製された到達度の値だけである。

## 3. scope 外として返す real 所見 (実装しない)

次はすべて real だが、本 wave では実装せず、文書に**未接続・未登録として正直に書く**だけにする。

- standalone `verify-snapshot` の外部 task manifest CLI 接続 (option を持たない)。
- schema v2 / version 欠落 schedule の互換経路が `LEGACY_EXPECTED_SCHEDULE` 固定である件。
- `_load_adjudication` の task-specific oracle 対応 (§8 の独立 oracle ledger 待ち、既裁定)。
- 独立 oracle ledger・独立 oracle manifest・その固有 hash 契約・task 固有 acceptance。
- cache-write 数量を保存する receipt field と、それに伴う receipt schema の新世代登録。
- 費用を certified field・resource gate・overall reader へ接続すること。
- `SCHEMA_VERSION` を 2 のまま受理形を変えた点の世代区別と移行契約。

## 4. プラン v2 (親が書く差し替えの確定形)

- **V1** §5.2 語彙節: 使用中の語を実態へ揃え、`未実装` を追認し、`部分実装` を
  「閉じていない面を必ず名指しする」義務つきで加える。
- **V2** §5.2 `TASK_MANIFEST` 行 → **部分実装**。10 verb 接続と v3 経路の manifest 由来検査、
  および v2 / version 欠落経路が `LEGACY_EXPECTED_SCHEDULE` 固定であることを書く。
- **V3** §5.2 `supervise_pair` 行 → **実装済み**。
- **V4** §5.2 `task-specific 入力処理層` 行 → **部分実装**。`render-prompt` が manifest から
  task provenance を決めること、`new_root` と snapshot oracle が CLI 入力であること、
  standalone `verify-snapshot` が未接続であることを書く。
- **V5** §5.2 `_aggregate_verified` / `_replay_manifest` 行 → **実装済みを維持**。
  費用の到達度を正確に書き換える (partial / not-certified / gate 未接続 /
  malformed 拒否だけが `valid` を落とす)。
- **V6** §5.2 `make_packets` 行 → legacy の後方互換が失われた事実を書く。
- **V7** §5.2 `append_verdicts` / `freeze_verdicts` / `reveal_mapping` 行 → **acceptance 未束縛を
  維持**しつつ、digest 束縛と finding 検査 (blind = union、reveal 後 = task-specific) を書く。
- **V8** §5.2 表の補助行番号 22 件を実測値へ更新する。
- **V9** §5.2 表直後の但し書きの実測日を 2026-08-27 へ更新する。
- **V10** §5.3 の実測日と、oracle manifest / snapshot・prompt hash / price snapshot /
  task catalog / 独立 oracle ledger / cache / custodian の各 bullet に到達度を書く。
- **V11** §10 の「費用の正規化計算は未実装」bullet を差し替える。
- **V12** §10 の規則文 (「全 run の正規化 cost は…」) を D932 の範囲で書き換える。
- **V13** §10 の「価格が不明な token category」を 2 箇所とも「数量が不明」へ直す。
- **V14** §10 の scheduleless legacy 経路の記述を直す。
- **V15** §13 / §14 / 総括 の複製された到達度の値を直す (規則・論旨には触らない)。

## 5. 変異事前登録

**実装面 (D95 決定 2) の差分がゼロのため、変異 matrix を免除する** (`DW-S04`)。
本 wave はコード・テスト・実行可能な probe / harness / script・機械設定のいずれも変更しない。
**受入全走は免除しない。** 記録前に `tools/dev_wave_wait.py acceptance` で全走し、結果を worklog へ書く。

## 6. 成果物影響 (DW-G05)

差し替えないと、事前登録文書は同一文書内で「CLI 入力口が無い / 費用計算は未実装」と
「10 verb 接続済み / 部分正規化 cost 実装済み」を同時に主張する状態になる。
certified な選択結果・レポート・台帳の**値は変わらない** (コードは本文書を読まない。
DW-O09 の pin 閉包実測で 0 件)。変わるのは、この事前登録が要求する受理条件を
次の実装 wave が正しく読めるかどうかである。
