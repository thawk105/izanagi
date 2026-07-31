# [T-194] 段 6 裁定 — レビュー A/B の real/refuted と fix 指示

逐語は `rev_a.md` (正しさ境界) と `rev_b.md` (テスト検出力)。本書は親の裁定だけを持つ。

## 総括

- 所見 24 件すべてを **real** と裁定した。refuted はゼロ。両レビューは独立に同じ穴 (中継 call site
  4 か所のうち 2 か所が無検査) へ到達しており、独立 2 例の一致として重く扱う
- **親自身の誤りが 3 件確定した** — brief の被害記述 (A-6)、不変条件の文言 (A-6b)、変異事前登録
  (B-2/B-3/B-4)。いずれも親が訂正する

## コード fix (codex 実装子へ再投)

| # | 由来 | 指示 |
|---|---|---|
| F1 | A-1, B-11 | `except BaseException` を `except Exception` へ絞り、`BaseException` (signal / SystemExit) は伝播させる。既存 signal 契約テスト (`test:923-949`) が緑のままであることを静的に確認する |
| F2 | A-2, A-11 | `BrokenPipeError` を専用枝にし、以降の中継を打ち切り、`os.dup2` で devnull へ差し替えて終了時 flush による exit status 120 を防ぐ。打ち切りは無音にせず、可能なら残る stream へ 1 行で告知する |
| F3 | A-3, B-10 | 中継本文を行単位で prefix する (例 `| `)。枠行にも request ID を埋め、子出力が `[Pegasus dispatch]` 行や end 枠を詐称できないようにする。**規律 6 (信頼境界) の要求**であり体裁の問題ではない |
| F4 | A-4 | 切り詰めたときは枠行に実サイズと省略量を出す (`record["size"]` と `record["omitted_bytes"]` は既存)。無告知の切り詰めを禁じる |
| F5 | A-7, B-9 | **(P1) を改訂**: 赤側にも上限を入れる。`DEFAULT_FAILURE_RELAY_LIMIT_BYTES = 64 * 1024`。全量は receipt に残るので一次資料は失われない。既存テスト T2 の「全量」期待はこの改訂に合わせて書き換えてよい (親の裁定変更に伴う正当な更新であり、テストの弱体化ではない) |
| F6 | A-8 | infra 3 経路で dispatcher 自身の原因行を必ず中継より**先**に出す。原因が子ログの山に押し下げられないようにする |
| F7 | A-5, B-1 | `:1179` (receipt 永続化失敗経路) の中継を検査するテストを足す (既存 `test:815` に capsys を足す形でよい) |
| F8 | B-4 | 宣言の巻き上げ (`:881-882`) を戻すと原因が偽装される件を固定するテストを足す (collection 到達前に投げる経路で、原因文字列が `infrastructure failure` 側に出ることを assert) |
| F9 | B-8 | 緑枠 4 KiB / 赤枠 64 KiB の**リテラル**を pin するテストを足す (定数から期待値を導出するだけでは枠の縮小を検出できない) |
| F10 | B-11 | 中継例外時のテストに `_emit` 到達性の assert を足し、前件が消えたとき恒真化しないようにする |
| F11 | B-7 | infra 経路のテストは stdout 側だけを見る形にし、stream 分離の主張は専用テストへ一本化する (単一理由性) |

## 親が行う訂正 (docs / insights)

- **A-6 (brief の被害記述が過大)**: scope 1 の「台帳の受入欄から node 名が欠落する」は誤り。
  `tools/run_tests.py:903` が `sidecar=None` を渡すため、中継を入れても `output/task-runs` の
  `collected_node_digest` は `None` のままである。中継の価値は**親・人間が読める一次資料の確保**に
  限られる。worklog にはこの限界を明記し、台帳欄の修復は別タスクとして起票する
- **A-6b (不変条件の文言が欠陥)**: 「中継の例外を握って rc を変えてはならない」を
  「中継の **I/O 失敗 (`Exception`)** で rc を変えない。`BaseException` (シグナル・`SystemExit`) は
  従来どおり伝播させる」へ改める。旧文言が実装子を `except BaseException` へ追い込んだ

## 変異事前登録の是正 (DW-M01 の再適用)

`s4-adjudication.md` の登録は、call site を特定していないため `DW-M04` の置換一意性を満たさない。
下表で置き換える。anchor は fix 後の最終 diff で `DW-M07` により再検証してから本走する。

