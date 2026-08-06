---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-06
wave: dev-wave-t564-dependency-source
seq: 1
---

## {{D:dependency-source-out-of-home}}. certify が pin する依存 source の所在を home の外へ移し、凍結 evidence の binding を歴史値として分離する

**決定:** 共有 `tools/pegasus/policy.json` の `gflags_source_path` / `glog_source_path` を移す。
受理する値は各 key ごとにちょうど 1 つで、旧 = `/home/SFC/tanab/github/gflags` および
`/home/SFC/tanab/github/glog`、新 = `/work/SFC/tanab/github/gflags` および
`/work/SFC/tanab/github/glog` である (一般形は `/work/<project>/<user>/github/` 配下だが、
受理集合はこの exact な 2 値であって path family ではない)。
併せて、この 2 値を固定していた境界テストを次の形へ移す (D96 の手続義務による同一変更単位の更新)。

1. `orchestrator/tests/test_pegasus_tools.py` の path oracle 2 箇所を新 path の singleton へ移す。
   旧 path と新 path の併用は許容しない。expected HEAD・path 不在・HEAD 不一致・dirty の
   fail-closed 検査は変更しない。
2. `orchestrator/tests/test_silo_ladder_rung1_evidence.py` の `binding["policy"]` を、同 test が
   `driver` に対して既に用いている「歴史定数へ exact pin + 現行 bytes とは不一致」の分岐へ移す。
   歴史 identity tuple を 5 要素へ伸ばし、index 4 に旧 policy binding の値を置く。
3. `orchestrator/tests/test_t126_pegasus_tools.py` に現行 policy bytes の sha256 を**唯一の定数**として
   置き、「現行 bytes == 定数」と「凍結 binding != 現行 bytes」の 2 本立てにする。
   歴史値をこの file へ重複記載しない。

**理由:**

- home 配下の pin 済み source tree が環境から消えており、certification job は `gflags source path
  missing` で 11 秒 fail-closed していた。新較正の取得は、活性化権限や source proof 以前にこの一点で
  不能だった。運用方針として作業物を home へ置かない以上、同じ場所への再作成は採らない。
- 凍結 evidence (`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json`) は過去の走行が
  使った bytes の記録であり、**書き換えは歴史の改竄**である。したがって動かすのは検査の根拠だけとする。
  同 evidence の `driver` binding は既に同じ理由で歴史値へ移してあり、本決定はその先例に揃えたものである。
- 「凍結 evidence と一致」を検知の根拠にしたままだと、共有 policy を正当に更新するたびに
  歴史記録の側を書き換える圧力が生まれる。現行 bytes の明示 pin へ根拠を移すことで、
  **検知力を保存したまま**この圧力を断つ。変更前も変更後も、policy の任意の byte 変更は赤になる。
- 現行 bytes の定数は、実装子が編集後のファイルから算出すると誤った編集にも一致する自己成就 pin に
  なる。親が変更前 bytes から独立に算出した値を与え、実装が 1 byte でも違えば赤くなる形にした。

**path 表記の選択:** 計算ノード上の実測で、`/work/SFC/...` と `/work/1/SFC/...` はともに可視・
pin 済み HEAD 一致・porcelain 空だった。可視性に差が無いため、storage shard 番号を固定しない
`/work/SFC/...` を採る。**この観測の射程を限定する** — 1 node allocation (`-b 1`) の 1 job・
1 host・1 時刻であって、**専有は確認していない**。「非 symlink」も末端の gflags / glog directory
だけの性質で、採用した表記は `/work/SFC → /work/1/SFC` という祖先 alias に依存する。
alias が存在しない host では 10 consumer の source path が一斉に不在になる。

**この 2 値を読む consumer は 10 本ある** (本決定の影響範囲):
shell = `certify_calibration.sh`、`floor_campaign.sh`、`floor_scoping.sh`、`silo_ladder_rung1.sh`、
`t126_qualification.sh`、`t141_region_profile.sh`。
Python = `fetch_third_party.py`、`orchestrator/campaign/silo_ladder_rung1.py`、
`orchestrator/qualification/identity.py`、`orchestrator/qualification/submission.py`。
policy は T-126 の code identity 入力でもあるため、**新規 series identity と新規 campaign binding は
変わる**。旧 policy で作った preimage / receipt を新しい checkout で継続すると fail-closed になりうる。
過去の成果物 (T-139 / T-141 / T-293 の witness、登録済み較正) は過去実測の記録であり、書き換えない。

**名乗りの段階を分ける。** この決定が可能にするのは「job が依存段を通過すること」までで、
certify の完走・accepted calibration の取得・較正の活性化はそれぞれ別の段階であり、
別の blocker を持つ。段階を跨いだ名乗りをしない。

**却下した選択肢:**

- **同じ home path へ pin 済み HEAD で再作成する** — 作業物を home へ置かない運用方針と衝突する。
  消えた原因が特定できていない以上、同じ場所への再作成は同じ消失を招きうる。
- **依存 source も cache 経由の hydrate 対象へ広げる** — `fetch_third_party.py` は FetchContent の
  3 source を cache へ取りに行く道具で、この 2 依存を再作成する経路を持たない。対象拡張は
  機体固有の絶対 path 結合そのものを除去でき、source proof の課題とも噛み合うが、
  復旧の最小変更を超える。別タスクへ送る。
- **凍結 evidence 側の binding を新しい hash へ書き換える** — 過去の走行が使った値の記録であり、
  書き換えは歴史の改竄になる。採らない。
