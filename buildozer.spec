[app]
title = Lilu
package.name = lilu
package.domain = ru.lilu
source.dir = .
source.include_exts = py,png,jpg,ttf,otf,wav
version = 1.0
requirements = python3,pygame
orientation = portrait
fullscreen = 1
android.archs = arm64-v8a
android.api = 34
android.minapi = 21
android.accept_sdk_license = True
android.allow_backup = True
# Для Google Play нужен формат AAB (а не APK):
android.release_artifact = aab

[buildozer]
log_level = 2
warn_on_root = 1
