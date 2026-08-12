---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t316-copyout-t840
seq: 1
---

## {{D:build-output-copyout-contract}}. build 出力 copy-out は allowlist した binary 1 本の inode 束縛に限定する

**決定。** buildcache の v2 / legacy とも、staging directory を丸ごと `os.rename` で publish するのを
やめる。allowlist した binary 1 本だけを、保持した dir-fd から `O_NOFOLLOW` で辿って読み出し、
clean directory へ再構築して publish する。metadata (`completion.json` / `admission.json`) は
untrusted staging からコピーせず host が生成する。

**主張の範囲を cache publish 時点の inode 厳格化に限定する。** 次はいずれも主張しない。

- host-security boundary
- certified の安全性
- 実行時の binary identity (publish 後に pathname で開き直して実行する経路は残る。R3-4 / [T-841] の領分)
- staging tree 全体の fd anchor (build subprocess には cmake `-B` で pathname を渡さざるを得ない)
- directory publish の create-only 原子性 (Python 3.10 stdlib に `renameat2(RENAME_NOREPLACE)` がない)

**cache hit 側は no-follow 読みだけを入れ、member allowlist を遡及強制しない。** 強制すると
旧実装が作った既存 cache entry を全件無効化し、正しさの穴でないのに大量の再 build を強制するため
(規律 4)。旧 entry が extra member を持ちうることは残余として docstring に書く。

**環境の POSIX capability 検査は fail-closed にするが、これは platform capability の検査であって、
in-process の関数差し替えに対する防壁ではない。** 判定は import 時に snapshot した original の
`os` 関数を `os.supports_dir_fd` と照合する形にする。現在の callable の同一性で判定すると、
意味を保つ観測用 wrapper まで capability 欠如と誤判定する (実際に既存の並行テストを含む 3 件が
赤くなった)。in-process の trusted caller を境界としない立場は build-admission の既存の立場と同じで、
規律 2 の緩和ではない。段 6 の敵対レビュー 2 本が独立にこの判定を支持した。

## {{D:coder-issuer-machine-closure}}. [T-840] は issuer 集合の機械閉包に限定し、成果物隔離は返す

**決定。** ユーザー裁定は [T-840] を「非認証成果物としての機械隔離」とし、[T-841] の receipt 束縛を
「R3-3 / R3-9 後」として別項に分離した。しかし**この 2 つは成果物のレベルでは分離できない**。

`artifact_admission` は trigger-machine campaign の binding 特例を除き、構造的に妥当な post-policy
campaign を一律 `admission_status="admitted"` で返し、coder 由来かどうかも quarantine を通ったかも
読まない。layer3 はその `admitted` だけを certifying input の条件にしている。したがって
「生成物を非認証として隔離する」を成立させるには分類を下流が消費する必要があり、それが
[T-841] の receipt 束縛そのものである。registry に分類を書くだけでは**恒真ラベル**になる。

この依存関係は裁定時点で提示されていない (2026-08-11 の裁定パッケージ R-2 は
「機械隔離するか、残余のまま台帳に明示するか」の二択として提示し、機械隔離が [T-841] を要すると
書いていない)。よって親は不採用にせず、**新事実つきでユーザー再裁定へ返す**。

**本 wave が実装するのは、曖昧さなく実装でき受理集合を 1 件も縮めない部分だけとする。**

- 単一 registry を site kind (`DIRECT_MATERIALIZER` / `CODER_ENTRYPOINT`) で型付き拡張する。
  第 2 registry を作らない。既存の projection と診断 dict の schema は変えない。
- **未登録 site からの coder authority 発行を、token 生成前に fail-closed で拒否する。**
  現存する 6 entry point はすべて登録済みなので、今通っているものは 1 件も落ちない。
- 補助の AST 閉包は tracked Python 全体を母集合とし、除外を
  `(path, function, helper, count)` の exact allowlist にする。low-level helper binding の
  非 `Call.func` load を taint として拒否する。
- **`QUARANTINE_GATED` という status を新設しない。** 実際の `DiffQuarantineResult.passed` を
  観測しないラベルに quarantine を名乗らせない。
- **site は process-local な authority object へ束縛するが、receipt / WAL / cache identity /
  COMMIT / freeze には 1 bit も入れない。** 保存済みで未消費であり、拒否 gate ではないと docstring に書く。

閉じているのは静的に追跡できる Python issuer だけである。完全動的な文字列、`eval` / `exec`、
外部注入、同一 process からの private factory 直接呼び出し、shell materializer、任意 binary path、
`output/**` の runnable script、下流 artifact admission はいずれも閉じていない。逐語で列挙する。

## {{D:redundant-gate-not-counted-as-evidence}}. 単独で殺せない検査は冗長 gate として証拠から外す

**決定。** 変異検査で、通常ファイル検査 (`stat.S_ISREG`) を単独で無効化しても 1 件も赤にならなかった
(SURVIVED、rc=0)。FIFO はコピー処理の `os.lseek` が ESPIPE を、directory は `os.read` が EISDIR を
先に出して拒否するためで、当該 2 ケースについてこの検査は**冗長**である。

この変異を「殺せた」と記録できないので、次のように扱う。

- 単独変異 (M2) は **`SURVIVED` 期待として登録**し、単独変異の証拠から外す。初回結果は erratum に残す。
- **実効層を含む両層同時変異 (M2b)** を登録し、`S_ISREG` 検査とコピー処理の位置合わせを両方
  無効化すると FIFO のテスト 2 件が落ちることを実測して、防壁の存在を裏付ける。

**「変異を殺せたから防壁が効いている」と書かないための処置である。** 単独で殺せない検査を
効いている証拠に数えると、変異台帳が受理集合の変化を偽って報告する。
