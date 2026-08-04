# 段 4 裁定 — [T-410] sort 軸の構造化 integrity witness

## 結論

**この wave では実装しない。** 遷移は `4→7→8→9`。実装差分が無いため変異事前登録 (`DW-M01`)、
変異 matrix、受入全走は対象外とする。**[T-410] は中止しない** — 設計契約を確定して記録し、
実装の可否をユーザー再裁定へ返す。

## 止める根拠 (裁定時点で未見の新事実、親が実測)

`orchestrator/campaign/silo_ladder_rung1.py` の `_runtime_module_paths` は
`*sorted(verifier.rglob("*.py"))` を含み、**`orchestrator/verifier/` 配下の全 Python** を
committed qualification evidence `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` の
`binding.runtime_modules` へ束縛する。`binding.verifier_module` は `orchestrator/verifier/report.py`、
`binding.driver` は driver 自身を束縛する。

**実測 (worktree 内、復元済み・差分ゼロ):** `orchestrator/verifier/report.py` にコメント 2 行を
追記しただけで `test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` が
`1 failed, 77 passed` になる。無変異時は 78 passed。

- **退避先が無い。** D107 の先例は同型事故 (共有 `tools/pegasus/policy.json` が同じ evidence に
  束縛され同じテストが赤になった) に対し「**後から key を足す側が退く**」と裁定した。本件は
  verifier が witness の producer 本体であり、退く先が存在しない。
- **正規の再束縛経路が無い。** binding を書くのは `collect` (実 job の成果物収集) だけで、
  `verify-result` は検査のみ。evidence 記録後、verifier は 1 度も変更されていない
  (`git log --since=2026-08-01 -- orchestrator/verifier/` が空)。前回の verifier 変更時は
  campaign を実 job で再走している (`c47a01a`「merge 後 verifier での evidence 再取得 — campaign 5」)。
- **迂回は全て禁止。** evidence の hash 書換え、binding 検査の緩和、テストの skip/xfail は
  proof chain の falsification であり `DW-STOP` と規律 2 に反する。

## ユーザーへ返す裁定パッケージ (3 択)

- **(a) rung-1 qualification campaign を実 job で再走し evidence を再発行してから実装する。**
  先例あり (`c47a01a`)。計算資源と単独性確認が要る。実装の意味は変わらない。
- **(b) binding の射程を変える。** verifier を `runtime_modules` から外す、または evidence に版を
  切って「この版はこの verifier bytes に対応する」と明示する。**proof chain の意味を変えるため
  D96 級の手続 (新 D + 境界テスト同時更新) が要る。** 安易に外すと「certified はこの bytes から
  出た」という主張が弱まる。
- **(c) witness を verifier の外 (束縛対象外 module) に作る。** 実装は通るが、T-410 が解こうとした
  「consumer が生 trace を再パースする」問題を温存する (s5 driver の `_count_p_reasons` と同型の
  重複をもう 1 つ増やす)。**親の推奨は (a) または (b)** で、(c) は非推奨。

## 確定する設計契約 (docs へ記録。実装はしない)

D138 が「確定していないこと」に挙げた **sort 軸の同値関係**を、次のとおり確定する。

1. **因果同値ではなく観測同値とする。** P 行の `reason` は comparator の壊れ方ではなく、
   producer 側の**事後検査の分岐名**である。producer は先に size を比べ、size が等しいときだけ
   `rcdptr_` multiset を比べる短絡順で、非反射・非対称・非推移のどの comparator 違反も
   「無傷 / size 変化 / size 同一だが multiset 変化」のいずれにもなりうる。
   したがって comparator 法則 → reason は関数ですらない。
2. **閉じた観測コードへ写像する。** `size-changed` → (size_preserved=false,
   rcdptr_multiset_preserved=NOT_EVALUATED)、`rcdptr-set-changed` → (size_preserved=true,
   rcdptr_multiset_preserved=false)。`reason` の生文字列を意味キーにしない。
3. **同値は固定 origin 内で定義する。** D138 は cut key を origin manifest・emitter・
   verifier policy・environment contract・IR schema へ束縛し、変われば新 origin とする。
   裸の `(kind, reason)` を大域キーにすると、emitter 版が変わって意味が変わっても同一クラスに
   束ねてしまう。
4. **event と class を型として分ける。** dataclass の既定 equality (thid を含む) と同値キー
   (thid を含まない) が併存すると、実効キーに schedule ノイズが戻る。
   `thid`・出現順・件数・txn 境界は class に含めない。
5. **thid は payload でない。** P 行は thid を持たず、`trace_<n>.log` という命名規約からの推定に
   すぎない。`source_thread_hint` のように推定であることを名前に出し、`basis` を持たせ、
   非 canonical 名では None とする (parse error にしない)。
6. **未知 reason は捨てず、意味層では fail-closed。** parser は現行どおり任意の 1 token を受理し
   受理集合を変えない。ただし `recognized=false` を立て、将来の P6 adapter は未知 reason を
   契約エラーにする。観測後に新しい危険クラスを自動生成してはならない。
7. **外部露出は集約する。** 実測で P 行は 1 run あたり最大 879,025 件
   (`s5_permutation_coverage.json` の swap_single)。1 P 行 = 1 JSON object を WAL・critic・
   材料レポートへ無制限に流すと、verifier timeout・巨大 WAL 1 行・critic context 切詰めを招く。
   露出は reason 別件数と bounded sample とし、件数固定 (`len == 3` 等) を受入条件にしない。
