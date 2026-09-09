---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-09
wave: dev-wave-t2224-certify-protocol-axes
seq: 2
---

## {{D:certify-protocol-axis-table-stays-independent}}. 認定 launcher の protocol 別軸表は shell 側に独立して持ち、genome 空間から実行時導出しない

**決定:** `tools/pegasus/certify_calibration.sh` は protocol → CCBENCH define の対応を、1 protocol
1 block の静的 `case` として自分で持つ。`orchestrator.campaign.genome.SPACES` から実行時に導出しない。
そのうえでテストが、shell を実際に parse して得た表と `SPACES` という **2 つの独立した実体**を突き合わせる。
突き合わせるのは軸名だけでなく、(a) 値まで含めた exact 表との一致、(b) 軸の割り当てが
`SPACES[protocol].enumerate()` の要素であること、の 2 つとする。

**理由:**

- launcher が `SPACES` から軸を導出すると、受け手 `orchestrator/calibrator/cli.py` の
  `missing_axes` 検査が同じ正本を読むため構造的に真になり続ける。producer が軸を落としたことを
  独立に見つける歯が失われる。
- 軸名だけの照合では足りない。制約を持つ protocol では、名前が揃っていても値の組が
  genome 空間の外に出る。tictoc の no-wait を両方 1 にすると `SPACES` の制約が除外する組合せに
  なるが、名前集合の照合では緑のまま通る。段 6 の敵対レビューが反例を構成した。
- テストが `SPACES` から shell の値を生成して比べる形にすると、(a) も (b) も同じ恒真化に落ちる。
  file を読んで得た表と別 module の値を比べる形でなければならない。

**却下した選択肢:**

- **実行時に `SPACES` から導出する** — 上記の恒真化。受け手の検査が 1 つ死ぬ。
- **別の静的成果物へ表を出す** — 新しい正本と同期規則が要る。3 protocol の変更に対して重く、
  生成物にすれば導出案と同じ恒真化、手書きにすれば drift を別 file へ移すだけになる。

## {{D:certification-records-only-values-that-reach-the-compiler}}. 認定 launcher は、コンパイラへ届かない値と供給していない define を genome に載せない

**決定:** 認定較正の genome へ載せてよいのは、その値が実際にコンパイラへ届く define だけとする。
次の 2 つを帰結として固定する。

1. genome 軸名に対応する CMake cache 変数が実体と食い違う protocol は、認定の受理集合へ入れない。
   cicada はこれに当たる。`SPACES` の軸 `INLINE_VERSION_OPT` に対応する cache 変数は
   `CCBENCH_INLINE_VERSION_OPT_CICADA` であり、汎用名で渡すと CMake が未使用と報告して
   値が届かない。
2. patch が供給する define を、その patch を materialize しない経路で新しい protocol へ広げない。
   `BACKOFF_FIXED` はこれに当たる。silo の現行挙動は据え置き、扱いはユーザー裁定へ返す。

**理由:**

- 届いていない値を genome として記録することは、D1374 の却下欄「検査していないことを検査したと
  読ませる」型そのものである。genome は build の忠実な写像でなければならない。
- 旧 cache 名を論理名へ正規化する alias 案は、旧名単独の受領証を偽 genome として受理する反例がある。
  false reject の方が false certified genome より安全である。
- 供給していない define を宣言する行為は、D1198 が「条件が供給されず別の条件を測った型」として
  名指しした失敗そのものであり、新しい protocol でそれを新規に作る理由がない。

**却下した選択肢:**

- **受け手側に protocol 別の alias 正規化を足す** — 受理集合を広げるうえに反例が閉じない。
  実装面も launcher の外へ広がる。
- **cicada を「既定値なら偶然一致する」として通す** — 値 0 のときだけ結果的に正しくなるだけで、
  構造として正しくない。値 1 は上流の死にコードでビルドも通らない。
