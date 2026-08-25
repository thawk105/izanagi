---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-25
wave: dev-wave-t1669-floor-ledger-recovery
seq: 1
---

## {{D:floor-cut6-reissues-same-attempt}}. 床値の cut 6 は同じ attempt を測り直させ、次 ordinal を開かない

**決定:** consumed marker が在り attempt-ledger の行が欠けた crash cut (復帰手順書の cut 6) では、
admission が marker から ledger を再構築し、**同じ `attempt_id` の observation admission を
再発行する**。新しい ordinal を開かず、retry 枠も消費しない。

再発行を許すのは次のすべてが成立するときだけとする。

- consumed marker が実在し、claim と main ledger から完全再導出した document と exact 一致する。
- attempt-ledger の対応行が**欠けていた**。
- その attempt に完了 `session` 行が無い。

marker から ledger 行を捏造する向き、ledger 行があり marker が無い向きは拒否する。
復旧と再発行は shared root lock の同じ critical section で行う。

**理由:**

- 復帰手順書の真偽表は cut 6 を「marker が消費の権威、ledger はその projection、
  **observe できる。ledger の欠落を理由に止めない**」と定めている。この決定はそれを実装しただけである。
- D796 は「attempt-ledger は consumed marker の projection であって独立の権威ではない」と定める。
  projection の再構築は admission 自身の権威の中にあり、状態主張を伴わない。
- 現行の書き込み順 (marker → ledger 追記 → receipt 発行) が固定されているため、
  **ledger 行の欠落は receipt 未発行を静的に証明する。** 観測が始まっていないことを
  admission 自身の artifact だけで示せるので、registry を必要としない。

**却下した選択肢:**

- **admission 側の journal へ recovery event を書き、それを次 ordinal の trigger にする** —
  段 2 の plan はこの形だったが、段 3 の敵対 2 レンズが独立に「『前の attempt は放棄された』という
  状態主張であり、D796 が禁じた二重権威を作る」と示した。payload に terminal status も
  失敗理由も持たせなくても、次 slot を開く根拠にした時点で状態主張になる。
- **marker と ledger の不整合を放置する** — D496 が禁じる行き止まりが残る。
- **M+A+ でも再発行する** — 観測が始まったか否かを admission だけでは証明できない。
  fail-closed のまま残す。

## {{D:floor-next-ordinal-needs-registry-recovery}}. 床値の次 ordinal は registry の検証済み recovery でだけ認可し、authority は admission に pin する

**決定:** 床値 campaign の retry trigger を、次の**排他的二択**にする。

- 旧経路: 同 cell / round の planned `session` が一意で `valid is False`。
- 新経路: trigger attempt に対する **attempt registry の検証済み recovery** が存在する。

排他は分岐の成立値でなく**候補 evidence の件数**で判定する。両方あれば拒否、どちらも無ければ拒否。
新経路では trigger 側 attempt の consumed marker の実在も要求し、journal の自己申告だけでは認可しない。

recovery の authority (`authority_id` と `authority_policy_sha256` の対) は
**admission に pin した許可集合**でのみ受理する。候補 receipt が自分の trust root を選ぶことを禁じる。
**この許可集合は今日は空である。** したがって新経路は production では fail-closed で発火しない。

**理由:**

- 復帰手順書の真偽表は cut 10 を「registry の recovery と外部受領証を根拠に、
  次 ordinal を 1 つだけ認可する」と定める。状態の権威は registry だと D796 が定めている以上、
  admission は registry を読む側でしかありえない。
- 8b の retryable 集合は空なので、`retryable-failure` の terminal を作れない。
  検証済み recovery は 8b で唯一の再走経路であり、admission がそこを塞いでいる限り
  registry 側が完成しても復帰機構は発火しない。この決定はその塞ぎを外す。
- 「今日は発火しない」を言葉でなくコードで強制するために、許可集合を空にする。
  scheduler accounting collector を作る作業がここへ登録する。
- 段 6 のレビューが「候補 receipt から authority を採っている」穴を現物で示した。
  検証対象の artifact が自分の信頼の根を名乗れる形は、絶対規律 2 が想定する
  最適化圧力の攻撃面そのものである。

**却下した選択肢:**

- **admission が registry adapter を import する** — adapter の production 非接続は
  D797 と meta-test が固定している。検証には共通 core を使い、campaign からも読ませない。
- **旧 `valid=False` 経路を同時に廃止する** — 既存 campaign の受理集合が変わる。
  registry の空 `retryable_failure_reasons` との不整合は既知で、別裁定へ回す。
  本 wave はその不整合を**増やさない**。
- **authority を frozen protocol へ持たせる** — 凍結 bytes の変更と refreeze が要る。
  空の pin 集合で fail-closed にすれば、発火しないという性質は同じ強さで得られる。

## {{D:same-gate-different-time-is-not-asymmetry}}. 認可時と履歴再検査時で評価時点の違う述語は、明示引数で分ける

**決定:** consume (新しい認可を出す時点) と最終 evidence 検査 (履歴を再検査する時点) が
同じ gate を共有するとき、**評価時点に依存する述語だけを明示的な引数で分岐**させる。
暗黙の分岐、呼び出し側での事前フィルタ、片側だけの緩和で代替しない。

床値の retry 認可では「その cell で最新の retry start であること」がこれに当たる。
consume では要求し、最終検査では要求しない。ordinal の連続 prefix と trigger の一意性は
両時点で要求する。

**理由:**

- 「最新であること」を最終検査にも課すと、recovery が連鎖した正当な履歴
  (planned が retry1 を開き、retry1 の recovery が retry2 を開く) を再検査するとき、
  retry1 の時点で最新が retry2 になるため**正当な履歴が必ず拒否される。**
  測定はできても成果物が `artifact-invalid` で終わる行き止まりになる。
- これは検査の厳しさを場所によって変えることではない。同じ規則を評価する時点が違うだけであり、
  その違いをコードに書かないと、片方を直したときにもう片方が黙って壊れる。
- 実測で見つかった。静的レビュー 3 本 (敵対 2 + 焦点再レビュー 1) は
  この退行を検出できず、親のテスト実走が初めて赤にした。

**却下した選択肢:**

- **最終検査側で対象を事前にフィルタする** — 「どの履歴を検査しないか」という判断が
  呼び出し側に散り、gate の射程が読めなくなる。
- **両側で最新を要求し、テストの履歴を単純化する** — 実運用で起きる連鎖 recovery を
  テストから外すだけで、行き止まりは production に残る。
