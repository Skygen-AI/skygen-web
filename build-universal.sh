#!/bin/bash
# Универсальная сборка для Intel + Apple Silicon

echo "🔧 Собираем для ARM64..."
rustup target add aarch64-apple-darwin
cargo build --release --target aarch64-apple-darwin

echo "🔧 Собираем для Intel..."  
rustup target add x86_64-apple-darwin
cargo build --release --target x86_64-apple-darwin

echo "🔗 Создаем универсальный бинарник..."
mkdir -p target/release
lipo -create \
  target/aarch64-apple-darwin/release/app \
  target/x86_64-apple-darwin/release/app \
  -output target/release/app

echo "✅ Универсальная сборка готова!"
file target/release/app


