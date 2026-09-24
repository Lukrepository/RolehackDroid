# Rolehack for Android

Rolehack is a NetHack 5.0 variant built around new roles, with a touch interface designed for two thumbs. This repository is the Android app: [JodiJodington's NetHack 5.0 port](https://github.com/JodiJodington/NetHack-Android) with Rolehack's game changes. It runs the interface from [RolehackFront](https://github.com/Lukrepository/RolehackFront).

- **`rolehack`** — everything Rolehack. This is the branch to use.
- **`master`** — upstream, unchanged.

## What's new

- **A fourteenth role, the Apothecary.** Its quest is set at the Royal Mint in Isaac Newton's London. The quest artifact is the Lapis Philosophorum, and the nemesis is the counterfeiter William Chaloner.
- **Grappling** for Cavemen (`#grapple`). Grip, stun and throw.
- **The Rolehack interface**, in landscape. Keycaps sit in a terminal case, with the map framed as a screen. There are three colour styles, and the case can be switched off. See the [RolehackFront README](https://github.com/Lukrepository/RolehackFront/blob/rolehack-ui/README.md) for the controls.

## Playing it

You don't need to build anything to play. You need the APK file: an Android app installer.

1. **Get the APK.** There are no public releases yet, so ask Lucas for the file. It is built for 64-bit ARM (`arm64-v8a`), which covers almost every Android phone from the last several years.
2. **Check for the original NetHack 5 app.** This build still installs as "NetHack 5", under JodiJodington's app ID. If JodiJodington's NetHack 5 is already on your phone, this one will refuse to install over it. Uninstalling the original deletes its saved games.
3. **Install.** Open the APK from your Files app or browser. Android asks whether to allow installs from that app; allow it, then tap Install.
4. **Protect your saves.** Go to Settings → Apps → NetHack 5 → Battery and choose **Unrestricted**. Otherwise Android may stop the app while it is saving, and the save is lost (from the [upstream notes](UPSTREAM-README.md)).
5. **Turn the phone sideways.** The Rolehack interface is landscape-only. In portrait you get the classic button panels.
6. **Adjust it.** Tap MENU (top right) → Settings → Mobile interface. That screen has the colour style, the case on or off, the fonts, the movement key size, and an overall scale.
7. **Quit safely.** Either:
   - use GAME → Save; or
   - press Home, then wait about half a minute before closing the app or installing an update.

   Never force-stop it mid-game.

## Building it

This is the setup that builds the APK today, on Ubuntu 24.04. WSL2 on Windows works; it is what this was built on.

**You need:**

- `gcc`, `make`, `git` and `curl`;
- **JDK 17**;
- the Android SDK command-line tools, with `platforms;android-36` and `build-tools;36.0.0`;
- the **Android NDK r27d**. The makefiles expect it at `/opt/android-ndk-r27d`.

**RolehackFront must be checked out beside this repository.** The Gradle build includes it from `../../../RolehackFront`, relative to `sys/android`:

```
somewhere/RolehackDroid     <- this repository, branch rolehack
somewhere/RolehackFront     <- branch rolehack-ui
```

```sh
git clone -b rolehack    https://github.com/Lukrepository/RolehackDroid.git
git clone -b rolehack-ui https://github.com/Lukrepository/RolehackFront.git
cd RolehackDroid

# Only if your NDK is somewhere other than /opt/android-ndk-r27d:
sed -i "s,^NDK = .*,NDK = /path/to/android-ndk-r27d," sys/android/Makefile.src sys/android/Makefile.top

(cd sys/android && sh ./setup.sh)
make fetch-lua
make install      # the native game library, into sys/android/app/libs/arm64-v8a/

cd sys/android
echo "sdk.dir=/path/to/android-sdk" > local.properties
JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64 ./gradlew assembleDebug
# -> app/build/outputs/apk/debug/app-arm64-v8a-debug.apk

adb install -r app/build/outputs/apk/debug/app-arm64-v8a-debug.apk
```

**Changed game data?** If you changed anything the game reads from `dat/` (levels, quest text), raise the number in `sys/android/app/assets/ver`. The app only unpacks its data again when that number changes.

## Credits and licences

- **NetHack 5.0:** the NetHack DevTeam, under the NetHack General Public License (`dat/license`).
- **NetHack for Android:** gurrhack, with the NetHack 5.0 port by JodiJodington. The upstream README is kept here as [UPSTREAM-README.md](UPSTREAM-README.md).
- **The ForkFront user interface:** gurrhack and JodiJodington, with the Rolehack interface in [RolehackFront](https://github.com/Lukrepository/RolehackFront). ForkFront has no licence file in its upstream repositories; its copyright remains with its authors.
- **Rolehack:** Lucas Ruiz.
