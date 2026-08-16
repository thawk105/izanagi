---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-floor-reseal-authority
seq: 2
---

## {{D:ai-floor-reseal-authority}}. 床値 protocol の束縛の張り替えだけを AI へ開放し、組ごとに 1 件で機械封鎖する

**決定 (2026-08-16 ユーザー裁定 = 案 1 + 案 3。案 2 は不採用):**

床値 protocol のうち **AI が更新してよいのは `contract_sha256` と `ccbench_pin` の 2 field だけ**とする。
残る 16 field (`schema` / `formula` / `env_tag` / `freeze` / `stock_configuration` / `n_sessions` /
`reps` / `master_seed` / `schedule_algorithm` / `extime_s` / `wired_min_rel_floor` /
`retry_slots_per_cell` / `session_cv_max` / `cell_cv_max` / `scale_adequacy_rel_tolerance` /
`allowed_excluded_reasons`) は不変で、その改訂は引き続き人間手番である。
床値 protocol は **(contract_sha256, ccbench_pin) の組ごとに 1 件**とし、同じ組への 2 件目を
機械的に拒否する。既存の凍結 bytes は 1 件も上書きしない (追加のみ)。

実装の確定形は次のとおり。

1. 格納 path は `output/s8b-freeze/floor-protocols/<contract_sha256>--<ccbench_pin>.json` とし、
   組から一意に導出する。issuer の公開 API は零引数で、path・contract・pin・先行 protocol の
   いずれも呼び手が指定できない。
2. 新 namespace を launch certificate の chain record pattern へ登録する。
   **登録しなければ、versioned protocol を 1 件置いた瞬間に freeze namespace の未知 file 拒否が
   発火し、既存の床値 campaign が起動できなくなる。**
3. 不変 16 field は先行 protocol から field ごとの canonical bytes で byte-exact に継承し、
   承認定数から再導出しない。定数は人間が編集できるため、定数経由で不変 field が動く経路を塞ぐ。
4. lineage anchor は working tree でなく、一度だけ解決した固定 HEAD commit の exact 100644 blob から
   読む。issuer の全 Git read は同じ commit OID と衛生化した環境 (repository / object / config /
   replacement 系の環境変数を除去し `GIT_NO_REPLACE_OBJECTS` を設定、argv にも
   `--no-replace-objects`) で行う。
5. 既裁定 Q3 (両成分がともに交代) の機械化として、**target の `contract_sha256` が組 index に
   既出なら発行を拒否する**。この拒否は issuer だけでなく組 index 自身の不変条件でもあり、
   何らかの経路で同一 contract の 2 件が入った repository は以後の全 scan が fail-closed になる。
6. 撃てないゲートは積まない。publish 直前の環境契約再照合は、authority snapshot が
   PID ごとに cache されるため必ず一致する恒真ゲートであり、実装しない。
   代わりに publish 直後の HEAD commit 移動検査を置く。
7. 発行後の検査失敗では artifact を自動削除しない (既存の人間手番 seal と同じ方針)。
   ただし例外 message に作成された artifact の exact path と、
   取り除くまで新しい床値 protocol を発行できない旨を必ず載せる。

**この決定が変えないもの:** 規律 2、凍結の履歴不変条件、較正 (環境側) の取得手順と受入検査、
人間手番の seal 経路 (`--confirm-user-freeze` + 対話 shell + T-080 receipt)、
承認定数、凍結台帳の 23 key、凍結チェーン検証の保留状態。

**理由:**
- ワークロード・受理閾値・seed・実験手順・除外理由が動かせないため、
  「低い床値が出る設計を選ぶ」自由度が構造的に存在しない。動くのは束縛の張り替えだけである。
- 組ごとに 1 件へ固定すると、同一条件で測り直して良い結果を選ぶ経路が消える。
  追加のみで既存 bytes を上書きしないため、凍結の履歴不変条件とも両立する。
- 環境契約 hash と ccbench pin は実 repository から機械的に決まる。呼び手が渡せる面を持たせないと
  決めれば、「どの条件で測るか」を submitter が選ぶ経路そのものが無くなる。
- 撃てないゲートを防壁として数えると、防壁台帳の件数と実効防壁が食い違う。
  恒真な再照合を残すより、発火しうる検査 1 本に置き換えるほうが強い。

**却下した選択肢:**
- **測り直しの事前登録 + 全走行の記録 (案 2)** — ユーザーが不採用と裁定した。
  案 1 と案 3 で設計の自由度が消えるため追加機構は要らない、が理由である。
- **path を receipt や引数で選ばせる** — 検証対象を submitter が選べる受理拡大になる。
  組からの決定的導出であれば、path と document の相互束縛を機械検査できる。
- **不変 16 field を承認定数から再導出する** — 定数は人間が編集できるため、
  定数の drift が AI 発行の protocol へ黙って入る経路が残る。
- **anchor を working tree から読む** — 単体 validator は `master_seed` を非空文字列、
  `wired_min_rel_floor` を範囲でしか検査しない。working tree の改変値が
  validator を通過し、全 successor へ正確に継承される。
- **共有 Git env helper 側を直す** — 同型の穴を持つ第 2 の consumer をまだ実測していない。
  単発事故の族一般化は独立 2 例を要する。

**残る限界 (この決定では閉じない):**
- ccbench pin を前進させれば新しい組ができるため、消えたのは「同じ組で 2 本目」であって
  「pin を進めて新しい組で測り直す」ではない。
- 組の一意性は sanctioned namespace 内に限る。ratified freeze の pointer は
  任意 canonical path を受理する。
- protocol 単位の封鎖であって run 単位ではない。同一 protocol の複数回実走は現在許されている。
- 発行済み artifact を削除すれば同じ組を再発行できる。履歴不変条件の検査は凍結チェーン保留の対象である。

**supersede:** D437 は「環境世代 g2 の活性化は上位権限束の人間 lockstep に従属する」と結論し、
その根拠に 2026-08-10 / 08-11 の Q2 (承認 A・発効 X ともに人間) を挙げた。
**2026-08-16 のユーザー裁定は、束縛の張り替え (環境契約 hash と ccbench pin の更新) に限り
Q2 を解除した。** D437 のうちこの限定範囲に関する部分は本決定が supersede する。
Q3 (lockstep) と、ワークロード・閾値の改訂が人間手番である点は D437 のまま不変である。

**研究状態への影響:** 本決定は certified 選択・材料レポート・試行台帳の**現在値を 1 件も変えない**。
実 repository へ protocol artifact を追加しないためである。変わるのは launch certificate の
受理集合の 1 点だけで、chain record pattern に合致する path が「未知 file」から
「chain record」へ移る。現在その path に file は無いため、今日の launch 判定も変わらない。
