# [T-1721] 非認証成果物型は現行の所有制約下では作れない — 停止と再開 scope

- wave: `dev-wave-t1721-noncertifying-a1`
- branch: `worktree-dev-wave-t1721-noncertifying-a1`
- base: local main `dd66213978d3d30eed567484ec013216bff6926b`
- 測定 tip: `a0a0cdf463d97101cd47eb5328b285f5385bbfdd` (main 取り込み後。closure 25 path は不変)
- 実装面の差分: **ゼロ**。本 wave は docs のみを追加する。

## 何を依頼され、何をしたか

D1028 に従い「認証権限を持たない成果物型の確定」と「A-1 対測定の投入器」を同じ変更単位で
作ることを依頼された。段 1 で前提を実測し、段 2 で file:line プランを起草させ、段 3 で 2 レンズの
敵対検査を並列で行い、段 4 で **実装しない**と裁定した。

停止の根拠は D1038 が自ら定めた先行条件である。

> 着手条件は、**認証済みの consumer へ昇格できないことを鍵・記録・schema・consumer の
> 全層で固定できる**ことである。field の除去や付け替えで昇格できる作りしか取れないなら、作らない。

## 一次証拠 — 非認証宣言は v2 再包装で無効化される

親が repo 外の temp directory にだけ書く read-only probe を実行した。probe は repo へ 1 byte も
書かず、実 campaign を 1 つも作らない。手順と観測値は次のとおり。

1. `contract_loader_binding.capture_contract_loader_binding()` で現行 closure を取得する。
   **この関数は批准を検査しない。** 得られたのは commit `a0a0cdf46...` の 25 path map。
2. `search_config` に `artifact_class: "non-certifying"` と `promotion_prohibited: true` を
   入れた inner identity を組む。
3. `env_contract.verified_current_activation_state()` から activation を取る。**公開関数である。**
   `activation_serial = 1`、
   `activation_state_sha256 = f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed`、
   active contract `1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7`。
4. `campaign_lock.encode_campaign_lock_v2()` で 2 の identity を 3 の authority で包む。
   **受理された。**
5. temp campaign root へその lock を置き、
   `artifact_admission.require_campaign_verifier_epoch(..., purpose=CERTIFIED_ACCEPTANCE)` を当てる。

観測結果:

```
LOCK-ONLY CERTIFIED GATE: PASSED
  state       = E1
  reason_code = recorded-closure
  epoch       = E1:ab51c89f52ff51fe61e81 ...
```

**未批准の closure から作った、内側で「非認証」「昇格禁止」と明記した lock が、
certified 受入の gate を E1 で通った。** 段 3 の lens A が独立の context で同じ probe を組み、
同じ epoch 値 `E1:ab51c8...` を得ている。2 独立実行で同値である。

base `dd66213` と取り込み後の `a0a0cdf46` の双方で再現した。

### なぜ通るのか

- `campaign_lock.py` の `_validate_identity` は identity の exact 5 key と型だけを検査し、
  `search_config` には `dict` であることしか要求しない。宣言 field を 1 度も見ない。
- `artifact_admission.py` の `require_campaign_verifier_epoch` は campaign.lock だけを読み、
  記録 map と現在 map の equality だけで E1 を出す。**批准台帳を 1 度も参照しない。**
- v2 authority の材料 (closure map、activation state、環境契約 hash) は**すべて公開**で、
  非認証 run に固有の秘密も発行 capability も要らない。

## なぜ「触ってよい面」では閉じられないのか

決定的なのは上記の lock-only 経路である。この経路は
`campaign_lock.py` / `contract_loader_binding.py` / `artifact_admission.py` の 3 file だけで
判定が閉じており、編集可能面 (`ident.py` / `wal.py` / `env_contract*.py` / `pipeline.py` /
`loop.py` / `layout.py` / `replay.py`) を 1 つも通らない。

本 wave は稼働中の `dev-wave-t1629-ratification-broker` と編集面が重なる恐れがあると指示され、
起動時に重複検査を行った。その結果、上記 3 file はいずれも同 wave の所有だった。

4 層別の到達点:

| 層 | 状態 | 理由 |
|---|---|---|
| 鍵 | 固定できない | v2 authority に署名鍵も非公開 capability も無い |
| 記録 | 固定できない | WAL に hash chain が無く、COMMIT の `contract_sha256` は公開値なので付け戻せる |
| schema | 固定できない | 閉集合は編集禁止 file の中 |
| consumer | 固定できない | lock-only E1 と view 発行は編集禁止 file の中 |

部分的に `ident.py` / `wal.py` だけへ拒否を入れる案は採らなかった。full admission 経路は
閉じるが lock-only 経路が開いたまま「閉じた型がある」という表示だけが立つため、現状より危険になる。

## 既存の marker は既に恒真だった

