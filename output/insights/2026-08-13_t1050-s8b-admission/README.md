# [T-1050] S8b content-addressed binary store の admission receipt 束縛

- wave: `worktree-dev-wave-t1050-s8b-admission`
- 実施日: 2026-08-13 (JST)
- 正本の裁定: ユーザー裁定 第 10 回 #2 (起票)、`output/insights/2026-08-13_t897-trigger-admission/README.md` RP-4
- 逐語: `verbatim/`、変異台帳: `mutation-spec.json` / `mutation-result.json`

## 何が問題だったか

S8b floor が build した binary は content-addressed store へ保存され、resume・floor manifest・
oracle 実走前検査で再利用される。しかし portable record は binary path / hash / store path しか
持たず、build gateway が発行した admission receipt を持っていなかった。
その結果、**admission を証明していない binary でも hash さえ一致すれば** floor 測定値・
manifest・oracle report の証拠鎖へ入れた。

## 何をしたか

`orchestrator/campaign/s8b_binary_admission.py` を新設し、root 非依存の canonical 派生 receipt
(`s8b-binary-admission/v1`) を導入した。発行時に sealed `BuildAdmission` を完全検証したうえで、
policy・review 入力・source digest・ccbench pin・cell・freeze binding・binary SHA・contract を
1 つの receipt へ束縛する。この receipt を保存 → resume → portable projection → floor 測定直前 →
oracle 実走直前まで搬送し、各層で検証する。

拒否する 4 型はいずれも fail-closed である。

| 型 | 拒否層 |
|---|---|
| receipt 欠落 | portable exact-key 契約 + receipt object 契約の二重 |
| receipt と record の不一致 | subject↔record の SHA / tuple 照合 |
| 別 cell の valid receipt 組替え | cell/holdout/configuration/entry/binding の 5 要素 tuple gate |
| store bytes 差し替え | 発行時・store preflight・resume・測定直前・oracle 実走直前の bytes 再 hash |

## 設計上の要点

### raw receipt をコピーしなかった理由

親 brief の provisional 案 (P1) は raw `build-admission/v1` を exact-key field としてコピーする
ものだった。段 2・段 3 の実測により、raw receipt は絶対パス (`source_root`) を含み outer SHA も
root 依存であるため、既存の「異なる root でも production emitter の blob/tree/commit が同一」契約と
両立しないことが判明した。したがって `source_root` だけを除いた root 非依存の派生 receipt を採った。

### 権威を経路で分けた理由

- **live 経路** (build → store → projection → resume → floor 測定直前 → oracle 実走直前) は、
  `build_admission.py` の公開 policy resolver から現行 policy を**独立に再構築**して照合する。
  artifact 内の policy を期待値に使うと恒真検査になり gate として無価値になるため、これを禁じた。
- **historical reverify 経路** (published freeze の再検証) は current policy 一致を要求せず、
  構造・subject・binding・cell 間 policy 一意性だけを要求する。policy は `CURRENT_PIN` から
  導出されるため、pin が進むと過去 freeze の再検証が原理的に落ちるからである。

## 保証の範囲 (過大主張をしない)

この wave が保証するのは「**発行時に検証した admission の、保存から oracle 実走直前までの
連続束縛**」である。「gateway が発行したことの暗号学的証明」ではない。

durable artifact 上の receipt は、整合した JSON を手で書けば自己発行できる。これを閉じるには
署名か外部 trust root が要るが、**[T-868] の既裁定 (2026-08-12)** が同型の問いに対して
「署名方式と trust root は設けない。自己発行可能な性質は明示したまま受容する」と決めている。
本 wave はその裁定に従い、信頼根を新設せず保証名を狭めて明示した。

なお [T-868] は限界を機械可読な limitation 宣言で明示しているが、その宣言経路は T-810
preregistration 族の機構であり、S8b portable record 側には存在しない
(`grep -rn "limitations/" --include=*.py orchestrator/campaign/` は 0 件)。DW-G04 に従い、
発火する既存 artifact path を書けない機構は新設せず、限界の記録は本文書と docstring で行う。

## 敵対レビューが実証した 3 つの罠

段 3 と段 6 で計 4 本の独立レンズを回した。特に重要な発見は次の 3 つである。

1. **恒真な検査**: 「current policy を全 consumer へ渡す」という当初案には値の出所がなく、
   artifact 内の policy を期待値に流用すると `P* == P*` の恒真検査になる。公開 resolver を
   置くことで閉じた。
