# Izanagi 開発用コンテナ (開発層)
#
# 役割: CCBench のビルド・trace 検証・orchestrator 開発 (Phase 1 タスク0-3)。
# 注意: このコンテナは「開発層」。性能計測・calibration には使わない。
#       Mac 上の Docker は VM 内 Linux のため HW PMU (perf の LLC-load-misses 等) が
#       取れず、性能数値も VM オーバーヘッドで歪む。計測は Linux 実機で行う。
#       詳細: docs/decisions.md D10 (環境の二層戦略)

FROM mcr.microsoft.com/devcontainers/base:ubuntu-24.04

# CCBench (v1/v2) のビルドに必要な代表的パッケージ。
# 正確な依存は external/ccbench/build_tools/ubuntu.deps にあり、
# submodule 追加後に post-create.sh が読み込んで追加インストールする。
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    ninja-build \
    git \
    libgflags-dev \
    libgoogle-glog-dev \
    libtbb-dev \
    libjemalloc-dev \
    python3 \
    python3-pip \
    python3-venv \
    linux-tools-generic \
    && rm -rf /var/lib/apt/lists/*

# linux-tools-generic (perf) を入れてあるが、Mac 上の Docker では
# カーネル不一致と PMU 非パススルーのため機能が限定される。
# perf を本格的に使うのは Linux 実機 (計測層) のみ。
