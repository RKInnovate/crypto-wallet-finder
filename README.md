# Wallet Finder

A desktop application to help find cryptocurrency wallet seeds based on target addresses. The application uses multiprocessing for efficient seed generation and checking.

## Features

- Modern Tkinter-based GUI interface
- Multi-threaded wallet address generation
- Support for custom BIP39 wordlists
- Real-time progress updates
- Save and load target addresses
- Export found results
- Configurable chunk size for performance optimization

## Requirements

- Python 3.10 or higher
- Required Python packages (included in the bundled app):
  - `tkinter` for GUI
  - `pycryptodome` for cryptographic operations
  - `requests` for blockchain API calls
  - `more-itertools` for efficient processing

## Installation

### Using the Pre-built Application (Recommended)

1. Download the latest `WalletFinder.app` from the `dist` directory
2. Move it to your Applications folder
3. Double-click to run

### Building from Source

1. Clone the repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Build the application:

   ```bash
   pyinstaller -y -n WalletFinder \
      --add-data=bip39_wordlist.txt:./ \
      --add-data=icon.png:./ --icon=icon.icns \
      --noconsole finder.py
   ```

   **Note:** Optional arguments only for MacOs

   - --osx-bundle-identifier='{{BUNDLE_NAME}}'
   - --target-architecture={{ARCH_NAME}}
   - --codesign-identity='Developer ID Application: TEAM NAME (TEAM_ID)'
   - --osx-entitlements-file={{ENTITLEMENTS_FILE}}

5. Apple Notarization(Only for MacOS):
   ```bash
   xcrun notarytool submit ubmit WalletFinder.zip \
      --team-id "XXXXXXXXXX" \
      --apple-id "apple@developer.id" \
      --password "XXXX-XXXX-XXXX-XXXX" \
      --wait
   ```

## Usage

1. Launch the application
2. Add target addresses using the "Add Address" button
3. (Optional) Load a custom wordlist file
4. Click "Start" to begin the search
5. Monitor progress in real-time
6. Found matches will appear in the results area
7. Use "Export Results" to save any found matches

## Performance Tips

- The application uses multiprocessing to leverage all available CPU cores
- Larger chunk sizes generally provide better performance but may delay UI updates
- Consider using a focused wordlist to reduce the search space

## Notes

- The application requires an active internet connection to verify addresses
- For security reasons, never share your seed phrases or private keys
- The search process can be CPU intensive

## License

MIT License
