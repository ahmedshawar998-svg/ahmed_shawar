name: Build Android APK

on:
  push:
    branches: [ "main" ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install --upgrade pip
        pip install buildozer cython
        
    - name: Build APK
      run: |
        buildozer init
        sed -i 's/^requirements =.*/requirements = python3,requests/g' buildozer.spec
        sed -i 's/^android.permissions =.*/android.permissions = INTERNET,READ_EXTERNAL_STORAGE,WRITE_EXTERNAL_STORAGE/g' buildozer.spec
        buildozer -v android debug
        
    - name: Upload APK
      uses: actions/upload-artifact@v4
      with:
        name: android-apk
        path: bin/*.apk
        if-no-files-found: error
        retention-days: 90
