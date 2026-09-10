# 段 4 裁定 — [T-474] 旧 trigger artifact に admitted view を名乗らせない

親裁定。段 2 プラン (方向 A の狭い版) と段 3 敵対 2 レンズ (両方 NO-GO) を突き合わせ、
real/refuted と採否、plan v2、変異事前登録を確定する。

## 0. 方向の確定

**方向 A (狭い版) を採る。方向 B (親 brief の P3) は棄却する。**

理由: 方向 B は `require_admitted_campaign` が `AdmittedCampaign` を発行し続けるため、
ユーザー裁定「admitted view を名乗らせない」を満たさない (段 2 プラン、レンズ A 所見 3、
レンズ B F-2 が独立に同じ結論)。親の provisional (P3) は**誤り**であり撤回する。
(P2)「方向 A ならユーザー再裁定が要る」も**誤り** — 再裁定は 2026-08-05 に既に存在する (下記 F-1)。

## 1. 所見の裁定

| # | 所見 | 裁定 | 採否 | scope |
|---|---|---|---|---|
| A-1 | machine-only 判定の帰属不足・過剰拒否を検出できない | **real** | 採用 | 内 |
| A-2 | TOCTOU/ABA で trusted hash と別 bytes の分類を合成できる | **real** | 部分採用 (lock 側のみ) | 一部内 |
| A-3 | 方向 B の field は capability gate でなく警告 | **real** | 採用 (方向 B 棄却の根拠) | 内 |
| A-4 / B-F-7 | post-policy 機械 sweep の membership 穴が残る | **real** | **不採用 (scope 外)** | 外 → 起票 |
| A-5 | M2 は付随レポート文字列の membership しか証明していない | **real** | 採用 (主張を狭める) | 内 (記録) |
| A-6 / B-F-1 | 「ユーザー選択の記録がない」は誤り | **real (段 2 の誤り)** | 採用 | 内 |
| A-7 | P1〜P4 の根拠区分が曖昧 | **real** | 採用 (下記 §2) | 内 |
| B-F-2 | brief の P2/P3 が確定権威と食い違う | **real** | 採用 (撤回) | 内 |
| B-F-3 | freeze consumer は admission gate を通らず二層状態になる | **real** | 採用 (新 D に境界を明記) | 内 (記録) |
| B-F-4 | 方向 B は consumer 結線が伴わない | **real** | 採用 (方向 B 棄却の根拠) | 内 |
| B-F-5 | 同一 schema version への必須 field 追加は in-place 変更 | **real** | 採用 (方向 B 棄却の根拠) | 内 |
| B-F-6 | validator SHA drift が repo 外 receipt を失効させうる | **real (影響は実測で 0 件)** | 採用 (限界を明記) | 内 (記録) |

refuted は 0 件。ただし A-6 は「段 2 プランの主張が誤り」という形の real である。

### 裁定の根拠 (親の実測)

- **F-1 / A-6**: `rulings-inbox/2026-08-04-rulings-session-5rulings.md` §11 に
  発話「基本推奨通りで。codex枠切れは解消しました」と
  「[T-409] = 択一 A=(a) 破棄 + C 縮小版」が明記されている。`docs/worklog.md` (193)(194) にも
  fold 済み。段 2 は superseded.md 1 本しか読まなかったため見落とした。
  **ユーザー再裁定は不要。** ただし D160 決定 5 の該当結果を限定 supersede する新 D を、
  実装・境界テストと同じ変更単位に含める (D96 手続)。
- **F-6**: `/work/1/SFC/tanab` 配下を実測した結果、`admission_decision` を持つ persisted
  artifact は repo 内 0 件、repo 外 0 件 (hit したのは worktree 複製と変異台帳の log のみ)。
  他 filesystem の run-root までは証明できないため、これは**限界として記録する**。
- **A-2**: `artifact_admission.py` は lock を 527 行で hash し、589 行で読み直して parse し、
  602 行で再 hash する。A→B→A の書き換えで、hash は A・分類は B にできる。
  本 wave が追加する判定は**その parse 済み lock を読む**ため、新 gate の回避経路になる。
  よって lock 側は本 wave の scope 内として閉じる。WAL 側の同型露出は既存欠陥であり、
  閉じるには `wal` API の bytes 渡し改修が要るため **scope 外として起票**する。

