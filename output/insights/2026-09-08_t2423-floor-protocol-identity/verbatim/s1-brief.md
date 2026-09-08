# 段 1 brief — [T-2423] 権威 floor 成果物の identity 要素 `protocol` を凍結 spec へ足す

wave: dev-wave-t2423-floor-protocol-identity / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2423-floor-protocol-identity` (local main 34af5a571、clean)
Codex author = D95。実装面は Codex 実装子だけが書く。親は docs-only 本文だけ編集する。

## §0 依頼と、brief 前に実測した新事実

依頼 (command 引数、逐語は `verbatim-t2423-origin.md`): D1641 が権威 floor 成果物名へ求める 5 要素 (env_tag・protocol・threads・workload・campaign 識別子) のうち `protocol` が凍結 spec (`floor-pair-spec/v3`) に無く、build receipt からも導出できないため、issuer が発行を拒否する。択一 (a) 凍結 spec に `protocol` を足す、(b) D1641 の命名要素を 4 要素へ訂正する追記。台帳の推奨 (a)。段 4 で択一を裁定してから実装。

- N1 **凍結 spec の実 instance は repo に存在しない。** `floor-pair-spec/v3` を schema に持つ JSON は insights の変異台帳を除き 0 件。D1774 (`verbatim-d1774.md`) も「driver は production で spec を 1 度も load できていない」と記す。したがって「凍結後の spec 改訂は erratum」の対象となる凍結済み instance は無く、変えるのは spec の **schema (loader の exact key 集合)** である。B-4 事前登録本文 (`docs/phase3-b4-reflux-ablation-preregistration.md`、発効前 draft) は (a) では変更不要 — D1641 の 5 要素はそのまま立つ。
- N2 **build receipt に protocol は無い (依頼の前提は真)。** receipt は `s8b-binary-admission/v2` で、`s8b_binary_admission.py:42-66` の `_SUBJECT_KEYS` / `_BINDING_KEYS` / record exact key に protocol 相当の欄が無い。issuer の `_derive_identity` (`p3_b4_floor_artifact_issuer.py:755-781`) は receipt 内の `protocol` key を探すが、実 receipt では常に失敗し `missing=("protocol",)` を返す。テストは monkeypatch で receipt 検証を差し替えて偽の `protocol` を通している (`test_p3_b4_floor_artifact_issuer.py:56-84`)。
- N3 **`protocol` の意味は CC protocol 名 (`silo` / `mocc` 等)。** 出所は事前登録 §11.2 事実欄「between-run floor driver の出力名は環境 tag・protocol・スレッド数・workload」(`verbatim-prereg-11-2-identity.md`) と `between_run_floor.py:201-207` の命名 (`protocol="silo"`、`_{protocol}` 接尾)。D1641 §3 はそれを 5 要素目 campaign 識別子と共に成果物名へ求める。
- N4 **protocol の検証について既裁定 2 件。** D1696 (`verbatim-d1696.md`): 凍結 spec 側の保証 (成果物名の 5 要素を含む 9 項目) は人手レビュー責任のまま置き validator を拡張しない (再訪条件 = 実害 1 件)。D1373: between-run floor の protocol 許可は固定リストで決めず compiled source の事実へ束縛する — これは between_run_floor 自身の gate の話で、本 wave が spec に新しい許可リストや source 束縛 gate を足す根拠にはならない。
- N5 **SPEC_SCHEMA 文字列は window / plan 成果物へ書かれる** (`floor_pair_driver.py:1302,1316,1328,3049`)。schema id を変えれば window 成果物 bytes も変わる。ただし N1 のとおり production 成果物は無い。test 側の literal pin は `test_floor_pair_driver.py:483-487` (`test_all_four_semantic_schema_identifiers_are_bumped`)。
- N6 **編集面の重複:** 稼働中 wave `dev-wave-t2412-frozen-spec-fixpoint` (peer `frozen spec circularity t-2412 [2e7075]`、locked worktree、未 commit 差分あり、main 未着地) が `floor_pair_driver.py` の HEAD 束縛部 (main 行 1163-1195・1227-1240、`_git_show_head` / 新設 `_git_is_ancestor`)、`test_floor_pair_driver.py` の `_install_git` / `_prepare_spec` / `_prepare_configured_spec` (306-560)、`test_p3_b4_floor_artifact_issuer.py` 行 66・109・507-512 を編集中。本 wave はこれらの行に触れない (§4)。受入直前に main を再読し、t2412 が着地していれば取り込んでから受入する。
- N7 D1759 (`verbatim-d1759.md`): 受理する producer 版は単一定数 1 値、意味の変わる版は fail-closed。issuer の pin は summary 版 (`floor-pair-summary/v3`) であり spec 版ではない。

## §1 親の provisional 裁定 (攻撃対象、段 4 で確定)

- **(P1) 択一は (a) を採る。** (b) は protocol を名前から落とすが、床値は CC protocol ごとに別の量 (between_run_floor も §11.2 も protocol で名前を分ける)。今は 3 driver とも silo だが、名前から protocol を消すと mocc 等の床値と同名衝突する。(a) は D1641 を変えず、事前登録の erratum も要らない (N1)。
- **(P2) 置き場は spec の top-level key `protocol` (1 spec に 1 値、`_identifier` = canonical ID 検査のみ)。** artifacts ごとに持たせると issuer 側に「全 artifact で一致」検査が要り (D1696 の方向へ逸れる)、`environment` に入れるのは意味が違う (protocol は環境でなく測定対象の性質)。
- **(P3) `SPEC_SCHEMA` を `floor-pair-spec/v3` → `floor-pair-spec/v4` へ進める。** exact key 集合が変わる = 同じ id で受理集合が変わる版を作らない (D1759 の向き)。PLAN / WINDOW / SUMMARY の id は変えない (spec の key を持たない)。異論: 「instance が 1 つも無いので v3 のまま key を足してよい」— 段 3 で攻撃せよ。
- **(P4) issuer は `spec.protocol` から identity を取り、receipt から protocol を読む経路 (`_derive_identity` 755-781) を削除する。** spec loader が `protocol` 欠落を exact key で拒否するので、issuer の `missing` に `protocol` が現れる経路は消える。`B4FloorIdentityError` / `missing_identity_elements` の機構自体は残す (threads 不一致・campaign 空は今も起こりうる)。テストの `receipt_has_protocol` と `validate_portable_binary_record` の monkeypatch は削除し、負例は「`protocol` key の無い spec は loader が拒否し issuer は `spec_rejected_by_producer` を返す」、正例は「成果物名と `artifact_identity.protocol` が spec の値と一致」とする。
- **(P5) protocol の値を CCBench source や許可リストへ束縛する gate は足さない。** D1696 と依頼の scope 除外に従う。値の正しさは凍結 spec を書く人手責任 (D1696 の 9 項目と同列)。裁定パッケージ候補として書き残すだけ。

## §2 scope

scope 内: `floor_pair_driver.py` (spec schema + dataclass + loader)、`p3_b4_floor_artifact_issuer.py` (identity 導出、docstring/エラー文言の "receipt" 削除)、両 test file、受入所要台帳の新 nodeid 追加 (必要なら)。
scope 外: 事前登録本文の編集、build receipt schema の変更、protocol の source 束縛・許可リスト、t2412 の provenance 子孫束縛、T-2424 / T-2425 / T-2426、CLI やドキュメントの一般化、新規 gate・検査・台帳。

## §3 不変条件

- 規律 2: issuer は identity 要素が 1 つでも欠ければ発行しない (推測しない)。この性質を変えない。
- `_validate_build_receipt` と receipt の strict 検証 (`floor_pair_driver.py:1052-1080`) は 1 byte も変えない。
- 既存の非保証文 (`NON_GUARANTEES`、driver の `NOT_PROVEN`) を削らない。
- summary / window / plan の schema id は変えない。issuer の受理 summary 版 pin (`floor-pair-summary/v3`) は変えない。
- t2412 の編集行 (N6) に触れない。

## §4 変更面の実アンカー表 (main 34af5a571 の行番号)

| file | 位置 | 変更 |
|---|---|---|
| `orchestrator/campaign/floor_pair_driver.py` | 56 `SPEC_SCHEMA` | v3 → v4 (P3) |
| 同 | 263-280 `FloorPairSpec` | `protocol: str` を `outputs` の後に追加 (t2412 未接触領域) |
| 同 | 1196-1201 top-level key 集合 | `"protocol"` を追加 |
| 同 | 1202-1214 各 parse の並び | `protocol = _identifier(top["protocol"], label="protocol")` |
| 同 | 1241-1257 `return FloorPairSpec(...)` | `protocol=protocol` を `outputs=outputs` の直後に追加 (t2412 の変更は 1240 で終わる) |
| `orchestrator/campaign/p3_b4_floor_artifact_issuer.py` | 7-10 docstring、736-805 `_derive_identity`、890-894 `_authority_value` の文言 | receipt 由来の protocol 導出を削除し `spec.protocol` を使う |
| `orchestrator/tests/test_floor_pair_driver.py` | 185-300 `_valid_document` | `"protocol": "silo"` を追加。483-487 literal を v4 へ。正例 (parsed.protocol) と負例 (key 欠落 → `FloorPairSpecError`、非 ID 値 → 拒否) を追加 |
| `orchestrator/tests/test_p3_b4_floor_artifact_issuer.py` | 40-90 fixture、217-250、473-500、505/557/578 呼出し | `receipt_has_protocol` と monkeypatch を撤去、負例を loader 拒否型へ、正例は名前と identity の一致 |
| `orchestrator/tests/acceptance_duration_ledger.json` | 新 nodeid | 被覆 gate の要否を段 2 で裏取り |

## §5 分割方針・実測環境

実装子 1 本 (Codex author、差分見込み 150 行以下)。段 6 は敵対レビュー 2 本 (レンズ A: 規律 2 / 受理集合、レンズ B: 整合・pin 閉包・t2412 との衝突面) + fix 1 本。
テスト実測は親が login node で焦点走 (`orchestrator/tests/test_floor_pair_driver.py`、`test_p3_b4_floor_artifact_issuer.py`、`test_ccbench_spawn_sites.py`)、受入全走は `tools/dev_wave_wait.py acceptance --lease-optional`。計測は無い (計測層に触れない)。

## §6 変異候補 (段 4 で事前登録、段 2 で精査)

- M1 `_identifier(top["protocol"])` → `_exact_text(...)`: 非 ID 値の負例が殺す。
- M2 issuer が `spec.protocol` でなく `spec.environment.env_tag` を protocol に使う: 名前/identity 一致の正例が殺す。
- M3 `_artifact_filename` から `__protocol-` を落とす: 既存 `test_authority_filename_contains_all_five_derived_components` が殺す。
- M4 `SPEC_SCHEMA` を v3 へ戻す: literal test が殺す (弱い pin であることを明記)。
- M5 top-level key 集合から `"protocol"` を外す: 正例 (protocol 付き spec) 全件が赤 → 帰属が広すぎるなら登録しない。
- M6 issuer が protocol 欠落時に既定値 `"silo"` を推測する: (P4) 後は loader が先に拒否するため issuer 単体では殺せない → 帰属不成立の候補として段 2 で判定。