8. **LLM 可視面は閉じた語彙にする。** trace 由来文字列は規律 6 のデータであり、critic prompt へ
   素通しされる。判別子は `size-changed | rcdptr-set-changed | unknown` に閉じ、未知語は
   件数と bounded escaped sample として残す (黙って捨てない)。
9. **受理集合不変の証明は実経路で取る。** 手構築 `Integrity` の比較では、`permutation_violations`
   を作る parser/core 自身の変更に発火しない。`parse_trace_dir → verify_trace_dir →
   result_to_dict` を通し、P のみ / 同一 reason 重複 / 複数 trace file / 未知 reason /
   非 canonical filename / 極大件数で旧値と比較する。

## 所見の裁定

### レンズ A

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| 1 | evidence が verifier source を byte-binding | **real (実測で確認)** | 採用 | 裁定パッケージ (実装中止の根拠) |
| 2 | `len(sort_witnesses)==3` は実測件数と両立しない | real | 採用 | 設計契約 7 |
| 3 | 1 P 行 1 object の無制限露出 | real | 採用 | 設計契約 7 |
| 4 | 受理不変の証明が mapper 不変を仮定 | real | 採用 | 設計契約 9 |
| 5 | K12/K13 を同じ `/v1` に押し込む | real | 採用 | 裁定パッケージ (D96 手続) |
| 6 | critic 無変更では P4 を満たさず注入面が広がる | real | 採用 | 設計契約 8 |
| 7 | codex role adapter を live consumer とする | **refuted** | プラン当該項目を削除 | scope 外 |
| 8 | C++ / trace-disabled への観測者効果 | refuted | 対応不要 | — |

所見 7 は親も独立に実測した — verifier role の integrity schema は `{clean}` のみ +
`additionalProperties: false` の縮約射影、`permutation_violations` は manifest に 0 件、
`verification_result` を構築する非テスト経路は 0 件 (dormant)。プランどおり manifest へ
`permutation_violations` / witness を足すと **role の可視範囲を広げる遮断設計の後退**になる。

### レンズ B

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| 1 | reason は事後検査の分岐名で因果でない | real | 採用 | 設計契約 1・2 |
| 1b | 現検査は順序も key↔rcdptr の対応も検査しない | real | 採用 | 裁定パッケージ (C++ producer 改変) |
| 2 | プランの式自体は同値関係 | refuted | — | 定義域の明記のみ採用 |
| 3 | equality が二重化し schedule ノイズが戻る | real | 採用 | 設計契約 4 |
| 4 | 未知 reason が意味層で fail-open | real | 採用 | 設計契約 6 |
| 5 | P6-ready の名乗りは過大 | real | 採用 | 設計契約 2 |
| 6 | thid は filename 由来 hint | real | 採用 | 設計契約 5 |
| 7 | 大域 `(kind, reason)` は origin 境界を破る | real | 採用 | 設計契約 3 |
| 8 | P0 は新経路の E2E 証拠にならない | real | 採用 | P0 を縮小 (下記) |
| 9 | 「T-410 を実装しない」は成立しない | refuted | 同意 | T-410 は継続 |

所見 1b は「現行の permutation 保存検査は multiset しか見ないため、要素の順序が正しいかも、
key と rcdptr_ の対応が保たれているかも検査していない」という**現行検査の被覆の狭さ**である。
コードを読めば確認できる事実として採用する。ただし「非 SWO comparator の UB で実際に
対応だけが入れ替わる」到達可能性は未実証であり、そう書かない。

## 親 brief の provisional 裁定の帰結

- **(P0)** → **縮小して採用。** 実 artifact (`s5_permutation_coverage.json`、all_pass=true、
  erase 249,252 / swap 879,025) は「P 分岐が実在し発火する」という**表現層の最小 gate**は満たす。
  しかし新 witness 経路の E2E 証拠にはならない (driver は検証後に生 trace を削除し、artifact は
  aggregate count しか持たない)。
- **(P1)** → **書き換え。** 「reason 種別のみ」は因果同値としては誤り。固定 origin 内の
  **観測同値**として上記 1〜3 の形で確定する。
- **(P2)** → **保留。** integrity 内配置自体は判定不変にできるが、evidence binding と schema 版が
  解けるまで実装できない。
- **(P3)** → **反対を採用。** login で走らせない点は正しいが、新経路を再現できない以上
  「受入済み」ではなく **E2E 未確認**と記録する。
- **(P4)** → **設計契約 8 として維持。** critic を無変更にすると witness の読み手が増えないため
  「実装したふり」になる。ただし実装は本 wave では行わない。

## 親 brief の誤りの訂正 (worklog へ正しい形で記録する)

1. integrity の exact-key 検査は `codex_roles/policy.py` ではなく
   `campaign/silo_ladder_rung1.py` の evidence schema にある。policy.py は意味不変条件のみ。
2. 「`integrity.notes` の機械 consumer は 0 件」は **refuted** — `critic/digest.py` が
   rejection 描画で notes を 1 行ずつ LLM prompt へ出す。sort 軸の reason 内訳が次手生成へ届く
   唯一の経路がこの自然文である、が正しい言い方。
3. 「reason 内訳は notes でしか assert されていない」は不正確。`test_verifier.py` は
   `ParseIssues.permutation_violations` を `set(...)` で構造的に assert している。
   構造化されていないのは**公開 JSON (`result_to_dict`) の側**である。
