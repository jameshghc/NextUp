# Next Up 0.2.0 (draft)

**Next Up turns your own folders of films and TV into a streaming service of your own,** with tonight's pick, continue-where-you-left-off, TV-style channels and your ratings, all running on your own PC. 0.2 is the first release with **the phone fully on board**. It keeps its own library and streams from the PC over home Wi-Fi, and now it also works as a **remote control for the big screen**.

## Highlights

- **The phone as a remote.** A remote tab on the phone lights up whenever the PC is reachable. It has play/pause, a seek bar you can actually catch, skip, volume, audio delay, subtitles, the channels, and STOP. **▶ ON PC** on any poster starts it on the big screen. You can answer "Are you still watching?" from bed.
- **Streaming from the PC over home Wi-Fi.** Everything on the PC lights up on the phone and plays in mpv-android with no copying, carrying on from wherever you stopped on either device.
- **SEND MY LIBRARY.** One press over the USB cable gives the phone your whole catalogue, ratings, favourites and history, and pairs it for Wi-Fi. Video files are never sent.
- **History that follows you.** Ratings, favourites and watch points swap between phone and PC over the cable and over Wi-Fi.
- **Copy films to the phone** from the PC's Library with a progress bar, the same way you'd fill a USB drive.
- **"Are you still watching?" that actually works mid-film.** It pauses and asks, and if nobody answers it rewinds ten minutes before closing, so you can find your place tomorrow.
- **Glass.** A new frosted-glass look with the film's artwork behind the page. **Settings > Appearance** lets you choose Classic or Glass, the accent colour, glass strength, background art and corners. Glass works on the phone too.
- **A calmer Now page.** Tonight's pick has buttons that stay in one place, a genre chooser that combines tags, and a Continue row with films back in it.
- **Settings in tabs:** Library, Playback, Phone & sharing, Appearance and Storage.
- Per-film **audio delay memory** and **FIND subtitles** (OpenSubtitles) are on the remote.

## Installing

Full, step-by-step instructions are in the [README](../README.md).

1. **PC:** install mpv (`winget install --id shinchiro.mpv -e`) and get a free [TMDB key](../README.md#a-free-tmdb-key).
2. Put `NextUp-0.2.0-windows.exe` in a folder of its own (e.g. `Documents\Next Up`) and double-click it. If Windows says "Windows protected your PC", click More info, then Run anyway.
3. **Settings** (the gear): add your media folders, press **SAVE**, paste the TMDB key, then **SCAN MY FOLDERS**. See [Installing and first run](../README.md#installing-and-first-run).
4. **Phone (optional):** install mpv-android, then `NextUp-0.2.0-android.apk`, and pair with **SEND MY LIBRARY**. See [The phone app](../README.md#the-phone-app).

Upgrading from 0.1.x: put the new exe in the same folder as the old one. Your library, ratings and settings live in that folder, so they carry straight over.

## Known limitations

- **The Android APK is a debug-signed build.** It installs from the file with "install unknown apps" allowed, and Play Protect may warn about it. Updates must be built on the same machine (with the same signing key), or Android will refuse to install them over the top.
- **The desktop app is Windows only** in this release. There's no Mac or Linux package for 0.2.
- **mpv is needed** on the PC, and **mpv-android** on the phone. Next Up doesn't include a player of its own.
- **Phone pairing needs Android's USB tool on the PC** (`winget install Google.PlatformTools`) and **USB debugging** switched on on the phone.
- **The phone link needs the network to cooperate.** Windows Firewall must allow port 8790 (TCP and UDP) on the home network. VPN "LAN invisibility" options (NordVPN's *Invisibility on LAN*) hide the PC, guest Wi-Fi networks keep devices apart, and a sleeping PC can't be reached. The fixes are in [Troubleshooting](../README.md#the-phone-cant-see-the-pc).
- **The exe isn't code-signed,** so Windows SmartScreen warns the first time.
- Profiles share one set of ratings and history for now.
