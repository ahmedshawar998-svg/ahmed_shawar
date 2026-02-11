name: Build Android APK

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install dependencies
        run: |
          pip install buildozer cython
          
      - name: Build APK
        run: |
          buildozer init
          buildozer android debug
          
      - name: Upload APK
        uses: actions/upload-artifact@v3
        with:
          name: android-apk
          path: bin/*.apk
