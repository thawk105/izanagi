"""orchestrator/tests 共通 pytest 設定 — 一時ディレクトリを tmpfs へ向ける。

campaign 系 (wal / freeze / budget / marker) は耐久性のため書き込みごとに
flush+fsync する。ジャーナリング FS 上の一時 dir ではその 1 回 1 回が実ディスク
バリアになり、スイートが I/O 律速で数百倍遅くなる (実測は worklog 2026-07-17)。
tmpfs では fsync がほぼ無償なので、fsync を呼ぶコード経路はそのまま保たれ
(検査は弱めない)、物理バリアだけが消える。

- 明示的な TMPDIR はユーザー指定として尊重し、何もしない (従来動作へ戻す口)
- /dev/shm が無い・書けない・空きが小さい環境では何もしない (従来動作)。容量
  ガードは、tmpfs が数十 MB しかない環境 (コンテナの既定 shm 等) で TMPDIR を
  読む大容量経路 (patchharness / calibrator runner / trace 生成) が誤誘導的な
  ENOSPC に落ちるのを防ぐ (敵対レビュー所見、insights 2026-07-17)
- pytest の tmp_path も、テスト内の tempfile.* 直接使用も、テストが env を継承
  して起動する subprocess も影響を受ける (いずれも TMPDIR 由来)。素の python3
  実行 (二重 runner) は conftest を経由しない — 必要なら TMPDIR=/dev/shm を手で
  与える (tests/README.md「一時ディレクトリと速度」)
"""
import os
import tempfile

_SHM = "/dev/shm"
_MIN_FREE_BYTES = 1 << 30  # 1 GiB 未満の tmpfs (コンテナ既定 shm=64MB 等) は採用しない


def _shm_usable() -> bool:
    if not (os.path.isdir(_SHM) and os.access(_SHM, os.W_OK | os.X_OK)):
        return False
    try:
        st = os.statvfs(_SHM)
    except OSError:
        return False
    return st.f_bavail * st.f_frsize >= _MIN_FREE_BYTES


if "TMPDIR" not in os.environ and _shm_usable():
    os.environ["TMPDIR"] = _SHM
    # gettempdir() は初回呼び出し結果をキャッシュする — 破棄して TMPDIR を再評価させる
    tempfile.tempdir = None