| # | 変異 | site | 種別 | 期待 |
|---|---|---|---|---|
| M1 | 通常帰還の中継呼び出しを削除 | 正常経路 | pin | 赤時の stdout 中継を見るテスト群 |
| M2 | 赤でも緑枠へ切り詰め | 正常経路の `successful=` | pin | 赤枠を見るテスト |
| M3 | 緑の枠切り詰めを撤廃 | `_relay_scheduler_logs` の分岐 | pin | 緑枠を見るテスト |
| M4 | 子 stderr の宛先を親 stdout へ | stream 対応表 | pin | stream 分離テスト |
| M5 | 中継の例外捕捉を外す | `except Exception` | **kill** | rc が child_rc から INFRA_RC へ動く |
| M6a | marker 欠落経路の中継を削除 | marker infra site | pin | marker 経路の中継テスト |
| M6b | 外側 except 経路の中継を削除 | 外側 except site | pin | accounting / stage 経路の中継テスト |
| M7 | 中継を receipt 永続化の前へ移す | 正常経路 | **pin へ格下げ** | 順序プローブが赤 (receipt 消失は起きない) |
| M8 | 宣言の巻き上げを try 内へ戻す | 関数冒頭の宣言 | **kill** | 原因文字列が偽の setup 失敗へすり替わる |
| M9 | receipt 永続化失敗経路の中継を削除 | 永続化失敗 site | pin | F7 で新設するテスト |
| M10 | 赤側の上限を撤廃 | 赤枠の切り詰め | pin | F9 のリテラル pin |
| M11 | M5 ∧ M7 の連言 | 上記 2 site | **kill** | receipt が永続化されないまま rc が動く (B-3 が要求した真の kill) |

- kill は M5 / M8 / M11 の 3 件。残り 9 件は `DW-M08` の diagnostic sensitivity pin として別枠に記録する
- harness は第一失敗 node を **assert 行の粒度**で記録する (B-5)。関数名粒度では M1/M5/M7 が衝突する
- 検出力の証明: 新設テストを除外した状態で全変異を走らせ、既存テストでは何件生存するかを併記する

## erratum — 焦点再レビュー (`focus.md`) による登録の再是正

独立の焦点再レビューが上表の登録に 6 件の欠陥を見つけた。すべて real と裁定し、下記で置き換える。
初回登録は消さず本 erratum で上書きする (`DW-M02` の erratum 規律)。

1. **M5 の anchor は一意でない**。`except Exception` は fix 後の中継領域だけで 4 か所ある。
   anchor は `except Exception:` + `continue` の**対**とし、`_redirect_broken_stream_to_devnull` 内の
   枝を潰さないこと。一意でない anchor のままでは harness が誤 site を潰し偽 SURVIVED を記録する
2. **M6a / M6b / M9 の 3 呼び出しは字下げを除いて byte 一致**である (引数まで同一)。anchor には
   必ず先行空白を含める。含めなければ 3 か所にマッチして `DW-M04` の置換一意性で harness が停止する
3. **M8 は「削除」ではなく「移動」**。宣言を単純削除すると正常経路まで `UnboundLocalError` になり、
   B-4 が固定したかった経路とは別の (はるかに検出しやすい) 変異になる。「try 内の収集ブロック直前へ
   移動」と読む
4. **M11 の期待文言を訂正**。「receipt が永続化されないまま rc が動く」は誤りで、receipt は書かれる。
   実害は**その内容が `kind: child` から偽の `kind: infra` へすり替わる**ことである。kill 判定自体は成立
5. **M12 / M13 を追加登録**する。fix で新設された最重要 2 経路が未登録だった —
   M12 = `except _SignalAbort: raise` の削除 (削除すると A-1 が完全再発。kill)、
   M13 = BrokenPipe 枝の削除 (削除すると F2 が丸ごと消える。kill)。
   これらを欠いたまま「中継の fail-closed 挙動を全経路検査した」と台帳へ書くことはできない
6. **assert 行粒度は nit ではなく前提条件**。M1 と M5 は同じテスト関数を赤にするが赤になる行が違い、
   M8 は 1 行だけが kill を担う。harness は第一失敗を**関数名ではなく assert 行**で記録すること

kill は M5 / M8 / M11 / M12 / M13 の **5 件**、pin は残り 8 件、合計 13 件とする。
anchor 逐語は fix 2 巡目の最終差分に対して harness 作成時に確定し、`DW-M07` で本走直前に再検証する。

## erratum 2 — 焦点再レビュー 2 (`focus2.md`) による登録の最終確定

fix 2 巡目後の独立検証で、**erratum 1 の登録がさらに 4 点失効した**。fix が変異検出力を食う型の
副作用であり、`DW-M07` (fix 後 anchor 再検証) の必要性がそのまま実証された。以下で最終確定する。

1. **M5 の anchor が失効した**。erratum 1 は「`except Exception:` + `continue` の対」を指定したが、
   2 巡目で汎用枝の中身が告知呼び出しに変わり、その形の site は**現在ゼロ**。anchor は
   **字下げ 8 の `except Exception:`** とする (字下げ 4 と 12 は別 site で、8 は 1 か所のみ)
2. **M12 / M13 の anchor に字下げ指定が必須になった**。2 巡目で `except _SignalAbort:` が 3→4 site、
   `except BrokenPipeError:` が 1→2 site へ増え、字下げ 4 の双子ができた。どちらも**字下げ 8** を明記する
3. **M13 は kill ではなく pin へ格下げ**。BrokenPipe 枝を削除しても汎用枝が拾って告知先を devnull へ
   差し替えるため、exit-120 の穴は再発しない。失われるのは打ち切りと健全側への告知だけで rc は動かない
