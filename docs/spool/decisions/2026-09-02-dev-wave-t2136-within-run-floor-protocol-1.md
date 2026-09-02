---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-02
wave: dev-wave-t2136-within-run-floor-protocol
seq: 1
---

## {{D:within-run-genome-from-receipt}}. within-run 較正の protocol は受入証の実行済み build argv から導出し、申告を受けない

**決定:** certify 経路の producer は canonical genome を `acquisition_receipt.ccbench.build_argv`
から導出して成果物へ書く。`--genome` のような自己申告の引数は作らない。導出は次を benchmark の
**前**にすべて要求し、1 つでも欠ければ `receipt-genome-invalid` で測定前に停止する。
configure と build を分ける `&&` がちょうど 1 つ、build 側に `--target ycsb_<protocol>.exe` が
ちょうど 1 つ、測定 binary の basename が target と一致、protocol が `SPACES` に登録済み、
`space_for(protocol).axes` の**全軸**が configure 側の define に現れる、
`-DCCBENCH_TRACE` がちょうど 1 つで値が 0、flag の重複・非整数・値なしがない、
build 側に CCBENCH define が混入していない。
軸でない define (`BACKOFF_FIXED` 等) は genome から落とさず記録する。
非 certify 経路には genome を書かない。schema は `calibration/v2` のまま、
従来の key 集合と genome を足した key 集合の **2 形状だけ**を exact 受理する。

**理由:**
- D1374 は「出所を知らないまま bytes を書き換えない」「検査していないことを検査したと読ませない」を
  理由に、genome 不在の歴史的 record を silo 仮定として表示させた。手渡し binary へ genome を
  申告させる案は、その構図をそのまま再生産する。受入証の build argv は実際に実行された
  configure/build であり、その出力 binary の SHA-256 は測定 binary と既存経路で照合されている。
  申告ではなく process provenance に基づく。
- 全軸の存在を要求しないと、軸の一部を欠く受入証でも形式だけ canonical な文字列が通り、
  将来の厳密な genome 照合を汚す。protocol の登録要求と併せて閉じる。
- 軸でない define を落とすと、異なる binary が同じ genome 文字列を持ちうる。記録は
  探索空間の射影ではなく build の忠実な写像とする。`SPACES` は探索の空間であって
  正規の flag 全体ではなく、可変でもある。
- schema を任意 field 許容へ一般化すると、key 集合の完全一致という fail-closed 性質を失う。
  2 形状に限れば、凍結済みの登録済み較正は従来形のまま通り bytes を 1 bit も変えずに済む。

**却下した選択肢:**
- producer が genome から build する — 認定取得は pinned-clean worktree、専用依存物、
  fresh build、条件 gate、別建ての検査を経てから較正器を呼ぶ。build 経路の置換は
  記録の追加という目的を超え、予約時間と熱状態の順序まで変える。
- 手渡し binary と申告 genome を再 build で照合する — 認定の fresh build と既存 build API は
  build root も依存物経路も異なり、現行 API に照合経路がない。
- `schema_version` を上げて世代交代する — 二重 validator と fixture の分岐を招き、
  記録 1 field の追加に対して過大である。世代付き移行は段 0 権限束の所有のまま置く (D1284)。
- 軸を `SPACES` へ射影して記録する — 実際に渡した define を落とし、記録が可変な登録簿に依存する。

## {{D:layer3-contract-pin-additive}}. 層 3 の認定較正 pin は加法的とし、pin だけに絞らない

**決定:** 層 3 の within-run floor 候補は、calibration directory 直下の glob と、campaign の
v2 authority が束縛する ever-active 環境契約の content-addressed calibration **1 件**の
和集合とし、解決後の実 path で重複排除する。`registered/` 全体は走査しない。
pin の解決は加法的かつ best-effort とする。

- pin が存在しない → 候補なしとして扱い、直下候補だけで従来どおり照合し、
  その事実を検索詳細へ機械可読に記録する。レポートは従来どおり出す。
- authority の契約 env_tag と WAL の env_tag が食い違う → 同じく候補なしとして記録する。
- pin が存在して SHA-256 が不一致、repo 外、当該 env の calibration directory 外、
  `..` 成分あり、通常 file でない → 従来どおり fail-closed で拒否する。

一致した within-run floor には根拠語を必ず載せ、値域を 3 つに分ける。
受入証を持つ認定較正は `receipt-derived-build-argv`、build から作られた genome を持つ doc は
`canonical-floor-genome`、genome を持たない record は `genome-absent-legacy-record` とする。
`layer3_schema.json` の当該 field は 3 値 enum へ広げ、`schema_version` は据え置き
`required` にも入れない。

**理由:**
- `registered/` を走査に足すだけでは閉じない。実在する登録済み較正 2 件は genome 不在で
  records・threads・workload が同一のため、両方が一致して複数一致の fail-closed に落ちる。
  区別できる artifact 内 field は無く、環境契約の pin だけが 1 件を選べる。
- pin だけに絞ると受理集合が狭まる。ある環境の契約が pin するのは 1 動作点だけだが、
  directory 直下には別動作点の実在 record がある。pin-only にすると、その動作点の campaign が
  実在値を失って一致なしへ後退する。実在する測定の意味を記録形式の後付け変更で無効にしない。
- pin の不在を硬い赤にすると、自分の出力 root 配下に較正を持たない既存 campaign で
  レポート自体が出なくなる。これも受理集合を狭める方向の回帰であり、
  承認外の過剰拒否である。改竄と境界違反だけを硬い赤に残せば、
  検証できなかった値を採ることは一度もない。
- 較正器は「その build argv がその binary を作った」因果を認証していない。受入証は
  呼び手が渡す JSON である。build から genome を作った producer と同じ根拠語で名乗ると、
  検査していないことを検査したと読ませる。新しい field を足さず、doc に受入証があるかどうかで
  書き分ければ bytes から判定できる。
- schema は producer の実測値域へ合わせる (D829)。この schema への加法的変更では版を上げず
  `required` も変えない (D828)。既存 artifact は従来の値のままで通り、後方互換は保たれる。

**却下した選択肢:**
- `registered/` 全体を glob する — 上記のとおり複数一致で硬直する。
- v2 campaign の候補を pin 1 件に限定する — 実在する別動作点の値を失わせる。
- pin 不在を fail-closed にする — 較正を同梱しない既存 campaign のレポートを止める。
- 環境契約と WAL の env 不一致を硬い赤にする — campaign 全体の整合検査は別の主題であり、
  既存の正常な試験データを新たに拒否する。
- 根拠語を一律にする — 強さの違う根拠が同じ顔で成果物へ入る。
- 根拠語のために新しい field を足す — 受入証の有無から導けるものを二重に持つ。