## 2. P1〜P4 の根拠区分 (A-7 への応答)

- **P1** = observed (歴史枝が検証を通らず view を出す) + hypothesized (読み手の混同という実害)。
  実装判断は observed 部分だけに依拠する。
- **P2** = **撤回** (再裁定は存在する)。
- **P3** = **撤回** (裁定を満たさない)。
- **P4** (reinspection ledger を作らない) = 維持。ただし理由を差し替える。費用ではなく、
  **既存の Git snapshot 三点照合 (`_is_proven_pre_policy_artifact`) が既に exact 台帳として
  機能しており、二重の権威を作らないため**である。

## 3. plan v2 (実装内容)

### 3.1 production (`orchestrator/campaign/artifact_admission.py` のみ)

1. **lock の read-once 化**: `lock_raw = lock_path.read_bytes()` を hash 取得の位置へ移し、
   `lock_sha = hashlib.sha256(lock_raw).hexdigest()` とする。以後 parse・分類・snapshot 照合・
   receipt はすべて**同じ bytes**に由来させる。overlay 枝の membership は hash 比較のみなので
   意味は不変であることを実装子が確認する。
2. **純関数の新設**: `_is_legacy_trigger_lock(lock) -> bool` を追加する。
   真 = `lock` が dict かつ `search_config` が dict かつ `search_config["axis"] == wal.TRIGGER_AXIS`。
   **機械 sweep 形状 (generator/space) では限定しない** — 裁定の文言は「旧 trigger artifact」であり、
   未知形の歴史 trigger も fail-closed 側へ倒す (A-1 への応答)。
3. **歴史枝の分類**: `_is_proven_pre_policy_artifact` を通り、かつ 2 が真なら
   `admission_status = "legacy-unclassified"` を返す。`classification` は
   `"historical-pre-admission-schema"` のまま変えない。偽なら従来どおり
   `"historical-not-reclassified"`。既存の `admitted` property と
   `require_admitted_campaign` の raise 経路をそのまま使う (新 status も新 field も作らない)。

### 3.2 テスト

`orchestrator/tests/test_artifact_admission.py` に次を足す。既存テストの期待値は変更しない。

- **単体真理値表** (corpus 非依存、A-1 の帰属を成立させる):
  `_is_legacy_trigger_lock` を合成 lock で検査する。trigger 軸 × {機械形状 / proposal 形状 /
  未知形状}、非 trigger 軸、`search_config` 非 dict、`search_config` 欠落、lock 非 dict。
- **corpus 反例**: 旧 trigger sweep 6 件を parameterize し、path と lock/WAL の sha256 literal を
  pin した上で `classify_campaign` が `legacy-unclassified` を返し
  `require_admitted_campaign` が `CampaignNotAdmitted` を上げることを検査する。
- **corpus 正例 (過剰拒否の検出)**: 現在 `historical-not-reclassified` で admitted な
  歴史 campaign を**明示 literal の一覧**として列挙し、全件が admitted のままであることを
  parameterize して検査する。これが `p3-` prefix・定数 True 等の広げ変異を殺す。
- `orchestrator/tests/test_layer3_report.py`: 代表 sweep 1 件から新規レポートを発行できず
  `Layer3ReportError` になり、出力ファイルが作られないことを検査する。

### 3.3 非接触

`s8a_trigger_sweep.py`、`output/s1-freeze/`、`output/s8b-freeze/`、既存 campaign/WAL/provenance/
Layer3 の全 bytes、`layer3_schema.json`、`autonomous_trial_completeness.py`、
`s1_direct_comparison.py`、`s1_verify_extime_calibration.py` (並行 wave 所有)。

## 4. 変異事前登録 (DW-M01)