4. **M12 を殺すテストが 2 巡目で消滅した (N1)**。汎用枝が告知経由で同じ signal を再送出するため、
   再送出枝を削除しても既存テストは緑のままになる。fix 3 巡目で派生テストを 1 本追加して kill を回復する
5. **追加登録**: M14 = 告知先 broken pipe の devnull 差し替え撤廃 (**kill**。R1 を再開通させ rc が 120 へ
   化ける)、M15 = 汎用例外枝の切断告知撤廃 (pin)、M16 = 告知先 stream 選択の固定化 (pin。killer が
   無いため fix 3 巡目でテスト 1 本追加)、M17a/b/c = 中継を原因行の**前**へ移す 3 site (pin。現行登録は
   削除変異しか持たず、順序性そのものを撃つ変異が無かった)

### 最終登録 (20 件: kill 5 / pin 15)

- **kill (5)**: M5 (中継の例外捕捉削除 → rc が動く)、M8 (宣言の巻き上げを戻す → 原因が偽 setup failure へ
  すり替わる)、M11 (M5∧M7 → receipt が偽 `kind: infra` へすり替わる)、M12 (signal 再送出枝の削除 →
  中断走行が偽の緑として台帳に載る)、M14 (告知先 devnull 差し替えの撤廃 → rc が 120 へ化ける)
- **pin (15)**: M1, M2, M3, M4, M6a, M6b, M7, M9, M10, M13, M15, M16, M17a, M17b, M17c

### harness への前提条件

- 第一失敗は**関数名でなく assert 行**の粒度で記録する。M1 と M5 は同じ関数を別の行で赤にし、
  M8 は 1 行だけが kill を担う
- anchor は**先行空白を含めて**照合し、置換一意性 (`DW-M04`) を各変異で assert する
- M4 は 4 node、M5 は 3 node を赤にする。`DW-M08` の diagnostic 欄に併記する
- 検出力の証明は kill 5 件について「新設テストを除外した状態でも殺せるか」を併走させる

## erratum 3 — 本走後の親裁定 (M8 の kill/pin)

変異本走の結果は 20/20 が期待どおり (KILLED 5 / PINNED 15 / SURVIVED 0 / INVALID 0)。台帳は
`mutation-ledger.json` を一次資料とする。ただし **M8 の分類だけは親が harness と異なる裁定を出す**。

- harness の判定: **KILLED**。根拠 = 「rc は 16 のままだが、収集到達前の例外で error path 自体が
  `UnboundLocalError` で落ち、(a) 真の原因が偽の setup failure へすり替わり、(b) 全 infra 経路の中継が
  消える。dispatcher が自分の失敗理由を捏造する点で診断文字列だけの差ではない」
- **親の裁定: pin へ格下げする**。`DW-M03` は「kill は受理集合か fail-closed 挙動が期待方向へ
  変わったときだけ」と定め、`DW-M08` は「受理集合を変えず構造化シグナルだけを pin する変異は kill でなく
  diagnostic sensitivity pin として別枠に記録する」と定める。M8 は rc も受理集合も動かさないため、
  規律の文言に従えば pin である。harness の言い分 (原因の捏造は診断文字列以上の害) には理があるが、
  **kill の定義を運用側で広げると台帳の kill 件数が規律の外で膨らむ**ため採らない
- したがって本 wave の最終分類は **kill 4 件 (M5 / M11 / M12 / M14) / pin 16 件**とする。
  台帳の生値 (M8 = KILLED) は一次資料として改変せず、本 erratum を併読の正本とする

## backlog へ送る (本 wave の scope 外、次の一手へ起票)

- 台帳 `collected_node_digest` の sidecar 還送 (A-6)。中継とは別経路の設計が要る
- `_bounded_log` の省略注記がリテラルのバックスラッシュ + n で改行になっていない既存欠陥
  (A-9 / B-12)。HEAD にも存在し本 diff は無罪だが、中継が端末上へ露出させた
- 終端待ち中の先読みを将来入れた場合に `:991` / `:1012` が収集済みログを捨てる腐り (A-10)
- 切り詰め経路 (`omitted_bytes > 0`) の中継テスト (B-12)
- **R2 (焦点再レビュー)**: 中継中にシグナルが来たときの複合副作用 — receipt が `kind: child` と
  `kind: infra` の 2 通に分かれる、同じログを二度中継する、`dispatch()` の catch まで抜けると原因が
  `setup failure` とラベルされる。受理集合は動かず (fallback / setup receipt の consumer は自テストのみと
  実測)、rc が INFRA_RC になるのは既存 signal 契約と整合するため本 wave では受容する。ただし
  **この複合経路を通すテストは 1 本もない**
- 告知 stream の ID 表記が生 `request_id`、`_progress` が `normalized_id` で 2 種混在する (R9)
- stdout だけが壊れた場合に健全な stderr 中継まで捨てる (R8。F2 の指示どおりだがコストとして記録)