`paper_story_a1_paired.py` の campaign config は既に `promotion_prohibited=True` を持っている。
本 probe はその値を保ったまま certified gate を通した。**この marker は現状 1 つも発火していない。**
`declared_use_class` も同型で、`layout.py` / `loop.py` / `pipeline.py` / `buildcache.py` と
複数 driver に現れるが、いずれも保存先と build 材料の選択に使われるだけで、
文字列を書き換えれば official にできる。official と exploration で campaign id が同一になることを
固定した既存テストもある。**どちらも昇格不能性の根拠にはならない。**

## 副産物 — 再開時にそのまま使える材料

型が作れないという結論とは独立に、投入器側の調査は完了した。F634 が名指しした
「A-1 の投入器が存在しない」は現在も成立する (`tools/pegasus/submit_*.sh` は 8 本あり
A-1 用は 0 本、`paper-story-a1-paired-submission/v1` を書く実装は tracked file に 0 件)。

段 2・段 3 が確定させた材料は verbatim に保全した。

- acquisition receipt の必須 field と述語 (top-level 11、`submit_observation` 6、
  `qstat_visibility` 5、PBS observation 3)。段 3 が段 2 の表から落ちていた述語を 5 件補った
- `qsub` の argv と `-v` に載せる環境変数 6 個、job が内部で導出する値
- create-only の実装法 — temp file を `O_EXCL` で開き `fsync` し、同じ parent dir 内で
  `link()` する。`os.replace()` と最終 path の直接 open は create-only と呼ばない
- 既存 submitter 8 本の作法比較。A-1 用は `submit_b10_backoff_shape.sh` の即時 qstat と
  `submit_t126_qualification.sh` の invocation claim を組み合わせるのが近い

## 再開 wave が 1 land 単位にまとめるもの

段 3 が、段 2 の A/B 分割では端から端まで経路が通らないことを 3 箇所で示した。
再開時は次を分割せず 1 単位にする。

1. 非認証成果物型 (4 層)
2. **A-1 の campaign config への型の結線** — 現行 `campaign_config()` は新 class を設定しない。
   これが無いと A-1 は既定 certified のまま批准 gate で止まる
3. 投入器 (submit script + acquisition receipt producer)
4. **新 terminal stage への collector 対応** — 現行の集計器は stage 列の末尾を
   `STAGE_COMMIT` に固定している
5. **scheduler completion receipt の producer** — tracked tree の全数検索で 0 件。
   materializer は exact 10-field の completion document を必須にする
6. **materialize の起動手** — `run_materialize()` の呼び手が存在しない
7. 非認証結果を限定付き観測として読む reader / pointer
8. 波及する凍結 provenance の再生成 — `artifact_admission.py` の bytes は
   fig4 の validator SHA として再導出される

さらに段 3 は、禁止 2 file を編集するだけでも十分ではないと指摘した。marker を inner identity から
除去して v2 を再生成できるため、署名された identity 束縛か、全 consumer が参照する
改変不能な外部台帳まで設計する必要がある。

## 訂正 (段 1 で親が書いた誤り)

- 段 1 M5 は `declared_use_class` を「`pipeline.py` の引数と `layout.py` の出力 root 選択にしか
  存在しない」と書いたが誤り。`loop.py`、`buildcache.py`、複数 driver にも存在する。
  結論 (`CampaignConfig` と campaign 同一性には無い) は変わらない。
- 段 1 の追加測定は「予約 key を足しても既存 campaign の id が変わらない」と要約したが、
  正確には「その key を**持たない**既存 campaign の id が変わらない」である。key を持つ campaign の
  id は変わる。既存 certified の id を保ったまま宣言を入れるには、既定値を canonical preimage へ
  serialize しない条件付き serialization が要る。
- 段 1 の `docs/failures.md` 引用は、批准 gate の観測例外を「履歴が strict prefix extension でない」
  としていたが、base `dd66213` の実測は `enforcement-source-closure-unratified: closure digest is
  absent from the read-only ledger` だった。塞がれている事実は同じで、落ちる層が違う。

## 検査

- 実装面の差分ゼロのため変異 matrix は免除 (`DW-S04`)。受入全走は免除しない。
- probe はすべて read-only で、repo 内へは 1 byte も書いていない。
- codex 子は本 repo で pytest を実走できないため、子の出力を緑として記録していない。

## verbatim

- `verbatim/s1-brief.md` — 段 1 brief (前提実測 M1〜M7 を含む)
- `verbatim/s2-plan.md` — 段 2 プラン (停止結論、投入器の完全契約、変異候補)
- `verbatim/s3-lensA.md` — 段 3 正しさ境界レンズ (昇格経路の独立検証、第 3 の接ぎ目の探索)
- `verbatim/s3-lensB.md` — 段 3 整合・実効性レンズ (分割の着地可否、経路の切断 3 箇所、終端判定)
- `verbatim/s4-adjudication.md` — 段 4 裁定 (所見 14 件の real/refuted と採否)
