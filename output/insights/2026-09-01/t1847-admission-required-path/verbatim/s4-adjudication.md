# 段 4 裁定 — [T-1784][T-1847] 受理記録の置き場所を 1 本に固定する

## 結論

**実装する。** plan v2 は段 2 プランを基礎とし、下記の裁定で 6 点を変更する。
実装面は Codex `role=author` 1 単位。

## 所見の裁定

### sol-1 / 親 (P1-a): 「1 本」は global 1 path か driver ごと 1 path か — **real、per-driver で確定**

- sol は未裁定として親へ戻すよう求めた。luna は独立に事前登録 §5.1 (`:229-233`) と §10 (`:793-797`) を
  読み、driver ごとの 3 canonical path が文書と両立し文書改訂は不要と判定した。
- **採用: driver ごとに 1 path。** 根拠は 3 つ。
  (a) §10 は逐語で「その版へ束縛した admission record を **driver ごとに発行する**」と書く。
  (b) 現 schema は projection 期待値を単一値として持ち、検証器は
      `projection_closure_sha256_by_driver[driver_kind]` と照合する
      (`p3_b4_admission_record.py:770-775`)。global 1 file 案は schema version 昇格を伴う。
      D998 の却下選択肢は「schema 昇格は gate を 1 bit も強くしない」と既に退けている。
  (c) D1050 の趣旨は「複数置ける構造そのものを残さない」ことであり、
      path が `driver_kind` の全域関数であれば**運用者に選択の余地は無い**。本数ではなく
      選択可能性が閉じるべきものである。
- **ユーザーへ戻さない理由:** D1050 は既にユーザー裁定であり、残っているのは実装形の選択である。
  裁定時の未見事実ではない。

### sol-7 / 親 (P1-b): 実装が literal path を先に決めることの是非 — **real、命名を縮めて採用**

- sol は「文書またはユーザー裁定で path を先に固定すべき」とした。この懸念は正しい方向を指すが、
  D1050 の実装を無期限に止める代償が大きい。**折衷を採る。**
- **採用 (a): 規範語を名前から外す。** `CANONICAL` と `CONTRACT` を使わない。
  - 定数: `_REQUIRED_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER`
  - 例外文言: `[admission-record] record repository path is not the path required for driver_kind`
  - テスト名も `canonical` を使わず `required path` の語で書く。
  これは D1000 の「名前で主張を越えない」の直接適用である。この関門が主張するのは
  「検証器がこの driver_kind に要求する path と一致するか」だけで、その path が
  事前登録された正本であるとは主張しない。
- **採用 (b): docstring に sol が指摘した 2 つの非保証を足す。**
  「この module の mapping が事前登録された正本であることは証明しない」
  「driver をまたいで単一 path であることは証明しない」。
- **不採用: 実装を止めて裁定へ戻すこと。** 上記 (a)(b) により、実装は文書の内容を支配しない。
  path 名を後から文書側で固定するときも、この定数は「実装が要求する path」であって
  「事前登録が定めた path」ではないと読める。

### sol-2 / luna: commit をまたぐ record 差し替えは閉じない — **real、docstring に明記のみ**

- 検証器は検証時 HEAD の blob 一致しか要求せず、canonical file を別の valid record へ書き換えて
  新しい HEAD を commit すれば別 invocation で再受理される。
- **採用: docstring に非保証として書く。機構は足さない。** これを閉じるには外部 append-only ledger か
  署名 token が要り、T-1842 として別に裁定待ちである。本 wave の scope 外 (DW-G05)。

### sol-6: 変異の帰属 — **real、fixture を分離して採用**

- mapping literal の同一性 assertion と enforcement の assertion を同じテストに置くと、
  mapping を変える変異では前者が先に落ち、関門の実効性へ到達しない (過剰決定)。
- **採用: enforcement テストでは production mapping との equality assertion を行わない。**
  mapping literal の検査は別テストに置く。変異は「条件付き `raise` を no-op にする」1 点に絞る。

### sol-3 / luna: test factory は関門を通らない — **real、記述の限定として採用**

- `create_b4_closed_critic_pair_for_test` は admission record を取らない
  (`test_p3_b4_closed_critic.py:315-379`)。ただし test-only receipt は certified gate が拒否する。
- **採用: 親 brief と記録の「3 呼び手すべて」を「production の 3 呼び手」へ限定する。**
  実装追加は不要。

### luna: 親 brief の「§5 は 1 欄も未記入」が現物と不一致 — **real、親の誤り。訂正する**

- 事前登録 `:160` は `n = 201、検定単位 = block` を記入済み、`:167` は
  `実行責任者 = thawk105、開始時刻 = 未記入` と部分記入済み。10 欄中 2 欄が埋まっている。
- **親の記述を訂正する。** ただし D1332 の拘束は変わらない。D1332 の再訪条件は
  「記入時の型の誤りが実際に 1 件観測されたとき」であり、記入の有無ではない。
  型の誤りは 1 件も観測されていない。**依頼 (1) は引き続き scope 外。**

### sol / luna: consumer 全件検索と decisions.md 現物確認が射影不足で未完了 — **real、親が実測して補完**

- 親が実測した (下記「親の実測」)。両子の射影不足は prompt 設計の問題であり、所見自体は正しい。

### 不採用・nit

