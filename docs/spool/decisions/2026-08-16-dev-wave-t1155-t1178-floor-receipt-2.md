---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-16
wave: dev-wave-t1155-t1178-floor-receipt
seq: 2
---

## {{D:floor-receipt-binding-boundary}}. 床値 record の SWO receipt は束縛であって oracle 実行の証明ではない

**決定:** sort_best cell の SWO PASS receipt を床値の durable record へ束縛する。射影は
`cell_id` / `holdout_id` / `configuration_id` / `entry_sha256` / `binary_sha256` の identity 5 項目を
含み、binary record 側の同名値との完全一致を要求する。ホスト絶対パス
(`compiler_realpath` / `dependency_root_realpath`) は成果物へ載せず、`compiler_version` は
sha256 だけを載せる。raw receipt 全体の sha256 を commitment として持つ。

**この receipt が保証するのは「床値 record がどの oracle 実行 receipt を主張しているか」の
durable な辺であって、oracle が実際に走ったことではない。** receipt の全 field は公開かつ決定的で、
oracle を実行せずに合成できる。`receipt_sha256` は private evidence への commitment であり、
raw receipt が到達可能な環境でだけ検算できる。この境界を module と両関数の docstring へ明記する。

**理由:**
- 実行証明には検証時の oracle 再実行か、artifact author と分離された署名付き追記専用 authority が
  要る。どちらも署名・束縛機構の新設であり、bytes 級 provenance 機構は既定で見送りという
  2026-08-12 のユーザー裁定に該当する。
- 一方で identity 束縛は安価で実利がある。これが無いと別 comparator の PASS receipt を
  移植でき、束縛という主張自体が空になる。
- 保証範囲を書かずに land すると、成果物が実際より強い保証を持つと読まれる。

**却下した選択肢:**
- 絶対パスも placeholder 化して全 field を載せる — portable 契約の予約 placeholder 検査と衝突し、
  `compiler_version` は外部 compiler 出力の任意文字列なので軸情報漏洩の迂回路になる。
- sanitized 射影そのものを hash する — 射影は成果物に在るので hash が何も足さない。
- receipt を載せない — 束縛の辺が無いままになり、当該タスクが解けない。

## {{D:live-admission-public-entry}}. 公開 verifier は expected を caller から受け取らない

**決定:** floor 成果物の検証を 2 つの API へ分ける。純射影 verifier は expected admission receipt を
必須 keyword で受け取り、docstring に「live admission を保証しない」と明記する。
公開 consumer (ratified closure / holdout freeze / report) が使う入口は別関数とし、
**その関数自身が live inspector を呼ぶ。expected を受け取る引数を署名に持たない。**

台帳へ到達できない場合も内容不一致と**別 reason** で必ず拒否する。skip・警告化・環境変数の
逃がし道を作らない。

**理由:**
- expected を caller が渡せると、成果物自身の申告値を expected として自己投入でき、
  台帳を消しても完全一致して検出できない。引数の有無という構造で塞ぐのが唯一の確実な形である。
- 到達不能を skip にすると、台帳を消す攻撃が「検証できない」経路で素通りする。
  拒否理由を 2 分するのは、どこで再審査すべきかを判別可能にするためである。

**却下した選択肢:**
- 純 verifier に `repo_root` を渡して内部で inspector を呼ぶ — 純関数であることを壊し、
  artifact だけを持つ既存 consumer が使えなくなる。
- 到達不能を警告に留める — 規律 2 に反する。

## {{D:measurement-head-non-authoritative}}. measurement_head は成果物 identity を束縛しない

**決定:** admission 台帳の `measurement_head` (測定 authority repository の Git HEAD) を、
成果物の portable digest の入力から除外する。形状検査、ledger 行の完全一致、claim の完全一致では
引き続き照合し、片側だけの変更は拒否する。**非権威的な同値確認用 field である**ことを docstring へ
明記する。

**理由:**
- repository-local な値であり、同一の run を別 root で検証すると値が変わる。digest に含めると
  成果物が root 依存になり、成果物の bytes 決定性を固定している既存検査と両立しない。
- 権威化には測定 commit の外部期待値が要り、commit 束縛機構の新設に当たる。
  bytes 級 provenance 機構は既定で見送りという既裁定に該当する。
- 台帳と claim を**同期して**書き換えれば digest も受理集合も変わらない。この性質を隠さず書く。

**却下した選択肢:**
- digest に残す — 成果物が測定 repo の HEAD に依存し、別 root での検証が必ず不一致になる。
- field ごと削除する — 片側改変の検出という現に効いている性質まで失う。