| ID | 変異 (署名) | 期待 kill |
|---|---|---|
| M1 | `_is_legacy_trigger_lock` の本体を `return False` へ置換 | corpus 反例 6 件 + layer3 拒否 + 真理値表 |
| M2 | 同関数を `return True` へ置換 | corpus 正例 (歴史非 trigger) + 真理値表 |
| M3 | 軸比較を `search.get("axis") is not None` へ置換 | 真理値表 (非 trigger 軸) + corpus 正例 |
| M4 | 軸比較を機械形状の連言 (`is_trigger_machine_campaign_lock`) へ差し替え | 真理値表 (trigger 軸 proposal 形状 / 未知形状) |
| M5 | 歴史枝の `"legacy-unclassified"` を `"historical-not-reclassified"` へ戻す | corpus 反例 + layer3 拒否 |
| M6 | `require_admitted_campaign` の `if not decision.admitted` を `if False` へ | corpus 反例 + 既存 `test_three_legacy_campaigns_are_denied` |
| M7 | 判定を歴史枝の外 (post-policy 枝) へも適用 | 既存 `test_post_policy_trigger_machine_sweep_does_not_require_binding` |
| M8 | `lock_sha` を `hashlib.sha256(lock_raw)` から `_sha256_file(lock_path)` へ戻す | **生存見込み** — 静止 repo では等価。ABA は決定論的注入路が無く、テストで到達できない。DW-M04 に従い diff で注入実在を確認し、equivalent ではなく**検出力の穴**として台帳へ記録する |

M8 以外は、同じ入力を拒否する層が前後に無いことを実装子が確認する。

## 5. scope 外として起票する項目 (裁定パッケージ候補)

1. **post-policy 機械 sweep の membership 穴** (A-4 / B-F-7)。`validate_trigger_bindings` が
   機械 lock に `{}` を返し、producer も quarantine へ membership 証明を渡さない。
   `s8a_trigger_sweep.py` が s1 freeze の記録対象であるため所有境界を跨ぐ。
2. **WAL 側 ABA** (A-2 の残部)。`wal.read_records_checked` が bytes を返さないため、
   hash した bytes と parse した bytes の同一性を保証できない。
3. **`implementation` field の二義化** (A-5)。付随レポートで述語と説明文が同じ key に入り、
   かつ built source (`src_token`) へ束縛されていない。

## 6. 成果物影響 (DW-G05)

実装後: 旧 trigger artifact 6 件は raw view と新規 Layer3 発行の受理集合から外れる。
既存の凍結成果物・certified 選択・既存 v2 レポートの bytes は不変で、
`known_axes_freeze` 等の exact-hash 派生は grandfather する (新 D に明記)。
実装しない場合: 6 件は admitted のまま新規材料を発行でき、その材料は trigger membership に
ついて何の証拠も持たないまま「受理済み」と名乗り続ける。

---

## 7. 段 6 追記 (親の訂正)

敵対レビュー 2 本 (R1 = 防壁の実効性と変異検出力、R2 = consumer・契約・所有境界) はいずれも NO-GO。
must-fix 3 件・nit 4 件を real と裁定し、次のとおり対応した。refuted は 0 件。

- **R1-F1 (must-fix、コード)**: read-once 化で終端の lock 再照合が消え、競合更新の検出器を失った。
  終端照合を「拒否専用」として戻す (分類・receipt は最初に読んだ bytes のまま) → fix 子へ。
- **R1-F2 (must-fix、テスト)**: **§4 の M8 登録は誤りだった。** `read_bytes` と hash は別呼び出しであり、
  決定論的な注入路が存在する。M8 は「生存見込みの検出力の穴」ではなく **kill 可能**である。
  境界テストを足して殺す → fix 子へ。
- **R2-1 (must-fix、docs)**: validator sha drift の限界が新 D の非主張から欠落。親が追記済み。
- **R1-F3 / R2-4 (nit ×2、独立指摘のため採用)**: corpus literal の census sentinel → fix 子へ。
- **R2-2 / R2-3 (nit、docs)**: 分類値と consumer の記述精度、supersede 条項の限定。親が修正済み。

段 6 時点の親実測: 対象 2 ファイル 100 passed (request 889258)、全受入
5935 passed / 19 skipped / 0 failed (request 889262)。いずれも fix 前の版に対する測定である。
