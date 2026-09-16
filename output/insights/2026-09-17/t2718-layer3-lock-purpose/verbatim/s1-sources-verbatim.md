# 必読資料の逐語射影 (親が sed で抜粋、編集なし)

## docs/decisions.md D422 (行 17555-17585)
## D422. verifier epoch は導出ラベルとし、読み手に受理目的を表明させる (2026-08-16)

**決定:** `campaign_verifier_epoch` は新しい artifact でも新しい lock field でもなく、
**v2 lock の既存 authority (`contract_loader_blob_sha256s`) からの導出ラベル**とする。
`E1` = 記録された blob map が現在の enforcement source closure と exact 一致、
`E1-stale` = v2 authority を持つが不一致、`E0` = v2 authority を持たない。

除外の適用点は**読み取り側の受理層 1 箇所**に集約し、consumer ごとに散らさない。
各 consumer は `require_admitted_campaign(root, purpose=...)` の `purpose` で、
`CERTIFIED_ACCEPTANCE` (certified を名乗る受理集合として読む) か
`HISTORICAL_RAW` (epoch 表示付きの歴史生値として読む) かを**呼び出し方で表明する**。
`purpose` は既定値を持たず、省略は `TypeError` とする。
certified 側だけが受け取れる view 型を分け、歴史側の view が型境界を越えられないようにする。

**理由:**
- 新しい pin や署名機構を足すと、それ自体が「policy を変えずに受理意味論だけ変える」抜け道に
  なりうる。実 enforcement bytes への束縛だけが、正しさ防壁の書き換えと連動して壊れる。
- 適用点を散らすと、新しい consumer が追加されたときに黙って抜ける。1 箇所へ集約し、かつ
  `purpose` を必須にすると、**新しい呼び出しは表明しない限りコンパイルもテストも通らない**。
  実際、本 wave の取り込みでは、この必須性が別 wave から入った 2 件の未表明呼び出しを露出させた。
- 表明を「呼び出し方」に置くのは、consumer 側の意図を機械が読める形で残すためである。
  同じ campaign を certified として読む経路と歴史生値として読む経路が同居しても、
  どちらの意味で読んだかが呼び出し点に書かれている。

**却下した選択肢:**
- lock へ epoch field を新設する — `IDENTITY_KEYS` / `AUTHORITY_KEYS` は exact key 集合検査なので、
  field 追加は既存 lock を全部不正にする。既存 campaign を引けなくなる。
- consumer ごとに epoch を検査する — 追加漏れが黙って通る。悉皆性を機械で保証できない。
- 受理集合を変えずラベルを表示するだけにする — 「certified を名乗る出力が未検証の証拠に載る」
  という当の問題が残る。裁定 Q1(a) が明示的に除外を選んでいる。
- `purpose` に既定値を与える — 既定が付いた瞬間、新しい呼び出しが黙って片方の意味に倒れる。

## docs/decisions.md D1653 (行 50673-50711)
## D1653. 旧閉包 grammar は歴史閲覧限定の別 decoder で読む (2026-09-05)

**決定 (ユーザー指示による codex 相談を経た親裁定):** enforcement source closure を広げた結果
decode できなくなる旧 grammar の campaign lock は、**`HISTORICAL_RAW` の読み取りに限って**
専用 decoder で読む。現行 certified 経路の受理集合は 1 mm も広げない。
収載する grammar は**実在 corpus が確認できたものだけ**とする。

**理由:**
- 閉包を広げると、旧 grammar を記録した成果物が decode 段で拒否される。この拒否は目的判定より
  前に起きるため、歴史閲覧でも回避できない。外部 root の official lock 11 件が該当し、
  そのうち 3 件は論文図 fig2c の生成経路が実際に読んでいた。**閉包拡張に帰属する回帰である。**
- 記録を新閉包で発行し直す案は規律 7 に反する。lock は WAL より前に live capture して作られるため、
  測定後に不足 path の blob hash を計算しても「測定時に disk bytes と blob が一致した」事実は
  復元できない。lock hash は下流の completion / receipt / manifest の digest 鎖へ伝播しており、
  凍結成果物の bytes を変えない条件とも両立しない。