- **不採用: 段 2 プランの `docs/` 配置を `output/` へ移す案。** 両子とも `docs/` 配置に所見を出していない。
  親の独立確認では `tools/check_docs.py` は `docs/` 直下を glob せず (明示列挙 +
  `phase3-s*-runbook.md` + `docs/dev-wave/**` + `docs/provenance/**` の再帰列挙のみ)、
  JSON を置いても文書検査に掛からない。record は生成物ではなく**人間が書いて commit する宣言**であり、
  束縛先の事前登録文書と同じ場所に置くのが読み手にとって自然である。`docs/` を維持する。
- **nit (luna-4): 焦点走コマンドが plan に明文化されていない。** 下記で親が固定する。

## 親の実測 (子の射影外)

1. **`p3-b4-prerun-admission/v1` の record file は repo に 1 件も存在しない** (`find` 全走)。
   親 brief (P1-d) は成立する。
2. **consumer の全件検索 (DW-O26)。** `p3_b4_admission_record` / `verify_b4_admission_record` /
   `_committed_admission_fixture` を参照する file は 9 件。段 2 プランが挙げていない consumer が **3 件**ある。
   - `orchestrator/tests/test_p3_b4_raw_record_producer.py:50,316,893` — shared fixture を import する。
     配置変更の影響を受ける。**焦点走に必須。**
   - `orchestrator/tests/test_ccbench_spawn_sites.py:132` — `("campaign/p3_b4_admission_record.py",
     "<module>._git_call"): 1` と **spawn site 件数を pin する内容走査の一覧検査**。
     本変更は subprocess 呼び出しを増やさないので値は変わらない見込みだが、
     名前 grep では出てこない型の検査なので **焦点走に必須。**
   - `orchestrator/campaign/p3_b4_raw_record_producer.py:663` — projection 閉包を**独立に再導出**する
     二本目の列挙。live 導出なので literal pin は無い。閉包 member の増減は無いので同期は崩れない。
3. **§5 の記入状況** — 10 欄中、`n` 欄が記入済み、`実行責任者・開始時刻` 欄が部分記入済み。

## plan v2 (段 2 プランからの差分)

1. 定数名を `_REQUIRED_ADMISSION_RECORD_REPOSITORY_PATH_BY_DRIVER` にする (`CANONICAL` を使わない)。
2. 例外文言を
   `[admission-record] record repository path is not the path required for driver_kind` にする
   (`contract` / `canonical` を使わない)。
3. docstring の非保証列挙に 2 項を追加する — mapping が事前登録の正本であるとは証明しないこと、
   driver をまたいで単一 path であるとは証明しないこと。commit をまたぐ差し替えの非保証も残す。
4. enforcement テストから production mapping との equality assertion を外し、
   mapping literal の検査を独立したテストに分ける。
5. 焦点走の対象を **5 file** に固定する (段 2 の 3 file + raw_record_producer + ccbench_spawn_sites)。
6. path 選定・関門位置・呼び手の非変更・受理集合の向きは段 2 プランのまま採用する。

## 不変条件 (実装子への拘束)

- 既存テストの期待値 (拒否する入力と拒否理由の exact 署名) を 1 件も変えない。
  置き場所だけを移す。反転・緩和・skip・削除を禁じる。
- 受理集合は狭くする方向にだけ変える。
- 逃がし道 (環境変数・CLI flag・既定引数・警告降格) を作らない。
- `docs/phase3-b4-reflux-ablation-preregistration.md` を編集しない。
- `orchestrator/campaign/p3_b4_wiring_probe.py` と同テストを編集しない。
- 新しい台帳・一般化 resolver・互換層・将来のための抽象を足さない。

## 変異事前登録 (DW-M01)

実装前に登録する。本走は段 6 の fix 後 anchor commit に対して行う (DW-M07)。

|#|変異位置|変異内容|期待|期待 node (完全集合)|単一理由性の根拠|
|---|---|---|---|---|---|
|M1|`p3_b4_admission_record.py` の新設関門|条件付き `raise` を no-op にする (mapping 定数は残す)|KILLED|新設 enforcement テストの負例 node のみ|関門の前段 (`_repository_relative_regular_file`) は repo 内 regular file を通し、後段 (HEAD blob / schema / document binding / projection) は正例と同一 bytes・同一 HEAD の record なので全て通る。落ちる理由は path 一致だけ|
|M2|同 mapping の `base` の値|`"admission.json"` へ差し替える|KILLED|mapping literal 検査の node のみ|enforcement テストは mapping との equality を持たないので、mapping 変異はそちらを落とさない (裁定 sol-6)|

- **M1 が SURVIVED した場合**、他層の mask を疑い、`DW-M02` に従って実効 gate へ再照準する。
  初回結果は消さず erratum に残す。
- 受理集合を**狭める** wave なので、`DW-M01` に従い**承認外の過剰拒否の正例**も登録する。
  正例 = driver ごとの required path に置いた正しい record が受理されること。
  M1・M2 のいずれでもこの正例は緑のままでなければならない (正例が赤になる変異は過剰拒否の兆候)。

## 受入

- 焦点走 5 file → 変異 matrix → 記録 commit → 受入全走 (`tools/dev_wave_wait.py acceptance`)。
- 変更前 baseline (焦点 3 file) は 122 passed / rc=0、計算ノード request 963064.nqsv で実測済み。
