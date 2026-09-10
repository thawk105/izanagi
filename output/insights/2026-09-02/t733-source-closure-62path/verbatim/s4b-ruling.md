# 段 4b 裁定 — 旧 grammar lock の扱い (受入の赤を閉じる)

ユーザーから「codex に相談して決めてください」と指示された。read-only codex 2 レンズへ相談し、
親が独立に裏取りしたうえで裁定する。

## 結論: 案 1 を、exact-24 grammar だけに限定して採る (案 1a)

`HISTORICAL_RAW` の読み取りに限り、**pre-T733 の exact-24 grammar** を decode できるようにする。
現行 certified 経路は exact-62 のまま 1 mm も緩めない。

2 レンズが独立に案 1 を推し、独立に同じ条件を付けた —
**通常 decoder を union grammar へ広げてはならない**。親もこれに同意する。

## なぜ他案を採らないか

- **案 2 (11 件を再発行)** は規律 7 に正面から反する。lock は WAL より前に live capture して作られる
  (`ident.py:575-602`)。測定後に残り 38 path の blob hash を計算しても、「測定時に disk bytes と
  blob が一致した」事実は復元できない。さらに lock hash は B10 の completion / receipt chain と
  A2 の raw manifest / acquisition digest 鎖へ伝播しており、外部 20〜40 file を書き換えることになる。
  凍結 provenance の bytes を変えないという本 wave の条件とも両立しない。
- **案 3 (fig2c を bytes 束縛へ移す)** は中央 admission を fig2c だけ迂回する局所対応で、
  activation tuple、記録 commit blob 照合、deny overlay、attempt topology、build receipt の
  検査を失う。作業量は最小 (120〜260 行) だが、失うものが正しさ側にある。
- **第 4 案 (hash allowlist)** は受理集合が案 1 より狭い一方、正の allowlist を新設し
  B10 に既にある hash 台帳を重複させる。将来の歴史成果物ごとに登録が要る。一般性が低い。

## なぜ exact-24 だけに限るか

旧 grammar は 8 / 12 / 14 / 24 / 25 / 27 がありうるが、**実在が確認できた corpus は exact-24 だけ**
である (外部 root の 11 件)。実在しない grammar を受理集合へ入れる根拠が無い。
D1075 の段階実装の趣旨とも合う。追加は実 corpus と consumer を添えて別 wave で行う。

## 親自身の誤りの確定

- 段 4 §5-1 の「repo 側 consumer は 11 件を decode 経由で読んでいない」「受入は赤にならず
  図の再生成も壊れない」は**誤り**だった。実 call chain は
  `test_plot_b10_extended_backoff.py` → `plot_b10_extended_backoff.load_measurements()` →
  `plot_backoff.load_campaign()` → `require_admitted_campaign(HISTORICAL_RAW)` で、
  親が `plot_backoff.py:267-270` を直接読んで確認した。
- 「本 wave が新たに作る回帰ではない」も不正確。旧 grammar 拒否という一般方針は以前からあるが、
  exact-24 の成果物は T-733 直前まで読めており、exact-62 へ置換した本 wave で初めて読めなくなった。
  **具体的な互換性回帰は本 wave に帰属する。**
- 「`HISTORICAL_RAW` から certified 主張への経路は無い」も強すぎる。`CertifiedCampaignView` の
  発行は token と exact E1 で閉じているが、歴史 view の `records` は共通 `ImmutableWalRecord` で、
  `require_persisted_certified_commit()` は view 型を要求しない。`critic/digest.py` と
  `critic/online_digest.py` は両 view を受け入れる。**間接利用は存在する。**
  したがって「当時記録された certified 証拠」と明記し、現行認証と読み替えない条件を付ける。

## 実装の不変条件 (両レンズの条件の合併)

1. **通常経路を変えない。** `decode_campaign_lock()`、`decode_campaign_lock_bytes()`、
   `_validate_authority()`、encode、resume、certified admission は exact-62 のまま。
2. **別入口・別返却型。** 歴史 decode は名前と型が違う専用経路とし、通常の
   `DecodedCampaignLock` と交換可能にしない。boolean 引数による緩和にしない。
3. **purpose を decode より前に exact enum で確定する。** `HISTORICAL_RAW` のときだけ
   歴史 decoder を選ぶ。`classify_campaign()` と全 certified 経路は通常 decoder だけを使う。
4. **grammar は exact ordered tuple で識別する。** path 数で判定しない。
   pre-T733 の 24 path を順序込みの定数として置き、未知集合・subset・superset は拒否する。
5. **記録 commit blob との digest 照合は維持する。** 歴史 grammar の path 集合全体で行う。
6. **歴史 epoch は記録 grammar の順序と、その grammar 固有の scope 文言で計算する。**
   現行 exact-62 の scope 文言を流用しない。現行適合は必ず `unknown` とする。
7. **互換実装を新 module へ分離しない。** 新 module を作ると、それ自身を閉包へ入れるべきかの
   問題が生じる (D1128)。`campaign_lock.py` と `artifact_admission.py` の中に置く。
8. **exact-24 だけ。** 8 / 12 / 14 / 25 / 27 は実在 corpus が無いので入れない。
9. 凍結成果物 (fig2b / fig2c / fig4) の bytes と外部 11 lock は変更しない。
10. `qualification/artifacts.py`、`layer3_report.py`、`s1_report.py` の直接 decoder は
    **触らない**。現状これらは旧 grammar を拒否しており、それは弱化ではなく現状維持である。
    整理は別 wave の裁定へ送る。

## 変異事前登録 (追加分)

| # | 変異 | 期待 |
|---|---|---|
| M06 | 歴史 decoder の grammar 判定を「key 数が 24 なら通す」へ緩める | KILLED |
| M07 | `purpose` の判定を外し、certified 経路でも歴史 decoder を選べるようにする | KILLED |
| M08 | 歴史 decode で記録 commit blob との digest 照合を飛ばす | KILLED |

正例 (過剰拒否の検出):

| # | 正例 | 要求 |
|---|---|---|
| P3 | 外部 exact-24 lock が `HISTORICAL_RAW` で読め、fig2c の生成経路が通る | 通ること |
| P4 | 同じ bytes を certified 目的で読むと拒否される | 拒否されること |