- 生成経路を bytes 束縛へ移す案は作業量最小だが、失うのが正しさ側の検査
  (環境の起動記録、記録 commit blob 照合、拒否 overlay、試行構成、build receipt) である。
- 独立した 2 レンズが別々に同じ結論と同じ条件へ到達した。

**必須の条件:**
- 通常 decoder / encode / resume / certified admission は現行 grammar のまま。union にしない。
- 別入口・別返却型にする。flag や boolean 引数による緩和にしない。
- `purpose` を decode より前に exact enum で確定する。
- grammar は path 数でなく **exact ordered tuple** で識別し、subset / superset / 同数別集合 /
  順序違いを拒否する。旧 tuple は現行 tuple の slice ではなく独立 literal として置く。
- 記録 commit blob との digest 照合を旧 grammar の全 path で維持する。
- 歴史 epoch は記録 grammar の順序とその grammar 固有の scope 文言で計算し、現行適合は `unknown`。
- 互換実装を新 module へ分離しない (閉包へ入れるべきかという別問題を作らないため、D1128)。

**却下した選択肢:**
- **旧記録を新閉包で発行し直す** — 規律 7 に反し、下流の digest 鎖と凍結成果物を巻き込む。
- **生成経路を bytes 束縛へ移す** — 中央 admission の検査を失う。
- **通常 decoder を union grammar へ広げる** — 認証側の consumer まで旧 grammar を受理する。
- **hash allowlist で個別に許可する** — 既存の hash 台帳を重複させ、成果物ごとの登録が要る。

## D1654. 呼び出し一覧の赤は私有 helper を登録して閉じない (2026-09-05)

**決定:** 呼び出し箇所を exact な一覧として固定する検査が、他 module の**私有 helper** への
到達を検出した場合、期待一覧へその呼び出しを登録して閉じてはならない。

## docs/archive/worklog-phase3-0916-1568.md の T-2718 起票 (行 710-715)
- [T-2718] **P2・新規**: `layer3_report._read_campaign_lock`
  (`orchestrator/campaign/layer3_report.py`) が `purpose` を見ず `decode_campaign_lock` を
  無条件に呼ぶため、中央の歴史閲覧 admission を通った lock でも材料レポート生成段で再拒否される。
  [T-2483] で exact-62 が中央 API から読めるようになった後も、この経路からは読めないままである。
  段 3 のレンズ B が指摘し親が現物で確認したが、読取り経路の本題を超えるので scope 外とした。
  成果物影響 = 歴史閲覧用途の材料レポートが、中央 admission が受理した記録に対して生成できない。

## output/insights/2026-09-16_t2483-exact62-historical-grammar/README.md §6 (行 93-107)
- 「並行編集なし」は 2026-09-16 の測定時点で、114 branch の `main...<branch>` 差分と
  116 worktree の作業ツリーにおける**指定 2 file** に限る。テスト file・他 file・列挙外 checkout・
  測定後の編集には及ばない。
- [T-2125] が本件を塞がないことは、3 本の `search_config.build_admission` が測定時の
  `_current_policy().as_preimage()` と正規化 sha256 `949ddcc295…` で一致した、という意味に限る。
- 受理集合が広がるのは **grammar 単位**であって「この 3 本だけ」ではない。
  D1653 は個体 hash allowlist を却下しており、本 wave もそれに従う。
  ユーザー引数の「対象は既知の 3 本に限定」は、調査と収載 grammar の限定として実施した。

## 7. 段 3・段 6 の所見と裁定

逐語は `verbatim/s3-lensA.md`、`verbatim/s3-lensB.md`、`verbatim/s6-revA.md`、`verbatim/s6-revB.md`。
段 4 裁定の全文は `verbatim/s4-ruling.md`。

| 所見 | 判定 | 対応 |