2. **先取りされる変異**: 事前登録した「receipt key 欠落」の変異は、exact-key 検査が先に発火して
   受理集合を変えないため、診断文字列の変化を kill と誤記録するところだった。
3. **等価変異**: oracle の receipt-subject 対応検査は、validator の事後条件から論理的に冗長で、
   単独削除しても受理集合が変わらない。テスト側が validator の戻り値を monkeypatch で壊して
   初めて赤くなる形になっていた。撤去した。

いずれも「謳うだけで発火しない保証」であり、放置すれば検出力を偽装したまま land していた。

## 変異による裏取り

`mutation-result.json` — **5 本すべて KILLED、期待 node 完全一致 (MISMATCH 0)、baseline 緑**。

| ID | 緩めた gate | 赤になったテスト |
|---|---|---|
| M-B | subject↔record の binary SHA equality | `test_validate_rejects_binary_sha_record_mismatch` |
| M-C | 5 要素 tuple gate | `test_validate_rejects_foreign_cell_receipt_with_identical_other_subjects`, `test_validate_binds_subject_to_record_before_external_expected_tuple` |
| M-D | live policy 一致 | `test_validate_rejects_current_policy_mismatch_after_outer_sha_is_resealed` |
| M-E | live ccbench pin 外部照合 | `test_validate_rejects_external_ccbench_pin_mismatch` |
| M-F | live contract SHA 外部照合 | `test_validate_rejects_external_contract_sha256_mismatch` |

M-C は binary・source・entry・binding が同一で `cell_id` / `holdout_id` だけが異なる 2 receipt を
隔離入力に使った。binary SHA が異なる 2 cell を交換すると binary 検査が先に発火し、
tuple gate の検出力を実証できないためである。

### 変異 probe が暴いた未検査 gate

変異 spec の起動前検査で、**M-E / M-F が対象とする 2 つの外部照合 gate に負例テストが
1 件も存在しない**ことが判明した。`expected_ccbench_pin` を渡す既存箇所はすべて正例だった。
この 2 gate は敵対レビューが blocker と判定した所見の実体であるため、負例 2 本を追加してから
本走した (commit `1d708851`)。**変異の事前登録が、テストの穴を land 前に暴いた例である。**

### 単独変異で殺せない型 (正直に記録する)

- **receipt 欠落**: exact-key 契約と receipt object 契約の二重で構造的に拒否され、
  単独変異でも両層変異でも受理側へ倒せない。冗長 gate として記録し、kill には数えない。
- **oracle の receipt-subject 対応検査**: 上記のとおり等価変異であり、fix で削除した。

## ユーザーへ返す裁定候補 (本 wave では実装しない)

1. **信頼根の不在** — 保証は自己整合 provenance に留まる。[T-868] に従い署名は作らなかった。
   再訪条件は [T-868] と同じく外部公開時と考えられる。
2. **実走後の store 再検証** — `s8b_oracle_report.py` / `s8b_oracle_judge.py` は oracle 実走**後**に
   store bytes を再読しない。ユーザーが指定した境界「oracle 実走直前まで」の外なので非接触とした。
   塞ぐなら別 wave。report は `output_root` を持つが judge は持たないため、
   最終 store seal / report receipt / judge API のどれを採るかの設計裁定が要る。
3. **`BuildResult` の admission 結合** — `BuildResult` は admission receipt も completion manifest
   hash も返さないため、「その binary がその admission を使った build の出力である」ことは
   issuer では検査できない。production の `build_fn` は official wrapper で固定されているので
   露出しているのは test seam であり、`buildcache.py` は非接触とした。
4. **旧 portable artifact の拒否** — 互換 loader・schema 移行・遡及再取得は scope 外のため、
   receipt を持たない旧 artifact は拒否される。tracked `output/s8b-freeze` に該当は
   **0 件** (active v2 generation / approval / active pointer / `binaries` を持つ JSON いずれも 0) で
   repo 内の影響はない。**repo 外の過去 run directory・計算ノード上の durable store・
   手元の resume artifact は再 build か破棄が必要**である。件数は未確認。
5. **`verify_floor_artifact` の残余** — 単体では per-cell freeze entry の権威を持たないため、
   独立 gate とは呼べない。縮小形 (新必須引数を足さず、単体で検査できる範囲を無条件検査) を採り、
   freeze entry 権威は ratified / holdout が持つと docstring に明記した。

## 逐語

`verbatim/` に段 2〜段 6 の子成果物を置く。
`mutation-spec.json` / `mutation-result.json` が変異の事前登録と結果である。
